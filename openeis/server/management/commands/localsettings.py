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
                    metavar='HOST', help='Append host to ALLOWED_HOSTS'),
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
