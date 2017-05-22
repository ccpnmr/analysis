"""This file contains ChemicalShiftTable class

intial version by Simon;
extensively modified by Geerten 1-7/12/2016
tertiary version by Ejb 9/5/17
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
__dateModified__ = "$dateModified: 2017-04-07 11:40:38 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import ChemicalShiftListPulldown
from ccpn.ui.gui.widgets.Table import ObjectTable, Column, ColumnViewSettings,  ObjectTableFilter
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from PyQt4 import QtGui

from ccpn.util.Logging import getLogger
ALL = '<all>'

class ChemicalShiftTableModule(CcpnModule):
  """
  This class implements the module by wrapping a NmrResidueTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'top'

  className = 'ChemicalShiftTableModule'

  # we are subclassing this Module, hence some more arguments to the init
  def __init__(self, mainWindow, chemicalShiftLists=None, name='Chemical Shift Table'):
    """
    Initialise the Module widgets
    """
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current
    # settings

    # Put all of the NmrTable settings in a widget, as there will be more added in the PickAndAssign, and
    # backBoneAssignment modules
    self._CSTwidget = Widget(self.settingsWidget, setLayout=True,
                             grid=(0,0), vAlign='top', hAlign='left')

    # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
    # underpinning the addNotifier call do not allow for it either
    colwidth = 140
    self.displaysWidget = ListCompoundWidget(self._CSTwidget,
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
                                             self._CSTwidget,
                                             grid=(1,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Show sequential strips:',
                                             checked = False
                                            )

    self.markPositionsWidget = CheckBoxCompoundWidget(
                                             self._CSTwidget,
                                             grid=(2,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Mark positions:',
                                             checked = True
                                            )
    self.autoClearMarksWidget = CheckBoxCompoundWidget(
                                             self._CSTwidget,
                                             grid=(3,0), vAlign='top', stretch=(0,0), hAlign='left',
                                             #minimumWidths=(colwidth, 0),
                                             fixedWidths=(colwidth, 30),
                                             orientation = 'left',
                                             labelText = 'Auto clear marks:',
                                             checked = True
                                            )

    # main window
    self.chemicalShiftTable = ChemicalShiftTable(parent=self.mainWidget, setLayout=True,
                                               application=self.application,
                                               moduleParent=self,
                                               grid=(0,0))
    # settingsWidget
    self.displayColumnWidget = ColumnViewSettings(parent=self._CSTwidget, table=self.chemicalShiftTable, grid=(4, 0))
    self.searchWidget = ObjectTableFilter(parent=self._CSTwidget, table=self.chemicalShiftTable, grid=(5, 0))

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
    self.chemicalShiftTable._close()
    super(ChemicalShiftTableModule, self)._closeModule()


class ChemicalShiftTable(ObjectTable):
  """
  Class to present a NmrResidue Table and a NmrChain pulldown list, wrapped in a Widget
  """
  columnDefs = [('#', lambda cs:cs.nmrAtom.serial, 'NmrAtom serial number', None),
             ('NmrResidue', lambda cs:cs._key.rsplit('.', 1)[0], 'NmrResidue Id', None),
             ('Name', lambda cs:cs._key.rsplit('.', 1)[-1], 'NmrAtom name', None),
             ('Shift', lambda cs:'%8.3f' % ChemicalShiftTable._stLamFloat(cs, 'value'), 'Value of chemical shift, in selected ChemicalShiftList', None),
             ('Std. Dev.', lambda cs:'%6.3f' % ChemicalShiftTable._stLamFloat(cs, 'valueError'), 'Standard deviation of chemical shift, in selected ChemicalShiftList', None),
             ('Shift list peaks',
              lambda cs:'%3d ' % ChemicalShiftTable._getShiftPeakCount(cs), 'Number of peaks assigned to this NmrAtom in PeakLists associated with this'
                                                                                    'ChemicalShiftList', None),
             ('All peaks',
              lambda cs:'%3d ' % len(set(x for x in cs.nmrAtom.assignedPeaks)), 'Number of peaks assigned to this NmrAtom across all PeakLists', None),
              ('Comment', lambda cs:ChemicalShiftTable._getCommentText(cs), 'Notes',
                 lambda cs, value:ChemicalShiftTable._setComment(cs, value))
             ]

  className = 'ChemicalShiftListTable'
  attributeName = 'chemicalShiftLists'

  def __init__(self, parent, application, moduleParent, **kwds):
    """
    Initialise the widgets for the module.
    """
    self.moduleParent = moduleParent
    self._application = application
    self._project = application.project
    self._current = application.current
    self._widget = Widget(parent=parent, **kwds)
    self.chemicalShiftList = None

    # create the column objects
    columns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

    # create the table; objects are added later via the displayTableForNmrChain method
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(0, 0), gridSpan=(1, 1))
    self.ncWidget = ChemicalShiftListPulldown(parent=self._widget,
                                     project=self._project, default=0,
                                     # first NmrChain in project (if present)
                                     grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                     showSelectName=True,
                                     callback=self._selectionPulldownCallback
                                     )
    self.spacer = Spacer(self._widget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(2, 0), gridSpan=(1, 1))
    ObjectTable.__init__(self, parent=self._widget, setLayout=True,
                         columns=columns, objects=[],
                         autoResize=True,
                         actionCallback=self._actionCallback,
                         selectionCallback=self._selectionCallback,
                         grid=(3, 0), gridSpan=(1, 6)
                         )
    # Notifier object to update the table if the nmrChain changes
    self._chemicalShiftNotifier = Notifier(self._project
                                   , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                   , ChemicalShiftList.__name__
                                   , self._updateCallback)
    # TODO: see how to handle peaks as this is too costly at present
    # Notifier object to update the table if the peaks change
    self._peaksNotifier = None
    self._updateSilence = False  # flag to silence updating of the table

  def addWidgetToTop(self, widget, col=2, colSpan=1):
    """
    Convenience to add a widget to the top of the table; col >= 2
    """
    if col < 2:
      raise RuntimeError('Col has to be >= 2')
    self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)

  def displayTableForChemicalShift(self, chemicalShiftList):
    """
    Display the table for all chemicalShift
    """
    self.ncWidget.select(chemicalShiftList.pid)
    self._update(chemicalShiftList)

  def _updateCallback(self, data):
    """
    Notifier callback for updating the table
    """
    thisChemicalShiftList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the restraintList
    if self.chemicalShiftList in thisChemicalShiftList:
      self.displayTableForChemicalShift(self.chemicalShiftList)
    else:
      self.clearTable()

  def _update(self, chemicalShiftList):
    """
    Update the table
    """
    if not self._updateSilence:
      self.clearTable()
      self._silenceCallback = True
      self.setObjects(chemicalShiftList.chemicalShifts)
      self._updateSettingsWidgets()
      self._silenceCallback = False
      self.show()

  def setUpdateSilence(self, silence):
    """
    Silences/unsilences the update of the table until switched again
    """
    self._updateSilence = silence

  def _actionCallback(self, chemicalShift, row, column):
    """
    Notifier DoubleClick action on item in table
    """
    print('ChemicalShift>>>', chemicalShift, row, column)

  def _selectionCallback(self, obj, row, col):
    """
    Notifier Callback for selecting a row in the table
    """
    self._current.chemicalShift = obj

    #FIXME:ED - this is copied form the original version below
    if obj: # should presumably always be the case
      chemicalShift = obj
      self._current.nmrAtom = chemicalShift.nmrAtom
      self._current.nmrResidue = chemicalShift.nmrAtom.nmrResidue

  def _selectionPulldownCallback(self, item):
    """
    Notifier Callback for selecting NmrChain from the pull down menu
    """
    self.chemicalShiftList = self._project.getByPid(item)
    # print('>selectionPulldownCallback>', item, type(item), nmrChain)
    if self.chemicalShiftList is not None:
      self.displayTableForChemicalShift(self.chemicalShiftList)
    else:
      self.clearTable()

  def _close(self):
    """
    Cleanup the notifiers when the window is closed
    """
    if self._chemicalShiftNotifier is not None:
      self._chemicalShiftNotifier.unRegister()
    if self._peaksNotifier is not None:
      self._peaksNotifier.unRegister()

  def _updateSettingsWidgets(self):
    """
    CCPN-INTERNAL: Update settings Widgets according with the new displayed table
    """
    displayColumnWidget = self.moduleParent._getDisplayColumnWidget()
    displayColumnWidget.updateWidgets(self)
    searchWidget = self.moduleParent._getSearchWidget()
    searchWidget.updateWidgets(self)

  @staticmethod
  def _getShiftPeakCount(chemicalShift):
    """
    CCPN-INTERNAL: Return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList
    """
    chemicalShiftList = chemicalShift.chemicalShiftList
    peaks = chemicalShift.nmrAtom.assignedPeaks
    return (len(set(x for x in peaks
                    if x.peakList.chemicalShiftList is chemicalShiftList)))

  @staticmethod
  def _getCommentText(chemicalShift):
    """
    CCPN-INTERNAL: Get a comment from ObjectTable
    """
    if chemicalShift.comment == '' or not chemicalShift.comment:
      return ' '
    else:
      return chemicalShift.comment

  @staticmethod
  def _setComment(chemicalShift, value):
    """
    CCPN-INTERNAL: Insert a comment into ObjectTable
    """
    chemicalShift.comment = value

  @staticmethod
  def _stLamFloat(row, name):
    """
    CCPN-INTERNAL: used to display Table
    """
    try:
      return float(getattr(row, name))
    except:
      return None

