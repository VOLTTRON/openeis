# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}

from setuptools import setup, find_packages
import sys
import os

install_requires = [
        # This will be installed after the bootstrap. 'ephem',
        # This will be installed after the bootstrap. 'workalendar',
        'python-dateutil',
        'django>=1.6,<1.7',
        'django-filter>=0.8,<0.9',
        #'django-guardian',
        'djangorestframework>=2.3,<2.4',
        'django-rest-swagger>=0.1,<0.2',
        #'django-nose',
        'jsonschema',
        #'openeis-ui>0.1.dev70',
        # note we use both of them.  django-pytest allows the
        # runner when using openeis test
        'pytest-django',
        'django-pytest',
        'pytz',
        'pytest-django'
]

basepath = os.path.dirname(os.path.abspath(__file__))

def get_files(path):
    '''Recursivly walks a directory returning list of files'''

    file_names = []
    abspath = os.path.abspath(path)
    origpath = os.getcwd()
    os.chdir(path)

    # the walk needs to be relatative to the currently changed
    # directory. So that it is put into the package correctly.
    for root, dirs, files in os.walk('.', topdown=False):
        for name in files:
            if '__pycache__' not in root:
                file_names.append(os.path.join(root, name)) #(os.path.join(root, name)))
    os.chdir(origpath)

    return file_names

if sys.platform != 'win32':
    install_requires.append('numpy')
    install_requires.append('scipy')

setup(
    name = 'openeis',
    version = '2.5',
    description = 'Open Energy Information System (OpenEIS) server.',
    author = 'Bora Akyol',
    author_email = 'bora@pnnl.gov',
    url = 'http://www.pnnl.gov',
    packages = find_packages(),
    # ['openeis.server', 'openeis.projects', 
    #            'openeis.applications', 'openeis.projects.storage'],

    install_requires = install_requires,
    entry_points = '''
        [console_scripts]
        openeis = openeis.server.manage:main
    ''',
    package_data = {
        'openeis.projects': [ os.path.join('static', x) for x in get_files(os.path.join(basepath, 'openeis', 'projects', 'static'))]
    }
)

