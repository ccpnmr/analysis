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
__version__ = "$Revision: 3.0.0 $"
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
columnWidths = [150, 100, 75]

# Set some tooltip texts
help = {'Spectrum': 'Check spectra for which to check for close peaks.',
        'Peak list': 'Peak list to check close peaks.',
        'Tolerances': 'Tolerances defining closeness of peaks. Peaks that are close within all tolerances will be copied to a new peak list.',
        'Axis': 'Spectrum axis',
        'Find close peaks': 'Finds close peaks within selected peak lists, and copies to a new peak list for inspection.',
        }

defaultTolerances = {'H': 0.02, 'C': 0.05, 'N': 0.05}

class FindClosePeaksGuiPlugin(PluginModule):

    className = 'FindClosePeaks'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super(FindClosePeaksGuiPlugin, self)
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

        self.pluginPath = os.path.join(self.project.path,FindClosePeaksGuiPlugin.className)

        # Create ORDERED dictionary to store all parameters for the run
        # deepcopy doesn't work on dictionaries with the qt widgets, so to get a separation of gui widgets and values for storage
        # it is needed to create the two dictionaries alongside each other
        self.guiDict  = OD([('Spectra',OD())])
        self.settings = OD([('Spectra',OD())])

        for i in range(len(self.project.spectra)):
            self.guiDict['Spectra'][self.project.spectra[i].id] = OD()
            self.settings['Spectra'][self.project.spectra[i].id] = OD()

        # # Input check
        # validInput = self._inputDataCheck()
        # if not validInput:
        #     return

        # Set peak list, use pulldown, FindClosePeaks only allows one list at a time

        grid = (0,0)

        widget = Label(self.scrollAreaLayout,text='Spectra', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout,text='Peak list', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout, text='Merge tolerances', grid=grid, gridSpan=(1,4), tipText=help['Tolerances'])
        _setWidgetProperties(widget, _setWidth(columnWidths, grid), widthType='')

        for spectrumId in sorted(self.settings['Spectra']):
            spectrum = self._spectrumId2Spectrum(spectrumId)
            grid = _addRow(grid)

            widget = CheckBox(self.scrollAreaLayout, text=spectrumId, checked=True, grid=grid, tipText=help['Spectrum'],callback=partial(self._selectPeaklist,spectrumId))
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            self.guiDict['Spectra'][spectrumId] = OD([('Active', widget)])
            self.settings['Spectra'][spectrumId] = OD([('Active', self._getValue(widget))])

            grid = _addColumn(grid)
            widget = PulldownList(self.scrollAreaLayout, grid=grid, tipText=help['Peak list'])
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            self.guiDict['Spectra'][spectrumId]['Peak list'] = widget
            self._selectPeaklist(spectrumId)
            self.settings['Spectra'][spectrumId]['Peak list'] = self._getValue(widget)

            # For each dimension, add tolerances
            self.guiDict['Spectra'][spectrumId]['Tolerances']= OD()
            self.settings['Spectra'][spectrumId]['Tolerances']= OD()
            for axis in spectrum.axisCodes:
                isotope = axis[0].upper()
                tolerance = defaultTolerances[isotope]

                grid = _addColumn(grid)
                widget = Label(self.scrollAreaLayout, text=axis, grid=grid, tipText=help['Axis'])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
                grid = _addColumn(grid)

                widget = DoubleSpinbox(self.scrollAreaLayout, value=tolerance, step=0.001, decimals=3,grid=grid, tipText=help['Tolerances'])
                widget.setRange(0.001,spectrum.assignmentTolerances[spectrum.axisCodes.index(axis)])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
                widget.setButtonSymbols(2)

                self.guiDict['Spectra'][spectrumId]['Tolerances'][axis] = widget
                self.settings['Spectra'][spectrumId]['Tolerances'][axis] = self._getValue(widget)


        # Action buttons: Filter creates a new filtered peak list
        grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
        grid = _addColumn(grid)
        texts = ['Find close peaks']
        tipTexts = [help['Find close peaks']]
        callbacks = [self._findClosePeaks]
        widget = ButtonList(parent=self.scrollAreaLayout, texts=texts, callbacks=callbacks, tipTexts=tipTexts, grid=grid, gridSpan=(1,2))
        _setWidgetProperties(widget,_setWidth(columnWidths,grid),heightType='Minimum')

        Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0]+1, 10),
               gridSpan=(1, 1))

    def _spectrumId2Spectrum(self,spectrumId):
        return self.project.getByPid('SP:'+spectrumId)

    def _selectPeaklist(self, spectrumId):
        if self.guiDict['Spectra'][spectrumId]['Active'].isChecked():
            spectrum = self._spectrumId2Spectrum(spectrumId)

            widget = self.guiDict['Spectra'][spectrumId]['Peak list']
            widget.setData([str(PL.serial) for PL in spectrum.peakLists])
            widget.setEnabled(True)
            self.settings['Spectra'][spectrumId]['Peak list'] = self._getValue(widget)

        else:
            widget = self.guiDict['Spectra'][spectrumId]['Peak list']
            widget.setEnabled(False)


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

    def _comparePeaks(self, spectrum, peakList):
        nDims = spectrum.dimensionCount

        # Place the tolerances in a list
        tolerances = []
        for axis in spectrum.axisCodes:
            tolerances.append(self.settings['Spectra'][spectrum.id]['Tolerances'][axis])

        # Sort the peaks on chemical shift for faster comparison
        peakPositions = []
        for peak in peakList.peaks:
            peakPosition = [peak]
            for shift in peak.position:
                peakPosition.append(shift)
            peakPositions.append(peakPosition)

        sortedPeakPositions = sorted(peakPositions, key=operator.itemgetter(*range(1,nDims+1)))

        sortedPeaks = []
        for peakPosition in sortedPeakPositions:
            peak = peakPosition[0]
            sortedPeaks.append(peak)

        # Create a list of close peaks, for copying to a new peak list
        closePeaks = []
        for i in range(len(sortedPeaks)-1):
            close = self._checkClosePosition(sortedPeaks[i],sortedPeaks[i+1],tolerances)
            if close == True:
                if sortedPeaks[i] not in closePeaks:
                    closePeaks.append(sortedPeaks[i])
                if sortedPeaks[i+1] not in closePeaks:
                    closePeaks.append(sortedPeaks[i+1])
                    
        return closePeaks

    def _checkClosePosition(self, peak1, peak2, tolerances):
        a = peak1.position
        b = peak2.position

        close = True
        for j in range(len(tolerances)):
            if abs(a[j] - b[j]) > tolerances[j]:
                close = False

        return close

    def _findClosePeaks(self):
        # Get values from the GUI widgets and save in the settings
        self._updateSettings(self.guiDict, self.settings)

        message = 'Close peaks found:\n'
        for spectrumId in self.settings['Spectra']:
            if self.settings['Spectra'][spectrumId]['Active'] == True:
                spectrum = self._spectrumId2Spectrum(spectrumId)
                peakList = self.project.getByPid('PL:{0}.{1}'.format(spectrumId,self.settings['Spectra'][spectrumId]['Peak list']))
                closePeaks = self._comparePeaks(spectrum,peakList)

                if len(closePeaks) != 0:
                    spectrum.newPeakList()
                    newPeakList = spectrum.peakLists[-1]
                    for peak in closePeaks:
                        peak.copyTo(newPeakList)
                
                message += '{0} peak list {1}:\t{2}\n'.format(spectrumId,self.settings['Spectra'][spectrumId]['Peak list'],len(closePeaks))

        showMessage('Message', message)


class FindClosePeaksPlugin(Plugin):
    PLUGINNAME = 'Find Close Peaks'
    guiModule = FindClosePeaksGuiPlugin

    def run(self, **kwargs):
        ''' Insert here the script for running Tsar '''
        print('Finding close peaks', kwargs)


# FindClosePeaksPlugin.register()  # Registers the pipe in the pluginList
# Set tolerances from project.spectrum.tolerances by default
