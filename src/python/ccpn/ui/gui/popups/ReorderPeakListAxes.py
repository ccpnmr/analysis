"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-03-30 15:15:03 +0100 (Mon, March 30, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-03-30 11:32:43 +0000 (Mon, March 30, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups.AxisOrderingPopup import AxisOrderingPopup
from PyQt5 import QtWidgets
from itertools import permutations
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown
from ccpn.util.Logging import getLogger


class ReorderPeakListAxes(CcpnDialogMainWidget):
    """
    Set the axis ordering for the selected peakLists
    """

    def __init__(self, parent=None, mainWindow=None, peakList=None, selectFirstItem=True, title='Reorder PeakList Axes', label='', **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.project = self.mainWindow.project
        self.application = self.mainWindow.application
        self.current = self.application.current
        self.peakList = peakList
        self.axisCodes = None       #peakList.axisCodes
        self._axisOrdering = None           #peakList.axisCodes
        self._label = label

        row = 0
        self.pLwidget = PeakListPulldown(parent=self.mainWidget,
                                         mainWindow=self.mainWindow,
                                         grid=(row, 0), gridSpan=(1, 1),
                                         showSelectName=True,
                                         minimumWidths=(0, 100),
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=self._pulldownPLcallback)

        # row += 1
        # self.peakListLabel = Label(self.mainWidget, text='', bold=True, grid=(row, 0), gridSpan=(1, 3))

        row += 1
        self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self.mainWidget, labelText="Select New Axis Ordering:",
                                                                     grid=(row, 0), gridSpan=(1, 3), vAlign='t',
                                                                     callback=self._setAxisCodeOrdering)
        self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidget)

        # enable the buttons
        self.setOkButton(callback=self._accept)
        self.setCancelButton(callback=self.reject)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

        self._populate()

        self.__postInit__()
        self._okButton = self.getButton(self.OKBUTTON)
        self._cancelButton = self.getButton(self.CANCELBUTTON)

        if peakList is not None:
            self.selectPeakList(peakList)
        elif selectFirstItem:
            self.pLwidget.selectFirstItem()

    def _populate(self):
        """Populate the widgets from the current selected peakList
        """
        if self.peakList:
            # self._label = self.peakList.id
            # self.peakListLabel.setText(self._label + ' - ' + str(self._axisOrdering))

            self.axisCodes = self.peakList.spectrum.axisCodes
            self._axisOrdering = self.peakList.spectrum.axisCodes
            self._fillPreferredWidget()
            self.preferredAxisOrderPulldown.setEnabled(True)
        else:
            self.preferredAxisOrderPulldown.pulldownList.setData(['<None>'])
            self.preferredAxisOrderPulldown.setEnabled(False)

    def _fillPreferredWidget(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = None

        ll = ['<None>']
        axisPerms = []
        axisOrder = []
        if self.mainWindow and self.peakList:
            # add permutations for the axes
            axisPerms = permutations([axisCode for axisCode in self.axisCodes])
            axisOrder = tuple(permutations(list(range(len(self.axisCodes)))))
            ll += [" ".join(ax for ax in perm) for perm in axisPerms]

        self.preferredAxisOrderPulldown.pulldownList.setData(ll)
        self.preferredAxisOrderPulldown.setIndex(1 if len(ll) > 1 else 0)

    def _setAxisCodeOrdering(self, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        index = self.preferredAxisOrderPulldown.getIndex()

        axisOrder = tuple(permutations(list(range(len(self.axisCodes)))))
        if index > 0:
            self._axisOrdering = tuple(axisOrder[index - 1])
        else:
            self._axisOrdering = None

    def _accept(self):
        self.accept()

        self._setAxisCodeOrdering(None)
        if self._axisOrdering:
            with undoBlock():
                self.peakList.reorderPeakListAxes(self._axisOrdering)

    def selectPeakList(self, peakList=None):
        """Manually select a PeakList from the pullDown
        """
        if peakList is None:
            self.pLwidget.selectFirstItem()
        else:
            if not isinstance(peakList, PeakList):
                getLogger().warning('select: Object is not of type PeakList')
                raise TypeError('select: Object is not of type PeakList')
            else:
                for widgetObj in self.pLwidget.textList:
                    if peakList.pid == widgetObj:
                        self.peakList = peakList
                        self.pLwidget.select(self.peakList.pid)

    def _pulldownPLcallback(self, data):
        """Select the peakList from the pulldown text
        """
        self.peakList = self.project.getByPid(self.pLwidget.getText())
        self._populate()
