"""
Utility functions that convert inputs to desired units.


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


def convertCelciusToFahrenheit(temperature):
    """
    Convert `temperature` from Celcius to Fahrenheit.

    Parameters:
        - `temperature`, array-like sequence of temperatures [C] (float).
    Returns:
        - `temperature`, array-like sequence of temperatures in [F] (float).
    """
    return ( np.add(np.multiply(temperature,1.8),32.))


def convertFahrenheitToCelcius(temperature):
    """
    Convert `temperature` from Fahrenheit to Celcius.

    Parameters:
        - `temperature`, array-like sequence of temperatures [C] (float).
    Returns:
        - `temperature`, array-like sequence of temperatures in [F] (float).
    """
    return ( np.divide(np.subtract(temperature,32.),1.8) )


def convertKelvinToCelcius(temperature):
    """
    Convert `temperature` in Celcius to Kelvin.

    Parameters:
        - `temperature`, array-like sequence of temperatures [C] (float).
    Returns:
        - `temperature`, array-like sequence of temperatures in [F] (float).
    """
    return ( np.subtract(temperature,273.15) )


def getFactor_powertoKW(powerUnit):
    """
    Find factor to convert power to kW.

    Parameters:
        - `powerUnit`, current unit of measure of power (string).
    Returns:
        - `conversionFactor`, multiplier to convert to [kW].
    Throws:
        - ValueError if `powerUnit` not recognized.
    """
    assert( type(powerUnit) == str )

    # Find conversion factor associated with prefix of {powerUnit}.
    #   Convert to {kilo-baseUnit}.  For example:
    # - 'kilowatt' --> 1*'kilo-watt'
    # - 'horsepower' --> 1e-3*'kilo-horsepower'
    baseUnit = powerUnit
    conversionFactor = 1e-3
    if( powerUnit.startswith('milli') ):
        baseUnit = powerUnit[5:]
        conversionFactor = 1e-6  # 1e-3 / 1e3
    elif( powerUnit.startswith('kilo') ):
        baseUnit = powerUnit[4:]
        conversionFactor = 1
    elif( powerUnit.startswith('mega') ):
        baseUnit = powerUnit[4:]
        conversionFactor = 1e3  # 1e6 / 1e3
    elif( powerUnit.startswith('giga') ):
        baseUnit = powerUnit[4:]
        conversionFactor = 1e6  # 1e9 / 1e3

    # Here, {conversionFactor} * {powerUnit} --> {kilo-baseUnit}.
    # Continue converting {baseUnit} to [W].
    if( 'btus_per_hour' == baseUnit ):
        conversionFactor *= 0.29307107  # 1 BTU/hr [=] 0.29307107 W
    elif( 'foot_pounds_per_second' == baseUnit ):
        conversionFactor *= 1.35581795  # 1 ft-lb/s [=] 1.35581795 W
    elif( 'horsepower' == baseUnit ):
        conversionFactor *= 745.699872
    elif( 'joules_per_hour' == baseUnit ):
        conversionFactor /= 3600  # (1 J/s)*(60 s/min)*(60 min/hr) [=] 1 W
    elif( 'tons_refrigeration' == baseUnit ):
        conversionFactor *= 3.5168525e-3  # 1 RT [=] 3.5168525 kW
    elif( 'watt' != baseUnit ):
        raise ValueError( 'Unknown unit for power: [{}]'.format(powerUnit) )

    return ( conversionFactor )


def conversiontoKBTU(energyUnits):
    """
    Find factor to convert energy to kBTU.

    Parameters:
        - `energyUnits`, current unit of measure of energy (string).
    Returns:
        - `conversionFactor`, multiplier to convert to [kBTU].
    """
    # TODO: Need to tighten this up, to match fcn getFactor_powertoKW().
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
