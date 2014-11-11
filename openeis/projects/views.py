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

from contextlib import closing
from pytz import timezone
import datetime
import itertools
import json
import logging
import posixpath
import threading
import traceback

import dateutil

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import utc, get_current_timezone

from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, link
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import exceptions as rest_exceptions
from rest_framework.settings import api_settings

from . import models, renderers, serializers
from .models import INFO, WARNING, ERROR, CRITICAL
from .protectedmedia import protected_media, ProtectedMediaResponse
from .conf import settings as proj_settings
from .storage.clone import CloneProject
from .storage.ingest import ingest_files, iter_rows, IngestError
from .storage.sensormap import Schema as Schema
from .storage.db_input import DatabaseInput
from .storage.db_output import DatabaseOutput, DatabaseOutputZip
from openeis.applications import get_algorithm_class
from openeis.applications import _applicationDict as apps
from openeis.filters import apply_filters, column_modifiers


from openeis.projects import version

_logger = logging.getLogger(__name__)


@protected_media
@user_passes_test(lambda user: user.is_staff)
def get_protected_file(request, path):
    '''Handle requests from the admin tool for protected files.'''
    return path


class IsOwner(permissions.BasePermission):
    '''Restrict access to the object owner.'''
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsProjectOwner(permissions.BasePermission):
    '''Restrict access to the owner of the parent project.'''
    def has_object_permission(self, request, view, obj):
        return obj.project.owner == request.user

class IsAuthenticatedOrPost(permissions.BasePermission):
    '''Restrict access to authenticated users or to POSTs.'''
    def has_object_permission(self, request, view, obj):
        return ((request.method == 'POST') ^
                (request.user and request.user.pk is not None))


