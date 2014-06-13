from setuptools import setup


setup(
    name = 'openeis-ui',
    version = '0.2.dev0',
    description = 'Open Energy Information System (OpenEIS) API client.',
    author = 'Bora Akyol',
    author_email = 'bora@pnnl.gov',
    url = 'http://www.pnnl.gov',
    packages = ['openeis.ui'],
    package_data = {
        'openeis.ui': ['static/openeis-ui/' + name for name in
                       ['index.html', 'settings.js',
                        'sensormap-schema.json',
                        'css/app.css', 'js/app.min.js']],
    },
    zip_safe = False,
)
