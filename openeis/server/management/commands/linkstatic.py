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

from optparse import make_option
import os

from django.core.management.base import NoArgsCommand, CommandError
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage


class Command(NoArgsCommand):
    help = 'Link project and application static directories to static root.'
    requires_model_validation = False
    option_list = NoArgsCommand.option_list + (
        make_option('-n', '--dry-run', action='store_true', default=False,
                    help='Do everything except modify the filesystem.'),
        make_option('-c', '--clear', action='store_true', default=False,
                    help='Clear the existing file using the storage '
                         'before trying to link the original file.'),
        make_option('--relative-depth', type='int', default=5,
                    help='Set maximum backup depth for making links relative; '
                         '0 forces absolute, -1 forces relative'),
        make_option('--static-root', default=None,
                    help='Override settings.STATIC_ROOT'),
    )

    def handle_noargs(self, verbosity=1, relative_depth=5, clear=False,
                      dry_run=False, static_root=None, **options):
        verbosity = int(verbosity)
        static_root = os.path.realpath(
                static_root if static_root else staticfiles_storage.path(''))

        def log(msg, level=2):
            '''Utility to write log message at appropriate log level.'''
            if verbosity >= level:
                self.stdout.write(msg)

        def make_path(path, start):
            '''Build a relative or absolute path.

            If relative_depth < 0, always return a relative path. If the
            number of .. components at the head of the relative path is
            greater than relative_depth or relative_depth evaluates to
            False (== 0), return path unchanged.  Otherwise, return a
            relative path. The arguments are the same as for
            os.path.relpath.
            '''
            if not relative_depth:
                return path
            rel_path = os.path.relpath(path, start)
            if relative_depth < 0:
                return rel_path
            count = 0
            for name in rel_path.split(os.sep, relative_depth + 1):
                if name != '..':
                    break
                count += 1
            return path if count > relative_depth else rel_path

        def link(names, storage, dirs=False):
            '''Link each name from its storage to the static root.

            names is a list of file or directory names, storage is
            the storage for the source file, and dirs indicates whether
            or not names are all directories (only important on Windows).
            '''
            if storage.prefix:
                dst_dir = os.path.join(static_root, storage.prefix)
                if not os.path.exists(dst_dir):
                    log('creating directory {}'.format(dst_dir))
                    if not dry_run:
                        os.mkdir(dst_dir)
            else:
                dst_dir = static_root
            for name in names:
                dst_path = os.path.join(dst_dir, name)
                if os.path.lexists(dst_path):
                    if clear:
                        log('removing {}'.format(dst_path))
                        if not dry_run:
                            os.unlink(dst_path)
                    else:
                        log('exists: {}'.format(dst_path), level=1)
                        continue
                src_path = make_path(storage.path(name),
                                     os.path.dirname(dst_path))
                log('linking {} to {}'.format(src_path, dst_path))
                if not dry_run:
                    os.symlink(src_path, dst_path, target_is_directory=dirs)

        # Iterate through all the static storage and link to static root.
        for finder in finders.get_finders():
            for storage in finder.storages.values():
                dirs, files = storage.listdir('')
                link(dirs, storage, True)
                link(files, storage, False)
