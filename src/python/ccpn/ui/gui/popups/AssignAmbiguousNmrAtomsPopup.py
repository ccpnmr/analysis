"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-03-11 20:20:22 +0000 (Thu, March 11, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-03-05 11:01:32 +0000 (Fri, March 05, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Spectrum import Spectrum
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.guiSettings import getColours, SOFTDIVIDER
from collections import defaultdict
from functools import partial
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from collections import OrderedDict
from ccpn.ui.gui.widgets.Widget import Widget
from collections import OrderedDict as od
from itertools import groupby
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showInfo
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.CheckBox import CheckBox, EditableCheckBox




PriorityNmrAtoms = [
    'H', 'Hn', #'HA', 'HB', 'HD1', 'HE' , 'HG',
    'N', 'Nh', #'ND1', 'ND2', 'NE', 'NE1', 'NE2', 'NZ',
    'C', 'CA', 'CB', #'CG', 'CD', 'CE', 'CZ'
    'F' ]


SHOWALLSPECTRA = True


DEFAULTSPACING = (5, 5)
ZEROMARGINS = (0, 0, 0, 0)  # l, t, r, b


class ObjectsSelectionWidget(Widget):

    def __init__(self, parent, mainWindow, labelName, objects, checkedObjects = None, priorityNames=None,
                 enabledAll=True, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        self.mainWindow = mainWindow
        self.labelName = labelName
        self.objects = objects
        self.objectsDict = {x.name:x for x in objects if hasattr(x, 'name')}
        self.priorityNames  = priorityNames or []
        self.checkedObjects = checkedObjects or []
        self.checkedObjectsDict = {x.name:x for x in self.checkedObjects if hasattr(x, 'name')}
        self.allCheckBoxes = []
        self.enabledAll = enabledAll
        print(self.enabledAll, 'ggg')
        self._setWidgets()

    def _setWidgets(self):
        i = 0
        labelnmrAtomNames = Label(self, text=self.labelName, grid=(i, 0), vAlign='t')
        self.scrollArea = ScrollArea(self, setLayout=False, grid=(i, 1), hAlign='c')
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = Frame(self, setLayout=True)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.getLayout().setAlignment(QtCore.Qt.AlignTop)
        priorityNmrAtoms = [i for i in self.priorityNames if i in self.objectsDict.keys()]
        allOthersNmrAtoms = [i for i in self.objectsDict.keys() if i not in priorityNmrAtoms]

        n = 0
        allOthersNmrAtoms.sort()  # sort alphabetically than divide in sublists
        allOthersNmrAtoms = [list(g) for k, g in groupby(allOthersNmrAtoms, key=lambda x: x[0])]
        for nmrAtomName in priorityNmrAtoms:
            atomSelection = CheckBox(self.scrollAreaWidgetContents, text=nmrAtomName,
                                     checked=nmrAtomName in self.checkedObjectsDict.keys(),
                                     checkable=self.enabledAll, grid=(n, 0))
            self.allCheckBoxes.append(atomSelection)
            n += 1

        i += 1
        for groupNmrAtoms in allOthersNmrAtoms:
            if len(groupNmrAtoms) > 0:
                n += 1
                for nmrAtomName in groupNmrAtoms:
                    atomSelection = CheckBox(self.scrollAreaWidgetContents, text=nmrAtomName,
                                             checked=nmrAtomName in self.checkedObjectsDict.keys(),
                                             checkable=self.enabledAll, grid=(n, 0))

                    self.allCheckBoxes.append(atomSelection)
                    n += 1
        i += 1

    def getSelectedObjects(self):
        selected = []
        for cb in self.allCheckBoxes:
            if cb.isChecked():
                obj = self.objectsDict.get(str(cb.text()))
                if obj:
                   selected.append(obj)
        return selected


i = 0


class AssignNmrAtoms4AxisCodesPopup(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = False
    FIXEDHEIGHT = False

    title = 'AssignNmrAtoms for AxisCodes'
    def __init__(self, parent=None, mainWindow=None, title=title, axisCode4NmrAtomsDict=None,
                 checkedAxisCode4NmrAtomsDict = None, uncheckableObjects = None, **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project

        else:
            self.mainWindow = None
            self.application = None
            self.current = None
            self.project = None

        self.axisCode4NmrAtomsDict = axisCode4NmrAtomsDict or defaultdict(set)
        self.checkedAxisCode4NmrAtomsDict = checkedAxisCode4NmrAtomsDict or defaultdict(set)
        self.selectionWidgets = []
        # self.uncheckablesDict = {'Un-assignable':uncheckableObjects}
        self._createWidgets(self.axisCode4NmrAtomsDict, enabledAll=True)
        self._createWidgets(self.checkedAxisCode4NmrAtomsDict, checkAll=True)
        # self._createWidgets(self.uncheckablesDict, checkAll=False, enabledAll=False)

        # enable the buttons
        self.setOkButton(callback=self._okCallback, tipText='Assign selected NmrAtoms to each AxisCode', text='Ok', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)

        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)


    def _createWidgets(self, _dict, checkAll=False, enabledAll=True):
        """Create the widgets for the popup
        """
        global i
        for axisCode, nmrAtoms in _dict.items():
            checkedObjects = []
            if checkAll:
                checkedObjects = nmrAtoms
            selectionWidget = ObjectsSelectionWidget(self.mainWidget, self.mainWindow, axisCode, nmrAtoms,
                                                     priorityNames=PriorityNmrAtoms, checkedObjects=checkedObjects,
                                                     enabledAll=enabledAll, grid=(i,0))
            self.selectionWidgets.append(selectionWidget)
            # HLine(self.mainWidget, grid=(i, 0), gridSpan=(1, 3), height=15)  # colour=getColours()[DIVIDER],
            i+=1

    def getSelectedObjects(self):
        dd = defaultdict(set)
        for w in self.selectionWidgets:
            dd[w.labelName] = w.getSelectedObjects()
        return dd

    def _okCallback(self):
        self.accept()
        # return self.getSelectedObjects()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication


    app = TestApplication()

    from ccpn.ui.gui.popups.AssignAmbiguousNmrAtomsPopup import AssignNmrAtoms4AxisCodesPopup

    popup = AssignNmrAtoms4AxisCodesPopup(None,
                               nmrAtoms=['H', 'Hn', 'Hr', 'F', 'Ca'],
                               checked=['H'],
                               relativeContribuitions=rc,
                               size=[500, 450],
                               grid=(0, 0))

    popup.show()
    popup.raise_()
    app.start()
