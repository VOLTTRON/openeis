import datetime

def economizer(DAT, OAT, HVACstat):
    """
    Economizer takes in diffuser air temperature (DAT), outdoor air temperature
    (OAT), and HVAC status (HVACstat) and checks if it is economizing for more
    than 70% when it can be economizing.  If it the data indicates otherwise,
    it will return a dictionary of diagnostics.

    Parameters: DAT, OAT, HVACstat
        - DAT: diffuser air temperature
        - OAT: outdoor air temperature
        - HVACstat: HVAC status
            - HVAC: 0 - off 1 - fan 3 - compressor
        * Assume that each is a 2-D array with datetime and data
        * DAT, OAT, HVACstat should have the same number of points
        * Datetimes must match up
    Returns: a dictionary of diagnostics or None
    """
    # counts points when the economizer is on
    econ_on = 0
    # counts points when the RTU is on
    RTU_on = 0

    # iterate through all data points
    i = 0
    while (i < len(DAT)):
        if ((DAT[i][1] < 70) and (OAT[i][1] <= 65)):
            # if the economizer on, increment econ_on
            if (HVACstat[i][1] == 1):
                econ_on += 1
            # count when RTU is on
            if (HVACstat[i][1] != 0):
                RTU_on += 1
        i += 1

    # percentage is when the economizer is on
    percentage = econ_on/RTU_on
    if (percentage < 0.7):
        return {'Problem': "Under use of 'free cooling', i.e.,under-economizing.",
                'Diagnostic': "More than 30 percent of the time, the economizer is not taking advantage of 'free cooling' when it is possible to do so.",
                'Recommendation': "Ask an HVAC service contractor to check the economizer control sequence, unless the RTU does not have an economizer."}

