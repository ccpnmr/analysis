# =========================================================================================
# Licence, Reference and Credits
# =========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
# =========================================================================================
# Last code modification
# =========================================================================================
__modifiedBy__ = "$modifiedBy: Chris Spronk $"
__dateModified__ = "$dateModified: 2017-08-22 16:32:26 +0100 (Tue, Aug 22, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
# =========================================================================================
# Created
# =========================================================================================
__author__ = "$Author: Chris Spronk $"
__date__ = "$Date: 2017-08-22 10:28:42 +0000 (Tue, Aug 22, 2017) $"
# =========================================================================================
# Start of code
# =========================================================================================

import os
from PyQt4 import QtCore, QtGui
from ccpn.framework.lib.Plugin import Plugin
from ccpn.ui.gui.modules.PluginModule import PluginModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.util.nef import GenericStarParser, StarIo
from ccpn.util.nef.GenericStarParser import SaveFrame, DataBlock, DataExtent, Loop, LoopRow
from functools import partial

############
# Settings #
############

# Fixed column width for nice widget alignments
fixedColumnWidth = 100

# Set some tooltip texts
toleranceHelp = 'Recommended value = spectral width (Hz) / (number of increments * spectrometer frequency (MHz)'
peakSignHelp  = 'p = positive, n = negative, u = unknown'

# Set the basis and backbone assignment experiment type synonyms as valid inputs
# The Tsar basis experiment is typically:
#  - 15N-HSQC for 3D/4D based automated assignment (HNCO preferred for 4D)
#  - 3D HNCO for 4D and 5D based automated assignment
# Backbone experiments currently implemented for 3D based assignment are organised in this dictionary.
# The dictionary contains the nuclei for chemical shift matches with their peak signs.
# Peak sign values in Tsar can be 'p', 'n', 'u' for positive, negative and unknown
# The list of experiment can be expanded as Tsar can handle any type, see Tsar manual.
tsarBasisExperiments    = ['15N HSQC/HMQC', 'HNCO']
tsarBackboneExperiments = {'HNCO':      {'Peak signs': {'CO': 'p'}, 'Connectivities': ['CO -1 N 0 HN 0']},
                           'HNcaCO':    {'Peak signs': {'CO': 'p'}, 'Connectivities': ['CO 0 N 0 HN 0']},
                           'HNcoCA':    {'Peak signs': {'CA': 'p'}, 'Connectivities': ['CA -1 N 0 HN 0']},
                           'HNCA':      {'Peak signs': {'CA': 'p'}, 'Connectivities': ['CA 0 N 0 HN 0', 'CA -1 N 0 HN 0']},
                           'CB/CAcoNH': {'Peak signs': {'CA': 'p', 'CB': 'p'},'Connectivities': ['CA -1 N 0 HN 0', 'CB -1 N 0 HN 0']},
                           'HNcoCA/CB': {'Peak signs': {'CA': 'p', 'CB': 'p'},'Connectivities': ['CA -1 N 0 HN 0', 'CB -1 N 0 HN 0']},
                           'HNCA/CB':   {'Peak signs': {'CA': 'p', 'CB': 'n'},'Connectivities': ['CA 0 N 0 HN 0', 'CA -1 N 0 HN 0', 'CB 0 N 0 HN 0','CB -1 N 0 HN 0']}
                           }


