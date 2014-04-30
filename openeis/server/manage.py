import os
import sys

from django.core import management as core_management

from . import management


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
                     core_management.find_commands(management.__path__[0])})
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
