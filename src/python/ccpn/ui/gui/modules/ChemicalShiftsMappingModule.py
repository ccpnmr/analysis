"""
Module Documentation

  This module has three sections plus settings:
  
  ------------------------------- 
 |          |    TABLE | PLOTS   |
 | Settings |    -------------   |
 |          |      BAR CHART     |
  -------------------------------

  This module plots a bar chart of NmrResidue number as function of delta shift for its (nmrAtoms) assigned peaks.

  ** Only  NmrResidue with an integer as sequenceCode is allowed **.
    E.G.: OK  -->  sequenceCode = 44;
          NO  -->  sequenceCode = '44i-1';

  There are four modes of Deltadelta calculation (Settings): POSITIONS, HEIGHT, VOLUME, LINEWIDTHS
    The delta shift for POSITIONS and LINEWIDTHS is calculated from the peak properties as following,
    assuming the NmrAtoms of interest H and N:

      CSPi = √((Δδ_Hi )^2+α(Δδ_Ni )^2 )

    The delta shift for HEIGHT and VOLUME is calculated from the peak properties as following:
      CSPi = √((Δδ )^2

  The peaks used are as default taken from the last peak list for the selected spectra (settings tab).
  Any sensible combination of NmrAtoms is allowed.
  See tutorials for more information.
  
  Macros:
  # Example 1: On a the TStar project with all peaks correctly fitted to their spectra, this macro will show how to
              extrapolate data from the CSM module and plot different properties.
              Paste into the Macro editor Module or directly into the PythonConsole Module and run it.

    >>>
    import numpy as np
    from ccpn.util.Common import splitDataFrameWithinRange
    from ccpn.ui.gui.widgets.PlotterWidget import PlotterWidget
    from ccpn.ui.gui.modules.NmrResidueTable import KD, Deltas
    from ccpn.core.lib.DataFrameObject import  DATAFRAME_OBJECT
    
    moduleName = 'Chemical Shift Mapping:1' # The displayed CSM module name you want to get information from.
    csm = mainWindow.moduleArea.modules[moduleName]
    tableData = csm.tableData # dataframe as the displayed table. See https://pandas.pydata.org for Pandas documentation.
    deltasColumn = tableData[Deltas] # name in the table column
    deltasROI = [np.std(deltasColumn), np.max(deltasColumn)] # Deltas Region of Interest. Min the std of all deltas.
    kdsROI = [0.01, 0.2]  # Kds Region of Interest.
    inner, outer =  splitDataFrameWithinRange(tableData, Deltas, KD, *deltasROI, *kdsROI) # Split the data based on ROIs
    inner.index = [nr.sequenceCode+" "+nr.residueType for nr in inner.index] # will be used to make labels on the plot.
    widget = PlotterWidget()
    plot = widget.plotDataFrame(dataFrame=inner, kind='bar',title='KDs and Deltas') # See Pandas and Matplotlib for plots customisations.
    widget.show(windowTitle='Macro CSM', size=(500, 500))
    >>>
    
    
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-04 15:23:20 +0100 (Fri, June 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:43 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from datetime import datetime
import os
import numpy as np
import pyqtgraph as pg
import random
import pandas as pd
from functools import partial
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.BarGraph import BarGraph
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.SpectraSelectionWidget import SpectraSelectionWidget
from ccpn.ui.gui.widgets.CheckBox import CheckBox, EditableCheckBox
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.GuiTable import exportTableDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.LegendItem import LegendItem
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.PulldownListsForObjects import SpectrumGroupPulldown, SELECT
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CustomExportDialog import CustomExportDialog
from ccpn.ui.gui.lib.mouseEvents import leftMouse, controlLeftMouse
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.widgets.BarGraphWidget import BarGraphWidget
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
from ccpn.ui.gui.modules.NmrResidueTable import _CSMNmrResidueTable, KD, Deltas
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.modules.PyMolUtil import _CSMSelection2PyMolFile
from ccpn.ui.gui.lib.Strip import navigateToNmrAtomsInStrip, _getCurrentZoomRatio, navigateToNmrResidueInDisplay
from ccpn.util.Logging import getLogger
from ccpn.util.Constants import concentrationUnits
from ccpn.util.Common import splitDataFrameWithinRange, _fillListToLenght
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.peakUtils import getNmrResidueDeltas, _getKd, oneSiteBindingCurve, _fit1SiteBindCurve, _fitExpDecayCurve, \
    MODES, LINEWIDTHS, HEIGHT, POSITIONS, VOLUME, DefaultAtomWeights, H, N, OTHER, C, DISPLAYDATA, \
    getRawDataFrame, RAW, getNmrResiduePeakProperty, _getPeaksForNmrResidue
from ccpn.core.lib import CcpnSorting
from ccpn.core.lib.DataFrameObject import DATAFRAME_OBJECT
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Spectrum import Spectrum
from ccpn.core.Peak import Peak
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Project import Project
from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar
from ccpn.ui.gui.widgets.Font import Font, getFont


# Default values on init
DefaultConcentration = 0.0
DefaultThreshould = 0.1
DefaultConcentrationUnit = concentrationUnits[0]

# General Labels
DefaultSeriesUnit = ''
RelativeDisplacement = 'Relative Displacement'
PymolScriptName = 'chemicalShiftMapping_Pymol_Template.py'
DELTA = '\u0394'
Delta = '\u03B4'
MORE, LESS = 'More', 'Less'
PreferredNmrAtoms = ['H', 'HA', 'HB', 'C', 'CA', 'CB', 'N', 'NE', 'ND']
ONESITE = 'One-site binding'
DECAY = 'Exponential decay'
NIY = "This option has not been implemented yet"
DropHereLabel = 'Drop SpectrumGroup here to start'
NewSG = '<New SpectrumGroup>'
RelativeContribuitions = 'RelativeContribuitions'
SelectedNmrAtomNames = 'SelectedNmrAtomNames'

FittingAvailable = [ONESITE, DECAY]

# colours
BackgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
OriginAxes = pg.functions.mkPen(hexToRgb(getColours()[GUISTRIP_PIVOT]), width=1, style=QtCore.Qt.DashLine)
FittingLine = pg.functions.mkPen(hexToRgb(getColours()[DIVIDER]), width=0.5, style=QtCore.Qt.DashLine)
SelectedPoint = pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
SelectedLabel = pg.functions.mkBrush(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
c = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
GridPen = pg.functions.mkPen(c, width=1, style=QtCore.Qt.SolidLine)
# GridFont = Font('Helvetica', 16, bold=True)
GridFont = getFont()

DEFAULTSPACING = (5, 5)
TABMARGINS = (1, 10, 10, 1)  # l, t, r, b
ZEROMARGINS = (0, 0, 0, 0)  # l, t, r, b


class ChemicalShiftsMapping(CcpnModule):
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'
    className = 'ChemicalShiftsMapping'

    ######################################################################################################################
    ######################################          Public Functions        ##############################################
    ######################################################################################################################
    ## These functions help users to get raw data displayed in the module widgets

    @property
    def tableData(self):
        """
        :return: dataFrame containing all data on the Chemical Shift Mapping Module table

                         |     Columns    | "as the displayed table"
        | index          |    #   | Index | Pid, _object, Sequence, Deltas, Kd ...
        |----------------+--------|-------|
        | 1              |    1   |   1   |
        | 2              |    2   |   2   |

        """
        if self.nmrResidueTable._dataFrameObject:
            df = self.nmrResidueTable._dataFrameObject.dataFrame
            df.index = df[DATAFRAME_OBJECT]
            return df

        else:
            getLogger().warning("Error getting Chemical Shift Mapping data. DataFrame on NmrResidueTable not defined")

    def getBindingCurves(self, nmrResidues):
        """ Gets binding curve as dataFrame for specific NmrResidues.
          Returns a DataFrame as: Index -> nmrResidue Object, columns: int or float, raw values: int or float

                           |     Columns    |as the concentration/time/etc value
          | index          |    1   |   2   |
          |----------------+--------|-------|
          | nmrResidue1    |    1.0 |   1.1 |
          | nmrResidue2    |    2.0 |   1.2 |

         """
        return self._getBindingCurves(nmrResidues)

    ########### GUI Public Functions ############

    def refresh(self):
        """ Updates all widgets and data in the CSM module"""
        self._updateModule()

    def close(self):
        """ Closes the CSM module """
        self._closeModule()

    @property
    def thresholdValue(self):
        """ Gets the threshold value currently displayed on the graph   """
        return self.thresholdSpinBox.value()

    def setThresholdValue(self, value):
        """Sets the Threshold Line to a new value and updates the graph """
        self.thresholdSpinBox.set(value)

    ######################################################################################################################
    ######################################          Private Functions        #############################################
    ######################################################################################################################

    def __init__(self, mainWindow, name='Chemical Shift Mapping', nmrChain=None, **kwds):
        super().__init__(mainWindow=mainWindow, name=name, settingButton=True)

        BarGraph.mouseClickEvent = self._barGraphClickEvent
        BarGraph.mouseDoubleClickEvent = self._navigateToNmrItems

        self.mainWindow = mainWindow
        self.relativeContribuitions = DefaultAtomWeights  # used in other classes (set in popup)
        self.selectedNmrAtomNames = []  # used in other classes  (set in popup)
        self._selectedSpectrumGroup = None
        self.project = self.mainWindow.project
        self.application = self.mainWindow.application
        self.current = self.application.current

        self.thresholdLinePos = DefaultThreshould
        self._bindingExportDialog = None
        self._fittingMode = None

        self.showStructureIcon = Icon('icons/showStructure')
        self.updateIcon = Icon('icons/update')
        self._zoomOnInit = True
        self._bindingItemClicked = None  #used for the bindingPlot callback
        self._seriesUnit = DefaultSeriesUnit
        self._availableFittingPlots = {
            ONESITE: self._plot1SiteBindFitting,  # Only this implemented
            DECAY  : self._plotExponentialDecay,
            }

        self._initMainWidgets()
        self._initSettingsWidgets()
        self._selectCurrentNRNotifier = Notifier(self.current, [Notifier.CURRENT], targetName='nmrResidues',
                                                 callback=self._selectCurrentNmrResiduesNotifierCallback, onceOnly=True)
        self._peakDeletedNotifier = Notifier(self.project, [Notifier.DELETE], 'Peak', self._peakDeletedCallBack)
        self._nrChangedNotifier = Notifier(self.project, [Notifier.CHANGE], 'NmrResidue', self._nmrObjectChanged)
        self._nrDeletedNotifier = Notifier(self.project, [Notifier.DELETE], 'NmrResidue', self._nmrResidueDeleted)
        self._sgNotifier = Notifier(self.project, [Notifier.CREATE], 'SpectrumGroup', self._onSGcreation)
        self._sgDeleteNotifier = Notifier(self.project, [Notifier.DELETE], 'SpectrumGroup', self._onSGdeletion)

        # self._addSettingsWAttr(self.nmrAtomsCheckBoxes)
        # self._selectCurrentNmrResiduesNotifierCallback()

        if self.project:
            if len(self.project.nmrChains) > 0:
                if self.nmrResidueTable.ncWidget.getIndex() == 0:
                    self.nmrResidueTable.ncWidget.select(self.project.nmrChains[-1].pid)
                    if len(self.project.spectrumGroups) > 0:
                        self.spectrumGroupPulldown.select(self.project.spectrumGroups[-1])
                        self._setThresholdLineBySTD()
                        if len(self.selectedNmrAtomNames) == 0:
                            sg = self.spectrumGroupPulldown.getObject()
                            self._selectedSpectrumGroup = sg
                            if isinstance(sg, SpectrumGroup):
                                if len(sg.spectra) > 0:
                                    self.selectedNmrAtomNames = sg.spectra[0].axisCodes
                                    self._updateModule()

    #####################################################
    #############   Main widgets creation    ############
    #####################################################

    def _initMainWidgets(self):
        """ All the main widgets are created in this function
        Current Splitters Layout:

        # TABLE | PLOTS  # vertical   splitter
        # -------------  # horizontal splitter
        #     BARS

        Splitters are nested. Children Widgets don't follow the normal base grid rule: grid = (0,0).
        Plots are inside a Tab Widget

        """

        self.hPlotsTableSplitter = Splitter()  # Horizontal
        self.vBarTableSplitter = Splitter(horizontal=False)  # Vertical

        self.barGraphWidget = BarGraphWidget(self.mainWidget, application=self.application, backgroundColour=BackgroundColour)
        self._setBarGraphWidget()

        self.nmrResidueTable = _CSMNmrResidueTable(parent=self.mainWidget, mainWindow=self.mainWindow,
                                                   # selectionCallback=self._nmrTableSelectionCallback,
                                                   actionCallback=self._customActionCallBack,
                                                   checkBoxCallback=self._checkBoxCallback,
                                                   setLayout=True, grid=(0, 0))
        self.nmrResidueTable.chemicalShiftsMappingModule = self
        self.nmrResidueTable.displayTableForNmrChain = self._displayTableForNmrChain
        self.tabWidget = Tabs(self.mainWidget, setLayout=True)

        ## 1 Tab binding Plot
        self.bindingPlotFrame = Frame(self.mainWidget, setLayout=True)
        # self.bindingPlotFrame.setContentsMargins(1, 10, 1, 10)
        self._setBindingPlot(layoutParent=self.bindingPlotFrame)
        self.tabWidget.addTab(self.bindingPlotFrame, 'Binding Curve')

        ## 2 Tab fitting
        self.fittingFrame = Frame(self.mainWidget, setLayout=True)
        self._setFittingPlot(layoutParent=self.fittingFrame)
        self.tabWidget.addTab(self.fittingFrame, 'Fitting')

        ## 3 Tab scatter Kd-deltas
        self.scatterFrame = Frame(self.mainWidget, setLayout=True)
        self.scatterFrame.setContentsMargins(1, 10, 1, 10)
        self._setScatterTabWidgets(layoutParent=self.scatterFrame)
        self.tabWidget.addTab(self.scatterFrame, 'Scatter')

        ## These buttons have to be inside the Table layout. Ugly solution but the only way to get them aligned to the rest.
        self.showOnViewerButton = Button(self.nmrResidueTable._widget, tipText='Show on Molecular Viewer',
                                         icon=self.showStructureIcon, callback=self._showOnMolecularViewer,
                                         grid=(1, 1), hAlign='l')
        self.showOnViewerButton.setFixedHeight(25)
        self.updateButton1 = Button(self.nmrResidueTable._widget, text='', icon=self.updateIcon, tipText='Update all',
                                    callback=self._updateModule, grid=(1, 2), hAlign='r')
        self.updateButton1.setFixedHeight(25)

        self.hPlotsTableSplitter.addWidget(self.nmrResidueTable)
        self.hPlotsTableSplitter.addWidget(self.tabWidget)
        self.hPlotsTableSplitter.setStretchFactor(0, 1)
        self.vBarTableSplitter.addWidget(self.hPlotsTableSplitter)  # Foundamental! The horizontal splitter MUST be added
        # to the vertical as a widget before adding any other widgets to it ( to the vertical).
        # Then, only the vertical splitter is added to the main widget Layout.
        # Nested and nasty Qt.
        self.vBarTableSplitter.addWidget(self.barGraphWidget)
        self.vBarTableSplitter.setStretchFactor(0, 1)
        self.mainWidget.getLayout().addWidget(self.vBarTableSplitter)
        # self.mainWidget.setContentsMargins(5, 5, 5, 5)  # l,t,r,b

    #####################################################
    ##########   Settings widgets creation  #############
    #####################################################

    def _initSettingsWidgets(self):

        self.scrollAreaWidgetContents = self.settingsWidget

        i = 0
        self.inputLabel = Label(self.scrollAreaWidgetContents, text='Select Spectrum Group', grid=(i, 0), vAlign='t')
        self.spectrumGroupPulldown = PulldownList(self.scrollAreaWidgetContents, callback=self._sgPulldownCallback,
                                                  grid=(i, 1))
        self._setSpectrumGroupPulldown()
        i += 1
        self.editSGLabel = Label(self.scrollAreaWidgetContents, text='Edit SpectrumGroup ', grid=(i, 0))
        self.editSGButton = Button(self.scrollAreaWidgetContents, text='Edit series...', callback=self._editSpectrumGroup,
                                   grid=(i, 1))
        i += 1
        self.modeLabel = Label(self.scrollAreaWidgetContents, text='Calculation mode ', grid=(i, 0))
        self.modeButtons = RadioButtons(self.scrollAreaWidgetContents, selectedInd=0, texts=MODES,
                                        callback=self._toggleRawDataOption, grid=(i, 1))
        i += 1
        self.displayDataLabel = Label(self.scrollAreaWidgetContents, text='Display data ', grid=(i, 0))
        self.displayDataButton = RadioButtons(self.scrollAreaWidgetContents, selectedInd=0, texts=DISPLAYDATA,
                                              grid=(i, 1), hAlign='l')
        self.displayDataButton.hide()
        self.displayDataLabel.hide()
        i += 1
        self.atomsLabel = Label(self.scrollAreaWidgetContents, text='Select NmrAtoms', grid=(i, 0))
        self.showNmrAtoms = Button(self.scrollAreaWidgetContents, text='NmrAtoms settings',
                                   callback=self.showNmrAtomsSettings, grid=(i, 1))
        i += 1
        self.thresholdLAbel = Label(self.scrollAreaWidgetContents, text='Threshold value', grid=(i, 0))
        self.thresholdFrame = Frame(self.scrollAreaWidgetContents, setLayout=True, grid=(i, 1))

        self.thresholdSpinBox = DoubleSpinbox(self.thresholdFrame, value=DefaultThreshould, step=0.01,
                                              decimals=3, callback=self._updateThresholdLineValue,
                                              tipText='Threshold value for deltas',
                                              grid=(0, 0))
        self.thresholdButton = Button(self.thresholdFrame, text='Default', callback=self._setDefaultThreshold,
                                      tipText='Default: STD of deltas',
                                      grid=(0, 1))
        self.thresholdButton.setMaximumWidth(50)
        v = self.thresholdSpinBox.get()
        self.barGraphWidget.xLine.setPos(v)

        i += 1
        self.scaleBindingC = Label(self.scrollAreaWidgetContents, text='Scale binding curves', grid=(i, 0))
        self.scaleBindingCCb = CheckBox(self.scrollAreaWidgetContents, checked=True,
                                        callback=self._plotBindingCFromCurrent, grid=(i, 1))
        i += 1
        self.fittingModeL = Label(self.scrollAreaWidgetContents, text='Fitting mode', grid=(i, 0))
        self.fittingModeRB = RadioButtons(self.scrollAreaWidgetContents, texts=FittingAvailable, grid=(i, 1))
        #
        # i += 1 ####  # Text editor to allow user curve fitting. N.B. Not implemented yet the mechanism to do this
        # self.fittingModeTextL = Label(self.scrollAreaWidgetContents, text='', grid=(i, 0))
        # self.fittingModeEditor = TextEditor(self.scrollAreaWidgetContents,    grid=(i, 1))
        # self.fittingModeEditor.hide()

        i += 1
        self.aboveThresholdColourLabel = Label(self.scrollAreaWidgetContents, text='Above threshold colour', grid=(i, 0))
        self.aboveThresholdColourBox = PulldownList(self.scrollAreaWidgetContents, grid=(i, 1))
        for item in spectrumColours.items():
            pix = QtGui.QPixmap(QtCore.QSize(20, 20))
            pix.fill(QtGui.QColor(item[0]))
            self.aboveThresholdColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
        try:
            self.aboveThresholdColourBox.select('lime')
        except:
            self.aboveThresholdColourBox.select(random.choice(self.aboveThresholdColourBox.texts))

        i += 1
        self.belowThresholdColourLabel = Label(self.scrollAreaWidgetContents, text='Below threshold colour', grid=(i, 0))
        self.belowThresholdColourBox = PulldownList(self.scrollAreaWidgetContents, grid=(i, 1))

        for item in spectrumColours.items():
            pix = QtGui.QPixmap(QtCore.QSize(20, 20))
            pix.fill(QtGui.QColor(item[0]))
            self.belowThresholdColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
        try:
            self.belowThresholdColourBox.select('red')
        except:
            self.belowThresholdColourBox.select(random.choice(self.belowThresholdColourBox.texts))

        i += 1
        disappearedTipText = 'Mark NmrResidue bar with selected colour where assigned peaks have disapperead from the spectra'
        self.disappearedColourLabel = Label(self.scrollAreaWidgetContents, text='Disappeared peaks colour', grid=(i, 0))
        self.disappearedColourBox = PulldownList(self.scrollAreaWidgetContents, grid=(i, 1))
        for item in spectrumColours.items():
            pix = QtGui.QPixmap(QtCore.QSize(20, 20))
            pix.fill(QtGui.QColor(item[0]))
            self.disappearedColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
        try:
            self.disappearedColourBox.select('cyan')
        except:
            self.disappearedColourBox.select(random.choice(self.disappearedColourBox.texts))

        i += 1
        self.disappearedBarThreshold = Label(self.scrollAreaWidgetContents, text='Disappeared value', grid=(i, 0))
        self.disappearedBarThresholdSpinBox = DoubleSpinbox(self.scrollAreaWidgetContents, value=1, step=0.01,
                                                            decimals=3, callback=None, grid=(i, 1))
        i += 1
        # molecular Structure
        self.molecularStructure = Label(self.scrollAreaWidgetContents, text='Molecular structure', grid=(i, 0))
        texts = ['PDB', 'CCPN Ensembles', 'Fetch From Server']
        self.molecularStructureRadioButton = RadioButtons(self.scrollAreaWidgetContents, texts=texts, direction='h',
                                                          grid=(i, 1))
        self.molecularStructureRadioButton.set(texts[0])
        self.molecularStructureRadioButton.setEnabled(False)
        self.molecularStructureRadioButton.setToolTip('Not implemented yet')
        i += 1
        self.mvWidgetContents = Frame(self.scrollAreaWidgetContents, setLayout=True, grid=(i, 1))
        self.pdbLabel = Label(self.mvWidgetContents, text='PDB File Path', grid=(0, 0))
        scriptPath = None
        if self.mainWindow:
            # scriptPath = os.path.join(getScriptsDirectoryPath(self.project),'pymol')
            scriptPath = self.application.pymolScriptsPath
        self.pathPDB = LineEditButtonDialog(self.mvWidgetContents, textDialog='Select PDB File',
                                            fileFilter="PDB files (*.pdb)", directory=scriptPath, grid=(0, 1))
        i += 1
        self.updateButton = Button(self.scrollAreaWidgetContents, text='Update All', callback=self._updateModule,
                                   grid=(i, 1))

        i += 1
        self._spacer = Spacer(self.scrollAreaWidgetContents, 5, 5,
                              QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding, grid=(i, 3))

    #####################################################
    #################   Bar Graph        ################
    #####################################################

    def _setBarGraphWidget(self):
        ### barGraph Widget Plot setup
        self.barGraphWidget.setViewBoxLimits(0, None, 0, None)
        self.barGraphWidget.xLine.setPos(DefaultThreshould)
        self.barGraphWidget.xLine.sigPositionChangeFinished.connect(self._threshouldLineMoved)
        self.barGraphWidget.customViewBox.mouseClickEvent = self._viewboxMouseClickEvent
        self.barGraphWidget.customViewBox.selectAboveThreshold = self._selectNmrResiduesAboveThreshold
        self.barGraphWidget.plotWidget.plotItem.getAxis('bottom').setPen(GridPen)
        self.barGraphWidget.plotWidget.plotItem.getAxis('left').setPen(GridPen)
        self.barGraphWidget.plotWidget.plotItem.getAxis('bottom').tickFont = GridFont
        self.barGraphWidget.plotWidget.plotItem.getAxis('left').tickFont = GridFont

    def _viewboxMouseClickEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            event.accept()
            self.barGraphWidget.customViewBox._raiseContextMenu(event)
            self.barGraphWidget.customViewBox._resetBoxes()

        elif event.button() == QtCore.Qt.LeftButton:
            self.barGraphWidget.customViewBox._resetBoxes()
            self.application.current.clearNmrResidues()
            event.accept()

    def _selectBarLabels(self, values):
        for bar in self.barGraphWidget.barGraphs:
            for label in bar.labels:
                if label.text() in values:
                    label.setSelected(True)
                    label.setBrush(SelectedLabel)
                    label.setVisible(True)
                else:
                    label.setSelected(False)
                    label.setBrush(QtGui.QColor(bar.brush))
                    if label.isBelowThreshold and not self.barGraphWidget.customViewBox.allLabelsShown:
                        label.setVisible(False)

    def _barGraphClickEvent(self, event):

        position = int(event.pos().x())
        df = self.tableData
        if df is not None:
            objDf = df.loc[df['Sequence'] == str(position)]

            if len(objDf.index) > 0:
                obj = objDf.index[0]
                selected = set(self.current.nmrResidues)
                if leftMouse(event):
                    self.current.nmrResidue = obj
                    event.accept()

                elif controlLeftMouse(event):
                    # Control-left-click;  add to selection
                    selected.add(obj)
                    self.current.nmrResidues = selected
                    event.accept()
                else:
                    event.ignore()

    #####################################################
    #################   NMR Table         ################
    #####################################################

    def _customActionCallBack(self, data):
        # nmrResidue = data[Notifier.OBJECT]
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            nmrResidue = objs[0]
        else:
            nmrResidue = objs

        if nmrResidue:

            xPos = int(nmrResidue.sequenceCode)
            yPos = nmrResidue._delta
            if xPos and yPos:
                xr, yr = _getCurrentZoomRatio(self.barGraphWidget.customViewBox.viewRange())
                self.barGraphWidget.customViewBox.setRange(xRange=[xPos - (xr / 2), xPos + (xr / 2)], yRange=[0, yPos + (yr / 2)], )
        self._navigateToNmrItems()

    #####################################################
    #################   Binding Plot     ################
    #####################################################

    def _setBindingPlot(self, layoutParent):
        ###  Plot setup
        self._bindingPlotView = pg.GraphicsLayoutWidget()
        self._bindingPlotView.setBackground(BackgroundColour)
        self.bindingPlot = self._bindingPlotView.addPlot()
        self.bindingPlot.mouseDoubleClickEvent = self._bindingPlotDoubleClick

        self.bindingPlot.addLegend(offset=[1, 10])
        self._bindingPlotViewbox = self.bindingPlot.vb
        self._bindingPlotViewbox.mouseClickEvent = self._bindingViewboxMouseClickEvent
        self.bindingVLine = pg.InfiniteLine(angle=90, pos=0, pen=OriginAxes, movable=False, )
        self.bindingHLine = pg.InfiniteLine(angle=0, pos=0, pen=OriginAxes, movable=False, )
        self.bindingPlot.setLabel('bottom', self._seriesUnit)
        self.bindingPlot.setLabel('left', DELTA + Delta)
        self.bindingPlot.setMenuEnabled(False)
        self.bindingPlot.getAxis('bottom').setPen(GridPen)
        self.bindingPlot.getAxis('left').setPen(GridPen)
        self.bindingPlot.getAxis('bottom').tickFont = GridFont
        self.bindingPlot.getAxis('left').tickFont = GridFont
        self._bindingPlotViewbox.addItem(self.bindingVLine)
        self._bindingPlotViewbox.addItem(self.bindingHLine)
        layoutParent.getLayout().addWidget(self._bindingPlotView)

    def _clearBindingPlot(self):
        self.bindingPlot.clear()
        # self._clearLegendBindingC()
        self.bindingLine.hide()

    def _showExportDialog(self, viewBox):
        """
        :param viewBox: the viewBox obj for the selected plot
        :return:
        """
        if self._bindingExportDialog is None:
            self._bindingExportDialog = CustomExportDialog(viewBox.scene(), titleName='Exporting')
        self._bindingExportDialog.show(viewBox)

    def _raiseBindingCPlotContextMenu(self, ev):
        """ Creates all the menu items for the scatter context menu. """
        self._bindingContextMenu = Menu('', None, isFloatWidget=True)
        self._bindingContextMenu.addAction('Reset View', self.bindingPlot.autoRange)
        self._bindingContextMenu.addAction('Legend', self._togleBindingCLegend)
        self._bindingContextMenu.addSeparator()

        self._bindingContextMenu.addSeparator()
        self.exportAction = QtGui.QAction("Export...", self,
                                          triggered=partial(self._showExportDialog, self._bindingPlotViewbox))
        self.exporAllAction = QtGui.QAction("Export All...", self, triggered=partial(exportTableDialog,
                                                                                     self._getAllBindingCurvesDataFrameForChain()))
        self._bindingContextMenu.addAction(self.exportAction)
        self._bindingContextMenu.addAction(self.exporAllAction)
        self._bindingContextMenu.exec_(ev.screenPos().toPoint())

    def _togleBindingCLegend(self):
        if self.bindingPlot.legend.isVisible():
            self.bindingPlot.legend.hide()
        else:
            self.bindingPlot.legend.show()

    def _bindingViewboxMouseClickEvent(self, event):
        """ click on scatter viewBox. The parent of scatterPlot. Opens the context menu at any point. """
        if event.button() == QtCore.Qt.RightButton:
            event.accept()
            self._raiseBindingCPlotContextMenu(event)

    def _plotBindingCFromCurrent(self):
        # check current nmrResidues are present in the selected nmrChain. Otherwise keep the displayed plot
        isOk = False
        nc = self.project.getByPid(self.nmrResidueTable.ncWidget.getText())
        if nc:
            nrs = [nr for nr in self.current.nmrResidues if nr in nc.nmrResidues]
            if len(nrs) == len(self.current.nmrResidues):
                isOk = True
        if isOk:
            self.bindingPlot.clear()
            self._clearLegend(self.bindingPlot.legend)
            # self.bindingPlot.setLimits(xMin=0, xMax=None, yMin=0, yMax=None)

            if self.current.nmrResidues is not None:
                plotData, peaksDF = self._getBindingCurves(self.current.nmrResidues)
                if self.scaleBindingCCb.isChecked():
                    plotData = self._getScaledBindingCurves(plotData)

                if plotData is not None:
                    plotData = plotData.replace(np.nan, 0)
                    for obj, row, in plotData.iterrows():
                        ys = list(row.values)
                        xs = list(plotData.columns)
                        pksPids = list(peaksDF.loc[obj].values)
                        points = []
                        pairs = list([i, j] for i, j in zip(xs, ys))
                        for pair, peakPid in zip(pairs, pksPids):
                            peak = self.project.getByPid(peakPid)

                            if isinstance(peak, Peak):
                                spectrum = peak.peakList.spectrum
                                dd = {'pos': [0, 0], 'data': 'obj', 'brush': pg.mkBrush(255, 0, 0), 'symbol': 'o', 'size': 10,
                                      'pen': None}  # red default
                                dd['pos'] = pair
                                dd['data'] = peak
                                if hasattr(spectrum, 'positiveContourColour'):  # colour from the spectrum. The only CCPN obj implemeted so far
                                    brush = pg.functions.mkBrush(hexToRgb(spectrum.positiveContourColour), width=10)
                                    dd['brush'] = brush
                                points.append(dd)

                        if obj._colour:
                            pen = pg.functions.mkPen(hexToRgb(obj._colour), width=5)
                            brush = pg.functions.mkBrush(hexToRgb(obj._colour), width=1)
                            plot = self.bindingPlot.plot(xs, ys, pen=pen, symbolBrush=brush, symbol='o', symbolSize=1,
                                                         name=obj.pid)  # name used for legend and retireve the obj

                            plot.scatter.addPoints(points)
                        else:
                            plot = self.bindingPlot.plot(xs, ys, symbol='o', name=obj.pid)
                        plot.sigPointsClicked.connect(self._bindingPlotSingleClick)
                        self.bindingPlot.autoRange()
                        self.bindingPlot.setLabel('left', 'Y')  # DELTA+Delta)
                        self.bindingPlot.setLabel('bottom', self._seriesUnit)

    def _bindingPlotSingleClick(self, item, points):
        """sig callback from the binding plot. Gets the obj from the curve name."""
        obj = self.project.getByPid(item.name())

        for p in points:
            if isinstance(p.data(), (Spectrum, Peak)):
                self._bindingItemClicked = p.data()

    def _bindingPlotDoubleClick(self, event):
        if self._bindingItemClicked is not None:
            if isinstance(self._bindingItemClicked, Peak):
                self._navigateToPeakPosition(self._bindingItemClicked)
            if isinstance(self._bindingItemClicked, NmrResidue):
                self._navigateToNmrItems(self._bindingItemClicked)

    def _getBindingCurves(self, nmrResidues, singleColumn=False):
        """
        :param nmrResidues:
        :return: dataframe
        """
        mode = self.modeButtons.getSelectedText()
        if not mode in MODES:
            return
        weights = self.relativeContribuitions
        selectedAtomNames = self.selectedNmrAtomNames
        values = []
        peaksDFs = []
        sg = self._selectedSpectrumGroup
        if isinstance(sg, SpectrumGroup):
            spectra = sg.spectra
            for nmrResidue in nmrResidues:
                if self._isInt(nmrResidue.sequenceCode):
                    peaksPids = []
                    if len(spectra) > 1:
                        if self.displayDataButton.get() == RAW and mode in [HEIGHT, VOLUME]:
                            deltas, peaks = getNmrResiduePeakProperty(nmrResidue, selectedAtomNames, spectra, mode)
                            for i, p in enumerate(peaks):
                                peaksPids.append(p.pid)

                        else:
                            zeroSpectrum, otherSpectra = spectra[0], spectra[1:]
                            deltas = []
                            peaks = _getPeaksForNmrResidue(nmrResidue, selectedAtomNames, spectra)
                            # deltas.append(0)
                            for i, spectrum in enumerate(spectra):
                                if nmrResidue._includeInDeltaShift:
                                    delta = getNmrResidueDeltas(nmrResidue, selectedAtomNames, mode=mode, spectra=[zeroSpectrum, spectrum],
                                                                atomWeights=weights)
                                    deltas.append(delta)
                                else:
                                    deltas.append(None)
                            if len(spectra) != len(peaks):
                                continue
                            else:
                                for i, p in enumerate(peaks):
                                    peaksPids.append(p.pid)
                        if not None in sg.series:
                            concentrationsValues = sg.series
                            self._seriesUnit = sg.seriesUnits
                        else:
                            concentrationsValues = [i for i in range(len(spectra))]
                        if len(deltas) < len(concentrationsValues):
                            deltas = _fillListToLenght(deltas, len(concentrationsValues), np.nan)
                        df = pd.DataFrame([deltas], index=[nmrResidue], columns=concentrationsValues)
                        if len(peaksPids) < len(concentrationsValues):
                            peaksPids = _fillListToLenght(peaksPids, len(concentrationsValues), '')
                        dfPeaks = pd.DataFrame([peaksPids], index=[nmrResidue], columns=concentrationsValues)
                        df = df.replace(np.nan, 0)
                        values.append(df)
                        peaksDFs.append(dfPeaks)
        if len(values) > 0:
            df = pd.concat(values)
            dfPeaks = pd.concat(peaksDFs)
            return df, dfPeaks
        return pd.DataFrame(), pd.DataFrame()

    def _getScaledBindingCurves(self, bindingCurves):
        if isinstance(bindingCurves, pd.DataFrame):
            aMean = bindingCurves.mean(axis=1)  # mean of each row
            scaled = bindingCurves.div(aMean, axis=0)  # divide each row by its mean
            return scaled

    #####################################################
    #################   Fitting Plot     ################
    #####################################################

    def _setFittingPlot(self, layoutParent):
        ###  Plot setup
        self._fittingPlotView = pg.GraphicsLayoutWidget()
        self._fittingPlotView.setBackground(BackgroundColour)
        self.fittingPlot = self._fittingPlotView.addPlot()
        self.fittingPlot.addLegend(offset=[1, 10])
        self._fittingPlotViewbox = self.fittingPlot.vb
        # self._fittingPlotViewbox.mouseClickEvent = self._fittingViewboxMouseClickEvent
        self.fittingPlot.setLabel('left', RelativeDisplacement)
        self.fittingPlot.setMenuEnabled(False)
        self.fittingLine = pg.InfiniteLine(angle=90, pen=FittingLine, movable=False, label=' ')  # label needs to be defined here.
        self.atHalfFitLine = pg.InfiniteLine(angle=0, pos=0.5, pen=FittingLine, movable=False, label=' ')  # label needs to be defined here.

        self._fittingPlotViewbox.addItem(self.fittingLine)
        self._fittingPlotViewbox.addItem(self.atHalfFitLine)

        self.fittingPlot.setLimits(xMin=0, xMax=None, yMin=0, yMax=1)
        self.fittingPlot.getAxis('bottom').setPen(GridPen)
        self.fittingPlot.getAxis('left').setPen(GridPen)
        self.fittingPlot.getAxis('bottom').tickFont = GridFont
        self.fittingPlot.getAxis('left').tickFont = GridFont

        layoutParent.getLayout().addWidget(self._fittingPlotView)

    #####################################################
    #################   Scatter Plot     ################
    #####################################################

    def _setScatterTabWidgets(self, layoutParent):
        ### Scatter Plot setup
        self._scatterView = pg.GraphicsLayoutWidget()
        self._scatterView.setBackground(BackgroundColour)
        self._plotItem = self._scatterView.addPlot()
        self._scatterViewbox = self._plotItem.vb
        self._addScatterSelectionBox()
        self._plotItem.setMenuEnabled(False)
        self._scatterViewbox.mouseDragEvent = self._scatterMouseDragEvent
        self.scatterPlot = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0))
        self.scatterPlot.mouseClickEvent = self._scatterMouseClickEvent
        self.scatterPlot.mouseDoubleClickEvent = self._navigateToNmrItems
        # self._scatterViewbox.mouseClickEvent = self._scatterViewboxMouseClickEvent #use this for right click Context menu
        # self._scatterViewbox.scene().sigMouseMoved.connect(self.mouseMoved) #use this if you need the mouse Posit
        self.scatterXLine = pg.InfiniteLine(angle=90, pos=0, pen=OriginAxes)
        self.scatterYLine = pg.InfiniteLine(angle=0, pos=0, pen=OriginAxes)

        self._plotItem.addItem(self.scatterPlot)
        self._plotItem.addItem(self.scatterXLine)
        self._plotItem.addItem(self.scatterYLine)
        layoutParent.getLayout().addWidget(self._scatterView)

    ########### Selection box for scatter Plot ############

    def _addScatterSelectionBox(self):
        """ Create the red box for selection on the scatter plot """
        self._scatterSelectionBox = QtWidgets.QGraphicsRectItem(0, 0, 1, 1)
        self._scatterSelectionBox.setPen(pg.functions.mkPen((255, 0, 255), width=1))
        self._scatterSelectionBox.setBrush(pg.functions.mkBrush(255, 100, 255, 100))
        self._scatterSelectionBox.setZValue(1e9)
        self._scatterViewbox.addItem(self._scatterSelectionBox, ignoreBounds=True)
        self._scatterSelectionBox.hide()

    def _updateScatterSelectionBox(self, p1: float, p2: float):
        """
        Updates drawing of selection box as mouse is moved.
        """
        vb = self._scatterViewbox
        r = QtCore.QRectF(p1, p2)
        r = vb.childGroup.mapRectFromParent(r)
        self._scatterSelectionBox.setPos(r.topLeft())
        self._scatterSelectionBox.resetTransform()
        self._scatterSelectionBox.scale(r.width(), r.height())
        self._scatterSelectionBox.show()
        minX = r.topLeft().x()
        minY = r.topLeft().y()
        maxX = minX + r.width()
        maxY = minY + r.height()
        return [minX, maxX, minY, maxY]

    def _resetSelectionBox(self):
        "Reset/Hide the boxes "
        self._successiveClicks = None
        self._scatterSelectionBox.hide()
        self._scatterViewbox.rbScaleBox.hide()

    def _scatterMouseClickEvent(self, ev):
        """
          Re-implementation of scatter mouse event to allow selections of a single point
        """
        plot = self.scatterPlot
        pts = plot.pointsAt(ev.pos())
        obj = None
        if len(pts) > 0:
            point = pts[0]
            obj = point.data()

        if leftMouse(ev):
            if obj:
                self._selectedObjs = [obj]
                if self.current:
                    self.current.nmrResidues = self._selectedObjs
                ev.accept()
            else:
                # "no spots, clear selection"
                self._selectedObjs = []
                if self.current:
                    self.current.nmrResidues = self._selectedObjs
                ev.accept()

        elif controlLeftMouse(ev):
            # Control-left-click;  add to selection
            self._selectedObjs.extend([obj])
            if self.current:
                self.current.nmrResidues = self._selectedObjs
            ev.accept()

        else:
            ev.ignore()

    def _scatterMouseDragEvent(self, event, *args):
        """
        Re-implementation of PyQtGraph mouse drag event to allow custom actions off of different mouse
        drag events. Same as spectrum Display. Check Spectrum Display View Box for more documentation.
        Known bug: left drag on the axis, raises a pyqtgraph exception
        """
        if leftMouse(event):
            pg.ViewBox.mouseDragEvent(self._scatterViewbox, event)

        elif controlLeftMouse(event):

            self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())
            event.accept()
            if not event.isFinish():
                self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())
            else:  ## the event is finished.
                pts = self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())

                i, o = splitDataFrameWithinRange(self._getScatterData(),
                                                 Deltas, KD, *pts)
                # self._selectedObjs.extend(i.index)
                self.current.nmrResidues = i.index
                self._resetSelectionBox()
        else:
            self._resetSelectionBox()
            event.ignore()

    def _getScatterData(self):
        if self.tableData is not None:
            df = self.tableData[[Deltas, KD]]
            df.index = self.tableData[DATAFRAME_OBJECT]
            return df

    def _plotScatters(self, dataFrame, selectedObjs=None, *args):
        """

        :param dataFrame: in the format from the PCA Class
              index: Pid --> obj
              Columns: Deltas Kds,  values: floats
        :return:  transform the dataFrame in the (pyqtGraph) plottable data format and plot it on the scatterPlot

        """
        if selectedObjs is None:
            selectedObjs = self._selectedObjs

        if dataFrame is None:
            self.scatterPlot.clear()
            return
        spots = []
        for obj, row in dataFrame.iterrows():
            dd = {'pos': [0, 0], 'data': 'obj', 'brush': pg.mkBrush(255, 0, 0), 'symbol': 'o', 'size': 10, 'pen': None}  #red default
            dd['pos'] = [row[Deltas], row[KD]]  # from table columns
            dd['data'] = obj
            if obj._colour:
                dd['brush'] = pg.functions.mkBrush(hexToRgb(obj._colour))
            if obj in selectedObjs:
                dd['pen'] = SelectedPoint
            spots.append(dd)
        self._plotSpots(spots)
        self._plotItem.setLabel('bottom', DELTA + Delta)
        self._plotItem.setLabel('left', KD)

    def _plotSpots(self, spots):
        """
        plots the data in the format requested by the pg.ScatterPlot widget
        :param spots: a list of dict with these Key:value
                    [{
                    'pos': [0, 0], # [x,y] which will be the single spot position
                    'data': 'pid', any python object. pid for NMR residue
                    'brush': pg.mkBrush(255, 255, 255, 120), the colour of the spot
                    'symbol': 'o', will give the shape of the spot
                    'size': 10,
                    'pen' = pg.mkPen(None)
                     }, ...]
        :return:
        """
        self.scatterPlot.clear()
        self.scatterPlot.addPoints(spots)

    def _scatterViewboxMouseClickEvent(self, event):
        """ click on scatter viewBox. The parent of scatterPlot. Opens the context menu at any point. """
        if event.button() == QtCore.Qt.RightButton:
            event.accept()
            self._raiseScatterContextMenu(event)

    #############################################################
    ############   Settings widgets callbacks    ################
    #############################################################

    def _editSpectrumGroup(self):
        sg = self._selectedSpectrumGroup
        if isinstance(sg, SpectrumGroup):
            sge = SpectrumGroupEditor(parent=self, mainWindow=self.mainWindow, obj=sg, editMode=True)
            sge._tabWidget.setCurrentIndex(2)  # the series tab is the last
            sge.exec_()
        else:
            MessageDialog.showWarning(title='', message='No SpectrumGroup selected.\nSelect a SpectrumGroup from the input pulldown.')

    def _sgPulldownCallback(self, text):
        if self.spectrumGroupPulldown.getText() == NewSG:
            sge = SpectrumGroupEditor(parent=self, mainWindow=self.mainWindow, editMode=False)
            sge.exec_()
            sg = sge.obj
            if isinstance(sg, SpectrumGroup):
                self.spectrumGroupPulldown.select(sg)
                self._selectedSpectrumGroup = sg
            else:
                self.spectrumGroupPulldown.setCurrentIndex(0)
                self._selectedSpectrumGroup = None
        sg = self.spectrumGroupPulldown.getObject()
        if isinstance(sg, SpectrumGroup):
            self._selectedSpectrumGroup = sg
            if sg.seriesUnits:
                self._seriesUnit = sg.seriesUnits
                self.fittingPlot.setLabel('bottom', self._seriesUnit)
                self.bindingPlot.setLabel('bottom', self._seriesUnit)

    def _setSpectrumGroupPulldown(self, objects=None, index=None, *args):
        if objects is None:
            objects = [sg for sg in self.project.spectrumGroups if not sg.isDeleted]
        objects.insert(0, None)
        texts = [NewSG] + [getattr(ob, 'name') for ob in objects if ob]
        self.spectrumGroupPulldown.setData(texts=texts, objects=objects, headerText=SELECT, headerEnabled=False, index=index)

    def _onSGcreation(self, dd):
        newSg = dd.get('object')
        objs = self.project.spectrumGroups
        lastSelected = self._selectedSpectrumGroup
        if isinstance(lastSelected, SpectrumGroup):
            ix = self.spectrumGroupPulldown.getItemIndex(lastSelected.name)
            self._setSpectrumGroupPulldown(objects=objs)
            self.spectrumGroupPulldown.select(lastSelected.name)

        else:
            self._setSpectrumGroupPulldown(objects=objs)

    def _onSGdeletion(self, dd):
        lastSelected = self._selectedSpectrumGroup
        deleted = dd.get('object')
        objs = [o for o in self.project.spectrumGroups if o != deleted]
        if deleted == lastSelected:
            self._setSpectrumGroupPulldown(objects=objs, index=0)
            self._selectedSpectrumGroup = None
            self._updateModule()
        else:
            if isinstance(lastSelected, SpectrumGroup):
                self._setSpectrumGroupPulldown(objects=objs)
                self.spectrumGroupPulldown.select(lastSelected.name)
                # no need of updating the whole module if another sg was deleted
            else:
                self._setSpectrumGroupPulldown(objects=objs, index=0)
                self._updateModule()

    def showNmrAtomsSettings(self):
        from ccpn.ui.gui.widgets.NmrAtomsSelections import _NmrAtomsSelection

        if self.project:
            nmrAtoms = list(set([n.name for n in self.project.nmrAtoms]))

            popup = _NmrAtomsSelection(self,
                                       nmrAtoms=nmrAtoms,
                                       checked=self.selectedNmrAtomNames,
                                       relativeContribuitions=self.relativeContribuitions,
                                       size=[500, 450],
                                       grid=(0, 0))
            popup.show()
            popup.raise_()

    def _navigateToPeakPosition(self, peak):
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, _getCurrentZoomRatio

        if self.current is not None:
            if self.current.strip is not None:
                widths = _getCurrentZoomRatio(self.current.strip.viewRange())
                navigateToPositionInStrip(strip=self.current.strip, positions=peak.position, widths=widths)

    def _navigateToNmrItems(self, nmrResidue=None, *args):
        """
        _ccpnInternal. NB Called by several points within the CSM
        navigates To current NmrResidue or its atoms if at least 1.
        """
        if not isinstance(nmrResidue, NmrResidue):
            nmrResidue = self.current.nmrResidue
        if nmrResidue is None:
            return
        self.mainWindow.clearMarks()
        self.nmrResidueTable.scrollToSelectedIndex()
        if self.current.strip is not None:
            strip = self.current.strip

            if len(nmrResidue.selectedNmrAtomNames) > 0:
                nmrAtoms = [nmrResidue.getNmrAtom(str(i)) for i in nmrResidue.selectedNmrAtomNames]
                if len(nmrAtoms) <= 1:
                    navigateToNmrResidueInDisplay(display=strip.spectrumDisplay,
                                                  nmrResidue=nmrResidue,
                                                  widths=_getCurrentZoomRatio(strip.viewRange()),
                                                  markPositions=True
                                                  )
                else:
                    navigateToNmrAtomsInStrip(strip,
                                              nmrAtoms=nmrAtoms,
                                              widths=_getCurrentZoomRatio(strip.viewRange()),
                                              markPositions=True
                                              )
        else:
            if len(self.project.strips) > 0:
                selectFirst = MessageDialog.showYesNo('No Strip selected.', ' Use first available?')
                if selectFirst:
                    self.current.strip = self.project.strips[0]
                    self._navigateToNmrItems()
            else:
                if self._openSpectra():
                    self._navigateToNmrItems()

    def _toggleRawDataOption(self):
        value = self.modeButtons.getSelectedText()
        if value == HEIGHT or value == VOLUME:
            self.displayDataButton.show()
            self.displayDataLabel.show()
        else:
            self.displayDataButton.hide()
            self.displayDataLabel.hide()

    def _setDefaultThreshold(self):
        self._updateModule(silent=True)
        self._setThresholdLineBySTD()

    def _setThresholdLineBySTD(self):
        nc = self.project.getByPid(self.nmrResidueTable.ncWidget.getText())
        if nc:
            deltas = [n._delta for n in nc.nmrResidues if n._delta is not None]
            if len(deltas) > 0:
                if not None in deltas:
                    std = np.std(deltas)
                    if std:
                        self.thresholdLinePos = std
                        self.thresholdSpinBox.set(std)

    def _displayTableForNmrChain(self, nmrChain):
        """ Add custom action when selecting a chain on the table pulldown"""
        self._addNmrResidueColour(nmrChain)
        self._updateModule()

    def _peakDeletedCallBack(self, data):
        if len(self.current.peaks) == 0:
            self._updateModule()

    def _addNmrResidueColour(self, nmrChain):
        colours = _getRandomColours(len(nmrChain.nmrResidues))
        for nmrR, colour in zip(nmrChain.nmrResidues, colours):
            if nmrR._colour is None:
                nmrR._colour = colour

    # def _peakChangedCallBack(self, data):
    #   """ Update a module on a single peak move. Bad idea. What if you move 100 peaks together!"""
    #   peak = data[Notifier.OBJECT]
    #   if self._peakChangedNotifier.lastPeakPos != peak.position:
    #     self._peakChangedNotifier.lastPeakPos = peak.position
    #     self._updateModule()

    def _checkBoxCallback(self, data):
        """
        Callback from checkboxes inside a table
        """
        objs = data[Notifier.OBJECT]

        itemSelection = data['rowItem']
        # att = self.nmrResidueTable.horizontalHeaderItem(itemSelection.column()).text()
        # if att == 'Included':
        obj = data[Notifier.OBJECT]
        if obj:
            obj._includeInDeltaShift = data['checked']
            # obj._finaliseAction('change')
            self._updateModule()
        # pass

    def _nmrTableSelectionCallback(self, data):
        """
        Notifier Callback for selecting a row in the table
        """
        getLogger().Warning('Table temp disabled')

    def _nmrObjectChanged(self, data):
        self._updateModule()

    def _nmrResidueDeleted(self, data):
        if len(self.current.nmrResidues) == 0:
            self._updateModule()

    def _selectNmrResiduesAboveThreshold(self):
        if self.aboveObjects:
            self.current.nmrResidues = self.aboveObjects

    def _threshouldLineMoved(self):
        pos = self.barGraphWidget.xLine.pos().y()
        self.thresholdSpinBox.setValue(pos)
        self._updateBarGraph()

    def _isInt(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def _setNmrColours(self, nmrResidues):
        colours = _getRandomColours(nmrResidues)
        for nmrR, colour in zip(nmrResidues, colours):
            if not hasattr(nmrR, 'colour'):
                nmrR._colour = colour

    def _updateModule(self, silent=False):
        """

        :param silent: if silent does not update the module!
        :return: deltas
        """

        mode = self.modeButtons.getSelectedText()
        if not mode in MODES:
            return
        weights = self.relativeContribuitions
        selectedAtomNames = self.selectedNmrAtomNames
        sg = self._selectedSpectrumGroup

        if isinstance(sg, SpectrumGroup):
            spectra = sg.spectra
        else:
            spectra = []
        if self.nmrResidueTable:
            if self.nmrResidueTable._nmrChain is not None:
                for nmrResidue in self.nmrResidueTable._nmrChain.nmrResidues:
                    if self._isInt(nmrResidue.sequenceCode):
                        self._updatedPeakCount(nmrResidue, spectra)
                        if nmrResidue._includeInDeltaShift:
                            nmrResidue.spectraCount = len(spectra)
                            nmrResidueAtoms = [atom.name for atom in nmrResidue.nmrAtoms]
                            nmrResidue.selectedNmrAtomNames = [atom for atom in nmrResidueAtoms if atom in selectedAtomNames]
                            nmrResidue._delta = getNmrResidueDeltas(nmrResidue, selectedAtomNames, mode=mode, spectra=spectra, atomWeights=weights)

                            df, peaksdf = self._getBindingCurves([nmrResidue])
                            bindingCurves = self._getScaledBindingCurves(df)
                            if bindingCurves is not None:
                                plotData = bindingCurves.replace(np.nan, 0)
                                columns = df.columns
                                y = plotData.values.flatten(order='F')
                                xss = np.array([columns] * plotData.shape[0])
                                x = xss.flatten(order='F')
                                kd = _getKd(oneSiteBindingCurve, x, y)
                                if not kd:
                                    getLogger().debug('Kd not set for nmrResidue %s' % nmrResidue.pid)
                                nmrResidue._estimatedKd = kd
                        else:
                            nmrResidue._delta = None
                if not silent:
                    self._updateTable(self.nmrResidueTable._nmrChain)
                    self._updateBarGraph()
                    self._plotScatters(self._getScatterData(), selectedObjs=self.current.nmrResidues)
                    self._plotBindingCFromCurrent()

    def _showOnMolecularViewer(self):
        """
        1) write the script in the scripts/pymol dir
        2) run pymol with the script
        """
        import json
        import subprocess

        filePath = os.path.join(self.application.pymolScriptsPath, PymolScriptName)

        pymolPath = self.application.preferences.externalPrograms.pymol
        pdbPath = self.pathPDB.get()

        if not os.path.exists(pymolPath):
            ok = MessageDialog.showOkCancelWarning('Molecular Viewer not Set'
                                                   , 'Select the executable file on preferences')
            if ok:
                from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup

                pp = PreferencesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, preferences=self.application.preferences)
                pp.tabWidget.setCurrentIndex(pp.tabWidget.count() - 1)
                pp.exec_()
                return

        while not pdbPath.endswith('.pdb'):
            sucess = self.pathPDB._openFileDialog()
            if sucess:
                pdbPath = self.pathPDB.get()
            else:
                return

        aboveThresholdResidues = "+".join([str(x) for x in self.aboveX])
        belowThresholdResidues = "+".join([str(x) for x in self.belowX])
        missingdResidues = "+".join([str(x) for x in self.disappearedX])
        selection = "+".join([str(x.sequenceCode) for x in self.current.nmrResidues])
        colourAboveThreshold = hexToRgb(self.aboveBrush)
        colourBelowThreshold = hexToRgb(self.belowBrush)
        colourMissing = hexToRgb(self.disappearedPeakBrush)
        scriptPath = _CSMSelection2PyMolFile(filePath, pdbPath, aboveThresholdResidues, belowThresholdResidues,
                                             missingdResidues, colourMissing, colourAboveThreshold, colourBelowThreshold,
                                             selection)
        try:
            self.pymolProcess = subprocess.Popen(pymolPath + ' -r ' + scriptPath,
                                                 shell=True,
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE)
        except Exception as e:
            getLogger().warning('Pymol not started. Check executable.', e)

    def _toggleUserFncBox(self):
        if self.fittingModeRB.get() == OTHER:
            self.fittingModeEditor.show()
        else:
            self.fittingModeEditor.hide()

    def _selectCurrentNmrResiduesNotifierCallback(self, *args):
        nmrResidues = self.current.nmrResidues
        if len(nmrResidues) > 0:
            pss = [str(nmrResidue.sequenceCode) for nmrResidue in nmrResidues]
            self._plotBindingCFromCurrent()
            self._plotFittedCallback()
            self._plotScatters(self._getScatterData(), selectedObjs=nmrResidues)
            self._selectBarLabels(pss)

    def _getAllBindingCurvesDataFrameForChain(self):
        nmrChainTxt = self.nmrResidueTable.ncWidget.getText()
        nmrChain = self.project.getByPid(nmrChainTxt)
        if nmrChain is not None:
            dataFrame, pkDf = self._getBindingCurves(nmrChain.nmrResidues)
            return dataFrame

    def _plotFittedCallback(self):
        self.fittingPlot.clear()
        self._clearLegend(self.fittingPlot.legend)

        plotData, pksdf = self._getBindingCurves(self.current.nmrResidues, True)
        plotData = self._getScaledBindingCurves(plotData)

        if plotData is not None:
            if self.fittingModeRB.get() in self._availableFittingPlots:
                ff = self._availableFittingPlots.get(self.fittingModeRB.get())
                ff(plotData)
            else:
                getLogger().warning(NIY)

    def _plot1SiteBindFitting(self, bindingCurves):
        """ """
        if bindingCurves is None:
            return

        self.fittingLine.hide()
        ### the actual fitting call
        x_atHalf_Y, bmax, xs, yScaled, xf, yf = _fit1SiteBindCurve(bindingCurves)
        ## setting the plot
        if not np.any(yScaled) or not np.any(yf):
            return  # just zeros
        if x_atHalf_Y <= 0:
            return
        self.fittingPlot.plot(xs, yScaled, symbol='o', pen=None)
        self.fittingPlot.plot(xf, yf, name='Fitted')
        self.fittingLine.setValue(x_atHalf_Y)
        self.fittingLine.label.setText('kd ' + str(round(x_atHalf_Y, 3)))
        self.fittingLine.show()
        self.fittingPlot.setLabel('left', RelativeDisplacement)
        self.fittingPlot.setLabel('bottom', self._seriesUnit)
        self.fittingPlot.setRange(xRange=[0, max(xf)], yRange=[0, 1])
        self.bindingPlot.autoRange()

    def _plotExponentialDecay(self, bindingCurves):
        """ """
        if bindingCurves is None:
            return

        bindingCurves = bindingCurves.replace(np.nan, 0)
        self.fittingLine.hide()
        ### the actual fitting call
        xs, ys, xf, yf, *popt = _fitExpDecayCurve(bindingCurves)
        ## setting the plot
        if not np.any(yf):
            return  # just zeros
        A, K, = popt
        label = 'Fitted Function: %.2f, %.3f' % (A, K)
        self.fittingPlot.plot(xs, ys, symbol='o', pen=None)
        self.fittingPlot.plot(xf, yf, name=label)
        self.fittingPlot.setLimits(xMin=0, xMax=None, yMin=-1, yMax=None)
        self.bindingPlot.autoRange()

    def _openSpectra(self):
        openSpectra = MessageDialog.showYesNo('No Spectra displayed.', 'Impossible to navigate to peak position.'
                                                                       'Open a new SpectrumDisplay?')
        if openSpectra:
            try:
                from ccpn.ui.gui.lib.MenuActions import _openItemObject

                sg = self._selectedSpectrumGroup
                if sg is not None:
                    _openItemObject(self.mainWindow, sg.spectra)
                return True
            except:
                getLogger().warning('Failed to open selected objects')
        return False

    #############################################################
    ######   Updating widgets (plots and table) callbacks #######
    #############################################################

    # from ccpn.util.decorators import profile
    # @profile
    def _updateBarGraph(self):
        xs = []
        ys = []
        obs = []
        self.disappearedX = []
        self.disappearedY = []
        self.disappereadObjects = []
        self.aboveX = []
        self.aboveY = []
        self.aboveObjects = []
        self.belowX = []
        self.belowY = []
        self.belowObjects = []
        self.aboveBrush = 'g'
        self.belowBrush = 'r'
        self.disappearedPeakBrush = 'b'
        # check if all values are none:
        if self.nmrResidueTable._dataFrameObject is None: return
        shifts = [nmrResidue._delta for nmrResidue in self.nmrResidueTable._dataFrameObject.objects]
        if not any(shifts):
            self.barGraphWidget.clear()
            return

        if self.barGraphWidget.xLine:
            self.thresholdLinePos = self.barGraphWidget.xLine.pos().y()

            if self.nmrResidueTable._dataFrameObject:
                for nmrResidue in self.nmrResidueTable._dataFrameObject.objects:
                    if nmrResidue:
                        nmrResidue.missingPeaks = False
                        if hasattr(nmrResidue, '_spectraWithMissingPeaks'):
                            if len(nmrResidue._spectraWithMissingPeaks) != 0:
                                if nmrResidue.sequenceCode:

                                    x = int(nmrResidue.sequenceCode)
                                    # x = self.nmrResidueTable._dataFrameObject.objects.index(nmrResidue)
                                    if nmrResidue._delta:
                                        y = nmrResidue._delta
                                    else:
                                        if nmrResidue._includeInDeltaShift:
                                            y = self.disappearedBarThresholdSpinBox.value()
                                        else:
                                            y = 0
                                    self.disappearedY.append(y)
                                    self.disappearedX.append(x)
                                    self.disappereadObjects.append(nmrResidue)
                                    nmrResidue.missingPeaks = True
                        if nmrResidue._delta:
                            if not nmrResidue.missingPeaks:
                                if nmrResidue.sequenceCode:

                                    x = int(nmrResidue.sequenceCode)
                                    # x = self.nmrResidueTable._dataFrameObject.objects.index(nmrResidue)
                                    y = float(nmrResidue._delta)

                                    xs.append(x)
                                    ys.append(y)
                                    obs.append(nmrResidue)
                                    if y > self.thresholdLinePos:
                                        self.aboveY.append(y)
                                        self.aboveX.append(x)
                                        self.aboveObjects.append(nmrResidue)
                                    else:
                                        self.belowX.append(x)
                                        self.belowY.append(y)
                                        self.belowObjects.append(nmrResidue)

        selectedNameColourA = self.aboveThresholdColourBox.getText()
        for code, name in spectrumColours.items():
            if name == selectedNameColourA:
                self.aboveBrush = code

        selectedNameColourB = self.belowThresholdColourBox.getText()
        for code, name in spectrumColours.items():
            if name == selectedNameColourB:
                self.belowBrush = code

        selectedNameColourC = self.disappearedColourBox.getText()  #disappeared peaks
        for code, name in spectrumColours.items():
            if name == selectedNameColourC:
                self.disappearedPeakBrush = code

        self.barGraphWidget.clear()
        self.barGraphWidget._lineMoved(aboveX=self.aboveX,
                                       aboveY=self.aboveY,
                                       aboveObjects=self.aboveObjects,
                                       belowX=self.belowX,
                                       belowY=self.belowY,
                                       belowObjects=self.belowObjects,
                                       belowBrush=self.belowBrush,
                                       aboveBrush=self.aboveBrush,
                                       disappearedX=self.disappearedX,
                                       disappearedY=self.disappearedY,
                                       disappearedObjects=self.disappereadObjects,
                                       disappearedBrush=self.disappearedPeakBrush,
                                       )
        if xs and ys:
            self.barGraphWidget.setViewBoxLimits(0, max(xs) * 10, 0, max(ys) * 10)
            if self._zoomOnInit:
                self.barGraphWidget.customViewBox.setRange(xRange=[min(xs) - 10, max(xs) + 10], yRange=[0, max(ys)], )
            self._zoomOnInit = False  # do only at startup
            # self._selectBarLabels([str(nmrResidue.sequenceCode) for nmrResidue in self.current.nmrResidues])

    def _updateThresholdLineValue(self, value):
        if self.barGraphWidget:
            self.barGraphWidget.xLine.setPos(value)
            self._updateBarGraph()

    def _updateThreshold(self):
        self.thresholdSpinBox.setValue(self.barGraphWidget.xLine.pos().y())
        self._updateBarGraph()
        # self.barGraphWidget._lineMoved()

    def _updateTable(self, nmrChain):
        """ Updates table based on the given nmrChain """
        self.nmrResidueTable.ncWidget.select(nmrChain.pid)
        self.nmrResidueTable._update(nmrChain)
        self.nmrResidueTable._selectOnTableCurrentNmrResidues(self.current.nmrResidues)

    def _updatedPeakCount(self, nmrResidue, spectra):
        if len(nmrResidue.nmrAtoms) > 0:
            peaks = [p for p in nmrResidue.nmrAtoms[0].assignedPeaks if p.peakList.spectrum in spectra]

            spectraWithPeaks = [peak.peakList.spectrum for peak in peaks]
            spectraWithMissingPeaks = [spectrum for spectrum in spectra if spectrum not in spectraWithPeaks]
            nmrResidue._spectraWithMissingPeaks = spectraWithMissingPeaks

            return nmrResidue._spectraWithMissingPeaks

    def _clearModule(self):
        self.nmrResidueTable.ncWidget.select(SELECT)

    def _clearLegend(self, legend):
        while legend.layout.count() > 0:
            legend.layout.removeAt(0)
        legend.items = []

    def restoreWidgetsState(self, **widgetsState):

        if 'Spectra' or 'Groups' in widgetsState:
            _BackCompatibility._spectraToSpectrumGroup(self, **widgetsState)
        self.selectedNmrAtomNames = widgetsState.get(SelectedNmrAtomNames, {})
        self.relativeContribuitions = widgetsState.get(RelativeContribuitions, {})
        super().restoreWidgetsState(**widgetsState)
        self._updateModule()

    @CcpnModule.widgetsState.getter
    def widgetsState(self):
        """return  {"variableName":"value"}  of all gui Variables  """
        widgetsState = super().widgetsState
        widgetsState[RelativeContribuitions] = self.relativeContribuitions
        widgetsState[SelectedNmrAtomNames] = self.selectedNmrAtomNames
        return widgetsState

    def _closeModule(self):
        """
        Re-implementation of closeModule function from CcpnModule to unregister notification on current
        """
        try:
            self._selectCurrentNRNotifier.unRegister()
            self._sgNotifier.unRegister()
            self._sgDeleteNotifier.unRegister()
            self._peakDeletedNotifier.unRegister()
            self._nrChangedNotifier.unRegister()
            self._nrDeletedNotifier.unRegister()
            self.nmrResidueTable._close()
        except Exception as es:
            getLogger().warning(str(es))
        finally:
            super()._closeModule()


class _BackCompatibility():

    @staticmethod
    def _spectraToSpectrumGroup(guiModule, **widgetsState):
        """
        A small helper to create spectrumGroups from spectra if opening a project with a CSM module saved in a layout
        before version 3.0.3.
        Up to Version 3.0.3 multiple spectra could be selected from the settings as input data.
        After 3.0.3 only one spectrumGroup at the time. This methods helps to create a new usable
        spectrumGroup from the stored spectra in the layout file.
        Concentrations as series value were stored in sample/samples components. Series are created if this
        information is fetched.

        :param guiModule:
        :param widgetsState:
        :return:
        """

        isSpectraSelected = widgetsState.get('Spectra')
        isSGSelected = widgetsState.get('Groups')
        if isSpectraSelected:
            needCreateNewSG = MessageDialog.showYesNo('Chemical Shift Mapping Module changes from version 3.0.3',
                                                      'A single spectrum selection is not allowed from on this module.'
                                                      '\nDo you want create a new SpectrumGroup from the previous selection?')
            if needCreateNewSG:
                spectraPids = list(map(lambda x: x.pid, guiModule.project.spectra))
                pids = [k for k in widgetsState.keys() if k in spectraPids]
                availableSpectra = [guiModule.project.getByPid(pid) for pid in pids]
                spectra = []
                concentrations = []
                cunits = []
                for spectrum in availableSpectra:
                    if widgetsState.get(spectrum.pid):  #use only if checked
                        if spectrum.sample is not None:
                            sample = spectrum.sample
                            sampleComponent = sample._fetchSampleComponent(name=spectrum.name)
                            concentrations.append(sampleComponent.concentration)
                            cunits.append(sampleComponent.concentrationUnit)
                            spectra.append(spectrum)
                time = datetime.now().time().strftime("%H:%M:%S")
                sg = guiModule.project.newSpectrumGroup('Restored_' + time, spectra=spectra)
                sg.series = concentrations
                sg.seriesUnits = cunits[-1]
                sg.sortSpectraBySeries(False)
                try:
                    guiModule.spectrumGroupPulldown.select(sg)
                except Exception as e:
                    MessageDialog.showWarning('Chemical Shift Mapping Module',
                                              'Impossible to select automatically the spectrumGroup')

        if isSGSelected:
            sgPids = list(map(lambda x: x.pid, guiModule.project.spectrumGroups))
            pids = [k for k in widgetsState.keys() if k in sgPids]
            availableSgs = [guiModule.project.getByPid(pid) for pid in pids]
            for sg in availableSgs:
                if widgetsState.get(sg.pid):  # use only if checked
                    try:
                        guiModule.spectrumGroupPulldown.select(sg)
                    except Exception as e:
                        MessageDialog.showWarning('Chemical Shift Mapping Module',
                                                  'Impossible to select automatically the spectrumGroup')
                    break

# if __name__ == '__main__':
#   from PyQt5 import QtGui, QtWidgets
#   from ccpn.ui.gui.widgets.Application import TestApplication
#   from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
#
#
#   app = TestApplication()
#   win = QtWidgets.QMainWindow()
#
#   moduleArea = CcpnModuleArea(mainWindow=None)
#   # module = ChemicalShiftsMapping(mainWindow=None, name='My Module')
#   # moduleArea.addModule(module)
#
#
#   win.setCentralWidget(moduleArea)
#   win.resize(1000, 500)
#   # win.setWindowTitle('Testing %s' % module.moduleName)
#   win.show()
#
#
#   app.start()
#   win.close()
