"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:04 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.ui.gui.widgets.Table import ObjectTable, Column, ColumnViewSettings,  ObjectTableFilter
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import RestraintsPulldown
from ccpn.core.RestraintList import RestraintList
from ccpn.core.Restraint import Restraint

from ccpn.util.Logging import getLogger
logger = getLogger()
ALL = '<all>'


class RestraintTableModule(CcpnModule):
  """
  This class implements the module by wrapping a restaintsTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'top'

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
                                             fixedWidths=(colwidth, colwidth, colwidth),
                                             orientation = 'left',
                                             labelText='Display(s):',
                                             tipText = 'SpectrumDisplay modules to respond to double-click',
                                             texts=[ALL] + [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
                                             )
    self.displaysWidget.setFixedHeigths((None, None, 40))

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
                                        , setLayout=True
                                        , application=self.application
                                        , moduleParent=self
                                        , grid=(0,0))
    # settingsWidget
    self.displayColumnWidget = ColumnViewSettings(parent=self._RTwidget, table=self.restraintTable, grid=(4, 0))
    self.searchWidget = ObjectTableFilter(parent=self._RTwidget, table=self.restraintTable, grid=(5, 0))

    if restraintList is not None:
      self.selectRestraintList(restraintList)

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
    self.restraintTable._close()
    super(RestraintTableModule, self)._closeModule()


class RestraintTable(ObjectTable):
  """
  Class to present a RestraintTable pulldown list, wrapped in a Widget
  """
  columnDefs = [('#', '_key', 'Restraint Id', None),
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
                ]

  className = 'RestraintTable'
  attributeName = 'restraintLists'

  OBJECT = 'object'
  TABLE = 'table'

  def __init__(self, parent, application, moduleParent, restraintList=None, **kwds):
    """
    Initialise the widgets for the module.
    """
    self.moduleParent = moduleParent
    self._application = application
    self._project = application.project
    self._current = application.current
    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)
    self.restraintList = None

    # create the column objects
    self.RLcolumns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

    # create the table; objects are added later via the displayTableForRestraints method
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(0, 0), gridSpan=(1, 1))
    self.rtWidget = RestraintsPulldown(parent=self._widget
                                     , project=self._project, default=0
                                     , grid=(1,0), gridSpan=(1,1), minimumWidths=(0,100)
                                     , showSelectName=True
                                     , callback=self._selectionPulldownCallback)
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(2, 0), gridSpan=(1, 1))
    ObjectTable.__init__(self, parent=self._widget, setLayout=True,
                         columns=self.RLcolumns, objects=[],
                         autoResize=True,
                         selectionCallback=self._selectionCallback,
                         actionCallback=self._actionCallback,
                         grid=(3, 0), gridSpan=(1, 6)
                         )

    self._restraintListNotifier = None
    self._restraintNotifier = None
    
    #TODO: see how to handle peaks as this is too costly at present
    # Notifier object to update the table if the peaks change
    self._peaksNotifier = None
    self._updateSilence = False  # flag to silence updating of the table
    self._setNotifiers()

    if restraintList is not None:
      self._selectRestraintList(restraintList)

  def addWidgetToTop(self, widget, col=2, colSpan=1):
    """
    Convenience to add a widget to the top of the table; col >= 2
    """
    if col < 2:
      raise RuntimeError('Col has to be >= 2')
    self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

  def _selectRestraintList(self, restraintList=None):
    """
    Manually select a NmrChain from the pullDown
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
            self.nmrChain = restraintList
            self.rtWidget.select(self.nmrChain.pid)

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
      self.clearTable()

  def _update(self, restraintList):
    """
    Update the table
    """
    if not self._updateSilence:
      self.setColumns(self.RLcolumns)
      self.setObjects(restraintList.restraints)
      self._updateSettingsWidgets()
      self.show()

  def setUpdateSilence(self, silence):
    """
    Silences/unsilences the update of the table until switched again
    """
    self._updateSilence = silence

  def _selectionCallback(self, restraint, row, col):
    """
    Notifier Callback for selecting a row in the table
    """
    self._current.restraint = restraint
    RestraintTableModule._currentCallback = {'object':self.restraintList, 'table':self}

  def _actionCallback(self, atomRecordTuple, row, column):
    """
    Notifier DoubleClick action on item in table
    """
    logger.debug('RestraintTable>>>', atomRecordTuple, row, column)

  def _selectionPulldownCallback(self, item):
    """
    Notifier Callback for selecting restraint from the pull down menu
    """
    self.restraintList = self._project.getByPid(item)
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

  @staticmethod
  def _getCommentText(chemicalShift):
    """
    CCPN-INTERNAL: Get a comment from ObjectTable
    """
    try:
      if chemicalShift.comment == '' or not chemicalShift.comment:
        return ''
      else:
        return chemicalShift.comment
    except:
      return ''

  @staticmethod
  def _setComment(chemicalShift, value):
    """
    CCPN-INTERNAL: Insert a comment into ObjectTable
    """
    chemicalShift.comment = value

  def _setNotifiers(self):
    """
    Set a Notifier to call when an object is created/deleted/renamed/changed
    rename calls on name
    change calls on any other attribute
    """
    self._clearNotifiers()
    self._restraintListNotifier = Notifier(self._project
                                      , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                      , RestraintList.__name__
                                      , self._updateCallback)
    self._restraintNotifier = Notifier(self._project
                                      , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE]
                                      , Restraint.__name__
                                      , self._updateCallback)

  def _clearNotifiers(self):
    """
    clean up the notifiers
    """
    if self._restraintListNotifier is not None:
      self._restraintListNotifier.unRegister()
    if self._restraintNotifier is not None:
      self._restraintNotifier.unRegister()
    if self._peaksNotifier is not None:
      self._peaksNotifier.unRegister()

  def _close(self):
    """
    Cleanup the notifiers when the window is closed
    """
    self._clearNotifiers()


  def _updateSettingsWidgets(self):
    """
    CCPN-INTERNAL: Update settings Widgets according with the new displayed table
    """
    displayColumnWidget = self.moduleParent._getDisplayColumnWidget()
    displayColumnWidget.updateWidgets(self)
    searchWidget = self.moduleParent._getSearchWidget()
    searchWidget.updateWidgets(self)

