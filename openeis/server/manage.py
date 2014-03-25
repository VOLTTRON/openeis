import os
import sys

from django.core import management


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          __package__ + '.settings.desktop')
    sys.exit(management.execute_from_command_line())

if __name__ == '__main__':
    main()
