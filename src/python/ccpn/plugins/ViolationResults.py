"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2022-02-25 19:08:07 +0000 (Fri, February 25, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-02-25 16:03:34 +0100 (Fri, February 25, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from PyQt5 import QtWidgets

from ccpn.core.DataTable import DataTable
from ccpn.core.lib import Pid
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.modules.PluginModule import PluginModule
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget, EntryCompoundWidget
from ccpn.ui.gui.widgets.PulldownListsForObjects import RestraintTablePulldown, ViolationTablePulldown
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.HLine import LabeledHLine
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.guiSettings import BORDERNOFOCUS_COLOUR
from ccpn.ui.gui.lib.Validators import LineEditValidatorCoreObject
from ccpn.framework.lib.Plugin import Plugin
from ccpn.util.AttrDict import AttrDict


LineEditsMinimumWidth = 195
DEFAULTSPACING = 3
DEFAULTMARGINS = (14, 14, 14, 14)
DEFAULT_RUNNAME = 'run'

# Set some tooltip texts
RUNBUTTON = 'Run'
_help = {RUNBUTTON: 'Run the plugin', }


class ViolationResultsGuiPlugin(PluginModule):
    className = 'ViolationResults'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super().__init__(mainWindow=mainWindow, plugin=plugin, application=application)

        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.preferences = mainWindow.application.preferences
        else:
            self.application = None
            self.project = None
            self.preferences = None

        # set up object to pass information to the main plugin
        self.obj = AttrDict()

        # set up the widgets
        self._setWidgets()
        self._populate()

        self.plugin._loggerCallback = self._guiLogger

    def _guiLogger(self, *args):
        self._textEditor.append(*args)

    def _setWidgets(self):
        """Set up the mainwidgets
        """
        # set up a scroll area in the mainWidget
        self._scrollFrame = ScrollableFrame(parent=self.mainWidget,
                                            showBorder=False, setLayout=True,
                                            acceptDrops=True, grid=(0, 0), gridSpan=(1, 1), spacing=(5, 5))
        self._scrollAreaWidget = self._scrollFrame._scrollArea
        self._scrollAreaWidget.setStyleSheet('ScrollArea { border-right: 1px solid %s;'
                                             'border-bottom: 1px solid %s;'
                                             'background: transparent; }' % (BORDERNOFOCUS_COLOUR, BORDERNOFOCUS_COLOUR))
        self._scrollFrame.insertCornerWidget()
        self._scrollFrame.setContentsMargins(*DEFAULTMARGINS)
        self._scrollFrame.getLayout().setSpacing(DEFAULTSPACING)

        # add contents to the scroll frame
        parent = self._scrollFrame
        row = 0
        Label(parent, text='Calculate Violation Results dataTable', bold=True, grid=(row, 0))

        row += 1
        self._rTable = RestraintTablePulldown(parent=parent,
                                              mainWindow=self.mainWindow,
                                              grid=(row, 0), gridSpan=(1, 2),
                                              showSelectName=True,
                                              minimumWidths=(150, 100),
                                              sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                              callback=self._selectRTableCallback)

        row += 1
        self._vTable = PulldownListCompoundWidget(parent=parent,
                                                  mainWindow=self.mainWindow,
                                                  labelText="Violation Tables",
                                                  grid=(row, 0), gridSpan=(1, 2),
                                                  minimumWidths=(150, 100),
                                                  sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                  callback=None)

        row += 1
        self._dTable = EntryCompoundWidget(parent=parent,
                                           mainWindow=self.mainWindow,
                                           labelText="Results Name",
                                           grid=(row, 0), gridSpan=(1, 2),
                                           minimumWidths=(150, 100),
                                           sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                           callback=None,
                                           compoundKwds={'backgroundText': '> Enter name <'},
                                           )
        _validator = LineEditValidatorCoreObject(parent=self._dTable.entry, project=self.project, klass=DataTable,
                                                 allowSpace=False, allowEmpty=False)
        self._dTable.entry.setValidator(_validator)

        row += 1
        texts = [RUNBUTTON]
        tipTexts = [_help[RUNBUTTON]]
        callbacks = [self.runGui]
        ButtonList(parent=parent, texts=texts, callbacks=callbacks, tipTexts=tipTexts,
                   grid=(row, 1), gridSpan=(1, 1), hAlign='r')

        row += 1
        LabeledHLine(parent, text='Output', grid=(row, 0), gridSpan=(1, 3), height=16, colour=getColours()[DIVIDER])

        row += 1
        self._textEditor = TextEditor(parent, grid=(row, 0), gridSpan=(1, 3), enabled=True, addWordWrap=True)
        self._textEditor.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        row += 1
        parent.getLayout().setColumnStretch(2, 1)

    def runGui(self):
        """Run the plugin
        """
        _rTable = self.project.getByPid(self._rTable.getText())
        _vTable = self.project.getByPid(self._vTable.getText())
        _runName = self._dTable.getText()

        if not (_rTable and _vTable):
            showWarning('Violation Plugin', 'Please select from the pulldowns')
        if not _runName:
            showWarning('Violation Plugin', 'Please select output dataTable name')

        else:
            self.obj.restraintTable = _rTable
            self.obj.violationTable = _vTable
            self.obj.runName = _runName

            if (result := self.plugin.run(**self.obj)):
                self._populate(name=result.name)

    def _populate(self, name=None):
        """Populate the pulldowns from the project restraintTables
        """
        firstItemName = self._rTable.getFirstItemText()
        if firstItemName:
            # set the item in the pulldown
            self._rTable.select(firstItemName)
        self._dTable.setText(name or DEFAULT_RUNNAME)
        self._dTable.entry.validator().resetCheck()

    def _selectRTableCallback(self, pid):
        """Handle the callback from the restraintTable selection
        """
        if self.project.getByPid(pid):
            _texts = [''] + [vt.pid for vt in self.project.violationTables if vt.getMetadata('restraintTable') == pid]
            self._vTable.modifyTexts(texts=_texts)


