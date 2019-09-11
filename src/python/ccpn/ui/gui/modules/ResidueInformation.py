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
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.core.lib.AssignmentLib import CCP_CODES
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.modules.SequenceModule import SequenceModule
from ccpn.ui.gui.guiSettings import getColours
from ccpn.ui.gui.guiSettings import LABEL_SELECTEDBACKGROUND, LABEL_SELECTEDFOREGROUND, LABEL_HIGHLIGHT


class ResidueInformation(CcpnModule):
    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'
    className = 'ResidueInformation'

    _residueWidth = '3'

    def __init__(self, mainWindow, name='Residue Information', **kwds):
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if self.mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        # add a splitter to contain the residue table and the sequence module
        self.splitter = Splitter(self.mainWidget, horizontal=False)
        self._sequenceModuleFrame = Frame(None, setLayout=True)
        # self._SequenceGraphFrame = Frame(self.splitter, setLayout=True)
        self.mainWidget.getLayout().addWidget(self.splitter, 1, 0)

        # initialise the sequence module
        self.thisSequenceModule = SequenceModule(moduleParent=self,
                                                 parent=self._sequenceModuleFrame,
                                                 mainWindow=mainWindow)

        # add a scroll area to contain the residue table
        self._widgetScrollArea = ScrollArea(parent=self.mainWidget, grid=(0, 0), scrollBarPolicies=('asNeeded', 'asNeeded'), **kwds)
        self._widgetScrollArea.setWidgetResizable(True)
        self._widget = Widget(parent=self._widgetScrollArea, setLayout=True)
        self._widgetScrollArea.setWidget(self._widget)
        self._widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # insert into the mainWidget
        self.splitter.addWidget(self._widgetScrollArea)
        self.splitter.addWidget(self._sequenceModuleFrame)
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setChildrenCollapsible(False)

        # make a frame to contain the pulldown widgets
        self._pulldownFrame = Frame(self._widget, setLayout=True, showBorder=False, grid=(0, 0))

        # insert into pulldownFrame
        self.chainLabel = Label(self._pulldownFrame, text='Chain', grid=(0, 0))
        # self.layout.addWidget(chainLabel, 0, 0)
        chainPulldown = PulldownList(self._pulldownFrame, callback=self._setChain, grid=(0, 1))
        chainPulldownData = [chain.pid for chain in self.project.chains]
        chainPulldownData.append('<All>')
        chainPulldown.setData(chainPulldownData)
        self.selectedChain = self.project.getByPid(chainPulldown.currentText())
        self.residueLabel = Label(self._pulldownFrame, text='Residue ', grid=(0, 3))

        self.colourScheme = self.application.colourScheme
        self.residuePulldown = PulldownList(self._pulldownFrame, callback=self._setCurrentResidue,
                                            grid=(0, 4))

        self._residueWidthLabel = Label(self._pulldownFrame, text='Residue window width', grid=(0, 5))
        self._residueWidthData = PulldownList(self._pulldownFrame, #callback=self._setResidueWidth,
                                            grid=(0, 6))
        self._residueWidthData.setData(texts=['1', '3', '5', '7'])
        self._residueWidthData.set(self._residueWidth)

        self.residuePulldown.setData(CCP_CODES)
        self.selectedResidueType = self.residuePulldown.currentText()

        # set the callback after populating
        self._residueWidthData.setCallback(self._setResidueWidth)
        # add under the pulldownFrame
        self.residueWidget = Widget(self._widget, setLayout=True,
                                    grid=(1, 0), gridSpan=(1, 2))

        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
                             grid=(2, 3), gridSpan=(1, 1))

        self._widget.setContentsMargins(5, 5, 5, 5)

        # self.residueWidget = QtWidgets.QWidget(self)
        # self.residueWidget.setLayout(QtWidgets.QGridLayout())
        # self.project = project
        # self.layout.addWidget(self.residueWidget, 1, 0, 1, 5)
        self._getResidues()

    def _setResidueWidth(self, *args):
        self._residueWidth = self._residueWidthData.get()
        self._getResidues()

    def _setChain(self, value: str):
        """
        Sets the selected chain to the specified value and updates the module.
        """
        if value == '<All>':
            self.selectedChain = 'All'
        else:
            self.selectedChain = self.project.getByPid(value)
        self._getResidues()

    def _setCurrentResidue(self, value: str):
        """
        Sets the selected residue to the specified value and updates the module.
        """
        self.selectedResidueType = value
        self._getResidues()

    def _setWidgetColour(self, widget):
        """Set the colour for the label
        """
        palette = widget.palette()
        palette.setColor(QtGui.QPalette.Foreground, QtGui.QColor(LABEL_SELECTEDFOREGROUND))
        palette.setColor(QtGui.QPalette.Background, QtGui.QColor(LABEL_SELECTEDBACKGROUND))
        widget.setPalette(palette)

    def _removeWidget(self, widget, removeTopWidget=False):
        """Destroy a widget and all it's contents
        """
        def deleteItems(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
                        widget.setParent(None)
                        del widget

        deleteItems(widget.getLayout())
        if removeTopWidget:
            del widget

    def _getResidues(self):
        """
        Finds all residues of the selected type along with one flanking residue either side and displays
        this information in the module.
        """
        colours = getColours()
        stylesheet = """Label { background-color: %s; color: %s;}
                     Label::hover { background-color: %s}""" % (colours[LABEL_SELECTEDBACKGROUND],
                                                                colours[LABEL_SELECTEDFOREGROUND],
                                                                colours[LABEL_HIGHLIGHT])

        # # self.setDefaultTextColor(QtGui.QColor(self.colours[GUINMRRESIDUE]))
        #
        # if self.colourScheme == 'dark':
        #     # stylesheet = 'Label {background-color: #f7ffff; color: #2a3358;}'
        #     stylesheet = """Label { background-color: %s; color: %s;}
        #                  Label::hover { background-color: %s}""" % (colours[LABEL_SELECTEDBACKGROUND],
        #                                                                colours[LABEL_SELECTEDFOREGROUND],
        #                                                                colours[LABEL_SELECTEDFOREGROUND])
        # elif self.colourScheme == 'light':
        #     # stylesheet = 'Label {background-color: #bd8413; color: #fdfdfc;}'
        #     stylesheet = """Label { background-color: %s; color: %s;}
        #                  Label::hover { background-color: %s}""" % (colours[LABEL_SELECTEDBACKGROUND],
        #                                                                colours[LABEL_SELECTEDFOREGROUND],
        #                                                                colours[LABEL_SELECTEDFOREGROUND])

        foundResidues = []

        if self.selectedChain == 'All':
            residues = self.project.residues
        else:
            if self.selectedChain is not None:
                residues = self.selectedChain.residues
            else:
                return

        if residues:
            width = int(self._residueWidthData.get()) // 2

            for resInd, residue in enumerate(residues):
                if residue.residueType == self.selectedResidueType.upper():
                    # add the previous and next residue chains to the visible list for this residue
                    resList = [residue]
                    leftRes = residue
                    rightRes = residue
                    for count in range(width):
                        if leftRes:
                            resList.insert(0, leftRes.previousResidue)
                            leftRes = leftRes.previousResidue
                        else:
                            resList.insert(0, None)
                    for count in range(width):
                        if rightRes:
                            resList.append(rightRes.nextResidue)
                            rightRes = rightRes.nextResidue
                        else:
                            resList.append(None)
                    foundResidues.append(resList)

            self._removeWidget(self.residueWidget, removeTopWidget=False)

            for i, checkResidues in enumerate(foundResidues):
                for rr in range(int(self._residueWidthData.get())):
                    if rr >= 0 and rr < len(checkResidues):
                        if checkResidues[rr] is not None:
                            label = Label(self, text=checkResidues[rr].id,
                                           hAlign='c')
                            label.setMaximumHeight(30)
                            if checkResidues[rr].nmrResidue is not None:
                                label.setStyleSheet(stylesheet)
                                # self._setWidgetColour(label1)

                            self.residueWidget.layout().addWidget(label, i, rr)

            self.spacer = Spacer(self.residueWidget, 5, 5,
                                 QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
                                 grid=(i+1, rr+1), gridSpan=(1, 1))
