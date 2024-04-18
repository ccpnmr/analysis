"""Simple wrapper to make time more managable


from https://strftime.org/
%a	Sun	    Weekday as locale’s abbreviated name.
%A	Sunday	Weekday as locale’s full name.
%w	0	    Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
%d	08	    Day of the month as a zero-padded decimal number.
%-d	8	    Day of the month as a decimal number. (Platform specific)
%b	Sep	    Month as locale’s abbreviated name.
%B	September	Month as locale’s full name.
%m	09	    Month as a zero-padded decimal number.
%-m	9	    Month as a decimal number. (Platform specific)
%y	13	    Year without century as a zero-padded decimal number.
%Y	2013	Year with century as a decimal number.
%H	07	    Hour (24-hour clock) as a zero-padded decimal number.
%-H	7	    Hour (24-hour clock) as a decimal number. (Platform specific)
%I	07	    Hour (12-hour clock) as a zero-padded decimal number.
%-I	7	    Hour (12-hour clock) as a decimal number. (Platform specific)
%p	AM	    Locale’s equivalent of either AM or PM.
%M	06	    Minute as a zero-padded decimal number.
%-M	6	    Minute as a decimal number. (Platform specific)
%S	05	    Second as a zero-padded decimal number.
%-S	5	    Second as a decimal number. (Platform specific)
%f	000000	Microsecond as a decimal number, zero-padded to 6 digits.
%z	+0000	UTC offset in the form ±HHMM[SS[.ffffff]] (empty string if the object is naive).
%Z	UTC	    Time zone name (empty string if the object is naive).
%j	251	    Day of the year as a zero-padded decimal number.
%-j	251	    Day of the year as a decimal number. (Platform specific)
%U	36	    Week number of the year (Sunday as the first day of the week) as a zero-padded decimal number. All days in a new year preceding the first Sunday are considered to be in week 0.
%-U	36	    Week number of the year (Sunday as the first day of the week) as a decimal number. All days in a new year preceding the first Sunday are considered to be in week 0. (Platform specific)
%W	35	    Week number of the year (Monday as the first day of the week) as a zero-padded decimal number. All days in a new year preceding the first Monday are considered to be in week 0.
%-W	35	    Week number of the year (Monday as the first day of the week) as a decimal number. All days in a new year preceding the first Monday are considered to be in week 0. (Platform specific)
%c	Sun Sep 8 07:06:05 2013	Locale’s appropriate date and time representation.
%x	09/08/13	Locale’s appropriate date representation.
%X	07:06:05	Locale’s appropriate time representation.
%%	%	    A literal '%' character.

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-04-18 14:07:55 +0100 (Thu, April 18, 2024) $"
__version__ = "$Revision: 3.2.4 $"
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

    def date(self, format='%Y-%m-%d') -> str:
        """return date part of self formatted by format
        :param format: a valid datetime.strftime format string (see module doc above)
        """
        st = datetime.datetime.fromtimestamp(self)
        return st.strftime(format)

    def time(self, format='%H:%M:%S') -> str:
        """return time part of self formatted by format
        :param format: a valid datetime.strftime format string (see module doc above)
        """
        st = datetime.datetime.fromtimestamp(self)
        return st.strftime(format)

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
