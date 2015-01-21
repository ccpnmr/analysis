__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpncore.gui.Icon import Icon
import os

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpnmrcore.modules.GuiStrip1d import GuiStrip1d
from ccpnmrcore.modules.spectrumItems.GuiSpectrumView1d import GuiSpectrumView1d

from ccpncore.gui.Label import Label
from ccpncore.gui.VerticalLabel import VerticalLabel


class GuiStripDisplay1d(GuiSpectrumDisplay):

  def __init__(self, dockArea, apiSpectrumDisplay1d):
    if not apiSpectrumDisplay1d.strips:
      apiSpectrumDisplay1d.newStrip1d()
    self.apiStripDisplay1d = apiSpectrumDisplay1d
    GuiSpectrumDisplay.__init__(self, dockArea, apiSpectrumDisplay1d)
    self.fillToolBar()
    self.addSpinSystemSideLabel()

  def addSpectrum(self, spectrum):

    apiDataSource = spectrum._wrappedData
    apiSpectrumView = self.apiSpectrumDisplay.findFirstSpectrumView(dataSource=apiDataSource)

    # guiSpectrumView = GuiSpectrumView1d(self, apiStripDisplay1d)
    # # guiSpectrumView.name = apiSpectrumDislay1d.name
    # for guiStrip in self.guiStrips:
    #   guiStrip.addSpectrum(apiStripDisplay1d, guiSpectrumView)

    if not apiSpectrumView:
      ##axisCodes=spectrum.axisCodes
      axisCodes = ('H', 'intensity')  # TEMP
      apiSpectrumView = self.apiSpectrumDisplay.newSpectrumView(dataSourceSerial=apiDataSource.serial,
                          experimentName=apiDataSource.experiment.name, axisCodes=axisCodes)
    guiSpectrumView = GuiSpectrumView1d(self, apiSpectrumView)

    for guiStrip in self.guiStrips:
      guiStrip.addSpectrum(spectrum, guiSpectrumView)

  def fillToolBar(self):
    GuiSpectrumDisplay.fillToolBar(self)
    autoScaleAction = self.spectrumUtilToolBar.addAction("AutoScale", self.zoomYAll)
    autoScaleActionIcon = Icon('icons/zoom-fit-best')
    # autoScaleActionIcon.actualSize(QtCore.QSize(10, 10))
    autoScaleAction.setIcon(autoScaleActionIcon)
    # autoScaleAction.setText("AutoScale")
    fullZoomAction = self.spectrumUtilToolBar.addAction("Full", self.zoomXAll)
    fullZoomIcon = Icon('icons/zoom-full')
    fullZoomAction.setIcon(fullZoomIcon)
    storeZoomAction = self.spectrumUtilToolBar.addAction("Store Zoom", self.storeZoom)
    storeZoomIcon = Icon('icons/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = self.spectrumUtilToolBar.addAction("Restore Zoom", self.restoreZoom)
    restoreZoomIcon = Icon('icons/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')

  def addStrip(self):

    apiStrip = self.apiSpectrumDisplay.newStrip1d()
    print('HERE221')
    n = len(self.apiSpectrumDisplay.strips) - 1
    guiStrip = GuiStrip1d(self.stripFrame, apiStrip, grid=(1, n), stretch=(0, 1))
    if n > 0:
      prevGuiStrip = self.guiStrips[n-1]
      prevGuiStrip.axes['right']['item'].hide()
      guiStrip.setYLink(prevGuiStrip)

    print('HERE222')

    #self.stripCount+=1

      # self.strips[-1].axes['right']['item'].tickLength = 5000
    # self.grid = pg.GridItem()
    # newPane.addItem(self.grid)
    """
    self.spectrumWidgetLayout.addWidget(newPane, 0, self.stripCount)
    widget = self.spectrumWidgetLayout
    if len(self.strips) > 0:
      print(len(self.strips))
      self.strips[-1].axes['right']['item'].hide()
      # self.strips[-1].axes['right']['item'].orientation = 'left'
      newPane.setYLink(self.strips[-1])
      for item in self.strips[0].spectrumItems:
        newPane.addSpectrum(item.spectrum)
        self.addPlaneToolbar(item, widget, newPane)
      """

  def addSpinSystemSideLabel(self):
    spinSystemSideLabel = VerticalLabel(self, text='A.147.ALA.HA')
    # spinSystemSideLabel.setText()
    self.addWidget(spinSystemSideLabel, 1, 0, 1, 1)
    # print(spinSystemSideLabel.paintEvent())
    spinSystemSideLabel.setFixedWidth(30)
