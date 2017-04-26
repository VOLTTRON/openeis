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
import dateutil.tz
from datetime import timedelta as td
from copy import deepcopy
import numpy as np
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
default_if_none = -9999

type_data = 'data'
type_peak = 'peak'
type_valley = 'valley'
type_setpoint = 'setpoint'
type_cycling = 'cycling'
available_tz = {1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern'}


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filtfilt(data, cutoff, fs, order=5):
    try:
        b, a = butter_lowpass(cutoff, fs, order=order)
        y = filtfilt(b, a, data)
    except:
        y = []
    return y

def find_intersections(m1, m2, std1, std2):
    a = 1. / (2. * std1 ** 2) - 1. / (2. * std2 ** 2)
    b = m2 / (std2 ** 2) - m1 / (std1 ** 2)
    c = m1 ** 2 / (2 * std1 ** 2) - m2 ** 2 / (2 * std2 ** 2) - np.log(std2 / std1)
    return np.roots([a, b, c])


def locate_min_max(*args):
    filtered_timeseries = butter_lowpass_filtfilt(args[0], cutoff, fs)

    maximums = detect_peaks(filtered_timeseries, args[1], mpd=10, valley=False)
    minimums = detect_peaks(filtered_timeseries, args[1], mpd=10, valley=True)
    return minimums, maximums, filtered_timeseries


def align_pv(zone_temperature_array, peak_ind, val_ind, dtime):
    """
    align_pv takes the indices of peaks (peak_ind) and indices of
    valleys (val_ind) and ensures that there is only one valley
    in-between two consecutive peaks and only one peak between two
    consecutive valleys.  If there are two or more peaks between
    valleys the largest value is kept.  If there are two or more
    valleys between two peaks then the smallest value is kept.
    """
    try:
        reckon = 0
        aligned = False
        find_peak = True if peak_ind[0] < val_ind[0] else False
        begin = 0
        while not aligned:
            if find_peak:
                while peak_ind[reckon + 1] < val_ind[reckon + begin]:
                    if zone_temperature_array[peak_ind[reckon]] > zone_temperature_array[peak_ind[reckon + 1]]:
                        peak_ind = np.delete(peak_ind, reckon + 1)
                    else:
                        peak_ind = np.delete(peak_ind, reckon)
                if (dtime[val_ind[reckon + begin]] - dtime[peak_ind[reckon]]) <= td(minutes=5):
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
                    if zone_temperature_array[val_ind[reckon]] > zone_temperature_array[val_ind[reckon + 1]]:
                        val_ind = np.delete(val_ind, reckon)
                    else:
                        val_ind = np.delete(val_ind, reckon + 1)
                if (dtime[peak_ind[reckon + begin]] - dtime[val_ind[reckon]]) <= td(minutes=5):
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
    """
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
    """
    data = np.array(data)
    if data.size < 3:
        return np.array([], dtype=int)
    if mph is not None:
        mph = np.array(mph)
    if valley:
        data = -data
        mph = -mph if mph is not None else None

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
            ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
        if edge.lower() in ['falling', 'both']:
            ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
    ind = np.unique(np.hstack((ine, ire, ife)))

    # handle NaN's
    if ind.size and indnan.size:
        # NaN's and values close to NaN's cannot be peaks
        ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan - 1, indnan + 1))), invert=True)]
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
                idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) & (
                data[ind[i]] > data[ind] if kpsh else True)
                idel[i] = 0  # Keep currentent peak
        # remove the small peaks and sort back
        # the indices by their occurrentence
        ind = np.sort(ind[~idel])
    return ind


