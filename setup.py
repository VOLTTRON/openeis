
from distutils.core import Command
from distutils.command.build import build as _build
from distutils.errors import DistutilsOptionError
from distutils.util import get_platform
from distutils import log
import html.parser
import os
import posixpath
import re
import sys
import tarfile
import threading
import urllib.parse
import urllib.request
import zipfile

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:
    commands = {}
else:
    class bdist_wheel(_bdist_wheel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.distribution.is_pure = lambda *args: False
        def finalize_options(self):
            super().finalize_options()
            self.root_is_purelib = False
        def get_tag(self):
            tag = getattr(self.distribution, 'tag', None)
            if tag:
                return tag
            return super().get_tag()
    commands = {'bdist_wheel': bdist_wheel}

from setuptools import setup


_PSQL_BINARY_DOWNLOAD_URL = ('http://www.enterprisedb.com/'
                             'products-services-training/pgbindownload')
_PSQL_BINARY_DOWNLOAD_RE = re.compile(
    r'^/postgresql-[0-9-]+-binaries-(\w+)(?:\?.*)?$')


def urlhead(url, *handlers):
    opener = urllib.request.build_opener(*handlers)
    request = urllib.request.Request(url, method='HEAD')
    return opener.open(request)


def get_download_url(front_url):
    cookie_handler = urllib.request.HTTPCookieProcessor()
    response = urlhead(front_url, cookie_handler)
    assert response.status == 200
    for cookie in cookie_handler.cookiejar:
        if cookie.name == 'downloadFile':
            return urllib.parse.unquote(cookie.value)


def get_front_urls(plat_name, url=_PSQL_BINARY_DOWNLOAD_URL):
    platform = {'linux-i386': 'linux32', 'linux-x86_64': 'linux64',
                'win32': 'windows32', 'win-amd64': 'windows64',
                'darwin': 'osx'}[plat_name]
    links = []
    class LinkParser(html.parser.HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                for name, value in attrs:
                    if name == 'href':
                        match = _PSQL_BINARY_DOWNLOAD_RE.match(value)
                        if match and match.group(1).lower() == platform:
                            links.append(value)
                        break
    parser = LinkParser()
    with urllib.request.urlopen(url) as response:
        parser.feed(response.read().decode('utf-8'))
    parts = urllib.parse.urlsplit(url)
    for i, link in enumerate(links):
        links[i] = urllib.parse.urlunsplit(
            parts[:2] + urllib.parse.urlsplit(link)[2:])
    return links


def get_download_urls(front_urls, threadcount=None):
    front_urls = list(enumerate(front_urls))
    if not threadcount:
        threadcount = len(front_urls)
    download_urls = []
    def fetch_url():
        while True:
            try:
                index, url = front_urls.pop()
            except IndexError:
                return
            download_urls.append((index, get_download_url(url)))
    threads = []
    for i in range(threadcount):
        thread = threading.Thread(target=fetch_url, daemon=True)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    download_urls.sort()
    return [url for i, url in download_urls]


def get_latest_url(plat_name):
    front_urls = get_front_urls(plat_name)
    download_urls = get_download_urls(front_urls[:1])
    return download_urls[0]


def download_archive(url, path):
    with urllib.request.urlopen(url) as response, \
            open(path, 'wb') as archive:
        while True:
            buf = response.read(4096)
            if not buf:
                break
            archive.write(buf)


def same_size(url, path):
    response = urlhead(url)
    if response.status == 200:
        size = response.headers.get('Content-Length')
        return size == os.stat(path).st_size


_ACCEPT_RE = re.compile(
    r'^pgsql(?:/(?:(?:bin|lib|include|share/postgresql)(?:/.*)?)?)?$', re.I)
_REJECT_RE = re.compile(r'(^|/)\.\.(/|$)')


def _accept(name):
    return _ACCEPT_RE.match(name) and not _REJECT_RE.search(name)


def _unpack_tarfile(archive, destdir):
    symlinks = set()
    for item in archive:
        if not _accept(item.name):
            log.debug('skipping %s', item.name)
            continue
        if item.issym():
            linkname = os.path.normpath(os.path.join(
                    os.path.dirname(item.name), item.linkname))
            if not _accept(linkname):
                log.debug('skipping %s symlinked to %s', item.name, linkname)
        path = os.path.join(destdir, item.name)
        item.mode = (item.mode | 0o644) & 0o755
        try:
            st = os.stat(path)
        except FileNotFoundError:
            pass
        else:
            if st.st_mtime == item.mtime and st.st_size == item.size:
                log.info('skipping existing file %s', path)
            continue
        log.info('extracting %s to %s', item.name, destdir)
        archive.extract(item, destdir)
        if item.issym():
            symlinks.add(item.name)
    for name in symlinks:
        path = os.path.join(destdir, name)
        if not os.path.exists(path):
            log.info('removing broken symlink %s', path)
            os.unlink(path)


def _unpack_zipfile(archive, destdir):
    for item in archive.infolist():
        if not _accept(item.filename):
            log.debug('skipping %s', item.filename)
            continue
        log.info('extracting %s to %s', item.filename, destdir)
        archive.extract(item, destdir)
        filemode = (item.external_attr >> 16) & 0xFFFF
        mode = (filemode | 0o644) & 0o755
        if mode != filemode:
            os.chmod(os.path.join(destdir, item.filename), mode)


def unpack(archive_path, destdir):
    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path) as archive:
            _unpack_tarfile(archive, destdir)
    elif zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(os.path.abspath(archive_path)) as archive:
            _unpack_zipfile(archive, destdir)
    else:
        raise ValueError('unknown archive format')


class download(Command):

    description = 'download PostgreSQL binary archive'

    user_options = [
        ('build-temp=', 't',
         'temporary build directory'),
        ('force', 'f',
         'overwrite existing archive'),
        ('plat-name=', 'p',
         "platform name to build for, if supported "
         "(default: %s)" % get_platform()),
    ]

    boolean_options = ['force']

    def initialize_options(self):
        self.build_temp = None
        self.plat_name = None
        self.force = False

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_temp', 'build_temp'),
                                   ('plat_name', 'plat_name'))

    def run(self):
        log.info('PostgreSQL binary archive not given; finding latest '
                 'release from %s', _PSQL_BINARY_DOWNLOAD_URL)
        url = get_latest_url(self.plat_name)
        parts = urllib.parse.urlsplit(url)
        path = os.path.join(self.build_temp, posixpath.basename(parts.path))
        if self.force or not os.path.exists(path):
            log.info('downloading %s to %s', url, self.build_temp)
            os.makedirs(self.build_temp, exist_ok=True)
            download_archive(url, path)
        else:
            log.info('skipping download of existing file %s', path)
        self.path = path

