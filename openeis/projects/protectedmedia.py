# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

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
