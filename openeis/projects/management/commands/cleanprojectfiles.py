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
