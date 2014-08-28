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

import csv


class CSVFile:
    '''Auto dialect detecting CSV file iterator.

    First, the given file (which must be seekable) is read up to
    sample_size. Then, the dialect is sniffed and used to create a CSV
    reader object. An internal readline method is used to overcome a bug
    in Django's File iterator and to limit the line lengths via the
    max_line_size argument. If the encoding argument is not given, UTF-8
    is used to decode the file. Raises csv.Error for any CSV problems.
    '''
    def __init__(self, file, *, max_line_size=10000,
                 encoding='utf-8', sample_size=10000):
        self.file = file
        self.max_line_size = max_line_size
        self.encoding = 'utf-8'
        self.dialect, self.has_header = self._sniff(sample_size)
        self.reader = csv.reader(self._iterlines(), self.dialect)

    def _sniff(self, size=10000, delimiters=', \t|'):
        '''Detect a header and the dialect within the first size bytes.'''
        self.file.seek(0)
        sample = self.file.read(size)
        try:
            sample = sample.decode(self.encoding)
        except UnicodeDecodeError:
            raise csv.Error('Encountered invalid Unicode character')
        except AttributeError:
            pass
        self.file.seek(0)
        sniffer = csv.Sniffer()
        return sniffer.sniff(sample, delimiters), sniffer.has_header(sample)

    def _iterlines(self):
        '''Iterate over the lines of the file.'''
        readline = self._readline
        while True:
            line = readline()
            if not line:
                return
            yield line

    def _readline(self):
        '''Read a single decoded line from the file.'''
        line = self.file.readline(self.max_line_size)
        if not line:
            return ''
        if not line[-1] == '\n' and len(line) >= self.max_line_size:
            raise csv.Error('Line exceeds maximum size of {}'.format(
                             self.max_line_size))
        try:
            return line.decode(self.encoding)
        except UnicodeDecodeError:
            raise csv.Error('Encountered invalid Unicode character')
        except AttributeError:
            return line

    def __next__(self):
        return next(self.reader)

    def __iter__(self):
        return self
