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

'''A pseudo-module for advanced loading of OpenEIS settings.

Allows one to use any Python file as the Django settings module rather
than only a module available on the path.  If the OPENEIS_SETTINGS
environment variable is defined, it will be used and interpreted as a
filesystem path, if the name contains a path separator, or as a python
module name otherwise. A path may be either a file or a directory. If a
file, it will be loaded and used as the settings module. If a directory,
it will be considered a rutime configuration directory and handled as
described below.  If the path or module are not found, ImportError will
be raised

If OPENEIS_SETTINGS is not set, a search will be made for a settings.py
file or a settings.d directory in the following directories (in the
order given):

    * $PROJDIR/.openeis (only if using venv)
    * ~/.config/openeis
    * ~/.openeis
    * ~/_openeis (Windows only)
    * %LOCALAPPDATA%/OpenEIS (Windows only)
    * %APPDATA%/OpenEIS (Windows only)

Where $PROJDIR is the directory where the openeis source code is rooted.  It is
calculated as follows: os.path.join(os.path.dirname(__file__), '..', '..').  If
the user directory cannot be determined, /etc/openeis will be tried (except on
Windows). If settings.py and settings.d are not found, importing
openeis.server._settings will try to load openeis.local.settings and revert to
loading openeis.server.settings.

A runtime configuration directory holds a list of files that will be
exec'd in order within the context of the openeis.server._settings
module.  Files must start with two digits followed by a hyphen and end
with a .py extension to be included. Because they share the same global
context, variables from earlier files may be used in subsequent files.
The modules __path__ variable will contain a single item that is the
path to the directory.
'''


import importlib.machinery
import os
import sys


def _load_module(name, package=None):
    '''Copy public attributes from a module into the current namespace.'''
    assert name != __name__
    module = importlib.import_module(name, package)
    try:
        names = module.__all__
    except AttributeError:
        names = [n for n in dir(module) if not n.startswith('_')]
    names.extend(['__doc__', '__file__'])
    globals().update((name, value) for name, value in vars(module).items()
                     if name in names)
    globals()['_source_'] = 'module', module.__name__


def _load_file(path):
    '''Load a module from file into the current namespace.'''
    importlib.machinery.SourceFileLoader(
            __name__, path).exec_module(sys.modules[__name__])
    globals()['_source_'] = 'file', path


def _load_directory(dirname):
    '''Load modules from a directory into the current namespace.'''
    names = [name for name in os.listdir(dirname)
             if (name[:2].isdigit() and name[2:3] == '-' and
                 name[-3:].lower() == '.py')]
    names.sort()
    used = []
    for name in names:
        try:
            path = os.path.join(dirname, name)
            with open(path) as file:
                source = file.read()
        except IsADirectoryError:
            continue
        exec(compile(source, path, 'exec'), globals(), globals())
        used.append(name)
    globals()['_source_'] = 'directory', (os.path.abspath(dirname), used)


def _load():
    '''Do all the hard work and remove _load from the module.'''

    del globals()['_load']

    debug = print if __name__ == '__main__' else lambda *a: None

    try:
        path = os.path.expanduser(os.path.expandvars(
                os.environ['OPENEIS_SETTINGS']))
    except KeyError:
        debug('OPENEIS_SETTINGS is not set.')
    else:
        debug('OPENEIS_SETTINGS is set')
        if os.sep in path:
            if os.path.isdir(path):
                debug('loading settings from directory:', path)
                return _load_directory(path)
            debug('loading settings from file:', path)
            return _load_file(path)
        else:
            debug('loading settings from module:', path)
            return _load_module(path)
    paths = []
    if sys.prefix != sys.base_prefix:
        # executing in a virtual environment
        paths = [os.path.normpath(os.path.join(
                 os.path.dirname(__file__), '..', '..', '.openeis'))]
    home = os.path.expanduser('~')
    if not home or home == '/':
        if os.path.__name__ == 'posixpath':
            paths.append(os.path.join('/', 'etc', 'openeis'))
    elif os.path.exists(home):
        paths.extend([os.path.join(home, '.config', 'openeis'),
                      os.path.join(home, '.openeis')])
    if os.path.__name__ != 'posixpath':
        if os.path.exists(home):
            paths.append(os.path.join(home, '_openeis'))
        try:
            paths.append(os.path.join(os.environ['LOCALAPPDATA'], 'OpenEIS'))
        except KeyError:
            pass
        try:
            paths.append(os.path.join(os.environ['APPDATA'], 'OpenEIS'))
        except KeyError:
            pass
    debug('searching for settings in:', paths)
    for dirname in paths:
        path = os.path.join(dirname, 'settings.py')
        if os.path.exists(path):
            debug('loading settings from file:', path)
            return _load_file(path)
        path = os.path.join(dirname, 'settings.d')
        if os.path.exists(path):
            debug('loading settings from directory:', path)
            return _load_directory(path)
    try:
        debug('trying to load settings from module: openeis.local.settings')
        return _load_module('..local.settings', __package__)
    except ImportError:
        pass
    debug('loading default settings from module: openeis.server.settings')
    return _load_module('.settings', __package__)
_load()
