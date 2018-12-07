"""
A widget to get     concentration Values and  concentrationUnits
"""


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:26 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

import decimal
from functools import partial
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from collections import OrderedDict
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.util.Constants import concentrationUnits


class ConcentrationWidget(Widget):

  def __init__(self, parent, names, mainWindow=None,  **kwds):
    super().__init__(parent, setLayout=True, **kwds)

    self.project = None # Testing reasons
    # Derive application, project, and current from mainWindow
    self.names = names or []
    self.concentrationEditors = []
    self.concentrationUnitEditors = []

    if mainWindow is not None:
      self.mainWindow = mainWindow
      self.application = mainWindow.application
      self.project = mainWindow.application.project
      self.current = mainWindow.application.current

    self._setWidgets()



  def _setWidgets(self):

    self.scrollArea = ScrollArea(self, setLayout=False, grid=(0, 0), )
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = Frame(self, setLayout=True)
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.scrollAreaWidgetContents.getLayout().setAlignment(QtCore.Qt.AlignTop)
    i = 0
    labelUnit = Label(self.scrollAreaWidgetContents, text="Unit", grid=(i, 0))
    self.concentrationUnitsEditor = RadioButtons(self.scrollAreaWidgetContents, texts=concentrationUnits, grid=(i, 1))
    i += 1
    for name in self.names:
      label = Label(self.scrollAreaWidgetContents, text=name, grid=(i, 0))
      concentrationEdit = DoubleSpinbox(self.scrollAreaWidgetContents, value=0.00, grid=(i, 1))
      self.concentrationEditors.append(concentrationEdit)
      i += 1

  def setValues(self, values):
    for value, editor, in zip(values, self.concentrationEditors,):
      editor.setValue(value)


  def setUnit(self, unit):
    self.concentrationUnitsEditor.set(unit)


  def getValues(self):
    values = []
    for valueEditor in self.concentrationEditors:
      values.append(valueEditor.get())

    return values

  def getUnit(self):
    return self.concentrationUnitsEditor.get()







if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication

  app = TestApplication()

  popup = CcpnDialog(windowTitle='Test', setLayout=True)
  popup.setGeometry(200, 200, 200, 200)

  widget = ConcentrationWidget(popup, names=['a','b','c'], mainWindow=None, grid=(0,0))
  popup.show()
  popup.raise_()
  app.start()
