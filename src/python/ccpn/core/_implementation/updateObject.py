"""
updateObject class decorator
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-11-16 12:02:37 +0000 (Tue, November 16, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2021-11-10 10:28:41 +0000 (Wed, November 10, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from decorator import decorator

@decorator
def updateObject(version, updateFunction):
    """Class decorator to register updateFunction for a core-class in the _updateFunctions list.
    updateFunction with updating version to the next higher version

    profile updateFunction:

        updateFunction(obj) -> versionString

        obj: object that is being restored
        :return
    """

    def theDecorator(cls):
        """This function will decorate cls with _update, _updateHandler list and registers the updateHandler
        """
        if not hasattr(cls, '_updateFunctions'):
            raise RuntimeError('class %s does not have the attribute _updateFunctions')

        cls._updateFunctions.append( (version, updateFunction) )
        return cls

    return theDecorator
