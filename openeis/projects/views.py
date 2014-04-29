from contextlib import closing
import posixpath
import traceback

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404

from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework import decorators
from rest_framework.decorators import action, link
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import models
from .protectedmedia import protected_media, ProtectedMediaResponse
from . import serializers
from .conf import settings as proj_settings


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
        print('is-authenticated-or-is-post')
        return (request.method == 'POST') ^ (request.user is not None)


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


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.MinimalUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('last_name', 'first_name', 'username')


def send_traceback(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            tb = traceback.format_exc()
        response = HttpResponse(tb, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        response['Content-Type'] = 'text/plain'
        return response
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    wrapper.__dict__ = fn.__dict__
    return wrapper


class AccountViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    permission_classes = (IsAuthenticatedOrPost,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateUserSerializer
        return serializers.UserSerializer

    def get_object(self):
        user = self.request.user
        if user.pk is None:
            raise Http404()
        return user

    def pre_save(self, user):
        if self.request.method == 'POST':
            user.is_active = False
        user.full_clean()

    def post_save(self, user, created=False):
        if created:
            try:
                verify = models.AccountVerification(
                        account=user, data={'verify': 'create'})
                verify.save()
                user.email_user('OpenEIS Account Creation Verification',
                        self.request.build_absolute_uri(reverse('account-verify',
                                kwargs={'code': verify.code})), 'openeis@pnnl.gov')
            except Exception:
                user.delete()
                raise
            return

    def verify(self, request, *args, code=None, **kwargs):
        verify = get_object_or_404(models.AccountVerification, code=code)
        if verify.data.get('verify') == 'create':
            user = verify.account
            user.is_active = True
            user.save()
        verify.delete()
        # XXX: Respond with success page or JS depending on Accept header
        return HttpResponseRedirect('/')
