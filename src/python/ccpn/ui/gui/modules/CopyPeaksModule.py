from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget


class CopyPeaksModule(CcpnModule):
  def __init__(self, project,  **kw):
    super(CopyPeaksModule, self)
    CcpnModule.__init__(self, name='Copy Peaks to PeakLists')
    self.application = QtCore.QCoreApplication.instance()._ccpnApplication
    self.project = project

    self._setMainLayout()
    self._createWidgets()
    self._addWidgetsToMainLayout()

    self.__registerNotifiers()

  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule to unregister notification
    """
    self.__deregisterNotifiers()
    self.close()

  def __registerNotifiers(self):
    self.project.registerNotifier('Peak', 'create', self._refreshInputPeaksWidget, onceOnly=True)
    self.project.registerNotifier('Peak', 'rename', self._refreshInputPeaksWidget, onceOnly=True)
    self.project.registerNotifier('Peak', 'delete', self._refreshInputPeaksWidget, onceOnly=True)
    self.project.registerNotifier('PeakList', 'create', self._refreshInputPeaksListWidget, onceOnly=True)
    self.project.registerNotifier('PeakList', 'rename', self._refreshInputPeaksListWidget, onceOnly=True)
    self.project.registerNotifier('PeakList', 'delete', self._refreshInputPeaksListWidget, onceOnly=True)
    self.application.current.registerNotify(self._selectCurrentPeaks, 'peaks')

  def __deregisterNotifiers(self):
    self.project.unRegisterNotifier('Peak', 'create', self._refreshInputPeaksWidget)
    self.project.unRegisterNotifier('Peak', 'rename', self._refreshInputPeaksWidget)
    self.project.unRegisterNotifier('Peak', 'delete', self._refreshInputPeaksWidget)
    self.project.unRegisterNotifier('PeakList', 'create', self._refreshInputPeaksListWidget)
    self.project.unRegisterNotifier('PeakList', 'rename', self._refreshInputPeaksListWidget)
    self.project.unRegisterNotifier('PeakList', 'delete', self._refreshInputPeaksListWidget)
    self.application.current.unRegisterNotify(self._selectCurrentPeaks, 'peaks')

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0)

  def _addWidgetsToMainLayout(self):
    self.mainLayout.addWidget(self.inputPeaksWidgetLabel, 0,0)
    self.mainLayout.addWidget(self.inputPeaksWidget, 1, 0)
    self.mainLayout.addWidget(self.outputPeakListsWidgetLabel, 0, 1)
    self.mainLayout.addWidget(self.inputPeaksListWidget, 1, 1)
    self.mainLayout.addWidget(self.copyButtons, 2, 1)

  def _createWidgets(self):
    self.inputPeaksWidgetLabel = Label(self, 'Select Peaks')
    self.inputPeaksWidget = ListWidget(self, multiSelect= True, callback=None)


    self.outputPeakListsWidgetLabel = Label(self, 'Select PeakLists')
    self.inputPeaksListWidget = ListWidget(self, multiSelect= True, callback=None)

    self.copyButtons = ButtonList(self, texts=['Clear All', ' Copy '],
                                  callbacks=[self.clearSelections, self._copyButton],
                                  tipTexts=['Clear All Selections', 'Copy Peaks'])

    self.populatePeakWidget()
    self.populatePeakListsWidget()

  def populatePeakWidget(self):
    self.inputPeaksWidget.setObjects(self.project.peaks, name='pid')

  def populatePeakListsWidget(self):
    self.inputPeaksListWidget.setObjects(self.project.peakLists, name='pid')

  def _refreshInputPeaksWidget(self, *args):
    self.populatePeakWidget()

  def _refreshInputPeaksListWidget(self, *args):
    self.populatePeakListsWidget()


  def _copyButton(self):
      peakLists = self.inputPeaksListWidget.getSelectedObjects()
      peaks = self.inputPeaksWidget.getSelectedObjects()
      if len(peaks)>0:
        if len(peakLists) > 0:
          for peak in peaks:
            for peakList in peakLists:
              peak.copyTo(peakList)
      self.project._logger.warn('Peaks copied. Finished')

  def _selectCurrentPeaks(self, peaks):

    if len(peaks) >0:
      self.inputPeaksWidget.selectObjects(peaks)


  def clearSelections(self):
    self.inputPeaksWidget.clearSelection()
    self.inputPeaksListWidget.clearSelection()

