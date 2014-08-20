import os.path
import posixpath

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, StreamingHttpResponse


class ProtectedFileSystemStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        super().__init__(location=location or settings.PROTECTED_MEDIA_ROOT,
                         base_url=base_url or settings.PROTECTED_MEDIA_URL)


class XSendfileResponse(HttpResponse):
    '''Add X-Sendfile to header for Apache.'''
    def __init__(self, filename, **kwargs):
        super().__init__(**kwargs)
        self['X-Sendfile'] = os.path.join(
                settings.PROTECTED_MEDIA_ROOT, filename)


class XAccelRedirectResponse(HttpResponse):
    '''Add X-Accel-Redirect to header for Nginx.'''
    def __init__(self, filename, **kwargs):
        super().__init__(**kwargs)
        self['X-Accel-Redirect'] = posixpath.join(
                settings.PROTECTED_MEDIA_URL, filename)


def _read_file(filename):
    with open(filename,'rb') as file:
        while True:
            data = file.read(4096)
            if not data:
                break
            yield data


class DirectFileResponse(StreamingHttpResponse):
    '''Serve the file directly from Django.'''
    def __init__(self, filename, **kwargs):
        super().__init__(_read_file(os.path.join(
                settings.PROTECTED_MEDIA_ROOT, filename)), **kwargs)


def ProtectedMediaResponse(filename):
    '''Return the appropriate response type for configured method.

    The send method is set via the PROTECTED_MEDIA_METHOD setting, which
    can be one of X-Accel-Redirect, X-Sendfile, or direct. The
    underlying server should be configured appropriately for the
    selected method.

    The filename should be a string which is the path to the file
    relative to PROTECTED_MEDIA_ROOT.
    '''
    method = getattr(settings, 'PROTECTED_MEDIA_METHOD', 'direct').lower()
    cls = {'x-accel-redirect': XAccelRedirectResponse,
           'x-sendfile': XSendfileResponse,
           'direct': DirectFileResponse,
          }[method]
    response = cls(filename)
    basename = posixpath.basename(filename)
    response['Content-Type'] = 'application/unknown'
    response['Content-Disposition'] = 'attachment; filename=' + basename
    return response


def protected_media(view):
    '''Decorator for view function to send file from protected storage.'''
    def wrapper(*args, **kwargs):
        filename = view(*args, **kwargs)
        return ProtectedMediaResponse(filename)
    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    wrapper.__dict__ = view.__dict__
    return wrapper
