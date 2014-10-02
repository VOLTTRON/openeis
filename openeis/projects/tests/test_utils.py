
from rest_framework.test import APIClient

def get_authenticated_client():
	client = APIClient()
	assert client.login(username='test_user', password='test')
	return client