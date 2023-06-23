
#=========================================================================================
# General CCPN Licence, Reference and Credits
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")

#=========================================================================================
# Macro Created by:
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-06-23 16:04:23 +0100 (Fri, June 23, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author__author__ =  "$Author: Luca Mureddu $"
__date__ = "$Date__date__ =    "$Date: 2021-05-20 12:34:46 +0100 (Thu, May 20, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================
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
