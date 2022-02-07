"""
This file contains CcpnNefImporter class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-02-07 16:46:08 +0000 (Mon, February 07, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-02-05 10:28:48 +0000 (Saturday, February 5, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
from ccpn.util.nef.GenericStarParser import DataBlock

from ccpn.core.lib.ContextManagers import undoStackBlocking, notificationBlanking
from ccpn.framework.lib.ccpnNef import CcpnNefIo
from ccpn.framework.lib.ccpnNef.CcpnNefImporter import CcpnNefImporter

def _convertToDataBlock(project,
                        skipPrefixes: Sequence = (),
                        expandSelection: bool = True,
                        pidList: list = None):
    """
    Export selected contents of the project to a Nef file.

      skipPrefixes: ( 'ccpn', ..., <str> )
      expandSelection: <bool> }

      Include 'ccpn' in the skipPrefixes list will exclude ccpn specific items from the file
      expandSelection = True  will include all data from the project, this may not be data that
                              is not defined in the Nef standard.

    PidList is a list of <str>, e.g. 'NC:@-', obtained from the objects to be included.
    The Nef file may also contain further dependent items associated with the pidList.

    :param skipPrefixes: items to skip
    :param expandSelection: expand the selection
    :param pidList: a list of pids
    """
    # from ccpn.core.lib import CcpnNefIo

    with undoStackBlocking():
        with notificationBlanking():
            t0 = time()
            dataBlock = CcpnNefIo.convertToDataBlock(project, skipPrefixes=skipPrefixes,
                                                     expandSelection=expandSelection,
                                                     pidList=pidList)
            t2 = time()
            getLogger().info('File to dataBlock, time = %.2fs' % (t2 - t0))

    return dataBlock

@staticmethod
def _writeDataBlockToFile(dataBlock: DataBlock = None, path: str = None,
                          overwriteExisting: bool = False):
    # Export the modified dataBlock to file
    # from ccpn.core.lib import CcpnNefIo

    with undoStackBlocking():
        with notificationBlanking():
            t0 = time()
            CcpnNefIo.writeDataBlock(dataBlock, path=path, overwriteExisting=overwriteExisting)
            t2 = time()
            getLogger().info('Exporting dataBlock to file, time = %.2fs' % (t2 - t0))