class TsarGuiPlugin(PluginModule):
    def __init__(self, mainWindow=None, tipText=peakSignHelp, plugin=None, application=None, **kw):
        super(TsarGuiPlugin, self)
        PluginModule.__init__(self, mainWindow=mainWindow, plugin=plugin, application=application)

        # self.userPluginPath = self.application.preferences.general.userPluginPath
        self.outputPath = self.application.preferences.general.dataPath
        self.mainWidget.setContentsMargins(20, 20, 20, 20)

        # Set the basis and backbone assignment experiment type synonyms as valid inputs
        self.basisSpectra    = [self.project.spectra[i].id for i in range(len(self.project.spectra))
                                if self.project.spectra[i].synonym in tsarBasisExperiments]


        # Spectrum ids are unique. For easier lookup later, we create a dictionary here that duplicates ExperimentTypes info with spectrum id as keys
        # Easier for later extraction and export to NEF
        self.data = {}
        for i in range(len(self.project.spectra)):
            if self.project.spectra[i].synonym in tsarBackboneExperiments:
                self.data[self.project.spectra[i].id] = tsarBackboneExperiments[self.project.spectra[i].synonym]
        print(self.data)
        # Run name
        row = 0
        self.runNameLabel = Label(self.mainWidget, 'Run Name', grid=(row, 0))
        self.runNameLineEdit = LineEdit(self.mainWidget, 'Run 1', textAligment='l', grid=(row, 1))
        self.runNameLineEdit.setFixedWidth(fixedColumnWidth)

        # Set basis spectrum
        row += 1
        label = Label(self.mainWidget, text="Basis spectrum", grid=(row, 0))
        # Basis spectrum selection updates the peak list pulldown using spectrum selection function.
        self.basisSpectrumPulldown = PulldownList(self.mainWidget, grid=(row, 1), callback=self._selectBasisSpectrum)
        self.basisSpectrumPulldown.setData(self.basisSpectra)
        self.basisPeaklistPulldown = PulldownList(self.mainWidget, grid=(row, 2))

        # Call the callback function to catch the selection in case only one spectrum is available as basisExperiment
        self.basisSpectrum = self._selectBasisSpectrum(self.basisSpectra[0])

        # Set fixed widths
        self.basisSpectrumPulldown.setFixedWidth(fixedColumnWidth)
        self.basisPeaklistPulldown.setFixedWidth(fixedColumnWidth)

        # Create header row for clean plugin content organisation
        row += 1
        Spacer(self.mainWidget, 0, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed, grid=(row, 0), gridSpan=(1, 1))
        row += 1
        column = -1

        for text in ['Spectrum', 'Active', 'Peak list', '13C Tolerance', 'Peak signs']:
            column += 1
            label = Label(self.mainWidget, text=text, grid=(row, column), hAlign='c')
            label.setFixedWidth(fixedColumnWidth)

        for spectrumId in sorted(self.data):
            column = 0
            spectrum = self._spectrumId2Spectrum(spectrumId)

            row += 1
            label = Label(self.mainWidget, text=spectrumId, grid=(row, column))
            label.setFixedWidth(fixedColumnWidth)

            column += 1
            self.data[spectrumId]['Active'] = CheckBox(self.mainWidget, text='', checked=True, grid=(row, column),
                                                       callback=partial(self._selectBackbonePeaklist, spectrumId))

            column += 1
            self.data[spectrumId]['Peak list'] = PulldownList(self.mainWidget, grid=(row, column))
            self._selectBackbonePeaklist(spectrumId)

            self.data[spectrumId]['Active'].setFixedWidth(fixedColumnWidth)
            self.data[spectrumId]['Peak list'].setFixedWidth(fixedColumnWidth)

            # Tolerances
            if spectrum.dimensionCount == 3 and self.basisSpectrum.synonym == '15N HSQC/HMQC':
                # In case of 3D spectra, we only need one tolerance, for the Carbon
                column += 1
                self.data[spectrumId]['Tolerance1'] = DoubleSpinbox(self.mainWidget, value=0.500, step=0.05, decimals=3,
                                                                    grid=(row, column), tipText=toleranceHelp)
                self.data[spectrumId]['Tolerance1'].setFixedWidth(fixedColumnWidth)
                self.data[spectrumId]['Tolerance1'].setAlignment(QtCore.Qt.AlignRight)

            else:
                # This needs expansion when 4D/5D is included, for now we limit to 3D
                column += 1
                # label = Label(self.mainWidget, '13C Tolerance', grid=(row, column))
                # label.setFixedWidth(fixedColumnWidth)
                # column += 1
                self.data[spectrumId]['Tolerance1'] = DoubleSpinbox(self.mainWidget, value=0.500, step=0.05, decimals=3,
                                                                    grid=(row, column), tipText=toleranceHelp)
                self.data[spectrumId]['Tolerance1'].setFixedWidth(fixedColumnWidth)
                self.data[spectrumId]['Tolerance1'].setAlignment(QtCore.Qt.AlignRight)
                column += 1
                # label = Label(self.mainWidget, '1H Tolerance', grid=(row, column))
                # label.setFixedWidth(fixedColumnWidth)
                # column += 1
                self.data[spectrumId]['Tolerance2'] = DoubleSpinbox(self.mainWidget, value=0.050, step=0.005,
                                                                    decimals=3, grid=(row, column),
                                                                    tipText=toleranceHelp)
                self.data[spectrumId]['Tolerance2'].setFixedWidth(fixedColumnWidth)
                self.data[spectrumId]['Tolerance2'].setAlignment(QtCore.Qt.AlignRight)

            # Peak signs
            listValues = ['p', 'n', 'u']
            for nucleus in sorted(self.data[spectrumId]['Peak signs'].keys()):
                # Set the default value to start with
                defaultValue = self.data[spectrumId]['Peak signs'][nucleus]
                column += 1
                label = Label(self.mainWidget, nucleus, grid=(row, column), hAlign='r')
                label.setFixedWidth(50)
                column += 1
                self.data[spectrumId]['Peak signs'][nucleus] = PulldownList(self.mainWidget, texts=listValues,
                                                                            tipText=peakSignHelp, grid=(row, column))

                self.data[spectrumId]['Peak signs'][nucleus].setCurrentIndex(listValues.index(defaultValue))
                self.data[spectrumId]['Peak signs'][nucleus].setFixedWidth(50)


        # Run Button
        row += 1
        Spacer(self.mainWidget, 0, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed, grid=(row, 0), gridSpan=(1, 1))
        self.runButton = Button(self.mainWidget, text='Run TSAR', callback=self._run, grid=(row, 1))
        self.runButton.setMinimumHeight(25)
        Spacer(self.mainWidget, 5, 5, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding, grid=(row + 1, 10),
               gridSpan=(1, 1))
    
    def _spectrumId2Spectrum(self,spectrumId):
        return self.project.getByPid('SP:'+spectrumId)
    
    def _selectBasisSpectrum(self,spectrumId):
        spectrum = self._spectrumId2Spectrum(spectrumId)
        self.basisPeaklistPulldown.setData([str(PL.serial) for PL in spectrum.peakLists])
        return spectrum

    def _selectBackbonePeaklist(self, spectrumId):
        if self.data[spectrumId]['Active'].isChecked():
            spectrum = self._spectrumId2Spectrum(spectrumId)

            self.data[spectrumId]['Peak list'].setData([str(PL.serial) for PL in spectrum.peakLists])
            self.data[spectrumId]['Peak list'].setEnabled(True)
        else:
            self.data[spectrumId]['Peak list'].setEnabled(False)

    # def _checkTsarPath(self):
    #   self.TsarPath = self.userPluginPath+'Tsar/'
    #   if not os.path.exists(self.TsarPath):
    #     os.makedirs(self.TsarPath)

    def _printValues(self):
        print('###########\n\n')
        for spectrumId in sorted(self.data):
            if self.data[spectrumId]['Active'].isChecked():

                print('Peak list {0} {1}'.format(spectrumId, self.data[spectrumId]['Peak list'].get()))
                print('Tolerance {0}'.format(self.data[spectrumId]['Tolerance1'].value()))
                print('Connectivities')
                for connectivity in self.data[spectrumId]['Connectivities']:
                    print('  {0}'.format(connectivity))
                for y in self.data[spectrumId]['Peak signs']:
                    print(y, self.data[spectrumId]['Peak signs'][y].get())
                    self._temp()

    def _temp(self):
        DB = DataBlock(name='firstBlock')

        for spectrumId in sorted(self.data):
            if self.data[spectrumId]['Active'].isChecked():

                newSaveFrame = SaveFrame(name=spectrumId)
                DB.addItem(spectrumId, newSaveFrame)

                # print('Peak list {0} {1}'.format(spectrumId, self.data[spectrumId]['Peak list'].get()))
                # print('Tolerance {0}'.format(self.data[spectrumId]['Tolerance1'].value()))

                newSaveFrame.addItem('_{0}.sf_category'.format(''), spectrumId)
                newSaveFrame.addItem('_{0}.sf_framecode'.format(''), spectrumId)

                newSaveFrame.addItem('_{0}.peakList_name'.format(''), spectrumId)
                newSaveFrame.addItem('_{0}.peakList_num'.format(''), self.data[spectrumId]['Peak list'].get())
                newSaveFrame.addItem('_{0}.peakList_tolerance'.format(''), self.data[spectrumId]['Tolerance1'].value())

                newLoop = Loop(name='connectivity')
                newSaveFrame.addItem('connectivity', newLoop)

                for columnName in ['1', '2', '3', '4', '5', '6']:
                    newLoop.addColumn(columnName='_.{0}'.format(columnName))

                for connectivity in self.data[spectrumId]['Connectivities']:
                    newLoop.newRow(connectivity.split())

                # Tsar requires peaks to be grouped per 'cross-section' for each spinsystem (sequenceCode) and number of peaks on that cross section
                #

                newLoop = Loop(name='peaks')
                newSaveFrame.addItem('peaks', newLoop)

                for columnName in ['sequenceCode','dimension1', 'dimension2','height']:
                    newLoop.addColumn(columnName='_.{0}'.format(columnName))



                peaklist = self.project.getByPid('PL:'+spectrumId+'.'+self.data[spectrumId]['Peak list'].get())

                filteredPeaks = self._filterPeaks(peaklist.peaks)
                sortedPeaks = self._sortPeaks(filteredPeaks)

                for peak in sortedPeaks:
                    try:
                        positions = [peak.assignedNmrAtoms[0][0].nmrResidue.sequenceCode,'{0:.6f}'.format(peak.position[1]),'{0:.6f}'.format(peak.position[1]),'{0:.6f}'.format(peak.height)]
                    except (IndexError,AttributeError) as error:
                        continue
                    newLoop.newRow(positions)


        with open('/Users/ccpn/Desktop/tempOutput.nef', 'w') as op:
            op.write(DB.toString())

        newFile = GenericStarParser.parseFile('/Users/ccpn/Desktop/tempOutput.nef')
        pass

    def _filterPeaks(self,peaks):
        # Only peaks that have assignments for both the basis dimensions should be used, as these are used to define the Tsar spinsystem
        filteredPeaks = []
        for peak in peaks:
            try:
                peak.assignedNmrAtoms[0][0].nmrResidue.sequenceCode
            except (IndexError, AttributeError) as error:
                continue
            filteredPeaks.append(peak)
        return filteredPeaks

    def _sortPeaks(self,peaks):
        sortList = sorted(peaks, key=lambda peak: int(peak.assignedNmrAtoms[0][0].nmrResidue.sequenceCode), reverse=False)
        return sortList

    def _createTsarBackbonePeaks(self,spectrumId):
        # Function loops over the backbone peak list, and gets all the sequenceCodes, to match with Tsar cross sections
        # Tsar cross sections contain a number of peaks that correspond to a single spin system.
        # So it is important that peaks in backbone experiments contain the assignments of the corresponding root NH peaks.
        #
        pass

    def _run(self):
        # pids = self.treeView.getSelectedObjectsPids()
        # try:
        #   self.project.exportNef(str(self.TsarPath+self.runNameLineEdit.get()), pidList=pids)
        #   self.plugin.run(**self.widgetsState)
        # except Exception as e:
        #   showWarning(message=str(e), title='Error')
        self._printValues()

        # For 3D spectra, tolerances are duplicated

class TsarPlugin(Plugin):
    PLUGINNAME = 'TSAR - Automated backbone assignment'
    guiModule = TsarGuiPlugin

    def run(self, **kwargs):
        ''' Insert here the script for running Tsar '''
        print('Running TSAR', kwargs)


#TsarPlugin.register()  # Registers the pipe in the pluginList
