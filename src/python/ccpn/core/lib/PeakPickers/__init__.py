"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-05-28 16:26:13 +0100 (Fri, May 28, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

"""
User peakPickers are to go in this directory
"""


def loadPeakPickerModules(paths):
    """
    dynamic peakPicker importer. Called upon initialisation of the program for loading the registered ccpn peakPickers.
    Path = path of the top dir containing the peakPicker files.
    """
    import pkgutil as _pkgutil
    import traceback
    from ccpn.util.Logging import getLogger
    import sys

    modules = []

    for loader, name, isPpkg in _pkgutil.walk_packages(paths):
        if name:
            try:
                found = loader.find_module(name)
                if found:
                    if sys.modules.get(name):  # already loaded.
                        continue
                    else:
                        module = found.load_module(name)
                        modules.append(module)
            except Exception as err:
                traceback.print_tb(err.__traceback__)
                getLogger().warning('Error Loading PeakPicker %s. %s' % (name, str(err)))
    return modules


loadPeakPickerModules(__path__)
