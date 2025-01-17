#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-04-05 14:31:47 +0100 (Sun, April 05, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import AutoGeneratedGuiPipe

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe

########################################################################################################################
###   Attributes:
###   Used in setting-up the GuiPipe and Pipe
########################################################################################################################

Option = 'Option'
Option1 = 'Option-1'
Option2 = 'Option-2'
PipeName = 'Auto-Generated GuiPipe Demo'

########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

def myAlgorithm(data, *kargs):
    # do something with data and key arguments
    return data

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################

class AutoGeneratedGuiPipeDemo(AutoGeneratedGuiPipe):
    pipeName = PipeName
    autoGuiParams = [{
                    'variable': Option,
                    'value': (Option1, Option2),
                    'label': 'Select Option',
                    'default': Option1
                    }]

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(AutoGeneratedGuiPipeDemo, self)
        AutoGeneratedGuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)

########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################

class DemoPipe2(SpectraPipe):
    'Demo pipe with autoGenerated gui'

    _kwargs = {
               Option: Option1,
               }

    guiPipe = AutoGeneratedGuiPipeDemo
    pipeName = PipeName

    def runPipe(self, data):
        result = myAlgorithm(data, *self._kwargs)
        return data

# DemoPipe2.register()