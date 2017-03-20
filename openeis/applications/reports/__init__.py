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

'''Report meta data objects for applications to describe output for user presentation.'''

class Report:

    def __init__(self, description):
        self.description = description
        self.elements = []

    def add_element(self, element):
        if isinstance(element, ReportElement) is False:
            raise ValueError('Can only add ReportElement to Report')
        self.elements.append(element)

    def __str__(self):
        results = 'Report: '
        results += self.description + '\n'
        results += 'Report Elements: \n'
        for element in self.elements:
            results += str(element)
            results += '\n'
        return results

class ReportElement:

    def __init__(self, title=None, description=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.description = description

    def __str__(self):
        members = dir(self)
        result = self.__class__.__name__ + ': '
        for key in members:
            if key.startswith("_") or callable(getattr(self, key)) is True:
                continue
            value = getattr(self, key)
            if value is not None:
                result += '\n\t' + key + ' = ' + str(value)
        return result

class TextBlurb(ReportElement):

    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text

class Table(ReportElement):

    def __init__(self, table_name, column_info, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

        'This is a list of tuples which is used for ordering and describing columns'
        self.column_info = column_info



class XYDataSet():

    def __init__(self, table_name, x_column, y_column):
        self.table_name = table_name
        self.x_column = x_column
        self.y_column = y_column

    def __repr__(self):
        result = self.__class__.__name__ + '('
        result += self.table_name + ','
        result += self.x_column + ','
        result += self.y_column + ')'
        return result


class XYPlot(ReportElement):

    def __init__(self, xy_dataset_list, x_label, y_label, **kwargs):
        super().__init__(**kwargs)
        self.xy_dataset_list = xy_dataset_list
        self.x_label = x_label
        self.y_label = y_label


class LinePlot(XYPlot):
    pass

class BarChart(XYPlot):
    pass

class ScatterPlot(XYPlot):
    pass

class DatetimeScatterPlot(XYPlot):
    pass

class HeatMap(ReportElement):

    def __init__(self, table_name, x_column, y_column, z_column, x_label=None, y_label=None, z_label=None, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name
        self.x_column = x_column
        self.y_column = y_column
        self.z_column = z_column
        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label

class LoadProfile(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

class LoadProfileRx(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

class RetroCommissioningOAED(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name


class RetroCommissioningAFDD(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

class RxStaticPressure(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name
class RxSupplyTemp(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name
class RxOperationSchedule(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name
class SetpointDetector(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name
class ScheduleDetector(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name
class CyclingDetector(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

class RetroCommissioningAFDDEcam(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name


class ZoneEcam(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name


class Ecam(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

class AhuEcam(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

class HWPlantViz(ReportElement):
    def __init__(self, table_name, **kwargs):
        super().__init__(**kwargs)
        self.table_name = table_name

if __name__ == '__main__':

    report = Report("This is a report description")

    table = Table("XYZ", (('columnA', 'My first column'), ('columnB', 'My Second Column')))

    report.add_element(table)

    text_blurb = TextBlurb(text="this is a text blurb")
    report.add_element(text_blurb)

    xy_dataset_list = []
    xy_dataset_list.append(XYDataSet('OAT', 'Timestamp', 'Temperature'))
    xy_dataset_list.append(XYDataSet('Sensor', 'Timestamp', 'SensorValue'))
    line_plot = LinePlot(xy_dataset_list, title='line chart', x_label='Temperature', y_label='values')
    report.add_element(line_plot)

    bar_chart = BarChart(xy_dataset_list, title='bar chart', x_label='Temperature', y_label='values')
    report.add_element(bar_chart)

    scatter_plot = ScatterPlot(xy_dataset_list, title='scatter plot', x_label='Temperature', y_label='values')
    report.add_element(scatter_plot)

    heat_map = HeatMap(table_name='OAT_HeatMap', x_column='HourOfDay', y_column='Date', z_column='Temperature')
    report.add_element(heat_map)

    print(report)
