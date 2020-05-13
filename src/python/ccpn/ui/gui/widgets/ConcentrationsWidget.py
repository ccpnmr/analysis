"""
A widget to get     concentration Values and  concentrationUnits
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2019-12-05 09:40:40 +0000 (Thu, December 05, 2019) $"
__version__ = "$Revision: 3.0.0 $"
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
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from collections import OrderedDict
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.util.Constants import concentrationUnits


class ConcentrationWidget(ScrollableFrame):

    def __init__(self, parent, names, mainWindow=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        self.project = None  # Testing reasons
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
        i = 0
        labelUnit = Label(self, text="Unit", grid=(i, 0))
        self.concentrationUnitsEditor = RadioButtons(self, texts=concentrationUnits, grid=(i, 1))
        i += 1
        for name in self.names:
            label = Label(self, text=name, grid=(i, 0))
            concentrationEdit = ScientificDoubleSpinBox(self,
                                                        value=0.00, decimals=4, min=0.0,
                                                        grid=(i, 1))
            self.concentrationEditors.append(concentrationEdit)
            i += 1

    def setValues(self, values):
        for value, editor, in zip(values, self.concentrationEditors, ):
            if value is not None:
                editor.setValue(value)

    def setUnit(self, unit):
        if unit is not None:
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

    widget = ConcentrationWidget(popup, names=['a', 'b', 'c'], mainWindow=None, grid=(0, 0))
    popup.exec_()
    # app.start()
