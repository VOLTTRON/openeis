from datetime import datetime
import numpy as np
from utils import get_CBECS

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

    #
    if (HVACstat):
        HVAC_op, HVAC_non_op = separate_hours(HVACstat, op_hours[0],
                op_hours[1], op_hours[2])
    else:
        HVAC_op = []
        HVAC_non_op = []
    #
    op_cool_dat, op_heat_dat, op_hvac_dat = _grab_data(DAT_op, ZAT_op, DAT_op, HVAC_op)
    non_cool_dat, non_heat_dat, non_hvac_dat = _grab_data(DAT_non_op, ZAT_non_op, DAT_non_op,
            HVAC_non_op)
    #
    avg_DAT_c_occ = np.mean(op_cool_dat)
    avg_DAT_h_occ = np.mean(op_heat_dat)
    #
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

    non_cool_zat, non_heat_zat, non_hvac_zat = _grab_data(DAT_non_op, ZAT_non_op, ZAT_non_op,HVAC_non_op)
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
        c_savings = (ZAT_cool_threshold-min_ZAT_c_unocc) * 0.03 * c_val * percent_c * elec_cost \
                * percent_unocc
        h_savings = (max_ZAT_h_unocc-ZAT_heat_threshold) * 0.03 * h_val * percent_h * elec_cost \
                * percent_unocc
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
            'Savings': round(c_savings + h_savings + ven_savings, 2)}
    else:
        return {}

def _grab_data(DAT, ZAT, copyTemp, HVACstat=None):
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
                    if (HVACstat[i][1] != 3):
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

def separate_hours(data, op_hours, days_op, holidays=[]):
    """
    Given a dataset and a building's operational hours, this function will
    separate data from operational hours and non-operational hours.

    Parameters:
        - data: array of arrays that have [datetime, data]
        - op_hours: operational hour for the building in military time
            - i.e. [9, 17]
        - days_op: days of the week it is operational as a list
            - Monday = 1, Tuesday = 2 ... Sunday = 7
            - i.e. [1, 2, 3, 4, 5] is Monday through Friday
        - holidays: a list of datetime.date that are holidays.
            - data with these dates will be put into non-operational hours
    """
    operational = []
    non_op = []
    for point in data:
        if (point[0].date() in holidays) or \
            (point[0].isoweekday() not in days_op):
            non_op.append(point)
        elif ((point[0].hour >= op_hours[0]) and (point[0].hour < op_hours[1])):
            operational.append(point)
        else:
            non_op.append(point)
    return operational, non_op
