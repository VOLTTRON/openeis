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
from math import ceil
from datetime import timedelta as td
from copy import deepcopy
from dateutil .parser import parse
import os

import numpy as np
from scipy.stats import norm
from scipy.signal import butter, filtfilt

from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor,
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results,
                                  Descriptor,
                                  reports)

cutoff = 300
fs = 3000

type_data = 'data'
type_peak = 'peak'
type_valley = 'valley'
type_setpoint = 'setpoint'

DATE_FORMAT = '%m-%d-%y %H:%M'

class Application(DrivenApplicationBaseClass):
    type = 'type' #can be: data, peak, valley, setpoint
    timestamp = 'date'  # For Rcx
    fan_status_name = 'fan_status'
    zone_temp_name = 'zone_temp'
    zone_temp_setpoint_name = 'zone_temp_setpoint'

    def __init__(self, *args, minimum_data_count=5, area_distribution_threshold=0.1, **kwargs):
        super().__init__(*args, **kwargs)
        self.setpoint_detector = SetPointDetector(minimum_data_count, area_distribution_threshold)

    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        dgr_sym = u'\N{DEGREE SIGN}'
        return {
            'minimum_data_count':
                ConfigDescriptor(int,
                                 'Minimum data count ',
                                 value_default=5),
            'area_distribution_threshold':
                ConfigDescriptor(float,
                                 'Area distribution threshold',
                                 value_default=0.1)
        }

    @classmethod
    def get_self_descriptor(cls):
        name = 'Temperature Setpoint Detector'
        desc = 'Temperature Setpoint Detector'
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.fan_status_name:
                InputDescriptor('SupplyFanStatus',
                                'Supply fan status', count_min=0),
            cls.zone_temp_name:
                InputDescriptor('ZoneTemperature',
                                'Zone temperature', count_min=1)
        }

    def reports(self):
        '''Called by UI to assemble information for creation of the diagnostic
        visualization.
        '''
        report = reports.Report('Setpoint Detector Report')
        report.add_element(reports.SetpointDetector(
            table_name='SetpointDetector'))
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
        type_topic  = '/'.join(output_topic_base + ['SetpointDetector', cls.type])
        ts_topic = '/'.join(output_topic_base + ['SetpointDetector', cls.timestamp])
        fanstatus_topic = '/'.join(output_topic_base + ['SetpointDetector', cls.fan_status_name])
        zonetemp_topic = '/'.join(output_topic_base + ['SetpointDetector', cls.zone_temp_name])
        zonetempsetpoint_topic = '/'.join(output_topic_base + ['SetpointDetector', cls.zone_temp_setpoint_name])
        peakvalley_topic = '/'.join(output_topic_base + ['SetpointDetector', 'peak_valley'])
        note_topic = '/'.join(output_topic_base + ['SetpointDetector', 'note'])

        output_needs = {
            'SetpointDetector': {
                'type': OutputDescriptor('string', type_topic),
                'datetime': OutputDescriptor('string', ts_topic),
                'FanStatus': OutputDescriptor('integer', fanstatus_topic),
                'ZoneTemperature': OutputDescriptor('float', zonetemp_topic),
                'ZoneTemperatureSetPoint': OutputDescriptor('float', zonetempsetpoint_topic),
                'peak_valley': OutputDescriptor('float', peakvalley_topic),
                'note': OutputDescriptor('string', note_topic)
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

        fan_stat_data = []
        zone_temp_data = []
        for key, value in device_dict.items():
            if key.startswith(self.fan_status_name) and value is not None:
                fan_stat_data.append(value)
            if key.startswith(self.zone_temp_name) and value is not None:
                zone_temp_data.append(value)

        zonetemp = (sum(zone_temp_data) / len(zone_temp_data))
        fanstat = None
        if len(fan_stat_data)>0:
            fanstat = (sum(fan_stat_data) / len(fan_stat_data))
        diagnostic_result = self.setpoint_detector.on_new_data(current_time, fanstat, zonetemp, diagnostic_result)
        return diagnostic_result

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filtfilt(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def find_intersections(m1, m2, std1, std2):
    a = 1. / (2. * std1 ** 2) - 1. / (2. * std2 ** 2)
    b = m2 / (std2 ** 2) - m1 / (std1 ** 2)
    c = m1 ** 2 / (2 * std1 ** 2) - m2 ** 2 / (2 * std2 ** 2) - np.log(std2 / std1)
    return np.roots([a, b, c])

def locate_min_max(timeseries):
    try:
        filtered_timeseries = butter_lowpass_filtfilt(timeseries, cutoff, fs)
        maximums = detect_peaks(timeseries, mpd=1, valley=False)
        minimums = detect_peaks(timeseries, mpd=1, valley=True)
    except:
        filtered_timeseries = np.empty(0)
        maximums = np.empty(0)
        minimums = np.empty(0)
    return minimums, maximums, filtered_timeseries

def align_pv(zonetemp_array, peak_ind, val_ind, dtime):
    '''align_pv takes the indices of peaks (peak_ind) and indices of

    valleys (val_ind) and ensures that there is only one valley
    in-between two consecutive peaks and only one peak between two
    consecutive valleys.  If there are two or more peaks between
    valleys the largest value is kept.  If there are two or more
    valleys between two peaks then the smallest value is kept.
    '''
    try:
        reckon = 0
        aligned = False
        find_peak = True if peak_ind[0] < val_ind[0] else False
        begin = 0
        while not aligned:
            if find_peak:
                while peak_ind[reckon + 1] < val_ind[reckon + begin]:
                    if (zonetemp_array[peak_ind[reckon]] > zonetemp_array[peak_ind[reckon + 1]]):
                        peak_ind = np.delete(peak_ind, reckon + 1)
                    else:
                        peak_ind = np.delete(peak_ind, reckon)
                if ((dtime[val_ind[reckon + begin]] - dtime[peak_ind[reckon]]) <= td(minutes=5)):
                    val_ind = np.delete(val_ind, reckon + begin)
                    peak_ind = np.delete(peak_ind, reckon + 1)
                else:
                    find_peak = False
                    begin += 1
                    if begin > 1:
                        begin = 0
                        reckon += 1
            else:
                while val_ind[reckon + 1] < peak_ind[reckon + begin]:
                    if (zonetemp_array[val_ind[reckon]] > zonetemp_array[val_ind[reckon + 1]]):
                        val_ind = np.delete(val_ind, reckon)
                    else:
                        val_ind = np.delete(val_ind, reckon + 1)
                if ((dtime[peak_ind[reckon + begin]] - dtime[val_ind[reckon]]) <= td(minutes=5)):
                    val_ind = np.delete(val_ind, reckon + 1)
                    peak_ind = np.delete(peak_ind, reckon + begin)
                else:
                    find_peak = True
                    begin += 1
                    if begin > 1:
                        begin = 0
                        reckon += 1
            if (reckon + 1) == min(val_ind.size, peak_ind.size):
                aligned = True
        if peak_ind.size > val_ind.size:
            peak_ind = np.resize(peak_ind, val_ind.size)
        elif val_ind.size > peak_ind.size:
            val_ind = np.resize(val_ind, peak_ind.size)
        return peak_ind, val_ind
    except:
        return np.empty(0), np.empty(0)

def detect_peaks(data, mph=None, threshold=0, mpd=1, edge='rising',
                 kpsh=False, valley=False, ax=None):
    '''
    Detect peaks in data based on their amplitude and other features.
    Original source for detect_peaks function can be obtained at:
    https://github.com/demotu/BMC/blob/master/functions/detect_peaks.py

    __author__ = "Marcos Duarte, https://github.com/demotu/BMC"
    __version__ = "1.0.4"
    __license__ = "MIT"

    Copyright (c) 2013 Marcos Duarte
    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
    '''
    data = np.array(data)
    if data.size < 3:
        return np.array([], dtype=int)
    if valley:
        data = -data
        # mph = -mph
    # find indices of all peaks
    dx = data[1:] - data[:-1]
    # handle NaN's
    indnan = np.where(np.isnan(data))[0]
    if indnan.size:
        data[indnan] = np.inf
        dx[np.where(np.isnan(dx))[0]] = np.inf
    ine, ire, ife = np.array([[], [], []], dtype=int)
    if not edge:
        ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
    else:
        if edge.lower() in ['rising', 'both']:
            ire = np.where((np.hstack((dx, 0)) <= 0) &
                           (np.hstack((0, dx)) > 0))[0]

        if edge.lower() in ['falling', 'both']:
            ife = np.where((np.hstack((dx, 0)) < 0) &
                           (np.hstack((0, dx)) >= 0))[0]
    ind = np.unique(np.hstack((ine, ire, ife)))

    # handle NaN's
    if ind.size and indnan.size:
        # NaN's and values close to NaN's cannot be peaks
        ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan - 1,
                                                    indnan + 1))),
                          invert=True)]
    # first and last values of data cannot be peaks
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == data.size - 1:
        ind = ind[:-1]
    # remove peaks < minimum peak height
    if ind.size and mph is not None:
        ind = ind[data[ind] > mph[ind]]
    # remove peaks - neighbors < threshold
    if ind.size and threshold > 0:
        dx = np.min(np.vstack([data[ind] - data[ind - 1], data[ind] - data[ind + 1]]), axis=0)
        ind = np.delete(ind, np.where(dx < threshold)[0])
    # detect small peaks closer than minimum peak distance
    if ind.size and mpd > 1:
        ind = ind[np.argsort(data[ind])][::-1]  # sort ind by peak height
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if not idel[i]:
                # keep peaks with the same height if kpsh is True
                idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                              & (data[ind[i]] > data[ind] if kpsh else True)
                idel[i] = 0  # Keep current peak
        # remove the small peaks and sort back
        # the indices by their occurrence
        ind = np.sort(ind[~idel])
    return ind

