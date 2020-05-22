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
__dateModified__ = "$dateModified: 2020-05-22 19:02:19 +0100 (Fri, May 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.core.MultipletList import MULTIPLETAVERAGINGTYPES
from ccpn.ui.gui.popups.PMIListPropertiesPopupABC import PMIListPropertiesPopupABC, queueStateChange
from ccpn.ui.gui.popups.Dialog import _verifyPopupApply
from ccpn.core.MultipletList import MultipletList


MULTIPLETAVERAGING = 'multipletAveraging'


class MultipletListPropertiesPopup(PMIListPropertiesPopupABC):
    """
    Popup to handle changing parameters in multipletLists
    """

    # class of lists handled by popup
    klass = MultipletList
    attributes = [('id', getattr, None, {'backgroundText': '> Not defined <'}),
                  ('comment', getattr, setattr, {'backgroundText': '> Optional <'}),
                  ]
    _symbolColourOption = True
    _textColourOption = True
    _lineColourOption = True
    _meritColourOption = True
    _meritOptions = True

    def __init__(self, parent=None, mainWindow=None, multipletList=None, title=None, **kwds):
        super().__init__(parent=parent, mainWindow=mainWindow, ccpnList=multipletList,
                         title='%s Properties' % self.klass.className, **kwds)

        self.multipletAveragingLabel = Label(self.mainWidget, text="Multiplet Averaging:", grid=(self._rowForNewItems, 0))
        multipletAveraging = self.ccpnList.multipletAveraging
        self.multipletAveraging = RadioButtons(self.mainWidget, texts=MULTIPLETAVERAGINGTYPES,
                                               selectedInd=MULTIPLETAVERAGINGTYPES.index(
                                                       multipletAveraging) if multipletAveraging in MULTIPLETAVERAGINGTYPES else 0,
                                               callback=self._queueSetMeritAveraging,
                                               direction='v',
                                               grid=(self._rowForNewItems, 1), hAlign='l',
                                               tipTexts=None,
                                               )

        self.__postInit__()

    def _getSettings(self):
        """Fill the settings dict from the listView object
        """
        super()._getSettings()

        # add the merit averaging
        self.listViewSettings[MULTIPLETAVERAGING] = getattr(self.ccpnList, MULTIPLETAVERAGING, None) or \
                                                    MULTIPLETAVERAGINGTYPES[0]

    def _setWidgetSettings(self):
        """Populate the widgets from the settings dict
        """
        super()._setWidgetSettings()

        multipletAveraging = self.listViewSettings[MULTIPLETAVERAGING]
        self.multipletAveraging.setIndex(MULTIPLETAVERAGINGTYPES.index(multipletAveraging)
                                         if multipletAveraging in MULTIPLETAVERAGINGTYPES else 0)

    def _setListViewFromWidgets(self):
        """Set listView object from the widgets
        """
        super()._setListViewFromWidgets()

        multipletAveraging = self.multipletAveraging.getIndex()
        setattr(self.ccpnList, MULTIPLETAVERAGING, MULTIPLETAVERAGINGTYPES[multipletAveraging])

    def _setListViewFromSettings(self):
        """Set listView object from the original settings dict
        """
        super()._setListViewFromSettings()

        multipletAveraging = self.listViewSettings[MULTIPLETAVERAGING]
        if multipletAveraging is not None:
            setattr(self.ccpnList, MULTIPLETAVERAGING, multipletAveraging)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _refreshGLItems(self):
        # emit a signal to rebuild all peaks and multiplets
        self.GLSignals.emitEvent(targets=[self.ccpnList], triggers=[GLNotifier.GLMULTIPLETLISTS,
                                                                    GLNotifier.GLMULTIPLETLISTLABELS])

    def _getListViews(self, ccpnList):
        """Return the listViews containing this list
        """
        return [multipletListView for multipletListView in ccpnList.project.multipletListViews
                if multipletListView.multipletList == ccpnList]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @queueStateChange(_verifyPopupApply)
    def _queueSetMeritAveraging(self):
        value = MULTIPLETAVERAGINGTYPES[self.multipletAveraging.getIndex()]
        # set the state of the other buttons
        if value != getattr(self.COMPARELIST, MULTIPLETAVERAGING, MULTIPLETAVERAGINGTYPES[0]):
            return partial(self._setMeritAveraging, value)

    def _setMeritAveraging(self, value):
        setattr(self.ccpnList, MULTIPLETAVERAGING, value)
