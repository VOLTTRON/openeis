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

'''Ingest CSV files and parse them according to a sensor defintion.'''

from collections import namedtuple
from datetime import datetime
import json
import os
import sys
import pytz
import dateutil.parser

from .csvfile import CSVFile


class IngestError(ValueError):
    def __init__(self, value, column, exc=None):
        self.value = value
        self.column = column
        msg = self.__class__._fmt.format(self)
        super().__init__(msg, value, column)
        if exc is not None:
            self.__cause__ = exc

    @property
    def column_num(self):
        '''Get the one-based index of the column source(s).'''
        column = self.column.column
        if not isinstance(column, int):
            return [i + 1 for i in column]
        return column + 1

    @property
    def data_type(self):
        return self.column.data_type


class ParseError(IngestError):
    _fmt = 'could not convert string to {0.data_type}: {0.value!r}'

class OutOfRangeError(IngestError):
    _fmt = '{0.value} is out of range [{0._min},{0._max}]'

    @property
    def _min(self):
        return self.column.minimum or ''

    @property
    def _max(self):
        return self.column.maximum or ''


class BaseColumn:
    '''Base class for column parsers.

    Provides default handling of column number and default value as well
    as a repr formatter. Also allows minimum and maximum keyword values
    to be passed through without error. Parsing is performed by calling
    the class instance. The default value is returned if the column is
    blank and a ValueError is raised if parsing fails.
    '''
    def __init__(self, column, *, default=None, minimum=None, maximum=None):
        self.column = column
        self.default = default

    def __repr__(self, *args, **kwargs):
        options = ['']
        if self.default:
            options.append(('default', self.default))
        for name in args:
            attr = getattr(self, name)
            if attr:
                options.append((name, attr))
        options.extend(kwargs.items())
        return '{}({}{})'.format(self.__class__.__name__, self.column,
                                 ', '.join(opt and '{}={!r}'.format(*opt)
                                           for opt in options))


class DateTimeColumn(BaseColumn):
    '''Parse columns of date/time data.

    In this case column can be a single column or a list or tuple of
    columns, in which case the values will be concatenated together
    (separated by sep -- a space by default) before being parsed.
    Multiple formatting strings may be attempted by passing them via the
    formats argument. Final parsing is attempted by dateutil.
    '''

    data_type = 'datetime'

    def __init__(self, column, *, formats=(), sep=' ', tzinfo=pytz.utc, **kwargs):
        super().__init__(column, **kwargs)
        self.formats = formats
        self.sep = sep
        self.tzinfo = tzinfo

    def _ensure_tz(self, dt):
        if not dt.tzinfo and self.tzinfo:
            dt = self.tzinfo.localize(dt)
        return dt.astimezone(pytz.utc)

    def __call__(self, row):
        columns = [self.column] if isinstance(self.column, int) else self.column
        raw_value = self.sep.join([row[i].strip() for i in columns])
        if not raw_value.strip():
            return self.default
        for fmt in self.formats:
            try:
                return self._ensure_tz(datetime.strptime(raw_value, fmt))
            except ValueError:
                pass
        try:
            return self._ensure_tz(dateutil.parser.parse(raw_value))
        except (ValueError, TypeError):
            pass
        return ParseError(raw_value, self)

    def __repr__(self):
        kwargs = {'sep': self.sep} if self.sep != ' ' else {}
        return super().__repr__('formats', **kwargs)


class StringColumn(BaseColumn):
    '''Parse a column as string data (this one is easy).'''

    data_type = 'string'

    def __call__(self, row):
        return row[self.column] or self.default


class IntegerColumn(BaseColumn):
    '''Parse a column as integer data.

    Automatic detection of the numeric base is performed and the value
    is tested against the minimum and maximum, if given.
    '''

    data_type = 'integer'

    def __init__(self, column, *,
                 minimum=None, maximum=None, **kwargs):
        super().__init__(column, **kwargs)
        self.minimum = minimum
        self.maximum = maximum

    def __call__(self, row):
        raw_value = row[self.column]
        if not raw_value:
            return self.default
        base = 10
        if raw_value.startswith('0') and len(raw_value) > 1:
            prefix = raw_value[:2].lower()
            if prefix == '0x':
                base = 16
            elif prefix == '0o' or prefix[1].isdigit():
                base = 8
            elif prefix == '0b':
                base = 2
        try:
            value = int(raw_value, base)
        except ValueError as e:
            return ParseError(raw_value, self)
        if ((self.minimum and value < self.minimum) or
                (self.maximum and value > self.maximum)):
            return OutOfRangeError(value, self)
        return value

    def __repr__(self):
        return super().__repr__('minimum', 'maximum')


class FloatColumn(BaseColumn):
    '''Parse a float column.'''

    data_type = 'float'

    def __init__(self, column, *, minimum=None, maximum=None, **kwargs):
        super().__init__(column, **kwargs)
        self.minimum = minimum
        self.maximum = maximum

    def __call__(self, row):
        raw_value = row[self.column]
        if not raw_value:
            return self.default
        try:
            value = float(raw_value)
        except ValueError as e:
            return ParseError(raw_value, self)
        if ((self.minimum and value < self.minimum) or
                (self.maximum and value > self.maximum)):
            return OutOfRangeError(value, self)
        return value

    def __repr__(self):
        return super().__repr__('minimum', 'maximum')


