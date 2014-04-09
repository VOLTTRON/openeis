from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.shortcuts import render_to_response

from openeis.projects.urls import urlpatterns as projects_urls


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'django.contrib.auth.views.login', {'template_name': 'index.html'}),
    url(r'^', include(projects_urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/auth$', 'openeis.server.views.auth'),
)
