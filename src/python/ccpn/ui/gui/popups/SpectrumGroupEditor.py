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
__dateModified__ = "$dateModified: 2020-01-23 13:20:54 +0000 (Thu, January 23, 2020) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.PulldownListsForObjects import SpectrumGroupPulldown
from ccpn.ui.gui.popups._GroupEditorPopupABC import _GroupEditorPopupABC
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import ColourTab, ContoursTab


DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 1, 5)  # l, t, r, b


class SpectrumGroupEditor(_GroupEditorPopupABC):
    """
    A popup to create and manage SpectrumGroups

    Used in 'New' or 'Edit' mode:
    - For creating new SpectrumGroup (editMode==False); optionally uses passed in spectra list
      i.e. NewSpectrumGroup of SideBar and Context menu of SideBar

    - For editing existing SpectrumGroup (editMode==True); requires spectrumGroup argument
      i.e. Edit of SpectrumGroup of SideBar
    or
      For selecting and editing SpectrumGroup (editMode==True)
      i.e. Menu Spectrum->Edit SpectrumGroup...

    """
    KLASS = SpectrumGroup
    KLASS_ITEM_ATTRIBUTE = 'spectra'  # Attribute in KLASS containing items
    KLASS_PULLDOWN = SpectrumGroupPulldown

    PROJECT_NEW_METHOD = 'newSpectrumGroup'  # Method of Project to create new KLASS instance
    PROJECT_ITEM_ATTRIBUTE = 'spectra'  # Attribute of Project containing items
    PLURAL_GROUPED_NAME = 'Spectrum Groups'
    SINGULAR_GROUP_NAME = 'Spectrum Group'

    GROUP_PID_KEY = 'SG'
    ITEM_PID_KEY = 'SP'

    # make this a tabbed dialog, with the default widget going into tab 0
    USE_TAB = 0
    NUMBER_TABS = 3  # create the first tab

    def __init__(self, parent=None, mainWindow=None, editMode=True, obj=None, defaultItems=None, **kwds):
        """
        Initialise the widget, note defaultItems is only used for create
        """
        super().__init__(parent=parent, mainWindow=mainWindow, editMode=editMode, obj=obj, defaultItems=defaultItems, **kwds)

        self.TAB_NAMES = (('Spectra', self._initSpectraTab),
                          ('General', self._initGeneralTab),
                          ('Series', self._initSeriesTab))

        self.spectraTab = self._tabWidget.widget(0)._scrollContents
        self.generalTab = self._tabWidget.widget(1)._scrollContents
        self.seriesTab = self._tabWidget.widget(2)._scrollContents

        self.currentSpectra = self._getSpectraFromList()

        for tNum, (tabName, tabFunc) in enumerate(self.TAB_NAMES):
            self._tabWidget.setTabText(tNum, tabName)
            if tabFunc:
                tabFunc()

        # TODO:ED set to the size of the first tab - or a fixed size so the first tab looks nice

        self._populate()
        self.setMinimumSize(600, 550)       # change to a calculation rather than a guess

        self.connectSignals()

    def connectSignals(self):
        # connect to changes in the spectrumGroup
        self.leftListWidget.model().dataChanged.connect(self._spectraChanged)
        self.leftListWidget.model().rowsRemoved.connect(self._spectraChanged)
        self.leftListWidget.model().rowsInserted.connect(self._spectraChanged)
        self.leftListWidget.model().rowsMoved.connect(self._spectraChanged)

    def _initSpectraTab(self):
        thisTab = self.spectraTab

    def _initGeneralTab(self):
        thisTab = self.generalTab
        self._colourTabs = Tabs(thisTab, grid=(0, 0))

        # TODO:ED need to get the list of spectra from the first tab

        # self.orderedSpectrumViews = orderedSpectrumViews
        # self.orderedSpectra = OrderedSet([spec.spectrum for spec in self.orderedSpectrumViews])

        # remember the state when switching tabs
        self.copyCheckBoxState = []

        for specNum, thisSpec in enumerate(self.currentSpectra or []):
            contoursTab = ContoursTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec,
                                      showCopyOptions=True if len(self.currentSpectra) > 1 else False,
                                      copyToSpectra=self.currentSpectra)
            self._colourTabs.addTab(contoursTab, thisSpec.name)
            contoursTab.setContentsMargins(*TABMARGINS)

        self._colourTabs.setTabClickCallback(self._tabClicked)

    def _initSeriesTab(self):
        thisTab = self.generalTab

        # TODO:ED setup a pandas table for the spectra as the first column
        pass

    def _populate(self):
        """Populate the widgets in the tabs
        """
        with self.blockWidgetSignals():
            for aTab in tuple(self._colourTabs.widget(ii) for ii in range(self._colourTabs.count())):
                aTab._populateColour()

    def _tabClicked(self, index):
        """Callback for clicking a tab - needed for refilling the checkboxes and populating the pulldown
        """
        aTabs = tuple(self._colourTabs.widget(ii) for ii in range(self._colourTabs.count()))
        if hasattr(aTabs[index], '_populateCheckBoxes'):
            aTabs[index]._populateCheckBoxes()

    def _getSpectraFromList(self):
        """Get the list of spectra from the list
        """
        return [spec for spec in [self.project.getByPid(spectrum) if isinstance(spectrum, str) else spectrum for spectrum in self._groupedObjects] if spec]

    def _spectraChanged(self, *args):
        """Respond to a change in the list of spectra to add the spectrumGroup
        """
        self._newSpectra = self._getSpectraFromList()

        # TODO:ED remove tabs for spectra removed from list
        #           add new tabs in correct place
        #           remember to remove any _queue settings from updated colour tabs
        #           populate new tabs


