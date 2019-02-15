"""This macro folds the currently selected peaks
Fails if peaks from multiple spectra are selected which a different axes ordering of the data
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:38 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning


class AliasingPopup(CcpnDialog):

    def __init__(self, parent=None, mainWindow=None):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Set peak aliasing')

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        if len(self.current.peaks) == 0:
            raise RuntimeError('No peaks selected')

        peak = self.current.peaks[0]
        spectrum = peak.peakList.spectrum

        self.axes = [a.code for a in self.current.strip.axes]
        self.indices = spectrum.getByAxisCodes('indices', self.axes)

        row = 0

        Label(self, 'Set aliasing of %d peaks' % len(self.current.peaks), bold=True, grid=(row, 0), gridSpan=(1, 2))
        row += 1
        self.addSpacer(0, 10, grid=(row, 0))
        row += 1

        self.pulldowns = {}
        for axis, indx in zip(self.axes, self.indices):
            Label(self, 'Along "%s"-axis' % axis, grid=(row, 0))
            self.pulldowns[indx] = PulldownList(self, texts='-2 -1 0 1 2'.split(), index=2, grid=(row, 1))
            row += 1

        self.addSpacer(0, 10, grid=(row, 0))
        row += 1

        ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(row, 0), gridSpan=(1, 2))

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        """

        from ccpn.core.lib.ContextManagers import undoBlock

        with undoBlock():
            try:
                for peak in self.current.peaks:
                    aliasing = [0, 0]
                    for indx in self.indices:
                        aliasing[indx] = int(self.pulldowns[indx].getText())
                    #print('>>>', peak, aliasing)
                    peak.aliasing = aliasing

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))
                if self.application._isInDebugMode:
                    raise es
                return False

            return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()


if len(current.peaks) == 0:
    showWarning('Set peak aliasing', 'No peaks selected')
else:
    popup = AliasingPopup(mainWindow=mainWindow)
    popup.exec()