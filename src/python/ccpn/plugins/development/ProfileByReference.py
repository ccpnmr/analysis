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
help = {'Spectrum'        : 'Select spectrum',
        'Peak list'       : 'Peak list to filter noise',
        'Reference peaks' : 'Estimated number of peaks to use as reference. Minimum 10. Set to about 50% of expected real peaks in the spectrum.',
        'Threshold factor': 'Standard deviations from average noise score derivative for noise score threshold calculation. Typically between 4-8',
        'Filter'          : 'Filters noise from the current peak list.',
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

        # # Input check
        # validInput = self._inputDataCheck()
        # if not validInput:
        #     return

        # setup database metabolite tables
        self.settings['Simulators']['HMDB'] = Simulator(self.project, '/home/mh491/Database/Remediated_Databases/ccpn_metabolites_hmdb.db')
        self.settings['Simulators']['BMRB'] = Simulator(self.project, '/home/mh491/Database/Remediated_Databases/ccpn_metabolites_bmrb.db')
        self.settings['Simulators']['GISSMO'] = Simulator(self.project, '/home/mh491/Database/Remediated_Databases/ccpn_metabolites_gissmo.db')

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

        # create the simulated spectrum group
        if 'Reference_Spectra' not in self.project.spectrumGroups:
            self.settings['Spectrum']['referenceSpectrumGroup'] = self.project.newSpectrumGroup(name='Reference_Spectra')

        grid = (0, 0)
        self.guiDict['Spectrum']['SimulatedSpectrumAttributes'] = []

        # pull down list for selecting the spectrum group to overlay on
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Spectrum Group', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2), tipText=help['Spectrum'])
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        self.spectrumGroups = [spectrumGroup.id for spectrumGroup in sorted(self.project.spectrumGroups)]
        widget.setData(self.spectrumGroups)
        self.guiDict['Spectrum']['SpectrumGroupId'] = widget
        self.settings['Spectrum']['SpectrumGroupId'] = self._getValue(widget)

        # pull down list for selecting the database to reference from
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Database', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, gridSpan=(1, 2),
                              callback=self._selectMetaboliteList, tipText=help['Spectrum'])
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
                              callback=self._setupNewMetabolite, tipText=help['Spectrum'])
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
        grid = (index+5, index+5)
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

    def scaleChange(self):
        scale = self.guiDict['Spectrum']['Scale'].value()
        self.simspec.scaleSpectrum(scale)

    def frequencyChange(self):
        frequency = self.guiDict['Spectrum']['Frequency'].value()
        self.simspec.setFrequency(frequency)

    '''def _databaseTableID2DatabaseTable(self, databaseTableID):
        return self.project.getByPid('DT:' + databaseTableID)'''

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
        self.simspec = self.settings['Simulators'][currentDatabase].pure_spectrum(metabolite_id=metaboliteID, width=0.002, frequency=700, plotting='spin_system')[0]
        if self.guiDict['Spectrum']['SimulatedSpectrumAttributes']:
            for widget in self.guiDict['Spectrum']['SimulatedSpectrumAttributes']:
                widget.deleteLater()
            self.guiDict['Spectrum']['SimulatedSpectrumAttributes'] = []

        grid = (3, 1)
        # Add a widget for the simulated spectrum scale
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text=f'Scale', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))
        self.guiDict[f'Spectrum']['SimulatedSpectrumAttributes'].append(widget)

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=1, decimals=1, step=1, grid=grid, gridSpan=(1, 2))
        widget.setRange(0, 10000000)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)
        widget.valueChanged.connect(self.scaleChange)
        self.guiDict[f'Spectrum']['SimulatedSpectrumAttributes'].append(widget)
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
        self.guiDict[f'Spectrum']['SimulatedSpectrumAttributes'].append(widget)
        self.settings['Spectrum']['Frequency'] = self._getValue(widget)

        for index in range(len(self.simspec.spinSystemMatrix)):
            self.addDoubleSpinbox(index)
        self.project.widgetList = self.guiDict['Spectrum']['SimulatedSpectrumAttributes']

    def _inputDataCheck(self):
        # Checks available input data at plugin start
        inputWarning = ''
        if len(self.project.chains) == 0:
            inputWarning += 'No molecular chains found in the project\n'
        if len(self.project.chemicalShiftLists) == 0:
            inputWarning += 'No chemical shift lists found in the project\n'
        if inputWarning != '':
            showWarning('Warning', inputWarning)
            #self._closeModule()
            self.deleteLater()
            return False
        return True

    def _runDataCheck(self):
        # Checks data before run time
        inputWarning = ''

        if len(self.settings['General']['Run name'].strip()) == 0:
            inputWarning += 'No run name specified\n'
        if len(self.settings['General']['Run name'].split()) > 1:
            inputWarning += 'Run name may not contain spaces\n'

        if inputWarning != '':
            showWarning('Warning', inputWarning)
            setupComplete = False
        else:
            setupComplete = True
        return setupComplete

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

    def _updateSettings(self, inputDict, outputDict):
        # Gets all the values from a dictionary that contains widgets
        # and writes values to the dictionary with the same structure
        for k, v in inputDict.items():
            if isinstance(v, dict):
                self._updateSettings(v, outputDict[k])
            else:
                outputDict[k] = self._getValue(v)
        return outputDict

    def _calcFirstNoiseScore(self, peak):

        if not None in peak.lineWidths:
            lws = list(peak.lineWidths)
            for i in range(len(lws)):
                lws[i] = abs(lws[i])

            lws = sorted(lws, reverse=True)
            shapeFactor = lws[0]
            areaFactor = lws[0]
            for lw in lws[1:]:
                shapeFactor = abs(shapeFactor / lw)
                areaFactor = abs(areaFactor * lw)

            return (shapeFactor / abs(peak.height)) / areaFactor
        else:
            return 1e100

    def _gauss(self, mean, value, sd):
        gauss = 1 / (math.sqrt(2 * math.pi) * sd) * math.e ** (-0.5 * (float(value - mean) / sd) ** 2)
        return gauss

    def _normalisedGauss(self, mean, value, sd):
        gauss = math.e ** (-0.5 * (float(value - mean) / sd) ** 2)
        return gauss

    def _calcLwDevFactor(self, peak, lwReferences):
        # Replace with Gaussian weighted dev factor.
        # lwReferences = [(avg,sd),(avg,sd), .... ]
        lwDevFactor = 1
        for i in range(len(lwReferences)):
            try:
                # lwDevFactor = lwDevFactor * abs(peak.lineWidths[i] - lwReferences[i])
                lwDevFactor = lwDevFactor / self._gauss(lwReferences[i][0], peak.lineWidths[i], lwReferences[i][0])
            except TypeError:
                pass

        return lwDevFactor

    @logCommand(get='self')
    def filterNoiseButton(self, *args, **kwds):
        """Call the filter function from the button
        """
        with undoBlock():
            self._filterNoisePeaks()

    def _filterNoisePeaks(self):
        # Get values from the GUI widgets and save in the settings
        self._updateSettings(self.guiDict, self.settings)

        minPeaks = self.settings['Spectrum']['Reference peaks']
        thresholdFactor = self.settings['Spectrum']['Threshold factor']

        spectrumId = self.settings['Spectrum']['SpectrumId']
        spectrum = self._spectrumId2Spectrum(spectrumId)
        nDims = spectrum.dimensionCount

        peakListId = 'PL:{0}.{1}'.format(spectrumId, self.settings['Spectrum']['Peak list'])
        peakList = self.project.getByPid(peakListId)

        # First sort the peaks on the first noise score factor.
        peakScores = []
        for peak in peakList.peaks:
            firstNoiseScore = self._calcFirstNoiseScore(peak)
            peakScores.append([peak, firstNoiseScore])

        sortedPeakScores = sorted(peakScores, key=operator.itemgetter(1))
        # for peak in sortedPeakScores:
        #     # print(peak[0].lineWidths, peak[0].height, peak[1])
        #     print(peak[1])
        # for peak in sortedPeakScores:
        #     print(peak[0].lineWidths, peak[0].height, peak[1])

        # Reference average linewidths can be best obtained by two step sorting and analysing:
        # - Sort with firstNoiseScore
        # - Calculate reference lineWidths and 2nd Noise Score
        # - Sort on 2nd Noise Score
        # - Calculate reference lineWidths again, and calculate 3rd Noise score

        # Calculate the linewidth averages of the first minPeaks ranking peaks

        lwReferences = []
        for i in range(nDims):
            lwReferences.append([])

        for peak in sortedPeakScores[:minPeaks]:
            # print (peak[0].lineWidths)
            for lwi in range(len(peak[0].lineWidths)):
                lwReferences[lwi].append(peak[0].lineWidths[lwi])

        # Calculate the average and sd
        for i in range(len(lwReferences)):
            lwReferences[i] = (numpy.mean(lwReferences[i]), numpy.std(lwReferences[i]))
            # print (lwReferences[i])

        # Add the 2nd noise score
        for peak in sortedPeakScores:
            peak.append(peak[1] * self._calcLwDevFactor(peak[0], lwReferences))

        # Sort on 2ndNoiseScore
        sortedPeakScores = sorted(sortedPeakScores, key=operator.itemgetter(2))

        # for peak in sortedPeakScores:
        #     print(peak[0].lineWidths, peak[0].height, peak[1], peak[2])

        # Calculate new line width averages and SD
        lwReferences = []
        for i in range(nDims):
            lwReferences.append([])

        for peak in sortedPeakScores[:minPeaks]:
            # print (peak[0].lineWidths)
            for lwi in range(len(peak[0].lineWidths)):
                lwReferences[lwi].append(peak[0].lineWidths[lwi])

        # Calculate the average and sd
        for i in range(len(lwReferences)):
            lwReferences[i] = (numpy.mean(lwReferences[i]), numpy.std(lwReferences[i]))
            # print (lwReferences[i])

        # Add the 3rd noise score
        for peak in sortedPeakScores:
            peak.append(peak[1] * self._calcLwDevFactor(peak[0], lwReferences))

        # Sort on 3rdNoiseScore
        sortedPeakScores = sorted(sortedPeakScores, key=operator.itemgetter(3))

        # for peak in sortedPeakScores:
        #     print(peak[0].lineWidths, peak[0].height, peak[1], peak[2], peak[3])

        #
        # # Sort again
        # sortedPeakScores = sorted(sortedPeakScores, key=operator.itemgetter(1))

        # Determine cutoff for noise/peak separation.
        # Calculate the noise score average and sd for the 20 first ranking peaks

        nTrainingPeaks = 20
        noiseScoreReferenceList = []
        for peak in sortedPeakScores[1:nTrainingPeaks]:
            noiseScoreReferenceList.append(peak[1])
            print(peak[0], peak[1])

        # For all peaks in the sorted peak list, calculate the derivative
        # and update the average and standard deviation of the derivatives
        # The transition from peaks to noise peaks is where the derivative suddenly changes.
        # If the derivative changes more than n*SD of the average of the previous, this becomes the noise threshold.

        noiseScoreThreshold = None
        derivatives = []

        for i in range(1, len(sortedPeakScores) - 1):
            derivative = (sortedPeakScores[i - 1][3] + sortedPeakScores[i + 1][3]) / 2
            if len(derivatives) > minPeaks:
                avg = numpy.mean(derivatives)
                std = numpy.std(derivatives)
                if derivative > avg + thresholdFactor * std:
                    noiseScoreThreshold = sortedPeakScores[i][3]
                    break
            derivatives.append(derivative)

        if not noiseScoreThreshold:
            print('>> No threshold calculated')
            return

        npnoiseScoreThreshold = numpy.mean(noiseScoreReferenceList) + 4 * numpy.std(noiseScoreReferenceList)

        print(">>>noiseScoreThreshold", noiseScoreThreshold)
        print(">>>npnoiseScoreThreshold", npnoiseScoreThreshold)
        print(">>>numPeakScores", len(sortedPeakScores))
        #spectrum = self._spectrumId2Spectrum(self.settings['Spectrum']['SpectrumId'])
        #spectrum.newPeakList()
        #newPeakList = spectrum.peakLists[-1]

        for peak in sortedPeakScores:
            #print(peak[0], peak[1])
            # if peak[1] < noiseScoreThreshold or peak[1] == 1e100:
            #     print (peak[0].lineWidths,peak[0].height, peak[1])
            #     #PyQt5
            # else:
            #     peakId = 'PK:{0}.{1}.{2}'.format(self.settings['Spectrum']['SpectrumId'],
            #                                      self.settings['Spectrum']['Peak list'],peak[0].serial)
            #     self.project.deleteObjects(peakId)
            # if peak[3] > noiseScoreThreshold and peak[3] != 1e100:
            if peak[3] > noiseScoreThreshold:
                print(peak[0].lineWidths, peak[0].height, peak[1])
                peakId = 'PK:{0}.{1}.{2}'.format(self.settings['Spectrum']['SpectrumId'],
                                                 self.settings['Spectrum']['Peak list'], peak[0].serial)
                self.project.deleteObjects(peakId)

        # Now copy any peaks with noise lower than the threshold to a new peak list

    # # Check if all input requirements are met
    # setupComplete = self._runDataCheck()
    #
    # if setupComplete == True:
    #     # Check if tree exists, and if to overwrite
    #     overwrite = False
    #     if os.path.exists(self.runPath):
    #         overwrite = showYesNo('Warning', 'Run {0} exists. Overwrite?'.format(self.settings['General']['Run name']))
    #         if overwrite == False:
    #             showMessage('Message', 'Project set up aborted')
    #             return
    #
    #     if overwrite == True:
    #         shutil.rmtree(self.runPath)
    #
    #     # Create a (new) directory tree
    #     self._createRunTree()
    #     self._writeFilterNoisePeaks()
    #     showMessage('Message', 'Filter Noise Peaks complete')

    def _createRunTree(self):
        if not os.path.exists(self.pluginPath):
            os.makedirs(self.pluginPath)

        if not os.path.exists(self.runPath):
            os.makedirs(self.runPath)


class FilterNoisePeaksPlugin(Plugin):
    PLUGINNAME = 'Profile by Reference'
    guiModule = ProfileByReferenceGuiPlugin
    CCPNPLUGIN = True

    def run(self, **kwargs):
        """ Insert here the script for running Tsar """
        print('Filtering noise peaks', kwargs)


FilterNoisePeaksPlugin.register()  # Registers the pipe in the pluginList
# Set tolerances from project.spectrum.tolerances by default