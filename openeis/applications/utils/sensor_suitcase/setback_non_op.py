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

from datetime import datetime
import numpy as np
from openeis.applications.utils.sensor_suitcase.utils import separate_hours, get_CBECS


def setback_non_op(ZAT, DAT, op_hours, elec_cost, area, HVACstat=None):
    """
    Checks to see if a location is being cooled or heated during non-operational
    hours.

    Parameters:
        - ZAT: zone air temperature, 2D array of datetime and data
        - DAT: discharge air temperature, 2D array of datetime and data
        - HVACstat: HVAC status (optional), 2D array of datetime and data
            - 0 - off, 1 - ventilation, 3 - compressor
        - op_hours: operational hours
            - [[operational hours], [business days], [holidays]]
        - elec_cost: The electricity cost used to calculate savings.
    Returns:
        - flag indicating whether or not this should be flagged
    """
    # separate hours of ZAT and DAT
    ZAT_op, ZAT_non_op = separate_hours(ZAT, op_hours[0], op_hours[1],
            op_hours[2])
    DAT_op, DAT_non_op = separate_hours(DAT, op_hours[0], op_hours[1],
            op_hours[2])

    # if HVAC status exists, separate that too
    if (HVACstat):
        HVAC_op, HVAC_non_op = separate_hours(HVACstat, op_hours[0],
                op_hours[1], op_hours[2])
    else:
        HVAC_op = []
        HVAC_non_op = []

    # separate data into cooling, heating, and hvac
    op_cool_dat, op_heat_dat, op_hvac_dat = _grab_data(DAT_op, ZAT_op, DAT_op, \
            HVAC_op)
    non_cool_dat, non_heat_dat, non_hvac_dat = _grab_data(DAT_non_op, \
            ZAT_non_op, DAT_non_op, HVAC_non_op)

    # find the average cooling diffuser set temp
    avg_DAT_c_occ = np.mean(op_cool_dat)
    avg_DAT_h_occ = np.mean(op_heat_dat)

    # count to see if cooling is on
    c_flag = 0
    for pt in non_cool_dat:
        if ((pt < avg_DAT_c_occ) or (abs(pt - avg_DAT_h_occ) < 0.1)):
            c_flag += 1
    #
    h_flag = 0
    for pt in non_heat_dat:
        if ((pt > avg_DAT_h_occ) or (abs(pt - avg_DAT_h_occ) < 0.1)):
            h_flag += 1
    #
    non_op_data_len = len(DAT_non_op)
    c_val = c_flag/non_op_data_len
    h_val = h_flag/non_op_data_len
    vent_val = non_hvac_dat/non_op_data_len
    percent_unocc = non_op_data_len/len(DAT)

    non_cool_zat, non_heat_zat, non_hvac_zat = _grab_data(DAT_non_op, \
            ZAT_non_op, ZAT_non_op, HVAC_non_op)
    #
    ZAT_cool_threshold = 80
    ZAT_heat_threshold = 55
    #
    if non_cool_zat != []:
        min_ZAT_c_unocc = np.min(non_cool_zat)
    else:
        min_ZAT_c_unocc = ZAT_cool_threshold

    if non_heat_zat != []:
        max_ZAT_h_unocc = np.max(non_heat_zat)
    else:
        max_ZAT_h_unocc = ZAT_heat_threshold
    #
    if ((c_val + h_val + vent_val) > 0.3):
        percent_l, percent_h, percent_c, med_num_op_hrs, per_hea_coo, \
                 percent_HV = get_CBECS(area)
        c_savings = (ZAT_cool_threshold-min_ZAT_c_unocc) * 0.03 * c_val * \
                percent_c * elec_cost * percent_unocc
        h_savings = (max_ZAT_h_unocc-ZAT_heat_threshold) * 0.03 * h_val * \
                percent_h * elec_cost * percent_unocc
        ven_savings = 0.06* vent_val * elec_cost * percent_unocc
        return {
            'Problem': "Nighttime thermostat setbacks are not enabled.",
            'Diagnostic': "More than 30 percent of the data indicates that the " + \
                    "building is being conditioned or ventilated normally " + \
                    "during unoccupied hours.",
            'Recommendation': "Program your thermostats to decrease the " + \
                    "heating setpoint, or increase the cooling setpoint during " + \
                    "unoccuppied times.  Additionally, you may have a " + \
                    "contractor configure the RTU to reduce ventilation.",
            'Savings': round((c_savings + h_savings + ven_savings), 2)}
    else:
        return {}

def _grab_data(DAT, ZAT, copyTemp, HVACstat=None):
    """
    Separates data out into when it is cooling, heating, or venting.

    Parameters
        DAT - array of diffuser air temperatures
        ZAT - array of zone air temperatures
        copyTemp - data needed to separate
        HVACstat - array of HVAC statuses

    Returns:
        cool_on - data points in copyTemp that is considered 'cooling'
        heat_on - datat points in copyTemp that is considered 'heating'
        vent_on - number of points in which ventilation is on
    """

    cool_on = []
    heat_on = []
    vent_on = 0
    i = 0

    while (i < len(DAT)):
        if ((ZAT[i][1] > 55) and (ZAT[i][1] < 80)):
            # if DAT is less than 90% of ZAT, it's cooling
            if (DAT[i][1] < (0.9 * ZAT[i][1])):
                # If there's HVAC, make sure it's actually cooling
                if (HVACstat):
                    if (HVACstat[i][1] != 2):
                        i += 1
                        continue
                cool_on.append(copyTemp[i][1])
            # if DAT greater than 110% ZAT, then it's heating
            elif (DAT[i][1] > (1.1 * ZAT[i][1])):
                # if there's HVAC status, make sure it's actually heating
                if (HVACstat):
                    if (HVACstat[i][1] == 0):
                        i += 1
                        continue
                heat_on.append(copyTemp[i][1])
            elif (HVACstat):
                if (HVACstat[i][1] == 1):
                    vent_on += 1
        i += 1
    return cool_on, heat_on, vent_on


