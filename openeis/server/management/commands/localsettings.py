from optparse import make_option
import os
import string
import random

from django.core.management.base import NoArgsCommand
from django.template.loader import render_to_string

from openeis.server.cleantemplate import clean_render


class Command(NoArgsCommand):
    help = 'Create openeis.local package with skeleton settings.'
    requires_model_validation = False
    option_list = NoArgsCommand.option_list + (
        make_option('--base-dir', default=None,
                    help='Install local settings package into given directory.'),
        make_option('--debug', action='store_true', default=False,
                    help='Set DEBUG variables to True'),
        make_option('-f', '--force', action='store_true', default=False,
                    help='Overrite existing module.'),
        make_option('--host', dest='hosts', action='append', default=[],
                    help='Append host to ALLOWED_HOSTS'),
        make_option('--no-https', action='store_true', default=False,
                    help='Disable HTTPS security settings.'),
        make_option('--server', default='generic', type='choice',
                    choices=('generic', 'apache', 'nginx'),
                    help='Server type: generic (default), apache, or nginx'),
    )

    def handle_noargs(self, base_dir=None, **options):
        if base_dir is None:
            base_dir = os.path.dirname(__file__)
            for i in range(__package__.count('.') + 1):
                base_dir = os.path.dirname(base_dir)
        mod_dir = os.path.join(base_dir, 'openeis', 'local')
        if not os.path.exists(mod_dir):
            os.makedirs(mod_dir)
        path = os.path.join(mod_dir, '__init__.py')
        if not os.path.exists(path):
            open(path, 'w').close()
        path = os.path.join(mod_dir, 'settings.py')
        if not os.path.exists(path) or options.get('force'):
            chars = ''.join(getattr(string, name) for name in
                            ['ascii_letters', 'digits', 'punctuation'])
            options['secret_key'] = repr(''.join(random.choice(chars)
                                                 for i in range(50)))
            options['pm_method'] = repr({'generic': 'direct',
                                         'apache': 'X-Sendfile',
                                         'nginx': 'X-Accel-Redirect'}
                                        [options['server']])
            with clean_render():
                content = render_to_string('server/management/settings.py', options)
            with open(path, 'w') as file:
                file.write(content)
        self.stdout.write("Edit `{}' to your liking.".format(path))
