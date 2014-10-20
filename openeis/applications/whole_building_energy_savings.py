"""
Implement a building baseline load prediction model based on temperature and time-of-week (TTOW).
Calculates the <total/cumulative> savings from the difference between predicted
and measured energy use.

See Johanna L. Mathieu, Phillip N. Price, Sila Kiliccote, and Mary Ann Piette,
"Quantifying Changes in Building Electricity Use, with Application to Demand Response",
Lawrence Berkeley National Laboratory,
report LBNL-4944E
(April 2011)
http://escholarship.org/uc/item/6068k5nh


Copyright
=========

OpenEIS Algorithms Phase 2 Copyright (c) 2014,
The Regents of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the U.S.
Department of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov
referring to "OpenEIS Algorithms Phase 2 (LBNL Ref 2014-168)".

NOTICE:  This software was produced by The Regents of the University of
California under Contract No. DE-AC02-05CH11231 with the Department of Energy.
For 5 years from November 1, 2012, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, and perform
publicly and display publicly, by or on behalf of the Government. There is
provision for the possible extension of the term of this license. Subsequent to
that period or any extension granted, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, distribute copies
to the public, perform publicly and display publicly, and to permit others to
do so. The specific term of the license can be identified by inquiry made to
Lawrence Berkeley National Laboratory or DOE. Neither the United States nor the
United States Department of Energy, nor any of their employees, makes any
warranty, express or implied, or assumes any legal liability or responsibility
for the accuracy, completeness, or usefulness of any data, apparatus, product,
or process disclosed, or represents that its use would not infringe privately
owned rights.


License
=======

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
"""
# TODO: Make sure this is working!

from openeis.applications import DriverApplicationBaseClass, InputDescriptor, \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
import logging
import datetime as dt
from django.db.models import Avg
from openeis.applications.utils.baseline_models import day_time_temperature_model as ttow
from openeis.applications.utils import conversion_utils as cu



