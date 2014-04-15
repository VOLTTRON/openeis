from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.views.decorators.csrf import ensure_csrf_cookie
import json


@ensure_csrf_cookie
def auth(request):
    if request.method == 'GET':
        if request.user.is_authenticated():
            return HttpResponse('{{"username":"{}"}}'.format(request.user.username))
        return HttpResponseForbidden()

    if request.method == 'DELETE':
        logout(request);
        return HttpResponse()

    if request.method != 'POST':
        return HttpResponseNotAllowed(['GET', 'POST', 'DELETE'])

    creds = json.loads(request.body.decode(encoding='UTF-8'))

    user = authenticate(username=creds['username'], password=creds['password'])

    if user is not None:
        login(request, user)
        return HttpResponse('{{"username":"{}"}}'.format(user.username))

    return HttpResponseForbidden()