# class ChemicalShiftTable(CcpnModule):
#   def __init__(self, parent=None, chemicalShiftLists=None, name='Chemical Shift Table', **kw):
#
#     if not chemicalShiftLists:
#       chemicalShiftLists = []
#
#     CcpnModule.__init__(self, name=name)
#
#     self.chemicalShiftLists = chemicalShiftLists
#
#     self.label = Label(self, "ChemicalShiftList:", grid=(0,0), gridSpan=(1,1))
#     self.chemicalShiftListPulldown = PulldownList(self, grid=(0, 1), gridSpan=(1,2))
#
#     columns = [('#', '_key'),
#                ('Shift', lambda chemicalShift: '%8.3f' % chemicalShift.value),
#                ('Std. Dev.', lambda chemicalShift: ('%6.3f' % chemicalShift.valueError
#                                                     if chemicalShift.valueError else '   0   ')),
#                ('Peak count', lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift))
#                ]
#
#     tipTexts = ['Atom Pid',
#                 'Value of chemical shift',
#                 'Standard deviation of chemical shift',
#                 'Number of peaks associated with this ChemicalShiftList that are assigned to this '
#                 'NmrAtom']
#
#     self.chemicalShiftTable = GuiTableGenerator(self, chemicalShiftLists,
#                                                 actionCallback=self._callback, columns=columns,
#                                                 selector=self.chemicalShiftListPulldown,
#                                                 tipTexts=tipTexts, objectType='chemicalShifts',
#                                                 grid=(1,0), gridSpan=(1,6)
#                                                 )
#
#   def _getShiftPeakCount(self, chemicalShift):
#     """return number of peaks assigned to NmrAtom in Experiments and PeakLists
#     using ChemicalShiftList"""
#     chemicalShiftList = chemicalShift.chemicalShiftList
#     peaks = chemicalShift.nmrAtom.assignedPeaks
#     return (len(set(x for x in peaks
#                     if x.peakList.chemicalShiftList is chemicalShiftList)))
#
#   def _callback(self, obj, row, col):
#     pass


