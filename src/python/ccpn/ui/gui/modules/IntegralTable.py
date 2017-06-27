#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:14 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt4 import QtGui
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.ui.gui.widgets.Table import ObjectTable, Column, ColumnViewSettings, ObjectTableFilter
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import IntegralListPulldown
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Integral import Integral

from ccpn.util.Logging import getLogger

logger = getLogger()
ALL = '<all>'


class IntegralTableModule(CcpnModule):
  """
  This class implements the module by wrapping a integralTable instance
  """
  includeSettingsWidget = True
  includeColumnsWidget = False
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'top'

  className = 'IntegralTableModule'

  # we are subclassing this Module, hence some more arguments to the init
  def __init__(self, mainWindow=None, name='Integral Table', integralList=None):
    """
    Initialise the Module widgets
    """
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current


    self._ITwidget = Widget(self.settingsWidget, setLayout=True,
                            grid=(0, 0), vAlign='top', hAlign='left')


    
    self.integralTable = IntegralTable(parent=self.mainWidget
                                         , setLayout=True
                                         , application=self.application
                                         , moduleParent=self
                                         , grid=(0, 0))
    # settingsWidget
    if self.includeColumnsWidget:
      self.displayColumnWidget = ColumnViewSettings(parent=self._ITwidget, table=self.integralTable, grid=(4, 0))

    self.searchWidget = ObjectTableFilter(parent=self._ITwidget, table=self.integralTable, grid=(5, 0))

    if integralList is not None:
      self.selectIntegralList(integralList)

  def selectIntegralList(self, integralList=None):
    """
    Manually select a IL from the pullDown
    """
    self.integralTable._selectIntegralList(integralList)



  def _getSearchWidget(self):
    """
    CCPN-INTERNAL: used to get searchWidget
    """
    return self.searchWidget

  def _closeModule(self):
    """
    CCPN-INTERNAL: used to close the module
    """
    self.integralTable._close()
    super(IntegralTableModule, self)._closeModule()

  def close(self):
    """
    Close the table from the commandline
    """
    self._closeModule()


