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
__dateModified__ = "$dateModified: 2021-05-11 09:59:06 +0100 (Tue, May 11, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-05-07 12:52:12 +0100 (Fri, May 07, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.nef.NefImporter import NefImporter
from ccpn.util.nef.Specification import CifDicConverter
from ccpn.util.nef import ErrorLog as el
from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath


class CcpnCifDicConverter(CifDicConverter):
    """Subclass the CifDictionary converter to subclass _logging to Ccpn logger
    """

    def _logging(self, *args):
        """Log messages as required
        """
        try:
            getLogger().info('{}'.format(' '.join([str(arg) for arg in args])))
        except Exception as es:
            getLogger().info('>>> Error during logging: {}'.format(str(es)))


class CcpnNefImporter(NefImporter):
    """Subclass of nefImporter to subclass _logging to Ccpn logger
    """

    @el.ErrorLog(errorCode=el.NEFERROR_ERRORLOADINGFILE)
    def loadValidateDictionary(self, fileName=None, mode='standard'):
        _path = aPath(fileName)
        if not _path.exists() and _path.is_file():
            raise ValueError('Error: file does not exist')

        with open(fileName) as fp:
            data = fp.read()
        converter = CcpnCifDicConverter(data)
        converter.convertToNef()
        self._validateNefDict = converter.result

        return True
