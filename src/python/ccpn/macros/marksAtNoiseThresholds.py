
#=========================================================================================
# General CCPN Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ =   ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ =   ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")

#=========================================================================================
# Macro Created by:
#=========================================================================================
__author__      =   "$Author: Luca Mureddu $"
__date__        =   "$Date: 2021-05-20 12:34:46 +0100 (Thu, May 20, 2021) $"
__version__     =   "$Revision: 3.1.beta $"
__Title__       =   "Colour PeakLists"
__Category__    =   "Screening"
__tags__        =   ("Colours", "marks", "noiseThresholds")
__Description__ =   """
                    Add marks at spectrum noise threshold          
                    """
__Prerequisites__ = """
                    """


##################################################################################################
#######################################  start of the code #######################################
##################################################################################################
from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking

spectra = current.strip.spectra #do only in the selected strip
with undoBlockWithoutSideBar():
    mainWindow.clearMarks() # clean first the existing marks
    for spectrum in spectra:
        positiveThreshold = spectrum.noiseLevel or spectrum.estimateNoise()
        negativeThreshold = spectrum.negativeNoiseLevel or -spectrum.noiseLevel
        hexColour = spectrum.sliceColour
        # Positive mark
        mainWindow.newMark(colour=hexColour,
                           positions=[positiveThreshold],
                           axisCodes=['intensity'],
                           labels=([f'{spectrum.name}_+NoiseThreshold']))
        # Negative mark
        mainWindow.newMark(colour=hexColour,
                           positions=[negativeThreshold],
                           axisCodes=['intensity'],
                           labels=([f'{spectrum.name}_-NoiseThreshold']))