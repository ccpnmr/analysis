"""This file contains ChemicalShiftTable class

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

from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList


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


class ChemicalShiftTable(CcpnModule):
  """Alternative proposal to the ChemicalShiftTable
  """

  def __init__(self, parent=None, chemicalShiftLists=None, name='Chemical Shift Table', **kw):

    CcpnModule.__init__(self, name=name)

    if not chemicalShiftLists:
      chemicalShiftLists = []
    self.chemicalShiftLists = chemicalShiftLists

    self.labelWidget = Label(self.mainWidget, "ChemicalShiftList:", grid=(0,0), gridSpan=(1,1))
    self.chemicalShiftListPulldown = PulldownList(self.mainWidget, grid=(0,1), gridSpan=(1,1))

    columns = [('#', lambda chemicalShift: chemicalShift.nmrAtom.serial),
               ('NmrResidue', lambda chemicalShift: chemicalShift._key.rsplit('.', 1)[0]),
               ('Name', lambda chemicalShift: chemicalShift._key.rsplit('.', 1)[-1]),
               ('Shift', lambda chemicalShift: '%8.3f' % chemicalShift.value),
               ('Std. Dev.', lambda chemicalShift: ('%6.3f' % chemicalShift.valueError
                                                    if chemicalShift.valueError else '   0   ')),
               ('Shift list peaks',
                lambda chemicalShift: '%3d ' % self._getShiftPeakCount(chemicalShift)),
               ('All peaks',
                lambda chemicalShift: '%3d ' % len(set(x for x in
                                                       chemicalShift.nmrAtom.assignedPeaks))
                )
               ]

    tipTexts = ['NmrAtom serial number',
                'NmrResidue Id',
                'NmrAtom name',
                'Value of chemical shift, in selected ChemicalShiftList',
                'Standard deviation of chemical shift, in selected ChemicalShiftList',
                'Number of peaks assigned to this NmrAtom in PeakLists associated with this '
                'ChemicalShiftList',
                'Number of peaks assigned to this NmrAtom across all PeakLists']

    self.chemicalShiftTable = GuiTableGenerator(self.mainWidget, chemicalShiftLists,
                                                selectionCallback=self._callback,
                                                actionCallback=None,
                                                columns=columns,
                                                selector=self.chemicalShiftListPulldown,
                                                tipTexts=tipTexts,
                                                objectType='chemicalShifts',
                                                grid=(1,0), gridSpan=(1,6)
                                                )

  def _getShiftPeakCount(self, chemicalShift):
    """return number of peaks assigned to NmrAtom in Experiments and PeakLists
    using ChemicalShiftList"""
    chemicalShiftList = chemicalShift.chemicalShiftList
    peaks = chemicalShift.nmrAtom.assignedPeaks
    return (len(set(x for x in peaks
                    if x.peakList.chemicalShiftList is chemicalShiftList)))

  def _callback(self, obj, row, col):

    if obj: # should presumably always be the case
      chemicalShift = obj
      chemicalShift.project._appBase.current.nmrAtom = chemicalShift.nmrAtom
      chemicalShift.project._appBase.current.nmrResidue = chemicalShift.nmrAtom.nmrResidue

