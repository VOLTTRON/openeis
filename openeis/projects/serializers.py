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
import posixpath

from rest_framework import serializers
from rest_framework.reverse import reverse

from .storage.csvfile import CSVFile
from . import models


class JSONField(serializers.CharField):
    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


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

    name = serializers.CharField(required=False)
    timestamp = JSONField(required=False)

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
        except csv.Error as e:
            raise serializers.ValidationError(str(e))
        file.seek(0)
        return attrs

    def validate_name(self, attrs, source):
        if not attrs.get(source):
            attrs[source] = getattr(attrs.get('file'), 'name', '')
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
    timestamp = JSONField(required=False)
    download_url = serializers.CharField(source='pk', read_only=True)
    size = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        model = models.DataFile
        read_only_fields = ('project',)
        exclude = ('file',)

    def transform_download_url(self, obj, value):
        return reverse('datafile-download', kwargs={'pk': value},
                       request=getattr(self, 'request', None))

    def transform_size(self, obj, value):
        return obj.file.file.size


class MinimalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ('id', 'username', 'last_name', 'first_name')


class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccountVerification
        fields = ('id', 'initiated', 'what')


class UserSerializer(serializers.ModelSerializer):
    verifications = VerificationSerializer(source='accountverification_set',
                                           many=True, read_only=True)

    class Meta:
        model = models.User
        fields = ('id', 'username', 'email', 'last_name', 'first_name',
                  'date_joined', 'last_login', 'groups', 'verifications')
        read_only_fields = ('username', 'last_login', 'date_joined', 'groups')


class CreateUserSerializer(UserSerializer):
    password = serializers.CharField(required=True, write_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('password',)
        read_only_fields = UserSerializer.Meta.read_only_fields[1:]

    def restore_object(self, attrs, instance=None):
        password = attrs.pop('password', None)
        instance = super().restore_object(attrs, instance)
        if password:
            instance.set_password(password)
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def restore_object(self, attrs, instance=None):
        return (attrs.get('old_password', instance and instance[0]),
                attrs.get('new_password', instance and instance[1]))


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, write_only=True)

    def restore_object(self, attrs, instance=None):
        return attrs.get('password', instance)


class ResetRequestSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)

    def restore_object(self, attrs, instance=None):
        return attrs.get('username_or_email', instance)


class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    code = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def restore_object(self, attrs, instance=None):
        return (attrs.get('username', instance and instance[0]),
                attrs.get('code', instance and instance[1]),
                attrs.get('password', instance and instance[2]))


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def restore_object(self, attrs, instance=None):
        return (attrs.get('username', instance and instance[0]),
                attrs.get('password', instance and instance[1]))


class CreateDataMapSerializer(serializers.ModelSerializer):
    map = JSONField()
    class Meta:
        model = models.DataMap

class DataMapSerializer(serializers.ModelSerializer):
    map = JSONField()
    class Meta:
        model = models.DataMap
        read_only_fields = ('project',)

class ReadOnlyDataMapSerializer(DataMapSerializer):
    map = JSONField(read_only=True)


class SensorIngestFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SensorIngestFile
        fields = ('name', 'file')


class SensorIngestLogSerializer(serializers.ModelSerializer):
    file = serializers.CharField(source='file.name', read_only=True)

    class Meta:
        model = models.SensorIngestLog
        fields = ('file', 'message', 'level', 'column', 'row' )


class SensorIngestCreateSerializer(serializers.ModelSerializer):

    files = SensorIngestFileSerializer(many=True, required=True)

    class Meta:
        model = models.SensorIngest
        read_only_fields = ('start', 'end', 'project')

    def validate(self, attrs):
        map = attrs['map'].map
        map_files = set(map['files'].keys())
        files = {f.name for f in attrs['files']}
        missing = map_files - files
        errors = []
        if missing:
            errors.append('missing file(s): {!r}'.format(list(missing)))
        extra = files - map_files
        if extra:
            errors.append('extra file(s): {!r}'.format(list(extra)))
        # XXX: check for duplicate DataFiles
        # XXX: check that file signatures match
        if errors:
            raise serializers.ValidationError({'files': errors})
        return attrs

    def to_native(self, obj):
        result = super().to_native(obj)
        if obj and result:
            result['datamap'] = obj.map.map
        return result


class SensorIngestSerializer(serializers.ModelSerializer):

    files = SensorIngestFileSerializer(many=True, read_only=True)

    class Meta:
        model = models.SensorIngest
        read_only_fields = ('start', 'end', 'project', 'map')

    def validate(self, attrs):
        # Empty names slipped by with PATCH, so catch them here.
        if not attrs['name']:
            raise serializers.ValidationError(
                {'name': ['This field is required.']})
        return attrs

    def to_native(self, obj):
        result = super().to_native(obj)
        result['datamap'] = obj.map.map
        return result


class DataSetPreviewSerializer(serializers.Serializer):
    map = JSONField(required=True)
    files = SensorIngestFileSerializer(many=True, required=True)
    rows = serializers.IntegerField(required=False)


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Analysis
        read_only_fields = ('added', 'started', 'ended', 'progress_percent',
                            'reports', 'status', 'project')

class AnalysisUpdateSerializer(AnalysisSerializer):
    class Meta:
        model = AnalysisSerializer.Meta.model
        read_only_fields = (('dataset', 'application', 'configuration') +
                            AnalysisSerializer.Meta.read_only_fields)


class SharedAnalysisSerializer(serializers.ModelSerializer):
    analysis = serializers.PrimaryKeyRelatedField()
    name = serializers.CharField(source='analysis.name', read_only=True)
    reports = serializers.CharField(source='analysis.reports', read_only=True)

    class Meta:
        model = models.SharedAnalysis
        read_only_fields = ('key',)


class ApplicationSerializer(serializers.Serializer):
    parameters = serializers.SerializerMethodField('_get_parameters')
    inputs = serializers.SerializerMethodField('_get_inputs')

    def _convert_parameter(self, parameter):
        parameter.config_type = parameter.config_type.__name__
        return parameter.__dict__

    def _get_parameters(self, obj):
        return {k: self._convert_parameter(v) for k, v in
                obj.get_config_parameters().items()}

    def _get_inputs(self, obj):
        return {k: v.__dict__ for k, v in obj.required_input().items()}


class ReportSerializer(serializers.Serializer):
    description = serializers.CharField()
    elements = serializers.SerializerMethodField('_get_elements')

    def _get_elements(self, obj):
        elements = []
        for element in obj.elements:
            elements.append(element.__dict__)
            elements[-1]['type'] = type(element).__name__
            if 'xy_dataset_list' in elements[-1]:
                elements[-1]['xy_dataset_list'] = [dataset.__dict__ for dataset
                                                   in element.xy_dataset_list]
        return elements
