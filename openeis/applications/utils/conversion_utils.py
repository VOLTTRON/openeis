'''Utility functions that convert inputs to acceptable values.'''

#--- Provide access.
#
import numpy as np


def convertCelciusToFahrenheit(temperature):
    """
    Convert *temperature* in Celcius to Fahrenheit.

    **Args:**

    - *temperature*, array-like sequence of temperatures [C] (float).

    **Returns:**

    - *temperature*, array-like sequence of temperatures in [F] (float).
    """

    return ( np.add(np.multiply(temperature,1.8),32.))

def convertFahrenheitToCelcius(temperature):
    """
    Convert *temperature* in Fahrenheit to Celcius.

    **Args:**

    - *temperature*, array-like sequence of temperatures [C] (float).

    **Returns:**

    - *temperature*, array-like sequence of temperatures in [F] (float).
    """

    return ( np.divide(np.subtract(temperature,32.),1.8) )

def convertKelvinToCelcius(temperature):
    """
    Convert *temperature* in Celcius to Kelvin.

    **Args:**

    - *temperature*, array-like sequence of temperatures [C] (float).

    **Returns:**

    - *temperature*, array-like sequence of temperatures in [F] (float).
    """

    return ( np.subtract(temperature,273.2) )

def conversiontoKWH(energyUnits):
    """
    Convert fuel *energyValues* to kBTU.

    **Args:**

    - *energyUnits*, string that defines the current unit of measure of *energyValues*.

    **Returns:**

    - *conversionFactor*, multiplier for the .
    """

    assert ( type(energyUnits) == str)

    conversionFactor = 1 
    # Convert everything to BTU first then convert to kBTU.
    #- Prefix Finder
    if 'milli' in energyUnits:
        conversionFactor = 1.0E-3
    elif 'kilo' in energyUnits:
        conversionFactor = 1.0E+3    
    elif 'mega' in energyUnits:
        conversionFactor = 1.0E+6    
    elif 'giga' in energyUnits:
        conversionFactor = 1.0E+9
        
    #- Base Finder, convert to watt-hour
    if 'joule' in energyUnits:
        conversionFactor = conversionFactor / 3.6E+3
    elif 'btus' in energyUnits:
        conversionFactor = conversionFactor / 3.412
    
    return ( conversionFactor / 1000.)

def conversiontoKBTU(energyUnits):
    """
    Convert fuel *energyValues* to kBTU.

    **Args:**

    - *energyUnits*, string that defines the current unit of measure of *energyValues*.

    **Returns:**

    - *conversionFactor*, multiplier for the .
    """

    assert ( type(energyUnits) == str)

    conversionFactor = 1 
    # Convert everything to BTU first then convert to kBTU.
    #- Prefix Finder
    if 'milli' in energyUnits:
        conversionFactor = 1.0E-3
    elif 'kilo' in energyUnits:
        conversionFactor = 1.0E+3    
    elif 'mega' in energyUnits:
        conversionFactor = 1.0E+6    
    elif 'giga' in energyUnits:
        conversionFactor = 1.0E+9
        
    #- Base Finder, convert to btus
    if 'joule' in energyUnits:
        conversionFactor = conversionFactor * (3.412 / 3.6E+3 )
    elif 'watt' in energyUnits:
        conversionFactor = conversionFactor * 3.412
    
    return ( conversionFactor / 1000.)
    
