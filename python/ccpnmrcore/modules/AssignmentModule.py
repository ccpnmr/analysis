#from imp import reload

from PyQt4 import QtGui, QtCore

from ccpn.lib.Assignment import CCP_CODES, ATOM_NAMES

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.CheckBox import CheckBox

from ccpnmrcore.gui.assignmentModuleLogic import (nmrAtomsForPeaks,
                                                      peaksAreOnLine,
                                                      sameAxisCodes)

from ccpnmrcore.popups.NmrResiduePopup import NmrResiduePopup

from functools import partial

class AssignmentModule(CcpnDock, Base):
  '''Module that can be used to assign nmrAtoms
     to peaks.

  '''

  #_instance = None

  def __init__(self, parent=None, project=None, peaks=None, **kw):
    '''Init.

    '''

    #self.__class__._instance = self
    CcpnDock.__init__(self, name="Assignment Module")
    Base.__init__(self, **kw)
    self.project = project

    # If self.vertically_stacked = True, it looks
    # more like the v2 assignment Popup.
    self.vertically_stacked = False
    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    #self.infoLabel = Label(self, text='', grid=(0, 0))

    # Added an extra grid layout because the amount
    # of dimensions can not be known beforehand and in
    # this way it can shrink,
    self.selectionLayout = QtGui.QGridLayout()
    self.filterLayout = QtGui.QGridLayout()
    self.advancedLayout = QtGui.QGridLayout()
    self.layout.addLayout(self.advancedLayout, 2, 0)
    self.layout.addLayout(self.selectionLayout, 1, 0)
    self.layout.addLayout(self.filterLayout, 0, 0)
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
    self.moreButtons = []
    self.nmrResidueWidgets = []



    # double tolerance
    self.doubleToleranceCheckbox = CheckBox(self, checked=False)
    self.doubleToleranceCheckbox.stateChanged.connect(self.updateInterface)
    doubleToleranceCheckboxLabel = Label(self, text="Double Tolerances ")
    self.filterLayout.addWidget(self.doubleToleranceCheckbox, 0, 1)
    self.filterLayout.addWidget(doubleToleranceCheckboxLabel, 0, 0)

    # intra-residual only
    self.intraCheckbox = CheckBox(self, checked=False)
    self.intraCheckbox.stateChanged.connect(self.updateInterface)
    intraCheckboxLabel = Label(self, text="Only Intra-residual ")
    self.filterLayout.addWidget(self.intraCheckbox, 0, 3)
    self.filterLayout.addWidget(intraCheckboxLabel, 0, 2)

    # Allow multiple peaks to be selected and assigned at same time.
    self.multiCheckbox = CheckBox(self, checked=True)
    self.multiCheckbox.stateChanged.connect(self.updateInterface)
    multiCheckboxLabel = Label(self, text="Allow multiple peaks ")
    self.filterLayout.addWidget(self.multiCheckbox, 0, 5)
    self.filterLayout.addWidget(multiCheckboxLabel, 0, 4)
    self.expCheckBox = CheckBox(self, checked=True)
    expCheckBoxLabel = Label(self, "Filter By Experiment")
    self.filterLayout.addWidget(expCheckBoxLabel, 0, 6)
    self.filterLayout.addWidget(self.expCheckBox, 0, 7)
    # nmrResidueButton = Button(self, "Show NmrResidues", callback=self.showNmrResiduePopup)
    # self.filterLayout.addWidget(nmrResidueButton, 1, 0)
    self.filterLayout.addItem(QtGui.QSpacerItem(0, 20), 4, 0)
    # self.updateButton = Button(self, 'Update', callback=self.update)
    # self.filterLayout.addWidget(self.updateButton, 3, 0)

    self.current.registerNotify(self.updateInterface, 'peaks')
    self.updateInterface()



  # functions to create empty widgets

  def createEmptyNmrAtomsTable(self, dim):
    '''Can be used to add a new table before setting
       the content.

    '''

    columns = [Column('NMR Atom', lambda nmrAtom: str(nmrAtom.pid)),
               Column('Shift', lambda nmrAtom: self.getShift(nmrAtom)),
               Column('Delta', lambda nmrAtom: self.getDeltaShift(nmrAtom, dim))]

    objectTable = ObjectTable(self, columns,
                              callback=partial(self.assignNmrAtomToDim, dim),
                              objects=[])

    # Needed to use this syntax because wanted double click not single.
    # objectTable.doubleClicked.connect(lambda index: self.assignNmrAtomToDim(dim))
    objectTable.setFixedHeight(80)
    self.objectTables.append(objectTable)

  def createEmptyListWidget(self, dim):
    '''Can be used to add a new listWidget before
       setting the content.

    '''
    listWidget = ListWidget(self, callback=partial(self.getNmrAtom, dim),
                            rightMouseCallback=self.updateNmrAtomsFromListWidgets)
    listWidget.setFixedHeight(80)
    self.listWidgets.append(listWidget)

  def createEmptyWidgetLabel(self, dim):

    positions = [peak.position[dim] for peak in self.current.peaks]
    avgPos = round(sum(positions)/len(positions), 3)
    axisCode = self.current.peak.peakList.spectrum.axisCodes[dim]
    text = axisCode + ' ' + str(avgPos)
    label = Label(self, text=text)
    label.setStyleSheet("border: 0px solid; color: #f7ffff;")
    self.labels.append(label)


  def createAssignmentWidget(self, dim):
    newAssignmentWidget = QtGui.QWidget()
    newLayout = QtGui.QGridLayout()
    chainLabel = Label(self, 'Chain', hAlign='c')
    seqCodeLabel = Label(self, 'Sequence', hAlign='c')
    atomTypeLabel = Label(self, 'Atom', hAlign='c')
    chainPulldown = self.createChainPulldown(dim)
    seqCodePulldown = self.createSeqCodePulldown(dim)
    atomTypePulldown = self.createAtomTypePulldown(dim)
    applyButton = Button(self, 'Apply', callback=partial(self.setAssignment, dim))
    newLayout.addWidget(chainLabel, 0, 0)
    newLayout.addWidget(chainPulldown, 1, 0)
    newLayout.addWidget(seqCodeLabel, 0, 1)
    newLayout.addWidget(seqCodePulldown, 1, 1)
    newLayout.addWidget(atomTypeLabel, 0, 2)
    newLayout.addWidget(atomTypePulldown, 1, 2)
    newLayout.addWidget(applyButton, 1, 3)
    newAssignmentWidget.setLayout(newLayout)
    self.assignmentWidgets.append(newAssignmentWidget)

  def createMoreButton(self, dim):
    moreButton = Button(self, 'More...', callback=partial(self.toggleNmrPopup, dim))
    moreButton.setFixedWidth(50)
    self.moreButtons.append(moreButton)

  def createNmrResidueWidgets(self):
    nmrWidget = NmrResiduePopup(parent=self, project=self.project)
    self.nmrResidueWidgets.append(nmrWidget)



  def setAssignment(self, dim):

    nmrChain = self.project.fetchNmrChain(self.chainPulldowns[dim].currentText())
    nmrResidue = nmrChain.fetchNmrResidue(self.seqCodePulldowns[dim].currentText())
    nmrAtom = nmrResidue.fetchNmrAtom(self.atomTypePulldowns[dim].currentText())
    for peak in self.current.peaks:
      dimNmrAtoms = peak.dimensionNmrAtoms[dim]
      currentItem = self.listWidgets[dim].currentItem()
      currentObject = self.project.getByPid(currentItem.text())
      toAssign = dimNmrAtoms.index(currentObject)

      dimNmrAtoms[toAssign] = nmrAtom
      allAtoms = list(peak.dimensionNmrAtoms)
      allAtoms[dim] = dimNmrAtoms
      peak.dimensionNmrAtoms = allAtoms

    self.updateInterface()


  def createChainPulldown(self, dim):
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    pulldownList.lineEdit().editingFinished.connect(partial(self.addItemToPulldown, pulldownList))
    self.chainPulldowns.append(pulldownList)
    return pulldownList

  def createSeqCodePulldown(self, dim):
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    self.seqCodePulldowns.append(pulldownList)
    return pulldownList


  def createAtomTypePulldown(self, dim):
    pulldownList = PulldownList(self)
    pulldownList.setEditable(True)
    self.atomTypePulldowns.append(pulldownList)
    return pulldownList


  def natural_key(self, string_):
    import re
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

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

    for dim in range(len(self.moreButtons), Ndimensions):
      self.createMoreButton(dim)

    for dim in range(len(self.nmrResidueWidgets), Ndimensions):
      self.createNmrResidueWidgets()


    self.widgetItems = list(zip(self.labels[:Ndimensions], self.listWidgets[:Ndimensions],
                    self.assignmentWidgets[:Ndimensions], self.objectTables[:Ndimensions]))

    for pair in self.widgetItems:
      widget = QtGui.QWidget(self)
      layout = QtGui.QVBoxLayout()
      layout.setSpacing(10)
      layout.setMargin(5)
      layout.setContentsMargins(4, 4, 4, 4)
      widget.setStyleSheet("border: 1px solid #bec4f3")
      # pair[0].setFixedHeight(10)
      for item in range(len(pair)):
        layout.addWidget(pair[item], 0, QtCore.Qt.AlignTop)
        pair[item].setStyleSheet("border: 0px solid; color: #f7ffff;")
      layout.addWidget(self.moreButtons[self.widgetItems.index(pair)], QtCore.Qt.AlignTop)
      # self.moreButtons[self.widgetItems.index(pair)]
      pair[2].setStyleSheet("PulldownList {color: black; border: 0px solid;}")
      pair[2].setStyleSheet("border: 0px solid")
      pair[3].setStyleSheet("color: black; border: 0px solid;")
      widget.setLayout(layout)
      self.widgets.append(widget)
      self.selectionLayout.addWidget(widget, 0, self.widgetItems.index(pair))
      layout.addWidget(self.nmrResidueWidgets[self.widgetItems.index(pair)])
      # self.nmrResidueWidgets[self.widgetItems.index(pair)].setStyleSheet("border: 1px solid #bec4f3")
      self.nmrResidueWidgets[self.widgetItems.index(pair)].hide()
    self.updateLayout(self.selectionLayout, Ndimensions)



  def toggleNmrPopup(self, dim):
    if self.nmrResidueWidgets[dim].isVisible():
      self.nmrResidueWidgets[dim].hide()
    else:
      self.nmrResidueWidgets[dim].show()


  # Update functions


  def updateInterface(self, peaks=None):
    '''Updates the whole widget, including recalculation
       of which nmrAtoms fit to the peaks.

    '''
    # self.updatePeaks()
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
      label.setStyleSheet("border: 0px solid; color: #f7ffff;")


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
        objectTable.setObjects(sorted(nmrAtoms) + [NEW])
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
    required_heights = [23]

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

  def updateLayout(self, layout, ndim):

    rowCount = layout.rowCount()
    colCount = layout.columnCount()

    for r in range(rowCount):
      for m in range(ndim, colCount):
        item = layout.itemAtPosition(r, m)
        if item:
          if item.widget():
            item.widget().hide()
        layout.removeItem(item)


  def getNmrAtom(self, dim, item):
    nmrAtom = self.project.getByPid(item.text())
    self.project._appBase.current.nmrAtom = nmrAtom
    chain = nmrAtom.nmrResidue.nmrChain
    sequenceCode = nmrAtom.nmrResidue.sequenceCode
    self.chainPulldowns[dim].setData([chain.id for chain in self.project.nmrChains])
    self.chainPulldowns[dim].setIndex(self.chainPulldowns[dim].texts.index(chain.id))
    sequenceCodes = [nmrResidue.sequenceCode for nmrResidue in self.project.nmrResidues]
    self.seqCodePulldowns[dim].setData(sorted(sequenceCodes, key=self.natural_key))
    self.seqCodePulldowns[dim].setIndex(self.seqCodePulldowns[dim].texts.index(sequenceCode))
    atomPrefix = self.current.peak.peakList.spectrum.isotopeCodes[dim][-1]
    atomNames = [atomName for atomName in ATOM_NAMES if atomName[0] == atomPrefix] + [nmrAtom.name]
    self.atomTypePulldowns[dim].setData(atomNames)
    self.atomTypePulldowns[dim].setIndex(self.atomTypePulldowns[dim].texts.index(nmrAtom.name))
    self.nmrResidueWidgets[dim].updatePopup(nmrAtom.nmrResidue, nmrAtom)


  def setResidueType(self, dim, index):
    sequenceCode = self.seqCodePulldowns[dim].texts[index]
    nmrChain = self.project.fetchNmrChain(self.chainPulldowns[dim].currentText())
    residueType = nmrChain.fetchNmrResidue(sequenceCode).residueType
    self.resTypePulldowns[dim].setIndex(self.resTypePulldowns[dim].texts.index(residueType.upper()))



  def addItemToPulldown(self, pulldown):
    if pulldown.lineEdit().isModified():
      text = pulldown.lineEdit().text()
      if text not in pulldown.texts:
        pulldown.addItem(text)


  def getNmrResidue(self, item):
    self.project._appBase.current.nmrResidue = self.project.getByPid(item.text()).nmrResidue
    if hasattr(self, 'NmrResiduePopup'):
      self.NmrResiduePopup.update()
    self.project._appBase.current.nmrAtom = self.project.getByPid(item.text())


  def getPeakName(self, peak, dim):
    '''Get the name of a peak, not used yet.'''

    if peak.dimensionNmrAtoms[dim].name is not None:
      return peak.dimensionNmrAtoms[dim].name
    else:
      return None


  def getDeltaShift(self, nmrAtom, dim):
    '''Calculation of delta shift to add to the table.

    '''
    if not self.current.peaks:
      return ''

    if nmrAtom is NEW or nmrAtom is NOL:
      return ''

    deltas = []
    for peak in self.current.peaks:
      shiftList = peak.peakList.chemicalShiftList
      # shiftList = getShiftlistForPeak(peak)
      if shiftList:
        shift = shiftList.getChemicalShift(nmrAtom.id)
        if shift:
          position = peak.position[dim]
          deltas.append(abs(shift.value-position))
    average = sum(deltas)/len(deltas)
    return round(average, 3)

  def getShift(self, nmrAtom):
    '''Calculation of delta shift to add to the table.

    '''
    if not self.current.peaks:
      return ''

    if nmrAtom is NEW or nmrAtom is NOL:
      return ''

    for peak in self.current.peaks:
      shiftList = peak.peakList.chemicalShiftList
      if shiftList:
        shift = shiftList.getChemicalShift(nmrAtom.id)
        if shift:
          return shift.value


  def peaksAreCompatible(self):
    '''If multiple peaks are selected, a check is performed
       to determine whether assignment of corresponding
       dimensions of a peak allowed.

    '''

    if len(self.current.peaks) == 1:
      return True
    if not self.multiCheckbox.isChecked():
      print('Multiple peaks selected, not allowed.')
      return False
    dimensionalities = set([len(peak.position) for peak in self.current.peaks])
    if len(dimensionalities) > 1:
      print('Not all peaks have the same number of dimensions.')
      return False
    for dim in range(len(self.current.peak.position)):
      if not sameAxisCodes(self.current.peaks, dim):
        print('''The combination of axiscodes is different for multiple
                 selected peaks.''')
        return False
    return True


  def emptyAllTablesAndLists(self):
    '''Quick erase of all present information.

    '''

    for objectTable in self.objectTables:
      objectTable.setObjects([])
    for listWidget in self.listWidgets:
      listWidget.clear()





  def assignNmrAtomToDim(self, row, col, obj, dim):
    '''Assign the nmrAtom that is clicked on to the
       the corresponding dimension of the selected
       peaks.

    '''
    objectTable = self.objectTables[dim]
    nmrAtom = objectTable.getCurrentObject()

    if nmrAtom is NOL:
      return
    elif nmrAtom is NEW:
      isotopeCode = self.current.peak.peakList.spectrum.isotopeCodes[dim]
      ###NBNB
      nmrAtom = self.project.fetchNmrChain(shortName='@-').newNmrResidue().newNmrAtom(isotopeCode=isotopeCode)

    for peak in self.current.peaks:
      # axisCode = getAxisCodeForPeakDimension(peak, dim)

      if nmrAtom not in peak.dimensionNmrAtoms[dim]:
        newAssignments = peak.dimensionNmrAtoms[dim] + [nmrAtom]
        axisCode = peak.peakList.spectrum.axisCodes[dim]
        peak.assignDimension(axisCode, newAssignments)

    self.listWidgets[dim].addItem(nmrAtom.pid)

  def closeDock(self):
    self.project._appBase.current.unRegisterNotify(self.updateInterface, 'peaks')
    self.close()

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
