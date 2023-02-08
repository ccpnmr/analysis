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
__dateModified__ = "$dateModified: 2023-02-08 19:52:32 +0000 (Wed, February 08, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-01-20 15:57:58 +0100 (Fri, January 20, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from dataclasses import dataclass

from PyQt5 import QtWidgets

from ccpn.ui.gui.lib.GuiStripContextMenus import _selectedPeaksMenuItem, _addMenuItems, _getNdPeakMenuItems, _setEnabledAllItems
from ccpn.ui.gui.widgets.table._TableAdditions import TableMenuABC


UNITS = ['ppm', 'Hz', 'point']
HeaderIndex = '#'
HeaderPeak = 'Peak Serial'
HeaderObject = '_object'
HeaderExpand = 'Expand'
HeaderRestraint = 'Restraint Pid'
HeaderAtoms = 'Atoms'
HeaderTarget = 'Target Value'
HeaderLowerLimit = 'Lower Limit'
HeaderUpperLimit = 'Upper Limit'
HeaderMin = 'Min'
HeaderMax = 'Max'
HeaderMean = 'Mean'
HeaderStd = 'STD'
HeaderCount1 = 'Count > 0.3'
HeaderCount2 = 'Count > 0.5'
nefHeaders = ['restraintpid', 'atoms',
              'target_value', 'lower_limit', 'upper_limit',
              'min', 'max', 'mean', 'std',
              'count_0_3', 'count_0_5']
Headers = [HeaderRestraint,
           HeaderAtoms,
           HeaderTarget,
           HeaderLowerLimit,
           HeaderUpperLimit,
           HeaderMin,
           HeaderMax,
           HeaderMean,
           HeaderStd,
           HeaderCount1,
           HeaderCount2]
_OLDHEADERS = {'RestraintPid': HeaderRestraint,
               'Count>0.3'   : HeaderCount1,
               'Count>0.5'   : HeaderCount2}
PymolScriptName = 'Restraint_Pymol_Template.py'
_COLLECTION = 'Collection'
_COLLECTIONBUTTON = 'CollectionButton'
_SPECTRUMDISPLAYS = 'SpectrumDisplays'
_RESTRAINTTABLES = 'RestraintTables'
_VIOLATIONTABLES = 'ViolationTables'
_RESTRAINTTABLE = 'restraintTable'
_VIOLATIONRESULT = 'violationResult'
_DEFAULTMEANTHRESHOLD = 0.0

ALL = '<Use all>'


#=========================================================================================
# _ModuleHandler - information common to all classes/widgets in the module
#=========================================================================================

@dataclass
class _ModuleHandler(QtWidgets.QWidget):
    # Use a QWidget as it can handle signals - maybe for later

    # gui resources
    guiModule = None
    guiFrame = None

    # non-gui resources
    _restraintTables = []
    _outputTables = []
    # _sourcePeaks = []
    _thisPeakList = None

    _collectionPulldown = None
    _collectionButton = None
    _displayListWidget = None
    _resTableWidget = None
    _outTableWidget = None
    _modulePulldown = None

    _meanLowerLimitSpinBox = None
    _autoExpandCheckBox = None
    _autoExpand = False

    _restraintTableFilter = {}
    _outputTableFilter = {}
    _modulePulldownFilter = []


#=========================================================================================
# _RestraintOptions - additions to the right-mouse menu
#=========================================================================================

class _RestraintOptions(TableMenuABC):
    """Class to handle peak-driven Restraint Analysis options from a right-mouse menu.
    """

    def addMenuOptions(self, menu):
        """Add options to the right-mouse menu
        """
        parent = self._parent

        menu.addSeparator()
        _peakItem = _selectedPeaksMenuItem(None)
        _addMenuItems(parent, menu, [_peakItem])

        # _selectedPeaksMenu submenu - add to Strip._selectedPeaksMenu
        items = _getNdPeakMenuItems(menuId='Main')
        # attach to the _selectedPeaksMenu submenu
        _addMenuItems(parent, parent._selectedPeaksMenu, items)

    def setMenuOptions(self, menu):
        """Update options in the right-mouse menu
        """
        parent = self._parent
        submenu = parent._selectedPeaksMenu

        # Enable/disable menu items as required
        parent._navigateToPeakMenuMain.setEnabled(False)
        _setEnabledAllItems(submenu, bool(parent.current.peaks))

    #=========================================================================================
    # Properties
    #=========================================================================================

    pass

    #=========================================================================================
    # Class methods
    #=========================================================================================

    pass

    #=========================================================================================
    # Implementation
    #=========================================================================================

    pass
