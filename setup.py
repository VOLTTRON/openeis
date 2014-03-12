from setuptools import setup

setup(
    name = 'openeis.server',
    version = '0.1',
    description = 'OpenEIS server.',
    author = 'Bora Akyol',
    author_email = 'bora@pnnl.gov',
    url = 'http://www.pnnl.gov',
    packages = ['openeis.server'],
    install_requires = ['django>=1.6,<1.7'],
)

