import csv
import posixpath

from rest_framework import serializers
from rest_framework.reverse import reverse

from . import models


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

    def _sniff(self, size=10000):
        '''Detect a header and the dialect within the first size bytes.'''
        self.file.seek(0)
        sample = self.file.read(size)
        try:
            sample = sample.decode(self.encoding)
        except UnicodeDecodeError:
            raise csv.Error('Encountered invalid Unicode character')
        self.file.seek(0)
        sniffer = csv.Sniffer()
        return sniffer.sniff(sample), sniffer.has_header(sample)

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

    def __next__(self):
        return next(self.reader)

    def __iter__(self):
        return self


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        exclude = ('owner',)


# Split file creation from other file operations because the file should
# be unchangeable once it is uploaded and assigned to the user's # project.

class CreateFileSerializer(serializers.ModelSerializer):
    '''Serializer used to create/upload file.
    
    It ensures the file is associated with the appropriate project.
    '''
    class Meta:
        model = models.DataFile
        exclude = ('project',)

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

    def validate_file(self, attrs, source):
        # Only perform this validation when called from our add_file view.
        if self.project is None:
            return attrs
        file = attrs[source].file
        try:
            csv_file = CSVFile(file)
            cols = len(next(csv_file))
            for row in csv_file:
                if len(row) != cols:
                    raise csv.Error('Inconsistent number of columns')
        except csv.Error as e:
            raise serializers.ValidationError(str(e))
        file.seek(0)
        return attrs

    def restore_object(self, attrs, instance=None):
        #if self.project is not None:
        #    attrs['project'] = self.project
        #return super().restore_object(attrs, instance)
        obj = super().restore_object(attrs, instance)
        if self.project is not None:
            obj.project = self.project
        return obj


class FileSerializer(serializers.ModelSerializer):
    '''Serializer for file viewing/modification.

    Only the comments field of the file is updateable. If the request
    attribute is set, download_url will contain an absolute URL.
    '''
    download_url = serializers.CharField(source='pk', read_only=True)
    size = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        model = models.DataFile
        read_only_fields = ('project', 'file')

    def transform_file(self, obj, value):
        return posixpath.basename(value)

    def transform_download_url(self, obj, value):
        return reverse('datafile-download', kwargs={'pk': value},
                       request=getattr(self, 'request', None))

    def transform_size(self, obj, value):
        return obj.file.file.size
