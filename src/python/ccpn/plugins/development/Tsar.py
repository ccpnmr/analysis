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
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Chris Spronk $"
__date__ = "$Date: 2017-11-28 10:28:42 +0000 (Tue, Nov 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#=========================================================================================
# TODO
# Catch exceptions in case no valid spectra are in the project, now the plugin doesn't open
# when no spectra are in the project
# Output path selection ? If not default
# Tsar installation path ? if not default
# support for 4D and 5D data sets, including tolerance and nucleus selection
# import of Tsar results (assigned peak lists in nef format)
#=========================================================================================




import os,copy,json,pprint,math,shutil
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
columnWidths = [150,100,75,100,75]

# Set some tooltip texts
help = {'Run name': 'Name of the run directory. Spaces will be converted to "_"',
        'Run path': 'Path in which the run directory will be created. Relative to the project path.',
        'Chains': 'Check chains from which to calculate structures',
        'Is IDP': 'Check if protein is intrinsically disordered.',
        'Spectrum': 'Select basis spectrum and check backbone spectra to use.',
        'Basis spectrum': 'Select basis spectrum.',
        'Backbone spectrum': 'Check backbone spectrum to include.',
        'Peak list': 'Select peak list.',
        '13C tolerance': 'Recommended value = spectral width (Hz) / (number of increments * spectrometer frequency (MHz). Default setting taken from spectrum tolerances.',
        'Peak sign': 'Peak sign, e.g.: p = positive, n = negative, u = unknown.',
        'Opposite sign': 'Tsar notation for residues with opposite sign and their relative position, e.g. "G -1", "VIDNASCYF -1"',
        'Setup': 'Sets up the project directory structure and scripts.',
        'Write': 'Writes the current settings in JSON and human readable format to the project notes, with the run name as title',
        'Run': 'Runs the calculations.',
        'Import': 'Imports the results. Wait for calculations to finish.'
        }


# Set the basis and backbone assignment experiment type synonyms as valid inputs
# The Tsar basis experiment is typically:
#  - 15N-HSQC for 3D/4D based automated assignment (HNCO preferred for 4D)
#  - 3D HNCO for 4D and 5D based automated assignment
# Backbone experiments currently implemented for 3D based assignment are organised in this dictionary.
# The dictionary contains the nuclei for chemical shift matches with their peak signs, and the experiment axis matches
# Peak sign values in Tsar can be 'p', 'n', 'u' for positive, negative and unknown
# The list of experiment can be expanded as Tsar can handle any type, see Tsar manual.
# Peak signs are not needed for basis experiments, only connectivities.
# Atom nomenclature follows IUPAC, so HN --> H, in contrast to Tsar HN

tsarBasisExperiments    = ['15N HSQC/HMQC','HNCO']
tsarBackboneExperiments = ['HNCO','HNcaCO','HNcoCA','HNCA','hbCB/haCAcoNH','HNcoCA/CB','HNCA/CB']

# Tsar experiments.
# Peak signs per nuclei contain default peak sign and residues with opposite sign as in Tsar definition style:
# i.e. sequence of residues in one-letter capitalised, followed by relative position: 'G -1' or 'VIDNASCYF -1'
# Comma separated when multiple relative positions are possible, e.g.: 'VIDNASCYF -1, 'W -2' (check if this actually happens.

