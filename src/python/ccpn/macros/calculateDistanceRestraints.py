"""
This macro opens a popup for creating distance Restraints from a peakList containing assigned peaks.
Alpha released in Version 3.0.3
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: VickyAH $"
__dateModified__ = "$dateModified: 2022-05-17 12:23:33 +0100 (Tue, May 17, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-03-05 11:01:32 +0000 (Fri, March 05, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups.DistanceRestraintPopup import CalculateDistanceRestraintsPopup

if __name__ == '__main__':
    popup = CalculateDistanceRestraintsPopup(mainWindow=mainWindow)
    popup.show()
    popup.raise_()
