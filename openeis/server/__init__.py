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


from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import SourceFileLoader, ModuleSpec
import os
import sys


__all__ = ['exec_parts']


def exec_parts(rcdir, globals=None, locals=None, include=None):
    '''Read each file in rcdir and exec the source code.
    
    May be used by a settings module to split settings among multiple
    files in a directory. Files are exec'd in lexical order. globals and
    locals are passed on to the exec() function. If include is given, it
    must be a function which accepts a name as the input and returns a
    boolean indicating whether the file of that name should be included.
    The default inclusion test checks that the name starts with to
    digits followed by a hyphen.
    '''
    if include is None:
        include = lambda name: name[:2].isdigit() and name[2:3] == '-'
    names = [name for name in os.listdir(rcdir) if include(name)]
    names.sort()
    for name in names:
        try:
            path = os.path.join(rcdir, name)
            with open(path) as file:
                source = file.read()
        except IsADirectoryError:
            continue
        exec(compile(source, path, 'exec'), globals, locals)


class ModuleLoader(Loader):
    '''Use the given module, or sensible default, for settings.

    Loads the given module and copies all public variables to the newly
    created module. If fullname is None, openeis.local.settings will be
    loaded, if it exists; otherwise openeis.server.settings will be
    used.
    '''

    def __init__(self, fullname=None):
        self.fullname = fullname

    def exec_module(self, module):
        if self.fullname:
            settings = __import__(self.fullname)
        else:
            try:
                settings = __import__('openeis.local.settings')
                self.fullname = 'openeis.local.settings'
            except ImportError:
                settings = __import__('openeis.server.settings')
                self.fullname = 'openeis.server.settings'
        for name in self.fullname.split('.')[1:]:
            settings = getattr(settings, name)
        try:
            names = settings.__all__
        except AttributeError:
            names = [n for n in dir(settings) if not n.startswith('_')]
        for name in names:
            setattr(module, name, getattr(settings, name))
        for name in ['__doc__', '__file__']:
            try:
                setattr(module, name, getattr(settings, name))
            except AttributeError:
                pass


class DirectoryLoader(Loader):
    '''Load settings from an runtime configuration directory.'''

    def __init__(self, path):
        self.path = path

    def exec_module(self, module):
        module.__path__ = [os.path.abspath(self.path)]
        exec_parts(self.path, module.__dict__, module.__dict__)


class FileLoader(SourceFileLoader):
    '''Load the module from a file and set its path.'''

    def exec_module(self, module):
        module.__file__ = os.path.abspath(self.path)
        try:
            super().exec_module(module)
        except OSError:
            raise ImportError("No module named 'openeis.settings'")
    

class SettingsFinder(MetaPathFinder):
    '''A finder for 'openeis.settings' pseudo-module.

    Allows one to use any Python file as the Django settings module
    rather than only a module available on the path.  If the
    OPENEIS_SETTINGS environment variable is defined, it will be used
    and interpreted as a filesystem path, if the name contains a path
    separator, or as a python module name otherwise. A path may be
    either a file or a directory. If a file, it will be loaded and used
    as the settings module. If a directory, it will be considered a
    rutime configuration directory and handled as described below.

    If OPENEIS_SETTINGS is not set, a search will be made for a
    settings.py file or a settings.d directory in the following
    subdirectories of the current user's home directory, in the given
    order:

        * .config/openeis
        * .openeis
        * _config/openeis (on Windows only)
        * _openeis (one Windows only)

    If the user's home directory cannot be determined, /etc/openeis will
    be searched. If settings.py and settings.d are not found, importing
    openeis.settings will fail.

    A runtime configuration directory holds a list of files that will be
    exec'd in order within the context of the openeis.settings module.
    Files must start with two digits followed by a hyphen to be
    included. Because they share the same global context, variables from
    earlier files may be used in subsequent files. The modules __path__
    variable will contain a single item that is the path to the
    directory.
    '''

    def find_spec(self, fullname, path, target=None):
        if fullname == 'openeis.settings':
            try:
                path = os.path.expanduser(os.path.expandvars(
                        os.environ['OPENEIS_SETTINGS']))
            except KeyError:
                pass
            else:
                if os.sep in path:
                    if os.path.isdir(path):
                        return ModuleSpec(fullname, DirectoryLoader(path))
                    return ModuleSpec(fullname, FileLoader(fullname, path))
                else:
                    return ModuleSpec(fullname, ModuleLoader(path))
            home = os.path.expanduser('~')
            if os.path.exists(home):
                paths = [os.path.join('.config', 'openeis'),
                         os.path.join('.openeis')]
                if os.path.__name__ != 'posixpath':
                    paths.expand([os.path.join(home, '_config', 'openeis'),
                                  os.path.join(home, '_openeis')])
            else:
                home = '/'
                paths = [os.path.join('etc', 'openeis')]
            for path in paths:
                settings = os.path.join(home, path, 'settings.py')
                if os.path.exists(settings):
                    return ModuleSpec(fullname, FileLoader(fullname, settings))
                rcdir = os.path.join(home, path, 'settings.d')
                if os.path.exists(rcdir):
                    return ModuleSpec(fullname, DirectoryLoader(rcdir))
            return ModuleSpec(fullname, ModuleLoader())


sys.meta_path.append(SettingsFinder())
