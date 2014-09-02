''' Automation file for building openeis installer for distribution.

    
'''
import json
import os
import posixpath
import shutil
import subprocess
import sys

basedir = os.path.abspath(os.path.dirname(__file__))
setup_cfg = os.path.join(basedir, 'setup.cfg.json')
if not os.path.exists(setup_cfg):
    sys.stderr.write('Invalid config file specified\n\t{}'.format(setup_cfg))
    sys.exit()

cfg = json.loads(open(setup_cfg, 'r').read())
    

# This is the python (extracted from the msi file)
# that should be distributed with openeis.
CLEAN_PYTHON_DIR = cfg['CLEAN_PYTHON_DIR']

# A writeable directory for full installation
# of support files.
WORKING_DIR = cfg['WORKING_DIR']

# The checked out src directory from the git repository.
OPENEIS_SRC_DIR = cfg['OPENEIS_SRC_DIR']

# The location of the cache wheel directory so we
# don't need to re download things from the internet.
WHEEL_DIR = cfg['WHEEL_DIR']

# A folder that contains a numpy and numpy dist egg info file.
# This folder needs to be suitable for droping directly into
# the site-packages directory of the python distributed by
# openeis
NUMPY_DIR= cfg['NUMPY_DIR']

# Misc directory that will get copied to the root directory
# of the installed application when installing on the client
# machine.
MISC_DIR = cfg['MISC_DIR']

# The directory of an extracted inno setup folder.  This can
# be obtained through innoextractor program from the internet.
INNO_SETUP_DIR = cfg['INNO_SETUP_DIR']

ORIG_CWD = os.getcwd()

def move_wheel(src_file):
    '''Move the src_file wheel from the current directories dist dir to wheeldir

    Requires that the cwd is in the same location as it was during the creation
    of the wheel.
'''
    if os.path.exists(os.path.join(WHEEL_DIR, src_file)):
        os.remove(os.path.join(WHEEL_DIR, src_file))
    shutil.move(os.path.join('dist', src_file),
                             os.path.join(WHEEL_DIR, src_file))

def build_wheels():
    '''Builds the openeis and openeis-ui wheels, puts them in WHEEL_DIR

    This assumes that the executing python has bee activated with
    a bootstrapped python.
'''
    try:
        os.chdir(os.path.join(OPENEIS_SRC_DIR))
        if os.path.exists('build'):
            shutil.rmtree('build')
        
        print('Executing wheel on openeis')
        ret = subprocess.check_call(['python', 'setup.py', 'bdist_wheel'])
        
        for f in os.listdir('dist'):
            if f[-3:] == 'whl':
                move_wheel(f)
                
        
        os.chdir(os.path.join(OPENEIS_SRC_DIR, 'lib', 'openeis-ui'))
        if os.path.exists('build'):
            shutil.rmtree('build')
        ret = subprocess.check_call(['python', 'setup.py', 'bdist_wheel'])
        
        for f in os.listdir('dist'):
            if f[-3:] == 'whl':
                move_wheel(f)
        
    finally:
        os.chdir(ORIG_CWD)

def move_to_working_dir():
    tocopy=(CLEAN_PYTHON_DIR, NUMPY_DIR, WHEEL_DIR)
    try:
        if os.path.exists(WORKING_DIR):
            shutil.rmtree(WORKING_DIR)
        os.makedirs(WORKING_DIR)
        os.chdir(WORKING_DIR)

        
        shutil.copytree(CLEAN_PYTHON_DIR, "python")
        shutil.copytree(NUMPY_DIR, "numpy")
        shutil.copytree(WHEEL_DIR, "wheels")
        shutil.copytree(MISC_DIR, "misc")

        setup_file = os.path.join(OPENEIS_SRC_DIR, 'dist','openeis-support',
                                  'windows-setup-support', 'setup.iss')
        shutil.copy(setup_file, 'setup.iss')

        data = open('setup.iss').read()
        for x in ('WORKING_DIR',):
            data = data.replace('~~{}~~'.format(x), cfg[x].replace('/', '\\'))

        with open('setup.iss', 'w') as f:
            f.write(data)
        
    finally:
        os.chdir(ORIG_CWD)


def make_installer():
    os.chdir(WORKING_DIR)
    try:
        compiler = os.path.join(INNO_SETUP_DIR.replace('/','\\'), 'iscc.exe')
                                                       
        ret = subprocess.check_call([compiler, 'setup.iss'])
    finally:
        os.chdir(ORIG_CWD)
        
def make_setup():
    print("Configuration for setup:")
    for x in ('CLEAN_PYTHON_DIR', 'WORKING_DIR', 'OPENEIS_SRC_DIR', 
              'WHEEL_DIR', 'NUMPY_DIR', 'INNO_SETUP_DIR', 'MISC_DIR'):
        print("{}->{}".format(x, cfg[x]))
    build_wheels()
    move_to_working_dir()
    make_installer()

def rename_dirs(src_dir, working_dir):
    '''Allow caller to change the source dir and working dir'''
    global cfg, OPENEIS_SRC_DIR, WORKING_DIR
    OPENEIS_SRC_DIR = cfg['OPENEIS_SRC_DIR'] = src_dir.replace('\\','/')
    WORKING_DIR = cfg['WORKING_DIR'] = working_dir.replace('\\','/')
    
    if not os.path.exists(OPENEIS_SRC_DIR):
        sys.stderr.write('invalid src dir {}\n'.format(OPENEIS_SRC_DIR))
        sys.exit(500)

    if not os.path.exists(WORKING_DIR):
        sys.stderr.write('invalid src dir {}\n'.format(WORKING_DIR))
        sys.exit(500)
    

if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        # Change the source dir
        rename_dirs(sys.argv[1], sys.argv[2])
    
    make_setup()
               
