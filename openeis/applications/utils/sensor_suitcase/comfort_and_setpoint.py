from utils.separate_hours import separate_hours
from numpy import mean

def comfort_and_setpoint(IAT, DAT, op_hours, HVACstat=None):
    """
    Checks if the building is comfortable.

    Parameters:
        - IAT: Indoor air temperature
            - 2d array with each element as [datetime, data]
        - DAT: Diffuser air temperature
            - 2d array with each element as [datetime, data]
        - HVACstat (optional): HVAC status
            - 2d array with each element as [datetime, data]
        - op_hours: operational hours, list
            - [operational hours, [days operating], [holidays]]
    """
    # separate data to get occupied data
    IAT_op, IAT_non_op = \
        separate_hours(IAT, op_hours[0], op_hours[1], op_hours[2])
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
    if (HVACstat):
        HVAC_op, HVAC_non_op = \
                separate_hours(HVACstat, op_hours[0], op_hours[1], op_hours[2])

    # iterate through the data
    i = 0
    while (i < len(DAT_op)):
        # if DAT is less than 90% of IAT, it's cooling
        if (DAT_op[i][1] < (0.9 * IAT_op[i][1])):
            # If there's HVAC, make sure it's actually cooling
            if (HVACstat):
                if (HVAC_op[i][1] != 3):
                    continue
            # if DAT is less than 75 F, it's over cooling
            if (DAT_op[i][1] < 75):
                over_cool += 1
            # if DAT is greater than 80 F, it's under cooling
            elif (DAT_op[i][1] > 80):
                under_cool += 1
            cool_on.append(IAT_op[i][1])
        # if DAT greater than 110% IAT, then it's heating
        elif (DAT_op[i][1] > (1.1 * IAT_op[i][1])):
            # if there's HVAC status, make sure it's actually heating
            if (HVACstat):
                if (HVAC_op[i][1] == 0):
                    continue
            # if DAT is less than 69 F, it's under heating
            if (DAT_op[i][1] < 69):
                under_heat += 1
            # if DAT is over 72 F, it's over heating
            elif (DAT_op[i][1] > 72):
                over_heat += 1
            heat_on.append(IAT_op[i][1])
        i += 1

    heating_setpt = mean(heat_on)
    cooling_setpt = mean(cool_on)

    if ((heating_setpt > 76) and (cooling_setpt < 72)):
        setpoint_flag = True
    else:
        setpoint_flat = False

    if (over_cool/len(DAT_op) > 0.3):
        comfort_flag = "Over cooling flag"
    elif (under_cool/len(DAT_op) > 0.3):
        comfort_flag = "Under cooling flag"
    elif (over_heat/len(DAT_op) > 0.3):
        comfort_flag = "Over heating flag"
    elif (under_heat/len(DAT_op) > 0.3):
        comfort_flag = "Under heating flag"
    else:
        comfort_flag = False

    return comfort_flag, setpoint_flag


