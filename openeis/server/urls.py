from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin

from openeis.projects.urls import urlpatterns as projects_urls
from openeis.ui.urls import urlpatterns as ui_urls


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include(projects_urls)),
    url(r'^admin', include(admin.site.urls)),
    url(r'^api/auth$', 'openeis.server.views.auth'),
)

if settings.DEBUG:
    urlpatterns += [
        url(r'', include(ui_urls)),
    ]
