"""
This file contains StructureTableModule and StructureTable classes
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:04 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import StructurePulldown
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.lib.Strip import navigateToNmrResidueInDisplay

from ccpn.util.Logging import getLogger
logger = getLogger()

ALL = '<all>'


class PandasModel(QtCore.QAbstractTableModel):
  """
  Class to populate a table view with a pandas dataframe
  """
  # 'modelNumber'
  # 'chainCode'
  # 'sequenceId'
  # 'insertionCode'
  # 'residueName'
  # 'atomName'
  # 'altLocationCode'
  # 'element'
  # 'x'
  # 'y'
  # 'z'
  # 'occupancy'
  # 'bFactor'
  # 'nmrChainCode'
  # 'nmrSequenceCode'
  # 'nmrResidueName'
  # 'nmrAtomName'

  def __init__(self, data, parent=None):
    QtCore.QAbstractTableModel.__init__(self, parent)
    self._data = data

  def rowCount(self, parent=None):
    return len(self._data.values)

  def columnCount(self, parent=None):
    return self._data.columns.size

  def data(self, index, role=QtCore.Qt.DisplayRole):
    if index.isValid():
      if role == QtCore.Qt.DisplayRole:
        return str(self._data.values[index.row()][index.column()])
    return None

  def headerData(self, col, orientation, role):
    if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
      return self._data.columns[col]
    return None

  def setData(self, index, value, role):
    if not index.isValid():
      return False
    if role != QtCore.Qt.EditRole:
      return False
    row = index.row()
    if row < 0 or row >= len(self._data.values):
      return False
    column = index.column()
    if column < 0 or column >= self._data.columns.size:
      return False
    self._data.values[row][column] = value
    self.dataChanged.emit(index, index)
    return True

  def flags(self, index):
    flags = super(self.__class__, self).flags(index)
    flags |= QtCore.Qt.ItemIsEditable
    flags |= QtCore.Qt.ItemIsSelectable
    flags |= QtCore.Qt.ItemIsEnabled
    flags |= QtCore.Qt.ItemIsDragEnabled
    flags |= QtCore.Qt.ItemIsDropEnabled
    return flags


class StructureTableModule(CcpnModule):
  """
  This class implements the module by wrapping a StructureTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsOnTop = True

  className = 'StructureTableModule'

  # we are subclassing this Module, hence some more arguments to the init
  def __init__(self, mainWindow, name='Structure Table'):

    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    self.ensemble = self.project.newStructureEnsemble()
    self.data = self.ensemble.data

    self.testAtomName = ['CA', 'C', 'N', 'O', 'H'
      , 'CB', 'HB1', 'HB2', 'HB3'
      , 'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23'
      , 'CE', 'HE1', 'HE2', 'HE3'
      , 'CG', 'HG1', 'HG2', 'HG3'
      , 'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
    self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + [
                                                                                                   'VAL'] * 8
    self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
    self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8

    self.data['atomName'] = self.testAtomName
    self.data['residueName'] = self.testResidueName
    self.data['chainCode'] = self.testChainCode
    self.data['sequenceId'] = self.testSequenceId
    self.data['modelNumber'] = self.testModelNumber
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    self.ensemble = self.project.newStructureEnsemble()
    self.data = self.ensemble.data

    self.testAtomName = ['CA', 'C', 'N', 'O', 'H'
      , 'CB', 'HB1', 'HB2', 'HB3'
      , 'CE', 'HE1', 'HE2', 'HE3'
      , 'CG', 'HG1', 'HG2', 'HG3'
      , 'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23'
      , 'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
    self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + [
                                                                                                   'VAL'] * 8
    self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
    self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8

    self.data['atomName'] = self.testAtomName
    self.data['residueName'] = self.testResidueName
    self.data['chainCode'] = self.testChainCode
    self.data['sequenceId'] = self.testSequenceId
    self.data['modelNumber'] = self.testModelNumber
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

    # settings

    # Put all of the NmrTable settings in a widget, as there will be more added in the PickAndAssign, and
    # backBoneAssignment modules
    self._NTSwidget = Widget(self.settingsWidget, setLayout=True,
                             grid=(0,0), vAlign='top', hAlign='left')
    #self._NTSwidget = self.settingsWidget

    # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
    # underpinning the addNotifier call do not allow for it either
    colwidth = 140
    self.displaysWidget = ListCompoundWidget(self._NTSwidget,
                                             grid=(0,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             vPolicy='minimal',
                                             #minimumWidths=(colwidth, 0, 0),
                                             fixedWidths=(colwidth, colwidth, colwidth),
                                             orientation = 'left',
                                             labelText='Display(s):',
                                             tipText = 'SpectrumDisplay modules to respond to double-click',
                                             texts=[ALL] + [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
                                             )
    self.displaysWidget.setFixedHeigths((None, None, 40))

    self.sequentialStripsWidget = CheckBoxCompoundWidget(
                                             self._NTSwidget,
                                             grid=(1,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Show sequential strips:',
                                             checked = False
                                            )

    self.markPositionsWidget = CheckBoxCompoundWidget(
                                             self._NTSwidget,
                                             grid=(2,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Mark positions:',
                                             checked = True
                                            )
    self.autoClearMarksWidget = CheckBoxCompoundWidget(
                                             self._NTSwidget,
                                             grid=(3,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Auto clear marks:',
                                             checked = True
                                            )

    # main window
    self.structureTable = StructureTable(parent=self.mainWidget, setLayout=True,
                                           application=self.application,
                                           grid=(0,0)
                                          )

  def _getDisplays(self):
    "return list of displays to navigate; done so BackboneAssignment module can subclass"
    displays = []
    # check for valid displays
    gids = self.displaysWidget.getTexts()
    if len(gids) == 0: return displays
    if ALL in gids:
        displays = self.application.ui.mainWindow.spectrumDisplays
    else:
        displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
    return displays

  # def navigateToStructure(self, structureEnsemble, row=None, col=None):
  #   "Navigate in selected displays to nmrResidue; skip if none defined"
  #   logger.debug('StructureEnsemble=%s' % (structureEnsemble.id))
  #
  #   displays = self._getDisplays()
  #   if len(displays) == 0:
  #     logger.warn('Undefined display module(s); select in settings first')
  #     showWarning('startAssignment', 'Undefined display module(s);\nselect in settings first')
  #     return
  #
  #   self.application._startCommandBlock('%s.navigateToStructure(project.getByPid(%r))' %
  #       (self.className, structureEnsemble.pid))
  #   try:
  #       # optionally clear the marks
  #       if self.autoClearMarksWidget.checkBox.isChecked():
  #           self.application.ui.mainWindow.clearMarks()
  #
  #       # navigate the displays
  #       for display in displays:
  #           if len(display.strips) > 0:
  #             pass
  #               # self.navigateToStructureInDisplay(structureEnsemble, display, stripIndex=0,
  #               #                               widths=['full'] * len(display.strips[0].axisCodes),
  #               #                               showSequentialStructures = (len(display.axisCodes) > 2) and
  #               #                               self.sequentialStripsWidget.checkBox.isChecked(),
  #               #                               markPositions = self.markPositionsWidget.checkBox.isChecked()
  #               # )
  #   finally:
  #       self.application._endCommandBlock()


class StructureTable(ObjectTable):
  """
  Class to present a StructureTable and a StructureData pulldown list, wrapped in a Widget
  """

  def testy(self, row, name):
    try:
      return getattr(row, name)
    except:
      return 0

  #row.modelNumber, etc., may not exist..

  columnDefs = [
                ('modelNumber', lambda row: int(StructureTable.testy(StructureTable, row, 'modelNumber')), 'modelNumber'),
                ('chainCode', lambda row: str(StructureTable.testy(StructureTable, row, 'chainCode')), 'chainCode'),
                ('sequenceId', lambda row: int(StructureTable.testy(StructureTable, row, 'sequenceId')), 'sequenceId'),
                ('insertionCode', lambda row: str(StructureTable.testy(StructureTable, row, 'insertionCode')), 'insertionCode'),
                ('residueName', lambda row: str(StructureTable.testy(StructureTable, row, 'residueName')), 'residueName'),
                ('atomName', lambda row: str(StructureTable.testy(StructureTable, row, 'atomName')), 'atomName'),
                ('altLocationCode', lambda row: str(StructureTable.testy(StructureTable, row, 'altLocationCode')), 'altLocationCode'),
                ('element', lambda row: str(StructureTable.testy(StructureTable, row, 'element')), 'element'),
                ('x', lambda row: float(StructureTable.testy(StructureTable, row, 'x')), 'x'),
                ('y', lambda row: float(StructureTable.testy(StructureTable, row, 'y')), 'y'),
                ('z', lambda row: float(StructureTable.testy(StructureTable, row, 'z')), 'z'),
                ('occupancy', lambda row: float(StructureTable.testy(StructureTable, row, 'occupancy')), 'occupancy'),
                ('bFactor', lambda row: float(StructureTable.testy(StructureTable, row, 'bFactor')), 'bFactor'),
                ('nmrChainCode', lambda row: str(StructureTable.testy(StructureTable, row, 'nmrChainCode')), 'nmrChainCode'),
                ('nmrSequenceCode', lambda row: str(StructureTable.testy(StructureTable, row, 'nmrSequenceCode')), 'nmrSequenceCode'),
                ('nmrResidueName', lambda row: str(StructureTable.testy(StructureTable, row, 'nmrResidueName')), 'nmrResidueName'),
                ('nmrAtomName', lambda row: str(StructureTable.testy(StructureTable, row, 'nmrAtomName')), 'nmrAtomName')
  ]

  def __init__(self, parent, application, **kwds):

    self._application = application
    self._project = application.project
    self._current = application.current
    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)

    # create the column objects
    columns = [Column(colName, func, tipText=tipText) for colName, func, tipText in self.columnDefs]

    # selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
    # create the table; objects are added later via the displayTableForStructure method
    ObjectTable.__init__(self, parent=self._widget, setLayout=True,
                         columns=columns, objects = [],
                         autoResize=True,
                         selectionCallback=self._selectionCallback,
                         actionCallback=self._actionCallback,
                         grid = (1, 0), gridSpan = (1, 6)
                         )

    # Notifier object to update the table if the nmrChain changes
    self._structureNotifier = None
    #TODO: see how to handle peaks as this is too costly at present
    # Notifier object to update the table if the peaks change
    self._peaksNotifier = None
    # self._peaksNotifier = Notifier(self._project,
    #                                [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], 'Peak',
    #                                 self._updateCallback
    #                                )
    self._updateSilence = False  # flag to silence updating of the table

    # This widget will display a pulldown list of NmrChain pids in the project
    self.ncWidget = StructurePulldown(parent=self._widget,
                                     project=self._project, default=0,  #first NmrChain in project (if present)
                                     grid=(0,0), gridSpan=(1,1), minimumWidths=(0,100),
                                     callback=self._selectionPulldownCallback
                                     )

    if len(self._project.structureEnsembles) > 0:
      self.displayTableForStructure(self._project.structureEnsembles[0])

  def addWidgetToTop(self, widget, col=2, colSpan=1):
    "Convenience to add a widget to the top of the table; col >= 2"
    if col < 2:
      raise RuntimeError('Col has to be >= 2')
    self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

  def displayTableForStructure(self, structureEnsemble):
    "Display the table for all StructureEnsembles"

    if self._structureNotifier is not None:
      # we have a new nmrChain and hence need to unregister the previous notifier
      self._structureNotifier.unRegister()
    # register a notifier for this nmrChain
    self._structureNotifier = Notifier(structureEnsemble,
                                   [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], 'StructureEnsemble',
                                    self._updateCallback
                                  )

    self.ncWidget.select(structureEnsemble.pid)
    self._update(structureEnsemble)

  def _update(self, structureEnsemble):
    "Update the table"
    if not self._updateSilence:
      self.clearTable()
      self._silenceCallback = True

      # model = PandasModel(structureEnsemble.data)   # ejb - interesting, set QTableView form Pandas
      # self.setModel(model)
      # self.setSortingEnabled(True)
      tuples = structureEnsemble.data.as_namedtuples()
      self.setObjects(tuples)
      self._silenceCallback = False
      self.show()

  def setUpdateSilence(self, silence):
    "Silences/unsilences the update of the table until switched again"
    self._updateSilence = silence

  def _selectionCallback(self, structureEnsemble, row, col):
    "Callback for selecting a row in the table"
    self._current.structureEnsemble = structureEnsemble

  def _actionCallback(self, atomRecordTuple, row, column):
    print(atomRecordTuple, row, column)

  def _selectionPulldownCallback(self, item):
    "Callback for selecting NmrChain"
    structureEnsemble = self._project.getByPid(item)
    # print('>selectionPulldownCallback>', item, type(item), nmrChain)
    if structureEnsemble is not None:
      self.displayTableForStructure(structureEnsemble)

  def _updateCallback(self, data):
    "callback for updating the table"
    structureEnsemble = data['theObject']
    # print('>updateCallback>', data['notifier'], nmrChain, data['trigger'], data['object'], self._updateSilence)
    if structureEnsemble is not None:
      self._update(structureEnsemble)

  def destroy(self):
    "Cleanup of self"
    if self._structureNotifier is not None:
      self._structureNotifier.unRegister()
    if self._peaksNotifier is not None:
      self._peaksNotifier.unRegister()


  def navigateToStructureInDisplay(structureEnsemble, display, stripIndex=0, widths=None,
                                    showSequentialStructures=False, markPositions=True):

    getLogger().debug('display=%r, nmrResidue=%r, showSequentialResidues=%s, markPositions=%s' %
                      (display.id, structureEnsemble.id, showSequentialStructures, markPositions)
                      )

    return None

