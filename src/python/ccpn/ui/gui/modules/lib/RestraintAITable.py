"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-02-09 18:53:19 +0000 (Thu, February 09, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-01-20 16:18:53 +0100 (Fri, January 20, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial

import numpy as np
import pandas as pd
import warnings
from PyQt5 import QtCore

from ccpn.core.Peak import Peak
from ccpn.core.PeakList import PeakList
from ccpn.core.RestraintTable import RestraintTable
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.lib._CoreMITableFrame import _CoreMITableWidgetABC  # _CoreMITableFrameABC
from ccpn.ui.gui.lib._CoreTableFrame import _CoreTableFrameABC
import ccpn.ui.gui.modules.PyMolUtil as pyMolUtil
from ccpn.ui.gui.modules.lib.RestraintAITableCommon import _RestraintOptions, UNITS, \
    HeaderIndex, HeaderPeak, HeaderObject, HeaderRestraint, HeaderAtoms, HeaderTarget, \
    HeaderLowerLimit, HeaderUpperLimit, HeaderMin, HeaderMax, HeaderMean, HeaderStd, \
    HeaderCount1, HeaderCount2, _OLDHEADERS, _RESTRAINTTABLE, _VIOLATIONRESULT, ALL, PymolScriptName
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.GuiTable import _getValueByHeader
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.table._TableModel import _TableModel
from ccpn.util.Common import flattenLists, makeIterableList
from ccpn.util.Logging import getLogger
from ccpn.util.Path import joinPath

# NOTE:ED - this needs moving
from sandbox.Ed._MITableDelegates import _ExpandVerticalCellDelegate


#=========================================================================================
# _MultiSort
#=========================================================================================

class _MultiSort(_TableModel):
    """Subclass of the basic table-model to allow sorting into groups
    """

    def _setSortOrder(self, column: int, order: QtCore.Qt.SortOrder = ...):
        """Get the new sort order based on the sort column and sort direction
        """
        self._oldSortIndex = self._sortIndex
        col = self._df.columns[column]

        if self._view.enableMultiColumnSort:
            with warnings.catch_warnings():
                warnings.filterwarnings(action='error', category=FutureWarning)

                try:
                    vp = self._df[self._df.columns[self._view.PIDCOLUMN]].apply(lambda val: universalSortKey(val))
                    vVal = self._df[col]  # .apply(lambda val: universalSortKey(val)) <- fails new[DIFF] calculation
                    newDf = pd.DataFrame([vp, vVal]).T
                    newDf.reset_index(drop=True, inplace=True)

                    groupCol = newDf.columns[0]  # first column should be the grouped column from source dataFrame
                    MAX, MIN, DIFF = 'max', 'min', 'diff'

                    if self._view.applySortToGroups:
                        # ascending/descending - group and subgroup
                        if self._view.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.AscendingOrder:
                            newDf[MIN] = newDf.groupby([groupCol])[[col]].transform(MIN)
                            newDf = newDf.sort_values([MIN, groupCol, col], ascending=True).drop(MIN, axis=1)

                        else:
                            newDf[MAX] = newDf.groupby([groupCol])[[col]].transform(MAX)
                            newDf = newDf.sort_values([MAX, groupCol, col], ascending=False).drop(MAX, axis=1)

                    elif self._view.horizontalHeader().sortIndicatorOrder() == QtCore.Qt.AscendingOrder:
                        # ascending - min->max of each group / subgroup always max->min
                        newDf[MAX] = newDf.groupby([groupCol])[[col]].transform(MAX)
                        newDf[DIFF] = newDf[MAX] - newDf[col]
                        newDf = newDf.sort_values([MAX, groupCol, DIFF], ascending=True).drop([MAX, DIFF], axis=1)

                    else:
                        print(f'sorting    {groupCol}    {col}    {MAX}')

                        # descending - max->min of each group / subgroup always max->min
                        newDf[MAX] = newDf.groupby([groupCol])[[col]].transform(MAX)
                        newDf = newDf.sort_values([MAX, groupCol, col], ascending=False).drop(MAX, axis=1)

                        # KEEP THIS BIT! this is the opposite of the min->max / max->min (3rd option above)
                        # max->min of each group / min->max within group
                        # newDf[MIN] = newDf.groupby([groupCol])[[col]].transform(MIN)
                        # newDf[DIFF] = newDf[MIN] - newDf[col]
                        # newDf = newDf.sort_values([MIN, groupCol, DIFF], ascending=False).drop([MIN, DIFF], axis=1)

                    self._sortIndex = list(newDf.index)

                except Exception as es:
                    # log warning and drop-out to default sorting
                    getLogger().debug2(f'issue sorting table: probably unsortable column - {es}')

                    newDf = self._universalSort(self._df[col])
                    self._sortIndex = list(newDf.sort_values(ascending=(order == QtCore.Qt.AscendingOrder)).index)

        else:
            # single column sort on the specified column
            newDf = self._universalSort(self._df[col])
            self._sortIndex = list(newDf.sort_values(ascending=(order == QtCore.Qt.AscendingOrder)).index)

        # map the old sort-order to the new sort-order
        if self._filterIndex is not None:
            self._oldFilterIndex = self._filterIndex
            self._filterIndex = sorted([self._sortIndex.index(self._oldSortIndex[fi]) for fi in self._filterIndex])


