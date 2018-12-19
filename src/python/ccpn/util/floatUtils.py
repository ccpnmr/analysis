"""
fExp and fMan are the functions giving the exponent and mantissa of the decimal floating point representation of a float then we'd expect the following statements to all return true:

fExp(154.3) == 2.0
fMan(154.3) == 1.543
fExp(-1000) == 3
fMan(-1000) == -1

fRepr(number) -> (mantissa, exponent)

fRound(number) -> round to nearest base-10 value;
fRound(154.3) == 200

Solution taken from: https://stackoverflow.com/questions/45332056/decompose-a-float-into-mantissa-and-exponent-in-base-10-without-strings
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from decimal import Decimal
import math


def fExp(number) -> int:
    (sign, digits, exponent) = Decimal(number).as_tuple()
    return int(len(digits) + exponent - 1)


def fMan(number) -> float:
    return float(Decimal(number).scaleb(-fExp(number)).normalize())


def fRepr(number) -> tuple:
    """base10 equivalent of math.frepr"""
    return (fMan(number), fExp(number))


def fRound(number) -> float:
    """round to nearest base-10 value"""
    f, e = fRepr(number)
    f = float(int(f + 0.5))
    return f * math.pow(10.0, e)
