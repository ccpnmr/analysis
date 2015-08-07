#from imp import reload

from PyQt4 import QtGui, QtCore

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.CheckBox import CheckBox

from ccpnmrcore.gui.assignmentModuleLogic import (getAllNmrAtoms, nmrAtomsForPeaks,
                                                      peaksAreOnLine, intersectionOfAll,
                                                      sameAxisCodes,
                                                      getAxisCodeForPeakDimension,
                                                      getIsotopeCodeForPeakDimension,
                                                      getShiftlistForPeak)

from ccpnmrcore.popups.NmrResiduePopup import NmrResiduePopup


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
    self.vertically_stacked = True
    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    #self.infoLabel = Label(self, text='', grid=(0, 0))

    # Added an extra grid layout because the amount
    # of dimensions can not be known beforehand and in
    # this way it can shrink,
    self.selectionLayout = QtGui.QGridLayout()
    self.filterLayout = QtGui.QGridLayout()
    self.layout.addLayout(self.selectionLayout, 0, 0)
    self.layout.addLayout(self.filterLayout, 1, 0)
    self.selectionLayout.setRowMinimumHeight(0, 0)
    self.selectionLayout.setRowStretch(0, 0)
    self.selectionLayout.setRowStretch(1, 1)
    self.listWidgets = []
    self.objectTables = []

    # double tolerance
    self.doubleToleranceCheckbox = CheckBox(self, checked=False)
    self.doubleToleranceCheckbox.stateChanged.connect(self.update)
    doubleToleranceCheckboxLabel = Label(self, text="Double Tolerances:")
    self.filterLayout.addWidget(self.doubleToleranceCheckbox, 0, 1)
    self.filterLayout.addWidget(doubleToleranceCheckboxLabel, 0, 0)

    # intra-residual only
    self.intraCheckbox = CheckBox(self, checked=False)
    self.intraCheckbox.stateChanged.connect(self.update)
    intraCheckboxLabel = Label(self, text="Only Intra-residual:")
    self.filterLayout.addWidget(self.intraCheckbox, 1, 1)
    self.filterLayout.addWidget(intraCheckboxLabel, 1, 0)

    # Allow multiple peaks to be selected and assigned at same time.
    self.multiCheckbox = CheckBox(self, checked=True)
    self.multiCheckbox.stateChanged.connect(self.update)
    multiCheckboxLabel = Label(self, text="Allow multiple peaks:")
    self.filterLayout.addWidget(self.multiCheckbox, 2, 1)
    self.filterLayout.addWidget(multiCheckboxLabel, 2, 0)
    nmrResidueButton = Button(self, "Show NmrResidues", callback=self.showNmrResiduePopup)
    self.filterLayout.addWidget(nmrResidueButton, 3, 0)
    self.filterLayout.addItem(QtGui.QSpacerItem(0, 20), 4, 0)

    self.update()


  def showNmrResiduePopup(self):

    self.NmrResiduePopup = NmrResiduePopup(self, self.project)
    scrollArea = ScrollArea(self)
    scrollArea.setWidget(self.NmrResiduePopup)
    self.filterLayout.addWidget(scrollArea, 5, 0)


  def update(self):
    '''Updates the whole widget, including recalculation
       of which nmrAtoms fit to the peaks.

    '''
    self.updatePeaks()
    self.emptyAllTablesAndLists()
    if not self.peaks or not self.peaksAreCompatible():
      return
    self.createEnoughTablesAndLists()
    self.updateTables()
    self.updateAssignedNmrAtomsListwidgets()

  def peaksAreCompatible(self):
    '''If multiple peaks are selected, a check is performed
       to determine whether assignment of corresponding
       dimensions of a peak allowed.

    '''

    if len(self.peaks) == 1:
      return True
    if not self.multiCheckbox.isChecked():
      print('Multiple peaks selected, not allowed.')
      return False
    dimensionalities = set([len(peak.position) for peak in self.peaks])
    if len(dimensionalities) > 1:
      print('Not all peaks have the same number of dimensions.')
      return False
    for dim in range(len(self.peaks[0].position)):
      if not sameAxisCodes(self.peaks, dim):
        print('''The combination of axiscodes is different for multiple
                 selected peaks.''')
        return False
    return True

  def updatePeaks(self, peaks=None):
    '''If argument peaks is not given, the currently
       selected peaks are returned. This method is mostly
       necessary because when no peaks are selected,
       self.project._appBase.current.peaks is None instead
       of an empty list. Which would probably be handier.

    '''
    if not peaks:
      self.peaks = self.project._appBase.current.peaks or []
    else:
      self.peaks = peaks

  def getNmrResidue(self, item):
    self.project._appBase.current.nmrResidue = self.project.getById(item.text()).nmrResidue
    if hasattr(self, 'NmrResiduePopup'):
      self.NmrResiduePopup.update()
    self.project._appBase.current.nmrAtom = self.project.getById(item.text())


  def updateTables(self):
    '''Updates the tables indicating the different assignment
       possibilities of the peak dimensions.

    '''

    peaks = self.peaks
    doubleTolerance = self.doubleToleranceCheckbox.isChecked()
    intraResidual = self.intraCheckbox.isChecked()
    allNmrAtoms = getAllNmrAtoms(self.project)
    nmrAtomsForTables = nmrAtomsForPeaks(peaks, allNmrAtoms,
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

  def createEnoughTablesAndLists(self):
    '''Makes sure there are enough tables for the amount
       of dimensions of the currently selected peak(s).
       This method only runs when all peaks have the same
       amount of dimensions as is guaranteed by running
       peaksAreCompatible.

    '''

    Ndimensions = len(self.peaks[0].position)

    # Create extra tables if needed.
    for dim in range(len(self.objectTables), Ndimensions):
      self.createEmptyNmrAtomsTable(dim)

    # Hide tables that exceed the amount of peak dimensions.
    for objectTable in self.objectTables[Ndimensions:]:
      objectTable.setObjects([])
      objectTable.hide()

    for dim in range(len(self.listWidgets), Ndimensions):
      self.createEmptyListWidget(dim)

    for listWidget in self.listWidgets[Ndimensions:]:
      listWidget.clear()
      listWidget.hide()

  def emptyAllTablesAndLists(self):
    '''Quick erase of all present information.

    '''

    for objectTable in self.objectTables:
      objectTable.setObjects([])
    for listWidget in self.listWidgets:
      listWidget.clear()

  def createEmptyNmrAtomsTable(self, dim):
    '''Can be used to add a new table before setting
       the content.

    '''

    columns = [Column('NMR Atom', lambda nmrAtom: str(nmrAtom.pid)),
               Column('Shift', lambda nmrAtom: self.getShift(nmrAtom)),
               Column('Delta', lambda nmrAtom: self.deltaShift(nmrAtom, dim))]

    #callback = lambda nmrAtom, row, column: self.assignNmrAtomToDim(nmrAtom, dim)
    objectTable = ObjectTable(self, columns,
                              callback=None,
                              objects=[])

    # Needed to use this syntax because wanted double click not single.
    objectTable.doubleClicked.connect(lambda index: self.assignNmrAtomToDim(dim))
    objectTable.setFixedHeight(100)
    self.objectTables.append(objectTable)
    if self.vertically_stacked:
      self.selectionLayout.addWidget(objectTable, dim, 1)
      self.selectionLayout.addItem(QtGui.QSpacerItem(0, 10))
    else:
      self.selectionLayout.addWidget(objectTable, 1, dim)
      self.selectionLayout.addItem(QtGui.QSpacerItem(0, 10))
    objectTable.show()

  def createEmptyListWidget(self, dim):
    '''Can be used to add a new listWidget before
       setting the content.

    '''
    listWidget = ListWidget(self, callback=self.getNmrResidue)
    listWidget.setFixedHeight(100)
    self.listWidgets.append(listWidget)
    if self.vertically_stacked:
      self.selectionLayout.addWidget(listWidget, dim, 0)
      self.selectionLayout.addItem(QtGui.QSpacerItem(0, 10))
    else:
      self.selectionLayout.addWidget(listWidget, 0, dim)
      self.selectionLayout.addItem(QtGui.QSpacerItem(0, 10))

  def updateAssignedNmrAtomsListwidgets(self):
    '''Update the listWidget showing which nmrAtoms
       are assigned to which peak dimensions. If multiple
       peaks are selected, only the assignment that they
       have in common are shown. Maybe this should be all
       assignments. You can see that at the peak anotation
       though.

    '''

    Ndimensions = len(self.peaks[0].position)
    required_heights = [23]

    for dim, listWidget in zip(range(Ndimensions), self.listWidgets):

      self.nmrAtoms = [set(peak.dimensionNmrAtoms[dim]) for peak in self.peaks]
      self.nmrAtoms = intersectionOfAll(self.nmrAtoms)
      listWidget.addItems([str(a.pid) for a in self.nmrAtoms])
      listWidget.show()
      required_heights.append(listWidget.sizeHintForRow(0) * len(self.nmrAtoms))

    required_height = max(required_heights) + 5

    if not self.vertically_stacked:
      for listWidget in self.listWidgets:
        listWidget.setMaximumHeight(required_height)

  def getPeakName(self, peak, dim):
    '''Get the name of a peak, not used yet.'''

    if peak.dimensionNmrAtoms[dim].name is not None:
      return peak.dimensionNmrAtoms[dim].name
    else:
      return None

  def assignNmrAtomToDim(self, dim):
    '''Assign the nmrAtom that is clicked on to the
       the corresponding dimension of the selected
       peaks.

    '''
    objectTable = self.objectTables[dim]
    nmrAtom = objectTable.getCurrentObject()

    if nmrAtom is NOL:
      return
    elif nmrAtom is NEW:
      isotope = getIsotopeCodeForPeakDimension(self.peaks[0], dim)
      nmrAtom = self.project.newNmrChain().newNmrResidue().newNmrAtom(isotopeCode=isotope)

    for peak in self.peaks:
      axisCode = getAxisCodeForPeakDimension(peak, dim)

      if nmrAtom not in peak.dimensionNmrAtoms[dim]:
        newAssignments = peak.dimensionNmrAtoms[dim] + [nmrAtom]
        peak.assignDimension(axisCode, newAssignments)
    self.update()

  def deltaShift(self, nmrAtom, dim):
    '''Calculation of delta shift to add to the table.

    '''
    self.updatePeaks()
    if not self.peaks:
      return ''

    if nmrAtom is NEW or nmrAtom is NOL:
      return ''

    deltas = []
    for peak in self.peaks:
      shiftList = getShiftlistForPeak(peak)
      if shiftList:
        shift = shiftList.findChemicalShift(nmrAtom)
        if shift:
          position = peak.position[dim]
          deltas.append(abs(shift.value-position))
    average = sum(deltas)/len(deltas)
    return round(average, 3)

  def getShift(self, nmrAtom):
    '''Calculation of delta shift to add to the table.

    '''
    self.updatePeaks()
    if not self.peaks:
      return ''

    if nmrAtom is NEW or nmrAtom is NOL:
      return ''

    deltas = []
    for peak in self.peaks:
      shiftList = getShiftlistForPeak(peak)
      if shiftList:
        shift = shiftList.findChemicalShift(nmrAtom)
        if shift:
          return shift.value

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
