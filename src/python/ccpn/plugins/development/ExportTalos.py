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


#=========================================================================================
# TODO
# Catch exceptions in case no valid spectra are in the project, now the plugin doesn't open
# when no spectra are in the project
# Output path selection ? If not default
# Tsar installation path ? if not default
# support for 4D and 5D data sets, including tolerance and nucleus selection
# import of Tsar results (assigned peak lists in nef format)
#=========================================================================================




import os,copy,json,pprint,math,shutil,pandas,operator
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
        'Chains': 'Check chains from which to calculate structures',
        'Chemical shift list': 'Select chemical shift list.',
        'Export': 'Sets up the project directory structure and exports Talos shifts.',
        'Write': 'Writes the current settings in JSON and human readable format to the project notes, with the run name as title',
        }

# Talos Nuclei map
nuclei = {'H':    'HN',
          'HA':   'HA',
          'HAx': 'HA2',
          'HAy': 'HA3',
          'HA2': 'HA2',
          'HA3': 'HA3',
          'HA%': 'HA2,HA3',
          'C':    'C',
          'CA':   'CA',
          'CB':   'CB',
          'N':    'N'
          }

class TalosGuiPlugin(PluginModule):

    className = 'TALOS'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super(TalosGuiPlugin, self)
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

        self.pluginPath = os.path.join(self.project.path,TalosGuiPlugin.className)

        # Create ORDERED dictionary to store all parameters for the run
        # deepcopy doesn't work on dictionaries with the qt widgets, so to get a separation of gui widgets and values for storage
        # it is needed to create the two dictionaries alongside each other
        self.guiDict  = OD([('General',OD()), ('Chains',OD()), ('Chemical shift list',OD())])
        self.settings = OD([('General',OD()), ('Chains',OD()), ('Chemical shift list',OD())])

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

        # Set molecular chains, use pulldown, Talos only allows one chain at a time
        grid = _addVerticalSpacer(self.scrollAreaLayout,grid)
        grid = _addRow(grid)

        widget = Label(self.scrollAreaLayout,text='Molecular chains', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, tipText=help['Chains'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        self.chains = [chain.id for chain in sorted(self.project.chains)]
        widget.setData(self.chains)
        self.guiDict['Chains'] = widget
        self.settings['Chains'] = self._getValue(widget)

        # Set Chemical shift list, use checkboxes with own labels
        grid = _addVerticalSpacer(self.scrollAreaLayout,grid)
        grid = _addRow(grid)

        widget = Label(self.scrollAreaLayout,text='Chemical shift list', grid=grid)
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))

        grid = _addColumn(grid)
        widget = PulldownList(self.scrollAreaLayout, grid=grid, tipText=help['Chemical shift list'])
        _setWidgetProperties(widget,_setWidth(columnWidths,grid))
        self.shiftLists = [shiftList.id for shiftList in sorted(self.project.chemicalShiftLists)]
        widget.setData(self.shiftLists)
        self.guiDict['Chemical shift list'] = widget
        self.settings['Chemical shift list'] = self._getValue(widget)

        # Action buttons: Set up, Run, import
        grid = _addVerticalSpacer(self.scrollAreaLayout, grid)
        grid = _addColumn(grid)
        texts = ['Export Talos', 'Write settings']
        tipTexts = [help['Export'], help['Write']]
        callbacks = [self._exportTalos, self._writeSettings]
        widget = ButtonList(parent=self.scrollAreaLayout, texts=texts, callbacks=callbacks, tipTexts=tipTexts, grid=grid, gridSpan=(1,4))
        _setWidgetProperties(widget,_setWidth(columnWidths,grid),heightType='Minimum')

        Spacer(self.scrollAreaLayout, 5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(grid[0]+1, 10),
               gridSpan=(1, 1))


    def _createTalosSequence(self, chain):
        # Create a sequence string

        first_resid = chain.residues[0].sequenceCode

        talosSequence = 'DATA FIRST_RESID {0}\n'.format(first_resid)

        sequence = ''
        for r in chain.residues:
            resName = r.shortName
            if r.shortName == 'C' and r.residueVariant == '-HG':
                resName = 'c'
            sequence += resName

        # Split the sequence into chunks of 10
        sequence = [sequence[i:i + 10] for i in range(0, len(sequence), 10)]

        # Add up to 5 chunks of 10 residues per SEQUENCE line
        for i in range(1+int(len(sequence)/5)):
            talosSequence += '\nDATA SEQUENCE '
            for j in range(0,5):
                try:
                    talosSequence += sequence[5*i+j] + ' '
                except IndexError:
                    pass
        return talosSequence

    def _getSortedShifts(self, shiftList, molecularChain):
        shifts = []
        cnt = 0
        for cs in shiftList.chemicalShifts:

            # Shifts have to match Talos nuclei and the selected molecular chain
            if not cs.nmrAtom.name in nuclei:
                continue

            if not cs.nmrAtom.nmrResidue.nmrChain.chain == molecularChain:
                continue

            # Get the assignments
            shift = cs.value
            atomName = cs.nmrAtom.name
            resName = cs.nmrAtom.nmrResidue.residue.shortName
            resId = int(cs.nmrAtom.nmrResidue.sequenceCode)

            if cs.nmrAtom.nmrResidue.residue.shortName == 'C' and cs.nmrAtom.nmrResidue.residue.residueVariant == '-HG':
                resName = 'c'

            # Convert to Talos atom name
            if not ',' in nuclei[atomName]:
                atomName = nuclei[atomName]
                shifts.append([resId, resName, atomName, shift])
            else:
                atomNames = nuclei[atomName].split(',')
                for atomName in atomNames:
                    shifts.append([resId, resName, atomName, shift])

        # Sort the chemical shifts on residue number and atom name
        sortedShifts = sorted(shifts, key=operator.itemgetter(0,2))

        return sortedShifts

    def _writeTalos(self):
        chainId = self.settings['Chains']
        shiftListId = self.settings['Chemical shift list']
        chain = self.project.getByPid('MC:'+chainId)
        shiftList = self.project.getByPid('CL:' + shiftListId)
        talosSequence = self._createTalosSequence(chain)
        sortedShifts = self._getSortedShifts(shiftList,chain)

        out =  'REMARK Chemical shift table.\n'
        out += 'REMARK Chain: {0}\n'.format(chainId)
        out += 'REMARK Shift list: {0}\n\n'.format(shiftListId)
        out += '{0}\n\n'.format(talosSequence)
        out += 'VARS   RESID RESNAME ATOMNAME SHIFT\n'
        out += 'FORMAT %4d   %1s     %4s      %8.3f\n\n'
        for shift in sortedShifts:
            out += '{0:>4d} {1:1s} {2:>4s} {3:>8.3f}\n'.format(shift[0],shift[1],shift[2],shift[3])

        output = open(os.path.join(self.runPath,'{0}_talos.tab'.format(self.settings['General']['Run name'])),'w')
        output.write(out)
        output.close()

    def _inputDataCheck(self):
        # Checks available input data at plugin start

        return True

        inputWarning = ''
        if len(self.project.chains) == 0:
            inputWarning += 'No molecular chains found in the project\n'
        if len(self.project.chemicalShiftLists) == 0:
            inputWarning += 'No Chemical shift list found in the project\n'
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


    # def _checkTsarPath(self):
    #   self.TsarPath = self.userPluginPath+'Tsar/'
    #   if not os.path.exists(self.TsarPath):
    #     os.makedirs(self.TsarPath)

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
        # # Create a data block of the regular CCPN objects, which would normally be exported directly.
        # self._createPidList()
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

            noteTitle = '{0} - Export Talos'.format(self.settings['General']['Run name'])
            note = self.project.newNote(noteTitle)
            note.text = formatted + '\n\nJSON format:\n\n' + jsonString
            showMessage('Message', 'Created project note {0}'.format(noteTitle))


    def _exportTalos(self):
        # Get values from the GUI widgets and save in the settings
        self._updateSettings(self.guiDict, self.settings)

        # Set the run path
        self.runPath = os.path.join(self.pluginPath, self.settings['General']['Run name'])

        # Check if all input requirements are met
        setupComplete = self._runDataCheck()

        if setupComplete == True:
            # Check if tree exists, and if to overwrite
            overwrite = False
            if os.path.exists(self.runPath):
                overwrite = showYesNo('Warning', 'Run {0} exists. Overwrite?'.format(self.settings['General']['Run name']))
                if overwrite == False:
                    showMessage('Message', 'Project set up aborted')
                    return

            if overwrite == True:
                shutil.rmtree(self.runPath)

            # Create a (new) directory tree
            self._createRunTree()
            self._writeTalos()
            showMessage('Message', 'Talos export complete')


    def _createRunTree(self):
        if not os.path.exists(self.pluginPath):
            os.makedirs(self.pluginPath)

        if not os.path.exists(self.runPath):
            os.makedirs(self.runPath)

class TalosPlugin(Plugin):
    PLUGINNAME = 'Export Talos'
    guiModule = TalosGuiPlugin

    def run(self, **kwargs):
        ''' Insert here the script for running Tsar '''
        print('Running Talos', kwargs)


# TalosPlugin.register()  # Registers the pipe in the pluginList
# Set tolerances from project.spectrum.tolerances by default
