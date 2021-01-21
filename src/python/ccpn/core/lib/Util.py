"""CCPN-level utility code independent of model content

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-01-21 11:48:08 +0000 (Thu, January 21, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import inspect
from typing import Optional
from ccpn.core.lib import Pid
from ccpn.core import _coreClassMap


def pid2PluralName(pid: str) -> str:
    """Get plural class name, (e.g. 'peaks', 'spectra' from short-form or long-form, Pid string
    Unrecognised strings are returned unchanged"""
    from ccpn.core.Project import Project

    tag = pid.split(Pid.PREFIXSEP, 1)[0]
    cls = Project._className2Class.get(tag)
    if cls is None:
        return tag
    else:
        return cls._pluralLinkName


def getParentPid(childPid) -> Pid.Pid:
    """Get the pid of parent of childPid; only uses Pid definitions (i.e. does not involve the actual objects)
    :returns Pid instance defining parent
    """
    if not isinstance(childPid, (str, Pid.Pid)):
        raise ValueError('Invalid pid "%s"' % childPid)
    childPid = Pid.Pid(childPid)
    if childPid.type not in _coreClassMap:
        raise ValueError('Invalid pid "%s"' % childPid)

    klass = _coreClassMap[childPid.type]
    parentClass = klass._parentClass
    offset = klass._numberOfIdFields
    fields = [parentClass.shortClassName] + list(childPid.fields[:-offset])
    parentPid = Pid.Pid.new(*fields)
    return parentPid


def getParentObjectFromPid(project, pid):
    """Get a parent object from a pid, which may represent a deleted object.

    :returns: Parent object or None on error/non-existence

    Example:
        pid = 'NA:A.40.ALA.CB'
        getParentObjectFromPid(pid) -> 'NR:A.40.ALA'
    """
    if not isinstance(pid, (str, Pid.Pid)):
        raise ValueError('Invalid pid "%s"' % pid)

    obj = None
    # First try if the object defined by pid still exists
    try:
        obj = project.getByPid(pid)
        if obj is not None:
            return obj._parent
    except:
        pass

    if obj is None:
        parentPid = getParentPid(pid)
        obj = project.getByPid(parentPid)
    return obj


# Atom ID
AtomIdTuple = collections.namedtuple('AtomIdTuple', ['chainCode', 'sequenceCode',
                                                     'residueType', 'atomName', ])


def commandParameterString(*params, values: dict = None, defaults: dict = None):
    """Make parameter string to insert into function call string.

    params are positional parameters in order, values are keyword parameters.
    If the defaults dictionary is passed in,
    only parameters in defaults are added to the string, and only if the value differs from the
    default. This allows you to pass in values=locals(). The order of keyword parameters
    follows defaults if given, else values, so you can get ordered parameters by passing in
    ordered dictionaries.

    Wrapper object values are replaced with their Pids

    Example:

    commandParameterString(11, values={a:1, b:<Note NO:notename>, c:2, d:3, e:4},
                            defaults=OrderedDict(d=8, b=None, c=2))

      will return

      "11, d=3, b='NO:notename'"
      """

    from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject

    ll = []
    for val in params:
        if isinstance(val, AbstractWrapperObject):
            val = val.pid
        ll.append(repr(val))

    if values:
        if defaults:
            for tag, default in defaults.items():
                val = values[tag]
                if val != default:
                    if isinstance(val, AbstractWrapperObject):
                        val = val.pid
                    ll.append('%s=%s' % (tag, repr(val)))

        else:
            for tag, val in values.items():
                if isinstance(val, AbstractWrapperObject):
                    val = val.pid
                ll.append('%s=%s' % (tag, repr(val)))
    #
    return ', '.join(ll)


def commandParameterStringValues(*params, values: dict = None, defaults: dict = None):
    """Make parameter string to insert into function call string.

    params are positional parameters in order, values are keyword parameters.
    If the defaults dictionary is passed in,
    only parameters in defaults are added to the string, and only if the value differs from the
    default. This allows you to pass in values=locals(). The order of keyword parameters
    follows defaults if given, else values, so you can get ordered parameters by passing in
    ordered dictionaries.

    Wrapper object values are replaced with their Pids

    Example:

    commandParameterString(11, values={a:1, b:<Note NO:notename>, c:2, d:3, e:4},
                            defaults=OrderedDict(d=8, b=None, c=2))

      will return

      "11, d=3, b='NO:notename'"
      """

    from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject

    ll = []
    for val in params:
        if isinstance(val, AbstractWrapperObject):
            val = val.pid
        ll.append(repr(val))

    if values:
        if defaults:
            for tag, default in defaults.items():
                val = values[tag]
                if val != default:
                    if isinstance(val, AbstractWrapperObject):
                        val = val.pid
                    ll.append('%s=%s' % (tag, repr(val)))

        else:
            for tag, val in values.items():
                if isinstance(val, AbstractWrapperObject):
                    val = val.pid
                ll.append('%s=%s' % (tag, repr(val)))
    #
    return ', '.join(ll)


def funcCaller() -> Optional[str]:
    """
    return the name of the current function
    (actually the parent caller to this function, hence the index of '1')
    :return: string name
    """
    try:
        return inspect.stack()[1][3]
    except:
        return None
