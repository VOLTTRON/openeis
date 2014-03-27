from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import user_passes_test

from openeis.projects.urls import urlpatterns as projects_urls
from openeis.projects.protectedmedia import protected_media


def staff_test(user):
    return user.is_staff

@protected_media
@user_passes_test(staff_test)
def get_protected_file(request, path):
    return path


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^(?:index.html)?$', lambda request: render_to_response('base.html')),
    url(r'^files/(.*)$', get_protected_file),
    url(r'^projects/', include(projects_urls)),
    url(r'^admin/', include(admin.site.urls)),
)
