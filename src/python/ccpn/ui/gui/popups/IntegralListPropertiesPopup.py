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

from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.ui.gui.popups.PMIListPropertiesPopupABC import PMIListPropertiesPopupABC
from ccpn.core.IntegralList import IntegralList


class IntegralListPropertiesPopup(PMIListPropertiesPopupABC):
    """
    Popup to handle changing parameters in multipletLists
    """
    # class of lists handled by popup
    _baseClass = IntegralList
    _symbolColourOption = True
    _textColourOption = True
    _lineColourOption = False
    _meritColourOption = True
    _meritOptions = True

    def __init__(self, parent=None, mainWindow=None, integralList=None, title=None, **kwds):
        super().__init__(parent=parent, mainWindow=mainWindow, ccpnList=integralList,
                         title='%s Properties' % self._baseClass.className, **kwds)

        self.__postInit__()

    def _refreshGLItems(self):
        # emit a signal to rebuild all peaks and multiplets
        self.GLSignals.emitEvent(targets=[self.ccpnList], triggers=[GLNotifier.GLINTEGRALLISTS,
                                                                    GLNotifier.GLINTEGRALLISTLABELS])

    def _getListViews(self, ccpnList):
        """Return the listViews containing this list
        """
        return [integralListView for integralListView in ccpnList.project.integralListViews
                if integralListView.integralList == ccpnList]
