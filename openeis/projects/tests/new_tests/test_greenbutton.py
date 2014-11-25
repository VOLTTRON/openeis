import datetime
from collections import namedtuple

from django.utils.timezone import utc
import csv
import io
import json
import os
import pytest
import sys
from xml.etree.ElementTree import parse
from rest_framework.test import force_authenticate, APIRequestFactory, APIClient
from rest_framework import status
from openeis.projects import views
from .conftest import detail_view
from openeis.server.parser.converter import Convert, split_namespace,\
    get_uom_type, get_currency_type, get_child_node_text, build_header_list,\
    process_row

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
def test_malformed(active_user, project):
    convert_greenbutton_file(active_user, project, os.path.join('greenbutton', 'TestGBDataoneMonthBinnedDailyWCost_EDITED_FOR_MALFORMED_TEST.xml'))

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
    input_file = os.path.join(os.path.dirname(views.__file__),'fixtures/greenbutton','TestGBDataoneMonthBinnedDailyWCost.xml')
    tree = parse(input_file)
    root = tree.getroot()
    csv.register_dialect('csvdialect', delimiter=',', lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
    # with open(os.devnull, 'w') as nullout:
    #     writer = csv.writer(nullout, 'csvdialect')
    output = io.StringIO()
    writer = csv.writer(output, 'csvdialect')
    
    ns = {
        'espi': "http://naesb.org/espi"
    }
    
    IntervalReading = root.find('.//espi:IntervalReading', namespaces=ns)
    assert (IntervalReading is not None)
    
    process_row(IntervalReading, writer, ns)
    expected_row = '"2014-06-01 04:00:00","3600","2014-06-01 05:00:00",0.02585,"861",""'
    written_row = (output.getvalue()).strip()
    assert(expected_row == written_row)
    
    

def test_build_header_list():
    input_file = os.path.join(os.path.dirname(views.__file__),'fixtures/greenbutton','TestGBDataoneMonthBinnedDailyWCost.xml')
    tree = parse(input_file)
    root = tree.getroot()
    
    ns = {
        'espi': "http://naesb.org/espi"
    }
    
    header_list = ['cost', 'duration', 'start', 'value']
    headers_retrieved = build_header_list(root, ns)
    assert(headers_retrieved == header_list)

def test_get_child_node_text():
    input_file = os.path.join(os.path.dirname(views.__file__),'fixtures/greenbutton','TestGBDataoneMonthBinnedDailyWCost.xml')
    tree = parse(input_file)
    root = tree.getroot()
    
    ns = {
        'espi': "http://naesb.org/espi"
    }
    
    text_node = '1401595200'
    text_retrieved = get_child_node_text(root, ns, 'start')
    invalid_text = get_child_node_text(root, ns, 'invalid node')
    assert(text_node == text_retrieved)
    assert(invalid_text == "")

def test_get_currency_type():
    input_file = os.path.join(os.path.dirname(views.__file__),'fixtures/greenbutton','TestGBDataoneMonthBinnedDailyWCost.xml')
    tree = parse(input_file)
    root = tree.getroot()
    
    ns = {
        'espi': "http://naesb.org/espi"
    }
    
    node_currency = 'US Dollar'
    currency_retrieved = get_currency_type(root, ns)
    assert(node_currency == currency_retrieved)

def test_get_retail_customer():
    pass

def test_get_uom_type():
    '''Test that uom type is correctly retrieved.'''
    input_file = os.path.join(os.path.dirname(views.__file__),'fixtures/greenbutton','TestGBDataoneMonthBinnedDailyWCost.xml')
    tree = parse(input_file)
    root = tree.getroot()
    
    ns = {
        'espi': "http://naesb.org/espi"
    }
    
    node_uom = 'Real energy (Watt-hours)'
    prefixed_uom = 'Giga-Real energy (Giga-Watt-hours)'
    uom_retrieved = get_uom_type(root, ns)
    uom_prefixed_retrieved = get_uom_type(root, ns, 'Giga')
    assert(node_uom == uom_retrieved)
    assert(prefixed_uom == uom_prefixed_retrieved)

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
    
    assert(row_count == node_count)
    
    
