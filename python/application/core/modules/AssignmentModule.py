#from imp import reload

from PyQt4 import QtGui, QtCore

from ccpn.lib.Assignment import CCP_CODES, ATOM_NAMES
from ccpncore.lib.Constants import  defaultNmrChainCode

from ccpn import NmrAtom, Peak, Project

from application.core.widgets.Base import Base
from application.core.widgets.Button import Button
from application.core.widgets.Dock import CcpnDock
from application.core.widgets.Label import Label
from application.core.widgets.ListWidget import ListWidget
from application.core.widgets.PulldownList import PulldownList
from application.core.widgets.Table import ObjectTable, Column
from application.core.widgets.CheckBox import CheckBox

from ccpn.lib import CcpnSorting
import typing

from application.core.base.assignmentModuleLogic import (nmrAtomsForPeaks,
                                                      peaksAreOnLine,
                                                      sameAxisCodes)

from functools import partial

class AssignmentModule(CcpnDock, Base):
  '''Module that can be used to assign nmrAtoms
     to peaks.

  '''

  def __init__(self, parent=None, project:Project=None, peaks:typing.List[Peak]=None, **kw):

    CcpnDock.__init__(self, name="Peak Assigner")
    Base.__init__(self, **kw)
    self.project = project
    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    self.selectionLayout = QtGui.QGridLayout()
    self.filterLayout = QtGui.QGridLayout()
    self.widget1.setLayout(QtGui.QGridLayout())
    self.advancedLayout = QtGui.QGridLayout()
    self.widget1.layout().addLayout(self.selectionLayout, 1, 0)
    self.widget1.layout().addLayout(self.filterLayout, 0, 0)
    self.selectionLayout.setRowMinimumHeight(0, 0)
    self.selectionLayout.setRowStretch(0, 0)
    self.selectionLayout.setRowStretch(1, 1)
    self.current = self.project._appBase.current
    self.listWidgets = []
    self.objectTables = []
    self.labels = []
    self.assignmentWidgets = []
    self.chainPulldowns = []
    self.seqCodePulldowns = []
    self.resTypePulldowns = []
    self.atomTypePulldowns = []
    self.colourScheme = self.project._appBase.preferences.general.colourScheme

    self.doubleToleranceCheckbox = CheckBox(self.widget1, checked=False)
    self.doubleToleranceCheckbox.stateChanged.connect(self.updateInterface)
    doubleToleranceCheckboxLabel = Label(self.widget1, text="Double Tolerances ")
    self.filterLayout.addWidget(self.doubleToleranceCheckbox, 0, 1)
    self.filterLayout.addWidget(doubleToleranceCheckboxLabel, 0, 0)

    self.intraCheckbox = CheckBox(self.widget1, checked=False)
    self.intraCheckbox.stateChanged.connect(self.updateInterface)
    intraCheckboxLabel = Label(self.widget1, text="Only Intra-residual ")
    self.filterLayout.addWidget(self.intraCheckbox, 0, 3)
    self.filterLayout.addWidget(intraCheckboxLabel, 0, 2)

    self.multiCheckbox = CheckBox(self.widget1, checked=True)
    self.multiCheckbox.stateChanged.connect(self.updateInterface)
    multiCheckboxLabel = Label(self.widget1, text="Allow multiple peaks ")
    self.filterLayout.addWidget(self.multiCheckbox, 0, 5)
    self.filterLayout.addWidget(multiCheckboxLabel, 0, 4)
    self.expCheckBox = CheckBox(self.widget1, checked=True)
    expCheckBoxLabel = Label(self.widget1, "Filter By Experiment")
    self.filterLayout.addWidget(expCheckBoxLabel, 0, 6)
    self.filterLayout.addWidget(self.expCheckBox, 0, 7)

    self.current.registerNotify(self.updateInterface, 'peaks')
    self.updateInterface()



  # functions to create empty widgets

  def createEmptyNmrAtomsTable(self, dim:int):
    '''Create an empty table for the specified peak dimension to contain possible Nmr Atoms that
    can be assigned to that peak dimension.

    '''

    columns = [Column('NMR Atom', lambda nmrAtom: str(nmrAtom.id)),
               Column('Shift', lambda nmrAtom: self.getShift(nmrAtom)),
               Column('Delta', lambda nmrAtom: self.getDeltaShift(nmrAtom, dim))]

    objectTable = ObjectTable(self, columns,
                              actionCallback=partial(self.assignNmrAtomToDim, dim),
                              objects=[])

    self.objectTables.append(objectTable)

  def createEmptyListWidget(self, dim:int):
    """
    Creates an empty ListWidget to contain the dimensionNmrAtoms assigned to a peak dimension.
    """
    listWidget = ListWidget(self, callback=partial(self.updateAssigmentWidget, dim),
                            rightMouseCallback=self.updateNmrAtomsFromListWidgets)

    self.listWidgets.append(listWidget)

  def createEmptyWidgetLabel(self, dim:int):
    """
    Creates an empty Label to contain peak dimension position.
    """
    positions = [peak.position[dim] for peak in self.current.peaks]
    avgPos = round(sum(positions)/len(positions), 3)
    axisCode = self.current.peak.peakList.spectrum.axisCodes[dim]
    text = axisCode + ' ' + str(avgPos)
    label = Label(self, text=text)
    if self.colourScheme == 'dark':
      label.setStyleSheet("border: 0px solid; color: #f7ffff;")
    elif self.colourScheme == 'light':
      label.setStyleSheet("border: 0px solid; color: #555d85;")
    self.labels.append(label)


  def createAssignmentWidget(self, dim:int):
    """
    Creates an assignment widget consisting of three PulldownLists.
    """
    newAssignmentWidget = QtGui.QWidget()
    newLayout = QtGui.QGridLayout()
    chainLabel = Label(self, 'Chain', hAlign='c')
    seqCodeLabel = Label(self, 'Sequence', hAlign='c')
    atomTypeLabel = Label(self, 'Atom', hAlign='c')
    chainPulldown = self.createChainPulldown(dim)
    seqCodePulldown = self.createSeqCodePulldown(dim)
    atomTypePulldown = self.createAtomTypePulldown(dim)
    applyButton = Button(self, 'New', callback=partial(self.createNewNmrAtom, dim))
    self.reassignButton = Button(self, 'Assign', callback=partial(self.setAssignment, dim))
    newLayout.addWidget(chainLabel, 0, 0)
    newLayout.addWidget(chainPulldown, 0, 1)
    newLayout.addWidget(seqCodeLabel, 1, 0)
    newLayout.addWidget(seqCodePulldown, 1, 1)
    newLayout.addWidget(atomTypeLabel, 2, 0)
    newLayout.addWidget(atomTypePulldown, 2, 1)
    newLayout.addWidget(applyButton, 3, 0, 1, 1)
    newLayout.addWidget(self.reassignButton, 3, 1, 1, 1)
    newAssignmentWidget.setLayout(newLayout)
    self.assignmentWidgets.append(newAssignmentWidget)


  def setAssignment(self, dim:int):
    """
    Assigns dimensionNmrAtoms to peak dimension when called using Assign Button in assignment widget.
    """

    nmrChain = self.project.fetchNmrChain(self.chainPulldowns[dim].currentText())
    nmrResidue = nmrChain.fetchNmrResidue(self.seqCodePulldowns[dim].currentText())
    nmrAtom = nmrResidue.fetchNmrAtom(self.atomTypePulldowns[dim].currentText())
    for peak in self.current.peaks:
      dimNmrAtoms = peak.dimensionNmrAtoms[dim]
      currentItem = self.listWidgets[dim].currentItem()
      if not currentItem:
        self.listWidgets[dim].addItem(nmrAtom.pid)
        currentItem = self.listWidgets[dim].item(self.listWidgets[dim].count()-1)
      currentObject = self.project.getByPid(currentItem.text())
      toAssign = dimNmrAtoms.index(currentObject)

      dimNmrAtoms[toAssign] = nmrAtom
      allAtoms = list(peak.dimensionNmrAtoms)
      allAtoms[dim] = dimNmrAtoms
      peak.dimensionNmrAtoms = allAtoms

    self.updateInterface()


  def createChainPulldown(self, dim:int) -> PulldownList:
    """
    Creates a PulldownList for selection of NmrChains.
    """
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    pulldownList.lineEdit().editingFinished.connect(partial(self.addItemToPulldown, pulldownList))
    self.chainPulldowns.append(pulldownList)
    return pulldownList

  def createSeqCodePulldown(self, dim:int) -> PulldownList:
    """
    Creates a PulldownList for selection of NmrResidue Sequence codes.
    """
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    self.seqCodePulldowns.append(pulldownList)
    return pulldownList


  def createAtomTypePulldown(self, dim:int) -> PulldownList:
    """
    Creates a PulldownList for selection of atom types.
    """
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    self.atomTypePulldowns.append(pulldownList)
    return pulldownList


  def createEnoughTablesAndLists(self):
    '''Makes sure there are enough tables for the amount
       of dimensions of the currently selected peak(s).
       This method only runs when all peaks have the same
       amount of dimensions as is guaranteed by running
       peaksAreCompatible.py

    '''

    Ndimensions = len(self.current.peak.position)


    # Create extra tables if needed.
    for dim in range(len(self.objectTables), Ndimensions):
      self.createEmptyNmrAtomsTable(dim)

    for dim in range(len(self.listWidgets), Ndimensions):
      self.createEmptyListWidget(dim)

    for dim in range(len(self.labels), Ndimensions):
      self.createEmptyWidgetLabel(dim)

    for dim in range(len(self.assignmentWidgets), Ndimensions):
      self.createAssignmentWidget(dim)

    self.widgetItems = list(zip(self.labels[:Ndimensions], self.listWidgets[:Ndimensions],
                    self.assignmentWidgets[:Ndimensions], self.objectTables[:Ndimensions]))

    for pair in self.widgetItems:
      widget = QtGui.QWidget(self)
      layout = QtGui.QGridLayout()
      layout.setSpacing(10)
      layout.setMargin(5)
      layout.setContentsMargins(4, 4, 4, 4)
      if self.colourScheme == 'dark':
        widget.setStyleSheet("border: 1px solid #bec4f3")
      elif self.colourScheme == 'light':
        widget.setStyleSheet("border: 1px solid #bd8413")
      layout.addWidget(pair[0], 0, 0, 1, 1)
      layout.addWidget(pair[1], 1, 0, 2, 1)
      layout.addWidget(pair[2], 1, 1, 2, 1)
      layout.addWidget(pair[3], 3, 0, 1, 2)
      pair[2].setStyleSheet("PulldownList {border: 0px solid;}")
      pair[2].setStyleSheet("border: 0px solid")
      pair[3].setStyleSheet("color: black; border: 0px solid;")
      widget.setLayout(layout)
      self.widgets.append(widget)
      self.selectionLayout.addWidget(widget, 0, self.widgetItems.index(pair))
    #
    self.updateLayout(self.selectionLayout, Ndimensions)

  # Update functions


  def updateInterface(self, peaks:typing.List[Peak]=None):
    """Updates the whole module, including recalculation
       of which nmrAtoms fit to the peaks.

    """
    self.emptyAllTablesAndLists()
    if not self.current.peaks or not self.peaksAreCompatible():
      return
    self.createEnoughTablesAndLists()
    self.updateTables()
    self.updateAssignedNmrAtomsListwidgets()
    self.updateWidgetLabels()



  def updateWidgetLabels(self):

    Ndimensions = len(self.current.peak.position)

    for dim, label in zip(range(Ndimensions), self.labels):
      positions = [peak.position[dim] for peak in self.current.peaks]
      avgPos = round(sum(positions)/len(positions), 3)
      axisCode = self.current.peak.peakList.spectrum.axisCodes[dim]
      text = axisCode + ' ' + str(avgPos)
      label.setText(text)
      if self.colourScheme == 'dark':
        label.setStyleSheet("border: 0px solid; color: #f7ffff;")
      elif self.colourScheme == 'light':
        label.setStyleSheet("border: 0px solid; color: #555d85;")


  def updateTables(self):
    '''Updates the tables indicating the different assignment
       possibilities of the peak dimensions.

    '''

    peaks = self.current.peaks
    doubleTolerance = self.doubleToleranceCheckbox.isChecked()
    intraResidual = self.intraCheckbox.isChecked()
    nmrAtomsForTables = nmrAtomsForPeaks(peaks, self.project.nmrAtoms,
                                             doubleTolerance=doubleTolerance,
                                             intraResidual=intraResidual)
    Ndimensions = len(nmrAtomsForTables)
    for dim, objectTable, nmrAtoms in zip(range(Ndimensions),
                                          self.objectTables,
                                          nmrAtomsForTables):
      if peaksAreOnLine(peaks, dim):
        objectTable.show()
      else:
        objectTable.setObjects([NOL])



  def updateAssignedNmrAtomsListwidgets(self):
    '''Update the listWidget showing which nmrAtoms
       are assigned to which peak dimensions. If multiple
       peaks are selected, only the assignment that they
       have in common are shown. Maybe this should be all
       assignments. You can see that at the peak annotation
       though.

    '''

    Ndimensions = len(self.current.peak.position)

    if self.current.peaks:
      for dim, listWidget in zip(range(Ndimensions), self.listWidgets):

        ll = [set(peak.dimensionNmrAtoms[dim]) for peak in self.current.peaks]
        self.nmrAtoms = list(sorted(set.intersection(*ll)))
        listWidget.addItems([str(a.pid) for a in self.nmrAtoms])

  def updateNmrAtomsFromListWidgets(self):

    assignmentArray = [0] * len(self.listWidgets)
    for listWidget in self.listWidgets:
      assignments = [self.project.getByPid(listWidget.item(i).text()) for i in range(listWidget.count())]
      index = self.listWidgets.index(listWidget)
      assignmentArray[index] = assignments

    self.current.peak.dimensionNmrAtoms = assignmentArray

  def updateLayout(self, layout:QtGui.QLayout, ndim:int):
    """
    Remove excess assignment widgets if number of dimensions is less than number of assignment
    widgets displayed.
    """

    rowCount = layout.rowCount()
    colCount = layout.columnCount()

    for r in range(rowCount):
      for m in range(ndim, colCount):
        item = layout.itemAtPosition(r, m)
        if item:
          if item.widget():
            item.widget().hide()
        layout.removeItem(item)


  def updateAssigmentWidget(self, dim:int, item:object):
    """
    Update all information in assignment widget when NmrAtom is selected in list widget of that
    assignment widget.
    """
    nmrAtom = self.project.getByPid(item.text())
    self.project._appBase.current.nmrAtom = nmrAtom
    chain = nmrAtom.nmrResidue.nmrChain
    sequenceCode = nmrAtom.nmrResidue.sequenceCode
    self.chainPulldowns[dim].setData([chain.id for chain in self.project.nmrChains])
    self.chainPulldowns[dim].setIndex(self.chainPulldowns[dim].texts.index(chain.id))
    sequenceCodes = [nmrResidue.sequenceCode for nmrResidue in self.project.nmrResidues]
    self.seqCodePulldowns[dim].setData(sorted(sequenceCodes, key=CcpnSorting.stringSortKey))
    self.seqCodePulldowns[dim].setIndex(self.seqCodePulldowns[dim].texts.index(sequenceCode))
    atomPrefix = self.current.peak.peakList.spectrum.isotopeCodes[dim][-1]
    atomNames = [atomName for atomName in ATOM_NAMES if atomName[0] == atomPrefix] + [nmrAtom.name]
    self.atomTypePulldowns[dim].setData(atomNames)
    self.atomTypePulldowns[dim].setIndex(self.atomTypePulldowns[dim].texts.index(nmrAtom.name))


  def setResidueType(self, dim:int, index:int):
    """
    Set residue type in assignment widget based on chain and sequence code.
    """
    sequenceCode = self.seqCodePulldowns[dim].texts[index]
    nmrChain = self.project.fetchNmrChain(self.chainPulldowns[dim].currentText())
    residueType = nmrChain.fetchNmrResidue(sequenceCode).residueType
    self.resTypePulldowns[dim].setIndex(self.resTypePulldowns[dim].texts.index(residueType.upper()))



  def addItemToPulldown(self, pulldown:object):
    """
    Generic function to add items to pulldown list if text in pulldown list widget is changed
    """
    if pulldown.lineEdit().isModified():
      text = pulldown.lineEdit().text()
      if text not in pulldown.texts:
        pulldown.addItem(text)


  def getDeltaShift(self, nmrAtom:NmrAtom, dim:int) -> float:
    """
    Calculation of delta shift to add to the table.
    """
    if not self.current.peaks:
      return ''

    if nmrAtom is NOL:
      return ''

    deltas = []
    for peak in self.current.peaks:
      shiftList = peak.peakList.chemicalShiftList
      if shiftList:
        shift = shiftList.getChemicalShift(nmrAtom.id)
        if shift:
          position = peak.position[dim]
          deltas.append(abs(shift.value-position))
    average = sum(deltas)/len(deltas)
    return '%6.3f' % average

  def getShift(self, nmrAtom:NmrAtom) -> float:
    """
    Calculation of chemical shift value to add to the table.
    """
    if not self.current.peaks:
      return ''

    if nmrAtom is NOL:
      return ''

    for peak in self.current.peaks:
      shiftList = peak.peakList.chemicalShiftList
      if shiftList:
        shift = shiftList.getChemicalShift(nmrAtom.id)
        if shift:
          return '%8.3f' % shift.value


  def peaksAreCompatible(self) -> bool:
    """
    If multiple peaks are selected, a check is performed
    to determine whether assignment of corresponding
    dimensions of a peak allowed.
    """

    if len(self.current.peaks) == 1:
      return True
    if not self.multiCheckbox.isChecked():
      self.project._logger.warning("Multiple peaks selected, not allowed.")
      return False
    dimensionalities = set([len(peak.position) for peak in self.current.peaks])
    if len(dimensionalities) > 1:
      self.project._logger.warning('Not all peaks have the same number of dimensions.')
      return False
    for dim in range(len(self.current.peak.position)):
      if not sameAxisCodes(self.current.peaks, dim):
        self.project._logger.warning('''The combination of axiscodes is different for multiple
                 selected peaks.''')
        return False
    return True


  def emptyAllTablesAndLists(self):
    """
    Quick erase of all present information in ListWidgets and ObjectTables.
    """

    for objectTable in self.objectTables:
      objectTable.setObjects([])
    for listWidget in self.listWidgets:
      listWidget.clear()


  def createNewNmrAtom(self, dim):
    isotopeCode = self.current.peak.peakList.spectrum.isotopeCodes[dim]
    nmrAtom = self.project.fetchNmrChain(shortName=defaultNmrChainCode
                                           ).newNmrResidue().newNmrAtom(isotopeCode=isotopeCode)


    for peak in self.current.peaks:
      if nmrAtom not in peak.dimensionNmrAtoms[dim]:
        newAssignments = peak.dimensionNmrAtoms[dim] + [nmrAtom]
        axisCode = peak.peakList.spectrum.axisCodes[dim]
        peak.assignDimension(axisCode, newAssignments)
    self.listWidgets[dim].addItem(nmrAtom.pid)
    self.updateTables()



  def assignNmrAtomToDim(self, dim:int, row:int=None, col:int=None, obj:object=None):
    '''Assign the nmrAtom that is double clicked to the
       the corresponding dimension of the selected
       peaks.

    '''
    #### Should be
    objectTable = self.objectTables[dim]
    nmrAtom = objectTable.getCurrentObject()

    if nmrAtom is NOL:
      return

    for peak in self.current.peaks:
      #### Should be simplified with function in Peak class
      if nmrAtom not in peak.dimensionNmrAtoms[dim]:
        newAssignments = peak.dimensionNmrAtoms[dim] + [nmrAtom]
        axisCode = peak.peakList.spectrum.axisCodes[dim]
        peak.assignDimension(axisCode, newAssignments)

    self.listWidgets[dim].addItem(nmrAtom.pid)

  def closeDock(self):
    """
    Re-implementation of closeDock function from CcpnDock to unregister notification on current.peaks
    """
    self.project._appBase.current.unRegisterNotify(self.updateInterface, 'peaks')
    self.close()

class NotOnLine(object):
  """
  Small 'fake' object to get a message the user in the assignment
  Table that a specific dimension can not be assigned in one go
  since the frequencies of the peaks in this dimension are not on
  one line (i.e. the C frequencies of the CA and CB in a strip for
  instance).
  """

  def __init__(self):
    self.pid = 'Multiple selected peaks not on line.'
    self.id = 'Multiple selected peaks not on line.'

NOL = NotOnLine()
