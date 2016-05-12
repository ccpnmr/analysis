__author__ = 'luca'


from functools import partial
from PyQt4 import QtCore, QtGui
from application.core.widgets.Label import Label
from application.core.widgets.GroupBox import GroupBox
from application.core.widgets.LineEdit import LineEdit
from application.core.widgets.ScrollArea import ScrollArea
from application.core.widgets.Dock import CcpnDock
from application.core.widgets.CheckBox import CheckBox
from collections import OrderedDict
from application.core.widgets.PulldownList import PulldownList
from application.core.widgets.ButtonList import ButtonList
from application.core.widgets.Button import Button
from application.core.widgets.Icon import Icon
from application.core.modules.GuiBlankDisplay import GuiBlankDisplay
from application.core.widgets.Dock import CcpnDock



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