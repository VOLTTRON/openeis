from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter, SimpleRouter, Route

from . import views
from . import swagger_patch


class SingleObjectRouter(SimpleRouter):
    routes = [
        # Detail route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'post': 'create',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated routes.
        # Generated using @action or @link decorators on methods of the viewset.
        Route(
            url=r'^{prefix}/{methodname}{trailing_slash}$',
            mapping={
                '{httpmethod}': '{methodname}',
            },
            name='{basename}-{methodnamehyphen}',
            initkwargs={}
        ),
    ]


router = DefaultRouter(trailing_slash=False)
router.register(r'projects', views.ProjectViewSet)
router.register(r'files', views.FileViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'sensormaps', views.SensorMapDefViewSet)
router.register(r'analyses', views.AnalysisViewSet)
router.register(r'shared-analyses', views.SharedAnalysisViewSet)
api_urls = list(router.urls)
api_urls.append(url(r'^datasets/preview$',
                    views.DataSetPreviewViewSet.as_view({'post': 'preview'}),
                    name='datasets-preview'))
router = DefaultRouter(trailing_slash=False)
router.register(r'datasets', views.DataSetViewSet)
api_urls.extend(router.urls)

router = SingleObjectRouter(trailing_slash=False)
router.register(r'account', views.AccountViewSet, base_name='account')
api_urls.extend(router.urls)
api_urls.append(
    url(r'^account/verify/(?P<id>\d+)/(?P<pk>\d+)/(?P<code>[a-zA-Z0-9]{50})$',
        views.AccountViewSet.as_view({'get': 'verify'}), name='account-verify'))

api_urls.append(url(r'applications',
                    views.ApplicationViewSet.as_view({'get': 'list'}),
                    name='applications'))

urlpatterns = patterns('openeis.projects.views',
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-docs/', include('rest_framework_swagger.urls')),
    url(r'^api/', include(api_urls)),
    url(r'^files/(.*)$', 'get_protected_file'),
)
