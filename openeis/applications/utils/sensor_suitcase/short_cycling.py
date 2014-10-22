"""
Part of the `Sensor Suitcase` suite of applications.


Copyright
=========

OpenEIS Algorithms Phase 2 Copyright (c) 2014,
The Regents of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the U.S.
Department of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov
referring to "OpenEIS Algorithms Phase 2 (LBNL Ref 2014-168)".

NOTICE:  This software was produced by The Regents of the University of
California under Contract No. DE-AC02-05CH11231 with the Department of Energy.
For 5 years from November 1, 2012, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, and perform
publicly and display publicly, by or on behalf of the Government. There is
provision for the possible extension of the term of this license. Subsequent to
that period or any extension granted, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, distribute copies
to the public, perform publicly and display publicly, and to permit others to
do so. The specific term of the license can be identified by inquiry made to
Lawrence Berkeley National Laboratory or DOE. Neither the United States nor the
United States Department of Energy, nor any of their employees, makes any
warranty, express or implied, or assumes any legal liability or responsibility
for the accuracy, completeness, or usefulness of any data, apparatus, product,
or process disclosed, or represents that its use would not infringe privately
owned rights.


License
=======

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
"""


from datetime import datetime, timedelta
from openeis.applications.utils.sensor_suitcase.utils import get_CBECS

import pprint
def short_cycling(HVAC_stat, elec_cost, area):
    """
    Checks to see if the HVAC is short cycling.

    Parameter:
        - HVAC_stat: HVAC status
            - 2d array with [datetime, data]
            - data is 0 - off, 1 - fan is on, 2 - compressor on
        - elec_cost: The electricity cost used to calculate savings.
    Return:
        - True if the problem should be flagged
    """
    compressor_on = []
    for point in HVAC_stat:
        if (point[1] == 2):
            compressor_on.append(1)
        else:
            compressor_on.append(0)
    change_status = []
    cycle_start = []

    i = 0
    while (i < (len(compressor_on) - 1)):
        status = compressor_on[i+1] - compressor_on[i]
        if (status == 1):
            cycle_start.append(HVAC_stat[i+1])
        change_status.append(status)
        i += 1
        
    fault_count = 0
    i = 0
    while (i < (len(cycle_start) - 1)):
        delta = (cycle_start[i+1][0] - cycle_start[i][0])
        if (delta.seconds < 300):
            fault_count += 1
        i += 1
    
    if (fault_count > 10):
        percent_l, percent_h, percent_c, med_num_op_hrs, per_hea_coo, \
                 percent_HVe = get_CBECS(area)
        return {
            'Problem': "RTU cycling on and off too frequently, potentially " + \
                    "leading to equipment failure.",
            'Diagnostic': "For more than 10 consecutive cycles during the " + \
                    "monitoring period the RTU switched from on to off in under " + \
                    "5 minutes.",
            'Recommendation': "Ask HVAC service providers to check refrigerant " + \
                    "levels, thermostat location, and control sequences.",
            'Savings': round((percent_h + percent_c) * 0.10 * elec_cost, 2)}
    else:
        return {}


