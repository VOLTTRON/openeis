from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.shortcuts import render_to_response

from openeis.projects.urls import urlpatterns as projects_urls


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^(?:index.html)?$', lambda request: render_to_response('base.html')),
    url(r'^', include(projects_urls)),
    url(r'^admin/', include(admin.site.urls)),
)