class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None,
                              baseline_startdate=None,
                              baseline_stopdate=None,
                              savings_startdate=None,
                              savings_stopdate=None,
                              **kwargs):
        # Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args, **kwargs)

        self.default_building_name_used = False

        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name
        self.baseline_start = dt.datetime.strptime(baseline_startdate, '%Y-%m-%d')
        self.baseline_stop = dt.datetime.strptime(baseline_stopdate, '%Y-%m-%d')
        self.savings_start = dt.datetime.strptime(savings_startdate, '%Y-%m-%d')
        self.savings_stop = dt.datetime.strptime(savings_stopdate, '%Y-%m-%d')

    @classmethod
    def get_config_parameters(cls):
        # Called by UI
        # load_query = self.inp.get_query_sets('load', group_by='day')
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True),
            "baseline_startdate": ConfigDescriptor(str, "Baseline Start Date (YYYY-MM-DD)", optional=False),
            "baseline_stopdate": ConfigDescriptor(str, "Baseline End Date (YYYY-MM-DD)", optional=False),
            "savings_startdate": ConfigDescriptor(str, "Savings Start Date (YYYY-MM-DD)", optional=False),
            "savings_stopdate": ConfigDescriptor(str, "Savings End Date (YYYY-MM-DD)", optional=False)
            }


    @classmethod
    def required_input(cls):
        # Called by UI
        # Sort out units.
        return {
            'oat':InputDescriptor('OutdoorAirTemperature', 'Outdoor Temperature'),
            'load':InputDescriptor('WholeBuildingElectricity', 'Building Load')
            }

    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output:
            datetimeValues: datetime objectes for each energy value.
            predictedValues: values returned after applying the day_time model
            measuredValues: values directly measured from the building
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]

        # TODO: Should names derived from "day time temperature model" be replaced, to
        # reflect the new branding of this application as "whole building energy savings"?
        time_values = '/'.join(output_topic_base + ['daytimetemperature', 'datetime'])
        predicted_values = '/'.join(output_topic_base + ['daytimetemperature', 'predicted'])
        measured_values  = '/'.join(output_topic_base + ['daytimetemperature', 'measured'])
        cusum_values  = '/'.join(output_topic_base + ['daytimetemperature', 'cusum'])

        output_needs = {
            'DayTimeTemperatureModel': {
                'datetimeValues': OutputDescriptor('datetime', time_values),
                'measured': OutputDescriptor('float', measured_values),
                'predicted': OutputDescriptor('float', predicted_values),
                'cumulativeSum' : OutputDescriptor('float', cusum_values)
                }
            }
        return output_needs


    @classmethod
    def reports(cls, output_object):
        # Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and columns
        for that viz
        """

        report = reports.Report('Whole-Building Energy Savings')

        text_blurb = reports.TextBlurb(text="Analysis shows the cumulative sum of the savings between the \
                                            baseline model and the measured values for a single building.")
        report.add_element(text_blurb)

        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('DayTimeTemperatureModel', 'datetimeValues', 'cumulativeSum'))
        cumsum_plot = reports.DatetimeScatterPlot(xy_dataset_list,
                                   title='Cumulative Whole Building Energy Savings',
                                   x_label='Timestamp',
                                   y_label='Energy [kWh]'
                                   )
        report.add_element(cumsum_plot)

        text_guide1= reports.TextBlurb(text="A flat slope of the cumulative sum time series indicates that use has\
                                             remained the same. A positive slope indicates energy savings, while a \
                                             negative slope indicates that more energy is being used after the \
                                             supposed \"improvement\" date")
        report.add_element(text_guide1)

        report_list = [report]

        return report_list

    def execute(self):
        # Called after User hits GO
        """
        Calculates weather sensitivity using Spearman rank.
        Also, outputs data points for energy signature scatter plot.
        """
        self.out.log("Starting Day Time Temperature Analysis", logging.INFO)

        # Gather loads and outside air temperatures. Reduced to an hourly average

        load_query = self.inp.get_query_sets('load', group_by='hour',
                                             group_by_aggregation=Avg,
                                             exclude={'value':None},
                                             wrap_for_merge=True)
        oat_query = self.inp.get_query_sets('oat', group_by='hour',
                                             group_by_aggregation=Avg,
                                             exclude={'value':None},
                                             wrap_for_merge=True)

        # Get conversion factor
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()
        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
        temperature_unit = meta_topics['oat'][base_topic['oat'][0]]['unit']

        load_convertfactor = cu.conversiontoKWH(load_unit)

        # Match the values by timestamp
        merged_load_oat = self.inp.merge(load_query, oat_query)

        load_values = []
        oat_values = []
        datetime_values = []

        for x in merged_load_oat:
            if temperature_unit == 'celcius':
                convertedTemp = cu.convertCelciusToFahrenheit(x['oat'][0])
            elif temperature_unit == 'kelvin':
                convertedTemp = cu.convertKelvinToCelcius(
                                cu.convertCelciusToFahrenheit(x['oat'][0]))
            else:
                convertedTemp = x['oat'][0]

            load_values.append(x['load'][0] * load_convertfactor) #Converted to kWh
            oat_values.append(convertedTemp)
            datetime_values.append(dt.datetime.strptime(x['time'],'%Y-%m-%d %H'))

        indexList = {}
        indexList['trainingStart'] = ttow.findDateIndex(datetime_values, self.baseline_start)
        self.out.log('@trainingStart '+str(indexList['trainingStart']), logging.INFO)
        indexList['trainingStop'] = ttow.findDateIndex(datetime_values, self.baseline_stop)
        self.out.log('@trainingStop '+str(indexList['trainingStop']), logging.INFO)
        indexList['predictStart'] = ttow.findDateIndex(datetime_values, self.savings_start)
        self.out.log('@predictStart '+str(indexList['predictStart']), logging.INFO)
        indexList['predictStop'] = ttow.findDateIndex(datetime_values, self.savings_stop)
        self.out.log('@predictStop '+str(indexList['predictStop']), logging.INFO)

        for indx in indexList.keys():
            if indexList[indx] == None:
                self.out.log("Date not found in the datelist", logging.WARNING)

        # Break up data into training and prediction periods.
        timesTrain = datetime_values[indexList['trainingStart']:indexList['trainingStop']]
        timesPredict = datetime_values[indexList['predictStart']:indexList['predictStop']]

        valsTrain = load_values[indexList['trainingStart']:indexList['trainingStop']]
        valsActual = load_values[indexList['predictStart']:indexList['predictStop']]

        oatsTrain = oat_values[indexList['trainingStart']:indexList['trainingStop']]
        oatsPredict = oat_values[indexList['predictStart']:indexList['predictStop']]

        # Generate other information needed for model.
        timeStepMinutes = (timesTrain[1] - timesTrain[0]).total_seconds()/60
        # TODO: Should this be calculated in the utility function
        binCt = 6  # TODO: Allow caller to pass this in as an argument.

        # Form the temperature-time-of-week model.
        self.out.log("Starting baseline model", logging.INFO)
        ttowModel = ttow.formModel(timesTrain,
                                   oatsTrain,
                                   valsTrain,
                                   timeStepMinutes,
                                   binCt)

        # Apply the model.
        self.out.log("Applying baseline model", logging.INFO)
        valsPredict = ttow.applyModel(ttowModel, timesPredict, oatsPredict)

        # Output for scatter plot
        prevSum = 0
        for ctr in range(len(timesPredict)):
            # Calculate cumulative savings.
            prevSum += (valsPredict[ctr] - valsActual[ctr])
            self.out.insert_row("DayTimeTemperatureModel", {
                                "datetimeValues": timesPredict[ctr],
                                "measured": valsActual[ctr],
                                "predicted": valsPredict[ctr],
                                "cumulativeSum": prevSum
                                })