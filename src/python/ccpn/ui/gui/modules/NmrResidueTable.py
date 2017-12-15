"""
This file contains NmrResidueTableModule and NmrResidueTable classes

The NmrResidueModule allows for selection of displays, after which double-clicking a row 
navigates the displays to the relevant positions and marks the NmrAtoms of the selected 
NmrResidue.

Geerten 1-7/12/2016; 11/04/2017
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:45 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.QuickTable import QuickTable
from ccpn.ui.gui.widgets.Column import Column, ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Blank import Blank
from ccpn.ui.gui.lib.Strip import navigateToNmrResidueInDisplay
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
from PyQt4 import QtGui, QtCore
from pyqtgraph import dockarea
from pyqtgraph.dockarea import DockArea
from pyqtgraph.dockarea.DockArea import TempAreaWindow
from ccpn.util.Logging import getLogger
import numpy as np

logger = getLogger()
ALL = '<all>'


class NmrResidueTableModule(CcpnModule):
  """
  This class implements the module by wrapping a NmrResidueTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'left'

  className = 'NmrResidueTableModule'

  # we are subclassing this Module, hence some more arguments to the init
  def __init__(self, mainWindow=None, name='NmrResidue Table', nmrChain=None):
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
                                             fixedWidths=(colwidth, 2*colwidth, None),
                                             orientation = 'left',
                                             labelText='Display(s):',
                                             tipText = 'SpectrumDisplay modules to respond to double-click',
                                             texts=[ALL] + [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
                                             )
    self.displaysWidget.setFixedHeigths((None, None, 40))
    self.displaysWidget.pulldownList.set(ALL)

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
    self.nmrResidueTable = NmrResidueTable(parent=self.mainWidget
                                           , mainWindow=self.mainWindow
                                           , moduleParent=self
                                           , setLayout=True
                                           , actionCallback=self.navigateToNmrResidue
                                           , grid=(0,0))

    if nmrChain is not None:
      self.selectNmrChain(nmrChain)

    # trying to catch the minimise event
    self._oldParent = None
    self._newParent = None
    self.eventFilter = self._eventFilter
    self.installEventFilter(self)

  def selectNmrChain(self, nmrChain=None):
    """
    Manually select an NmrChain from the pullDown
    """
    self.nmrResidueTable._selectNmrChain(nmrChain)

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

  # def navigateToNmrResidue(self, nmrResidue, row=None, col=None):
  def navigateToNmrResidue(self, data):
    """
    Navigate in selected displays to nmrResidue; skip if none defined
    """
    from ccpn.core.lib.CallBack import CallBack

    nmrResidue = data[CallBack.OBJECT]

    logger.debug('nmrResidue=%s' % (nmrResidue.id))

    displays = self._getDisplays()
    if len(displays) == 0:
      logger.warning('Undefined display module(s); select in settings first')
      showWarning('startAssignment', 'Undefined display module(s);\nselect in settings first')
      return

    self.application._startCommandBlock('%s.navigateToNmrResidue(project.getByPid(%r))' %
        (self.className, nmrResidue.pid))
    try:
        # optionally clear the marks
        if self.autoClearMarksWidget.checkBox.isChecked():
            self.application.ui.mainWindow.clearMarks()

        # navigate the displays
        for display in displays:
            if len(display.strips) > 0:
                navigateToNmrResidueInDisplay(nmrResidue, display, stripIndex=0,
                                              widths=['full'] * len(display.strips[0].axisCodes),
                                              showSequentialResidues = (len(display.axisCodes) > 2) and
                                              self.sequentialStripsWidget.checkBox.isChecked(),
                                              markPositions = self.markPositionsWidget.checkBox.isChecked()
                )
    finally:
        self.application._endCommandBlock()


  def _closeModule(self):
    """
    CCPN-INTERNAL: used to close the module
    """
    self.nmrResidueTable._close()
    super(NmrResidueTableModule, self)._closeModule()

  def close(self):
    """
    Close the table from the commandline
    """
    self._closeModule()

  def paintEvent(self, ev):
    try:
      print('>>>', ev.oldState())
    except:
      pass

    finally:
      super(NmrResidueTableModule, self).paintEvent(ev)

  def _eventFilter(self, obj, event):
  # def changeEvent(self, event):
    if event.type() == QtCore.QEvent.ParentAboutToChange:
      if self.windowState() & QtCore.Qt.WindowMinimized:
        print('Dock - changeEvent: Minimised')
      # elif event.oldState() & QtCore.Qt.WindowMinimized:
      #   print('Dock - changeEvent: Normal/Maximised/FullScreen')

        # TODO:ED update table from dataFrame

        # self.nmrResidueTable._maximise()
      else:
        print ('Dock - ~~~~', self.windowState())
        self._oldParent = self.parent()
    elif event.type() == QtCore.QEvent.ParentChange:
      self._newParent = self.parent()
      print ('Dock - >>>changeEvent', self, self._oldParent, self._newParent)

      try:
        print (self.parent())
        print (self.parent().parent())
        print (self.parent().parent().parent())
        print (self.parent().parent().parent().parent())

        # self._OldChangeEvent = self.parent().parent().parent().changeEvent
        # self.parent().parent().parent().changeEvent = self._changeEvent

        if isinstance(self.parent().parent().parent(), TempAreaWindow):
          # newWin = Blank()
          # newWin.show()
          # newWin.raise_()

          tempWindow = self.parent().parent().parent()
          tempWindow.hide()

          newWin = CcpnModuleArea(mainWindow=self)
          newWin.show()
          newWin.raise_()

          newWin.addModule(self)
          # tempWindow.deleteLater()

        # if isinstance(self.parent(), dockarea):
        #   self.setParent(newWin.moduleArea)

      except:
        pass
      # if not self._newParent:
      #   newWin.layout().addWidget(self)

    return super(NmrResidueTableModule, self)._eventFilter(obj,event)

  def _changeEvent(self, event):
    if event.type() == QtCore.QEvent.WindowStateChange:
      if self.windowState() & QtCore.Qt.WindowMinimized:
        print('>>>TEMP changeEvent: Minimised')
      elif event.oldState() & QtCore.Qt.WindowMinimized:
        print('>>>TEMP changeEvent: Normal/Maximised/FullScreen')

        # TODO:ED update table from dataFrame

      else:
        print ('>>>TEMP ~~~~')
    else:
      print ('>>>TEMP changeEvent', event.type())

    self._OldChangeEvent(event)

