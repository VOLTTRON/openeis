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

import subprocess

__version__ = '0.1'

def product_version():
    return __version__

def vcs_version_count():
    """
    # Returns revision count: 
    # git rev-list --count HEAD
    """
    
    global _revision_count
    try: 
        return _revision_count
    except NameError:
        pass
    
    _revision_count = ""
    
    revision_args = ['git', 'rev-list', '--count', 'HEAD']
    revision_subprocess = subprocess.Popen(revision_args, stdout=subprocess.PIPE, shell=True)
    revision_out, revision_err = revision_subprocess.communicate()
    _revision_count = (revision_out.decode('utf-8')).strip()   # bytes/byte string, must be converted to utf-8
    return _revision_count

def vcs_short_hash():
    """
    # Returns short revision hash:
    # git --no-pager log -n 1 --pretty=format:'%h'
    """
    
    global _revision_hash
    try: 
        return _revision_hash
    except NameError:
        pass
    
    _revision_hash = ""
    args = ['git', '--no-pager', 'log', '-n', '1', '--pretty=format:\'%h\'']
    result = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    hash_out, hash_err = result.communicate()
    _revision_hash = (hash_out.decode('utf-8')).strip('\'\"')   # bytes/byte string, must be decoded
    return _revision_hash

def vcs_updated():
    '''
    # Returns updated timestamp:
    # git --no-pager log -n 1 --pretty=format:'%ct'
    '''
    
    global _revision_timestamp
    try:
        return _revision_timestamp
    except NameError:
        pass
    
    _revision_timestamp = ""
    args = ['git', '--no-pager', 'log', '-n', '1', '--pretty=format:\'%ct\'']
    command_result = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
    time_out, time_err = command_result.communicate()
    _revision_timestamp = (time_out.decode('utf-8')).strip("\'")
    return _revision_timestamp
    

def vcs_version():
    """
    # To get both short hash and local timestamp:
    # git --no-pager log -n 1 --date=local --pretty=format:'%h %ct
    # 
    # Returns dictionary of version information:
    #   'version': program version
    #   'vcs_version': The version control system (vcs) last commit short hash in Git
    #   'updated': The last updated vcs commit date
    #   'revision': The count of the vcs revisions (number of commits)
    """
    
    global _results_dict
    try:
        return _results_dict
    except NameError:
        pass
    
    _results_dict = {}
    
    # abbreviated hash and timestamp
    # hash_args = ['git', '--no-pager', 'log', '-n', '1', '--date=local', '--pretty=format:\'%h %ct\'']
    # hash_result = subprocess.Popen(hash_args, stdout=subprocess.PIPE, shell=True)
    # hash_out, hash_err = hash_result.communicate()
    # hash_converted = hash_out.decode('utf-8')   # bytes/byte string, must be converted
    # _results_dict['vcs_version'], _results_dict['updated'] = (hash_converted.strip("\"\'").split())
    
    _results_dict['version'] = __version__
    _results_dict['vcs_version'] = vcs_short_hash()
    _results_dict['updated'] = vcs_updated()
    _results_dict['revision'] = vcs_version_count()
    
    """
    # Example from EIS-481
    {
        "version": "1.2.431",
        "vcs_version": "1a2b3cd",
        "updated": "2014-10-28T09:33:45.123Z",
        "revision": 431
    }
    """
    return _results_dict


if __name__ == '__main__':
    print(vcs_short_hash())
    print(vcs_updated())
    print(vcs_version_count())
    print(vcs_version())