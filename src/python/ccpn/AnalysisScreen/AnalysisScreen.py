from ccpn.framework.Framework import Framework

applicationName = 'Screen'


class Screen(Framework):
  """Root class for Screen application"""

  def __init__(self, applicationName, applicationVersion, commandLineArguments):
    Framework.__init__(self, applicationName, applicationVersion, commandLineArguments)
    # self.components.add('Screen')




  #########################################    Start setup Menu      #############################################
  def setupMenus( self ):
    super().setupMenus( )

    menuSpec = ('Screen',[
                         ("Pick Peaks "      , self.showPickPeakPopup),
                         ("Generate Mixtures " , self.showMixtureGenerationPopup, [('shortcut', 'cs')]),
                         ("Mixtures Analysis " , self.showSampleAnalysis,         [('shortcut', 'st')]),
                         ("Screening Settings" , self.showScreeningSetup,         [('shortcut', 'pp')]),
                         ("Hit Analysis"       , self.showHitAnalysisModule,      [('shortcut', 'ha')]),
                         ]
                )

    self.addApplicationMenuSpec(menuSpec)

  def showPickPeakPopup(self):
    from ccpn.ui.gui.popups.PickPeaks1DPopup import PickPeak1DPopup
    popup = PickPeak1DPopup(parent=self.ui.mainWindow, project=self.project)
    popup.exec_()
    popup.raise_()
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showSamplePopup()")
    self.project._logger.info("application.showSamplePopup()")

  def showMixtureGenerationPopup(self):
    """
    Displays Sample creation popup.
    """

    from ccpn.AnalysisScreen.popups.MixtureGenerationPopup import MixtureGenerationPopup
    popup = MixtureGenerationPopup(self.ui.mainWindow,  project=self.project)
    popup.exec_()
    popup.raise_()
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showSamplePopup()")
    self.project._logger.info("application.showSamplePopup()")

  def showSampleAnalysis(self, position='bottom', relativeTo=None):
    """
    Displays Sample Analysis Module
    """
    from ccpn.AnalysisScreen.modules.MixtureAnalysis import MixtureAnalysis
    showSa = MixtureAnalysis(self.ui.mainWindow,  project=self.project)
    self.ui.mainWindow.moduleArea.addModule(showSa, position=position, relativeTo=relativeTo)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showSampleAnalysis()")
    # self.project._logger.info("application.showSampleAnalysis()")

  def showScreeningSetup(self, position='bottom', relativeTo=None):
    from ccpn.AnalysisScreen.modules.ScreeningSettings import ScreeningSettings
    showSc = ScreeningSettings(self.ui.mainWindow,  project=self.project)
    self.ui.mainWindow.moduleArea.addModule(showSc, position=position)
    # self.pythonConsole.writeConsoleCommand("application.showScreeningSetup()")
    # self.project._logger.info("application.showScreeningSetup()")

  def showHitAnalysisModule(self, position='top', relativeTo= None):
    from ccpn.AnalysisScreen.modules.ShowScreeningHits import ShowScreeningHits
    self.showScreeningHits = ShowScreeningHits(self.ui.mainWindow,  project=self.project)
    self.ui.mainWindow.moduleArea.addModule(self.showScreeningHits, position, None)
    # spectrumDisplay = self.createSpectrumDisplay(self.project.spectra[0])
    # spectrum only to create a display
    # self.project.strips[0].viewBox.autoRange()
    # self.showScreeningHits._clearDisplayView()
    # self.moduleArea.moveModule(spectrumDisplay.module, position='top', neighbor=self.showScreeningHits)
    # returns a clean display

    # self.pythonConsole.writeConsoleCommand("application.showScreeningHits()")
    # self.project._logger.info("application.showScreeningHits()")
    #########################################    End setup Menus      #############################################
