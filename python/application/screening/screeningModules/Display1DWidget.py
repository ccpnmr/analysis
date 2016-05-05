__author__ = 'luca'


from functools import partial
from PyQt4 import QtCore, QtGui
from ccpncore.gui.Label import Label
from ccpncore.gui.GroupBox import GroupBox
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.CheckBox import CheckBox
from collections import OrderedDict
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Button import Button
from ccpncore.gui.Icon import Icon
from application.core.modules.GuiBlankDisplay import GuiBlankDisplay
from ccpncore.gui.Dock import CcpnDock



class Display1DWidget(QtGui.QFrame):
  def __init__(self, parent=None, project=None, **kw):
    super(Display1DWidget, self).__init__(parent)
    self.mainWindow = project._appBase.mainWindow

    self.mainLayout = QtGui.QVBoxLayout()
    self.setLayout(self.mainLayout)


    display = self.mainWindow.createSpectrumDisplay(project.spectra[0])
    display.spectrumToolBar.hide()
    display.spectrumUtilToolBar.hide()
    display.dock.hideTitleBar()
    self.mainLayout.addWidget(display.dock)