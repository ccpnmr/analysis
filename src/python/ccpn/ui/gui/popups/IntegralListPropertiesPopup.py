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
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import ccpn.util.Colour as Colour
from ccpn.ui.gui.widgets.MessageDialog import MessageDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger


class IntegralListPropertiesPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, integralList=None, title='Integral List Properties', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.integralList = integralList

        if not self.integralList:
            MessageDialog.showWarning(title, 'No integralList Found')
            self.close()

        else:
            self.peakListViews = [integralListView for integralListView in integralList.project.peakListViews if integralListView.peakList == integralList]

            # NOTE: below is not sorted in any way, but if we change that, we also have to change loop in _fillColourPulldown
            spectrumColourKeys = list(Colour.spectrumColours.keys())
            if not self.integralList.symbolColour:
                self.integralList.symbolColour = spectrumColourKeys[0]  # default
            if not self.integralList.textColour:
                self.integralList.textColour = spectrumColourKeys[1]  # default*

            self.integralListLabel = Label(self, "Integral List Name ", grid=(0, 0))
            self.integralListLabel = Label(self, integralList.id, grid=(0, 1))

            self.symbolColourLabel = Label(self, 'Integral Colour', grid=(3, 0))
            self.symbolColourPulldownList = PulldownList(self, grid=(3, 1))
            Colour.fillColourPulldown(self.symbolColourPulldownList, allowAuto=True)

            c = integralList.symbolColour
            if c in spectrumColourKeys:
                self.symbolColourPulldownList.setCurrentText(Colour.spectrumColours[c])
            else:
                Colour.addNewColourString(c)
                Colour.fillColourPulldown(self.symbolColourPulldownList, allowAuto=True)
                Colour.selectPullDownColour(self.symbolColourPulldownList, c, allowAuto=True)

            self.symbolColourPulldownList.activated.connect(self._applyChanges)

            # self.textColourLabel = Label(self, 'Integral Text Colour', grid=(4, 0))
            # self.textColourPulldownList = PulldownList(self, grid=(4, 1))
            # Colour.fillColourPulldown(self.textColourPulldownList, allowAuto=True)
            #
            # c = integralList.textColour
            # if c in spectrumColourKeys:
            #   self.textColourPulldownList.setCurrentText(Colour.spectrumColours[c])
            # else:
            #   Colour.addNewColourString(c)
            #
            #   # repopulate both pulldowns
            #   Colour.fillColourPulldown(self.symbolColourPulldownList, allowAuto=True)
            #   Colour.fillColourPulldown(self.textColourPulldownList, allowAuto=True)
            #   Colour.selectPullDownColour(self.textColourPulldownList, c, allowAuto=True)
            #
            # self.textColourPulldownList.activated.connect(self._applyChanges)

            self.closeButton = Button(self, text='Close', grid=(6, 1), callback=self._accept)

        self.numUndos = 0

    def _changeColours(self):
        value = self.symbolColourPulldownList.currentText()
        colour = Colour.getSpectrumColour(value, defaultReturn='#')
        self.integralList.symbolColour = colour

        # value = self.textColourPulldownList.currentText()
        # colour = Colour.getSpectrumColour(value, defaultReturn='#')
        # self.integralList.textColour = colour

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        while self.numUndos > 0:  # remove any previous undo from this popup
            # self.application.undo()     # so only the last colour change is kept
            self.project._undo.undo()  # this doesn't popup the undo progressManager
            self.numUndos -= 1

        applyAccept = False
        oldUndo = self.project._undo.numItems()

        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
        from ccpn.core.lib.ContextManagers import undoBlockManager

        GLSignals = GLNotifier(parent=self)

        with undoBlockManager():
            try:
                self._changeColours()

                applyAccept = True

                # repaint
                GLSignals.emitEvent(targets=[self.integralList], triggers=[GLNotifier.GLINTEGRALLISTS])

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))

        if applyAccept is False:
            # should only undo if something new has been added to the undo deque
            # may cause a problem as some things may be set with the same values
            # and still be added to the change list, so only undo if length has changed
            errorName = str(self.__class__.__name__)
            if oldUndo != self.project._undo.numItems():
                self.project._undo.undo()
                getLogger().debug('>>>Undo.%s._applychanges' % errorName)
            else:
                getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

            return False
        else:
            self.numUndos += 1
            return True

    def _okButton(self):
        if self._applyChanges() is True:
            self._accept()

    def _accept(self):
        self.symbolColourPulldownList.activated.disconnect(self._applyChanges)
        # self.textColourPulldownList.activated.disconnect(self._applyChanges)
        self.accept()
