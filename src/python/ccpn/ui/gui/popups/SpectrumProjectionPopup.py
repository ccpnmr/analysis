from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList

import os

class SpectrumProjectionPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(SpectrumProjectionPopup, self).__init__(parent)
    Base.__init__(self, **kw)

    self.setWindowTitle('Make Spectrum Projection')
    projectionMethods = ('max', 'sum', 'sum above noise')
    self.project = project
    spectrumLabel = Label(self, 'Spectrum to project', grid=(0, 0))
    self.spectrumPulldown = PulldownList(self, grid=(0, 1), callback=self.setAxisPulldown, gridSpan=(1, 2))
    self.spectrumPulldown.setData([spectrum.pid for spectrum in project.spectra])
    filePathLabel = Label(self, 'New Spectrum Path', grid=(1, 0))
    self.filePathLineEdit = LineEdit(self, grid=(1, 1))
    self.pathButton = Button(self, grid=(1, 2), callback=self._getSpectrumFile, icon='icons/applications-system')
    axisLabel = Label(self, 'Projection axis', grid=(2, 0))
    self.axisPulldown = PulldownList(self, grid=(2, 1), gridSpan=(1, 2))
    self.axisPulldown.setData(project.spectra[0].axisCodes)
    methodLabel = Label(self, 'Projection Method', grid=(4, 0))
    self.methodPulldown = PulldownList(self, grid=(4, 1), gridSpan=(1, 2))
    self.methodPulldown.setData(projectionMethods)
    self.buttonBox = ButtonList(self, grid=(5, 1), callbacks=[self.reject, self.makeProjection],
                                texts=['Cancel', 'Make Projection'], gridSpan=(1, 2))

    self.setAxisPulldown(self.spectrumPulldown.currentText())

  def setAxisPulldown(self, spectrumPid):
    spectrum = self.project.getByPid(spectrumPid)
    axisCodes = self.project.getByPid(spectrumPid).axisCodes
    path = '/'.join(spectrum.filePath.split('/')[:-1])+'/'+spectrum.name+'-proj.ft2'
    self.filePathLineEdit.setText(path)
    self.axisPulldown.setData(axisCodes)



  def makeProjection(self):
    spectrum = self.project.getByPid(self.spectrumPulldown.currentText())
    projectionAxisCode = self.axisPulldown.currentText()
    filePath = self.filePathLineEdit.text()
    method = self.methodPulldown.currentText()
    axisIndices = [spectrum.axisCodes.index(x) for x in spectrum.axisCodes]
    axisCodeIndex = spectrum.axisCodes.index(projectionAxisCode)
    axisIndices.remove(axisCodeIndex)
    xDim, yDim = axisIndices
    spectrum.projectedToFile(path=filePath, xDim=xDim+1, yDim=yDim+1, method=method)
    self.project.loadData(filePath)
    self.accept()

  def _getSpectrumFile(self):
    if os.path.exists('/'.join(self.filePathLineEdit.text().split('/')[:-1])):
      currentSpectrumDirectory = '/'.join(self.filePathLineEdit.text().split('/')[:-1])
    elif self.project._appBase.preferences.general.dataPath:
      currentSpectrumDirectory = self.project._appBase.preferences.general.dataPath
    else:
      currentSpectrumDirectory = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Projection File', directory=currentSpectrumDirectory,
                        fileMode=0, acceptMode=1,
                        preferences=self.project._appBase.preferences.general)
    directory = dialog.selectedFiles()
    if len(directory) > 0:
      self.filePathLineEdit.setText(directory[0])