class ProjectViewSet(viewsets.ModelViewSet):
    '''List all projects owned by the active user.'''

    model = models.Project
    serializer_class = serializers.ProjectSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwner)

    def pre_save(self, obj):
        '''Always set the project owner to the current user.'''
        obj.owner = self.request.user

    def get_queryset(self):
        '''Only allow user to see projects they own.'''
        user = self.request.user
        return user.projects.all()

    @action(methods=['POST'],
            serializer_class=serializers.CreateFileSerializer,
            permission_classes=permission_classes)
    def add_file(self, request, *args, **kwargs):
        '''Always set the owning project when adding files.'''
        project = self.get_object()
        serializer = serializers.CreateFileSerializer(
                project=project, data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            obj = serializer.save(force_insert=True)
            serializer = serializers.FileSerializer(
                    instance=obj, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @link()
    def files(self, request, *args, **kwargs):
        project = self.get_object()
        return HttpResponseRedirect(reverse('datafile-list', request=request) +
                                    '?project={}'.format(project.id))

    @action()
    def clone(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        clone_project = CloneProject()
        clone = clone_project.clone_project(self.get_object(), request.DATA['name'])
        serializer = self.get_serializer(clone)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FileViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    '''List all files owned by the active user.

    project -- Restrict the list to those with the given project ID.
    '''

    model = models.DataFile
    serializer_class = serializers.FileSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectOwner)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('project',)

    def get_queryset(self):
        '''Only allow users to see files they own.'''
        user = self.request.user
        return models.DataFile.objects.filter(project__owner=user)

    def pre_save(self, file):
        '''Check if email changed and that all user fields are valid.'''
        file.full_clean()

    @link()
    def download(self, request, *args, **kwargs):
        '''Retrieve the file.'''
        data_file = self.get_object()
        name = data_file.name.replace('"', '\\"')
        file = data_file.file
        response = ProtectedMediaResponse(file.name)
        response['Content-Type'] = 'text/csv; name="{}"'.format(name)
        response['Content-Disposition'] = 'filename="{}"'.format(name)
        return response

    @link()
    def head(self, request, *args, **kwargs):
        '''Return the first N rows of the file, split into columns.

        If a header row is detected, it does not count towards N.

        N defaults to FILE_HEAD_ROWS_DEFAULT projects setting and can be
        overridden using the rows query parameter. However, rows may not
        exceed FILE_HEAD_ROWS_MAX projects setting.
        '''
        try:
            count = int(request.QUERY_PARAMS['rows'])
        except (KeyError, ValueError):
            count = proj_settings.FILE_HEAD_ROWS_DEFAULT
        count = min(count, proj_settings.FILE_HEAD_ROWS_MAX)
        has_header, rows = self.get_object().csv_head(count)
        return Response({'has_header': has_header, 'rows': rows})


    @link()
    def timestamps(self, request, *args, **kwargs):
        '''Parse the timestamps of the first lines of the file.

        The rows query parameter matches that of top and head. If
        columns is provided, it is a comma separated list of column
        names or 0-based numerical indexes of columns containing the
        timestamp. All portions are concatenated, with a single space
        separating each, and used as the timestamp to be parsed.  If no
        column is given, the first column is used. If datefmt is given,
        it is used to parse the time instead of performing automatic
        parsing.
        '''
        columns = request.QUERY_PARAMS.get('columns', '0').split(',')
        fmt = request.QUERY_PARAMS.get('datefmt')
        count = min(request.QUERY_PARAMS.get(
                     'rows', proj_settings.FILE_HEAD_ROWS_DEFAULT),
                    proj_settings.FILE_HEAD_ROWS_MAX)
        tzinfo = timezone(request.QUERY_PARAMS.get('time_zone', 'UTC'))
        time_offset = float(request.QUERY_PARAMS.get('time_offset', 0))
        has_header, rows = self.get_object().csv_head(count)
        num_columns = len(rows[0])
        headers = rows.pop(0) if has_header else []
        for i, column in enumerate(columns):
            try:
                column = int(column)
            except ValueError:
                if column[:1] in '\'"' and column[:1] == column[-1:]:
                    column = column[1:-1]
                try:
                    column = headers.index(column)
                except ValueError:
                    return Response(
                        {'columns': ['invalid column: {!r}'.format(columns[i])]},
                        status=status.HTTP_400_BAD_REQUEST)
            if not 0 <= column < num_columns:
                return Response(
                    {'columns': ['invalid column: {!r}'.format(columns[i])]},
                    status=status.HTTP_400_BAD_REQUEST)
            columns[i] = column
        parse = ((lambda s: datetime.datetime.strptime(s, fmt))
                 if fmt else dateutil.parser.parse)
        times = []
        for row in rows:
            ts = ' '.join(row[i] for i in columns)
            try:
                dt = parse(ts)
            except (ValueError, TypeError):
                parsed = None
            else:
                if time_offset != 0:
                    dt += datetime.timedelta(seconds=time_offset)
                if not dt.tzinfo:
                    dt = tzinfo.localize(dt)
                parsed = dt.isoformat()
            times.append([ts, parsed])
        return Response(times)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    '''List active users.'''
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.MinimalUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('last_name', 'first_name', 'username')


class AccountViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    '''Create, update, and delete user accounts.'''

    permission_classes = (IsAuthenticatedOrPost,)

    def get_serializer_class(self):
        '''Return appropriate serializer class for POST.'''
        if self.request.method == 'POST':
            return serializers.CreateUserSerializer
        return serializers.UserSerializer

    def get_object(self):
        '''Operate on currently logged in user or raise 404 error.'''
        user = self.request.user
        self.check_object_permissions(self.request, user)
        if user.pk is None:
            raise Http404()
        return user

    def pre_save(self, user):
        '''Check if email changed and that all user fields are valid.'''
        user.full_clean()
        self.verify_email = not User.objects.filter(
                pk=user.pk, email=user.email).exists()

    def post_save(self, user, created=False):
        '''Send email verification if email address changed.'''
        if (created or self.verify_email) and user.email:
            models.AccountVerification.objects.filter(
                    account=user, what='email').delete()
            verify = models.AccountVerification(account=user, what='email')
            verify.save()
            # XXX: The email should come from a template.
            user.email_user('OpenEIS E-mail Verification',
                self.request.build_absolute_uri(reverse('account-verify',
                kwargs={'id': user.id, 'pk': verify.pk, 'code': verify.code})),
                'openeis@pnnl.gov')

    def destroy(self, request, *args, **kwargs):
        '''Request account deletion.'''
        # Rename account and set inactive rather than delete.
        user = self.get_object()
        serializer = serializers.DeleteAccountSerializer(data=request.DATA)
        if serializer.is_valid():
            if user.check_password(serializer.object):
                prefix = datetime.datetime.now().strftime('__DELETED_%Y%m%d%H%M%S%f_')
                user.username = prefix + user.username
                user.is_active = False
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'password': 'Invalid password.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def verify(self, request, *args, id=None, pk=None, code=None, **kwargs):
        '''Verify account update.'''
        get_object_or_404(models.AccountVerification,
                          account__id=id, pk=pk, code=code).delete()
        # XXX: Respond with success page or JS depending on Accept header.
        #      Or perhaps we should redirect to the main app.
        return Response('Verification succeeded. Thank you!')

    @action(methods=['POST'],
            serializer_class=serializers.ChangePasswordSerializer,
            permission_classes=(permissions.IsAuthenticated,))
    def change_password(self, request, *args, **kwargs):
        '''Change user password.'''
        user = self.get_object()
        serializer = serializers.ChangePasswordSerializer(data=request.DATA)
        if serializer.is_valid():
            old, new = serializer.object
            if user.check_password(old):
                user.set_password(new)
                user.save()
                #user.email_user('OpenEIS Account Change Notification',
                #                'Your password changed!', 'openeis@pnnl.gov')
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'old_password': 'Invalid password.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST', 'PUT', 'DELETE'])
    def password_reset(self, request, *args, **kwargs):
        handler = {'POST': self._request_reset,
                   'PUT': self._reset_password,
                   'DELETE': self._clear_reset}[request.method]
        return handler(request, *args, **kwargs)

    def _request_reset(self, request, *args, **kwargs):
        '''Request password reset.'''
        serializer = serializers.ResetRequestSerializer(data=request.DATA)
        if serializer.is_valid():
            username_or_email = serializer.object
            query = Q(username=username_or_email) | Q(email=username_or_email)
            user = get_object_or_404(models.User, query)
            models.AccountVerification.objects.filter(
                    account=user, what='password-reset').delete()
            verify = models.AccountVerification(
                    account=user, what='password-reset')
            verify.save()
            # XXX: The email should come from a template.
            user.email_user('OpenEIS Account Reset Verification',
                            'Username: {}\nCode: {}'.format(
                                    user.username, verify.code),
                            'openeis@pnnl.gov')
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _reset_password(self, request, *args, **kwargs):
        '''Reset user password.'''
        serializer = serializers.PasswordResetSerializer(data=request.DATA)
        if serializer.is_valid():
            username, code, password = serializer.object
            user = get_object_or_404(models.User, username=username)
            verify = get_object_or_404(models.AccountVerification, account=user,
                                       what='password-reset', code=code)
            user.set_password(password)
            user.save()
            verify.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _clear_reset(self, request, *args, **kwargs):
        '''Clear password reset request.'''
        user = self.get_object()
        models.AccountVerification.objects.filter(
                account=user, what='password-reset').delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'],
            serializer_class=serializers.LoginSerializer)
    def login(self, request, *args, **kwargs):
        '''Create or delete cookie-based session.'''
        if request.method == 'DELETE':
            logout(request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = serializers.LoginSerializer(data=request.DATA)
        if serializer.is_valid():
            username, password = serializer.object
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response({'detail': 'Account is disabled.'},
                                status=status.HTTP_403_FORBIDDEN)
            return Response({'detail': 'Invalid username/password.'},
                            status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataMapViewSet(viewsets.ModelViewSet):
    '''Manipulate all data maps owned by the active user.'''

    model = models.DataMap
    serializer_class = serializers.DataMapSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectOwner)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('project', 'name')

    def get_queryset(self):
        '''Only allow users to see data maps they own.'''
        user = self.request.user
        return models.DataMap.objects.filter(project__owner=user, removed=False)

    def pre_save(self, obj):
        '''Check the project owner against the current user.'''
        if obj.project.owner != self.request.user:
            raise rest_exceptions.PermissionDenied(
                    "Invalid project pk '{}' - "
                    'permission denied.'.format(obj.project.pk))

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateDataMapSerializer
        obj = getattr(self, 'object', None)
        if obj and obj.datasets.exists() or hasattr(self, 'object_list'):
            return serializers.ReadOnlyDataMapSerializer
        return serializers.DataMapSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.datasets.exists():
            obj.removed = True
            obj.save()
        else:
            obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


_ingest_processes = {}

def iter_ingest(ingest):
    '''Ingest into the common schema tables from the DataFiles.'''
    datamap = ingest.map.map
    files = {f.name: {'file': f.file.file.file,
                      'time_offset':f.file.time_offset,
                      'time_zone': f.file.time_zone}
             for f in ingest.files.all()}
    ingest_file = None
    try:
        ingested = list(ingest_files(datamap, files))
        total_bytes = sum(file.size for file in ingested)
        processed_bytes = 0.0
        for file in ingested:
            sensors = []
            for i, name in enumerate(file.sensors):
                if name is None:
                    continue
                sensor, created = models.Sensor.objects.get_or_create(
                        map=ingest.map, name=name)
                if created:
                    sensor.data_type = file.types[i][0]
                    sensor.save()
                sensors.append((sensor, sensor.data_class))
            ingest_file = ingest.files.get(name=file.name)
            for row in file.rows:
                time = row.columns[0]
                objects = []
                if isinstance(time, IngestError):
                    obj = models.SensorIngestLog(
                            dataset=ingest, file=ingest_file,
                            row=row.line_num, column=time.column_num,
                            level=models.ERROR,
                            message=str(time))
                    objects.append(obj)
                else:
                    for (sensor, cls), column in zip(sensors, row.columns[1:]):
                        if isinstance(column, IngestError):
                            obj = models.SensorIngestLog(
                                    dataset=ingest, file=ingest_file,
                                    row=row.line_num, column=column.column_num,
                                    level=models.ERROR,
                                    message=str(column))
                        else:
                            obj = cls(ingest=ingest, sensor=sensor, time=time,
                                      value=column)
                        objects.append(obj)
                yield (objects, file.name, row.position, file.size,
                       processed_bytes + row.position, total_bytes)
            processed_bytes += file.size
    except Exception:
        models.SensorIngestLog.objects.create(dataset=ingest, file=ingest_file,
                                      row=0, column=0,
                                      level=models.CRITICAL,
                                      message='an unhandled server error '
                                              'occurred during ingestion')
        raise


def _update_ingest_progress(ingest_id, file_id, pos, size, processed, total):
    _ingest_processes[ingest_id] = {
        'id': ingest_id,
        'status': 'processing',
        'percent': processed * 100.0 / total if total else 0.0,
        'current_file_percent': pos * 100.0 / size if size else 0.0,
        'current_file': file_id,
    }


def perform_ingestion(ingest, batch_size=999, report_interval=1000):
    '''Iterate over ingested objects, saving in batches.

    Once batch_size objects are cached, they are sorted according to
    class type and inserted using bulk_create. Progress information
    is updated every report_interval objects.
    '''
    beforeIteration = True
    try:
        last_file_id, next_pos = None, 0
        keyfunc = lambda obj: obj.__class__.__name__
        it = iter_ingest(ingest)
        beforeIteration = False
        while True:
            batch = []
            for objects, *args in it:
                batch.extend(objects)
                file_id, pos, *_ = args
                if file_id != last_file_id:
                    _update_ingest_progress(ingest.id, *args)
                    last_file_id, next_pos = file_id, report_interval
                elif pos >= next_pos:
                    _update_ingest_progress(ingest.id, *args)
                    next_pos = pos + report_interval
                if len(batch) >= batch_size:
                    break
            if not batch:
                break
            batch.sort(key=keyfunc)
            for class_name, group in itertools.groupby(batch, keyfunc):
                objects = list(group)
                cls = objects[0].__class__
                cls.objects.bulk_create(objects)
    except Exception as e:
        if beforeIteration:
            models.SensorIngestLog(level=CRITICAL, dataset=ingest, message='an unhandled exception occurred during sensor '
                          'ingestion ({}) the message was: {}'.format(ingest.id, e), row=-1).save()
        else:
            models.SensorIngestLog(level=CRITICAL, dataset=ingest, message=str(e), row=-1).save()
        logging.exception('an unhandled exception occurred during sensor '
                          'ingestion ({})'.format(ingest.id))
    finally:
        ingest.end = datetime.datetime.utcnow().replace(tzinfo=utc)
        ingest.save()
        _ingest_processes.pop(ingest.id, None)


class DataSetViewSet(viewsets.ModelViewSet):
    model = models.SensorIngest
    permission_classes = (permissions.IsAuthenticated, IsProjectOwner)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('project', 'name')

    @link(permission_classes = (permissions.IsAuthenticated,))
    def status(self, request, *args, **kwargs):
        ingest = self.get_object()
        try:
            process = _ingest_processes[ingest.id]
        except KeyError:
            process = {
                'id': ingest.id,
                'status': 'complete' if ingest.end else 'incomplete',
                'percent': 100.0,
                'current_file_percent': 0.0,
                'current_file': None
            }
        return Response(process)

    @link()
    def errors(self, request, *args, **kwargs):
        '''Retrieves all errors that occured during an ingestion.'''
        ingest = self.get_object()
        errors = ingest.logs.all()
        if not ingest.end and ingest.id not in _ingest_processes:
            error = models.SensorIngestLog(dataset=ingest, level=models.CRITICAL,
               message='Processing ended prematurely. Not all files and/or '
                       'records were read. Please delete this dataset and '
                       'retry. If you continue to have problems, please '
                       'contact technical support.')
            errors = itertools.chain((error,), errors)
        serializer = serializers.SensorIngestLogSerializer(errors, many=True)
        return Response(serializer.data)

    def pre_save(self, obj):
        '''Check the project owner against the current user.'''
        if obj.map.project.owner != self.request.user:
            raise rest_exceptions.PermissionDenied(
                    "Invalid map pk '{}' - "
                    'permission denied.'.format(obj.map.pk))
        obj.project = obj.map.project

    def post_save(self, obj, created):
        '''After the SensorIngest object has been saved start a threaded
        data ingestion process.
        '''
        if created:
            _update_ingest_progress(obj.id, None, 0, 0, 0, 0)
            threading.Thread(
                    target=perform_ingestion, args=(obj,), daemon=True).start()

    def get_queryset(self):
        '''Only allow users to see ingests they own.'''
        user = self.request.user
        queryset = models.SensorIngest.objects.filter(map__project__owner=user)
        try:
            project = int(self.request.QUERY_PARAMS['project'])
        except KeyError:
            return queryset
        except ValueError:
            return []
        return queryset.filter(map__project=project)

    def get_serializer_class(self):
        if self.action=='manipulate':
            return serializers.DataSetManipulateSerializer
        if self.request.method == 'POST':
            return serializers.SensorIngestCreateSerializer
        return serializers.SensorIngestSerializer

    def _parse_int_or_datetime(self, value):
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return dateutil.parser.parse(value)
            except (ValueError, TypeError):
                return None

    @link(
        renderer_classes=([renderers.CSVRenderer] +
            api_settings.DEFAULT_RENDERER_CLASSES)
    )
    def download(self, request, *args, **kwargs):
        '''Retrieve the data set.

        start -- integer or datetime indicating the start row or time.
        end -- integer or datetime indicating the end time or row count.
        format -- string indicating download format: csv, json, etc.

        The Accept HTTP request header can also be set to indicate the
        desired response format (defaults to text/csv).
        '''
        dataset = self.get_object()
        start = self._parse_int_or_datetime(request.QUERY_PARAMS.get('start'))
        end = self._parse_int_or_datetime(request.QUERY_PARAMS.get('end'))
        rows = dataset.merge(start=start, end=end)
        if request.accepted_renderer.format == 'csv':
            response = renderers.StreamingCSVResponse(rows)
            response['Content-Type'] = 'text/csv; name="dataset.csv"'
            response['Content-Disposition'] = 'attachment; filename="dataset.csv"'
        else:
            response = Response(rows)
        return response

    @link()
    def head(self, request, *args, **kwargs):
        try:
            count = int(request.QUERY_PARAMS['rows'])
        except (KeyError, ValueError):
            count = proj_settings.FILE_HEAD_ROWS_DEFAULT
        count = min(count, proj_settings.FILE_HEAD_ROWS_MAX)
        dataset = self.get_object()
        rows = dataset.merge()
        result = {'cols': [], 'rows': [], 'extra_rows': []}
        result['cols'] = rows.__next__()
        d = {}
        for col_index, col_value in enumerate(result['cols']):
            d[col_index] = False
        for row in rows:
            if len(result['rows']) < count:
                   result['rows'].append(row)
                   for col_index,col_value in  enumerate(row):
                       if d[col_index] == False and col_value is not None:
                           d[col_index] = True
            else:
                for col_index in d.keys():
                    if d[col_index] == False and row[col_index] is not None:
                        result['extra_rows'].append(row)
                        d[col_index] = True
        return Response(result)
    
    @action(methods=['POST'],
            serializer_class=serializers.DataSetManipulateSerializer,
            permission_classes=permission_classes)
    def manipulate(self, request, *args, **kargs):
        
        def _iter_data(sensordata):
            for data in sensordata:
                yield data.time, data.value
        
        #request_data = "{\"config\": [[\"pnnl/isb2/OutdoorAirTemperature\", \"LinearInterpolation\", \
        #{\"period_seconds\": 300, \"drop_extra\": false}],[\"pnnl/isb2/OutdoorAirTemperature\", \"RoundOff\", {\"places\": 2}]]}";
        #config_string = json.loads(request_data)
        #print(config_string['config'])*/
        serializer = serializers.DataSetManipulateSerializer(data=request.DATA)
        if serializer.is_valid():
            dataset_id = self.get_object().id
            config = serializer.object['config']
            sensoringest = models.SensorIngest.objects.get(pk=dataset_id)
            datamap = sensoringest.map
            sensors = list(datamap.sensors.all())
            sensor_names = [s.name for s in sensors]
            sensordata = [sensor.data.filter(ingest=sensoringest) for sensor in sensors]
            generators = {} 
            for name, qs in zip(sensor_names, sensordata):
                #TODO: Add data type from schema
                value = {"gen":_iter_data(qs),
                         "type":None}
                generators[name] = value
                
            generators, errors = apply_filters(generators, config)
            
            if errors:
                print('Errors:')
                return Response(errors, status.HTTP_400_BAD_REQUEST)
            
            datamap.id = None 
            datamap.name = datamap.name+' version - '+str(datetime.datetime.now())
            datamap.save()
            
            sensoringest.name = str(sensoringest.id) + ' - '+str(datetime.datetime.now())
            sensoringest.id = None
            sensoringest.map = datamap
            sensoringest.save()
            
            for sensor in sensors:
                sensor.id= None
                sensor.map = datamap
                sensor.save()
                data_class = sensor.data_class
                generator = generators[sensor.name]['gen']
                sensor_data_list = []
                for time,value in generator:
                    sensor_data = data_class(sensor=sensor, ingest=sensoringest,
                                             time=time, value=value)
                    sensor_data_list.append(sensor_data)
                    if len(sensor_data_list) >= 1000:
                        data_class.objects.bulk_create(sensor_data_list)
                        sensor_data_list = []
                if sensor_data_list:
                    data_class.objects.bulk_create(sensor_data_list)
                    
            
            return Response(datamap.id)
        
        else:
            return Response("Not a valid config", status.HTTP_400_BAD_REQUEST)
            


def preview_ingestion(datamap, input_files, count=15):
    '''Given a datamap instance and input_file mapping, generate a preview
    of the dataset. Up to count rows will be included.'''

    def _iter_rows(file):
        '''Alternate between returning the time of the current row and
        the row values, if the times match, or a row of Nones otherwise.
        Works with _merge() below to merge multiple files into one stream.
        '''
        empty = [None] * (len(file.sensors) - 1)
        for timestamp, *values in iter_rows(file):
            while True:
                time = (yield timestamp)
                if timestamp == time:
                    yield values
                    break
                yield empty
        while True:
            yield None
            yield empty
    def _merge(iterators):
        '''Given a list of _iter_rows() generators, iteratively collect
        the next lowest timestamp and use it to merge matching rows from
        each file. Basically turns two streams like this:
        
                      STREAM 1                          STREAM 2
                  time          c1.1  c1.2          time          c2.1  c2.2
          ====================  ====  ====  ====================  ====  ====
          2014-02-01T18:00:00Z  43.1  5     2014-02-01T18:00:30Z  58.2  1
          2014-02-01T18:01:00Z  41.2  4     2014-02-01T18:01:00Z  58.3  2
          2014-02-01T18:02:00Z  50.6  3     2014-02-01T18:01:30Z  58.8  3
          2014-02-01T18:03:00Z  43.4  2     2014-02-01T18:02:00Z  58.1  4

        into a single stream like this:

                  time          c1.1  c1.2  c2.1  c2.2
          ====================  ====  ====  ====  ====
          2014-02-01T18:00:00Z  43.1     5  None  None
          2014-02-01T18:00:30Z  None  None  58.2     1
          2014-02-01T18:01:00Z  41.2     4  58.3     2
          2014-02-01T18:01:30Z  None  None  58.8     3
          2014-02-01T18:02:00Z  50.6     3  58.1     4
          2014-02-01T18:03:00Z  43.4     2  None  None
        '''
        while True:
            try:
                time = min(t for t in (next(i) for i in iterators) if t)
            except ValueError:
                break
            row = [time]
            for line in [i.send(time) for i in iterators]:
                row.extend(line)
            yield row
    inputs = {f.name: {'file': f.file.file.file,
                       'time_zone': f.file.time_zone,
                       'time_offset': f.file.time_offset}
              for f in input_files}
    headers, iterators, rows, extras = ['time'], [], [], []
    for file in ingest_files(datamap, inputs):
        headers.extend(file.sensors[1:])
        iterators.append(_iter_rows(file))
    generator = _merge(iterators)
    # Get the requested number of rows
    for _ in range(count):
        try:
            row = next(generator)
        except StopIteration:
            break
        rows.append(row)
    if not rows:
        # All rows are missing
        missing = list(range(len(headers)))
    else:
        missing = [i for i, col in enumerate(zip(*rows))
                   if all(val is None for val in col)]
    # Get at least one value for each column, if possible
    while missing:
        try:
            row = next(generator)
        except StopIteration:
            break
        if any(row[i] for i in missing):
            extras.append(row)
            missing = [i for i in missing if row[i] is None]
    result = {'cols': headers, 'rows': rows}
    if extras:
        result['extra_rows'] = extras
    return result


class DataSetPreviewViewSet(viewsets.GenericViewSet):
    '''Return sample rows from DataSet ingestion.

    If map has a property of 'id' or map is an integer, then the map with
    the given ID is retreived from the database and used (if owned by the
    current user).  Otherwise, map should be a valid data map definition and
    will be validated before processing continues. Set rows to change the
    number of rows returned for each file.
    '''

    serializer_class = serializers.DataSetPreviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def preview(self, request, *args, **kwargs):
        serializer = serializers.DataSetPreviewSerializer(data=request.DATA)
        if serializer.is_valid():
            user = self.request.user
            obj = serializer.object
            datamap = obj['map']
            if isinstance(datamap, int):
                datamap = get_object_or_404(models.DataMap,
                                  pk=datamap, project__owner=user).map
            elif 'id' in datamap:
                datamap = get_object_or_404(models.DataMap,
                                  pk=datamap['id'], project__owner=user).map
            else:
                schema = Schema()
                errors = schema.validate(datamap)
                if errors:
                    return Response({('map' + ''.join('[{!r}]'.format(name)
                                      for name in path)): value
                                     for path, value in errors.items()},
                                   status=status.HTTP_400_BAD_REQUEST)

            files = obj['files']
            for file in files:
                if file.file.project.owner != user:
                    raise rest_exceptions.PermissionDenied()
            count = min(obj.get('rows', proj_settings.FILE_HEAD_ROWS_DEFAULT),
                        proj_settings.FILE_HEAD_ROWS_MAX)
            result = preview_ingestion(datamap, files, count=count)
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplicationViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kw):
        '''Return list of applications with inputs and parameters.'''
        app_list = []
        for app_id, app in apps.items():
            app_list.append(serializers.ApplicationSerializer(app).data)
            app_list[-1]['id'] = app_id
            if app.get_self_descriptor():
                app_list[-1]['name'] = app.get_self_descriptor().name
                app_list[-1]['description'] = app.get_self_descriptor().description
        return Response(app_list)
    
class FilterViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    
    def list(self, request, *args, **kargs):
        '''Return list of filters with parameters.'''
        filter_list = []
        for filter_id, filter_ in column_modifiers.items():
            # Filter has __iter__ method, many has to be set as False otherwise it will crash
            filter_list.append(serializers.ConfigurableObjectSerializer(filter_, many=False).data)
            filter_list[-1]['id'] = filter_id
            if filter_.get_self_descriptor():
                filter_list[-1]['name'] = filter_.get_self_descriptor().name
                filter_list[-1]['description'] = filter_.get_self_descriptor().description
        return Response(filter_list)


_analysis_processes = set()

def _perform_analysis(analysis):
    '''Create thread for individual runs of an applicaton.'''
    try:
        analysis.started = datetime.datetime.utcnow().replace(tzinfo=utc)
        analysis.save()
        try:
            db_input = DatabaseInput(analysis.dataset.map.id,
                    analysis.configuration["inputs"], analysis.dataset.id)
            klass = get_algorithm_class(analysis.application)
            output_format = klass.output_format(db_input)
            kwargs = analysis.configuration['parameters']
            #if analysis.debug:
            db_output = DatabaseOutputZip(analysis, output_format, analysis.configuration)
            #else:
            #    db_output = DatabaseOutput(analysis, output_format)

            try:
                app = klass(db_input, db_output, **kwargs)
                app.run_application()
                analysis.reports = [serializers.ReportSerializer(report).data
                                    for report in klass.reports(output_format)]
            except Exception:
                db_output.appenFileToZip("stackTrace.txt", traceback.format_exc())
        finally:
            analysis.ended = datetime.datetime.utcnow().replace(tzinfo=utc)
            analysis.save()
    except Exception:
        # TODO: log errors
        print(traceback.format_exc())
    finally:
        _analysis_processes.discard(analysis.id)


