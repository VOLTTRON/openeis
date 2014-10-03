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

from openeis.projects import models
import json
from openeis.projects.storage import sensorstore

class CloneProject():
    
    def __init__(self):
        pass
    
    def clone_project(self,project, new_project_name):
        ''' Clones project. Copies existing project and save with new name.
            Copies data map, sensor ingest, sensors and analyses from existing project to cloned project.
        '''
        data_maps = models.DataMap.objects.filter(project=project)
        #data_files = models.DataFile.objects.filter(project=project)
        self.src_project_id = project.id
        project.id = None
        project.name = new_project_name
        project.save()
    
        #clone_data_files(list(data_files), project)
        self.clone_data_map_definition(list(data_maps), project)
    
        return project
    
    def clone_data_files(self, data_files_list, project):
        for data_file in data_files_list:
            data_file.id = None
            data_file.save()
    
    def clone_data_map_definition(self, data_maps_list,project):
        for data_map in data_maps_list:
    
            sensor_ingests = models.SensorIngest.objects.filter(map=data_map)
            sensors = models.Sensor.objects.filter(map=data_map)
    
            data_map.id = None
            data_map.project = project
            data_map.save()
    
            self.clone_sensor_ingest(list(sensor_ingests),data_map)
            self.clone_sensors(list(sensors), data_map)
    
    def clone_sensor_ingest(self, sensor_ingests_list, data_map_definition):
        for sensor_ingest in sensor_ingests_list:
    
            analyses = models.Analysis.objects.filter(dataset=sensor_ingest)
    
            sensor_ingest.id = None
            sensor_ingest.map = data_map_definition
            sensor_ingest.save()
    
            self.clone_analysis(list(analyses), sensor_ingest)
    
    def clone_sensors(self, sensors_list, data_map):
        for sensor in sensors_list:
            sensor.id= None
            sensor.map = data_map
            sensor.save()
    
    def clone_analysis(self, analyses_list, sensor_ingest):
        for analysis in analyses_list:
            app_output_list = models.AppOutput.objects.filter(analysis=analysis)
            analysis.id= None
            analysis.dataset = sensor_ingest
            analysis.save()
            self.clone_appOutput(app_output_list, analysis)
            
    def clone_appOutput(self, app_output_list, analysis):
        for app_output in app_output_list:
            model_klass = sensorstore.get_data_model(app_output,
                                                         self.src_project_id,
                                                         app_output.fields)
            query_set = model_klass.objects.all()
            app_output.id = None
            app_output.analysis = analysis
            app_output.save()
            
            self.clone_appOutputData(query_set, app_output)
            
    def clone_appOutputData(self, query_set, app_output):
        model_klass = sensorstore.get_data_model(app_output,
                                                         app_output.analysis.dataset.map.project.id,
                                                         app_output.fields)
        
        model_klass_instances = []
        for row in query_set:
            kwargs = dict((x,getattr(row,x)) for x in app_output.fields)
            instance = model_klass(**kwargs)          
            model_klass_instances.append(instance)
            #instance.save()
            #print(kwargs)
            
        model_klass.objects.bulk_create(model_klass_instances)
            
        
            
            
            
            
        
