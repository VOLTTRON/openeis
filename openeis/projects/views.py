from contextlib import closing
from multiprocessing import Process
import posixpath
import traceback
import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404

from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, link
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import exceptions as rest_exceptions

from . import models
from .protectedmedia import protected_media, ProtectedMediaResponse
from . import serializers
from .conf import settings as proj_settings
from .storage.ingest import ingest_files


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
    def top(self, request, *args, **kwargs):
        '''Return the top rows of the file split into columns.

        N defaults to FILE_HEAD_ROWS_DEFAULT projects setting and can be
        overridden using the rows query parameter. However, rows may not
        exceed FILE_HEAD_ROWS_MAX projects setting.
        '''
        try:
            count = int(request.QUERY_PARAMS['rows'])
        except (KeyError, ValueError):
            count = proj_settings.FILE_HEAD_ROWS_DEFAULT
        count = min(count, proj_settings.FILE_HEAD_ROWS_MAX)
        rows = []
        file = self.get_object().file
        file.open()
        with closing(file):
            csv_file = serializers.CSVFile(file)
            for row in csv_file:
                rows.append(row)
                if len(rows) >= count:
                    break
        return Response({'has_header': csv_file.has_header, 'rows': rows})


    @link()
    def head(self, request, *args, **kwargs):
        '''Return the first lines of the file.

        N defaults to FILE_HEAD_ROWS_DEFAULT projects setting and can be
        overridden using the rows query parameter. However, rows may not
        exceed FILE_HEAD_ROWS_MAX projects setting.
        '''
        try:
            rows = int(request.QUERY_PARAMS['rows'])
        except (KeyError, ValueError):
            rows = proj_settings.FILE_HEAD_ROWS_DEFAULT
        rows = min(rows, proj_settings.FILE_HEAD_ROWS_MAX)
        lines = []
        file = self.get_object().file
        file.open()
        with closing(file):
            while len(lines) < rows:
                # File iteration is broken in Django FileSystemStorage,
                # but readline() still works, so we do it this way.
                line = file.readline()
                if not line:
                    break
                lines.append(line.decode('utf-8'))
        return Response(lines)


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
                prefix = datetime.now().strftime('__DELETED_%Y%m%d%H%M%S%f_')
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


processes = {}
def get_files_for_ingestion(obj):
    name_file_map = {}
    for f in obj.files.all():
        name_file_map[f.name] = f.file.file.file
    return name_file_map

@transaction.atomic
def perform_ingestion(sensormap, ingest_id):
    '''
    Ingest into the common schema tables from the DataFiles.
    '''
    
    ingest = models.SensorIngest.objects.get(pk=ingest_id)
    files = get_files_for_ingestion(ingest)
    processes[ingest_id] = {
                                'id': ingest_id,
                                'status': 'processing',
                                'percent': 0.0,
                                'current_file_percent': 0.0,
                                'current_file': None,                                           
                            }
    
    total_bytes = 0.0
    # Get the total bytes for progress.
    for file in ingest_files(sensormap, files):
        total_bytes += file.size
        
    processed_bytes = 0.0
    for file in ingest_files(sensormap, files):
        processes[ingest_id]['current_file'] = file.name
        previous_bytes = 0
        print(file.columns)
        for row in file.rows:
            if len(row.errors) > 0:
                print("logging error")
            else:
                
                pass
            
            processes[ingest_id]['current_file_percent'] = row.position * 100 // file.size
            
            processed_bytes += row.position - previous_bytes
            processes[ingest_id]['percent'] = processed_bytes * 100  // total_bytes ## * 100
            print(processes[ingest_id]['current_file_percent'], processes[ingest_id]['percent'])
            previous_bytes = row.position
            
    del(processes[ingest_id])
              
    print("perform_ingestion complete")
            
class SensorIngestViewSet(viewsets.ModelViewSet):
    model = models.SensorIngest
    serializer_class = serializers.SensorIngestSerializer
    permission_classes = (permissions.IsAuthenticated,)

 
    @link()
    def status(self, request, *args, **kwargs):
        ingest = self.get_object()
        #ingest = get_object_or_404(models.SensorIngest)
        print("ingest id:", ingest.id)                
        if ingest.id in processes:
            return Response(json.dumps(processes[id], status.HTTP_200_OK))
        else:
            return Response("Complete")
             
    
        
    def post_save(self, obj, created):
        '''
        After the SensorIngest object has been saved start a threaded
        data ingestion process.
        '''
        if created:
            process = Process(target=perform_ingestion, args=(obj.map.map, obj.id)) #jsonmap, files))
            process.start()
        
        
            
    def get_queryset(self):
        return models.SensorIngest.objects.all() # (Response({'abc': 2, "def":4}))        
