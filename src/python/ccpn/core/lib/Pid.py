"""Pid (Project ID) class for within-project unique ID strings.
Version-3 Pid routines

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:32 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import List, Optional, Tuple

# try:
#   from cing import __version__
# except ImportError:
#   __version__ = '???'

# set separators
PREFIXSEP = ':'
IDSEP = '.'

# Set translation between IDSEP and alternative character
altCharacter = '^'
backupAltCharacter = '`'
remapSeparators = str.maketrans(IDSEP, altCharacter)
unmapSeparators = str.maketrans(altCharacter, IDSEP)


def createPid(head: str, *args: str) -> 'Pid':
    """make pid from head and list of successive keys.
    Head may be an existing pid, or a naked string
    Keys are converted to string, and illegal characters are converted to altCharacter
    The head is  not checked - it should be either a valid pid or a class code"""

    # map args to corrected strings
    ll = [val.translate(remapSeparators) for val in args]

    if head[-1] == PREFIXSEP:
        sep = ''
    elif PREFIXSEP in head:
        sep = IDSEP
    else:
        sep = PREFIXSEP
    #
    return Pid(sep.join((head, IDSEP.join(ll))))


def createId(*args) -> str:
    """make id from list of successive keys.
    Keys are converted to string, and illegal characters are converted to altCharacter"""

    # map args to corrected strings
    return IDSEP.join(('' if val is None else str(val).translate(remapSeparators))
                      for val in args)


def splitId(idString) -> List[Optional[str]]:
    """Split idString into tuple of component elements,
    mapping altCharacter back to separator and replacing empty strings with None"""

    # map args to corrected strings
    return list((val.translate(unmapSeparators) or None) for val in idString.split(IDSEP))


def decodePid(sourceObject, thePid: 'Pid') -> 'Optional[Pid]':
    """
    try to decode thePid relative to sourceObject
    return decoded pid object or None on not found or Error
    """

    # REFACTOR. This DOES decode PID parts. TBD NBNB

    import cing.Libs.io as io

    if thePid is None:
        return None

    # assure a Pid object
    if not isinstance(thePid, Pid):
        strPid = str(thePid)

        # Modified by Rasmus to match new isValid behaviour)
        # thePid = Pid(str(thePid))
        # NB Assumes that asPid wi;ll raise VALUEeRROR (as Pid does) if something goes wrong
        try:
            if hasattr(thePid, 'asPid'):
                # we probably did get passed an object
                thePid = thePid.asPid

            else:
                # just try it as a string
                thePid = Pid(strPid)
        except ValueError:
            io.error('decodePid: pid "{0}" is invalid', thePid)

        #end if
    #end if

    if not thePid.isValid:
        io.error('decodePid: pid "{0}" is invalid', thePid)
        return None
    #end if

    # check if thePid describes the source object
    if hasattr(sourceObject, 'asPid'):
        if sourceObject.asPid == thePid:
            return sourceObject
    #end if
    # apparently not, let try to traverse down to find the elements of thePid
    obj = sourceObject
    for p in thePid:
        #print( 'decodePid>>', p, object)
        if p not in obj:
            return None
        obj = obj[p]
    #end for
    # found an object, check if it is the right kind
    # Necessary as ccpn wrapper objects use .className insteaad of .__class__.__name__
    objType = obj.className if hasattr(obj, 'className') else obj.__class__.__name__
    if thePid.type != objType:
        io.error('decodePid: type "{0}" does not match object type "{1}"',
                 thePid.type, objType)
        return None
    return obj


class Pid(str):
    """Pid routines, adapted from path idea in: Python Cookbook,
    A. Martelli and D. Ascher (eds), O'Reilly 2002, pgs 140-142

    A Pid is a string with extra functionality.
    It consists of a non-empty type substring separated by a mandatory ':' character
    from an optional id substring, consisting of field substrings separated by dots.
    The isValid function checks for validity

    The type, id, and list of fields are available as properties.

    New Pids can be created by pid.clone, by pid.extend (which creates a new Pid with
    additional fields) and by Pid.new, which combines a type and a list of fields into a new
    Pid, converting the values to string as necessary.

    Pids can also be created by modifying individual fields relative to a source pid.
    pid.modify(index, value) will set the value of the field at index,
    whereas pid.increment(index, value) (resp. decrement) will convert the field at
    index to an integer (where possible) and increment (decrement) it by 'value'.

    Examples:
    
    pid = Pid.new('Residue','mol1','A', 502) # elements need not be strings; but will be converted
    -> Residue:mol1.A.502   (Pid instance)

    which is equivalent to:

    pid = Pid('Residue:mol1.A.502')
    -> Residue:mol1.A.502   (Pid instance)

    Behaves as a string:
    pid == 'Residue:mol1.A.502'
    -> True

    pid.str
    -> 'Residue:mol1.A.502' (str instance)

    pid.type
    -> 'Residue' (str instance)

    pid.id
    -> 'mol1.A.502' (str instance)
    
    pid2 = pid.modify(1, 'B', type='Atom')
    -> Atom:mol1.B.502  (Pid instance)
    
    but also:
    pid3 = Pid('Residue').extend('mol2')
    -> Residue:mol2  (Pid instance)
    
    pid4 = pid.decrement(2,1)
    -> Residue:mol1.A.501  (Pid instance)
    or
    pid4 = pid.increment(2,-1)
    NB fails on elements that cannot be converted to int's
    
    pid5 = pid.clone()   # equivalent to pid5 = Pid(pid)
    -> Residue:mol1.A.502  (Pid instance)
    
    pid==pid5
    -> True
    
    '502' in pid.fields
    -> True

    502 in pid.fields
    -> False    # all pid elements are strings
    """

    # name mapping dictionary
    nameMap = dict(
            MO='Molecule'
    )

    def __init__(self, string: str, **kwds):
        """First argument ('string' must be a valid pid string with at least one, non-initial PREFIXSEP
        Additional arguments are converted to string with disallowed characters changed to altCharacter
        """
        super().__init__(**kwds)  # GWV does not understand this

        # inlining this here is 1) faster, 2) guarantees that we never get invalid Pids.
        # We can then assume validity for the rest of the functions
        if PREFIXSEP not in self or self.startswith(PREFIXSEP):
            raise ValueError("String %s is not a valid Pid" % str.__repr__(self))

        self._version = 'CcpNmr:%s' % __version__

    @property
    def type(self) -> str:
        """return type part of pid"""
        return self.split(PREFIXSEP, 1)[0]

    @property
    def id(self) -> str:
        """return id part of pid"""
        return self.split(PREFIXSEP, 1)[1]

    @property
    def fields(self) -> Tuple[str, ...]:
        """id part of pid as a tuple of fields"""
        return tuple(self._split()[1:])

    @staticmethod
    def isValid(text: str) -> bool:
        return PREFIXSEP in text and text[0] != PREFIXSEP

    # NBNB TODO function name 'str' confuses Sphinx documentation and is bad for, Change it?
    @property
    def str(self):
        """
        Convenience: return as string rather than object;
        allows to do things as obj.asPid.str rather then str(obj.asPid)
        """
        return str(self)

    def _split(self):
        """Return a splitted pid as list or empty list on error"""
        parts = self.split(PREFIXSEP, 1)
        result = [parts[0]]
        if parts[1]:
            result.extend(parts[1].split(IDSEP))
        return result

    @staticmethod
    def new(*args: object) -> 'Pid':
        """
        Return Pid object from arguments
        Apply str() on all arguments
        Have to use this as intermediate as str baseclass of Pid only accepts one argument
        """
        # use str operator on all arguments
        args = [str(x) for x in args]
        # could implement mapping here
        if (len(args) > 0) and (args[0] in Pid.nameMap):
            #args = list(args) # don't know why I have to use the list operator
            args[0] = Pid.nameMap[args[0]]
        #end if
        return Pid(Pid._join(*args))

    @staticmethod
    def _join(*args: str) -> str:
        """Join args using the rules for constructing a pid
        """

        # NB the behaviour if len(args) == 1 is correct (return "type:")
        if args:
            return PREFIXSEP.join((args[0], IDSEP.join(args[1:])))
        else:
            return ''

    def modify(self, index: int, newId: object, newType: str = None) -> 'Pid':
        """Return new pid with position index modified by newId or newType replaced
        """
        parts = self._split()

        idparts = parts[1:]
        try:
            # NB this allows negative indices also, according to normal Python rules
            idparts[index] = newId
        except IndexError:
            import cing.Libs.io as io
            io.error('Pid.modify: invalid index ({0})\n', index + 1)
        parts[1:] = idparts

        if newType is not None:
            parts[0] = newType

        return Pid.new(*parts)

    def extend(self, *args: object):
        """Make copy with additional fields """
        return self._join(self._split() + [str(x) for x in args])

    def increment(self, index: str, value: int = 1) -> 'Pid':
        """Return new pid with position index incremented by value
        Assumes integer valued id at position index
        """
        parts = self._split()
        parts[index + 1] = int(parts[index + 1]) + value
        return Pid.new(*parts)

    def decrement(self, index: int, value: int = 1) -> 'Pid':
        """Return new pid with position index decremented by value
        Assumes integer valued id at position index
        """
        return self.increment(index, -value)

    def clone(self) -> 'Pid':
        """Return copy of pid
        """
        # Use Pid.new to pass it by any 'translater/checking routine'
        parts = self._split()
        return Pid.new(*parts)

    def definesInstance(self, klass):
        """Returns True if pid.type defines an instance of V3-object klass
        """
        if hasattr(klass, 'shortClassName') and self.type == klass.shortClassName:
            return True
        if hasattr(klass, 'className') and self.type == klass.className:
            return True
        return False
