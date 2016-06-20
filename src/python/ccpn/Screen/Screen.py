from ccpn.framework.lib.SvnRevision import applicationVersion
from ccpn.framework.Framework import defineProgramArguments, Framework

applicationName = 'Screen'


class Screen(Framework):
  """Root class for Screen application"""

  def __init__(self, applicationName, applicationVersion, commandLineArguments):
    Framework.__init__(self, applicationName, applicationVersion, commandLineArguments)
    self.components.add('Screen')



  #########################################    Start setup Menu      #############################################
  def setupMenus( self ):
    super().setupMenus( )

    menuSpec = ('Screen',[
                         ("Lookup Setup "      , self.showLookupSetupPopup ),
                         ("Generate Mixtures " , self.showMixtureGenerationPopup, [('shortcut', 'cs')]),
                         ("Mixtures Analysis " , self.showSampleAnalysis,         [('shortcut', 'st')]),
                         ("Screening Settings" , self.showScreeningSetup,         [('shortcut', 'pp')]),
                         ("Hit Analysis"       , self.showHitAnalysisModule,      [('shortcut', 'ha')]),
                         ]
                )

    self.addApplicationMenuSpec(menuSpec)

  def showLookupSetupPopup(self):
    from ccpn.Screen.popups.LookupSetupPopup import LookupSetupPopup
    popup = LookupSetupPopup(parent=self.ui.mainWindow, project=self.project)
    popup.exec_()
    popup.raise_()
    self.pythonConsole.writeConsoleCommand("application.showSamplePopup()")
    self.project._logger.info("application.showSamplePopup()")

  def showMixtureGenerationPopup(self):
    """
    Displays Sample creation popup.
    """

    from ccpn.Screen.popups.MixtureGenerationPopup import MixtureGenerationPopup
    popup = MixtureGenerationPopup(self.ui.mainWindow,  project=self.project)
    popup.exec_()
    popup.raise_()
    self.pythonConsole.writeConsoleCommand("application.showSamplePopup()")
    self.project._logger.info("application.showSamplePopup()")

  def showSampleAnalysis(self, position='bottom', relativeTo=None):
    """
    Displays Sample Analysis Module
    """
    from ccpn.Screen.modules.MixtureAnalysis import MixtureAnalysis
    showSa = MixtureAnalysis(self.ui.mainWindow,  project=self.project)
    self.ui.mainWindow.moduleArea.addModule(showSa, position=position, relativeTo=relativeTo)
    self.pythonConsole.writeConsoleCommand("application.showSampleAnalysis()")
    self.project._logger.info("application.showSampleAnalysis()")

  def showScreeningSetup(self, position='bottom', relativeTo=None):
    from ccpn.Screen.modules.ScreeningSettings import ScreeningSettings
    showSc = ScreeningSettings(self.ui.mainWindow,  project=self.project)
    self.ui.mainWindow.moduleArea.addModule(showSc, position=position)
    self.pythonConsole.writeConsoleCommand("application.showScreeningSetup()")
    self.project._logger.info("application.showScreeningSetup()")

  def showHitAnalysisModule(self, position='top', relativeTo= None):
    from ccpn.Screen.modules.ShowScreeningHits import ShowScreeningHits
    self.showScreeningHits = ShowScreeningHits(self.ui.mainWindow,  project=self.project)
    self.ui.mainWindow.moduleArea.addModule(self.showScreeningHits, position, None)
    # spectrumDisplay = self.createSpectrumDisplay(self.project.spectra[0])
    # spectrum only to create a display
    # self.project.strips[0].viewBox.autoRange()
    # self.showScreeningHits._clearDisplayView()
    # self.moduleArea.moveModule(spectrumDisplay.module, position='top', neighbor=self.showScreeningHits)
    # returns a clean display

    self.pythonConsole.writeConsoleCommand("application.showScreeningHits()")
    self.project._logger.info("application.showScreeningHits()")
    #########################################    End setup Menus      #############################################
if __name__ == '__main__':

  # argument parser
  parser = defineProgramArguments()

  # add any additional commandline argument here
  commandLineArguments = parser.parse_args()

  program = Screen(applicationName, applicationVersion, commandLineArguments)
  program.start()
