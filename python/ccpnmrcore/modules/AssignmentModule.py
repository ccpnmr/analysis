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

from ccpnmrcore import Current

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
    self.listWidgets = []
    self.objectTables = []
    self.labels = []
    self.advancedButtons = []
    self.nmrPopups = []

    # double tolerance
    self.doubleToleranceCheckbox = CheckBox(self, checked=False)
    self.doubleToleranceCheckbox.stateChanged.connect(self.updateInterface)
    doubleToleranceCheckboxLabel = Label(self, text="Double Tolerances:")
    self.filterLayout.addWidget(self.doubleToleranceCheckbox, 0, 1)
    self.filterLayout.addWidget(doubleToleranceCheckboxLabel, 0, 0)

    # intra-residual only
    self.intraCheckbox = CheckBox(self, checked=False)
    self.intraCheckbox.stateChanged.connect(self.updateInterface)
    intraCheckboxLabel = Label(self, text="Only Intra-residual:")
    self.filterLayout.addWidget(self.intraCheckbox, 0, 3)
    self.filterLayout.addWidget(intraCheckboxLabel, 0, 2)

    # Allow multiple peaks to be selected and assigned at same time.
    self.multiCheckbox = CheckBox(self, checked=True)
    self.multiCheckbox.stateChanged.connect(self.updateInterface)
    multiCheckboxLabel = Label(self, text="Allow multiple peaks:")
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

    self.project._appBase.current.registerNotify(self.updateInterface, 'peaks')
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
                              callback=None,
                              objects=[])

    # Needed to use this syntax because wanted double click not single.
    objectTable.doubleClicked.connect(lambda index: self.assignNmrAtomToDim(dim))
    objectTable.setFixedHeight(80)
    self.objectTables.append(objectTable)

  def createEmptyListWidget(self, dim):
    '''Can be used to add a new listWidget before
       setting the content.

    '''
    listWidget = ListWidget(self, callback=self.getNmrResidue,
                            rightMouseCallback=self.updateNmrAtomsFromListWidgets)
    listWidget.setFixedHeight(80)
    self.listWidgets.append(listWidget)

  def createEmptyWidgetLabel(self, dim):

    positions = [peak.position[dim] for peak in self.peaks]
    avgPos = round(sum(positions)/len(positions), 3)
    axisCode = self.peaks[0].peakList.spectrum.axisCodes[dim]
    text = axisCode + ' ' + str(avgPos)
    label = Label(self, text=text)
    label.setStyleSheet("border: 0px solid; color: #f7ffff;")
    self.labels.append(label)

  def createAdvancedButton(self, dim):
    advancedButton = Button(self, text="Advanced", hAlign='c')
    advancedButton.setFixedWidth(100)
    from functools import partial
    advancedButton.setCheckable(True)
    advancedButton.toggled.connect(partial(self.toggleNmrResiduePopup, dim))
    self.advancedButtons.append(advancedButton)

  def createEnoughTablesAndLists(self):
    '''Makes sure there are enough tables for the amount
       of dimensions of the currently selected peak(s).
       This method only runs when all peaks have the same
       amount of dimensions as is guaranteed by running
       peaksAreCompatible.py

    '''

    Ndimensions = len(self.peaks[0].position)

    # Create extra tables if needed.
    for dim in range(len(self.objectTables), Ndimensions):
      self.createEmptyNmrAtomsTable(dim)

    for dim in range(len(self.listWidgets), Ndimensions):
      self.createEmptyListWidget(dim)

    for dim in range(len(self.labels), Ndimensions):
      self.createEmptyWidgetLabel(dim)

    for dim in range(len(self.advancedButtons), Ndimensions):
      self.createAdvancedButton(dim)
      self.showNmrResiduePopup(dim)

    self.widgetItems = list(zip(self.labels[:Ndimensions], self.listWidgets[:Ndimensions], self.objectTables[:Ndimensions], self.advancedButtons[:Ndimensions]))
    # self.putListAndTablesIntoWidgets(self.widgetItems)
    for pair in self.widgetItems:
      widget = QtGui.QWidget(self)
      layout = QtGui.QVBoxLayout()
      layout.setSpacing(10)
      layout.setMargin(5)
      layout.setContentsMargins(4, 4, 4, 4)
      widget.setStyleSheet("border: 1px solid #bec4f3")
      pair[0].setFixedHeight(10)
      for item in range(len(pair)):
        layout.addWidget(pair[item], 0, QtCore.Qt.AlignTop)
        layout.addItem(QtGui.QSpacerItem(0, 20))
        pair[item].setStyleSheet("border: 0px solid; color: #f7ffff;")



      pair[2].setStyleSheet("color: black; border: 0px solid;")
      pair[3].setChecked(False)
      layout.setAlignment(pair[3], QtCore.Qt.AlignHCenter)
      widget.setLayout(layout)
      self.widgets.append(widget)
      self.selectionLayout.addWidget(widget, 0, self.widgetItems.index(pair))

    self.updateLayout(self.selectionLayout, Ndimensions)
    for nmrPopup in self.nmrPopups:
      nmrPopup.hide()

    self.update()


  # Update functions


  def updateInterface(self, peaks=None):
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
    self.updateWidgetLabels()


  def updateWidgetLabels(self):

    Ndimensions = len(self.peaks[0].position)

    for dim, label in zip(range(Ndimensions), self.labels):
      positions = [peak.position[dim] for peak in self.peaks]
      avgPos = round(sum(positions)/len(positions), 3)
      axisCode = self.peaks[0].peakList.spectrum.axisCodes[dim]
      text = axisCode + ' ' + str(avgPos)
      label.setText(text)
      label.setStyleSheet("border: 0px solid; color: #f7ffff;")


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


  def updateAssignedNmrAtomsListwidgets(self):
    '''Update the listWidget showing which nmrAtoms
       are assigned to which peak dimensions. If multiple
       peaks are selected, only the assignment that they
       have in common are shown. Maybe this should be all
       assignments. You can see that at the peak annotation
       though.

    '''

    Ndimensions = len(self.peaks[0].position)
    required_heights = [23]

    for dim, listWidget in zip(range(Ndimensions), self.listWidgets):

      self.nmrAtoms = [set(peak.dimensionNmrAtoms[dim]) for peak in self.peaks]
      self.nmrAtoms = intersectionOfAll(self.nmrAtoms)
      listWidget.addItems([str(a.pid) for a in self.nmrAtoms])

  def updateNmrAtomsFromListWidgets(self):

    assignmentArray = [0] * len(self.listWidgets)
    for listWidget in self.listWidgets:
      assignments = [self.project.getById(listWidget.item(i).text()) for i in range(listWidget.count())]
      index = self.listWidgets.index(listWidget)
      assignmentArray[index] = assignments

    self.peaks[0].dimensionNmrAtoms = assignmentArray

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


  # Popup functions

  def showNmrResiduePopup(self, dim):

    nmrResiduePopup = NmrResiduePopup(self, self.project)

    scrollArea = ScrollArea(self)
    scrollArea.setWidget(nmrResiduePopup)
    self.nmrPopups.append(scrollArea)
    self.selectionLayout.addWidget(self.nmrPopups[dim], 7, dim, 1, 1)
    self.nmrPopups[dim].hide()


  def toggleNmrResiduePopup(self, dim):

    if self.nmrPopups[dim].isVisible():
      self.nmrPopups[dim].hide()
    else:
      self.nmrPopups[dim].show()





  def getNmrResidue(self, item):
    self.project._appBase.current.nmrResidue = self.project.getById(item.text()).nmrResidue
    if hasattr(self, 'NmrResiduePopup'):
      self.NmrResiduePopup.update()
    self.project._appBase.current.nmrAtom = self.project.getById(item.text())


  def getPeakName(self, peak, dim):
    '''Get the name of a peak, not used yet.'''

    if peak.dimensionNmrAtoms[dim].name is not None:
      return peak.dimensionNmrAtoms[dim].name
    else:
      return None


  def getDeltaShift(self, nmrAtom, dim):
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
        shift = shiftList.getChemicalShift(nmrAtom.id)
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
        shift = shiftList.getChemicalShift(nmrAtom.id)
        if shift:
          return shift.value


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


  def emptyAllTablesAndLists(self):
    '''Quick erase of all present information.

    '''

    for objectTable in self.objectTables:
      objectTable.setObjects([])
    for listWidget in self.listWidgets:
      listWidget.clear()





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

    self.listWidgets[dim].addItem(nmrAtom.nmrResidue.pid)



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
