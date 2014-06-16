import os
from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured


if not settings.DEBUG:
    raise ImproperlyConfigured('OpenEIS UI files are static and should not be '
                               'served by Django in production.')

UI_STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             'static/openeis-ui'))

urlpatterns = [
    url(r'^(?P<path>settings\.js|sensormap-schema\.json)$', 'django.views.static.serve',
        {'document_root': UI_STATIC_DIR}),
    url(r'^(?P<path>(?:css|js)/.+)$', 'django.views.static.serve',
        {'document_root': UI_STATIC_DIR}),
    url(r'', 'django.views.static.serve',
        {'path': 'index.html', 'document_root': UI_STATIC_DIR}),
]
