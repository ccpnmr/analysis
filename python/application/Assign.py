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

from application.core.AppBase import AppBase, startProgram
from application.core.Version import applicationVersion
from application.core.lib.Window import MODULE_DICT
from application.core.modules import GuiStrip
from application.core.modules import GuiStripNd
from application.core.modules import GuiSpectrumDisplay
from application.core.modules import GuiStripDisplayNd


applicationName = 'Assign'

class Assign(AppBase):
  """Root class for Assign application"""

  def initGraphics(self):
    """Set up graphics system after loading"""

    # Initialise strips
    project = self.project
    for strip in project.strips:
      GuiStrip._setupGuiStrip(project, strip._wrappedData)

    # Initialise Rulers
    for task in project.tasks:
      for apiMark in task._wrappedData.sortedMarks():
        for apiRuler in apiMark.sortedRulers():
          GuiStrip._rulerCreated(project, apiRuler)

    # Initialise SpectrumViews
    for spectrumDisplay in project.spectrumDisplays:
      apiSpectrumDisplay = spectrumDisplay._wrappedData
      for apiSpectrumView in apiSpectrumDisplay.sortedSpectrumViews():
        GuiStripDisplayNd._createdSpectrumView(project, apiSpectrumView)

      for apiStrip in apiSpectrumDisplay.orderedStrips:
        for apiStripSpectrumView in apiStrip.stripSpectrumViews:
          GuiStripNd._spectrumViewCreated(project, apiStripSpectrumView)
          GuiStripDisplayNd._createdStripSpectrumView(project, apiStripSpectrumView)
          for apiStripPeakListView in apiStripSpectrumView.stripPeakListViews:
            GuiSpectrumDisplay._createdStripPeakListView(project, apiStripPeakListView)
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
  import argparse  
  # from PyQt4 import QtGui, QtCore
  # import os
  # from ccpncore.util import Path
  # splashPng = os.path.join(Path.getPythonDirectory(), 'ccpncore', 'gui', 'ccpnmr-splash-screen.png')
  # splash_pix = QtGui.QPixmap(splashPng)
  # splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
  # splash.show()
  parser = argparse.ArgumentParser(description='Process startup arguments')
  for component in ('Assignment', 'Screening', 'Structure'):
    parser.add_argument('--'+component.lower(), dest='include'+component, action='store_true',
                        help='Show %s component' % component.lower())
  parser.add_argument('--language', help='Language for menus, etc.')
  parser.add_argument('--skip-user-preferences', dest='skipUserPreferences', action='store_true', help='Skip loading user preferences')
  parser.add_argument('--nologging', dest='nologging', action='store_true', help='Do not log information to a file')
  parser.add_argument('projectPath', nargs='?', help='Project path')
  args = parser.parse_args()
  
  components = set()
  for component in ('Assignment', 'Screening', 'Structure'):
    if getattr(args, 'include'+component):
      components.add(component)
      
  if not components:
    components.add('Assignment')
  
  startProgram(Assign, applicationName, applicationVersion, components, args.projectPath,
               args.language, args.skipUserPreferences, args.nologging)
  # splash.hide()

