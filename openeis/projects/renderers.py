
import csv
from io import StringIO

from django.http import StreamingHttpResponse

from rest_framework import renderers


class CSVRenderer(renderers.BaseRenderer):
    '''Renders 2-dimensional lists to CSV.'''
    
    media_type = 'text/csv'
    format = 'csv'
    dialect = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        '''Render `data` to serialized CSV.'''
        if data is None:
            return ''
        stream = StringIO()
        writer = csv.writer(stream, dialect=self.dialect)
        for row in data:
            writer.writerow(row)
        result = stream.getvalue()
        stream.close()
        return result


class CSVStreamer:
    '''Iterate over rows, generating valid CSV.'''

    def __init__(self, rows, dialect=None):
        self.rows = iter(rows)
        self.writer = csv.writer(self, dialect=dialect)

    def __iter__(self):
        return self

    def __next__(self):
        row = next(self.rows)
        self.writer.writerow(row)
        return self.row

    def write(self, row):
        self.row = row


class StreamingCSVResponse(StreamingHttpResponse):
    def __init__(self, rows, *args, dialect=None, **kwargs):
        super().__init__(CSVStreamer(rows, dialect=dialect), *args, **kwargs)