#
#     tipTexts = ['Restraint Id',
#                 'Atoms involved in the restraint',
#                 'Target value for the restraint',
#                 'Upper limit for the restraint',
#                 'Lower limitf or the restraint',
#                 'Error on the restraint',
#                 'Number of peaks used to derive this restraint'
#                 ]

# class RestraintTable(CcpnModule):
#   def __init__(self, mainWindow=None, name='Restraint Table', restraintLists=None, **kw):
#     CcpnModule.__init__(self, mainWindow=mainWindow, name=name)
# 
#     self.mainWindow = mainWindow
#     self.application = mainWindow.application
#     self.project = mainWindow.application.project
#     self.current = mainWindow.application.current
# 
#     project = kw.get('project')
# 
#     if not restraintLists:
#       if project is None:
#         restraintLists = []
#       else:
#         restraintLists = project.restraintLists
# 
#     self.restraintLists = restraintLists
# 
#     self._RTwidget = Widget(self.settingsWidget, setLayout=True,
#                              grid=(0,0), vAlign='top', hAlign='left')
# 
#     # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
#     # underpinning the addNotifier call do not allow for it either
# 
#     #FIXME:ED - need to check label text and function of these
#     colwidth = 140
#     self.displaysWidget = ListCompoundWidget(self._RTwidget,
#                                              grid=(0,0), vAlign='top', stretch=(0,0), hAlign='left',
#                                              vPolicy='minimal',
#                                              #minimumWidths=(colwidth, 0, 0),
#                                              fixedWidths=(colwidth, colwidth, colwidth),
#                                              orientation = 'left',
#                                              labelText='Display(s):',
#                                              tipText = 'ResidueList modules to respond to double-click',
#                                              texts=[ALL] + [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
#                                              )
#     self.displaysWidget.setFixedHeigths((None, None, 40))
# 
#     self.sequentialStripsWidget = CheckBoxCompoundWidget(
#                                              self._RTwidget,
#                                              grid=(1,0), vAlign='top', stretch=(0,0), hAlign='left',
#                                              #minimumWidths=(colwidth, 0),
#                                              fixedWidths=(colwidth, 30),
#                                              orientation = 'left',
#                                              labelText = 'Show sequential strips:',
#                                              checked = False
#                                             )
# 
#     self.markPositionsWidget = CheckBoxCompoundWidget(
#                                              self._RTwidget,
#                                              grid=(2,0), vAlign='top', stretch=(0,0), hAlign='left',
#                                              #minimumWidths=(colwidth, 0),
#                                              fixedWidths=(colwidth, 30),
#                                              orientation = 'left',
#                                              labelText = 'Mark positions:',
#                                              checked = True
#                                             )
#     self.autoClearMarksWidget = CheckBoxCompoundWidget(
#                                              self._RTwidget,
#                                              grid=(3,0), vAlign='top', stretch=(0,0), hAlign='left',
#                                              #minimumWidths=(colwidth, 0),
#                                              fixedWidths=(colwidth, 30),
#                                              orientation = 'left',
#                                              labelText = 'Auto clear marks:',
#                                              checked = True
#                                             )
# 
# 
# 
# 
#     label = Label(self, "Restraint List:")
#     widget1 = QtGui.QWidget(self)
#     widget1.setLayout(QtGui.QGridLayout())
#     widget1.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
#     self.restraintListPulldown = PulldownList(self, grid=(0, 1))
#     widget1.layout().addWidget(self.restraintListPulldown, 0, 1)
#     self.layout.addWidget(widget1, 0, 0)
# 
#     columns = [('#', '_key'),
#                ('Atoms', lambda restraint: self._getContributions(restraint)),
#                ('Target Value.', 'targetValue'),
#                ('Upper Limit', 'upperLimit'),
#                ('Lower Limit', 'lowerLimit'),
#                ('Error', 'error'),
#                ('Peaks', lambda restraint: '%3d ' % self._getRestraintPeakCount(restraint))
#                # ('Peak count', lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift))
#                ]
# 
#     tipTexts = ['Restraint Id',
#                 'Atoms involved in the restraint',
#                 'Target value for the restraint',
#                 'Upper limit for the restraint',
#                 'Lower limitf or the restraint',
#                 'Error on the restraint',
#                 'Number of peaks used to derive this restraint '
#                 ]
# 
#     self.restraintTable = GuiTableGenerator(self.mainWidget, restraintLists,
#                                                 actionCallback=self._callback, columns=columns,
#                                                 selector=self.restraintListPulldown,
#                                                 tipTexts=tipTexts, objectType='restraints')
# 
#     newLabel = Label(self, '', grid=(2, 0))
#     self.layout.addWidget(self.restraintTable, 3, 0, 1, 4)
# 
#     self.mainWidget.setContentsMargins(5, 5, 5, 5)    # ejb - put into CcpnModule?
# 
# 
#   def _getContributions(self, restraint):
#     """return number of peaks assigned to NmrAtom in Experiments and PeakLists
#     using ChemicalShiftList"""
#     if restraint.restraintContributions[0].restraintItems:
#       return ' - '.join(restraint.restraintContributions[0].restraintItems[0])
#
#
#   def _getRestraintPeakCount(self, restraint):
#     """return number of peaks assigned to NmrAtom in Experiments and PeakLists
#     using ChemicalShiftList"""
#     peaks = restraint.peaks
#     if peaks:
#       return len(peaks)
#     else:
#       return 0
#
#   def _callback(self):
#     pass
# 
