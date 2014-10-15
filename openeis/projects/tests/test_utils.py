import tempfile

from rest_framework.test import APIClient
from openeis.projects.models import User

def get_authenticated_client():
	'''
	
	'''
	if not User.objects.get(username='test_user'):
		u = User(username='test_user', email='test@test.com', password='test')
		u.save()
	
	client = APIClient()
	assert client.login(username='test_user', password='test')
	return client

def upload_temp_file_data(project, data=None):
        '''
        Uploads a filestream that is created from a known stream of data.
        
        The data in this instance should be rows of comma delimited data.
        '''
        # Create a temp file for uploading to the server.
        tf = tempfile.NamedTemporaryFile(suffix='.cxv')
        if data:
            tf.write(bytes(data, 'utf-8'))
        else:
            tf.write(bytes(UPLOAD_DATA, 'utf-8'))
        tf.flush()
        tf.seek(0)

        client = get_authenticated_client()
        response = client.post('/api/projects/{}/add_file'.format(project), {'file':tf})
        assert response.status_code == 201, "Couldn't create file for project." 
        return response.data["id"]
       
def create_project(project_name):
	client = get_authenticated_client()
	params = {"name":project_name}
	response = client.post('/api/projects', params )
	assert response.status_code == 201, 'Invalid response code detected in project creation.'
	return response.data["id"]