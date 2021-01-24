#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-01-24 17:58:24 +0000 (Sun, January 24, 2021) $"
__version__ = "$Revision: 3.0.3 $"
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
# Output path selection ? If not default
#
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
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning, showMessage, showYesNo
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.nef import GenericStarParser, StarIo
from ccpn.util.nef.GenericStarParser import SaveFrame, DataBlock, DataExtent, Loop, LoopRow
from functools import partial
import multiprocessing

############
# Settings #
############

# Widths in pixels for nice widget alignments, length depends on the number of fixed columns in the plugin.
# Variable number of columns will take the last value in the list
columnWidths = [100,200,75]

# Set some tooltip texts
help = {'Run name': 'Name of the run directory. Spaces will be converted to "_"',
        'Run path': 'Path in which the run directory will be created. Relative to the project path.',
        'Chains': 'Check chains from which to calculate structures',
        'Restraint list': 'Check restraint lists to use',
        'Final weight': 'Weights during log normal solvent refinement phase.\nWeights are relative to distance restraints',
        'Rdc magnitude': 'Rdc tensor magnitude',
        'Rdc rhombicity': 'Rdc tensor rhombicity',
        'Karplus A': 'Karplus equation coefficient A',
        'Karplus B': 'Karplus equation coefficient B',
        'Karplus C': 'Karplus equation coefficient C',
        'Karplus P': 'Karplus equation phase',
        'Engine': 'Check structure calculation engines to use',
        'Generate': 'Number of conformers to generate.',
        'Keep': 'Number of best conformers to keep.',
        'MD Steps': 'Total number of MD Steps throughout the protocol.',
        'CPUs': 'Number of CPU threads to use per engine. Calculations are run in series.',
        'Setup': 'Sets up the project directory structure and scripts.',
        'Write': 'Writes the current settings in JSON and human readable format to the project notes, with the run name as title',
        'Run': 'Runs the calculations.',
        'Import': 'Imports the results. Wait for calculations to finish.'
        }


# Parameters related to calculation engines:
# Get number of available threads on the current machine, and set maximum allowed threads (e.g. to use for runs on clusters)
threads      = multiprocessing.cpu_count()
maxThreads   = 128

# Set Rdc default parameters
rdcParameters = {'Rdc magnitude': 0.00000,
                 'Rdc rhombicity': 0.00000
                }

# Set Karplus default parameters:
karplusParameters = {'Karplus A': 6.98,
                     'Karplus B': -1.38,
                     'Karplus C': 1.72,
                     'Karplus P': -60.00
                    }

# Set the structure calculation engines and MD Steps per residue
# MD Steps per residue is a way to set the number of steps for the calculations, with the idea being larger protein needs more steps.
# Assume linear increase (check with authors of packages). We take conservative values, and round up to the next multiple of 5000.
#

# Set supported restraint types per engine, or will engine skip non-supproted rstraints in the NEF file?
calculationEngines = {'CYANA':     {'MD Steps': 100, 'Generate': 100, 'Keep': 20, 'Restraint types': 'All'},
                      'XPLOR-NIH': {'MD Steps': 100, 'Generate': 60, 'Keep': 20, 'Restraint types': 'All'},
                      'CNS':       {'MD Steps': 200, 'Generate': 60, 'Keep': 20, 'Restraint types': 'All'},
                      'YARIA':     {'MD Steps': None, 'Generate': 40, 'Keep': 20, 'Restraint types': ['Distance','Dihedral','Rdc']},
                     }

refineRelativeWeights = {'Rdc': 0.01, 'JCoupling': 0.01}

# Define the restraint types available in CCPN to use here (subset of all possibilities, check which other ones are available)
# Hbond restraints are in Distance restraints class, with different origin. Can be picked up by restraintList.origin (If defined I guess)
# restraintTypes         = ['Distance','Dihedral','Rdc','JCoupling','ChemicalShift','Csa']
# We may restrict the restraintTypes here for the time being, since some engines may not be able to deal with all types

