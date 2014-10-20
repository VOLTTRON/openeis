"""
General utilities to facilitate testing.


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


import math
import datetime

# Taken from reference code
def findMean(xxs):
    """
    Find the mean of non-``NAN`` entries in a vector *xxs*.

    Do so in a fairly laborious way, i.e., without relying on :mod:`numpy`,
    in order to make explict how ``NAN`` values get handled.

    Parameters:
        - xxs: a list of numbers
    Returns:
        - xxMeans: the list's mean
    """
    #
    # Find sum and count of non-``NAN`` entries.
    cts = len(xxs)
    xxSum = 0.0
    xxCt  = 0
    for idx in range(cts):
        xx = xxs[idx]
        if( not math.isnan(xx) ):
            xxSum += xx
            xxCt  += 1
    #
    # Find mean.
    if( xxSum == 0 ):
        # Here, all-``NAN`` gave ``xxCt == 0``.
        xxMean = 0
    else:
        xxMean = xxSum / xxCt
    #
    return( xxMean )
    #

# Taken directly from reference code.
def findCorrelationCoeff(xxs, yys, expectZeroMeans):
    """
    Find the correlation coefficient between two vectors *xxs* and *yys*.

    Do so in a fairly laborious way, i.e., without relying on :mod:`numpy`,
    in order to make explict how ``NAN`` values get handled.

    Parameters:
        - xxs, yys: two lists of numbers
        - expectZeroMeans: whether we expect zero means or not
    Returns:
        - corrCoeff: Spearman correlation coefficient of the two lists
    """

    cts = len(xxs)
    assert( len(yys) == cts )

    xxMean = findMean(xxs)
    yyMean = findMean(yys)
    if( expectZeroMeans ):
        assert( math.fabs(xxMean) < 1e-20 )
        xxMean = 0
        assert( math.fabs(yyMean) < 1e-20 )
        yyMean = 0

    xyAccum = 0.0
    xxAccum = 0.0
    yyAccum = 0.0
    for idx in range(cts):
        xMinusMean = xxs[idx]
        if( math.isnan(xMinusMean) ):
            continue
        xMinusMean -= xxMean

        yMinusMean = yys[idx]
        if( math.isnan(yMinusMean) ):
            continue
        yMinusMean -= yyMean

        xyAccum += xMinusMean * yMinusMean
        xxAccum += xMinusMean * xMinusMean
        yyAccum += yMinusMean * yMinusMean

    denom = xxAccum * yyAccum
    if( denom == 0 ):
        corrCoeff = 0
    else:
        corrCoeff = xyAccum / math.sqrt(denom)
    return( corrCoeff )

def set_up_datetimes(first, last, increment):
    """
    Creates an array of datetimes with the FIRST and LAST dateimes inputted
    with INCREMENTS in seconds.  These datetimes are also in arrays for
    easy iterating and appending data.

    Parameters:
        - first: first datetime to start incrementing from
        - last: final datetime to end on
        - increment: increments in seconds (int) between each datetime
    Returns:
        -base: An array of [datetimes]
            Ex: [[[datetime.datetime(2014, 1, 1, 0, 0)],
                [datetime.datetime(2014, 1, 1, 6, 0)]]
    """
    delta = datetime.timedelta(0, increment)

    base = []
    while (first != last):
        base.append([first])
        first += delta
    base.append([last])

    return base

def append_data_to_datetime(dates, data):
    """
    Takes data and puts it into dates.  Assumes that they are the same
    length.

    Parameters:
        - dates: an array of datetimes in lists.
            Ex: [[[datetime.datetime(2014, 1, 1, 0, 0)],
                [datetime.datetime(2014, 1, 1, 6, 0)]]
        - data: an array of data
    """
    assert(len(dates) == len(data))
    i = 0
    while (i < len(dates)):
        dates[i].append(data[i])
        i += 1
