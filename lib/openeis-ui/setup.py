from setuptools import setup
import os

basepath = os.path.dirname(os.path.abspath(__file__))

def get_files(path):
    '''Recursivly walks a directory returning list of files'''
    
    file_names = []
    abspath = os.path.abspath(path)
    #print("moving to: ")
    cpath = os.getcwd()
    os.chdir(path)
    
    for root, dirs, files in os.walk('.', topdown=False):
        for name in files:
            if '__pycache__' not in root:
                #print (name)
                file_names.append(os.path.join(root, name)) #(os.path.join(root, name)))
    os.chdir(cpath)
    return file_names

setup(
    name = 'openeis-ui',
    version = '0.2.dev0',
    description = 'Open Energy Information System (OpenEIS) API client.',
    author = 'Bora Akyol',
    author_email = 'bora@pnnl.gov',
    url = 'http://www.pnnl.gov',
    packages = ['openeis.ui'],
    package_data = {
        'openeis.ui': get_files(os.path.join(basepath, 'openeis', 'ui'))
        
        #['static/openeis-ui/' + name for name in
        #               ['index.html', 'settings.js',
        #                'sensormap-schema.json',
        #                'css/app.css', 'js/app.min.js']],
    },
    zip_safe = False,
)
