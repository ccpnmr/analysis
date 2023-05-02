#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-03-29 13:40:33 +0100 (Tue, March 29, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Chris Spronk $"
__date__ = "$Date: 2017-11-28 10:28:42 +0000 (Tue, Nov 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import os, copy, json, pprint, math, shutil, pandas, operator, numpy
from collections import OrderedDict as OD

import pandas as pd
from math import log10
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.framework.lib.Plugin import Plugin
from ccpn.ui.gui.modules.PluginModule import PluginModule
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning, showMessage, showYesNo
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.table.Table import Table
from ccpn.util.nef import GenericStarParser, StarIo
from ccpn.util.nef.GenericStarParser import SaveFrame, DataBlock, DataExtent, Loop, LoopRow
from functools import partial
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.util.decorators import logCommand
from Classes.Simulator import Simulator, SimulatedSpectrum
from Classes.DatabaseCaller import DatabaseCaller
import numpy as np
from Functions.LineshapeCreator import createLineshape
from .pluginAddons import _addRow, _addColumn, _addVerticalSpacer, _setWidth, _setWidgetProperties


############
# Settings #
############

# Widths in pixels for nice widget alignments, length depends on the number of fixed columns in the plugin.
# Variable number of columns will take the last value in the list
columnWidths = [75]

# Set some tooltip texts
help = {'SimulationType': 'The type of simulation to create. Spin System: Accurate and flexible but only for very small molecules. Peak List: Less flexible but can be made for any molecule.'}


