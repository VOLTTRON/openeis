
__version__ = '1'

import argparse
from distutils.util import get_platform
from distutils import log
import html.parser
import os
import posixpath
import re
import shutil
import sys
import tarfile
import tempfile
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
        def finalize_options(self):
            super().finalize_options()
            self.root_is_purelib = False
        def get_tag(self):
            tag = getattr(self.distribution, 'tag', None)
            if tag:
                return tag
            return super().get_tag()
    commands = {'bdist_wheel': bdist_wheel}


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
                'win32': 'win32', 'win-amd64': 'win64',
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


def find_files(path):
    names = []
    lastdir = os.getcwd()
    os.chdir(path)
    try:
        _, dirs, _ = next(os.walk('.'))
        dirs.sort(reverse=True)
        while dirs:
            dirname = dirs.pop()
            for dirpath, dirnames, filenames in os.walk(dirname):
                names.extend(os.path.join(dirpath, name)
                             for name in filenames)
                dirnames.sort(reverse=True)
                dirs.extend(dirnames)
    finally:
        os.chdir(lastdir)
    return names


_ACCEPT_RE = re.compile(
    r'^pgsql(?:/(?:(?:bin|lib|include|share/postgresql)(?:/.*)?)?)?$', re.I)
_REJECT_RE = re.compile(r'(^|/)\.\.(/|$)')


def _accept(name):
    return _ACCEPT_RE.match(name) and not _REJECT_RE.search(name)


def _unpack_tarfile(archive, destdir):
    symlinks = set()
    for item in archive:
        # Skip files not matching our accept pattern
        if not _accept(item.name):
            log.debug('skipping %s', item.name)
            continue
        if item.issym():
            linkname = os.path.normpath(
                os.path.join(os.path.dirname(item.name), item.linkname))
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

'''

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

    user_options = [
        ('archive=', 'a',
         'archive containing PostgreSQL'),
    ]

    def initialize_options(self):
        self.archive = None

    def run(self):
        dist = self.distribution
        if not self.archive:
            self.run_command('download')
            self.archive = dist.get_command_obj('download').path
        basename = os.path.basename(self.archive)
        match = re.match(r'^postgresql-(\d+(?:\.\d+)+(?:-\d+)?)-(.*)-binaries'
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
        unpack(self.archive, self.build_lib)
        metadata = {
            'platform': platform,
            'version': version
        }
        with open('metadata.json', metadata)
        json.dump('metadata.json', metadata)

        #self.plat_name = platform
        #self.distribution.metadata.version = version
        #self.distribution.tag = ('py2.py3', 'none', platform.replace('-', '_'))

commands['build'] = build
'''
_SETUP_PY = '''
from distutils.core import setup
import os

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:
    commands = {{}}
else:
    class bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            super().finalize_options()
            self.root_is_purelib = False
        def get_tag(self):
            return ('cp{pyver.major}{pyver.minor}', 'none', {tagplatform!r})
    commands = {{'bdist_wheel': bdist_wheel}}

def find_files(path):
    names = []
    lastdir = os.getcwd()
    os.chdir(path)
    try:
        _, dirs, _ = next(os.walk('.'))
        dirs.sort(reverse=True)
        while dirs:
            dirname = dirs.pop()
            for dirpath, dirnames, filenames in os.walk(dirname):
                names.extend(os.path.join(dirpath, name)
                             for name in filenames)
                dirnames.sort(reverse=True)
                dirs.extend(dirnames)
    finally:
        os.chdir(lastdir)
    return names

setup(
    name = 'virtual-postgresql',
    version = '{pgversion}_{version}',
    description = 'PostgreSQL for virtual environments',
    author = 'Brandon Carpenter',
    author_email = 'brandon.carpenter@pnnl.gov',
    url = 'http://www.pnnl.gov',
    platforms = ['{platform}'],
    packages = ['pgsql'],
    package_data = {{'pgsql': find_files('pgsql')}},
    cmdclass=commands,
)
'''

PLATFORM_CHOICES = ['linux-i386', 'linux-x86_64',
                    'win32', 'win-amd64', 'darwin']

def main(argv):
    parser = argparse.ArgumentParser(prog=os.path.basename(argv[0]))
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--archive', '-a')
    group.add_argument('--platform', '-p', choices=PLATFORM_CHOICES)
    parser.add_argument('--force', '-f', action='store_true')
    parser.add_argument('--keep', '-k', action='store_true')
    parser.add_argument('dest')
    parser.set_defaults(platform=get_platform())

    args = parser.parse_args(argv[1:])
    tmpdir = None
    created = False
    try:
        os.mkdir(args.dest)
    except FileExistsError:
        if not args.force:
            parser.error(
                '{} exists; use -f/--force to overwrite'.format(args.dest))
    except OSError as exc:
        parser.error('{}: {}'.format(exc, args.dest))
    else:
        created = True
    try:
        if not args.archive:
            print('Finding latest release from', _PSQL_BINARY_DOWNLOAD_URL, '...')
            url = get_latest_url(args.platform)
            parts = urllib.parse.urlsplit(url)
            tmpdir = tempfile.mkdtemp()
            path = os.path.join(tmpdir, posixpath.basename(parts.path))
            print('downloading to', path, '...')
            download_archive(url, path)
            args.archive = path
        unpack(args.archive, args.dest)
        basename = os.path.basename(args.archive)
        match = re.match(r'^postgresql-(\d+(?:\.\d+)+(?:-\d+)?)-(.*)-binaries'
                         r'\.(?:tar\.gz|zip)$', basename, re.I)
        if not match:
            parser.error(
                '{} is not a valid postgresql archive'.format(args.archive))
        version, plat = match.groups()
        try:
            platform = {'linux': 'linux-i386', 'linux-x64': 'linux-x86_64',
                        'windows': 'win32', 'windows-x64': 'win-amd64',
                        'osx': 'darwin'}[plat]
        except KeyError:
            parser.error('unknown platform for {}: {}'.format(args.archive, plat))
        open(os.path.join(args.dest, 'pgsql', '__init__.py'), 'w').close()
        with open(os.path.join(args.dest, 'setup.py'), 'w') as setup_py:
            setup_py.write(_SETUP_PY.format(
                pgversion=version.replace('-', '_'), version=__version__,
                platform=platform, tagplatform=platform.replace('-', '_'),
                pyver=sys.version_info))
    except Exception:
        if created:
            shutil.rmtree(args.dest, True)
        raise
    finally:
        if tmpdir and not args.keep:
            shutil.rmtree(tmpdir, True)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
