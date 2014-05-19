import os
import socket
import subprocess
import sys

try:
    from django.contrib.staticfiles.management.commands.runserver import Command as RSCommand
except:
    from django.core.management.commands.runserver import Command as RSCommand

class Command(RSCommand):
    help = 'Updates UI package.\n' + RSCommand.help

    def handle(self, addrport='', *args, **options):
        # Handle multiple calls due to autoreload
        # See https://code.djangoproject.com/ticket/8085
        if not os.environ.get('RUN_MAIN', False):
            try:
                self.stdout.write('Attempting to update UI package...')
                socket.getaddrinfo('openeis-dev.pnl.gov', 80)
                subprocess.call([sys.executable, '-m', 'pip', 'install', '-U',
                    '-f', 'http://openeis-dev.pnl.gov/dist/openeis-ui/',
                    '--no-index', '--pre', 'openeis-ui'])
            except socket.gaierror:
                self.stdout.write('openeis-dev.pnl.gov:80 unreachable, '
                                  'skipping UI package update...')
        super(Command, self).handle(addrport, *args, **options)
