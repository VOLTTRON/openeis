from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin

from openeis.projects.urls import urlpatterns as projects_urls


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include(projects_urls)),
    url(r'^admin', include(admin.site.urls)),
    url(r'^api/auth$', 'openeis.server.views.auth'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^(?P<path>(?:css|js|partials)/.+)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_UI_DIR}),
        url(r'^(?:index.html)?$', 'django.views.static.serve',
            {'path': 'index.html', 'document_root': settings.STATIC_UI_DIR}),
    )
