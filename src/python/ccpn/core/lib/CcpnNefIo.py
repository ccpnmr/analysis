"""Code for CCPN-specific NEF I/O
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-05-01 20:55:34 +0100 (Fri, May 01, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import random
import os
import sys
import time
import typing
import itertools
import errno
from functools import partial
from datetime import datetime
from collections import OrderedDict as OD
# from collections import Counter
from operator import attrgetter, itemgetter
from typing import List, Union, Optional, Sequence, Tuple
from ccpn.core.lib import Pid
from ccpn.core import _coreImportOrder
from ccpn.util import Common as commonUtil
from ccpn.util import Constants
from ccpn.util import jsonIo
from ccpn.util.nef import Specification
from ccpn.util.nef import StarIo
from ccpnmodel.ccpncore.lib import Constants as coreConstants
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Complex import Complex
from ccpn.core.PeakList import PeakList
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Integral import Integral
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Multiplet import Multiplet
from ccpn.core.PeakCluster import PeakCluster
from ccpn.core.Peak import Peak
from ccpn.core.Sample import Sample
# from ccpn.core.SampleComponent import SampleComponent
from ccpn.core.Substance import Substance
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.core.Chain import Chain
# from ccpn.core.Residue import Residue
# from ccpn.core.Atom import Atom
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
# from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.ChemicalShiftList import ChemicalShiftList
# from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.core.DataSet import DataSet
from ccpn.core.RestraintList import RestraintList
from ccpn.core.Note import Note
from ccpn.core.lib import SpectrumLib
from ccpn.core.lib.MoleculeLib import extraBoundAtomPairs
from ccpn.core.lib import RestraintLib
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpn.util.Logging import getLogger
from ccpn.util.OrderedSet import OrderedSet


# Max value used for random integer. Set to be expressible as a signed 32-bit integer.
maxRandomInt = 2000000000

# Current NEF version (as float)
currentNefVersion = 1.1
# Lowest version that this reader can read (may not be the same), as float:
minimumNefVersion = 0.9

# TODO These should be consolidated with the same constants in NefIo
# (and likely those in ExportNefPopup) and likely replaced with a list of classes
CHAINS = 'chains'
CHEMICALSHIFTLISTS = 'chemicalShiftLists'
RESTRAINTLISTS = 'restraintLists'
PEAKLISTS = 'peakLists'
INTEGRALLISTS = 'integralLists'
MULTIPLETLISTS = 'multipletLists'
SAMPLES = 'samples'
SUBSTANCES = 'substances'
NMRCHAINS = 'nmrChains'
DATASETS = 'dataSets'
COMPLEXES = 'complexes'
SPECTRUMGROUPS = 'spectrumGroups'
NOTES = 'notes'
PEAKCLUSTERS = 'peakClusters'

#  - saveframe category names in reading order
# The order is significant, because setting of crosslinks relies on the order frames are read
# Frames are read in correct order regardless of how they are in the file
saveFrameReadingOrder = [
    'nef_nmr_meta_data',
    'nef_molecular_system',
    'ccpn_sample',
    'ccpn_substance',
    'ccpn_assignment',
    'nef_chemical_shift_list',
    'ccpn_dataset',
    'nef_distance_restraint_list',
    'nef_dihedral_restraint_list',
    'nef_rdc_restraint_list',
    'nef_nmr_spectrum',
    'nef_peak_restraint_links',
    'ccpn_complex',
    'ccpn_spectrum_group',
    'ccpn_restraint_list',
    'ccpn_peak_cluster_list',
    'ccpn_notes',
    'ccpn_additional_data'
    ]

# Saveframe writing order - must start with official 'nef_' frames
saveFrameWritingOrder = ([x for x in saveFrameReadingOrder if x.startswith('nef_')] +
                         [x for x in saveFrameReadingOrder if not x.startswith('nef_')])

# NEf to CCPN tag mapping (and tag order)
#
# Contents are:
# Nef2CcpnMap = {saveframe_or_loop_category:contents}
# contents = {tag:ccpn_tag_or_None}
# loopMap = {tag:ccpn_tag}
#
# Loops are entered as saveFrame contents with their category as tag and 'ccpn_tag' None
# and at the top level under their category name
# This relies on loop categories being unique, both at the top level, and among the item
# names within a saveframe

# Sentinel value - MUST evaluate as False
_isALoop = ()

# This dictionary is used directly to control what is read from and written to
# NEF. The top level keys are the tags for saveframes and loops, which must
# either have their own entries in the Reader 'imprters' dictionary, of (if loops)
# be read directly by the parent samveframe).
# The next level down desceibes saveframe attributes or loop elements.
#
# Each saveframe or loop row matches a wrapper object, and the nef2CcpnMap map
# is used to read and write starting at that object.
# There are several variants. Using nef_sequence as an example:
#
# ('residue_name','residueType') means that the NEF value is read AND written
#  to residue.residueType.
#
# ('chain_code','chain.shortName') means that the NEF value is set (for writing) automatically,
# but the code for reading from NEF and passing it into the project must be done by hand
#
# ('cis_peptide',None), means that the tag exists, but that both on reading and writing it
# must be handled  explicitly.
#
# values _isALoop have an obvious meaning
#
# Note the _parametersFromSaveFrame and _parametersFromLoopRow functions
# that make a parameters dictionary (for use in object creation), using these mappings
nef2CcpnMap = {
    'nef_nmr_meta_data'              : OD((
        ('format_name', None),
        ('format_version', None),
        ('program_name', None),
        ('program_version', None),
        ('creation_date', None),
        ('uuid', None),
        ('coordinate_file_name', None),
        ('ccpn_dataset_serial', None),
        ('ccpn_dataset_comment', None),
        ('nef_related_entries', _isALoop),
        ('nef_program_script', _isALoop),
        ('nef_run_history', _isALoop),
        )),

    'nef_related_entries'            : OD((
        ('database_name', None),
        ('database_accession_code', None),
        )),

    'nef_program_script'             : OD((
        ('program_name', None),
        ('script_name', None),
        ('script', None),
        )),

    'nef_run_history'                : OD((
        ('run_number', 'serial'),
        ('program_name', 'programName'),
        ('program_version', 'programVersion'),
        ('script_name', 'scriptName'),
        ('script', 'script'),
        ('ccpn_input_uuid', 'inputDataUuid'),
        ('ccpn_output_uuid', 'outputDataUuid'),
        )),

    'nef_molecular_system'           : OD((
        ('nef_sequence', _isALoop),
        ('nef_covalent_links', _isALoop),
        )),

    'nef_sequence'                   : OD((
        ('index', None),
        ('chain_code', 'chain.shortName'),
        ('sequence_code', 'sequenceCode'),
        ('residue_name', 'residueType'),
        ('linking', 'linking'),
        ('residue_variant', 'residueVariant'),
        ('cis_peptide', None),
        ('ccpn_comment', 'comment'),
        ('ccpn_chain_role', 'chain.role'),
        ('ccpn_compound_name', 'chain.compoundName'),
        ('ccpn_chain_comment', 'chain.comment'),
        )),

    'nef_covalent_links'             : OD((
        ('chain_code_1', None),
        ('sequence_code_1', None),
        ('residue_name_1', None),
        ('atom_name_1', None),
        ('chain_code_2', None),
        ('sequence_code_2', None),
        ('residue_name_2', None),
        ('atom_name_2', None),
        )),

    'nef_chemical_shift_list'        : OD((
        ('ccpn_serial', 'serial'),
        ('ccpn_auto_update', 'autoUpdate'),
        ('ccpn_is_simulated', 'isSimulated'),
        ('ccpn_comment', 'comment'),
        ('nef_chemical_shift', _isALoop),
        )),

    'nef_chemical_shift'             : OD((
        ('chain_code', None),
        ('sequence_code', None),
        ('residue_name', None),
        ('atom_name', None),
        ('value', 'value'),
        ('value_uncertainty', 'valueError'),
        ('element', None),
        ('isotope_number', None),
        ('ccpn_figure_of_merit', 'figureOfMerit'),
        ('ccpn_comment', 'comment'),
        )),

    'nef_distance_restraint_list'    : OD((
        ('potential_type', 'potentialType'),
        ('restraint_origin', 'origin'),
        ('ccpn_tensor_chain_code', 'tensorChainCode'),
        ('ccpn_tensor_sequence_code', 'tensorSequenceCode'),
        ('ccpn_tensor_residue_name', 'tensorResidueType'),
        ('ccpn_tensor_magnitude', 'tensorMagnitude'),
        ('ccpn_tensor_rhombicity', 'tensorRhombicity'),
        ('ccpn_tensor_isotropic_value', 'tensorIsotropicValue'),
        ('ccpn_serial', 'serial'),
        ('ccpn_dataset_serial', 'dataSet.serial'),
        ('ccpn_unit', 'unit'),
        ('ccpn_comment', 'comment'),
        ('nef_distance_restraint', _isALoop),
        )),

    'nef_distance_restraint'         : OD((
        ('index', None),
        ('restraint_id', 'restraint.serial'),
        ('restraint_combination_id', 'combinationId'),
        ('chain_code_1', None),
        ('sequence_code_1', None),
        ('residue_name_1', None),
        ('atom_name_1', None),
        ('chain_code_2', None),
        ('sequence_code_2', None),
        ('residue_name_2', None),
        ('atom_name_2', None),
        ('weight', 'weight'),
        ('target_value', 'targetValue'),
        ('target_value_uncertainty', 'error'),
        ('lower_linear_limit', 'additionalLowerLimit'),
        ('lower_limit', 'lowerLimit'),
        ('upper_limit', 'upperLimit'),
        ('upper_linear_limit', 'additionalUpperLimit'),
        ('ccpn_figure_of_merit', 'restraint.figureOfMerit'),
        ('ccpn_comment', 'restraint.comment'),
        )),

    'nef_dihedral_restraint_list'    : OD((
        ('potential_type', 'potentialType'),
        ('restraint_origin', 'origin'),
        ('ccpn_tensor_chain_code', 'tensorChainCode'),
        ('ccpn_tensor_sequence_code', 'tensorSequenceCode'),
        ('ccpn_tensor_residue_name', 'tensorResidueType'),
        ('ccpn_tensor_magnitude', 'tensorMagnitude'),
        ('ccpn_tensor_rhombicity', 'tensorRhombicity'),
        ('ccpn_tensor_isotropic_value', 'tensorIsotropicValue'),
        ('ccpn_serial', 'serial'),
        ('ccpn_dataset_serial', 'dataSet.serial'),
        ('ccpn_unit', 'unit'),
        ('ccpn_comment', 'comment'),
        ('nef_dihedral_restraint', _isALoop),
        )),

    'nef_dihedral_restraint'         : OD((
        ('index', None),
        ('restraint_id', 'restraint.serial'),
        ('restraint_combination_id', 'combinationId'),
        ('chain_code_1', None),
        ('sequence_code_1', None),
        ('residue_name_1', None),
        ('atom_name_1', None),
        ('chain_code_2', None),
        ('sequence_code_2', None),
        ('residue_name_2', None),
        ('atom_name_2', None),
        ('chain_code_3', None),
        ('sequence_code_3', None),
        ('residue_name_3', None),
        ('atom_name_3', None),
        ('chain_code_4', None),
        ('sequence_code_4', None),
        ('residue_name_4', None),
        ('atom_name_4', None),
        ('weight', 'weight'),
        ('target_value', 'targetValue'),
        ('target_value_uncertainty', 'error'),
        ('lower_linear_limit', 'additionalLowerLimit'),
        ('lower_limit', 'lowerLimit'),
        ('upper_limit', 'upperLimit'),
        ('upper_linear_limit', 'additionalUpperLimit'),
        ('name', None),
        ('ccpn_figure_of_merit', 'restraint.figureOfMerit'),
        ('ccpn_comment', 'restraint.comment'),
        )),

    'nef_rdc_restraint_list'         : OD((
        ('potential_type', 'potentialType'),
        ('restraint_origin', 'origin'),
        ('tensor_magnitude', 'tensorMagnitude'),
        ('tensor_rhombicity', 'tensorRhombicity'),
        ('tensor_chain_code', 'tensorChainCode'),
        ('tensor_sequence_code', 'tensorSequenceCode'),
        ('tensor_residue_name', 'tensorResidueType'),
        ('ccpn_tensor_isotropic_value', 'tensorIsotropicValue'),
        ('ccpn_serial', 'serial'),
        ('ccpn_dataset_serial', 'dataSet.serial'),
        ('ccpn_unit', 'unit'),
        ('ccpn_comment', 'comment'),
        ('nef_rdc_restraint', _isALoop),
        )),

    'nef_rdc_restraint'              : OD((
        ('index', None),
        ('restraint_id', 'restraint.serial'),
        ('restraint_combination_id', 'combinationId'),
        ('chain_code_1', None),
        ('sequence_code_1', None),
        ('residue_name_1', None),
        ('atom_name_1', None),
        ('chain_code_2', None),
        ('sequence_code_2', None),
        ('residue_name_2', None),
        ('atom_name_2', None),
        ('weight', 'weight'),
        ('target_value', 'targetValue'),
        ('target_value_uncertainty', 'error'),
        ('lower_linear_limit', 'additionalLowerLimit'),
        ('lower_limit', 'lowerLimit'),
        ('upper_limit', 'upperLimit'),
        ('upper_linear_limit', 'additionalUpperLimit'),
        ('scale', 'scale'),
        ('distance_dependent', 'isDistanceDependent'),
        ('ccpn_vector_length', 'restraint.vectorLength'),
        ('ccpn_figure_of_merit', 'restraint.figureOfMerit'),
        ('ccpn_comment', 'restraint.comment'),
        )),

    'nef_nmr_spectrum'               : OD((
        ('num_dimensions', 'spectrum.dimensionCount'),
        ('chemical_shift_list', None),
        ('experiment_classification', 'spectrum.experimentType'),
        ('experiment_type', 'spectrum.experimentName'),
        ('ccpn_positive_contour_count', 'spectrum.positiveContourCount'),
        ('ccpn_positive_contour_base', 'spectrum.positiveContourBase'),
        ('ccpn_positive_contour_factor', 'spectrum.positiveContourFactor'),
        ('ccpn_positive_contour_colour', 'spectrum.positiveContourColour'),
        ('ccpn_negative_contour_count', 'spectrum.negativeContourCount'),
        ('ccpn_negative_contour_base', 'spectrum.negativeContourBase'),
        ('ccpn_negative_contour_factor', 'spectrum.negativeContourFactor'),
        ('ccpn_negative_contour_colour', 'spectrum.negativeContourColour'),
        ('ccpn_slice_colour', 'spectrum.sliceColour'),
        ('ccpn_spectrum_scale', 'spectrum.scale'),
        ('ccpn_spinning_rate', 'spectrum.spinningRate'),
        ('ccpn_spectrum_comment', 'spectrum.comment'),
        ('ccpn_spectrum_file_path', None),
        ('ccpn_sample', None),
        ('ccpn_file_header_size', 'spectrum._wrappedData.dataStore.headerSize'),
        ('ccpn_file_number_type', 'spectrum._wrappedData.dataStore.numberType'),
        ('ccpn_file_complex_stored_by', 'spectrum._wrappedData.dataStore.complexStoredBy'),
        ('ccpn_file_scale_factor', 'spectrum._wrappedData.dataStore.scaleFactor'),
        ('ccpn_file_is_big_endian', 'spectrum._wrappedData.dataStore.isBigEndian'),
        ('ccpn_file_byte_number', 'spectrum._wrappedData.dataStore.nByte'),
        ('ccpn_file_has_block_padding', 'spectrum._wrappedData.dataStore.hasBlockPadding'),
        ('ccpn_file_block_header_size', 'spectrum._wrappedData.dataStore.blockHeaderSize'),
        ('ccpn_file_type', 'spectrum._wrappedData.dataStore.fileType'),
        ('ccpn_peaklist_serial', 'serial'),
        ('ccpn_peaklist_comment', 'comment'),
        ('ccpn_peaklist_name', 'title'),
        ('ccpn_peaklist_is_simulated', 'isSimulated'),
        ('ccpn_peaklist_symbol_colour', 'symbolColour'),
        ('ccpn_peaklist_symbol_style', 'symbolStyle'),
        ('ccpn_peaklist_text_colour', 'textColour'),
        ('nef_spectrum_dimension', _isALoop),
        ('ccpn_spectrum_dimension', _isALoop),
        ('nef_spectrum_dimension_transfer', _isALoop),
        ('nef_peak', _isALoop),
        ('ccpn_integral_list', _isALoop),
        ('ccpn_integral', _isALoop),
        ('ccpn_multiplet_list', _isALoop),
        ('ccpn_multiplet', _isALoop),
        ('ccpn_multiplet_peaks', _isALoop),
        ('ccpn_spectrum_hit', _isALoop),
        )),

    'nef_spectrum_dimension'         : OD((
        ('dimension_id', None),
        ('axis_unit', 'axisUnits'),
        ('axis_code', 'isotopeCodes'),
        ('spectrometer_frequency', 'spectrometerFrequencies'),
        ('spectral_width', 'spectralWidths'),
        ('value_first_point', None),
        ('folding', None),
        ('absolute_peak_positions', None),
        ('is_acquisition', None),
        ('ccpn_axis_code', 'axisCodes'),
        )),

    # NB PseudoDimensions are not yet supported
    'ccpn_spectrum_dimension'        : OD((
        ('dimension_id', None),
        ('point_count', 'pointCounts'),
        ('reference_point', 'referencePoints'),
        ('total_point_count', 'totalPointCounts'),
        ('point_offset', 'pointOffsets'),
        ('assignment_tolerance', 'assignmentTolerances'),
        ('lower_aliasing_limit', None),
        ('higher_aliasing_limit', None),
        ('measurement_type', 'measurementTypes'),
        ('phase_0', 'phases0'),
        ('phase_1', 'phases1'),
        ('window_function', 'windowFunctions'),
        ('lorentzian_broadening', 'lorentzianBroadenings'),
        ('gaussian_broadening', 'gaussianBroadenings'),
        ('sine_window_shift', 'sineWindowShifts'),
        ('dimension_is_complex', '_wrappedData.dataStore.isComplex'),
        ('dimension_block_size', '_wrappedData.dataStore.blockSizes'),
        )),

    'nef_spectrum_dimension_transfer': OD((
        ('dimension_1', None),
        ('dimension_2', None),
        ('transfer_type', None),
        ('is_indirect', None),
        )),

    'ccpn_peak_list'                 : OD((
        ('ccpn_peaklist_serial', 'serial'),
        ('ccpn_peaklist_comment', 'comment'),
        ('ccpn_peaklist_name', 'title'),
        ('ccpn_peaklist_is_simulated', 'isSimulated'),
        ('ccpn_peaklist_symbol_colour', 'symbolColour'),
        ('ccpn_peaklist_symbol_style', 'symbolStyle'),
        ('ccpn_peaklist_text_colour', 'textColour'),
        )),

    # NBNB: boxWidths and lineWidths are NOT included.
    'nef_peak'                       : OD((
        # # NOTE:ED - testing multiple peak lists per spectrum
        # ('peak_list_serial', 'peakList.serial'),

        ('index', None),
        ('peak_id', 'serial'),
        ('volume', 'volume'),
        ('volume_uncertainty', 'volumeError'),
        ('height', 'height'),
        ('height_uncertainty', 'heightError'),
        ('position_1', None),
        ('position_uncertainty_1', None),
        ('position_2', None),
        ('position_uncertainty_2', None),
        ('position_3', None),
        ('position_uncertainty_3', None),
        ('position_4', None),
        ('position_uncertainty_4', None),
        ('position_5', None),
        ('position_uncertainty_5', None),
        ('position_6', None),
        ('position_uncertainty_6', None),
        ('position_7', None),
        ('position_uncertainty_7', None),
        ('position_8', None),
        ('position_uncertainty_8', None),
        ('position_9', None),
        ('position_uncertainty_9', None),
        ('position_10', None),
        ('position_uncertainty_10', None),
        ('position_11', None),
        ('position_uncertainty_11', None),
        ('position_12', None),
        ('position_uncertainty_12', None),
        ('position_13', None),
        ('position_uncertainty_13', None),
        ('position_14', None),
        ('position_uncertainty_14', None),
        ('position_15', None),
        ('position_uncertainty_15', None),
        ('chain_code_1', None),
        ('sequence_code_1', None),
        ('residue_name_1', None),
        ('atom_name_1', None),
        ('chain_code_2', None),
        ('sequence_code_2', None),
        ('residue_name_2', None),
        ('atom_name_2', None),
        ('chain_code_3', None),
        ('sequence_code_3', None),
        ('residue_name_3', None),
        ('atom_name_3', None),
        ('chain_code_4', None),
        ('sequence_code_4', None),
        ('residue_name_4', None),
        ('atom_name_4', None),
        ('chain_code_5', None),
        ('sequence_code_5', None),
        ('residue_name_5', None),
        ('atom_name_5', None),
        ('chain_code_6', None),
        ('sequence_code_6', None),
        ('residue_name_6', None),
        ('atom_name_6', None),
        ('chain_code_7', None),
        ('sequence_code_7', None),
        ('residue_name_7', None),
        ('atom_name_7', None),
        ('chain_code_8', None),
        ('sequence_code_8', None),
        ('residue_name_8', None),
        ('atom_name_8', None),
        ('chain_code_9', None),
        ('sequence_code_9', None),
        ('residue_name_9', None),
        ('atom_name_9', None),
        ('chain_code_10', None),
        ('sequence_code_10', None),
        ('residue_name_10', None),
        ('atom_name_10', None),
        ('chain_code_11', None),
        ('sequence_code_11', None),
        ('residue_name_11', None),
        ('atom_name_11', None),
        ('chain_code_12', None),
        ('sequence_code_12', None),
        ('residue_name_12', None),
        ('atom_name_12', None),
        ('chain_code_13', None),
        ('sequence_code_13', None),
        ('residue_name_13', None),
        ('atom_name_13', None),
        ('chain_code_14', None),
        ('sequence_code_14', None),
        ('residue_name_14', None),
        ('atom_name_14', None),
        ('chain_code_15', None),
        ('sequence_code_15', None),
        ('residue_name_15', None),
        ('atom_name_15', None),
        ('ccpn_figure_of_merit', 'figureOfMerit'),
        ('ccpn_linked_integral', None),
        ('ccpn_annotation', 'annotation'),
        ('ccpn_comment', 'comment'),
        )),

    # NB SpectrumHit crosslink to sample and sampleComponent are derived
    # And need not be stored here.
    'ccpn_spectrum_hit'              : OD((
        ('ccpn_substance_name', 'substanceName'),
        ('ccpn_pseudo_dimension_number', 'pseudoDimensionNumber'),
        ('ccpn_point_number', 'pointNumber'),
        ('ccpn_figure_of_merit', 'figureOfMerit'),
        ('ccpn_merit_code', 'meritCode'),
        ('ccpn_normalised_change', 'normalisedChange'),
        ('ccpn_is_confirmed_', 'isConfirmed'),
        ('ccpn_concentration', 'concentration'),
        ('ccpn_', 'concentrationError'),
        ('ccpn_concentration_uncertainty', 'concentrationUnit'),
        ('ccpn_comment', 'comment'),
        )),

    'nef_peak_restraint_links'       : OD((
        ('nef_peak_restraint_link', _isALoop),
        )),

    'nef_peak_restraint_link'        : OD((
        ('nmr_spectrum_id', None),
        ('peak_id', None),
        ('restraint_list_id', None),
        ('restraint_id', None),
        )),

    'ccpn_complex'                   : OD((
        ('name', 'name'),
        ('ccpn_complex_chain', _isALoop),
        )),

    'ccpn_complex_chain'             : OD((
        ('complex_chain_code', None),
        )),

    'ccpn_spectrum_group'            : OD((
        ('name', 'name'),
        ('ccpn_group_spectrum', _isALoop),
        )),

    'ccpn_group_spectrum'            : OD((
        ('nmr_spectrum_id', None),
        )),

    'ccpn_integral_list'             : OD((
        ('serial', 'serial'),
        ('name', 'title'),
        ('symbol_colour', 'symbolColour'),
        ('text_colour', 'textColour'),
        ('comment', 'comment'),
        )),

    'ccpn_integral'                  : OD((
        ('integral_list_serial', 'integralList.serial'),
        ('integral_serial', 'serial'),
        ('value', 'value'),
        ('value_uncertainty', 'valueError'),
        # ('volume', 'volume'),
        # ('volume_uncertainty', 'volumeError'),
        # ('height', 'height'),
        # ('height_uncertainty', 'heightError'),
        ('offset', 'offset'),
        ('figure_of_merit', 'figureOfMerit'),
        ('constraint_weight', 'constraintWeight'),
        # ('position', 'position'),
        # ('position_uncertainty', 'positionError'),
        ('slopes', 'slopes'),
        ('limits', 'limits'),
        ('point_limits', 'pointLimits'),
        ('ccpn_linked_peak', None),
        ('annotation', 'annotation'),
        ('comment', 'comment'),
        )),

    'ccpn_multiplet_list'            : OD((
        ('serial', 'serial'),
        ('name', 'title'),
        ('symbol_colour', 'symbolColour'),
        ('text_colour', 'textColour'),
        ('comment', 'comment'),
        )),

    'ccpn_multiplet'                 : OD((
        ('multiplet_list_serial', 'multipletList.serial'),
        ('multiplet_serial', 'serial'),
        ('height', 'height'),
        ('height_uncertainty', 'heightError'),
        ('volume', 'volume'),
        ('volume_uncertainty', 'volumeError'),
        ('offset', 'offset'),
        ('figure_of_merit', 'figureOfMerit'),
        ('constraint_weight', 'constraintWeight'),
        ('position', 'position'),
        ('position_uncertainty', 'positionError'),
        ('slopes', 'slopes'),
        ('limits', 'limits'),
        ('point_limits', 'pointLimits'),
        ('annotation', 'annotation'),
        ('comment', 'comment'),
        )),

    'ccpn_multiplet_peaks'           : OD((
        ('multiplet_list_serial', None),
        ('multiplet_serial', None),
        ('multiplet_peak', None),
        )),

    'ccpn_peak_cluster_list'         : OD((
        # ('serial',None),
        # ('comment','comment'),
        ('ccpn_peak_clusters', _isALoop),
        ('ccpn_peak_cluster_peaks', _isALoop),
        )),

    'ccpn_peak_clusters'             : OD((
        ('serial', None),
        ('annotation', 'annotation'),
        # ('peak', None),
        # ('ccpn_peak_cluster',_isALoop),
        )),

    'ccpn_peak_cluster_peaks'        : OD((
        ('serial', None),
        ('peak', None),
        # ('name',None),
        # ('comment',None),
        )),

    # NB Sample crosslink to spectrum is handled on the spectrum side
    'ccpn_sample'                    : OD((
        ('name', 'name'),
        ('pH', 'ph'),
        ('ionic_strength', 'ionicStrength'),
        ('amount', 'amount'),
        ('amount_unit', 'amountUnit'),
        ('is_hazardous', 'isHazardous'),
        ('is_virtual', 'isVirtual'),
        ('creation_date', 'creationDate'),
        ('batch_identifier', 'batchIdentifier'),
        ('plate_identifier', 'plateIdentifier'),
        ('row_number', 'rowNumber'),
        ('column_number', 'columnNumber'),
        ('comment', 'comment'),
        ('ccpn_sample_component', _isALoop),
        )),

    'ccpn_sample_component'          : OD((
        ('name', 'name'),
        ('labelling', 'labelling'),
        ('role', 'role'),
        ('concentration', 'concentration'),
        ('concentration_error', 'concentrationError'),
        ('concentration_unit', 'concentrationUnit'),
        ('purity', 'purity'),
        ('comment', 'comment'),
        )),

    'ccpn_substance'                 : OD((
        ('name', 'name'),
        ('labelling', 'labelling'),
        ('substance_type', None),
        ('user_code', 'userCode'),
        ('smiles', 'smiles'),
        ('inchi', 'inChi'),
        ('cas_number', 'casNumber'),
        ('empirical_formula', 'empiricalFormula'),
        ('sequence_string', None),
        ('mol_type', None),
        ('start_number', None),
        ('is_cyclic', None),
        ('molecular_mass', 'molecularMass'),
        ('atom_count', 'atomCount'),
        ('bond_count', 'bondCount'),
        ('ring_count', 'ringCount'),
        ('h_bond_donor_count', 'hBondDonorCount'),
        ('h_bond_acceptor_count', 'hBondAcceptorCount'),
        ('polar_surface_area', 'polarSurfaceArea'),
        ('log_partition_coefficient', 'logPartitionCoefficient'),
        ('comment', 'comment'),
        ('ccpn_substance_synonym', _isALoop),
        )),

    'ccpn_substance_synonym'         : OD((
        ('synonym', None),
        )),

    'ccpn_assignment'                : OD((
        ('nmr_chain', _isALoop),
        ('nmr_residue', _isALoop),
        ('nmr_atom', _isALoop),
        )),

    'nmr_chain'                      : OD((
        ('short_name', 'shortName'),
        ('serial', None),
        ('label', 'label'),
        ('is_connected', 'isConnected'),
        ('comment', 'comment'),
        )),

    'nmr_residue'                    : OD((
        ('chain_code', 'nmrChain.shortName'),
        ('sequence_code', 'sequenceCode'),
        # ('residue_name',None),
        ('residue_name', 'residueType'),
        ('serial', None),
        ('comment', 'comment'),
        )),

    'nmr_atom'                       : OD((
        ('chain_code', 'nmrResidue.nmrChain.shortName'),
        ('sequence_code', 'nmrResidue.sequenceCode'),
        ('serial', None),
        ('name', 'name'),
        ('isotope_code', 'isotopeCode'),
        ('comment', 'comment'),
        )),

    'ccpn_dataset'                   : OD((
        ('serial', 'serial'),
        ('title', 'title'),
        ('program_name', 'programName'),
        ('program_version', 'programVersion'),
        ('data_path', 'dataPath'),
        ('creation_date', None),
        ('uuid', 'uuid'),
        ('comment', 'comment'),
        ('ccpn_calculation_step', _isALoop),
        ('ccpn_calculation_data', _isALoop),
        )),

    'ccpn_calculation_step'          : OD((
        ('serial', None),
        ('program_name', 'programName'),
        ('program_version', 'programVersion'),
        ('script_name', 'scriptName'),
        ('script', 'script'),
        ('input_data_uuid', 'inputDataUuid'),
        ('output_data_uuid', 'outputDataUuid'),
        )),

    'ccpn_calculation_data'          : OD((
        ('data_name', 'name'),
        ('attached_object_pid', 'attachedObjectPid'),
        ('parameter_name', None),
        ('parameter_value', None),
        )),

    'ccpn_restraint_list'            : OD((
        ('potential_type', 'potentialType'),
        ('restraint_origin', 'origin'),
        ('tensor_chain_code', 'tensorChainCode'),
        ('tensor_sequence_code', 'tensorSequenceCode'),
        ('tensor_residue_name', 'tensorResidueType'),
        ('tensor_magnitude', 'tensorMagnitude'),
        ('tensor_rhombicity', 'tensorRhombicity'),
        ('tensor_isotropic_value', 'tensorIsotropicValue'),
        # NB These tags have 'ccpn' prefix to match corresponding nef restraitn lists
        ('ccpn_serial', 'serial'),
        ('ccpn_dataset_serial', 'dataSet.serial'),
        ('name', 'name'),
        ('restraint_type', 'restraintType'),
        ('restraint_item_length', 'restraintItemLength'),
        ('unit', 'unit'),
        ('measurement_type', 'measurementType'),
        ('comment', 'comment'),
        ('ccpn_restraint', _isALoop),
        )),

    'ccpn_restraint'                 : OD((
        ('index', None),
        ('restraint_id', 'restraint.serial'),
        ('restraint_combination_id', 'combinationId'),
        ('chain_code_1', None),
        ('sequence_code_1', None),
        ('residue_name_1', None),
        ('atom_name_1', None),
        ('chain_code_2', None),
        ('sequence_code_2', None),
        ('residue_name_2', None),
        ('atom_name_2', None),
        ('chain_code_3', None),
        ('sequence_code_3', None),
        ('residue_name_3', None),
        ('atom_name_3', None),
        ('chain_code_4', None),
        ('sequence_code_4', None),
        ('residue_name_4', None),
        ('atom_name_4', None),
        ('weight', 'weight'),
        ('target_value', 'targetValue'),
        ('target_value_uncertainty', 'error'),
        ('lower_linear_limit', 'additionalLowerLimit'),
        ('lower_limit', 'lowerLimit'),
        ('upper_limit', 'upperLimit'),
        ('upper_linear_limit', 'additionalUpperLimit'),
        ('scale', 'scale'),
        ('distance_dependent', 'isDistanceDependent'),
        ('name', None),
        ('vector_length', 'restraint.vectorLength'),
        ('figure_of_merit', 'restraint.figureOfMerit'),
        # NB This tag has 'ccpn' prefix to match corresponding nef restraint lists
        ('ccpn_comment', 'restraint.comment'),
        )),

    'ccpn_notes'                     : OD((
        ('ccpn_note', _isALoop),
        )),

    'ccpn_note'                      : OD((
        ('serial', None),
        ('name', 'name'),
        ('created', None),
        ('last_modified', None),
        ('text', 'text'),
        )),

    'ccpn_additional_data'           : OD((
        ('ccpn_internal_data', _isALoop),
        )),

    'ccpn_internal_data'             : OD((
        ('ccpn_object_pid', None),
        ('internal_data_string', None)
        )),

    }


def saveNefProject(project: Project,
                   path: str,
                   overwriteExisting: bool = False,
                   skipPrefixes=()):
    """Save project NEF file to path"""

    dirPath, fileName = os.path.split(path)
    if not fileName:
        # we got a directory - derive filename from project
        fileName = project.name + '.nef'

    filePath = os.path.join(dirPath, fileName)

    if os.path.exists(filePath) and not overwriteExisting:
        raise IOError("%s already exists" % filePath)

    text = convert2NefString(project, skipPrefixes=skipPrefixes)

    if dirPath and not os.path.isdir(dirPath):
        os.makedirs(dirPath)

    open(filePath, 'w').write(text)


def exportNef(project: Project,
              path: str,
              overwriteExisting: bool = False,
              skipPrefixes: typing.Sequence = (),
              expandSelection: bool = True,
              # exclusionDict={},
              pidList: typing.Sequence = None):
    """export NEF file to path"""

    if path[-4:] != '.nef':
        path = path + '.nef'
        getLogger().debug('Adding .nef extension to filename %s' % path)

    if os.path.exists(path) and not overwriteExisting:
        raise IOError("%s already exists" % path)

    text = convert2NefString(project, skipPrefixes=skipPrefixes, expandSelection=expandSelection,
                             pidList=pidList)  #, exclusionDict=exclusionDict)

    dirPath, fileName = os.path.split(path)
    if dirPath and not os.path.isdir(dirPath):
        os.makedirs(dirPath)

    with open(path, 'w') as f:  # save write
        f.write(text)


def convertToDataBlock(project: Project,
                       # path:str,
                       # overwriteExisting:bool=False,
                       skipPrefixes: typing.Sequence = (),
                       expandSelection: bool = True,
                       # exclusionDict={},
                       pidList: typing.Sequence = None):
    """export NEF file to path"""
    # ejb - dialog added to allow the changing of the name from the current project name.

    dataBlock = convertToCcpnDataBlock(project, skipPrefixes=skipPrefixes, expandSelection=expandSelection,
                                       pidList=pidList)  #, exclusionDict=exclusionDict)

    return dataBlock


def writeDataBlock(dataBlock, path: str, overwriteExisting: bool = False):
    if path[-4:] != '.nef':
        path = path + '.nef'
        getLogger().debug('Adding .nef extension to filename %s' % path)

    if os.path.exists(path) and not overwriteExisting:
        raise IOError("%s already exists" % path)

    dirPath, fileName = os.path.split(path)
    if dirPath and not os.path.isdir(dirPath):
        os.makedirs(dirPath)

    with open(path, 'w') as f:  # save write
        f.write(dataBlock.toString())


def convert2NefString(project: Project, skipPrefixes: typing.Sequence = (), expandSelection: bool = True,
                      pidList: list = None):  #, exclusionDict:dict={}):
    """Convert project to NEF string"""

    converter = CcpnNefWriter(project)

    dataBlock = converter.exportProject(expandSelection=expandSelection, pidList=pidList)  #, exclusionDict=exclusionDict)

    # Delete tags starting with certain prefixes.
    # NB designed to strip out 'ccpn' tags to make output comparison easier
    for prefix in skipPrefixes:
        # Could be done faster, but this is a rare operation
        for sftag in list(dataBlock.keys()):
            if sftag.startswith(prefix):
                del dataBlock[sftag]
            else:
                sf = dataBlock[sftag]
                for tag in list(sf.keys()):
                    if tag.startswith(prefix):
                        del sf[tag]
                    else:
                        val = sf[tag]
                        if isinstance(val, StarIo.NmrLoop):
                            # This is a loop:
                            for looptag in val.columns:
                                # NB val.columns is a tuple (encapsulation) and will not change during the loop
                                if looptag.startswith(prefix):
                                    val.removeColumn(looptag, removeData=True)

    return dataBlock.toString()


def convertToCcpnDataBlock(project: Project, skipPrefixes: typing.Sequence = (), expandSelection: bool = True,
                           pidList: list = None):  #, exclusionDict:dict={}):
    """Convert project to NEF string"""

    converter = CcpnNefWriter(project)

    dataBlock = converter.exportProject(expandSelection=expandSelection, pidList=pidList)  #, exclusionDict=exclusionDict)

    # Delete tags starting with certain prefixes.
    # NB designed to strip out 'ccpn' tags to make output comparison easier
    for prefix in skipPrefixes:
        # Could be done faster, but this is a rare operation
        for sftag in list(dataBlock.keys()):
            if sftag.startswith(prefix):
                del dataBlock[sftag]
            else:
                sf = dataBlock[sftag]
                for tag in list(sf.keys()):
                    if tag.startswith(prefix):
                        del sf[tag]
                    else:
                        val = sf[tag]
                        if isinstance(val, StarIo.NmrLoop):
                            # This is a loop:
                            for looptag in val.columns:
                                # NB val.columns is a tuple (encapsulation) and will not change during the loop
                                if looptag.startswith(prefix):
                                    val.removeColumn(looptag, removeData=True)

    return dataBlock


class CcpnNefWriter:
    """CCPN NEF reader/writer"""

    def __init__(self, project: Project, specificationFile: str = None, mode: str = 'strict',
                 programName: str = None, programVersion: str = None):
        self.project = project
        self.mode = mode
        if specificationFile is None:
            self.specification = None
        else:
            # NBNB TBD reconsider whether we want the spec summary or something else
            self.specification = Specification.getCcpnSpecification(specificationFile)

        if hasattr(project, '_appBase'):
            programName = programName or project._appBase.applicationName
            programVersion = programVersion or project._appBase.applicationVersion
        self.programName = programName or 'CcpnNefWriter'
        self.programVersion = programVersion
        self.ccpn2SaveFrameName = {}

    def exportObjects(self, expandSelection: bool = True,
                      chains: typing.Sequence[Chain] = (),
                      chemicalShiftLists: typing.Sequence[ChemicalShiftList] = (),
                      restraintLists: typing.Sequence[RestraintList] = (),
                      peakLists: typing.Sequence[PeakList] = (),
                      integralLists: typing.Sequence[IntegralList] = (),
                      multipletLists: typing.Sequence[MultipletList] = (),
                      samples: typing.Sequence[Sample] = (),
                      substances: typing.Sequence[Substance] = (),
                      nmrChains: typing.Sequence[NmrChain] = (),
                      dataSets: typing.Sequence[DataSet] = (),
                      complexes: typing.Sequence[Complex] = (),
                      spectrumGroups: typing.Sequence[SpectrumGroup] = (),
                      notes: typing.Sequence[Note] = (),
                      peakClusters: typing.Sequence[PeakCluster] = (), ):
        """Export objects passed in and objects they are linked to.

            if expandSelection is True (strongly recommended):
            Will add PeakLists (Spectra) from SpectrumGroups (first peakList only),
            Samples and ChemicalShiftLists from peakLists (Spectra)
            Samples from SpectrumHits,
            Substances from Samples
            RestraintLists from DataSets
            NmrChains from ChemicalShifts
            and Chains from Substances, SampleComponents, NmrChains, and Complexes"""

        # set-up
        self.ccpn2SaveFrameName = {}
        saveFrames = []
        project = self.project

        if expandSelection:
            # Add linked-to objects - we can not skip these without altering the data:

            # SpectrumGroups and PeakLists
            peakLists = list(peakLists)
            integralLists = list(integralLists)
            multipletLists = list(multipletLists)

            spectrumSet = set(x.spectrum for x in peakLists)
            for spectrumGroup in spectrumGroups:
                for spectrum in spectrumGroup.spectra:
                    if spectrum not in spectrumSet:
                        spectrumSet.add(spectrum)

                        pl = spectrum.peakLists
                        if pl:
                            # Add one of the peakLists
                            peakLists.append(pl[0])
                        else:
                            peakLists.append(spectrum.newPeakList())

                        il = spectrum.integralLists
                        if il:
                            # Add one of the peakLists
                            integralLists.append(il[0])
                        else:
                            integralLists.append(spectrum.newIntegralList())

                        ml = spectrum.multipletLists
                        if ml:
                            # Add one of the peakLists
                            multipletLists.append(ml[0])
                        else:
                            multipletLists.append(spectrum.newMultipletList())
            peakLists = sorted(peakLists)
            integralLists = sorted(integralLists)
            multipletLists = sorted(multipletLists)

            # PeakClusters
            peakClusterLists = set(peakClusters)
            for peakCluster in peakClusterLists:
                peakClusterLists.add(peakCluster)
            peakClusterLists = sorted(peakClusters)

            # ChemicalShiftLists
            chemicalShiftListSet = set(chemicalShiftLists)
            for peakList in peakLists:
                xx = peakList.chemicalShiftList
                if xx is None:
                    raise ValueError(
                            "PeakList %s has no ChemicalShiftList attached and cannot be exported to NEF")
                else:
                    chemicalShiftListSet.add(xx)
            chemicalShiftLists = sorted(chemicalShiftListSet)

            # Samples
            sampleSet = set(samples)
            for spectrum in spectrumSet:
                sample = spectrum.sample
                if sample is not None:
                    sampleSet.add(sample)
                for spectrumHit in spectrum.spectrumHits:
                    sample = spectrumHit.sample
                    if sample is not None:
                        sampleSet.add(sample)
            samples = sorted(sampleSet)

            # restraintLists
            restraintListSet = set(restraintLists)
            for dataSet in dataSets:
                restraintListSet.update(dataSet.restraintLists)
            restraintLists = sorted(restraintListSet)

            # ChemicalShiftLists and NmrChains
            nmrChainSet = set(nmrChains)
            for chemicalShiftList in chemicalShiftLists:
                for chemicalShift in chemicalShiftList.chemicalShifts:
                    nmrChainSet.add(chemicalShift.nmrAtom.nmrResidue.nmrChain)
            nmrChains = sorted(nmrChainSet)

            # NmrChains and Chains
            chainSet = set(chains)
            for nmrChain in nmrChains:
                chain = nmrChain.chain
                if chain is not None:
                    chainSet.add(chain)

            # Complexes and Chains
            for complex in complexes:
                chainSet.update(complex.chains)

            # Samples, Substances and Chains
            substanceSet = set(substances)
            for sample in samples:
                for sampleComponent in sample.sampleComponents:
                    substance = sampleComponent.substance
                    if substance is not None:
                        substanceSet.add(substance)
                    # chain = sampleComponent.chain
                    # if chain is not None:
                    #     chainSet.add(chain)
            substances = sorted(substanceSet)

            # Substances and Chains
            for substance in substances:
                for chain in substance.chains:  # ejb - modified
                    if chain is not None:
                        chainSet.add(chain)
            chains = sorted(chainSet)

        # MetaData
        saveFrames.append(self.makeNefMetaData(project))

        # Chains
        saveFrames.append(self.chains2Nef(sorted(chains)))

        # CCPN assignment
        saveFrames.append(self.ccpnAssignentToNef(nmrChains))

        # ChemicalShiftLists
        for obj in sorted(chemicalShiftLists):
            saveFrames.append(self.chemicalShiftList2Nef(obj))

        # RestraintLists and
        restraintLists = sorted(restraintLists, key=attrgetter('restraintType', 'serial'))
        singleDataSet = bool(restraintLists) and len(set(x.dataSet for x in restraintLists)) == 1
        for obj in restraintLists:
            saveFrames.append(self.restraintList2Nef(obj, singleDataSet=singleDataSet))

        # NOTE:ED - need to make an active list of spectra and export from there with the required
        #           PeakLists/IntegralLists/MultipletLists

        # Spectra/PeakLists/IntegralLists/MultipletLists
        # NOTE:ED - this is a stupid hack for more than one peakList per spectrum
        _exportedSpectra = set()
        for obj in sorted(peakLists):
            saveFrames.append(self.peakList2Nef(obj, integralLists, multipletLists, obj.spectrum not in _exportedSpectra))
            _exportedSpectra.add(obj.spectrum)

        # restraint-peak links
        saveFrame = self.peakRestraintLinks2Nef(restraintLists)
        if saveFrame:
            saveFrames.append(saveFrame)

        # Now add CCPN-specific data:

        # TODO temporarily blanked out, pending bug fixes
        # # NmrChains
        # saveFrames.append(self.assignments2Nef(project))

        # SpectrumGroups
        for obj in project.spectrumGroups:
            saveFrames.append(self.spectrumGroup2Nef(obj))

        # PeakClusters
        saveFrame = self.peakClusters2Nef(sorted(peakClusters))
        if saveFrame:
            saveFrames.append(saveFrame)

        # Samples
        for obj in sorted(samples):
            saveFrames.append(self.sample2Nef(obj))

        # Substances
        for obj in sorted(substances):
            saveFrames.append(self.substance2Nef(obj))

        # Complexes
        for obj in project.complexes:
            saveFrames.append(self.complex2Nef(obj))

        # TODO temporarily blanked out, pending bug fixes
        # # DataSets - NB does not include RestraintLists, which are given above
        # for obj in project.dataSets:
        #   saveFrames.append(self.dataSet2Nef(obj))

        # Notes
        saveFrame = self.notes2Nef(sorted(notes))
        if saveFrame:
            saveFrames.append(saveFrame)

        # Additional data
        saveFrame = self.additionalData2Nef(project)
        if saveFrame:
            saveFrames.append(saveFrame)

        # make and return dataBlock with saveframes in export order
        result = StarIo.NmrDataBlock(name=self.project.name)
        for saveFrame in self._saveFrameNefOrder(saveFrames):
            result.addItem(saveFrame['sf_framecode'], saveFrame)
        #
        return result

    def exportDataSet(self, dataSet: DataSet) -> StarIo.NmrDataBlock:
        """Get dataSet and all objects linked to therein as NEF object tree for export"""

        saveFrames = list()

        saveFrames.append(self.makeNefMetaData(dataSet))

        # etc.

        # make and return dataBlock with saveframes in export order
        result = StarIo.NmrDataBlock(name=dataSet.name)
        for saveFrame in self._saveFrameNefOrder(saveFrames):
            result.addItem(saveFrame['sf_framecode'], saveFrame)
        #
        return result

    # def exportProject(self, expandSelection:bool=False,
    #                   pidList:list=None,
    #                   exclusionDict:dict=None) -> typing.Optional[StarIo.NmrDataBlock]:
    def exportProject(self, expandSelection: bool = False,
                      pidList: list = None) -> typing.Optional[StarIo.NmrDataBlock]:
        """
        Get project and all contents as NEF object tree for export
        """
        project = self.project

        # ejb - added items to be removed from the list
        # gets a copy of all the lists in the project that are relevant to Nef files

        # assume that a list of pids to include is being passed in
        # if there is none

        if pidList is None:
            # use as a flag to export everything

            return self.exportObjects(expandSelection=expandSelection,
                                      chains=project.chains, chemicalShiftLists=project.chemicalShiftLists,
                                      restraintLists=project.restraintLists, peakLists=project.peakLists,
                                      integralLists=project.integralLists, multipletLists=project.multipletLists,
                                      samples=project.samples, substances=project.substances,
                                      nmrChains=project.nmrChains, dataSets=project.dataSets,
                                      complexes=project.complexes, spectrumGroups=project.spectrumGroups,
                                      notes=project.notes, peakClusters=project.peakClusters)
        else:
            # export selection of objects
            # either everything minus the exclusionDict or the list of pids
            # if pidList is not None and exclusionDict is not None:
            #   lists must be mutually exclusive
            # return None

            self.chains = []
            self.chemicalShiftLists = []
            self.restraintLists = []
            self.peakLists = []
            self.integralLists = []
            self.multipletLists = []
            self.samples = []
            self.substances = []
            self.nmrChains = []
            self.dataSets = []
            self.complexes = []
            self.spectrumGroups = []
            self.notes = []
            self.peakClusters = []

            checkList = [CHAINS, CHEMICALSHIFTLISTS, RESTRAINTLISTS, PEAKLISTS,
                         INTEGRALLISTS, MULTIPLETLISTS,
                         SAMPLES, SUBSTANCES, NMRCHAINS,
                         DATASETS, COMPLEXES, SPECTRUMGROUPS, NOTES, PEAKCLUSTERS]

            # put the pids in the correct lists
            for name in checkList:
                attrib = getattr(self, name)
                for aPid in pidList:
                    pidObj = project.getByPid(aPid)
                    if pidObj is not None and pidObj._pluralLinkName == name:  # need to check this
                        attrib.append(pidObj)

                # if name in exclusionDict:        # if not in list then still write all values
                #   # setattr(self, name, [])           # make it an empty list
                #   attrib = getattr(self, name)
                #   for obj in getattr(project, name):
                #     if obj.pid in exclusionDict[name]:
                #       # attrib.append(obj)              # append the found items to the list
                #       attrib.remove(obj)            # treat as exclusion list

            return self.exportObjects(expandSelection=expandSelection,
                                      chains=self.chains, chemicalShiftLists=self.chemicalShiftLists,
                                      restraintLists=self.restraintLists, peakLists=self.peakLists,
                                      integralLists=self.integralLists, multipletLists=self.multipletLists,
                                      samples=self.samples, substances=self.substances,
                                      nmrChains=self.nmrChains, dataSets=self.dataSets,
                                      complexes=self.complexes, spectrumGroups=self.spectrumGroups,
                                      notes=self.notes, peakClusters=self.peakClusters)

        # self.ccpn2SaveFrameName = {}
        # saveFrames = []
        #
        # project = self.project
        #
        # # MetaData
        # saveFrames.append(self.makeNefMetaData(project))
        #
        # # Chains
        # saveFrames.append(self.chains2Nef(sorted(project.chains)))
        #
        # # ChemicalShiftLists
        # for obj in sorted(project.chemicalShiftLists):
        #     saveFrames.append(self.chemicalShiftList2Nef(obj))
        #
        # # RestraintLists and
        # restraintLists = sorted(project.restraintLists,
        #                         key=attrgetter('restraintType', 'serial'))
        # singleDataSet = bool(restraintLists) and len(set(x.dataSet for x in restraintLists)) == 1
        # for obj in restraintLists:
        #     saveFrames.append(self.restraintList2Nef(obj, singleDataSet=singleDataSet))
        #
        # # Spectra
        # for obj in sorted(project.spectra):
        #     # NB we get multiple saveframes, one per peakList
        #     saveFrames.extend(self.spectrum2Nef(obj))
        #
        # # restraint-peak links
        # saveFrame = self.peakRestraintLinks2Nef(restraintLists)
        # if saveFrame:
        #     saveFrames.append(saveFrame)
        #
        # # Now add CCPN-specific data:
        #
        # # PeakClusters
        # saveFrames.append(self.peakClusters2Nef(project))
        #
        # # NmrChains
        # saveFrames.append(self.assignments2Nef(project))
        #
        # # SpectrumGroups
        # for obj in project.spectrumGroups:
        #     saveFrames.append(self.spectrumGroup2Nef(obj))
        #
        # # Samples
        # for obj in sorted(project.samples):
        #     saveFrames.append(self.sample2Nef(obj))
        #
        # # Substances
        # for obj in sorted(project.substances):
        #     saveFrames.append(self.substance2Nef(obj))
        #
        # # # DataSets - NB does not include RestraintLists, which are given above
        # # for obj in project.dataSets:
        # #   saveFrames.append(self.dataSet2Nef(obj))
        #
        # # Notes
        # saveFrame = self.notes2Nef(sorted(project.notes))
        # if saveFrame:
        #     saveFrames.append(saveFrame)
        #
        # # Additional data
        # saveFrame = self.additionalData2Nef(project)
        # if saveFrame:
        #     saveFrames.append(saveFrame)
        #
        # # make and return dataBlock with saveframes in export order
        # result = StarIo.NmrDataBlock(name=self.project.name)
        # for saveFrame in self._saveFrameNefOrder(saveFrames):
        #     result.addItem(saveFrame['sf_framecode'], saveFrame)
        # #
        # return result

    def makeNefMetaData(self, headObject: Union[Project, DataSet],
                        coordinateFileName: str = None) -> StarIo.NmrSaveFrame:
        """make NEF metadata saveframe from Project"""

        # NB No attributes can be set from map here, so we do not try

        category = 'nef_nmr_meta_data'
        result = self._newNefSaveFrame(headObject, category, category)

        # NBNB TBD FIXME add proper values for format version from specification file
        result['format_name'] = 'nmr_exchange_format'
        result['format_version'] = currentNefVersion
        # format_version=None
        result['coordinate_file_name'] = coordinateFileName
        if headObject.className == 'Project':
            result['program_name'] = self.programName
            result['program_version'] = self.programVersion
            result['creation_date'] = timeStamp = commonUtil.getTimeStamp()
            result['uuid'] = '%s-%s-%s' % (self.programName, timeStamp, random.randint(0, maxRandomInt))

            # This attribute is only present when exporting DataSets
            del result['ccpn_dataset_comment']
            # This loop is only set when exporting DataSets
            del result['nef_related_entries']
            # This loop is only set when exporting DataSets
            del result['nef_run_history']

            loop = result['nef_program_script']
            loop.newRow(dict(program_name='CcpNmr', script_name='exportProject'))

        else:
            assert headObject.className == 'DataSet', "Parameter must be a Project or DataSet"
            result['program_name'] = headObject.programName
            result['program_version'] = headObject.programVersion
            result['creation_date'] = headObject.creationDate
            result['uuid'] = headObject.uuid
            result['ccpn_dataset_comment'] = headObject.comment

            # NBNB TBD FIXME nef_related_entries is still to be implemented
            del result['nef_related_entries']

            loop = result['nef_run_history']
            # NBNB TBD FIXME nef_run_history is still to be wrapped
            del result['nef_run_history']
        #
        return result

    def chains2Nef(self, chains: List[Chain]) -> StarIo.NmrSaveFrame:
        """Convert selected Chains to CCPN NEF saveframe"""

        category = 'nef_molecular_system'
        if chains:
            project = chains[0].project
            result = self._newNefSaveFrame(project, category, category)

            loopName = 'nef_sequence'
            loop = result[loopName]

            index = 0
            for chain in chains:
                for residue in sorted(chain.residues):
                    index += 1
                    rowdata = self._loopRowData(loopName, residue)
                    rowdata['index'] = index
                    loop.newRow(rowdata)

            loop = result['nef_covalent_links']
            columns = ('chain_code_1', 'sequence_code_1', 'residue_name_1', 'atom_name_1',
                       'chain_code_2', 'sequence_code_2', 'residue_name_2', 'atom_name_2'
                       )

            boundAtomPairs = extraBoundAtomPairs(project, selectSequential=False)

            if boundAtomPairs:
                for atom1, atom2 in boundAtomPairs:
                    if atom1.residue.chain in chains and atom2.residue.chain:
                        loop.newRow(dict(zip(columns, (atom1._idTuple + atom2._idTuple))))
            else:
                del result['nef_covalent_links']
            #
            return result

        else:
            return self._newNefSaveFrame(None, category, category)

    def peakClusters2Nef(self, peakClusters) -> StarIo.NmrSaveFrame:
        """Convert PeakClusters to saveframe"""

        category = 'ccpn_peak_cluster_list'
        if peakClusters:
            result = self._newNefSaveFrame(peakClusters[0].project, category, category)

            loopName = 'ccpn_peak_clusters'
            loop = result[loopName]
            for peakCluster in sorted(peakClusters[0].project.peakClusters):
                row = loop.newRow(self._loopRowData(loopName, peakCluster))
                row['serial'] = peakCluster.serial

            loopName = 'ccpn_peak_cluster_peaks'
            loop = result[loopName]
            for peakCluster in sorted(peakClusters[0].project.peakClusters):

                for peak in peakCluster.peaks:
                    row = loop.newRow(self._loopRowData(loopName, peak))
                    row['serial'] = peakCluster.serial
                    row['peak'] = peak.pid

            return result

    def assignments2Nef(self, project: Project) -> StarIo.NmrSaveFrame:
        """Convert NmrChains, NmrResidues and NmrAtoms to saveframe"""

        category = 'ccpn_assignment'
        result = self._newNefSaveFrame(project, category, category)

        nmrChainLoopName = 'nmr_chain'
        nmrChainLoop = result[nmrChainLoopName]
        nmrResidueLoopName = 'nmr_residue'
        nmrResidueLoop = result[nmrResidueLoopName]
        nmrAtomLoopName = 'nmr_atom'
        nmrAtomLoop = result[nmrAtomLoopName]

        for nmrChain in sorted(project.nmrChains):
            rowdata = self._loopRowData(nmrChainLoopName, nmrChain)
            rowdata['serial'] = nmrChain.serial
            nmrChainLoop.newRow(rowdata)

            # Use sorting - should give correct results
            for nmrResidue in sorted(nmrChain.nmrResidues):
                rowdata = self._loopRowData(nmrResidueLoopName, nmrResidue)
                rowdata['serial'] = nmrResidue.serial
                rowdata['residue_name'] = nmrResidue.residueType or None
                nmrResidueLoop.newRow(rowdata)

                for nmrAtom in sorted(nmrResidue.nmrAtoms):
                    rowdata = self._loopRowData(nmrAtomLoopName, nmrAtom)
                    rowdata['serial'] = nmrAtom.serial
                    nmrAtomLoop.newRow(rowdata)
        #
        return result

    def chemicalShiftList2Nef(self, chemicalShiftList: ChemicalShiftList) -> StarIo.NmrSaveFrame:
        """Convert ChemicalShiftList to CCPN NEF saveframe"""

        # Set up frame
        category = 'nef_chemical_shift_list'
        result = self._newNefSaveFrame(chemicalShiftList, category, chemicalShiftList.name)

        self.ccpn2SaveFrameName[chemicalShiftList] = result['sf_framecode']

        # Fill in loop - use dictionary rather than list as this is more robust against reorderings
        loopName = 'nef_chemical_shift'
        loop = result[loopName]
        atomCols = ['chain_code', 'sequence_code', 'residue_name', 'atom_name', ]
        # NB We cannot use nmrAtom.id.split('.'), since the id has reserved characters remapped
        shifts = sorted(chemicalShiftList.chemicalShifts)
        if shifts:
            for shift in shifts:
                rowdata = self._loopRowData(loopName, shift)
                nmrAtom = shift.nmrAtom
                rowdata.update(zip(atomCols, nmrAtom._idTuple))
                isotopeCode = nmrAtom.isotopeCode.upper()
                isotope, element = commonUtil.splitIntFromChars(isotopeCode)
                if isotope is not None:
                    rowdata['element'] = element
                    rowdata['isotope_number'] = isotope

                # Correct for atom names starting with the isotopeCode (e.g. 2HA, 111CD)
                name = rowdata['atom_name']
                if name.startswith(isotopeCode):
                    plainName = name[len(str(isotope)):]
                    if chemicalShiftList.getChemicalShift(nmrAtom.nmrResidue._id + Pid.IDSEP + plainName) is None:
                        # There is no shift in this list that has the corresponding name without the
                        # isotope number prefix. Remove the prefix for writing
                        rowdata['atom_name'] = plainName

                loop.newRow(rowdata)
        else:
            del result[loopName]
        #
        return result

    def dataSet2Nef(self, dataSet: DataSet) -> StarIo.NmrSaveFrame:
        """Convert DataSet to CCPN NEF saveframe"""

        # Set up frame
        category = 'ccpn_dataset'
        result = self._newNefSaveFrame(dataSet, category, str(dataSet.serial))

        self.ccpn2SaveFrameName[dataSet] = result['sf_framecode']

        # Fill in loops
        loopName = 'ccpn_calculation_step'
        loop = result[loopName]
        calculationSteps = dataSet.calculationSteps
        if calculationSteps:
            for calculationStep in calculationSteps:
                loop.newRow(self._loopRowData(loopName, calculationStep))
        else:
            del result[loopName]

        loopName = 'ccpn_calculation_data'
        loop = result[loopName]
        calculationData = dataSet.data
        if calculationData:
            for obj in calculationData:
                loop.newRow(self._loopRowData(loopName, obj))
        else:
            del result[loopName]
        #
        return result

    # 'ccpn_dataset':OD((
    #   ('serial','serial'),
    #   ('title','title'),
    #   ('program_name','programName'),
    #   ('program_version','programVersion'),
    #   ('data_path','dataPath'),
    #   ('creation_date',None),
    #   ('uuid','uuid'),
    #   ('comment','comment'),
    #   ('ccpn_calculation_step',_isALoop),
    #   ('ccpn_data',_isALoop),
    # )),
    #
    # 'ccpn_calculation_step':OD((
    #   ('serial', None),
    #   ('program_name','programName'),
    #   ('program_version','programVersion'),
    #   ('script_name','scriptName'),
    #   ('script','script'),
    #   ('input_data_uuid','inputDataUuid'),
    #   ('output_data_uuid','outputDataUuid'),
    # )),
    #
    # 'ccpn_calculation_data':OD((
    #   ('data_name','name'),
    #   ('attached_object_pid','attachedObjectPid'),
    #   ('parameter_name', None),
    #   ('parameter_value', None),
    # )),

    def restraintList2Nef(self, restraintList: RestraintList, singleDataSet: bool = False
                          ) -> StarIo.NmrSaveFrame:
        """Convert RestraintList to CCPN NEF saveframe"""

        project = restraintList._project

        # Set up frame
        restraintType = restraintList.restraintType
        itemLength = restraintList.restraintItemLength

        if restraintType == 'Distance':
            category = 'nef_distance_restraint_list'
            loopName = 'nef_distance_restraint'
        elif restraintType == 'Dihedral':
            category = 'nef_dihedral_restraint_list'
            loopName = 'nef_dihedral_restraint'
        elif restraintType == 'Rdc':
            category = 'nef_rdc_restraint_list'
            loopName = 'nef_rdc_restraint'
        else:
            category = 'ccpn_restraint_list'
            loopName = 'ccpn_restraint'

        max = itemLength + 1
        multipleAttributes = OD((
            ('chainCodes', tuple('chain_code_%s' % ii for ii in range(1, max))),
            ('sequenceCodes', tuple('sequence_code_%s' % ii for ii in range(1, max))),
            ('residueTypes', tuple('residue_name_%s' % ii for ii in range(1, max))),
            ('atomNames', tuple('atom_name_%s' % ii for ii in range(1, max))),
            ))

        name = restraintList.name
        if not singleDataSet:
            # If there are multiple DataSets, add the dataSet serial for disambiguation
            ss = '`%s`' % restraintList.dataSet.serial
            if not name.startswith(ss):
                name = ss + name

        result = self._newNefSaveFrame(restraintList, category, name)

        self.ccpn2SaveFrameName[restraintList] = result['sf_framecode']

        # for tag in ('tensor_magnitude', 'tensor_rhombicity', 'tensor_isotropic_value',
        #             'ccpn_tensor_magnitude', 'ccpn_tensor_rhombicity', 'ccpn_tensor_isotropic_value'):
        #   if result.get(tag) == 0:
        #     # Tensor components default to 0
        #     result[tag] = None
        #
        # tensor = restraintList.tensor
        # if tensor is not None:
        #   result['tensor_magnitude'] = tensor.axial or None
        #   result['tensor_rhombicity'] = tensor.rhombic or None
        #   if category == 'ccpn_restraint_list':
        #     result['tensor_isotropic_value'] = tensor.isotropic or None
        #   else:
        #     result['ccpn_tensor_isotropic_value'] = tensor.isotropic or None

        loop = result[loopName]

        if itemLength < 4:
            # Remove unnecessary columns
            removeNameEndings = ('_1', '_2', '_3', '_4')[itemLength:]
            for tag in loop.columns:
                if tag[-2:] in removeNameEndings:
                    loop.removeColumn(tag, removeData=True)

        index = 0
        for contribution in sorted(restraintList.restraintContributions):
            rowdata = self._loopRowData(loopName, contribution)
            for item in contribution.restraintItems:
                row = loop.newRow(rowdata)
                index += 1
                row['index'] = index

                # NBNB TBD FIXME Using the PID, as we do here, you are remapping '.' to '^'
                # NBNB reconsider!!!

                # Set individual parts of assignment one by one.
                # NB _set command takes care of varying number of items
                assignments = list(x.split('.') for x in item)
                for ii, attrName in enumerate(('chainCodes', 'sequenceCodes', 'residueTypes', 'atomNames',)):
                    for jj, tag in enumerate(multipleAttributes[attrName]):
                        row[tag] = assignments[jj][ii] or None
                if category == 'nef_dihedral_restraint_list':
                    row['name'] = RestraintLib.dihedralName(project, item)
        #
        return result

    # def spectrum2Nef(self, spectrum: Spectrum) -> StarIo.NmrSaveFrame:
    #     """Convert spectrum to NEF saveframes - one per peaklist
    #
    #     Will create a peakList if none are present"""
    #
    #     result = []
    #
    #     peakLists = sorted(spectrum.peakLists)
    #     if not peakLists:
    #         peakLists = [spectrum.newPeakList()]
    #
    #     # NOTE:ED - this is a stupid hack for more than one peakList per spectrum
    #     first = True
    #     for peakList in peakLists:
    #         result.append(self.peakList2Nef(peakList, exportCompleteSpectrum=first))
    #         first = False
    #     #
    #     return result

    def peakList2Nef(self, peakList: PeakList, integralLists, multipletLists,
                     exportCompleteSpectrum: bool = True
                     ) -> StarIo.NmrSaveFrame:
        """Convert PeakList to CCPN NEF saveframe.
        Used for all spectrum export, as there is one frame per PeakList
        """

        spectrum = peakList.spectrum

        # framecode for saveFrame that holds spectrum adn first peaklist.
        # If not None, the peakList will be read into that specttum
        spectrumAlreadySaved = bool(self.ccpn2SaveFrameName.get(spectrum))

        # We do not support sampled or unprocessed dimensions yet. NBNB TBD.
        if any(x != 'Frequency' for x in spectrum.dimensionTypes):
            raise NotImplementedError(
                    "NEF only implemented for processed frequency spectra, dimension types were: %s"
                    % (spectrum.dimensionTypes,)
                    )

        # Get unique frame name
        name = spectrum.name
        if spectrumAlreadySaved:
            # not the first time this spectrum appears.
            name = '%s`%s`' % (name, peakList.serial)
            while spectrum.project.getSpectrum(name):
                # Realistically this should never happen,
                # but it is a further (if imperfect) guard against clashes
                # This name is taken - modify it
                name = '%s`%s`' % (name, peakList.serial)

        # Set up frame
        category = 'nef_nmr_spectrum'
        result = self._newNefSaveFrame(peakList, category, name)

        path = spectrum.filePath
        if path:
            result['ccpn_spectrum_file_path'] = path

        self.ccpn2SaveFrameName[peakList] = result['sf_framecode']
        if not spectrumAlreadySaved:
            self.ccpn2SaveFrameName[spectrum] = result['sf_framecode']

        result['chemical_shift_list'] = self.ccpn2SaveFrameName.get(peakList.chemicalShiftList)
        result['ccpn_sample'] = self.ccpn2SaveFrameName.get(spectrum.sample)

        # Will give wrong values for Hz or pointNumber units, and
        # Will fill in all None for non-Frequency dimensions
        loopName = 'nef_spectrum_dimension'
        loop = result[loopName]
        data = OD()
        for neftag, attrstring in nef2CcpnMap[loopName].items():
            if attrstring is None:
                # to fill in later
                data[neftag] = [None] * spectrum.dimensionCount
            else:
                data[neftag] = attrgetter(attrstring)(spectrum)

        data['folding'] = ['none' if x is None else x for x in spectrum.foldingModes]
        data['value_first_point'] = [tt[1] for tt in spectrum.spectrumLimits]
        # NBNB All CCPN peaks are in principle at the correct unaliased positions
        # Whether they are set correctly is another matter.
        data['absolute_peak_positions'] = spectrum.dimensionCount * [True]
        acquisitionAxisCode = spectrum.acquisitionAxisCode
        if acquisitionAxisCode is None:
            data['is_acquisition'] = spectrum.dimensionCount * [None]
        else:
            data['is_acquisition'] = [(x == acquisitionAxisCode) for x in spectrum.axisCodes]

        for ii in range(spectrum.dimensionCount):
            rowdata = dict((tt[0], tt[1][ii]) for tt in data.items())
            row = loop.newRow(rowdata)
            row['dimension_id'] = ii + 1

        loopName = 'ccpn_spectrum_dimension'
        loop = result[loopName]
        data = OD()
        for neftag, attrstring in nef2CcpnMap[loopName].items():
            if attrstring is None:
                # to fill in later
                data[neftag] = [None] * spectrum.dimensionCount
            else:
                try:
                    data[neftag] = attrgetter(attrstring)(spectrum)
                except AttributeError:
                    self.project._logger.debug("Could not get %s from Spectrum %s\n" % (attrstring, spectrum))

        aliasingLimits = spectrum.aliasingLimits
        for ii in range(spectrum.dimensionCount):
            rowdata = dict((tt[0], tt[1][ii]) for tt in data.items())
            rowdata['lower_aliasing_limit'], rowdata['higher_aliasing_limit'] = aliasingLimits[ii]
            row = loop.newRow(rowdata)
            row['dimension_id'] = ii + 1

        loopName = 'nef_spectrum_dimension_transfer'
        loop = result[loopName]
        transfers = spectrum.magnetisationTransfers
        if transfers:
            for tt in transfers:
                loop.newRow(dict(zip(['dimension_1', 'dimension_2', 'transfer_type', 'is_indirect'], tt)))
        else:
            del result[loopName]

        loopName = 'nef_peak'
        loop = result[loopName]

        # Remove superfluous tags
        removeNameEndings = ('_1', '_2', '_3', '_4', '_5', '_6', '_7', '_8', '_9',
                             '_10', '_11', '_12', '_13', '_14', '_15',)[spectrum.dimensionCount:]
        for tag in loop.columns:
            if any(tag.endswith(x) for x in removeNameEndings):
                loop.removeColumn(tag)

        # Get name map for per-dimension attributes
        max = spectrum.dimensionCount + 1
        multipleAttributes = {
            'position'     : tuple('position_%s' % ii for ii in range(1, max)),
            'positionError': tuple('position_uncertainty_%s' % ii for ii in range(1, max)),
            'chainCodes'   : tuple('chain_code_%s' % ii for ii in range(1, max)),
            'sequenceCodes': tuple('sequence_code_%s' % ii for ii in range(1, max)),
            'residueTypes' : tuple('residue_name_%s' % ii for ii in range(1, max)),
            'atomNames'    : tuple('atom_name_%s' % ii for ii in range(1, max)),
            'slopes'       : tuple('slopes_%s' % ii for ii in range(1, max)),
            'lowerLimits'  : tuple('lower_limits_%s' % ii for ii in range(1, max)),
            'upperLimits'  : tuple('upper_limits_%s' % ii for ii in range(1, max)),
            }

        index = 0
        for peak in sorted(peakList.peaks):
            rowdata = self._loopRowData(loopName, peak)

            assignments = peak.assignedNmrAtoms
            if assignments:
                for tt in sorted(assignments):
                    # Make one row per assignment
                    row = loop.newRow(rowdata)
                    index += 1
                    row['index'] = index
                    values = peak.position
                    for ii, tag in enumerate(multipleAttributes['position']):
                        row[tag] = values[ii]
                    values = peak.positionError
                    for ii, tag in enumerate(multipleAttributes['positionError']):
                        row[tag] = values[ii]
                    # NB the row._set function will set position_1, position_2 etc.
                    # row._set('position', peak.position)
                    # row._set('position_uncertainty', peak.positionError)

                    # Add the assignments
                    ll = list(x if x is None else x._idTuple for x in tt)
                    for ii, attrName in enumerate(
                            ('chainCodes', 'sequenceCodes', 'residueTypes', 'atomNames')
                            ):
                        tags = multipleAttributes[attrName]
                        for jj, val in enumerate(ll):
                            row[tags[jj]] = None if val is None else val[ii]
                    # # Add the assignments
                    # ll =list(zip(*(x._idTuple if x else (None, None, None, None) for x in tt)))
                    # row._set('chain_code', ll[0])
                    # row._set('sequence_code', ll[1])
                    # row._set('residue_name', ll[2])
                    # row._set('atom_name', ll[3])

            else:
                # No assignments - just make one unassigned row
                row = loop.newRow(rowdata)
                index += 1
                row['index'] = index
                values = peak.position
                for ii, tag in enumerate(multipleAttributes['position']):
                    row[tag] = values[ii]
                values = peak.positionError
                for ii, tag in enumerate(multipleAttributes['positionError']):
                    row[tag] = values[ii]
                # # NB the row._set function will set position_1, position_2 etc.
                # row._set('position', peak.position)
                # row._set('position_uncertainty', peak.positionError)
            row['ccpn_linked_integral'] = None if peak.integral is None else peak.integral.pid

        if exportCompleteSpectrum and spectrum.spectrumHits:
            loopName = 'ccpn_spectrum_hit'
            loop = result[loopName]
            for spectrumHit in spectrum.spectrumHits:
                loop.newRow(self._loopRowData(loopName, spectrumHit))
        else:
            del result['ccpn_spectrum_hit']

        spectrumIntegralLists = set(spectrum.integralLists) & set(integralLists)
        if exportCompleteSpectrum and spectrumIntegralLists:
            loopName = 'ccpn_integral_list'

            loop = result[loopName]
            for tag in loop.columns:
                if any(tag.endswith(x) for x in removeNameEndings):
                    loop.removeColumn(tag)
            for integralList in sorted(spectrumIntegralLists):
                row = loop.newRow(self._loopRowData(loopName, integralList))
                row['serial'] = integralList.serial

            loopName = 'ccpn_integral'
            loop = result[loopName]
            for tag in loop.columns:
                if any(tag.endswith(x) for x in removeNameEndings):
                    loop.removeColumn(tag)
            for integral in sorted([intgrl for intgrl in spectrum.integrals if intgrl.integralList in spectrumIntegralLists]):
                row = loop.newRow(self._loopRowData(loopName, integral))
                row['integral_serial'] = integral.serial
                # values = integral.slopes
                # for ii, tag in enumerate(multipleAttributes['slopes']):
                #   row[tag] = None if values is None else values[ii]
                # # lowerlimits,upperLimits = zip(integral.limits)
                # lowerlimits = integral.limits
                # upperLimits = integral.limits
                # for ii, tag in enumerate(multipleAttributes['lowerLimits']):
                #   row[tag] = None if lowerlimits is None else lowerlimits[ii]
                # for ii, tag in enumerate(multipleAttributes['upperLimits']):
                #   row[tag] = None if upperLimits is None else upperLimits[ii]
                row['ccpn_linked_peak'] = None if integral.peak is None else integral.peak.pid
        else:
            del result['ccpn_integral_list']
            del result['ccpn_integral']

        spectrumMultipletLists = set(spectrum.multipletLists) & set(multipletLists)
        if exportCompleteSpectrum and spectrumMultipletLists:
            loopName = 'ccpn_multiplet_list'

            loop = result[loopName]
            for tag in loop.columns:
                if any(tag.endswith(x) for x in removeNameEndings):
                    loop.removeColumn(tag)
            for multipletList in sorted(spectrumMultipletLists):
                row = loop.newRow(self._loopRowData(loopName, multipletList))
                row['serial'] = multipletList.serial

            loopName = 'ccpn_multiplet'
            loop = result[loopName]
            for tag in loop.columns:
                if any(tag.endswith(x) for x in removeNameEndings):
                    loop.removeColumn(tag)
            for multiplet in sorted([mltpt for mltpt in spectrum.multiplets if mltpt.multipletList in spectrumMultipletLists]):
                row = loop.newRow(self._loopRowData(loopName, multiplet))
                row['multiplet_serial'] = multiplet.serial
                # values = multiplet.slopes
                # for ii, tag in enumerate(multipleAttributes['slopes']):
                #   row[tag] = None if values is None else values[ii]
                # # lowerlimits,upperLimits = zip(multiplet.limits)
                # lowerlimits = multiplet.limits
                # upperLimits = multiplet.limits
                # for ii, tag in enumerate(multipleAttributes['lowerLimits']):
                #   row[tag] = None if lowerlimits is None else lowerlimits[ii]
                # for ii, tag in enumerate(multipleAttributes['upperLimits']):
                #   row[tag] = None if upperLimits is None else upperLimits[ii]

            # loopName = 'ccpn_multiplet_peaks'
            # loop = result[loopName]
            # for tag in loop.columns:
            #     if any(tag.endswith(x) for x in removeNameEndings):
            #         loop.removeColumn(tag)
            # for multiplet in sorted(spectrum.multiplets):
            #     for peak in multiplet.peaks:
            #         row = loop.newRow(self._loopRowData(loopName, peak))
            #         row['multiplet_list_serial'] = multiplet.multipletList.serial
            #         row['multiplet_serial'] = multiplet.serial
            #         row['multiplet_peak'] = peak.pid

        else:
            del result['ccpn_multiplet_list']
            del result['ccpn_multiplet']
            # del result['ccpn_multiplet_peaks']

            # NB do more later (e.g. SpectrumReference)

        # NOTE:ED - needs to be in all spectra to deal with cross-spectrum multiplets
        if spectrumMultipletLists:
            loopName = 'ccpn_multiplet_peaks'
            loop = result[loopName]
            for tag in loop.columns:
                if any(tag.endswith(x) for x in removeNameEndings):
                    loop.removeColumn(tag)
            for multiplet in sorted([mltpt for mltpt in spectrum.multiplets if mltpt.multipletList in spectrumMultipletLists]):
                for peak in multiplet.peaks:
                    row = loop.newRow(self._loopRowData(loopName, peak))
                    row['multiplet_list_serial'] = multiplet.multipletList.serial
                    row['multiplet_serial'] = multiplet.serial
                    row['multiplet_peak'] = peak.pid
        else:
            del result['ccpn_multiplet_peaks']

        return result

    def peakRestraintLinks2Nef(self, restraintLists: Sequence[RestraintList]) -> StarIo.NmrSaveFrame:

        data = []
        for restraintList in sorted(restraintLists):
            restraintListFrame = self.ccpn2SaveFrameName.get(restraintList)
            if restraintListFrame is not None:
                for restraint in sorted(restraintList.restraints):
                    for peak in sorted(restraint.peaks):
                        peakListFrame = self.ccpn2SaveFrameName.get(peak.peakList)
                        if peakListFrame is not None:
                            data.append((peakListFrame, peak.serial, restraintListFrame, restraint.serial))

        if data:
            category = 'nef_peak_restraint_links'
            columns = ('nmr_spectrum_id', 'peak_id', 'restraint_list_id', 'restraint_id',)
            # Set up frame
            result = self._newNefSaveFrame(restraintLists[0].project, category, category)
            loopName = 'nef_peak_restraint_link'
            loop = result[loopName]
            for rowdata in sorted(data):
                loop.newRow(dict(zip(columns, rowdata)))
        else:
            result = None
        #
        return result

    def spectrumGroup2Nef(self, spectrumGroup: SpectrumGroup) -> StarIo.NmrSaveFrame:
        """Convert SpectrumGroup to CCPN NEF saveframe"""

        # Set up frame
        category = 'ccpn_spectrum_group'
        result = self._newNefSaveFrame(spectrumGroup, category, spectrumGroup.name)

        self.ccpn2SaveFrameName[spectrumGroup] = result['sf_framecode']

        # Fill in loop
        loopName = 'ccpn_group_spectrum'
        loop = result[loopName]
        spectra = sorted(spectrumGroup.spectra)
        if spectra:
            for spectrum in spectra:
                loop.newRow((spectrum.name,))
        else:
            del result[loopName]
        #
        return result

    def complex2Nef(self, complex: Complex) -> StarIo.NmrSaveFrame:
        """Convert Complex to CCPN NEF saveframe"""

        # Set up frame
        category = 'ccpn_complex'
        result = self._newNefSaveFrame(complex, category, complex.name)

        self.ccpn2SaveFrameName[complex] = result['sf_framecode']

        # Fill in loop
        loopName = 'ccpn_complex_chain'
        loop = result[loopName]
        chains = sorted(complex.chains)
        if chains:
            for chain in chains:
                loop.newRow((chain.shortName,))
        else:
            del result[loopName]
        #
        return result

    # TODO:ED add the correct function for converting structureEnsemble to Nef
    # def structureEnsemble2Nef(self, ensemble:StructureEnsemble) -> StarIo.NmrSaveFrame:
    #   """Convert StructureEnsemble to CCPN NEF saveframe"""
    #
    #   # Set up frame
    #   category = 'ccpn_structure_ensemble'
    #   result = self._newNefSaveFrame(ensemble, category, ensemble.name)
    #
    #   return result

    def sample2Nef(self, sample: Sample) -> StarIo.NmrSaveFrame:
        """Convert Sample to CCPN NEF saveframe"""

        # Set up frame
        category = 'ccpn_sample'
        result = self._newNefSaveFrame(sample, category, sample.name)

        self.ccpn2SaveFrameName[sample] = result['sf_framecode']

        # Fill in loop
        loopName = 'ccpn_sample_component'
        loop = result[loopName]
        components = sorted(sample.sampleComponents)
        if components:
            for sampleComponent in components:
                loop.newRow(self._loopRowData(loopName, sampleComponent))
        else:
            del result[loopName]
        #
        return result

    def substance2Nef(self, substance: Substance) -> StarIo.NmrSaveFrame:
        """Convert Substance to CCPN NEF saveframe"""

        # Set up frame
        category = 'ccpn_substance'
        name = '%s.%s' % (substance.name, substance.labelling)
        result = self._newNefSaveFrame(substance, category, name)

        substanceType = substance.substanceType
        result['substance_type'] = substanceType
        if substanceType == 'Molecule':
            apiMolecule = substance._wrappedData.molecule
            if apiMolecule is not None:
                result['sequence_string'] = substance.sequenceString
                result['start_number'] = apiMolecule.sortedMolResidues()[0].seqCode
                result['is_cyclic'] = apiMolecule.isStdCyclic
                molType = apiMolecule.molType
                if molType and not '/' in molType:
                    # 'protein', 'DNA', or 'RNA'. Excludes 'DNA/RNA'
                    result['mol_type'] = molType

        self.ccpn2SaveFrameName[substance] = result['sf_framecode']

        loopName = 'ccpn_substance_synonym'
        loop = result[loopName]
        synonyms = substance.synonyms
        if synonyms:
            for synonym in synonyms:
                loop.newRow((synonym,))
        else:
            del result[loopName]
        #
        return result

    def ccpnAssignentToNef(self, nmrChains: List[NmrChain]):
        """Write CCPN assignment data, to preserve serials etc."""
        category = 'ccpn_assignment'
        if nmrChains:
            project = nmrChains[0].project
            result = self._newNefSaveFrame(project, category, category)

            loopName = 'nmr_chain'
            loop = result[loopName]
            for nmrChain in nmrChains:
                row = loop.newRow(self._loopRowData(loopName, nmrChain))
                row['serial'] = nmrChain.serial

            loopName = 'nmr_residue'
            loop = result[loopName]
            for nmrResidue in project.nmrResidues:
                row = loop.newRow(self._loopRowData(loopName, nmrResidue))
                row['serial'] = nmrResidue.serial

            loopName = 'nmr_atom'
            loop = result[loopName]
            for nmrAtom in project.nmrAtoms:
                row = loop.newRow(self._loopRowData(loopName, nmrAtom))
                row['serial'] = nmrAtom.serial

        else:
            result = None
        #
        return result

    def notes2Nef(self, notes: List[Note]) -> StarIo.NmrSaveFrame:
        """Convert Notes to CCPN NEF saveframe"""

        # Set up frame
        category = 'ccpn_notes'
        if notes:
            result = self._newNefSaveFrame(notes[0].project, category, category)
            loopName = 'ccpn_note'
            loop = result[loopName]
            for note in sorted(notes):
                row = loop.newRow(self._loopRowData(loopName, note))
                row['serial'] = note.serial
                row['created'] = note._wrappedData.created.strftime(Constants.isoTimeFormat)
                row['last_modified'] = note._wrappedData.lastModified.strftime(
                        Constants.isoTimeFormat)
        else:
            result = None
        #
        return result

    def additionalData2Nef(self, project: Project) -> StarIo.NmrSaveFrame:
        """Make singleton saveFrame for additional data (ccpnInternalData)"""

        # Set up frame
        category = 'ccpn_additional_data'
        pid2Obj = project._pid2Obj
        data = {}
        for className in _coreImportOrder:
            # Use importOrder to get all classNames. The actual order does not matter here.
            dd = pid2Obj.get(className)
            if dd:
                for obj in dd.values():
                    internalData = obj._ccpnInternalData
                    if internalData:
                        data[obj.longPid] = internalData

        if data:
            result = self._newNefSaveFrame(project, category, category)
            loopName = 'ccpn_internal_data'
            loop = result[loopName]
            for key, val in sorted(data.items()):
                row = loop.newRow((key, jsonIo.dumps(val)))
        else:
            result = None
        #
        return result

    def _saveFrameNefOrder(self, saveframes: List[Optional[StarIo.NmrSaveFrame]]
                           ) -> List[StarIo.NmrSaveFrame]:
        """Reorder saveframes in NEF export order, and filter out Nones"""
        dd = {}
        for saveframe in saveframes:
            if saveframe is not None:
                ll = dd.setdefault(saveframe['sf_category'], [])
                ll.append(saveframe)
        #
        result = []
        for tag in saveFrameWritingOrder:
            if tag in dd:
                ll = dd.pop(tag)
                result.extend(ll)
        if dd:
            raise ValueError("Unknown saveframe types in export: %s" % list(dd.keys()))
        #
        return result

    def _loopRowData(self, loopName: str, wrapperObj: AbstractWrapperObject) -> dict:
        """Fill in a loop row data dictionary from master mapping and wrapperObj.
        Unmapped data to be added afterwards"""

        rowdata = {}
        for neftag, attrstring in nef2CcpnMap[loopName].items():
            if attrstring is not None:

                val = attrgetter(attrstring)(wrapperObj)
                if val != '':
                    rowdata[neftag] = val
                else:
                    rowdata[neftag] = None
        return rowdata

    def _newNefSaveFrame(self, wrapperObj: Optional[AbstractWrapperObject],
                         category: str, name: str) -> StarIo.NmrSaveFrame:
        """Create new NEF saveframe of category for wrapperObj using data from self.Nef2CcpnMap
        The functions will fill in top level items and make loops, but not
        fill in loop data
        """

        name = StarIo.string2FramecodeString(name)
        if name != category:
            name = '%s_%s' % (category, name)

        # Set up frame
        result = StarIo.NmrSaveFrame(name=name, category=category)
        result.addItem('sf_category', category)
        result.addItem('sf_framecode', name)

        if wrapperObj is not None:
            # Add data
            frameMap = nef2CcpnMap[category]
            for tag, itemvalue in frameMap.items():
                if itemvalue is None:
                    result.addItem(tag, None)
                elif isinstance(itemvalue, str):
                    try:
                        result.addItem(tag, attrgetter(itemvalue)(wrapperObj))
                    except AttributeError:
                        # You can get this error if a) the mapping is incorrect
                        # The dotted navigation expression can not always be followed
                        # as is the case e.g. for (PeakList.)spectrum._wrappedData.dataStore.headerSize'
                        # where the dataStore is sometimes None
                        self.project._logger.debug("Could not get %s from %s\n" % (itemvalue, wrapperObj))
                else:
                    # This is a loop
                    assert itemvalue == _isALoop, "Invalid item specifier in Nef2CcpnMap: %s" % (itemvalue,)
                    result.newLoop(tag, nef2CcpnMap[tag])
        #
        return result

    ####################################################################################
    #
    #       NEF reader code:
    #
    ####################################################################################


