"""Simple wrapper to make time more managable

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
__dateModified__ = "$dateModified: 2017-07-07 16:33:00 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time


class Time(float):
    """Simple class to print time in ascii, represented as floats as in time.time()"""

    def __str__(self):
        """Print as a string"""
        return time.asctime(time.localtime(self))

    def __add__(self, other):
        t = float(self) + float(other)
        return Time(t)

    def __sub__(self, other):
        t = float(self) - float(other)
        return Time(t)

    @staticmethod
    def fromString(string):
        """Make from a string, inverse of __str__"""
        return Time(time.mktime(time.strptime(string)))


#end class

def now():
    return Time(time.time())


day = 24 * 3600.0
week = 7 * day
year = 365 * day
