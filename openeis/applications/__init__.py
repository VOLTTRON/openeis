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

from abc import ABCMeta,abstractmethod
#from schema.schema import sensordata
import logging
import pkgutil
from collections import defaultdict
from datetime import datetime

_applicationList = [name for _, name, _ in pkgutil.iter_modules(__path__)]

_applicationDict = {}


#make these available here so we don't have to fix all application just yet.
from openeis.core.descriptors import (OutputDescriptor,
                                      ConfigDescriptor,
                                      InputDescriptor,
                                      Descriptor,
                                      ConfigDescriptorBaseClass,
                                      SelfDescriptorBaseClass)

class DriverApplicationBaseClass(ConfigDescriptorBaseClass, 
                                 SelfDescriptorBaseClass,
                                 metaclass=ABCMeta):

    def __init__(self,inp=None,out=None,**kwargs):
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(**kwargs)
        self.inp = inp
        self.out = out

    def _pre_execute(self):
        pass

    def _post_execute(self):
        self.out.close()

    def run_application(self):
        try:
            self._pre_execute()
            self.execute()
        finally:
            self._post_execute()

    @classmethod
    @abstractmethod
    def required_input(cls):
        """
        Applications will override this method to return a dictionary specifying their
        data needs. This method will be called by the UI to do the mapping based on this.

        required input schema
                {
                    'key1':InputDescriptor1,
                    'key2':InputDescriptor2
                }
             e.g.:
                # OAT1 returns a list of 1 OAT
                # OAT2 returns a list of 3 OATs
                # CFP1 returns a list of minimum 3 and maximum all CFP1

                {
                    'OAT1':InputDescriptor('OutdoorAirTemperature','Hillside OAT'),
                    'OAT2':InputDescriptor('OutdoorAirTemperature','Roof OATs',count_min=3)
                    'CFP1':InputDescriptor('CondenserFanPower','CFP Desc',count_min=3,count_max=None)
                }
        """

    @classmethod
    @abstractmethod
    def output_format(cls, input_object):
        """
        The output object takes the resulting input object as a argument
         so that it may give correct topics to it's outputs if needed.

        output schema description
           {TableName1: {name1:OutputDescriptor1, name2:OutputDescriptor2,...},....}

           eg: {'OAT': {'Timestamp':OutputDescriptor('timestamp', 'foo/bar/timestamp'),'OAT':OutputDescriptor('OutdoorAirTemperature', 'foo/bar/oat')},
                'Sensor': {'SomeValue':OutputDescriptor('integer', 'some_output/value'),
                           'SomeOtherValue':OutputDescriptor('boolean', 'some_output/value),
                           'SomeString':OutputDescriptor('string', 'some_output/string)}}

        Should always call the parent class output_format and update the dictionary returned from
        the parent.

        result = super().output_format(input_object)
        my_output = {...}
        result.update(my_output)
        return result
        """
        return {}

    @abstractmethod
    def execute(self):
        """
        Called when user says Go! in the UI
        """
        "The algorithm to run."

    @classmethod
    @abstractmethod
    def reports(cls, output_obj):
        """describe output"""


class DrivenApplicationBaseClass(DriverApplicationBaseClass, metaclass=ABCMeta):

    def drop_partial_lines(self):
        """Specifies the merge strategy for driven application data.
        This is used as the drop_partial_lines argument for the
        DatabaseInput.merge call used to preprocess incoming data."""
        return False


    def execute(self):
        '''Iterate over input calling run each time'''
        query_list = []
        topic_map = self.inp.get_topics()

        for input_name in topic_map:
            query_list.append(self.inp.get_query_sets(input_name, wrap_for_merge=True))

        merged_input_gen = self.inp.merge(*query_list, drop_partial_lines=self.drop_partial_lines())

        time_stamp = datetime.min

        for merged_input in merged_input_gen:
            time_stamp = merged_input.pop('time')
            flat_input = self._flatten_input(merged_input)
            results = self.run(time_stamp, flat_input)

            if not self._process_results(time_stamp, results):
                break

        results = self.shutdown()
        self._process_results(time_stamp, results)


    def _process_results(self, time_stamp, results):
        '''
        Iterate over results and put values in command, log and any other table specified by results.
        Return False if application has terminated normally.
        '''
        for point, value in results.commands.items():
            row = {"timestamp":time_stamp,
                   "point": point,
                   "value": value}
            self.out.insert_row('commands', row)

        for level, msg in results.log_messages:
            self.out.log(msg, level, time_stamp)

        for table, rows in results.table_output.items():
            for row in rows:
                self.out.insert_row(table, row)

        if results._terminate:
            self.out.log('Terminated normally', logging.DEBUG, time_stamp)
            return False

        return True


    @staticmethod
    def _flatten_input(merged_input):
        '''
        flattens the input dictionary returned from self.inp.merge
        '''
        result={}
        key_template = '{table}&&&{n}'
        for table, value_list in merged_input.items():
            for n, value in enumerate(value_list, start=1):
                key = key_template.format(table=table, n=n)
                result[key] = value

        return result

    @classmethod
    def output_format(cls, input_object):
        '''
        Override this method to add output tables.

        Call super().output_format and update the dictionary returned from
        the parent.

        result = super().output_format(input_object)
        my_output = {...}
        result.update(my_output)
        return result
        '''
        results = super().output_format(input_object)
        command_table = {'commands': {'timestamp':OutputDescriptor('timestamp', 'commands/timestamp'),
                                      'point':OutputDescriptor('string', 'commands/point'),
                                      'value':OutputDescriptor('float', 'commands/value')}}
        results.update(command_table)
        return results

    @abstractmethod
    def run(self, time, inputs):
        '''Do work for each batch of timestamped inputs
           time- current time
           inputs - dict of point name -> value

           Must return a results object.'''
        pass

    def shutdown(self):
        '''Override this to add shutdown routines.'''
        return Results()

class Results:
    def __init__(self, terminate=False):
        self.commands = {}
        self.log_messages = []
        self._terminate = terminate
        self.table_output = defaultdict(list)

    def command(self, point, value):
        self.commands[point]=value

    def log(self, message, level=logging.DEBUG):
        self.log_messages.append((level, message))

    def terminate(self, terminate):
        self._terminate = bool(terminate)

    def insert_table_row(self, table, row):
        self.table_output[table].append(row)

for applicationName in _applicationList:
    try:
        absolute_app = '.'+applicationName
        module = __import__(applicationName, globals(), locals(), ['Application'], 1)
        klass = module.Application
    except Exception as e:
        logging.error('Module {name} cannot be imported. Reason: {ex}'.format(name=applicationName, ex=e))
        continue

    #Validation of Algorithm class

    if not issubclass(klass, DriverApplicationBaseClass):
        logging.warning('The implementation of {name} does not inherit from openeis.algorithm.DriverApplicationBaseClass.'.format(name=applicationName))

    _applicationDict[applicationName] = klass

#print(_applicationDict)


def get_algorithm_class(name):
    return _applicationDict.get(name)

