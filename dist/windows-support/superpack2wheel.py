
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

from wheel.tool import convert


def extract(superpack, caps=['sse3'], verboseness=1):
    name = os.path.basename(superpack)
    match = re.match(r'^([^-]+)-([^-]+)-win32-superpack-'
                     r'python(\d+\.\d+).exe$', name, re.I)
    if not match:
        raise ValueError('{}: invalid installer name'.format(name))
    project, version, pyver = match.groups()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract installer archive to temporary directory
        cmd = ['7z', 'e', '-o' + tmpdir, superpack]
        for cap in caps:
            cmd.append('*-{}.exe'.format(cap))
        if verboseness > 1:
            subprocess.check_call(cmd)
        elif verboseness:
            print('Extracting installer ...')
            with open(os.path.join(tmpdir, 'output.txt'), 'w+') as stdout:
                try:
                    subprocess.check_call(cmd, stdout=stdout)
                except subprocess.CalledProcessError:
                    stdout.seek(0)
                    sys.stderr.write(stdout.read())
                    raise
        else:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

        # Save current directory and change to temporary directory
        dirname = os.getcwd()
        os.chdir(tmpdir)
        try:
            exename = '{}-{}.win32-py{}.exe'.format(project, version, pyver)
            whlname = '{}-{}{{}}-cp{}-none-win32.whl'.format(
                project, version, pyver.replace('.', ''))
            wheels = []
            for srcname in os.listdir():
                # wheel.tool.convert() expects win32 installers to be named
                # a certain way. Iterate over each extracted installer and
                # name like exename above and rename to match whlname above
                # saving the CPU caps tag to add back to the file afterward.
                match = re.match(r'.*-(nosse|sse[23]).exe', srcname, re.I)
                if not match:
                    continue
                cap, = match.groups()
                os.rename(srcname, exename)
                convert([exename], '.', verboseness > 1)
                os.remove(exename)
                # Rename the generated wheel to include the caps tag.
                ssewheel = whlname.format('_' + cap)
                os.rename(whlname.format(''), ssewheel)
                wheels.append(os.path.join(tmpdir, ssewheel))
        finally:
            os.chdir(dirname)
        for wheel in wheels:
            try:
                shutil.move(wheel, '.')
            except shutil.Error as exc:
                print(exc, file=sys.stderr)

def main(argv):
    parser = argparse.ArgumentParser(
        prog=os.path.basename(argv[0]),
        description='Convert Windows superpack installer for '
                    'Scientific Python packages to wheel.'
    )
    parser.add_argument('--force', action='store_true',
        help='overwrite existing file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet', dest='verboseness', action='store_const', const=0,
        help='produce less output')
    group.add_argument('-v', '--verbose', dest='verboseness', action='store_const', const=2,
        help='produce extra output')
    parser.add_argument('--sse3', dest='caps', action='append_const', const='sse3',
        help='create a wheel for CPUs with SSE3 support')
    parser.add_argument('--sse2', dest='caps', action='append_const', const='sse2',
        help='create a wheel for CPUs with SSE2 support')
    parser.add_argument('--nosse', dest='caps', action='append_const', const='nosse',
        help='create a wheel for CPUs with no SSE support')
    parser.add_argument('--keep-temp', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('superpack', help='superpack installer to convert')
    parser.set_defaults(caps=[], verboseness=1)

    args = parser.parse_args(argv[1:])
    if not args.caps:
        args.caps.append('sse3')
    return extract(args.superpack, args.caps, args.verboseness)


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        pass
