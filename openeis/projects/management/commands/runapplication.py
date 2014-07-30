from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from openeis.projects.storage.db_output import DatabaseOutputFile
from openeis.projects.storage.db_input import DatabaseInput

from openeis.applications import get_algorithm_class

from configparser import ConfigParser


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

        config = ConfigParser()

        config.read(args[0])

        application = config['global_settings']['application']
        klass = get_algorithm_class(application)

        dataset_ids = None
        if config.has_option('global_settings', 'dataset_id'):
            dataset_id_string = config['global_settings']['dataset_id']
            dataset_ids = [int(x) for x in dataset_id_string.split(',')]

        sensormap_id = int(config['global_settings']['sensormap_id'])
        topic_map = {}

        inputs = config['inputs']
        for group, topics in inputs.items():
            topic_map[group] = topics.split()


        db_input = DatabaseInput(sensormap_id, topic_map, dataset_ids=dataset_ids)

        output_format = klass.output_format(db_input)
        file_output = DatabaseOutputFile(application, output_format)

        kwargs = {}
        if config.has_section('application_config'):
            for arg, str_val in config['application_config'].items():
                kwargs[arg] = eval(str_val)

        if( verbosity > 1 ):
            print('Running application:', application)
            print('- Sensor map id:', sensormap_id)
            if dataset_ids is not None:
                print('- Data set ids:', dataset_ids)
            print('- Topic map:', topic_map)
            print('- Output format:', output_format)

        app = klass(db_input, file_output, **kwargs)
        app.run_application()

        reports = klass.reports(output_format)

        for report in reports:
            print(report)

