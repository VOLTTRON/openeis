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

