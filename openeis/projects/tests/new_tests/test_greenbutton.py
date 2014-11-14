import datetime
from collections import namedtuple

from django.utils.timezone import utc
import json
import os
import pytest
import sys
from xml.etree.ElementTree import parse
from rest_framework.test import force_authenticate, APIRequestFactory, APIClient
from rest_framework import status
from openeis.projects import views
from .conftest import detail_view
from openeis.server.parser.converter import Convert, split_namespace

pytestmark = pytest.mark.django_db


#@pytest.mark.skipif(True, reason='Skipping until GreenButton APIs are complete.')
def test_TestGBDataoneMonthBinnedDailyWCost(active_user, project):
#    convert_greenbutton_file(active_user, project, os.path.join('greenbutton', 'malformed_GB_data-broken-xml.xml'))
    convert_greenbutton_file(active_user, project, os.path.join('greenbutton', 'TestGBDataoneMonthBinnedDailyWCost.xml'))
def test_Premise1_2011_GreenButtonData_Texas(active_user, project):
    convert_greenbutton_file(active_user, project, os.path.join('greenbutton', 'Premise1_2011_GreenButtonData_Texas.xml'))
def test_TestGBDataOneYearDailyBinnedMonthly(active_user, project):
    convert_greenbutton_file(active_user, project, os.path.join('greenbutton', 'TestGBDataOneYearDailyBinnedMonthly.xml'))
def test_BigFile(active_user, project):
    convert_greenbutton_file(active_user, project, os.path.join('greenbutton', 'cc_customer_11.xml'))
    

def convert_greenbutton_file(active_user, project, fname):
    '''Tests the content negotiation of the dataset download API.'''
    rf = APIRequestFactory()
#    client = APIClient()
#    client.force_authenticate(user=active_user)
    url = '/api/projects/{}/add_file'.format(project.id)
    #look up relative path to file    
    path = os.path.join(os.path.dirname(views.__file__),'fixtures',fname)
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

def test_process_row():
    pass

def test_build_header_list():
    pass

def test_get_child_node_text():
    pass

def test_get_currency_type():
    pass

def test_get_retail_customer():
    pass

def test_get_uom_type():
    pass

def test_split_namespace():
    '''Tests the ability to split various valid and invalid namespaces.'''
    
    strings = {
        'valid_namespace': '{http://naesb.org/espi}IntervalReading',
        'invalid_namespace': '{http://naesb.org/espiIntervalReading'
    }
    
    assert (split_namespace(strings['valid_namespace']) == 'IntervalReading')
    assert (split_namespace(strings['invalid_namespace']) == "{http://naesb.org/espiIntervalReading")
    


def test_row_count():
    '''Test that data does not go missing during conversion.'''
    input_file = os.path.join(os.path.dirname(views.__file__),'fixtures/greenbutton','TestGBDataoneMonthBinnedDailyWCost.xml')
    
    tree = parse(input_file)
    root = tree.getroot()
    
    ns = {
        'espi': "http://naesb.org/espi"
    }
    
    # process xml nodes of input file, get count of IntervalReading nodes
    node_count = len(root.findall('.//espi:IntervalReading', namespaces=ns))
    
    # call Convert, get count of rows actually written
    with open(os.devnull, 'w') as nullout:
        row_count = Convert(input_file, nullout)
    row_count += 1
    
    assert(row_count == node_count)
    
    
