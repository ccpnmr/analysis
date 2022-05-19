"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-05-19 12:50:36 +0100 (Thu, May 19, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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
from ccpn.ui.gui.modules.PeakTable import _NewPeakTableWidget
from ccpn.util.OrderedSet import OrderedSet


logger = getLogger()
UNITS = ['ppm', 'Hz', 'point']


class MultipletPeakTableWidget(_NewPeakTableWidget):
    """Class to present a peakTable linked to a multipletTable
    """
    className = 'MultipletPeakTable'
    attributeName = 'peakLists'

    # define the notifiers that are required for the specific table-type
    tableClass = None
    rowClass = Peak
    cellClass = None
    tableName = 'multipletPeak'
    rowName = rowClass.className
    cellClassNames = {NmrAtom: 'assignedPeaks'}
    selectCurrent = True
    callBackClass = Peak
    search = False

    # NOTE:ED - need to check what needs putting back in here

    # def __init__(self, parent=None, mainWindow=None, moduleParent=None, peakList=None, multiSelect=False,
    #              actionCallback=None, selectionCallback=None, **kwds):
    #     """
    #     Initialise the table
    #     """
    #     super(MultipletPeakTableWidget, self).__init__(parent=parent, mainWindow=mainWindow, moduleParent=moduleParent,
    #                                                        # multiSelect=multiSelect,
    #                                                        # peakList=peakList,
    #                                                        actionCallback=actionCallback, selectionCallback=selectionCallback, **kwds)
    # 
    #     self._selectedMultipletPeakList = None
    #     self._clearTableNotifiers()
    # 
    #     self.setTableNotifiers(tableClass=None,
    #                            rowClass=Peak,
    #                            cellClassNames=(NmrAtom, 'assignedPeaks'),
    #                            tableName='multiplet', rowName='peak',
    #                            changeFunc=self._updateAllModule,
    #                            className=self.attributeName,
    #                            updateFunc=self._updateAllModule,
    #                            tableSelection='_selectedMultipletPeakList',
    #                            pullDownWidget=None,
    #                            callBackClass=Peak,
    #                            selectCurrentCallBack=self._selectOnTableCurrentPeaksNotifierCallback,
    #                            moduleParent=moduleParent)

    # def _update(self, useSelectedPeakList=True, peaks=None, peakList=None):
    #     """Display the peaks on the table for the selected PeakList.
    #     Obviously, If the peak has not been previously deleted
    #     """
    #
    #     print(f'  UPDATE')
    #     if self._selectedMultipletPeakList:      # always use selection
    #
    #         peaks = OrderedSet()
    #         [peaks.add(peak) for mt in self._selectedMultipletPeakList for peak in mt.peaks]
    #         peaks = tuple(peaks)
    #
    #         if peaks and peaks[0].peakList:
    #             self.populateTable(rowObjects=peaks,
    #                                columnDefs=self._getTableColumns(peaks[0].peakList),
    #                                selectedObjects=self.current.peaks)
    #         else:
    #             self.clear()
    #
    #     else:
    #         self.clear()

    # def _selectPeakList(self, peakList=None):
    #     """Manually select a PeakList from the pullDown
    #     """
    #     print('>>>PeakTable _selectPeakList', repr(self))
    # 
    # def _getPullDownSelection(self):
    #     raise RuntimeError('not defined for this table')

    # def getIndexList(self, classItems, attribute):
    #     """Get the list of objects on which to before the indexing
    #     """
    #     # classItem is usually a type such as PeakList, MultipletList
    #     # with an attribute such as peaks/peaks
    #
    #     # Actually, the peaks don't have an index at the moment so redundant, but argument still stands
    #     if self._selectedMultipletPeakList:
    #         peaks = OrderedSet()
    #         [peaks.add(peak) for mt in self._selectedMultipletPeakList for peak in mt.peaks]
    #         peaks = tuple(peaks)
    #
    #         return peaks
