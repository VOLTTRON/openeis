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

from openeis.filters import SimpleRuleFilter, BaseFilter, register_column_modifier
from openeis.core.descriptors import ConfigDescriptor, Descriptor
from datetime import timedelta
import abc

class BaseSimpleNormalize(BaseFilter, metaclass=abc.ABCMeta):
    def __init__(self, period_seconds=60, drop_extra = True, **kwargs):
        super().__init__(**kwargs)
        self.period = timedelta(seconds=period_seconds)
        self.previous_point = None
        self.next_point = None
        self.current_dt = None
        self.drop_extra = drop_extra
    def __iter__(self):
        def generator():
            try:
                iterator = iter(self.parent)
                self.previous_point = self.next_point = next(iterator)
                self.current_dt = self.find_starting_dt(self.previous_point[0])
                while True:
                    while self.next_point[0] <= self.current_dt:
                        self.previous_point = self.next_point
                        self.next_point = next(iterator)

                        if (not self.drop_extra and
                            self.previous_point[0] != self.current_dt):
                            yield self.previous_point

                    if self.previous_point[0] == self.current_dt:
                        yield self.previous_point
                    else:
                        yield self.calculate_value(self.current_dt)

                    self.current_dt += self.period
            except StopIteration:
                pass
        return generator()

    @classmethod
    def filter_type(cls):
        return "fill"

    @abc.abstractclassmethod
    def calculate_value(self, target_dt):
        pass

    def find_starting_dt(self, dt):
        midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_from_midnight = (dt-midnight).total_seconds()
        period_seconds = self.period.total_seconds()

        offset = seconds_from_midnight %  period_seconds

        if not offset:
            return dt

        previous_in_seconds = seconds_from_midnight // period_seconds
        next_in_seconds = previous_in_seconds + period_seconds

        from_midnight =  timedelta(seconds=next_in_seconds)
        return midnight + from_midnight

    @classmethod
    def get_config_parameters(cls):
        return {
                'period_seconds': ConfigDescriptor(int, "Period in second",
                                                   description='Period to of time to normalize to in seconds.',
                                                   value_default=60),
                'drop_extra': ConfigDescriptor(bool, "Drop Extra",
                                               description='Drop values that do no line up exactly with the specified period.',
                                               value_default=True)
                }

class BaseSimpleAggregate(BaseFilter, metaclass=abc.ABCMeta):
    def __init__(self, period_seconds=3600, round_time=False, **kwargs):
        super().__init__(**kwargs)
        self.period = timedelta(seconds=period_seconds)
        self.previous_point = None
        self.next_point = None
        self.current_dt = None
        self.round_time = round_time
        if self.round_time:
            self.half_period = self.period / 2
    def __iter__(self):
        def generator():
            try:
                iterator = iter(self.parent)
                current_point = next(iterator)
            except StopIteration:
                return

            self.init_current_dt(current_point[0])
            value_list = [current_point]

            for dt, value in iterator:
                if not self.update_dt(dt):
                    value_list.append((dt, value))
                else:
                    yield self.old_dt, self.aggregate_values(self.old_dt, value_list)
                    value_list.clear()
                    value_list.append((dt, value))

            if value_list:
                yield self.current_dt, self.aggregate_values(self.current_dt, value_list)

        return generator()

    @classmethod
    def filter_type(cls):
        return "aggregation"

    @abc.abstractclassmethod
    def aggregate_values(self, target_dt, value_list):
        pass

    def update_dt(self, dt):
        self.old_dt = self.current_dt

        if self.round_time:
            while self.current_dt + self.half_period <= dt:
                self.current_dt += self.period
        else:
            while self.current_dt + self.period <= dt:
                self.current_dt += self.period

        return self.old_dt != self.current_dt

    def init_current_dt(self, dt):
        self.current_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        self.update_dt(dt)
        #Make sure old_dt it correct after init.
        self.old_dt = self.current_dt


    @classmethod
    def get_config_parameters(cls):
        return {
                'period_seconds': ConfigDescriptor(int, "Period in second",
                                                   description='Period to of time to normalize to in seconds.',
                                                   value_default=3600),
                'round_time': ConfigDescriptor(bool, "Round Time",
                                               description='Round time to nearest period, otherwise truncate time to period.',
                                               value_default=False)
                }