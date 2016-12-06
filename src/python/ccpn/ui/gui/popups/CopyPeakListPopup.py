from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ButtonList import ButtonList


class CopyPeakListPopup(QtGui.QDialog):
  def __init__(self, parent, application, **kw):
    super(CopyPeakListPopup, self).__init__(parent)

    self.application = application
    self.project = self.application.project

    self._setMainLayout()
    self.setWidgets()
    self.addWidgetsToLayout()

  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Copy PeakList")
    self.mainLayout.setContentsMargins(20, 20, 20, 5)  # L,T,R,B
    self.setFixedWidth(300)
    self.setFixedHeight(130)

  def setWidgets(self):
    self.sourcePeakListLabel = Label(self, 'Source PeakList')
    self.sourcePeakListPullDown = PulldownList(self)
    self._populateSourcePeakListPullDown()

    self.targetSpectraLabel = Label(self, 'Target Spectrum')
    self.targetSpectraPullDown = PulldownList(self)
    self._populateTargetSpectraPullDown()

    self.okCancelButtons = ButtonList(self, texts=['Cancel', ' Ok '],
                                      callbacks=[self.reject, self._okButton],
                                      tipTexts=['Close Popup', 'Copy PeakList'])

  def addWidgetsToLayout(self):
    self.mainLayout.addWidget(self.sourcePeakListLabel, 0,0)
    self.mainLayout.addWidget(self.sourcePeakListPullDown, 0, 1)
    self.mainLayout.addWidget(self.targetSpectraLabel, 1, 0)
    self.mainLayout.addWidget(self.targetSpectraPullDown, 1, 1)
    self.mainLayout.addWidget(self.okCancelButtons, 2, 1)

  def _okButton(self):
      self.sourcePeakList = self.project.getByPid(self.sourcePeakListPullDown.getText())
      self.targetSpectrum = self.project.getByPid(self.targetSpectraPullDown.getText())
      self._copyPeakListToSpectrum()
      self.accept()

  def _copyPeakListToSpectrum(self):
    if self.sourcePeakList is not None:
      if self.targetSpectrum is not None:
        self.sourcePeakList.copyTo(self.targetSpectrum)

  def _populateSourcePeakListPullDown(self):
    sourcePullDownData = []
    if len(self.project.peakLists)>0:
      for pl in self.project.peakLists:
        sourcePullDownData.append(str(pl.pid))
    self.sourcePeakListPullDown.setData(sourcePullDownData)
    self._selectDefaultPeakList()

  def _populateTargetSpectraPullDown(self):
    targetPullDownData = []
    if len(self.project.spectra)>0:
      for sp in self.project.spectra:
        targetPullDownData.append(str(sp.pid))
    self.targetSpectraPullDown.setData(targetPullDownData)
    self._selectDefaultSpectrum()


  def _selectDefaultPeakList(self):
    if self.application.current.peak is not None:
      defaultPeakList = self.application.current.peak.peakList
      self.sourcePeakListPullDown.select(defaultPeakList.pid)
      # print('Selected defaultPeakList: "current.peak.peakList" ',defaultPeakList) #Testing statement to be deleted
      return
    if self.application.current.strip is not None:
      defaultPeakList = self.application.current.strip.spectra[0].peakLists[-1]
      self.sourcePeakListPullDown.select(defaultPeakList.pid)
      # print('Selected defaultPeakList: "current.strip.spectra[0].peakLists[-1]" ', defaultPeakList)  #Testing statement to be deleted
      return
    else:
      defaultPeakList = self.project.spectra[0].peakLists[-1]
      self.sourcePeakListPullDown.select(defaultPeakList.pid)
      # print('Selected defaultPeakList: "self.project.spectra[0].peakLists[-1]" ', defaultPeakList) #Testing statement to be deleted
      return

  def _selectDefaultSpectrum(self):
    if self.application.current.strip is not None:
      defaultSpectrum = self.application.current.strip.spectra[-1]
      self.targetSpectraPullDown.select(defaultSpectrum.pid)
      # print('Selected defaultSpectrum: "current.strip.spectra[-1]" ', defaultSpectrum) #Testing statement to be deleted
      return
    else:
      defaultSpectrum = self.project.spectra[-1]
      self.targetSpectraPullDown.select(defaultSpectrum.pid)
      # print('Selected defaultSpectrum: "self.project.spectra[-1]" ', defaultSpectrum) #Testing statement to be deleted
      return