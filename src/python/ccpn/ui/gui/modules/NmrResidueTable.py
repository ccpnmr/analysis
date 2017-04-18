"""
This file contains NmrResidueTableModule and NmrResidueTable classes

intial version by Simon;
extensively modified by Geerten 1-7/12/2016; 11/04/2017
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpn.ui.gui.lib.Strip import navigateToNmrAtomsInStrip
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
#from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown

from ccpn.ui.gui.lib.Strip import navigateToNmrAtomsInStrip, navigateToNmrResidueInDisplay

from ccpn.util.Logging import getLogger
logger = getLogger()

ALL = '<all>'

class NmrResidueTableModule(CcpnModule):
  """
  This class implements the module by wrapping a NmrResidueTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsOnTop = True

  className = 'NmrResidueTableModule'

  # we are subclassing this Module, hence some more arguments to the init
  def __init__(self, parent=None, name=None, callback=None):

    name = 'NmrResidue Table' if name is None else name
    CcpnModule.__init__(self, name=name)
    # project, current, application and mainWindow are inherited from CcpnModule

    # settings
    # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
    # underpinning the addNotifier call do not allow for it either
    self.displaysWidget = ListCompoundWidget(self.settingsWidget, grid=(0,0), vAlign='top',
                                             minimumWidths=(100, 0, 0),
                                             maximumWidths=(150, 150, 150),
                                             orientation = 'left',
                                             labelText="Display module(s):",
                                             texts=[ALL] + [display.pid for display in self.mainWindow.spectrumDisplays]
    )
    #self.displaysWidget.listWidget.setHeight(40)

    self.sequentialStripsWidget = CheckBoxCompoundWidget(self.settingsWidget, grid=(1,0), vAlign='top',
                                             minimumWidths=(100, 0),
                                             maximumWidths=(100, 30),
                                             orientation = 'left',
                                             labelText = 'Show sequential strips:',
                                             checked = False
    )

    self.markPositionsWidget = CheckBoxCompoundWidget(self.settingsWidget, grid=(2,0), vAlign='top',
                                             minimumWidths=(100, 0),
                                             maximumWidths=(100, 30),
                                             orientation = 'left',
                                             labelText = 'Mark positions:',
                                             checked = True
    )
    self.autoClearMarksWidget = CheckBoxCompoundWidget(self.settingsWidget, grid=(3,0), vAlign='top',
                                             minimumWidths=(100, 0),
                                             maximumWidths=(100, 30),
                                             orientation = 'left',
                                             labelText = 'Auto clear marks:',
                                             checked = True
    )
    # main window
    if callback is None: callback = self.navigateToNmrResidue
    self.nmrResidueTable = NmrResidueTable(self.mainWidget, self.project, callback=callback)
    self.mainWidget.layout().addWidget(self.nmrResidueTable)

  def _getDisplays(self):
    "return list of displays to navigate; done so BackboneAssignment module can subclass"
    displays = []
    # check for valid displays
    gids = self.displaysWidget.getTexts()
    if len(gids) == 0: return displays
    if ALL in gids:
        displays = self.mainWindow.spectrumDisplays
    else:
        displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
    return displays

  def navigateToNmrResidue(self, nmrResidue, row=None, col=None):
    "Navigate in selected displays to nmrResidue; skip if none defined"
    logger.debug('nmrResidue=%s' % (nmrResidue.id))

    displays = self._getDisplays()
    if len(displays) == 0: return

    self.application._startCommandBlock('%s.navigateToNmrResidue(project.getByPid(%r))' %
        (self.className, nmrResidue.pid))
    try:
        # optionally clear the marks
        if self.autoClearMarksWidget.checkBox.isChecked():
            self.mainWindow.clearMarks()

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


class NmrResidueTable(Widget):

  def __init__(self, parent=None, project=None, callback=None, **kw):

    Widget.__init__(self, parent, **kw)

    self.project = project
    self.nmrChains = project.nmrChains
    self.callback = callback

    self.ncWidget = NmrChainPulldown(parent=self, project=project,
                                     grid=(0,0), gridSpan=(1,2), minimumWidths=(0,100)
                                     )

    columns = [('#', lambda nmrResidue: nmrResidue.serial),
               ('NmrChain', lambda nmrResidue: nmrResidue._parent.id),
               ('Sequence', 'sequenceCode'),
               # ('Sequence',lambda nmrResidue: '%-8s' % nmrResidue.sequenceCode),
               ('Type', 'residueType'),
               ('NmrAtoms', lambda nmrResidue: self._getNmrAtoms(nmrResidue)),
               ('Peak count', lambda nmrResidue: '%3d ' % self._getNmrResiduePeaks(nmrResidue))]

    tipTexts = ['NmrResidue serial number', 'Nmr Residue key',
                'Sequence code of NmrResidue', 'Type of NmrResidue',
                'Atoms in NmrResidue', 'Number of peaks assigned to Nmr Residue']

    self.nmrResidueTable = GuiTableGenerator(self, self.project.nmrChains,
                                             actionCallback=self.callback,
                                             columns=columns,
                                             selector=self.ncWidget.pulldownList,
                                             tipTexts=tipTexts,
                                             objectType='nmrResidues',
                                             selectionCallback=self._setNmrResidue,
                                             grid=(1,0), gridSpan=(1,6)
                                             )

  def _getNmrAtoms(self, nmrResidue):
    return ', '.join(sorted(set([atom.name for atom in nmrResidue.nmrAtoms]),
                            key=CcpnSorting.stringSortKey))

  def _getNmrResiduePeaks(self, nmrResidue):
    l1 = [peak for atom in nmrResidue.nmrAtoms for peak in atom.assignedPeaks]
    return len(set(l1))

  def _setNmrResidue(self, nmrResidue, row, col):
    self.project._appBase.current.nmrResidue = nmrResidue

  def updateTable(self):
    self.nmrResidueTable.updateTable()

  def selectNmrChain(self, nmrChain):
    if not nmrChain:
      logger.warn('No NmrChain specified')
      return

    self.ncWidget.pulldownList.select(nmrChain)
    self.updateTable()



