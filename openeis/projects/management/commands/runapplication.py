from optparse import make_option

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Run an application from the command-line.'

    # Add options here. See optparse documentation for help.
    option_list = BaseCommand.option_list + (
        make_option('-n', '--dry-run', action='store_true', default=False,
                    help="Don't make any permanent modifications."),
    )

    def handle(self, *args, verbosity=1, dry_run=False, **options):
        # Put of importing modules that access the database to allow
        # Django to magically install the plumbing first.
        from openeis.projects.storage import sensorstore

        verbosity = int(verbosity)

        def log(msg, level=2):
            '''Utility to write log message at appropriate log level.'''
            if verbosity >= level:
                self.stdout.write(msg)

        # Application running logic goes here.
        # args holds positional arguments from the command-line.
        # options are stored in options or keyword arguments.
        sensors = sensorstore.get_sensors(2, 'a/b/c')

