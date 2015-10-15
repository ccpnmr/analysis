__author__ = 'luca'


import os

from PyQt4 import QtGui, QtCore

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.DateTime import DateTime
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.RadioButton import RadioButton
from ccpncore.gui.TextEditor import TextEditor

from functools import partial


SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']
CONCENTRATION_UNIT = ['mM', 'µM', 'nM', 'pM']
VOLUME_UNIT = ['mL', 'µL', 'nL', 'pL']
MASS_UNIT = ['kg','g','mg', 'µg', 'ng', 'pg']

class SamplePropertiesPopup(QtGui.QDialog, Base):
  def __init__(self, sample, item, parent=None, project=None, **kw):
    super(SamplePropertiesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.project = project
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
    self.sampleName = LineEdit(self.areaContents, grid=(1, 2), hAlign='r' )
    self.sampleName.setStyleSheet(""" background-color:  white""")
    self.sampleName.setFixedWidth(195)
    self.sampleName.setFixedHeight(25)
    self.sampleName.setText(sample.name)
    self.sampleName.editingFinished.connect(self.changeSampleName)

    # Sample Components
    SampleComponents = Label(self.areaContents, text="Sample Components ", grid=(2, 1), hAlign='l')
    spPid = [sp.pid for sp in sample.spectra]
    self.spInMixture = PulldownList(self.areaContents, grid=(2, 2), hAlign='c' )
    self.spInMixture.setStyleSheet(""" background-color:  white""")
    self.spInMixture.setFixedWidth(195)
    self.spInMixture.setFixedHeight(25)
    self.spInMixture.setData(spPid)
    self.spInMixture.setEditable(True)

#   #Sample Spectra
    sampleSpectra = Label(self.areaContents, text="Sample Spectra ", vAlign='t', hAlign='l', grid=(3, 1))
    self.sampleExperimentType = PulldownList(self.areaContents, hAlign='c', grid=(3, 2))#, vAlign='t'
    self.sampleExperimentType.addItems(spPid)
    self.sampleExperimentType.setStyleSheet(""" background-color:  white""")
    self.sampleExperimentType.setFixedWidth(195)
    self.sampleExperimentType.setFixedHeight(25)

#   #Sample  Unit
    sampleUnitLabel = Label(self.areaContents, text="Sample Unit ", grid=(4, 1), hAlign='l')

    self.sampleVolumeUnitRadio1 = RadioButton(self.areaContents,text="Vol", textColor='White',
                                               grid=(4, 2), hAlign='l' )
    self.sampleVolumeUnitRadio1.toggled.connect(self.sampleUnitChangedInVolume)

    self.sampleMassUnitRadio3 = RadioButton(self.areaContents,text="Mass", textColor='White',
                                               grid=(4, 2), hAlign='r' )
    self.sampleMassUnitRadio3.toggled.connect(self.sampleUnitChangedInMass)

    self.sampleConcentrationUnitRadio2 = RadioButton(self.areaContents, text="[C]", textColor='White',
                                                     grid=(4, 2), hAlign='c' )
    self.sampleConcentrationUnitRadio2.setChecked(True)
    self.sampleConcentrationUnitRadio2.toggled.connect(self.sampleUnitChangedInConcentration)


#   #Sample Amount Unit
    sampleAmountUnitLabel = Label(self.areaContents, text="Sample Amount Unit ", grid=(5, 1), hAlign='l')
    self.sampleAmountUnit = PulldownList(self.areaContents, grid=(5, 2), hAlign='c' )
    self.sampleAmountUnit.setData(CONCENTRATION_UNIT)
    self.sampleAmountUnit.setFixedWidth(195)
    self.sampleAmountUnit.setFixedHeight(25)
    self.sampleAmountUnit.setStyleSheet(""" background-color:  white""")

    self.sampleAmountUnit.activated[str].connect(self.sampleAmountUnitChanged)


#    # Sample Amount
    sampleAmountLabel = Label(self.areaContents, text="Sample Amount ", grid=(6, 1), hAlign='l')
    self.sampleAmount = DoubleSpinbox(self.areaContents, grid=(6, 2), hAlign='r' )
    self.sampleAmount.setRange(0.00, 1000.00)
    self.sampleAmount.setSingleStep(0.01)
    self.sampleAmount.setStyleSheet(""" background-color:  white""")
    self.sampleAmount.setFixedWidth(195)
    self.sampleAmount.setFixedHeight(25)
    # self.sampleAmount.setValue(float(500.00))
    self.sampleAmount.valueChanged.connect(self.sampleAmountChanged)

    # Sample pH
    samplepHLabel = Label(self.areaContents, text="Sample pH ", grid=(7, 1), hAlign='l')
    self.samplepH = DoubleSpinbox(self.areaContents, grid=(7, 2), hAlign='r' )
    self.samplepH.setRange(0.00, 14.00)
    self.samplepH.setSingleStep(0.01)
    self.samplepH.valueChanged.connect(self.samplepHchanged)
    self.samplepH.setStyleSheet(""" background-color:  white""")
    self.samplepH.setFixedWidth(195)
    self.samplepH.setFixedHeight(25)


    # Sample Date
    sampleDate = Label(self.areaContents, text="Sample Creation Date ", grid=(8, 1), hAlign='l')
    self.sampleDate = DateTime(self.areaContents, grid=(8, 2), hAlign='r')
    self.sampleDate.setStyleSheet(""" background-color:  white""")
    self.sampleDate.setFixedWidth(195)
    self.sampleDate.setFixedHeight(25)
    if sample.creationDate is None:
     setToday = QtCore.QDate.currentDate()
     self.sampleDate.setDate(setToday)
    # self.sampleDate.setText(sample.creationDate)

    # Sample Plate Identifier
    samplePlateIdentifierLabel = Label(self.areaContents, text="Sample Plate Identifier ", grid=(9, 1), hAlign='l')
    self.plateIdentifier = LineEdit(self.areaContents, grid=(9, 2), hAlign='r' )
    self.plateIdentifier.setStyleSheet(""" background-color:  white""")
    self.plateIdentifier.setFixedWidth(195)
    self.plateIdentifier.setFixedHeight(25)
    self.plateIdentifier.setText(sample.plateIdentifier)
    self.plateIdentifier.editingFinished.connect(self.plateIdentifierChanged)

    # Sample Row Number
    samplerowNumberLabel = Label(self.areaContents, text="Sample Row Number ", grid=(10, 1), hAlign='l')
    self.rowNumber = LineEdit(self.areaContents, grid=(10, 2), hAlign='r' )
    self.rowNumber.setStyleSheet(""" background-color:  white""")
    self.rowNumber.setFixedWidth(195)
    self.rowNumber.setFixedHeight(25)
    if sample.rowNumber is not None:
      self.rowNumber.setText(sample.rowNumber)
    # else:
    #   self.rowNumber.setText(str('<Insert 0 + Row Num. Eg. 01 >'))
    self.rowNumber.editingFinished.connect(self.columnNumberChanged)
    self.rowNumber.editingFinished.connect(self.rowNumberChanged)

    # Sample Column Number
    sampleColumnNumberLabel = Label(self.areaContents, text="Sample Column Number ", grid=(11, 1), hAlign='l')
    self.columnNumber = LineEdit(self.areaContents, grid=(11, 2), hAlign='r' )
    self.columnNumber.setStyleSheet(""" background-color:  white""")
    self.columnNumber.setFixedWidth(195)
    self.columnNumber.setFixedHeight(25)
    if sample.columnNumber is not None:
      self.columnNumber.setText(sample.columnNumber)
    # else:
    #   self.columnNumber.setText(str('< Insert 0 + Col Num. Eg. 01 >'))
    self.rowNumber.editingFinished.connect(self.columnNumberChanged)

    # Sample Comment
    sampleCommentLabel = Label(self.areaContents, text="Comment ", grid=(12, 1), hAlign='l')
    self.comment = TextEditor(self.areaContents, grid=(12, 2), hAlign='l' )
    self.comment.setStyleSheet(""" background-color: white""")
    self.comment.setFixedWidth(200)
    self.comment.setFixedHeight(50)
    self.comment.setText(sample.comment)
    self.comment.textChanged.connect(self.commentChanged)


    # Only to align and center all nicely
    labelAllignLeft = Label(self.areaContents, text="", grid=(1, 0), hAlign='l')
    labelAllignRight = Label(self.areaContents, text="", grid=(1, 3), hAlign='l')


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