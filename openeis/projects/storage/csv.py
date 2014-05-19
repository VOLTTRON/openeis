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