# Cross sections are lists: [connectivity,sign,opposite sign]
# In case of multiple connectivities involving the same nucleus, add _0, _-1 etcetera
tsarExperimentDict   = {'15N HSQC/HMQC': {'Axes':           {'Hn': 'H', 'Nh': 'N'},
                                          'Basis':          {'Hn': 0, 'Nh': 0},
                                          'Connectivities': {}
                                         },
                        'HNCO':          {'Axes':           {'Hn': 'H', 'Nh': 'N', 'CO': 'CO'},
                                          'Basis':          {'Hn': 0, 'Nh': 0},
                                          'Connectivities': {'CO': [-1,'p','-']}
                                         },
                        'HNcaCO':        {'Axes':           {'Hn': 'H', 'Nh': 'N', 'CO': 'CO'},
                                          'Basis':          {'Hn': 0, 'Nh': 0},
                                          'Connectivities': {'CO': [0,'p','-']}
                                         },
                        'HNcoCA':        {'Axes':           {'Hn': 'H', 'Nh': 'N', 'CA': 'CA'},
                                          'Basis':          {'Hn': 0, 'Nh': 0},
                                          'Connectivities': {'CA': [-1,'p','-']}
                                         },
                        'HNCA':          {'Axes':           {'Hn': 'H', 'Nh': 'N', 'CA': ['CA_0','CA_-1']},
                                          'Basis':          {'Hn': 0, 'Nh': 0},
                                          'Connectivities': {'CA_0':  [0,'p','-'],
                                                             'CA_-1': [-1,'p','-']}
                                         },
                        'hbCB/haCAcoNH': {'Axes':           {'Hn': 'H', 'Nh': 'N', 'Ch': ['CA','CB']},
                                          'Basis':          {'Hn': 0, 'Nh': 0},
                                          'Connectivities': {'CA': [-1,'p','-'],
                                                             'CB': [-1,'p','-']}
                                         },
                        'HNcoCA/CB':     {'Axes':           {'Hn': 'H', 'Nh': 'N', 'C': ['CA','CB']},
                                          'Basis':          {'Hn': 0, 'Nh': 0},
                                          'Connectivities': {'CA': [-1,'p','-'],
                                                             'CB': [-1,'p','-']}
                                         },
                        'HNCA/CB':       {'Axes':           {'Hn': 'H', 'Nh': 'N', 'C': ['CA_0','CA_-1','CB_0','CB_-1']},
                                          'Basis':          {'Hn': 0, 'Nh': 0},
                                          'Connectivities': {'CA_0':  [0,'p','-'],
                                                             'CA_-1': [-1,'p','-'],
                                                             'CB_0':  [0,'n','-'],
                                                             'CB_-1': [-1,'n','-']
                                                            }
                                         }
                        }