class SetPointDetector(object):
    def __init__(self, minimum_data_count=5, area_distribution_threshold=0.1, **kwargs):
        self.minimum_data_count = minimum_data_count
        self.area_distribution_threshold = area_distribution_threshold
        self.initialize()

    def initialize(self):
        self.zonetemp_array = np.empty(0)
        self.fan_status_arr = np.empty(0)
        self.timestamp_array = np.empty(0)
        self.inconsistent_data_flag = 0
        self.number = 0
        self.startup = True
        self.available = []

    def get_output_obj(self, datetime, rec_type=type_data,
                       FanStatus=-9999, ZoneTemp=-9999, ZoneTempSp=-9999,
                       peak_valley=-9999, note=''):
        return {
            'type': rec_type,
            'datetime': datetime,
            'FanStatus': FanStatus,
            'ZoneTemperature': ZoneTemp,
            'ZoneTemperatureSetPoint': ZoneTempSp,
            'peak_valley': peak_valley,
            'note': note
        }

    def on_new_data(self, timestamp, fanstat, zonetemp, diagnostic_result):
        self.inconsistent_data_flag = 0
        fanstat_value = int(fanstat)
        zonetemp_val = float(zonetemp)
        #Insert raw data for plotting
        row = self.get_output_obj(timestamp, type_data,
                                       FanStatus=fanstat_value, ZoneTemp=zonetemp_val )
        diagnostic_result.insert_table_row('SetpointDetector', row)
        #Dx
        if not fanstat_value:
            diagnostic_result.log('Supply fan is off.  Data for {} '
                      'will not used'.format(str(timestamp)), logging.DEBUG)
            return diagnostic_result

        diagnostic_result = self.detect_stpt_main(zonetemp_val, timestamp, diagnostic_result)
        return diagnostic_result

    def check_run_status(self, current_time):
        if self.timestamp_array.size and self.timestamp_array[0].date() != current_time.date():
            return True
        return False

    def detect_stpt_main(self, zone_temp, current_time, diagnostic_result):
        try:
            if self.check_run_status(current_time):
                valleys, peaks, filtered_timeseries = locate_min_max(self.zonetemp_array)
                if np.prod(peaks.shape) < self.minimum_data_count or np.prod(valleys.shape) < self.minimum_data_count:
                    diagnostic_result.log('Set point detection is inconclusive.  Not enough data.', logging.DEBUG)
                    self.initialize()
                    return diagnostic_result
                peak_array, valley_array = align_pv(filtered_timeseries, peaks, valleys, self.timestamp_array)
                if (np.prod(peak_array.shape) < self.minimum_data_count or
                            np.prod(valley_array.shape) < self.minimum_data_count):
                    diagnostic_result.debug('Set point detection is inconclusive.  Not enough data.', logging.DEBUG)
                    self.initialize()
                    return diagnostic_result

                # for i in (0, peak_array.size-1):
                #     row = self.get_output_obj(timestamp, type_data,
                #                               FanStatus=fanstat_value, ZoneTemp=zonetemp_val)
                #     diagnostic_result.insert_table_row('SetpointDetector', row)
                #     peak_row = {
                #         'type': type_setpoint,
                #         'datetime': self.current_timestamp_array[i],
                #         'FanStatus': None,
                #         'ZoneTemperature': None,
                #         'ZoneTemperatureSetPoint': None
                #     }

                self.current_stpt_array, self.current_timestamp_array = self.create_setpoint_array(deepcopy(peak_array),
                                                                                                   deepcopy(
                                                                                                       valley_array))

                for i in (0, self.current_stpt_array.size-1):
                    row = self.get_output_obj(self.current_timestamp_array[i], type_setpoint,
                                              ZoneTempSp=self.current_stpt_array[i])
                    # stpt_row = {
                    #     'type': type_setpoint,
                    #     'datetime': self.current_timestamp_array[i],
                    #     'FanStatus': None,
                    #     'ZoneTemperature': None,
                    #     'ZoneTemperatureSetPoint': self.current_stpt_array[i]
                    # }
                    diagnostic_result.insert_table_row('SetpointDetector', row)

                # do domething with this
                #setpoint_array = self.check_timeseries_grouping()

                self.initialize()
        finally:
            self.timestamp_array = np.append(self.timestamp_array, current_time)
            self.zonetemp_array = np.append(self.zonetemp_array, zone_temp)
        return diagnostic_result

    def check_timeseries_grouping(self):
        incrementer = 0
        index = 0
        set_points = []
        number_groups = int(ceil(
            self.current_stpt_array.size)) - self.minimum_data_count if self.current_stpt_array.size > self.minimum_data_count else 1
        if number_groups == 1:
            current_stpt = [self.timestamp_array[0], self.timestamp_array[-1], np.average(self.current_stpt_array)]
            set_points.append(current_stpt)
        else:
            for grouper in range(number_groups):
                current = self.current_stpt_array[(0 + incrementer):(self.minimum_data_count + incrementer + index)]
                next_group = self.current_stpt_array[(1 + grouper):(self.minimum_data_count + grouper + 1)]

        if np.std(next_group) < 0.4:
            area = self.determine_distribution_area(current, next_group)
            if area < self.area_distribution_threshold:
                incrementer += 1
                current_stpt = [self.timestamp_array[0 + incrementer],
                                self.timestamp_array[self.minimum_data_count + incrementer + index],
                                np.average(current)]
                if np.std(current_stpt) < 0.4:
                    set_points.append(current_stpt)
                if grouper < number_groups - 1:
                    last_stpt = [self.timestamp_array[1 + grouper],
                                 self.timestamp_array[self.minimum_data_count + grouper + 1],
                                 np.average(next_group)]
            else:
                index += 1
                if grouper == number_groups - 1:
                    current = self.current_stpt_array[(0 + incrementer):(self.minimum_data_count + grouper + 1)]
                    current_stpt = [self.timestamp_array[0 + incrementer],
                                    self.timestamp_array[self.minimum_data_count + grouper + 1],
                                    np.average(current)]
            if np.std(current_stpt) < 0.4:
                set_points.append(current_stpt)

        return set_points

    def determine_distribution_area(self, current_ts, next_ts):

        def calculate_area():
            lower = min(norm.cdf(min(intersections), m1, std1), norm.cdf(min(intersections), m2, std2))
            mid_calc1 = 1 - norm.cdf(min(intersections), m1, std1) - (1 - norm.cdf(max(intersections), m1, std1))

            mid_calc2 = 1 - norm.cdf(min(intersections), m2, std2) - (1 - norm.cdf(max(intersections), m2, std2))
            mid = min(mid_calc1, mid_calc2)
            end = min(1 - norm.cdf(max(intersections), m1, std1), 1 - norm.cdf(max(intersections), m2, std2))
            return lower + mid + end

        if np.average(current_ts) > np.average(next_ts):
            current_max = True
            m1 = np.average(current_ts)
            m2 = np.average(next_ts)
            std1 = np.std(current_ts)
            std2 = np.std(next_ts)
        else:
            current_max = False
            m2 = np.average(current_ts)
            m1 = np.average(next_ts)
            std2 = np.std(current_ts)
            std1 = np.std(next_ts)
        intersections = find_intersections(m1, m2, std1, std2)
        area = calculate_area()

        return area

    def create_setpoint_array(self, pcopy, vcopy):

        peak_ts1 = zip(self.timestamp_array[pcopy], self.zonetemp_array[pcopy])
        valley_ts1 = zip(self.timestamp_array[vcopy], self.zonetemp_array[vcopy])

        peak_ts2 = zip(self.timestamp_array[pcopy], self.zonetemp_array[pcopy])
        valley_ts2 = zip(self.timestamp_array[vcopy], self.zonetemp_array[vcopy])

        peak_valley_ts1 = zip(peak_ts1, valley_ts1)
        peak_valley_ts2 = zip(peak_ts2, valley_ts2)

        remove_temp2 = [(y[0], y[1]) for x, y in peak_valley_ts2 if x[1] >= y[1] + 0.3]
        remove_temp1 = [(x[0], x[1]) for x, y in peak_valley_ts1 if x[1] >= y[1] + 0.3]

        peak_temp = [row[1] for row in remove_temp1]
        valley_temp = [row[1] for row in remove_temp2]

        peak_timestamp = [row[0] for row in remove_temp1]
        valley_timestamp = [row[0] for row in remove_temp2]

        if peak_timestamp[0] < valley_timestamp[0]:
            timestamp_array = np.array(peak_timestamp) + (np.array(valley_timestamp) - np.array(peak_timestamp)) / 2
        else:
            timestamp_array = np.array(valley_timestamp) + (np.array(peak_timestamp) - np.array(valley_timestamp)) / 2
        return (np.array(peak_temp) + np.array(valley_temp)) / 2, timestamp_array


