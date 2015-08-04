"""Qt related utility functions

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
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

import json
from ccpncore.lib.Constants import ccpnmrJsonData

def interpretEvent(event):
  """ Interpret drop event and return (type, data)
  """

  mimeData = event.mimeData()
  print('mimeData', mimeData.text())
  if mimeData.hasFormat(ccpnmrJsonData):
    print(mimeData.text(), '1111')
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
