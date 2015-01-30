"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import pyqtgraph.console as console
from PySide import QtGui

class Console(console.ConsoleWidget):
  def __init__(self, parent=None, namespace=None, historyFile=None):
    console.ConsoleWidget.__init__(self, parent, namespace)
    # self.console.addAction()
    self.runMacroButton = QtGui.QPushButton()
    # self.console.ui.runMacroButton.setCheckable(True)
    self.runMacroButton.setText('Run Macro')
    self.ui.horizontalLayout.addWidget(self.runMacroButton)
  #
  #
  def runMacro(self):
    print('runMacro')
    # macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro")
    # print(macroFile)

