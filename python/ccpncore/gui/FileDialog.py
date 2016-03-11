"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui

import sys

class FileDialog(QtGui.QFileDialog):

  def __init__(self, parent=None, fileMode=0, text=None, acceptMode=0, preferences=None, **kw):

    QtGui.QFileDialog.__init__(self, parent, caption=text, **kw)


    staticFunctionDict = {
      (0, 0): 'getOpenFileName',
      (0, 1): 'getOpenFileName',
      (0, 2): 'getExistingDirectory',
      (0, 3): 'getOpenFileNames',
      (1, 0): 'getSaveFileName',
      (1, 1): 'getSaveFileName',
      (1, 2): 'getSaveFileName',
      (1, 3): 'getSaveFileName',
    }

    self.setFileMode(fileMode)
    self.setAcceptMode(acceptMode)
    if preferences.colourScheme == 'dark':
      self.setStyleSheet("""
                         QFileDialog QWidget {
                                             background-color: #2a3358;
                                             color: #f7ffff;
                                             }
                        """)
    elif preferences.colourScheme == 'light':
      self.setStyleSheet("QFileDialog QWidget {color: #464e76; }")

    if preferences.useNative and not sys.platform.lower() == 'linux':
      funcName = staticFunctionDict[(acceptMode, fileMode)]
      getattr(self, funcName)(caption=text, **kw)
    else:
      self.exec_()




