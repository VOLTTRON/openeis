from datetime import datetime, timedelta

def short_cycling(HVAC_stat):
    """
    Checks to see if the HVAC is short cycling.

    Parameter:
        - HVAC_stat: HVAC status
            - 2d array with [datetime, data]
            - data is 0 - off, 1 - fan is on, 2 - compressor on
    Return:
        - True if the problem should be flagged
    """
    compressor_on = []
    for point in HVAC_stat:
        if (point[1] == 3):
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

    print("hoho: ", fault_count)

    if (fault_count > 10):
        return True
