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
__dateModified__ = "$dateModified: 2022-07-13 11:03:43 +0100 (Wed, July 13, 2022) $"
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
from ccpn.core.lib.AssignmentLib import CCP_CODES_SORTED

############################################################################################
##  SeriesDataTable common definitions. Used in I/O tables columns and throughtout modules
############################################################################################

NMRCHAINCODE     = 'nmrChainCode'           # -> str   | nmrChain Code
NMRRESIDUECODE   = 'nmrResidueCode'         # -> str   | nmrResidue Sequence Code (e.g.: '1', '1B')
NMRRESIDUETYPE   = 'nmrResidueType'         # -> str   | nmrResidue Type (e.g.: 'ALA')
NMRATOMNAME      = 'nmrAtomName'            # -> str   | nmrAtom name (e.g.: 'Hn')
NMRATOMNAMES     = f'{NMRATOMNAME}s'        # -> str   | nmrAtom names comma separated (e.g.: 'Hn, Nh'). Used in OutPut datarames instead of ATOMNAME

_ROW_UID         = '_ROW_UID'            # -> str   | Internal. Unique Identifier (e.g.: randomly generated 6 letters UUID)
VALUE            = 'Value'               # -> str   | The column header  prefix in a SeriesTable. Used to store data after the CONSTANT_TABLE_COLUMNS
TIME             = 'Time'                # -> str   | A general prefix in a SeriesTable.

SEP              =  '_'                  # the prefix-name-suffix global separator. E.g., used in Value columns: Value_height_at_0
VALUE_           = f'{VALUE}{SEP}'
TIME_            = f'{TIME}{SEP}'

DIMENSION        = 'dimension'
ISOTOPECODE      = 'isotopeCode'
CLUSTERID        = 'clusterId'
COLLECTIONID     = 'collectionId'
SERIESSTEP       = 'seriesStep'
SERIESUNIT       = 'seriesUnit'
PEAKPID          = 'peakPid'
SPECTRUMPID      = 'spectrumPid'
NMRATOMPID       = 'nmrAtomPid'
COLLECTIONPID    = 'collectionPid'
PID              = 'pid'
ASSIGNEDNMRATOMS = 'assignedNmrAtoms'

# fitting output Stat variables
MINIMISER        = 'minimiser'
R2               = 'R2'                  # -> float |
CHISQUARE        = 'Chi-square'
REDUCEDCHISQUARE = f'Red-{CHISQUARE}'
AKAIKE           = 'Akaike'
BAYESIAN         = 'Bayesian'
MINIMISER_METHOD = 'Method'


## Peak properties. Used to get nmrAtom assigned-peak by dimension and build tables.
_POINTPOSITION  = pu._POSITION
_PPMPOSITION    = pu._PPMPOSITION
_PPMPOSITIONS   = pu.PPMPOSITIONS
_LINEWIDTH      = pu._LINEWIDTH
_LINEWIDTHS     = pu.LINEWIDTHS
_HEIGHT         = pu.HEIGHT
_VOLUME         = pu.VOLUME

## ATOM Names
_H = pu.H
_N = pu.N
_C = pu.C
_OTHER = pu.OTHER

## IsotopeCode Names

ISOTOPECODES = 'isotopeCodes'
_1H  = '1H'
_15N = '15N'
_13C = '13C'


CONSTANT_STATS_OUTPUT_TABLE_COLUMNS = [MINIMISER_METHOD, R2, CHISQUARE, REDUCEDCHISQUARE, AKAIKE, BAYESIAN]

SpectrumPropertiesHeaders = [DIMENSION, ISOTOPECODE, SERIESSTEP, SERIESUNIT]
PeakPropertiesHeaders = [COLLECTIONID, _PPMPOSITION, _HEIGHT, _LINEWIDTH, _VOLUME]
AssignmentPropertiesHeaders = [NMRCHAINCODE, NMRRESIDUECODE, NMRRESIDUETYPE, NMRATOMNAME]
PidHeaders = [COLLECTIONPID, SPECTRUMPID, PEAKPID, NMRATOMPID]

KD = 'Kd'
BMAX = 'BMax'
_ERR = '_err'
ERROR = 'Error'

