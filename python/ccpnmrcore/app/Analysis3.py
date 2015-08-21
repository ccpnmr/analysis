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
from ccpnmrcore.modules import GuiStrip
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
          GuiStripDisplayNd._createdStripSpectrumView(project, apiStripSpectrumView)
          for apiStripPeakListView in apiStripSpectrumView.stripPeakListViews:
            GuiStripDisplayNd._createdStripPeakListView(project, apiStripPeakListView)


if __name__ == '__main__':
  import argparse  

  parser = argparse.ArgumentParser(description='Process startup arguments')
  parser.add_argument('--language', help='Language for menus, etc.')
  parser.add_argument('--skip-user-preferences', dest='skipUserPreferences', action='store_true', help='Skip loading user preferences')
  parser.add_argument('projectPath', nargs='?', help='Project path')
  args = parser.parse_args()
  
  startProgram(Analysis3, applicationName, applicationVersion, args.projectPath, args.language, args.skipUserPreferences)

