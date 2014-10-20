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
from numpy import mean
from datetime import datetime
from openeis.applications.utils.sensor_suitcase.utils import get_CBECS, separate_hours

def comfort_and_setpoint(ZAT, DAT, op_hours, area, elec_cost, HVACstat=None):
    """
    Checks if the building is comfortable and if the setpoints are too narrow.

    Parameters:
        - ZAT: Zone air temperature
            - 2d array with each element as [datetime, data]
        - DAT: Discharge air temperature
            - 2d array with each element as [datetime, data]
        - HVACstat (optional): HVAC status
            - 2d array with each element as [datetime, data]
        - op_hours: operational hours, list
            - [operational hours, [days operating], [holidays]]
        - elec_cost: The electricity cost used to calculate savings.
    Returns:
        - setpoint_flag: Dictionary of the problem, diagnostic, recommendation,
            and savings if there is an issue, otherwise is False.
        - comfort_flag: Dictionary of the problem, diagnostic, recommendation,
            and savings if there is an issue, otherwise is False.
    """
    # separate data to get occupied data
    ZAT_op, ZAT_non_op = \
        separate_hours(ZAT, op_hours[0], op_hours[1], op_hours[2])
    DAT_op, DAT_non_op = \
        separate_hours(DAT, op_hours[0], op_hours[1], op_hours[2])

    # get data in which cooling/heating are considered on
    cool_on = []
    heat_on = []
    # count the times it is deamed uncomfortable
    over_cool = 0
    under_cool = 0
    over_heat = 0
    under_heat = 0

    # if there's HVAC status, separate that data
    if (HVACstat != None):
        HVAC_op, HVAC_non_op = \
                separate_hours(HVACstat, op_hours[0], op_hours[1], op_hours[2])

    # iterate through the data
    i = 0
    while (i < len(DAT_op)):
        # if DAT is less than 90% of ZAT, it's cooling
        if (DAT_op[i][1] < (0.9 * ZAT_op[i][1])):
            # If there's HVAC, make sure it's actually cooling
            if (HVACstat):
                if (HVAC_op[i][1] != 3):
                    i += 1
                    continue
            # if DAT is less than 75 F, it's over cooling
            if (DAT_op[i][1] < 75):
                over_cool += 1
            # if DAT is greater than 80 F, it's under cooling
            elif (DAT_op[i][1] > 80):
                under_cool += 1
            cool_on.append(ZAT_op[i][1])
        # if DAT greater than 110% ZAT, then it's heating
        elif (DAT_op[i][1] > (1.1 * ZAT_op[i][1])):
            # if there's HVAC status, make sure it's actually heating
            if (HVACstat):
                if (HVAC_op[i][1] == 0):
                    i += 1
                    continue
            # if DAT is less than 69 F, it's under heating
            if (DAT_op[i][1] < 69):
                under_heat += 1
            # if DAT is over 72 F, it's over heating
            elif (DAT_op[i][1] > 72):
                over_heat += 1
            heat_on.append(ZAT_op[i][1])
        i += 1

    # Calculate the average
    cooling_threshold = 76.
    heating_threshold = 72.
    #
    if heat_on != []:
        heating_setpt = mean(heat_on)
    else:
        heating_setpt = heating_threshold

    if cool_on != []:
        cooling_setpt = mean(cool_on)
    else:
        cooling_setpt = cooling_threshold

    percent_l, percent_h, percent_c, med_num_op_hrs, per_hea_coo, \
                 percent_HV = get_CBECS(area)
    #
    percent_op = len(ZAT_op)/len(ZAT)
    over_cooling_perc = over_cool/len(DAT_op)
    over_heating_perc = over_heat/len(DAT_op)
    #
    percent_cooling = over_cooling_perc * percent_c * percent_op
    cooling_savings = (cooling_threshold - cooling_setpt) * 0.03 * percent_cooling *elec_cost
    #
    percent_heating = over_heating_perc * percent_h * percent_op
    heating_savings = (heating_setpt - heating_threshold) * 0.03 * percent_heating *elec_cost

    if ((heating_setpt > heating_threshold) and (cooling_setpt < cooling_threshold)):
        setpoint_flag = {
        'Problem': "Overly narrow separation between heating " + \
                "and cooling setpoints.",
        'Diagnostic': "During occupied hours, the cooling setpoint was lower " + \
                "than 76F and the heating setpoint was greater than 72F.",
        'Recommendation': "Adjust the heating and cooling setpoints so that " + \
                "they differ by more than four degrees.",
        'Savings': round(cooling_savings + heating_savings, 2)
        }
    else:
        setpoint_flag = {}

    if (over_cooling_perc > 0.3):
        comfort_flag = {
        'Problem': "Over-conditioning, thermostat cooling setpoint is low",
        'Diagnostic': "More than 30 percent of the time, the cooling setpoint " + \
                "during occupied hours was lower than 75F, a temperature that " + \
                "is comfortable to most occupants",
        'Recommendation': "Program your thermostats to increase the cooling " + \
                "setpoint during occupied hours.",
        'Savings': round(cooling_savings, 2)
        }
    elif (under_cool/len(DAT_op) > 0.3):
        comfort_flag =  {
        'Problem': "Under-conditioning, thermostat cooling " + \
                "setpoint is high.",
        'Diagnostic':  "More than 30 percent of the time, the cooling setpoint " + \
                "during occupied hours was greater than 80F.",
        'Recommendation': "Program your thermostats to decrease the cooling " + \
                "setpoint to improve building comfort during occupied hours."
        }
    elif (over_heating_perc > 0.3):
        comfort_flag = {
        'Problem': "Over-conditioning, thermostat heating " + \
                "setpoint is high.",
        'Diagnostic': "More than 30 percent of the time, the heating setpoint " + \
                "during occupied hours was greater than 72F, a temperature that " + \
                "is comfortable to most occupants.",
        'Recommendation': "Program your thermostats to decrease the heating " + \
                "setpoint during occupied hours.",
        'Savings': round(heating_savings, 2)
        }
    elif (under_heat/len(DAT_op) > 0.3):
        comfort_flag = {
        'Problem': "Under-conditioning - thermostat heating " + \
                "setpoint is low.",
        'Diagnostic': "For more than 30% of the time, the cooling setpoint " + \
                "during occupied hours was less than 69 degrees F.",
        'Recommendation': "Program thermostats to increase the heating " + \
                "setpoint to improve building comfort during occupied hours."
        }
    else:
        comfort_flag = {}

    return comfort_flag, setpoint_flag

