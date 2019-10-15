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
from functools import partial
from ccpn.core.lib.AssignmentLib import CCP_CODES
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label, ActiveLabel
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.PulldownListsForObjects import ChainPulldown
from ccpn.ui.gui.widgets.VLine import VLine
from ccpn.ui.gui.modules.SequenceModule import SequenceModule
from ccpn.core.Chain import Chain
from ccpn.ui.gui.guiSettings import getColours
from ccpn.ui.gui.guiSettings import LABEL_SELECTEDBACKGROUND, LABEL_SELECTEDFOREGROUND, LABEL_HIGHLIGHT
from ccpn.ui.gui.lib.Strip import navigateToNmrResidueInDisplay, navigateToNmrAtomsInStrip, _getCurrentZoomRatio
from ccpn.util.Logging import getLogger


logger = getLogger()
ALL = '<all>'

LINKTOPULLDOWNCLASS = 'linkToPulldownClass'


class ResidueInformation(CcpnModule):
    """
    This class implements the module for a residue table and sequence module
    """
    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'left'
    className = 'ResidueInformation'

    includeDisplaySettings = False
    includeSequentialStrips = False
    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False
    activePulldownClass = Chain

    _residueWidth = '3'

    textOptions = ['1', '3', '5', '7']
    textColumns = {'1': ([1], [0, 2]),
                   '3': ([0, 2, 4], (1, 3)),
                   '5': ([0, 1, 3, 5, 6], (2, 4)),
                   '7': ([0, 1, 2, 4, 6, 7, 8], (3, 5)),
                   }

    def __init__(self, mainWindow, name='Residue Information', chain=None, **kwds):
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

        self._moduleSettings = StripPlot(parent=self.settingsWidget, mainWindow=self.mainWindow,
                                         includeDisplaySettings=self.includeDisplaySettings,
                                         includeSequentialStrips=self.includeSequentialStrips,
                                         includePeakLists=self.includePeakLists,
                                         includeNmrChains=self.includeNmrChains,
                                         includeSpectrumTable=self.includeSpectrumTable,
                                         activePulldownClass=self.activePulldownClass,
                                         grid=(0, 0))

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

        # # insert into pulldownFrame
        # self.chainLabel = Label(self._pulldownFrame, text='Chain', grid=(0, 0))
        # # self.layout.addWidget(chainLabel, 0, 0)
        # chainPulldown = PulldownList(self._pulldownFrame, callback=self._setChain, grid=(0, 1))
        # chainPulldownData = [chain.pid for chain in self.project.chains]
        # # chainPulldownData.append(ALL)
        # chainPulldown.setData(chainPulldownData)

        self.chainPulldown = ChainPulldown(parent=self._pulldownFrame,
                                           project=self.project, default=None,  #first Chain in project (if present)
                                           grid=(0, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                           showSelectName=True,
                                           sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                           callback=self._selectionPulldownCallback
                                           )

        self.selectedChain = None  #self.project.getByPid(self.chainPulldown.currentText())
        self.residueLabel = Label(self._pulldownFrame, text='Residue', grid=(0, 3))

        self.colourScheme = self.application.colourScheme
        self.residuePulldown = PulldownList(self._pulldownFrame, callback=self._setCurrentResidue,
                                            grid=(0, 4))

        self._residueWidthLabel = Label(self._pulldownFrame, text='Residue window width', grid=(0, 5))
        self._residueWidthData = PulldownList(self._pulldownFrame, grid=(0, 6))
        self._residueWidthData.setData(texts=self.textOptions)
        self._residueWidthData.set(self._residueWidth)

        self.residuePulldown.setData(sorted(CCP_CODES))
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

        if chain is not None:
            self._selectChain(chain)

        self._getResidues()

        # set the notifies for current chain
        # TODO: put into subclass
        self._activePulldownClass = None
        self._activeCheckbox = None
        self._setCurrentPulldownNotifier = None

        if self.activePulldownClass:
            self._setCurrentPulldownNotifier = Notifier(self.current,
                                                        [Notifier.CURRENT],
                                                        targetName=self.activePulldownClass._pluralLinkName,
                                                        callback=self._selectCurrentPulldownClass)

        # put these in a smaller additional class
        if self.activePulldownClass:
            self._activePulldownClass = self.activePulldownClass
            self._activeCheckbox = getattr(self._moduleSettings, LINKTOPULLDOWNCLASS, None)

    def _selectCurrentPulldownClass(self, data):
        """Respond to change in current activePulldownClass
        """
        if self.activePulldownClass and self._activeCheckbox and self._activeCheckbox.isChecked() and self.current.chain:
            self._selectChain(self.current.chain)

    def _selectChain(self, chain=None):
        """Manually select a Chain from the pullDown
        """
        if chain is None:
            # logger.warning('select: No Chain selected')
            # raise ValueError('select: No Chain selected')
            self.chainPulldown.selectFirstItem()
        else:
            if not isinstance(chain, Chain):
                logger.warning('select: Object is not of type Chain')
                raise TypeError('select: Object is not of type Chain')
            else:
                for widgetObj in self.chainPulldown.textList:
                    if chain.pid == widgetObj:
                        self.selectedChain = chain
                        self.chainPulldown.select(self.selectedChain.pid)

    def _setResidueWidth(self, *args):
        self._residueWidth = self._residueWidthData.get()
        self._getResidues()

    def _selectionPulldownCallback(self, item):
        """Sets the selected chain to the specified value and updates the module.
        """
        if item == ALL:
            self.selectedChain = 'All'
        else:
            self.selectedChain = self.project.getByPid(item)

            if self._activePulldownClass and self._activeCheckbox and \
                    self.selectedChain != self.current.chain and self._activeCheckbox.isChecked():
                self.current.chain = self.selectedChain

        self._getResidues()

    def _setCurrentResidue(self, value: str):
        """Sets the selected residue to the specified value and updates the module.
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
        """Finds all residues of the selected type along with one flanking residue either side and displays
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
                residues = []

        self._removeWidget(self.residueWidget, removeTopWidget=False)

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

            i = rr = 0
            textCols = self.textColumns[self._residueWidth][0]
            columnCols = self.textColumns[self._residueWidth][1]

            for i, checkResidues in enumerate(foundResidues):
                for rr in range(int(self._residueWidth)):
                    if rr >= 0 and rr < len(checkResidues):
                        if checkResidues[rr] is not None:
                            item = ActiveLabel(self, text=checkResidues[rr].id,
                                               hAlign='c')
                            item.setMaximumHeight(30)
                            item.setSelectionCallback(partial(self._residueClicked, checkResidues[rr]))

                            if checkResidues[rr].nmrResidue is not None:
                                item.setStyleSheet(stylesheet)
                                item.setActionCallback(partial(self._residueDoubleClicked, checkResidues[rr]))
                                # self._setWidgetColour(label1)

                            self.residueWidget.layout().addWidget(item, i, textCols[rr])

            if i and rr:
                # put a couple of lines marking the centre section of the table
                for col in columnCols:
                    item = VLine(self.residueWidget, width=10, grid=(0, col), gridSpan=(i + 1, 1))

            self.spacer = Spacer(self.residueWidget, 5, 5,
                                 QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
                                 grid=(i + 1, textCols[-1] + 1), gridSpan=(1, 1))

    def _residueClicked(self, residue):
        """Handle cicking a residue in the table
        """
        self.current.residue = residue

    def _getDisplays(self, settings):
        """Return list of displays to navigate - if needed - need to update for all modules
        """
        displays = []
        # check for valid displays
        if settings.displaysWidget:
            gids = settings.displaysWidget.getTexts()
            if len(gids) == 0:
                return displays

            if self.includeDisplaySettings:
                if ALL in gids:
                    displays = self.application.ui.mainWindow.spectrumDisplays
                else:
                    displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
        else:
            if self.current.strip:
                displays.append(self.current.strip.spectrumDisplay)

        return displays

    def _residueDoubleClicked(self, residue):
        """Handle double-cicking a residue in the table
        """
        nmrResidue = residue.nmrResidue

        # just copied from nmrResidueTable
        from ccpn.core.lib.CallBack import CallBack

        data = CallBack(theObject=self.project,
                        object=nmrResidue,
                        targetName=nmrResidue.className,
                        trigger=CallBack.DOUBLECLICK,
                        )

        # handle a single nmrResidue - should always contain an object
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            nmrResidue = objs[0]
        else:
            nmrResidue = objs

        logger.debug('nmrResidue=%s' % str(nmrResidue.id if nmrResidue else None))

        _settings = self._moduleSettings
        displays = self._getDisplays(_settings)

        if len(displays) == 0 and self._moduleSettings.displaysWidget:
            logger.warning('Undefined display module(s); select in settings first')
            showWarning('startAssignment', 'Undefined display module(s);\nselect in settings first')
            return

        from ccpn.core.lib.ContextManagers import undoBlock

        with undoBlock():
            # optionally clear the marks
            if _settings.autoClearMarksWidget.checkBox.isChecked():
                self.application.ui.mainWindow.clearMarks()

            newWidths = []

            for specDisplay in displays:
                if self.current.strip in specDisplay.strips:

                    # just navigate to this strip
                    navigateToNmrAtomsInStrip(self.current.strip,
                                              nmrResidue.nmrAtoms,
                                              widths=newWidths,
                                              markPositions=_settings.markPositionsWidget.checkBox.isChecked(),
                                              setNmrResidueLabel=True)

                else:
                    #navigate to the specDisplay (and remove excess strips)
                    if len(specDisplay.strips) > 0:
                        newWidths = []
                        navigateToNmrResidueInDisplay(nmrResidue, specDisplay, stripIndex=0,
                                                      widths=newWidths,  #['full'] * len(display.strips[0].axisCodes),
                                                      showSequentialResidues=(len(specDisplay.axisCodes) > 2) and
                                                                             self.includeSequentialStrips and
                                                                             _settings.sequentialStripsWidget.checkBox.isChecked(),
                                                      markPositions=_settings.markPositionsWidget.checkBox.isChecked()
                                                      )

                # open the other headers to match
                for strip in specDisplay.strips:
                    if strip != self.current.strip and not strip.header.headerVisible:
                        strip.header.reset()
                        strip.header.headerVisible = True
