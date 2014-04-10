from optparse import make_option
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from openeis.server.cleantemplate import clean_render


class Command(BaseCommand):
    args = '[OUTPUT_FILE]'
    help = 'Create nginx configuration file from project settings.'
    requires_model_validation = False
    option_list = BaseCommand.option_list + (
        make_option('--no-https', default=False, action='store_true',
                    help='Do not configure HTTPS.'),
        make_option('--http-port', default=80, type=int,
                    help='Use non-standard HTTP port.'),
        make_option('--https-port', default=443, type=int,
                    help='Use non-standard HTTPS port.'),
        make_option('-s', '--socket', default=None,
                    help='Specify path for uWSGI Unix domain socket.'),
        make_option('--worker-processes', default=None, type=int,
                    help='Set number of worker processes.'),
        make_option('--server-root', default=None,
                    help='Override server root'),
    )

    def handle(self, config_file=None, **options):
        options['settings'] = settings
        with clean_render():
            content = render_to_string('server/management/nginx.conf', options)
        file = open(config_file, 'w') if config_file else sys.stdout
        try:
            file.write(content)
        finally:
            if config_file:
                file.close()
