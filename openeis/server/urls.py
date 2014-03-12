from django.conf.urls import patterns, include, url
from django.shortcuts import render_to_response

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^(?:index.html)?$', lambda request: render_to_response('base.html')),
    url(r'^admin/', include(admin.site.urls)),
)
