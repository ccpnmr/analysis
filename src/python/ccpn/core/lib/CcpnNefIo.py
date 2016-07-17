"""Code for CCPN-specific NEF I/O

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

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
import os
import time
from collections import OrderedDict as OD
from operator import attrgetter
from typing import List, Union, Optional, Sequence
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.lib import Constants as coreConstants
from ccpn.core.lib.MoleculeLib import extraBoundAtomPairs
from ccpn.core.lib import RestraintLib
from ccpn.util import Common as commonUtil
from ccpn.util.nef import Specification
from ccpn.util.nef import StarIo
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

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
  'ccpn_integral_list',
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
    ('ccpn_dataset_serial','name'),
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
    ('ccpn_tensor_magnitude', 'tensorMagnitude'),
    ('ccpn_tensor_rhombicity', 'tensorRhombicity'),
    ('ccpn_tensor_chain_code','tensorChainCode'),
    ('ccpn_tensor_sequence_code','tensorSequenceCode'),
    ('ccpn_tensor_residue_type','tensorResidueType'),
    ('ccpn_tensor_isotropic_value', 'tensorIsotropicValue'),
    ('ccpn_serial','serial'),
    ('ccpn_dataset_serial','dataSet.serial'),
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
    ('ccpn_figure_of_merit','restraint.figureOfMerit'),
    ('ccpn_comment','restraint.comment'),
  )),

  'nef_dihedral_restraint_list':OD((
    ('potential_type','potentialType'),
    ('origin','origin'),
    ('ccpn_tensor_magnitude', 'tensorMagnitude'),
    ('ccpn_tensor_rhombicity', 'tensorRhombicity'),
    ('ccpn_tensor_chain_code','tensorChainCode'),
    ('ccpn_tensor_sequence_code','tensorSequenceCode'),
    ('ccpn_tensor_residue_type','tensorResidueType'),
    ('ccpn_tensor_isotropic_value', 'tensorIsotropicValue'),
    ('ccpn_serial','serial'),
    ('ccpn_dataset_serial','dataSet.serial'),
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
    ('name',None),
    ('ccpn_figure_of_merit','restraint.figureOfMerit'),
    ('ccpn_comment','restraint.comment'),
  )),

  'nef_rdc_restraint_list':OD((
    ('potential_type','potentialType'),
    ('origin','origin'),
    ('tensor_magnitude', 'tensorMagnitude'),
    ('tensor_rhombicity', 'tensorRhombicity'),
    ('tensor_chain_code','tensorChainCode'),
    ('tensor_sequence_code','tensorSequenceCode'),
    ('tensor_residue_type','tensorResidueType'),
    ('ccpn_tensor_isotropic_value', 'tensorIsotropicValue'),
    ('ccpn_serial','serial'),
    ('ccpn_dataset_serial','dataSet.serial'),
    ('ccpn_unit','unit'),
    ('ccpn_comment','comment'),
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
    ('ccpn_comment','restraint.comment'),
  )),

  'nef_nmr_spectrum':OD((
    ('num_dimensions','spectrum.dimensionCount'),
    ('chemical_shift_list',None),
    ('experiment_classification','spectrum.experimentType'),
    ('experiment_type','spectrum.experimentName'),
    ('ccpn_positive_contour_count','spectrum.positiveContourCount'),
    ('ccpn_positive_contour_base','spectrum.positiveContourBase'),
    ('ccpn_positive_contour_factor','spectrum.positiveContourFactor'),
    ('ccpn_positive_contour_colour','spectrum.positiveContourColour'),
    ('ccpn_negative_contour_count','spectrum.negativeContourCount'),
    ('ccpn_negative_contour_base','spectrum.negativeContourBase'),
    ('ccpn_negative_contour_factor','spectrum.negativeContourFactor'),
    ('ccpn_negative_contour_colour','spectrum.negativeContourColour'),
    ('ccpn_slice_colour','spectrum.sliceColour'),
    ('ccpn_spectrum_scale','spectrum.scale'),
    ('ccpn_spinning_rate','spectrum.spinningRate'),
    ('ccpn_spectrum_file_path','spectrum.filePath'),
    ('ccpn_peaklist_serial','serial'),
    ('ccpn_peaklist_comment','comment'),
    ('ccpn_peaklist_name','title'),
    ('ccpn_peaklist_is_simulated','isSimulated'),
    ('nef_spectrum_dimension',_isALoop),
    ('nef_spectrum_dimension_transfer',_isALoop),
    ('nef_peak',_isALoop),
    ('ccpn_spectrum_hit',_isALoop),
  )),
  'nef_spectrum_dimension':OD((
    ('dimension_id',None),
    ('axis_unit','axisUnits'),
    ('axis_code','isotopeCodes'),
    ('spectrometer_frequency','spectrometerFrequencies'),
    ('spectral_width','spectralWidths'),
    ('value_first_point',None),
    ('folding',None),
    ('absolute_peak_positions',None),
    ('is_acquisition',None),
    ('ccpn_axis_code','axisCodes'),
    ('ccpn_point_count','pointCounts'),
    ('ccpn_reference_points','referencePoints'),
    ('ccpn_total_point_count','totalPointCounts'),
    ('ccpn_point_Offset','pointOffsets'),
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

  # NB needs ccpn_serial
  'ccpn_dataset':OD((
  )),

  'ccpn_integral_list':OD((
  )),

  'ccpn_restraint_list':OD((
    ('potential_type','potentialType'),
    ('origin','origin'),
    ('tensor_magnitude', 'tensorMagnitude'),
    ('tensor_rhombicity', 'tensorRhombicity'),
    ('tensor_chain_code','tensorChainCode'),
    ('tensor_sequence_code','tensorSequenceCode'),
    ('tensor_residue_type','tensorResidueType'),
    ('tensor_isotropic_value', 'tensorIsotropicValue'),
    ('ccpn_serial','serial'),
    ('dataset_serial','serial'),
    ('name','name'),
    ('restraint_type','restraintType'),
    ('restraint_item_length','restraintItemLength'),
    ('unit','unit'),
    ('measurement_type','measurementType'),
    ('comment','comment'),
    ('ccpn_restraint',_isALoop),
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
    ('vector_length','restraint.vectorLength'),
    ('figure_of_merit','restraint.figureOfMerit'),
    ('ccpn_comment','restraint.comment'),
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

  # TODO add function to get NefReader to load mutiple projects, settings

def saveNefProject(project:'Project', path:str, overwriteExisting:bool=False,
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


def convert2NefString(project, skipPrefixes=()):
  """Convert project to NEF string"""
  converter = CcpnNefWriter(project)
  dataBlock = converter.exportProject()

  # Delete tags starting with certain prefixes.
  # NB designed to strip out 'ccpn' tags to make output comaprison easier
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
              for looptag in list(val.columns):
                if looptag.startswith(prefix):
                  val.removeColumn(looptag, removeData=True)

  return dataBlock.toString()

class CcpnNefWriter:
  """CCPN NEF reader/writer"""

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
    singleDataSet = bool(restraintLists) and len(set(x.dataSet for x in restraintLists)) == 1
    for obj in restraintLists:
      saveFrames.append(self.restraintList2Nef(obj, singleDataSet=singleDataSet))

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

  def restraintList2Nef(self, restraintList, singleDataSet=False) -> StarIo.NmrSaveFrame:
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

    name = restraintList.name
    if not singleDataSet:
      # If there are multiple DataSets, add the dataSet serial for disambiguation
      name = '`%s`%s' % (restraintList.dataSet.serial, name)

    result = self._newNefSaveFrame(restraintList, category, name)

    self.ccpn2SaveFrameName[restraintList] = result['sf_framecode']

    if category in ('nef_rdc_restraint_list', 'ccpn_restraint_list'):
      tensor = restraintList.tensor
      if tensor is not None:
        result['tensor_magnitude'] = tensor.axial or None
        result['tensor_rhombicity'] = tensor.rhombic or None
        result['ccpn_tensor_isotropic_value'] = tensor.isotropic or None


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
        if category == 'nef_dihedral_restraint_list':
          row['name'] = RestraintLib.dihedralName(project, item)
    #
    return result

  def spectrum2Nef(self, spectrum:'ccpn.Spectrum') -> StarIo.NmrSaveFrame:
    """Convert spectrum to NEF saveframes - one per peaklist

    Will crate a peakList if none are present"""

    result = []

    peakLists = spectrum.peakLists
    if not peakLists:
      peakLists = [spectrum.newPeakList()]

    for peakList in peakLists:
      result.append(self.peakList2Nef(peakList))
    #
    return result

  def peakList2Nef(self, peakList:'ccpn.peakList',
                   exportCompleteSpectrum=False) -> StarIo.NmrSaveFrame:
    """Convert PeakList to CCPN NEF saveframe
    """

    spectrum = peakList.spectrum

    # frameCode for saveFrame that holds spectrum adn first peaklist.
    # If not None, the peakList will be read into that specttum
    spectrumAlreadySaved =  bool(self.ccpn2SaveFrameName.get(spectrum))

    # We do not support sampled or unprocessed dimensions yet. NBNB TBD.
    if any (x != 'Frequency' for x in spectrum.dimensionTypes):
      raise NotImplementedError(
        "NEF only implemented for processed frequency spectra, dimension types were: %s"
        % spectrum.dimensionTypes
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

    self.ccpn2SaveFrameName[peakList] = result['sf_framecode']
    if not spectrumAlreadySaved:
      self.ccpn2SaveFrameName[spectrum] = result['sf_framecode']

    result['chemical_shift_list'] = self.ccpn2SaveFrameName.get(peakList.chemicalShiftList)


    # NBNB TBD FIXME assumes ppm unit and Frequency dimensions for now
    # WIll give wrong values for Hz or pointNumber units, and
    # WIll fill in all None for non-Frequency dimensions
    loopName = 'nef_spectrum_dimension'
    loop = result[loopName]
    data = OD()
    for neftag,attrstring in nef2CcpnMap[loopName].items():
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
      columns = ('nmr_spectrum_id', 'peak_id', 'restraint_list_id', 'restraint_id', )
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

    loopName = 'ccpn_substance_synonym'
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
    for tag in saveFrameOrder:
      if tag in dd:
        ll = dd.pop(tag)
        result.extend(ll)
    if dd:
      raise ValueError("Unknown saveframe types in export: %s" % list(dd.keys()))
    #
    return result

  def _loopRowData(self, loopName:str, wrapperObj:AbstractWrapperObject) -> dict:
    """Fill in a loop row data dictionary from master mapping and wrapperObj.
    Unmapped data to be added afterwards"""

    rowdata = {}
    for neftag,attrstring in nef2CcpnMap[loopName].items():
      if attrstring is not None:
        rowdata[neftag] = attrgetter(attrstring)(wrapperObj)
    return rowdata

  def _newNefSaveFrame(self, wrapperObj:AbstractWrapperObject,
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
        assert itemvalue == _isALoop, "Invalid item specifier in Nef2CcpnMap: %s" % (itemvalue,)
        result.newLoop(tag, nef2CcpnMap[tag])
    #
    return result



  ####################################################################################
  #
  ###    NEF reader code:
  #
  ####################################################################################


class CcpnNefReader:

  # Importer functions - used for converting saveframes and loops
  importers = {}

  def __init__(self, application, specificationFile=None, mode='standard',
               testing=False):

    self.application = application
    self.mode=mode
    self.saveFrameName = None
    self.warnings = []
    self.errors = []
    self.testing = testing

    # Map for resolving crosslinks in NEF file
    self.frameCode2Object = {}

    self.defaultDataSetSerial = None
    self.defaultNmrChain = None
    self.mainDataSetSerial = None


  def getNefData(self, path):
    """Get NEF data structure from file"""
    nmrDataExtent = StarIo.parseNefFile(path)
    dataBlocks = list(nmrDataExtent.values())
    dataBlock = dataBlocks[0]
    #
    return dataBlock

  # def loadNewProject(self, path:str):
  #   """Load NEF file at path into project"""
  #
  #   dataBlock = self.getNefData(path)
  #   project = self.application.newProject(dataBlock.name)
  #   self.application._echoBlocking += 1
  #   self.application.project._undo.increaseBlocking()
  #   try:
  #     self.importNewProject(project, dataBlock)
  #   finally:
  #     self.application._echoBlocking -= 1
  #     self.application.project._undo.decreaseBlocking()
  #
  #   #
  #   return project

  def importNewProject(self, project:Project, dataBlock:StarIo.NmrDataBlock,
                       projectIsEmpty=True):
    """Import entire project from dataBlock into empty Project"""


    # TODO Add error handling
    # TODO Add provision for out-of-order files (we assume correct order, e.g. for crosslinks)

    self.warnings = []

    self.project = project

    metaDataFrame = dataBlock['nef_nmr_meta_data']

    self.saveFrameName = 'nef_nmr_meta_data'
    self.load_nef_nmr_meta_data(project, metaDataFrame)

    # Preload certain saveframes
    for saveFrameName, saveFrame in dataBlock.items():

      sf_category = saveFrame.get('sf_category')

      if sf_category == 'ccpn_dataset':
        # Must be preloaded to make sure the serial numbers are used correctly
        serial = saveFrame['ccpn_serial']
        if serial is None:
          # Error. Should never happen. TODO handle it
          pass
        else:
          dataSet = self.project.newDataSet(serial=serial)

    extraCategories = []

    for saveFrameName, saveFrame in dataBlock.items():
      # TODO NBNB this assumes we get them in the right order. Reconsider later

      if saveFrameName == 'nef_nmr_meta_data':
        # Done already
        continue

      self.saveFrameName = saveFrameName

      sf_category = saveFrame.get('sf_category')
      importer = self.importers.get(sf_category)
      if importer is None:
        print ("WARNING, unknown saveframe category", sf_category)
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
          # ues newObject here

    # Put metadata in main dataset
    self.updateMetaData(metaDataFrame)

    for msg in self.warnings:
      print ('====> ', msg)
    self.project = None


  def load_nef_nmr_meta_data(self, project, saveFrame):
    """load nef_nmr_meta_data saveFrame"""

    # Other data are read in here at the end of the load
    self.mainDataSetSerial = saveFrame.get('ccpn_dataset_serial')

    return None

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
        loop = saveFrame.get(tag)
        if loop:
          importer = self.importers[tag]
          importer(self, project, loop)
    #
    return None
  #
  importers['nef_molecular_system'] = load_nef_molecular_system


  def load_nef_sequence(self, project, loop):
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
        newSubstance = project.fetchNefSubstance(sequence=rows, name=compoundName)
        newChain = newSubstance.createChain(shortName=chainCode, role=role,
                                            comment=comment)
        sequence2Chain[sequence] = newChain
      else:
        newChain = lastChain.substance.createChain(shortName=chainCode, role=role,
                                                   comment=comment)
      #
      result.append(newChain)

      # Add Residue comments
      for ii, apiResidue in enumerate(newChain._wrappedData.sortedResidues()):
        # WE must do this at the API level to be sure we get the Residues in the
        # input order rather than in sorted order
        comment = rows[ii].get('ccpn_comment')
        if comment:
          apiResidue.details = comment
    #
    return result
  #
  importers['nef_sequence'] = load_nef_sequence


  def load_nef_covalent_links(self, project, loop):
    """Load nef_sequence loop"""

    result = []

    for row in loop.data:
      id1 = Pid.createId(row[x] for x in ('chain_code_1', 'sequence_code_1',
                                           'residue_type_1', 'atom_name_1', ))
      id2 = Pid.createId(row[x] for x in ('chain_code_2', 'sequence_code_2',
                                           'residue_type_2', 'atom_name_2', ))
      atom1 = project.getAtom(id1)
      atom2 = project.getAtom(id2)
      if atom1 is None or atom2 is None:
        self.warning("Unknown atom for bond  %s - %s Skipping..." % (id1, id2))
      else:
        result.append((atom1, atom2))
        atom1.addInterAtomBond(atom2)
    #
    return result
  #
  importers['nef_covalent_links'] = load_nef_covalent_links



  def load_nef_chemical_shift_list(self, project, saveFrame):
    """load nef_chemical_shift_list saveFrame"""

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]

    parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)

    parameters['name'] = framecode[len(category) + 1:]

    # Make main object
    result = project.newChemicalShiftList(**parameters)

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

  def load_nef_chemical_shift(self, parent, loop):
    """load nef_chemical_shift loop"""

    # TODO NBNB add mechanism for loading all NmrResidues with reserved names first,
    # to ensure the can be set to the correct serial whenever possible

    result = []

    creatorFunc = parent.newChemicalShift

    mapping = nef2CcpnMap[loop.name]
    map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
    for row in loop.data:
      parameters = self._parametersFromLoopRow(row, map2)
      try:
        tt = tuple(row.get(tag) for tag in ('chain_code', 'sequence_code', 'residue_type',
                                            'atom_name'))
        nmrResidue = self.produceNmrResidue(*tt[:3])
        nmrAtom = self.produceNmrAtom(nmrResidue, tt[3])
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

  def load_nef_restraint_list(self, project, saveFrame):
    """Serves to load nef_distance_restraint_list, nef_dihedral_restraint_list,
     nef_rdc_restraint_list and ccpn_restraint_list"""

    # Get ccpn-to-nef mappping for saveframe
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
      restraintType = saveFrame.get('restraintType')
      if not restraintType:
        self.warning("Missing restraintType  %s for saveFrame %s" %
                     (restraintType, framecode))
        return
    parameters['restraintType'] = restraintType
    namePrefix = restraintType[:3].capitalize() + '-'

    # Get name from frameCode, add typ e disambiguation, and correct for ccpn dataSetSerial addition
    name = framecode[len(category) + 1:]
    if not name.startswith(namePrefix):
      # Add prefix for disambiguation since NEF but NOT CCPN has separate namespaces
      # for different constraint types
      if not restraintType.lower() in name.lower():
        name = namePrefix + name
    dataSetSerial = saveFrame.get('ccpn_dataset_serial')
    if dataSetSerial is not None:
      ss = '`%s`' % dataSetSerial
      if name.startswith(ss):
        name = name[len(ss):]
    parameters['name'] = name

    # Make main object
    dataSet = self.fetchDataSet(dataSetSerial)
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

  def load_nef_restraint(self, restraintList, loop, itemLength=None):
    """Serves to load nef_distance_restraint, nef_dihedral_restraint,
     nef_rdc_restraint and ccpn_restraint loops"""

    # NB Restraint.name - written out for dihedral restraints - is not read.
    # Which is probably OK, it is derived from the atoms.

    result = []

    # set itemLength if not passed in:
    if not itemLength:
      itemLength = coreConstants.constraintListType2ItemLength.get(restraintList.restraintType)

    mapping = nef2CcpnMap[loop.name]
    map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
    restraints = {}
    restraintContributions = {}
    assignTags = ('chain_code', 'sequence_code', 'residue_type', 'atom_name')
    for row in loop.data:

      # get or make restraint
      serial = row.get('restraint_id')
      restraint = restraints.get(serial)
      # TODO check that row matches restraint values
      # - as it is we use first appearance only
      if restraint is None:
        dd = {'serial':serial}
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
      parameters = self._parametersFromLoopRow(row, map2)
      combinationId = parameters.get('combinationId')
      contribution = restraintContributions.get((serial, combinationId))
      # TODO check that row matches contribution values
      # - as it is we use first appearance only
      if not contribution:
        contribution = restraint.newRestraintContribution(**parameters)
        restraintContributions[(serial, combinationId)] = contribution

      # Add item
      ll = [row._get(tag)[:itemLength] for tag in assignTags]
      idStrings = []
      for item in zip(*ll):
        idStrings.append(Pid.IDSEP.join(('' if x is None else str(x)) for x in item))
      try:
        contribution.addRestraintItem(idStrings)
      except ValueError:
        self.warning("Cannot Add restraintItem %s. Identical to previous. Skipping" % idStrings)

    #
    return result
  #
  importers['nef_distance_restraint'] = load_nef_restraint
  importers['nef_dihedral_restraint'] = load_nef_restraint
  importers['nef_rdc_restraint'] = load_nef_restraint
  importers['ccpn_restraint'] = load_nef_restraint

  def load_nef_nmr_spectrum(self, project, saveFrame):

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]


    # Get peakList parameters and make peakList
    peakListParameters, dummy = self._parametersFromSaveFrame(saveFrame, mapping)

    # Get spectrum parameters
    spectrumParameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping,
                                                                  ccpnPrefix='spectrum')
    # Get name from spectrum parameters, or from the frameCode
    spectrumName = framecode[len(category) + 1:]
    peakListSerial = peakListParameters.get('serial')
    if peakListSerial:
      ss = '`%s`' % peakListSerial
      # Remove peakList serial suffix (which was added for disambiguation)
      # So that multiple pealkLists all go to one Spectrum
      if spectrumName.endswith(ss):
        spectrumName = spectrumName[:-len(ss)]

    shiftListFrameCode = saveFrame.get('chemical_shift_list')
    if shiftListFrameCode:
      spectrumParameters['chemicalShiftList'] = self.frameCode2Object[shiftListFrameCode]

    # get per-dimension data - NB these are mandatory and cannot be worked around
    dimensionData = self.read_nef_spectrum_dimension(project,
                                                     saveFrame['nef_spectrum_dimension'])

    spectrum = produceSpectrum(project, spectrumName, spectrumParameters, dimensionData)

    # read and incorporate dimension transfer data - better to get spectrum fully ready first
    loopName = 'nef_spectrum_dimension_transfer'
    # Those are treated elsewhere
    loop = saveFrame.get(loopName)
    if loop:
      importer = self.importers[loopName]
      importer(self, spectrum, loop)

    if not dimensionData.get('axisCodes:'):
      # Set CCPN Hn/Nh (etc.) axis codes if not read in
      # Must be done after nef_spectrum_dimension_transfer is read
      self.adjustAxisCodes(spectrum, dimensionData)
    # Make PeakLst
    peakList = spectrum.newPeakList(**peakListParameters)
    # Load peaks
    self.load_nef_peak(peakList, saveFrame.get('nef_peak'))

    # Load remaining loops, with spectrum as parent
    for loopName in loopNames:
      if loopName not in  ('nef_spectrum_dimension', 'nef_peak',
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


  def load_nef_spectrum_dimension_transfer(self, spectrum, loop):

    transferTypes = ('onebond', 'Jcoupling', 'Jmultibond', 'relayed', 'through-space',
                     'relayed-alternate')

    if loop:
      apiExperiment = spectrum._wrappedData.experiment

      data = loop.data
      # Remove invalid data rows
      dataLists = []
      for row in data:
        ll = [row.get(tag) for tag in ('dimension_1', 'dimension_2', 'transfer_type',
                                       'is_indirect')]
        if (apiExperiment.findFirstExpDim(dim=row['dimension_1']) is None or
            apiExperiment.findFirstExpDim(dim=row['dimension_2']) is None or
            row['transfer_type'] not in transferTypes):
          self.warning("Illegal values in nef_spectrum_dimension_transfer: %s"
                       % list(row.values()))
        else:
          dataLists.append(ll)

      # Store expTransfers in API as we can not be sure we will get a refExperiment
      for ll in dataLists:
        expDimRefs = []
        for dim in ll[:2]:
          expDim = apiExperiment.findFirstExpDim(dim=dim)
          # After spectrum creation there will be one :
          expDimRefs.append(expDim.sortedExpDimRefs()[0])
        if apiExperiment.findFirstExpTransfer(expDimRefs=expDimRefs) is None:
          xx = apiExperiment.newExpTransfer(expDimRefs=expDimRefs, transferType=ll[2],
                                       isDirect=not ll[3])
        else:
          self.warning("Duplicate nef_spectrum_dimension_transfer: %s" % (ll,))
  #
  importers['nef_spectrum_dimension_transfer'] = load_nef_spectrum_dimension_transfer

  def adjustAxisCodes(self, spectrum, dimensionData):

      pass
      #print ('@~@~ CCPN data. Still TODO')

      # # Use data to rename axisCodes
      # axisCodes = spectrum.axisCodes
      # newCodes = list(axisCodes)
      # atomTypes = [commonUtil.splitIntFromChars(x)[1] for x in spectrum.isotopeCodes]
      # acquisitionAxisCode = spectrum.acquisitionAxisCode
      # if acquisitionAxisCode is not None:
      #   acquisitionDim = axisCodes.index(acquisitionAxisCode) + 1
      #   if acquisitionAxisCode == atomTypes[acquisitionDim - 1]:
      #     # this axisCode needs improvement
      #     for pair in oneBondPairs:
      #       # First do acquisition dimension
      #       if acquisitionDim in pair:
      #         ll = pair.copy()
      #         ll.remove(acquisitionDim)
      #         otherDim = ll[0]
      #         otherCode = axisCodes[otherDim - 1]
      #         if otherCode == atomTypes[otherDim - 1]:






  def read_nef_spectrum_dimension(self, project, loop):
    """Read nef_spectrum_dimension loop and convert data to a dictionary
    of ccpnTag:[per-dimension-value]"""

    # TODO Add more ccpn-specific data

    # NB we are not using absolute_peak_positions - if false what could we do?

    result = {}
    nefTag2ccpnTag = nef2CcpnMap['nef_spectrum_dimension']

    rows = [(row['dimension_id'], row) for row in loop.data]
    rows = [tt[1] for tt in sorted(rows)]

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
    # Not needed further on.
    del result['dimension_id']
    #
    return result


  def load_nef_peak(self, peakList, loop):
    """Serves to load nef_peak loop"""

    result = []

    dimensionCount = peakList.spectrum.dimensionCount

    mapping = nef2CcpnMap[loop.name]
    map2 = dict(item for item in mapping.items() if item[1] and '.' not in item[1])
    peaks = {}
    for row in loop.data:

      parameters = self._parametersFromLoopRow(row, map2)

      # get or make peak
      serial = parameters['serial']
      peak = peaks.get(serial)
      # TODO check if peak parameters are teh same fora all rows, and do something about it
      # For now wee simply use the first row that appears
      if peak is None:
        parameters['position'] = row._get('position')[:dimensionCount]
        parameters['positionError'] = row._get('position_uncertainty')[:dimensionCount]
        peak = peakList.newPeak(**parameters)
        peaks[serial] = peak
        result.append(peak)

      # Add assignment
      chainCodes = row._get('chain_code')[:dimensionCount]
      sequenceCodes = row._get('sequence_code')[:dimensionCount]
      residueTypes = row._get('residue_type')[:dimensionCount]
      atomNames = row._get('atom_name')[:dimensionCount]
      assignments = zip(chainCodes, sequenceCodes, residueTypes, atomNames)
      nmrAtoms = []
      for tt in assignments:
        if all(x is None for x in tt):
          # No assignment
          nmrAtoms.append(None)
        elif tt[1] and tt[3]:
          # Enough for an assignment - make it
          nmrResidue = self.produceNmrResidue(*tt[:3])
          nmrAtom = self.produceNmrAtom(nmrResidue, tt[3])
          nmrAtoms.append(nmrAtom)
        else:
          # partial and unusable assignment
          self.warning("Uninterpretable Peak assignment for peak %s: %s. Set to None"
                       % (peak.serial, tt))
          nmrAtoms.append(None)
      else:
        peak.addAssignment(nmrAtoms)
    #
    return result
  #
  importers['nef_peak'] = load_nef_peak


  def load_nef_peak_restraint_links(self, project, saveFrame):
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


  def load_nef_peak_restraint_link(self, project, loop):
    """Load nef_peak_restraint_link loop"""

    links = {}

    # NBNB TODO. There was a very strange bug in this function
    # When I was using PeakList.getPeak(str(serial))
    # and RestraintList.getRestraint(str(serial), peaks and restraints were
    # sometimes missed even though teh data were present.
    # Doing the test at tge API level (as now) fixed the problem
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


  def load_ccpn_spectrum_group(self, project, saveFrame):

    print ("ccpn_spectrum_group reading is not implemented yet")

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]
  #
  importers['ccpn_spectrum_group'] = load_ccpn_spectrum_group


  def load_ccpn_sample(self, project, saveFrame):

    print ("ccpn_sample reading is not implemented yet")

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]
  #
  importers['ccpn_sample'] = load_ccpn_sample


  def load_ccpn_substance(self, project, saveFrame):

    print ("ccpn_substance reading is not implemented yet")

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]
  #
  importers['ccpn_substance'] = load_ccpn_substance


  def load_ccpn_assignments(self, project, saveFrame):

    print ("ccpn_assignments reading is not implemented yet")

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]
  #
  importers['ccpn_assignments'] = load_ccpn_assignments


  def load_ccpn_notes(self, project, saveFrame):

    print ("ccpn_notes reading is not implemented yet")

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]
  #
  importers['ccpn_notes'] = load_ccpn_notes


  def load_ccpn_integral_list(self, project, saveFrame):

    print ("ccpn_integral_list reading is not implemented yet")

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]
  #
  importers['ccpn_integral_list'] = load_ccpn_integral_list


  def load_ccpn_dataset(self, project, saveFrame):

    print ("ccpn_dataset reading is not implemented yet")

    # Get ccpn-to-nef mappping for saveframe
    category = saveFrame['sf_category']
    framecode = saveFrame['sf_framecode']
    mapping = nef2CcpnMap[category]
  #
  importers['ccpn_dataset'] = load_ccpn_dataset


  def _parametersFromSaveFrame(self, saveFrame, mapping, ccpnPrefix=None):

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
          parts = ccpnTag.split('.')
          if len(parts) == 2 and parts[0] == ccpnPrefix:
            val = saveFrame.get(tag)
            if val is not None:
              # necessary as tags like ccpn_serial should NOT be set if absent of None
              parameters[parts[1]] = val

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

  def produceNmrChain(self, chainCode:str=None):
    """Get NmrChain, correcting for possible errors"""

    if chainCode is None:
        chainCode = coreConstants.defaultNmrChainCode
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

  def produceNmrResidue(self, chainCode:str=None, sequenceCode:str=None, residueType:str=None):
    """Get NmrResidue, correcting for possible errors"""

    if not sequenceCode:
      raise ValueError("Cannot produce NmrResidue for sequenceCode: %s" % repr(sequenceCode))

    nmrChain = self.produceNmrChain(chainCode)

    rt = residueType or ''
    cc = nmrChain.shortName
    newSequenceCode = sequenceCode
    while True:
      try:
        nmrResidue = nmrChain.fetchNmrResidue(newSequenceCode, residueType)
        break
      except ValueError:
        newSequenceCode = '`%s`' % newSequenceCode
        self.warning("New NmrResidue:%s.%s.%s name caused an error.  Renamed %s.%s.%s"
                     % (cc, sequenceCode, rt, cc, newSequenceCode, rt))
    #
    return nmrResidue

  def produceNmrAtom(self, nmrResidue, name):
    """Get NmrAtom from NmrResidue and name, correcting for possible errors"""

    if not name:
      raise ValueError("Cannot produce Nmratom for atom name: %s" % repr(name))

    newName = name
    while True:
      try:
        nmrAtom = nmrResidue.fetchNmrAtom(newName)
        break
      except ValueError:
        raise
        newName = '`%s`' % newName
        self.warning("New NmrAtom:%s.%s name caused an error.  Renamed %s.%s"
                     % (nmrResidue._id, name, nmrResidue._id, newName))
    #
    return nmrAtom

  def updateMetaData(self, metaDataFrame):
    """Add meta information to main data set. Must be done at end of read"""
    dataSet = self.fetchDataSet(self.mainDataSetSerial)
    self.mainDataSetSerial = None

  def fetchDataSet(self, serial=None):
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
      dataSet.title = 'Data_%s' % serial
      self.defaultDataSetSerial = serial

    else:
      # take or create dataset matching serial
      dataSet = self.project.getDataSet(str(serial))
      if dataSet is None:
        dataSet = self.project.newDataSet(serial=serial)
        dataSet.title = 'Data_%s' % serial
    #
    return dataSet


def produceSpectrum(project:'Project', spectrumName:str, spectrumParameters:dict,
                    dimensionData:dict):
  """Get or create spectrum using dictionaries of attributes, such as read in from NEF.

  :param spectrumParameters keyword-value dictionary of attribute to set on resulting spectrum

  :params Dictionary of keyword:list parameters, with per-dimension parameters.
  Either 'axisCodes' or 'isotopeCodes' must be present and fully populated.
  A number of other dimensionData are
  treated specially (see below)
  """


  dimTags = list(dimensionData.keys())

  spectrum = project.getSpectrum(spectrumName)
  if spectrum is None:
    # Spectrum did not already exist

    # First try to load it - we override the loaded attribute values below
    # but loading gives a more complete parameter set.
    spectrum = None
    filePath = spectrumParameters.get('filePath')
    if filePath and os.path.exists(filePath):
      try:
        dataType, subType, usePath = ioFormats.analyseUrl(path)
        if dataType == 'Spectrum':
          spectra = project.loadSpectrum(usePath, subType)
          if spectra:
            spectrum = spectra[0]
      except:
        # Deliberate - any error should be skipped
        pass
      if spectrum is None:
        project._logger.warning("Failed to load spectrum from spectrum path %s" % filePath)
      elif 'axisCodes' in dimensionData:
          # get axisCodes
          spectrum.axisCodes = dimensionData['axisCodes']

    if spectrum is None:
      # Spectrum could not be loaded - now create a dummy spectrum
      if 'axisCodes' in dimTags:
        dimTags.remove('axisCodes')
        axisCodes = dimensionData['axisCodes']

      else:
        # axisCodes were not set - produce a serviceable set
        axisCodes = []
        for isotopeCode in dimensionData['isotopeCodes']:
          ss = axisCode = commonUtil.splitIntFromChars(isotopeCode)[1]
          ii = 0
          while axisCode in axisCodes:
            ii += 1
            axisCode = ss + str(ii)
          axisCodes.append(axisCode)

      # make new spectrum with default parameters
      spectrum = project.createDummySpectrum(axisCodes, spectrumName)

      # Delete autocreated peaklist  and reset - we want any read-in peakList to be the first
      # If necessary an empty PeakList is added downstream
      spectrum.peakLists[0].delete()
      spectrum._wrappedData.__dict__['_serialDict']['peakLists'] = 0

    # (Re)set all spectrum attributes

    # First per-dimension ones
    if 'absolute_peak_positions' in dimensionData:
      # NB We are not using these. What could we do with them?
      dimTags.remove('absolute_peak_positions')
    if 'is_acquisition' in dimensionData:
      dimTags.remove('is_acquisition')
      values = dimensionData['is_acquisition']
      if values.count(True) == 1:
        ii = values.index(True)
        spectrum.acquisitionAxisCode = axisCodes[ii]
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
      vals = [x if x is not None else oldVals[ii] for ii,x in enumerate(vals)]
      setattr(spectrum, tag, vals)

    # Set referencing.
    value_first_point = dimensionData.get('value_first_point')
    if value_first_point is not None:
      referencePoints = dimensionData.get('referencePoints')
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
            refVal -= ((refPoint-1) * sw[ii] / pointCounts[ii])
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


def _printOutMappingDict(mappingDict):
  """Utility - print out mapping dict for editing and copying"""
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

def _testTextIo(path):

  from ccpn.framework.Framework import getFramework

  path = os.path.normpath(os.path.abspath(path))

  if path.endswith('.nef'):
    outPath = path[:-4] + '.out.nef'
  else:
    raise ValueError("File name does not end in '.nef': %s" % path)

  time1 = time.time()
  application = getFramework()
  application.nefReader.testing = True
  application.loadProject(path)

  project = application.project
  time2 = time.time()
  print ("====> Loaded %s from NEF file in seconds %s" % (project.name, time2-time1))
  saveNefProject(project, outPath, overwriteExisting=True, skipPrefixes=('ccpn',))
  time3 = time.time()
  print ("====> Saved  %s  to  NEF file in seconds %s" % (project.name, time3-time2))


if __name__ == '__main__':
  import sys
  path = sys.argv[1]
  _testTextIo(path)