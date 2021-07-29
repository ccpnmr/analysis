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
__dateModified__ = "$dateModified: 2021-07-29 20:46:52 +0100 (Thu, July 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-07-07 12:10:32 +0100 (Wed, July 07, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict as OD
from ccpn.core.lib.NefImporter.NefSaveFrameABC import SaveFrameABC, _isALoop


class MetaData(SaveFrameABC):
    """First saveframe in Nef specification containing file information
    """

    saveFrameType = 'nef_nmr_meta_data'

    nef2CcpnMap = {
        'nef_nmr_meta_data'  : OD((
            ('format_name', None),
            ('format_version', None),
            ('program_name', None),
            ('program_version', None),
            ('creation_date', None),
            ('uuid', None),
            ('coordinate_file_name', None),
            ('nef_related_entries', _isALoop),
            ('nef_program_script', _isALoop),
            ('nef_run_history', _isALoop),
            )),

        'nef_related_entries': OD((
            ('database_name', None),
            ('database_accession_code', None),
            )),

        'nef_program_script' : OD((
            ('program_name', None),
            ('script_name', None),
            ('script', None),
            )),

        'nef_run_history'    : OD((
            ('run_number', 'serial'),
            ('program_name', 'programName'),
            ('program_version', 'programVersion'),
            ('script_name', 'scriptName'),
            ('script', 'script'),
            ('ccpn_input_uuid', 'inputDataUuid'),
            ('ccpn_output_uuid', 'outputDataUuid'),
            )),
        }


MetaData.register()
