"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

from ccpncore.gui.Icon import Icon

from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay

from ccpncore.gui.VerticalLabel import VerticalLabel


class GuiStripDisplay1d(GuiSpectrumDisplay):

  def __init__(self):
    # if not apiSpectrumDisplay1d.strips:
    #   apiSpectrumDisplay1d.newStrip1d()

    GuiSpectrumDisplay.__init__(self)
    self.fillToolBar()
    self.addSpinSystemSideLabel()
    self.setAcceptDrops(True)

  # def addSpectrum(self, spectrum):
  #
  #   apiDataSource = spectrum._wrappedData
  #   apiSpectrumView = self.apiSpectrumDisplay.findFirstSpectrumView(dataSource=apiDataSource)
  #
  #   #axisCodes = spectrum.axisCodes
  #   axisCodes = LibSpectrum.getAxisCodes(spectrum)
  #   axisCodes = axisCodes + ('intensity',)
  #   if axisCodes != self.apiSpectrumDisplay.axisCodes:
  #     raise Exception('Cannot overlay that spectrum on this display')
  #
  #   # guiSpectrumView = GuiSpectrumView1d(self, apiStripDisplay1d)
  #   # # guiSpectrumView.name = apiSpectrumDislay1d.name
  #   # for guiStrip in self.guiStrips:
  #   #   guiStrip.addSpectrum(apiStripDisplay1d, guiSpectrumView)
  #
  #   if not apiSpectrumView:
  #     ##axisCodes=spectrum.axisCodes
  #     dimensionOrdering = (1, 0) # 0 because that is the intensity axis so gets mapped to nothing in the spectrum
  #     apiSpectrumView = self.apiSpectrumDisplay.newSpectrumView(spectrumName=apiDataSource.name,
  #                           dimensionOrdering=dimensionOrdering)
  #   guiSpectrumView = GuiSpectrumView1d(self, apiSpectrumView)
  #
  #   for guiStrip in self.guiStrips:
  #     guiStrip.addSpectrum(spectrum, guiSpectrumView)

  def fillToolBar(self):
    GuiSpectrumDisplay.fillToolBar(self)
    
    spectrumUtilToolBar = self.spectrumUtilToolBar
    
    autoScaleAction = spectrumUtilToolBar.addAction("AutoScale", self.zoomYAll)
    autoScaleActionIcon = Icon('icons/zoom-fit-best')
    # autoScaleActionIcon.actualSize(QtCore.QSize(10, 10))
    autoScaleAction.setIcon(autoScaleActionIcon)
    # autoScaleAction.setText("AutoScale")
    fullZoomAction = spectrumUtilToolBar.addAction("Full", self.zoomXAll)
    fullZoomIcon = Icon('icons/zoom-full')
    fullZoomAction.setIcon(fullZoomIcon)
    storeZoomAction = spectrumUtilToolBar.addAction("Store Zoom", self.storeZoom)
    storeZoomIcon = Icon('icons/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = spectrumUtilToolBar.addAction("Restore Zoom", self.restoreZoom)
    restoreZoomIcon = Icon('icons/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')

  # def addStrip(self):
  #
  #   apiStrip = self.apiSpectrumDisplay.newStrip1d()
  #   n = len(self.apiSpectrumDisplay.strips) - 1
  #   guiStrip = GuiStrip1d(self.stripFrame, apiStrip, grid=(1, n), stretch=(0, 1))
  #   if n > 0:
  #     prevGuiStrip = self.guiStrips[n-1]
  #     prevGuiStrip.axes['right']['item'].hide()
  #     guiStrip.setYLink(prevGuiStrip)
  #

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

  # def addSpinSystemSideLabel(self):
  #   dock = self.dock
  #   # spinSystemSideLabel = VerticalLabel(dock, text=None)
  #   # spinSystemSideLabel.setText()
  #   dock.addWidget(spinSystemSideLabel, 1, 0, 1, 1)
  #   # print(spinSystemSideLabel.paintEvent())
  #   spinSystemSideLabel.setFixedWidth(30)
