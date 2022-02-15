"""Simple wrapper to make time more managable

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-02-15 16:47:15 +0000 (Tue, February 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time
import datetime


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

def now() -> Time:
    """:return a Time instance representing now"""
    return Time(time.time())

def timeStamp():
    """:return a string that can be used as a timestamp
    """
    return datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')


day = 24 * 3600.0
week = 7 * day
year = 365 * day
