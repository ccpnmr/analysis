"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.Version import applicationVersion
from ccpn.ui.gui.AppBase import AppBase, defineProgramArguments
from ccpn.ui.gui.lib.Window import MODULE_DICT
from ccpn.ui.gui.modules import GuiStrip

# from ccpn.ui.gui.modules import GuiStripNd
# from ccpn.ui.gui.modules import GuiSpectrumDisplay
# from ccpn.ui.gui.modules import GuiStripDisplayNd


applicationName = 'AnalysisAssign'

class Assign(AppBase):
  """Root class for Assign application"""

  def __init__(self, applicationName, applicationVersion, commandLineArguments):
    AppBase.__init__(self, applicationName, applicationVersion, commandLineArguments)
    self.components.add('Assignment')

  def initGraphics(self):
    """Set up graphics system after loading"""

    # Initialise strips
    project = self.project
    for strip in project.strips:
      GuiStrip._setupGuiStrip(project, strip._wrappedData)

      # if isinstance(strip, GuiStripNd) and not strip.haveSetupZWidgets:
      #   strip.setZWidgets()

    # Initialise Rulers
    for task in project.tasks:
      for apiMark in task._wrappedData.sortedMarks():
        for apiRuler in apiMark.sortedRulers():
          GuiStrip._rulerCreated(project, apiRuler)

    # Initialise SpectrumViews
    for spectrumDisplay in project.spectrumDisplays:
      for strip in spectrumDisplay.strips:
        for spectrumView in strip.spectrumViews:
          spectrumView._createdSpectrumView()
          for peakList in spectrumView.spectrum.peakLists:
            strip.showPeaks(peakList)

    self.initLayout()

  def initLayout(self):
    """
    Restore layout of modules from previous save after graphics have been set up.
    """
    import yaml, os
    if os.path.exists(os.path.join(self.project.path, 'layouts', 'layout.yaml')):
      with open(os.path.join(self.project.path, 'layouts', 'layout.yaml')) as f:
        layout = yaml.load(f)
        typ, contents, state = layout['main']

        containers, docks = self._appBase.mainWindow.dockArea.findAll()
        flatten = lambda *n: (e for a in n
        for e in (flatten(*a) if isinstance(a, (tuple, list)) else (a,)))
        flatContents = list(flatten(contents))
        for item in flatContents:
          if item in list(MODULE_DICT.keys()):
            obj = docks.get(item)
            if not obj:
             func = getattr(self._appBase.mainWindow, MODULE_DICT[item])
             func()
        for s in layout['float']:
          typ, contents, state = s[0]['main']

          containers, docks = self._appBase.mainWindow.dockArea.findAll()
          for item in contents:
            if item[0] == 'dock':
              print(obj)
              obj = docks.get(item[1])
              if not obj:
                func = getattr(self._appBase.mainWindow, MODULE_DICT[item[1]])
                func()
        self._appBase.mainWindow.dockArea.restoreState(layout)


if __name__ == '__main__':

  # argument parser
  parser = defineProgramArguments()
  # add any additional commandline argument here
  commandLineArguments = parser.parse_args()

  program = Assign(applicationName, applicationVersion, commandLineArguments)
  program.start()

