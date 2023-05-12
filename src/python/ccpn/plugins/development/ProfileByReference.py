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
from Classes.DatabaseCaller import DatabaseCaller
from .pluginAddons import _addRow, _addColumn, _addVerticalSpacer, _setWidth, _setWidgetProperties
from ccpn.util.Colour import hexToRgbRatio
from ccpn.ui.gui.widgets.SettingsWidgets import SpectrumDisplaySelectionWidget


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
        self.simulator = Simulator(self.project)
        self.caller = DatabaseCaller('/Users/mh653/Documents/PhD/Database/Merged_Databases/merged_database.db')

        metabolites = self.caller.execute_query('select * from metabolites')

        if 'DT:metabolites_table' not in [dataTable.pid for dataTable in self.project.dataTables]:
            self.metabolites = self.project.newDataTable(name='metabolites_table', data=metabolites)
        else:
            self.metabolites = self.project.application.get('DT:metabolites_table')

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


        try:
            self.spectra = [spectrum.id for spectrum in self.project.getByPid(self.settings['Current']['SpectrumGroupId']).spectra]
        except:
            raise Exception("Please create a spectrum group first.")
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

        self.settings['Current']['MultipletUpdateStatus'] = True

        '''Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0] + 1, 10),
               gridSpan=(1, 1))'''

    def addDoubleSpinbox(self, index, multipletId):
        def valueChange():
            shift = widget.value()
            update = self.settings['Current']['MultipletUpdateStatus']
            self.simspec.moveMultiplet(multipletId, shift, update)
            self.refreshSumSpectrum()
        def lineValueChange():
            shift = lineWidget.values
            widget.setValue(shift)
        def resetMultiplet():
            widget.setValue(self.simspec.originalMultiplets[multipletId]['center'] + self.simspec.globalShift)
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

        brush = hexToRgbRatio(self.simspec.spectrum.sliceColour) + (0.3,)
        lineWidget = self.display.strips[0]._CcpnGLWidget.addInfiniteLine(values=self.simspec.multiplets[multipletId]['center'], colour=brush, movable=True, lineStyle='dashed',
                                                   lineWidth=2.0, obj=self.simspec.spectrum, orientation='v',)
        lineWidget.valuesChanged.connect(lineValueChange)
        self.guiDict['TemporaryWidgets'][f'Multiplet{index + 1}Line'] = lineWidget

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
        multipletWidgetList = [widget for widget in self.guiDict['TemporaryWidgets'] if widget.endswith('ChemicalShift')]
        if len(multipletWidgetList) > 0:
            self.settings['Current']['MultipletUpdateStatus'] = False
            for widgetNum, widget in enumerate(multipletWidgetList):
                if widgetNum+1 == len(multipletWidgetList):
                    self.settings['Current']['MultipletUpdateStatus'] = True
                self.guiDict['TemporaryWidgets'][widget].setValue(self.guiDict['TemporaryWidgets'][widget].value() + difference)
        else:
            self.simspec.globalShift(difference)
        self.simspec.globalShift = shift
        self.refreshSumSpectrum()

    def _selectSpectrumGroup(self, spectrumGroupID):
        spectrumGroup = self.project.getByPid('SG:' + spectrumGroupID)
        self.display = self.project.application.mainWindow.newSpectrumDisplay([spectrum for spectrum in spectrumGroup.spectra], axisCodes=('H',), stripDirection='Y', position='top', relativeTo='MO:Profile by Reference')
        self.display.rename("Profile_By_Reference_Display")
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
        self.settings['Current']['ActiveSpectrum'] = spectrum
        self.settings['Current']['ActiveSpectrumScale'] = log10(numpy.mean(spectrum.intensities[spectrum.intensities > 1]))
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
        self.settings['Current']['metaboliteData'] = selectedRow
        metabolite_id = selectedRow.metabolite_id.iloc[0]
        widget = self.guiDict['CoreWidgets']['Simulation']
        data = self.caller.getSpectra(metabolite_id)
        widget.updateDf(data)

    def _addUnknownSignal(self):
        self.settings["Current"]["UnknownSignalCount"] += 1
        self.settings['Current']['metabolite'] = f'Unknown_Substance_{self.settings["Current"]["UnknownSignalCount"]}'
        widget = self.guiDict['CoreWidgets']['Simulation']
        data = pd.DataFrame({'name': self.settings['Current']['metabolite'],
                             'metabolite_id': None,
                             'spectrum_id': None,
                             'origin': 'unknown_substance'}, index=[len(self.metabolites.data)])
        widget.updateDf(data)
        data = {'name': self.settings['Current']['metabolite']}
        row = pd.DataFrame(data, columns=self.metabolites.data.columns, index=[len(self.metabolites.data)])
        self.metabolites.data = pd.concat([self.metabolites.data, row])
        df = self.metabolites.data.sort_values('name')[
            ['name', 'hmdb_accession', 'bmrb_id', 'chemical_formula', 'average_molecular_weight', 'smiles', 'inchi',
             'metabolite_id', 'description']]
        self.guiDict['CoreWidgets']['Metabolite'].updateDf(df)
        self.settings['Current']['metaboliteData'] = row

    def _setupSimulatedSpectrum(self, newRow, previousRow, selectedRow, lastRow):
        metaboliteData = self.settings['Current']['metaboliteData']
        metaboliteID = selectedRow.metabolite_id.iloc[0]
        spectrumId = selectedRow.spectrum_id.iloc[0]
        origin = selectedRow.origin.iloc[0]
        metaboliteName = metaboliteData.name.iloc[0]
        self.settings['Current']['currentSimulatedSpectrumId'] = spectrumId
        self.settings['Current']['currentMetaboliteName'] = metaboliteName
        if spectrumId not in self.metaboliteSimulations:
            width = 1
            scale = self.settings['Current']['ActiveSpectrumScale']
            globalShift = 0
            frequency = round(self.settings['Current']['referenceSumSpectrumFrequency']/10)*10
            if origin != 'unknown_substance':
                simulationData = self.caller.getSimulationData(spectrumId)
                sampleData = self.caller.getSampleData(simulationData['SpectrumData'].sample_id.iloc[0])
                spectrumData = simulationData['SpectrumData']
                synonyms = ([synonym for synonym in self.caller.getSynonymData(metaboliteID).synonym])
                self.simspec = self.simulator.spectrumFromDatabase(simulationData, points=self.settings['Current']['referenceSumSpectrumPoints'], limits=self.settings['Current']['referenceSumSpectrumLimits'])
                self.simulator.buildCcpnObjects(self.simspec, metaboliteName=f"{metaboliteName}_{origin}_{simulationData['SpectrumData'].spectrum_type.iloc[0]}",
                                                frequency=spectrumData.frequency.iloc[0],
                                                temperature=spectrumData.temperature.iloc[0], pH=sampleData.pH.iloc[0],
                                                smiles=metaboliteData.smiles.iloc[0],
                                                inChi=metaboliteData.inchi.iloc[0],
                                                empiricalFormula=metaboliteData.chemical_formula.iloc[0],
                                                molecularMass=metaboliteData.average_molecular_weight.iloc[0],
                                                synonyms=synonyms, description=metaboliteData.description.iloc[0])
                if simulationData['SpectrumData'].spectrum_type.iloc[0] == 'spin_system':
                    self.simspec.setFrequency(frequency)
            else:
                self.simspec = self.simulator.spectrumFromScratch(frequency=frequency, points=self.settings['Current']['referenceSumSpectrumPoints'], limits=self.settings['Current']['referenceSumSpectrumLimits'])
                self.simulator.buildCcpnObjects(self.simspec, metaboliteName, frequency)
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
            if 'Line' in key:
                self.display.strips[0]._CcpnGLWidget.removeInfiniteLine(self.guiDict['TemporaryWidgets'][key])
            else:
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
        self.scaleChange()

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

        if self.simspec.multiplets and origin != 'unknown_substance':
            for index, multipletId in enumerate(self.simspec.multiplets):
                self.addDoubleSpinbox(index, multipletId)
            if origin == 'bmrb':
                for widget in [widget for widget in self.guiDict['TemporaryWidgets'] if 'Multiplet' in widget]:
                    self.guiDict['TemporaryWidgets'][widget].setUpdatesEnabled(False)
                    self.guiDict['TemporaryWidgets'][widget].setEnabled(False)
        else:
            grid = _addColumn(grid)
            self.settings['Current']['Grid'] = grid
            self.settings['Current']['SignalCount'] = 0
            buttonWidget = Button(parent=self.scrollAreaLayout, text='Add Signal From Scratch', grid=grid, callback=self._addSignalFromScratch)
            _setWidgetProperties(buttonWidget, heightType='Minimum')
            self.guiDict['TemporaryWidgets'][f'AddSignalFromScratch'] = buttonWidget

            grid = _addColumn(grid)
            buttonWidget = Button(parent=self.scrollAreaLayout, text='Add Signal From Peaks', grid=grid,
                                  callback=self._addSignalFromPeaks)
            _setWidgetProperties(buttonWidget, heightType='Minimum')
            self.guiDict['TemporaryWidgets'][f'AddSignalFromPeaks'] = buttonWidget
        self.project.widgetDict = self.guiDict['TemporaryWidgets']

    def _addSignalFromScratch(self):
        def shiftChange():
            shift = shiftWidget.value()
            self.simspec.moveMultiplet(str(count), shift)
            self.refreshSumSpectrum()
        def heightChange():
            height = 10 ** heightWidget.value()
            self.simspec.scaleMultiplet(str(count), height)
            self.refreshSumSpectrum()
        grid = self.settings['Current']['Grid']
        grid = _addRow(grid)
        self.settings['Current']['Grid'] = grid
        count = self.settings['Current']['SignalCount'] + 1
        self.settings['Current']['SignalCount'] = count
        self.simspec.multiplets[f'{count}'] = {'center': 0, 'indices': [count-1]}
        self.simspec.peakList.append((0, 1, self.simspec.width/self.simspec.frequency, str(count)))

        labelWidget = Label(self.scrollAreaLayout, text=f'Signal_{count}', grid=grid)
        _setWidgetProperties(labelWidget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets'][f'Signal_{count}_label'] = labelWidget

        grid = _addColumn(grid)
        shiftWidget = DoubleSpinbox(self.scrollAreaLayout, value=0, decimals=4, step=0.0001, grid=grid, gridSpan=(1, 1))
        shiftWidget.setRange(0, 10)
        _setWidgetProperties(shiftWidget, _setWidth(columnWidths, grid), hAlign='r')
        shiftWidget.valueChanged.connect(shiftChange)
        self.settings['Current'][f'Signal_{count}_Shift'] = self._getValue(shiftWidget)
        self.guiDict['TemporaryWidgets'][f'Signal_{count}_Shift'] = shiftWidget

        grid = _addColumn(grid)
        heightWidget = DoubleSpinbox(self.scrollAreaLayout, value=0, decimals=3, step=0.001, grid=grid, gridSpan=(1, 1))
        heightWidget.setRange(-7, 7)
        _setWidgetProperties(heightWidget, _setWidth(columnWidths, grid), hAlign='r')
        heightWidget.valueChanged.connect(heightChange)
        self.settings['Current'][f'Signal_{count}_Height'] = self._getValue(heightWidget)
        self.guiDict['TemporaryWidgets'][f'Signal_{count}_Height'] = heightWidget

    def _addSignalFromPeaks(self):
        if len(self.settings['Current']['ActiveSpectrum'].multiplets) > 0:
            peakList = []
            for i, multiplet in enumerate(self.settings['Current']['ActiveSpectrum'].multiplets):
                for peak in multiplet.peaks:
                    peakList.append((peak.position[0], peak.height/(10**self.settings['Current']['Scale']), self.simspec.width/self.simspec.frequency, str(i)))
        else:
            peakList = [(peak.position[0], peak.height/(10**self.settings['Current']['Scale']), self.simspec.width/self.simspec.frequency, '1') for peak in self.settings['Current']['ActiveSpectrum'].peaks]
        if len(peakList) < 1:
            raise Exception(f"Please pick at least one peak in spectrum {self.settings['Current']['ActiveSpectrum'].pid}")
        self.simspec.peakList = peakList
        self.simspec.setSpectrumLineshape()

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
