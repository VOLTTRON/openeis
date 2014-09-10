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

'''
distutils setup file for creating a cx_Freeze windows exe  

This file is meant to be used with version 5.0 of cx_Freeze which
at the time of writing was available only from source code.  See
documentation http://cx-freeze.readthedocs.org and source code 
https://bitbucket.org/anthony_tuininga/cx_freeze.

Author: Craig Allwardt

'''
from cx_Freeze import setup, Executable
import sys
import os

def get_files(root_path, rel_base):
    '''Returns list of tuples
    
    The first element in the tuples is the path to the file on disk.  The
    second element in the tuple is the path relative to the root in the
    archive/filesystem.
    '''
    
    file_paths = []
    for root, dirs, files in os.walk(root_path, topdown=False):
        for name in files:
            #print (name)
            file_paths.append((os.path.join(root, name), os.path.join(root, name)))
    return file_paths

#include_files = get_files(os.path.join('lib', 'openeis-ui', 'openeis', 'ui','static'))
include_files = get_files('data/static', 'data/static')
zip_includes = [
    (r'jsonschema\schemas\draft3.json',r'jsonschema\schemas\draft3.json'),
    (r'jsonschema\schemas\draft4.json',r'jsonschema\schemas\draft4.json'),
    ]
namespace_packages = ['openeis', 'django']
excludes = []
packages = [
    'openeis.server', 
    'openeis.projects', 
    'openeis.applications', 
    'openeis.ui', 
    'django',
    ]

build_exe_options = {
                     
   'namespace_packages': namespace_packages,
   'packages': packages,
   'include_files': include_files,
   'zip_includes': zip_includes
    }


########################################
# Here is a list of the Executable options
########################################

#"script":               #the name of the file containing the script which is to be frozen
#"initScript":           #the name of the initialization script that will be executed before the actual script is executed; this script is used to set up the environment for the executable; if a name is given without an absolute path the names of files in the initscripts subdirectory of the cx_Freeze package is searched
#"base":                 #the name of the base executable; if a name is given without an absolute path the names of files in the bases subdirectory of the cx_Freeze package is searched
#"path":                 #list of paths to search for modules
#"targetDir":            #the directory in which to place the target executable and any dependent files
#"targetName":           #the name of the target executable; the default value is the name of the script with the extension exchanged with the extension for the base executable
#"includes":             #list of names of modules to include
#"excludes":             #list of names of modules to exclude
#"packages":             #list of names of packages to include, including all of the package's submodules
#"replacePaths":         #Modify filenames attached to code objects, which appear in tracebacks. Pass a list of 2-tuples containing paths to search for and corresponding replacement values. A search for '*' will match the directory containing the entire package, leaving just the relative path to the module.
#"compress":             #boolean value indicating if the module bytecode should be compressed or not
#"copyDependentFiles":   #boolean value indicating if dependent files should be copied to the target directory or not
#"appendScriptToExe":    #boolean value indicating if the script module should be appended to the executable itself
#"appendScriptToLibrary":#boolean value indicating if the script module should be appended to the shared library zipfile
#"icon":                 #name of icon which should be included in the executable itself on Windows or placed in the target directory for other platforms
#"namespacePackages":    #list of packages to be treated as namespace packages (path is extended using pkgutil)
#"shortcutName":         #the name to give a shortcut for the executable when included in an MSI package
#"shortcutDir":          #the directory in which to place the shortcut when being installed by an MSI package; see the MSI Shortcut table documentation for more information on what values can be placed here.

executables = [
    #Executable('openeis-personal.py'),
    Executable('serve.py')
]

setup(
    name = 'openeis',
    version = '0.1',
    description = 'Open Energy Information System (OpenEIS) server.',
    author = 'Bora Akyol',
    author_email = 'bora@pnnl.gov',
    url = 'http://www.pnnl.gov',
    executables = executables,
    options = {"build_exe": build_exe_options},
)

