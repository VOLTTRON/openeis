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
# from numpy.f2py.__version__ import version_info

'''functions for determining package version information.

All available version information can be retrieved using get_version_info(),
which returns a dictionary containing the product and VCS version information.
This function hides underlying VCS exceptions and can be used without exception
handling.

product_version() returns the product version and also may be called without
exception handling. It currently just returns __version__.

have_vcs() returns a boolean indicating whether the package is under version
control and can be called without exception handling. It just checks for the
existence of a .git directory where the repository root should be.

All of the vcs_* functions call out to the version control executable, which is
currently expected to be git. These functions raise NotUnderVersionControl if
the .git directory was not found or VersionControlNotFound if the git
executable was not found. The subprocess module may raise CalledProcessError if
there was an error running a git command. These are not handled by this module.
The git command should be on the PATH or set in the GIT environment variable.
'''


from datetime import datetime
import os
import subprocess
from subprocess import CalledProcessError

import openeis


__all__ = ['NotUnderVersionControl', 'VersionControlNotFound',
           'CalledProcessError', 'have_vcs', 'product_version', 'vcs_revision',
           'vcs_version', 'vcs_timestamp', 'get_version_info']

__version__ = '2.5'


class NotUnderVersionControl(Exception):
    pass


class VersionControlNotFound(Exception):
    pass


def _vcs_path():
    '''Return the project base path if under VCS control, None otherwise.'''
    basedir = os.path.dirname(os.path.dirname(openeis.__file__))
    gitdir = os.path.join(basedir, '.git')
    return basedir if os.path.exists(gitdir) else None


def _git(*args):
    '''Wrapper to make git calls.'''
    vcsdir = _vcs_path()
    if vcsdir is not None:
        cmd = [os.environ.get('GIT', 'git')]
        cmd.extend(args)
        try:
            return subprocess.check_output(
                    cmd, cwd=vcsdir, stdin=subprocess.DEVNULL).decode('utf-8')
        except FileNotFoundError:
            raise VersionControlNotFound('The git executable was not found')
    raise NotUnderVersionControl('The project is not under version control')
        

def have_vcs():
    '''Return a boolean inidcating if projects is under VCS control.'''
    return _vcs_path is not None


def product_version():
    '''Return the product version.'''
    return __version__


def vcs_revision():
    '''Return the git revision number (count of commits).'''
    global _revision_count
    try: 
        return _revision_count
    except NameError:
        pass
    _revision_count = int(_git('rev-list', '--count', 'HEAD').strip())
    return _revision_count


def vcs_version():
    '''Return the shortened git hash for the current revision.'''
    global _revision_hash
    try: 
        return _revision_hash
    except NameError:
        pass
    _revision_hash = _git('rev-parse', '--short', 'HEAD').strip()
    return _revision_hash


def vcs_timestamp():
    '''Return timestamp of latest commit.'''
    
    global _revision_timestamp
    try:
        return _revision_timestamp
    except NameError:
        pass
    time = _git('log', '-n', '1', "--pretty=format:%ci").strip()
    _revision_timestamp = datetime.strptime(time, '%Y-%m-%d %H:%M:%S %z')
    return _revision_timestamp
    

def get_version_info():
    '''Return a dictionary containing version information.

    The dictionary contains the following

        'version': program version (from product_version())
        'vcs_version': VCS version unique identifier (from vcs_version())
        'updated': a datetime object containing the last commit time
                   (from vcs_timestamp())
        'revision': number of commits (from vcs_revision())
    
    Example:
        {
            "version": "1.2",
            "vcs_version": "1a2b3cd",
            "updated": datetime("2014-10-28T09:33:45.123Z"),
            "revision": 431
        }
    """
    '''
    
    global _version_info
    try:
        return _version_info
    except NameError:
        pass
    _version_info = {'version': product_version()}
    try:
        _version_info['vcs_version'] = vcs_version()
        _version_info['updated'] = vcs_timestamp()
        _version_info['revision'] = vcs_revision()
    except (NotUnderVersionControl, VersionControlNotFound):
        filepath = os.path.expanduser('~\\.openeis\\version.cfg')
        try:
            filehandle = open(filepath, 'r')
            versionstr = filehandle.read()
            versionparsed = versionstr.strip().split('-')
            if(len(versionparsed) == 3):
                _version_info['vcs_version'] = versionparsed[0]
                _version_info['updated'] = versionparsed[1]
                _version_info['revision'] = versionparsed[2]
        except (FileNotFoundError):
            versionstr = 'setup'
    return _version_info


if __name__ == '__main__':
    #print(vcs_version())
    #print(vcs_timestamp())
    #print(vcs_revision())
    print(get_version_info())
