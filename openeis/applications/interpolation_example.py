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

from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor, Descriptor
from openeis.projects.storage.db_output import DatabaseOutputFile
import logging
import datetime
from datetime import timedelta
from pytz import timezone
import django.db.models as django
from django.db.models import Max, Min,Avg,Sum,StdDev, Variance
from django.db import models
from dateutil.relativedelta import relativedelta
from openeis.applications import reports
import dateutil
from django.db.models.aggregates import StdDev
from builtins import print
from openeis.projects.storage import db_output



class Application(DriverApplicationBaseClass):

    def __init__(self,*args,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {

                }
    
    @classmethod
    def get_self_descriptor(cls):
        name = 'interpolation_example'
        desc = 'interpolation_example'
        return Descriptor(name=name, description=desc)


    @classmethod
    def required_input(cls):
        #Called by UI
        return {
                    'oat':InputDescriptor('OutdoorAirTemperature','Outdoor Temp', count_min=1,count_max=10),
                    'load':InputDescriptor('WholeBuildingPower','Building Load'),
                }

    @classmethod
    def output_format(cls, input_object):
        #Called when app is staged
        topics = input_object.get_topics()
        oats = topics['oat']

        output_needs =  {'Time_Table':
                            {'time':OutputDescriptor('string', 'site/building/analysis/date'),
                             'load':OutputDescriptor('float', 'site/building/analysis/load')}}
        for count, oat in enumerate(oats):
            name = "oat" + str(count)
            output_needs['Time_Table'][name] = OutputDescriptor('float', 'site/building/analysis/{}'.format(name))

        return output_needs

    @classmethod
    def reports(cls, output_object):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table


        display elements is a list of display objects specifying viz and columns for that viz
        """
        rep_desc = 'Data Interpolation Example'

        report = reports.Report(rep_desc)

        column_info = (('time', 'Timestamp'), ('load', 'Load'))

        keys = list(output_object['Time_Table'].keys())
        keys.sort()

        column_info += tuple((key,key) for key in keys if key.startswith('oat'))

        text_blurb = reports.TextBlurb('')
        summary_table = reports.Table('Time_Table',
                                      column_info,
                                      title='Data Interpolation Results',
                                      description='A table showing data interpolation')


        report.add_element(summary_table)

        # list of report objects

        report_list = [report]

        return report_list

    def execute(self):
        self.out.log("Starting analysis", logging.INFO)

        load = self.inp.get_query_sets('load',wrap_for_merge=True)
        oat = self.inp.get_query_sets('oat',wrap_for_merge=True)

        data = self.inp.merge_fill_in_data(load,oat)

        for row in data:
            ts = row['time']

            tz = timezone('America/Los_Angeles')
            print(tz)
#            ts = ts.astimezone(timezone('US/Pacific'))
            oats = row['oat']

            timestring = ts.strftime("%Y-%m-%d %H:%M")

            row_to_write = {"time": timestring, "load": row['load'][0]}

            count = 0
            for oat in oats:
                name = 'oat'+str(count)
                row_to_write[name] = oats[count]
                count += 1

#            for count, oat in oats:
#                name = 'oat'+str(count)
#                row_to_write[name] = oats[count]
            self.out.insert_row("Time_Table", row_to_write)

