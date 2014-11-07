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


import datetime
from openeis.applications.utils.sensor_suitcase.utils import get_CBECS, separate_hours

import pprint 

def excessive_nighttime(light_data, op_sched, area, elec_cost):
    """
    Excessive Nighttime Lightingchecks to see a single sensor should be flagged.
    Parameters:
        - light_data: a 2d array with datetime and data
            - lights are on (1, True) or off (0, False)
            - assumes light_data is only for non-operational hours
        - op_sched: 2d array of operating schedule
            -[[operational hours], [days operating], [holidays]]
        - elec_cost: The electricity cost used to calculate savings.
    Returns: True or False (true meaning that this sensor should be flagged)
    """
    occupied_data, nonoccupied_data = separate_hours(light_data, op_sched[0], op_sched[1], op_sched[2])
    # Grabs the first time it starts logging so we know when the next day is
    day_marker = nonoccupied_data[0][0]
    # Counts the seconds when the lights are on
    time_on = datetime.timedelta(0)
    # Counts the total number of days
    day_count = 0

    if (nonoccupied_data[0][1] == True):
        last_on = nonoccupied_data[0][0]
    else:
        last_on = None
        
    # Iterate through the light data
    i = 1
    while (i < len(nonoccupied_data)):
        # NOTE: Assumes that status changes right when switches are turned. 
        # If the lights are on or a change from 'on' to 'off' then calculate the difference 
        # between the 'last_on' and the current date. 
        if (nonoccupied_data[i][1] == True): 
            if last_on != None: 
                time_on += (nonoccupied_data[i][0] - last_on)
            last_on = nonoccupied_data[i][0]
        else: 
            if last_on != None: 
                time_on += (nonoccupied_data[i][0] - last_on)
            last_on = None

        # Check if it's a new day
        if (nonoccupied_data[i][0].date() != day_marker.date() or i == len(nonoccupied_data)-1):
            day_count += 1
            day_marker = nonoccupied_data[i][0]

        i += 1

    if (time_on.days != 0):
        total_time = (time_on.days * 24) + (time_on.seconds / 3600)
    else:
        total_time = (time_on.seconds / 3600)
    
    if ((total_time / day_count) > 3):
        percent_l, percent_h, percent_c, med_num_op_hrs, per_hea_coo, \
                 percent_HV = get_CBECS(area)
        total_time = nonoccupied_data[-1][0] - nonoccupied_data[0][0]
        total_weeks = ((total_time.days * 24) + (total_time.seconds / 3600)) \
                / 168
        avg_week = ((total_time.days * 24) + (total_time.seconds / 3600)) \
                / total_weeks
        return {
            'Problem': "Excessive lighting during unoccupied/nighttime " + \
                    "hours.",
            'Diagnostic': "For more than half of the monitoring period, the " + \
                    "lights were on for more than three hours during  " + \
                    "after-hours periods.",
            'Recommendation': "Install occupancy sensors in locations where it " + \
                    "is not necessary or intended for the lights to be on all " + \
                    "night, or encourage occupants to turn the lights off upon " + \
                    "exit.",
            'Savings': round((0.4 * 0.1 * elec_cost * percent_l * \
                    (avg_week/(24*7-med_num_op_hrs))),2)
        }
    else:
        return {}