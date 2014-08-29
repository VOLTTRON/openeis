''' Automation file for building openeis installer for distribution.

    
'''
import json
import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))
setup_cfg = os.path.join(basedir, 'setup.cfg.json')
if not os.path.exits(setup_cfg):
    sys.stderr.write('Invalid config file specified\n\t{}'.format(setup_cfg))
    sys.exit()

cfg = json.loads(open(setup_cfg, 'r'))
    

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
WHEEL_DIR = cfg['WHEEL_DIRWHEEL_DIR']

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

def build_wheels():
    '''Builds the openeis and openeis-ui wheels, puts them in WHEEL_DIR

    This assumes that the executing python has bee activated with
    a bootstrapped python.
'''
    
    
    
    pass

def make_setup():
    pass

if __name__ == '__main__':
    make_setup()
               
