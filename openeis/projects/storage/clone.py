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
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

#}}}

from openeis.projects import models


def clone_project(project, new_project_name):
    ''' Clones project. Copies existing project and save with new name. 
        Copies sensor map, sensor ingest, sensors and analyses from existing project to cloned project.
    '''
    sensor_maps = models.SensorMapDefinition.objects.filter(project=project)
    #data_files = models.DataFile.objects.filter(project=project)
    
    project.id = None
    project.name = new_project_name
    project.save()
    
    #clone_data_files(list(data_files), project)
    clone_sensor_map_definition(list(sensor_maps), project)
        
    return project

def clone_data_files(data_files_list, project):
    for data_file in data_files_list:
        data_file.id = None
        data_file.save()

def clone_sensor_map_definition(sensor_maps_list,project):
    for sensor_map in sensor_maps_list:
        
        sensor_ingests = models.SensorIngest.objects.filter(map=sensor_map)
        sensors = models.Sensor.objects.filter(map=sensor_map)
        
        sensor_map.id = None
        sensor_map.project = project
        sensor_map.save()
        
        clone_sensor_ingest(list(sensor_ingests),sensor_map)
        clone_sensors(list(sensors), sensor_map)

def clone_sensor_ingest(sensor_ingests_list, sensor_map_definition):
    for sensor_ingest in sensor_ingests_list:
        
        analyses = models.Analysis.objects.filter(dataset=sensor_ingest)
        
        sensor_ingest.id = None
        sensor_ingest.map = sensor_map_definition
        sensor_ingest.save()
        
        clone_analysis(list(analyses), sensor_ingest)
        
def clone_sensors(sensors_list, sensor_map):
    for sensor in sensors_list:
        sensor.id= None
        sensor.map = sensor_map
        sensor.save()

def clone_analysis(analyses_list, sensor_ingest):
    for analysis in analyses_list:
        analysis.id= None
        analysis.dataset = sensor_ingest
        analysis.save()