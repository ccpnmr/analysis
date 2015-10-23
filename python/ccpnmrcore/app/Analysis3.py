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

import sys

from ccpnmrcore.app.AppBase import AppBase, startProgram
from ccpnmrcore.app.Version import applicationVersion
from ccpnmrcore.lib.Window import MODULE_DICT
from ccpnmrcore.modules import GuiStrip
from ccpnmrcore.modules import GuiStripNd
from ccpnmrcore.modules import GuiStripDisplayNd


applicationName = 'Analysis3'

class Analysis3(AppBase):
  """Root class for Analysis3 application"""

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
            GuiStripDisplayNd._createdStripPeakListView(project, apiStripPeakListView)
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
        for item in contents:
          if item[0] == 'dock':
            obj = docks.get(item[1])
            if obj is None:
             func = getattr(self._appBase.mainWindow, MODULE_DICT[item[1]])
             func()
        for s in layout['float']:
          typ, contents, state = s[0]['main']

          containers, docks = self._appBase.mainWindow.dockArea.findAll()
          for item in contents:
            if item[0] == 'dock':
              obj = docks.get(item[1])
              if obj is None:
                func = getattr(self._appBase.mainWindow, MODULE_DICT[item[1]])
                func()
        self._appBase.mainWindow.dockArea.restoreState(layout)


if __name__ == '__main__':
  import argparse  

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
  
  startProgram(Analysis3, applicationName, applicationVersion, components, args.projectPath,
               args.language, args.skipUserPreferences, args.nologging)

