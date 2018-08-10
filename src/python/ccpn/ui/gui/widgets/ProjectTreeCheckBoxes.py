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
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.core.Chain import Chain
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.RestraintList import RestraintList
from ccpn.core.PeakList import PeakList
from ccpn.core.IntegralList import IntegralList
from ccpn.core.MultipletList import MultipletList
from ccpn.core.PeakCluster import PeakCluster
from ccpn.core.Sample import Sample
from ccpn.core.Substance import Substance
from ccpn.core.NmrChain import NmrChain
from ccpn.core.DataSet import DataSet
from ccpn.core.Complex import Complex
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Note import Note


# TODO These should maybe be consolidated with the same constants in CcpnNefIo
# (and likely those in Project)
CHAINS = 'chains'
NMRCHAINS = 'nmrChains'
RESTRAINTLISTS = 'restraintLists'
CCPNTAG = 'ccpn'
SKIPPREFIXES = 'skipPrefixes'
EXPANDSELECTION = 'expandSelection'


class ProjectTreeCheckBoxes(QtWidgets.QTreeWidget, Base):
    """Class to handle exporting project to Nef file
    """

    # set the items in the project that can be exported
    checkList = [
        Chain._pluralLinkName,
        ChemicalShiftList._pluralLinkName,
        RestraintList._pluralLinkName,
        PeakList._pluralLinkName,
        IntegralList._pluralLinkName,
        MultipletList._pluralLinkName,
        Sample._pluralLinkName,
        Substance._pluralLinkName,
        NmrChain._pluralLinkName,
        DataSet._pluralLinkName,
        Complex._pluralLinkName,
        SpectrumGroup._pluralLinkName,
        Note._pluralLinkName,
        PeakCluster._pluralLinkName,
    ]

    # set which items can be selected/deselected, others are automatically set
    selectableItems = [
        Chain._pluralLinkName,
        ChemicalShiftList._pluralLinkName,
        RestraintList._pluralLinkName,
        NmrChain._pluralLinkName,
        PeakList._pluralLinkName,
        IntegralList._pluralLinkName,
        MultipletList._pluralLinkName,
        PeakCluster._pluralLinkName,
    ]

    def __init__(self, parent=None, project=None, maxSize=(250, 300), **kw):
        """Initialise the widget
        """
        QtWidgets.QTreeWidget.__init__(self, parent)
        Base.__init__(self, setLayout=False, **kw)

        # self.setMaximumSize(*maxSize)
        self.headerItem = QtWidgets.QTreeWidgetItem()
        self.item = QtWidgets.QTreeWidgetItem()
        self.project = project
        self.header().hide()
        if self.project is not None:
            for name in self.checkList:
                if hasattr(self.project, name):  # just to be safe
                    item = QtWidgets.QTreeWidgetItem(self)
                    item.setText(0, name)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

                    for obj in getattr(self.project, name):
                        child = QtWidgets.QTreeWidgetItem(item)
                        child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                        child.setData(1, 0, obj)
                        child.setText(0, obj.pid)
                        child.setCheckState(0, QtCore.Qt.Unchecked)

                    item.setCheckState(0, QtCore.Qt.Checked)
                    item.setExpanded(False)
                    item.setDisabled(name not in self.selectableItems)

        self.itemClicked.connect(self._clicked)

    def getSelectedObjects(self):
        """Get selected objects from the check boxes
        """
        selectedObjects = []
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                obj = item.data(1, 0)
                if hasattr(obj, 'pid'):
                    selectedObjects += [obj]
        return selectedObjects

    def getSelectedObjectsPids(self):
        """Get the pids of the selected objects
        """
        pids = []
        for item in self.getSelectedObjects():
            pids += [item.pid]
        return pids

    def selectObjects(self, pids):
        """handle changing the state of checkboxes
        """
        items = self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
        for item in items:
            if item.text(0) in pids:
                item.setCheckState(0, QtCore.Qt.Checked)

    def _clicked(self, *args):
        pass

    def _uncheckAll(self):
        """Clear all selection
        """
        for itemTree in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            for i in range(itemTree.childCount()):
                itemTree.child(i).setCheckState(0, QtCore.Qt.Unchecked)

class PrintTreeCheckBoxes(ProjectTreeCheckBoxes):
    """Class to handle exporting peaks/integrals/multiplets to PDF or SVG files
    """

    # set the items in the project that can be printed
    checkList = [
        PeakList._pluralLinkName,
        IntegralList._pluralLinkName,
        MultipletList._pluralLinkName,
    ]

    # all items can be selected
    selectableItems = [
        PeakList._pluralLinkName,
        IntegralList._pluralLinkName,
        MultipletList._pluralLinkName,
    ]

    def __init__(self, parent=None, project=None, maxSize=(250, 300), **kw):
        super(PrintTreeCheckBoxes, self).__init__(parent=parent, project=project, maxSize=maxSize, **kw)