#=========================================================================================
# _NewRestraintWidget - main widget for table, will need to change to _MultiIndex
#=========================================================================================


# class _NewRestraintWidget(_CoreTableWidgetABC):
class _NewRestraintWidget(_CoreMITableWidgetABC):
    """Class to present a peak-driven Restraint Analysis Inspector Table
    """
    className = 'PeakTable'
    attributeName = 'peakLists'

    _OBJECT = ('_object', '_object')
    OBJECTCOLUMN = ('_object', '_object')

    defaultHidden = [(HeaderIndex, HeaderIndex), OBJECTCOLUMN]
    _internalColumns = ['isDeleted', (HeaderIndex, HeaderIndex), OBJECTCOLUMN]  # columns that are always hidden

    #     defaultHidden = ['#',
    #                      'Restraint Pid_1', 'Restraint Pid_2', 'Restraint Pid_3', 'Restraint Pid_4', 'Restraint Pid_5',
    #                      'Restraint Pid_6', 'Restraint Pid_7', 'Restraint Pid_8', 'Restraint Pid_9',
    #                      'Target Value_1', 'Target Value_2', 'Target Value_3', 'Target Value_4', 'Target Value_5',
    #                      'Target Value_6', 'Target Value_7', 'Target Value_8', 'Target Value_9',
    #                      'Lower Limit_1', 'Lower Limit_2', 'Lower Limit_3', 'Lower Limit_4', 'Lower Limit_5',
    #                      'Lower Limit_6', 'Lower Limit_7', 'Lower Limit_8', 'Lower Limit_9',
    #                      'Min_1', 'Min_2', 'Min_3', 'Min_4', 'Min_5',
    #                      'Min_6', 'Min_7', 'Min_8', 'Min_9',
    #                      'Max_1', 'Max_2', 'Max_3', 'Max_4', 'Max_5',
    #                      'Max_6', 'Max_7', 'Max_8', 'Max_9',
    #                      'Mean_1', 'Mean_2', 'Mean_3', 'Mean_4', 'Mean_5',
    #                      'Mean_6', 'Mean_7', 'Mean_8', 'Mean_9',
    #                      'STD_1', 'STD_2', 'STD_3', 'STD_4', 'STD_5',
    #                      'STD_6', 'STD_7', 'STD_8', 'STD_9',
    #                      'Count > 0.5_1', 'Count > 0.5_2', 'Count > 0.5_3', 'Count > 0.5_4', 'Count > 0.5_5',
    #                      'Count > 0.5_6', 'Count > 0.5_7', 'Count > 0.5_8', 'Count > 0.5_9',
    #                      ]

    # define self._columns here - these are wrong
    columnHeaders = {'#'      : '#',
                     'Pid'    : 'Pid',
                     '_object': '_object',
                     'Comment': 'Comment',
                     }

    tipTexts = ('Peak serial number',
                'Pid of the Peak',
                'Object',
                'Optional user comment'
                )

    # define the notifiers that are required for the specific table-type
    tableClass = PeakList
    rowClass = Peak
    cellClass = None
    tableName = tableClass.className
    rowName = rowClass.className
    cellClassNames = None
    selectCurrent = True
    callBackClass = Peak
    search = False

    positionsUnit = UNITS[0]  # default

    # set the queue handling parameters
    _maximumQueueLength = 10

    # _autoExpand = False
    _selectedPeakList = None
    _defaultEditable = False

    # define _columns for multi-column sorting
    # NOTE:ED - check and remove redundant
    MERGECOLUMN = 1
    PIDCOLUMN = 1
    EXPANDERCOLUMN = 1
    SPANCOLUMNS = (1,)
    MINSORTCOLUMN = 0

    defaultTableModel = _MultiSort
    enableMultiColumnSort = True
    # subgroups are always max->min
    applySortToGroups = False

    def __init__(self, *args, **kwds):
        super(_NewRestraintWidget, self).__init__(*args, **kwds)

        delegate = _ExpandVerticalCellDelegate(parent=self.verticalHeader(), table=self)
        for col in self.SPANCOLUMNS:
            # add delegates to show expand/collapse icon
            self.setItemDelegateForColumn(col, delegate)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def _sourceObjects(self):
        """Get/set the list of source objects
        """
        return (self._table and self._table.peaks) or []

    @_sourceObjects.setter
    def _sourceObjects(self, value):
        # shouldn't need this
        self._table.peaks = value

    @property
    def _sourceCurrent(self):
        """Get/set the associated list of current objects
        """
        return self.current.peaks

    @_sourceCurrent.setter
    def _sourceCurrent(self, value):
        if value:
            self.current.peaks = value
        else:
            self.current.clearPeaks()

    @property
    def _restraintTables(self):
        """Link to the parent containing the restraintTables
        """
        return self.resources._restraintTables

    @_restraintTables.setter
    def _restraintTables(self, value):
        self.resources._restraintTables = value

    @property
    def _outputTables(self):
        """Link to the parent containing the outputTables
        """
        return self.resources._outputTables

    @_outputTables.setter
    def _outputTables(self, value):
        self.resources._outputTables = value

    # @property
    # def _sourcePeaks(self):
    #     """Link to the parent containing the sourcePeaks
    #     """
    #     return self.resources._sourcePeaks
    #
    # @_sourcePeaks.setter
    # def _sourcePeaks(self, value):
    #     self.resources._sourcePeaks = value

    @property
    def _resTableWidget(self):
        """Link to the parent containing the _resTableWidget
        """
        return self.resources._resTableWidget

    @property
    def _outTableWidget(self):
        """Link to the parent containing the _outTableWidget
        """
        return self.resources._outTableWidget

    #=========================================================================================
    # Widget callbacks
    #=========================================================================================

    def selectionCallback(self, selected, deselected, selection, lastItem):
        """Handle item selection has changed in table - call user callback
        :param selected: table indexes selected
        :param deselected: table indexes deselected
        """
        # NOTE:ED - feedback loop? seems a little slow
        try:
            if not (objs := list(selection[self._OBJECT])):
                return
        except Exception as es:
            getLogger().debug2(f'{self.__class__.__name__}.selectionCallback: No selection\n{es}')
            return

        if objs is None:
            self.current.clearPeaks()
            self.current.clearRestraints()
        else:
            newRes = list({res for pk in objs for res in pk.restraints
                           if res and res.restraintTable in self._restraintTables})
            self.current.peaks = objs
            self.current.restraints = newRes

    def actionCallback(self, selection, lastItem):
        """Handle item selection has changed in table - call user callback
        """
        getLogger().debug(f'{self.__class__.__name__}.actionCallback')

        # If current strip contains the double-clicked peak will navigateToPositionInStrip
        from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip, _getCurrentZoomRatio

        # multi-selection table will return a list of objects
        if not (objs := list(selection[self._OBJECT])):
            return

        peak = objs[0] if isinstance(objs, (tuple, list)) else objs

        if self.current.strip is not None:
            validPeakListViews = [pp.peakList for pp in self.current.strip.peakListViews if isinstance(pp.peakList, PeakList)]

            if peak and peak.peakList in validPeakListViews:
                widths = None

                if peak.peakList.spectrum.dimensionCount <= 2:
                    widths = _getCurrentZoomRatio(self.current.strip.viewRange())
                navigateToPositionInStrip(strip=self.current.strip,
                                          positions=peak.position,
                                          axisCodes=peak.axisCodes,
                                          widths=widths)
        else:
            getLogger().warning('Impossible to navigate to peak position. Set a current strip first')

    #=========================================================================================
    # Create table and row methods
    #=========================================================================================

    def _updateTableCallback(self, data):
        """Respond to table notifier.
        """
        obj = data[Notifier.OBJECT]
        if obj != self._table:
            # discard the wrong object
            return

        self._update()

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    # currently in _PeakTableOptions

    def addTableMenuOptions(self, menu):
        self.restraintMenu = _RestraintOptions(self, True)
        self._tableMenuOptions.append(self.restraintMenu)

        super().addTableMenuOptions(menu)

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _getTableColumns(self, source=None):
        """Add default columns plus the ones according to peakList.spectrum dimension
        format of column = ( Header Name, value, tipText, editOption)
        editOption allows the user to modify the value content by doubleclick
        """
        _restraintColumns = [((HeaderRestraint, HeaderRestraint), lambda rt: ''),
                             ((HeaderAtoms, HeaderAtoms), lambda rt: ''),
                             ((HeaderTarget, HeaderTarget), lambda rt: 0.0),
                             ((HeaderLowerLimit, HeaderLowerLimit), lambda rt: 0.0),
                             ((HeaderUpperLimit, HeaderUpperLimit), lambda rt: 0.0),
                             ((HeaderMin, HeaderMin), lambda rt: 0.0),
                             ((HeaderMax, HeaderMax), lambda rt: 0.0),
                             ((HeaderMean, HeaderMean), lambda rt: 0.0),
                             ((HeaderStd, HeaderStd), lambda rt: 0.0),
                             ((HeaderStd, HeaderStd), lambda rt: 0.0),
                             ((HeaderCount2, HeaderCount2), lambda rt: 0.0),
                             ]

        # define self._columns here
        # create the column objects
        _cols = [
            ((HeaderIndex, HeaderIndex), lambda row: _getValueByHeader(row, HeaderIndex), 'TipTex1', None, None),
            ((HeaderPeak, HeaderPeak), lambda row: _getValueByHeader(row, HeaderPeak), 'TipTex2', None, None),
            ((HeaderObject, HeaderObject), lambda row: _getValueByHeader(row, HeaderObject), 'TipTex3', None, None),
            ]

        resLists = self._restraintTables
        outTables = self._outputTables

        # if len(resLists) > 0:
        #     # _buildColumns.append((HeaderExpand, lambda pk, rt: self._downIcon))
        #     _cols.append(((HeaderExpand, HeaderExpand)), lambda row: None, 'TipTex4', None, None))

        # get the dataSets that contain data with a matching 'result' name - should be violations
        violationResults = {resList: viols.data.copy() if viols is not None else None
                            for resList in resLists
                            for viols in outTables
                            if resList.pid == viols.getMetadata(_RESTRAINTTABLE) and viols.getMetadata(_VIOLATIONRESULT) is True
                            }

        if violationResults:
            for resList in resLists:
                if resList in violationResults:
                    _right = violationResults[resList]

                    # create new column headings
                    newCols = [((resList.id, f'{_colID}'), lambda row: _getValueByHeader(row, f'{_colID}'), f'{_colID}', None, None)
                               for _colID in (HeaderRestraint, HeaderAtoms,
                                              HeaderTarget, HeaderLowerLimit, HeaderUpperLimit,
                                              HeaderMin, HeaderMax, HeaderMean, HeaderStd,
                                              HeaderCount1, HeaderCount2)
                               ]

                else:
                    # create new column headings
                    newCols = [((resList.id, f'{_colID}'), lambda row: _getValueByHeader(row, f'{_colID}'), f'{_colID}', None, None)
                               for _colID in (HeaderRestraint, HeaderAtoms)
                               ]

                _cols.extend(newCols)

        else:
            # only show the restraints
            for resList in resLists:
                # create new column headings
                newCols = [((resList.id, f'{_colID}'), lambda row: _getValueByHeader(row, f'{_colID}'), f'{_colID}', None, None)
                           for _colID in (HeaderRestraint, HeaderAtoms)
                           ]

                _cols.extend(newCols)

        # return the table _columns
        return ColumnClass(_cols)

    def buildTableDataFrame(self):
        """Return a Pandas dataFrame from an internal list of objects.
        The columns are based on the 'func' functions in the columnDefinitions.
        :return pandas dataFrame
        """

        def _getContributions(restraint):
            # create a table of the cross-links for speed - does not update!
            return [' - '.join(sorted(ri)) for rc in restraint.restraintContributions
                    for ri in rc.restraintItems]

        rss = self.resources

        # get the target peakLists
        pks = (self._table and self._table.peaks) or []  # ._sourcePeaks
        resLists = self._restraintTables

        INDEXCOL = ('index', 'index')
        PEAKSERIALCOL = ('PeakSerial', 'PeakSerial')
        OBJCOL = ('_object', '_object')

        # need to remove the 'str' and use pd.MultiIndex.from_tuples(list[tuple, ...])

        _cols = [
            (INDEXCOL, lambda row: _getValueByHeader(row, HeaderIndex), 'TipTex1', None, None),
            (PEAKSERIALCOL, lambda row: _getValueByHeader(row, HeaderPeak), 'TipTex2', None, None),
            (OBJCOL, lambda row: _getValueByHeader(row, HeaderObject), 'TipTex3', None, None),
            ]

        if resLists:
            # make references for quicker access later
            contribs = {res: _getContributions(res) for rList in resLists for res in rList.restraints}

            # make a dict of peak.restraints as this is reverse generated by the api every call to peak.restraints
            pkRestraints = {}
            for resList in resLists:
                for res in resList.restraints:
                    for pk in res.peaks:
                        pkRestraints.setdefault(pk.serial, set()).add(res)

            # get the maximum number of restraintItems from each restraint list
            counts = [np.array([sum(len(contribs[res]) for res in (pkRestraints.get(pk.serial) or ()) if res and res.restraintTable == rList
                                    )
                                for pk in pks])
                      for rList in resLists]
            maxCount = np.max(counts, axis=0)

            allPkSerials = pd.DataFrame([pk.serial for pk, count in zip(pks, maxCount) for _ in range(count)],
                                        columns=[PEAKSERIALCOL, ])

            index = pd.DataFrame(list(range(1, len(allPkSerials) + 1)),
                                 columns=[INDEXCOL, ])

            allPks = pd.DataFrame([(pk.serial, pk) for pk, count in zip(pks, maxCount) for _ in range(count)],
                                  columns=[PEAKSERIALCOL, OBJCOL])

            # make matching length tables for each of the restraintTables for each peak so the rows match up in the table
            dfs = {}
            for lCount, rl in enumerate(resLists):
                ll = [(None, None)] * sum(maxCount)
                head = 0
                for pk, cc, maxcc in zip(pks, counts[lCount], maxCount):
                    # ensure that the atoms are sorted so that they are matched correctly
                    _res = [(res.pid, ' - '.join(sorted(_atom.split(' - '), key=universalSortKey)) if _atom else None)
                            for res in (pkRestraints.get(pk.serial) or ()) if res.restraintTable == rl
                            for _atom in contribs[res]]
                    if _res:
                        ll[head:head + len(_res)] = _res

                    head += maxcc

                COLS = [(rl.id, f'{HeaderRestraint}'),
                        (rl.id, 'Atoms')]

                # put the serial and atoms into another table to be concatenated to the right, lCount = index in resLists
                dfs[rl] = pd.concat([allPkSerials,
                                     # pd.DataFrame(ll, columns=[f'{HeaderRestraint}_{lCount + 1}',
                                     #                           f'Atoms_{lCount + 1}'])], axis=1)
                                     pd.DataFrame(ll, columns=COLS)], axis=1)

            # get the dataSets that contain data with a matching 'result' name - should be violations
            violationResults = {resList: viols.data.copy() if viols is not None else None
                                for resList in resLists
                                for viols in self._outputTables
                                if resList.pid == viols.getMetadata(_RESTRAINTTABLE) and viols.getMetadata(_VIOLATIONRESULT) is True
                                }

            if violationResults:

                # rename the columns to match the order in visible list - number must match the position in the selected restraintTables
                for ii, (rl, resViol) in enumerate(violationResults.items()):
                    ind = resLists.index(rl)

                    # change old columns to new columns
                    newCols = [_OLDHEADERS.get(cc, None) or cc for cc in resViol.columns]
                    # resViol.columns = [vv + f'_{ind + 1}' for vv in resViol.columns]
                    # resViol.columns = [vv + f'_{ind + 1}' for vv in newCols]
                    resViol.columns = [(rl.id, vv) for vv in newCols]

                # merge all the tables for each restraintTable
                _out = [index, allPks]
                zeroCols = []
                for ii, resList in enumerate(resLists):
                    if resList in violationResults:

                        HEADERSCOL = (resList.id, f'{HeaderRestraint}')
                        ATOMSCOL = (resList.id, 'Atoms')
                        HEADERMEANCOL = (resList.id, f'{HeaderMean}')

                        _left = dfs[resList]

                        try:
                            # remove any duplicated violations - these add bad rows
                            _right = violationResults[resList].drop_duplicates([HEADERSCOL, ATOMSCOL])

                            # NOTE:ED - hmm, seems to be restraint_id, atom_name_1, etc.

                        except Exception:
                            continue

                        if (HEADERSCOL in _left.columns and ATOMSCOL in _left.columns) and \
                                (HEADERSCOL in _right.columns and ATOMSCOL in _right.columns):
                            _new = pd.merge(_left, _right, on=[HEADERSCOL, ATOMSCOL], how='left').drop(columns=[PEAKSERIALCOL]).fillna(0.0)
                            _out.append(_new)

                            zeroCols.append(HEADERMEANCOL)

                        # _right = violationResults[resList].drop_duplicates([f'{HeaderRestraint}_{ii + 1}', f'Atoms_{ii + 1}'])
                        # if (f'{HeaderRestraint}_{ii + 1}' in _left.columns and f'Atoms_{ii + 1}' in _left.columns) and \
                        #         (f'{HeaderRestraint}_{ii + 1}' in _right.columns and f'Atoms_{ii + 1}' in _right.columns):
                        #     _new = pd.merge(_left, _right, on=[f'{HeaderRestraint}_{ii + 1}', f'Atoms_{ii + 1}'], how='left').drop(columns=[PEAKSERIALCOL]).fillna(0.0)
                        #     _out.append(_new)
                        #
                        #     zeroCols.append(f'{HeaderMean}_{ii + 1}')
                        #
                        for _colID in (HeaderRestraint, HeaderAtoms,
                                       HeaderTarget, HeaderLowerLimit, HeaderUpperLimit,
                                       HeaderMin, HeaderMax, HeaderMean, HeaderStd,
                                       HeaderCount1, HeaderCount2):
                            if (resList.id, _colID) in list(_right.columns):
                                # check whether all the columns exist - discard otherwise
                                # columns should have been renamed and post-fixed with _<num>. above
                                _cols.append(((resList.id, _colID), lambda row: _getValueByHeader(row, f'{_colID}_{ii + 1}'), f'{_colID}_Tip{ii + 1}', None, None))

                    else:
                        # lose the PeakSerial column for each
                        _new = dfs[resList].drop(columns=[PEAKSERIALCOL]).fillna(0.0)
                        _out.append(_new)

                        # # creat new column headings
                        # for _colID in (HeaderRestraint, HeaderAtoms):
                        #     _cols.append((f'{_colID}_{ii + 1}', lambda row: _getValueByHeader(row, f'{_colID}_{ii + 1}'), f'{_colID}_Tip{ii + 1}', None, None))

                # concatenate the final dataFrame
                # _table = pd.concat([index, allPks, *_out.values()], axis=1)
                _table = pd.concat(_out, axis=1)
                # # purge all rows that contain all means == 0, the fastest method
                # _table = _table[np.count_nonzero(_table[zeroCols].values, axis=1) > 0]
                # process all row that have means > 0.3, keep only rows that contain at least one valid mean
                if zeroCols and rss._meanLowerLimit:
                    _table = _table[(_table[zeroCols] >= rss._meanLowerLimit).sum(axis=1) > 0]

            else:
                # only show the restraints

                _out = [index, allPks]
                # no results - just show the table
                for ii, resList in enumerate(resLists):
                    # lose the PeakSerial column for each
                    _new = dfs[resList].drop(columns=[PEAKSERIALCOL]).fillna(0.0)
                    _out.append(_new)

                    # # creat new column headings
                    # for _colID in (HeaderRestraint, HeaderAtoms):
                    #     _cols.append((f'{_colID}_{ii + 1}', lambda row: _getValueByHeader(row, f'{_colID}_{ii + 1}'), f'{_colID}_Tip{ii + 1}', None, None))

                # concatenate to give the final table
                _table = pd.concat(_out, axis=1)

        else:
            # make a table that only has peaks
            index = pd.DataFrame(list(range(1, len(pks) + 1)), columns=[INDEXCOL])
            allPks = pd.DataFrame([(pk.serial, pk) for pk in pks], columns=[PEAKSERIALCOL, OBJCOL])

            _table = pd.concat([index, allPks], axis=1)

        _table.columns = pd.MultiIndex.from_tuples(_table.columns)

        # # set the table _columns
        # self._columns = ColumnClass(_cols)

        # set the table from the dataFrame
        _dataFrame = DataFrameObject(dataFrame=_table,
                                     columnDefs=[],
                                     table=self,
                                     )
        # extract the row objects from the dataFrame
        _objects = list(_table.itertuples())
        _dataFrame._objects = _objects

        return _dataFrame

    #=========================================================================================
    # Updates
    #=========================================================================================

    # NOTE:ED - not done yet
    # def refreshTable(self):
    #     # subclass to refresh the groups
    #     self.setTableFromDataFrameObject(self._dataFrameObject)
    #     self.updateTableExpanders()
    #
    # def setDataFromSearchWidget(self, dataFrame):
    #     """Set the data for the table from the search widget
    #     """
    #     self.setData(dataFrame.values)
    #     self._updateGroups(dataFrame)
    #     self.updateTableExpanders()

    @staticmethod
    def _getSortedContributions(restraint):
        """
        CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
        using ChemicalShiftList
        """
        return [sorted(ri) for rc in restraint.restraintContributions for ri in rc.restraintItems if ri]

    # def _updateGroups(self, df):
    #     self._groups = {}
    #     # collate max/min information
    #     for row in df.itertuples(index=False):
    #         name = str(row[self.PIDCOLUMN])
    #         if name not in self._groups:
    #             _row = tuple(universalSortKey(x) for x in row)
    #             self._groups[name] = {'min': _row, 'max': _row}
    #         else:
    #             self._groups[name]['min'] = tuple(map(lambda x, y: min(universalSortKey(x), y), row, self._groups[name]['min']))
    #             self._groups[name]['max'] = tuple(map(lambda x, y: max(universalSortKey(x), y), row, self._groups[name]['max']))

    def _update(self):
        """Display the objects on the table for the selected list.
        """
        if self._table:
            # NOTE:ED - check whether to use _table or resources
            # self.resources._sourcePeaks = self._table
            self.populateTable()
        else:
            self.populateEmptyTable()

    def _updateTable(self, useSelectedPeakList=True, peaks=None, peakList=None):
        """Display the restraints on the table for the selected PeakList.
        Obviously, If the restraint has not been previously deleted
        """
        rss = self.resources

        # rss._sourcePeaks = self.project.getByPid(rss._modulePulldown.getText())
        self._groups = None
        self.hide()

        # get the correct restraintTables/violationTables from the settings
        rTables = rss._resTableWidget.getTexts()
        if ALL in rTables:
            rTables = self.project.restraintTables
        else:
            rTables = [self.project.getByPid(rList) for rList in rTables]
            rTables = [rList for rList in rTables if rList is not None and isinstance(rList, RestraintTable)]

        vTables = rss._outTableWidget.getTexts()
        if ALL in vTables:
            vTables = [vt for vt in self.project.violationTables if vt.getMetadata(_VIOLATIONRESULT)]
        else:
            vTables = [self.project.getByPid(rList) for rList in vTables]
            vTables = list(filter(None, vTables))
        rss.guiModule._updateCollectionButton(True)

        rss._restraintTables = rTables
        rss._outputTables = vTables

        if useSelectedPeakList:
            if self._table:  # rss._sourcePeaks:
                self.populateTable(rowObjects=self._table.peaks,
                                   selectedObjects=self.current.peaks
                                   )
            else:
                self.populateEmptyTable()

        else:
            if peaks:
                if peakList:
                    self.populateTable(rowObjects=peaks,
                                       selectedObjects=self.current.peaks
                                       )
            else:
                self.populateEmptyTable()

        self.updateTableExpanders()
        self.show()

    #=========================================================================================
    # Widgets callbacks
    #=========================================================================================

    ...

    #=========================================================================================
    # Signal responses
    #=========================================================================================

    def _postChangeSelectionOrderCallback(self, *args):
        super(_NewRestraintWidget, self)._postChangeSelectionOrderCallback(*args)

        print('_postChangeSelectionOrderCallback')
        self.updateTableExpanders()

    #=========================================================================================
    # object properties
    #=========================================================================================

    def updateTableExpanders(self, expandState=None):
        """Update the state of the expander buttons
        """
        if not isinstance(expandState, (bool, type(None))):
            raise TypeError('expandState must be bool or None')

        if self.MERGECOLUMN >= self.columnCount():
            return

        rows = self.rowCount()
        _order = [self.model().index(ii, self.MERGECOLUMN).data() for ii in range(rows)]
        if not _order:
            return

        self.clearSpans()

        row = rowCount = 0
        lastRow = _order[row]
        _expand = self.resources._autoExpand if expandState is None else expandState

        for i in range(rows):

            nextRow = _order[i + 1] if i < (rows - 1) else None  # catch the last group, otherwise need try/except
            if lastRow == nextRow:
                rowCount += 1

            elif rowCount > 0:

                for col in self.SPANCOLUMNS:
                    self.setSpan(row, col, rowCount + 1, 1)
                self.setRowHidden(row, False)
                for rr in range(row + 1, row + rowCount):
                    self.setRowHidden(rr, not _expand)
                self.setRowHidden(row + rowCount, not _expand)

                rowCount = 0
                row = i + 1

            else:
                self.setRowHidden(i, False)
                row = i + 1

            lastRow = nextRow

        self.resizeRowsToContents()

    #=========================================================================================
    # Subclass MITable
    #=========================================================================================


