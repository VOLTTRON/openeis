from datetime import datetime
import subprocess
import pytest

from rest_framework.test import APIClient

from openeis.projects.version import vcs_version,\
    product_version, __version__, _vcs_path, have_vcs, vcs_revision,\
    vcs_timestamp, get_version_info


def test_have_vcs():
    '''Test the have_vcs method of version.py.'''
    vcs_value = _vcs_path()
    assert((vcs_value is not None) == have_vcs())
    

def test_product_version():
    '''Test the product_version method of version.py.'''
    version_value = __version__
    assert (version_value == product_version())
    
def test_vcs_revision():
    '''Test the vcs_revision method of version.py.'''
    vcsdir = _vcs_path()
    if vcsdir is not None:
        revision_args = ['git', 'rev-list', '--count', 'HEAD']
        revision_count = subprocess.check_output(
                    revision_args, cwd=vcsdir, stdin=subprocess.DEVNULL, shell=True).decode('utf-8').strip()
        print(revision_count)
        assert (int(revision_count) == vcs_revision())

def test_vcs_version():
    '''Test the vcs_version method of version.py.'''
    vcsdir = _vcs_path()
    if vcsdir is not None:
        args = ['git', 'rev-parse', '--short', 'HEAD']
        revision_hash = subprocess.check_output(
                    args, cwd=vcsdir, stdin=subprocess.DEVNULL, shell=True).decode('utf-8').strip()
        
        assert (revision_hash == vcs_version())

def test_vcs_timestamp():
    vcsdir = _vcs_path()
    if vcsdir is not None:
        args = ['git', 'log', '-n', '1', "--pretty=format:%ci"]
        time_stamp = subprocess.check_output(
                    args, cwd=vcsdir, stdin=subprocess.DEVNULL, shell=True).decode('utf-8').strip()
        assert (time_stamp == vcs_timestamp())

def test_get_version_info():
    vcsdir = _vcs_path()
    versionthing = {'version': product_version()} 
    if vcsdir is not None:
        versionthing['vcs_version'] = vcs_version()
        versionthing['updated'] = vcs_timestamp()
        versionthing['revision'] = vcs_revision()
    
    assert (versionthing == get_version_info())


@pytest.mark.django_db
def test_api_endpoint(active_user):
    '''Test version API endpoint.'''
    
    # see test_dataset.py, test_dataset_download_url
    
    client = APIClient()
    client.force_authenticate(user=active_user)
    url = '/api/version/{}'
    response = client.get(url)
    assert (response.data['version'] == __version__)
    if have_vcs():
        assert (response.data['vcs_version'] == vcs_version())
        assert (response.data['updated'] == vcs_timestamp())
        assert (response.data['revision'] == vcs_revision())
    
    
    