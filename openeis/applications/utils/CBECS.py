"""
Grab CBECS data used to calculate savings in Sensor Suitcase algorithms.
"""

def getCBECS(area):
    if (area <= 5000):
        percentLe = 0.24
        percentH = 0.31
        percentC = 0.07
        medNumOpHrs = 48
        perHeaCoo = 0.38
        percentHVe = 0.16
    elif ((area > 5001) and (area <= 10000)):
        percentLe = 0.31
        percentH = 0.38
        percentC = 0.07
        medNumOpHrs = 50
        perHeaCoo = 0.45
        percentHVe = 0.18
    elif ((area > 10001) and (area <= 25000)):
        percentLe = 0.37
        percentH = 0.42
        percentC = 0.06
        medNumOpHrs = 55
        perHeaCoo = 0.48
        percentHVe = 0.16
    else:
        percentLe = 0.34
        percentH = 0.39
        percentC = 0.08
        medNumOpHrs = 60
        perHeaCoo = 0.47
        percentHVe = 0.2
    return [percentLe, percentH, percentC, medNumOpHrs, perHeaCoo, percentHVe]
