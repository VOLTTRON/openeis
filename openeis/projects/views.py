from contextlib import closing
import datetime
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

from . import models
from .protectedmedia import protected_media, ProtectedMediaResponse
from . import serializers
from .conf import settings as proj_settings
from .storage.ingest import ingest_files, IngestError, BooleanColumn, DateTimeColumn, FloatColumn, StringColumn, IntegerColumn


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

class IsSensorMapDefOwner(permissions.BasePermission):
    '''Restrict access to the owner of the parent project.'''
    def has_object_permission(self, request, view, obj):
        return obj.map.project.owner == request.user

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
            serializer = serializers.FileSerializer(instance=obj)
            serializer.request = request
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @link()
    def files(self, request, *args, **kwargs):
        project = self.get_object()
        return HttpResponseRedirect(reverse('datafile-list', request=request) +
                                    '?project={}'.format(project.id))


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

    def get_serializer(self, *args, **kwargs):
        '''Set the request member on the serializer.

        This allows the serializer to generate absolute URIs to files.
        '''
        result = super().get_serializer(*args, **kwargs)
        result.request = self.request
        return result

    @link()
    def download(self, request, *args, **kwargs):
        '''Retrieve the file.'''
        file = self.get_object().file
        response = ProtectedMediaResponse(file.name)
        response['Content-Type'] = 'text/csv; name="{}"'.format(
                file.name.replace('"', '\\"'))
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
        try:
            count = min(int(request.QUERY_PARAMS['rows']),
                        settings.FILE_HEAD_ROWS_MAX)
        except KeyError:
            count = proj_settings.FILE_HEAD_ROWS_DEFAULT
        except ValueError as e:
            return Response({'rows': [str(e)]},
                            status=status.HTTP_400_BAD_REQUEST)
        has_header, rows = self.get_object().csv_head(count)
        headers = rows.pop(0) if has_header else []
        for i, column in enumerate(columns):
            try:
                column = int(column)
                if column >= len(columns):
                    return Response(
                        {'columns': ['invalid column: {!r}'.format(columns[i])]},
                        status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                if column[:1] in '\'"' and column[:1] == column[-1:]:
                    column = column[1:-1]
                try:
                    column = columns.index(column)
                except ValueError:
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
            except ValueError:
                parsed = None
            else:
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=utc)
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


class SensorMapDefViewSet(viewsets.ModelViewSet):
    '''Manipulate all sensor maps owned by the active user.'''

    model = models.SensorMapDefinition
    serializer_class = serializers.SensorMapDefSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectOwner)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('project', 'name')

    def get_queryset(self):
        '''Only allow users to see sensor maps they own.'''
        user = self.request.user
        return models.SensorMapDefinition.objects.filter(project__owner=user)

    def pre_save(self, obj):
        '''Check the project owner against the current user.'''
        user = self.request.user
        if not models.Project.objects.filter(
                owner=user, pk=obj.project.pk).exists():
            raise rest_exceptions.PermissionDenied(
                    "Invalid project pk '{}' - "
                    'permission denied.'.format(obj.project.pk))


_processes = {}

@transaction.atomic
def perform_ingestion(ingest):
    '''Ingest into the common schema tables from the DataFiles.'''
    sensormap = ingest.map.map
    files = {f.name: f.file.file.file for f in ingest.files.all()}
    ingest_file = None
    try:
        ingested = list(ingest_files(sensormap, files))
        total_bytes = sum(file.size for file in ingested)
        processed_bytes = 0.0
        for file in ingested:
            _processes[ingest.id] = {
                'id': ingest.id,
                'status': 'processing',
                'percent': processed_bytes * 100.0 / total_bytes,
                'current_file_percent': 0.0,
                'current_file': file.name,
            }
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
            previous_bytes = 0
            for row in file.rows:
                time = row.columns[0]
                for (sensor, cls), column in zip(sensors, row.columns[1:]):
                    if isinstance(column, IngestError):
                        models.SensorIngestLog(file=ingest_file,
                                row=row.line_num, column=column.column_num,
                                level=models.SensorIngestLog.ERROR,
                                message=str(column)).save()
                    else:
                        cls(ingest=ingest, sensor=sensor, time=time,
                            value=column).save()
                if row.position - previous_bytes >= 1000:
                    _processes[ingest.id] = {
                        'id': ingest.id,
                        'status': 'processing',
                        'percent': (processed_bytes + row.position) * 100.0 / total_bytes,
                        'current_file_percent': row.position * 100.0 / file.size,
                        'current_file': file.name,
                    }
                    previous_bytes = row.position
            processed_bytes += file.size
    except Exception:
        logging.exception('an unhandled exception occurred during sensor '
                          'ingestion ({})'.format(ingest.id))
        models.SensorIngestLog(file=ingest_file, row=0, column=0,
                               level=models.SensorIngestLog.CRITICAL,
                               message='an unhandled server error occurred '
                                       'during ingestion').save()
    finally:
        ingest.end = datetime.datetime.utcnow().replace(tzinfo=utc)
        ingest.save()
        del _processes[ingest.id]


class DataSetViewSet(viewsets.ModelViewSet):
    model = models.SensorIngest
    serializer_class = serializers.SensorIngestSerializer
    permission_classes = (permissions.IsAuthenticated, IsSensorMapDefOwner)

    @link(permission_classes = (permissions.IsAuthenticated,))
    def status(self, request, *args, **kwargs):
        ingest = self.get_object()
        process = _processes.get(ingest.id)
        if process:
            return Response(process)
        return Response({
            'id': ingest.id,
            'status': 'complete',
            'percent': 100.0,
            'current_file_percent': 0.0,
            'current_file': None
        })

    @link()
    def errors(self, request, *args, **kwargs):
        '''Retrieves all errors that occured during an ingestion.'''
        ingest = self.get_object()
        serializer = serializers.SensorIngestLogSerializer(
                ingest.logs, many=True)
        return Response(serializer.data)

    def post_save(self, obj, created):
        '''After the SensorIngest object has been saved start a threaded
        data ingestion process.
        '''
        if created:
            _processes[obj.id] = {
                'id': obj.id,
                'status': 'processing',
                'percent': 0.0,
                'current_file_percent': 0.0,
                'current_file': None,
            }
            thread = threading.Thread(target=perform_ingestion, args=(obj,))
            thread.start()

    def get_queryset(self):
        '''Only allow users to see ingests they own.'''
        user = self.request.user
        return models.SensorIngest.objects.filter(map__project__owner=user)