class IntegralTable(ObjectTable):
  """
  Class to present a IntegralTable pulldown list, wrapped in a Widget
  """
  columnDefs = [
                ('#', lambda integral: integral.serial, '', None),
                ('Value', lambda integral: integral.value, '', None),
                ('Lower Limit', lambda integral: IntegralTable._getLowerLimit(integral), '', None),
                ('Higher Limit', lambda integral:IntegralTable._getHigherLimit(integral), '', None),
                ('ValueError', lambda integral: integral.valueError,'', None),
                ('Bias', lambda integral: integral.bias, '', None),
                ('FigureOfMerit', lambda integral: integral.figureOfMerit, '', None),
                ('Slopes', lambda integral: integral.slopes, '', None),
                ('Annotation', lambda integral: integral.annotation, '', None),
                ('Comment', lambda integral: integral.annotation, '', None),


                 ]
  className = 'IntegralTable'
  attributeName = 'integralLists'

  OBJECT = 'object'
  TABLE = 'table'

  def __init__(self, parent, application, moduleParent, integralList=None, **kwds):
    """
    Initialise the widgets for the module.
    """
    self.moduleParent = moduleParent
    self._application = application
    self._project = application.project
    self._current = application.current
    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)
    self.integralList = None

    # create the column objects
    self.ITcolumns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for
                      colName, func, tipText, editValue in self.columnDefs]

    # create the table; objects are added later via the displayTableForIntegrals method
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(0, 0), gridSpan=(1, 1))
    self.itWidget = IntegralListPulldown(parent=self._widget
                                         , project=self._project, default=0
                                         , grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100)
                                         , showSelectName=True
                                         , callback= self._selectionPulldownCallback)
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(2, 0), gridSpan=(1, 1))
    ObjectTable.__init__(self, parent=self._widget, setLayout=True,
                         columns=self.ITcolumns, objects=[],
                         autoResize=True,
                         selectionCallback=self._selectionCallback,
                         actionCallback=self._actionCallback,
                         grid=(3, 0), gridSpan=(1, 6)
                         )

    self._integralListNotifier = None
    self._integralNotifier = None


    self._updateSilence = False  # flag to silence updating of the table
    self._setNotifiers()

    if integralList is not None:
      self._selectIntegralList(integralList)


  def _selectIntegralList(self, integralList=None):
    """
    Manually select a NmrChain from the pullDown
    """
    if integralList is None:
      logger.debug('select: No IntegralList selected')
      raise ValueError('select: No IntegralList selected')
    else:
      if not isinstance(integralList, IntegralList):
        logger.debug('select: Object is not of type IntegralList')
        raise TypeError('select: Object is not of type IntegralList')
      else:
        for widgetObj in self.itWidget.textList:
          if integralList.pid == widgetObj:
            self.integralList = integralList
            self.itWidget.select(self.integralList.pid)

  def displayTableForIntegralList(self, integralList):
    """
    Display the table for all integrals"
    """
    self.itWidget.select(integralList.pid)
    self._update(integralList)

  def _updateCallback(self, data):
    """
    Notifier callback for updating the table
    """
    thisIntegralList = getattr(data[Notifier.THEOBJECT], self.attributeName)  # get the integralList
    if self.integralList in thisIntegralList:
      self.displayTableForIntegralList(self.integralList)
    else:
      self.clearTable()

  def _update(self, integralList):
    """
    Update the table
    """
    if not self._updateSilence:
      self.setColumns(self.ITcolumns)
      self.setObjects(integralList.integrals)
      self._updateSettingsWidgets()
      self.show()

  def setUpdateSilence(self, silence):
    """
    Silences/unsilences the update of the table until switched again
    """
    self._updateSilence = silence

  def _selectionCallback(self, integral,*kw):
    """
    Notifier Callback for selecting a row in the table
    """
    self._current.integral = integral


  def _actionCallback(self, *kw):
    """
    Notifier DoubleClick action on item in table
    """
    logger.debug(str(NotImplemented))

  def _selectionPulldownCallback(self, item):
    """
    Notifier Callback for selecting integral from the pull down menu
    """
    if item is not None:
      self.integralList = self._project.getByPid(item)
      if self.integralList is not None:
        self.displayTableForIntegralList(self.integralList)
      else:
        self.clearTable()


  @staticmethod
  def _getHigherLimit(integral):
    """
    Returns HigherLimit
    """
    if integral is not None:
      if len(integral.limits)>0:
        limits = integral.limits[0]
        if limits is not None:
          return float(max(limits))

  @staticmethod
  def _getLowerLimit(integral):
    """
    Returns Lower Limit
    """
    if integral is not None:
      if len(integral.limits) > 0:
        limits = integral.limits[0]
        if limits:
          return float(min(limits))


  @staticmethod
  def _getCommentText(integral):
    """
    CCPN-INTERNAL: Get a comment from ObjectTable
    """
    try:
      if integral.comment == '' or not integral.comment:
        return ''
      else:
        return integral.comment
    except:
      return ''

  @staticmethod
  def _setComment(integral, value):
    """
    CCPN-INTERNAL: Insert a comment into ObjectTable
    """
    integral.comment = value

  def _setNotifiers(self):
    """
    Set a Notifier to call when an object is created/deleted/renamed/changed
    rename calls on name
    change calls on any other attribute
    """
    self._clearNotifiers()
    self._integralListNotifier = Notifier(self._project
                                           , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                           , IntegralList.__name__
                                           , self._updateCallback)
    self._integralNotifier = Notifier(self._project
                                       , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE]
                                       , Integral.__name__
                                       , self._updateCallback)

  def _clearNotifiers(self):
    """
    clean up the notifiers
    """
    if self._integralListNotifier is not None:
      self._integralListNotifier.unRegister()
    if self._integralNotifier is not None:
      self._integralNotifier.unRegister()

  def _close(self):
    """
    Cleanup the notifiers when the window is closed
    """
    self._clearNotifiers()

  def _updateSettingsWidgets(self):
    """
    CCPN-INTERNAL: Update settings Widgets according with the new displayed table
    """
    searchWidget = self.moduleParent._getSearchWidget()
    searchWidget.updateWidgets(self)


