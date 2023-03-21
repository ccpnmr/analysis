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
from ccpn.util.nef import GenericStarParser, StarIo
from ccpn.util.nef.GenericStarParser import SaveFrame, DataBlock, DataExtent, Loop, LoopRow
from functools import partial
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.util.decorators import logCommand
from Classes.Simulator_rework import Simulator
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
        self.guiDict = OD([('Spectrum', OD())])
        self.settings = OD([('Spectrum', OD()), ('Databases', OD()), ('Simulators', OD())])
        self.metaboliteSimulations = OD()
        self.sumSpectra = OD()

        # # Input check
        # validInput = self._inputDataCheck()
        # if not validInput:
        #     return

        # setup database metabolite tables
        self.settings['Simulators']['HMDB'] = Simulator(self.project, '/Users/mh653/Documents/PhD/Database/Remediated_Databases/ccpn_metabolites_hmdb.db')
        self.settings['Simulators']['BMRB'] = Simulator(self.project, '/Users/mh653/Documents/PhD/Database/Remediated_Databases/ccpn_metabolites_bmrb.db')
        self.settings['Simulators']['GISSMO'] = Simulator(self.project, '/Users/mh653/Documents/PhD/Database/Remediated_Databases/ccpn_metabolites_gissmo.db')

        hmdb_metabolites = self.settings['Simulators']['HMDB'].caller.execute_query('select metabolite_id, name, hmdb_accession, '
                                                               'chemical_formula, average_molecular_weight, smiles, '
                                                               'inchi from metabolites')
        bmrb_metabolites = self.settings['Simulators']['BMRB'].caller.execute_query('select distinct metabolite_id, name, accession, '
                                                               'chemical_formula, average_molecular_weight, smiles, '
                                                               'inchi from metabolites natural join samples')
        gissmo_metabolites = self.settings['Simulators']['GISSMO'].caller.execute_query('select metabolite_id, name, inchi from metabolites')

        self.settings['Databases']['HMDB'] = self.project.newDataTable(name='hmdb_metabolites_table', data=hmdb_metabolites)
        self.settings['Databases']['BMRB'] = self.project.newDataTable(name='bmrb_metabolites_table', data=bmrb_metabolites)
        self.settings['Databases']['GISSMO'] = self.project.newDataTable(name='gissmo_metabolites_table', data=gissmo_metabolites)

        grid = (0, 0)
        self.guiDict['Spectrum']['SimulatedSpectrumAttributes'] = []

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
        self.guiDict['Spectrum']['SpectrumGroupId'] = widget
        self.settings['Spectrum']['SpectrumGroupId'] = f'SG:{self._getValue(widget)}'

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

        self.spectrumGroups = [spectrumGroup.id for spectrumGroup in sorted(self.project.spectrumGroups)]
        self.spectra = [spectrum.id for spectrum in self.project.getByPid(self.settings['Spectrum']['SpectrumGroupId']).spectra]
        widget.setData(self.spectra)
        self.guiDict['Spectrum']['SpectrumId'] = widget
        self.settings['Spectrum']['SpectrumId'] = self._getValue(widget)

        # pull down list for selecting the database to reference from
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Database', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2),
                              callback=self._selectMetaboliteList, tipText=help['MetaboliteList'])
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        databaseTables = list(self.settings['Simulators'].keys())
        widget.setData(databaseTables)
        self.guiDict['Spectrum']['dataTableID'] = widget
        self.settings['Spectrum']['dataTableID'] = self._getValue(widget)

        # pull down list for selecting the current metabolite from the database
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Metabolite', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2),
                              callback=self._setupNewMetabolite, tipText=help['Metabolite'])
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        self.guiDict['Spectrum']['metabolite'] = widget
        self.settings['Spectrum']['metabolite'] = self._getValue(widget)

        '''# Action buttons: Filter creates a new filtered peak list
        grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
        grid = _addColumn(grid)
        grid = _addColumn(grid)
        texts = ['Filter']
        tipTexts = [help['Filter']]
        callbacks = [self.filterNoiseButton]
        widget = ButtonList(parent=self.scrollAreaLayout, texts=texts, callbacks=callbacks, tipTexts=tipTexts, grid=grid)
        _setWidgetProperties(widget, heightType='Minimum')'''

        '''Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0] + 1, 10),
               gridSpan=(1, 1))'''

    def addDoubleSpinbox(self, index):
        def valueChange():
            shift = widget.value()
            self.simspec.moveSpinSystemMultiplet(index, shift)
            self.refreshSumSpectrum()
        grid = (index+7, index+7)
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Multiplet {index+1} Chemical Shift', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict[f'Spectrum']['SimulatedSpectrumAttributes'].append(widget)

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=self.simspec.spinSystemMatrix[index][index], decimals=4,
                               step=0.0001, grid=grid, gridSpan=(1, 2), suffix='ppm')
        widget.setRange(0, 10)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(valueChange)

        self.guiDict[f'Spectrum']['SimulatedSpectrumAttributes'].append(widget)
        self.settings['Spectrum'][f'Multiplet {index+1} Chemical Shift'] = self._getValue(widget)

    def widthChange(self):
        width = self.guiDict['Spectrum']['Width'].value()/self.guiDict['Spectrum']['Frequency'].value()
        self.simspec.setWidth(width)
        self.refreshSumSpectrum()

    def scaleChange(self):
        scale = 10**self.guiDict['Spectrum']['Scale'].value()
        self.simspec.scaleSpectrum(scale)
        self.refreshSumSpectrum()

    def frequencyChange(self):
        frequency = self.guiDict['Spectrum']['Frequency'].value()
        self.simspec.setFrequency(frequency)
        self.refreshSumSpectrum()

    def _selectSpectrumGroup(self, spectrumGroupID):
        spectrumGroup = self.project.getByPid('SG:' + spectrumGroupID)
        valuesColumns = ['Metabolite Name', 'Database'] + [spectrum.name for spectrum in spectrumGroup.spectra]
        self.values = pandas.DataFrame(columns=valuesColumns)
        # create the simulated spectrum group
        if 'Reference_Spectra' not in self.project.spectrumGroups:
            self.settings['Spectrum']['referenceSpectrumGroup'] = self.project.newSpectrumGroup(
                name='Reference_Spectra')

    def _selectSpectrum(self, spectrumID):
        spectrum = self.project.getByPid('SP:' + spectrumID)
        limits = (max(spectrum.positions), min(spectrum.positions))
        points = len(spectrum.positions)
        self.settings['Spectrum']['referenceSumSpectrumLimits'] = limits
        self.settings['Spectrum']['referenceSumSpectrumPoints'] = points
        x = numpy.linspace(limits[0], limits[1], points)
        y = numpy.zeros(points)
        if spectrumID not in self.sumSpectra:
            self.sumSpectra[spectrumID] = self.project.newEmptySpectrum(['1H'], name=f'Reference_Sum_{spectrumID}', intensities=y, positions=x)
            self.settings['Spectrum']['referenceSumSpectrum'] = self.sumSpectra[spectrumID]
            self.settings['Spectrum']['referenceSpectrumGroup'].addSpectrum(self.settings['Spectrum']['referenceSumSpectrum'])

    def _selectMetaboliteList(self, databaseName):
        databaseTable = self.settings['Databases'][databaseName]
        widget = self.guiDict['Spectrum']['metabolite']
        metaboliteNames = databaseTable.data.sort_values('name').name.tolist()
        widget.setData(metaboliteNames)
        self.settings['Spectrum']['metabolite'] = self._getValue(widget)
        self.settings['Spectrum']['currentDatabase'] = databaseName

    def _setupNewMetabolite(self, metaboliteName):
        currentDatabase = self.settings['Spectrum']['currentDatabase']
        metabolitesData = self.settings['Databases'][currentDatabase].data
        metaboliteID = metabolitesData.loc[metabolitesData['name'] == metaboliteName].metabolite_id.iloc[0]
        if metaboliteName not in self.metaboliteSimulations:
            self.simspec = self.settings['Simulators'][currentDatabase].pure_spectrum(metabolite_id=metaboliteID, width=0.002, frequency=700, points=self.settings['Spectrum']['referenceSumSpectrumPoints'], limits=self.settings['Spectrum']['referenceSumSpectrumLimits'], plotting='spin_system')[0]
            self.metaboliteSimulations[metaboliteName] = self.simspec
            self.addSimSpectrumToList(self.simspec)
            self.settings['Spectrum']['referenceSpectrumGroup'].addSpectrum(self.simspec.spectrum)
            self.refreshSumSpectrum()
        else:
            self.simspec = self.metaboliteSimulations[metaboliteName]

        if self.guiDict['Spectrum']['SimulatedSpectrumAttributes']:
            for widget in self.guiDict['Spectrum']['SimulatedSpectrumAttributes']:
                widget.deleteLater()
            self.guiDict['Spectrum']['SimulatedSpectrumAttributes'] = []

        grid = (4, 1)
        # Add a widget for the simulated spectrum peak width
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Width', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict[f'Spectrum']['SimulatedSpectrumAttributes'].append(widget)

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=1, decimals=1, step=0.1, grid=grid, gridSpan=(1, 2))
        widget.setRange(0.1, 5)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.widthChange)
        self.guiDict['Spectrum']['SimulatedSpectrumAttributes'].append(widget)
        self.guiDict['Spectrum']['Width'] = widget
        self.settings['Spectrum']['Width'] = self._getValue(widget)

        # Add a widget for the simulated spectrum scale
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Scale', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict[f'Spectrum']['SimulatedSpectrumAttributes'].append(widget)

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=1, decimals=3, step=0.001, grid=grid, gridSpan=(1, 2))
        widget.setRange(-7, 7)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.scaleChange)
        self.guiDict['Spectrum']['SimulatedSpectrumAttributes'].append(widget)
        self.guiDict['Spectrum']['Scale'] = widget
        self.settings['Spectrum']['Scale'] = self._getValue(widget)

        # Add a widget for the simulated spectrum frequency
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Frequency', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict[f'Spectrum']['SimulatedSpectrumAttributes'].append(widget)

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=self.simspec.frequency, decimals=1, step=10,
                               grid=grid,
                               gridSpan=(1, 2))
        widget.setRange(100, 1200)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.frequencyChange)
        self.guiDict['Spectrum']['SimulatedSpectrumAttributes'].append(widget)
        self.guiDict['Spectrum']['Frequency'] = widget
        self.settings['Spectrum']['Frequency'] = self._getValue(widget)

        for index in range(len(self.simspec.spinSystemMatrix)):
            self.addDoubleSpinbox(index)
        self.project.widgetList = self.guiDict['Spectrum']['SimulatedSpectrumAttributes']

    def addSimSpectrumToList(self, spectrum):
        if 'SimulatedSpectra' not in self.settings['Spectrum']:
            self.settings['Spectrum']['SimulatedSpectra'] = [spectrum]
        else:
            self.settings['Spectrum']['SimulatedSpectra'].append(spectrum)

    def refreshSumSpectrum(self):
        sumIntensities = numpy.zeros(self.settings['Spectrum']['referenceSumSpectrumPoints'])
        for spectrum in self.settings['Spectrum']['SimulatedSpectra']:
            sumIntensities += spectrum.spectrum.intensities
        self.settings['Spectrum']['referenceSumSpectrum'].intensities = sumIntensities

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