class ViolationResultsPlugin(Plugin):
    """Plugin to create violation results from restraintTables and processed violationTables
    """
    PLUGINNAME = 'Violation Results'
    guiModule = ViolationResultsGuiPlugin

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self._kwds = AttrDict()
        self._loggerCallback = None

    def _logger(self, *args):
        if self._loggerCallback:
            self._loggerCallback(*args)

    def run(self, **kwargs):
        """Generate the output dataTable
        """
        # pd.set_option('display.max_columns', None)
        # pd.set_option('display.max_rows', 7)

        _requiredColumns = ['model_id', 'restraint_id', 'atoms', 'violation']

        self._logger('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

        # check the parameters
        if not (restraintTable := kwargs.get('restraintTable')):
            self._logger('ERROR:   RestraintTable not specified')
            return
        if not (violationTable := kwargs.get('violationTable')):
            self._logger('ERROR:   ViolationTable not specified')
            return
        _df = violationTable.data
        if _df is None:
            self._logger('ERROR:   ViolationTable contains no data')
            return

        self._logger(f'Running - {self.PLUGINNAME}')
        self._logger(f'  {_df.columns}')

        _invalidColumns = [col for col in _requiredColumns if col not in _df.columns]
        if _invalidColumns:
            self._logger(f'ERROR:   missing required columns {_invalidColumns}')
            return

        # get the models defined for the violations
        models = [v for k, v in _df.groupby(['model_id'], as_index=False)]

        if models:
            self._logger(f'MODELS {len(models)}')
            self._logger(f'{models[0].columns}')

            restraintsFromModels = []

            # use the serial to get the restraint from the peak - make list for each model just to check is actually working
            for mm, _mod in enumerate(models):
                restraintsFromModel = []
                restraintsFromModels.append(restraintsFromModel)
                for serial in _mod['restraint_id']:
                    restraintId = Pid.IDSEP.join(('' if x is None else str(x)) for x in (restraintTable.structureData.name, restraintTable.name, serial))
                    modelRestraint = self.project.getObjectsByPartialId(className='Restraint', idStartsWith=restraintId)
                    restraintsFromModel.append(modelRestraint[0].pid if modelRestraint else None)

            # check all the same
            self._logger(str(all(restraintsFromModels[0] == resMod for resMod in restraintsFromModels)))

            # calculate statistics for the violations and concatenate into a single dataFrame
            average = pd.concat([v['violation'].reset_index(drop=True) for v in models],
                                ignore_index=True,
                                axis=1).agg(['min',
                                             'max',
                                             'mean',
                                             'std',
                                             lambda x: int(sum(x > 0.3)),
                                             lambda x: int(sum(x > 0.5)), ], axis=1)

            self._logger('**** average *****')
            self._logger(str(average))

            # # merge the atom columns - done in nef loader?
            # atoms = models[0]['atom1'].map(str) + ' - ' + models[0]['atom2'].map(str)

            # remove the indexing for the next concat
            atoms = models[0]['atoms'].reset_index(drop=True)
            average.reset_index(drop=True)

            self._logger('**** atoms *****')
            self._logger(str(atoms))
            pids = pd.DataFrame(restraintsFromModels[0], columns=['pid'])
            # ids = models[0]['restraint_id']
            # subIds = models[0]['restraint_sub_id']

            # build the result dataFrame
            result = pd.concat([pids, atoms, average], ignore_index=True, axis=1)

            # rename the columns (lambda just gives the name 'lambda') - try multiLevel?
            result.columns = ('RestraintPid', 'Atoms', 'Min', 'Max', 'Mean', 'STD', 'Count>0.3', 'Count>0.5')

            # put into a new dataTable
            _data = self.project.newDataTable(name=kwargs.get('runName'))
            _data.setMetadata('restraintTable', restraintTable.pid)
            _data.setMetadata('violationResult', True)
            _data.data = result

            self._logger(f'\n input restraintTable:    {restraintTable.pid}')
            self._logger(f' input violationTable:    {violationTable.pid}\n')
            self._logger(f' output dataTable:        {_data.name}\n')

            return _data

        else:
            self._logger('ERROR:   violationTable contains no models')


ViolationResultsPlugin.register()  # Registers the plugin