FLAG = 'Flag'
SERIAL = 'Serial'
############################################################################################
### Used in SeriesFrame tables ABCs
############################################################################################
SERIESANALYSISINPUTDATA = 'SeriesAnalysisInputData'
RELAXATION_OUTPUT_FRAME = 'RelaxationOutputFrame'
CSM_OUTPUT_FRAME        = 'CSMOutputFrame'

SERIESFRAMETYPE         = 'SERIESFRAMETYPE'
_assignmentHeaders      = '_assignmentHeaders'
_valuesHeaders          = '_valuesHeaders'
_peakPidHeaders         = '_peakPidHeaders'

_SpectrumPropertiesHeaders = 'spectrumPropertiesHeaders'


OUTPUT_SERIESFRAME_TYPES = [
                    CSM_OUTPUT_FRAME,
                    RELAXATION_OUTPUT_FRAME,
                    ]



############################################################################################
### Used in SeriesAnalyisBC
############################################################################################
ChemicalShiftMappingAnalysis = 'ChemicalShiftMappingAnalysis'  # used in SeriesName for the ChemicalShiftMappingAnalysis
RelaxationAnalysis = 'RelaxationAnalysis'                      # used in SeriesName for the RelaxationAnalysisBC


## Series Units
SERIES_TIME_UNITS = constants.TIME_UNITS
SERIES_CONCENTRATION_UNITS = constants.CONCENTRATION_UNITS
SERIES_UNITS = constants.ALL_SERIES_UNITS



## Alpha Factors Definitions used in ChemicalShiftAnalysis DeltaDeltas
uALPHA = '\u03B1'
uDELTA = '\u0394'
uDelta = '\u03B4'
DELTA = 'Delta'
DELTA_DELTA = f'{DELTA*2}'
EUCLIDEAN_DISTANCE = 'Euclidean Distance'
DELTA_DELTA_MEAN = f'{DELTA*2}(Mean)'
DELTA_DELTA_SUM = f'{DELTA*2}(Sum)'
DELTA_DELTA_STD = f'{DELTA*2}(STD)'
DEFAULT_H_ALPHAFACTOR = 1
DEFAULT_N_ALPHAFACTOR = 0.142
DEFAULT_C_ALPHAFACTOR = 0.25
DEFAULT_OTHER_ALPHAFACTOR = 1
DEFAULT_ALPHA_FACTORS = OrderedDict((
                            (_1H, DEFAULT_H_ALPHAFACTOR),
                            (_15N, DEFAULT_N_ALPHAFACTOR),
                            (_13C, DEFAULT_C_ALPHAFACTOR),
                            (_OTHER, DEFAULT_OTHER_ALPHAFACTOR)
                            ))
DEFAULT_FILTERING_ATOMS = (_H, _N)
DEFAULT_EXCLUDED_RESIDUES = ['PRO']

FILTERINGATOMS  = 'FilteringAtoms'
ALPHAFACTORS    = 'AlphaFactors'

## Fitting models

FITTING_MODEL = 'fittingModel'
MODEL_NAME = 'modelName'
FITTING_MODELS = f'{FITTING_MODEL}s'
OVERRIDE_OUTPUT_DATATABLE = 'overrideOutputDataTables'
OUTPUT_DATATABLE_NAME = 'outputDataTableName'


## OneSiteBindingModel
ONE_BINDING_SITE_MODEL = 'One Site Binding'
FRACTION_BINDING_MODEL = 'Fraction Binding'

#### residues names
CCP_3LETTER_CODES = CCP_CODES_SORTED
EXCLUDEDRESIDUETYPES = 'ExcludedResidueTypes'

LEASTSQ = 'leastsq'

T1 = 'T1'
T2 = 'T2'

## Warnings
UNDER_DEVELOPMENT_WARNING = f'''This functionality is currently under active development. Use it at your own risk.'''
NIY_WARNING = f'''This functionality has not been implemented yet.'''
# Errors
OMIT_MODE = 'omit'
RAISE_MODE = 'raise'


# FLAG
FLAG_EXCLUDED = 'Excluded'
FLAG_INCLUDED = 'Included'
