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
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial

from PyQt5 import QtGui, QtWidgets

from ccpn.core.lib.AssignmentLib import CCP_CODES, ATOM_NAMES
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from ccpn.core.lib.CcpnSorting import stringSortKey

# from ccpn.ui.gui.base.assignmentModuleLogic import (getAllNmrAtoms, nmrAtomsForPeaks,
#                                                       peaksAreOnLine, intersectionOfAll,
#                                                       sameAxisCodes,
#                                                       getAxisCodeForPeakDimension,
#                                                       getIsotopeCodeForPeakDimension,
#                                                       getShiftlistForPeak,
#                                                       matchingNmrAtomsForDimensionOfPeaks)

class ObjectAssigner(Widget):
  def __init__(self, parent, mainWindow, dim, objects, opts, **kw):

    super().__init__(parent, **kw)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    self.dim = dim
    self.opts = opts
    self.objects = objects
    self.label = self.createEmptyWidgetLabel(dim, objects, grid=(0, 0))
    self.listWidget = self.createEmptyListWidget(dim, grid=(1, 0))
    self.objectTable = self.createEmptyNmrAtomsTable(grid=(3, 0))
    self.assignmentWidget = self.createAssignmentWidget(dim)
    self.layout().addWidget(self.assignmentWidget, 2, 0)



  def createEmptyNmrAtomsTable(self, grid):
    '''Can be used to add a new table before setting
       the content.

    '''


    columnHeadings = self.opts.get('objectTableColumnHeadings')
    columnFunctions = self.opts.get('objectTableColumnGetValues')
    callback = self.opts.get('objectTableCallBack')
    if columnFunctions is not None:
      columns = [Column(i, j) for i, j in zip(columnHeadings, columnFunctions)]
    else:
      columns = [Column(i, j) for i, j in zip(columnHeadings, columnHeadings)]
    objectTable = ObjectTable(self, columns, callback=callback, objects=[], grid=grid)

    objectTable.setFixedHeight(80)
    return objectTable

  def createEmptyListWidget(self, dim, grid):
    '''Can be used to add a new listWidget before
       setting the content.

    '''
    listWidget = ListWidget(self, callback=self.getNmrAtom,
                            rightMouseCallback=self.opts['listWidgetCallback'], grid=grid)
    listWidget.setFixedHeight(80)
    return listWidget
    # self.listWidgets.append(listWidget)

  def createEmptyWidgetLabel(self, dim, objects, grid):

    positions = [peak.position[dim] for peak in objects]
    avgPos = round(sum(positions)/len(positions), 3)
    axisCode = objects[0].peakList.spectrum.axisCodes[dim]
    text = axisCode + ' ' + str(avgPos)
    label = Label(self, text=text, grid=grid)
    # label.setStyleSheet("border: 0px solid; color: #f7ffff;")
    return label
    # self.labels.append(label)

  def createAssignmentWidget(self, dim):
    newAssignmentWidget = QtWidgets.QWidget()
    newLayout = QtWidgets.QGridLayout()
    chainLabel = Label(self, 'Chain', hAlign='c')
    seqCodeLabel = Label(self, 'Sequence', hAlign='c')
    residueTypeLabel = Label(self, 'Type', hAlign='c')
    atomTypeLabel = Label(self, 'Atom', hAlign='c')
    chainPulldown = self.createChainPulldown()
    seqCodePulldown = self.createSeqCodePulldown()
    residueTypePulldown = self.createResTypePulldown()
    atomTypePulldown = self.createAtomTypePulldown()
    newLayout.addWidget(chainLabel, 0, 0)
    newLayout.addWidget(chainPulldown, 1, 0)
    newLayout.addWidget(seqCodeLabel, 0, 1)
    newLayout.addWidget(seqCodePulldown, 1, 1)
    newLayout.addWidget(residueTypeLabel, 0, 2)
    newLayout.addWidget(residueTypePulldown, 1, 2)
    newLayout.addWidget(atomTypeLabel, 0, 3)
    newLayout.addWidget(atomTypePulldown, 1, 3)
    newAssignmentWidget.setLayout(newLayout)
    return newAssignmentWidget
    # self.assignmentWidgets.append(newAssignmentWidget)


  def createChainPulldown(self):
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    # pulldownList.lineEdit().editingFinished.connect(partial(self.addItemToPulldown, pulldownList))
    # pulldownList.editTextChanged.connect(self.addItemToPulldown)
    # pulldownList.setData([chain.pid for chain in self.project.nmrChains])
    # self.chainPulldowns.append(pulldownList)
    return pulldownList

  def createSeqCodePulldown(self):
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    # pulldownList.editTextChanged.connect(self.addItemToPulldown)
    # sequenceCodes = [nmrResidue.sequenceCode for nmrResidue in self.project.nmrResidues]
    # pulldownList.setData(sorted(sequenceCodes, key=self.natural_key))
    # self.seqCodePulldowns.append(pulldownList)
    return pulldownList


  def createResTypePulldown(self):
    pulldownList = PulldownList(self)
    # self.resTypePulldowns.append(pulldownList)
    pulldownList.setEditable(True)
    # pulldownList.editTextChanged.connect(self.addItemToPulldown)
    return pulldownList

  def createAtomTypePulldown(self):
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    # pulldownList.editTextChanged.connect(self.addItemToPulldown)
    # self.atomTypePulldowns.append(pulldownList)
    return pulldownList

  def setNmrChain(self, item):
    # NBNB FIxed. Assumes that item is a chainCode. NBNB otherwise will BERAK!.  Rasmus Dec 2015
    self.current.nmrAtom.nmrResidue.assignTo(chainCode=item)

  def setSequenceCode(self, item):
    self.current.nmrAtom.nmrResidue.sequenceCode = item

  def setResidueType(self, item):
    self.current.nmrAtom.nmrResidue.residueType = item

  def setAtomType(self, item):
    self.current.nmrAtom.name = item

  # Obsolete, replaced by CcpnSorting.stringSortKey
  # def natural_key(self, string_):
  #   import re
  #   """See http://www.codinghorror.com/blog/archives/001018.html"""
  #   return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]



  def getNmrAtom(self, dim, item):
    # print(item.text(), self.project.getById(item.text()))
    nmrAtom = self.project.getById(item.text())
    self.current.nmrAtom = nmrAtom
    chain = nmrAtom.nmrResidue.nmrChain
    sequenceCode = nmrAtom.nmrResidue.sequenceCode
    residueType = nmrAtom.nmrResidue.residueType
    atomType = nmrAtom.name
    if not nmrAtom.nmrResidue.assignedResidue:

      # TODO NBNB probably BROKEN!
      # TODO wrapper NmrResidue has no attribute assignedResidue!

      self.chainPulldowns[dim].setData([chain.id for chain in self.project.nmrChains])
      # self.chainPulldowns[dim].setIndex(self.chainPulldowns[dim].texts.index(chain.id))
      self.chainPulldowns[dim].setCallback(partial(self.setNmrChain))
      sequenceCodes = [nmrResidue.sequenceCode for nmrResidue in self.project.nmrResidues]
      self.seqCodePulldowns[dim].setData(sorted(sequenceCodes, key=stringSortKey))
      # self.seqCodePulldowns[dim].setIndex(self.seqCodePulldowns[dim].texts.index(sequenceCode))
      self.seqCodePulldowns[dim].setCallback(partial(self.setSequenceCode))
      residueTypes = [code.upper() for code in CCP_CODES] + ['']
      self.resTypePulldowns[dim].setData(residueTypes)
      # self.resTypePulldowns[dim].setIndex(self.resTypePulldowns[dim].texts.index(residueType.upper()))
      self.resTypePulldowns[dim].setCallback(partial(self.setResidueType))
      atomPrefix = self.peaks[0].peakList.spectrum.isotopeCodes[dim][-1]
      atomNames = [atomName for atomName in ATOM_NAMES if atomName[0] == atomPrefix] + [nmrAtom.name]
      self.atomTypePulldowns[dim].setData(atomNames)
      # self.atomTypePulldowns[dim].setIndex(self.atomTypePulldowns[dim].texts.index(nmrAtom.name))
      self.atomTypePulldowns[dim].setCallback(partial(self.setAtomType))

    else:
      self.chainPulldowns[dim].setData([])
      self.seqCodePulldowns[dim].setData([])
      self.resTypePulldowns[dim].setData([])
      self.atomTypePulldowns[dim].setData([])






class New(object):
  '''Small 'fake' object to get a non-nmrAtom in the objectTable.
     Maybe this should be solved differently. It works well though.

  '''

  def __init__(self):
    self.pid = 'New NMR Atom'


class NotOnLine(object):
  '''Small 'fake' object to get a message the user in the assignment
     Table that a specific dimension can not be assigned in one go
     since the frequencies of the peaks in this dimension are not on
     one line (i.e. the C frequencies of the CA and CB in a strip for
     instance).
     Maybe this should be solved differently. It works well though.

  '''

  def __init__(self):
    self.pid = 'Multiple selected peaks not on line.'

NEW = New()
NOL = NotOnLine()
