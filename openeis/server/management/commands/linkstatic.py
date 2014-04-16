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
