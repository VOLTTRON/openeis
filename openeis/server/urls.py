import re

from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.http import HttpResponseRedirect, Http404

from openeis.projects.urls import urlpatterns as projects_urls
from openeis.ui.urls import urlpatterns as ui_urls


def not_found(request, *args, **kwargs):
    raise Http404()


admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include(projects_urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/auth$', 'openeis.server.views.auth'),
    # Look-ahead and look-behind patterns don't work, so
    # short circuit these requests from returning the index page.
    url(r'^(?:admin|api|api-auth|api-docs|files|static)(?:/|$)', not_found),
)

if settings.DEBUG:
    urlpatterns += [
        url(r'', include(ui_urls)),
    ]
