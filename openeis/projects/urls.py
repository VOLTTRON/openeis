from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'files', views.FileViewSet)

urlpatterns = patterns('openeis.projects.views',
    url(r'^api/auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include(router.urls)),
    url(r'^files/(.*)$', 'get_protected_file'),
)
