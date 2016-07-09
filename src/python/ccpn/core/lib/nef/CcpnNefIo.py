"""Code for CCPN-specific NEF I/O

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from pandas.io.gbq import _Dataset

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import random
from collections import OrderedDict as OD
from functools import partial
from operator import attrgetter
from typing import List, Union, Optional, Sequence

from ccpn.core._implementation import Io as coreIo
from ccpn.core.lib import Pid
from ccpn.core.lib.MoleculeLib import extraBoundAtomPairs
from ccpn.util import Common as commonUtil
from . import Specification
from . import StarIo

# Max value used for random integer. Set to be expressible as a signed 32-bit integer.
maxRandomInt =  2000000000



#  - saveframe category names in writing order
saveFrameOrder = [
  'nef_nmr_meta_data',
  'nef_molecular_system',
  'nef_chemical_shift_list',
  'nef_distance_restraint_list',
  'nef_dihedral_restraint_list',
  'nef_rdc_restraint_list',
  'nef_nmr_spectrum',
  'nef_peak_restraint_links',
  'ccpn_spectrum_group',
  'ccpn_sample',
  'ccpn_substance',
  'ccpn_assignments',
  'ccpn_dataset',
  'ccpn_restraint_list',
  'ccpn_notes',
]


# NEf to CCPN tag mapping (and tag order)
#
# Contents are:
# Nef2CcpnMap = {saveframe_or_loop_category:contents}
# contents = {tag:ccpn_tag_or_None}
# loopMap = {tag:ccpn_tag}
#
# Loops are entered as saveFrame contents with their category as tag and 'ccpn_tag' None
# and at the top level under their category name
# This relies on loop categories being unique, both at teh top level, and among the item
# names within a saveframe

# Sentinel value - MUST evaluate as False
_isALoop = ()
nef2CcpnMap = {
  'nef_nmr_meta_data':OD((
    ('format_name',None),
    ('format_version',None),
    ('program_name',None),
    ('program_version',None),
    ('creation_date',None),
    ('uuid',None),
    ('coordinate_file_name',None),
    ('ccpn_dataset_name','name'),
    ('ccpn_dataset_comment',None),
    ('nef_related_entries',_isALoop),
    ('nef_program_script',_isALoop),
    ('nef_run_history',_isALoop),
  )),
  'nef_related_entries':OD((
    ('database_name',None),
    ('database_accession_code',None),
  )),
  'nef_program_script':OD((
    ('program_name',None),
    ('script_name',None),
    ('script',None),
  )),
  'nef_run_history':OD((
    ('run_ordinal','serial'),
    ('program_name','programName'),
    ('program_version','programVersion'),
    ('script_name','scriptName'),
    ('script','script'),
    ('ccpn_input_uuid','inputDataUuid'),
    ('ccpn_output_uuid','outputDataUuid'),
  )),

  'nef_molecular_system':OD((
    ('nef_sequence',_isALoop),
    ('nef_covalent_links',_isALoop),
  )),
  'nef_sequence':OD((
    ('chain_code','chain.shortName'),
    ('sequence_code','sequenceCode'),
    ('residue_type','residueType'),
    ('linking','linking'),
    ('residue_variant','residueVariant'),
    ('ccpn_comment','comment'),
    ('ccpn_chain_role','chain.role'),
    ('ccpn_compound_name','chain.compoundName'),
    ('ccpn_chain_comment','chain.comment'),
  )),
  'nef_covalent_links':OD((
    ('chain_code_1',None),
    ('sequence_code_1',None),
    ('residue_type_1',None),
    ('atom_name_1',None),
    ('chain_code_2',None),
    ('sequence_code_2',None),
    ('residue_type_2',None),
    ('atom_name_2',None),
  )),

  'nef_chemical_shift_list':OD((
    ('name', None),
    ('atom_chemical_shift_units','unit'),
    ('ccpn_serial','serial'),
    ('ccpn_autoUpdate','autoUpdate'),
    ('ccpn_isSimulated','isSimulated'),
    ('ccpn_comment','comment'),
    ('nef_chemical_shift',_isALoop),
  )),
  'nef_chemical_shift':OD((
    ('chain_code',None),
    ('sequence_code',None),
    ('residue_type',None),
    ('atom_name',None),
    ('value','value'),
    ('value_uncertainty','valueError'),
    ('ccpn_figure_of_merit','figureOfMerit'),
    ('ccpn_comment','comment'),
  )),

  'nef_distance_restraint_list':OD((
    ('potential_type','potentialType'),
    ('origin','origin'),
    ('ccpn_serial','serial'),
    ('ccpn_name','name'),
    ('ccpn_unit','unit'),
    ('ccpn_comment','comment'),
    ('nef_distance_restraint',_isALoop),
  )),
  'nef_distance_restraint':OD((
    ('ordinal',None),
    ('restraint_id','restraint.serial'),
    ('restraint_combination_id','combinationId'),
    ('chain_code_1',None),
    ('sequence_code_1',None),
    ('residue_type_1',None),
    ('atom_name_1',None),
    ('chain_code_2',None),
    ('sequence_code_2',None),
    ('residue_type_2',None),
    ('atom_name_2',None),
    ('weight','weight'),
    ('target_value','targetValue'),
    ('target_value_uncertainty','error'),
    ('lower_linear_limit','additionalLowerLimit'),
    ('lower_limit','lowerLimit'),
    ('upper_limit','upperLimit'),
    ('upper_linear_limit','additionalUpperLimit'),
    ('scale','scale'),
    ('distance_dependent','isDistanceDependent'),
    ('ccpn_figure_of_merit','restraint.figureOfMerit'),
  )),

  'nef_dihedral_restraint_list':OD((
    ('potential_type','potentialType'),
    ('origin','origin'),
    ('ccpn_serial','serial'),
    ('ccpn_name','name'),
    ('ccpn_unit','unit'),
    ('ccpn_comment','comment'),
    ('nef_dihedral_restraint',_isALoop),
  )),
  'nef_dihedral_restraint':OD((
    ('ordinal',None),
    ('restraint_id','restraint.serial'),
    ('restraint_combination_id','combinationId'),
    ('chain_code_1',None),
    ('sequence_code_1',None),
    ('residue_type_1',None),
    ('atom_name_1',None),
    ('chain_code_2',None),
    ('sequence_code_2',None),
    ('residue_type_2',None),
    ('atom_name_2',None),
    ('chain_code_3',None),
    ('sequence_code_3',None),
    ('residue_type_3',None),
    ('atom_name_3',None),
    ('chain_code_4',None),
    ('sequence_code_4',None),
    ('residue_type_4',None),
    ('atom_name_4',None),
    ('weight','weight'),
    ('target_value','targetValue'),
    ('target_value_uncertainty','error'),
    ('lower_linear_limit','additionalLowerLimit'),
    ('lower_limit','lowerLimit'),
    ('upper_limit','upperLimit'),
    ('upper_linear_limit','additionalUpperLimit'),
    ('scale','scale'),
    ('distance_dependent','isDistanceDependent'),
    ('name',None),
    ('ccpn_figure_of_merit','restraint.figureOfMerit'),
  )),

  'nef_rdc_restraint_list':OD((
    ('potential_type','potentialType'),
    ('origin','origin'),
    ('tensor_magnitude',None),
    ('tensor_rhombicity',None),
    ('tensor_chain_code','tensorChainCode'),
    ('tensor_sequence_code','tensorSequenceCode'),
    ('tensor_residue_type','tensorResidueType'),
    ('ccpn_serial','serial'),
    ('ccpn_name','name'),
    ('ccpn_unit','unit'),
    ('ccpn_comment','comment'),
    ('ccpn_tensor_isotropic_value',None),
    ('nef_rdc_restraint',_isALoop),
  )),
  'nef_rdc_restraint':OD((
    ('ordinal',None),
    ('restraint_id','restraint.serial'),
    ('restraint_combination_id','combinationId'),
    ('chain_code_1',None),
    ('sequence_code_1',None),
    ('residue_type_1',None),
    ('atom_name_1',None),
    ('chain_code_2',None),
    ('sequence_code_2',None),
    ('residue_type_2',None),
    ('atom_name_2',None),
    ('weight','weight'),
    ('target_value','targetValue'),
    ('target_value_uncertainty','error'),
    ('lower_linear_limit','additionalLowerLimit'),
    ('lower_limit','lowerLimit'),
    ('upper_limit','upperLimit'),
    ('upper_linear_limit','additionalUpperLimit'),
    ('scale','scale'),
    ('distance_dependent','isDistanceDependent'),
    ('ccpn_vector_length','restraint.vectorLength'),
    ('ccpn_figure_of_merit','restraint.figureOfMerit'),
  )),

  'nef_nmr_spectrum':OD((
    ('num_dimensions','spectrum.dimensionCount'),
    ('chemical_shift_list',None),
    ('experiment_classification','spectrum.experimentType'),
    ('experiment_type','spectrum.experimentName'),
    ('ccpn_peaklist_serial','serial'),
    ('ccpn_peaklist_comment','comment'),
    ('ccpn_peaklist_name','title'),
    ('ccpn_peaklist_is_simulated','isSimulated'),
    ('ccpn_spectrum_name','spectrum.name'),
    ('ccpn_complete_spectrum_data',None),
    ('nef_spectrum_dimension',_isALoop),
    ('nef_spectrum_dimension_transfer',_isALoop),
    ('nef_peak',_isALoop),
    ('ccpn_spectrum_hit',_isALoop),
  )),
  'nef_spectrum_dimension':OD((
    ('dimension_id',None),
    ('axis_unit',None),
    ('axis_code',None),
    ('spectrometer_frequency',None),
    ('spectral_width',None),
    ('value_first_point',None),
    ('folding',None),
    ('absolute_peak_positions',None),
    ('is_acquisition',None),
  )),
  'nef_spectrum_dimension_transfer':OD((
    ('dimension_1',None),
    ('dimension_2',None),
    ('transfer_type',None),
    ('is_indirect',None),
  )),
  'nef_peak':OD((
    ('ordinal',None),
    ('peak_id','serial'),
    ('volume','volume'),
    ('volume_uncertainty','volumeError'),
    ('height','height'),
    ('height_uncertainty','heightError'),
    ('position_1',None),
    ('position_uncertainty_1',None),
    ('position_2',None),
    ('position_uncertainty_2',None),
    ('position_3',None),
    ('position_uncertainty_3',None),
    ('position_4',None),
    ('position_uncertainty_4',None),
    ('position_5',None),
    ('position_uncertainty_5',None),
    ('position_6',None),
    ('position_uncertainty_6',None),
    ('position_7',None),
    ('position_uncertainty_7',None),
    ('position_8',None),
    ('position_uncertainty_8',None),
    ('position_9',None),
    ('position_uncertainty_9',None),
    ('position_10',None),
    ('position_uncertainty_10',None),
    ('position_11',None),
    ('position_uncertainty_11',None),
    ('position_12',None),
    ('position_uncertainty_12',None),
    ('position_13',None),
    ('position_uncertainty_13',None),
    ('position_14',None),
    ('position_uncertainty_14',None),
    ('position_15',None),
    ('position_uncertainty_15',None),
    ('chain_code_1',None),
    ('sequence_code_1',None),
    ('residue_type_1',None),
    ('atom_name_1',None),
    ('chain_code_2',None),
    ('sequence_code_2',None),
    ('residue_type_2',None),
    ('atom_name_2',None),
    ('chain_code_3',None),
    ('sequence_code_3',None),
    ('residue_type_3',None),
    ('atom_name_3',None),
    ('chain_code_4',None),
    ('sequence_code_4',None),
    ('residue_type_4',None),
    ('atom_name_4',None),
    ('chain_code_5',None),
    ('sequence_code_5',None),
    ('residue_type_5',None),
    ('atom_name_5',None),
    ('chain_code_6',None),
    ('sequence_code_6',None),
    ('residue_type_6',None),
    ('atom_name_6',None),
    ('chain_code_7',None),
    ('sequence_code_7',None),
    ('residue_type_7',None),
    ('atom_name_7',None),
    ('chain_code_8',None),
    ('sequence_code_8',None),
    ('residue_type_8',None),
    ('atom_name_8',None),
    ('chain_code_9',None),
    ('sequence_code_9',None),
    ('residue_type_9',None),
    ('atom_name_9',None),
    ('chain_code_10',None),
    ('sequence_code_10',None),
    ('residue_type_10',None),
    ('atom_name_10',None),
    ('chain_code_11',None),
    ('sequence_code_11',None),
    ('residue_type_11',None),
    ('atom_name_11',None),
    ('chain_code_12',None),
    ('sequence_code_12',None),
    ('residue_type_12',None),
    ('atom_name_12',None),
    ('chain_code_13',None),
    ('sequence_code_13',None),
    ('residue_type_13',None),
    ('atom_name_13',None),
    ('chain_code_14',None),
    ('sequence_code_14',None),
    ('residue_type_14',None),
    ('atom_name_14',None),
    ('chain_code_15',None),
    ('sequence_code_15',None),
    ('residue_type_15',None),
    ('atom_name_15',None),
  )),
  'ccpn_spectrum_hit':OD((
    ('ccpn_substance_name','substanceName'),
    ('ccpn_pseudo_dimension_number','pseudoDimensionNumber'),
    ('ccpn_point_number','pointNumber'),
    ('ccpn_figure_of_merit','figureOfMerit'),
    ('ccpn_merit_code','meritCode'),
    ('ccpn_normalised_change','normalisedChange'),
    ('ccpn_is_confirmed_','isConfirmed'),
    ('ccpn_concentration','concentration'),
    ('ccpn_','concentrationError'),
    ('ccpn_concentration_uncertainty','concentrationUnit'),
    ('ccpn_comment','comment'),
  )),

  'nef_peak_restraint_links':OD((
    ('nef_peak_restraint_link',_isALoop),
  )),
  'nef_peak_restraint_link':OD((
    ('nmr_spectrum_id',None),
    ('peak_id',None),
    ('restraint_list_id',None),
    ('restraint_id',None),
  )),

  'ccpn_spectrum_group':OD((
  )),

  'ccpn_sample':OD((
    ('name','name'),
    ('pH','ph'),
    ('ionic_strength','ionicStrength'),
    ('amount','amount'),
    ('amount_unit','amountUnit'),
    ('is_hazardous','isHazardous'),
    ('is_virtual','isVirtual'),
    ('creation_date','creationDate'),
    ('batch_identifier','batchIdentifier'),
    ('plate_identifier','plateIdentifier'),
    ('row_number','rowNumber'),
    ('column_number','columnNumber'),
    ('comment','comment'),
    ('ccpn_sample_component',_isALoop),
  )),
  'ccpn_sample_component':OD((
    ('name','name'),
    ('labeling','labeling'),
    ('role','role'),
    ('concentration','concentration'),
    ('concentration_error','concentrationError'),
    ('concentration_unit','concentrationUnit'),
    ('purity','purity'),
    ('comment','comment'),
  )),

  'ccpn_substance':OD((
    ('name','name'),
    ('labeling','labeling'),
    ('substance_type','substanceType'),
    ('user_code','userCode'),
    ('smiles','smiles'),
    ('inchi','inChi'),
    ('cas_number','casNumber'),
    ('empirical_formula','empiricalFormula'),
    ('sequence_string','sequenceString'),
    ('molecular_mass','molecularMass'),
    ('atom_count','atomCount'),
    ('bond_count','bondCount'),
    ('ring_count','ringCount'),
    ('h_bond_donor_count','hBondDonorCount'),
    ('h_bond_acceptor_count','hBondAcceptorCount'),
    ('polar_surface_area','polarSurfaceArea'),
    ('log_partition_coefficient','logPartitionCoefficient'),
    ('comment','comment'),
    ('ccpn_substance_synonym',_isALoop),
  )),
  'ccpn_substance_synonym':OD((
    ('synonym',None),
  )),

  'ccpn_assignments':OD((
  )),

  'ccpn_dataset':OD((
  )),

  'ccpn_integral_list':OD((
  )),

  'ccpn_restraint_list':OD((
    ('potential_type','potentialType'),
    ('origin','origin'),
    ('tensor_magnitude',None),
    ('tensor_rhombicity',None),
    ('tensor_chain_code','tensorChainCode'),
    ('tensor_sequence_code','tensorSequenceCode'),
    ('tensor_residue_type','tensorResidueType'),
    ('ccpn_serial','serial'),
    ('ccpn_name','name'),
    ('ccpn_restraint_type','restraintType'),
    ('ccpn_restraint_item_length','restraintItemLength'),
    ('ccpn_unit','unit'),
    ('ccpn_measurement_type','measurementType'),
    ('ccpn_comment','comment'),
    ('ccpn_tensor_isotropic_value',None),
  )),
  'ccpn_restraint':OD((
    ('ordinal',None),
    ('restraint_id','restraint.serial'),
    ('restraint_combination_id','combinationId'),
    ('chain_code_1',None),
    ('sequence_code_1',None),
    ('residue_type_1',None),
    ('atom_name_1',None),
    ('chain_code_2',None),
    ('sequence_code_2',None),
    ('residue_type_2',None),
    ('atom_name_2',None),
    ('chain_code_3',None),
    ('sequence_code_3',None),
    ('residue_type_3',None),
    ('atom_name_3',None),
    ('chain_code_4',None),
    ('sequence_code_4',None),
    ('residue_type_4',None),
    ('atom_name_4',None),
    ('weight','weight'),
    ('target_value','targetValue'),
    ('target_value_uncertainty','error'),
    ('lower_linear_limit','additionalLowerLimit'),
    ('lower_limit','lowerLimit'),
    ('upper_limit','upperLimit'),
    ('upper_linear_limit','additionalUpperLimit'),
    ('scale','scale'),
    ('distance_dependent','isDistanceDependent'),
    ('name',None),
    ('ccpn_vector_length','restraint.vectorLength'),
    ('ccpn_figure_of_merit','restraint.figureOfMerit'),
  )),

  'ccpn_notes':OD((
    ('ccpn_note',_isALoop),
  )),
  'ccpn_note':OD((
    ('serial','serial'),
    ('name','name'),
    ('created','created'),
    ('last_modified','lastModified'),
    ('text','text'),
  )),

}

# Validity check
if sorted(nef2CcpnMap.keys()) != sorted(saveFrameOrder):
  raise TypeError("Coding Error - saveFrameOrder does not match nef2CcpnMap:\n%s\n%s\n"
                  % (sorted(saveFrameOrder), sorted(nef2CcpnMap.keys())))

# Add loop dictionaries to nef2CcpnMap:
for category in saveFrameOrder:
  for tag, val in nef2CcpnMap[category]:
    if isinstance(val, OD):
      nef2CcpnMap[tag] = val


# # CCPN-NEF mapping:
# #
# # Eventually this should probably be moved to the NEF specification files.
# # Pending agreement on how io integrate it there, we leave it here:
# #
# # The data structure is made of nested orderedDicts:
# # {savefremeName:{loopName:{itemName:ccpnAttributeExpression}}}
# # Order is the recommended writing order.
# # loopName is NOne for items directly inside teh saveFrame.
# # The ccpnAttributeExpression is a string with dots that gives you the relevant attribute
# # starting form he object matching the saveeframe or loop row, as passed to operator.attrgetter.
# # Where this is not possible, the expression is left as None.
# # FOr 'list' attributes, such as Peak.position, the mapping isi given only of position_1
# # and is left as None for the rest.
# # The code must determine how many of the attributes (up to e.g. Peak.position_15) to include
#
#
# # Saveframe map for generic restraint - later modified for the official versions
# _RestraintListMap = OD((
#   ('potential_type','potentialType'),
#   ('origin', 'origin'),
#   ('tensor_magnitude', None),
#   ('tensor_rhombicity', None),
#   ('tensor_chain_code', 'tensorChainCode'),
#   ('tensor_sequence_code', 'tensorSequenceCode'),
#   ('tensor_residue_type', 'tensorResidueType'),
#   ('ccpn_serial', 'serial'),
#   ('ccpn_name', 'name'),
#   ('ccpn_restraint_type', 'restraintType'),
#   ('ccpn_restraint_item_length', 'restraintItemLength'),
#   ('ccpn_unit', 'unit'),
#   ('ccpn_measurement_type', 'measurementType'),
#   ('ccpn_comment', 'comment'),
#   ('ccpn_tensor_isotropic_value', None),
# ))
#
# # Restraint loop columns for generic restraint - abridged for the official versions
# _RestraintColumns = OD((                   # Matching class: RestraintContribution
#   ('ordinal', None), ('restraint_id', 'restraint.serial'),
#   ('restraint_combination_id', 'combinationId'),
#   ('chain_code_1', None), ('sequence_code_1', None), ('residue_type_1', None), ('atom_name_1',None),
#   ('chain_code_2', None), ('sequence_code_2', None), ('residue_type_2', None), ('atom_name_2',None),
#   ('chain_code_3', None), ('sequence_code_3', None), ('residue_type_3', None), ('atom_name_3',None),
#   ('chain_code_4', None), ('sequence_code_4', None), ('residue_type_4', None), ('atom_name_4',None),
#   ('weight', 'weight'), ('target_value', 'targetValue'), ('target_value_uncertainty', 'error'),
#   ('lower_linear_limit', 'additionalLowerLimit'), ('lower_limit', 'lowerLimit'),
#   ('upper_limit', 'upperLimit'), ('upper_linear_limit', 'additionalUpperLimit'),
#   ('scale', 'scale'), ('distance_dependent', 'isDistanceDependent'),
#   ('name', None),
#   ('ccpn_vector_length', 'restraint.vectorLength'),
#   ('ccpn_figure_of_merit', 'restraint.figureOfMerit')
# ))

# # NEF supported restraint list maps:
#
# _removeCcpnItems = ('ccpn_restraint_type', 'ccpn_restraint_item_length', 'ccpn_measurement_type')
# _removeRdcColumns = ('ccpn_vector_length', )
# _removeDihedralColumns = ('name', )
#
# # Distance restraint list Map
# _DistanceRestraintListMap = OD(tt for tt in _RestraintListMap.items()
#                                if not 'tensor' in tt[0] and tt[0] not in _removeCcpnItems)
# columns = OD(tt for tt in _RestraintColumns.items()
#              if tt[0][-2:] not in ('_3', '_4')
#              and tt[0] not in (_removeRdcColumns + _removeDihedralColumns))
# _DistanceRestraintListMap['nef_distance_restraint'] = columns
#
# # Dihedral restraint list Map
# _DihedralRestraintListMap = OD(tt for tt in _RestraintListMap.items()
#                                if not 'tensor' in tt[0])
# for tag in _removeCcpnItems:
#   del _DihedralRestraintListMap[tag]
# columns = OD(tt for tt in _RestraintColumns.items() if tt[0] not in _removeRdcColumns)
# _DihedralRestraintListMap['nef_dihedral_restraint'] = columns
#
# # Rdc restraint list Map
# _RdcRestraintListMap = _RestraintListMap.copy()
# for tag in _removeCcpnItems:
#   del _RdcRestraintListMap[tag]
# columns = OD(tt for tt in _RestraintColumns.items() if tt[0][-2:] not in ('_3', '_4')
#              and tt[0] not in _removeDihedralColumns)
# _RdcRestraintListMap['nef_rdc_restraint'] = columns
#
# _RestraintListMap['ccpn_restraint'] = _RestraintColumns


def convert2NefString(project):
  """Convert project ot NEF string"""
  converter = CcpnNefWriter(project)
  dataBlock = converter.exportProject()
  return dataBlock.toString()

class CcpnNefWriter:
  """CCPN NEF reader/writer"""

  # # Saveframes in output order with contained items and loops
  # # End-of-line comments show the CCPN object(s) providing the data
  # # String item values is a navigation expression to get item value from top l;evel object
  # # List item values is the list of columns for a loop.
  # Nef2CcpnMap = OD((
  #
  #   ('nef_nmr_meta_data', OD((                   # Singleton Metadata - from Project or DataSet
  #     ('format_name', None),
  #     ('format_version', None),
  #     ('program_name', None),
  #     ('program_version', None),
  #     ('creation_date', None),
  #     ('uuid', None),
  #     ('coordinate_file_name', None),
  #     ('ccpn_dataset_name', 'name'),
  #     ('ccpn_dataset_comment', None),
  #     ('nef_related_entries', OD((                         # No Matching class
  #       ('database_name', None), ('database_accession_code', None),
  #     ))),
  #     ('nef_program_script', OD((                          # No Matching class
  #       ('program_name', None), ('script_name', None), ('script', None),
  #     ))),
  #     ('nef_run_history', OD((                             # Matching class: CalculationStep
  #       ('run_ordinal', 'serial'), ('program_name', 'programName'),
  #       ('program_version', 'programVersion'),
  #       ('script_name', 'scriptName'), ('script', 'script'),
  #       ('ccpn_input_uuid', 'inputDataUuid'), ('ccpn_output_uuid', 'outputDataUuid'),
  #     ))),
  #   ))),
  #
  #   ('nef_molecular_system', OD((                # Singleton (Chains)
  #     ('nef_sequence', OD((                               # Matching class: Residue
  #       ('chain_code', 'chain.shortName'), ('sequence_code', 'sequenceCode'),
  #       ('residue_type', 'residueType'),
  #       ('linking', 'linking'), ('residue_variant', 'residueVariant'),
  #      ))),
  #
  #     # NBNB REDO - (we no longer have Bonds
  #
  #     ('nef_covalent_links', OD((               # Matching class : Bond
  #       ('chain_code_1', None), ('sequence_code_1', None),
  #       ('residue_type_1', None), ('atom_name_1', None),
  #       ('chain_code_2', None), ('sequence_code_2', None),
  #       ('residue_type_2', None), ('atom_name_2', None),
  #     ))),
  #   ))),
  #
  #   ('nef_chemical_shift_list', OD((             # Matching class: ChemicalShiftList
  #     ('atom_chemical_shift_units', 'unit'),
  #     ('ccpn_serial', 'serial'),
  #     ('ccpn_name', 'name'),
  #     ('ccpn_autoUpdate', 'autoUpdate'),
  #     ('ccpn_isSimulated', 'isSimulated'),
  #     ('ccpn_comment', 'comment'),
  #     ('nef_chemical_shift', OD((                # Matching class: ChemicalShift
  #       ('chain_code', None), ('sequence_code', None), ('residue_type', None), ('atom_name', None),
  #       ('value', 'value'), ('value_uncertainty', 'valueError'),
  #       ('ccpn_figure_of_merit', 'figureOfMerit'), ('ccpn_comment', 'comment'),
  #     ))),
  #   ))),
  #
  #   ('nef_distance_restraint_list', _DistanceRestraintListMap),     # Matching class: RestraintList
  #
  #   ('nef_dihedral_restraint_list', _DihedralRestraintListMap),     # Matching class: RestraintList
  #
  #   ('nef_rdc_restraint_list', _RdcRestraintListMap),               # Matching class: RestraintList
  #
  #   # NBNB TBD Add SpectrumReference, ccpn-specific parameters for Spectrum
  #
  #   ('nef_nmr_spectrum', OD((                    # Matching class: PeakList
  #     ('num_dimensions', 'spectrum.dimensionCount'),
  #     ('chemical_shift_list', None),
  #     ('experiment_classification', 'spectrum.experimentType'),
  #     ('experiment_type', 'spectrum.experimentName'),
  #     ('ccpn_peaklist_serial', 'serial'),
  #     ('ccpn_peaklist_comment', 'comment'),
  #     ('ccpn_peaklist_name', 'title'),
  #     ('ccpn_peaklist_is_simulated', 'isSimulated'),
  #     ('ccpn_spectrum_name', 'spectrum.name'),
  #     ('ccpn_complete_spectrum_data', None),
  #     ('nef_spectrum_dimension', OD((            # No Matching class
  #       ('dimension_id', None), ('axis_unit', None), ('axis_code', None),
  #       ('spectrometer_frequency', None), ('spectral_width', None), ('value_first_point', None),
  #       ('folding', None), ('absolute_peak_positions', None), ('is_acquisition', None),
  #     ))),
  #     ('nef_spectrum_dimension_transfer', OD((   # No Matching class
  #       ('dimension_1', None), ('dimension_2', None), ('transfer_type', None), ('is_indirect',None),
  #     ))),
  #     ('nef_peak', OD((                          # Matching class: Peak
  #       ('ordinal', None),
  #       ('peak_id', 'serial'),
  #       ('volume', 'volume'),
  #       ('volume_uncertainty', 'volumeError'),
  #       ('height', 'height'),
  #       ('height_uncertainty', 'heightError'),
  #       ('position_1', None), ('position_uncertainty_1', None),
  #       ('position_2', None), ('position_uncertainty_2', None),
  #       ('position_3', None), ('position_uncertainty_3', None),
  #       ('position_4', None), ('position_uncertainty_4', None),
  #       ('position_5', None), ('position_uncertainty_5', None),
  #       ('position_6', None), ('position_uncertainty_6', None),
  #       ('position_7', None), ('position_uncertainty_7', None),
  #       ('position_8', None), ('position_uncertainty_8', None),
  #       ('position_9', None), ('position_uncertainty_9', None),
  #       ('position_10', None), ('position_uncertainty_10', None),
  #       ('position_11', None), ('position_uncertainty_11', None),
  #       ('position_12', None), ('position_uncertainty_12', None),
  #       ('position_13', None), ('position_uncertainty_13', None),
  #       ('position_14', None), ('position_uncertainty_14', None),
  #       ('position_15', None), ('position_uncertainty_15', None),
  #       ('chain_code_1', None), ('sequence_code_1', None), ('residue_type_1', None),
  #       ('atom_name_1', None),
  #       ('chain_code_2', None), ('sequence_code_2', None), ('residue_type_2', None),
  #       ('atom_name_2', None),
  #       ('chain_code_3', None), ('sequence_code_3', None), ('residue_type_3', None),
  #       ('atom_name_3', None),
  #       ('chain_code_4', None), ('sequence_code_4', None), ('residue_type_4', None),
  #       ('atom_name_4', None),
  #       ('chain_code_5', None), ('sequence_code_5', None), ('residue_type_5', None),
  #       ('atom_name_5', None),
  #       ('chain_code_6', None), ('sequence_code_6', None), ('residue_type_6', None),
  #       ('atom_name_6', None),
  #       ('chain_code_7', None), ('sequence_code_7', None), ('residue_type_7', None),
  #       ('atom_name_7', None),
  #       ('chain_code_8', None), ('sequence_code_8', None), ('residue_type_8', None),
  #       ('atom_name_8', None),
  #       ('chain_code_9', None), ('sequence_code_9', None), ('residue_type_9', None),
  #       ('atom_name_9', None),
  #       ('chain_code_10', None), ('sequence_code_10', None), ('residue_type_10', None),
  #       ('atom_name_10', None),
  #       ('chain_code_11', None), ('sequence_code_11', None), ('residue_type_11', None),
  #       ('atom_name_11', None),
  #       ('chain_code_12', None), ('sequence_code_12', None), ('residue_type_12', None),
  #       ('atom_name_12', None),
  #       ('chain_code_13', None), ('sequence_code_13', None), ('residue_type_13', None),
  #       ('atom_name_13', None),
  #       ('chain_code_14', None), ('sequence_code_14', None), ('residue_type_14', None),
  #       ('atom_name_14', None),
  #       ('chain_code_15', None), ('sequence_code_15', None), ('residue_type_15', None),
  #       ('atom_name_15', None),
  #     ))),
  #     ('ccpn_spectrum_hit', OD((
  #       ('ccpn_substance_name', 'substanceName'),
  #       ('ccpn_pseudo_dimension_number', 'pseudoDimensionNumber'),
  #       ('ccpn_point_number', 'pointNumber'),
  #       ('ccpn_figure_of_merit', 'figureOfMerit'),
  #       ('ccpn_merit_code', 'meritCode'),
  #       ('ccpn_normalised_change', 'normalisedChange'),
  #       ('ccpn_is_confirmed_', 'isConfirmed'),
  #       ('ccpn_concentration', 'concentration'),
  #       ('ccpn_', 'concentrationError'),
  #       ('ccpn_concentration_uncertainty', 'concentrationUnit'),
  #       ('ccpn_comment', 'comment'),
  #     ))),
  #   ))),
  #
  #   # NB Must be calculated after all PeakLists and RestraintLists:
  #   ('nef_peak_restraint_links', OD((          # Singleton (RestraintsLists, PeakLists)
  #     ('nef_peak_restraint_link', OD((
  #       ('nmr_spectrum_id', None), ('peak_id', None), ('restraint_list_id', None),
  #       ('restraint_id', None),
  #     ))),
  #   ))),
  #
  #   ('ccpn_spectrum_group', OD()),               # SpectrumGroup
  #
  #   ('ccpn_sample', OD((                         # Matching class: Sample
  #     ('name', 'name'),
  #     ('pH', 'ph'),
  #     ('ionic_strength', 'ionicStrength'),
  #     ('amount', 'amount'),
  #     ('amount_unit', 'amountUnit'),
  #     ('is_hazardous', 'isHazardous'),
  #     ('is_virtual', 'isVirtual'),
  #     ('creation_date', 'creationDate'),
  #     ('batch_identifier', 'batchIdentifier'),
  #     ('plate_identifier', 'plateIdentifier'),
  #     ('row_number', 'rowNumber'),
  #     ('column_number', 'columnNumber'),
  #     ('comment', 'comment'),
  #     ('ccpn_sample_component', OD((
  #       ('name', 'name'), ('labeling', 'labeling'), ('role', 'role'),
  #       ('concentration', 'concentration'),
  #       ('concentration_error', 'concentrationError'), ('concentration_unit', 'concentrationUnit'),
  #       ('purity', 'purity'), ('comment', 'comment'),
  #     ))),
  #   ))),
  #
  #   ('ccpn_substance', OD((                      # Matching class: Substance
  #     ('name', 'name'),
  #     ('labeling', 'labeling'),
  #     ('substance_type', 'substanceType'),
  #     ('user_code', 'userCode'),
  #     ('smiles', 'smiles'),
  #     ('inchi', 'inChi'),
  #     ('cas_number', 'casNumber'),
  #     ('empirical_formula', 'empiricalFormula'),
  #     ('sequence_string', 'sequenceString'),
  #     ('molecular_mass', 'molecularMass'),
  #     ('atom_count', 'atomCount'),
  #     ('bond_count', 'bondCount'),
  #     ('ring_count', 'ringCount'),
  #     ('h_bond_donor_count', 'hBondDonorCount'),
  #     ('h_bond_acceptor_count', 'hBondAcceptorCount'),
  #     ('polar_surface_area', 'polarSurfaceArea'),
  #     ('log_partition_coefficient', 'logPartitionCoefficient'),
  #     ('comment', 'comment'),
  #     ('ccpn_substance_synonyms', OD((
  #       ('synonym', None),
  #     ))),
  #   ))),
  #
  #   ('ccpn_assignments', OD()),                  # Singleton (NmrChains)
  #   ('ccpn_dataset', OD()),                      # DataSet
  #
  #   ('ccpn_restraint_list', _RestraintListMap),  # Matching class: RestraintList
  #
  #   ('ccpn_notes', OD((                          # Singleton (Notes)
  #     ('ccpn_note', OD((
  #       ('serial', 'serial'), ('name', 'name'), ('created', 'created'),
  #       ('last_modified', 'lastModified'), ('text', 'text'),
  #     ))),
  #   ))),
  # ))

  def __init__(self, project:'ccpn.Project', specificationFile=None, mode='strict',
               programName=None, programVersion=None):
    self.project = project
    self.mode=mode
    if specificationFile is None:
      self.specification = None
    else:
      # NBNB TBD reconsider whether we want the spec summary or something else
      self.specification = Specification.getCcpnSpecification(specificationFile)

    self.programName = programName or project._appBase.applicationName
    self.programVersion = programVersion or project._appBase.applicationVersion
    self.ccpn2SaveFrameName = {}


  def exportDataSet(self, dataSet:'DataSet') -> StarIo.NmrDataBlock:
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


  def exportProject(self) -> StarIo.NmrDataBlock:
    """Get project and all contents as NEF object tree for export"""

    self.ccpn2SaveFrameName = {}
    saveFrames = []

    project = self.project

    # MetaData
    saveFrames.append(self.makeNefMetaData(project))

    # Chains
    saveFrames.append(self.chains2Nef(project.chains))

    # ChemicalShiftLists
    for obj in project.chemicalShiftLists:
      saveFrames.append(self.chemicalShiftList2Nef(obj))

    # RestraintLists and
    restraintLists = sorted(project.restraintLists,
                            key=attrgetter('restraintType', 'serial'))
    for obj in restraintLists:
      saveFrames.append(self.restraintList2Nef(obj))

    # Spectra
    for obj in project.spectra:
      # NB we get multiple saveframes, one per peakList
      saveFrames.extend(self.spectrum2Nef(obj))

    # restraint-peak links
    saveFrame = self.peakRestraintLinks2Nef(restraintLists, project.peakLists)
    if saveFrame:
      saveFrames.append(saveFrame)

    # Now add CCPN-specific data:
    # # SpectrumGroups
    # for obj in project.spectrumGroups:
    #   saveFrames.append(self.spectrumGroup2Nef(obj))

    # Samples
    for obj in project.samples:
      saveFrames.append(self.sample2Nef(obj))

    # Substances
    for obj in project.substances:
      saveFrames.append(self.substance2Nef(obj))

    # # NmrChains
    # saveFrames.append(self.nmrChains2Nef(project.nmrChains))

    # # DataSets - NB does not include RestraintLists, which are given above
    # for obj in project.dataSets:
    #   saveFrames.append(self.dataSet2Nef(obj))

    # Notes
    saveFrame = self.notes2Nef(project.notes)
    if saveFrame:
      saveFrames.append(saveFrame)

    # make and return dataBlock with sameframes in export order
    result = StarIo.NmrDataBlock(name=self.project.name)
    for saveFrame in self._saveFrameNefOrder(saveFrames):
      result.addItem(saveFrame['sf_framecode'], saveFrame)
    #
    return result

  def makeNefMetaData(self, headObject:'Union[ccpn.Project, ccpn.DataSet]',
                          coordinateFileName:str=None) -> StarIo.NmrSaveFrame:
    """make NEF metadata saveframe from Project"""

    # NB No attributes can be set from map here, so we do not try

    category = 'nef_nmr_meta_data'
    result = self._newNefSaveFrame(headObject, category, category)

    # NBNB TBD FIXME add proper values for format version from specification file
    result['format_name'] = 'nmr_exchange_format'
    # format_version=None
    result['coordinate_file_name'] = coordinateFileName
    if headObject.className == 'Project':
      result['program_name'] = self.programName
      result['program_version'] = self.programVersion
      result['creation_date'] = timeStamp = commonUtil.getTimeStamp()
      result['uuid'] = '%s-%s-%s' % (self.programName, timeStamp, random.randint(0, maxRandomInt))


      # TODO NBNB now set automatically


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

  def chains2Nef(self, chains:List['ccpn.Chain']) -> StarIo.NmrSaveFrame:
    """Convert selected Chains to CCPN NEF saveframe"""

    category = 'nef_molecular_system'
    if chains:
      project = chains[0].project
      result = self._newNefSaveFrame(project, category, category)

      loopName = 'nef_sequence'
      loop = result[loopName]

      for chain in chains:
        for residue in chain.residues:
          rowdata = self._loopRowData(loopName, residue)
          loop.newRow(rowdata)

      loop = result['nef_covalent_links']
      columns = ('chain_code_1', 'sequence_code_1', 'residue_type_1', 'atom_name_1',
                 'chain_code_2', 'sequence_code_2', 'residue_type_2', 'atom_name_2'
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

  def chemicalShiftList2Nef(self, chemicalShiftList) -> StarIo.NmrSaveFrame:
    """Convert ChemicalShiftList to CCPN NEF saveframe"""

    # Set up frame
    category = 'nef_chemical_shift_list'
    result = self._newNefSaveFrame(chemicalShiftList, category, chemicalShiftList.name)

    self.ccpn2SaveFrameName[chemicalShiftList] = result['sf_framecode']

    # Fill in loop - use dictionary rather than list as this is more robust against reorderings
    loopName = 'nef_chemical_shift'
    loop = result[loopName]
    atomCols = ['chain_code', 'sequence_code', 'residue_type', 'atom_name',]
    # NB We cannot use nmrAtom.id.split('.'), since the id has reserved characters remapped
    for shift in chemicalShiftList.chemicalShifts:
      rowdata = self._loopRowData(loopName, shift)
      rowdata.update(zip(atomCols, shift.nmrAtom._idTuple))
      loop.newRow(rowdata)
    #
    return result

  def restraintList2Nef(self, restraintList) -> StarIo.NmrSaveFrame:
    """Convert RestraintList to CCPN NEF saveframe"""

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


    result = self._newNefSaveFrame(restraintList, category, restraintList.name)

    self.ccpn2SaveFrameName[restraintList] = result['sf_framecode']

    if category in ('nef_rdc_restraint_list', 'ccpn_restraint_list'):
      tensor = restraintList.tensor
      if tensor is not None:
        result['tensor_magnitude'] = tensor.axial
        result['tensor_rhombicity'] = tensor.rhombic
        result['ccpn_tensor_isotropic_value'] = tensor.isotropic


    loop = result[loopName]

    if category == 'ccpn_restraint_list':
      # Remove unnecessary columns
      removeNameEndings = ('_1', '_2', '_3', '_4')[itemLength:]
      for tag in loop.columns:
        if tag[:-2] in removeNameEndings:
          loop.removeColumn(tag)

    ordinal = 0
    for contribution in restraintList.restraintContributions:
      rowdata = self._loopRowData(loopName, contribution)
      for item in contribution.restraintItems:
        row = loop.newRow(rowdata)
        ordinal += 1
        row._set('ordinal', ordinal)

        # NBNB TBD FIXME Using the PID, as we do here, you are remapping '.' to '^'
        # NBNB reconsider!!!

        # Set individual parts of assignment one by one.
        # NB _set command takes care of varying number of items
        assignments = list(zip(*(x.split('.') for x in item)))
        for ii,tag in enumerate(('chain_code', 'sequence_code', 'residue_type', 'atom_name',)):
          row._set(tag, assignments[ii])
    #
    return result

  def spectrum2Nef(self, spectrum:'ccpn.Spectrum') -> StarIo.NmrSaveFrame:
    """Convert spectrum to NEF saveframes - one per peaklist

    Will crate a peakList if none are present"""

    peakLists = spectrum.peakLists
    if not peakLists:
      peakLists = [spectrum.newPeakList()]

    result = [self.peakList2Nef(peakLists[0], exportCompleteSpectrum=True)]
    for peakList in peakLists[1:]:
      result.append(self.peakList2Nef(peakList))
    #
    return result

  def peakList2Nef(self, peakList:'ccpn.peakList',
                   exportCompleteSpectrum=False) -> StarIo.NmrSaveFrame:
    """Convert PeakList to CCPN NEF saveframe
    """

    spectrum = peakList.spectrum

    # We do not support sampled or unprocessed dimensions yet. NBNB TBD.
    if any (x != 'Frequency' for x in spectrum.dimensionTypes):
      raise NotImplementedError(
        "NEF only implemented for processed frequency spectra, dimension types were: %s"
        % spectrum.dimensionTypes
      )

    # Get unique frame name
    name = spectrum.name
    if len(spectrum.peakLists) > 1:
      ss = '_'
      name = '%s%s%s' % (name ,ss, peakList.serial)
      while spectrum.project.getSpectrum(name):
        # This name is taken - modify it
        ss += '_'
        name = '%s%s%s' % (name ,ss, peakList.serial)

    # Set up frame
    category = 'nef_nmr_spectrum'
    print('@~@~ spec. PL, exp, ds', spectrum.name, peakList.title,
          spectrum._wrappedData.experiment.name, spectrum._wrappedData.name)
    result = self._newNefSaveFrame(peakList, category, name)

    self.ccpn2SaveFrameName[peakList] = result['sf_framecode']

    result['chemical_shift_list'] = self.ccpn2SaveFrameName.get(peakList.chemicalShiftList)

    result['ccpn_complete_spectrum_data'] = exportCompleteSpectrum

    # NBNB TBD FIXME assumes ppm unit and Frequency dimensions for now
    # WIll give wrong values for Hz or pointNumber units, and
    # WIll fill in all None for non-Frequency dimensions

    loopName = 'nef_spectrum_dimension'
    loop = result[loopName]
    data = OD()
    data['axis_unit'] = spectrum.axisUnits
    data['axis_code'] = spectrum.isotopeCodes
    data['spectrometer_frequency'] = spectrum.spectrometerFrequencies
    data['spectral_width'] = spectrum.spectralWidths
    data['value_first_point'] = [tt[1] for tt in spectrum.spectrumLimits]
    data['folding'] = spectrum.foldingModes
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

    loopName = 'nef_spectrum_dimension_transfer'
    loop = result[loopName]
    for tt in spectrum.magnetisationTransfers:
      loop.newRow(dict(zip(['dimension_1', 'dimension_2', 'transfer_type', 'is_indirect'], tt)))


    loopName = 'nef_peak'
    loop = result[loopName]

    # Remove superfluous tags
    removeNameEndings = ('_1', '_2', '_3', '_4', '_5', '_6', '_7', '_8', '_9',
                         '_10', '_11', '_12', '_13', '_14', '_15',)[spectrum.dimensionCount:]
    for tag in loop.columns:
      if any(tag.endswith(x) for x in removeNameEndings):
        loop.removeColumn(tag)

    ordinal = 0
    for peak in peakList.peaks:
      rowdata = self._loopRowData(loopName, peak)

      assignments = peak.assignedNmrAtoms
      if assignments:
        for tt in assignments:
          # Make one row per assignment
          row = loop.newRow(rowdata)
          ordinal += 1
          row._set('ordinal', ordinal)
          # NB the row._set function will set position_1, position_2 etc.
          row._set('position', peak.position)
          row._set('position_uncertainty', peak.positionError)

          # Add the assignments
          ll =list(zip(*(x.id.split('.') if x else [None, None, None, None] for x in tt)))
          row._set('chain_code', ll[0])
          row._set('sequence_code', ll[1])
          row._set('residue_type', ll[2])
          row._set('atom_name', ll[3])

      else:
        # No assignments - just make one unassigned row
        row = loop.newRow(rowdata)
        ordinal += 1
        row._set('ordinal', ordinal)
        # NB the row._set function will set position_1, position_2 etc.
        row._set('position', peak.position)
        row._set('position_uncertainty', peak.positionError)


    if exportCompleteSpectrum and spectrum.spectrumHits:
      loopName = 'ccpn_spectrum_hit'
      loop = result[loopName]
      for spectrumHit in spectrum.spectrumHits:
        loop.newRow(self._loopRowData(loopName, spectrumHit))
    else:
      del result['ccpn_spectrum_hit']

      # NB do more later (e.g. SpectrumReference)

    #
    return result


  def peakRestraintLinks2Nef(self, restraintLists:Sequence['ccpn.RestraintList'],
                             peakLists:Sequence['ccpn.PeakList']) -> StarIo.NmrSaveFrame:

    data = []
    for restraintList in restraintLists:
      restraintListFrame = self.ccpn2SaveFrameName.get(restraintList)
      if restraintListFrame is not None:
        for restraint in restraintList.restraints:
          for peak in restraint.peaks:
            peakListFrame = self.ccpn2SaveFrameName.get(peak.peakList)
            if peakListFrame is not None:
              data.append((peakListFrame, peak.serial, restraintListFrame, restraint.serial))

    if data:
      category = 'nef_peak_restraint_links'
      columns = ('nmr_spectrum_id', 'peak_id', 'restraint_list_id', 'restraint_list_id', )
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



  def sample2Nef(self, sample:'ccpn.Sample') -> StarIo.NmrSaveFrame:
    """Convert Sample to CCPN NEF saveframe"""

    # Set up frame
    category = 'ccpn_sample'
    result = self._newNefSaveFrame(sample, category, sample.name)

    self.ccpn2SaveFrameName[sample] = result['sf_framecode']

    # Fill in loop
    loopName = 'ccpn_sample_component'
    loop = result[loopName]
    for sampleComponent in sample.sampleComponents:
      loop.newRow(self._loopRowData(loopName, sampleComponent))
    #
    return result

  def substance2Nef(self, substance:'ccpn.Substance') -> StarIo.NmrSaveFrame:
    """Convert Substance to CCPN NEF saveframe"""

    # Set up frame
    category = 'ccpn_substance'
    name = '%s.%s' % (substance.name, substance.labeling)
    result = self._newNefSaveFrame(substance, category, name)

    self.ccpn2SaveFrameName[substance] = result['sf_framecode']

    loopName = 'ccpn_substance_synonyms'
    loop = result[loopName]
    for synonym in substance.synonyms:
      loop.newRow((synonym,))
    #
    return result

  def notes2Nef(self, notes:List['ccpn.Note']) -> StarIo.NmrSaveFrame:
    """Convert Notes to CCPN NEF saveframe"""

    # Set up frame
    category = 'ccpn_notes'
    if notes:
      result = self._newNefSaveFrame(notes[0].project, category, category)
      loopName = 'ccpn_note'
      loop = result[loopName]
      for note in sorted(notes):
        loop.newRow(self._loopRowData(loopName, note))
    else:
      result = None
    #
    return result

  def _saveFrameNefOrder(self, saveframes:List[Optional[StarIo.NmrSaveFrame]]
                         ) -> List[StarIo.NmrSaveFrame]:
    """Reorder saveframes in NEF export order, and filter out Nones"""
    dd = {}
    for saveframe in saveframes:
      if saveframe is not None:
        ll = dd.setdefault(saveframe['sf_category'], [])
        ll.append(saveframe)
    #
    result = []
    for tag in nef2CcpnMap.keys():
      if tag in dd:
        ll = dd.pop(tag)
        result.extend(ll)
    if dd:
      raise ValueError("Unknown saveframe types in export: %s" % list(dd.keys()))
    #
    return result

  def _loopRowData(self, loopName:str, wrapperObj:'ccpn.AbstractWrapperObject') -> dict:
    """Fill in a loop row data dictionary from master mapping and wrapperObj.
    Unmapped data to be added afterwards"""

    rowdata = {}
    for neftag,attrstring in nef2CcpnMap[loopName].items():
      if attrstring is not None:
        rowdata[neftag] = attrgetter(attrstring)(wrapperObj)
    return rowdata

  def _newNefSaveFrame(self, wrapperObj:'ccpn.AbstractWrapperObject',
                      category:str, name:str) -> StarIo.NmrSaveFrame:
    """Create new NEF saveframe of category for wrapperObj using data from self.Nef2CcpnMap
    The functions will fill in top level items and maek loops, but not
    fill in loop data
    """

    name = StarIo.string2FramecodeString(name)
    if name != category:
      name = '%s_%s' % (category, name)


    # Set up frame
    result = StarIo.NmrSaveFrame(name=name, category=category)
    result.addItem('sf_category', category)
    result.addItem('sf_framecode', name)

    # Add data
    frameMap = nef2CcpnMap[category]
    for tag,itemvalue in frameMap.items():
      if itemvalue is None:
        result.addItem(tag, None)
      elif isinstance(itemvalue, str):
        result.addItem(tag, attrgetter(itemvalue)(wrapperObj))
      else:
        # This is a loop
        assert isinstance(itemvalue, OD), "Invalid item specifier in Nef2CcpnMap: %s" % itemvalue
        result.newLoop(tag, itemvalue)
    #
    return result


class CcpnNefReader:

  # Importer functions - used for converting saveframes and loops
  importers = {}

  def __init__(self, specificationFile=None, mode='standard'):

    self.mode=mode
    self.saveFrameName = None
    self.warnings = []
    self.errors = []

    # Map for resolving crosslinks in NEF file
    self.frameCode2Object = {}


  def loadFile(self, path:str, project=None):
    """Load NEF file at path into project"""

    if project is not None:
      raise NotImplementedError("Loading NEF files into existing projects not implemented yet")

    # TODO Add error handling
    # TODO Add provision for out-of-order files (we assume correct order, e.g. for crosslinks)

    nmrDataExtent = StarIo.parseNefFile(path)
    dataBlocks = list(nmrDataExtent.values)
    dataBlock = dataBlocks[0]
    if project is None:
      project = self.project = coreIo.newProject(dataBlock.name)

    for saveFrameName, saveFrame in dataBlock.items():
      # TODO NBNB this assumes we get them in the right order. Reconsider later

      self.saveFrameName = saveFrameName

      sf_category = saveFrame.get('sf_category')
      importer = self.importers.get(sf_category)
      # NB - newObject may be project, for some saveframes.
      importer(project, saveFrame)

      # Handle unmapped elements
      extraTags = [x for x in saveFrame
                   if x not in nef2CcpnMap[sf_category]
                   and x not in ('sf_category', 'sf_framecode')]
      if extraTags:
        print("WARNING - unused tags in saveframe %s: %s" % (saveFrameName, extraTags))
        # TODO put here function that stashes data in object, or something
        # ues newObject here


  def load_nef_nmr_meta_data(self, project, saveFrame):
    """load nef_nmr_meta_data saveFrame"""

    return project

    # TODO - store data in this saveframe
    # for now we store none of this, as the storage slots are in DataSet, not Project
    # Maybe for another load function?
  #
  importers['nef_nmr_meta_data'] = load_nef_nmr_meta_data


  def load_nef_molecular_system(self, project, saveFrame):
    """load nef_molecular_system saveFrame"""
    mapping = nef2CcpnMap['nef_molecular_system']
    for tag, ccpnTag in mapping.items():
      if ccpnTag == _isALoop:
        loop = saveFrame.get(ccpnTag)
        if loop:
          importer = self.importers[ccpnTag]
          importer(self, project, loop)
    #
    return project
  #
  importers['nef_molecular_system'] = load_nef_molecular_system


  def load_nef_sequence(self, project, loop):
    """Load nef_sequence loop"""

    chainData = {}
    for row in loop.data:
      chainCode = row['chain_code']
      ll = chainData.setdefault(chainCode, [])
      ll.append(row)

    defaultChainCode = 'A'
    if None in chainData:
      # Replace chainCode None with actual chainCode
      while defaultChainCode in chainData:
        defaultChainCode = commonUtil.incrementName(defaultChainCode)
      chainData[defaultChainCode] = chainData.pop(None)


    sequence2Chain = {}
    tags =('sequence_code', 'residue_type', 'linking', 'residue_variant')
    for chainCode, rows in sorted(chainData.items()):
      compoundName = rows[0].get('ccpn_compound_name')
      role = rows[0].get('ccpn_chain_role')
      comment = rows[0].get('ccpn_chain_comment')
      sequence = tuple(tuple(row.get(tag) for tag in tags) for row in rows)
      lastChain = sequence2Chain.get(sequence)
      if lastChain is None:
        newSubstance = project.fetchNefSubstance(sequence=rows, compoundName=compoundName)
        newChain = newSubstance.createChainFromSubstance(shortName=chainCode, role=role,
                                                         comment=comment)
        sequence2Chain[sequence] = newChain
      else:
        newChain = lastChain.substance.createChainFromSubstance(shortName=chainCode,
                                                                role=role, comment=comment)
  #
  # 'nef_sequence':OD((
  #   ('chain_code','chain.shortName'),
  #   ('sequence_code','sequenceCode'),
  #   ('residue_type','residueType'),
  #   ('linking','linking'),
  #   ('residue_variant','residueVariant'),
  #   ('ccpn_comment','comment'),
  #   ('ccpn_chain_role','chain.role'),
  #   ('ccpn_compound_name','chain.compoundName'),
  #   ('ccpn_chain_comment','chain.comment'),
  # )),
  # 'nef_covalent_links':OD((
  #   ('chain_code_1',None),
  #   ('sequence_code_1',None),
  #   ('residue_type_1',None),
  #   ('atom_name_1',None),
  #   ('chain_code_2',None),
  #   ('sequence_code_2',None),
  #   ('residue_type_2',None),
  #   ('atom_name_2',None),
  # )),


  def _defaultSaveFrameLoader(self, parent, saveFrame, creatorFuncName):
    """load standard saveFrame"""

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]

    parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

    # Get name from frameCode, if the mapping has one
    # A bit of a hack,this, but it should work for
    # 1) unique saveframes, where the frameCOde is the same s the category (no-op)
    # 2) saveframes where there is a 'name' attribute set from the frameCode
    name = framecode[len(category) + 1:]
    if name and 'name' in mapping and mapping['name'] is None:
      parameters['name'] = name

    # Make main object
    result = getattr(parent, creatorFuncName)(**parameters)

    # Load loops, with object as parent
    for loopName in loopNames:
      loop = saveFrame.get(loopName)
      if loop:
        importer = self.importers[loopName]
        importer(self, result, loop)
    #
    return result
  #

  importers['nef_chemical_shift_list'] = partial(_defaultSaveFrameLoader,
                                                 creatorFuncName='newChemicalShiftList')

  def load_nef_chemical_shift(self, parent, loop):
    """load nef_chemical_shift loop"""

    # TODO NBNB add mechanism for loading all NmrResidues with reserved names first,
    # to ensure the can be set to the correct serial whenever possible

    creatorFunc = parent.newChemicalShift

    mapping = nef2CcpnMap[loop.name]
    map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
    for row in loop.data:
      parameters = self._parametersFromLoopRow(row, map2)
      nmrResidue = self.produceNmrResidue(chainCode=row.get('chain_code'),
                                          sequenceCode=row.get('sequence_code'),
                                          residueType=row.get('residue_type'))
      nmrAtom = self.produceNmrAtom(nmrResidue, row.get('atom_name'))

      parameters['nmrAtom'] = nmrAtom
      creatorFunc(**parameters)
  #
  importers['nef_chemical_shift'] = load_nef_chemical_shift


# saveFrameOrder = [
#   DONE 'nef_nmr_meta_data',
#   'nef_molecular_system',
#   DONE 'nef_chemical_shift_list',
#   'nef_distance_restraint_list',
#   'nef_dihedral_restraint_list',
#   'nef_rdc_restraint_list',
#   'nef_nmr_spectrum',
#   'nef_peak_restraint_links',
#   'ccpn_spectrum_group',
#   'ccpn_sample',
#   'ccpn_substance',
#   'ccpn_assignments',
#   'ccpn_dataset',
#   'ccpn_restraint_list',
#   'ccpn_notes',
# ]

  def _parametersFromSaveFrame(self, saveFrame, mapping):

    # Get attributes that have a simple tag mapping, and make a separate loop list
    parameters = {}
    loopNames = []
    for tag, ccpnTag in mapping.items():
      if ccpnTag == _isALoop:
        loopNames.append(tag)
      elif ccpnTag and '.' not in ccpnTag:
        val = saveFrame.get(tag)
        if val is not None:
          #necessary as tags like ccpn_serial should NOT be set if absent of None
          parameters[ccpnTag] = val
    #
    return parameters, loopNames

  def warning(self, message):
    template = "WARNING in saveFrame%s\n%s"
    self.warnings.append(template % (self.saveFrameName, message))

  def _parametersFromLoopRow(self, row, mapping):
    parameters = {}
    for tag, ccpnTag in mapping.items():
      val = row.get(tag)
      if val is not None:
        parameters[ccpnTag] = val
    #
    return parameters
  def produceNmrChain(self, chainCode:str):
    """Get NmrResidue, correcting for possible errors"""
    newChainCode = chainCode
    while True:
      try:
        nmrChain = self.project.fetchNmrChain(newChainCode)
        break
      except ValueError:
        newChainCode = '`%s`' % newChainCode
        self.warning("New NmrChain:%s name caused an error.  Renamed %s"
                     % (chainCode, newChainCode))
    #
    return nmrChain

  def produceNmrResidue(self, chainCode:str, sequenceCode:str, residueType:str=None):
    """Get NmrResidue, correcting for possible errors"""

    nmrChain = self.produceNmrChain(chainCode)

    rt = residueType or ''
    cc = nmrChain.shortName
    newSequenceCode = sequenceCode
    while True:
      try:
        nmrResidue = self.project.fetchNmrResidue(newSequenceCode, residueType)
        break
      except ValueError:
        newSequenceCode = '`%s`' % newSequenceCode
        self.warning("New NmrResidue:%s.%s.%s name caused an error.  Renamed %s.%s.%s"
                     % (cc, sequenceCode, rt, cc, newSequenceCode, cc))
    #
    return nmrResidue

  def produceNmrAtom(self, nmrResidue, name):
    """Get NmrAtom from NmrResidue and name, correcting for possible errors"""

    newName = name
    while True:
      try:
        nmrAtom = nmrResidue.fetchNmrAtom(newName)
        break
      except ValueError:
        newName = '`%s`' % newName
        self.warning("New NmrAtom:%s.%s name caused an error.  Renamed %s.%s"
                     % (nmrResidue._id, name, nmrResidue._id, newName))
    #
    return nmrAtom




  ####################################################################################
  #
  ###    NEF reader code:
  #
  ####################################################################################



def _printOutMappingDict(mappingDict):
  """Utility - print uot mapping dict for eciting and copying"""
  saveframeOrder = []
  print("# NEf to CCPN tag mapping (and tag order)")
  print("{\n")
  for category, od in mappingDict.items():
    saveframeOrder.append(category)
    print("  %s:OD((" % repr(category))
    for tag, val in od.items():
      if isinstance(val,str) or val is None:
        print("    (%s,%s)," % (repr(tag), repr(val)))
      else:
        # This must be a loop OD
        print("    (%s,OD((" % repr(tag))
        for tag2, val2 in val.items():
          print("      (%s,%s)," % (repr(tag2), repr(val2)))
        print("    ))),")
    print("  )),\n")
  print("}\n")

  print ("#SaveFrameOrder\n[")
  for tag in saveframeOrder:
    print ("  %s," %repr(tag))
  print ("]\n")


if __name__ == '__main__':
  import sys
  from ccpn.framework import Framework
  path = sys.argv[1]
  # project = core.loadProject(path)
  project = Framework.getFramework(projectPath=path).project
  if path.endswith('/'):
    path = path[:-1]
  outPath = path + '.nef'
  print ('@~@~ writing to ', outPath)
  open(outPath, 'w').write(convert2NefString(project))