"""Calculate the parameters for the Day-Time-Temperature baseline model."""


#--- Provide access.
#
import datetime as dt
import numpy as np

def findDateIndex(datelist, locatedate):
    """Given a list of date objects, return index of a specific date."""
    
    ctr = 0
    dateIndex = None
    while ctr < len(datelist):
        if (datelist[ctr].year == locatedate.year) & (datelist[ctr].month == locatedate.month) & (datelist[ctr].day == locatedate.day): 
           dateIndex = ctr 
           break
        else:
           ctr += 1
    if (dateIndex == None): 
        newlocatedate = locatedate - dt.timedelta(days=1)
        dateIndex = findDateIndex(datelist, newlocatedate)
         
    return dateIndex
        

def getBins(oat, binCt):
    """
    Determines boundary values for `binCt` bins
    - binCt, the number of bins desired
    - oat, outdoor air temperature vector for the period of interest
    
    Outputs:
    - boundary values for bins (binCt-1)
    ***The functions using this don't work properly for 2 bins
        If there is an issue in testing 2 bin change pt models, I can adjust"""
    L = 2 # low end percentile of OAT to use for binned portion
    H = 100-L
    [TL, TH] = np.percentile(oat, [L,H])
    if binCt > 2:
        B = np.arange(TL,TH,(TH-TL)/(binCt-1))
    else:
        B=list([np.median(oat)])
    return B
    
def getTc(oat,B):
    """ 
    Returns Tc values
    oat = outdoor air temperature (as vector)
    B = vector of divisions between bins (use 'getBins')
    Output:
    Tc = matrix of values for component temps.
        Each row represents one value in oat
    """
    B=np.array(B)
    #Tc=np.tile(oat*0,(1,len(B)+1))
    Tc=np.zeros((len(oat),(len(B)+1)))
    
    # Writes Tc according to Mathieu, Price et al 2011
    oatt=np.reshape(oat,len(oat))
    Tc[:,0]=oatt
    Tc[oatt>B[0],0]=B[0]

    for i in range(1,len(B)):  #last call is for i=len(B)-1
        tempA=np.array((oatt<=B[i]) & (oatt>B[i-1]))
        Tc[tempA,i]=oatt[tempA]-B[i-1]
        Tc[oatt>B[i],i]=B[i]-B[i-1]
    tempB=np.array(oatt>B[len(B)-1])
    Tc[:,len(B)]=(oatt-B[len(B)-1])*tempB
    return Tc
    

def findThresholdValue(datevec, e):
    """Find the threshold value for each time of day."""
    tv=[0,0,0,0,0,0,0]
    dow=np.array([x.weekday() for x in datevec])    # day of week vector
    for i in range(0,7):
        [L10, L90] = np.percentile(e[dow==i], [10,90])
        tv[i] = L10 + 0.1*(L90-L10) #threshhold value for 'occupied'
    return tv


def _getOccupiedTime(datevec, medianval, timeStepMinutes, thresholdvec):
    """
    Return array showing `True` (occupied) or `False` (unoccupied), based on
    comparing the median entry in `medianval` at a given time, against the day-of-week
    threshhold in `thresholdvec`.

    Array indices:
    - dow, day-of-week
    - hod, hour-of-day
    - moh, minute-of-hour
    """
    dow = np.array([x.weekday() for x in datevec])  # day of week vector
    hod = np.array([x.hour for x in datevec])       # hour of day vector
    moh = np.array([x.minute for x in datevec])     # minutes 
    timeDiv = int(round(60/timeStepMinutes))           # of timesteps per hour
    
    OvU = np.ones([7,24,timeDiv], dtype=bool)
    
    tint=round(timeStepMinutes/60)
    for i in range(0,7):
        threshold = thresholdvec[i] #threshold value for 'occupied'
        for j in range(0,24):
            for k in range(1,tint+1):
                mask = (dow==i) & (hod==j) & (moh==(k-1)*timeStepMinutes)
                if( np.any(mask) ):
                    OvU[i,j,k-1] = (np.median(medianval[mask]) > threshold)
    return OvU


def sch2vec(OvU,datevec,timeStepMinutes):
    """Converts schedule of occupied vs non-occupied table to values for specific date vector."""
    Ovec = np.array([OvU[x.weekday(),x.hour,round(x.minute/timeStepMinutes)] for x in datevec], dtype=bool)
    return Ovec