class TsarGuiPlugin(PluginModule):

    className = 'TSAR'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super(TsarGuiPlugin, self)
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

        self.pluginPath = os.path.join(self.project.path,TsarGuiPlugin.className)

        # Create ORDERED dictionary to store all parameters for the run
        # deepcopy doesn't work on dictionaries with the qt widgets, so to get a separation of gui widgets and values for storage
        # it is needed to create the two dictionaries alongside each other
        self.guiDict  = OD([('General',OD()), ('Chains',OD()), ('Basis spectrum', OD()), ('Backbone spectra', OD())])
        self.settings = OD([('General',OD()), ('Chains',OD()), ('Basis spectrum', OD()), ('Backbone spectra', OD())])

        # Set the basis type synonyms as valid inputs
        self.basisSpectra = [self.project.spectra[i].id for i in range(len(self.project.spectra))
                             if self.project.spectra[i].synonym in tsarBasisExperiments]

        # Spectrum ids are unique. For easier lookup later, duplicate ExperimentTypes info with spectrum id as keys
        # Easier for later extraction and export to NEF
        for i in range(len(self.project.spectra)):
            if self.project.spectra[i].synonym in tsarBackboneExperiments:
                self.guiDict['Backbone spectra'][self.project.spectra[i].id] = OD()
                self.settings['Backbone spectra'][self.project.spectra[i].id] = OD()

        # Input check
        validInput = self._inputDataCheck()
        if not validInput:
            return

        # Run name
        grid = 0,0
        widget = Label(self.scrollAreaLayout,text='Run name', grid=grid,tipText=help['Run name'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = LineEdit(self.scrollAreaLayout, text = 'Run_1', grid=grid,tipText=help['Run name'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        self.guiDict['General']['Run name'] = widget
        self.settings['General']['Run name'] = self._getValue(widget)

        # Set molecular chains, use checkboxes with own labels
        grid = _addVerticalSpacer(self.scrollAreaLayout,grid)
        grid = _addRow(grid)

        widget = Label(self.scrollAreaLayout,text='Molecular chains', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        for chain in sorted(self.project.chains):
            grid = _addColumn(grid)
            # Check whether to use the name, id or serial, docs are confusing here
            widget = CheckBox(self.scrollAreaLayout, text=chain.shortName, checked=True, grid=grid, tipText=help['Chains'])
            _setWidgetProperties(widget,_setWidth(columnWidths,grid))
            self.guiDict['Chains'][chain.id] = OD([('Active', widget)])
            self.settings['Chains'][chain.id] = OD([('Active', self._getValue(widget))])

        # Folded protein or IDP selection
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout,text='Folding state', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = CheckBox(self.scrollAreaLayout, text='Is IDP', checked=False, grid=grid, tipText=help['Is IDP'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        self.guiDict['General']['Folding state'] = widget
        self.settings['General']['Folding state'] = self._getValue(widget)

        # Create header row for clean plugin content organisation
        grid = _addVerticalSpacer(self.scrollAreaLayout,grid)
        for header in ['Spectrum', 'Peak list', '13C tolerance']:
            grid = _addColumn(grid)
            widget = Label(self.scrollAreaLayout, text=header, grid=grid, tipText=help[header])
            _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout, text='Peak', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid), hAlign='r')
        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout, text='Sign', grid=grid, tipText=help['Peak sign'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        grid = _addColumn(grid)
        widget = Label(self.scrollAreaLayout, text='Opposite sign', grid=grid, tipText=help['Opposite sign'])
        _setWidgetProperties(widget,width=100)

        # Set basis spectrum
        grid = _addRow(grid)
        widget = Label(self.scrollAreaLayout, text='Basis spectrum', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        # Basis spectrum selection updates the peak list pulldown using spectrum selection function.
        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, callback=self._selectBasisPeaklist, tipText=help['Basis spectrum'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        widget.setData(self.basisSpectra)
        self.guiDict['Basis spectrum']['SpectrumId'] = widget
        self.settings['Basis spectrum']['SpectrumId'] = self._getValue(widget)

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, tipText=help['Peak list'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        self.guiDict['Basis spectrum']['Peak list'] = widget
        self.settings['Basis spectrum']['Peak list'] = self._getValue(widget)
        # Invoke the callback function to catch the selection in case only one spectrum is available as basisExperiment

        if self.basisSpectra:
            self._selectBasisPeaklist(self.basisSpectra[0])

        # Add the backbone spectra
        grid = _addVerticalSpacer(self.scrollAreaLayout,grid)

        # Create a header, depending on the type of spectra in the project
        widget = Label(self.scrollAreaLayout, text='Backbone spectra', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        # Add the backbone spectra, and tolerances depending on the selected basis experiment
        # Basis spectrum callback will need adaptation for 4D / 5D
        basisSpectrum = self._spectrumId2Spectrum(self.settings['Basis spectrum']['SpectrumId'])
        for spectrumId in sorted(self.settings['Backbone spectra']):
            spectrum = self._spectrumId2Spectrum(spectrumId)

            grid = _addColumn(grid)
            widget = CheckBox(self.scrollAreaLayout, text=spectrumId, checked=True, grid=grid,callback=partial(self._selectBackbonePeaklist, spectrumId), tipText=help['Backbone spectrum'])
            _setWidgetProperties(widget,_setWidth(columnWidths,grid))
            self.guiDict['Backbone spectra'][spectrumId]['Active'] = widget
            self.settings['Backbone spectra'][spectrumId]['Active'] = self._getValue(widget)

            grid = _addColumn(grid)
            widget = PulldownList(self.scrollAreaLayout, grid=grid, tipText=help['Peak list'])
            _setWidgetProperties(widget,_setWidth(columnWidths,grid))
            self.guiDict['Backbone spectra'][spectrumId]['Peak list'] = widget
            self.settings['Backbone spectra'][spectrumId]['Peak list'] = self._getValue(widget)
            self._selectBackbonePeaklist(spectrumId)

            # Tolerances
            if spectrum.dimensionCount == 3 and basisSpectrum.synonym == '15N HSQC/HMQC':
                # In case of 3D spectra, we only need one tolerance, for the Carbon
                # Check which is the carbon dimension
                tolerance = spectrum.assignmentTolerances[spectrum.isotopeCodes.index('13C')]

                grid = _addColumn(grid)
                widget = DoubleSpinbox(self.scrollAreaLayout, value=tolerance, step=0.05, decimals=3,grid=grid, tipText=help['13C tolerance'])
                _setWidgetProperties(widget,_setWidth(columnWidths,grid), hAlign='r')
                widget.setButtonSymbols(2)
                self.guiDict['Backbone spectra'][spectrumId]['Tolerance1'] = widget
                self.settings['Backbone spectra'][spectrumId]['Tolerance1'] = self._getValue(widget)

            else:
                # This needs expansion when 4D/5D is included, for now we limit to 3D
                grid = _addColumn(grid)
                widget = DoubleSpinbox(self.scrollAreaLayout, value=tolerance, step=0.05, decimals=3,grid=grid, tipText=help['13C tolerance'])
                _setWidgetProperties(widget,_setWidth(columnWidths,grid), hAlign='r')
                widget.setButtonSymbols(2)
                self.guiDict['Backbone spectra'][spectrumId]['Tolerance1'] = widget
                self.settings['Backbone spectra'][spectrumId]['Tolerance1'] = self._getValue(widget)

                grid = _addColumn(grid)
                widget = DoubleSpinbox(self.scrollAreaLayout, value=tolerance, step=0.05, decimals=3,grid=grid, tipText=help['13C tolerance'])
                _setWidgetProperties(widget,_setWidth(columnWidths,grid), hAlign='r')
                widget.setButtonSymbols(2)
                self.guiDict['Backbone spectra'][spectrumId]['Tolerance2'] = widget
                self.settings['Backbone spectra'][spectrumId]['Tolerance2'] = self._getValue(widget)

            # Peak signs
            listValues = ['p', 'n', 'u']
            experiment = tsarExperimentDict[spectrum.synonym]
            cnt = 0
            self.guiDict['Backbone spectra'][spectrumId]['Peak signs'] = OD([])
            self.settings['Backbone spectra'][spectrumId]['Peak signs'] = OD([])

            for connectivity in sorted(experiment['Connectivities']):
                if cnt > 0:
                    grid = (grid[0]+1,3)

                # Set the default value to start with
                nucleus             = connectivity.split('_')[0]
                label               = '{0} {1:>2}'.format(nucleus,experiment['Connectivities'][connectivity][0])
                defaultSign         = experiment['Connectivities'][connectivity][1]
                defaultOppositeSign = experiment['Connectivities'][connectivity][2]

                grid = _addColumn(grid)
                widget = Label(self.scrollAreaLayout, text=label, grid=grid)
                _setWidgetProperties(widget,_setWidth(columnWidths,grid), hAlign='r')

                grid = _addColumn(grid)
                widget = PulldownList(self.scrollAreaLayout, texts=listValues, grid=grid, tipText=help['Peak sign'])
                widget.setCurrentIndex(listValues.index(defaultSign))
                _setWidgetProperties(widget,_setWidth(columnWidths,grid), hAlign='c')
                if connectivity not in self.guiDict['Backbone spectra'][spectrumId]['Peak signs']:
                    self.guiDict['Backbone spectra'][spectrumId]['Peak signs'][connectivity] = OD([('Sign', widget)])
                    self.settings['Backbone spectra'][spectrumId]['Peak signs'][connectivity] = OD([('Sign', self._getValue(widget))])
                else:
                    self.guiDict['Backbone spectra'][spectrumId]['Peak signs'][connectivity]['Sign'] = widget
                    self.settings['Backbone spectra'][spectrumId]['Peak signs'][connectivity]['Sign'] = self._getValue(widget)

                # Add residues with opposite peak sign
                grid = _addColumn(grid)
                widget = LineEdit(self.scrollAreaLayout, text=defaultOppositeSign, grid=grid, tipText=help['Opposite sign'])
                _setWidgetProperties(widget,width=100)
                self.guiDict['Backbone spectra'][spectrumId]['Peak signs'][connectivity]['Opposite sign'] = widget
                self.settings['Backbone spectra'][spectrumId]['Peak signs'][connectivity]['Opposite sign'] = self._getValue(widget)
                cnt += 1
            grid = _addRow(grid)
            grid = _addVerticalSpacer(self.scrollAreaLayout, grid)

        # Action buttons: Set up, Run, import
        grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
        grid = _addColumn(grid)
        texts = ['Set up project', 'Write settings', 'Run calculation', 'Import results']
        tipTexts = [help['Setup'], help['Write'], help['Run'], help['Import']]
        # callbacks = [self._setupProject, partial(self._writeSettings,''), self._runCalculation, self._importResults]
        callbacks = [self._setupProject, self._writeSettings, self._runCalculation, self._importResults]
        widget = ButtonList(parent=self.scrollAreaLayout, texts=texts, callbacks=callbacks, tipTexts=tipTexts, grid=grid, gridSpan=(1,6))
        _setWidgetProperties(widget,_setWidth(columnWidths,grid),heightType='Minimum')

        Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0]+1, 10),
               gridSpan=(1, 1))

    def _inputDataCheck(self):
        # Checks available input data at plugin start

        return True

        inputWarning = ''
        if len(self.project.chains) == 0:
            inputWarning += 'No molecular chains found in the project\n'
        if len(self.basisSpectra) == 0:
            inputWarning += 'No valid basis spectrum found in the project\n'
        if len(self.settings['Backbone spectra']) == 0:
            inputWarning += 'No valid backbone spectra found in the project\n'
        if inputWarning != '':
            showWarning('Warning',inputWarning)
            #self._closeModule()
            self.deleteLater()
            return False
        return True

    def _runDataCheck(self):
        # Checks data before run time
        inputWarning = ''
        chains = 0
        spectra = 0

        # for i in ['Run name','Run path']:
        #     if len(self.settings['General'][i].strip()) == 0:
        #         inputWarning += 'No {0} specified\n'.format(i)
        #     if len(self.settings['General'][i].split()) > 1:
        #         inputWarning += '{0} may not contain spaces\n'.format(i)
        if len(self.settings['General']['Run name'].strip()) == 0:
            inputWarning += 'No run name specified\n'
        if len(self.settings['General']['Run name'].split()) > 1:
            inputWarning += 'Run name may not contain spaces\n'

        for pid in self.exportPidList:
            if 'MC' in pid:
                chains += 1
            if 'PL' in pid:
                spectra += 1
        if chains == 0:
            inputWarning += 'No molecular chains selected\n'
        if spectra <= 1:
            # Backbone peak list is always in, the plugin doesn't start without backbone spectrum
            inputWarning += 'No backbone spectra selected\n'
        if inputWarning != '':
            showWarning('Warning',inputWarning)
            setupComplete = False
        else:
            setupComplete = True
        return setupComplete

    def _spectrumId2Spectrum(self,spectrumId):
        if spectrumId:
            return self.project.getByPid('SP:'+spectrumId)

    def _selectBasisPeaklist(self,spectrumId):
        spectrum = self._spectrumId2Spectrum(spectrumId)
        widget = self.guiDict['Basis spectrum']['Peak list']
        widget.setData([str(PL.serial) for PL in spectrum.peakLists])
        self.settings['Basis spectrum']['Peak list'] = self._getValue(widget)

    def _selectBackbonePeaklist(self, spectrumId):
        if self.guiDict['Backbone spectra'][spectrumId]['Active'].isChecked():
            spectrum = self._spectrumId2Spectrum(spectrumId)

            widget = self.guiDict['Backbone spectra'][spectrumId]['Peak list']
            widget.setData([str(PL.serial) for PL in spectrum.peakLists])
            widget.setEnabled(True)
            self.settings['Backbone spectra'][spectrumId]['Peak list'] = self._getValue(widget)

        else:
            widget = self.guiDict['Backbone spectra'][spectrumId]['Peak list']
            widget.setEnabled(True)

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

    def _writeSettings(self):
        # Get values from the GUI widgets and save in the settings
        self._updateSettings(self.guiDict, self.settings)
        # Create a data block of the regular CCPN objects, which would normally be exported directly.
        self._createPidList()
        # Check if all input requirements are met
        setupComplete = self._runDataCheck()

        if setupComplete == True:
            # Creates a JSON string and a cleaned up human readable string, both added to notes, in a single note
            jsonString = json.dumps(self.settings,indent=4)

            s = pprint.pformat(jsonString)
            n = ''
            maxChars = 0
            for line in s.split('\n'):
                for char in ['"','{','}',',',"'",'(',')','\\']:
                    line = line.replace(char,'')
                # Remove preceding 5 spaces and \n without removing newline
                line = line[5:-1].rstrip(' ') + '\n'
                if len(line.split(':')[0]) > maxChars:
                    maxChars = len(line)
                # Don't write unnecessary empty newlines
                if not len(line.split()) == 0:
                    n += line

            # Justify key and values nicely
            formatted = ''
            for line in n.split('\n'):
                try:
                    k,v = line.split(':')
                    line = '{0}{1}\n'.format((k + ':').ljust(maxChars + 4), v)
                    # For non mono spaced fonts we need to convert spaces to tabs, but tab locations in the notes are different
                    # from the editor, where this method works:
                    # nTabs = math.ceil((maxChars - len(k))/4)
                    # line = '{0}{1}{2} {3} {4} {5}\n'.format(k+':',nTabs*'\t', str(v).strip(), len(k), maxChars, nTabs)
                except ValueError:
                    pass
                formatted += line

            noteTitle = '{0} - Tsar'.format(self.settings['General']['Run name'])
            note = self.project.newNote(noteTitle)
            note.text = formatted + '\n\nJSON format:\n\n' + jsonString
            showMessage('Message', 'Created project note {0}'.format(noteTitle))

    def _createPidList(self):

        # Get basis experiment
        self.basisSpectrumId         = self.settings['Basis spectrum']['SpectrumId']
        self.basisSpectrumPeakListId = self.settings['Basis spectrum']['Peak list']
        self.basisSpectrum           = self._spectrumId2Spectrum(self.basisSpectrumId)

        # 1.
        # Create the list of standard project objects to be written, which is a list of their pids
        self.exportPidList = []

        # Add sequence pids:
        # We only support a single chain for the moment, hetero multimers would require writing all chains
        for chainId in self.settings['Chains']:
            if self.settings['Chains'][chainId]['Active'] == True:
                self.exportPidList.append('MC:' + chainId)

        # Add peak lists
        # Basis spectrum peak list
        self.exportPidList.append('PL:{0}.{1}'.format(self.basisSpectrumId,self.basisSpectrumPeakListId))
        # Backbone spectra peak lists
        for spectrumId in self.settings['Backbone spectra']:
            if self.settings['Backbone spectra'][spectrumId]['Active'] == True:
                self.exportPidList.append('PL:{0}.{1}'.format(spectrumId,self.settings['Backbone spectra'][spectrumId]['Peak list']))

    def _convertNefToDataBlock(self):
        # Convert the standard NEF data to a Data block
        self.dataBlock = self.project._convertToDataBlock(skipPrefixes=(), expandSelection=False,pidList=self.exportPidList)

    def _createConnectivities(self,spectrum):

        connectivities    = []
        peakSigns         = []
        peakOppositeSigns = []

        # Basis connectivities, no connectivities
        if tsarExperimentDict[spectrum.synonym]['Connectivities'] == {}:
            s = ''
            for axisCode in spectrum.axisCodes:
                s += '{0} {1} '.format(tsarExperimentDict[spectrum.synonym]['Axes'][axisCode],tsarExperimentDict[spectrum.synonym]['Basis'][axisCode])
            connectivities.append(s.strip())

        else:
            for connectivity in sorted(tsarExperimentDict[spectrum.synonym]['Connectivities']):
                s = ''
                for axisCode in spectrum.axisCodes:
                    if axisCode in tsarExperimentDict[spectrum.synonym]['Basis']:
                        nucleus = tsarExperimentDict[spectrum.synonym]['Axes'][axisCode]
                        s += '{0} {1} '.format(nucleus,tsarExperimentDict[spectrum.synonym]['Basis'][axisCode])
                    else:
                        nucleus = connectivity.split('_')[0]
                        s += '{0} {1} '.format(nucleus,tsarExperimentDict[spectrum.synonym]['Connectivities'][connectivity][0])
                        # Peak signs and opposite signs need to be taken from self.settings
                        peakSigns.append(self.settings['Backbone spectra'][spectrum.id]['Peak signs'][connectivity]['Sign'])
                        peakOppositeSigns.append(self.settings['Backbone spectra'][spectrum.id]['Peak signs'][connectivity]['Opposite sign'])
                connectivities.append(s.strip())
        return connectivities,peakSigns,peakOppositeSigns

    def _addTsarBlocks(self):
        # Get Run name
        runName = self.settings['General']['Run name'].strip()

        # Get IDP state (y/n)
        if self.settings['General']['Folding state'] == True:
            self.isIdp = 'y'
        else:
            self.isIdp = 'n'

        # NEFS removed because they are not in NEF definitions yet
        sf_category = 'ccpn_tsar_run'
        sf_framecode = sf_category+'_settings'
        newSaveFrame = SaveFrame(name=sf_framecode)
        newSaveFrame.addItem('_{0}.sf_category'.format(sf_category),sf_category)
        newSaveFrame.addItem('_{0}.sf_framecode'.format(sf_category),sf_framecode)
        newSaveFrame.addItem('_{0}.name'.format(sf_category),runName)
        self.dataBlock.addItem(sf_category, newSaveFrame)

        sf_category = 'ccpn_tsar_folding_state'
        sf_framecode = sf_category + '_settings'
        newSaveFrame = SaveFrame(name=sf_framecode)
        newSaveFrame.addItem('_{0}.sf_category'.format(sf_category),sf_category)
        newSaveFrame.addItem('_{0}.sf_framecode'.format(sf_category),sf_framecode)
        newSaveFrame.addItem('_{0}.isIDP'.format(sf_category),self.isIdp)
        self.dataBlock.addItem(sf_category, newSaveFrame)

        sf_category = 'ccpn_tsar_basis_spectrum'
        sf_framecode = sf_category + '_{0}'.format(self.basisSpectrumId)
        newSaveFrame = SaveFrame(name=sf_framecode)
        newSaveFrame.addItem('_{0}.sf_category'.format(sf_category),sf_category)
        newSaveFrame.addItem('_{0}.sf_framecode'.format(sf_category),sf_framecode)

        connectivities, peakSigns, peakOppositeSigns = self._createConnectivities(self.basisSpectrum)
        newSaveFrame.addItem('_{0}.connectivities'.format(sf_category),connectivities)
        self.dataBlock.addItem(sf_category, newSaveFrame)

        # Add Tsar spectrum to connectivity mappings
        for spectrumId in sorted(self.settings['Backbone spectra']):
            if self.settings['Backbone spectra'][spectrumId]['Active'] == True:
                spectrum = self._spectrumId2Spectrum(spectrumId)
                sf_category = 'ccpn_tsar_backbone_spectrum'
                sf_framecode = sf_category + '_{0}'.format(spectrumId)
                newSaveFrame = SaveFrame(name=sf_framecode)
                newSaveFrame.addItem('_{0}.sf_category'.format(sf_category), sf_category)
                newSaveFrame.addItem('_{0}.sf_framecode'.format(sf_category), sf_framecode)

                connectivities, peakSigns, peakOppositeSigns = self._createConnectivities(spectrum)
                newSaveFrame.addItem('_{0}.connectivities'.format(sf_category),connectivities)
                newSaveFrame.addItem('_{0}.peak_signs'.format(sf_category),peakSigns)
                newSaveFrame.addItem('_{0}.opposite_signs'.format(sf_category),peakOppositeSigns)
                newSaveFrame.addItem('_{0}.13C_tolerance'.format(sf_category), '{0:.3f}'.format(self.settings['Backbone spectra'][spectrumId]['Tolerance1']))

                self.dataBlock.addItem(sf_framecode, newSaveFrame)

    def _exportNef(self):
        # self.outputPath = os.path.join(self.settings['General']['Run path'], '{0}.nef'.format(self.settings['General']['Run name']))
        # self.project._writeDataBlockToFile(dataBlock=self.dataBlock, path=self.outputPath, overwriteExisting=True)
        self.project._writeDataBlockToFile(dataBlock=self.dataBlock, path=os.path.join(self.runPath, '{0}.nef'.format(self.settings['General']['Run name'])), overwriteExisting=True)

    def _setupProject(self):
        # Get values from the GUI widgets and save in the settings
        self._updateSettings(self.guiDict, self.settings)
        # Create a data block of the regular CCPN objects, which would normally be exported directly.
        self._createPidList()
        # Check if all input requirements are met
        setupComplete = self._runDataCheck()

        # Check if tree exists, and if to overwrite
        # Set the run path
        self.runPath = os.path.join(self.pluginPath,self.settings['General']['Run name'])

        if setupComplete == True:
            if os.path.exists(self.runPath):
                overwrite = showYesNo('Warning', 'Run {0} exists. Overwrite?'.format(self.settings['General']['Run name']))
                if overwrite == False:
                    showMessage('Message', 'Project set up aborted')
                    return

                if overwrite == True:
                    shutil.rmtree(self.runPath)

            # Create a (new) directory tree
            self._createRunTree()
            # Convert data to NEF
            self._convertNefToDataBlock()
            # Add the calculation specific data blocks that describe additional input parameters
            self._addTsarBlocks()
            # Export the NEF file as input for Tsar
            self._exportNef()
            showMessage('Message', 'Project set up complete')

    def _createRunTree(self):
        if not os.path.exists(self.pluginPath):
            os.makedirs(self.pluginPath)

        if not os.path.exists(self.runPath):
            os.makedirs(self.runPath)

    def _runCalculation(self):
        # Check on presence of complete set up
        pass

    def _importResults(self):
        # Check on presence of completed calculation
        pass

class TsarPlugin(Plugin):
    PLUGINNAME = 'TSAR2 - Automated backbone assignment'
    guiModule = TsarGuiPlugin

    def run(self, **kwargs):
        ''' Insert here the script for running Tsar '''
        print('Running TSAR', kwargs)


# TsarPlugin.register()  # Registers the pipe in the pluginList
# Set tolerances from project.spectrum.tolerances by default
