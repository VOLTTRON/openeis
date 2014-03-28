from django.conf.urls import patterns, url

urlpatterns = patterns('openeis.projects.views',
    url(r'^files/(.*)$', 'get_protected_file'),
)
