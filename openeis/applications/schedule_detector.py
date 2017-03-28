'''
Copyright (c) 2014, Battelle Memorial Institute
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FreeBSD Project.

This material was prepared as an account of work sponsored by an
agency of the United States Government.  Neither the United States
Government nor the United States Department of Energy, nor Battelle,
nor any of their employees, nor any jurisdiction or organization
that has cooperated in the development of these materials, makes
any warranty, express or implied, or assumes any legal liability
or responsibility for the accuracy, completeness, or usefulness or
any information, apparatus, product, software, or process disclosed,
or represents that its use would not infringe privately owned rights.

Reference herein to any specific commercial product, process, or
service by trade name, trademark, manufacturer, or otherwise does
not necessarily constitute or imply its endorsement, recommendation,
r favoring by the United States Government or any agency thereof,
or Battelle Memorial Institute. The views and opinions of authors
expressed herein do not necessarily state or reflect those of the
United States Government or any agency thereof.

PACIFIC NORTHWEST NATIONAL LABORATORY
operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
under Contract DE-AC05-76RL01830
'''

import sys
import logging
import datetime as dt
from dateutil.parser import parse
import numpy as np
from scipy.stats import norm
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

DATE_FORMAT = '%m-%d-%y %H:%M'


class Application(DrivenApplicationBaseClass):
    type = 'type' #can be: data, peak, valley, setpoint
    timestamp = 'date'  # For Rcx
    zone_temp_name = 'zone_temp'
    status_name = 'schedule_status'

    def __init__(self, *args, no_required_data=25, sample_rate='30Min', alphabet='abcd', **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule_detector = ScheduleDetection(no_required_data, sample_rate, alphabet)

    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        dgr_sym = u'\N{DEGREE SIGN}'
        return {
            'no_required_data':
                ConfigDescriptor(int,
                                 'Minimum data count ',
                                 value_default=25),
            'sample_rate':
                ConfigDescriptor(str,
                                 'Sample Rate',
                                 value_default='30Min'),
            'alphabet':
                ConfigDescriptor(str,
                                 'Alphabet',
                                 value_default='abcd'),
        }

    @classmethod
    def get_self_descriptor(cls):
        name = 'Schedule Detector'
        desc = 'Schedule Detector'
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.zone_temp_name:
                InputDescriptor('ZoneTemperature',
                                'Zone temperature', count_min=1)
        }

    def reports(self):
        '''Called by UI to assemble information for creation of the diagnostic
        visualization.
        '''
        report = reports.Report('Schedule Detector Report')
        report.add_element(reports.ScheduleDetector(
            table_name='ScheduleDetector'))
        return [report]

    @classmethod
    def output_format(cls, input_object):
        '''Called when application is staged.

        Output will have the date-time and  error-message.
        '''
        result = super().output_format(input_object)
        topics = input_object.get_topics()
        topic = topics[cls.zone_temp_name][0]
        topic_parts = topic.split('/')
        output_topic_base = topic_parts[:-1]
        ts_topic = '/'.join(output_topic_base + ['ScheduleDetector', cls.timestamp])
        zonetemp_topic = '/'.join(output_topic_base + ['ScheduleDetector', cls.zone_temp_name])
        status_topic = '/'.join(output_topic_base + ['ScheduleDetector', cls.status_name])

        output_needs = {
            'ScheduleDetector': {
                'datetime': OutputDescriptor('string', ts_topic),
                'ZoneTemperature': OutputDescriptor('float', zonetemp_topic),
                'schedule': OutputDescriptor('integer', status_topic)
            }
        }
        # return output_needs
        result.update(output_needs)
        return result

    def run(self, current_time, points):
        device_dict = {}
        diagnostic_result = Results()
        topics = self.inp.get_topics()
        diagnostic_topic = topics[self.zone_temp_name][0]
        current_time = self.inp.localize_sensor_time(diagnostic_topic,
                                                     current_time)
        for key, value in points.items():
            device_dict[key.lower()] = value

        zone_temp_data = []
        for key, value in device_dict.items():
            if key.startswith(self.zone_temp_name) and value is not None:
                zone_temp_data.append(value)

        zonetemp = (sum(zone_temp_data) / len(zone_temp_data))
        diagnostic_result = self.schedule_detector.on_new_data(current_time, zonetemp, diagnostic_result)

        return diagnostic_result


def z_normalization(time_series, data_mean, std_dev):
    if np.prod(data_mean.shape) == 0 or np.prod(std_dev.shape) == 0:
        data_mean = time_series[0].mean(axis=0)
        std_dev = time_series[0].std(axis=0)
    return ((time_series[0] - data_mean) / std_dev), data_mean, std_dev


