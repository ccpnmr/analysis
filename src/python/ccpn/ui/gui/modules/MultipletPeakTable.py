"""Module Documentation here

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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Peak import Peak
from ccpn.core.NmrAtom import NmrAtom
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.modules.PeakTable import PeakListTableWidget
from ccpn.util.OrderedSet import OrderedSet


logger = getLogger()
UNITS = ['ppm', 'Hz', 'point']


class MultipletPeakListTableWidget(PeakListTableWidget):
    """
    Class to present a peakList Table linked to a multipletTable
    """
    className = 'MultipletPeakListTable'
    attributeName = 'peakLists'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, peakList=None, multiSelect=False,
                 actionCallback=None, selectionCallback=None, **kwds):
        """
        Initialise the table
        """
        super(MultipletPeakListTableWidget, self).__init__(parent=parent, mainWindow=mainWindow, moduleParent=moduleParent,
                                                           multiSelect=multiSelect, peakList=peakList,
                                                           actionCallback=actionCallback, selectionCallback=selectionCallback, **kwds)

        self._selectedMultipletPeakList = None
        self._clearTableNotifiers()

        self.setTableNotifiers(tableClass=None,
                               rowClass=Peak,
                               cellClassNames=(NmrAtom, 'assignedPeaks'),
                               tableName='multiplet', rowName='peak',
                               changeFunc=self._updateAllModule,
                               className=self.attributeName,
                               updateFunc=self._updateAllModule,
                               tableSelection='_selectedMultipletPeakList',
                               pullDownWidget=None,
                               callBackClass=Peak,
                               selectCurrentCallBack=self._selectOnTableCurrentPeaksNotifierCallback,
                               moduleParent=moduleParent)

    def _updateTable(self, useSelectedPeakList=True, peaks=None, peakList=None):
        """Display the peaks on the table for the selected PeakList.
        Obviously, If the peak has not been previously deleted and flagged isDeleted
        """

        if self._selectedMultipletPeakList:      # always use selection

            peaks = OrderedSet()
            [peaks.add(peak) for mt in self._selectedMultipletPeakList for peak in mt.peaks]
            peaks = tuple(peaks)

            if peaks and peaks[0].PeakList:
                self.populateTable(rowObjects=peaks,
                                   columnDefs=self._getTableColumns(peaks[0].peakList),
                                   selectedObjects=self.current.peaks)
            else:
                self.clear()

        else:
            self.clear()

    def _selectPeakList(self, peakList=None):
        """Manually select a PeakList from the pullDown
        """
        print('>>>PeakTable _selectPeakList', repr(self))

    def _getPullDownSelection(self):
        raise RuntimeError('not defined for this table')

    def getIndexList(self, classItems, attribute):
        """Get the list of objects on which to before the indexing
        """
        # classItem is usually a type such as PeakList, MultipletList
        # with an attribute such as peaks/peaks

        # Actually, the peaks don't have an index at the moment so redundant, but argument still stands
        if self._selectedMultipletPeakList:
            peaks = OrderedSet()
            [peaks.add(peak) for mt in self._selectedMultipletPeakList for peak in mt.peaks]
            peaks = tuple(peaks)

            return peaks

