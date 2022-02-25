"""
This module contains all definitions used in the various SeriesAnalysis modules.

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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-02-25 15:14:19 +0000 (Fri, February 25, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
import ccpn.util.Constants as constants
import ccpn.core.lib.peakUtils as pu



############################################################################################
##  SeriesDataTable common definitions. Used in I/O tables columns and throughtout modules
############################################################################################

CHAIN_CODE      = 'chain_code'           # -> str   | Chain Code
RESIDUE_CODE    = 'residue_code'         # -> str   | Residue Sequence Code (e.g.: '1', '1B')
RESIDUE_TYPE    = 'residue_type'         # -> str   | Residue Type (e.g.: 'ALA')
ATOM_NAME       = 'atom_name'            # -> str   | Atom name (e.g.: 'Hn')
ATOM_NAMES      = f'{ATOM_NAME}s'        # -> str   | Atom names comma separated (e.g.: 'Hn, Nh'). Used in OutPut datarames instead of ATOM_NAME

_ROW_UID         = '_ROW_UID'            # -> str   | Internal. Unique Identifier (e.g.: randomly generated 6 letters UUID)
VALUE            = 'Value'               # -> str   | The column header  prefix in a SeriesTable. Used to store data after the CONSTANT_TABLE_COLUMNS
TIME             = 'Time'                # -> str   | A general prefix in a SeriesTable.

SEP              =  '_'                  # the prefix-name-suffix global separator. E.g., used in Value columns: Value_height_at_0
VALUE_           = f'{VALUE}{SEP}'
TIME_            = f'{TIME}{SEP}'

# fitting output Stat variables
R2               = 'R2'                  # -> float |
CHISQUARE        = 'Chi-square'
REDUCEDCHISQUARE = f'Reduced-{CHISQUARE}'
AKAIKE           = 'Akaike'
BAYESIAN         = 'Bayesian'
MINIMISER_METHOD = 'Minimiser-Method'

CONSTANT_TABLE_COLUMNS = [CHAIN_CODE, RESIDUE_CODE, RESIDUE_TYPE, ATOM_NAME]
CONSTANT_OUTPUT_TABLE_COLUMNS = [CHAIN_CODE, RESIDUE_CODE, RESIDUE_TYPE, ATOM_NAMES]
CONSTANT_STATS_OUTPUT_TABLE_COLUMNS = [MINIMISER_METHOD, R2, CHISQUARE, REDUCEDCHISQUARE, AKAIKE, BAYESIAN]

############################################################################################
### Used in SeriesFrame tables ABCs
############################################################################################

RELAXATION_INPUT_FRAME  = 'RelaxationInputFrame'
RELAXATION_OUTPUT_FRAME = 'RelaxationOutputFrame'
CSM_INPUT_FRAME         = 'CSMInputFrame'
CSM_OUTPUT_FRAME        = 'CSMOutputFrame'

SERIESFRAMETYPE         = 'SERIESFRAMETYPE'

INPUT_SERIESFRAME_TYPES = [
                    CSM_INPUT_FRAME,
                    RELAXATION_INPUT_FRAME,
                    ]

OUTPUT_SERIESFRAME_TYPES = [
                    CSM_OUTPUT_FRAME,
                    RELAXATION_OUTPUT_FRAME,
                    ]

SERIESFRAME_TYPES = INPUT_SERIESFRAME_TYPES + OUTPUT_SERIESFRAME_TYPES


############################################################################################
### Used in SeriesAnalyisBC
############################################################################################
ChemicalShiftMappingAnalysis = 'ChemicalShiftMappingAnalysis'  # used in SeriesName for the ChemicalShiftMappingAnalysis
RelaxationAnalysis = 'RelaxationAnalysis'                      # used in SeriesName for the RelaxationAnalysisBC


## Series Units
SERIES_TIME_UNITS = constants.TIME_UNITS
SERIES_CONCENTRATION_UNITS = constants.CONCENTRATION_UNITS
SERIES_UNITS = constants.ALL_SERIES_UNITS

## Peak properties. Used to get nmrAtom assigned-peak by dimension and build tables.
_POINTPOSITION  = pu._POSITION
_PPMPOSITION    = pu._PPMPOSITION
_LINEWIDTH      = pu._LINEWIDTH
_HEIGHT         = pu.HEIGHT
_VOLUME         = pu.VOLUME

## ATOM Names
_H = pu.H
_N = pu.N
_C = pu.C
_OTHER = pu.OTHER

## Alpha Factors Definitions used in ChemicalShiftAnalysis DeltaDeltas

DELTA = 'Delta'
DELTA_DELTA = f'{DELTA*2}'

DEFAULT_H_ALPHAFACTOR = 1
DEFAULT_N_ALPHAFACTOR = 0.142
DEFAULT_C_ALPHAFACTOR = 0.25
DEFAULT_OTHER_ALPHAFACTOR = 1
DEFAULT_ALPHA_FACTORS = OrderedDict((
                            (_H, DEFAULT_H_ALPHAFACTOR),
                            (_N, DEFAULT_N_ALPHAFACTOR),
                            (_C, DEFAULT_C_ALPHAFACTOR),
                            (_OTHER, DEFAULT_OTHER_ALPHAFACTOR)
                            ))


## Fitting models

FITTING_MODEL = 'fittingModel'
FITTING_MODELS = f'{FITTING_MODEL}s'
OVERRIDE_OUTPUT_DATATABLE = 'overrideOutputDataTables'
OUTPUT_DATATABLE_NAME = 'outputDataTableName'


## OneSiteBindingModel
ONE_BINDING_SITE_MODEL = 'OneSiteBindingModel'

########

