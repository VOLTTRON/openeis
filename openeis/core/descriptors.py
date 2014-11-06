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

from abc import abstractmethod, ABCMeta

class Descriptor:
    def __init__(self,
                 name,
                 description=''):
        self.name = name
        self.description = description

class ConfigDescriptor:
    ''''''
    def __init__(self,
                 config_type,
                 display_name,
                 description='',
                 optional=False,
                 value_default=None,
                 value_min=None,
                 value_max=None,
                 value_list=None):
        # TODO: Throw exception on invalid values
        self.config_type = config_type
        self.display_name = display_name
        self.optional = optional
        self.value_default = value_default
        self.value_min = value_min
        self.value_max = value_max
        self.value_list = value_list
        self.description = description
        
class InputDescriptor:
    
    def __init__(self,
                 sensor_type,
                 display_name,
                 description='',
                 count_min=1,
                 count_max=1,
                 _id=None):
        # TODO: Throw exception on invalid values
        self.sensor_type = sensor_type
        self.display_name = display_name
        self.count_min = count_min
        self.count_max = count_max
        self.description = description

class OutputDescriptor:

    def __init__(self,
                 output_type,
                 topic):
        #TODO: check and throw exception if self.sensor_data is none
        #self.output_type = sensordata.get(sensor_type)
        self.output_type = output_type
        self.topic = topic
        
class ConfigDescriptorBaseClass(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def get_config_parameters(cls):
        """default config schema description used by the UI to get user input
            which will be passed into the application or filter (or whatever)
            Default values are used to prepopulate the UI, not to pass into the app by default

            See ConfigDescriptor for all arguments.
            {
                'Key1':ConfigDescriptor(Type1,Description1),
                'Key2':ConfigDescriptor(Type2,Description2)
            }

            e.g.:
            {
                "building_sq_ft": ConfigDescriptor(float, "Square footage"),
                "building_year_constructed": ConfigDescriptor(int, "Consruction Year"),
                "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }
        """
        
class SelfDescriptorBaseClass(metaclass=ABCMeta):        
    @classmethod
    @abstractmethod
    def get_self_descriptor(cls):
        """
            Returns Descriptor instance with application or filter name and description.
            e.g.:
            name = 'This is application name'
            desc = 'This is what applications does'
            return Descriptor(name=name, description=desc)
        """