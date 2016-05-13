__author__ = 'luca'


from functools import partial
from PyQt4 import QtCore, QtGui
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.GroupBox import GroupBox
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Dock import CcpnDock
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from collections import OrderedDict
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.modules.GuiBlankDisplay import GuiBlankDisplay
from ccpn.ui.gui.widgets.Dock import CcpnDock



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