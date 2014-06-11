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
        'python-dateutil',
        'django>=1.6,<1.7',
        'django-filter',
        'django-guardian',
        'djangorestframework>=2.3,<2.4',
        'django-rest-swagger>=0.1,<0.2',
        'django-nose',
        'jsonschema',
        'openeis-ui>0.1.dev70',
        'pytz',
    ],
    entry_points = '''
        [console_scripts]
        openeis = openeis.server.manage:main
    ''',
    package_data = {
        'openeis.projects': ['storage/sensormap-schema.json'],
    }
)

