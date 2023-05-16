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
columnWidths = [200]

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
        self.guiDict = OD([('CoreWidgets', OD()), ('TemporaryWidgets', OD())])
        self.settings = OD([('CoreWidgets', OD()), ('TemporaryWidgets', OD())])
        self.current = OD()
        self.spectra = OD([('SimulatedSpectra', OD())])
        self.resultsTables = OD()
        self.metaboliteSimulations = OD()
        self.sumSpectra = OD()
        self.subSpectra = OD()

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
        self.settings['CoreWidgets']['SpectrumGroupId'] = self._getValue(widget)

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
            spectra = [spectrum.id for spectrum in self.project.getByPid(f"SG:{self.settings['CoreWidgets']['SpectrumGroupId']}").spectra]
        except:
            raise Exception("Please create a spectrum group first.")
        widget.setData(spectra)
        self.guiDict['CoreWidgets']['SpectrumId'] = widget
        self.settings['CoreWidgets']['SpectrumId'] = self._getValue(widget)

        if spectra:
            self._selectSpectrum(spectra[0])

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
        self.current['UnknownSignalCount'] = 0

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

        self.multipletUpdateStatus = True

        '''Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0] + 1, 10),
               gridSpan=(1, 1))'''

    def addDoubleSpinbox(self, index, multipletId):
        def valueChange():
            shift = widget.value()
            update = self.multipletUpdateStatus
            self.simspec.moveMultiplet(multipletId, shift, update)
            lineWidget.setValue(shift)
            self.refreshSumAndSubSpectrum()
        def lineValueChange():
            shift = lineWidget.values
            if self._getValue(widget) != shift:
                widget.setValue(shift)
        def resetMultiplet():
            widget.setValue(self.simspec.originalMultiplets[multipletId]['center'] + self.simspec.globalShift)
        def navigateToMultiplet():
            target = widget.value()
            self.project.application.current.strip.navigateToPosition([target])
        grid = (index+8, index+8)
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Multiplet {index+1} Chemical Shift', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets'][f'Multiplet{index+1}Label'] = widget

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=self.simspec.multiplets[multipletId]['center'], decimals=4,
                               step=0.0001, grid=grid, gridSpan=(1, 2))
        widget.setRange(0, 10)
        _setWidgetProperties(widget, _setWidth([200], grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(valueChange)
        self.guiDict['TemporaryWidgets'][f'Multiplet{index+1}ChemicalShift'] = widget
        self.settings['TemporaryWidgets'][f'Multiplet{index+1}ChemicalShift'] = self._getValue(widget)

        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout, text='ppm', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='l')
        self.guiDict['TemporaryWidgets'][f'Multiplet{index+1}PpmLabel'] = widget

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
        resultsTableName = f"deconv_{self.settings['CoreWidgets']['SpectrumGroupId']}"
        self.resultsTables[resultsTableName].data.at[self._getValue(self.guiDict['CoreWidgets']['SpectrumId']), self.current['CurrentMetaboliteName']] = integration
        self.simspec.setWidth(width)
        self.refreshSumAndSubSpectrum()

    def scaleChange(self):
        scale = 10**self.guiDict['TemporaryWidgets']['Scale'].value()
        integration = scale * self.simspec.width
        resultsTableName = f"deconv_{self.settings['CoreWidgets']['SpectrumGroupId']}"
        self.resultsTables[resultsTableName].data.at[self._getValue(self.guiDict['CoreWidgets']['SpectrumId']), self.current['CurrentMetaboliteName']] = integration
        self.simspec.scaleSpectrum(scale)
        self.refreshSumAndSubSpectrum()

    def frequencyChange(self):
        frequency = self.guiDict['TemporaryWidgets']['Frequency'].value()
        self.simspec.setFrequency(frequency)
        self.refreshSumAndSubSpectrum()

    def globalShiftChange(self):
        shift = self.guiDict['TemporaryWidgets']['GlobalShift'].value()
        self.settings['TemporaryWidgets']['GlobalShift'] = shift
        difference = shift - self.simspec.globalShift
        multipletWidgetList = [widget for widget in self.guiDict['TemporaryWidgets'] if widget.endswith('ChemicalShift')]
        if len(multipletWidgetList) > 0:
            self.multipletUpdateStatus = False
            for widgetNum, widget in enumerate(multipletWidgetList):
                if widgetNum+1 == len(multipletWidgetList):
                    self.multipletUpdateStatus = True
                self.guiDict['TemporaryWidgets'][widget].setValue(self.guiDict['TemporaryWidgets'][widget].value() + difference)
        else:
            self.simspec.peakList = [(peak[0]+difference, peak[1], peak[2], peak[3]) for peak in self.simspec.peakList]
            self.simspec.setSpectrumLineshape()
        self.simspec.globalShift = shift
        self.refreshSumAndSubSpectrum()

    def _selectSpectrumGroup(self, spectrumGroupID):
        self.settings['CoreWidgets']['SpectrumGroupId'] = spectrumGroupID
        spectrumGroup = self.project.getByPid('SG:' + spectrumGroupID)
        self.display = self.project.application.mainWindow.newSpectrumDisplay([spectrum for spectrum in spectrumGroup.spectra], axisCodes=('H',), stripDirection='Y', position='top', relativeTo='MO:Profile by Reference')
        self.display.rename("Profile_By_Reference_Display")
        tableName = f'deconv_{spectrumGroupID}'
        spectra = [spectrum.name for spectrum in spectrumGroup.spectra]
        if tableName not in self.resultsTables:
            tableData = pd.DataFrame(spectra, columns=['spectrum'], index=spectra)
            resultsTable = self.project.newDataTable(name=tableName, data=tableData)
            self.resultsTables[tableName] = resultsTable
        # create the simulated spectrum group
        if 'Reference_Spectra' not in self.project.spectrumGroups:
            self.spectra['ReferenceSpectrumGroup'] = self.project.newSpectrumGroup(
                name='Reference_Spectra')
        for spectrumId in spectra:
            spectrum = self.project.getByPid('SP:' + spectrumId)
            limits = (max(spectrum.positions), min(spectrum.positions))
            points = len(spectrum.positions)
            frequency = spectrum.spectrometerFrequencies[0]
            x = numpy.linspace(limits[0], limits[1], points)
            y = numpy.zeros(points)
            if spectrumId not in self.sumSpectra:
                self.sumSpectra[spectrumId] = self.project.newEmptySpectrum(['1H'], name=f"Sum_Reference_{spectrumId}",
                                                                            intensities=y, positions=x,
                                                                            spectrometerFrequencies=[frequency])
            if spectrumId not in self.subSpectra:
                self.subSpectra[spectrumId] = self.project.newEmptySpectrum(['1H'], name=f"Subtraction_Reference_{spectrumId}",
                                                                            intensities=y, positions=x,
                                                                            spectrometerFrequencies=[frequency])

    def _selectSpectrum(self, spectrumId):
        self.settings['CoreWidgets']['SpectrumId'] = spectrumId
        spectrum = self.project.getByPid('SP:' + spectrumId)
        limits = (max(spectrum.positions), min(spectrum.positions))
        points = len(spectrum.positions)
        frequency = spectrum.spectrometerFrequencies[0]
        self.current['ActiveSpectrum'] = spectrum
        self.current['ActiveSpectrumScale'] = log10(numpy.mean(spectrum.intensities[spectrum.intensities > 1]))
        self.current['ReferenceSumSpectrumLimits'] = limits
        self.current['ReferenceSumSpectrumPoints'] = points
        self.current['ReferenceSumSpectrumFrequency'] = frequency

    def _selectMetabolite(self, newRow, previousRow, selectedRow, lastRow):
        metaboliteName = selectedRow.name.iloc[0]
        self.current['metabolite'] = metaboliteName
        self.current['metaboliteData'] = selectedRow
        metabolite_id = selectedRow.metabolite_id.iloc[0]
        widget = self.guiDict['CoreWidgets']['Simulation']
        data = self.caller.getSpectra(metabolite_id)
        widget.updateDf(data)

    def _addUnknownSignal(self):
        self.current['UnknownSignalCount'] += 1
        self.current['metabolite'] = f"Unknown_Substance_{self.current['UnknownSignalCount']}"
        widget = self.guiDict['CoreWidgets']['Simulation']
        data = pd.DataFrame({'name': self.current['metabolite'],
                             'metabolite_id': None,
                             'spectrum_id': None,
                             'origin': 'unknown_substance'}, index=[len(self.metabolites.data)])
        widget.updateDf(data)
        data = {'name': self.current['metabolite']}
        row = pd.DataFrame(data, columns=self.metabolites.data.columns, index=[len(self.metabolites.data)])
        self.metabolites.data = pd.concat([self.metabolites.data, row])
        df = self.metabolites.data.sort_values('name')[
            ['name', 'hmdb_accession', 'bmrb_id', 'chemical_formula', 'average_molecular_weight', 'smiles', 'inchi',
             'metabolite_id', 'description']]
        self.guiDict['CoreWidgets']['Metabolite'].updateDf(df)
        self.current['metaboliteData'] = row

    def _setupSimulatedSpectrum(self, newRow, previousRow, selectedRow, lastRow):
        metaboliteData = self.current['metaboliteData']
        metaboliteID = selectedRow.metabolite_id.iloc[0]
        spectrumId = selectedRow.spectrum_id.iloc[0]
        origin = selectedRow.origin.iloc[0]
        metaboliteName = metaboliteData.name.iloc[0]
        spectrumType = selectedRow.spectrum_type.iloc[0]
        self.current['CurrentSimulatedSpectrumId'] = spectrumId
        self.current['CurrentMetaboliteName'] = metaboliteName
        if spectrumId not in self.metaboliteSimulations:
            width = 1
            scale = self.current['ActiveSpectrumScale']
            globalShift = 0
            if spectrumType == 'spin_system':
                frequency = round(self.current['ReferenceSumSpectrumFrequency']/10)*10
            else:
                frequency = round(float(selectedRow.frequency.iloc[0])/10)*10
            if origin != 'unknown_substance':
                simulationData = self.caller.getSimulationData(spectrumId)
                sampleData = self.caller.getSampleData(simulationData['SpectrumData'].sample_id.iloc[0])
                spectrumData = simulationData['SpectrumData']
                synonyms = ([synonym for synonym in self.caller.getSynonymData(metaboliteID).synonym])
                self.simspec = self.simulator.spectrumFromDatabase(simulationData, points=self.current['ReferenceSumSpectrumPoints'], limits=self.current['ReferenceSumSpectrumLimits'])
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
                self.simspec = self.simulator.spectrumFromScratch(frequency=frequency, points=self.current['ReferenceSumSpectrumPoints'], limits=self.current['ReferenceSumSpectrumLimits'])
                self.simulator.buildCcpnObjects(self.simspec, metaboliteName, frequency)
            self.metaboliteSimulations[spectrumId] = self.simspec
            self.addSimSpectrumToList(self.simspec)
            self.spectra['ReferenceSpectrumGroup'].addSpectrum(self.simspec.spectrum)
            self.refreshSumAndSubSpectrum()
        else:
            self.simspec = self.metaboliteSimulations[spectrumId]
            scale = log10(self.simspec.scale)
            width = self.simspec.width
            frequency = self.simspec.frequency
            globalShift = self.simspec.globalShift
        resultsTableName = f"deconv_{self.settings['CoreWidgets']['SpectrumGroupId']}"
        if metaboliteName not in self.resultsTables[resultsTableName].data.columns.to_list():
            column = [None] * len(self.resultsTables[resultsTableName].data)
            self.resultsTables[resultsTableName].data[metaboliteName] = column
            self.resultsTables[resultsTableName].data.at[self.settings['CoreWidgets']['SpectrumId'], metaboliteName] = 1
        else:
            integration = scale * width
            self.resultsTables[resultsTableName].data.at[self.settings['CoreWidgets']['SpectrumId'], metaboliteName] = integration
        self.display.displaySpectrum(spectrum=self.simspec.spectrum.pid)

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
        widget = DoubleSpinbox(self.scrollAreaLayout, value=width, decimals=1, step=0.1, grid=grid, gridSpan=(1, 2))
        widget.setRange(0.1, 5)
        _setWidgetProperties(widget, _setWidth([200], grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.widthChange)
        self.guiDict['TemporaryWidgets']['Width'] = widget
        self.current['Width'] = self._getValue(widget)

        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout, text='Hz', grid=grid)
        _setWidgetProperties(widget, _setWidth([200], grid), hAlign='l')
        self.guiDict['TemporaryWidgets']['WidthHzLabel'] = widget

        # Add a widget for the simulated spectrum scale
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Scale (10^n)', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets']['ScaleLabel'] = widget

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=scale, decimals=3, step=0.001, grid=grid, gridSpan=(1, 2))
        widget.setRange(-7, 7)
        _setWidgetProperties(widget, _setWidth([200], grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.scaleChange)
        self.guiDict['TemporaryWidgets']['Scale'] = widget
        self.current['Scale'] = self._getValue(widget)
        self.scaleChange()

        # Add a widget for the simulated spectrum frequency
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Frequency', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets']['FrequencyLabel'] = widget

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=frequency, decimals=1, step=10,
                               grid=grid, gridSpan=(1, 2))
        widget.setRange(10, 1200)
        _setWidgetProperties(widget, _setWidth([200], grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.frequencyChange)
        self.guiDict['TemporaryWidgets']['Frequency'] = widget
        self.current['Frequency'] = self._getValue(widget)
        if spectrumType != 'spin_system':
            widget.setEnabled(False)

        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout, text='MHz', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='l')
        self.guiDict['TemporaryWidgets']['FrequencyMHzLabel'] = widget

        # Add a widget for the simulated spectrum global shift
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Global Shift', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict['TemporaryWidgets']['GlobalShiftLabel'] = widget

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=globalShift, decimals=4, step=0.0001,
                               grid=grid, gridSpan=(1, 2))
        widget.setRange(-10, 10)
        _setWidgetProperties(widget, _setWidth([200], grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.globalShiftChange)
        self.guiDict['TemporaryWidgets']['GlobalShift'] = widget
        self.settings['TemporaryWidgets']['GlobalShift'] = self._getValue(widget)

        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout, text='ppm', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='l')
        self.guiDict['TemporaryWidgets']['GlobalShiftPpmLabel'] = widget

        if self.simspec.multiplets and origin != 'unknown_substance':
            for index, multipletId in enumerate(self.simspec.multiplets):
                self.addDoubleSpinbox(index, multipletId)
            if origin == 'bmrb':
                for widget in [widget for widget in self.guiDict['TemporaryWidgets'] if 'Multiplet' in widget]:
                    self.guiDict['TemporaryWidgets'][widget].setUpdatesEnabled(False)
                    self.guiDict['TemporaryWidgets'][widget].setEnabled(False)
        else:
            grid = _addColumn(grid)
            self.current['Grid'] = grid
            self.current['SignalCount'] = 0
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
            lineWidget.setValue(shift)
            self.refreshSumAndSubSpectrum()
        def heightChange():
            height = heightWidget.value()
            self.simspec.scaleMultiplet(str(count), height)
            self.refreshSumAndSubSpectrum()
        def lineValueChange():
            shift = lineWidget.values
            if self._getValue(shiftWidget) != shift:
                shiftWidget.setValue(shift)

        grid = self.current['Grid']
        grid = _addRow(grid)

        if 'UnknownSignalChemicalShiftLabel' not in self.guiDict['TemporaryWidgets']:
            grid = _addRow(grid)
            grid = _addColumn(grid)
            widget = Label(self.scrollAreaLayout, text=f'Chemical Shift (ppm)', grid=grid)
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            self.guiDict['TemporaryWidgets']['UnknownSignalChemicalShiftLabel'] = widget
            grid = _addColumn(grid)
            widget = Label(self.scrollAreaLayout, text=f'Relative Intensity', grid=grid)
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            self.guiDict['TemporaryWidgets']['UnknownSignalRelativeIntensityLabel'] = widget
            grid = _addRow(grid)

        self.current['Grid'] = grid
        count = self.current['SignalCount'] + 1
        self.current['SignalCount'] = count
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
        self.current[f'Signal_{count}_Shift'] = self._getValue(shiftWidget)
        self.guiDict['TemporaryWidgets'][f'Signal_{count}_ChemicalShift'] = shiftWidget

        grid = _addColumn(grid)
        heightWidget = DoubleSpinbox(self.scrollAreaLayout, value=1, decimals=2, step=0.01, grid=grid, gridSpan=(1, 1))
        heightWidget.setRange(-7, 7)
        _setWidgetProperties(heightWidget, _setWidth(columnWidths, grid), hAlign='r')
        heightWidget.valueChanged.connect(heightChange)
        self.current[f'Signal_{count}_Height'] = self._getValue(heightWidget)
        self.guiDict['TemporaryWidgets'][f'Signal_{count}_Height'] = heightWidget

        brush = hexToRgbRatio(self.simspec.spectrum.sliceColour) + (0.3,)
        lineWidget = self.display.strips[0]._CcpnGLWidget.addInfiniteLine(
            values=self.simspec.multiplets[str(count)]['center'], colour=brush, movable=True, lineStyle='dashed',
            lineWidth=2.0, obj=self.simspec.spectrum, orientation='v', )
        lineWidget.valuesChanged.connect(lineValueChange)
        self.guiDict['TemporaryWidgets'][f'Multiplet{count}Line'] = lineWidget

    def _addSignalFromPeaks(self):
        if len(self.current['ActiveSpectrum'].multiplets) > 0:
            peakList = []
            for i, multiplet in enumerate(self.current['ActiveSpectrum'].multiplets):
                for peak in multiplet.peaks:
                    peakList.append((peak.position[0], peak.height/(10**self.current['Scale']), self.simspec.width/self.simspec.frequency, str(i)))
        else:
            peakList = [(peak.position[0], peak.height/(10**self.current['Scale']), self.simspec.width/self.simspec.frequency, '1') for peak in self.current['ActiveSpectrum'].peaks]
        if len(peakList) < 1:
            raise Exception(f"Please pick at least one peak in spectrum {self.current['ActiveSpectrum'].pid}")
        self.simspec.peakList = peakList
        self.simspec.setSpectrumLineshape()
        self.refreshSumAndSubSpectrum()

    def addSimSpectrumToList(self, spectrum):
        spectrumId = self.settings['CoreWidgets']['SpectrumId']
        if 'SimulatedSpectra' not in self.spectra['SimulatedSpectra']:
            self.spectra['SimulatedSpectra'][spectrumId] = [spectrum]
        else:
            self.spectra['SimulatedSpectra'][spectrumId].append(spectrum)

    def refreshSumAndSubSpectrum(self):
        spectrumId = self.settings['CoreWidgets']['SpectrumId']
        realSpectrum = self.project.getByPid('SP:' + spectrumId)
        sumIntensities = numpy.zeros(self.current['ReferenceSumSpectrumPoints'])
        for simulatedSpectrum in self.spectra['SimulatedSpectra'][spectrumId]:
            sumIntensities += simulatedSpectrum.spectrum.intensities
        self.sumSpectra[spectrumId].intensities = sumIntensities
        self.subSpectra[spectrumId].intensities = realSpectrum.intensities - sumIntensities

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
