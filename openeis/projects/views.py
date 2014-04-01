from django.contrib.auth.decorators import user_passes_test

from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, link
from rest_framework.response import Response

from . import models
from .protectedmedia import protected_media, ProtectedMediaResponse
from . import serializers


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


class ProjectViewSet(viewsets.ModelViewSet):
    '''REST API handler for Project model.'''

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

    @action(serializer_class=serializers.CreateFileSerializer)
    def add_file(self, request, *args, **kwargs):
        '''Always set the owning project when adding files.'''
        project = self.get_object()
        serializer = serializers.CreateFileSerializer(
                project=project, data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            serializer.save(force_insert=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class FileViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    '''REST API for viewing and modifying data files.'''

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
        '''Method for retrieving data files.'''
        file = self.get_object().file
        return ProtectedMediaResponse(file.name)
