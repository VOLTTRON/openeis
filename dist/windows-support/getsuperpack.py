
import argparse
from collections import namedtuple
import hashlib
import os
import re
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET


Release = namedtuple('Release', 'pubdate version name link size hash')


def iter_releases(source):
    tree = ET.parse(source)
    root = tree.getroot()
    namespaces = {'media': 'http://video.search.yahoo.com/mrss/'}
    path = ('./channel/item/media:content'
            '[@type="application/octet-stream; charset=binary"]/..')
    for item in root.iterfind(path, namespaces):
        title = item.findtext('title')
        if not title or title[-4:].lower() != '.exe':
            continue
        _, project, version, name, *rest = title.split('/')
        link = item.findtext('link')
        pubdate = item.findtext('pubDate')
        meta = item.find('media:content', namespaces)
        size = int(meta.attrib.get('filesize'))
        hash_ = meta.find('media:hash', namespaces)
        hash_ = (hash_.attrib.get('algo'), hash_.text)
        yield Release(pubdate, version, name, link, size, hash_)


def open_feed(project):
    url = 'http://sourceforge.net/projects/{}/rss'.format(project)
    response = urllib.request.urlopen(url)
    assert response.status == 200
    return response


def copy_feed(feed, path):
    with open(path, 'wb') as dest:
        shutil.copyfileobj(feed, dest)


def filter_releases(releases, version=None, pyver=None):
    prodver = '[^-]+' if version is None else re.escape(version)
    pyver = '[^-]+' if pyver is None else re.escape(pyver)
    pattern = r'^[^-]+-{}-win32-superpack-python{}.exe$'.format(prodver, pyver)
    regex = re.compile(pattern, re.I)
    for release in releases:
        if regex.match(release.name):
            yield release


def download_release(release, name=None):
    if name is None:
        name = release.name
    response = urllib.request.urlopen(release.link)
    assert response.status == 200
    if release.hash:
        algo, digest = release.hash
        hasher = hashlib.new(algo)
    else:
        hasher = None
    with open(name, 'wb') as dst:
        while True:
            data = response.read(4096)
            if not data:
                break
            dst.write(data)
            if hasher is not None:
                hasher.update(data)
    assert hasher is None or hasher.hexdigest() == digest


def _check_hash(name, algo, digest):
    hasher = hashlib.new(algo)
    with open(name, 'rb') as file:
        while True:
            data = file.read(4096)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest() == digest


def _check_existing(release):
    if release.size is not None:
        if os.stat(name).st_size != release.size:
            return False, '{}: wrong file size'.format(name)
        if not release.hash:
            return True, '{}: missing hash information'.format(name)
    if not release.hash:
        return False, '{}: missing size and hash information'.format(name)
    algo, digest = release.hash
    hasher = hashlib.new(algo)
    with open(name, 'rb') as file:
        while True:
            data = file.read(4096)
            if not data:
                break
            hasher.update(data)
    if hasher.hexdigest() == digest:
        return True, '{}: hash matches'.format(name)
    return False, '{}: hash does not match'.format(name)


def _list_releases(args, releases):
    if args.verbose:
        fmt = '\n    '.join([
            '{0.version}', 'Name:      {0.name}', 'Published: {0.pubdate}',
            'Link:      {0.link}', 'Size:      {0.size}',
            'Hash:      {0.hash!r}'])
    else:
        fmt = '{0.version}: {0.pubdate}\n    {0.name}'
    for release in releases:
        print(fmt.format(release))


def _fetch_release(parser, args, release):
    try:
        filesize = os.stat(release.name).st_size
    except FileNotFoundError:
        pass
    else:
        if not args.force:
            if filesize != release.size:
                extra_msg = ' with wrong size'
            if not _check_hash(release.name, *release.hash):
                extra_msg = ' with wrong hash'
            else:
                print('Verified', release.name)
                return
            parser.error('file exists{}: {}'.format(extra_msg, release.name))
    print('Downloading', release.name)
    download_release(release)


def main(argv):
    parser = argparse.ArgumentParser(
        prog=os.path.basename(argv[0]),
        description='Download Windows superpack installer for '
                    'Scientific Python packages.'
    )
    parser.add_argument('--force', action='store_true',
        help='overwrite existing file')
    parser.add_argument('-l', '--list', action='store_true',
        help='list available packages without downloading')
    parser.add_argument('--python-version', metavar='VERSION',
        help='force download of package for given Python version.')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='produce extra output')
    parser.add_argument('project', choices=['numpy', 'scipy'],
        help='name of Scientific Python project')
    parser.add_argument('version', nargs='?',
        help='download given package version instead of latest')
    parser.add_argument('--no-filter', action='store_true', help=argparse.SUPPRESS)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--from-file', help=argparse.SUPPRESS)
    group.add_argument('--save-feed', help=argparse.SUPPRESS)
    parser.set_defaults(
        list=False,
        python_version='{0.major}.{0.minor}'.format(sys.version_info))

    args = parser.parse_args(argv[1:])
    def verbose(*arg):
        if args.verbose:
            print(*arg, file=sys.stderr)
    if args.from_file:
        verbose('Using feed from', args.from_file)
        feed = open(args.from_file)
    else:
        verbose('Using SourceForge project feed')
        feed = open_feed(args.project)
        if args.save_feed:
            verbose('Saving feed to', args.save_feed)
            with feed:
                copy_feed(feed, args.save_feed)
            feed = open(args.save_feed)
    releases = iter_releases(feed)
    if args.no_filter:
        verbose('Skipping version filtering')
        releases = list(releases)
    else:
        releases = list(filter_releases(
            releases, args.version, args.python_version))
    if args.list:
        return _list_releases(args, releases)
    elif not releases:
        print('No releases found!')
        return 1
    release = releases[0]
    _fetch_release(parser, args, release)


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        pass