class Application(DrivenApplicationBaseClass):
    type = 'type' #can be: data, peak, valley, setpoint
    timestamp = 'date'  # For Rcx
    fanstatus_name = 'fan_status'
    zonetemperature_name = 'zone_temp'
    zonetemperature_stpt_name = 'zone_temp_setpoint'
    comprstatus_name = 'compressor_status'

    def __init__(self, *args, minimum_data_count=5, analysis_run_interval=500, local_tz=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.cycling_detector = CyclingDetector(minimum_data_count, analysis_run_interval)
        try:
            self.cur_tz = available_tz[local_tz]
        except:
            self.cur_tz = 'UTC'
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
            'analysis_run_interval':
                ConfigDescriptor(int,
                                 'Analysis Run Interval',
                                 value_default=500),
            'local_tz':
                ConfigDescriptor(int,
                                 "Integer corresponding to local timezone: [1: 'US/Pacific', 2: 'US/Mountain', 3: 'US/Central', 4: 'US/Eastern']",
                                 value_default=1)
        }

    @classmethod
    def get_self_descriptor(cls):
        name = 'Compressor Cycling Diagnostic'
        desc = 'Compressor Cycling Diagnostic'
        return Descriptor(name=name, description=desc)

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.zonetemperature_name:
                InputDescriptor('ZoneTemperature',
                                'Zone temperature', count_min=1),
            cls.zonetemperature_stpt_name:
                InputDescriptor('ZoneTemperatureSetPoint',
                                'Zone Temperature Set Point', count_min=0),
            cls.fanstatus_name:
                InputDescriptor('SupplyFanStatus',
                                'Supply fan status', count_min=1),
            cls.comprstatus_name:
                InputDescriptor('CompressorStatus',
                                'Compressor status', count_min=0)
        }

    def reports(self):
        """
        Called by UI to assemble information for creation of the diagnostic
        visualization.
        """
        report = reports.Report('Compressor Cycling Report')
        report.add_element(reports.CyclingDetector(table_name='CyclingDetector'))
        return [report]

    @classmethod
    def output_format(cls, input_object):
        """
        Called when application is staged.
        Output will have the date-time and  error-message.
        """
        result = super().output_format(input_object)
        topics = input_object.get_topics()
        topic = topics[cls.zonetemperature_name][0]
        topic_parts = topic.split('/')
        output_topic_base = topic_parts[:-1]

        type_topic  = '/'.join(output_topic_base + ['CyclingDetector', cls.type])
        ts_topic = '/'.join(output_topic_base + ['CyclingDetector', cls.timestamp])
        fanstatus_topic = '/'.join(output_topic_base + ['CyclingDetector', cls.fanstatus_name])
        zonetemp_topic = '/'.join(output_topic_base + ['CyclingDetector', cls.zonetemperature_name])
        zonetempsetpoint_topic = '/'.join(output_topic_base + ['CyclingDetector', cls.zonetemperature_stpt_name])
        cycling_topic = '/'.join(output_topic_base + ['CyclingDetector', 'cycling'])

        output_needs = {
            'CyclingDetector': {
                'type': OutputDescriptor('string', type_topic),
                'datetime': OutputDescriptor('string', ts_topic),
                'FanStatus': OutputDescriptor('integer', fanstatus_topic),
                'ComprStatus': OutputDescriptor('integer', fanstatus_topic),
                'ZoneTemperature': OutputDescriptor('float', zonetemp_topic),
                'ZoneTemperatureSetPoint': OutputDescriptor('float', zonetempsetpoint_topic),
                'cycling': OutputDescriptor('integer', cycling_topic)
            }
        }

        # return output_needs
        result.update(output_needs)
        return result

    def run(self, current_time, points):
        # topics = self.inp.get_topics()
        # diagnostic_topic = topics[self.zonetemperature_name][0]
        # current_time = self.inp.localize_sensor_time(diagnostic_topic, current_time)
        device_dict = {}
        diagnostic_result = Results()
        to_zone = dateutil.tz.gettz(self.cur_tz)
        current_time = current_time.astimezone(to_zone)

        for key, value in points.items():
            point_device = [_name.lower() for _name in key.split('&&&')]
            if point_device[0] not in device_dict:
                device_dict[point_device[0]] = [(point_device[1], value)]
            else:
                device_dict[point_device[0]].append((point_device[1], value))

        fan_stat_data = []
        zone_temp_data = []
        compr_stat_data = []
        zone_temp_setpoint_data = []

        def data_builder(value_tuple, point_name):
            value_list = []
            for item in value_tuple:
                value_list.append(item[1])
            return value_list

        for key, value in device_dict.items():
            data_name = key
            if value is None:
                continue
            if data_name == self.fanstatus_name:
                fan_stat_data = data_builder(value, data_name)
            if data_name == self.zonetemperature_stpt_name:
                zone_temp_setpoint_data = data_builder(value, data_name)
            if data_name == self.zonetemperature_name:
                zone_temp_data = data_builder(value, data_name)
            if data_name == self.comprstatus_name:
                compr_stat_data = data_builder(value, data_name)

        zonetemp = (sum(zone_temp_data) / len(zone_temp_data))
        fanstat = None
        comprstat = None
        zonetemp_setpoint = None

        if fan_stat_data:
            fanstat = (sum(fan_stat_data) / len(fan_stat_data))
        if compr_stat_data:
            comprstat = (sum(compr_stat_data) / len(compr_stat_data))
        if zone_temp_setpoint_data:
            zonetemp_setpoint = (sum(zone_temp_setpoint_data) / len(zone_temp_setpoint_data))


        zonetemp = zonetemp or default_if_none
        fanstat = fanstat or default_if_none
        comprstat = comprstat or default_if_none
        zonetemp_setpoint = zonetemp_setpoint or default_if_none

        diagnostic_result = self.cycling_detector.on_new_data(current_time, zonetemp, zonetemp_setpoint,
                                                              fanstat, comprstat, diagnostic_result)

        return diagnostic_result


