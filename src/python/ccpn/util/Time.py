"""Simple wrapper to make time more managable

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": gvuister $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

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
day = 24*3600.0
week = 7*day
year = 365*day
