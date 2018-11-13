"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.ui.gui.widgets.QuickTable import QuickTable
from ccpn.ui.gui.widgets.Column import Column, ColumnClass
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import RestraintsPulldown
from ccpn.core.RestraintList import RestraintList
from ccpn.core.Restraint import Restraint
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier

from ccpn.util.Logging import getLogger
logger = getLogger()
ALL = '<all>'


class RestraintTableModule(CcpnModule):
  """
  This class implements the module by wrapping a restaintsTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'left'

  className = 'RestraintTableModule'

  # we are subclassing this Module, hence some more arguments to the init
  def __init__(self, mainWindow=None, name='Restraint Table', restraintList=None):
    """
    Initialise the Module widgets
    """
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    # Put all of the NmrTable settings in a widget, as there will be more added in the PickAndAssign, and
    # backBoneAssignment modules
    self._RTwidget = Widget(self.settingsWidget, setLayout=True,
                             grid=(0,0), vAlign='top', hAlign='left')

    # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
    # underpinning the addNotifier call do not allow for it either

    #FIXME:ED - need to check label text and function of these
    colwidth = 140
    self.displaysWidget = ListCompoundWidget(self._RTwidget,
                                             grid=(0,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             vPolicy='minimal',
                                             #minimumWidths=(colwidth, 0, 0),
                                             fixedWidths=(colwidth, 2*colwidth, None),
                                             orientation = 'left',
                                             labelText='Display(s):',
                                             tipText = 'SpectrumDisplay modules to respond to double-click',
                                             texts=[ALL] + [display.pid for display in self.mainWindow.spectrumDisplays]
                                             )
    self.displaysWidget.setPreSelect(self._fillDisplayWidget)
    self.displaysWidget.setFixedHeights((None, None, 40))

    self.sequentialStripsWidget = CheckBoxCompoundWidget(
                                             self._RTwidget,
                                             grid=(1,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Show sequential strips:',
                                             checked = False
                                            )

    self.markPositionsWidget = CheckBoxCompoundWidget(
                                             self._RTwidget,
                                             grid=(2,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Mark positions:',
                                             checked = True
                                            )
    self.autoClearMarksWidget = CheckBoxCompoundWidget(
                                             self._RTwidget,
                                             grid=(3,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Auto clear marks:',
                                             checked = True
                                            )

    self.restraintTable = RestraintTable(parent=self.mainWidget
                                       , mainWindow=self.mainWindow
                                       , moduleParent=self
                                       , setLayout=True
                                       , grid=(0, 0))
    # settingsWidget

    if restraintList is not None:
      self.selectRestraintList(restraintList)

    # install the event filter to handle maximising from floated dock
    self.installMaximiseEventHandler(self._maximise, self._closeModule)

  def _fillDisplayWidget(self):
    list = ['> select-to-add <'] + [ALL] + [display.pid for display in self.mainWindow.spectrumDisplays]
    self.displaysWidget.pulldownList.setData(texts=list)

  def _maximise(self):
    """
    Maximise the attached table
    """
    self.restraintTable._maximise()

  def selectRestraintList(self, restraintList=None):
    """
    Manually select a StructureEnsemble from the pullDown
    """
    self.restraintTable._selectRestraintList(restraintList)

  def _getDisplays(self):
    """
    Return list of displays to navigate - if needed
    """
    displays = []
    # check for valid displays
    gids = self.displaysWidget.getTexts()
    if len(gids) == 0: return displays
    if ALL in gids:
        displays = self.application.ui.mainWindow.spectrumDisplays
    else:
        displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
    return displays

  def _closeModule(self):
    """
    CCPN-INTERNAL: used to close the module
    """
    self.restraintTable._close()
    super(RestraintTableModule, self)._closeModule()

  def close(self):
    """
    Close the table from the commandline
    """
    self._closeModule()


class RestraintTable(QuickTable):
  """
  Class to present a RestraintTable pulldown list, wrapped in a Widget
  """
  className = 'RestraintTable'
  attributeName = 'restraintLists'

  OBJECT = 'object'
  TABLE = 'table'

  def __init__(self, parent=None, mainWindow=None, moduleParent=None, restraintList=None, **kwds):
    """
    Initialise the widgets for the module.
    """
    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current
    self.moduleParent=moduleParent
    RestraintTable.project = self.project

    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)
    self.restraintList = None

    # create the column objects
    self.RLcolumns = ColumnClass([('#', '_key', 'Restraint Id', None),
                                  ('Pid', lambda restraint:restraint.pid, 'Pid of integral', None),
                                  ('_object', lambda restraint:restraint, 'Object', None),
                                  ('Atoms', lambda restraint:RestraintTable._getContributions(restraint),
                  'Atoms involved in the restraint', None),
                 ('Target Value.', 'targetValue', 'Target value for the restraint', None),
                 ('Upper Limit', 'upperLimit', 'Upper limit for the restraint', None),
                 ('Lower Limit', 'lowerLimit', 'Lower limit or the restraint', None),
                 ('Error', 'error', 'Error on the restraint', None),
                 ('Peaks', lambda restraint:'%3d ' % RestraintTable._getRestraintPeakCount(restraint),
                  'Number of peaks used to derive this restraint', None),
                 # ('Peak count', lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift))
                ('Comment', lambda restraint:RestraintTable._getCommentText(restraint), 'Notes',
                 lambda restraint, value:RestraintTable._setComment(restraint, value))
                ])      # [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

    # create the table; objects are added later via the displayTableForRestraints method
    self.spacer = Spacer(self._widget, 5, 5
                         , QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                         , grid=(0, 0), gridSpan=(1, 1))
    self.rtWidget = RestraintsPulldown(parent=self._widget
                                     , project=self.project, default=0
                                     , grid=(1,0), gridSpan=(1,1), minimumWidths=(0,100)
                                     , showSelectName=True
                                     , sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents
                                     , callback=self._selectionPulldownCallback)
    self.spacer = Spacer(self._widget, 5, 5
                         , QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                         , grid=(2, 0), gridSpan=(1, 1))

    self._widget.setFixedHeight(30)

    # initialise the currently attached dataFrame
    self._hiddenColumns = ['Pid']
    self.dataFrameObject = None

    # initialise the table
    QuickTable.__init__(self, parent=parent
                        , mainWindow=self.mainWindow
                        , dataFrameObject=None
                        , setLayout=True
                        , autoResize=True
                        , selectionCallback=self._selectionCallback
                        , actionCallback=self._actionCallback
                        , grid=(3, 0), gridSpan=(1, 6))

    # self._restraintListNotifier = None
    # self._restraintNotifier = None
    #
    # #TODO: see how to handle peaks as this is too costly at present
    # # Notifier object to update the table if the peaks change
    # self._peaksNotifier = None
    # self._updateSilence = False  # flag to silence updating of the table
    # self._setNotifiers()

    if restraintList is not None:
      self._selectRestraintList(restraintList)

    self.setTableNotifiers(tableClass=RestraintList,
                           rowClass=Restraint,
                           cellClassNames=None,
                           tableName='restraintList', rowName='restraint',
                           changeFunc=self.displayTableForRestraint,
                           className=self.attributeName,
                           updateFunc=self._update,
                           tableSelection='restraintList',
                           pullDownWidget=self.RLcolumns,
                           callBackClass=Restraint,
                           selectCurrentCallBack=None)
    self.droppedNotifier = GuiNotifier(self,
                                       [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                       self._processDroppedItems)

  def _getPullDownSelection(self):
    return self.rtWidget.getText()

  def _selectPullDown(self, value):
    self.rtWidget.select(value)


  def _processDroppedItems(self, data):
    """
    CallBack for Drop events
    """
    pids = data.get('pids', [])
    self._handleDroppedItems(pids, RestraintList, self.rtWidget)

  def addWidgetToTop(self, widget, col=2, colSpan=1):
    """
    Convenience to add a widget to the top of the table; col >= 2
    """
    if col < 2:
      raise RuntimeError('Col has to be >= 2')
    self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

  def _selectRestraintList(self, restraintList=None):
    """
    Manually select a restraintList from the pullDown
    """
    if restraintList is None:
      logger.debug('select: No RestraintList selected')
      raise ValueError('select: No RestraintList selected')
    else:
      if not isinstance(restraintList, RestraintList):
        logger.debug('select: Object is not of type RestraintList')
        raise TypeError('select: Object is not of type RestraintList')
      else:
        for widgetObj in self.rtWidget.textList:
          if restraintList.pid == widgetObj:
            self.restraintList = restraintList
            self.rtWidget.select(self.restraintList.pid)

  def displayTableForRestraint(self, restraintList):
    """
    Display the table for all Restraints"
    """
    self.rtWidget.select(restraintList.pid)
    self._update(restraintList)

  def _updateCallback(self, data):
    """
    Notifier callback for updating the table
    """
    thisRestraintList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the restraintList
    if self.restraintList in thisRestraintList:
      self.displayTableForRestraint(self.restraintList)
    else:
      self.clear()

  def _maximise(self):
    """
    Redraw the table on a maximise event
    """
    if self.restraintList:
      self.displayTableForRestraint(self.restraintList)
    else:
      self.clear()

  def _update(self, restraintList):
    """
    Update the table
    """
    self.project.blankNotification()
    objs = self.getSelectedObjects()

    self._dataFrameObject = self.getDataFrameFromList(table=self
                                                , buildList=restraintList.restraints
                                                , colDefs=self.RLcolumns
                                                , hiddenColumns=self._hiddenColumns)

    # populate from the Pandas dataFrame inside the dataFrameObject
    self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
    self._highLightObjs(objs)
    self.project.unblankNotification()

  def setUpdateSilence(self, silence):
    """
    Silences/unsilences the update of the table until switched again
    """
    self._updateSilence = silence

  def _selectionCallback(self, data, *args):
    """
    Notifier Callback for selecting a row in the table
    """
    restraint = data[Notifier.OBJECT]

    self.current.restraint = restraint
    RestraintTableModule.currentCallback = {'object':self.restraintList, 'table':self}

  def _actionCallback(self, data, *args):
    """
    Notifier DoubleClick action on item in table
    """
    restraint = data[Notifier.OBJECT]

    logger.debug(str(NotImplemented))

  def _selectionPulldownCallback(self, item):
    """
    Notifier Callback for selecting restraint from the pull down menu
    """
    self.restraintList = self.project.getByPid(item)
    logger.debug('>selectionPulldownCallback>', item, type(item), self.restraintList)
    if self.restraintList is not None:
      # self.thisDataSet = self._getAttachedDataSet(item)
      self.displayTableForRestraint(self.restraintList)
    else:
      self.clearTable()

  def navigateToRestraintInDisplay(restraint, display, stripIndex=0, widths=None,
                                    showSequentialStructures=False, markPositions=True):
    """
    Notifier Callback for selecting Object from item in the table
    """
    logger.debug('display=%r, nmrResidue=%r, showSequentialResidues=%s, markPositions=%s' %
                      (display.id, restraint.id, showSequentialStructures, markPositions)
                      )
    return None

  @staticmethod
  def _getContributions(restraint):
    """
    CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList
    """
    if restraint.restraintContributions[0].restraintItems:
      return ' - '.join(restraint.restraintContributions[0].restraintItems[0])

  @staticmethod
  def _getRestraintPeakCount(restraint):
    """
    CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList
    """
    peaks = restraint.peaks
    if peaks:
      return len(peaks)
    else:
      return 0

  def _callback(self):
    """
    CCPN-INTERNAL: Notifier callback inactive
    """
    pass

  # @staticmethod
  # def _getCommentText(chemicalShift):
  #   """
  #   CCPN-INTERNAL: Get a comment from ObjectTable
  #   """
  #   try:
  #     if chemicalShift.comment == '' or not chemicalShift.comment:
  #       return ''
  #     else:
  #       return chemicalShift.comment
  #   except:
  #     return ''
  #
  # @staticmethod
  # def _setComment(chemicalShift, value):
  #   """
  #   CCPN-INTERNAL: Insert a comment into ObjectTable
  #   """
  #   RestraintTable.project.blankNotification()
  #   chemicalShift.comment = value
  #   RestraintTable.project.unblankNotification()
  #
  # def _setNotifiers(self):
  #   """
  #   Set a Notifier to call when an object is created/deleted/renamed/changed
  #   rename calls on name
  #   change calls on any other attribute
  #   """
  #   self._clearNotifiers()
  #   self._restraintListNotifier = Notifier(self.project
  #                                     , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
  #                                     , RestraintList.__name__
  #                                     , self._updateCallback)
  #   self._restraintNotifier = Notifier(self.project
  #                                     , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE]
  #                                     , Restraint.__name__
  #                                     , self._updateCallback)
  #
  # def _clearNotifiers(self):
  #   """
  #   clean up the notifiers
  #   """
  #   if self._restraintListNotifier is not None:
  #     self._restraintListNotifier.unRegister()
  #   if self._restraintNotifier is not None:
  #     self._restraintNotifier.unRegister()
  #   if self._peaksNotifier is not None:
  #     self._peaksNotifier.unRegister()

  def _close(self):
    """
    Cleanup the notifiers when the window is closed
    """
    self.clearTableNotifiers()
