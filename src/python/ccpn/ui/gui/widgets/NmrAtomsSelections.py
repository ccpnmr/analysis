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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:26 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict as od
from itertools import groupby
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
import decimal
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showInfo

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
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.util.Constants import concentrationUnits
from ccpn.ui.gui.widgets.CheckBox import CheckBox, EditableCheckBox
from ccpn.core.lib import CcpnSorting
from ccpn.core.lib.DataFrameObject import  DATAFRAME_OBJECT
from ccpn.core.NmrChain import NmrChain
from ccpn.core.Spectrum import Spectrum
from ccpn.core.Peak import Peak
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Project import Project
from ccpn.core.lib.peakUtils import  DefaultAtomWeights, H, N, OTHER, C

i = 0 # used globally for layout

class _NmrAtomsSelection(CcpnDialog):
    """
    # used in Csm module
    """


    def __init__(self, parent=None, project=None, nmrAtoms=None, checked=None, **kwds):
        title = 'NmrAtoms settings'
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.parent = parent
        self.project = project
        self.nmrAtoms =nmrAtoms or []
        self.nmrAtomsCheckBoxes = []
        self.checked = checked or []
        self.nmrAtomsFrame = Frame(self, setLayout=True, grid=(0, 1))
        self.atomWeightSpinBoxes = []
        self.nmrAtomsCheckBoxes = []
        self.nmrAtomsLabels = []
        self.setRelativeContribuitions()
        self.setNmrAtomsCheckBoxes(self.nmrAtoms, setChecked=self.checked)
        self.addButtons()
        self.setFixedWidth(350)


    def addButtons(self):
        global i
        texts = ['info', 'UncheckAll', 'Cancel', 'Apply']
        calls = [self.showIndo, self.uncheckAll, self.reject, self._apply ]
        buttons = ButtonList(self, texts=texts, callbacks=calls, grid = (i,0), gridSpan=(i,2))

    def setRelativeContribuitions(self):
        global i
        for name, value in DefaultAtomWeights.items():
            labelRelativeContribution = Label(self, text='%s Relative Contribution' % name, grid=(i, 0))
            self.atomWeightSpinBox = DoubleSpinbox(self, value=DefaultAtomWeights[name],
                                                   prefix=str('Weight' + (' ' * 2)), grid=(i, 1),
                                                   tipText='Relative Contribution for the selected nmrAtom')
            self.atomWeightSpinBox.setObjectName(name)
            self.atomWeightSpinBox.setMaximumWidth(150)
            self.atomWeightSpinBoxes.append(self.atomWeightSpinBox)
            self.nmrAtomsLabels.append(labelRelativeContribution)
            i += 1

    def setNmrAtomsCheckBoxes(self, nmrAtomNames:list=[], setChecked:list=[]):
        global i
        labelnmrAtomNames = Label(self, text='nmrAtomNames', grid=(i, 0))
        self.scrollArea = ScrollArea(self, setLayout=False, grid=(i, 1))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = Frame(self, setLayout=True)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.getLayout().setAlignment(QtCore.Qt.AlignTop)

        n = 0
        nmrAtomNames.sort() #sort alphabetically than divede in sublists
        nmrAtomNamesGroups = [list(g) for k, g in groupby(nmrAtomNames, key=lambda x: x[0])]
        for groupNmrAtoms in nmrAtomNamesGroups:
            if len(groupNmrAtoms)>0:
                line = Label(self.scrollAreaWidgetContents, text='_'*25, grid=(n, 0))
                n += 1
                for nmrAtomName in groupNmrAtoms:
                        c = nmrAtomName in setChecked
                        self.atomSelection = CheckBox(self.scrollAreaWidgetContents, text=nmrAtomName,
                                                      checked=c, grid=(n, 0))
                        self.nmrAtomsCheckBoxes.append(self.atomSelection)
                        n += 1
        i+=1

    def getRelativeContribuitions(self):
        dd = od()
        for widget, name in zip(self.atomWeightSpinBoxes, DefaultAtomWeights.keys()):
            dd[name]  = widget.get()
        return dd

    def getNmrAtomNames(self):
        nn = [cb.text() for cb in self.nmrAtomsCheckBoxes if cb.isChecked()]
        return nn

    def showIndo(self):
        text = 'Select NmrAtoms which are present in all selected input Spectra.\n' \
               'Selecting multiple non compatible NmrAtoms can result in an empty bar chart.'
        showInfo('NmrAtom info',text)

    def _apply(self):
        if self.parent is not None:
            self.parent.relativeContribuitions = self.getRelativeContribuitions()
            self.parent.selectedNmrAtomNames = self.getNmrAtomNames()
        self.reject()

    def uncheckAll(self):
        nn = [cb.setChecked(False) for cb in self.nmrAtomsCheckBoxes]

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication


    app = TestApplication()




    popup = _NmrAtomsSelection(None,
                               nmrAtoms=['H', 'Hn', 'Hr', 'F', 'Ca'],
                               checked=['H'],
                               size=[500, 450],
                               grid=(0, 0))
    popup.show()
    popup.raise_()
    app.start()