commands['download'] = download


class extract(Command):
    
    description = 'extract PostgreSQL binary archive into build'

    user_options = _build.user_options + [
        ('archive=', 'a',
         'archive containing PostgreSQL'),
        ('build-platlib=', None,
         "build directory for platform-specific distributions"),
    ]

    def initialize_options(self):
        self.archive = None
        self.build_lib = None

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_lib', 'build_lib'))

    def _parse_archive(self):
        basename = os.path.basename(self.archive)
        re.match(r'^postgresql-(\d+(?:\.\d+)+(?:-\d+)?)-(.*)-binaries'
                 r'\.(?:tar\.gz|zip)$', basename, re.I)
        if not match:
            raise DistutilsOptionError(
                '{} is not a valid postgresql archive'.format(self.archive))
        version, plat = match.groups()
        version = '-'.join([version.replace('-', '.'),
                            self.distribution.get_version()])
        platform = {'linux': 'linux-i386', 'linux-x64': 'linux-x86_64',
                    'windows': 'win32', 'windows-x64': 'win-amd64',
                    'osx': 'darwin'}[plat]
        self.distribution.metadata.version = version
        self.distribution.tag = ('py2.py3', 'none', platform.replace('-', '_'))
        self.plat_name = platform

    def run(self):
        if not self.archive:
            self.run_command('download')
            self.archive = self.distribution.get_command_obj('download').path
        unpack(self.archive, self.build_lib)

commands['extract'] = extract


class build(_build):
    sub_commands = _build.sub_commands + [('extract', None)]

    def finalize_options(self):
        build_lib = self.build_lib
        super().finalize_options()
        if build_lib is None:
            self.build_lib = self.build_platlib

commands['build'] = build


if __name__ == '__main__':
    setup(
        name = 'virtual-postgresql',
        version = '1',
        description = 'PostgreSQL for virtual environments',
        author = 'Brandon Carpenter',
        author_email = 'brandon.carpenter@pnnl.gov',
        url = 'http://www.pnnl.gov',
        packages = ['pgsql'],
        #packages = find_packages(),
        #install_requires = install_requires,
        #entry_points = '''
        #    [console_scripts]
        #    openeis = openeis.server.manage:main
        #''',
        #package_data = {
        #    'openeis.projects': [ os.path.join('static', x) for x in get_files(os.path.join(basepath, 'openeis', 'projects', 'static'))]
        #}
        cmdclass=commands,
    )
