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
from openeis.applications.utils.sensor_suitcase.utils import get_CBECS


def excessive_nighttime(light_data, operational_hours, area, elec_cost):
    """
    Excessive Nighttime Lightingchecks to see a single sensor should be flagged.
    Parameters:
        - light_data: a 2d array with datetime and data
            - lights are on (1) or off (0)
            - assumes light_data is only for non-operational hours
        - operational_hours: building's operational in hours a day
        - elec_cost: The electricity cost used to calculate savings.
    Returns: True or False (true meaning that this sensor should be flagged)
    """
    # Grabs the first time it starts logging so we know when the next day is
    first_time = light_data[0][0]
    # counts the seconds when the lights are on
    time_on = datetime.timedelta(0)
    # counts the total number of days
    day_count = 0

    # accounts for the first point, checks if the lights are on, sets when
    # lights were last set to on to the first time
    if (light_data[0][1] == 1):
        lights_on = True
        last_on = first_time
    else:
        lights_on = False

    # Find the first index when lights are on.
    # FIXME: Is this a valid substitution?
    for light_dpt in light_data:
        if light_dpt[1]:
            last_on = light_dpt[0]
            break

    # iterate through the light data
    i = 1
    while (i < len(light_data)):
        # check if it's a new day
        if (light_data[i][0].time() == first_time.time()):
            # check if lights were left on yesterday
            # take the last point form yesterday and add the time to time_on
            if (light_data[i-1][1] == 1):
                time_on += (light_data[i-1][0] - last_on)
            day_count += 1
        # check lights were turned off, if so, increment on_to_off, lights
        # are now off, add time on to timeOn
        if ((lights_on) and (light_data[i][1] == 0)):
            lights_on = False
            time_on += (light_data[i][0] - last_on)
        # check if lights were turned on, set last_on to the current time
        elif ((not lights_on) and (light_data[i][1] == 1)):
            on = True
            last_on = light_data[i][0]
        i += 1

    if (time_on.days != 0):
        total_time = (time_on.days * 24) + (time_on.seconds / 60)
    else:
        total_time = (time_on.seconds / 60)

    if ((total_time / day_count) > 3):
        percent_l, percent_h, percent_c, med_num_op_hrs, per_hea_coo, \
                 percent_HV = get_CBECS(area)
        total_time = light_data[-1][0] - first_time
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

