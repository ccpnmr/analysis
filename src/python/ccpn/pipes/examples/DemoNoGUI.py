#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:39 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### NON GUI IMPORTS

from ccpn.framework.lib.Pipe import PandasPipe
import pandas as pd


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


def myAlgorithm(data):
    # do something
    return data


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################

##  GUI PIPE  -->  None . If the pipe is inserted in
## the guiPipeline will still appear as an empty guiPipe but without widgets.


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class DemoPipe3(PandasPipe):
    'Pandas pipe with No Gui, Feeds with a dataFrame, returns a DataFrame '
    pipeName = 'NoGui Pandas Pipe'

    def runPipe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        outputDataframe = myAlgorithm(dataframe)
        return outputDataframe
