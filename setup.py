from setuptools import setup

setup(
    name = 'openeis.server',
    version = '0.1',
    description = 'Open Energy Information System (OpenEIS) server.',
    author = 'Bora Akyol',
    author_email = 'bora@pnnl.gov',
    url = 'http://www.pnnl.gov',
    packages = ['openeis.server'],
    install_requires = [
        'django>=1.6,<1.7',
        'django-filter',
        'django-guardian',
        'djangorestframework',
        'jsonschema',
    ],
    extras_require = {
        'md': ['Markdown'],
        'yaml': ['PyYAML'],
    },
    entry_points = '''
        [console_scripts]
        openeis = openeis.server.manage:main
    ''',
)