#=========================================================================================
# Core Table for peak-list driven restraints
#=========================================================================================

class RestraintFrame(_CoreTableFrameABC):
    """Frame containing the pulldown and the table widget
    """
    # signal emitted when the manually changing the pulldown
    aboutToUpdate = QtCore.pyqtSignal(str)

    _TableKlass = _NewRestraintWidget
    _PulldownKlass = PeakListPulldown

    def __init__(self, parent, mainWindow=None, moduleParent=None, resources=None,
                 peakList=None, selectFirstItem=False, **kwds):
        super().__init__(parent, mainWindow=mainWindow, moduleParent=moduleParent,
                         obj=peakList, selectFirstItem=selectFirstItem, showGrid=True,
                         **kwds)

        # create widgets for expand/collapse, etc.
        self.expandButtons = ButtonList(parent=self, texts=[' Expand all', ' Collapse all'],
                                        callbacks=[partial(self._expandAll, True), partial(self._expandAll, False), ])
        self.showOnViewerButton = Button(self, tipText='Show on Molecular Viewer',
                                         icon=Icon('icons/showStructure'),
                                         callback=self._showOnMolecularViewer,
                                         hAlign='l')

        # move to the correct positions
        self.addWidgetToTop(self.expandButtons, 2)
        self.addWidgetToTop(self.showOnViewerButton, 3)

        # NOTE:ED - bit of a hack for the minute
        self.resources = resources
        self._tableWidget.resources = resources

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def _tableCurrent(self):
        """Return the list of source objects, e.g., _table.peaks/_table.nmrResidues
        """
        return self.current.peakList

    @_tableCurrent.setter
    def _tableCurrent(self, value):
        self.current.peakList = value

    #=========================================================================================
    # Widgets callbacks
    #=========================================================================================

    def _expandAll(self, expand):
        """Expand/collapse all groups
        """
        self._tableWidget.updateTableExpanders(expand)

    def _showOnMolecularViewer(self):
        """Show the structure in the viewer
        """
        selectedPeaks = self._tableWidget.getSelectedObjects() or []

        # get the restraints to display
        restraints = flattenLists([pk.restraints for pk in selectedPeaks])

        # get the PDB file from the parent restraintTable.
        if pdbPath := next((rs.restraintTable.structureData.moleculeFilePath for rs in restraints if rs.restraintTable.structureData.moleculeFilePath), None):
            getLogger().info(f'Using pdb file {pdbPath} for displaying violation on Molecular viewer.')

        else:
            MessageDialog.showWarning('No Molecule File found',
                                      'To add a molecule file path: Find the StructureData on sideBar,'
                                      'open the properties popup, add a full PDB file path in the entry widget.')
            return

        # run Pymol
        pymolSPath = joinPath(self.moduleParent.pymolScriptsPath, PymolScriptName)

        pymolScriptPath = pyMolUtil._restraintsSelection2PyMolFile(pymolSPath, pdbPath, restraints)
        pyMolUtil.runPymolWithScript(self.application, pymolScriptPath)

    def _selectionPulldownCallback(self, item):
        """Notifier Callback for selecting object from the pull down menu
        """
        if self._modulePulldown.underMouse():
            # tell the parent to clear its lists
            self.aboutToUpdate.emit(self._modulePulldown.getText())

        super(RestraintFrame, self)._selectionPulldownCallback(item)
