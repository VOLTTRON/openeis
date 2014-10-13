"""
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

def economizer(DAT, OAT, HVACstat, elec_cost, area):
    """
    Economizer takes in diffuser air temperature (DAT), outdoor air temperature
    (OAT), and HVAC status (HVACstat) and checks if it is economizing for more
    than 70% when it can be economizing.  If it the data indicates otherwise,
    it will return a dictionary of diagnostics.

    Parameters: DAT, OAT, HVACstat
        - DAT: discharge air temperature
        - OAT: outdoor air temperature
        - HVACstat: HVAC status
            - HVAC: 0 - off 1 - fan 3 - compressor
        * Assume that each is a 2-D array with datetime and data
        * DAT, OAT, HVACstat should have the same number of points
        * Datetimes must match up
        - elec_cost: The electricity cost used to calculate savings.
    Returns: a dictionary of diagnostics or False
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

    # Percentage is when the economizer is on
    percentage = econ_on/RTU_on
    if (percentage < 0.7):
        return {'Problem': "Under use of 'free cooling', i.e.,under-economizing.",
                'Diagnostic': "More than 30 percent of the time, the economizer is not taking advantage of 'free cooling' when it is possible to do so.",
                'Recommendation': "Ask an HVAC service contractor to check the economizer control sequence, unless the RTU does not have an economizer.",
                'Savings': get_CBECS(area)[5] * 0.1 * elec_cost}
    else:
        return {}

