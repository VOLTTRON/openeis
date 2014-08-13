'''All tables which name starts with projects_ are dropped, except for
the two organization membership tables, unless --all-tables is given.
'''

from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.db import connection, transaction


class Command(NoArgsCommand):
    help = 'Remove orphaned dynamic application output tables.'
    option_list = NoArgsCommand.option_list + (
        make_option('-f', '--force', action='store_true', default=False,
                    help='Tables will not be dropped without this flag.'),
        make_option('-a', '--all-tables', action='store_true', default=False,
                    help='Drop all project tables.'),
    )

    def handle_noargs(self, *, verbosity=1, force=False, all_tables=False,
                      **options):
        verbosity = int(verbosity)
        if not force and verbosity >= 1:
            self.stdout.write('Tables will not be dropped; '
                             'use -f or --force to drop tables.')
        with transaction.atomic():
            cursor = connection.cursor()
            for table in cursor.db.introspection.get_table_list(cursor):
                if not table.startswith('projects_'):
                    continue
                if not all_tables:
                    if table[9:] in ['membership', 'organization']:
                        if verbosity >=2:
                            self.stdout.write('Leaving table: {}'.format(table))
                        continue
                if verbosity >= 2:
                    self.stdout.write('Dropping table: {}'.format(table))
                if force:
                    options = '' if cursor.db.vendor == 'sqlite' else 'CASCADE'
                    cursor.execute('DROP TABLE {} {}'.format(table, options))
