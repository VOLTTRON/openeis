"""
Find Spearman rank correlation coefficient between two arrays.


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


#--- Provide access.
#
import numpy as np


def findSpearmanRank(xValues, yValues):
    """
    Given two arrays, find the Spearman rank correlation coefficient.

    **Args:**

    - *xValues* and *yValues*, array-like sequences of values.

    **Returns:**

    - *spearmanCoeff*, the Spearman rank correlation coefficient between the arrays.

    **Notes:**

    - Assume arguments do not contain any missing or corrupt values (i.e., no ``NAN``
      entries).
    - "Array-like" means list, tuple, numpy array, etc.
    """
    #
    # Check inputs.
    valCt = len(xValues)
    assert( valCt > 1 )
    assert( len(yValues) == valCt )
    #
    # Require numpy arrays with floating-point numbers.
    # TODO: Not sure need to do this anymore, since no longer allowing NaNs.
    if( type(xValues)!=np.ndarray or isinstance(xValues[0],int) ):
        xValues = np.array(xValues, dtype=np.float)
    if( type(yValues)!=np.ndarray or isinstance(yValues[0],int) ):
        yValues = np.array(yValues, dtype=np.float)
    #
    # Rank the values.
    xRanks = _rankForSpearman(xValues)
    yRanks = _rankForSpearman(yValues)
    #
    # Subtract out mean rank, so each resulting vector has mean of zero.
    xRanks = xRanks - xRanks.mean()
    yRanks = yRanks - yRanks.mean()
    #
    # Find Spearman rank correlation coefficient.
    spearmanCoeff = np.inner(xRanks, yRanks) / np.sqrt(
        np.inner(xRanks,xRanks) * np.inner(yRanks,yRanks)
        )
    #
    return( spearmanCoeff )
    #
    # End :func:`findSpearmanRank`.


def _rankForSpearman(values):
    """
    Find the ranks of a vector *values*, as defined for Spearman rank correlation coefficient.

    **Args:**

    - *values*, array-like sequences of values.

    **Notes:**

    - Rank smallest to largest.
    - Equal values get mean rank.
    - Assume argument does not contain any missing or corrupt values (i.e., no ``NAN``
      entries).
    """
    #
    # TODO:  Look into doing something easier, like this:
    # srtdToActIdx = np.argsort(values)
    # ranks = np.zeros(valCt)
    # ranks[srtdToActIdx] = numpy.arange(valCt)
    #   Then run through the ranks and find stretches with same values.
    #
    # TODO: Remove these, since they probably will turn out to be needless
    # requirements, given that NaNs are no longer an issue.
    # assert( type(values) == np.ndarray )
    # assert( values.ndim == 1 )
    #
    # Initialize.
    valCt = len(values)
    #
    # Find indices that would sort *values*.
    #   Example:
    # - values       = [1, 2, 5, 4, 3]
    # - srtdToActIdx = [0, 1, 4, 3, 2]
    srtdToActIdx = np.argsort(values)
    #
    # Step through *values* in sorted order, assigning ranks.
    ranks = np.zeros(valCt)
    lastVal = values[srtdToActIdx[0]]
    startRunIdx = 0
    currIdx = 1
    while( currIdx < valCt ):
        #
        currVal = values[srtdToActIdx[currIdx]]
        #
        # Assign ranks if *currVal* breaks a run of equal entries.
        if( currVal > lastVal ):
            # Here, indices *startRunIdx* to *currIdx*-1, inclusive, all had
            # the same value (*lastVal*).
            #   Their "natural" ranks are *startRunIdx*+1 to *currIdx*,
            # inclusive.  Assign all the indices the mean rank.
            #   Examples:
            # - startRunIdx=0, currIdx=1 ==> mean(1) ==> meanRank=1
            # - startRunIdx=0, currIdx=2 ==> mean(1,2) ==> meanRank=1.5
            # - startRunIdx=0, currIdx=5 ==> mean(1,2,3,4,5) ==> meanRank=3
            # - startRunIdx=1, currIdx=2 ==> mean(2) ==> meanRank=2
            # - startRunIdx=1, currIdx=4 ==> mean(2,3,4) ==> meanRank=3
            # - startRunIdx=1, currIdx=5 ==> mean(2,3,4,5) ==> meanRank=3.5
            # - startRunIdx=1, currIdx=6 ==> mean(2,3,4,5,6) ==> meanRank=4
            meanRank = 0.5 * (startRunIdx + currIdx + 1)
            while( startRunIdx < currIdx ):
                # Note that ``srtdToActIdx[startRunIdx]`` gives an index for
                # which *values* equals *lastVal*.
                ranks[srtdToActIdx[startRunIdx]] = meanRank
                startRunIdx += 1
            # Mark start of a new run.
            #   Note already have ``startRunIdx == currIdx``.
            lastVal = currVal
        #
        # Prepare for next iteration.
        currIdx += 1
    #
    # Here, still need to assign ranks for last entries inspected.
    #   This code should exactly copy that in the loop above.  There are ways
    # around this ugly duplication, but they are themselves ugly.
    meanRank = 0.5 * (startRunIdx + currIdx + 1)
    while( startRunIdx < currIdx ):
        ranks[srtdToActIdx[startRunIdx]] = meanRank
        startRunIdx += 1
    #
    # Here, *ranks* holds ranks, between 1 and *currIdx*, inclusive, for all
    # the entries in *values*.
    assert( currIdx == valCt )
    #
    return( ranks )
    #
    # End :func:`__rankForSpearman`.