class BooleanColumn(BaseColumn):
    '''Parse a boolean column.'''

    data_type = 'boolean'
    parse_map = {
        'true': True,
        'yes': True,
        'y': True,
        't': True,

        'false': False,
        'no': False,
        'n': False,
        'f': False
    }

    def __call__(self, row):
        raw_value = row[self.column]
        if not raw_value:
            return self.default
        try:
            return bool(float(raw_value))
        except ValueError:
            pass
        try:
            return self.parse_map[raw_value.strip().lower()]
        except KeyError:
            return ParseError(raw_value, self)


Row = namedtuple('Row', 'line_num position columns')


def ingest_file(file, columns):
    '''Return a generator to parse a file according to a column map.

    The file should be seekable and opened for reading. columns should
    be a list or tuple of column parser instances. For each row read
    from file, a list of parsed columns is generated in the order they
    were specified in the columns argument and returned in the columns
    attribute of a Row instances. Errors are indicated by the column
    value being an instance of IngestError. This function will not close
    the file object.
    '''
    csv_file = CSVFile(file)
    if csv_file.has_header:
        next(csv_file)
    return (Row(csv_file.reader.line_num, file.tell(),
                [col(row) for col in columns]) for row in csv_file if row)


def get_sensor_parsers(sensormap, files):
    '''Generate a mapping of files and sensor paths to columns.

    Returns a dictionary with the files from sensormap['files'] as keys
    and a list of 3-tuples as values, with each tuple containing a
    sensor path, a data type, and a column parser. The first entry in
    the list has a path of None and is the timestamp parser.
    '''

    def column_number(filename, column):
        if isinstance(column, (list, tuple)):
            return [column_number(filename, col) for col in column]
        if isinstance(column, str):
            file = sensormap['files'][filename]
            return file['signature']['headers'].index(column)
        return column

    def get_tz(fileid):
        return pytz.timezone(files[fileid]['time_zone'])

    def date_format(file):
        fmt = file['timestamp'].get('format')
        return [fmt] if fmt else []
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        'static', 'projects', 'json', 'general_definition.json')

    columns = {name: [(None, DateTimeColumn.data_type,
#                     DateTimeColumn(column_number(name, file['timestamp']['columns']),
                    DateTimeColumn(column_number(name, file['timestamp']['columns']),
                                   tzinfo=get_tz(name),
                                   formats=date_format(file)))]
             for name, file in sensormap['files'].items()}
    with open(path) as file:
        prototypes = json.load(file)['sensors']
    for name, sensor in sorted(sensormap['sensors'].items()):
        if 'type' not in sensor:
            continue
        type = sensor['type']
        filename = sensor['file']
        column = column_number(filename, sensor['column'])
        proto = prototypes[type]
        minimum = proto.get('minimum')
        maximum = proto.get('maximum')
        data_type = proto['data_type']
        cls = globals()[data_type.capitalize() + 'Column']
        obj = cls(column, minimum=minimum, maximum=maximum)
        columns[filename].append((name, cls.data_type, obj))
    return columns


IngestFile = namedtuple('IngestFile', 'name size sensors types rows time_zone time_offset')


def ingest_files(sensormap, files):
    '''Iterate over each file_dict in files to return a file parser iterator.

    file_dict is a dictionary with file, time_offset, and time_zone as keys.

    Creates a generator to iterate over each file in files and yield
    IngestFile objects with the following attributes:

      name - File name mapping keys from files to sensormap['files'].
      size - Total size of the file.
      sensors - List of sensor names from sensormap['sensors'].
      types - List of data types to expect in data.
      rows - Iterator to return Row instances of parsed file data.

    There are the same number of elements in sensors, types, and each
    row.columns representing columns of sensors.  The first item in
    sensors, types, and rows.columns is the timestamp and is represented
    by a sensor name of None.
    '''
    columnmap = get_sensor_parsers(sensormap, files)
    if hasattr(files, 'items'):
        files = files.items()
    for file_id, file_dict in files:
        file = file_dict['file']
        time_zone = file_dict['time_zone']
        time_offset = file_dict['time_offset']
        try:
            size = file.size
        except AttributeError:
            size = os.stat(file.fileno()).st_size
        names, types, columns = zip(*columnmap[file_id])
        rows = ingest_file(file, columns)
        yield IngestFile(file_id, size, names, types, rows, time_zone, time_offset)


def main(argv=sys.argv):
    '''Parse input files according to a given sensor map definition.

    The first argument is a sensor map definition file. The remaining
    arguments are name-file pairs mapping the sensor map files to real
    files.
    '''
    def log(name, row, col, exc):
        sys.stderr.write('error: {}:{}:{}: {}\n'.format(name, row, col, exc))
    with open(argv[1]) as file:
        sensormap = json.load(file)
    files = zip(argv[2::2],
                [open(filename, 'rb') for filename in argv[3::2]])
    errmsg = 'error: {0.name}:{1.line_num}:{1.column}[{1.index}]: {1.exc}\n'
    for file in ingest_files(sensormap, files):
        print(file.name)
        print(file.sensors)
        for row in file.rows:
            print(row.columns, row.position * 100 // file.size)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
