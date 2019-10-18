"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.core.MultipletList import MULTIPLETAVERAGINGTYPES
from ccpn.ui.gui.popups.PMIListPropertiesPopupABC import PMIListPropertiesPopupABC
from ccpn.core.MultipletList import MultipletList


class MultipletListPropertiesPopup(PMIListPropertiesPopupABC):
    """
    Popup to handle changing parameters in multipletLists
    """
    # class of lists handled by popup
    _baseClass = MultipletList
    _symbolColourOption = True
    _textColourOption = True
    _lineColourOption = True
    _meritColourOption = True
    _meritOptions = True

    def __init__(self, parent=None, mainWindow=None, multipletList=None, title=None, **kwds):
        super().__init__(parent=parent, mainWindow=mainWindow, ccpnList=multipletList,
                         title='%s Properties' % self._baseClass.className, **kwds)

        self.multipletAveragingLabel = Label(self, text="Multiplet Averaging:", grid=(self._rowForNewItems, 0))
        multipletAveraging = self.ccpnList.multipletAveraging
        self.multipletAveraging = RadioButtons(self, texts=MULTIPLETAVERAGINGTYPES,
                                               selectedInd=MULTIPLETAVERAGINGTYPES.index(
                                                   multipletAveraging) if multipletAveraging in MULTIPLETAVERAGINGTYPES else 0,
                                               callback=self._applyChanges,
                                               direction='v',
                                               grid=(self._rowForNewItems, 1), hAlign='l',
                                               tipTexts=None,
                                               )

        self.setFixedSize(self.sizeHint())

    def _setMeritAttributes(self):
        """set the attributes from the other widgets
        """
        super()._setMeritAttributes()

        value = self.multipletAveraging.getSelectedText()
        self.ccpnList.multipletAveraging = value

    def _refreshGLItems(self):
        # emit a signal to rebuild all peaks and multiplets
        self.GLSignals.emitEvent(targets=[self.ccpnList], triggers=[GLNotifier.GLMULTIPLETLISTS,
                                                                    GLNotifier.GLMULTIPLETLISTLABELS])

    def _getListViews(self, ccpnList):
        """Return the listViews containing this list
        """
        return [multipletListView for multipletListView in ccpnList.project.multipletListViews
                if multipletListView.multipletList == ccpnList]
