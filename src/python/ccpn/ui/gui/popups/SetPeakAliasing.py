"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget


MINALIASING = -3
MAXALIASING = 3
DEFAULTALIASING = 0 - MINALIASING
COLWIDTH = 140


class SetPeakAliasingPopup(CcpnDialog):
    """
    Open a small popup to allow setting aliasing value of selected 'current' items
    """

    def __init__(self, parent=None, mainWindow=None, title='Set Aliasing', items=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        row = 0
        self.spectra = OrderedDict()
        self.spectraPulldowns = OrderedDict()

        spectrumFrame = Frame(self, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1,2))
        for peak in self.current.peaks:

            if peak.peakList.spectrum not in self.spectra:
                spectrum = peak.peakList.spectrum
                self.spectra[spectrum] = set()

                # add pulldown widget
                Label(spectrumFrame, text='Spectrum: %s' % str(spectrum.pid), grid=(row, 0), bold=True)
                Label(spectrumFrame, text=' axisCodes:', grid=(row, 1))

                dims = spectrum.dimensionCount
                for dim in range(dims):
                    Label(spectrumFrame, text=spectrum.axisCodes[dim], grid=(row, dim+2))

                row += 1
                self.spectraPulldowns[spectrum] = []
                Label(spectrumFrame, text=' aliasing:', grid=(row, 1))
                for dim in range(dims):
                    self.spectraPulldowns[spectrum].append(PulldownList(spectrumFrame, texts=[str(tt) for tt in range(MINALIASING, MAXALIASING+1)],
                                                           grid=(row, dim+2)))  #, index=DEFAULTALIASING))

                row += 1
            self.spectra[peak.peakList.spectrum].add(peak)

        row += 1
        # add close buttons at the bottom
        self.buttonList = ButtonList(self, ['Close', 'OK'], [self.reject, self._okButton], grid=(row, 1))
        self.buttonList.buttons[1].setFocus()

        for spectrum in self.spectra.keys():
            dims = spectrum.dimensionCount
            dimAlias = []
            for dim in range(dims):
                dimAlias.append(set())

            for peak in self.spectra[spectrum]:
                pa = peak.aliasing
                for dim in range(dims):
                    dimAlias[dim].add(pa[dim])

            for dim in range(dims):
                if len(dimAlias[dim]) == 1:
                    self.spectraPulldowns[spectrum][dim].select(str(dimAlias[dim].pop()))
                else:
                    self.spectraPulldowns[spectrum][dim].select('0')

        self.setFixedSize(self.sizeHint())

        self.GLSignals = GLNotifier(parent=self)

    def _refreshGLItems(self):
        # emit a signal to rebuild all peaks
        self.GLSignals.emitEvent(triggers=[GLNotifier.GLALLPEAKS, GLNotifier.GLALLMULTIPLETS])

    def _okButton(self):
        """
        When ok button pressed: update and exit
        """
        applyAccept = False
        undo = self.project._undo
        oldUndo = undo.numItems()

        from ccpn.core.lib.ContextManagers import undoBlock, undoStackBlocking
        from functools import partial

        with undoBlock():
            try:
                # add item here to redraw items
                with undoStackBlocking() as addUndoItem:
                    addUndoItem(undo=self._refreshGLItems)

                for spec in self.spectra.keys():
                    newAlias = tuple([int(pullDown.get()) for pullDown in self.spectraPulldowns[spec]])

                    for peak in self.spectra[spec]:
                        peak.aliasing = newAlias

                # add item here to redraw items
                with undoStackBlocking() as addUndoItem:
                    addUndoItem(redo=self._refreshGLItems)

                applyAccept = True
            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))

        # redraw the items
        self._refreshGLItems()

        if applyAccept is False:
            # should only undo if something new has been added to the undo deque
            # may cause a problem as some things may be set with the same values
            # and still be added to the change list, so only undo if length has changed
            errorName = str(self.__class__.__name__)

            if oldUndo != undo.numItems():
                self.project._undo.undo()
                getLogger().debug('>>>Undo.%s._applychanges' % errorName)
            else:
                getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

        self.accept()