class NmrResidueTable(QuickTable):
  """
  Class to present a NmrResidue Table and a NmrChain pulldown list, wrapped in a Widget
  """
  className = 'NmrResidueTable'
  attributeName = 'nmrChains'

  OBJECT = 'object'
  TABLE = 'table'

  @staticmethod
  def _nmrIndex(nmrRes):
    """
    CCPN-INTERNAL: Insert an index into ObjectTable
    """
    try:
      return nmrRes.nmrChain.nmrResidues.index(nmrRes)
    except:
      return None

  def __init__(self, parent=None, mainWindow=None, moduleParent=None, actionCallback=None, selectionCallback=None, nmrChain=None,  multiSelect = False,
               **kwds):
    """
    Initialise the widgets for the module.
    """
    # Derive application, project, and current from mainWindow
    self._mainWindow = mainWindow
    self._application = mainWindow.application
    self._project = mainWindow.application.project
    self._current = mainWindow.application.current
    self.moduleParent=moduleParent
    self._widget = Widget(parent=parent, **kwds)

    self.nmrChain = None
    if actionCallback is None:
      actionCallback = self.defaultActionCallback

    NmrResidueTable._project = self._project

    # create the column objects
    self.NMRcolumns = ColumnClass([
      ('#',          lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None),
      ('Index',      lambda nmrResidue: NmrResidueTable._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None),
      # ('Index',      lambda nmrResidue: nmrResidue.nmrChain.nmrResidues.index(nmrResidue), 'Index of NmrResidue in the NmrChain', None),
      # ('NmrChain',   lambda nmrResidue: nmrResidue.nmrChain.id, 'NmrChain id', None),
      ('Sequence',   lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None),
      ('Type',       lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None),
      ('NmrAtoms',   lambda nmrResidue: NmrResidueTable._getNmrAtomNames(nmrResidue), 'NmrAtoms in NmrResidue', None),
      ('Peak count', lambda nmrResidue: '%3d ' % NmrResidueTable._getNmrResiduePeakCount(nmrResidue)
                    , 'Number of peaks assigned to NmrResidue', None),
      ('Comment', lambda nmr:NmrResidueTable._getCommentText(nmr), 'Notes',
       lambda nmr, value:NmrResidueTable._setComment(nmr, value))
    ])    # [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

    selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback

    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(0,0), gridSpan=(1,1))
    self.ncWidget = NmrChainPulldown(parent=self._widget,
                                     project=self._project, default=0,  #first NmrChain in project (if present)
                                     grid=(1,0), gridSpan=(1,1), minimumWidths=(0,100),
                                     showSelectName=True,
                                     sizeAdjustPolicy=QtGui.QComboBox.AdjustToContents,
                                     callback=self._selectionPulldownCallback
                                     )
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(2,0), gridSpan=(1,1))

    # ObjectTable.__init__(self, parent=self._widget, setLayout=True,
    #                      columns=self.NMRcolumns, objects = [],
    #                      autoResize=True,  multiSelect = multiSelect,
    #                      actionCallback=actionCallback, selectionCallback=selectionCallback,
    #                      grid = (3, 0), gridSpan = (1, 6), enableDelete=True
    #                      )

    self._hiddenColumns = []
    self.dataFrameObject = None

    QuickTable.__init__(self, parent=parent
                        , mainWindow=mainWindow

                        , dataFrameObject=None    # class collating table and objects and headings

                        # , dataFrame=None
                        # , columns=self._columnNames
                        # , hiddenColumns=self._hiddenColumns
                        # , objects=None
                        , setLayout=True
                        , autoResize=True,  multiSelect=multiSelect
                        , actionCallback=actionCallback
                        , selectionCallback=selectionCallback
                        , grid = (3, 0), gridSpan = (1, 6)
                        , enableDelete=True
                        )

    # Notifier object to update the table if the nmrChain changes
    self._chainNotifier = None
    self._residueNotifier = None
    self._selectOnTableCurrentNmrResiduesNotifier = None


    # TODO: see how to handle peaks as this is too costly at present
    # Notifier object to update the table if the peaks change
    self._peakNotifier = None
    self._updateSilence = False  # flag to silence updating of the table
    self._setNotifiers()

    if nmrChain is not None:
      self._selectNmrChain(nmrChain)

  def addWidgetToTop(self, widget, col=2, colSpan=1):
    """
    Convenience to add a widget to the top of the table; col >= 2
    """
    if col < 2:
      raise RuntimeError('Col has to be >= 2')
    self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

  def addWidgetToPos(self, widget, row=0, col=2, rowSpan=1, colSpan=1):
    """
    Convenience to add a widget to the top of the table; col >= 2
    """
    if col < 2:
      raise RuntimeError('Col has to be >= 2')
    self._widget.getLayout().addWidget(widget, row, col, rowSpan, colSpan)

  def _selectNmrChain(self, nmrChain=None):
    """
    Manually select a NmrChain from the pullDown
    """
    if nmrChain is None:
      logger.warning('select: No NmrChain selected')
      raise ValueError('select: No NmrChain selected')
    else:
      if not isinstance(nmrChain, NmrChain):
        logger.warning('select: Object is not of type NmrChain')
        raise TypeError('select: Object is not of type NmrChain')
      else:
        for widgetObj in self.ncWidget.textList:
          if nmrChain.pid == widgetObj:
            self.nmrChain = nmrChain
            self.ncWidget.select(self.nmrChain.pid)

  def defaultActionCallback(self, nmrResidue, *args):

    '''default Action Callback if not defined in the parent Module 
    If current strip contains the double clicked nmrResidue will navigateToPositionInStrip '''
    from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, _getCurrentZoomRatio

    self._application.ui.mainWindow.clearMarks()
    if self._current.strip is not None:
        strip = self._current.strip
        navigateToNmrResidueInDisplay(nmrResidue, strip.spectrumDisplay, stripIndex=0,

                                      widths=['default'] * len(strip.axisCodes))

    else:
      logger.warning('Impossible to navigate to peak position. Set a current strip first')

  def displayTableForNmrChain(self, nmrChain):
    """
    Display the table for all NmrResidue's of nmrChain
    """
    self.ncWidget.select(nmrChain.pid)
    self._update(nmrChain)

  def _updateChainCallback(self, data):
    """
    Notifier callback for updating the table
    """
    thisChainList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the chainList

    if self.nmrChain in thisChainList:
      self.displayTableForNmrChain(self.nmrChain)
    else:
      self.clearTable()

      # nmrChain = data['theObject']
    logger.debug('>updateCallback>', data['notifier'], self.nmrChain, data['trigger'], data['object'], self._updateSilence)
    # if nmrChain is not None:
    #   self._update(nmrChain)

  def _updateResidueCallback(self, data):
    """
    Notifier callback for updating the table for change in nmrResidues
    """
    thisChainList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the chainList
    nmrResidue = data[Notifier.OBJECT]
    trigger = data[Notifier.TRIGGER]

    if self.nmrChain in thisChainList:
      # is the nmrResidue in the visible list
      # TODO:ED move these into the table class

      if nmrResidue.pid in self._dataFrameObject.objectList and trigger == Notifier.DELETE:

          # remove item from self._dataFrameObject

        self._dataFrameObject.removeObject(nmrResidue)

      elif nmrResidue.pid not in self._dataFrameObject.objectList and trigger == Notifier.CREATE:

        # insert item into self._dataFrameObject

        if self.nmrChain.nmrResidues and len(self.nmrChain.nmrResidues) > 1:
          self._dataFrameObject.appendObject(nmrResidue)
        else:
          self._update(self.nmrChain)

    logger.debug('>updateResidueCallback>', data['notifier'], self.nmrChain, data['trigger'], data['object'], self._updateSilence)

  def _maximise(self):
    self._update(self.nmrChain)

  def _update(self, nmrChain):
    """
    Update the table with NmrResidues of nmrChain
    """
    if not self._updateSilence:
      # # objs = self.getSelectedObjects()
      # self.setObjectsAndColumns(nmrChain.nmrResidues,self.NMRcolumns)
      # # self.setColumns(self.NMRcolumns)
      # # self.setObjects(nmrChain.nmrResidues)
      # # self._highLightObjs(objs)
      # self._selectOnTableCurrentNmrResidues(self._current.nmrResidues)
      # # self.show()

      self._dataFrameObject = self.getDataFrameFromList(table=self
                                                  , buildList=nmrChain.nmrResidues
                                                  , colDefs=self.NMRcolumns
                                                  , hiddenColumns=self._hiddenColumns)

      # new populate from Pandas
      self._project.blankNotification()
      self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
      self._project.unblankNotification()


  def setUpdateSilence(self, silence):
    """
    Silences/unsilences the update of the table until switched again
    """
    self._updateSilence = silence

  def _selectionCallback(self, selected, row, col):
    """
    Notifier Callback for selecting a row in the table
    """
    if selected is not None:
      if self.multiSelect: #In this case selected is a List!!
        if isinstance(selected, list):
          self._current.nmrResidues = selected
      else:
        self._current.nmrResidue = selected
    else:
      self._current.clearNmrResidues()
    NmrResidueTableModule._currentCallback = {'object':self.nmrChain, 'table':self}


  def _selectionPulldownCallback(self, item):
    """
    Notifier Callback for selecting NmrChain
    """
    self.nmrChain = self._project.getByPid(item)
    logger.debug('>selectionPulldownCallback>', item, type(item), self.nmrChain)
    if self.nmrChain is not None:
      self.displayTableForNmrChain(self.nmrChain)
    else:
      self.clear()

  def _selectOnTableCurrentNmrResiduesNotifierCallback(self, data):
    '''callback from a notifier to select the current NmrResidue  '''
    currentNmrResidues = data['value']
    self._selectOnTableCurrentNmrResidues(currentNmrResidues)

  def _selectOnTableCurrentNmrResidues(self, currentNmrResidues):
    ''' highlight  current NmrResidues on the opened  table '''
    if len(currentNmrResidues)>0:
      self._highLightObjs(currentNmrResidues)
    else:
      self.clearSelection()

  @staticmethod
  def _getCommentText(nmrResidue):
    """
    CCPN-INTERNAL: Get a comment from ObjectTable
    """
    try:
      if nmrResidue.comment == '' or not nmrResidue.comment:
        return ''
      else:
        return nmrResidue.comment
    except:
      return ''

  @staticmethod
  def _setComment(nmrResidue, value):
    """
    CCPN-INTERNAL: Insert a comment into ObjectTable
    """
    NmrResidueTable._project.blankNotification()
    nmrResidue.comment = value
    NmrResidueTable._project.unblankNotification()

  @staticmethod
  def _getNmrAtomNames(nmrResidue):
    """
    Returns a sorted list of NmrAtom names
    """
    return ', '.join(sorted(set([atom.name for atom in nmrResidue.nmrAtoms]),
                            key=CcpnSorting.stringSortKey))

  @staticmethod
  def _getNmrResiduePeakCount(nmrResidue):
    """
    Returns peak list count
    """
    l1 = [peak for atom in nmrResidue.nmrAtoms for peak in atom.assignedPeaks]
    return len(set(l1))

  # @staticmethod
  # def _getMeanNmrResiduePeaksShifts(nmrResidue):
  #   deltas = []
  #   peaks = nmrResidue.nmrAtoms[0].assignedPeaks
  #   for i, peak in enumerate(peaks):
  #     deltas += [
  #       (((peak.position[0] - peaks[0].position[0]) * 7) ** 2 + (peak.position[1] - peaks[0].position[1]) ** 2) ** 0.5,]
  #   if not None in deltas and deltas:
  #     return round(float(np.mean(deltas)),3)
  #   return

  def _setNotifiers(self):
    """
    Set a Notifier to call when an object is created/deleted/renamed/changed
    rename calls on name
    change calls on any other attribute
    """
    self._clearNotifiers()
    self._chainNotifier = Notifier(self._project
                                      , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                      , NmrChain.__name__
                                      , self._updateChainCallback)
    self._residueNotifier = Notifier(self._project
                                      , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE]
                                      , NmrResidue.__name__
                                      , self._updateResidueCallback
                                      , onceOnly=True)
    # very slow
    # self._peakNotifier = Notifier(self._project
    #                               , [Notifier.DELETE, Notifier.CREATE, Notifier.CHANGE]
    #                               , 'Peak'
    #                               , self._updateCallback
    #                               , onceOnly = True
    #                               )

    self._selectOnTableCurrentNmrResiduesNotifier = Notifier(self._current
                                                       , [Notifier.CURRENT]
                                                       , targetName='nmrResidues'
                                                       , callback=self._selectOnTableCurrentNmrResiduesNotifierCallback)

  def _clearNotifiers(self):
    """
    clean up the notifiers
    """
    if self._chainNotifier is not None:
      self._chainNotifier.unRegister()
    if self._residueNotifier is not None:
      self._residueNotifier.unRegister()
    if self._peakNotifier is not None:
      self._peakNotifier.unRegister()
    if self._selectOnTableCurrentNmrResiduesNotifier is not None:
      self._selectOnTableCurrentNmrResiduesNotifier.unRegister()

  def _close(self):
    """
    Cleanup the notifiers when the window is closed
    """
    self._clearNotifiers()


