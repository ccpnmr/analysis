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

from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import StructurePulldown

from ccpn.util.Logging import getLogger
logger = getLogger()
ALL = '<all>'


class RestraintTable(CcpnModule):
  def __init__(self, mainWindow=None, name='Restraint Table', restraintLists=None, **kw):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    project = kw.get('project')

    if not restraintLists:
      if project is None:
        restraintLists = []
      else:
        restraintLists = project.restraintLists

    self.restraintLists = restraintLists

    self._NTSwidget = Widget(self.settingsWidget, setLayout=True,
                             grid=(0,0), vAlign='top', hAlign='left')

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
                                             tipText = 'ResidueList modules to respond to double-click',
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




    label = Label(self, "Restraint List:")
    widget1 = QtGui.QWidget(self)
    widget1.setLayout(QtGui.QGridLayout())
    widget1.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.restraintListPulldown = PulldownList(self, grid=(0, 1))
    widget1.layout().addWidget(self.restraintListPulldown, 0, 1)
    self.layout.addWidget(widget1, 0, 0)

    columns = [('#', '_key'),
               ('Atoms', lambda restraint: self._getContributions(restraint)),
               ('Target Value.', 'targetValue'),
               ('Upper Limit', 'upperLimit'),
               ('Lower Limit', 'lowerLimit'),
               ('Error', 'error'),
               ('Peaks', lambda restraint: '%3d ' % self._getRestraintPeakCount(restraint))
               # ('Peak count', lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift))
               ]

    tipTexts = ['Restraint Id',
                'Atoms involved in the restraint',
                'Target value for the restraint',
                'Upper limit for the restraint',
                'Lower limitf or the restraint',
                'Error on the restraint',
                'Number of peaks used to derive this restraint '
                ]

    self.restraintTable = GuiTableGenerator(self.mainWidget, restraintLists,
                                                actionCallback=self._callback, columns=columns,
                                                selector=self.restraintListPulldown,
                                                tipTexts=tipTexts, objectType='restraints')

    newLabel = Label(self, '', grid=(2, 0))
    self.layout.addWidget(self.restraintTable, 3, 0, 1, 4)

    self.mainWidget.setContentsMargins(5, 5, 5, 5)    # ejb - put into CcpnModule?


  def _getContributions(self, restraint):
    """return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList"""
    if restraint.restraintContributions[0].restraintItems:
      return ' - '.join(restraint.restraintContributions[0].restraintItems[0])


  def _getRestraintPeakCount(self, restraint):
    """return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList"""
    peaks = restraint.peaks
    if peaks:
      return len(peaks)
    else:
      return 0

  def _callback(self):
    pass

