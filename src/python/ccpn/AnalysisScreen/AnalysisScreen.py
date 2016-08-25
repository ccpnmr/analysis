from ccpn.framework.Framework import Framework
from ccpn.core.Project import Project
from ccpn.AnalysisScreen.lib.ScreenLookup import _loadScreenLookupFile
from ccpn.ui.gui.popups.PickPeaks1DPopup import PickPeak1DPopup
from ccpn.AnalysisScreen.popups.MixtureGenerationPopup import MixtureGenerationPopup
from ccpn.AnalysisScreen.modules.MixtureAnalysis import MixtureAnalysis
from ccpn.AnalysisScreen.modules.ScreeningSettings import initialiseScreeningPipelineModule
from ccpn.AnalysisScreen.modules.ShowScreeningHits import ShowScreeningHits

applicationName = 'Screen'

class Screen(Framework):
  """Root class for Screen application"""

  def __init__(self, applicationName, applicationVersion, commandLineArguments):
    Framework.__init__(self, applicationName, applicationVersion, commandLineArguments)
    Project._loadLookupFile = _loadScreenLookupFile

  #########################################    Start setup Menu      #############################################

  def setupMenus( self ):
    super().setupMenus( )

    menuSpec = ('Screen',[
                         ("Pick Peaks "        , self.showPickPeakPopup),
                         ("Generate Mixtures " , self.showMixtureGenerationPopup, [('shortcut', 'cs')]),
                         ("Mixtures Analysis " , self.showMixtureAnalysis,        [('shortcut', 'st')]),
                         ("Screening Pipeline" , self.showScreeningPipeline,      [('shortcut', 'sp')]),
                         ("Hit Analysis"       , self.showHitAnalysisModule,      [('shortcut', 'ha')]),
                         ]
                )

    self.addApplicationMenuSpec(menuSpec)

  def showPickPeakPopup(self):
    popup = PickPeak1DPopup(parent=self.ui.mainWindow, project=self.project)
    popup.exec_()
    popup.raise_()
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showSamplePopup()")
    self.project._logger.info("application.showSamplePopup()")

  def showMixtureGenerationPopup(self):
    """Displays Sample creation popup."""
    popup = MixtureGenerationPopup(self.ui.mainWindow,  project=self.project)
    popup.exec_()
    popup.raise_()
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showSamplePopup()")
    self.project._logger.info("application.showSamplePopup()")

  def showMixtureAnalysis(self, position='bottom', relativeTo=None):
    """ Displays the Mixtures Analysis Module """
    showSa = MixtureAnalysis(self.ui.mainWindow,  project=self.project)
    self.ui.mainWindow.moduleArea.addModule(showSa, position=position, relativeTo=relativeTo)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showMixtureAnalysis()")
    self.project._logger.info("application.showMixtureAnalysis()")

  def showScreeningPipeline(self, position='bottom', relativeTo=None):
    initialiseScreeningPipelineModule(project=self.project, application=self,)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showScreeningPipeline()")
    self.project._logger.info("application.showScreeningPipeline()")

  def showHitAnalysisModule(self, position='top', relativeTo= None):
    self.showScreeningHits = ShowScreeningHits(self.ui.mainWindow,  project=self.project)
    self.ui.mainWindow.moduleArea.addModule(self.showScreeningHits, position, None)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showHitAnalysisModule()")
    self.project._logger.info("application.showHitAnalysisModule()")

    #########################################    End setup Menus      #############################################