def getA(datevec,oat,timeStepMinutes,B):
    oat = oat.reshape(len(oat),1)
    if len(B)>1:
        oatM=getTc(oat,B)
    else:
        oatM=np.array(oat)
        oatM=oatM.reshape(len(oatM),1)
    tint=round(timeStepMinutes/60)
    L=24*tint*7 # time steps per week (# of alpha values)
    Ap=np.zeros((len(datevec),L))
    for i in range(0,len(datevec)):
        Nt=round(datevec[i].minute/tint)+datevec[i].hour*tint+datevec[i].weekday()*24*tint
        Ap[i,Nt]=1
    # Unoccupied type implementation: temp term and alpha for each TOW
    a=np.hstack((oatM,Ap))
    return a


def formModel(timesTrain, oatsTrain, valsTrain, timeStepMinutes, binCt):
    """
    Form the temperature-time-of-week model (i.e., perform the training stage).

    Arguments:
    - `timesTrain`, times with which to train model.
      A `np.ndarray` of `dt.datetime` objects.
    - `oatsTrain`, outdoor air temperatures with which to train model.
      A `np.ndarray` of floats.
    - `valsTrain`, energy use values with which to train model.
      A `np.ndarray` of floats.
    - `timeStepMinutes`, time step in minutes (15, 60).
    - `binCt`, number of bins for piecewise temperature model.
      Choose 1 for no piecewise.

    Returns:
    - Dictionary of information representing the model.
    """
    # TODO: Document what the information in the model means.

    # Check inputs.
    
    timesTrain = np.array(timesTrain)
    assert( timesTrain.ndim == 1 )
    assert( type(timesTrain[0]) is dt.datetime )

    oatsTrain = np.array(oatsTrain)
    assert( oatsTrain.ndim == 1 )
    assert( len(oatsTrain) == len(timesTrain) )
    assert( isinstance(oatsTrain[0], float) )

    valsTrain = np.array(valsTrain)
    assert( valsTrain.ndim == 1 )
    assert( len(valsTrain) == len(timesTrain) )
    assert( isinstance(valsTrain[0], float) )

    assert( np.isfinite(timeStepMinutes) )
    assert( timeStepMinutes > 0 )

    assert( type(binCt) is int )
    assert( binCt > 0 )
    
    thresholdval = findThresholdValue(timesTrain, valsTrain)
    OvU = _getOccupiedTime(timesTrain, valsTrain, timeStepMinutes, thresholdval)  
    # Specifies occ(1) or unoc(0) for each [dow,hod,increment of hour]
    Ovec = sch2vec(OvU, timesTrain, timeStepMinutes)  
    # Converts schedule to 0/1 for specific vector of dates

    # Occupied
    B = getBins(oatsTrain, binCt)
    sc = (np.isnan(valsTrain)==False) & (np.isnan(oatsTrain)==False) & Ovec
    a=getA(timesTrain[sc],oatsTrain[sc],timeStepMinutes,B)
    aN=a[:,np.sum(a,0)>0]
    w=np.linalg.lstsq(aN,valsTrain[sc])[0]
    wN=np.zeros(len(a[1,:]))
    wN[np.sum(a,0)>0]=w
    # Unoccupied
    scU = (np.isnan(valsTrain)==False) & (np.isnan(oatsTrain)==False) & (Ovec==False)
    aU=getA(timesTrain[scU],oatsTrain[scU],timeStepMinutes,[1])
    aUN=aU[:,np.sum(aU,0)>0]
    wU=np.linalg.lstsq(aUN,valsTrain[scU])[0]
    wUN=np.zeros(len(aU[1,:]))
    wUN[np.sum(aU,0)>0]=wU

    return( {
        'timeStepMinutes':timeStepMinutes,
        'B':B,
        'wN':wN,
        'wUN':wUN,
        'OvU':OvU
        # TODO: Consider adding further information, like `binCt` and some stats on training data.
        })
        
        
def applyModel(ttowModel, datevec, oat):
    """
    Calculates modeled energy based on parameters in ttowModel[`wN`], by forming matrix A
    Will work for different model forms as long as `wN` matches A in form
    """
    # Unpack model.
    timeStepMinutes = ttowModel['timeStepMinutes']
    B = ttowModel['B']
    wN = ttowModel['wN']
    wUN = ttowModel['wUN']
    OvU = ttowModel['OvU']
    datevec = np.array(datevec)
    oat = np.array(oat)

    Ovec=sch2vec(OvU,datevec,timeStepMinutes)
    
    #Occupied
    sc = (np.isnan(oat)==False) & Ovec
    a = getA(datevec[sc],oat[sc],timeStepMinutes,B)
    em=np.dot(a,wN)
    Eall=np.nan*sc
    Eall[sc]=em
    
    #Unoccupied
    scU = (np.isnan(oat)==False) & (Ovec==False)
    aU=getA(datevec[scU],oat[scU],timeStepMinutes,list([1]))
    emU=np.dot(aU,wUN)
    Eall[scU]=emU

    return Eall