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
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

#}}}

'''
This command iterates through all directories and files in the 'projects'
directory found in the directory defined by settings.PROTECTED_MEDIA_ROOT.
Each numeric directory that is a child of the 'projects' directory is
tested against the Project model to determine if the project exists. If it
no longer exists, the entire directory tree is removed. Otherwise, each file
in the directory is tested for existence against the DataFile model and each
file with no corresponding database record is also removed.
'''

from optparse import make_option
import os
import posixpath
import shutil

from django.core.management.base import NoArgsCommand, CommandError

from openeis.projects.models import DataFile, Project
from openeis.projects.protectedmedia import ProtectedFileSystemStorage


class Command(NoArgsCommand):
    help = 'Remove files orphaned by deleting database files and/or projects.'
    option_list = NoArgsCommand.option_list + (
        make_option('-n', '--dry-run', action='store_true', default=False,
                    help='Do everything except modify the filesystem.'),
    )

    def handle_noargs(self, *, verbosity=1, dry_run=False, **options):
        verbosity = int(verbosity)

        def log(msg, level=2):
            '''Utility to write log message at appropriate log level.'''
            if verbosity >= level:
                self.stdout.write(msg)

        def failure(fn, path, excinfo):
            log('error: {}: {}'.format(os.strerror(excinfo[1].errno), path), 1)

        storage = ProtectedFileSystemStorage()
        try:
            dirs, _ = storage.listdir('projects')
        except FileNotFoundError:
            return
        for dirname in dirs:
            path = posixpath.join('projects', dirname)
            if not dirname.isdigit():
                log('Skipping directory: {}'.format(path))
            elif not Project.objects.filter(pk=dirname).exists():
                log('Removing directory: {}'.format(path), 2)
                if not dry_run:
                    shutil.rmtree(storage.path(path), onerror=failure)
            else:
                _, files = storage.listdir(posixpath.join('projects', dirname))
                for name in files:
                    name = posixpath.join(path, name)
                    if DataFile.objects.filter(file=name).exists():
                        log('Keeping file: {}'.format(name), 3)
                    else:
                        log('Removing file: {}'.format(name), 2)
                        if not dry_run:
                            storage.delete(name)
