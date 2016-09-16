from PyQt4 import QtGui, QtCore


from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea

import os

class PrintSpectrumDisplayPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(PrintSpectrumDisplayPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    self.setWindowTitle('Print Spectrum Display')

    filePathLabel = Label(self, 'Image Path', grid=(1, 0))
    self.filePathLineEdit = LineEdit(self, grid=(1, 1))
    self.pathButton = Button(self, grid=(1, 2), callback=self._getSpectrumFile, icon='icons/applications-system')
    scrollArea = ScrollArea(self, grid=(2, 0), gridSpan=(2, 2))

    self.project = project
    self.spectrumSelectionWidget = SpectrumDisplaySelectionWidget(scrollArea, project)
    scrollArea.setWidgetResizable(True)
    scrollArea.setWidget(self.spectrumSelectionWidget)

    self.buttonBox = ButtonList(self, grid=(5, 1), callbacks=[self.reject, self.printSpectrum],
                                texts=['Cancel', 'Print Display'], gridSpan=(1, 2))



  def printSpectrum(self):

    spectrumDisplay = self.project.getByPid(self.spectrumSelectionWidget.getDisplayToPrint())
    if self.filePathLineEdit.text():
      self.project._appBase.ui.mainWindow.printToFile(spectrumDisplayOrStrip=spectrumDisplay, filePath=self.filePathLineEdit.text())
      self.accept()
    else:
      showWarning('No path specified', 'File path to save image has not been specified.')
      return

  def _getSpectrumFile(self):
    if os.path.exists('/'.join(self.filePathLineEdit.text().split('/')[:-1])):
      currentSpectrumDirectory = '/'.join(self.filePathLineEdit.text().split('/')[:-1])
    elif self.project._appBase.preferences.general.dataPath:
      currentSpectrumDirectory = self.project._appBase.preferences.general.dataPath
    else:
      currentSpectrumDirectory = os.path.expanduser('~')

    dialog = FileDialog(parent=self, fileMode=FileDialog.AnyFile, text='Print to File', directory=currentSpectrumDirectory,
                          acceptMode=FileDialog.AcceptSave, preferences=self.project._appBase.preferences.general, filter='SVG (*.svg)')
    path = dialog.selectedFile()
    if path:
      self.filePathLineEdit.setText(path)


class SpectrumDisplaySelectionWidget(QtGui.QWidget, Base):

  def __init__(self, parent, project, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    current = project._appBase.current
    # if current.spectrumDisplay:
    #   self.currentSpectrumDisplay = current.spectrumDisplay
    if current.strip:
      self.currentSpectrumDisplay = current.strip.spectrumDisplay
    else:
      self.currentSpectrumDisplay = project.spectrumDisplays[0]
    radioButton = RadioButton(self, text=self.currentSpectrumDisplay.pid, grid=(0, 0))
    self.ii=1
    self.radioButtons = [radioButton]
    self.spectrumDisplayIds = [sd.pid for sd in project.spectrumDisplays if sd is not self.currentSpectrumDisplay]
    radioButton.setChecked(True)

    for spectrumDisplayId in self.spectrumDisplayIds:
      self.addSpectrumDisplay(spectrumDisplayId)

  def addSpectrumDisplay(self, spectrumDisplayId):
    radioButton = RadioButton(self, text=spectrumDisplayId, grid=(self.ii, 0))
    self.radioButtons.append(radioButton)
    self.ii+=1

  def getDisplayToPrint(self):
    for radioButton in self.radioButtons:
      if radioButton.isChecked():
        index = self.radioButtons.index(radioButton)

    if index == 0:
      return self.currentSpectrumDisplay.pid
    else:
      return self.spectrumDisplayIds[index-1]