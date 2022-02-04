"""
This module contains all definitions used in the various SeriesAnalysis modules.

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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-02-04 09:19:36 +0000 (Fri, February 04, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


############################################################################################
##  SeriesDataTable common definitions. Used in I/O tables columns and throughtout modules
############################################################################################

CHAIN_CODE      = 'chain_code'           # -> str   | Chain Code
RESIDUE_CODE    = 'residue_code'         # -> str   | Residue Sequence Code (e.g.: '1', '1B')
RESIDUE_TYPE    = 'residue_type'         # -> str   | Residue Type (e.g.: 'ALA')
ATOM_NAME       = 'atom_name'            # -> str   | Atom name (e.g.: 'Hn')

_ROW_UID         = '_ROW_UID'            # -> str   | Internal. Unique Identifier (e.g.: randomly generated 6 letters UUID)

CONSTANT_TABLE_COLUMNS = [CHAIN_CODE, RESIDUE_CODE, RESIDUE_TYPE, ATOM_NAME]






