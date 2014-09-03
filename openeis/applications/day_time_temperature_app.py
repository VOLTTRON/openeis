"""
Implement a building baseline load prediction model based on temperature and time-of-week (TTOW).

See Johanna L. Mathieu, Phillip N. Price, Sila Kiliccote, and Mary Ann Piette,
"Quantifying Changes in Building Electricity Use, with Application to Demand Response",
Lawrence Berkeley National Laboratory,
report LBNL-4944E
(April 2011)
http://escholarship.org/uc/item/6068k5nh

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


from openeis.applications import DriverApplicationBaseClass, InputDescriptor, \
    OutputDescriptor, ConfigDescriptor
from openeis.applications import reports
import logging
import datetime as dt
from django.db.models import Avg
from .utils.baseline_models import day_time_temperature_model as ttow



class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, 
                              training_startdate=None,
                              training_stopdate=None,
                              prediction_startdate=None,
                              prediction_stopdate=None,
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
        self.training_start = dt.datetime.strptime(training_startdate, '%Y-%m-%d')
        self.training_stop = dt.datetime.strptime(training_stopdate, '%Y-%m-%d') 
        self.prediction_start = dt.datetime.strptime(prediction_startdate, '%Y-%m-%d') 
        self.prediction_stop = dt.datetime.strptime(prediction_stopdate, '%Y-%m-%d')
        

    @classmethod
    def get_config_parameters(cls):
        # Called by UI
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True),
            "training_startdate": ConfigDescriptor(str, "Training Start Date (YYYY-MM-DD)", optional=False),
            "training_stopdate": ConfigDescriptor(str, "Training End Date (YYYY-MM-DD)", optional=False),
            "prediction_startdate": ConfigDescriptor(str, "Prediction Start Date (YYYY-MM-DD)", optional=False),
            "prediction_stopdate": ConfigDescriptor(str, "Prediction End Date (YYYY-MM-DD)", optional=False)
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
            Energy Signature: outside air temperature and loads.
                Data will be used for scatter plot.
            Weather Sensitivity: dependent on OAT and loads.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        
        time_values = '/'.join(output_topic_base + ['daytimetemperature', 'datetime'])
        predicted_values = '/'.join(output_topic_base + ['daytimetemperature', 'predicted'])
        measured_values  = '/'.join(output_topic_base + ['daytimetemperature', 'measured'])

        output_needs = {
            'DayTimeTemperatureModel': {
                'datetimeValues': OutputDescriptor('datetime', time_values),
                'predictedValues': OutputDescriptor('float', predicted_values),
                'measuredValues' : OutputDescriptor('float', measured_values)
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

        report = reports.Report('Day-Time-Temperature Baseline Model')

        text_blurb = reports.TextBlurb(text="Analysis shows baseline model and the measured values for a single building.")
        report.add_element(text_blurb)

        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('DayTimeTemperatureModel', 'datetimeValues', 'predictedValues'))
        baseline_plot = reports.ScatterPlot(xy_dataset_list,
                                           title='Baseline Model',
                                           x_label='Timestamp',
                                           y_label='Power'
                                           )
        report.add_element(baseline_plot)

        xy_dataset_list = []
        xy_dataset_list.append(reports.XYDataSet('DayTimeTemperatureModel', 'datetimeValues', 'measuredValues'))
        measured_plot = reports.ScatterPlot(xy_dataset_list,
                                   title='Measured Values',
                                   x_label='Timestamp',
                                   y_label='Power'
                                   )
        report.add_element(measured_plot)

        
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
        # TODO: Convert to minutes? 
        load_query = self.inp.get_query_sets('load', group_by='hour',
                                             group_by_aggregation=Avg,
                                             exclude={'value':None},
                                             wrap_for_merge=True)
        oat_query = self.inp.get_query_sets('oat', group_by='hour', 
                                             group_by_aggregation=Avg,
                                             exclude={'value':None},
                                             wrap_for_merge=True)

        # Match the values by timestamp
        merged_load_oat = self.inp.merge(load_query, oat_query) 

        load_values = []
        oat_values = []
        datetime_values = []

        for x in merged_load_oat:
            load_values.append(x['load'][0])
            oat_values.append(x['oat'][0])
            datetime_values.append(dt.datetime.strptime(x['time'],'%Y-%m-%d %H'))

        indexList = {}
        indexList['trainingStart'] = ttow.findDateIndex(datetime_values, self.training_start)
        indexList['trainingStop'] = ttow.findDateIndex(datetime_values, self.training_stop)
        indexList['predictStart'] = ttow.findDateIndex(datetime_values, self.prediction_start)
        indexList['predictStop'] = ttow.findDateIndex(datetime_values, self.prediction_stop)
        
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
        for ctr in range(len(timesPredict)):
            self.out.insert_row("DayTimeTemperatureModel", { 
                                "datetimeValues": timesPredict[ctr],
                                "predictedValues": valsPredict[ctr],
                                "measuredValues": valsActual[ctr]
                                })