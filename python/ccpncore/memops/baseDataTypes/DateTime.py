""" NB this is a temporary implementation as a plain string. We will need a proper
dataTime type at some point


======================COPYRIGHT/LICENSE START==========================

DateTime.py: Basic data type implementation for CCPN Python data model API

Copyright (C) 2005 Rasmus Fogh (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../../../../license/LGPL.license
 
This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.
 
You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)

- email: ccpn@bioc.cam.ac.uk

=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
Rasmus H. Fogh, Wayne Boucher, Wim F. Vranken, Anne
Pajon, Tim J. Stevens, T.N. Bhat, John Westbrook, John M.C. Ionides and
Ernest D. Laue (2005). A framework for scientific data modeling and automated
software development. Bioinformatics 21, 1678-1684.

===========================REFERENCE END===============================
"""
import time

# Time class for use in reworking nthis type.

class Time(float):
    """Simple class to print time in ascii, represented as floats as in time.time()"""
    day = 24*3600.0
    week = 7*day
    year = 365*day

    def __str__(self):
        """Print as a string"""
        # equivalent to time.asctime(time.localtime(self))
        return time.ctime(self)

    def __repr__(self):
        return 'Time(%s)' % float.__repr__(self)

    @staticmethod
    def fromString(string):
        """Make from a string, inverse of __str__"""
        try:
          return Time(string)
        except ValueError:
          return Time(time.mktime(time.strptime(string)))

    @staticmethod
    def now():
        return Time(time.time())
#end class


# corresponding python type
PythonType = Time

# Python types acceptable as input instead of main type
compatibleTypes = (str, float)

# Special isValid function
# None

# conversion to String
toString  = str

# conversion from string
fromString = Time.fromString

# casting/creation function.
create = Time