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
__modifiedBy__ = "$modifiedBy: Chris Spronk $"
__dateModified__ = "$dateModified: 2017-11-28 16:32:26 +0100 (Tue, Nov 28, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Chris Spronk $"
__date__ = "$Date: 2017-11-28 10:28:42 +0000 (Tue, Nov 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import os,copy,json,pprint,math,shutil,pandas,operator,numpy
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
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning, showMessage,showYesNo
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.nef import GenericStarParser, StarIo
from ccpn.util.nef.GenericStarParser import SaveFrame, DataBlock, DataExtent, Loop, LoopRow
from functools import partial

############
# Settings #
############

# Widths in pixels for nice widget alignments, length depends on the number of fixed columns in the plugin.
# Variable number of columns will take the last value in the list
columnWidths = [100]

# Set some tooltip texts
help = {'Spectrum': 'Select spectrum',
        'Peak list': 'Peak list to filter noise',
        'Reference peaks': 'Estimated number of peaks to use as reference. Minimum 10. Set to about 50% of expected real peaks in the spectrum.',
        'Threshold factor': 'Standard deviations from average noise score derivative for noise score threshold calculation. Typically between 4-8',
        'Filter': 'Filters noise from the current peak list.',
        }

class FilterNoisePeaksGuiPlugin(PluginModule):

    className = 'FilterNoisePeaks'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super(FilterNoisePeaksGuiPlugin, self)
        PluginModule.__init__(self, mainWindow=mainWindow, plugin=plugin, application=application)

        # Import some functionality for placing widgets on the grid and setting their properties
        from .pluginAddons import _addRow, _addColumn, _addVerticalSpacer, _setWidth, _setWidgetProperties

        self.scrollArea = ScrollArea(self.mainWidget,grid=(0,0))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaLayout = Frame(None, setLayout=True)
        self.scrollArea.setWidget(self.scrollAreaLayout)
        self.scrollAreaLayout.setContentsMargins(20, 20, 20, 20)

        # self.userPluginPath = self.application.preferences.general.userPluginPath
        # self.outputPath = self.application.preferences.general.dataPath

        self.pluginPath = os.path.join(self.project.path,FilterNoisePeaksGuiPlugin.className)

        # Create ORDERED dictionary to store all parameters for the run
        # deepcopy doesn't work on dictionaries with the qt widgets, so to get a separation of gui widgets and values for storage
        # it is needed to create the two dictionaries alongside each other
        self.guiDict  = OD([('Spectrum',OD())])
        self.settings = OD([('Spectrum',OD())])

        # # Input check
        # validInput = self._inputDataCheck()
        # if not validInput:
        #     return

        # Set peak list, use pulldown, FilterNoisePeaks only allows one list at a time

        grid = (0,0)

        widget = Label(self.scrollAreaLayout,text='Spectrum', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid,callback=self._selectPeaklist, tipText=help['Spectrum'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        self.spectra = [spectrum.id for spectrum in sorted(self.project.spectra)]
        widget.setData(self.spectra)
        self.guiDict['Spectrum']['SpectrumId'] = widget
        self.settings['Spectrum']['SpectrumId'] = self._getValue(widget)

        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout,text='Peak list', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, tipText=help['Peak list'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        self.guiDict['Spectrum']['Peak list'] = widget
        self.settings['Spectrum']['Peak list'] = self._getValue(widget)

        # Invoke the callback function to catch the selection in case only one spectrum is available
        if self.spectra:
            self._selectPeaklist(self.spectra[0])

        # Number of reference peaks to use initially for estimating the noise factor threshold
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout,text='Reference peaks', grid=grid,tipText=help['Reference peaks'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = Spinbox(self.scrollAreaLayout, value=10, step=1, grid=grid,
                               tipText=help['Reference peaks'])
        widget.setRange(10, 100000)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)

        self.guiDict['Spectrum']['Reference peaks'] = widget
        self.settings['Spectrum']['Reference peaks'] = self._getValue(widget)


        # Number of standard deviations in derivative change of the noiseScores to use for noiseScoreThreshold
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout,text='Threshold factor', grid=grid,tipText=help['Threshold factor'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = DoubleSpinbox(self.scrollAreaLayout, value=6, decimals=1, step=0.1, grid=grid,
                               tipText=help['Threshold factor'])
        widget.setRange(1, 10)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
        widget.setButtonSymbols(2)

        self.guiDict['Spectrum']['Threshold factor'] = widget
        self.settings['Spectrum']['Threshold factor'] = self._getValue(widget)

        # Action buttons: Filter creates a new filtered peak list
        grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
        grid = _addColumn(grid)
        texts = ['Filter']
        tipTexts = [help['Filter']]
        callbacks = [self._filterNoisePeaks]
        widget = ButtonList(parent=self.scrollAreaLayout, texts=texts, callbacks=callbacks, tipTexts=tipTexts, grid=grid, gridSpan=(1,2))
        _setWidgetProperties(widget,_setWidth(columnWidths,grid),heightType='Minimum')

        Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0]+1, 10),
               gridSpan=(1, 1))

    def _spectrumId2Spectrum(self,spectrumId):
        return self.project.getByPid('SP:'+spectrumId)

    def _selectPeaklist(self,spectrumId):
        spectrum = self._spectrumId2Spectrum(spectrumId)
        widget = self.guiDict['Spectrum']['Peak list']
        widget.setData([str(PL.serial) for PL in spectrum.peakLists])
        self.settings['Spectrum']['Peak list'] = self._getValue(widget)

    def _inputDataCheck(self):
        # Checks available input data at plugin start
        inputWarning = ''
        if len(self.project.chains) == 0:
            inputWarning += 'No molecular chains found in the project\n'
        if len(self.project.chemicalShiftLists) == 0:
            inputWarning += 'No chemical shift lists found in the project\n'
        if inputWarning != '':
            showWarning('Warning',inputWarning)
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
            showWarning('Warning',inputWarning)
            setupComplete = False
        else:
            setupComplete = True
        return setupComplete

    def _getValue(self,widget):
        # Get the current value of the widget:
        if isinstance(widget,str):
            value = widget
        if not isinstance(widget, Button) and not isinstance(widget, ButtonList):
            if hasattr(widget,'get'):
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

            lws = sorted(lws,reverse=True)
            shapeFactor = lws[0]
            areaFactor = lws[0]
            for lw in lws[1:]:
                shapeFactor = abs(shapeFactor/lw)
                areaFactor = abs(areaFactor*lw)

            return (shapeFactor/abs(peak.height))/areaFactor
        else:
            return 1e100

    def _gauss(self,mean, value, sd):
        gauss = 1 / (math.sqrt(2 * math.pi) * sd) * math.e ** (-0.5 * (float(value - mean) / sd) ** 2)
        return gauss

    def _normalisedGauss(self,mean, value, sd):
        gauss = math.e ** (-0.5 * (float(value - mean) / sd) ** 2)
        return gauss

    def _calcLwDevFactor(self,peak,lwReferences):
        # Replace with Gaussian weighted dev factor.
        # lwReferences = [(avg,sd),(avg,sd), .... ]
        lwDevFactor = 1
        for i in range(len(lwReferences)):
            try:
                # lwDevFactor = lwDevFactor * abs(peak.lineWidths[i] - lwReferences[i])
                lwDevFactor = lwDevFactor / self._gauss(lwReferences[i][0],peak.lineWidths[i],lwReferences[i][0])
            except TypeError:
                pass

        return lwDevFactor

    def _filterNoisePeaks(self):
        # Get values from the GUI widgets and save in the settings
        self._updateSettings(self.guiDict, self.settings)

        minPeaks = self.settings['Spectrum']['Reference peaks']
        thresholdFactor = self.settings['Spectrum']['Threshold factor']

        spectrumId = self.settings['Spectrum']['SpectrumId']
        spectrum = self._spectrumId2Spectrum(spectrumId)
        nDims = spectrum.dimensionCount

        peakListId = 'PL:{0}.{1}'.format(spectrumId,self.settings['Spectrum']['Peak list'])
        peakList = self.project.getByPid(peakListId)

        # First sort the peaks on the first noise score factor.
        peakScores = []
        for peak in peakList.peaks:
            firstNoiseScore = self._calcFirstNoiseScore(peak)
            peakScores.append([peak,firstNoiseScore])

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
            lwReferences[i] = (numpy.mean(lwReferences[i]),numpy.std(lwReferences[i]))
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
            lwReferences[i] = (numpy.mean(lwReferences[i]),numpy.std(lwReferences[i]))
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

        # nTrainingPeaks = 60
        # noiseScoreReferenceList = []
        # for peak in sortedPeakScores[1:nTrainingPeaks]:
        #     noiseScoreReferenceList.append(peak[1])
        #     print (peak[0],peak[1])

        # For all peaks in the sorted peak list, calculate the derivative
        # and update the average and standard deviation of the derivatives
        # The transition from peaks to noise peaks is where the derivative suddenly changes.
        # If the derivative changes more than n*SD of the average of the previous, this becomes the noise threshold.

        derivatives = []
        for i in range(1,len(sortedPeakScores)-1):
            derivative = (sortedPeakScores[i-1][3] + sortedPeakScores[i+1][3])/2
            if len(derivatives) > minPeaks:
                avg = numpy.mean(derivatives)
                std = numpy.std(derivatives)
                if derivative > avg + thresholdFactor*std:
                    noiseScoreThreshold = sortedPeakScores[i][3]
                    break
            derivatives.append(derivative)

        # noiseScoreThreshold = numpy.mean(noiseScoreReferenceList) + 4 * numpy.std(noiseScoreReferenceList)
        # print (noiseScoreThreshold)
        # print (len(sortedPeakScores))
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
                # print (peak[0].lineWidths,peak[0].height, peak[1])
                peakId = 'PK:{0}.{1}.{2}'.format(self.settings['Spectrum']['SpectrumId'],
                                                 self.settings['Spectrum']['Peak list'],peak[0].serial)
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
    PLUGINNAME = 'Filter Noise Peaks'
    guiModule = FilterNoisePeaksGuiPlugin

    def run(self, **kwargs):
        ''' Insert here the script for running Tsar '''
        print('Filtering noise peaks', kwargs)


# FilterNoisePeaksPlugin.register()  # Registers the pipe in the pluginList
# Set tolerances from project.spectrum.tolerances by default
