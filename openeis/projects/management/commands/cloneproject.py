from django.core.management.base import BaseCommand, CommandError
from openeis.projects import models
from openeis.projects.storage import clone


class Command(BaseCommand):
    help = 'Run an application from the command-line.'

    def handle(self, *args, verbosity=1, dry_run=False, **options):
        
        project_id = int(args[0])
        new_project_name = args[1]
        
        project = models.Project.objects.get(id=project_id)
        
        clone.clone_project(project, new_project_name)