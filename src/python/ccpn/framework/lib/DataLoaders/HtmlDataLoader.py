"""
This module defines the data loading mechanism for loading a html file
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-09-16 15:02:26 +0100 (Fri, September 16, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-07-14 10:28:41 +0000 (Fri, July 14, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.framework.Framework import Framework


class HtmlDataLoader(DataLoaderABC):
    """An Html file data-loader.
    """
    dataFormat = 'htmlFile'
    suffixes = ['.html']  # a list of suffixes that get matched to path
    loadFunction = (Framework._loadHtmlFile, 'application')

HtmlDataLoader._registerFormat()
