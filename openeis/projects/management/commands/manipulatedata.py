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

from django.core.management.base import BaseCommand, CommandError

from openeis.projects.storage.db_output import DatabaseOutputFile, DatabaseOutputZip
from openeis.projects.storage.db_input import DatabaseInput

from openeis.applications import get_algorithm_class
from openeis.projects import serializers

from datetime import datetime
from django.utils.timezone import utc

from configparser import ConfigParser, NoOptionError

import traceback

from pprint import pprint
from openeis.filters import apply_filters
import json
import sys


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

        def _iter_data(sensordata):
            for data in sensordata:
                yield data.time, data.value
                    
        try:
            verbosity = int(verbosity)

            config = ConfigParser()

            config.read(args[0])

            dataset_id = int(config['global_settings']['dataset_id'])
            sensoringest = models.SensorIngest.objects.get(pk=dataset_id)
            datamap = sensoringest.map
            sensors = list(datamap.sensors.all())
            sensor_names = [s.name for s in sensors]
            sensordata = [sensor.data.filter(ingest=sensoringest) for sensor in sensors]
            generators = {} 
            for name, qs in zip(sensor_names, sensordata):
                #TODO: Add data type from schema
                value = {"gen":_iter_data(qs),
                         "type":None}
                generators[name] = value
                
            config_string = config['global_settings']['config']
            print("Config String: ", config_string)
            config = json.loads(config_string)
            
            pprint(config)
            
            generators, errors = apply_filters(generators, config)
            
            if errors:
                print('Errors:')
                pprint(errors)
                sys.exit(1)
            
            datamap.id = None 
            datamap.name = datamap.name+' version - '+str(datetime.now())
            datamap.save()
            
            sensoringest.name = str(sensoringest.id) + ' - '+str(datetime.now())
            sensoringest.id = None
            sensoringest.map = datamap
            sensoringest.save()
            
            for sensor in sensors:
                sensor.id= None
                sensor.map = datamap
                sensor.save()
                data_class = sensor.data_class
                generator = generators[sensor.name]['gen']
                sensor_data_list = []
                for time,value in generator:
                    sensor_data = data_class(sensor=sensor, ingest=sensoringest,
                                             time=time, value=value)
                    sensor_data_list.append(sensor_data)
                    if len(sensor_data_list) >= 1000:
                        data_class.objects.bulk_create(sensor_data_list)
                        sensor_data_list = []
                if sensor_data_list:
                    data_class.objects.bulk_create(sensor_data_list)

        except Exception as e:
            # TODO: log errors
            print(traceback.format_exc())

            
    
