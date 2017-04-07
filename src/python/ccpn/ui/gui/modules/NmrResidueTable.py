"""This file contains NmrResidueTable class

intial version by Simon;
extensively modified by Geerten 1-7/12/2016
"""
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
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Widget import Widget


class NmrResidueTableModule(CcpnModule):
  """
  This class implements the module by wrapping a NmrResidueTable instance
  """
  def __init__(self, parent=None, project=None, callback=None, **kw):
    CcpnModule.__init__(self, name='Nmr Residue Table')
    nmrResidueTable = NmrResidueTable(parent, project, callback=None, **kw)
    self.layout.addWidget(nmrResidueTable)

class NmrResidueTable(Widget):

  def __init__(self, parent=None, project=None, callback=None, **kw):

    Widget.__init__(self, parent, **kw)

    self.project = project
    self.nmrChains = project.nmrChains
    self.callback = callback

    self.labelWidget = Label(self, "NmrChain:", grid=(0,0), gridSpan=(1,1))
    self.nmrChainPulldown = PulldownList(self, grid=(0, 1), gridSpan=(1,1))

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
                                             selector=self.nmrChainPulldown,
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


