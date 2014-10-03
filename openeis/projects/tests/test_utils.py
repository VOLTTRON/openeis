
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