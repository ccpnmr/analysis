
#=========================================================================================
# General CCPN Licence, Reference and Credits
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
# Macro Created by:
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: VickyAH $"
__dateModified__ = "$dateModified: 2022-05-17 12:23:33 +0100 (Tue, May 17, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author__author__      =   "$Author: Luca Mureddu $"
__date__ = "$Date__date__        =   "$Date: 2021-06-09 14:02:46 +0100 (Wed, June 09, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================
__Title__       =   "CompareDatasets  "
__Category__    =   "Screening"
__tags__        =   ("Relaxation", "Refit peaks")
__Description__ =   """
                    Use this macro to open a dedicated module for comparing Screening Datasets in Version 3.0.4
                                   
                    """

__Prerequisites__ = """
                    Screening Datasets created using the Pipeline or the HitAnalysis module.
                    """


from ccpn.AnalysisScreen.gui.modules.CompareDatasets import CompareScreeningDataset
m = CompareScreeningDataset(mainWindow)
mainWindow.moduleArea.addModule(m)