class CreateDatabaseReferenceGuiPlugin(PluginModule):
    className = 'CreateDatabaseReferenceGuiPlugin'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super(CreateDatabaseReferenceGuiPlugin, self)
        PluginModule.__init__(self, mainWindow=mainWindow, plugin=plugin, application=application)

        # Import some functionality for placing widgets on the grid and setting their properties
        from .pluginAddons import _addRow, _addColumn, _addVerticalSpacer, _setWidth, _setWidgetProperties

        self.scrollArea = ScrollArea(self.mainWidget, grid=(0, 0))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaLayout = Frame(None, setLayout=True)
        self.scrollArea.setWidget(self.scrollAreaLayout)
        # self.scrollAreaLayout.setContentsMargins(20, 20, 20, 20)

        # self.userPluginPath = self.application.preferences.general.userPluginPath
        # self.outputPath = self.application.preferences.general.dataPath

        self.pluginPath = os.path.join(self.project.path, CreateDatabaseReferenceGuiPlugin.className)

        # Create ORDERED dictionary to store all parameters for the run
        # deepcopy doesn't work on dictionaries with the qt widgets, so to get a separation of gui widgets and values for storage
        # it is needed to create the two dictionaries alongside each other
        self.guiDict = OD([('CoreWidgets', OD()), ('TemporaryWidgets', OD())])
        self.settings = OD([('Spectra', OD()), ('Current', OD()), ('Simulations', OD())])

        # # Input check
        # validInput = self._inputDataCheck()
        # if not validInput:
        #     return

        # setup database metabolite tables
        self.simulator = Simulator(self.project)
        self.caller = DatabaseCaller('/Users/mh653/Documents/PhD/Database/Merged_Databases/merged_database.db')

        grid = (0, 0)

        widget = Label(self.scrollAreaLayout, text='Reference Spectrum', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2), callback=self._selectSpectrum)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        self.spectra = [spectrum.id for spectrum in self.project.spectra]
        widget.setData(self.spectra)
        self.guiDict['CoreWidgets']['SpectrumId'] = widget
        self.settings['Current']['SpectrumId'] = self._getValue(widget)
        if self.spectra:
            self._selectSpectrum(self.spectra[0])

        # Pull down and button to create a new reference spectrum
        grid = _addRow(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2), tipText=help['SimulationType'], callback=self._chooseSimulationType)
        _setWidgetProperties(widget, 200)

        simulationTypes = ['Spin System', 'Peak List']
        widget.setData(simulationTypes)
        self.guiDict['CoreWidgets']['SimulationTypePullDown'] = widget
        self._chooseSimulationType(simulationTypes[0])

        grid = _addColumn(_addColumn(grid))
        widget = Button(parent=self.scrollAreaLayout, text='Create New Simulation', grid=grid, gridSpan=(1, 2), callback=self._createNewSimulation)
        _setWidgetProperties(widget, 200)
        self.guiDict['CoreWidgets']['SimulationTypeButton'] = widget

        grid = _addColumn(_addColumn(grid))
        widget = Button(parent=self.scrollAreaLayout, text='Save to Database', grid=grid, gridSpan=(1, 2), callback=self._saveToDatabase)
        _setWidgetProperties(widget, 200)
        self.guiDict['CoreWidgets']['SaveToDatabaseButton'] = widget

    def _selectSpectrum(self, spectrumID):
        self.settings['Current']['ReferenceSpectrum'] = self.project.getByPid('SP:' + spectrumID)

    def _chooseSimulationType(self, type):
        self.settings['Current']['SimulationType'] = type

    def _createNewSimulation(self):
        for dictkey in self.guiDict['TemporaryWidgets']:
            for widgetkey in self.guiDict['TemporaryWidgets'][dictkey]:
                self.guiDict['TemporaryWidgets'][dictkey][widgetkey].deleteLater()
        self.guiDict['TemporaryWidgets'] = OD()
        self.guiDict['TemporaryWidgets']['SpectrumWidgets'] = OD()
        type = self.settings['Current']['SimulationType']
        referenceSpectrum = self.settings['Current']['ReferenceSpectrum']
        name = 'User_Defined_Metabolite'
        frequency = round(referenceSpectrum.spectrometerFrequencies[0]/10)*10
        points = len(referenceSpectrum.positions)
        limits = (max(referenceSpectrum.positions), min(referenceSpectrum.positions))
        temperature = referenceSpectrum.temperature
        simulatedSpectrum = self.simulator.spectrumFromScratch(frequency, points, limits)
        spectrum, sample, substance = self.simulator.buildCcpnObjects(simulatedSpectrum,
                                                                      metaboliteName=name,
                                                                      frequency=frequency, temperature=temperature)
        self.settings['Current']['Spectrum'] = spectrum
        simulatedSpectrum.spectrum = spectrum
        self.settings['Current']['SimulatedSpectrum'] = simulatedSpectrum
        simulatedSpectrum.scaleSpectrum(10)

        self.settings['Current']['MetaboliteName'] = name
        self.settings['Current']['Sample'] = sample
        self.settings['Current']['Substance'] = substance

        grid = (2, 0)

        # Add a widget for setting the metabolite name
        widget = Label(self.scrollAreaLayout, text=f'Metabolite Name', grid=grid, gridSpan=(1, 2))
        _setWidgetProperties(widget, 200)
        self.guiDict['TemporaryWidgets']['SpectrumWidgets']['NameLabel'] = widget
        grid = _addColumn(_addColumn(grid))
        widget = LineEdit(self.scrollAreaLayout, text=name, grid=grid, gridSpan=(1, 2))
        widget.textChanged.connect(self._nameChange)
        _setWidgetProperties(widget, 200)
        self.guiDict['TemporaryWidgets']['SpectrumWidgets']['Name'] = widget

        # Add a widget for the simulated spectrum peak width
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Peak Width', grid=grid, gridSpan=(1, 2))
        _setWidgetProperties(widget, 200)
        self.guiDict['TemporaryWidgets']['SpectrumWidgets']['WidthLabel'] = widget
        grid = _addColumn(_addColumn(grid))
        widget = DoubleSpinbox(self.scrollAreaLayout, value=1, decimals=1, step=0.1, grid=grid, gridSpan=(1, 2), callback=self._widthChange, suffix='Hz')
        widget.setRange(0.1, 5)
        _setWidgetProperties(widget, 200)
        self.guiDict['TemporaryWidgets']['SpectrumWidgets']['Width'] = widget
        self.settings['Current']['Width'] = self._getValue(widget)

        # Add a widget for the simulated spectrum scale
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Scale (10^n)', grid=grid, gridSpan=(1, 2))
        _setWidgetProperties(widget, 200)
        self.guiDict['TemporaryWidgets']['SpectrumWidgets']['ScaleLabel'] = widget
        grid = _addColumn(_addColumn(grid))
        widget = DoubleSpinbox(self.scrollAreaLayout, value=1, decimals=3, step=0.001, grid=grid, gridSpan=(1, 2), callback=self._scaleChange)
        widget.setRange(-10, 10)
        _setWidgetProperties(widget, 200)
        self.guiDict['TemporaryWidgets']['SpectrumWidgets']['Scale'] = widget
        self.settings['Current']['Scale'] = self._getValue(widget)

        # Add a widget for the simulated spectrum frequency
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Frequency', grid=grid, gridSpan=(1, 2))
        _setWidgetProperties(widget, 200)
        self.guiDict['TemporaryWidgets']['SpectrumWidgets']['FrequencyLabel'] = widget
        grid = _addColumn(_addColumn(grid))
        widget = DoubleSpinbox(self.scrollAreaLayout, value=frequency, step=10, grid=grid, gridSpan=(1, 2), suffix='MHz', callback=self._frequencyChange)
        widget.setRange(10, 1200)
        _setWidgetProperties(widget, 200)
        self.guiDict['TemporaryWidgets']['SpectrumWidgets']['Frequency'] = widget
        self.settings['Current']['Frequency'] = self._getValue(widget)

        if type == 'Spin System':
            grid = _addRow(grid)
            self.settings['Current']['SsmSize'] = 1
            self.settings['Current']['Values'] = np.zeros((12, 12))
            self.settings['Current']['ProtonCounts'] = [1]*12
            self.settings['Current']['Shifts'] = [0]*12
            widget = Label(self.scrollAreaLayout, text='Total Multiplets', grid=grid, gridSpan=(1, 2))
            _setWidgetProperties(widget, 200)
            self.guiDict['TemporaryWidgets']['SpectrumWidgets']['MultipletSpinboxLabel'] = widget
            grid = _addColumn(_addColumn(grid))
            widget = Spinbox(self.scrollAreaLayout, value=1, grid=grid, gridspan=(1, 1), callback=self._multipletChange)
            _setWidgetProperties(widget, 200)
            self.guiDict['TemporaryWidgets']['SpectrumWidgets']['MultipletSpinbox'] = widget
            widget.setRange(1, 10)
            self.setupSsmGrid()
        elif type == 'Peak List':
            pass

    def _nameChange(self, name):
        self.settings['Current']['MetaboliteName'] = name.replace(' ', '_')
        self.settings['Current']['Sample'].name = f'{name}_sample'
        self.settings['Current']['Substance'].rename(name=f'{name}_substance', labelling='metabolite')
        self.settings['Current']['Spectrum'].name = f'{name}_spectrum'

    def _widthChange(self, width):
        self.settings['Current']['SimulatedSpectrum'].setWidth(width)

    def _scaleChange(self, scale):
        scale = 10 ** scale
        self.settings['Current']['SimulatedSpectrum'].scaleSpectrum(scale)

    def _frequencyChange(self, frequency):
        self.settings['Current']['SimulatedSpectrum'].setFrequency(frequency)

    def _multipletChange(self, multiplets):
        self.settings['Current']['SsmSize'] = multiplets
        self.setupSsmGrid()

    def setupSsmGrid(self):
        if 'Spinboxes' in self.guiDict['TemporaryWidgets']:
            for key in self.guiDict['TemporaryWidgets']['Spinboxes']:
                self.guiDict['TemporaryWidgets']['Spinboxes'][key].deleteLater()
        self.guiDict['TemporaryWidgets']['Spinboxes'] = OD()
        self.guiDict['TemporaryWidgets']['Checkboxes'] = OD()
        multiplets = self.settings['Current']['SsmSize']
        self._guiGridToRealSsm()
        # self.settings['Current']['SimulatedSpectrum'].spinSystemMatrix = self.settings['Current']['Values'][:multiplets, :multiplets]
        grid = (7, 0)
        for i in range(multiplets):
            self.createProtonCountSpinbox(i)
            grid = _addRow(grid)
            self.settings['Current']['SimulatedSpectrum'].multiplets[str(i)] = {'center': float(0), 'indices': [i]}
            for j in range(multiplets):
                if i <= j:
                    self._createSsmGridSpinbox(i, j)

    def createProtonCountSpinbox(self, column):
        def changeProtonCount():
            count = widget.value()
            protonCounts = self.settings['Current']['ProtonCounts']
            protonCounts[column] = count
            self.settings['Current']['ProtonCounts'] = protonCounts
            self._guiGridToRealSsm()
            self.settings['Current']['SimulatedSpectrum'].updateLineshapeFromSpinSystem()
        widget = Spinbox(self.scrollAreaLayout, value=1, step=1, grid=(7, column+1), gridSpan=(1, 1))
        widget.setRange(1, 6)
        widget.valueChanged.connect(changeProtonCount)
        self.guiDict['TemporaryWidgets']['Spinboxes'][f'ProtonSpinbox-{column}'] = widget

    def _createSsmGridSpinbox(self, row, column):
        def changeMultipletCenter():
            shift = widget.value()
            shifts = self.settings['Current']['Shifts']
            shifts[row] = shift
            self.settings['Current']['Shifts'] = shifts
            self._guiGridToRealSsm()
            self.settings['Current']['SimulatedSpectrum'].updateLineshapeFromSpinSystem()
        def changeCouplingConstant():
            coupling = widget.value()
            self.settings['Current']['Values'][column][row] = coupling
            self.settings['Current']['Values'][row][column] = coupling
            self._guiGridToRealSsm()
            self.settings['Current']['SimulatedSpectrum'].updateLineshapeFromSpinSystem()
        grid = (row + 8, column + 1)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=self.settings['Current']['Values'][column][row], decimals=4, step=0.0001, grid=grid, gridspan=(1, 1))
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets']['Spinboxes'][f'Spinbox-{column}-{row}'] = widget
        if row == column:
            multipletId = str(column)
            widget.valueChanged.connect(changeMultipletCenter)
            widget.setRange(-2, 12)
        else:
            widget.valueChanged.connect(changeCouplingConstant)
            widget.setRange(0, 20)
            widget.setSingleStep(0.1)
        widget.coordinates = (row, column)

    def _guiGridToRealSsm(self):
        multiplets = self.settings['Current']['SsmSize']
        guiGrid = self.settings['Current']['Values'][:multiplets, :multiplets]
        protonCounts = self.settings['Current']['ProtonCounts'][:multiplets]
        shifts = self.settings['Current']['Shifts'][:multiplets]
        RealSsm = []
        count = 0
        for i, row in enumerate(guiGrid):
            for j in range(protonCounts[i]):
                newrow = []
                for k, value in enumerate(row):
                    count += 1
                    newrow += [value] * protonCounts[k]
                RealSsm.append(newrow)
        ss_matrix = np.array(RealSsm, dtype='float')
        ss_matrix = ss_matrix + ss_matrix.T
        RealShifts = []
        for i, shift in enumerate(shifts):
            RealShifts += [shift] * protonCounts[i]
        for i, shift in enumerate(RealShifts):
            ss_matrix[i][i] = shift
        self.settings['Current']['SimulatedSpectrum'].spinSystemMatrix = ss_matrix

    def _saveToDatabase(self):
        caller = self.simulator.caller

    def _getValue(self, widget):
        # Get the current value of the widget:
        if isinstance(widget, str):
            value = widget
        if not isinstance(widget, Button) and not isinstance(widget, ButtonList):
            if hasattr(widget, 'get'):
                value = widget.get()
            elif hasattr(widget, 'isChecked'):
                value = widget.isChecked()
            elif hasattr(widget, 'value'):
                value = widget.value()
        return value


class CreateDatabaseReference(Plugin):
    PLUGINNAME = 'Create Database Reference'
    guiModule = CreateDatabaseReferenceGuiPlugin
    CCPNPLUGIN = True

    def run(self, **kwargs):
        """ Insert here the script for running Tsar """
        print('Filtering noise peaks', kwargs)


CreateDatabaseReference.register()  # Registers the pipe in the pluginList
# Set tolerances from project.spectrum.tolerances by default