class CyclingDetector(object):
    """OpenEIS Compressor Cycling diagnostic agent."""
    def __init__(self, minimum_data_count=5, analysis_run_interval=500, **kwargs):
        self.minimum_data_count = minimum_data_count
        self.check_time = analysis_run_interval

        self.available_data_points = []
        self.inconsistent_data_flag = 0
        self.intervals = 1
        self.file = 1
        self.file_sp = 1

        # Initialize data arrays
        self.initialize()

    def initialize(self):
        """
        Initialize data arrays.
        """
        self.zone_temperature_array = []
        self.zone_temperature_stpt_array = []
        self.compressor_status_array = []
        self.timestamp_array = []
        self.last_state = None
        self.last_time = None
        self.startup = True
        self.mode = None

    def on_new_data(self, timestamp, zonetemp, zone_temp_setpoint, fanstat, compr_stat, diagnostic_result):
        """
        Determine diagnostic algorithm based on available data.
        Minimum data requirement is zone temperature and supply fan status.
        """
        if compr_stat != default_if_none and fanstat != default_if_none:
            self.mode = 1
        elif zonetemp != default_if_none and zone_temp_setpoint != default_if_none and fanstat != default_if_none:
            self.mode = 2
        elif zonetemp != default_if_none and fanstat != default_if_none:
            self.mode = 3
        else:
            self.mode = 4

        if self.mode == 4:
            diagnostic_result.log('Required data for diagnostic is not available or '
                      'configured names do not match published names!')
            return diagnostic_result

        results = {}

        if self.mode == 1:
            compressor_data = int(compr_stat)
            results = self.operating_mode1(compressor_data, timestamp, diagnostic_result)
        if self.mode == 2:
            zonetemp_data = float(zonetemp)
            zonetemp_stpt_data = float(zone_temp_setpoint)
            results = self.operating_mode2(zonetemp_data, zonetemp_stpt_data, timestamp, diagnostic_result)
        if self.mode == 3:
            zonetemp_data = float(zonetemp)
            results = self.operating_mode3(zonetemp_data, timestamp, diagnostic_result)

        cycling = 0
        if "cycles" in results:
            if results["cycles"] != 'INCONCLUSIVE':
                cycling = results["cycles"]

        row = self.get_output_obj(datetime=timestamp,
                                  rec_type=type_cycling,
                                  fan_status=fanstat,
                                  compr_status=compr_stat,
                                  zone_temp=zonetemp,
                                  zone_temp_sp=zone_temp_setpoint,
                                  cycling=cycling)

        diagnostic_result.insert_table_row('CyclingDetector', row)
        return diagnostic_result

    def get_output_obj(self, datetime, rec_type=type_data,
                       fan_status=-9999, compr_status=-9999, zone_temp=-9999,
                       zone_temp_sp=-9999, cycling=-9999):
        return {
            'type': rec_type,
            'datetime': datetime,
            'FanStatus': fan_status,
            'ComprStatus': compr_status,
            'ZoneTemperature': zone_temp,
            'ZoneTemperatureSetPoint': zone_temp_sp,
            'cycling': cycling
        }

    def operating_mode1(self, compressor_data, current_time, diagnostic_result):
        diagnostic_result.log('Running Cycling Dx Mode 1.')
        self.timestamp_array.append(current_time)
        self.compressor_status_array.append(compressor_data)
        iterate_on = len(self.compressor_status_array) - 1
        results = {}

        if self.timestamp_array[-1] - self.timestamp_array[0] >= td(minutes=self.check_time):
            on_indices = []
            off_indices = []
            for status in range(1, iterate_on):
                if self.compressor_status_array[status] and not self.compressor_status_array[status - 1]:
                    on_indices.append(status)
                if not self.compressor_status_array[status] and self.compressor_status_array[status - 1]:
                    off_indices.append(status)

            results = self.cycling_dx(on_indices, off_indices, diagnostic_result)
            #self.output_cycling()
            self.shrink(self.compressor_status_array)
            diagnostic_result.log('CyclingDx results: {}'.format(results))

        return results

    def operating_mode2(self, zonetemperature_data, zonetemperature_stpt_data, current_time, diagnostic_result):
        diagnostic_result.log('Running Cycling Dx Mode 2.')
        self.timestamp_array.append(current_time)
        self.zone_temperature_array.append(zonetemperature_data)
        self.zone_temperature_stpt_array.append(zonetemperature_stpt_data)
        results = {}

        if self.timestamp_array[-1] - self.timestamp_array[0] >= td(minutes=self.check_time):
            minimums, maximums, filtered_timeseries = locate_min_max(self.zone_temperature_array,
                                                                     self.zone_temperature_stpt_array)
            results = self.results_handler(maximums, minimums, filtered_timeseries, diagnostic_result)

        return results

    def operating_mode3(self, zonetemperature_data, current_time, diagnostic_result):
        diagnostic_result.log('Running CyclingDx Mode 3.')
        self.timestamp_array.append(current_time)
        self.zone_temperature_array.append(zonetemperature_data)
        results = {}

        if self.timestamp_array[-1] - self.timestamp_array[0] >= td(minutes=self.check_time):
            valleys, peaks, filtered_timeseries = locate_min_max(self.zone_temperature_array, None)
            if np.prod(valleys.shape) < self.minimum_data_count or np.prod(peaks.shape) < self.minimum_data_count:
                diagnostic_result.log('Set point detection is inconclusive.  Not enough data.')
                self.shrink(self.zone_temperature_array)
                results = {
                    "cycles": 'INCONCLUSIVE',
                    "Avg On Cycle": "INCONCLUSIVE",
                    "Avg Off Cycle": "INCONCLUSIVE"
                }

                return results

            peak_array, valley_array = align_pv(filtered_timeseries, peaks, valleys, self.timestamp_array)

            if np.prod(peak_array.shape) < self.minimum_data_count or np.prod(
                    peak_array.shape) < self.minimum_data_count:
                diagnostic_result.log('Set point detection is inconclusive.  Not enough data.')
                self.shrink(self.zone_temperature_array)
                results = {
                    "cycles": 'INCONCLUSIVE',
                    "Avg On Cycle": "INCONCLUSIVE",
                    "Avg Off Cycle": "INCONCLUSIVE"
                }

                return results

            self.zone_temperature_stpt_array = self.create_setpoint_array(deepcopy(peak_array), deepcopy(valley_array))

            if len(self.zone_temperature_stpt_array)>0:
                minimums, maximums, filtered_timeseries = locate_min_max(self.zone_temperature_array,
                                                                         self.zone_temperature_stpt_array)
                results = self.results_handler(maximums, minimums, filtered_timeseries, diagnostic_result)
            else:
                results = {
                    "cycles": 'INCONCLUSIVE',
                    "Avg On Cycle": "INCONCLUSIVE",
                    "Avg Off Cycle": "INCONCLUSIVE"
                }

        return results

    def shrink(self, array):
        self.timestamp_array = [item for item in self.timestamp_array if (item - self.timestamp_array[0]) >= td(minutes=self.check_time / 4)]
        shrink = len(array) - len(self.timestamp_array)
        self.zone_temperature_array = self.zone_temperature_array[shrink:]
        self.zone_temperature_stpt_array = self.zone_temperature_stpt_array[shrink:]
        self.compressor_status_array = self.compressor_status_array[shrink:]

    def results_handler(self, maximums, minimums, filtered_timeseries, diagnostic_result):
        if np.prod(maximums.shape) < self.minimum_data_count or np.prod(minimums.shape) < self.minimum_data_count:
            diagnostic_result.log('Set point detection is inconclusive.  Not enough data.')
            self.shrink(self.zone_temperature_array)
            results = {
                "cycles": 'INCONCLUSIVE',
                "Avg On Cycle": "INCONCLUSIVE",
                "Avg Off Cycle": "INCONCLUSIVE"
            }
            return results

        peak_array, valley_array = align_pv(filtered_timeseries, maximums, minimums, self.timestamp_array)

        if np.prod(peak_array.shape) < self.minimum_data_count or np.prod(valley_array.shape) < self.minimum_data_count:
            diagnostic_result.log('Set point detection is inconclusive.  Not enough data.')
            self.shrink(self.zone_temperature_array)
            results = {
                "cycles": 'INCONCLUSIVE',
                "Avg On Cycle": "INCONCLUSIVE",
                "Avg Off Cycle": "INCONCLUSIVE"
            }
            return results

        pcopy = deepcopy(peak_array)
        vcopy = deepcopy(valley_array)
        self.compressor_status_array = self.gen_status(pcopy, vcopy, self.timestamp_array, diagnostic_result)
        # self.output_cycling()
        results = self.cycling_dx(pcopy, vcopy, diagnostic_result)
        diagnostic_result.log('Cycling diagnostic results: ' + str(results))
        self.shrink(self.zone_temperature_array)

        return results

    def create_setpoint_array(self, pcopy, vcopy):
        """Creates setpoint array when zone temperature set point is not measured."""
        peak_ts1 = zip([self.timestamp_array[ind] for ind in pcopy], [self.zone_temperature_array[ind] for ind in pcopy])
        valley_ts1 = zip([self.timestamp_array[ind] for ind in vcopy], [self.zone_temperature_array[ind] for ind in vcopy])

        peak_ts2 = zip([self.timestamp_array[ind] for ind in pcopy], [self.zone_temperature_array[ind] for ind in pcopy])
        valley_ts2 = zip([self.timestamp_array[ind] for ind in vcopy], [self.zone_temperature_array[ind] for ind in vcopy])

        peak_ts3 = zip([self.timestamp_array[ind] for ind in pcopy], [self.zone_temperature_array[ind] for ind in pcopy])
        valley_ts3 = zip([self.timestamp_array[ind] for ind in vcopy], [self.zone_temperature_array[ind] for ind in vcopy])

        zip1 = zip(peak_ts1, valley_ts1)
        zip2 = zip(peak_ts2, valley_ts2)
        remove_temp1 = [(x[0], x[1]) for x, y in zip1 if x[1] >= y[1] + 0.25]
        remove_temp2 = [(y[0], y[1]) for x, y in zip2 if x[1] >= y[1] + 0.25]

        peak_ts_list = list(peak_ts3)
        valleys_ts_list = list(valley_ts3)

        peaks = [pcopy[x] for x in range(pcopy.size) if peak_ts_list[x][1] >= valleys_ts_list[x][1] + 0.25]
        valleys = [vcopy[x] for x in range(vcopy.size) if peak_ts_list[x][1] >= valleys_ts_list[x][1] + 0.25]

        zone_temperature_stpt = []

        if len(peaks)>0 and len(valleys)>0:
            peak_temp = [row[1] for row in remove_temp1]
            valley_temp = [row[1] for row in remove_temp2]

            setpoint_raw = [(peak_val + valley_val) / 2 for peak_val, valley_val in zip(peak_temp, valley_temp)]
            peak_timestamp = [row[0] for row in remove_temp1]
            valley_timestamp = [row[0] for row in remove_temp2]

            indexer = 0
            current = valleys if peak_timestamp[0] < valley_timestamp[0] else peaks

            for ind in range(len(self.zone_temperature_array)):
                if ind <= current[indexer]:
                    zone_temperature_stpt.append(setpoint_raw[indexer])
                elif indexer + 1 >= len(setpoint_raw):
                    zone_temperature_stpt.append(setpoint_raw[-1])
                    continue
                else:
                    indexer += 1
                    current = peaks if current == valleys else valleys
                    zone_temperature_stpt.append(setpoint_raw[indexer])

        return zone_temperature_stpt

    def cycling_dx(self, on_indices, off_indices, diagnostic_result):
        diagnostic_result.log('Determine if units is cycling excessively.')
        no_cycles = False
        always_on = False
        always_off = False
        on_count = self.compressor_status_array.count(1)

        if on_count == len(self.compressor_status_array):
            always_on = True
            no_cycles = True
        if sum(self.compressor_status_array) == 0:
            always_off = True
            no_cycles = True
        if no_cycles:
            if always_on: results = {"cycles": 0, "Avg On Cycle": "ALL", "Avg Off Cycle": 0}
            if always_off: results = {"cycles": 0, "Avg On Cycle": 0, "Avg Off Cycle": "ALL"}
            return results

        no_cycles = len(on_indices)
        on_check = 0
        off_check = 1

        if off_indices[0] < on_indices[0]:
            on_check = 1
            off_check = 0
        on_time = [(self.timestamp_array[off] - self.timestamp_array[on]).total_seconds() / 60 - 1 for on, off in zip(on_indices, off_indices[on_check:])]
        off_time = [(self.timestamp_array[on] - self.timestamp_array[off]).total_seconds() / 60 - 1 for on, off in zip(on_indices[off_check:], off_indices)]

        if self.last_state:
            from_previous = (self.timestamp_array[off_indices[0]] - self.last_time).total_seconds() / 60
            on_time.insert(0, from_previous)
        if self.last_state is not None and self.last_state == 0:
            from_previous = (self.timestamp_array[on_indices[0]] - self.last_time).total_seconds() / 60
            off_time.insert(0, from_previous)

        self.last_time = self.timestamp_array[0] + td(minutes=self.check_time / 4)

        if self.last_time not in self.timestamp_array:
            for item in self.timestamp_array:
                if (item - self.timestamp_array[0]) >= td(minutes=self.check_time / 4):
                    self.last_time = item
                    break
        try:
             state_ind = self.timestamp_array.index(self.last_time)
             self.last_state = self.compressor_status_array[state_ind]
        except:
             self.last_time = None
             self.last_state = None

        avg_on = np.mean(on_time) if on_time else -99.9
        avg_off = np.mean(off_time) if off_time else -99.9

        results = {"cycles": no_cycles, "Avg On Cycle": avg_on, "Avg Off Cycle": avg_off}
        return results

    def gen_status(self, peak, valley, time_array, diagnostic_result):
        '''Generate cycling status array.'''
        extrema_array = [peak, valley]
        first = min(peak[0], valley[0])
        first_array = peak if peak[0] == first else valley
        first_array_index = 0 if peak[0] == first else 1
        status_value = 1 if peak[0] == first else 0

        extrema_array.pop(first_array_index)
        second_array = extrema_array[0]
        current = first_array[0]
        _next = second_array[0]
        last_stat = self.last_state if self.last_state is not None else 0
        status_array = [last_stat for _ in range(0, current)]
        ascend = True
        index_count = 0

        while True:
            num_pts = int(_next - current)
            for _ in range(0, num_pts):
                status_array.append(status_value)
            if ascend:
                index_count += 1
                if index_count == min(len(valley), len(peak)):
                    break
                ascend = False
                _next = first_array[index_count]
                current = second_array[index_count - 1]
                status_value = 0 if status_value == 1 else 1
            else:
                ascend = True
                current = first_array[index_count]
                _next = second_array[index_count]
                status_value = 0 if status_value == 1 else 1
        status_value = 0
        if len(peak) > len(valley):
            status_value = 1
            for _ in range(peak[-1] - valley[-1]):
                status_array.append(0)
        while len(status_array) < len(time_array):
            status_array.append(status_value)
        return status_array

