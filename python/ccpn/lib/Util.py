"""CCPN-level utility code independent of model content

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpncore.util.Path import joinPath

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from collections import namedtuple
from ccpncore.util import Pid

def pid2PluralName(pid:str) -> str:
  """Get plural class name, (e.g. 'Peaks', 'Spectra' from short-form or long-form, Pid string
  Unrecognised strings are returned unchanged"""
  from ccpn import _pluralPidTypeMap as pluralPidTypeMap
  tag = pid.split(Pid.PREFIXSEP, 1)[0]
  return pluralPidTypeMap.get(tag, tag)

# Atom ID
AtomIdTuple = namedtuple('AtomIdTuple', ['chainCode', 'sequenceCode', 'residueType', 'atomName', ])


def expandDollarFilePath(dataLocationStore:'DataLocationStore', filePath:str) -> str:
  """Expand paths that start with $REPOSITORY to full path

  NBNB Should be moved to ccpncore.lib.ccp.general.DataLocation.DataLocationstore"""

  # Convert from custom repository names to full names
  stdRepositoryNames = {
    '$INSIDE/':'insideData',
    '$ALONGSIDE/':'alongsideData',
    '$DATA/':'remoteData',
  }

  if not filePath.startswith('$'):
    # Nothing to expand
    return filePath

  if dataLocationStore is None:
    # No DataLocationStore to work with
    return

  for prefix,dataUrlName in stdRepositoryNames.items():
    if filePath.startswith(prefix):
      dataUrl = dataLocationStore.findFirstDataUrl(name=dataUrlName)
      if dataUrl is not None:
        return joinPath(dataUrl.url.path, filePath[len(prefix):])
  #
  return filePath