# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}


""" Automation file for building openeis installer for distribution.
"""
import json
import os
import posixpath
import shutil
import subprocess
import sys
import tempfile

from openeis.projects.version import get_version_info

basedir = os.path.abspath(os.path.dirname(__file__))
# Script should always be called from the root of the repository.
OPENEIS_SRC_DIR = os.path.abspath(os.curdir)

cfg = {}

for x in ('CLEAN_PYTHON_DIR', 'WORKING_DIR', 'OPENEIS_SRC_DIR',
          'WHEEL_DIR', 'INNO_SETUP_DIR', 'MISC_DIR',
          'PRE_BUILT_WHEELS'):
    cfg[x] = ''


# This is the python (extracted from the msi file)
# that should be distributed with openeis.
CLEAN_PYTHON_DIR = cfg['CLEAN_PYTHON_DIR'].replace('/', '\\')

# A writeable directory for full installation
# of support files.
WORKING_DIR = cfg['WORKING_DIR'].replace('/', '\\')

# The location of the cache wheel directory so we
# don't need to re download things from the internet.
WHEEL_DIR = ''

# Misc directory that will get copied to the root directory
# of the installed application when installing on the client
# machine.
MISC_DIR = cfg['MISC_DIR'].replace('/', '\\')

# The directory of an extracted inno setup folder.  This can
# be obtained through innoextractor program from the internet.
INNO_SETUP_DIR = cfg['INNO_SETUP_DIR'].replace('/', '\\')


OUTPUT_FILE = ''

# A temp cirectory for use during this build.
TEMP_DIR = ''

ORIG_CWD = os.path.abspath(os.getcwd())

OPENEIS_SETUP_SUPPORT_DIR = ''

_vinfo = get_version_info()
_VERSION_STRING = 'openeis-setup_{}-{}-{}'.format(_vinfo['version'],
                                                  _vinfo['revision'],
                                                  _vinfo['vcs_version'])

# def build_exe():
#     print('building exe using spec file: {}'.format(cfg.spec_file))
#     cwd = os.getcwd()
#     try:
#         os.chdir(cfg.ece_server_dir)
#         do_call(['pyinstaller', '--onefile', '--clean', '--noconsole', # '--windowed',
#                  '--icon', cfg.icon_file,
#                  "{}".format('ece-app.py')])
#     finally:
#         os.chdir(cwd)


def move_wheel(src_file):
    """Move the src_file wheel from the current directories dist dir to wheeldir

    Requires that the cwd is in the same location as it was during the creation
    of the wheel.
    """
    if os.path.exists(os.path.join(WHEEL_DIR, src_file)):
        os.remove(os.path.join(WHEEL_DIR, src_file))
    shutil.move(os.path.join('dist', src_file),
                             os.path.join(WHEEL_DIR, src_file))


def cleanup():
    if os.path.exists('build'):
        shutil.rmtree('build')


def build_wheels():
    """Builds the openeis and openeis-ui wheels, puts them in WHEEL_DIR

    This assumes that the executing python has bee activated with
    a bootstrapped python.
    """
    try:
        os.chdir(os.path.join(OPENEIS_SRC_DIR))
        if os.path.exists('build'):
            shutil.rmtree('build')

        print('Executing wheel on openeis')
        ret = subprocess.check_call([r'env\Scripts\python.exe', 'setup.py', 'bdist_wheel'])

        for f in os.listdir('dist'):
            if f[-3:] == 'whl':
                move_wheel(f)

        os.chdir(os.path.join(OPENEIS_SRC_DIR, 'lib', 'openeis-ui'))
        if os.path.exists('build'):
            shutil.rmtree('build')
        ret = subprocess.check_call([r'{}\env\scripts\python.exe'.format(OPENEIS_SRC_DIR), 'setup.py', 'bdist_wheel'])

        for f in os.listdir('dist'):
            if f[-3:] == 'whl':
                move_wheel(f)

    finally:
        os.chdir(ORIG_CWD)


