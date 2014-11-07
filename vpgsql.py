
import argparse
from base64 import urlsafe_b64encode
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
from tarfile import DIRTYPE, REGTYPE, LNKTYPE, SYMTYPE
import tempfile
import zipfile


_revision = '1'


def pushd(path):
    return_path = os.getcwd()
    os.chdir(path)
    class popd:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            os.chdir(return_path)
    return popd()


class Recorder:
    def __init__(self, *, algo='sha256', blocksize=1<<16, absolute_paths=True):
        self.algo = algo
        self.blocksize = blocksize
        self.absolute_paths = absolute_paths
        self.record = []

    def add(self, path, digest=None, size=None, absolute=None):
        if self.absolute_paths if absolute is None else absolute:
            path = os.path.abspath(path)
        self.record.append((path, digest, size))

    def mkdir(self, path):
        try:
            os.mkdir(path)
        except FileExistsError:
            return
        if not path.endswith(os.sep):
            path += os.sep
        self.add(path)

    def makedirs(self, path):
        try:
            self.mkdir(path)
        except FileNotFoundError:
            self.makedirs(os.path.dirname(path))
            self.mkdir(path)

    def copy(self, src, dstpath, mode=0o644):
        h = hashlib.new(self.algo)
        try:
            dst = open(dstpath, 'xb')
        except FileNotFoundError:
            self.makedirs(os.path.dirname(dstpath))
            dst = open(dstpath, 'xb')
        with dst:
            os.fchmod(dst.fileno(), mode)
            while True:
                buf = src.read(self.blocksize)
                if not buf:
                    break
                dst.write(buf)
                h.update(buf)
            size = dst.tell()
        digest = h.digest()
        self.add(dstpath, digest, size)

    def symlink(self, srcpath, dstpath):
        try:
            os.symlink(srcpath, dstpath)
        except FileNotFoundError:
            self.makedirs(os.path.dirname(dstpath))
            os.symlink(srcpath, dstpath)
        self.add(dstpath)

    def link(self, srcpath, dstpath, mode=0o644):
        try:
            os.link(srcpath, dstpath)
        except FileNotFoundError:
            self.makedirs(os.path.dirname(dstpath))
            os.link(srcpath, dstpath)
        os.chmod(dstpath, mode)
        self.add(dstpath)

    def remove(self, path):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    def safe_remove(self, path, digest, size):
        with open(path, 'rb') as file:
            if os.fstat(file.fileno()).st_size != size:
                print('file size mismatch; not removing', path, file=sys.stderr)
                return
            h = hashlib.new(self.algo)
            while True:
                buf = file.read(self.blocksize)
                if not buf:
                    break
                h.update(buf)
        if h.digest() != digest:
            print('file hash mismatch; not removing', path, file=sys.stderr)
        else:
            self.remove(path)

    def rollback(self):
        for path, digest, size in reversed(self.record):
            if path.endswith(os.sep) or os.path.isdir(path):
                try:
                    os.removedirs(path)
                except OSError:
                    pass
            elif digest:
                self.safe_remove(path, digest, size)
            else:
                self.remove(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            return
        print('extraction error; backing out changes', file=sys.stderr)
        self.rollback()

    def __iter__(self):
        return self.iter_record()

    def iter_record(self):
        for path, digest, size in self.record:
            if digest:
                digest = '{}={}'.format(self.algo,
                    urlsafe_b64encode(digest).decode('latin1').rstrip('='))
            yield path, digest, size

    def dump(self, dumpfile):
        writer = csv.writer(dumpfile, lineterminator='\n')
        writer.writerows(iter(self))


class ZipFileProxy(zipfile.ZipFile):

    class ZipInfoProxy(zipfile.ZipInfo):
        __slots__ = ()
        name = property(lambda my: my.filename)
        mode = property(lambda my: (my.external_attr >> 16) & 0xFFFF)
        type = property(lambda my: DIRTYPE if my.filename.endsiwth('/') else REGTYPE)

    extractfile = property(lambda my: my.open)

    def getmembers(self):
        members = self.infolist()
        for member in members:
            member.__class__ = ZipFileProxy.ZipInfoProxy
        return members


def unpack(archive_path, destdir):
    if tarfile.is_tarfile(archive_path):
        archive = tarfile.open(archive_path)
    elif zipfile.is_zipfile(archive_path):
        archive = ZipFileProxy(archive_path)
    else:
        raise ValueError('unknown archive format')
    with pushd(destdir), archive, Recorder() as recorder:
        extracted = []
        for member in archive.getmembers():
            parts = member.name.split('/')
            try:
                root, subdir = parts[:2]
            except ValueError:
                continue
            if (root != 'pgsql' or
                    subdir not in ['bin', 'lib', 'include'] or '..' in parts):
                continue
            # Treat links like regular files because pip doesn't uninstall
            # symlinks and the link may come before the linked file.
            if member.type in [REGTYPE, SYMTYPE, LNKTYPE]:
                dstpath = os.path.join(*parts[1:])
                mode = (member.mode | 0o200) & 0o755
                try:
                    src = archive.extractfile(member)
                except KeyError:
                    if member.type != REGTYPE:
                        continue
                with src:
                    recorder.copy(src, dstpath, mode)
        version = subprocess.check_output(
            [os.path.join('bin', 'postgres'), '--version'],
            stdin=open(os.devnull)).split()[-1]
        site_path = os.path.join(
            'lib', 'python{}.{}'.format(*sys.version_info[:2]), 'site-packages')
        os.makedirs(site_path)
        with pushd(site_path):
            dist_info = 'vpgsql-{}.{}.dist-info'.format(version, _revision)
            record_path = os.path.join(dist_info, 'RECORD')
            recorder.add(record_path, absolute=False)
            with open(record_path, 'w') as dumpfile:
                recorder.dump(dumpfile)


_path = os.path.dirname(__file__) or os.getcwd()

#def main(directory=os.path.join(_path, 'env'), prompt='(openeis)'):
def main(argv):
    prog = os.path.basename(argv[0])
    parser = argparse.ArgumentParser(prog=prog,
        description='Install PostgreSQL into a venv virtual Python environment')
    parser.add_argument('-d', '--dir', metavar='PATH',
        help='extract PostgreSQL files into directory')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--pgversion', metavar='VERSION',
        help='specify an explicit PostgreSQL version to install')
    group.add_argument('-f', '--from-archive', metavar='PATH',
        help='install from specified archive')
    opts = parser.parse_args(argv[1:])
    return unpack(opts.from_archive, 'test')
    try:
        in_venv = sys.base_prefix != sys.prefix
    except AttributeError:
        print('{}: unsupported Python version'.format(prog), file=sys.stderr)
        return os.EX_USAGE
    #print(opts)
    if not in_venv:
        print('{}: not in a virtual environment'.format(prog), file=sys.stderr)
        return os.EX_USAGE
    unpack(opts.from_archive, sys.prefix)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        pass
