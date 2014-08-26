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

import os
import re
import sys

from django.core import management as core_management

from . import management


# find_commands() searches only for .py files which breaks frozen
# executables created by cx_Freeze. So we override the function as a fix.
#
# See the following links for more information:
#   https://code.djangoproject.com/ticket/23045
#   https://code.djangoproject.com/ticket/14952

def find_commands(management_dir):
    command_dir = os.path.join(management_dir, 'commands')
    regex = re.compile(r'^([^_].*)\.py[co]?$')
    try:
        return [match.group(1) for match in
                (regex.match(f) for f in os.listdir(command_dir)) if match]
    except OSError:
        return []
find_commands.__doc__ = core_management.find_commands.__doc__


# Command discovery is broken in Django when namespace packages are
# used, especially when PEP 420 namespace packages are used. Also,
# commands are only loaded for installed applications, not for the
# project. We overcome this by overriding the get_commands() function in
# django.core.management. Because get_commands() caches discovered
# commands, it is only necessary to override the first call.
#
# See https://code.djangoproject.com/ticket/14087,
#     https://code.djangoproject.com/ticket/20344, and
#     http://legacy.python.org/dev/peps/pep-0420/

_core_get_commands = core_management.get_commands
def _get_commands():
    commands = _core_get_commands()
    commands.update({name: __package__ for name in
                     find_commands(management.__path__[0])})
    core_management.get_commands = _core_get_commands
    return commands
core_management.get_commands = _get_commands


_core_find_management_module = core_management.find_management_module
def find_management_module(app_name):
    try:
        return _core_find_management_module(app_name)
    except ImportError as e:
        try:
            mod = __import__(app_name, fromlist=['management'])
            return mod.management.__path__[0]
        except (AttributeError, ImportError):
            raise e

# The following line to enables discovery of management commands in
# namespace packages. This has the side effect of loading each module
# during discovery which is avoided by the original function.
core_management.find_management_module = find_management_module


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', __package__ + '.settings')
    sys.exit(core_management.execute_from_command_line())

if __name__ == '__main__':
    main()
