"""
This module defines the data loading mechanism for loading a ChemComp file
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-10-06 22:35:43 +0100 (Fri, October 06, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-08-30 15:14:00 +0100 (Wed, August 30, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.core.Project import Project


class ChemCompDataLoader(DataLoaderABC):
    """The ChemComp data-loader. Only available from an XML file.
    """
    dataFormat = 'ChemComp'
    suffixes = ['.xml']  # a list of suffixes that get matched to path
    loadFunction = (Project._loadChemCompFile, 'project')

ChemCompDataLoader._registerFormat()
