__author__ = 'luca'

from collections import OrderedDict
from ccpn.ui.gui.modules.PipelineModule import GuiPipeline
import os
from ccpn.AnalysisMetabolomics import GuiPipeLine as gp


pipelineFilesDirName = '/guiPipeline/'
templates =   OrderedDict((
                          ('Wlogsy', 'WlogsyTemplate'),
                          ('STD', 'STDTemplate'),
                          ('Broadening1H', 'Broadening1HTemplate'),
                          ('t1Rho', 't1RhoTemplate'),
                         ))


def initialiseScreeningPipelineModule(project=None, application=None,):
  from ccpn.AnalysisScreen import guiPipeline as _pm
  pipelineMethods = _pm.__all__
  guiPipeline= GuiPipeline(application=application, pipelineMethods=pipelineMethods, project=project, templates=templates)
  mainWindow = application.ui.mainWindow
  mainWindow.moduleArea.addModule(guiPipeline, position='bottom')
