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

def get_CBECS(area):
    """
    Grab CBECS data used to calculate savings in Sensor Suitcase algorithms.
    """
    if (area <= 5000):
        percentLe = 0.24
        percentH = 0.31
        percentC = 0.07
        medNumOpHrs = 48
        perHeaCoo = 0.38
        percentHV = 0.16
    elif ((area > 5001) and (area <= 10000)):
        percentLe = 0.31
        percentH = 0.38
        percentC = 0.07
        medNumOpHrs = 50
        perHeaCoo = 0.45
        percentHV = 0.18
    elif ((area > 10001) and (area <= 25000)):
        percentLe = 0.37
        percentH = 0.42
        percentC = 0.06
        medNumOpHrs = 55
        perHeaCoo = 0.48
        percentHV = 0.16
    else:
        percentLe = 0.34
        percentH = 0.39
        percentC = 0.08
        medNumOpHrs = 60
        perHeaCoo = 0.47
        percentHV = 0.2
    return percentLe, percentH, percentC, medNumOpHrs, perHeaCoo, percentHV

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
