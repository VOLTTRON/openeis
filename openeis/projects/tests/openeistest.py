'''
Created on May 22, 2014
'''
import tempfile

from django.test import TestCase
from rest_framework.test import APIClient

UPLOAD_DATA = '''Date,Hillside OAT [F],Main Meter [kW],Boiler Gas [kBtu/hr]
9/29/2009 15:00,74.72,280.08,186.52
9/29/2009 16:00,75.52,259.67,169.82
9/29/2009 17:00,75.78,221.92,113.88
9/29/2009 18:00,76.19,145.24,54.74
9/29/2009 19:00,76.72,121.85,11.58
9/29/2009 20:00,76.3,113.72,11.17
9/29/2009 21:00,76.88,111.22,21.41
9/29/2009 22:00,77.16,107.01,29.2
9/29/2009 23:00,76.44,108.45,81.02
9/30/2009 0:00,76.9,116.66,170.73
9/30/2009 1:00,77.29,119.1,246.17
9/30/2009 2:00,76.99,117.57,213.78
9/30/2009 3:00,,121.98,215.91
9/30/2009 4:00,,139.2,385.73
9/30/2009 5:00,,151.42,477.32
9/30/2009 6:00,,162.47,701.29
9/30/2009 7:00,,189.76,691.95
9/30/2009 8:00,,221.91,624.79
9/30/2009 9:00,,228.19,454.43
9/30/2009 10:00,,236.93,468.05
9/30/2009 11:00,,239.53,308.18
9/30/2009 12:00,,246.81,268.58
9/30/2009 13:00,,249.38,229.05
9/30/2009 14:00,71.81,258.76,205.13
9/30/2009 15:00,71.14,261.77,204.11'''

class OpenEISTestBase(TestCase):
    
    
    def get_authenticated_client(self):
        client = APIClient()
        self.assertTrue(client.login(username='test_user', password='test'))
        return client
    
    def upload_temp_file_data(self, project):
        '''
        Uploads a filestream that is created from a known stream of valid data.
        '''
        # Create a temp file for uploading to the server.        
        tf = tempfile.NamedTemporaryFile(suffix='.cxv')
        tf.write(bytes(UPLOAD_DATA, 'utf-8'))
        tf.flush()
        tf.seek(0)
        
        client = self.get_authenticated_client()                         
        return client.post('/api/projects/{}/add_file'.format(project), {'file':tf})
        