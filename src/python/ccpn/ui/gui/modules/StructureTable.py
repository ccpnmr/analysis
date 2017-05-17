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

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import StructurePulldown
from ccpn.ui.gui.widgets.Table import ObjectTable, Column, ColumnViewSettings,  ObjectTableFilter
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.ui._implementation.Module import Module

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
    """
    Initialise the Module widgets
    """
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current
    self.itemPid = itemPid      # read the passed in object
                                # this could come from DataSet or Structures

    # #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # # add test structure Ensembles
    # try:
    #   StructureTableModule.defined
    # except:
    #   #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    #   self.ensemble = self.project.newStructureEnsemble()
    #   self.data = self.ensemble.data
    #
    #   self.testAtomName = ['CA', 'C', 'N', 'O', 'H'
    #     , 'CB', 'HB1', 'HB2', 'HB3'
    #     , 'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23'
    #     , 'CE', 'HE1', 'HE2', 'HE3'
    #     , 'CG', 'HG1', 'HG2', 'HG3'
    #     , 'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
    #   self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + [
    #                                                                                                  'VAL'] * 8
    #   self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
    #   self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    #   self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    #   self.comment = ['Test'] * 33
    #
    #   self.data['atomName'] = self.testAtomName
    #   self.data['residueName'] = self.testResidueName
    #   self.data['chainCode'] = self.testChainCode
    #   self.data['sequenceId'] = self.testSequenceId
    #   self.data['modelNumber'] = self.testModelNumber
    #   self.data['comment'] = self.comment
    #
    #   #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    #   self.ensemble = self.project.newStructureEnsemble()
    #   self.data = self.ensemble.data
    #
    #   self.testAtomName = ['CA', 'C', 'N', 'O', 'H'
    #     , 'CB', 'HB1', 'HB2', 'HB3'
    #     , 'CE', 'HE1', 'HE2', 'HE3'
    #     , 'CG', 'HG1', 'HG2', 'HG3'
    #     , 'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23'
    #     , 'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
    #   self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + [
    #                                                                                                  'VAL'] * 8
    #   self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
    #   self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    #   self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
    #
    #   self.data['atomName'] = self.testAtomName
    #   self.data['residueName'] = self.testResidueName
    #   self.data['chainCode'] = self.testChainCode
    #   self.data['sequenceId'] = self.testSequenceId
    #   self.data['modelNumber'] = self.testModelNumber
    #   self.data['comment'] = self.comment
    #
    #   self.ensemble = self.project.newStructureEnsemble()
    #   self.ensemble.data = self.data.extract(index='1, 2, 6-7, 9')
    #
    #   # make a test dataset in here
    #
    #   self.dataSet = self.project.newDataSet(self.ensemble.longPid)    # title - should be ensemble name/title/longPid
    #
    #   self.dataItem = self.dataSet.newData('derivedConformers')
    #   self.dataSet.attachedObject = self.ensemble       # the newest object
    #   self.dataItem.setParameter(name='backboneSelector', value=self.ensemble.data.backboneSelector)
    #
    #   StructureTableModule.defined=True
    #   # should be a DataSet with the corresponding stuff in it
    #   #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # finally:
    #   pass

    # settings
    # Put all of the NmrTable settings in a widget, as there will be more added in the PickAndAssign, and
    # backBoneAssignment modules
    self._STwidget = Widget(self.settingsWidget, setLayout=True,
                             grid=(0,0), vAlign='top', hAlign='left')

    # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
    # underpinning the addNotifier call do not allow for it either

    #FIXME:ED - need to check label text and function of these
    colwidth = 140
    self.displaysWidget = ListCompoundWidget(self._STwidget,
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
                                             self._STwidget,
                                             grid=(1,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Show sequential strips:',
                                             checked = False
                                            )

    self.markPositionsWidget = CheckBoxCompoundWidget(
                                             self._STwidget,
                                             grid=(2,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Mark positions:',
                                             checked = True
                                            )
    self.autoClearMarksWidget = CheckBoxCompoundWidget(
                                             self._STwidget,
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
                                        , moduleParent=self
                                        , grid=(0,0), itemPid=itemPid)
    # settingsWidget
    self.displayColumnWidget = ColumnViewSettings(parent=self._STwidget, table=self.structureTable, grid=(4, 0))
    self.searchWidget = ObjectTableFilter(parent=self._STwidget, table=self.structureTable, grid=(5, 0))


  def _getDisplays(self) -> list:
    """
    Return list of displays to navigate - if needed
    """
    displays = []
    # check for valid displays
    gids = self.displaysWidget.getTexts()
    if len(gids) == 0: return displays
    if ALL in gids:
        displays = self.mainWindow.spectrumDisplays
    else:
        displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
    return displays

  def _getDisplayColumnWidget(self):
    """
    CCPN-INTERNAL: used to get displayColumnWidget
    """
    return self.displayColumnWidget

  def _getSearchWidget(self):
    """
    CCPN-INTERNAL: used to get searchWidget
    """
    return self.searchWidget

  def _closeModule(self):
    """
    CCPN-INTERNAL: used to close the module
    """
    self.structureTable._close()
    super(StructureTableModule, self)._closeModule()


class StructureTable(ObjectTable):
  """
  Class to present a StructureTable and a StructureData pulldown list, wrapped in a Widget
  """
  #row.modelNumber, etc., may not exist..
  columnDefs = [
                ('#', lambda row: StructureTable._stLamInt(row, 'Index'), 'Index', None),
                ('modelNumber', lambda row: StructureTable._stLamInt(row, 'modelNumber'), 'modelNumber', None),
                ('chainCode', lambda row: StructureTable._stLamStr(row, 'chainCode'), 'chainCode', None),
                ('sequenceId', lambda row: StructureTable._stLamInt(row, 'sequenceId'), 'sequenceId', None),
                ('insertionCode', lambda row: StructureTable._stLamStr(row, 'insertionCode'), 'insertionCode', None),
                ('residueName', lambda row: StructureTable._stLamStr(row, 'residueName'), 'residueName', None),
                ('atomName', lambda row: StructureTable._stLamStr(row, 'atomName'), 'atomName', None),
                ('altLocationCode', lambda row: StructureTable._stLamStr(row, 'altLocationCode'), 'altLocationCode', None),
                ('element', lambda row: StructureTable._stLamStr(row, 'element'), 'element', None),
                ('x', lambda row: StructureTable._stLamFloat(row, 'x'), 'x', None),
                ('y', lambda row: StructureTable._stLamFloat(row, 'y'), 'y', None),
                ('z', lambda row: StructureTable._stLamFloat(row, 'z'), 'z', None),
                ('occupancy', lambda row: StructureTable._stLamFloat(row, 'occupancy'), 'occupancy', None),
                ('bFactor', lambda row: StructureTable._stLamFloat(row, 'bFactor'), 'bFactor', None),
                ('nmrChainCode', lambda row: StructureTable._stLamStr(row, 'nmrChainCode'), 'nmrChainCode', None),
                ('nmrSequenceCode', lambda row: StructureTable._stLamStr(row, 'nmrSequenceCode'), 'nmrSequenceCode', None),
                ('nmrResidueName', lambda row: StructureTable._stLamStr(row, 'nmrResidueName'), 'nmrResidueName', None),
                ('nmrAtomName', lambda row: StructureTable._stLamStr(row, 'nmrAtomName'), 'nmrAtomName', None),
                ('Comment', lambda row:StructureTable._getCommentText(row), 'Notes',
                 lambda row, value:StructureTable._setComment(row, 'comment', value))
  ]

  className = 'StructureTable'
  objectClass = 'StructureEnsemble'
  attributeName = 'structureEnsembles'

  OBJECT = 'object'
  TABLE = 'table'

  def __init__(self, parent, application, moduleParent, itemPid=None, **kwds):
    """
    Initialise the widgets for the module.
    :param parent: parent widget
    :param application: needed
    :param moduleParent: module area to insert module
    :param itemPid: should be None
    :param kwds:
    """
    self.moduleParent=moduleParent
    self._application = application
    self._project = application.project
    self._current = application.current
    self._widget = Widget(parent=parent, **kwds)
    self.itemPid=itemPid
    self.thisObj=None

    # create the column objects
    columns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

    # create the table; objects are added later via the displayTableForStructure method
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(0,0), gridSpan=(1,1))
    self.stWidget = StructurePulldown(parent=self._widget
                                     , project=self._project, default=0  # first Structure in project (if present)
                                     , grid=(1,0), gridSpan=(1,1), minimumWidths=(0,100)
                                     , showSelectName=True
                                     , callback=self._selectionPulldownCallback)
    self.stButtons = RadioButtons(self._widget, texts=['Ensemble', 'Average']
                                  , selectedInd=1
                                  , callback=self._selectionButtonCallback
                                  , direction='h'
                                  , tipTexts=None
                                  , setLayout=True
                                  , grid=(1,2), gridSpan=(1,3))
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(2,0), gridSpan=(1,1))
    ObjectTable.__init__(self, parent=self._widget, setLayout=True,
                         columns=columns, objects = [],
                         autoResize=True,
                         selectionCallback=self._selectionCallback,
                         actionCallback=self._actionCallback,
                         grid = (3, 0), gridSpan = (1, 6)
                         )

    # Notifier object to update the table if the Structure changes
    self._ensembleNotifier = Notifier(self._project
                                      , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                      , StructureEnsemble.__name__
                                      , self._updateCallback)

    #TODO: see how to handle peaks as this is too costly at present
    # Notifier object to update the table if the peaks change
    self._peaksNotifier = None
    self._updateSilence = False  # flag to silence updating of the table

    if self.itemPid:
      self.thisObj = self._project.getByPid(self.itemPid)
      self.thisDataSet = self._getAttachedDataSet(self.itemPid)
      self.displayTableForStructure(self.thisObj)
    else:
      self.thisObj=None

  def addWidgetToTop(self, widget, col=2, colSpan=1):
    """
    Convenience to add a widget to the top of the table; col >= 2
    """
    if col < 2:
      raise RuntimeError('Col has to be >= 2')
    self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

  def displayTableForStructure(self, structureEnsemble):
    """
    Display the table for all StructureEnsembles
    """
    self.stWidget.select(structureEnsemble.pid)
    self._update(structureEnsemble)

  def displayTableForDataSetStructure(self, structureEnsemble):
    """
    Display the table for all StructureDataSet
    """

    # self.stWidget.select(structureEnsemble.pid)
    #
    # if self.thisDataSet:
    #   for dt in self.thisDataSet.data:
    #     if dt.name is 'derivedConformers':
    #       try:
    #         self.params = dt.parameters
    #         thisFunc = self.params['backboneSelector']
    #         thisSubset = self.thisObj.data.extract(thisFunc)
    #         self._updateDataSet(thisSubset)
    #       except:
    #         pass

    from ccpn.util.StructureData import averageStructure        # ejb - from TJ
    try:
      self._updateDataSet(averageStructure(structureEnsemble.data))
    except:
      info = showWarning(self.thisObj.pid+' contains no Average', '')
      self.stButtons.setIndex(0)

    # self.stWidget.select(structureEnsemble.pid)

    # # ejb - doesn't work, can't store in a DataSet
    # if self.thisDataSet:
    #   for dt in self.thisDataSet.data:
    #     if dt.name is 'derivedConformers':
    #       # self.params = dt.parameters
    #       # self._updateDataSet(dt.parameters['Average'])
    #       self._updateDataSet(dt.attachedObject)

  def _getAttachedDataSet(self, item):
    """
    Get the DataSet object attached to this StructureEnsemble
    """
    thisObj = item
    Found=False
    dd = dt = None
    self.thisDataSet = None
    if self._project.dataSets:
      for dd in self._project.dataSets:
        if dd.title == thisObj.longPid:
          for dt in self.thisDataSet.data:
            if dt.name is 'derivedConformers':
              Found=True

    if not Found:
      dd = self._project.newDataSet(thisObj.longPid)  # title - should be ensemble name/title/longPid
      dt = dd.newData('derivedConformers')
    self.thisDataSet = dd

    if 'Average' not in dt.parameters:
      from ccpn.util.StructureData import averageStructure
      # dt.parameters['Average'] = averageStructure(item.data)
      # dt.setParameter(name='Average', value=averageStructure(item.data))
      # dt.attachedObject = averageStructure(item.data)
      # ejb - does't work, can't store in a DataSet

      # for dd in self._project.dataSets:
      #
      #   if dd.title == thisObj.longPid:
      #
      #     self.thisDataSet = dd
      #     for dt in self.thisDataSet.data:
      #       if dt.name is 'derivedConformers':
      #         self.params = dt.parameters
      #         # thisFunc = self.params['backboneSelector']
      #
      #         if 'Average' not in self.params:
      #           from ccpn.util.StructureData import averageStructure
      #           self.params['Average'] = averageStructure(item.data)
      #
      #         return self.params['Average']

    # if item:
    #   thisObj = self._project.getByPid(item)
    #   if self._project.dataSets:
    #     for dd in self._project.dataSets:
    #       if dd.title == thisObj.longPid:
    #
    #         self.thisDataSet = dd
    #         for dt in self.thisDataSet.data:
    #           if dt.name is 'derivedConformers':
    #             self.params = dt.parameters
    #             # thisFunc = self.params['backboneSelector']
    #
    #             if 'Average' not in self.params():
    #               from ccpn.util.StructureData import averageStructure
    #               self.params['Average'] = averageStructure(item.data)
    #
    #             return self.params['Average']
    # else:
    #   return None

  def _update(self, structureEnsemble):
    """
    Update the table from StructureEnsemble
    """
    if not self._updateSilence:
      self.clearTable()
      self._silenceCallback = True
      tuples = structureEnsemble.data.as_namedtuples()
      self.setObjects(tuples)
      self._updateSettingsWidgets()
      self._silenceCallback = False
      self.show()

  def _updateDataSet(self, structureData):
    """
    Update the table from EnsembleData
    """
    if not self._updateSilence:
      self.clearTable()
      self._silenceCallback = True
      tuples = structureData.as_namedtuples()
      self.setObjects(tuples)
      self._updateSettingsWidgets()
      self._silenceCallback = False
      self.show()

  def setUpdateSilence(self, silence):
    """
    Silences/unsilences the update of the table until switched again
    """
    self._updateSilence = silence

  def _selectionCallback(self, structureData, row, col):
    """
    Notifier Callback for selecting a row in the table
    """
    self._current.structureData = structureData
    StructureTable._current = {'object':self.thisObj, 'table':self}

  def _actionCallback(self, atomRecordTuple, row, column):
    """
    Notifier DoubleClick action on item in table
    """
    print('StructureTable>>>', atomRecordTuple, row, column)

  def _selectionPulldownCallback(self, item):
    """
    Notifier Callback for selecting Structure from the pull down menu
    """
    self.stButtons.setIndex(0)
    self.thisObj = self._project.getByPid(item)
    # print('>selectionPulldownCallback>', item, type(item), nmrChain)
    if self.thisObj is not None:
      # self._getAttachedDataSet(self.thisObj)        # no DataSets yet
      self.displayTableForStructure(self.thisObj)
    else:
      self.clearTable()

  def _selectionButtonCallback(self):
    """
    Notifier Callback for selecting Structure Ensemble or Average
    """
    item = self.stButtons.get()
    # print('>selectionPulldownCallback>', item, type(item), nmrChain)
    if self.thisObj is not None:
      if item is 'Ensemble':
        self.displayTableForStructure(self.thisObj)
      elif item is 'Average':
        self.displayTableForDataSetStructure(self.thisObj)
    else:
      self.clearTable()

  def _updateCallback(self, data):
    """
    Notifier Callback for updating the table
    """
    thisEnsembleList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the chainList
    # print('>updateCallback>', data['notifier'], nmrChain, data['trigger'], data['object'], self._updateSilence)
    if self.thisObj in thisEnsembleList:
      item = self.stButtons.get()
      # print('>selectionPulldownCallback>', item, type(item), nmrChain)
      if item is 'Ensemble':
        self.displayTableForStructure(self.thisObj)
      elif item is 'Average':
        self.displayTableForDataSetStructure(self.thisObj)
    else:
      self.clearTable()

  def navigateToStructureInDisplay(structureEnsemble, display, stripIndex=0, widths=None,
                                    showSequentialStructures=False, markPositions=True):
    """
    Notifier Callback for selecting Object from item in the table
    """
    getLogger().debug('display=%r, nmrResidue=%r, showSequentialResidues=%s, markPositions=%s' %
                      (display.id, structureEnsemble.id, showSequentialStructures, markPositions)
                      )
    return None

  @staticmethod
  def _getCommentText(structure):
    """
    CCPN-INTERNAL: Get a comment from ObjectTable
    """
    try:
      if structure.comment == '' or not structure.comment:
        return ''
      else:
        return structure.comment
    except:
      return ''       # .comment may not exist

  @staticmethod
  def _setComment(structure, column, value):
    """
    CCPN-INTERNAL: Insert a comment into ObjectTable
    """
    # structure.comment = value
    # ejb - need to use PandasMethod, value is an AtomRecordTuple

    index = structure.Index
    setKw = {column: value}
    thisObj = StructureTable._current[StructureTable.OBJECT].data

    thisData = thisObj.extract(index=[index])     # strange, needs to be a list
    try:
      thisObj[column]                             # check if the column exists
    except KeyError:
      numRows = len(thisObj.index)
      thisObj[column] = '' * numRows
      thisData[column] = '' * numRows             # need to set in both dataframes
    except:
      showWarning(StructureTable._current[StructureTable.OBJECT].pid+' update table error', '')
      return

    finally:
      thisObj.setValues(thisData, **setKw)        # ejb - update the object
      # StructureTable._current[StructureTable.TABLE]._updateDataSet(thisObj)

      tuples = thisObj.as_namedtuples()           # populate the table
      StructureTable._current[StructureTable.TABLE].setObjects(tuples)

  @staticmethod
  def _stLamInt(row, name):
    """
    CCPN-INTERNAL: Insert an int into ObjectTable
    """
    try:
      return int(getattr(row, name))
    except:
      return None

  @staticmethod
  def _stLamFloat(row, name):
    """
    CCPN-INTERNAL: Insert a float into ObjectTable
    """
    try:
      return float(getattr(row, name))
    except:
      return None

  @staticmethod
  def _stLamStr(row, name):
    """
    CCPN-INTERNAL: Insert a str into ObjectTable
    """
    try:
      return str(getattr(row, name))
    except:
      return None

  def _updateSettingsWidgets(self):
    """
    Update settings Widgets according with the new displayed table
    """
    displayColumnWidget = self.moduleParent._getDisplayColumnWidget()
    displayColumnWidget.updateWidgets(self)
    searchWidget = self.moduleParent._getSearchWidget()
    searchWidget.updateWidgets(self)

  def initialiseButtons(self, index):
    """
    Set index of radioButton
    """
    self.stButtons.setIndex(index)

  def _close(self):
    """
    Cleanup the notifiers when the window is closed
    """
    if self._ensembleNotifier is not None:
      self._ensembleNotifier.unRegister()
    if self._peaksNotifier is not None:
      self._peaksNotifier.unRegister()

