"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-02-04 12:07:36 +0000 (Thu, February 04, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.CustomExportDialog import CustomGLExportDialog
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb

import os
from ccpn.ui.gui.widgets.Spacer import Spacer


class SelectSpectrumDisplayPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Print to File', **kwds)

        self.mainWindow = mainWindow
        if self.mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = self.application.current
        else:
            self.application = None
            self.project = None

        # self.project = project

        self.setContentsMargins(15, 15, 15, 15)  # L,T,R,B
        # self.setFixedWidth(400)
        # self.setFixedHeight(300)

        self.label = Label(self, text='Select Strip to Print', grid=(0, 0), gridSpan=(1, 2),
                           hAlign='centre', vAlign='centre')
        # self.scrollArea = ScrollArea(self, grid=(2, 0), gridSpan=(2, 2), setLayout=True)

        # self._spacer = Spacer(self, 5, 5,
        #                        QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
        #                        grid=(2, 1), gridSpan=(1, 1))

        # self.scrollArea.setWidgetResizable(True)
        # self.scrollAreaWidgetContents = Frame(self, setLayout=True)#QtWidgets.QFrame()
        #
        # self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        # TODO:ED remove scroll area
        self.stripIds = [sd.id for sd in self.project.strips]
        self.stripPids = [sd.pid for sd in self.project.strips]
        self.radioButtonBox = RadioButtons(self,  #self.scrollAreaWidgetContents
                                           self.stripIds,
                                           grid=(3, 0), gridSpan=(1, 2),
                                           direction='v')

        # self.radioButtonBox.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
        #                                   QtWidgets.QSizePolicy.MinimumExpanding)

        # self.scrollArea.setWidget(self.radioButtonBox)

        # self.spectrumSelectionWidget = SpectrumDisplaySelectionWidget(self._sequenceGraphScrollArea, project, setLayout=True)
        self.buttonBox = ButtonList(self, grid=(4, 0), gridSpan=(1,3),
                                    callbacks=[self.reject, self.getStripToPrint],
                                    texts=['Cancel', 'Select Strip'])
        if self.mainWindow:
            self.radioButtonBox.set(self.current.strip.id)

        self.radioButtonBox.setMinimumSize(self.radioButtonBox.sizeHint())
        self.radioButtonBox.setContentsMargins(15, 15, 15, 15)  # L,T,R,B
        self.setFixedSize(self.sizeHint())

    def getStripToPrint(self):
        pIndex = self.radioButtonBox.getIndex()
        thisPid = self.stripPids[pIndex]
        strip = self.project.getByPid(thisPid)

        self.reject()  #close the popup, not needed anymore
        if strip:
            glWidget = strip._CcpnGLWidget

            self.exportDialog = CustomGLExportDialog(glWidget, titleName=strip.id, )
            self.exportDialog.show(strip.viewBox)
