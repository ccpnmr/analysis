"""Top level application version file

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-11-11 07:54:02 +0000 (Thu, November 11, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


class VersionString(str):
    """Version-string routines, adapted from path idea in: Python Cookbook,
    A. Martelli and D. Ascher (eds), O'Reilly 2002, pgs 140-142

    A VersionString is a string with extra functionality.
    It consists of three non-empty and one optional substrings separated by a mandatory dot '.' character:

        majorVersion.minorVersion.microVersion[.release]

     Examples: 3.0.4; 3.1.0.alfa

    The isValid function checks for validity

    The majorVersion, minorVersion, microVersion and release fields are available as properties.

    A VersionString instance supports comparisons with either another VersionString instance or a suitable
    formatted string; e.g.

     VersionString('3.1.0.alfa') > VersionString('3.0.4')    yields True
     VersionString('3.1.0.alfa') < '3.0.2'    yields False

    """

    def __init__(self, string: str, **kwds):
        """First argument ('string' must be a valid pid string with at least one, non-initial PREFIXSEP
        Additional arguments are converted to string with disallowed characters changed to altCharacter
        """
        super().__init__(**kwds)  # GWV does not understand this
        self._fields = tuple(self.split('.'))

        if len(self._fields) < 3:
            raise ValueError('Invalid VersionString "%s"; expected at least 3 fields' % self)

        for name, val in zip('majorVersion minorVersion microVersion'.split(), self._fields[:3]):
            try:
                int(val)
            except:
                raise ValueError('Invalid VersionString "%s"; expected number for field "%s" ("%s")' %
                                 (self, name, val))

    @property
    def majorVersion(self) -> str:
        """return majorVersion field of self"""
        return self.fields[0]

    @property
    def minorVersion(self) -> str:
        """return minorVersion field of self"""
        return self.fields[1]

    @property
    def microVersion(self) -> str:
        """return microVersion field of self"""
        return self.fields[2]

    @property
    def release(self) -> str:
        """return release field of self, or None if it does not exist
        """
        fields = self.fields
        if len(fields) >= 4:
            return self.fields[3]
        else:
            return None

    @property
    def fields(self) -> tuple:
        """Return a tuple of the fields of self
        """
        return self._fields

    @property
    def asStr(self) -> str:
        """Convenience: return as string rather than object;
        allows to do things as obj.asPid.str rather then str(obj.asPid)
        """
        return str(self)

    def withoutRelease(self) -> str:
        """Convenience: return self as str with the release field
        """
        return '.'.join(self.fields[:3])

    def __len__(self):
        return len(self.fields)

    def __getitem__(self, item):
        return self.fields[item]

    def __eq__(self, other):
        """Check if self equals other
        """
        if isinstance(other, str):
            try:
                other = VersionString(other)
            except ValueError:
                return False

        if len(self) != len(other):
            return False

        for fs, fo in zip(self.fields, other.fields):
            if fs != fo:
                return False

        return True

    def __lt__(self, other):
        """Check if self is lower then other;
         raise Value Error if other is an invalid object.
         Presence of development field implies an earlier version (i.e. __lt__ is True) compared to
         the absence of the field
        """
        if isinstance(other, str):
            other = VersionString(other)

        fields_S = self.fields
        fields_O = other.fields

        for fs, fo in zip(fields_S[:3], fields_O[0:3]):
            if int(fs) < int(fo):
                return True
            elif int(fs) > int(fo):
                return False

        # At this point, majorVersion, minorVersion and revision are all equal
        # Check development field
        if len(fields_S) == 4 and len(fields_O) == 3:
            return True

        elif len(fields_S) == 3 and len(fields_O) == 4:
            return False

        elif len(fields_S) == 4 and len(fields_O) == 4:
            return fields_S[3] < fields_O[3]

        return False

    def __gt__(self, other):
        """Check if self is greater then other;
         raise Value Error if other is an invalid object.
         Presence of development field implies an earlier version (i.e. __gt__ is False) compared to
         the absence of the field
        """
        if isinstance(other, str):
            other = VersionString(other)

        fields_S = self.fields
        fields_O = other.fields

        for fs, fo in zip(fields_S[:3], fields_O[0:3]):
            if int(fs) < int(fo):
                return False
            elif int(fs) > int(fo):
                return True

        # At this point, majorVersion, minorVersion and revision are all equal
        # Check development field
        if len(fields_S) == 4 and len(fields_O) == 3:
            return False

        elif len(fields_S) == 3 and len(fields_O) == 4:
            return True

        elif len(fields_S) == 4 and len(fields_O) == 4:
            return fields_S[3] > fields_O[3]

        return False

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)



applicationVersion = VersionString('3.1.0.alfa2')
# applicationVersion = '3.1.0'
revision = '3'