class StructureFromRestraintsGuiPlugin(PluginModule):

    className = 'StructureFromRestraints'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super(StructureFromRestraintsGuiPlugin, self)
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

        self.pluginPath = os.path.join(self.project.path,StructureFromRestraintsGuiPlugin.className)

        # Create ORDERED dictionary to store all parameters for the run
        # deepcopy doesn't work on dictionaries with the qt widgets, so to get a separation of gui widgets and values for storage
        # it is needed to create the two dictionaries alongside each other
        self.guiDict  = OD([('General',OD()), ('Chains',OD()), ('Restraints', OD()), ('Engines', OD())])
        self.settings = OD([('General',OD()), ('Chains',OD()), ('Restraints', OD()), ('Engines', OD())])

        # for restraintType in restraintTypes:
        for restraintList in self.project.restraintLists:
            # Separate Hbonds from distance restraints
            restraintType = restraintList.restraintType
            try:
                if restraintType == 'Distance' and restraintList.origin.upper() == 'HBOND':
                    restraintType = 'Hbond'
            except AttributeError:
                pass

            if restraintType not in self.settings['Restraints']:
                self.guiDict['Restraints'][restraintType] = OD([(restraintList.id, OD())])
                self.settings['Restraints'][restraintType] = OD([(restraintList.id, OD())])
            else:
                self.guiDict['Restraints'][restraintType][restraintList.id]= OD()
                self.settings['Restraints'][restraintType][restraintList.id] = OD()

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

        # # Run path
        # grid = _addRow(grid)
        # widget = Label(self.scrollAreaLayout,text='Run path', grid=grid,tipText=help['Run path'])
        # _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        #
        # grid = _addColumn(grid)
        # widget = LineEditButtonDialog(self.scrollAreaLayout,fileMode=QtGui.QFileDialog.Directory,grid=grid, gridSpan=(2,2),tipText=help['Run path'])
        # _setWidgetProperties(widget,columnWidths[1]+columnWidths[2],heightType='Minimum')
        # self.guiDict['General']['Run path'] = widget
        # self.settings['General']['Run path'] = self._getValue(widget)

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

        # Create header row for Distance, Hbond and Dihedral restraints
        grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
        widget = Label(self.scrollAreaLayout, text='Restraints', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        for header in ['Restraint list', 'Final weight']:
            grid = _addColumn(grid)
            widget = Label(self.scrollAreaLayout, text=header, grid=grid, tipText=help[header])
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        # for restraintType in sorted(self.settings['Restraints']):
        for restraintType in ['Distance', 'Hbond', 'Dihedral']:
            if restraintType in self.settings['Restraints']:
                grid = _addRow(grid)
                widget = Label(self.scrollAreaLayout, text=restraintType, grid=grid)
                _setWidgetProperties(widget, _setWidth(columnWidths, grid))

                for restraintListId in sorted(self.settings['Restraints'][restraintType]):
                    grid = _addColumn(grid)
                    widget = CheckBox(self.scrollAreaLayout, text=restraintListId, checked=True, grid=grid,tipText=help['Restraint list'])
                    _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                    self.guiDict['Restraints'][restraintType][restraintListId] = OD([('Active', widget)])
                    self.settings['Restraints'][restraintType][restraintListId] = OD([('Active', self._getValue(widget))])

                    grid = _addColumn(grid)
                    widget = Label(self.scrollAreaLayout, text='Auto', grid=grid, tipText=help['Final weight'])
                    _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                    grid = _addRow(grid)

        restraintType = 'Rdc'
        if restraintType in self.settings['Restraints']:
            # Create header row for RDC restraints
            grid = (grid[0] + 1, 2)
            # Add extra parameters
            for i in rdcParameters:
                grid = _addColumn(grid)
                widget = Label(self.scrollAreaLayout, text='{0}'.format(i), grid=grid, tipText=help[i])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            grid = _addRow(grid)

            widget = Label(self.scrollAreaLayout, text=restraintType, grid=grid)
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            for restraintListId in sorted(self.settings['Restraints'][restraintType]):
                grid = _addColumn(grid)
                widget = CheckBox(self.scrollAreaLayout, text=restraintListId.name, checked=True, grid=grid,tipText=help['Restraint list'])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                self.guiDict['Restraints'][restraintType][restraintListId] = OD([('Active', widget)])
                self.settings['Restraints'][restraintType][restraintListId] = OD([('Active', self._getValue(widget))])

                grid = _addColumn(grid)
                widget = DoubleSpinbox(self.scrollAreaLayout, value=refineRelativeWeights[restraintType], step=0.01,decimals=3, grid=grid, tiptext=help['Final weight'])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                # Remove arrows from double spinbox widget
                widget.setButtonSymbols(2)
                self.guiDict['Restraints'][restraintType][restraintListId]['Final weight'] = widget
                self.settings['Restraints'][restraintType][restraintListId]['Final weight'] = self._getValue(widget)

                # Add extra parameters with same default values
                for i in rdcParameters:
                    grid = _addColumn(grid)
                    widget = DoubleSpinbox(self.scrollAreaLayout, value=rdcParameters[i]['value'], step=0.00001,decimals=5, grid=grid, tiptext=help[i])
                    _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                    # Remove arrows from double spinbox widget
                    widget.setButtonSymbols(2)
                    self.guiDict['Restraints'][restraintType][restraintListId][i] = widget
                    self.settings['Restraints'][restraintType][restraintListId][i] = self._getValue(widget)

                grid = _addRow(grid)

        restraintType = 'JCoupling'
        if restraintType in self.settings['Restraints']:
            # Create header row for JCoupling restraints
            grid = (grid[0] + 1, 2)

            # Add headers for extra parameters
            for i in karplusParameters:
                grid = _addColumn(grid)
                widget = Label(self.scrollAreaLayout, text='{0}'.format(i), grid=grid, tipText=help[i])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid))

            grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
            widget = Label(self.scrollAreaLayout, text=restraintType, grid=grid, tipText=help['Restraint list'])
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            for restraintListId in sorted(self.settings['Restraints'][restraintType]):
                grid = _addColumn(grid)
                widget = CheckBox(self.scrollAreaLayout, text=restraintListId.name, checked=True, grid=grid,tipText=help['Restraint list'])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                self.guiDict['Restraints'][restraintType][restraintListId] = OD([('Active', widget)])
                self.settings['Restraints'][restraintType][restraintListId] = OD([('Active', self._getValue(widget))])

                grid = _addColumn(grid)
                widget = DoubleSpinbox(self.scrollAreaLayout, value=refineRelativeWeights[restraintType], step=0.01,decimals=3, grid=grid, tiptext=help['Final weight'])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                # Remove arrows from double spinbox widget
                widget.setButtonSymbols(2)
                self.guiDict['Restraints'][restraintType][restraintListId]['Final weight'] = widget
                self.settings['Restraints'][restraintType][restraintListId]['Final weight'] = self._getValue(widget)

                # Add extra parameters
                for i in karplusParameters:
                    grid = _addColumn(grid)
                    widget = DoubleSpinbox(self.scrollAreaLayout, value=karplusParameters[i], step=0.01, decimals=2,grid=grid, tiptext=help[i])
                    _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                    # Remove arrows from double spinbox widget
                    widget.setButtonSymbols(2)
                    self.guiDict['Restraints'][restraintType][restraintListId][i] = widget
                    self.settings['Restraints'][restraintType][restraintListId][i] = self._getValue(widget)
                grid = _addRow(grid)

        # Select calculation engines to run
        grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
        widget = Label(self.scrollAreaLayout, text='Software', grid=grid)
        _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        for header in ['Engine', 'Generate', 'Keep', 'MD Steps', 'CPUs']:
            grid = _addColumn(grid)
            widget = Label(self.scrollAreaLayout, text=header, grid=grid, tipText=help[header])
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))

        for engine in sorted(calculationEngines):
            grid = _addRow(grid)
            grid = _addColumn(grid)
            widget = CheckBox(self.scrollAreaLayout, text=engine, checked=True, grid=grid, tipText=help['Engine'])
            _setWidgetProperties(widget, _setWidth(columnWidths, grid))
            self.guiDict['Engines'][engine] = OD([('Active', widget)])
            self.settings['Engines'][engine] = OD([('Active', self._getValue(widget))])

            # Add structures to generate and keep
            for i in ['Generate', 'Keep']:
                grid = _addColumn(grid)
                widget = Spinbox(self.scrollAreaLayout, value=threads, step=1, grid=grid, tipText=help[i])
                widget.setRange(1, 1000)
                widget.setValue(calculationEngines[engine][i])
                _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
                widget.setButtonSymbols(2)
                self.guiDict['Engines'][engine][i] = widget
                self.settings['Engines'][engine][i] = self._getValue(widget)

            # Add MD Steps, if defined otherwise text string
            grid = _addColumn(grid)
            if calculationEngines[engine]['MD Steps'] != None:
                nResidues = 0
                for chain in self.project.chains:
                    nResidues += len(chain.residues)
                mdSteps = int(nResidues * calculationEngines[engine]['MD Steps'])
                # Round up to next 5000
                mdSteps = mdSteps if mdSteps % 5000 == 0 else mdSteps + 5000 - mdSteps % 5000

                widget = Spinbox(self.scrollAreaLayout, value=threads, step=1, grid=grid, tipText=help['MD Steps'])
                widget.setRange(5000, 1000000)
                widget.setValue(mdSteps)
                _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
                widget.setButtonSymbols(2)
                self.guiDict['Engines'][engine]['MD Steps'] = widget
                self.settings['Engines'][engine]['MD Steps'] = self._getValue(widget)
            else:
                widget = Label(self.scrollAreaLayout, text='Auto', grid=grid)
                _setWidgetProperties(widget, _setWidth(columnWidths, grid))
                self.guiDict['Engines'][engine]['MD Steps'] = 'Auto'
                self.settings['Engines'][engine]['MD Steps'] = 'Auto'

            # Add number of threads to use
            grid = _addColumn(grid)
            widget = Spinbox(self.scrollAreaLayout, value=threads, step=1, grid=grid, tipText=help['CPUs'])
            widget.setRange(1, maxThreads)
            _setWidgetProperties(widget, _setWidth(columnWidths, grid), hAlign='r')
            widget.setButtonSymbols(2)
            self.guiDict['Engines'][engine]['CPUs'] = widget
            self.settings['Engines'][engine]['CPUs'] = self._getValue(widget)

        # Action buttons: Set up, Run, import
        grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
        grid = _addColumn(grid)
        texts = ['Set up project', 'Write settings', 'Run calculation', 'Import results']
        tipTexts = [help['Setup'], help['Write'], help['Run'], help['Import']]
        callbacks = [self._setupProject, self._writeSettings, self._runCalculation, self._importResults]
        widget = ButtonList(parent=self.scrollAreaLayout, texts=texts, callbacks=callbacks, tipTexts=tipTexts, grid=grid, gridSpan=(1,5))
        _setWidgetProperties(widget,heightType='Minimum')

        Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0]+1, 10),
               gridSpan=(1, 1))

    def _inputDataCheck(self):
        # Checks available input data at plugin start

        return True

        inputWarning = ''
        if len(self.project.chains) == 0:
            inputWarning += 'No molecular chains found in the project\n'
        if len(self.project.restraintLists) == 0:
            inputWarning += 'No restraints found in the project\n'
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
        restraints = 0
        engines = 0

        if len(self.settings['General']['Run name'].strip()) == 0:
            inputWarning += 'No run name specified\n'
        if len(self.settings['General']['Run name'].split()) > 1:
            inputWarning += 'Run name may not contain spaces\n'

        for pid in self.exportPidList:
            if 'MC' in pid:
                chains += 1
            if 'RL' in pid:
                restraints += 1
        for engine in self.settings['Engines']:
            if self.settings['Engines'][engine]['Active'] == True:
                engines += 1

        if chains == 0:
            inputWarning += 'No molecular chains selected\n'
        if restraints == 0:
            inputWarning += 'No restraints selected\n'
        if engines == 0:
            inputWarning += 'No structure calculation software selected\n'

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

            noteTitle = '{0} - Structure calculation from restraints'.format(self.settings['General']['Run name'])
            note = self.project.newNote(noteTitle)
            note.text = formatted + '\n\nJSON format:\n\n' + jsonString
            showMessage('Message', 'Created project note {0}'.format(noteTitle))

    def _createPidList(self):
        # Create the list of standard project objects to be written, which is a list of their pids
        self.exportPidList = []

        # Add sequence pids:
        # We only support a single chain for the moment, hetero multimers would require writing all chains
        for chainId in self.settings['Chains']:
            if self.settings['Chains'][chainId]['Active'] == True:
                self.exportPidList.append('MC:' + chainId)

        # Add restraints lists
        for restraintType in sorted(self.settings['Restraints']):
            for restraintListId in self.settings['Restraints'][restraintType]:
                if self.settings['Restraints'][restraintType][restraintListId]['Active'] == True:
                    self.exportPidList.append('RL:{0}'.format(restraintListId))

    def _convertNefToDataBlock(self):
        # Convert the standard NEF data to a Data block
        self.dataBlock = self.project._convertToDataBlock(skipPrefixes=(), expandSelection=False,pidList=self.exportPidList)

    def _exportNef(self):
        # self.outputPath = os.path.join(self.settings['General']['Run path'], '{0}.nef'.format(self.settings['General']['Run name']))
        # self.project._writeDataBlockToFile(dataBlock=self.dataBlock, path=self.outputPath, overwriteExisting=True)
        self.project._writeDataBlockToFile(dataBlock=self.dataBlock, path=os.path.join(self.runPath, '{0}.nef'.format(self.settings['General']['Run name'])), overwriteExisting=True)

    def _addCalculationBlocks(self):
        runName = self.settings['General']['Run name'].strip()
        # NEFS removed because they are not in NEF definitions yet
        sf_category = 'ccpn_structure_from_restraints_run'
        sf_framecode = sf_category+'_settings'
        newSaveFrame = SaveFrame(name=sf_framecode)
        newSaveFrame.addItem('_{0}.sf_category'.format(sf_category),sf_category)
        newSaveFrame.addItem('_{0}.sf_framecode'.format(sf_category),sf_framecode)
        newSaveFrame.addItem('_{0}.name'.format(sf_category),runName)
        self.dataBlock.addItem(sf_category, newSaveFrame)

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
            self._addCalculationBlocks()
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
        # """ Insert here the script for running StructureFromRestraints """
        # with parameters for structure calculation engines, i.e. nef file, and protocol parameters
        # print('Running calculation', kwargs)
        pass

    def _importResults(self):
        # Check on presence of completed calculation
        pass


class StructureFromRestraintsPlugin(Plugin):
    PLUGINNAME = 'Calculate structure from restraints'
    guiModule = StructureFromRestraintsGuiPlugin
    CCPNPLUGIN = True

    def run(self, **kwargs):
        """ Insert here the script for running StructureFromRestraints """
        print('Running calculation', kwargs)


# StructureFromRestraintsPlugin.register()  # Registers the pipe in the pluginList
# Set tolerances from project.spectrum.tolerances by default
