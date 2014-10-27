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

import openeis.filters as f
from datetime import timedelta
import abc

@f.register_column_modifier
class RoundOff(f.SimpleRuleIterable):
    def __init__(self, places=0, **kwargs):
        super().__init__(**kwargs)
        self.places = places
    def rule(self, time, value):
        return time, round(value, self.places)

class BaseSimpleNormalize(f.BaseIterable, metaclass=abc.ABCMeta):
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
        
        previous_in_seconds = seconds_from_midnight //  period_seconds
        next_in_seconds = previous_in_seconds + period_seconds
        
        from_midnight =  timedelta(seconds=next_in_seconds)
        return midnight + from_midnight

@f.register_column_modifier    
class LinearInterpolation(BaseSimpleNormalize):
    def calculate_value(self, target_dt):
        x0 = self.previous_point[0]
        x1 = self.next_point[0]
        if x1 <= target_dt <= x0:
            raise RuntimeError('Tried to interpolate value during incorrect state.')
        y0 = self.previous_point[1]
        y1 = self.next_point[1]
        return target_dt, y0 + ((y1-y0)*((target_dt-x0)/(x1-x0)))
    
@f.register_column_modifier     
class Fill(BaseSimpleNormalize):
    def calculate_value(self, target_dt):
        return target_dt, self.previous_point[1]
            