# class oldChemicalShiftTable(CcpnModule):
#   """Alternative proposal to the ChemicalShiftTable
#   """
#
#   def __init__(self, mainWindow=None, chemicalShiftLists=None, name='Chemical Shift Table', **kw):
#     CcpnModule.__init__(self, mainWindow=mainWindow, name=name)
#
#     self.mainWindow = mainWindow
#     self.application = mainWindow.application
#     self.project = mainWindow.application.project
#     self.current = mainWindow.application.current
#
#     if not chemicalShiftLists:
#       chemicalShiftLists = []
#     self.chemicalShiftLists = chemicalShiftLists
#
#     self.labelWidget = Label(self.mainWidget, "ChemicalShiftList:", grid=(0,0), gridSpan=(1,1))
#     self.chemicalShiftListPulldown = PulldownList(self.mainWidget, grid=(0,1), gridSpan=(1,1))
#
#     columns = [('#', lambda chemicalShift: chemicalShift.nmrAtom.serial),
#                ('NmrResidue', lambda chemicalShift: chemicalShift._key.rsplit('.', 1)[0]),
#                ('Name', lambda chemicalShift: chemicalShift._key.rsplit('.', 1)[-1]),
#                ('Shift', lambda chemicalShift: '%8.3f' % chemicalShift.value),
#                ('Std. Dev.', lambda chemicalShift: ('%6.3f' % chemicalShift.valueError
#                                                     if chemicalShift.valueError else '   0   ')),
#                ('Shift list peaks',
#                 lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift)),
#                ('All peaks',
#                 lambda chemicalShift: '%3d ' % len(set(x for x in
#                                                        chemicalShift.nmrAtom.assignedPeaks))
#                 )
#                ]
#
#     tipTexts = ['NmrAtom serial number',
#                 'NmrResidue Id',
#                 'NmrAtom name',
#                 'Value of chemical shift, in selected ChemicalShiftList',
#                 'Standard deviation of chemical shift, in selected ChemicalShiftList',
#                 'Number of peaks assigned to this NmrAtom in PeakLists associated with this '
#                 'ChemicalShiftList',
#                 'Number of peaks assigned to this NmrAtom across all PeakLists']
#
#     self.chemicalShiftTable = GuiTableGenerator(self.mainWidget, chemicalShiftLists,
#                                                 selectionCallback=self._callback,
#                                                 actionCallback=None,
#                                                 columns=columns,
#                                                 selector=self.chemicalShiftListPulldown,
#                                                 tipTexts=tipTexts,
#                                                 objectType='chemicalShifts',
#                                                 grid=(1,0), gridSpan=(1,6)
#                                                 )
#
#   def _getShiftPeakCount(self, chemicalShift):
#     """return number of peaks assigned to NmrAtom in Experiments and PeakLists
#     using ChemicalShiftList"""
#     chemicalShiftList = chemicalShift.chemicalShiftList
#     peaks = chemicalShift.nmrAtom.assignedPeaks
#     return (len(set(x for x in peaks
#                     if x.peakList.chemicalShiftList is chemicalShiftList)))
#
#   def _callback(self, obj, row, col):
#
#     if obj: # should presumably always be the case
#       chemicalShift = obj
#       chemicalShift.project._appBase.current.nmrAtom = chemicalShift.nmrAtom
#       chemicalShift.project._appBase.current.nmrResidue = chemicalShift.nmrAtom.nmrResidue