class CcpnNefReader:
    # Importer functions - used for converting saveframes and loops
    importers = {}
    verifiers = {}
    contents = {}

    def __init__(self, application: str, specificationFile: str = None, mode: str = 'standard',
                 testing: bool = False):

        self.application = application
        self.mode = mode
        self.saveFrameName = None
        self.warnings = []
        self.errors = []
        self.ccpnContent = {}  # can change this name later

        self.testing = testing

        # Map for resolving crosslinks in NEF file
        self.frameCode2Object = {}

        # Map for speeding up restraint reading
        self._dataSet2ItemMap = None
        self._nmrResidueMap = None

        self.defaultDataSetSerial = None
        self.defaultNmrChain = None
        self.mainDataSetSerial = None
        self.defaultChemicalShiftList = None

    def getNefData(self, path: str):
        """Get NEF data structure from file"""
        nmrDataExtent = StarIo.parseNefFile(path)
        dataBlocks = list(nmrDataExtent.values())
        if len(dataBlocks) > 1:
            print('More than one datablock in a NEF file is not allowed.  Using the first and discarding the rest.')
        dataBlock = dataBlocks[0]

        # Initialise afresh for every file read
        self._dataSet2ItemMap = {}
        self._nmrResidueMap = {}
        #
        return dataBlock

    def getNMRStarData(self, path: str):
        """Get NEF data structure from file"""
        nmrDataExtent = StarIo.parseNmrStarFile(path)
        dataBlocks = list(nmrDataExtent.values())
        dataBlock = dataBlocks[0]

        # Initialise afresh for every file read
        self._dataSet2ItemMap = {}
        self._nmrResidueMap = {}
        #
        return dataBlock

    def _getSaveFramesInOrder(self, dataBlock: StarIo.NmrDataBlock) -> OD:
        """Get saveframes in fixed reading order as Ordereddict(category:[saveframe,])"""
        result = OD(((x, []) for x in saveFrameReadingOrder))
        result['other'] = otherFrames = []
        for saveFrameName, saveFrame in dataBlock.items():
            sf_category = saveFrame.get('sf_category')
            ll = result.get(sf_category)
            if ll is None:
                ll = otherFrames
            ll.append(saveFrame)
        #
        return result

    def verifyProject(self, project: Project, dataBlock: StarIo.NmrDataBlock,
                      projectIsEmpty: bool = True,
                      selection: typing.Optional[dict] = None):
        """Verify import of selection from dataBlock into existing/empty Project
        """
        # Initialise mapping dicts
        if not hasattr(self, '_dataSet2ItemMap') or projectIsEmpty:
            self._dataSet2ItemMap = {}
        if not hasattr(self, '_nmrResidueMap') or projectIsEmpty:
            self._nmrResidueMap = {}

        self.warnings = []
        self.project = project
        self.defaultChainCode = None

        saveframeOrderedDict = self._getSaveFramesInOrder(dataBlock)

        # Load metadata and molecular system first
        metaDataFrame = dataBlock['nef_nmr_meta_data']
        self.saveFrameName = 'nef_nmr_meta_data'
        self.verifiers['nef_nmr_meta_data'](self, project, metaDataFrame)
        del saveframeOrderedDict['nef_nmr_meta_data']

        saveFrame = dataBlock.get('nef_molecular_system')
        if saveFrame:
            self.saveFrameName = 'nef_molecular_system'
            self.verifiers['nef_molecular_system'](self, project, saveFrame)
        del saveframeOrderedDict['nef_molecular_system']

        # Load assignments, or preload from shiftlists
        # to make sure '@' and '#' identifiers match the right serials
        saveFrame = dataBlock.get('ccpn_assignment')
        if saveFrame:
            self.saveFrameName = 'ccpn_assignment'
            self.verify_ccpn_assignment(project, saveFrame)
            del saveframeOrderedDict['ccpn_assignment']
        # else:
        #     self.verify_preloadAssignmentData(dataBlock)

        for sf_category, saveFrames in saveframeOrderedDict.items():
            for saveFrame in saveFrames:
                saveFrameName = self.saveFrameName = saveFrame.name

                if selection and saveFrameName not in selection:
                    getLogger().debug('>>>   -- skip saveframe {}'.format(saveFrameName))
                    continue
                getLogger().debug('>>> verifying saveframe {}'.format(saveFrameName))

                verifier = self.verifiers.get(sf_category)
                if verifier is None:
                    print("    unknown saveframe category", sf_category, saveFrameName)
                else:
                    result = verifier(self, project, saveFrame)

        return (tuple(self.warnings or ()), tuple(self.errors or ()))

    def contentNef(self, project: Project, dataBlock: StarIo.NmrDataBlock,
                   projectIsEmpty: bool = True,
                   selection: typing.Optional[dict] = None):
        """Verify import of selection from dataBlock into existing/empty Project
        """
        # Initialise mapping dicts
        if not hasattr(self, '_dataSet2ItemMap') or projectIsEmpty:
            self._dataSet2ItemMap = {}
        if not hasattr(self, '_nmrResidueMap') or projectIsEmpty:
            self._nmrResidueMap = {}

        result = {}
        self.project = project
        self.defaultChainCode = None

        saveframeOrderedDict = self._getSaveFramesInOrder(dataBlock)

        # Load metadata and molecular system first
        metaDataFrame = dataBlock['nef_nmr_meta_data']
        self.saveFrameName = 'nef_nmr_meta_data'
        self.contents['nef_nmr_meta_data'](self, project, metaDataFrame)
        del saveframeOrderedDict['nef_nmr_meta_data']

        saveFrame = dataBlock.get('nef_molecular_system')
        if saveFrame:
            self.saveFrameName = 'nef_molecular_system'
            self.contents['nef_molecular_system'](self, project, saveFrame)
        del saveframeOrderedDict['nef_molecular_system']

        # Load assignments, or preload from shiftlists
        # to make sure '@' and '#' identifiers match the right serials
        saveFrame = dataBlock.get('ccpn_assignment')
        if saveFrame:
            self.saveFrameName = 'ccpn_assignment'
            result[self.saveFrameName] = self.content_ccpn_assignment(project, saveFrame)
            del saveframeOrderedDict['ccpn_assignment']
        # else:
        #     self.verify_preloadAssignmentData(dataBlock)

        for sf_category, saveFrames in saveframeOrderedDict.items():
            for saveFrame in saveFrames:
                saveFrameName = self.saveFrameName = saveFrame.name

                if selection and saveFrameName not in selection:
                    getLogger().debug('>>>   -- skip saveframe {}'.format(saveFrameName))
                    continue
                getLogger().debug('>>> verifying saveframe {}'.format(saveFrameName))

                content = self.contents.get(sf_category)
                if content is None:
                    print("    unknown saveframe category", sf_category, saveFrameName)
                else:
                    result[self.saveFrameName] = content(self, project, saveFrame)

        return self.ccpnContent, result

    def importExistingProject(self, project: Project, dataBlock: StarIo.NmrDataBlock,
                              projectIsEmpty: bool = True,
                              selection: typing.Optional[dict] = None):
        """Import selection from dataBlock into existing/empty Project
        """
        # Initialise mapping dicts
        if not hasattr(self, '_dataSet2ItemMap') or projectIsEmpty:
            self._dataSet2ItemMap = {}
        if not hasattr(self, '_nmrResidueMap') or projectIsEmpty:
            self._nmrResidueMap = {}

        self.importNewProject(project, dataBlock=dataBlock, projectIsEmpty=projectIsEmpty, selection=selection)

    def importNewProject(self, project: Project, dataBlock: StarIo.NmrDataBlock,
                         projectIsEmpty: bool = True,
                         selection: typing.Optional[dict] = None):
        """Import entire project from dataBlock into empty Project"""

        t0 = time.time()

        self.warnings = []
        self.project = project
        self.defaultChainCode = None

        saveframeOrderedDict = self._getSaveFramesInOrder(dataBlock)

        # Load metadata and molecular system first
        metaDataFrame = dataBlock['nef_nmr_meta_data']
        self.saveFrameName = 'nef_nmr_meta_data'
        self.load_nef_nmr_meta_data(project, metaDataFrame)
        del saveframeOrderedDict['nef_nmr_meta_data']

        saveFrame = dataBlock.get('nef_molecular_system')
        if saveFrame:
            self.saveFrameName = 'nef_molecular_system'
            self.load_nef_molecular_system(project, saveFrame)
        del saveframeOrderedDict['nef_molecular_system']

        # Load assignments, or preload from shiftlists
        # to make sure '@' and '#' identifiers match the right serials
        saveFrame = dataBlock.get('ccpn_assignment')
        if saveFrame:
            self.saveFrameName = 'ccpn_assignment'
            self.load_ccpn_assignment(project, saveFrame)
            del saveframeOrderedDict['ccpn_assignment']
        else:
            self.preloadAssignmentData(dataBlock)

        # t1 = time.time()
        # print ('@~@~ NEF load starting frames', t1-t0)

        for sf_category, saveFrames in saveframeOrderedDict.items():
            for saveFrame in saveFrames:
                saveFrameName = self.saveFrameName = saveFrame.name

                if selection and saveFrameName not in selection:
                    getLogger().debug('>>>  -- skip saveframe {}'.format(saveFrameName))
                    continue
                getLogger().debug('>>> loading saveframe {}'.format(saveFrameName))

                importer = self.importers.get(sf_category)
                if importer is None:
                    print("WARNING, unknown saveframe category", sf_category, saveFrameName)
                else:
                    # NB - newObject may be project, for some saveframes.
                    result = importer(self, project, saveFrame)
                    if isinstance(result, AbstractWrapperObject):
                        self.frameCode2Object[saveFrameName] = result
                    # elif not isinstance(result, list):
                    #   self.warning("Unexpected return %s while reading %s" %
                    #                (result, saveFrameName))

                    # Handle unmapped elements
                    extraTags = [x for x in saveFrame
                                 if x not in nef2CcpnMap[sf_category]
                                 and x not in ('sf_category', 'sf_framecode')]
                    if extraTags:
                        print("WARNING - unused tags in saveframe %s: %s" % (saveFrameName, extraTags))
                        # TODO put here function that stashes data in object, or something

        # Put metadata in main dataset
        self.updateMetaData(metaDataFrame)

        t2 = time.time()
        getLogger().debug('Loaded NEF file, time = %.2fs' % (t2 - t0))

        for msg in self.warnings:
            print('====> ', msg)
        self.project = None

    def importNewNMRStarProject(self, project: Project, dataBlock: StarIo.NmrDataBlock,
                                projectIsEmpty: bool = True):
        """Import entire project from dataBlock into empty Project"""

        t0 = time.time()

        self.warnings = []
        self.project = project
        self.defaultChainCode = None

        saveframeOrderedDict = self._getSaveFramesInOrder(dataBlock)

        # these sections below check each of the saveframes, extract the relevant information
        # and then discard if they are no longer required
        # the following saveframes can then be checked to find the corrct one holding the
        # chemical shift list information

        # # Load metadata and molecular system first
        # metaDataFrame = dataBlock['nef_nmr_meta_data']
        # self.saveFrameName = 'nef_nmr_meta_data'
        # self.load_nef_nmr_meta_data(project, metaDataFrame)
        # del saveframeOrderedDict['nef_nmr_meta_data']
        #
        # saveFrame = dataBlock.get('nef_molecular_system')
        # if saveFrame:
        #   self.saveFrameName = 'nef_molecular_system'
        #   self.load_nef_molecular_system(project, saveFrame)
        # del saveframeOrderedDict['nef_molecular_system']
        #
        # # Load assignments, or preload from shiftlists
        # # to make sure '@' and '#' identifiers match the right serials
        # saveFrame = dataBlock.get('ccpn_assignment')
        # if saveFrame:
        #   self.saveFrameName = 'ccpn_assignment'
        #   self.load_ccpn_assignment(project, saveFrame)
        #   del saveframeOrderedDict['ccpn_assignment']
        # else:
        #   self.preloadAssignmentData(dataBlock)

        # t1 = time.time()
        # print ('@~@~ NEF load starting frames', t1-t0)

        for sf_category, saveFrames in saveframeOrderedDict.items():
            for saveFrame in saveFrames:
                saveFrameName = self.saveFrameName = saveFrame.name

                importer = self.importers.get(sf_category)
                if importer is None:
                    print("WARNING, unknown saveframe category", sf_category, saveFrameName)
                else:
                    # NB - newObject may be project, for some saveframes.
                    result = importer(self, project, saveFrame)
                    if isinstance(result, AbstractWrapperObject):
                        self.frameCode2Object[saveFrameName] = result
                    # elif not isinstance(result, list):
                    #   self.warning("Unexpected return %s while reading %s" %
                    #                (result, saveFrameName))

                    # Handle unmapped elements
                    extraTags = [x for x in saveFrame
                                 if x not in nef2CcpnMap[sf_category]
                                 and x not in ('sf_category', 'sf_framecode')]
                    if extraTags:
                        print("WARNING - unused tags in saveframe %s: %s" % (saveFrameName, extraTags))
                        # TODO put here function that stashes data in object, or something

        # Put metadata in main dataset
        # self.updateMetaData(metaDataFrame)

        t2 = time.time()
        getLogger().debug('Loaded NEF file, time = %.2fs' % (t2 - t0))

        for msg in self.warnings:
            print('====> ', msg)
        self.project = None

    def _verifyLoops(self, project: Project, saveFrame: StarIo.NmrSaveFrame, addLoopAttribs=None, **kwds):
        """Iterate over the loops in a saveFrame, and verify contents
        """
        mapping = nef2CcpnMap[saveFrame.category]
        for tag, ccpnTag in mapping.items():
            if ccpnTag == _isALoop:
                loop = saveFrame.get(tag)
                if loop:
                    verify = self.verifiers[tag]
                    if addLoopAttribs:
                        dd = []
                        for name in addLoopAttribs:
                            dd.append(saveFrame.get(name))
                        verify(self, project, loop, *dd, **kwds)
                    else:
                        verify(self, project, loop, **kwds)

    def _noLoopVerify(self, project: Project, loop: StarIo.NmrLoop, *arg, **kwds):
        """Verify the contents of the loop
        This is a loop that requires no verification
        """
        pass

    def _contentLoops(self, project: Project, saveFrame: StarIo.NmrSaveFrame, addLoopAttribs=None):
        """Iterate over the loops in a saveFrame, and add to results"""
        result = {}
        mapping = nef2CcpnMap[saveFrame.category]
        for tag, ccpnTag in mapping.items():
            if ccpnTag == _isALoop:
                loop = saveFrame.get(tag)
                if loop:
                    content = self.contents[tag]
                    if addLoopAttribs:
                        dd = []
                        for name in addLoopAttribs:
                            dd.append(saveFrame.get(name))
                        result[tag] = content(self, project, loop, *dd)
                    else:
                        result[tag] = content(self, project, loop)

        self.storeContent(saveFrame, result)

    def _noLoopContent(self, project: Project, loop: StarIo.NmrLoop, *arg, **kwds):
        """Get contents of the loop
        This is a loop returning no information
        """
        return None

    def load_nef_nmr_meta_data(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """load nef_nmr_meta_data saveFrame"""

        # Other data are read in here at the end of the load
        self.mainDataSetSerial = saveFrame.get('ccpn_dataset_serial')

        formatName = saveFrame.get('format_name')
        formatVersion = saveFrame.get('format_version')
        if formatName == 'nmr_exchange_format':
            if formatVersion:
                try:
                    version = float(formatVersion)
                except ValueError:
                    raise ValueError("Illegal version string %s for nmr_exchange_format"
                                     % formatVersion)
                else:
                    if version < minimumNefVersion:
                        raise ValueError("Unsupported nef file version %s; minimum version is %s"
                                         % (formatVersion, minimumNefVersion))
            else:
                project._logger.warning("NEF file format version missing: Reading may fail.")

        else:
            project._logger.warning("NEF file format name '%s', not recognised. Reading may fail."
                                    % formatName)

        return None

        # TODO - store data in this saveframe
        # for now we store none of this, as the storage slots are in DataSet, not Project
        # Maybe for another load function?

    #
    importers['nef_nmr_meta_data'] = load_nef_nmr_meta_data

    def verify_nef_nmr_meta_data(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """verify nef_nmr_meta_data saveFrame"""
        self.mainDataSetSerial = saveFrame.get('ccpn_dataset_serial')

        formatName = saveFrame.get('format_name')
        formatVersion = saveFrame.get('format_version')
        if formatName == 'nmr_exchange_format':
            if formatVersion:
                try:
                    version = float(formatVersion)
                except ValueError:
                    self.error('Illegal version string {} for nmr_exchange_format'.format(formatVersion), saveFrame, None)
                else:
                    if version < minimumNefVersion:
                        self.error('Unsupported nef file version {}; minimum version is {}'.format(formatVersion, minimumNefVersion), saveFrame, None)
            else:
                self.warning('file format version missing: Reading may fail')
        else:
            self.warning("NEF file format name '{}', not recognised. Reading may fail.".format(formatName))

    verifiers['nef_nmr_meta_data'] = verify_nef_nmr_meta_data
    # not strictly needed
    verifiers['nef_related_entries'] = _noLoopVerify
    verifiers['nef_program_script'] = _noLoopVerify
    verifiers['nef_run_history'] = _noLoopVerify

    contents['nef_nmr_meta_data'] = _contentLoops
    contents['nef_related_entries'] = _noLoopContent
    contents['nef_program_script'] = _noLoopContent
    contents['nef_run_history'] = _noLoopContent

    def load_nef_molecular_system(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """load nef_molecular_system saveFrame"""

        mapping = nef2CcpnMap['nef_molecular_system']
        for tag, ccpnTag in mapping.items():
            if ccpnTag == _isALoop:
                loop = saveFrame.get(tag)
                if loop:
                    importer = self.importers[tag]
                    importer(self, project, loop)
        #
        return None

    #
    importers['nef_molecular_system'] = load_nef_molecular_system
    verifiers['nef_molecular_system'] = _verifyLoops

    def content_nef_molecular_system(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """Get the contents nef_molecular_system saveFrame"""
        # read nmr_sequence loop
        chainCode = 'chain_code'
        compoundName = 'ccpn_compound_name'
        nefSequence = 'nef_sequence'

        results = {chainCode   : OrderedSet(),
                   compoundName: OrderedSet()}

        mapping = nef2CcpnMap[nefSequence]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in saveFrame[nefSequence].data:
            results[chainCode].add(row[chainCode])
            results[compoundName].add(row[compoundName])

        self._contentLoops(project, saveFrame)
        self.updateContent(saveFrame, results)

    contents['nef_molecular_system'] = content_nef_molecular_system

    def load_nef_sequence(self, project: Project, loop: StarIo.NmrLoop):
        """Load nef_sequence loop"""

        result = []

        chainData = {}
        for row in loop.data:
            chainCode = row['chain_code']
            ll = chainData.get(chainCode)
            if ll is None:
                chainData[chainCode] = [row]
            else:
                ll.append(row)

        defaultChainCode = None
        if None in chainData:
            defaultChainCode = 'A'
            # Replace chainCode None with default chainCode
            # Selecting the first value that is not already taken.
            while defaultChainCode in chainData:
                defaultChainCode = commonUtil.incrementName(defaultChainCode)
            chainData[defaultChainCode] = chainData.pop(None)
        self.defaultChainCode = defaultChainCode

        sequence2Chain = {}
        tags = ('residue_name', 'linking', 'residue_variant')
        for chainCode, rows in sorted(chainData.items()):
            compoundName = rows[0].get('ccpn_compound_name')
            role = rows[0].get('ccpn_chain_role')
            comment = rows[0].get('ccpn_chain_comment')
            for row in rows:
                if row.get('linking') == 'dummy':
                    row['residue_name'] = 'dummy.' + row['residue_name']
            sequence = tuple(tuple(row.get(tag) for tag in tags) for row in rows)

            lastChain = sequence2Chain.get(sequence)
            if lastChain is None:
                newSubstance = project.fetchNefSubstance(sequence=rows, name=compoundName)
                newChain = newSubstance.createChain(shortName=chainCode, role=role,
                                                    comment=comment)
                sequence2Chain[sequence] = newChain

                # Set variant codes:
                for ii, residue in enumerate(newChain.residues):
                    variantCode = sequence[ii][2]

                    if variantCode:

                        atomNamesRemoved, atomNamesAdded = residue._wrappedData.getAtomNameDifferences()

                        for code in variantCode.split(','):
                            code = code.strip()  # Should not be necessary but costs nothing to catch those errors
                            atom = residue.getAtom(code[1:])
                            if code[0] == '-':
                                if atom is None:
                                    residue._project._logger.error(
                                            "Incorrect variantCode %s: No atom named %s found in %s. Skipping ..."
                                            % (variantCode, code, residue)
                                            )
                                else:
                                    atom.delete()

                            elif code[0] == '+':
                                if atom is None:
                                    residue.newAtom(name=code[1:])
                                else:
                                    residue._project._logger.error(
                                            "Incorrect variantCode %s: Atom named %s already present in %s. Skipping ..."
                                            % (variantCode, code, residue)
                                            )

                            else:
                                residue._project._logger.error(
                                        "Incorrect variantCode %s: must start with '+' or '-'. Skipping ..."
                                        % variantCode
                                        )

            else:
                newChain = lastChain.clone(shortName=chainCode)
                newChain.role = role
                newChain.comment = comment

            for apiResidue in newChain._wrappedData.sortedResidues():
                # Necessary to guarantee against name clashes
                # Direct access to avoid unnecessary notifiers
                apiResidue.__dict__['seqInsertCode'] = '__@~@~__'
            for ii, apiResidue in enumerate(newChain._wrappedData.sortedResidues()):
                # NB we have to loop over API residues to be sure we get the residues
                # in creation order rather than sorted order
                residue = project._data2Obj[apiResidue]
                residue.rename(rows[ii].get('sequence_code'))
                residue._resetIds()

            # Necessary as notification is blanked here:
            newChain._resetIds()

            #
            result.append(newChain)

            # Add Residue comments
            for ii, apiResidue in enumerate(newChain.residues):
                comment = rows[ii].get('ccpn_comment')
                if comment:
                    apiResidue.details = comment
        #
        return result

    #
    importers['nef_sequence'] = load_nef_sequence

    def verify_nef_sequence(self, project: Project, loop: StarIo.NmrLoop):
        """verify nef_sequence loop"""
        chainData = {}
        for row in loop.data:
            chainCode = row['chain_code']
            ll = chainData.get(chainCode)
            if ll is None:
                chainData[chainCode] = [row]
            else:
                ll.append(row)

        defaultChainCode = None
        if None in chainData:
            defaultChainCode = 'A'
            # Replace chainCode None with default chainCode
            # Selecting the first value that is not already taken.
            while defaultChainCode in chainData:
                defaultChainCode = commonUtil.incrementName(defaultChainCode)
            chainData[defaultChainCode] = chainData.pop(None)
        self.defaultChainCode = defaultChainCode

        sequence2Chain = {}
        tags = ('residue_name', 'linking', 'residue_variant')
        for chainCode, rows in sorted(chainData.items()):
            compoundName = rows[0].get('ccpn_compound_name')
            role = rows[0].get('ccpn_chain_role')
            comment = rows[0].get('ccpn_chain_comment')
            for row in rows:
                if row.get('linking') == 'dummy':
                    row['residue_name'] = 'dummy.' + row['residue_name']
            sequence = tuple(tuple(row.get(tag) for tag in tags) for row in rows)

            lastChain = sequence2Chain.get(sequence)
            if lastChain is None:
                # newSubstance = project.fetchNefSubstance(sequence=rows, name=compoundName)
                newSubstance = project.getNefSubstance(sequence=rows, name=compoundName)
                if newSubstance is not None:
                    self.error('nef_sequence - Substance {} already exists'.format(newSubstance), loop, (newSubstance,))

                result = project.getChain(chainCode)
                if result is not None:
                    self.error('nef_sequence - Chain {} already exists'.format(result), loop, (result,))

    verifiers['nef_sequence'] = verify_nef_sequence

    def content_nef_sequence(self, project: Project, loop: StarIo.NmrLoop) -> OrderedSet:
        """get contents of the nef_sequence loop"""
        residues = OrderedSet()

        for row in loop.data:
            chainCode = row['chain_code']
            sequenceCode = row['sequence_code']
            residue = row['residue_name']
            compoundName = row['ccpn_compound_name']
            residues.add((chainCode, sequenceCode, residue, compoundName))

        return residues

    contents['nef_sequence'] = content_nef_sequence

    def load_nef_covalent_links(self, project: Project, loop: StarIo.NmrLoop):
        """Load nef_sequence loop"""

        result = []

        for row in loop.data:
            id1 = Pid.createId(*(row[x] for x in ('chain_code_1', 'sequence_code_1',
                                                  'residue_name_1', 'atom_name_1',)))
            id2 = Pid.createId(*(row[x] for x in ('chain_code_2', 'sequence_code_2',
                                                  'residue_name_2', 'atom_name_2',)))
            atom1 = project.getAtom(id1)
            atom2 = project.getAtom(id2)
            if atom1 is None:
                self.warning("Unknown atom %s for bond to %s. Skipping..." % (id1, id2))
            elif atom2 is None:
                self.warning("Unknown atom %s for bond to %s. Skipping..." % (id2, id1))
            else:
                result.append((atom1, atom2))
                atom1.addInterAtomBond(atom2)
        #
        return result

    #
    importers['nef_covalent_links'] = load_nef_covalent_links
    verifiers['nef_covalent_links'] = _noLoopVerify

    def content_nef_covalent_links(self, project: Project, loop: StarIo.NmrLoop) -> OrderedSet:
        """get the contents of nef_covalent_links loop"""
        covalentLinks = OrderedSet()

        for row in loop.data:
            id1 = Pid.createId(*(row[x] for x in ('chain_code_1', 'sequence_code_1',
                                                  'residue_name_1', 'atom_name_1',)))
            id2 = Pid.createId(*(row[x] for x in ('chain_code_2', 'sequence_code_2',
                                                  'residue_name_2', 'atom_name_2',)))
            covalentLinks.add((id1, id2))

        return covalentLinks

    contents['nef_covalent_links'] = content_nef_covalent_links

    def preloadAssignmentData(self, dataBlock: StarIo.NmrDataBlock):
        """Set up NmrChains and NmrResidues with reserved names to ensure the serials are OK
    and create NmrResidues in connected nmrChains in order

    NB later we can store serials in CCPN projects, but something is needed that works anyway

    NB, without CCPN-specific tags you can NOT guarantee that connected stretches are stable,
    and that serials are put back where they came from.
    This heuristic creates NmrResidues in connected stretches in the order they are found,
    but this will break if connected stretches appear in multiple shiftlists and some are partial."""

        project = self.project

        for saveFrameName, saveFrame in dataBlock.items():

            # get all NmrResidue data in chemicalshift lists
            assignmentData = {}
            if saveFrameName.startswith('nef_chemical_shift_list'):
                loop = saveFrame.get('nef_chemical_shift')
                if loop:
                    for row in loop.data:
                        # NB the self.defaultChainCode guards against chainCode being None
                        chainCode = row['chain_code'] or self.defaultChainCode

                        nmrResidues = assignmentData.get(chainCode, OD())
                        assignmentData[chainCode] = nmrResidues
                        nmrResidues[(row['sequence_code'], row['residue_name'])] = None

        # Create objects with reserved names
        for chainCode in sorted(assignmentData):

            if chainCode[0] in '@#' and chainCode[1:].isdigit():
                # reserved name - make chain
                try:
                    project.fetchNmrChain(chainCode)
                except ValueError:
                    # Could not be done, probably because we have NmrChain '@1'. Leave for later
                    pass

        assignmentData2 = {}
        for chainCode, nmrResidues in sorted(assignmentData.items()):

            # Create NmrChain
            try:
                nmrChain = project.fetchNmrChain(chainCode)
            except ValueError:
                nmrChain = project.fetchNmrChain('`%s`' % chainCode)

            if nmrChain.isConnected:
                # Save data for later processing
                assignmentData2[nmrChain] = nmrResidues
            else:
                # Create non-assigned NmrResidues to reserve the serials. The rest can wait
                for sequenceCode, residueType in list(nmrResidues.keys()):
                    if sequenceCode[0] == '@' and sequenceCode[1:].isdigit():
                        nmrChain.fetchNmrResidue(sequenceCode=sequenceCode, residueType=residueType)

        for nmrChain, nmrResidues in sorted(assignmentData2.items()):
            # Create NmrResidues in order, to preserve connection order
            for sequenceCode, residueType in list(nmrResidues.keys()):
                # This time we want all non-offset, regardless of type - as we must get them in order
                if (len(sequenceCode) < 2 or sequenceCode[-2] not in '+-'
                        or not sequenceCode[-1].isdigit()):
                    # I.e. for sequenceCodes that do not include an offset
                    nmrChain.fetchNmrResidue(sequenceCode=sequenceCode, residueType=residueType)

    def verify_preloadAssignmentData(self, dataBlock: StarIo.NmrDataBlock):
        """Set up NmrChains and NmrResidues with reserved names to ensure the serials are OK
        and create NmrResidues in connected nmrChains in order"""

        # NOTE:ED - need to check and validate this bit

        project = self.project

        for saveFrameName, saveFrame in dataBlock.items():

            # get all NmrResidue data in chemicalshift lists
            assignmentData = {}
            if saveFrameName.startswith('nef_chemical_shift_list'):
                loop = saveFrame.get('nef_chemical_shift')
                if loop:
                    for row in loop.data:
                        # NB the self.defaultChainCode guards against chainCode being None
                        chainCode = row['chain_code'] or self.defaultChainCode

                        nmrResidues = assignmentData.get(chainCode, OD())
                        assignmentData[chainCode] = nmrResidues
                        nmrResidues[(row['sequence_code'], row['residue_name'])] = None

        # Create objects with reserved names
        for chainCode in sorted(assignmentData):

            if chainCode[0] in '@#' and chainCode[1:].isdigit():
                # reserved name - make chain
                nmrChain = project.getNmrChain(chainCode)
                if nmrChain:
                    self.warning('nmrChain {} already exists'.format(nmrChain))

    def load_nef_chemical_shift_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """load nef_chemical_shift_list saveFrame"""

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        parameters['name'] = framecode[len(category) + 1:]

        # Make main object
        result = project.newChemicalShiftList(**parameters)

        if self.defaultChemicalShiftList is None:
            # ChemicalShiftList should default to the unique ChemicalShIftList in the file
            # A file with multiple ChemicalShiftLists MUST have explicit chemical shift lists
            # given for all spectra- but this is nto hte place for validity checking
            self.defaultChemicalShiftList = result

        if self.testing:
            # When testing you want the values to remain as read
            result.autoUpdate = False
            # NB The above is how it ought to work.
            # The below is how it is working as of July 2016
            result._wrappedData.topObject.shiftAveraging = False

        # Load loops, with object as parent
        for loopName in loopNames:
            loop = saveFrame.get(loopName)
            if loop:
                importer = self.importers[loopName]
                importer(self, result, loop)
        #
        return result

    #

    importers['nef_chemical_shift_list'] = load_nef_chemical_shift_list

    def verify_nef_chemical_shift_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """verify nef_chemical_shift_list saveFrame"""
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        name = framecode[len(category) + 1:]

        # Verify main object
        result = project.getChemicalShiftList(name)
        if result is not None:
            self.error('nef_chemical_shift_list - ChemicalShiftList {} already exists'.format(result), saveFrame, (result,))

        self._verifyLoops(project, saveFrame, name=name)

    def content_nef_chemical_shift_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """Get the contents of nef_chemical_shift_list saveFrame"""
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']

        # store the name of the chemicalShiftList
        name = framecode[len(category) + 1:]
        result = {category: OrderedSet([name])}

        self._contentLoops(project, saveFrame)
        self.updateContent(saveFrame, result)

    verifiers['nef_chemical_shift_list'] = verify_nef_chemical_shift_list
    contents['nef_chemical_shift_list'] = content_nef_chemical_shift_list

    def load_nef_chemical_shift(self, parent: ChemicalShiftList, loop: StarIo.NmrLoop):
        """load nef_chemical_shift loop"""

        result = []

        creatorFunc = parent.newChemicalShift

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            tt = tuple(row.get(tag) for tag in ('chain_code', 'sequence_code', 'residue_name',
                                                'atom_name'))
            element = row.get('element')
            isotope = row.get('isotope_number')
            if element:
                if isotope:
                    isotopeCode = '%s%s' % (isotope, element.title())
                else:
                    isotopeCode = Constants.DEFAULT_ISOTOPE_DICT.get(element.upper())
            elif isotope:
                element = commonUtil.name2ElementSymbol(tt[3])
                isotopeCode = '%s%s' % (isotope, element.title())
            else:
                isotopeCode = None
            try:
                nmrResidue = self.produceNmrResidue(*tt[:3])
                nmrAtom = self.produceNmrAtom(nmrResidue, tt[3], isotopeCode=isotopeCode)
                parameters['nmrAtom'] = nmrAtom
                result.append(creatorFunc(**parameters))

            except ValueError:
                self.warning("Cannot produce NmrAtom for assignment %s. Skipping ChemicalShift" % (tt,))
                # Should eventually be removed - raise while still testing
                raise
        #
        return result

    #
    importers['nef_chemical_shift'] = load_nef_chemical_shift

    def verify_nef_chemical_shift(self, parent: ChemicalShiftList, loop: StarIo.NmrLoop, name=None):
        """verify nef_chemical_shift loop"""
        if name is None:
            self.error('Undefined chemicalShiftList', loop, None)
            return

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            tt = tuple(row.get(tag) for tag in ('chain_code', 'sequence_code', 'residue_name',
                                                'atom_name'))
            shiftId = Pid.IDSEP.join(('' if x is None else str(x)) for x in tt)

            # Verify main object
            shiftList = parent.getChemicalShiftList(name)
            if shiftList is not None:
                # find the chemicalShift
                shift = shiftList.getChemicalShift(shiftId)
                if shift is not None:
                    self.error('nef_chemical_shift - ChemicalShift {} already exists'.format(shift), loop, (shift,))

    verifiers['nef_chemical_shift'] = verify_nef_chemical_shift

    def content_nef_chemical_shift(self, parent: ChemicalShiftList, loop: StarIo.NmrLoop) -> OrderedSet:
        """Get the contents of nef_chemical_shift loop"""
        nmrAtoms = OrderedSet()

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            tt = tuple(row.get(tag) for tag in ('chain_code', 'sequence_code', 'residue_name',
                                                'atom_name'))
            nmrAtoms.add(tt)

        return nmrAtoms

    contents['nef_chemical_shift'] = content_nef_chemical_shift

    def load_nef_restraint_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """Serves to load nef_distance_restraint_list, nef_dihedral_restraint_list,
        nef_rdc_restraint_list and ccpn_restraint_list"""

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        if category == 'nef_distance_restraint_list':
            restraintType = 'Distance'
        elif category == 'nef_dihedral_restraint_list':
            restraintType = 'Dihedral'
        elif category == 'nef_rdc_restraint_list':
            restraintType = 'Rdc'
        else:
            restraintType = saveFrame.get('restraint_type')
            if not restraintType:
                self.warning("Missing restraint_type for saveFrame %s - value was %s" %
                             (framecode, restraintType))
                return
        parameters['restraintType'] = restraintType
        namePrefix = restraintType[:3].capitalize() + '-'

        # Get name from framecode, add type disambiguation, and correct for ccpn dataSetSerial addition
        name = framecode[len(category) + 1:]
        dataSetSerial = saveFrame.get('ccpn_dataset_serial')
        if dataSetSerial is not None:
            ss = '`%s`' % dataSetSerial
            if name.startswith(ss):
                name = name[len(ss):]

        # ejb - need to remove the rogue `n` at the beginning of the name if it exists
        #       as it is passed into the namespace and gets added iteratively every save
        #       next three lines remove all occurrences of `n` from name
        import re

        regex = u'\`\d*`+?'
        name = re.sub(regex, '', name)  # substitute with ''

        # Make main object
        dataSet = self.fetchDataSet(dataSetSerial)

        # need to fix the names here... cannot contain '.'

        previous = dataSet.getRestraintList(name)
        if previous is not None:
            # NEF but NOT CCPN has separate namespaces for different restraint types
            # so we may get name clashes
            # We should preserve NEF names, but it cannot be helped.
            if not name.startswith(namePrefix):
                # Add prefix for disambiguation since NEF but NOT CCPN has separate namespaces
                # for different constraint types
                name = namePrefix + name
                while dataSet.getRestraintList(name) is not None:
                    # This way we get a unique name even in the most bizarre cases
                    name = '`%s`' % name

        parameters['name'] = name

        result = dataSet.newRestraintList(**parameters)

        # Load loops, with object as parent
        for loopName in loopNames:
            loop = saveFrame.get(loopName)
            if loop:
                importer = self.importers[loopName]
                if loopName.endswith('_restraint'):
                    # NBNB HACK: the restrain loop reader needs an itemLength.
                    # There are no other loops currently, but if there ever is they will not need this
                    itemLength = saveFrame.get('restraint_item_length')
                    importer(self, result, loop, itemLength)
                else:
                    importer(self, result, loop)
        #
        return result

    #
    importers['nef_distance_restraint_list'] = load_nef_restraint_list
    importers['nef_dihedral_restraint_list'] = load_nef_restraint_list
    importers['nef_rdc_restraint_list'] = load_nef_restraint_list
    importers['ccpn_restraint_list'] = load_nef_restraint_list

    def verify_nef_restraint_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """Serves to verify nef_distance_restraint_list, nef_dihedral_restraint_list,
        nef_rdc_restraint_list and ccpn_restraint_list"""
        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        if category == 'nef_distance_restraint_list':
            restraintType = 'Distance'
        elif category == 'nef_dihedral_restraint_list':
            restraintType = 'Dihedral'
        elif category == 'nef_rdc_restraint_list':
            restraintType = 'Rdc'
        else:
            restraintType = saveFrame.get('restraint_type')
            if not restraintType:
                self.warning("Missing restraint_type for saveFrame %s - value was %s" %
                             (framecode, restraintType))
                return
        parameters['restraintType'] = restraintType
        namePrefix = restraintType[:3].capitalize() + '-'

        # Get name from framecode, add type disambiguation, and correct for ccpn dataSetSerial addition
        name = framecode[len(category) + 1:]
        dataSetSerial = saveFrame.get('ccpn_dataset_serial')
        if dataSetSerial is not None:
            ss = '`%s`' % dataSetSerial
            if name.startswith(ss):
                name = name[len(ss):]

        # ejb - need to remove the rogue `n` at the beginning of the name if it exists
        #       as it is passed into the namespace and gets added iteratively every save
        #       next three lines remove all occurrences of `n` from name
        import re

        regex = u'\`\d*`+?'
        name = re.sub(regex, '', name)  # substitute with ''

        # Make main object
        dataSet = self.getDataSet(dataSetSerial)
        if dataSet is not None:
            # find the restraintList
            restraint = dataSet.getRestraintList(name)
            if restraint is not None:
                self.error('nef_restraint_list - RestraintList {} already exists'.format(restraint), saveFrame, (restraint,))

        self._verifyLoops(project, saveFrame, name=name)

    verifiers['nef_distance_restraint_list'] = verify_nef_restraint_list
    verifiers['nef_dihedral_restraint_list'] = verify_nef_restraint_list
    verifiers['nef_rdc_restraint_list'] = verify_nef_restraint_list
    verifiers['ccpn_restraint_list'] = verify_nef_restraint_list

    def content_nef_restraint_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """Get the contents of nef_restraint_list saveFrame"""
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']

        # Get name from framecode, add type disambiguation, and correct for ccpn dataSetSerial addition
        name = framecode[len(category) + 1:]
        dataSetSerial = saveFrame.get('ccpn_dataset_serial')
        if dataSetSerial is not None:
            ss = '`%s`' % dataSetSerial
            if name.startswith(ss):
                name = name[len(ss):]

        # ejb - need to remove the rogue `n` at the beginning of the name if it exists
        #       as it is passed into the namespace and gets added iteratively every save
        #       next three lines remove all occurrences of `n` from name
        import re

        regex = u'\`\d*`+?'
        name = re.sub(regex, '', name)  # substitute with ''

        result = {category: OrderedSet([name])}

        self._contentLoops(project, saveFrame)
        self.updateContent(saveFrame, result)

    contents['nef_distance_restraint_list'] = content_nef_restraint_list        # could be _contentLoops
    contents['nef_dihedral_restraint_list'] = content_nef_restraint_list
    contents['nef_rdc_restraint_list'] = content_nef_restraint_list
    contents['ccpn_restraint_list'] = content_nef_restraint_list

    def load_nef_restraint(self, restraintList: RestraintList, loop: StarIo.NmrLoop,
                           itemLength: int = None):
        """Serves to load nef_distance_restraint, nef_dihedral_restraint,
        nef_rdc_restraint and ccpn_restraint loops"""

        # NB Restraint.name - written out for dihedral restraints - is not read.
        # Which is probably OK, it is derived from the atoms.

        result = []

        string2ItemMap = self._dataSet2ItemMap[restraintList.dataSet]

        # set itemLength if not passed in:
        if not itemLength:
            itemLength = coreConstants.constraintListType2ItemLength.get(restraintList.restraintType)

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        contributionTags = sorted(map2.values())
        restraints = {}
        # assignTags = ('chain_code', 'sequence_code', 'residue_name', 'atom_name')

        max = itemLength + 1
        multipleAttributes = OD((
            ('chainCodes', tuple('chain_code_%s' % ii for ii in range(1, max))),
            ('sequenceCodes', tuple('sequence_code_%s' % ii for ii in range(1, max))),
            ('residueTypes', tuple('residue_name_%s' % ii for ii in range(1, max))),
            ('atomNames', tuple('atom_name_%s' % ii for ii in range(1, max))),
            ))

        parametersFromLoopRow = self._parametersFromLoopRow
        defaultChainCode = self.defaultChainCode
        for row in loop.data:

            # get or make restraint
            serial = row.get('restraint_id')
            restraint = restraints.get(serial)
            if restraint is None:
                valuesToContribution = {}
                dd = {'serial': serial}
                val = row.get('ccpn_vector_length')
                if val is not None:
                    dd['vectorLength'] = val
                val = row.get('ccpn_figure_of_Merit')
                if val is not None:
                    dd['figureOfMerit'] = val
                val = row.get('ccpn_comment')
                if val is not None:
                    dd['comment'] = val
                restraint = restraintList.newRestraint(**dd)
                restraints[serial] = restraint
                result.append(restraint)

            # Get or make restraintContribution
            parameters = parametersFromLoopRow(row, map2)
            combinationId = parameters.get('combinationId')
            nonAssignmentValues = tuple(parameters.get(tag) for tag in contributionTags)
            if combinationId:
                # Items in a combination are ANDed, so each line has one contribution
                contribution = restraint.newRestraintContribution(**parameters)
            else:
                contribution = valuesToContribution.get(nonAssignmentValues)
                if contribution is None:
                    contribution = restraint.newRestraintContribution(**parameters)
                    valuesToContribution[nonAssignmentValues] = contribution

            # Add item
            # ll = [row._get(tag)[:itemLength] for tag in assignTags]
            ll = [list(row.get(x) for x in y) for y in multipleAttributes.values()]
            # Reset missing chain codes to default
            # ll[0] = [x or defaultChainCode for x in ll[0]]

            idStrings = []
            for item in zip(*ll):
                if defaultChainCode is not None and item[0] is None:
                    # ChainCode missing - replace with default chain code
                    item = (defaultChainCode,) + item[1:]
                idStrings.append(Pid.IDSEP.join(('' if x is None else str(x)) for x in item))
            try:
                contribution.addRestraintItem(idStrings, string2ItemMap)
            except ValueError:
                self.warning("Cannot Add restraintItem %s. Identical to previous. Skipping" % idStrings)

        #
        return result

    #
    importers['nef_distance_restraint'] = load_nef_restraint
    importers['nef_dihedral_restraint'] = load_nef_restraint
    importers['nef_rdc_restraint'] = load_nef_restraint
    importers['ccpn_restraint'] = load_nef_restraint

    # NOTE:ED - do restraint contributions need verifying?

    verifiers['nef_distance_restraint'] = _noLoopVerify
    verifiers['nef_dihedral_restraint'] = _noLoopVerify
    verifiers['nef_rdc_restraint'] = _noLoopVerify
    verifiers['ccpn_restraint'] = _noLoopVerify

    def content_nef_restraint(self, restraintList: RestraintList, loop: StarIo.NmrLoop, itemLength: int = None) -> Optional[OrderedSet]:
        """Get the contents for nef_distance_restraint, nef_dihedral_restraint,
        nef_rdc_restraint and ccpn_restraint loops"""
        result = OrderedSet()

        if itemLength is None:
            self.error('Undefined restraint item length', loop, None)
            return None

        mapping = nef2CcpnMap[loop.name]
        max = itemLength + 1
        multipleAttributes = OD((
            ('chainCodes', tuple('chain_code_%s' % ii for ii in range(1, max))),
            ('sequenceCodes', tuple('sequence_code_%s' % ii for ii in range(1, max))),
            ('residueTypes', tuple('residue_name_%s' % ii for ii in range(1, max))),
            ('atomNames', tuple('atom_name_%s' % ii for ii in range(1, max))),
            ))

        defaultChainCode = self.defaultChainCode
        for row in loop.data:
            ll = [list(row.get(x) for x in y) for y in multipleAttributes.values()]

            for item in zip(*ll):
                if defaultChainCode is not None and item[0] is None:
                    # ChainCode missing - replace with default chain code
                    item = (defaultChainCode,) + item[1:]

                result.add(item)

        return result

    contents['nef_distance_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Distance'))
    contents['nef_dihedral_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Dihedral'))
    contents['nef_rdc_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Rdc'))

    # NOTE:ED - need to check this one
    contents['ccpn_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Distance'))

    def load_nef_nmr_spectrum(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        dimensionTransferTags = ('dimension_1', 'dimension_2', 'transfer_type', 'is_indirect')

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        # Get peakList parameters and make peakList
        peakListParameters, dummy = self._parametersFromSaveFrame(saveFrame, mapping)

        # Get spectrum parameters
        spectrumParameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping,
                                                                      ccpnPrefix='spectrum')

        # Get name from spectrum parameters, or from the framecode
        spectrumName = framecode[len(category) + 1:]
        if spectrumName.endswith('`'):
            peakListSerial = peakListParameters.get('serial')
            if peakListSerial:
                ss = '`%s`' % peakListSerial
                # Remove peakList serial suffix (which was added for disambiguation)
                # So that multiple peakLists all go to one Spectrum
                if spectrumName.endswith(ss):
                    spectrumName = spectrumName[:-len(ss)]
            else:
                ll = spectrumName.rsplit('`', 2)
                if len(ll) == 3:
                    # name is of form abc`xyz`
                    try:
                        peakListParameters['serial'] = int(ll[1])
                    except ValueError:
                        pass
                    else:
                        spectrumName = ll[0]

        spectrum = project.getSpectrum(spectrumName)
        if spectrum is None:
            # Spectrum does not already exist - create it.
            # NB For CCPN-exported projects spectra with multiple peakLists are handled this way

            framecode = saveFrame.get('chemical_shift_list')
            if framecode:
                spectrumParameters['chemicalShiftList'] = self.frameCode2Object[framecode]
            else:
                # Defaults to first (there should be only one, but we want the read to work) ShiftList
                spectrumParameters['chemicalShiftList'] = self.defaultChemicalShiftList

            framecode = saveFrame.get('ccpn_sample')
            if framecode:
                spectrumParameters['sample'] = self.frameCode2Object[framecode]

            # get per-dimension data - NB these are mandatory and cannot be worked around
            dimensionData = self.read_nef_spectrum_dimension(project,
                                                             saveFrame['nef_spectrum_dimension'])
            # read  dimension transfer data
            loopName = 'nef_spectrum_dimension_transfer'
            # Those are treated elsewhere
            loop = saveFrame.get(loopName)
            if loop:
                data = loop.data
                transferData = [
                    SpectrumLib.MagnetisationTransferTuple(*(row.get(tag) for tag in dimensionTransferTags))
                    for row in data
                    ]
            else:
                transferData = []

            spectrum = createSpectrum(project, spectrumName, spectrumParameters, dimensionData,
                                      transferData=transferData)

            # Set experiment transfers at the API level
            if transferData and not spectrum.magnetisationTransfers:
                spectrum._setMagnetisationTransfers(transferData)

            # Make data storage object
            filePath = saveFrame.get('ccpn_spectrum_file_path')
            if filePath:
                storageParameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping,
                                                                             ccpnPrefix='spectrum._wrappedData.dataStore'
                                                                             )
                storageParameters['numPoints'] = spectrum.pointCounts
                spectrum._wrappedData.addDataStore(filePath, **storageParameters)

            # Load CCPN dimensions before peaks
            loopName = 'ccpn_spectrum_dimension'
            # Those are treated elsewhere
            loop = saveFrame.get(loopName)
            if loop:
                self.load_ccpn_spectrum_dimension(spectrum, loop)

        # Make PeakList
        peakList = spectrum.newPeakList(**peakListParameters)

        # Load peaks
        self.load_nef_peak(peakList, saveFrame.get('nef_peak'))

        # Load remaining loops, with spectrum as parent
        for loopName in loopNames:
            if loopName not in ('nef_spectrum_dimension', 'ccpn_spectrum_dimension', 'nef_peak',
                                'nef_spectrum_dimension_transfer'):
                # Those are treated elsewhere
                loop = saveFrame.get(loopName)
                if loop:
                    importer = self.importers[loopName]
                    importer(self, spectrum, loop)
        #
        return peakList

    #
    importers['nef_nmr_spectrum'] = load_nef_nmr_spectrum

    def verify_nef_nmr_spectrum(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        dimensionTransferTags = ('dimension_1', 'dimension_2', 'transfer_type', 'is_indirect')

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        # Get peakList parameters and make peakList
        peakListParameters, dummy = self._parametersFromSaveFrame(saveFrame, mapping)

        # Get spectrum parameters
        spectrumParameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping,
                                                                      ccpnPrefix='spectrum')

        # Get name from spectrum parameters, or from the framecode
        spectrumName = framecode[len(category) + 1:]
        if spectrumName.endswith('`'):
            peakListSerial = peakListParameters.get('serial')
            if peakListSerial:
                ss = '`%s`' % peakListSerial
                # Remove peakList serial suffix (which was added for disambiguation)
                # So that multiple peakLists all go to one Spectrum
                if spectrumName.endswith(ss):
                    spectrumName = spectrumName[:-len(ss)]
            else:
                ll = spectrumName.rsplit('`', 2)
                if len(ll) == 3:
                    # name is of form abc`xyz`
                    try:
                        peakListParameters['serial'] = int(ll[1])
                    except ValueError:
                        pass
                    else:
                        spectrumName = ll[0]

        spectrum = project.getSpectrum(spectrumName)
        if spectrum is not None:
            self.error('nef_nmr_spectrum - Spectrum {} already exists'.format(spectrum), saveFrame, (spectrum,))

            self._verifyLoops(spectrum, saveFrame, num_dimensions=saveFrame['num_dimensions'])

    verifiers['nef_nmr_spectrum'] = verify_nef_nmr_spectrum

    def content_nef_nmr_spectrum(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        # Get peakList parameters and make peakList
        peakListParameters, dummy = self._parametersFromSaveFrame(saveFrame, mapping)

        # Get name from spectrum parameters, or from the framecode
        spectrumName = framecode[len(category) + 1:]
        if spectrumName.endswith('`'):
            peakListSerial = peakListParameters.get('serial')
            if peakListSerial:
                ss = '`%s`' % peakListSerial
                # Remove peakList serial suffix (which was added for disambiguation)
                # So that multiple peakLists all go to one Spectrum
                if spectrumName.endswith(ss):
                    spectrumName = spectrumName[:-len(ss)]
            else:
                ll = spectrumName.rsplit('`', 2)
                if len(ll) == 3:
                    # name is of form abc`xyz`
                    try:
                        peakListParameters['serial'] = int(ll[1])
                    except ValueError:
                        pass
                    else:
                        spectrumName = ll[0]
        result = {category: OrderedSet([spectrumName])}

        self._contentLoops(project, saveFrame, addLoopAttribs=['num_dimensions'])
        self.updateContent(saveFrame, result)

    # contents['nef_nmr_spectrum'] = partial(_contentLoops, addLoopAttribs=['num_dimensions'])
    contents['nef_nmr_spectrum'] = content_nef_nmr_spectrum

    def read_nef_spectrum_dimension_transfer(self, loop: StarIo.NmrLoop):

        transferTypes = ('onebond', 'Jcoupling', 'Jmultibond', 'relayed', 'through-space',
                         'relayed-alternate')

        result = []

        if loop:
            data = loop.data
            for row in data:
                ll = [row.get(tag) for tag in ('dimension_1', 'dimension_2', 'transfer_type',
                                               'is_indirect')]
                result.append(SpectrumLib.MagnetisationTransferTuple(*ll))
        #
        return result

    def load_nef_spectrum_dimension_transfer(self, spectrum: Spectrum, loop: StarIo.NmrLoop):

        transferTypes = ('onebond', 'Jcoupling', 'Jmultibond', 'relayed', 'through-space',
                         'relayed-alternate')

        result = []

        if loop:
            apiExperiment = spectrum._wrappedData.experiment

            data = loop.data
            # Remove invalid data rows
            for row in data:
                ll = [row.get(tag) for tag in ('dimension_1', 'dimension_2', 'transfer_type',
                                               'is_indirect')]
                if (apiExperiment.findFirstExpDim(dim=row['dimension_1']) is None or
                        apiExperiment.findFirstExpDim(dim=row['dimension_2']) is None or
                        row['transfer_type'] not in transferTypes):
                    self.warning("Illegal values in nef_spectrum_dimension_transfer: %s"
                                 % list(row.values()))
                else:
                    result.append(SpectrumLib.MagnetisationTransferTuple(*ll))
        #
        return result

    def process_nef_spectrum_dimension_transfer(self, spectrum: Spectrum,
                                                dataLists: Sequence[Sequence]):
        # Store expTransfers in API as we can not be sure we will get a refExperiment

        apiExperiment = spectrum._wrappedData.experiment

        for ll in dataLists:
            expDimRefs = []
            for dim in ll[:2]:
                expDim = apiExperiment.findFirstExpDim(dim=dim)
                # After spectrum creation there will be one :
                expDimRefs.append(expDim.sortedExpDimRefs()[0])
            if apiExperiment.findFirstExpTransfer(expDimRefs=expDimRefs) is None:
                apiExperiment.newExpTransfer(expDimRefs=expDimRefs, transferType=ll[2],
                                             isDirect=not ll[3])
            else:
                self.warning("Duplicate nef_spectrum_dimension_transfer: %s" % (ll,))

    verifiers['nef_spectrum_dimension_transfer'] = _noLoopVerify
    contents['nef_spectrum_dimension_transfer'] = _noLoopContent

    def load_ccpn_spectrum_dimension(self, spectrum: Spectrum, loop: StarIo.NmrLoop) -> dict:
        """Read ccpn_spectrum_dimension loop, set the relevant values,
    and return the spectrum and other parameters for further processing"""

        params = {}
        extras = {}
        nefTag2ccpnTag = nef2CcpnMap['ccpn_spectrum_dimension']

        if not loop.data:
            raise ValueError("ccpn_spectrum_dimension is empty")

        rows = sorted(loop.data, key=itemgetter('dimension_id'))

        # Get spectrum attributes
        for nefTag, ccpnTag in nefTag2ccpnTag.items():
            if nefTag in rows[0]:
                ll = list(row.get(nefTag) for row in rows)
                if any(x is not None for x in ll):
                    if ccpnTag and not '.' in ccpnTag:
                        params[ccpnTag] = ll
                    else:
                        extras[nefTag] = ll

        # Set main values
        for tag, value in params.items():
            if tag != 'referencePoints':
                setattr(spectrum, tag, value)

        referencePoints = params.get('referencePoints')
        points = []
        values = []
        if referencePoints is not None:
            spectrumReferences = spectrum.spectrumReferences
            for ii, spectrumReference in enumerate(spectrumReferences):
                if spectrumReference is None:
                    points.append(None)
                    values.append(None)
                else:
                    point = referencePoints[ii]
                    points.append(point)
                    values.append(spectrumReference.pointToValue(point))
        spectrum.referencePoints = points
        spectrum.referenceValues = values

        # set storage attributes
        value = extras.get('dimension_is_complex')
        if value:
            spectrum._wrappedData.dataStore.isComplex = value
        value = extras.get('dimension_block_size')
        if value:
            spectrum._wrappedData.dataStore.blockSizes = value

        # set aliasingLimits
        defaultLimits = spectrum.dimensionCount * [None]
        lowerLimits = extras.get('lower_aliasing_limit', defaultLimits)
        higherLimits = extras.get('higher_aliasing_limit', defaultLimits)
        spectrum.aliasingLimits = list(zip(lowerLimits, higherLimits))

    importers['ccpn_spectrum_dimension'] = load_ccpn_spectrum_dimension
    verifiers['ccpn_spectrum_dimension'] = _noLoopVerify
    contents['ccpn_spectrum_dimension'] = _noLoopContent

    # def adjustAxisCodes(self, spectrum, dimensionData):
    #   # Use data to rename axisCodes
    #   axisCodes = spectrum.axisCodes
    #   newCodes = list(axisCodes)
    #   atomTypes = [commonUtil.splitIntFromChars(x)[1] for x in spectrum.isotopeCodes]
    #   acquisitionAxisCode = spectrum.acquisitionAxisCode
    #   if acquisitionAxisCode is not None:
    #     acquisitionDim = axisCodes.index(acquisitionAxisCode) + 1
    #     if acquisitionAxisCode == atomTypes[acquisitionDim - 1]:
    #       # this axisCode needs improvement
    #       for pair in oneBondPairs:
    #         # First do acquisition dimension
    #         if acquisitionDim in pair:
    #           ll = pair.copy()
    #           ll.remove(acquisitionDim)
    #           otherDim = ll[0]
    #           otherCode = axisCodes[otherDim - 1]
    #           if otherCode == atomTypes[otherDim - 1]:

    def read_nef_spectrum_dimension(self, project: Project, loop: StarIo.NmrLoop):
        """Read nef_spectrum_dimension loop and convert data to a dictionary
        of ccpnTag:[per-dimension-value]"""

        # NB we are not using absolute_peak_positions - if false what could we do?

        result = {}
        nefTag2ccpnTag = nef2CcpnMap['nef_spectrum_dimension']

        rows = sorted(loop.data, key=itemgetter('dimension_id'))
        # rows = [(row['dimension_id'], row) for row in loop.data]
        # rows = [tt[1] for tt in sorted(rows)]

        if not rows:
            raise ValueError("nef_spectrum_dimension is missing or empty")

        # Get spectrum attributes
        for nefTag, ccpnTag in nefTag2ccpnTag.items():
            if nefTag in rows[0]:
                if ccpnTag:
                    result[ccpnTag] = list(row.get(nefTag) for row in rows)
                else:
                    # Unmapped attributes are passed with the original tag for later processing
                    result[nefTag] = list(row.get(nefTag) for row in rows)
        #
        return result

    verifiers['nef_spectrum_dimension'] = _noLoopVerify
    contents['nef_spectrum_dimension'] = _noLoopContent

    def load_ccpn_integral_list(self, spectrum: Spectrum,
                                loop: StarIo.NmrLoop) -> List[IntegralList]:

        result = []

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        creatorFunc = spectrum.newIntegralList
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            integralList = creatorFunc(**parameters)
            # integralList.resetSerial(row['serial'])
            # NB former call was BROKEN!
            # modelUtil.resetSerial(integralList, row['serial'], 'integralLists')
            result.append(integralList)
        #
        return result

    importers['ccpn_integral_list'] = load_ccpn_integral_list

    def verify_ccpn_integral_list(self, spectrum: Spectrum, loop: StarIo.NmrLoop, **kwds):
        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        creatorFunc = spectrum.getIntegralList
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            integralList = creatorFunc(parameters['serial'])
            if integralList is not None:
                self.error('ccpn_integral_list - IntegralList {} already exists'.format(integralList), loop, (integralList,))

    verifiers['ccpn_integral_list'] = verify_ccpn_integral_list
    contents['ccpn_integral_list'] = _noLoopContent

    def load_ccpn_multiplet_list(self, spectrum: Spectrum,
                                 loop: StarIo.NmrLoop) -> List[MultipletList]:

        result = []

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        creatorFunc = spectrum.newMultipletList
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            multipletList = creatorFunc(**parameters)
            # multipletList.resetSerial(row['serial'])
            # NB former call was BROKEN!
            # modelUtil.resetSerial(multipletList, row['serial'], 'multipletLists')
            result.append(multipletList)

        return result

    importers['ccpn_multiplet_list'] = load_ccpn_multiplet_list

    def verify_ccpn_multiplet_list(self, spectrum: Spectrum, loop: StarIo.NmrLoop, **kwds):
        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        creatorFunc = spectrum.getMultipletList
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            multipletList = creatorFunc(parameters['serial'])
            if multipletList is not None:
                self.error('ccpn_multiplet_list - MultipletList {} already exists'.format(multipletList), loop, (multipletList,))

    verifiers['ccpn_multiplet_list'] = verify_ccpn_multiplet_list
    contents['ccpn_multiplet_list'] = _noLoopContent

    def load_ccpn_integral(self, spectrum: Spectrum,
                           loop: StarIo.NmrLoop) -> List[Integral]:

        result = []

        # Get name map for per-dimension attributes
        max = spectrum.dimensionCount + 1
        multipleAttributes = {
            'slopes'     : tuple('slopes_%s' % ii for ii in range(1, max)),
            'lowerLimits': tuple('lower_limits_%s' % ii for ii in range(1, max)),
            'upperLimits': tuple('upper_limits_%s' % ii for ii in range(1, max)),
            }

        serial2creatorFunc = dict((x.serial, x.newIntegral) for x in spectrum.integralLists)

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            integral = serial2creatorFunc[row['integral_list_serial']](**parameters)

            # integral.slopes = tuple(row.get(x) for x in multipleAttributes['slopes'])
            # lowerLimits = tuple(row.get(x) for x in multipleAttributes['lowerLimits'])
            # upperLimits = tuple(row.get(x) for x in multipleAttributes['upperLimits'])
            # # integral.slopes = row._get('slopes')
            # # lowerLimits = row._get('lower_limits')
            # # upperLimits = row._get('upper_limits')
            # integral.limits = zip((lowerLimits, upperLimits))

            if row['slopes']:
                integral.slopes = eval(row['slopes'])
            if row['limits']:
                integral.limits = eval(row['limits'])
            if row['point_limits']:
                integral.pointLimits = eval(row['point_limits'])

            # integral.resetSerial(row['integral_serial'])
            # NB former call was BROKEN!
            # modelUtil.resetSerial(integral, row['integral_serial'], 'integrals')
            mPeak = row['ccpn_linked_peak']
            peak = spectrum.project.getByPid(mPeak)
            if peak:
                integral.peak = peak

            result.append(integral)
        #
        return result

    importers['ccpn_integral'] = load_ccpn_integral

    # def verify_ccpn_integral(self, spectrum: Spectrum,
    #                          loop: StarIo.NmrLoop) -> List[Integral]:
    #     pass

    verifiers['ccpn_integral'] = _noLoopVerify

    # def content_ccpn_integral(self, spectrum: Spectrum, loop: StarIo.NmrLoop) -> Optional[dict]:
    #     self.storeContent(loop, None)
    #     return None

    contents['ccpn_integral'] = _noLoopContent

    def load_ccpn_multiplet(self, spectrum: Spectrum,
                            loop: StarIo.NmrLoop) -> List[Multiplet]:

        result = []

        # Get name map for per-dimension attributes
        max = spectrum.dimensionCount + 1
        serial2creatorFunc = dict((x.serial, x.newMultiplet) for x in spectrum.multipletLists)

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            multiplet = serial2creatorFunc[row['multiplet_list_serial']]()  #**parameters)

            if row['slopes']:
                multiplet.slopes = eval(row['slopes'])
            if row['limits']:
                multiplet.limits = eval(row['limits'])
            if row['point_limits']:
                multiplet.pointLimits = eval(row['point_limits'])

            # multiplet.resetSerial(row['multiplet_serial'])
            result.append(multiplet)

        return result

    importers['ccpn_multiplet'] = load_ccpn_multiplet

    # def verify_ccpn_multiplet(self, spectrum: Spectrum,
    #                           loop: StarIo.NmrLoop) -> List[Multiplet]:
    #     pass

    verifiers['ccpn_multiplet'] = _noLoopVerify

    # def content_ccpn_multiplet(self, spectrum: Spectrum,
    #                         loop: StarIo.NmrLoop) -> List[Multiplet]:
    #     self.storeContent(loop, None)
    #     return None

    contents['ccpn_multiplet'] = _noLoopContent

    def load_ccpn_multiplet_peaks(self, spectrum: Spectrum,
                                  loop: StarIo.NmrLoop) -> List[Multiplet]:

        result = []

        # Get name map for per-dimension attributes
        max = spectrum.dimensionCount + 1
        serial2creatorFunc = dict((x.serial, x.newMultiplet) for x in spectrum.multipletLists)

        # mapping = nef2CcpnMap[loop.name]
        # map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:

            mList = row['multiplet_list_serial']
            mSerial = row['multiplet_serial']
            mPeak = row['multiplet_peak']

            mlList = [ml for ml in spectrum.multipletLists if ml.serial == mList]
            mlts = [mt for ml in mlList for mt in ml.multiplets if mt.serial == mSerial]
            peak = spectrum.project.getByPid(mPeak)

            # NOTE:ED - there is a problem with cross-spectra peaks
            if mlts and peak and peak not in mlts[0].peaks:
                mlts[0].addPeaks(peak)

    importers['ccpn_multiplet_peaks'] = load_ccpn_multiplet_peaks

    # def verify_ccpn_multiplet_peaks(self, spectrum: Spectrum,
    #                                 loop: StarIo.NmrLoop) -> List[Multiplet]:
    #     pass

    verifiers['ccpn_multiplet_peaks'] = _noLoopVerify

    # def content_ccpn_multiplet_peaks(self, spectrum: Spectrum,
    #                               loop: StarIo.NmrLoop) -> List[Multiplet]:
    #     self.storeContent(loop, None)
    #     return None

    contents['ccpn_multiplet_peaks'] = _noLoopContent

    def load_ccpn_peak_cluster_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        # load ccpn_peak_clusters
        loopName = 'ccpn_peak_clusters'
        loop = saveFrame[loopName]
        creatorFunc = project.newPeakCluster

        result = []
        mapping = nef2CcpnMap[loopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            obj = creatorFunc(**parameters)

            # load time stamps and serial = must bypass the API, as they are frozen
            apiPeakCluster = obj._wrappedData
            obj.resetSerial(row['serial'])
            result.append(obj)

        # load ccpn_peak_clusters
        loopName = 'ccpn_peak_cluster_peaks'
        loop = saveFrame[loopName]

        for row in loop.data:
            pSerial = row['serial']
            pPeak = row['peak']

            pcs = [pc for pc in project.peakClusters if pc.serial == pSerial]
            peak = project.getByPid(pPeak)
            if pcs and peak:
                pcs[0].addPeaks(peak)

        return result

    importers['ccpn_peak_cluster_list'] = load_ccpn_peak_cluster_list

    # def verify_ccpn_peak_cluster_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     pass

    verifiers['ccpn_peak_cluster_list'] = _noLoopVerify

    # def content_ccpn_peak_cluster_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     self.storeContent(saveFrame, None)
    #     return None

    contents['ccpn_peak_cluster_list'] = _noLoopContent

    def load_nef_peak(self, peakList: PeakList, loop: StarIo.NmrLoop) -> List[Peak]:
        """Serves to load nef_peak loop"""

        result = []

        dimensionCount = peakList.spectrum.dimensionCount

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])

        # Get name map for per-dimension attributes
        max = dimensionCount + 1
        multipleAttributes = {
            'position'     : tuple('position_%s' % ii for ii in range(1, max)),
            'positionError': tuple('position_uncertainty_%s' % ii for ii in range(1, max)),
            'chainCodes'   : tuple('chain_code_%s' % ii for ii in range(1, max)),
            'sequenceCodes': tuple('sequence_code_%s' % ii for ii in range(1, max)),
            'residueTypes' : tuple('residue_name_%s' % ii for ii in range(1, max)),
            'atomNames'    : tuple('atom_name_%s' % ii for ii in range(1, max)),
            }

        peaks = {}
        assignedNmrAtoms = []

        for row in loop.data:

            parameters = self._parametersFromLoopRow(row, map2)

            # get or make peak
            serial = parameters['serial']
            peak = peaks.get(serial)
            # TODO check if peak parameters are the same for all rows, and do something about it
            # For now we simply use the first row that appears
            if peak is None:
                # start of a new peak

                # finalise last peak
                if result and assignedNmrAtoms:
                    # There is a peak in result, and the peak has assignments to set
                    result[-1].assignedNmrAtoms = assignedNmrAtoms
                    assignedNmrAtoms.clear()

                # make new peak  multipleAttributes
                # parameters['position'] = row._get('position')[:dimensionCount]
                parameters['ppmPositions'] = tuple(row.get(x) for x in multipleAttributes['position'])
                parameters['positionError'] = tuple(row.get(x) for x in multipleAttributes['positionError'])
                # parameters['positionError'] = row._get('position_uncertainty')[:dimensionCount]
                peak = peakList.newPeak(**parameters)
                peaks[serial] = peak
                result.append(peak)

            # Add assignment
            # NB the self.defaultChainCode or converts code None to the default chain code
            chainCodes = tuple(row.get(x) or self.defaultChainCode for x in multipleAttributes['chainCodes'])
            sequenceCodes = tuple(row.get(x) for x in multipleAttributes['sequenceCodes'])
            residueTypes = tuple(row.get(x) for x in multipleAttributes['residueTypes'])
            atomNames = tuple(row.get(x) for x in multipleAttributes['atomNames'])
            # chainCodes = row._get('chain_code')[:dimensionCount]
            # sequenceCodes = row._get('sequence_code')[:dimensionCount]
            # residueTypes = row._get('residue_name')[:dimensionCount]
            # atomNames = row._get('atom_name')[:dimensionCount]
            assignments = zip(chainCodes, sequenceCodes, residueTypes, atomNames)
            nmrAtoms = []
            foundAssignment = False
            for tt in assignments:
                if all(x is None for x in tt):
                    # No assignment
                    nmrAtoms.append(None)
                elif tt[1] and tt[3]:
                    # Enough for an assignment - make it
                    foundAssignment = True
                    nmrResidue = self.produceNmrResidue(*tt[:3])
                    nmrAtom = self.produceNmrAtom(nmrResidue, tt[3])
                    nmrAtoms.append(nmrAtom)
                else:
                    # partial and unusable assignment
                    self.warning("Uninterpretable Peak assignment for peak %s: %s. Set to None"
                                 % (peak.serial, tt))
                    nmrAtoms.append(None)
            if foundAssignment:
                assignedNmrAtoms.append(nmrAtoms)

        # finalise last peak
        if result and assignedNmrAtoms:
            # There is a peak in result, and the peak has assignments to set
            result[-1].assignedNmrAtoms = assignedNmrAtoms
            assignedNmrAtoms.clear()
        #
        return result

    #
    importers['nef_peak'] = load_nef_peak

    # def verify_nef_peak(self, peakList: PeakList, loop: StarIo.NmrLoop) -> List[Peak]:
    #     """Serves to verify nef_peak loop"""
    #     pass
    #
    # verifiers['nef_peak'] = verify_nef_peak

    verifiers['nef_peak'] = _noLoopVerify

    def content_nef_peak(self, peakList: PeakList, loop: StarIo.NmrLoop, itemLength: int = None) -> typing.Optional[OrderedSet]:
        """Get the contents of nef_peak loop"""
        result = OrderedSet()

        if itemLength is None:
            self.error('Undefined peak item length', loop, None)
            return None

        mapping = nef2CcpnMap[loop.name]
        max = itemLength + 1
        multipleAttributes = OD((
            ('chainCodes', tuple('chain_code_%s' % ii for ii in range(1, max))),
            ('sequenceCodes', tuple('sequence_code_%s' % ii for ii in range(1, max))),
            ('residueTypes', tuple('residue_name_%s' % ii for ii in range(1, max))),
            ('atomNames', tuple('atom_name_%s' % ii for ii in range(1, max))),
            ))

        defaultChainCode = self.defaultChainCode
        for row in loop.data:
            ll = [list(row.get(x) for x in y) for y in multipleAttributes.values()]

            idStrings = []
            for item in zip(*ll):
                if defaultChainCode is not None and item[0] is None:
                    # ChainCode missing - replace with default chain code
                    item = (defaultChainCode,) + item[1:]

                # pid = Pid.IDSEP.join(('' if x is None else str(x)) for x in item)

                if any(x is not None for x in item):
                    # ignore peaks that are not defined
                    result.add(item)

        return result

    contents['nef_peak'] = content_nef_peak

    def load_nef_peak_restraint_links(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        """load nef_peak_restraint_links saveFrame"""

        mapping = nef2CcpnMap['nef_peak_restraint_links']
        for tag, ccpnTag in mapping.items():
            if ccpnTag == _isALoop:
                loop = saveFrame.get(tag)
                if loop:
                    importer = self.importers[tag]
                    importer(self, project, loop)
        #
        return project

    #
    importers['nef_peak_restraint_links'] = load_nef_peak_restraint_links

    # def verify_nef_peak_restraint_links(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     """verify nef_peak_restraint_links saveFrame"""
    #     pass
    #
    # verifiers['nef_peak_restraint_links'] = verify_nef_peak_restraint_links
    verifiers['nef_peak_restraint_links'] = _verifyLoops

    # def content_nef_peak_restraint_links(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     """Get the contents of nef_peak_restraint_links saveFrame"""
    #     self.storeContent(saveFrame, None)
    #     return None

    contents['nef_peak_restraint_links'] = _contentLoops

    def load_nef_peak_restraint_link(self, project: Project, loop: StarIo.NmrLoop):
        """Load nef_peak_restraint_link loop"""

        links = {}

        # NBNB TODO:RASMUS There was a very strange bug in this function
        # When I was using PeakList.getPeak(str(serial))
        # and RestraintList.getRestraint(str(serial), peaks and restraints were
        # sometimes missed even though the data were present.
        # Doing the test at the API level (as now) fixed the problem
        # THIS SHOULD BE IMPOSSIBLE
        # At some point we ought to go back, reproduce the bug, and remove the reason for it.

        for row in loop.data:
            peakList = self.frameCode2Object.get(row.get('nmr_spectrum_id'))
            if peakList is None:
                self.warning(
                        "No Spectrum saveframe found with framecode %s. Skipping peak_restraint_link"
                        % row.get('nmr_spectrum_id')
                        )
                continue
            restraintList = self.frameCode2Object.get(row.get('restraint_list_id'))
            if restraintList is None:
                self.warning(
                        "No RestraintList saveframe found with framecode %s. Skipping peak_restraint_link"
                        % row.get('restraint_list_id')
                        )
                continue
            peak = peakList._wrappedData.findFirstPeak(serial=row.get('peak_id'))
            if peak is None:
                self.warning(
                        "No peak %s found in %s Skipping peak_restraint_link"
                        % (row.get('peak_id'), row.get('nmr_spectrum_id'))
                        )
                continue
            restraint = restraintList._wrappedData.findFirstConstraint(serial=row.get('restraint_id'))
            if restraint is None:
                self.warning(
                        "No restraint %s found in %s Skipping peak_restraint_link"
                        % (row.get('restraint_id'), row.get('restraint_list_id'))
                        )
                continue

            # Is all worked, now accumulate the lin
            ll = links.get(restraint, [])
            ll.append(peak)
            links[restraint] = ll

        # Set the actual links
        for restraint, peaks in links.items():
            restraint.peaks = peaks
        #
        return None

    #
    importers['nef_peak_restraint_link'] = load_nef_peak_restraint_link

    # def verify_nef_peak_restraint_link(self, project: Project, loop: StarIo.NmrLoop):
    #     """verify nef_peak_restraint_link loop"""
    #     pass

    verifiers['nef_peak_restraint_link'] = _noLoopVerify

    # def content_nef_peak_restraint_link(self, project: Project, loop: StarIo.NmrLoop):
    #     """Get the contents of nef_peak_restraint_link loop"""
    #     self.storeContent(loop, None)
    #     return None

    contents['nef_peak_restraint_link'] = _noLoopContent

    def load_ccpn_spectrum_group(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        # Make main object
        result = project.newSpectrumGroup(**parameters)

        # Load loops, with object as parent
        for loopName in loopNames:
            loop = saveFrame.get(loopName)
            if loop:
                importer = self.importers[loopName]
                importer(self, result, loop)
        #
        return result

    #
    importers['ccpn_spectrum_group'] = load_ccpn_spectrum_group

    # def verify_ccpn_spectrum_group(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     pass
    #
    # verifiers['ccpn_spectrum_group'] = verify_ccpn_spectrum_group
    verifiers['ccpn_spectrum_group'] = _verifyLoops

    # def content_ccpn_spectrum_group(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     self.storeContent(saveFrame, None)
    #     return None

    contents['ccpn_spectrum_group'] = _contentLoops

    def load_ccpn_group_spectrum(self, parent: SpectrumGroup, loop: StarIo.NmrLoop):
        """load ccpn_group_spectrum loop"""

        spectra = []
        for row in loop.data:
            spectrum = self.project.getSpectrum(row.get('nmr_spectrum_id'))
            if spectrum is None:
                self.warning(
                        "No Spectrum saveframe found with framecode %s. Skipping Spectrum from SpectrumGroup"
                        % row.get('nmr_spectrum_id')
                        )
            else:
                spectra.append(spectrum)
        #
        parent.spectra = spectra

    #
    importers['ccpn_group_spectrum'] = load_ccpn_group_spectrum

    # def verify_ccpn_group_spectrum(self, parent: SpectrumGroup, loop: StarIo.NmrLoop):
    #     """verify ccpn_group_spectrum loop"""
    #     pass

    verifiers['ccpn_group_spectrum'] = _noLoopVerify

    # def content_ccpn_group_spectrum(self, parent: SpectrumGroup, loop: StarIo.NmrLoop):
    #     """Get the contents of ccpn_group_spectrum loop"""
    #     self.storeContent(loop, None)
    #     return None

    contents['ccpn_group_spectrum'] = _noLoopContent

    def load_ccpn_complex(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        # Make main object
        result = project.newComplex(**parameters)

        # Load loops, with object as parent
        for loopName in loopNames:
            loop = saveFrame.get(loopName)
            if loop:
                importer = self.importers[loopName]
                importer(self, result, loop)
        #
        return result

    #
    importers['ccpn_complex'] = load_ccpn_complex

    # def verify_ccpn_complex(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     pass

    verifiers['ccpn_complex'] = _verifyLoops

    # def content_ccpn_complex(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     self.storeContent(saveFrame, None)
    #     return None

    contents['ccpn_complex'] = _contentLoops

    def load_ccpn_complex_chain(self, parent: Complex, loop: StarIo.NmrLoop):
        """load ccpn_complex_chain loop"""

        chains = []
        for row in loop.data:
            chain = self.project.getChain(row.get('complex_chain_code'))
            if chain is None:
                self.warning(
                        "No Chain found with code %s. Skipping Chain from Complex"
                        % row.get('complex_chain_code')
                        )
            else:
                chains.append(chain)
        #
        parent.chains = chains

    #
    importers['ccpn_complex_chain'] = load_ccpn_complex_chain

    # def verify_ccpn_complex_chain(self, parent: Complex, loop: StarIo.NmrLoop):
    #     """verify ccpn_complex_chain loop"""
    #     pass

    verifiers['ccpn_complex_chain'] = _noLoopVerify

    # def content_ccpn_complex_chain(self, parent: Complex, loop: StarIo.NmrLoop):
    #     """Get the contents of ccpn_complex_chain loop"""
    #     self.storeContent(loop, None)
    #     return None

    contents['ccpn_complex_chain'] = _noLoopContent

    def load_ccpn_sample(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        # NBNB TODO add crosslinks to spectrum (also for components)

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        # Make main object
        result = project.newSample(**parameters)

        # Load loops, with object as parent
        for loopName in loopNames:
            loop = saveFrame.get(loopName)
            if loop:
                importer = self.importers[loopName]
                importer(self, result, loop)
        #
        return result

    #
    importers['ccpn_sample'] = load_ccpn_sample

    def verify_ccpn_sample(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        # Verify main object
        result = project.getSample(parameters['name'])
        if result is not None:
            self.error('ccpn_sample - Sample {} already exists'.format(result), saveFrame, (result,))

        self._verifyLoops(project, saveFrame, addLoopAttribs=['name'])

    verifiers['ccpn_sample'] = verify_ccpn_sample
    contents['ccpn_sample'] = partial(_contentLoops, addLoopAttribs=['name'])

    def load_ccpn_sample_component(self, parent: Sample, loop: StarIo.NmrLoop):
        """load ccpn_sample_component loop"""

        result = []

        creatorFunc = parent.newSampleComponent

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            result.append(creatorFunc(**parameters))
        #
        return result

    #
    importers['ccpn_sample_component'] = load_ccpn_sample_component

    def verify_ccpn_sample_component(self, parent: Sample, loop: StarIo.NmrLoop,
                                     sampleName: str = None):
        """verify ccpn_sample_component loop"""
        creatorFunc = parent.getSampleComponent

        if sampleName is None:
            self.error('Undefined sampleName', loop, None)
            return None

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)

            # NOTE:ED - need to check if 'labelling' removed from pid (which is should be)
            result = creatorFunc('.'.join([sampleName, parameters['name'], parameters['labelling']]))
            if result is not None:
                self.error('ccpn_sample_component - SampleComponent {} already exists'.format(result), loop, (result,))

    verifiers['ccpn_sample_component'] = verify_ccpn_sample_component

    def content_ccpn_sample_component(self, parent: Sample, loop: StarIo.NmrLoop, sampleName: str = None) -> Optional[OrderedSet]:
        """Get the contents for ccpn_sample_component loop"""
        result = OrderedSet()

        if sampleName is None:
            self.error('Undefined sampleName', loop, None)
            return None

        mapping = nef2CcpnMap[loop.name]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)

            # NOTE:ED - need to check if 'labelling' removed from pid (which is should be)
            result.add('.'.join([sampleName, parameters['name'], parameters['labelling']]))

        return result

    contents['ccpn_sample_component'] = content_ccpn_sample_component

    def load_ccpn_substance(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]
        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        name = parameters.pop('name')
        if 'labelling' in parameters:
            labelling = parameters.pop('labelling')
        else:
            labelling = None
        previous = [x for x in project.substances if x.name == name]
        sequence = saveFrame.get('sequence_string')
        if sequence and not previous:
            # We have a 'Molecule' type substance with a sequence and no previous occurrence
            # Create it as new polymer
            if ',' in sequence:
                sequence = list(sequence.split(','))
            params = {'molType': saveFrame.get('mol_type')}
            startNumber = saveFrame.get('start_number')
            if startNumber is not None:
                params['startNumber'] = startNumber
            isCyclic = saveFrame.get('is_cyclic')
            if isCyclic is not None:
                params['isCyclic'] = isCyclic
            #
            result = project.createPolymerSubstance(sequence, name, labelling, **params)

        else:
            # find or create substance
            # NB substance could legitimately be existing already, since substances are created
            # when a chain is created.
            result = project.fetchSubstance(name, labelling)
            if previous:
                # In case this is a new Substance, (known name, different labelling)
                # set the sequenceString, if any, to the same as previous
                sequenceString = previous[0].sequenceString
                if sequenceString is not None:
                    result._wrappedData.seqString = sequenceString

        # Whether substance was pre-existing or not
        # overwrite the missing substance-specific parameters
        for tag, val in parameters.items():
            setattr(result, tag, val)

        # Load loops, with object as parent
        for loopName in loopNames:
            loop = saveFrame.get(loopName)
            if loop:
                importer = self.importers[loopName]
                importer(self, result, loop)

    #
    importers['ccpn_substance'] = load_ccpn_substance

    def verify_ccpn_substance(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]
        parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

        name = parameters.pop('name')
        if 'labelling' in parameters:
            labelling = parameters.pop('labelling')
        else:
            labelling = None
        previous = [x for x in project.substances if x.name == name]
        sequence = saveFrame.get('sequence_string')
        if sequence and not previous:
            pass

        else:
            # find existing substance
            result = project.getSubstance(name)
            if result is not None:
                self.error('ccpn_substance - Substance {} already exists'.format(result), saveFrame, (result,))

            # shouldn't need to verify loopNames

    verifiers['ccpn_substance'] = verify_ccpn_substance

    # def content_ccpn_substance(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     self.storeContent(saveFrame, None)
    #     return None

    contents['ccpn_substance'] = _contentLoops

    def load_ccpn_substance_synonym(self, parent: Substance, loop: StarIo.NmrLoop):
        """load ccpn_substance_synonym loop"""

        result = [row['synonym'] for row in loop.data]
        parent.synonyms = result
        #
        return result

    #
    importers['ccpn_substance_synonym'] = load_ccpn_substance_synonym

    # def verify_ccpn_substance_synonym(self, parent: Substance, loop: StarIo.NmrLoop):
    #     """verify ccpn_substance_synonym loop"""
    #     pass

    verifiers['ccpn_substance_synonym'] = _noLoopVerify

    # def content_ccpn_substance_synonym(self, parent: Substance, loop: StarIo.NmrLoop):
    #     """Get the contents of ccpn_substance_synonym loop"""
    #     print('??????>> contents synonym')
    #     return None

    contents['ccpn_substance_synonym'] = _noLoopContent

    def load_ccpn_assignment(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        # the saveframe contains nothing but three loops:
        nmrChainLoopName = 'nmr_chain'
        nmrResidueLoopName = 'nmr_residue'
        nmrAtomLoopName = 'nmr_atom'

        nmrChains = {}
        nmrResidues = {}

        # ejb - stop notifiers from generating spurious items in the sidebar
        project.blankNotification()

        # read nmr_chain loop
        mapping = nef2CcpnMap[nmrChainLoopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        creatorFunc = project.newNmrChain
        for row in saveFrame[nmrChainLoopName].data:
            parameters = self._parametersFromLoopRow(row, map2)
            if parameters['shortName'] == coreConstants.defaultNmrChainCode:
                nmrChain = project.getNmrChain(coreConstants.defaultNmrChainCode)
            else:
                nmrChain = creatorFunc(**parameters)
            nmrChain.resetSerial(row['serial'])
            nmrChains[parameters['shortName']] = nmrChain

        # resume notifiers again
        project.unblankNotification()

        # read nmr_residue loop
        mapping = nef2CcpnMap[nmrResidueLoopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])

        # reorder the residues so that i-1 residues are after the corresponding i residue
        nmrResidueLoopData = []
        for row in saveFrame[nmrResidueLoopName].data:

            # can't test with an empty list
            if nmrResidueLoopData:

                # check adjacent items have same chain_code and matching sequence_code
                # split should give [', '-...', ] if correct i-1 residue
                residueTest = nmrResidueLoopData[-1]['sequence_code'].split(row['sequence_code'])
                if row['chain_code'] == nmrResidueLoopData[-1]['chain_code'] \
                        and len(residueTest) > 1 \
                        and residueTest[0] == '' \
                        and residueTest[1].startswith('-'):
                    # if row['chain_code'] == nmrResidueLoopData[-1]['chain_code'] \
                    #     and row['sequence_code'] in nmrResidueLoopData[-1]['sequence_code']:

                    nmrResidueLoopData.insert(-1, row)  # insert 1 from the end

                else:
                    nmrResidueLoopData.append(row)  # else append

            else:  # add the first element
                nmrResidueLoopData.append(row)

        # for row in saveFrame[nmrResidueLoopName].data:
        for row in nmrResidueLoopData:
            parameters = self._parametersFromLoopRow(row, map2)
            parameters['residueType'] = row.get('residue_name')
            # NB chainCode None is not possible here (for ccpn data)
            chainCode = row['chain_code']
            # nmrChain = nmrChains[chainCode]
            nmrChain = project.fetchNmrChain(chainCode)
            nmrResidue = nmrChain.newNmrResidue(**parameters)
            nmrResidue.resetSerial(row['serial'])
            # NB former call was BROKEN!
            # modelUtil.resetSerial(nmrResidue, row['serial'], 'nmrResidues')
            nmrResidues[(chainCode, parameters['sequenceCode'])] = nmrResidue

        # read nmr_atom loop
        mapping = nef2CcpnMap[nmrAtomLoopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in saveFrame[nmrAtomLoopName].data:
            parameters = self._parametersFromLoopRow(row, map2)
            chainCode = row['chain_code']
            sequenceCode = row['sequence_code']
            nmrResidue = nmrResidues[(chainCode, sequenceCode)]
            nmrAtom = nmrResidue.newNmrAtom(**parameters)
            nmrAtom.resetSerial(row['serial'])
            # NB former call was BROKEN!
            # modelUtil.resetSerial(nmrAtom, row['serial'], 'nmrAtoms')

    #
    importers['ccpn_assignment'] = load_ccpn_assignment

    def verify_ccpn_assignment(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        # the saveframe contains nothing but three loops:
        nmrChainLoopName = 'nmr_chain'
        nmrResidueLoopName = 'nmr_residue'
        nmrAtomLoopName = 'nmr_atom'

        nmrChains = {}
        nmrResidues = {}

        # read nmr_chain loop
        mapping = nef2CcpnMap[nmrChainLoopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        creatorFunc = project.getNmrChain
        for row in saveFrame[nmrChainLoopName].data:
            parameters = self._parametersFromLoopRow(row, map2)
            if parameters['shortName'] == coreConstants.defaultNmrChainCode:
                result = project.getNmrChain(coreConstants.defaultNmrChainCode)
            else:
                name = parameters['shortName']
                result = creatorFunc(name)
                # shortName.translate(Pid.remapSeparators))
            if result:
                # warning as already exists
                self.error('ccpn_assignment - Chain {} already exists'.format(result), saveFrame, (result,))

    verifiers['ccpn_assignment'] = verify_ccpn_assignment
    verifiers['nmr_chain'] = _noLoopVerify
    verifiers['nmr_residue'] = _noLoopVerify
    verifiers['nmr_atom'] = _noLoopVerify

    def content_ccpn_assignment(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        # the saveframe contains nothing but three loops:
        nmrChainLoopName = 'nmr_chain'
        nmrResidueLoopName = 'nmr_residue'
        nmrAtomLoopName = 'nmr_atom'

        nmrChains = OrderedSet()
        nmrResidues = OrderedSet()
        nmrAtoms = OrderedSet()

        # read nmr_chain loop - add the details to nmrChain list
        mapping = nef2CcpnMap[nmrChainLoopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in saveFrame[nmrChainLoopName].data:
            parameters = self._parametersFromLoopRow(row, map2)
            chainCode = row['short_name']
            nmrChains.add(chainCode)

        # read nmr_residue loop - add the details to nmrChain/nmrResidue/nmrAtom lists
        tempResidueDict = {}
        mapping = nef2CcpnMap[nmrResidueLoopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in saveFrame[nmrResidueLoopName].data:
            parameters = self._parametersFromLoopRow(row, map2)
            chainCode = row['chain_code']
            sequenceCode = row['sequence_code']
            residueName = row['residue_name']
            nmrResidues.add((chainCode, sequenceCode, residueName))
            tempResidueDict[(chainCode, sequenceCode)] = residueName

        # read nmr_residue loop - add the details to nmrChain/nmrResidue/nmrAtom lists
        tempResidueDict = {}
        mapping = nef2CcpnMap[nmrAtomLoopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in saveFrame[nmrAtomLoopName].data:
            parameters = self._parametersFromLoopRow(row, map2)
            chainCode = row['chain_code']
            sequenceCode = row['sequence_code']
            name = row['name']
            nmrAtoms.add((chainCode, sequenceCode, tempResidueDict.get((chainCode, sequenceCode)), name))

        self.storeContent(saveFrame, {nmrChainLoopName  : nmrChains,
                                      nmrResidueLoopName: nmrResidues,
                                      nmrAtomLoopName   : nmrAtoms})

    contents['ccpn_assignment'] = content_ccpn_assignment
    contents['nmr_chain'] = _noLoopContent
    contents['nmr_residue'] = _noLoopContent
    contents['nmr_atom'] = _noLoopContent

    def load_ccpn_notes(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        # ccpn_notes contains nothing except for the ccpn_note loop
        loopName = 'ccpn_note'
        loop = saveFrame[loopName]
        creatorFunc = project.newNote

        result = []
        mapping = nef2CcpnMap[loopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            obj = creatorFunc(**parameters)
            result.append(obj)

            # load time stamps and serial = must bypass the API, as they are frozen
            apiNote = obj._wrappedData
            created = row.get('created')
            if created:
                apiNote.__dict__['created'] = datetime.strptime(created, Constants.isoTimeFormat)
            lastModified = row.get('last_modified')
            if lastModified:
                apiNote.__dict__['lastModified'] = datetime.strptime(lastModified,
                                                                     Constants.isoTimeFormat)
            serial = row.get('serial')
            if serial is not None:
                obj.resetSerial(serial)
        #
        return result

    #
    importers['ccpn_notes'] = load_ccpn_notes

    def verify_ccpn_notes(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        loopName = 'ccpn_note'
        loop = saveFrame[loopName]
        creatorFunc = project.getNote

        result = []
        mapping = nef2CcpnMap[loopName]
        map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
        for row in loop.data:
            parameters = self._parametersFromLoopRow(row, map2)
            name = parameters['name']
            result = creatorFunc(name)
            if result:
                self.error('ccpn_notes - Note {} already exists'.format(result), saveFrame, (result,))

    verifiers['ccpn_notes'] = verify_ccpn_notes

    verifiers['ccpn_note'] = _noLoopVerify

    # def content_ccpn_notes(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     self.storeContent(saveFrame, None)
    #     return None

    contents['ccpn_notes'] = _contentLoops

    contents['ccpn_note'] = _noLoopContent

    def load_ccpn_additional_data(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        # ccpn_additional_data contains nothing except for the ccpn_internal_data loop
        loopName = 'ccpn_internal_data'
        loop = saveFrame[loopName]
        for row in loop.data:
            pid, data = row.values()
            obj = project.getByPid(pid)
            if obj is None:
                getLogger().warning('Loading NEF additional data: unable to find object "%s"' % pid)
            else:
                obj._ccpnInternalData = jsonIo.loads(data)

    #
    importers['ccpn_additional_data'] = load_ccpn_additional_data

    def verify_ccpn_additional_data(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        loopName = 'ccpn_internal_data'
        loop = saveFrame[loopName]
        for row in loop.data:
            pid, data = row.values()
            obj = project.getByPid(pid)
            if obj is None:
                getLogger().warning('Loading NEF additional data: unable to find object "%s"' % pid)
            else:
                data = obj._ccpnInternalData
                if data:
                    self.error('ccpn_additional_data - Object {} contains internal data'.format(obj), saveFrame, (obj,))

    verifiers['ccpn_additional_data'] = verify_ccpn_additional_data

    verifiers['ccpn_internal_data'] = _noLoopVerify

    # def content_ccpn_additional_data(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     self.storeContent(saveFrame, None)
    #     return None

    contents['ccpn_additional_data'] = _contentLoops

    contents['ccpn_internal_data'] = _noLoopContent

    def load_ccpn_dataset(self, project: Project, saveFrame: StarIo.NmrSaveFrame):

        print("ccpn_dataset reading is not implemented yet")

        # Get ccpn-to-nef mapping for saveframe
        category = saveFrame['sf_category']
        framecode = saveFrame['sf_framecode']
        mapping = nef2CcpnMap[category]

    #
    importers['ccpn_dataset'] = load_ccpn_dataset

    # def verify_ccpn_dataset(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     # nothing required
    #     pass

    verifiers['ccpn_dataset'] = _verifyLoops

    verifiers['ccpn_calculation_step'] = _noLoopVerify
    verifiers['ccpn_calculation_data'] = _noLoopVerify

    # def content_ccpn_dataset(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
    #     self.storeContent(saveFrame, None)
    #     return None

    contents['ccpn_dataset'] = _contentLoops

    contents['ccpn_calculation_step'] = _noLoopContent
    contents['ccpn_calculation_data'] = _noLoopContent

    def _parametersFromSaveFrame(self, saveFrame: StarIo.NmrSaveFrame, mapping: OD,
                                 ccpnPrefix: str = None):
        """Extract {parameter:value} dictionary and list of loop names from saveFrame

    The mapping gives the map from NEF tags to ccpn tags.
    If the ccpn tag is of the form <ccpnPrefix.tag> it is ignored unless
    the first part of teh tag matches the passed-in ccpnPrefix
    (NB the ccpnPrefix may contain '.')."""

        # Get attributes that have a simple tag mapping, and make a separate loop list
        parameters = {}
        loopNames = []
        if ccpnPrefix is None:
            # Normal extraction from saveframe map
            for tag, ccpnTag in mapping.items():
                if ccpnTag == _isALoop:
                    loopNames.append(tag)
                elif ccpnTag and '.' not in ccpnTag:
                    val = saveFrame.get(tag)
                    if val is not None:
                        # necessary as tags like ccpn_serial should NOT be set if absent of None
                        parameters[ccpnTag] = val
        else:
            # extracting tags of the form `ccpnPrefix`.tag
            for tag, ccpnTag in mapping.items():
                if ccpnTag == _isALoop:
                    loopNames.append(tag)
                elif ccpnTag:
                    parts = ccpnTag.rsplit('.', 1)
                    if parts[0] == ccpnPrefix:
                        val = saveFrame.get(tag)
                        if val is not None:
                            # necessary as tags like ccpn_serial should NOT be set if absent of None
                            parameters[parts[1]] = val

        #
        return parameters, loopNames

    def error(self, message: str, source, objects: Optional[tuple] = None):
        """Update the error log with the message
        """
        # # MUST BE SUBCLASSED
        # raise NotImplementedError("Code error: function not implemented")
        template = "Error in saveFrame {}: {}"
        self.errors.append((template.format(self.saveFrameName, message), source, objects))

    def warning(self, message: str):
        template = "WARNING in saveFrame%s\n%s"
        self.warnings.append(template % (self.saveFrameName, message))

    def storeContent(self, source, objects: Optional[dict] = None):
        """Update the ccpnContent log with the contents of the saveFrames/loops
        """
        # # MUST BE SUBCLASSED
        # raise NotImplementedError("Code error: function not implemented")
        if source.name in self.ccpnContent:
            self.error('Source {} already exists in content'.format(source.name), source, None)
        else:
            self.ccpnContent[source.name] = (source, objects)

    def updateContent(self, source, objects: Optional[dict] = None):
        """Update the ccpnContent log with the contents of the saveFrames/loops
        """
        # # MUST BE SUBCLASSED
        # raise NotImplementedError("Code error: function not implemented")
        if source.name in self.ccpnContent:
            try:
                _, dd = self.ccpnContent[source.name]
                dd.update(objects)
            except:
                raise RuntimeError('Error updating dict')
        else:
            self.ccpnContent[source.name] = (source, objects)

    def _parametersFromLoopRow(self, row, mapping):
        parameters = {}
        for tag, ccpnTag in mapping.items():
            val = row.get(tag)
            if val is not None:
                parameters[ccpnTag] = val
        #
        return parameters

    def produceNmrChain(self, chainCode: str = None):
        """Get NmrChain, correcting for possible errors"""

        if chainCode is None:
            chainCode = self.defaultNmrChainCode
        newChainCode = chainCode
        while True:
            try:
                nmrChain = self.project.fetchNmrChain(newChainCode)
                return nmrChain
            except ValueError:
                newChainCode = '`%s`' % newChainCode
                self.warning("New NmrChain:%s name caused an error.  Renamed %s"
                             % (chainCode, newChainCode))

    def produceNmrResidue(self, chainCode: str = None, sequenceCode: str = None, residueType: str = None):
        """Get NmrResidue, correcting for possible errors"""

        chainCode = chainCode or self.defaultChainCode

        inputTuple = (chainCode, sequenceCode, residueType)
        result = self._nmrResidueMap.get(inputTuple)
        if result is not None:
            return result

        if not sequenceCode:
            raise ValueError("Cannot produce NmrResidue for sequenceCode: %s" % repr(sequenceCode))

        if isinstance(sequenceCode, int):
            sequenceCode = str(sequenceCode)

        nmrChain = self.produceNmrChain(chainCode)

        rt = residueType or ''
        cc = nmrChain.shortName

        try:
            result = nmrChain.fetchNmrResidue(sequenceCode, residueType)
            # return result
        except ValueError:
            # This can happen legitimately, e.g. for offset residues
            # Further processing needed.

            # Parse values from sequenceCode
            seqNo, insertCode, offset = commonUtil.parseSequenceCode(sequenceCode)

            if offset is None:
                if residueType:
                    # This could be a case where the NmrResidue had been created from an offset NmrResidue
                    # with the residueType therefore missing.
                    # If so, set the residueType
                    # NBNB this also has the effect of having real entries with empty residueType
                    # overridden by clashing entries with residueType set,
                    # but that does make some sense and anyway cannot be helped.

                    # NB this must be a pre-existing residue or it would have been created above.
                    try:
                        previous = nmrChain.fetchNmrResidue(sequenceCode)
                        if not previous.residueType:
                            result = previous
                            result._wrappedData.residueType = residueType
                            # return result
                    except ValueError:
                        # Deal with it below
                        pass

            else:
                # Offset NmrResidue - get mainNmrResidue
                ss = '%+d' % offset
                try:
                    # Fetch the mainNmrResidue. This will create it if it is missing (if possible)
                    mainNmrResidue = nmrChain.fetchNmrResidue(sequenceCode[:-len(ss)])
                except ValueError:
                    # No go
                    mainNmrResidue = None

                if mainNmrResidue is not None:
                    try:
                        result = nmrChain.fetchNmrResidue(sequenceCode, residueType)
                        # return result
                    except ValueError:
                        # Handle lower down
                        pass

        # If e get here, we could not make an NmrResidue that matched the input
        # Make with modified sequenceCode
        if result is None:
            newSequenceCode = sequenceCode
            while True:
                try:
                    result = nmrChain.fetchNmrResidue(newSequenceCode, residueType)
                    return result
                except ValueError:
                    newSequenceCode = '`%s`' % newSequenceCode
                    self.warning("New NmrResidue:%s.%s.%s name caused an error.  Renamed %s.%s.%s"
                                 % (cc, sequenceCode, rt, cc, newSequenceCode, rt))
        #
        # Result cannot have been in map, so put it there
        self._nmrResidueMap[inputTuple] = result
        return result

    def produceNmrAtom(self, nmrResidue: NmrResidue, name: str, isotopeCode=None):
        """Get NmrAtom from NmrResidue and name, correcting for possible errors"""

        if not name:
            raise ValueError("Cannot produce NmrAtom for atom name: %s" % repr(name))

        if isotopeCode:
            prefix = isotopeCode.upper()
            if not name.startswith(prefix):
                prefix = commonUtil.isotopeCode2Nucleus(isotopeCode)
                if prefix is None:
                    self.warning("Ignoring unsupported isotopeCode: %s for NmrAtom:%s.%s"
                                 % (isotopeCode, nmrResidue._id, name))
                elif not name.startswith(prefix):
                    newName = '%s@%s' % (prefix, name)
                    self.warning("NmrAtom name %s does not match isotopeCode %s - renamed to %s"
                                 % (isotopeCode, name, newName))
                    name = newName

        newName = name
        while True:
            nmrAtom = nmrResidue.getNmrAtom(newName.translate(Pid.remapSeparators))
            if nmrAtom is None:
                try:
                    nmrAtom = nmrResidue.newNmrAtom(newName, isotopeCode)
                    return nmrAtom
                except ValueError:
                    pass
            elif isotopeCode in (None, nmrAtom.isotopeCode):
                # We must ensure that the isotopeCodes match
                return nmrAtom
            else:
                # IsotopeCode mismatch. Try to
                if prefix == isotopeCode.upper():
                    # Something wrong here.
                    raise ValueError("Clash between NmrAtom %s (%s) and %s (%s) in %s"
                                     % (nmrAtom.name, nmrAtom.isotopeCode, newName, isotopeCode, nmrResidue))
                else:
                    newName = isotopeCode.upper() + newName[len(prefix):]
                    continue

            # If we get here there was an error. Change name and try again
            tt = newName.rsplit('_', 1)
            if len(tt) == 2 and tt[1].isdigit():
                newName = '%s_%s' % (tt[0], int(tt[1]) + 1)
            else:
                newName += '_1'
            self.warning("New NmrAtom:%s.%s name caused an error.  Renamed %s.%s"
                         % (nmrResidue._id, name, nmrResidue._id, newName))

    def updateMetaData(self, metaDataFrame: StarIo.NmrSaveFrame):
        """Add meta information to main data set. Must be done at end of read"""

        # NBNB NOT WORKING YET!

        # dataSet = self.fetchDataSet(self.mainDataSetSerial)
        self.mainDataSetSerial = None

    def fetchDataSet(self, serial: int = None):
        """Fetch DataSet with given serial.
    If input is None, use self.defaultDataSetSerial
    If that too is None, create a new DataSet and use its serial as the default

    NB when reading, all DataSets with known serials should be instantiated BEFORE calling
    with input None"""

        if serial is None:
            serial = self.defaultDataSetSerial

        if serial is None:
            # default not set - create one
            dataSet = self.project.newDataSet()
            serial = dataSet.serial
            dataSet.title = 'dataset_%s' % serial
            self.defaultDataSetSerial = serial
            self._dataSet2ItemMap[dataSet] = dataSet._getTempItemMap()

        else:
            # take or create dataSet matching serial
            # dataSet = self.project.getDataSet(str(serial))
            dataSet = self.project.getDataSet('dataset_%s' % serial)
            if dataSet is None:
                dataSet = self.project.newDataSet(serial=serial)
                # dataSet.resetSerial(serial)
                # NB former call was BROKEN!
                # modelUtil.resetSerial(dataSet._wrappedData, serial, 'nmrConstraintStores')

                # dataSet._finaliseAction('rename')
                dataSet.title = 'dataset_%s' % serial

                self._dataSet2ItemMap[dataSet] = dataSet._getTempItemMap()
        #
        return dataSet

    def getDataSet(self, serial: int = None):
        """Get the required DataSet with given serial.
        If input is None, use self.defaultDataSetSerial
        If that too is None, create a new DataSet and use its serial as the default

        NB when reading, all DataSets with known serials should be instantiated BEFORE calling
        with input None"""

        if serial is None:
            serial = self.defaultDataSetSerial or 1
        return self.project.getDataSet('dataset_{}'.format(serial))


def createSpectrum(project: Project, spectrumName: str, spectrumParameters: dict,
                   dimensionData: dict, transferData: Sequence[Tuple] = None):
    """Get or create spectrum using dictionaries of attributes, such as read in from NEF.

    :param spectrumParameters keyword-value dictionary of attribute to set on resulting spectrum

    :params Dictionary of keyword:list parameters, with per-dimension parameters.
    Either 'axisCodes' or 'isotopeCodes' must be present and fully populated.
    A number of other dimensionData are
    treated specially (see below)
    """

    spectrum = project.getSpectrum(spectrumName)
    if spectrum is None:
        # Spectrum did not already exist

        dimTags = list(dimensionData.keys())

        # First try to load it - we override the loaded attribute values below
        # but loading gives a more complete parameter set.
        spectrum = None
        filePath = spectrumParameters.get('filePath')
        if filePath and os.path.exists(filePath):
            try:
                dataType, subType, usePath = ioFormats.analyseUrl(path)
                if dataType == 'Spectrum':
                    # spectra = project.loadSpectrum(usePath, subType)

                    spectra = project.loadSpectrum(usePath, subType)
                    if spectra:
                        spectrum = spectra[0]
            except:
                # Deliberate - any error should be skipped
                pass
            if spectrum is None:
                project._logger.warning("Failed to load spectrum from spectrum path %s" % filePath)
            elif 'axisCodes' in dimensionData:
                # set axisCodes
                spectrum.axisCodes = dimensionData['axisCodes']

        acquisitionAxisIndex = None
        if 'is_acquisition' in dimensionData:
            dimTags.remove('is_acquisition')
            values = dimensionData['is_acquisition']
            if values.count(True) == 1:
                acquisitionAxisIndex = values.index(True)

        if spectrum is None:
            # Spectrum could not be loaded - now create a dummy spectrum

            if 'axisCodes' in dimTags:
                # We have the axisCodes, from ccpn
                dimTags.remove('axisCodes')
                axisCodes = dimensionData['axisCodes']

            else:
                if transferData is None:
                    raise ValueError("Function needs either axisCodes or transferData")

                dimensionIds = dimensionData['dimension_id']

                # axisCodes were not set - produce a serviceable set
                axisCodes = makeNefAxisCodes(isotopeCodes=dimensionData['isotopeCodes'],
                                             dimensionIds=dimensionIds,
                                             acquisitionAxisIndex=acquisitionAxisIndex,
                                             transferData=transferData)

            # make new spectrum with default parameters
            spectrum = project.createDummySpectrum(axisCodes, spectrumName,
                                                   chemicalShiftList=spectrumParameters.get('chemicalShiftList')
                                                   )
            if acquisitionAxisIndex is not None:
                spectrum.acquisitionAxisCode = axisCodes[acquisitionAxisIndex]

            # Delete autocreated peaklist  and reset - we want any read-in peakList to be the first
            # If necessary an empty PeakList is added downstream
            spectrum.peakLists[0].delete()
            spectrum._wrappedData.__dict__['_serialDict']['peakLists'] = 0

        # (Re)set all spectrum attributes

        # First per-dimension ones
        dimTags.remove('dimension_id')
        if 'absolute_peak_positions' in dimensionData:
            # NB We are not using these. What could we do with them?
            dimTags.remove('absolute_peak_positions')
        if 'folding' in dimensionData:
            dimTags.remove('folding')
            values = [None if x == 'none' else x for x in dimensionData['folding']]
            spectrum.foldingModes = values
        if 'pointCounts' in dimensionData:
            dimTags.remove('pointCounts')
            spectrum.pointCounts = pointCounts = dimensionData['pointCounts']
            if 'totalPointCounts' in dimensionData:
                dimTags.remove('totalPointCounts')
                spectrum.totalPointCounts = dimensionData['totalPointCounts']
            else:
                spectrum.totalPointCounts = pointCounts
        # Needed below:
        if 'value_first_point' in dimensionData:
            dimTags.remove('value_first_point')
        if 'referencePoints' in dimensionData:
            dimTags.remove('referencePoints')
        # value_first_point = dimensionData.get('value_first_point')
        # if value_first_point is not None:
        #   dimensionData.pop('value_first_point')
        # referencePoints = dimensionData.get('referencePoints')
        # if referencePoints is not None:
        #   dimensionData.pop('referencePoints')

        # Remaining per-dimension values match the spectrum. Set them.
        # NB we use the old (default) values where the new value is None
        # - some attributes like spectralWidths do not accept None.
        if 'spectrometerFrequencies' in dimTags:
            # spectrometerFrequencies MUST be set before spectralWidths,
            # as the spectralWidths are otherwise modified
            dimTags.remove('spectrometerFrequencies')
            dimTags.insert(0, 'spectrometerFrequencies')
        for tag in dimTags:
            vals = dimensionData[tag]
            # Use old values where new ones are None
            oldVals = getattr(spectrum, tag)
            vals = [x if x is not None else oldVals[ii] for ii, x in enumerate(vals)]
            setattr(spectrum, tag, vals)

        # Set referencing.
        value_first_point = dimensionData.get('value_first_point')
        referencePoints = dimensionData.get('referencePoints')
        if value_first_point is None:
            # If reading NEF we must get value_first_point,
            #  but in other uses we might be getting referencePoints, referenceValues directly
            referenceValues = dimensionData.get('referenceValues')
            if referenceValues and referencePoints:
                spectrum.referencePoints = referencePoints
                spectrum.referenceValues = referenceValues
        else:
            if referencePoints is None:
                # not CCPN data
                referenceValues = spectrum.referenceValues
                for ii, val in enumerate(value_first_point):
                    if val is None:
                        value_first_point[ii] = referenceValues[ii]
                spectrum.referenceValues = value_first_point
                spectrum.referencePoints = [1] * len(referenceValues)
            else:
                points = list(spectrum.referencePoints)
                values = list(spectrum.referenceValues)
                sw = spectrum.spectralWidths
                pointCounts = spectrum.pointCounts
                for ii, refVal in enumerate(value_first_point):
                    refPoint = referencePoints[ii]
                    if refVal is not None and refPoint is not None:
                        # if we are here refPoint should never be None, but OK, ...
                        # Set reference to use refPoint
                        points[ii] = refPoint
                        refVal -= ((refPoint - 1) * sw[ii] / pointCounts[ii])
                        values[ii] = refVal
                spectrum.referencePoints = points
                spectrum.referenceValues = values

        # Then spectrum-level ones
        for tag, val in spectrumParameters.items():
            if tag != 'dimensionCount':
                # dimensionCount is handled already and not settable
                setattr(spectrum, tag, val)
        #
        return spectrum

    else:
        raise ValueError("Spectrum named %s already exists" % spectrumName)


def makeNefAxisCodes(isotopeCodes: Sequence[str], dimensionIds: List[int],
                     acquisitionAxisIndex: int, transferData: Sequence[Tuple]):
    nuclei = [commonUtil.splitIntFromChars(x)[1] for x in isotopeCodes]
    dimensionToNucleus = dict((zip(dimensionIds, nuclei)))
    dimensionToAxisCode = dimensionToNucleus.copy()

    oneBondConnections = {}
    for startNuc in 'FH':
        # look for onebond to F or H, the latter taking priority
        for dim1, dim2, transferType, isIndirect in transferData:
            if transferType == 'onebond':
                nuc1, nuc2 = dimensionToNucleus[dim1], dimensionToNucleus[dim2]
                if startNuc in (nuc1, nuc2):
                    if startNuc == nuc1:
                        oneBondConnections[dim1] = dim2
                    else:
                        oneBondConnections[dim2] = dim1
                    dimensionToAxisCode[dim1] = nuc1 + nuc2.lower()
                    dimensionToAxisCode[dim2] = nuc2 + nuc1.lower()

    resultMap = {}
    acquisitionAtEnd = False
    if acquisitionAxisIndex is not None:
        acquisitionAtEnd = acquisitionAxisIndex >= 0.5 * len(isotopeCodes)
        # if acquisitionAtEnd:
        #   # reverse, because acquisition end of dimensions should
        #   # be the one WITHOUT number suffixes
        #   dimensionIds.reverse()

        # Put acquisition axis first, to make sure it gets the lowest number
        # even if it is not teh first to start with.
        acquisitionAxisId = dimensionIds[acquisitionAxisIndex]
        dimensionIds.remove(acquisitionAxisId)
        dimensionIds.insert(0, acquisitionAxisId)
    for dim in dimensionIds:
        axisCode = dimensionToAxisCode[dim]
        if axisCode in resultMap.values():
            ii = 0
            ss = axisCode
            while ss in resultMap.values():
                ii += 1
                ss = '%s%s' % (axisCode, ii)
            otherDim = oneBondConnections.get(dim)
            if otherDim is not None:
                # We are adding a suffix to e.g. Hc. Add the same suffix to equivalent Ch
                # NB this should only happen for certain 4D experiments.
                # NB not well tested, but better than leaving in a known error.
                ss = '%s%s' % (dimensionToAxisCode[otherDim], ii)
                if otherDim < dim:
                    resultMap[otherDim] = ss
                dimensionToAxisCode[otherDim] = ss

        resultMap[dim] = axisCode
    dimensionIds.sort()
    # NBNB new attempt - may not work
    # if acquisitionAtEnd:
    #   # put result back in dimension order
    #   dimensionIds.reverse()
    result = list(resultMap[ii] for ii in dimensionIds)
    #
    return result


def _printOutMappingDict(mappingDict: dict):
    """Utility - print out mapping dict for editing and copying"""
    saveframeOrder = []
    print("# NEf to CCPN tag mapping (and tag order)")
    print("{\n")
    for category, od in mappingDict.items():
        saveframeOrder.append(category)
        print("  %s:OD((" % repr(category))
        for tag, val in od.items():
            if isinstance(val, str) or val is None:
                print("    (%s,%s)," % (repr(tag), repr(val)))
            else:
                # This must be a loop OD
                print("    (%s,OD((" % repr(tag))
                for tag2, val2 in val.items():
                    print("      (%s,%s)," % (repr(tag2), repr(val2)))
                print("    ))),")
        print("  )),\n")
    print("}\n")

    print("#SaveFrameOrder\n[")
    for tag in saveframeOrder:
        print("  %s," % repr(tag))
    print("]\n")


def _exportToNef(path: str, skipPrefixes: Sequence[str] = ()):
    if path.endswith('.ccpn'):
        outPath = path[:-4] + 'nef'
    elif path.endswith('.ccpn/'):
        outPath = path[:-5] + 'nef'
    elif path.endswith('/'):
        outPath = path[:-1] + '.nef'
    else:
        outPath = path + '.nef'

    from ccpn.framework.Framework import createFramework

    path = os.path.normpath(os.path.abspath(path))
    time1 = time.time()
    application = createFramework()
    application.loadProject(path)
    project = application.project
    time2 = time.time()
    print("====> Loaded %s from file in seconds %s" % (project.name, time2 - time1))
    saveNefProject(project, outPath, overwriteExisting=True, skipPrefixes=skipPrefixes)
    time3 = time.time()
    print("====> Saved  %s  to  NEF file in seconds %s" % (project.name, time3 - time2))

    # Needed to clean up notifiers - not any more
    # project.delete()
    #
    return outPath


# from ccpn.util.nef.GenericStarParser import DataBlock
# from collections import OrderedDict
#
#
# def _convertToDataBlock(self: Project, skipPrefixes: typing.Sequence = (),
#                         expandSelection: bool = True,
#                         pidList: list = None):
#     """
#   Export selected contents of the project to a Nef file.
#
#     skipPrefixes: ( 'ccpn', ..., <str> )
#     expandSelection: <bool> }
#
#     Include 'ccpn' in the skipPrefixes list will exclude ccpn specific items from the file
#     expandSelection = True  will include all data from the project, this may not be data that
#                             is not defined in the Nef standard.
#
#   PidList is a list of <str>, e.g. 'NC:@-', obtained from the objects to be included.
#   The Nef file may also contain further dependent items associated with the pidList.
#
#   :param skipPrefixes: items to skip
#   :param expandSelection: expand the selection
#   :param pidList: a list of pids
#   """
#     from ccpn.core.lib.ContextManagers import undoBlockManager
#
#     with undoBlockManager():
#         dataBlock = convertToDataBlock(self, skipPrefixes=skipPrefixes,
#                                        expandSelection=expandSelection,
#                                        pidList=pidList)
#
#     return dataBlock
#
#
# def _writeDataBlockToFile(self: Project, dataBlock: DataBlock = None, path: str = None,
#                           overwriteExisting: bool = False):
#     # Export the modified dataBlock to file
#     from ccpn.core.lib.ContextManagers import undoBlockManager
#
#     with undoBlockManager():
#         writeDataBlock(dataBlock, path=path, overwriteExisting=overwriteExisting)


def _testNefIo(path: str, skipPrefixes: Sequence[str] = ()):
    from ccpn.framework.Framework import createFramework

    path = os.path.normpath(os.path.abspath(path))

    if path.endswith('.nef'):
        outPath = path[:-4] + '.out.nef'
    else:
        raise ValueError("File name does not end in '.nef': %s" % path)

    time1 = time.time()
    application = createFramework()
    application.nefReader.testing = True
    application.loadProject(path)

    project = application.project
    # spectrum = project.spectra[0]
    time2 = time.time()
    print("====> Loaded %s from NEF file in seconds %s" % (project.name, time2 - time1))
    saveNefProject(project, outPath, overwriteExisting=True, skipPrefixes=skipPrefixes)
    time3 = time.time()
    print("====> Saved  %s  to  NEF file in seconds %s" % (project.name, time3 - time2))
    # Needed to clean up notifiers
    project.delete()

    return outPath


# def _extractVariantsTable(aa_variants_cif:str)-> str:
#   """Read aa-variants.cif file contents and return variants mapping table string"""
#
#   lineformat = "%-15s    %-12s    %-7s    %-15s"
#   lines =[lineformat % ('MMCIF_code', "residue_name", "linking", "residue_variant")]
#
#   #
#   # 'LL'
#   # linkingMap = {
#   #   'LL':'middle',
#   #   'LEO2':'end', # deprotonated
#   #   'LEO2H':'end', # deprotonated
#   #   'LFOH':'single', # neutral
#   #   'LFZW':'single', # zwitter
#   #   'LSN3':'start', # protonated
#   #
#   # }
#
#   names = []
#
#   for line in open(aa_variants_cif):
#
#     hxt = False
#
#     if 'data_' in line:
#       ll = line.strip().split('_')
#       if len(ll) == 2:
#         pass
#       else:
#         name = ll[1]
#         names.append(name)
#         ll2 = []
#         lnk = ll[2]
#         linking = '.'
#         if lnk == 'LL':
#           linking = 'middle'
#         elif lnk == 'LEO2':
#           linking = 'end'
#         elif lnk == 'LEO2H':
#           linking = 'end'
#           hxt = True
#         elif lnk == 'LFZW':
#           linking = 'single'
#         elif lnk == 'LFOH':
#           linking = 'single'
#           ll2.append('-H3')
#           hxt = True
#         elif lnk == 'LSN3':
#           linking = 'start'
#         else:
#           print('WARNING, not recognised', ll)
#
#         if len(ll) > 3:
#           var = ll[3]
#           if var[0] == 'D':
#             ll2.append('-'+var[1:])
#           else:
#             print ("NB Ignoring MMcif variant %s" % var)
#
#         # Sort before further treatment, to make sure '+' markers come at the end
#         ll2.sort()
#
#         # Special handling for ASP and GLU - where default is side chain deprotonated
#         if name == 'ASP':
#           if '-HD2' in ll2:
#             ll2.remove('-HD2')
#           else:
#             ll2.append('+HD2')
#         elif name == 'GLU':
#           if '-HE2' in ll2:
#             ll2.remove('-HE2')
#           else:
#             ll2.append('+HE2')
#         elif name == 'HIS':
#           if '-HE2' in ll2:
#             ll2.remove('-HE2')
#           else:
#             ll2.append('+HE2')
#
#         # NBNB
#
#         if hxt:
#           ll2.append('+HXT')
#         if ll2:
#           variant = ','.join(ll2)
#         else:
#           variant = '.'
#         ss = lineformat % ('_'.join(ll[1:]), name, linking, variant)
#
#         lines.append(ss)
#
#   #
#   print (Counter(names))
#
#   #
#   return '\n'.join(lines)


if __name__ == '__main__':
    # Explanation:
    # _exportToNef will read a project from path and export the corresponding NEF file
    # skipPrefixes=('ccpn', ) means 'remove all ccpn-specific tags from the output';
    # default is to leave them in. Note that path may also be a NEF file,
    # which will then be imported and re-exported
    #
    # testNefIo will read a NEF file and re-export it (with a .out.nef suffix),
    # producing a V3 project on disk as a byproduct if the original is a V2 project.

    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("CcpnNefIo exports a project as a NEF file. Usage:"
              "\n\n One mandatory argument - the project directory to export")
    else:
        path = sys.argv[1]
        nefpath = _exportToNef(path)

    # _testNefIo(path, skipPrefixes=('ccpn', ))
    # _testNefIo(path)
    # _testNefIo(nefpath)
    # nefpath = _exportToNef(path, skipPrefixes=('ccpn', ))
    # _testNefIo(nefpath, skipPrefixes=('ccpn', ))
    # print(_extractVariantsTable(path))