def paa_transform(ts, n_pieces):
    splitted = np.array_split(ts, n_pieces)  ## along columns as we want
    return np.array([items[0] for items in splitted])


def sax_transform(ts, alphabet, data_mean, std_dev):
    n_pieces = ts[0].size
    alphabet_sz = len(alphabet)
    thresholds = norm.ppf(np.linspace(1. / alphabet_sz, 1 - 1. / alphabet_sz, alphabet_sz - 1))

    def translate(ts_values):
        return np.asarray([(alphabet[0] if ts_value < thresholds[0]
                            else (alphabet[-1]
                                  if ts_value > thresholds[-1]
                                  else alphabet[np.where(thresholds <= ts_value)[0][-1] + 1]))
                           for ts_value in ts_values])

    normalized_ts, data_mean, std_dev = z_normalization(ts, data_mean, std_dev)
    paa_ts = paa_transform(normalized_ts, n_pieces)

    return np.apply_along_axis(translate, 0, paa_ts), data_mean, std_dev


def create_alphabet_dict(alphabet):
    alphabet_dict = {}
    alphabet_length = len(alphabet)
    for item in range(alphabet_length):
        if item <= (alphabet_length - 1) / 2:
            alphabet_dict[alphabet[item]] = 0
        else:
            alphabet_dict[alphabet[item]] = 1
    return alphabet_dict


class ScheduleDetection(object):
    """Symbolic schedule detection.
    """

    def __init__(self, no_required_data=25, sample_rate='30Min', alphabet='abcd', **kwargs):
        """
        Initializes agent
        :param kwargs: Any driver specific parameters"""

        self.no_required_data = no_required_data
        sample = sample_rate
        self.sample = int(sample[0:2])
        self.sample_str = sample
        self.alphabet = alphabet
        self.alphabet_dict = create_alphabet_dict(self.alphabet)
        self.data_mean = np.empty(0)
        self.std_dev = np.empty(0)

        def date_parse(dates):
            return [parse(timestamp).time() for timestamp in dates]

        self.initialize()

    def initialize(self):
        self.data_array = []
        self.timestamp_array = []

    def weekly_reset(self):
        self.data_mean = np.empty(0)
        self.std_dev = np.empty(0)

    def check_run_status(self, current_time, no_required_data):
        last_time = self.timestamp_array[-1]
        if self.timestamp_array and last_time.day != current_time.day:
            if len(self.timestamp_array) < no_required_data:
                return None
            return True
        return False

    def on_new_data(self, current_time, zonetemp, diagnostic_result):
        check_run = False
        data_point = zonetemp
        status_array = []
        if self.timestamp_array:
            check_run = self.check_run_status(current_time, self.no_required_data)
        if check_run:
            ts_arr, data_arr, status_arr = self.timeseries_to_sax()
            for idx, val in enumerate(ts_arr):
                row = {
                    'datetime': ts_arr[idx],
                    'ZoneTemperature': data_arr[idx],
                    'schedule': status_arr[idx]
                }
                diagnostic_result.insert_table_row('ScheduleDetector', row)
            self.initialize()
        self.timestamp_array.append(current_time)
        self.data_array.append(data_point)

        return diagnostic_result


    def timeseries_to_sax(self):
        """Convert time series data to symbolic form."""
        timestamp_array, data_array = self._resample()
        sax_array = np.array([data_array, timestamp_array])
        sax_data, self.data_mean, self.std_dev = sax_transform(sax_array, self.alphabet, self.data_mean, self.std_dev)
        symbolic_array = [item[0] for item in sax_data]
        status_array = [self.alphabet_dict[symbol] for symbol in symbolic_array]

        if timestamp_array[0].weekday() == 6:
            self.weekly_reset()

        return timestamp_array, data_array, status_array


    def _resample(self):
        resampled_timestamp = []
        resampled_data = []
        data_accumulator = []
        first_time = self.timestamp_array[0]
        offset = first_time.minute % self.sample
        first_append = first_time - dt.timedelta(minutes=offset)
        resampled_timestamp.append(first_append)

        while resampled_timestamp[-1] < self.timestamp_array[-1]:
            next_timestamp = resampled_timestamp[-1] + dt.timedelta(minutes=self.sample)
            if next_timestamp.day != self.timestamp_array[-1].day:
                break
            resampled_timestamp.append(next_timestamp)

        _index = 0
        for ts in range(1, len(resampled_timestamp)):
            while self.timestamp_array[_index].replace(second=0, microsecond=0) < resampled_timestamp[ts].replace(
                    second=0, microsecond=0):
                data_accumulator.append(self.data_array.pop(0))
                _index += 1
            resampled_data.append(np.mean(data_accumulator))
            data_accumulator = []
        resampled_data.append(np.mean(self.data_array))

        return resampled_timestamp, resampled_data
