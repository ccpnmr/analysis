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

from PyQt4 import QtCore, QtGui

from ccpn import Project
from ccpn import Spectrum

from ccpncore.api.ccp.nmr.Nmr import DataSource as ApiDataSource

from ccpncore.util.Pid import Pid
from ccpncore.util.Types import Sequence

from ccpncore.gui.Icon import Icon

from application.core.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from application.core.modules.GuiStrip1d import GuiStrip1d

from ccpncore.gui.VerticalLabel import VerticalLabel

from ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView


class GuiStripDisplay1d(GuiSpectrumDisplay):

  def __init__(self):
    # if not apiSpectrumDisplay1d.strips:
    #   apiSpectrumDisplay1d.newStrip1d()

    GuiSpectrumDisplay.__init__(self)
    self.fillToolBar()
    # self.addSpinSystemSideLabel()
    self.setAcceptDrops(True)
    self.isGrouped = False
    self.spectrumActionDict = {}
    # below not needed in 1D???
    #self.activePeakItemDict = {}  # maps peakListView to apiPeak to peakItem for peaks which are being displayed
    # cannot use (wrapper) peak as key because project._data2Obj dict invalidates mapping before deleted callback is called
    # TBD: this might change so that we can use wrapper peak (which would make nicer code in showPeaks and deletedPeak below)
    #self.inactivePeakItems = set() # contains unused peakItems
    #self.inactivePeakItemDict = {}  # maps peakListView to apiPeak to peakItem for peaks which are not being displayed

  # def addSpectrum(self, spectrum):
  #
  #   apiDataSource = spectrum._wrappedData
  #   apiSpectrumView = self._apiSpectrumDisplay.findFirstSpectrumView(dataSource=apiDataSource)
  #
  #   #axisCodes = spectrum.axisCodes
  #   axisCodes = LibSpectrum.getAxisCodes(spectrum)
  #   axisCodes = axisCodes + ('intensity',)
  #   if axisCodes != self._apiSpectrumDisplay.axisCodes:
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
  #     apiSpectrumView = self._apiSpectrumDisplay.newSpectrumView(spectrumName=apiDataSource.name,
  #                           dimensionOrdering=dimensionOrdering)
  #   guiSpectrumView = GuiSpectrumView1d(self, apiSpectrumView)
  #
  #   for guiStrip in self.guiStrips:
  #     guiStrip.addSpectrum(spectrum, guiSpectrumView)

  def fillToolBar(self):
    """
    Adds specific icons for 1d spectra to the spectrum utility toolbar.
    """
    GuiSpectrumDisplay.fillToolBar(self)
    
    spectrumUtilToolBar = self.spectrumUtilToolBar
    
    autoScaleAction = spectrumUtilToolBar.addAction("AutoScale", self.zoomYAll)
    autoScaleActionIcon = Icon('iconsNew/zoom-best-fit')
    # autoScaleActionIcon.actualSize(QtCore.QSize(10, 10))
    autoScaleAction.setIcon(autoScaleActionIcon)
    # autoScaleAction.setText("AutoScale")
    fullZoomAction = spectrumUtilToolBar.addAction("Full", self.zoomXAll)
    fullZoomIcon = Icon('iconsNew/zoom-full')
    fullZoomAction.setIcon(fullZoomIcon)
    storeZoomAction = spectrumUtilToolBar.addAction("Store Zoom", self.storeZoom)
    storeZoomIcon = Icon('iconsNew/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = spectrumUtilToolBar.addAction("Restore Zoom", self.restoreZoom)
    restoreZoomIcon = Icon('iconsNew/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')

  # def addStrip(self):
  #
  #   apiStrip = self._apiSpectrumDisplay.newStrip1d()
  #   n = len(self._apiSpectrumDisplay.strips) - 1
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


  def processSpectra(self, pids:Sequence[str], event):
    """Display spectra defined by list of Pid strings"""
    for ss in pids:
      print('processing Spectrum', ss)
    print(self.parent())

  # def addSpinSystemSideLabel(self):
  #   dock = self.dock
  #   spinSystemSideLabel = VerticalLabel(dock, text=None)
  #   # spinSystemSideLabel.setText()
  #   dock.addWidget(spinSystemSideLabel, 1, 0, 1, 1)
  #   # print(spinSystemSideLabel.paintEvent())
  #   spinSystemSideLabel.setFixedWidth(30)

  def _updatePlotColour(self, spectrum):
    apiDataSource = spectrum._wrappedData
    action = self.spectrumActionDict.get(apiDataSource)
    if action:
      for strip in self.strips:
        for spectrumView in strip.spectrumViews:
          if spectrumView.spectrum is spectrum:
            spectrumView.plot.setPen(apiDataSource.sliceColour)
  
  def _deletedPeak(self, apiPeak):
    pass  # does anything need doing??
    
def _createdSpectrumView(project:Project, apiSpectrumView:ApiSpectrumView):
  """Set up SpectrumDisplay when new SpectrumView is created - for notifiers"""

  getDataObj = project._data2Obj.get
  spectrumDisplay = getDataObj(apiSpectrumView.spectrumDisplay)
  if not isinstance(spectrumDisplay, GuiStripDisplay1d):
    return

  apiDataSource = apiSpectrumView.dataSource
  action = spectrumDisplay.spectrumActionDict.get(apiDataSource)  # should always be None
  if not action:
    # add toolbar action (button)
    if len(apiDataSource.name) <= 12:
      spectrumName = apiDataSource.name
    elif len(apiDataSource.name) > 12:
      spectrumName = apiDataSource.name[:12]+'.....'
    action = spectrumDisplay.spectrumToolBar.addAction(spectrumName)
    action.setCheckable(True)
    action.setChecked(True)
    action.setToolTip(apiDataSource.name)
    widget = spectrumDisplay.spectrumToolBar.widgetForAction(action)
    widget.setIconSize(QtCore.QSize(120, 10))
    widget.setFixedSize(100, 30)
    widget.spectrumView = apiSpectrumView
    spectrumDisplay.spectrumActionDict[apiDataSource] = action
    spectrumDisplay._setActionIconColour(apiDataSource)

  return action

def _createdStripSpectrumView(project:Project, apiStripSpectrumView:ApiStripSpectrumView):
  """Set up SpectrumDisplay when new StripSpectrumView is created - for notifiers"""

  apiSpectrumView = apiStripSpectrumView.spectrumView
  getDataObj = project._data2Obj.get
  spectrumDisplay = getDataObj(apiSpectrumView.spectrumDisplay)
  if not isinstance(spectrumDisplay, GuiStripDisplay1d):
    return

  apiDataSource = apiSpectrumView.dataSource
  action = _createdSpectrumView(project, apiSpectrumView) # _createdStripSpectrumView is called before _createdSpectrumView so need this duplicate call here
  spectrumView = getDataObj(apiStripSpectrumView)
  action.toggled.connect(spectrumView.plot.setVisible)

  ##strip = spectrumView.strip
  ##for apiPeakList in apiDataSource.sortedPeakLists():
  ##  strip.showPeaks(getDataObj(apiPeakList))

def _deletedSpectrumView(project:Project, apiSpectrumView:ApiSpectrumView):
  """tear down SpectrumDisplay when new SpectrumView is deleted - for notifiers"""
  spectrumDisplay = project._data2Obj[apiSpectrumView.spectrumDisplay]
  if not isinstance(spectrumDisplay, GuiStripDisplay1d):
    return

  apiDataSource = apiSpectrumView.dataSource

  # remove toolbar action (button)
  action = spectrumDisplay.spectrumActionDict.get(apiDataSource)  # should always be not None
  if action:
    spectrumDisplay.spectrumToolBar.removeAction(action)
    del spectrumDisplay.spectrumActionDict[apiDataSource]

Project._setupNotifier(_createdSpectrumView, ApiSpectrumView, 'postInit')
Project._setupNotifier(_deletedSpectrumView, ApiSpectrumView, 'preDelete')
Project._setupNotifier(_createdStripSpectrumView, ApiStripSpectrumView, 'postInit')

def _updatePlotColour(project:Project, apiDataSource:ApiDataSource):

    
  getDataObj = project._data2Obj.get
  spectrum = getDataObj(apiDataSource)
  for task in project.tasks:
    if task.status == 'active':
      for spectrumDisplay in task.spectrumDisplays:
        if isinstance(spectrumDisplay, GuiStripDisplay1d):
          spectrumDisplay._updatePlotColour(spectrum)

Project._setupNotifier(_updatePlotColour, ApiDataSource, 'setSliceColour')


# Unnecessary - dimensionOrdering is frozen. RHF
# def _changedDimensionOrderingSpectrumView(project:Project, apiSpectrumView:ApiSpectrumView):
#
#   for apiStrip in apiSpectrumView.strips:
#     strip = project._data2Obj[apiStrip]
#     if isinstance(strip, GuiStrip1d):
#       strip.setZWidgets()
#
# Project._setupNotifier(_changedDimensionOrderingSpectrumView, ApiSpectrumView, 'dimensionOrdering')

# NBNB notifiers are same for 1D and nD and are written in GuiStripDisplayNd