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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog

class CreateDummySpectraGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = 'Create Dummy Spectra'

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(CreateDummySpectraGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    rowCount = 0

    self.useAsnewInputDataCheckBox = CheckBox(self.pipeFrame, checked=False, text='Use as new input data',  grid=(rowCount,0))
    rowCount += 1

    self.overWriteSameFile = CheckBox(self.pipeFrame, checked=False, text='OverWrite Same File',  grid=(rowCount,0))
    rowCount += 1

    self.saveAsHDF5CheckBox = CheckBox(self.pipeFrame, checked=False, text='Save spectra as HDF5',  grid=(rowCount,0))
    self.saveAsHDF5Label = Label(self.pipeFrame, 'Saving  directory path',  grid=(rowCount,1))
    self.saveAsHDF5LineEdit = LineEditButtonDialog(self.pipeFrame, fileMode=QtGui.QFileDialog.Directory,  grid=(rowCount,2))


# run this file to test the gui
if __name__ == '__main__':
  from PyQt4 import QtGui
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.PipelineWidgets import  PipelineDropArea

  app = TestApplication()
  win = QtGui.QMainWindow()

  pipeline = PipelineDropArea()
  createDummySpectraGuiPipe = CreateDummySpectraGuiPipe(parent=pipeline)
  pipeline.addDock(createDummySpectraGuiPipe)

  win.setCentralWidget(pipeline)
  win.resize(1000, 500)
  win.show()

  app.start()