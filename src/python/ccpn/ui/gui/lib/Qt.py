"""Qt related utility functions

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
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
__dateModified__ = "$dateModified: 2017-04-07 11:41:03 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from ccpnmodel.ccpncore.lib.Constants import ccpnmrJsonData

def interpretEvent(event):
  """ Interpret drop event and return (type, data)
  """

  mimeData = event.mimeData()
  if mimeData.hasFormat(ccpnmrJsonData):
    jsonData = json.loads(mimeData.text())
    pids = jsonData.get('pids')

    if pids is not None:
      # internal data transfer - series of pids
      return (pids, 'pids')

    # NBNB TBD add here slots for between-applications transfer, and other types as needed

  elif event.mimeData().hasUrls():
    filePaths = [url.path() for url in event.mimeData().urls()]
    return (filePaths, 'urls')

  elif event.mimeData().hasText():
    return(event.mimeData().text(), 'text')

  return (None, None)
