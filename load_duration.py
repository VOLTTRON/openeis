
import argparse
from datetime import datetime
import math
import os
import sys

import numpy
import pandas


def execute(self):
    """ Output is sorted loads values."""

    self.out.log("Starting application: load duration.", logging.INFO)

    self.out.log("Querying database.", logging.INFO)
    load_query = self.inp.get_query_sets('load',
            order_by='value', exclude={'value':None})

    self.out.log("Getting unit conversions.", logging.INFO)
    base_topic = self.inp.get_topics()
    meta_topics = self.inp.get_topics_meta()
    load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
    self.out.log(
        "Convert loads from [{}] to [kW].".format(load_unit),
        logging.INFO
        )
    load_convertfactor = cu.getFactor_powertoKW(load_unit)

    self.out.log("Compiling the report table.", logging.INFO)
    ctr = 1
    for x in load_query[0]:
        self.out.insert_row("Load_Duration", { "sorted load": x[1]*load_convertfactor,
                                               "percent time": (len(load_query[0])-ctr) / len(load_query[0]) } )
        ctr += 1

def load_duration(power):
    pwrcol = power.columns[0]
    power['count'] = 1
    total = len(power)
    def weight(count):
        return count / total
    counts = power.groupby(power.columns[0]).count().apply(weight).sort(
            'count', ascending=False).sort()
    yield from power.groupby(power.columns[0]).count().apply(weight).sort(
            'count', ascending=False).sort().itertuples()


def main(argv):
    parser = argparse.ArgumentParser(
        prog=os.path.basename(argv[0]),
        description='Calculate proportion of time building load is at or '
                    'above a given level',
    )
    parser.add_argument('--power-column', metavar='NUM|NAME', default='2')
    parser.add_argument('--no-header', action='store_true')
    parser.add_argument('datafile')
    parser.add_argument('outfile', nargs='?')
    args = parser.parse_args(argv[1:])
    try:
        args.power_column = int(args.power_column)
    except (TypeError, ValueError):
        pass
    kwargs = {
        'usecols': [args.power_column],
        'header': None if args.no_header else 0,
        'names': ['power'],
    }
    df = pandas.read_csv(args.datafile, header=None if args.no_header else 0,
                         usecols=[args.power_column])
    print('Power column:', df.columns[0])
    out = open(args.outfile, 'w') if args.outfile else sys.stdout
    try:
        out.write('Load,Percent Time\n')
        for row in load_duration(df):
            out.write('{},{}\n'.format(*row))
    finally:
        if args.outfile:
            out.close()


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        pass