def _get_output_data(request, analysis):
    output_name = request.QUERY_PARAMS.get('output', False)
    start = max(int(request.QUERY_PARAMS.get('start', 0)), 0)
    try:
        end = start + int(request.QUERY_PARAMS['count'])
    except (KeyError, ValueError):
        end = None

    if not output_name:
        outputs = {}

        for output in models.AppOutput.objects.filter(analysis=analysis):
            data_model = output.get_data_model()
            outputs[output.name] = {
                'rows': data_model.objects.count()
            }

        return Response(outputs)

    output = models.AppOutput.objects.get(analysis=analysis, name=output_name)
    data_model = output.get_data_model()

    start = max(start, 0)
    rows = data_model.objects.all()[start:end]

    # TODO: return JSON or CSV file as StreamingHTTPResponse instead
    data_response = []
    for row in rows:
        data_response.append({field: getattr(row, field) for field in output.fields})

    return Response(data_response)


class AnalysisViewSet(viewsets.ModelViewSet):
    model = models.Analysis
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            # Use different serializer to allow updates (e.g. renaming) but not
            # allow updates to dataset, application, and configuration fields
            return serializers.AnalysisUpdateSerializer
        return serializers.AnalysisSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['is_alive'] = lambda obj_id: obj_id in _analysis_processes
        return context

    def pre_save(self, obj):
        '''Check dataset ownership and application existence.'''
        if self.request.method == 'POST':
            if obj.dataset.project.owner != self.request.user:
                raise rest_exceptions.PermissionDenied(
                        "Invalid project pk '{}' - "
                        'permission denied.'.format(obj.project.pk))
            obj.project = obj.dataset.project
        if not get_algorithm_class(obj.application):
            raise rest_exceptions.ParseError(
                "Application '{}' not found.".format(obj.application))
        # TODO: validate dataset and application compatibility

    def post_save(self, obj, created):
        '''Start application run after Analysis object has been saved.'''
        if created:
            _analysis_processes.add(obj.id)
            threading.Thread(
                    target=_perform_analysis, args=(obj,), daemon=True).start()

    def get_queryset(self):
        '''Only show user analyses associated with projects they own,
        optionally filtered by project ID.'''
        queryset = models.Analysis.objects.filter(project__owner=self.request.user)
        try:
            project = int(self.request.QUERY_PARAMS['project'])
        except KeyError:
            return queryset
        except ValueError:
            return []
        return queryset.filter(project=project)

    @link()
    def data(self, request, *args, **kw):
        return _get_output_data(request, self.get_object())

    @link()
    def download(self, request, *args, **kwargs):
        '''Retrieve the debug zip file.'''
        analysis = self.get_object()
        path = posixpath.join('analysis', '{}.zip'.format(analysis.pk))
        response = ProtectedMediaResponse(path)
        response['Content-Type'] = 'application/zip; name="analysis-debug.zip"'
        response['Content-Disposition'] = 'filename="analysis-debug.zip"'
        return response


class SharedAnalysisPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS or
                request.user.is_authenticated())

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS or
                obj.analysis.project.owner==request.user)


class SharedAnalysisViewSet(mixins.CreateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.ReadOnlyModelViewSet):
    model = models.SharedAnalysis
    serializer_class = serializers.SharedAnalysisSerializer
    permission_classes = (SharedAnalysisPermission,)

    def get_queryset(self):
        try:
            key = self.request.QUERY_PARAMS['key']
            return models.SharedAnalysis.objects.filter(key=key)
        except (KeyError):
            pass

        user = self.request.user
        if not user.is_authenticated():
            return []

        return models.SharedAnalysis.objects.filter(analysis__dataset__map__project__owner=user)

    def pre_save(self, obj):
        '''Check analysis ownership.'''
        if obj.analysis.project.owner != self.request.user:
            raise rest_exceptions.PermissionDenied(
                    "Invalid analysis pk '{}' - "
                    'permission denied.'.format(obj.analysis.pk))

    @link()
    def data(self, request, *args, **kw):
        return _get_output_data(request, self.get_object().analysis)
