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
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import StructurePulldown
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.widgets.MessageDialog import showInfo
from ccpn.ui.gui.widgets.MessageDialog import showWarning

from ccpn.ui.gui.lib.Strip import navigateToNmrResidueInDisplay

from ccpn.util.Logging import getLogger
logger = getLogger()

ALL = '<all>'

class StructureTableModule(CcpnModule):
  """
  This class implements the module by wrapping a StructureTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsOnTop = True

  className = 'StructureTableModule'

  # we are subclassing this Module, hence some more arguments to the init
  def __init__(self, mainWindow, name='Structure Table', itemPid=None):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # add test structure Ensembles
    try:
      StructureTableModule.defined
    except:
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

      self.ensemble = self.project.newStructureEnsemble()
      self.ensemble.data = self.data.extract(index='1, 2, 6-7, 9')

      # make a test dataset in here

      self.dataSet = self.project.newDataSet(self.ensemble.longPid)    # title - should be ensemble name/title/longPid

      self.dataItem = self.dataSet.newData('derivedConformers')
      self.dataSet.attachedObject = self.ensemble       # the newest object
      self.dataItem.setParameter(name='backboneSelector', value=self.ensemble.data.backboneSelector)

      StructureTableModule.defined=True
      # should be a DataSet with the corresponding stuff in it
      #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    finally:
      pass

    # settings

    self.itemPid = itemPid      # read the passed in object
                                # this could come from DataSet or Structures

    # Put all of the NmrTable settings in a widget, as there will be more added in the PickAndAssign, and
    # backBoneAssignment modules
    self._NTSwidget = Widget(self.settingsWidget, setLayout=True,
                             grid=(0,0), vAlign='top', hAlign='left')
    #self._NTSwidget = self.settingsWidget

    # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
    # underpinning the addNotifier call do not allow for it either

    #FIXME:ED - need to check label text and function of these
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
    self.structureTable = StructureTable(parent=self.mainWidget
                                        , setLayout=True
                                        , application=self.application
                                        , grid=(0,0), itemPid=itemPid)
    self.mainWidget.setContentsMargins(5, 5, 5, 5)    # ejb - put into CcpnModule?

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


class StructureTable(ObjectTable):
  """
  Class to present a StructureTable and a StructureData pulldown list, wrapped in a Widget
  """
  def stLam(self, row, name, valType):
    try:
      thisVal = getattr(row, name)
      if valType is str:
        return str(thisVal)
      elif valType is float:
        return float(thisVal)
      elif valType is int:
        return int(thisVal)
      else:
        return None
    except:
      return None

  #row.modelNumber, etc., may not exist..

  columnDefs = [
                ('modelNumber', lambda row: StructureTable.stLam(StructureTable, row, 'modelNumber', int), 'modelNumber'),
                ('chainCode', lambda row: StructureTable.stLam(StructureTable, row, 'chainCode', str), 'chainCode'),
                ('sequenceId', lambda row: StructureTable.stLam(StructureTable, row, 'sequenceId', int), 'sequenceId'),
                ('insertionCode', lambda row: StructureTable.stLam(StructureTable, row, 'insertionCode', str), 'insertionCode'),
                ('residueName', lambda row: StructureTable.stLam(StructureTable, row, 'residueName', str), 'residueName'),
                ('atomName', lambda row: StructureTable.stLam(StructureTable, row, 'atomName', str), 'atomName'),
                ('altLocationCode', lambda row: StructureTable.stLam(StructureTable, row, 'altLocationCode', str), 'altLocationCode'),
                ('element', lambda row: StructureTable.stLam(StructureTable, row, 'element', str), 'element'),
                ('x', lambda row: StructureTable.stLam(StructureTable, row, 'x', float), 'x'),
                ('y', lambda row: StructureTable.stLam(StructureTable, row, 'y', float), 'y'),
                ('z', lambda row: StructureTable.stLam(StructureTable, row, 'z', float), 'z'),
                ('occupancy', lambda row: StructureTable.stLam(StructureTable, row, 'occupancy', float), 'occupancy'),
                ('bFactor', lambda row: StructureTable.stLam(StructureTable, row, 'bFactor', float), 'bFactor'),
                ('nmrChainCode', lambda row: StructureTable.stLam(StructureTable, row, 'nmrChainCode', str), 'nmrChainCode'),
                ('nmrSequenceCode', lambda row: StructureTable.stLam(StructureTable, row, 'nmrSequenceCode', str), 'nmrSequenceCode'),
                ('nmrResidueName', lambda row: StructureTable.stLam(StructureTable, row, 'nmrResidueName', str), 'nmrResidueName'),
                ('nmrAtomName', lambda row: StructureTable.stLam(StructureTable, row, 'nmrAtomName', str), 'nmrAtomName')
  ]

  def __init__(self, parent, application, itemPid=None, **kwds):
    self._application = application
    self._project = application.project
    self._current = application.current
    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)
    self.itemPid=itemPid

    # create the column objects
    columns = [Column(colName, func, tipText=tipText) for colName, func, tipText in self.columnDefs]

    # selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback
    # create the table; objects are added later via the displayTableForStructure method
    ObjectTable.__init__(self, parent=self._widget, setLayout=True,
                         columns=columns, objects = [],
                         autoResize=True,
                         selectionCallback=self._selectionCallback,
                         actionCallback=self._actionCallback,
                         grid = (2, 0), gridSpan = (1, 6)
                         )
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(1,0), gridSpan=(1,1))

    # Notifier object to update the table if the nmrChain changes
    self._ensembleNotifier = None
    #TODO: see how to handle peaks as this is too costly at present
    # Notifier object to update the table if the peaks change
    self._peaksNotifier = None
    # self._peaksNotifier = Notifier(self._project,
    #                                [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], 'Peak',
    #                                 self._updateCallback
    #                                )
    self._updateSilence = False  # flag to silence updating of the table

    # This widget will display a pulldown list of Structure pids in the project
    self.stWidget = StructurePulldown(parent=self._widget
                                     , project=self._project, default=0  # first Structure in project (if present)
                                     , grid=(0,0), gridSpan=(1,1), minimumWidths=(0,100)
                                     , callback=self._selectionPulldownCallback)

    # if self.itemPid:
    #   thisObj = self._project.getByPid(self.itemPid)
    #   if thisObj.shortClassName == 'SE':
    #     self.displayTableForStructure(thisObj)
    #   elif thisObj.shortClassName == 'DS':

    if not itemPid:
      if len(self._project.structureEnsembles) > 0:
        self.itemPid = self._project.structureEnsembles[0].pid

    self.thisObj = self._project.getByPid(self.itemPid)
    self.thisDataSet = self._getAttachedDataSet(self.itemPid)

    self.stButtons = RadioButtons(self._widget, texts=['Ensemble', 'Average']
                                  , selectedInd=1
                                  , callback=self._selectionButtonCallback
                                  , direction='h'
                                  , tipTexts=None
                                  , setLayout=True
                                  , grid=(0,2), gridSpan=(1,3))

    self.displayTableForStructure(self.thisObj)

  def addWidgetToTop(self, widget, col=2, colSpan=1):
    "Convenience to add a widget to the top of the table; col >= 2"
    if col < 2:
      raise RuntimeError('Col has to be >= 2')
    self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

  def displayTableForStructure(self, structureEnsemble):
    "Display the table for all StructureEnsembles"

    if self._ensembleNotifier is not None:
      # we have a new nmrChain and hence need to unregister the previous notifier
      self._ensembleNotifier.unRegister()
    # register a notifier for this structureEnsemble
    self._ensembleNotifier = Notifier(structureEnsemble,
                                   [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], 'StructureEnsemble',
                                    self._updateCallback
                                  )

    self.stWidget.select(structureEnsemble.pid)
    self._update(structureEnsemble)

  def displayTableForDataSetStructure(self, structureData):
    "Display the table for all StructureDataSet"

    #FIXME:ED doesn't work for StructureData, but only a test
    # if self._ensembleNotifier is not None:
    #   # we have a new nmrChain and hence need to unregister the previous notifier
    #   self._ensembleNotifier.unRegister()
    # register a notifier for this structureEnsemble
    # self._ensembleNotifier = Notifier(structureData,
    #                                [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], 'StructureData',
    #                                 self._updateCallback
    #                               )

    # self.stWidget.select(structureData.pid)
    for dt in self.thisDataSet.data:
      if dt.name is 'derivedConformers':
        try:
          self.params = dt.parameters
          thisFunc = self.params['backboneSelector']
          thisSubset = self.thisObj.data.extract(thisFunc)
          self._updateDataSet(thisSubset)
        except:
          pass

  def _getAttachedDataSet(self, item):
    if item:
      thisObj = self._project.getByPid(self.itemPid)
      if self._project.dataSets:
        for dd in self._project.dataSets:
          if dd.title is thisObj.longPid:

            thisDataSet = dd
            for dt in self.thisDataSet.data:
              if dt.name is 'derivedConformers':
                try:
                  self.params = dt.parameters
                  thisFunc = self.params['backboneSelector']
                  return thisDataSet
                  # thisSubset = thisAttached.data.extract(thisFunc)
                  # self.displayTableForStructure(thisSubset)
                  # self.displayTableForDataSetStructure(thisSubset)
                except:
                  return None
    else:
      return None

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

  def _updateDataSet(self, structureData):
    "Update the table"
    if not self._updateSilence:
      self.clearTable()
      self._silenceCallback = True

      # model = PandasModel(structureEnsemble.data)   # ejb - interesting, set QTableView form Pandas
      # self.setModel(model)
      # self.setSortingEnabled(True)
      tuples = structureData.as_namedtuples()
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
    "Callback for selecting Structure"
    structureEnsemble = self._project.getByPid(item)
    # print('>selectionPulldownCallback>', item, type(item), nmrChain)
    if structureEnsemble is not None:
      self.thisDataSet = self._getAttachedDataSet(item)
      self.displayTableForStructure(structureEnsemble)

  def _selectionButtonCallback(self):
    "Callback for selecting Structure Ensemble or Average"
    item = self.stButtons.get()
    # print('>selectionPulldownCallback>', item, type(item), nmrChain)
    if self.thisObj is not None:
      if item is 'Ensemble':
        self.displayTableForStructure(self.thisObj)
      elif item is 'Average':
        self.displayTableForDataSetStructure(self.thisObj)

  def _updateCallback(self, data):
    "callback for updating the table"
    structureEnsemble = data['theObject']
    # print('>updateCallback>', data['notifier'], nmrChain, data['trigger'], data['object'], self._updateSilence)
    if structureEnsemble is not None:
      self._update(structureEnsemble)

  def destroy(self):
    "Cleanup of self"
    if self._ensembleNotifier is not None:
      self._ensembleNotifier.unRegister()
    if self._peaksNotifier is not None:
      self._peaksNotifier.unRegister()


  def navigateToStructureInDisplay(structureEnsemble, display, stripIndex=0, widths=None,
                                    showSequentialStructures=False, markPositions=True):

    getLogger().debug('display=%r, nmrResidue=%r, showSequentialResidues=%s, markPositions=%s' %
                      (display.id, structureEnsemble.id, showSequentialStructures, markPositions)
                      )

    return None

