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

'''
Created on Apr 28, 2014

- assumes that each algo run would create a new table with a unique id
'''

import logging
import io
import os
import json
from .. import models
from . import sensorstore
from collections import defaultdict
from zipfile import ZipFile
import shutil
import tempfile
import csv
from datetime import datetime
from openeis.server.settings import DATA_DIR

BATCH_SIZE = 1000
LOG_TABLE_NAME = 'log'

class DatabaseOutput:

    def __init__(self, analysis, output_map):
        '''
        analysis - Analysis model instance to associate output to
        Expected output_map:
           {
               'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')},
               'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'),
                          'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                          'SomeString':OutputDescriptor('string', 'some_output/string)}
           }
        '''
        self.analysis_id = analysis.id
        self.table_map = {}

        self.batch_store = defaultdict(list)

        for table_name, table_description in output_map.items():
            fields = {col_name: descriptor.output_type
                      for col_name, descriptor
                      in table_description.items()}
            app_output = models.AppOutput.objects.create(analysis=analysis,
                                                         name=table_name,
                                                         fields=fields)
            model_klass = sensorstore.get_data_model(app_output,
                                                     analysis.dataset.map.project.id,
                                                     fields)

            self.table_map[table_name] = model_klass

        #create the logging table
        logging_fields = {'msg':'string', 'level':'integer', 'datetime':'datetime'}
        log_output = models.AppOutput.objects.create(analysis=analysis,
                                                     name=LOG_TABLE_NAME,
                                                     fields=logging_fields)
        log_klass = sensorstore.get_data_model(log_output,
                                               analysis.dataset.map.project.id,
                                               logging_fields)

        self.table_map[LOG_TABLE_NAME] = log_klass

        self.log_level = logging.ERROR
        if analysis.debug:
            self.log_level = logging.DEBUG


    def insert_row(self,table_name,row_data):
        #Dictionary of name and values based on the outputschema of the application
        klass = self.table_map[table_name]
        instance = klass(**row_data)
        self.batch_store[table_name].append(instance)

        if len(self.batch_store[table_name]) >= BATCH_SIZE:
            klass.objects.bulk_create(self.batch_store[table_name])
            self.batch_store[table_name] = []

    def log(self, msg, level=logging.DEBUG, timestamp=None):
        if level >= self.log_level:
            logging_fields = {'msg':msg, 'level':level, 'datetime':timestamp}
            self.insert_row(LOG_TABLE_NAME, logging_fields)

    def close(self):
        for table_name, batch_list in self.batch_store.items():
            if batch_list:
                klass = batch_list[0].__class__
                klass.objects.bulk_create(batch_list)
                self.batch_store[table_name] = []


class DatabaseOutputFile(DatabaseOutput):
    def __init__(self, analysis, output_map):
        '''
        analysis - Analysis model instance to associate output to
        Expected output_map:
           {
               'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')},
               'Sensor': {'SomeValue':OutputDescriptor('int', 'some_output/value'),
                          'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                          'SomeString':OutputDescriptor('string', 'some_output/string)}
           }
        '''
        super().__init__(analysis, output_map)

        self.output_names = {}
        for table_name, table_description in output_map.items():
            self.output_names[table_name] = table_description.keys()

        self.file_prefix = analysis.application+'_'+datetime.now().strftime('%m-%d-%Y %H %M %S')

        log_file = self.file_prefix + '.log'
        self._logger = logging.getLogger()
        formatter = logging.Formatter('%(levelname)s:%(name)s %(message)s')
        self._logger.setLevel(logging.INFO)

        str_handler = logging.StreamHandler()
        str_handler.setLevel(logging.ERROR)
        str_handler.setFormatter(formatter)
        self._logger.addHandler(str_handler)

        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setFormatter(formatter)
        self._logger.addHandler(self.file_handler)

        self.csv_table_map = {}
        self.file_table_map = {}
        for table_name, topics in output_map.items():
            csv_file = self.file_prefix+'_'+table_name+'.csv'
            f = open(csv_file,'w', newline='')
            self.csv_table_map[table_name] = csv.DictWriter(f, topics.keys())
            self.csv_table_map[table_name].writeheader()
            self.file_table_map[table_name] = f



#     def insert_row(self,table_name,row_data):
#         #Dictionary of name and values based on the outputschema of the application
#         self.table_map[table_name].writerow(row_data)


    def log(self, msg, level=logging.DEBUG, timestamp=None):
        super().log(msg, level=level, timestamp=timestamp)

        if timestamp is not None:
            self._logger.log(level, '{time} - {msg}'.format(time=timestamp.strftime('%m/%d/%Y %H:%M:%S'),msg=msg))
        else:
            self._logger.log(level, 'NO TIME GIVEN - {msg}'.format(msg=msg))

    def close(self):
        super().close()
        print('Writing CSV files.')
        for table_name, fields in self.output_names.items():
            klass = self.table_map[table_name]
            dict_writer =  self.csv_table_map[table_name]
            for k in klass.objects.all():
                row_data = dict((field, getattr(k, field)) for field in fields)
                dict_writer.writerow(row_data)
            fd = self.file_table_map[table_name]
            fd.close()
        
        self._logger.removeHandler(self.file_handler)
        self.file_handler.close()
        
class DatabaseOutputZip(DatabaseOutputFile):
    def __init__(self, analysis, output_map, config_dict):

        super().__init__(analysis, output_map)
        self.config_dict = config_dict

    def log(self, msg, level=logging.DEBUG, timestamp=None):
        super().log(msg, level=level, timestamp=timestamp)

    def close(self):
        super().close()
        print('Writing Debug zip file.')
        
        analysis_folder = '/'.join((DATA_DIR, 'files','analysis'))
        if os.path.exists(analysis_folder) == False:
            os.mkdir(analysis_folder)

        zip_file = analysis_folder+'/'+str(self.analysis_id)+'.zip'
        with ZipFile(zip_file, 'w') as myzip:

            
            for table_name in self.csv_table_map:
                csv_file = self.file_prefix +'_'+table_name+'.csv'
                print(os.path.abspath(csv_file))
                myzip.write(csv_file)
                os.remove(csv_file)
            
            log_file = self.file_prefix+".log"
            myzip.write(log_file)
            os.remove(log_file)

            d = (self.config_dict)
            jsonarray = json.dumps(d)
            config_file = self.file_prefix+'.json'
            myzip.writestr(config_file,jsonarray)

            


if __name__ == '__main__':

    from openeis.applications import OutputDescriptor

    topic_map = {'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')}, }
    output  = DatabaseOutputFile('test_algo', topic_map)

    row_data = {'Timestamp': datetime(2000,1,1,8,0,0),
                'OAT': 52.3}
    output.insert_row('OAT', row_data)

    output.log('test message', logging.ERROR, datetime.now())

