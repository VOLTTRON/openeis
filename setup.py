from setuptools import setup

setup(
    name = 'openeis',
    version = '0.1',
    description = 'Open Energy Information System (OpenEIS) server.',
    author = 'Bora Akyol',
    author_email = 'bora@pnnl.gov',
    url = 'http://www.pnnl.gov',
    packages = ['openeis.server', 'openeis.projects'],
    install_requires = [
        'django>=1.6,<1.7',
        'django-filter',
        'django-guardian',
        'djangorestframework',
        'django-rest-swagger',
        'jsonschema',
        'nose',
        'django-nose'        
    ],
    entry_points = '''
        [console_scripts]
        openeis = openeis.server.manage:main
    ''',
)

