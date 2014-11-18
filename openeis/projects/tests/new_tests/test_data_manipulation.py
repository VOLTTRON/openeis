import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

def test_data_manipulation(active_user, mixed_dataset):
    '''Tests data manipulation.'''

    client = APIClient()
    client.force_authenticate(user=active_user)
    dataset = mixed_dataset
    url = '/api/datasets/{}'.format(dataset.pk)
    response = client.get(url)
    assert response.data['download_url'] == 'http://testserver{}/download'.format(url)