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
from Classes.Simulator_rework import Simulator, SimulatedSpectrum
import numpy as np
from Functions.LineshapeCreator import createLineshape
from .pluginAddons import _addRow, _addColumn, _addVerticalSpacer, _setWidth, _setWidgetProperties


############
# Settings #
############

# Widths in pixels for nice widget alignments, length depends on the number of fixed columns in the plugin.
# Variable number of columns will take the last value in the list
columnWidths = [300]

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
        self.scrollAreaLayout.setContentsMargins(20, 20, 20, 20)

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
        self.simulator = Simulator(self.project, '/Users/mh653/Documents/PhD/Database/Merged_Databases/merged_database.db')

        grid = (0, 0)

        # Pull down and button to create a new reference spectrum
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2), tipText=help['SimulationType'], callback=self._chooseSimulationType)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        simulationTypes = ['Spin System', 'Peak List']
        widget.setData(simulationTypes)
        self.guiDict['CoreWidgets']['SimulationTypePullDown'] = widget
        self._chooseSimulationType(simulationTypes[0])

        grid = _addColumn(grid)
        widget = Button(parent=self.scrollAreaLayout, text='Create New Simulation', grid=grid, callback=self._createNewSimulation)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), heightType='Minimum')
        self.guiDict['CoreWidgets']['SimulationTypeButton'] = widget

    def _chooseSimulationType(self, type):
        self.settings['Current']['SimulationType'] = type

    def _createNewSimulation(self):
        type = self.settings['Current']['SimulationType']
        simulatedSpectrum = SimulatedSpectrum(self.project, [(0, 0, 0, None)], {'0': {'center': float(0), 'indices': [0]}},
                                              np.zeros((1, 1)), 500, 65536, (12, -2), 'lorentzian', False, None, None,
                                              None)
        x, y = createLineshape([(0, 0, 0, None)], limits=(12, -2))
        spectrum = self.project.newEmptySpectrum(['1H'], name='Reference', intensities=y, positions=x)
        self.settings['Current']['Spectrum'] = spectrum
        simulatedSpectrum.spectrum = spectrum
        self.settings['Current']['SimulatedSpectrum'] = simulatedSpectrum
        if type == 'Spin System':
            self._setupSsmWidgets()
        elif type == 'Peak List':
            pass

    def _setupSsmWidgets(self):
        def changeMultipletCenter():
            shift = widget.value()
            self.settings['Current']['SimulatedSpectrum'].moveMultiplet('0', shift)
        grid = (1, 0)
        self.settings['Current']['ProtonCount'] = 1

        grid = _addColumn(grid)
        widget = Button(parent=self.scrollAreaLayout, text='Remove Proton', grid=grid, callback=self._removeColumn)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), heightType='Minimum')
        self.guiDict['TemporaryWidgets']['RemoveProtonButton'] = widget

        grid = _addColumn(grid)
        widget = Button(parent=self.scrollAreaLayout, text='Add Proton', grid=grid,
                        callback=self._addColumn)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), heightType='Minimum')
        self.guiDict['TemporaryWidgets']['addProtonButton'] = widget

        grid = _addRow(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=float(0), decimals=4, step=0.0001, grid=grid, gridSpan=(1, 1))
        widget.setRange(0, 10)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='l')
        widget.valueChanged.connect(changeMultipletCenter)
        self.guiDict['TemporaryWidgets']['Column0ProtonSpinbox0'] = widget
        self.settings['Current']['ProtonCount'] = 1
        self.grid = grid

    def _removeColumn(self):
        num = self.settings['Current']['ProtonCount']
        if num == 1:
            return
        for key in self.guiDict['TemporaryWidgets']:
            if f'Column{num-1}' in key:
                self.guiDict['TemporaryWidgets'][key].deleteLater()
        self.settings['Current']['ProtonCount'] = num - 1
        self.grid = (self.grid[0]-1, 0)
        self._modifySpinSystemMatrix()

    def _addColumn(self):
        if self.settings['Current']['ProtonCount'] > 3:
            return
        self.settings['Current']['SimulatedSpectrum'].multiplets[str(self.settings['Current']['ProtonCount'])] = {'center': float(0), 'indices': [self.settings['Current']['ProtonCount']]}
        column = self.settings['Current']['ProtonCount']
        for row in range(column+1):
            self._addSsmSpinbox(column, row)
        self.settings['Current']['ProtonCount'] = column + 1
        self.grid = (2, column)
        self._modifySpinSystemMatrix()

    def _addSsmSpinbox(self, column, row):
        def changeMultipletCenter():
            shift = widget.value()
            self.settings['Current']['SimulatedSpectrum'].moveMultiplet(multipletId, shift)
        def changeCouplingConstant():
            coupling = widget.value()
            self.settings['Current']['SimulatedSpectrum'].editCouplingConstant(column, row, coupling)
        grid = (row + 2, column)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=0, decimals=4, step=0.0001, grid=grid, gridSpan=(1, 1))
        widget.setRange(0, 20)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets'][f'Column{column}ProtonSpinbox{row}'] = widget
        if row == column:
            multipletId = str(column)
            widget.valueChanged.connect(changeMultipletCenter)
        else:
            widget.valueChanged.connect(changeCouplingConstant)
            widget.setSingleStep(0.1)


    def _modifySpinSystemMatrix(self):
        dimension = self.settings['Current']['ProtonCount']
        ss_matrix = np.zeros((dimension, dimension))
        for key in [key for key in self.guiDict['TemporaryWidgets'] if key.startswith('Column')]:
            widget = self.guiDict['TemporaryWidgets'][key]
            value = widget.value()
            column = int(key[6]) - 1
            row = int(key[-1]) - 1
            ss_matrix[column][row] = value
            ss_matrix[row][column] = value
        self.settings['Current']['SimulatedSpectrum'].spinSystemMatrix = ss_matrix


    def addSimSpectrumToList(self, spectrum):
        if 'SimulatedSpectra' not in self.settings['Spectra']:
            self.settings['Spectra']['SimulatedSpectra'] = [spectrum]
        else:
            self.settings['Spectra']['SimulatedSpectra'].append(spectrum)

    def refreshSumSpectrum(self):
        sumIntensities = numpy.zeros(self.settings['Current']['referenceSumSpectrumPoints'])
        for spectrum in self.settings['Spectra']['SimulatedSpectra']:
            sumIntensities += spectrum.spectrum.intensities
        self.settings['Current']['referenceSumSpectrum'].intensities = sumIntensities

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
