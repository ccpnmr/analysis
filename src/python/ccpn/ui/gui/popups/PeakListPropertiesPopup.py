"""
Module Documentation here
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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-12-21 12:16:46 +0000 (Wed, December 21, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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
from ccpn.core.PeakList import PeakList


class PeakListPropertiesPopup(PMIListPropertiesPopupABC):
    """
    Popup to handle changing parameters in peakLists
    """

    # class of lists handled by popup
    klass = PeakList
    attributes = [('Id', getattr, None, {'backgroundText': '> Not defined <'}),
                  ('Comment', getattr, setattr, {'backgroundText': '> Optional <'}),
                  ]
    _symbolColourOption = True
    _textColourOption = True
    _lineColourOption = False
    _meritColourOption = True
    _meritOptions = True

    def __init__(self, parent=None, mainWindow=None, peakList=None, spectrum=None, title=None, **kwds):
        super().__init__(parent=parent, mainWindow=mainWindow, ccpnList=peakList, spectrum=spectrum,
                         title='%s Properties' % self.klass.className, **kwds)

        # initialise the buttons and dialog size
        self._postInit()

    def _refreshGLItems(self):
        # emit a signal to rebuild all peaks and multiplets
        self.GLSignals.emitEvent(targets=[self.ccpnList], triggers=[GLNotifier.GLPEAKLISTS,
                                                                    GLNotifier.GLPEAKLISTLABELS])

    def _getListViews(self, ccpnList):
        """Return the listViews containing this list
        """
        return [peakListView for peakListView in self.project.peakListViews
                if peakListView.peakList == ccpnList]

    def _applyAllChanges(self, changes):
        """Apply all changes - add new peaklist to the spectrum
        """
        super()._applyAllChanges(changes)
        if not self.EDITMODE:

            if 'id' in self.ccpnList:
                del self.ccpnList['id']

            # create the new peakList
            self.spectrum.newPeakList(**self.ccpnList)

    def _populateInitialValues(self):
        """Populate the initial values for an empty object
        """
        super()._populateInitialValues()

        # need to get the next available peaklist name
        _num = len(self.spectrum.peakLists) + 1
        self.ccpnList.id = '{}.{}'.format(self.spectrum.name, _num)

