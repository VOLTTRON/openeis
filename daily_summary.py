
import argparse
from datetime import datetime
import math
import os
import sys

import dateutil.tz
import numpy
import pandas
import pytz


def daily_summary(power, area_sqft):
    loads = power.groupby(lambda dt: dt.date).quantile([0.95, 0.05]).unstack()
    loads_95th = loads[0.95]
    loads_5th = loads[0.05]
    if area_sqft:
        peak_load_intensity = power.max() / area_sqft * 1000
    else:
        peak_load_intensity = 'N/A (requires area)'
    mean_95th = loads_95th.mean()
    mean_5th = loads_5th.mean()
    load_range = (loads_95th - loads_5th).mean()
    load_ratio = (loads_5th / loads_95th).mean()

    hr_variability = []
    for name, group in power.groupby(lambda dt: dt.hour):
        if len(group) < 2:
            continue
        hr_mean = group.mean()
        rootmeansq = math.sqrt(
            sum((x - hr_mean) ** 2 for x in group) / (len(group) - 1))
        hr_variability.append(rootmeansq / hr_mean)
    if len(hr_variability) > 1:
        load_variability = numpy.mean(hr_variability)
    else:
        load_variability = 'N/A (insufficient data)'

    print('Peak load benchmark [W/sf]:', peak_load_intensity)
    print('Daily load 95th percentile [kW]:', mean_95th)
    print('Daily load 5th percentile [kW]:', mean_5th)
    print('Daily load range [kW]:', load_range)
    print('Daily load ratio:', load_ratio)
    print('Load variability:', load_variability)
    #XXX: hour load stat


def main(argv):
    parser = argparse.ArgumentParser(
        prog=os.path.basename(argv[0]),
        description='Report daily metrics for electrical loads',
    )
    parser.add_argument('--date-format', metavar='FORMAT')
    parser.add_argument('--time-zone', metavar='FORMAT')
    parser.add_argument('--power-column', metavar='NUM|NAME', default='2')
    parser.add_argument('--no-header', action='store_true')
    parser.add_argument('--area', metavar='SQFT', type=float)
    parser.add_argument('datafile')
    args = parser.parse_args(argv[1:])
    kwargs = {
        'parse_dates': [0],
        'index_col': 0,
        'header': None if args.no_header else 0,
    }
    if args.date_format:
        def parse_date(s): return datetime.strptime(s, args.date_format)
        kwargs['date_parser'] = parse_date
    if args.time_zone:
        tzinfo = pytz.timezone(args.time_zone)
    else:
        tzinfo = dateutil.tz.tzlocal()
    df = pandas.read_csv(args.datafile, **kwargs).tz_localize(
            'UTC').tz_convert(tzinfo)
    try:
        power_col = df.columns[int(args.power_column) - 2]
    except (TypeError, ValueError, KeyError):
        power_col = args.power_column
    print('Power column:', power_col)
    power = df[power_col]
    daily_summary(power, args.area)


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        pass
