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
from Classes.Simulator import Simulator
from .pluginAddons import _addRow, _addColumn, _addVerticalSpacer, _setWidth, _setWidgetProperties


############
# Settings #
############

# Widths in pixels for nice widget alignments, length depends on the number of fixed columns in the plugin.
# Variable number of columns will take the last value in the list
columnWidths = [300]

# Set some tooltip texts
help = {'SpectrumGroup' : 'Select spectrum group',
        'Spectrum'      : 'Select spectrum',
        'MetaboliteList': 'Select the database to reference from',
        'Metabolite'    : 'Select the metabolite to add to the overlay',
        }


class ProfileByReferenceGuiPlugin(PluginModule):
    className = 'ProfileByReferenceGuiPlugin'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super(ProfileByReferenceGuiPlugin, self)
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

        self.pluginPath = os.path.join(self.project.path, ProfileByReferenceGuiPlugin.className)

        # Create ORDERED dictionary to store all parameters for the run
        # deepcopy doesn't work on dictionaries with the qt widgets, so to get a separation of gui widgets and values for storage
        # it is needed to create the two dictionaries alongside each other
        self.guiDict = OD([('Spectra', OD()), ('CoreWidgets', OD()), ('TemporaryWidgets', OD())])
        self.settings = OD([('Spectra', OD()), ('Current', OD()), ('Databases', OD()), ('Simulators', OD()), ('ResultsTables', OD())])
        self.metaboliteSimulations = OD()
        self.sumSpectra = OD()

        # # Input check
        # validInput = self._inputDataCheck()
        # if not validInput:
        #     return

        # setup database metabolite tables
        self.simulator = Simulator(self.project, '/Users/mh653/Documents/PhD/Database/Merged_Databases/merged_database.db')

        metabolites = self.simulator.caller.execute_query('select * from metabolites')

        self.metabolites = self.project.newDataTable(name='metabolites_table', data=metabolites)

        grid = (0, 4)

        # pull down list for selecting the spectrum group to overlay on
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Spectrum Group', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2),
                              callback=self._selectSpectrumGroup, tipText=help['SpectrumGroup'])
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        self.spectrumGroups = [spectrumGroup.id for spectrumGroup in sorted(self.project.spectrumGroups)]
        widget.setData(self.spectrumGroups)
        self.guiDict['CoreWidgets']['SpectrumGroupId'] = widget
        self.settings['Current']['SpectrumGroupId'] = f'SG:{self._getValue(widget)}'

        if self.spectrumGroups:
            self._selectSpectrumGroup(self.spectrumGroups[0])

        # pull down list for selecting the spectrum to overlay on
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Spectrum', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2),
                              callback=self._selectSpectrum, tipText=help['Spectrum'])
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        self.spectra = [spectrum.id for spectrum in self.project.getByPid(self.settings['Current']['SpectrumGroupId']).spectra]
        widget.setData(self.spectra)
        self.guiDict['CoreWidgets']['SpectrumId'] = widget
        self.settings['Current']['SpectrumId'] = self._getValue(widget)

        if self.spectra:
            self._selectSpectrum(self.spectra[0])

        # table widget for selecting the current metabolite by name
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Metabolite', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        df = self.metabolites.data.sort_values('name')[['name', 'hmdb_accession', 'bmrb_id', 'chemical_formula', 'average_molecular_weight', 'smiles', 'inchi', 'metabolite_id', 'description']]
        widget = Table(self.scrollAreaLayout, df=df, grid=grid, gridSpan=(1, 2), selectionCallback=self._selectMetabolite, borderWidth=4)
        _setWidgetProperties(widget, _setWidth([500], grid), 300)
        self.guiDict['CoreWidgets']['Metabolite'] = widget

        grid = _addColumn(_addColumn(grid))
        widget = Button(self.scrollAreaLayout, text='Add Unknown Signal', grid=grid, gridSpan=(1, 2), callback=self._addUnknownSignal)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['CoreWidgets']['AddUnknownSignalButton'] = widget
        self.settings['Current']['UnknownSignalCount'] = 0


        # table widget for selecting the simulation of the metabolite
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Simulation', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        df = pd.DataFrame(columns=['pH', 'amount', 'reference', 'sample_id', 'metabolite_id', 'frequency',
                                   'temperature', 'data_source', 'validation_scores', 'methods', 'spectrum_id',
                                   'origin'])
        widget = Table(self.scrollAreaLayout, df=df, grid=grid, gridSpan=(1, 2), selectionCallback=self._setupSimulatedSpectrum, borderWidth=4)
        _setWidgetProperties(widget, _setWidth([500], grid), 300)
        self.guiDict['CoreWidgets']['Simulation'] = widget

        '''Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0] + 1, 10),
               gridSpan=(1, 1))'''

    def addDoubleSpinbox(self, index, multipletId):
        def valueChange():
            shift = widget.value()
            self.simspec.moveMultiplet(multipletId, shift)
            self.refreshSumSpectrum()
        def resetMultiplet():
            widget.setValue(self.simspec.originalMultiplets[multipletId]['center'])
        def navigateToMultiplet():
            target = widget.value()
            # todo code here to move the view to the target value above
        grid = (index+8, index+8)
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Multiplet {index+1} Chemical Shift', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets'][f'Multiplet{index}Label'] = widget

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=self.simspec.multiplets[multipletId]['center'], decimals=4,
                               step=0.0001, grid=grid, gridSpan=(1, 2), suffix='ppm')
        widget.setRange(0, 10)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(valueChange)
        self.guiDict['TemporaryWidgets'][f'Multiplet{index+1}ChemicalShift'] = widget
        self.settings['Current'][f'Multiplet {index+1} Chemical Shift'] = self._getValue(widget)

        grid = _addColumn(grid)
        buttonWidget = Button(parent=self.scrollAreaLayout, text='Reset', grid=grid)
        _setWidgetProperties(buttonWidget, heightType='Minimum')
        buttonWidget.clicked.connect(resetMultiplet)
        self.guiDict['TemporaryWidgets'][f'Multiplet{index+1}Reset'] = buttonWidget

        grid = _addColumn(grid)
        buttonWidget = Button(parent=self.scrollAreaLayout, text='Navigate-to', grid=grid)
        _setWidgetProperties(buttonWidget, heightType='Minimum')
        buttonWidget.clicked.connect(navigateToMultiplet)
        self.guiDict['TemporaryWidgets'][f'Multiplet{index+1}NavigateTo'] = buttonWidget

    def widthChange(self):
        width = self.guiDict['TemporaryWidgets']['Width'].value()
        integration = self.simspec.scale * width
        self.settings['ResultsTables']['currentTable'].data.at[self.settings['Current']['currentSpectrumId'], self.settings['Current']['currentMetaboliteName']] = integration
        self.simspec.setWidth(width)
        self.refreshSumSpectrum()

    def scaleChange(self):
        scale = 10**self.guiDict['TemporaryWidgets']['Scale'].value()
        integration = scale * self.simspec.width
        self.settings['ResultsTables']['currentTable'].data.at[self.settings['Current']['currentSpectrumId'], self.settings['Current']['currentMetaboliteName']] = integration
        self.simspec.scaleSpectrum(scale)
        self.refreshSumSpectrum()

    def frequencyChange(self):
        frequency = self.guiDict['TemporaryWidgets']['Frequency'].value()
        self.simspec.setFrequency(frequency)
        self.refreshSumSpectrum()

    def globalShiftChange(self):
        shift = self.guiDict['TemporaryWidgets']['GlobalShift'].value()
        difference = shift - self.simspec.globalShift
        for widget in self.guiDict['TemporaryWidgets']:
            if widget.endswith('ChemicalShift'):
                self.guiDict['TemporaryWidgets'][widget].setValue(self.guiDict['TemporaryWidgets'][widget].value() + difference)
        self.simspec.shiftOriginalMultiplets(difference)
        self.simspec.globalShift = shift
        self.refreshSumSpectrum()

    def _selectSpectrumGroup(self, spectrumGroupID):
        spectrumGroup = self.project.getByPid('SG:' + spectrumGroupID)
        tableName = f'deconv_{spectrumGroupID}'
        if tableName not in self.settings['ResultsTables']:
            spectra = [spectrum.name for spectrum in spectrumGroup.spectra]
            tableData = pd.DataFrame(spectra, columns=['spectrum'], index=spectra)
            resultsTable = self.project.newDataTable(name=tableName, data=tableData)
            self.settings['ResultsTables'][tableName] = resultsTable
        self.settings['ResultsTables']['currentTable'] = resultsTable
        # create the simulated spectrum group
        if 'Reference_Spectra' not in self.project.spectrumGroups:
            self.settings['Current']['referenceSpectrumGroup'] = self.project.newSpectrumGroup(
                name='Reference_Spectra')

    def _selectSpectrum(self, spectrumID):
        spectrum = self.project.getByPid('SP:' + spectrumID)
        limits = (max(spectrum.positions), min(spectrum.positions))
        points = len(spectrum.positions)
        frequency = spectrum.spectrometerFrequencies[0]
        self.settings['Current']['referenceSumSpectrumLimits'] = limits
        self.settings['Current']['referenceSumSpectrumPoints'] = points
        self.settings['Current']['currentSpectrumId'] = spectrumID
        self.settings['Current']['referenceSumSpectrumFrequency'] = frequency
        x = numpy.linspace(limits[0], limits[1], points)
        y = numpy.zeros(points)
        if spectrumID not in self.sumSpectra:
            self.sumSpectra[spectrumID] = self.project.newEmptySpectrum(['1H'], name=f'Reference_Sum_{spectrumID}', intensities=y, positions=x)
            self.settings['Current']['referenceSumSpectrum'] = self.sumSpectra[spectrumID]
            self.settings['Current']['referenceSpectrumGroup'].addSpectrum(self.settings['Current']['referenceSumSpectrum'])

    def _selectMetabolite(self, newRow, previousRow, selectedRow, lastRow):
        metaboliteName = selectedRow.name.iloc[0]
        self.settings['Current']['metabolite'] = metaboliteName
        metabolite_id = selectedRow.metabolite_id.iloc[0]
        widget = self.guiDict['CoreWidgets']['Simulation']
        query = f'select * from samples natural join spectra where metabolite_id is "{metabolite_id}"'
        data = self.simulator.caller.execute_query(query)
        widget.updateDf(data)

    def _addUnknownSignal(self):
        self.settings["Current"]["UnknownSignalCount"] += 1
        self.settings['Current']['metabolite'] = f'Unknown_Signal_{self.settings["Current"]["UnknownSignalCount"]}'
        widget = self.guiDict['CoreWidgets']['Simulation']
        data = pd.DataFrame({'name': self.settings['Current']['metabolite'],
                             'metabolite_id': None,
                             'spectrum_id': None,
                             'origin': 'template'}, index=[len(self.metabolites.data)])
        widget.updateDf(data)
        data = {'name': self.settings['Current']['metabolite']}
        self.metabolites.data = self.metabolites.data.append(pd.Series(data, index=self.metabolites.data.columns[:len(data)]), ignore_index=True)
        self.guiDict['CoreWidgets']['Metabolite'].df = self.metabolites.data

    def _setupSimulatedSpectrum(self, newRow, previousRow, selectedRow, lastRow):
        metabolitesData = self.metabolites.data
        metaboliteID = selectedRow.metabolite_id.iloc[0]
        spectrumId = selectedRow.spectrum_id.iloc[0]
        origin = selectedRow.origin.iloc[0]
        if origin == 'gissmo':
            plotting = 'spinSystem'
        elif origin == 'bmrb':
            plotting = 'onlypeaks'
        elif origin == 'template':
            plotting = 'template'
        else:
            plotting = 'peaklist'
        # metaboliteName = metabolitesData.loc[metabolitesData['metabolite_id'] == metaboliteID, 'name'].iloc[0]
        metaboliteName = selectedRow.metabolite_id.iloc[0]
        self.settings['Current']['currentSimulatedSpectrumId'] = spectrumId
        self.settings['Current']['currentMetaboliteName'] = metaboliteName
        if spectrumId not in self.metaboliteSimulations:
            width = 1
            scale = 1
            globalShift = 0
            frequency = round(self.settings['Current']['referenceSumSpectrumFrequency']/10)*10
            if plotting != 'template':
                self.simspec = self.simulator.pureSpectrum(spectrumId=spectrumId, width=width, frequency=frequency, points=self.settings['Current']['referenceSumSpectrumPoints'], limits=self.settings['Current']['referenceSumSpectrumLimits'], plotting=plotting)
            else:
                self.simspec = self.simulator.blankSpectrum(frequency=frequency, points=self.settings['Current']['referenceSumSpectrumPoints'], limits=self.settings['Current']['referenceSumSpectrumLimits'])
            self.metaboliteSimulations[spectrumId] = self.simspec
            self.addSimSpectrumToList(self.simspec)
            self.settings['Current']['referenceSpectrumGroup'].addSpectrum(self.simspec.spectrum)
            self.refreshSumSpectrum()
        else:
            self.simspec = self.metaboliteSimulations[spectrumId]
            scale = log10(self.simspec.scale)
            width = self.simspec.width
            frequency = self.simspec.frequency
            globalShift = self.simspec.globalShift
        if metaboliteName not in self.settings['ResultsTables']['currentTable'].data.columns.to_list():
            column = [None] * len(self.settings['ResultsTables']['currentTable'].data)
            self.settings['ResultsTables']['currentTable'].data[metaboliteName] = column
            self.settings['ResultsTables']['currentTable'].data.at[self.settings['Current']['currentSpectrumId'], metaboliteName] = 1
        else:
            integration = scale * width
            self.settings['ResultsTables']['currentTable'].data.at[self.settings['Current']['currentSpectrumId'], metaboliteName] = integration

        for key in self.guiDict['TemporaryWidgets']:
            self.guiDict['TemporaryWidgets'][key].deleteLater()
        self.guiDict['TemporaryWidgets'] = OD()

        grid = (4, 1)
        # Add a widget for the simulated spectrum peak width
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Width', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets']['WidthLabel'] = widget

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=width, decimals=1, step=0.1, grid=grid, gridSpan=(1, 2), suffix='Hz')
        widget.setRange(0.1, 5)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.widthChange)
        self.guiDict['TemporaryWidgets']['Width'] = widget
        self.settings['Current']['Width'] = self._getValue(widget)

        # Add a widget for the simulated spectrum scale
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Scale (10^n)', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets']['ScaleLabel'] = widget

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=scale, decimals=3, step=0.001, grid=grid, gridSpan=(1, 2))
        widget.setRange(-7, 7)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.scaleChange)
        self.guiDict['TemporaryWidgets']['Scale'] = widget
        self.settings['Current']['Scale'] = self._getValue(widget)

        # Add a widget for the simulated spectrum frequency
        if origin != 'bmrb':
            grid = _addRow(grid)
            widget = Label(self.scrollAreaLayout, text=f'Frequency', grid=grid)
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            self.guiDict['TemporaryWidgets']['FrequencyLabel'] = widget

            grid = _addColumn(grid)
            widget = DoubleSpinbox(self.scrollAreaLayout, value=frequency, decimals=1, step=10,
                                   grid=grid, gridSpan=(1, 2), suffix='MHz')
            widget.setRange(10, 1200)
            _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
            widget.setButtonSymbols(2)
            widget.valueChanged.connect(self.frequencyChange)
            self.guiDict['TemporaryWidgets']['Frequency'] = widget
            self.settings['Current']['Frequency'] = self._getValue(widget)

        # Add a widget for the simulated spectrum global shift
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Global Shift', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets']['GlobalShiftLabel'] = widget

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=globalShift, decimals=4, step=0.0001,
                               grid=grid, gridSpan=(1, 2), suffix='ppm')
        widget.setRange(-1, 1)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.globalShiftChange)
        self.guiDict['TemporaryWidgets']['GlobalShift'] = widget
        self.settings['Current']['GlobalShift'] = self._getValue(widget)

        if self.simspec.multiplets:
            for index, multipletId in enumerate(self.simspec.multiplets):
                self.addDoubleSpinbox(index, multipletId)
        self.project.widgetDict = self.guiDict['TemporaryWidgets']

    def _setupTemplate(self):
        pass

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


class ProfileByReference(Plugin):
    PLUGINNAME = 'Profile by Reference'
    guiModule = ProfileByReferenceGuiPlugin
    CCPNPLUGIN = True

    def run(self, **kwargs):
        """ Insert here the script for running Tsar """
        print('Filtering noise peaks', kwargs)


ProfileByReference.register()  # Registers the pipe in the pluginList
# Set tolerances from project.spectrum.tolerances by default
