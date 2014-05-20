'''Ingest CSV files and parse them according to a sensor defintion.'''

from collections import namedtuple
from datetime import datetime
import json
import os
import sys

import dateutil.parser

from .csv import CSVFile


class OutOfRangeError(ValueError):
    def __init__(self, value, minimum, maximum):
        msg = '{} is out of range [{},{}]'.format(value,
                '' if minimum is None else minimum,
                '' if maximum is None else maximum)
        super().__init__(value, msg)
        self.value = value
        self.minimum = minimum
        self.maximum = maximum


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

    def __init__(self, column, *, formats=(), sep=' ', **kwargs):
        super().__init__(column, **kwargs)
        self.formats = formats
        self.sep = sep

    def __call__(self, row):
        columns = [self.column] if isinstance(self.column, int) else self.column
        raw_value = self.sep.join([row[i].strip() for i in columns])
        if not raw_value.strip():
            return self.default
        for fmt in self.formats:
            try:
                return datetime.strptime(raw_value, fmt)
            except ValueError:
                pass
        try:
            return dateutil.parser.parse(raw_value)
        except (ValueError, TypeError):
            pass
        raise ValueError('invalid timestamp: {!r}'.format(raw_value))

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
            elif prefix == '0o' or isdigit(prefix[1]):
                base = 8
            elif prefix == '0b':
                base = 2
        value = int(raw_value, base)
        if ((self.minimum and value < self.minimum) or
                (self.maximum and value > self.maximum)):
            raise OutOfRangeError(value, self.minimum, self.maximum)
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
        value = float(raw_value)
        if ((self.minimum and value < self.minimum) or
                (self.maximum and value > self.maximum)):
            raise OutOfRangeError(value, self.minimum, self.maximum)
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
            raise ValueError('invalid boolean value: {!r}'.format(raw_value))


Row = namedtuple('Row', 'line_num position columns errors')
ParseError = namedtuple('ParseError', 'line_num column index exc')


def ingest_file(file, columns):
    '''Return a generator to parse a file according to a column map.

    The file should be seekable and opened for reading. columns should
    be a list or tuple of column parser instances. For each row read
    from file, a list of parsed columns is generated in the order they
    were specified in the columns argument and returned in the columns
    attribute of a Row instances. Parse errors will be included in the
    errors attribute. This function will not close the file object.
    '''
    csv_file = CSVFile(file)
    if csv_file.has_header:
        next(csv_file)
    for row in csv_file:
        if not row:
            continue
        line_num = csv_file.reader.line_num
        parsed = []
        errors = []
        for index, col in enumerate(columns):
            try:
                value = col(row)
            except ValueError as e:
                if isinstance(col.column, int):
                    colnum = col.column + 1
                else:
                    colnum = [i + 1 for i in col.column]
                errors.append(ParseError(line_num, colnum, index, e))
                value = None
            parsed.append(value)
        yield Row(line_num, file.tell(), parsed, errors)


def get_sensor_parsers(sensormap):
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
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        'static', 'projects', 'json', 'general_definition.json')
    columns = {name: [(None, DateTimeColumn.data_type,
                     DateTimeColumn(column_number(name, file['timestamp']['columns']),
                                   formats=[file['timestamp'].get('format')]))]
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


IngestFile = namedtuple('IngestFile', 'name size sensors types rows')


def ingest_files(sensormap, files):
    '''Iterate over each file in files to return a file parser iterator.
    
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
    columnmap = get_sensor_parsers(sensormap)
    if hasattr(files, 'items'):
        files = files.items()
    for file_id, file in files:
        try:
            size = file.size
        except AttributeError:
            size = os.stat(file.fileno()).st_size
        names, types, columns = zip(*columnmap[file_id])
        rows = ingest_file(file, columns)
        yield IngestFile(file_id, size, names, types, rows)


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
            for error in row.errors:
                sys.stderr.write(errmsg.format(file, error))
            print(row.columns, row.position * 100 // file.size)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