def move_to_working_dir():
    print("move_to_working_dir")
    tocopy=(CLEAN_PYTHON_DIR, WHEEL_DIR)
    try:
        setup_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  'setup.iss'))
        if os.path.exists(WORKING_DIR):
            shutil.rmtree(WORKING_DIR)
        os.makedirs(WORKING_DIR)
        os.chdir(WORKING_DIR)

        shutil.copytree(CLEAN_PYTHON_DIR, "python")
        shutil.copytree(WHEEL_DIR, "wheels")
        shutil.copytree(MISC_DIR, "misc")

        shutil.copy(setup_file, 'setup.iss')

        data = open('setup.iss').read()
        for x in ('WORKING_DIR',):
            data = data.replace('~~{}~~'.format(x), eval(x).replace('/', '\\'))

        with open('setup.iss', 'w') as f:
            f.write(data)

    finally:
        os.chdir(ORIG_CWD)


def make_installer():
    print("make_installer")
    os.chdir(WORKING_DIR)
    try:
        compiler = os.path.join(INNO_SETUP_DIR.replace('/','\\'), 'iscc.exe')
        ret = subprocess.check_call([compiler, 'setup.iss'])

        file_created = os.path.abspath(os.path.join('Output', 'setup.exe'))

        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        print("Moving file {} to {}".format(file_created, OUTPUT_FILE))
        shutil.move(file_created, OUTPUT_FILE)
    finally:
        os.chdir(ORIG_CWD)


def make_setup():
    print("Configuration for setup:")
    for x in ('CLEAN_PYTHON_DIR', 'WORKING_DIR', 'OPENEIS_SRC_DIR',
              'WHEEL_DIR', 'INNO_SETUP_DIR', 'MISC_DIR'):
        print("{}->{}".format(x, eval(x)))
    make_requirements()
    build_wheels()
    move_to_working_dir()
    make_installer()
    cleanup()


def rename_dirs(src_dir, working_dir):
    """Allow caller to change the source dir and working dir"""
    global cfg, OPENEIS_SRC_DIR, WORKING_DIR
    OPENEIS_SRC_DIR = cfg['OPENEIS_SRC_DIR'] = src_dir.replace('\\','/')
    WORKING_DIR = cfg['WORKING_DIR'] = working_dir.replace('\\','/')

    if not os.path.exists(OPENEIS_SRC_DIR):
        sys.stderr.write('invalid src dir {}\n'.format(OPENEIS_SRC_DIR))
        sys.exit(500)

    if not os.path.exists(WORKING_DIR):
        sys.stderr.write('invalid src dir {}\n'.format(WORKING_DIR))
        sys.exit(500)


