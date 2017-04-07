"""CCPN-level utility code independent of model content

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpn.util.Path import joinPath

__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:34 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
from ccpn.core.lib import Pid

def pid2PluralName(pid:str) -> str:
  """Get plural class name, (e.g. 'peaks', 'spectra' from short-form or long-form, Pid string
  Unrecognised strings are returned unchanged"""
  from ccpn.core.Project import Project
  tag = pid.split(Pid.PREFIXSEP, 1)[0]
  cls = Project._className2Class.get(tag)
  if cls is None:
    return tag
  else:
    return cls._pluralLinkName

# Atom ID
AtomIdTuple = collections.namedtuple('AtomIdTuple', ['chainCode', 'sequenceCode',
                                                     'residueType', 'atomName', ])


def expandDollarFilePath(project:'Project', filePath:str) -> str:
  """Expand paths that start with $REPOSITORY to full path

  NBNB Should be moved to ccpnmodel.ccpncore.lib.ccp.general.DataLocation.DataLocationstore"""

  # Convert from custom repository names to full names
  stdRepositoryNames = {
    '$INSIDE/':'insideData',
    '$ALONGSIDE/':'alongsideData',
    '$DATA/':'remoteData',
  }

  if not filePath.startswith('$'):
    # Nothing to expand
    return filePath

  dataLocationStore = project._wrappedData.root.findFirstDataLocationStore(name='standard')

  if dataLocationStore is None:
    raise TypeError("Coding error - standard DataLocationStore has not been set")

  for prefix,dataUrlName in stdRepositoryNames.items():
    if filePath.startswith(prefix):
      dataUrl = dataLocationStore.findFirstDataUrl(name=dataUrlName)
      if dataUrl is not None:
        return joinPath(dataUrl.url.path, filePath[len(prefix):])
  #
  return filePath



def commandParameterString(*params, values:dict=None, defaults:dict=None):
  """Make  parameter string to insert into function call string.

  params are positional parameters in order, values are keyword parameters.
  If the defaults dictionary is passed in,
  only parameters in defaults are added to the string, and only if the value differs from the
  default. This allows you to pass in values=locals(). The order of keyword parameters
  follows defaults if given, else values, so you can get ordered parametrs by passing in
  ordered dictionaries.

  Wrapper object values are replaced with their Pids

  values is a dict of values to use, mandatories are mandatory positional parameters (in order),
  defaults are a (parameter:default} ordered dictionary for keyword arguments.
  Only values given in mandatories or defaults are added, and values equal to their default
  are not added to the string.
  Wrapper object values are replaced with their Pids

  Example:

  commandParameterString(11, values={a:1, b:<Note NO:notename>, c:2, d:3, e:4},
                          defaults=OrderedDict(d=8, b=None, c=2))

    will return

    "11, d=8, b='NO:notename'"
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
