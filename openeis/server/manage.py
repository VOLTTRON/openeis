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
