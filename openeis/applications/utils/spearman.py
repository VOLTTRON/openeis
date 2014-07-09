"""Find Spearman rank correlation coefficient between two arrays."""


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
