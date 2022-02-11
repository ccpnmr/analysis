"""
This file contains CcpnNefImporter class
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-02-11 11:45:57 +0000 (Fri, February 11, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-02-05 10:28:48 +0000 (Saturday, February 5, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.Application import getApplication
from ccpn.framework.lib.ccpnNef.CcpnNefIo import CcpnNefReader

from ccpn.util.Logging import getLogger
from ccpn.util.nef.NefImporter import NefImporter
from ccpn.util.nef.ErrorLog import NEF_STANDARD, NEF_STRICT
from ccpn.core.lib.ContextManagers import catchExceptions, undoBlockWithoutSideBar, notificationEchoBlocking


class CcpnNefImporter(NefImporter):
    """A class for custimization of the general NefImporter class
    """

    def __init__(self, errorLogging=NEF_STANDARD, validateDictPath=None, hidePrefix = True):
        """
        Initialise the CcpNefImporter instance. This will attach the logger and optionally a  Nef validation
        dictionary.
        :param errorLogging: Nef error logging level: one of (NEF_SILENT, NEF_STANDARD, NEF_STRICT)
        :param validateDictPath: Path to a Nef validation dictory definition (in star format)
        :param hidePrefix: hide nef prefixes
        """

        _app = getApplication()
        super().__init__(programName=_app.applicationName,
                         programVersion=_app.applicationVersion,
                         errorLogging=errorLogging,
                         hidePrefix=hidePrefix)

        # set the ccpn logger
        _logger = getLogger().error if errorLogging == NEF_STRICT else getLogger().warning
        self.logger = _logger

        self._reader = None
        self._application = _app

        if validateDictPath is not None:
            self.loadValidateDictionary(validateDictPath)


