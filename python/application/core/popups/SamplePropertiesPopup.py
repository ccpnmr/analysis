__author__ = 'luca'


from PyQt4 import QtGui, QtCore
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.DateTime import DateTime
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.TextEditor import TextEditor
from functools import partial


SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
OTHER_UNIT = ['µ','m', 'n', 'p']
CONCENTRATION_UNIT = ['µM', 'mM', 'nM', 'pM']
VOLUME_UNIT = ['µL', 'mL', 'nL', 'pL']
MASS_UNIT = ['µg','kg','g','mg', 'ng', 'pg']
SAMPLE_STATES = ['liquid', 'solid', 'ordered', 'powder', 'crystal', 'other']
TYPECOMPONENT =  ['Solvent', 'Compound', 'Target', 'inhibitor ', 'Other']
C_COMPONENT_UNIT = ['Molar', 'Mass/Volume',  'mol/Volume', ]

class SamplePropertiesPopup(QtGui.QDialog, Base):
  def __init__(self, sample, item, parent=None, project=None, **kw):
    super(SamplePropertiesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.project = project
    sideBar = project._appBase.mainWindow.sideBar
    print(self.project)
    self.sample = sample
    self.setWindowTitle("Sample Properties")
    self.area = ScrollArea(self)
    self.area.setWidgetResizable(True)
    self.area.setMinimumSize(450, 650)
    self.areaContents = QtGui.QWidget() # our 'Widget' doesn't follow the layout rule

    self.area.setStyleSheet(""" background-color:  #2a3358; """)
    self.area.setWidget(self.areaContents)
    self.layout().addWidget(self.area, 0, 0, 1, 0)
    buttonBox = ButtonList(self, grid=(2, 2), callbacks=[self.reject, self.accept], texts=['Cancel', 'Apply'])
    self.setMaximumSize(450, 650)

    # Widgets Properties:

    # SampleName
    sampleNameLabel = Label(self.areaContents, text="Sample name ", grid=(1, 1), hAlign='l')
    self.sampleName = LineEdit(self.areaContents, grid=(1, 2), hAlign='l' )
    self.sampleName.setStyleSheet(""" background-color:  white""")
    self.sampleName.setFixedWidth(203)
    self.sampleName.setFixedHeight(25)
    self.sampleName.setText(sample.name)
    self.sampleName.editingFinished.connect(self.changeSampleName)

#   # Sample Components
    SampleComponents = Label(self.areaContents, text="Sample Components ", grid=(2, 1), hAlign='l')
    spPid = [sp.pid for sp in sample.spectra]
    self.spInMixture = PulldownList(self.areaContents, grid=(2, 2), hAlign='l' )
    self.spInMixture.setStyleSheet(""" background-color:  white""")
    self.spInMixture.setFixedWidth(203)
    self.spInMixture.setFixedHeight(25)
    self.spInMixture.setData(spPid)
    self.spInMixture.setEditable(True)

#   # Add component

    self.sampleAddComponents = Button(self.areaContents, text="Add Sample Components ", grid=(13, 1),
                                      hAlign='l', callback=self.addComponents)
    self.sampleAddComponents.setStyleSheet(""" background-color:  white""")
    self.sampleAddComponents.setFixedWidth(195)
    self.sampleAddComponents.setFixedHeight(25)


#   #Sample Spectra
    sampleSpectra = Label(self.areaContents, text="Sample Spectra ", vAlign='t', hAlign='l', grid=(3, 1))
    self.sampleExperimentType = PulldownList(self.areaContents, hAlign='l', grid=(3, 2))#, vAlign='t'
    self.sampleExperimentType.addItems(spPid)
    self.sampleExperimentType.setStyleSheet(""" background-color:  white""")
    self.sampleExperimentType.setFixedWidth(203)
    self.sampleExperimentType.setFixedHeight(25)

#   #Sample  State
    sampleState = Label(self.areaContents, text="Sample State ", vAlign='t', hAlign='l', grid=(4, 1))
    self.sampleState = PulldownList(self.areaContents, hAlign='l', grid=(4, 2))#, vAlign='t'
    self.sampleState.addItems(SAMPLE_STATES)
    self.sampleState.setStyleSheet(""" background-color:  white""")
    self.sampleState.setFixedWidth(203)
    self.sampleState.setFixedHeight(25)
    self.sampleState.activated[str].connect(self.sampleStateChanged)

#   #Sample Amount Unit
    sampleAmountUnitLabel = Label(self.areaContents, text="Sample Amount ", grid=(5, 1), hAlign='l')
    self.sampleAmountUnit = PulldownList(self.areaContents, grid=(5, 2), hAlign='l' )
    self.sampleAmountUnit.setData(CONCENTRATION_UNIT)
    self.sampleAmountUnit.setFixedWidth(75)
    self.sampleAmountUnit.setFixedHeight(25)
    self.sampleAmountUnit.setStyleSheet(""" background-color:  white""")
    self.sampleAmountUnit.activated[str].connect(self.sampleAmountUnitChanged)

#    # Sample Amount
#     sampleAmountLabel = Label(self.areaContents, text="Sample Amount ", grid=(6, 1), hAlign='l')
    self.sampleAmount = DoubleSpinbox(self.areaContents, grid=(5, 2), hAlign='r' )
    self.sampleAmount.setRange(0.00, 1000.00)
    self.sampleAmount.setSingleStep(0.01)
    self.sampleAmount.setStyleSheet(""" background-color:  white""")
    self.sampleAmount.setFixedWidth(120)
    self.sampleAmount.setFixedHeight(25)
    # self.sampleAmount.setValue(float(500.00))
    self.sampleAmount.valueChanged.connect(self.sampleAmountChanged)

    # Sample pH
    samplepHLabel = Label(self.areaContents, text="Sample pH ", grid=(7, 1), hAlign='l')
    self.samplepH = DoubleSpinbox(self.areaContents, grid=(7, 2), hAlign='l' )
    self.samplepH.setRange(0.00, 14.00)
    self.samplepH.setSingleStep(0.01)
    self.samplepH.valueChanged.connect(self.samplepHchanged)
    self.samplepH.setStyleSheet(""" background-color:  white""")
    self.samplepH.setFixedWidth(203)
    self.samplepH.setFixedHeight(25)

    # Sample Date
    sampleDate = Label(self.areaContents, text="Sample Creation Date ", grid=(8, 1), hAlign='l')
    self.sampleDate = DateTime(self.areaContents, grid=(8, 2), hAlign='l')
    self.sampleDate.setStyleSheet(""" background-color:  white""")
    self.sampleDate.setFixedWidth(203)
    self.sampleDate.setFixedHeight(25)
    if sample.creationDate is None:
     setToday = QtCore.QDate.currentDate()
     self.sampleDate.setDate(setToday)
    # self.sampleDate.setText(sample.creationDate)

    # Sample Plate Identifier
    samplePlateIdentifierLabel = Label(self.areaContents, text="Sample Plate Identifier ", grid=(9, 1), hAlign='l')
    self.plateIdentifier = LineEdit(self.areaContents, grid=(9, 2), hAlign='l' )
    self.plateIdentifier.setStyleSheet(""" background-color:  white""")
    self.plateIdentifier.setFixedWidth(203)
    self.plateIdentifier.setFixedHeight(25)
    self.plateIdentifier.setText(sample.plateIdentifier)
    self.plateIdentifier.editingFinished.connect(self.plateIdentifierChanged)

    # Sample Row Number
    samplerowNumberLabel = Label(self.areaContents, text="Sample Row Number ", grid=(10, 1), hAlign='l')
    self.rowNumber = LineEdit(self.areaContents, grid=(10, 2), hAlign='l' )
    self.rowNumber.setStyleSheet(""" background-color:  white""")
    self.rowNumber.setFixedWidth(203)
    self.rowNumber.setFixedHeight(25)
    if sample.rowNumber is not None:
      self.rowNumber.setText(sample.rowNumber)
    # else:
    #   self.rowNumber.setText(str('<Insert 0 + Row Num. Eg. 01 >'))
    self.rowNumber.editingFinished.connect(self.columnNumberChanged)
    self.rowNumber.editingFinished.connect(self.rowNumberChanged)

    # Sample Column Number
    sampleColumnNumberLabel = Label(self.areaContents, text="Sample Column Number ", grid=(11, 1), hAlign='l')
    self.columnNumber = LineEdit(self.areaContents, grid=(11, 2), hAlign='l' )
    self.columnNumber.setStyleSheet(""" background-color:  white""")
    self.columnNumber.setFixedWidth(203)
    self.columnNumber.setFixedHeight(25)
    if sample.columnNumber is not None:
      self.columnNumber.setText(sample.columnNumber)
    # else:
    #   self.columnNumber.setText(str('< Insert 0 + Col Num. Eg. 01 >'))
    self.rowNumber.editingFinished.connect(self.columnNumberChanged)

    # Sample Comment
    sampleCommentLabel = Label(self.areaContents, text="Comment ", grid=(12, 1), hAlign='l')
    self.comment = TextEditor(self.areaContents, grid=(12, 2), hAlign='c' )
    self.comment.setStyleSheet(""" background-color: white""")
    self.comment.setFixedWidth(207)
    self.comment.setFixedHeight(50)
    self.comment.setText(sample.comment)
    self.comment.textChanged.connect(self.commentChanged)

    # Only to align and center all nicely
    labelAllignLeft = Label(self.areaContents, text="", grid=(1, 0), hAlign='l')
    labelAllignRight = Label(self.areaContents, text="", grid=(1, 3), hAlign='l')

  def addComponents(self):

    popup = AddSampleComponentPopup(parent=None, project=self.project, sample= self.sample)
    popup.exec_()
    popup.raise_()

  def changeSampleName(self):
    if self.sampleName.isModified():
      self.sample.rename(self.sampleName.text())
      self.item.setText(0, 'SA:'+self.sampleName.text())
      for i in range(self.item.childCount()):
        pid = self.item.child(i).text(0).split(':')[0]+':'+self.sampleName.text()+"."\
              + self.item.child(i).text(0).split('.')[1]
        self.item.child(i).setText(0, pid)

  def samplepHchanged(self, value):
    self.sample.pH = value
    print(self.sample.pH, 'pH')

  def sampleStateChanged(self, pressed):
    if pressed == 'liquid':
      self.sampleUnitChangedInVolume()
    elif pressed == 'other':
      self.sampleUnitChangedInConcentration()
    else:
      self.sampleUnitChangedInMass()


  def sampleUnitChangedInVolume(self):
    self.sampleAmountUnit.setData(VOLUME_UNIT)

  def sampleUnitChangedInConcentration(self):
    self.sampleAmountUnit.setData(CONCENTRATION_UNIT)

  def sampleUnitChangedInMass(self):
    self.sampleAmountUnit.setData(MASS_UNIT)

  def sampleAmountChanged(self, value):
    self.sample.sampleAmount = value
    print(self.sample.sampleAmount, 'sampleAmount')

  def sampleAmountUnitChanged(self, pressed):
    self.sample.amountUnit = str(pressed)
    print(self.sample.amountUnit, 'unit')

  def plateIdentifierChanged(self):
    self.sample.plateIdentifier = str(self.plateIdentifier.text())
    print(self.sample.plateIdentifier, 'plateIdentifier')

  def rowNumberChanged(self):
    self.sample.rowNumber = int(self.rowNumber.text())
    print(self.sample.rowNumber, 'rowNumber')

  def columnNumberChanged(self):
    self.sample.columnNumber = int(self.columnNumber.text())
    print(self.sample.columnNumber, 'columnNumber')

  def commentChanged(self):
    newText = self.comment.toPlainText()
    self.sample.comment = newText
    print(self.sample.comment)

  def keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      pass



class AddSampleComponentPopup(QtGui.QDialog):
  def __init__(self, parent=None, project=None, sample=None, **kw):
    super(AddSampleComponentPopup, self).__init__(parent)
    self.sample = sample
    self.project = project
    self.sideBar = project._appBase.mainWindow.sideBar
    self.newSampleSideBar = self.sideBar.newSample

    self.setWindowTitle("Add Sample Components")
    self.area = ScrollArea(self)
    self.area.setWidgetResizable(True)
    self.area.setMinimumSize(350, 350)
    self.layout().addWidget(self.area, 0, 0, 1, 0)
    buttonBox = ButtonList(self, grid=(2, 2), callbacks=[self.addComponent, self.reject], texts=['Add', 'Close'])
    labelAllignLeft = Label(self.area, text="", grid=(1, 0), hAlign='l')
    labelAllignRight = Label(self.area, text="", grid=(1, 3), hAlign='l')
    self.setMaximumSize(350, 350)

    typeLabel = Label(self.area, text="Type ", grid=(1, 1), hAlign='l')
    self.type = PulldownList(self.area, grid=(1, 2), hAlign='l' )
    self.type.setData(TYPECOMPONENT)
    self.type.setFixedWidth(155)
    self.type.setFixedHeight(25)
    self.type.activated[str].connect(self.typeComponent)

    sampleComponentsLabel = Label(self.area, text="Component Name ", grid=(2, 1), hAlign='l')
    self.nameComponents = LineEdit(self.area, grid=(2, 2), hAlign='r' )
    self.nameComponents.setText('New Sample Component')
    self.nameComponents.setFixedWidth(155)
    self.nameComponents.setFixedHeight(25)

    sampleComponentsLabelingLabel = Label(self.area, text="Labeling ", grid=(3, 1), hAlign='l')
    self.labeling = LineEdit(self.area, grid=(3, 2), hAlign='r' )
    self.labeling.setText('H')
    self.labeling.setFixedWidth(155)
    self.labeling.setFixedHeight(25)

#   #concentration unit
    concentrationUnitLabel = Label(self.area, text="Value Unit ", grid=(4, 1), hAlign='l')
    self.concentrationUnit = PulldownList(self.area, grid=(4, 2), hAlign='l' )
    self.concentrationUnit.setData(C_COMPONENT_UNIT)
    self.concentrationUnit.setFixedWidth(157)
    self.concentrationUnit.setFixedHeight(25)
    self.concentrationUnit.activated[str].connect(self.setConcentrationUnit)

    concentrationLabel = Label(self.area, text="Value 1 ", grid=(5, 1), hAlign='l')
    self.concentrationUnit1 = PulldownList(self.area, grid=(5, 2), hAlign='l' )
    self.concentrationUnit1.setFixedWidth(70)
    self.concentrationUnit1.setFixedHeight(25)

    self.concentration = DoubleSpinbox(self.area, grid=(5, 2), hAlign='r' )
    self.concentration.setRange(0.00, 1000.00)
    self.concentration.setSingleStep(0.01)
    self.concentration.setFixedWidth(70)
    self.concentration.setFixedHeight(25)

    self.concentrationLabel2 = Label(self.area, text="Value 2 ", grid=(6, 1), hAlign='l')
    self.concentrationUnit2 = PulldownList(self.area, grid=(6, 2), hAlign='l' )
    self.concentrationUnit2.setFixedWidth(70)
    self.concentrationUnit2.setFixedHeight(25)
    self.concentration2 = DoubleSpinbox(self.area, grid=(6, 2), hAlign='r' )
    self.concentration2.setRange(0.00, 1000.00)
    self.concentration2.setSingleStep(0.01)
    self.concentration2.setFixedWidth(70)
    self.concentration2.setFixedHeight(25)
    self.concentrationUnit2.hide()
    self.concentrationLabel2.hide()
    self.concentration2.hide()

  def setConcentrationUnit(self, pressed):
    if pressed == 'Molar':
      self.concentrationUnit1.setData(CONCENTRATION_UNIT)
      self.concentrationUnit2.hide()
      self.concentrationLabel2.hide()
      self.concentration2.hide()
    elif pressed == 'Mass/Volume':
      self.concentrationUnit1.setData(MASS_UNIT)
      self.concentrationUnit2.setData(VOLUME_UNIT)
      self.concentrationUnit2.show()
      self.concentrationLabel2.show()
      self.concentration2.show()
    elif pressed == 'mol/Volume':
      self.concentrationUnit1.setData(OTHER_UNIT)
      self.concentrationUnit2.setData(VOLUME_UNIT)
      self.concentrationUnit2.show()
      self.concentrationLabel2.show()
      self.concentration2.show()


  def typeComponent(self, pressed): #['Solvent', 'Compound', 'Target', 'inhibitor ', 'Other']

    if pressed == 'Compound':

      referenceSpectraLabel = Label(self.area, text="Reference Spectra", grid=(7, 1), hAlign='l')
      self.referenceSpectra = LineEdit(self.area, grid=(7, 2), hAlign='r' )
      self.referenceSpectra.setText('<Empty>')
      self.referenceSpectra.setFixedWidth(155)
      self.referenceSpectra.setFixedHeight(25)


      self.smileLabel = Label(self.area, text="Smile", grid=(8, 1), hAlign='l')
      self.smile = LineEdit(self.area, grid=(8, 2), hAlign='r' )
      self.smile.setText('<Empty>')
      self.smile.setFixedWidth(155)
      self.smile.setFixedHeight(25)

      self.empiricalFormulaLabel = Label(self.area, text="Empirical Formula", grid=(9, 1), hAlign='l')
      self.empiricalFormula = LineEdit(self.area, grid=(9, 2), hAlign='r' )
      self.empiricalFormula.setText('<Empty>')
      self.empiricalFormula.setFixedWidth(155)
      self.empiricalFormula.setFixedHeight(25)

      self.molecularMassLabel = Label(self.area, text="Molecular Mass", grid=(10, 1), hAlign='l')
      self.molecularMass = LineEdit(self.area, grid=(10, 2), hAlign='r' )
      self.molecularMass.setText('<Empty>')
      self.molecularMass.setFixedWidth(155)
      self.molecularMass.setFixedHeight(25)

    elif pressed == 'Solvent':
      pass

    elif pressed == 'Inhibitor':
      pass

    elif pressed == 'Target':
      if self.smile:
        self.smileLabel.hide()
        self.smile.hide()
        self.empiricalFormulaLabel.hide()
        self.empiricalFormula.hide()
        self.molecularMassLabel.hide()
        self.molecularMass.hide()

    elif pressed == 'Other':
      pass

  def addComponent(self):

    sampleComponent = self.sample.newSampleComponent(name=str(self.nameComponents.text()),
                                                      labeling=str(self.labeling.text()))


