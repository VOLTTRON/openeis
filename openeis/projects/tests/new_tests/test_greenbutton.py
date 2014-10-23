import datetime
from collections import namedtuple

from django.utils.timezone import utc
import json
import os
import pytest
from rest_framework.test import force_authenticate, APIRequestFactory, APIClient
from rest_framework import status
from openeis.projects import views
from .conftest import detail_view

pytestmark = pytest.mark.django_db


@pytest.mark.skipif(True, reason='Skipping until GreenButton APIs are complete.')
def test_greenbutton_file(active_user, project):
    '''Tests the content negotiation of the dataset download API.'''
    rf = APIRequestFactory()
#    client = APIClient()
#    client.force_authenticate(user=active_user)
    url = '/api/projects/{}/add_file'.format(project.id)
    #look up relative path to file    
    path = os.path.join(os.path.dirname(views.__file__),'fixtures','Premise1_2011_GreenButtonData_Texas.xml')
    print (path)
    with open(path, 'rb') as file:
        request = rf.post(url, {"file": file})
        force_authenticate(request, active_user)
        view = views.ProjectViewSet.as_view({'post': 'add_file'})
        response = view(request, pk=project.id)
    assert (response.status_code == status.HTTP_201_CREATED)
    
    assert (response.data['format'] == 'greenbutton')
    #check response data, look up obj
#    file = datafile_greenbutton
#    print(file)
