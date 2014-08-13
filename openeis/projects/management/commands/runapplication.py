from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from openeis.projects.storage.db_output import DatabaseOutputFile
from openeis.projects.storage.db_input import DatabaseInput

from openeis.applications import get_algorithm_class
from openeis.projects import serializers

from datetime import datetime
from django.utils.timezone import utc

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
        from openeis.projects import models
        
        
        
        try:
            verbosity = int(verbosity)
    
            config = ConfigParser()
    
            config.read(args[0])
    
            application = config['global_settings']['application']
            klass = get_algorithm_class(application)
    
            dataset_id = int(config['global_settings']['dataset_id'])
            dataset = models.SensorIngest.objects.get(pk=dataset_id)
    
            sensormap_id = int(config['global_settings']['sensormap_id'])
            
            now = datetime.utcnow().replace(tzinfo=utc)
            analysis = models.Analysis(added=now, started=now, status="running",
                                       application=application,
                                       dataset_id=sensormap_id)
            analysis.save()
            kwargs = {}
            if config.has_section('application_config'):
                for arg, str_val in config['application_config'].items():
                    kwargs[arg] = eval(str_val)
            
            topic_map = {}
    
            inputs = config['inputs']
            for group, topics in inputs.items():
                topic_map[group] = topics.split()
    
            now = datetime.utcnow().replace(tzinfo=utc)
            analysis = models.Analysis(added=now, started=now, status="running",
                                       dataset=dataset, application=application,
                                       configuration={'parameters': kwargs, 'inputs': topic_map},
                                       name='cli: {}, dataset {}'.format(application, dataset_id))
            analysis.save()
    
            db_input = DatabaseInput(dataset.map.id, topic_map, dataset_id)
    
            output_format = klass.output_format(db_input)
    
            file_output = DatabaseOutputFile(analysis, output_format)
    
            if( verbosity > 1 ):
                print('Running application:', application)
                if dataset_id is not None:
                    print('- Data set id:', dataset_id)
                print('- Topic map:', topic_map)
                print('- Output format:', output_format)
    
            app = klass(db_input, file_output, **kwargs)
            app.run_application()
    
            reports = klass.reports(output_format)
    
            for report in reports:
                print(report)
        
        except Exception as e:
            analysis.status = "error"
            # TODO: log errors
            print(e)
    
        finally:
            if analysis.status != "error":
                analysis.reports = [serializers.ReportSerializer(report).data for
                                    report in klass.reports(file_output)]
                analysis.status = "complete"
                analysis.progress_percent = 100
            analysis.ended = datetime.utcnow().replace(tzinfo=utc)
            analysis.save()
