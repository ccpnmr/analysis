#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:24 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.Spectrum import Spectrum
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList

class CopyPeaks(CcpnDialog):

  def __init__(self, parent=None,  mainWindow=None, title='Copy Peaks to PeakLists', **kw):
    CcpnDialog.__init__(self, parent=parent, setLayout=True, windowTitle=title, size=(300, 500), **kw)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.current = self.application.current
    self.project = mainWindow.project

    self._createWidgets()
    self._registerNotifiers()

  def _createWidgets(self):

    tipText = ' Select peaks and peakLists to be copied over then click copy'

    self.getLayout().setContentsMargins(10,10,10,10)
    row =  0
    self.spectraLabel1 = Label(self, 'Select Origin Spectra', grid=(row, 0), hAlign='l')
    self.spectraLabel2 = Label(self, 'Select Destination Spectra', grid=(row, 1),  hAlign='l')
    row += 1
    self.selectFromPullDown = PulldownList(self, texts=['All'], callback=self._populatePeakWidget, grid=(row, 0))
    self.selectToPullDown = PulldownList(self,texts=['All'], callback=self._populatePeakListsWidget,  grid=(row, 1))
    row += 1
    self.inputPeaksWidgetLabel = Label(self, 'Select Peaks To Copy', grid=(row, 0),  hAlign='l')
    self.outputPeakListsWidgetLabel = Label(self, 'Select Destination PeakLists',  grid=(row, 1),  hAlign='l')
    row += 1
    self.inputPeaksWidget = ListWidget(self, multiSelect= True, callback=None, tipText=tipText,  grid=(row, 0))
    self.inputPeaksListWidget = ListWidget(self, multiSelect= True, callback=None, tipText=tipText,  grid=(row, 1))
    row += 1
    self.copyButtons = ButtonList(self, texts=['Close','Clear All', ' Copy '],
                                  callbacks=[self._closePopup, self.clearSelections, self._copyButton],
                                  tipTexts=['Close','Clear All Selections', tipText],  grid=(row, 1))

    self._populatePeakWidget()
    self._populatePeakListsWidget()
    self._setPullDownData()


  def _setPullDownData(self):
    for spectrum in self.project.spectra:
      self.selectFromPullDown.addItem(text=spectrum.pid, object=spectrum)
      self.selectToPullDown.addItem(text=spectrum.pid, object=spectrum)

  def _populatePeakWidget(self, *args):
    obj = self.selectFromPullDown.getObject()

    if isinstance(obj, Spectrum):
      peaks = []
      for peakList in obj.peakLists:
        peaks.append(peakList.peaks)
      self.inputPeaksWidget.setObjects(*peaks, name='pid')
    else:
      self.inputPeaksWidget.setObjects(self.project.peaks, name='pid')


  def _populatePeakListsWidget(self, *args):

    obj = self.selectToPullDown.getObject()
    if isinstance(obj, Spectrum):
      self.inputPeaksListWidget.setObjects(obj.peakLists, name='pid')
    else:
      self.inputPeaksListWidget.setObjects(self.project.peakLists, name='pid')


    # self.inputPeaksListWidget.setObjects(self.project.peakLists, name='pid')

  def _refreshInputPeaksWidget(self, *args):
    self._populatePeakWidget()

  def _refreshInputPeaksListWidget(self, *args):
    self._populatePeakListsWidget()

  def _selectSpectrum(self, spectrum):
    self.selectFromPullDown.select(spectrum)


  def _copyButton(self):
    peakLists = self.inputPeaksListWidget.getSelectedObjects()
    peaks = self.inputPeaksWidget.getSelectedObjects()
    if len(peaks)>0:
      if len(peakLists) > 0:
        for peak in peaks:
          for peakList in peakLists:
            peak.copyTo(peakList)
    self.project._logger.warn('Peaks copied. Finished')
    self._deregisterNotifiers()


  def _selectPeaks(self, peaks):
    self.inputPeaksWidget.selectObjects(peaks)

  def clearSelections(self):
    self.inputPeaksWidget.clearSelection()
    self.inputPeaksListWidget.clearSelection()

  def _closePopup(self):
    """
    Re-implementation of closeModule function from CcpnModule to unregister notification
    """
    self._deregisterNotifiers()
    self.reject()


  def _registerNotifiers(self):

    self._peakNotifier = Notifier(self.project, [Notifier.DELETE, Notifier.CREATE, Notifier.RENAME], 'Peak', self._refreshInputPeaksWidget)
    self._peakListNotifier = Notifier(self.project, [Notifier.DELETE, Notifier.CREATE, Notifier.RENAME], 'PeakList', self._refreshInputPeaksListWidget)


  def _deregisterNotifiers(self):
    if self._peakNotifier:
      self._peakNotifier.unRegister()
    if self._peakListNotifier:
      self._peakListNotifier.unRegister()