def make_requirements():
    global MISC_DIR, WHEEL_DIR

    if not os.path.exists('env/Scripts/pip.exe'):
        raise Exception('must be called from root directory of the openeis project.')
    # wheelhouse = WHEEL_DIR.replace('/','\\')
    # We install wheel here so we can use it below.
    ret = subprocess.check_call([r'env\Scripts\pip.exe', 'install', 'wheel']) #{}\\wheel-0.24.0-py2.py3-none-any.whl'.format(wheelhouse)])
    print("Wheel installed: {}".format(ret))
    reqfile = MISC_DIR.replace('/','\\')+"\\requirements.txt"
    print("REQ FILE: "+reqfile)
    ret = subprocess.check_call([r'env\Scripts\pip.exe', 'freeze'], stdout=open(reqfile, 'w'))
    lines = ''
    for l in open(MISC_DIR.replace('/','\\')+"\\requirements.txt"):
        # Don't include libs that aren't in pypi.
        # We have included our numpy and scipy wheels in the repo.
        if not l.startswith("-e") and not l.startswith('openeis') and not \
                l.startswith('numpy') and not l.startswith('scipy'):
            lines += l

    open(MISC_DIR.replace('/','\\')+"\\requirements.txt", 'w').write(lines)
    cversion = '{}-{}-{}'.format(_vinfo['version'],
                                                  _vinfo['revision'],
                                                  _vinfo['vcs_version'])
    open(MISC_DIR.replace('/','\\')+"\\version.cfg", 'w').write(cversion)

    # now build all of the wheels for the requirements file
    ret = subprocess.check_call(['env\Scripts\pip.exe', 'wheel', '--wheel-dir='+WHEEL_DIR.replace('/','\\'), '-r', MISC_DIR.replace('/','\\')+'\\requirements.txt'])
    
    # TODO Do this better! so that this isn't hard coded!
    numpy_source = "{}\wheels\{}".format(OPENEIS_SETUP_SUPPORT_DIR, "numpy-1.11.3+mkl-cp34-cp34m-win_amd64.whl")
    scipy_source = "{}\wheels\{}".format(OPENEIS_SETUP_SUPPORT_DIR, "scipy-0.19.0-cp34-cp34m-win_amd64.whl")
    shutil.copy(numpy_source, WHEEL_DIR)
    shutil.copy(scipy_source, WHEEL_DIR)


def validate_and_setfolders(support_root, outdir):

    global cfg, OPENEIS_SRC_DIR, WORKING_DIR, MISC_DIR, LEGACY_WHEELS
    global INNO_SETUP_DIR, OUTPUT_FILE, TEMP_DIR, PRE_BUILT_WHEELS, WHEEL_DIR,CLEAN_PYTHON_DIR
    global OPENEIS_SETUP_SUPPORT_DIR

    outdir = os.path.abspath(outdir.replace('/', '\\'))
    print("Out directory is: "+outdir)
    support_root = os.path.abspath(support_root.replace('/', '\\'))
    
    OPENEIS_SETUP_SUPPORT_DIR = support_root

    WORKING_DIR = tempfile.mkdtemp()

    INNO_SETUP_DIR = os.path.join(support_root, 'extracted_inno_setup')
    MISC_DIR = os.path.join(support_root, 'misc')
    CLEAN_PYTHON_DIR = os.path.join(support_root, 'python-fresh')
    PRE_BUILT_WHEELS = os.path.join(support_root, 'pre-built-wheels')

    WORKING_DIR = os.path.join(TEMP_DIR, 'build')
    WHEEL_DIR = os.path.join(TEMP_DIR, 'wheels')

    if not os.path.exists(WHEEL_DIR):
        os.makedirs(WHEEL_DIR)

    if not os.path.exists(WORKING_DIR):
        os.makedirs(WORKING_DIR)

    if not os.path.exists(outdir):
        shutil.rmtree(outdir, ignore_errors=True)
        os.makedirs(outdir)

    OUTPUT_FILE = os.path.join(outdir, _VERSION_STRING)+'.exe'
    return True


def show_help():
    help = """
    python create_setup.py support_dir outdir

    support_dir    The directory wheere the support fiels from the
                   openeis-setup-support repository has ben cloned.

    outdir         The path to the output dir.  The command git describe
                   will be used to generate unique names.
"""
    sys.stdout.write(help)


if __name__ == '__main__':

    if len(sys.argv) != 3:
        sys.stderr.write('Invalid arguments!\n\n')
        show_help()
        sys.exit(500)

    TEMP_DIR = tempfile.mkdtemp()

    # checck and setup global variables.
    if not validate_and_setfolders(sys.argv[1], sys.argv[2]):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        sys.exit(500)



    #if os.path.isdir(WHEEL_DIR.replace('/','\\')):
    #    shutil.rmtree(WHEEL_DIR.replace('/','\\'))
    #os.makedirs(WHEEL_DIR.replace('/','\\'))
    make_setup()

    sys.stdout.write("clean up temp dir")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
