
import os
import re
import sys
import tarfile
import zipfile

from distutils.command.build import build as _build
from distutils.errors import DistutilsOptionError
from distutils import log

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:
    commands = {}
else:
    class bdist_wheel(_bdist_wheel):
        def get_tag(self):
            tag = getattr(self.distribution, 'tag', None)
            if tag:
                return tag
            return super().get_tag()
    commands = {'bdist_wheel': bdist_wheel}

from setuptools import setup


_accept_re = re.compile(r'^pgsql(?:/(?:(?:bin|lib|include|share/postgresql)(?:/.*)?)?)?$', re.I)
_reject_re = re.compile(r'(^|/)\.\.(/|$)')
_accept = lambda name: _accept_re.match(name) and not _reject_re.search(name)


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


class build(_build):
    user_options = _build.user_options + [
        ('archive=', 'a', 'archive containing PostgreSQL'),
    ]

    #boolean_options = ['compile', 'force']
    #negative_opt = {'no-compile' : 'compile'}

    def initialize_options(self):
        super().initialize_options()
        self.archive = None

    #def finalize_options(self):
    #    super().finalize_options()
    #    self.archive

    def run(self):
        #import pdb; pdb.set_trace()
        if self.archive is None:
            raise DistutilsOptionError("Don't know which archive to extract; use -a/--archive option")
        match = re.search(r'(?:^|{})postgresql-(\d+(?:\.\d+)+(?:-\d+)?)-(.*)-binaries\.(?:tar\.gz|zip)$'.format(re.escape(os.sep)), self.archive, re.I)
        if not match:
            raise DistutilsOptionError('{} is not a valid postgresql archive'.format(self.archive))
        version, platform = match.groups()
        version = version.replace('-', '.') + '-' + self.distribution.get_version()
        platform = {'linux': 'linux-i386', 'linux-x64': 'linux-x86_64',
                    'windows': 'win32', 'windows-x64': 'win-amd64',
                    'osx': 'darwin'}[platform]
        self.distribution.metadata.version = version
        self.distribution.is_pure = lambda *args: False
        self.distribution.tag = ('py2.py3', 'none', platform.replace('-', '_'))
        unpack(self.archive, self.build_lib)
        super().run()

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
