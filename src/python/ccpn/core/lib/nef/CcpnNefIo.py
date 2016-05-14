"""Code for CCPN-specific NEF I/O

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

# CCPN-NEF mapping:
#
# Eventually this should probably be moved to the NEF specification files.
# Pending agreement on how io integrate it there, we leave it here:
#
# The data structure is made of nested orderedDicts:
# {savefremeName:{loopName:{itemName:ccpnAttributeExpression}}}
# Order is the recommended writing order.
# loopName is NOne for items directly inside teh saveFrame.
# The ccpnAttributeExpression is a string with dots that gives you the relevant attribute
# starting form he object matching the saveeframe or loop row, as passed to operator.attrgetter.
# Where this is not possible, the expression is left as None.
# FOr 'list' attributes, such as Peak.position, the mapping isi given only of position_1
# and is left as None for the rest.
# The code must determine how many of the attributes (up to e.g. Peak.position_15) to include

import random
from collections import OrderedDict as OD
from operator import attrgetter
from typing import List, Union, Optional, Sequence

from ccpn.core.lib import Version

from ccpn.core.lib.nef import Specification
from ccpn.core.lib.nef import StarIo
from ccpn.util import Common as commonUtil

# Max value used for random integer. Set to be expressible as a signed 32-bit integer.
maxRandomInt =  2000000000

# Saveframe map for generic restraint - later modified for the official versions
_RestraintListMap = OD((
  ('potential_type','potentialType'),
  ('origin', 'origin'),
  ('tensor_magnitude', None),
  ('tensor_rhombicity', None),
  ('tensor_chain_code', 'tensorChainCode'),
  ('tensor_sequence_code', 'tensorSequenceCode'),
  ('tensor_residue_type', 'tensorResidueType'),
  ('ccpn_serial', 'serial'),
  ('ccpn_name', 'name'),
  ('ccpn_restraint_type', 'restraintType'),
  ('ccpn_restraint_item_length', 'restraintItemLength'),
  ('ccpn_unit', 'unit'),
  ('ccpn_measurement_type', 'measurementType'),
  ('ccpn_comment', 'comment'),
  ('ccpn_tensor_isotropic_value', None),
))

# Restraint loop columns for generic restraint - abridged for the official versions
_RestraintColumns = OD((                   # Matching class: RestraintContribution
  ('ordinal', None), ('restraint_id', 'restraint.serial'),
  ('restraint_combination_id', 'combinationId'),
  ('chain_code_1', None), ('sequence_code_1', None), ('residue_type_1', None), ('atom_name_1',None),
  ('chain_code_2', None), ('sequence_code_2', None), ('residue_type_2', None), ('atom_name_2',None),
  ('chain_code_3', None), ('sequence_code_3', None), ('residue_type_3', None), ('atom_name_3',None),
  ('chain_code_4', None), ('sequence_code_4', None), ('residue_type_4', None), ('atom_name_4',None),
  ('weight', 'weight'), ('target_value', 'targetValue'), ('target_value_uncertainty', 'error'),
  ('lower_linear_limit', 'additionalLowerLimit'), ('lower_limit', 'lowerLimit'),
  ('upper_limit', 'upperLimit'), ('upper_linear_limit', 'additionalUpperLimit'),
  ('scale', 'scale'), ('distance_dependent', 'isDistanceDependent'),
  ('name', None),
  ('ccpn_vector_length', 'restraint.vectorLength'),
  ('ccpn_figure_of_merit', 'restraint.figureOfMerit')
))

# NEF supported restraint list maps:

_removeCcpnItems = ('ccpn_restraint_type', 'ccpn_restraint_item_length', 'ccpn_measurement_type')
_removeRdcColumns = ('ccpn_vector_length', )
_removeDihedralColumns = ('name', )

# Distance restraint list Map
_DistanceRestraintListMap = OD(tt for tt in _RestraintListMap.items()
                               if not 'tensor' in tt[0] and tt[0] not in _removeCcpnItems)
columns = OD(tt for tt in _RestraintColumns.items()
             if tt[0][-2:] not in ('_3', '_4')
             and tt[0] not in (_removeRdcColumns + _removeDihedralColumns))
_DistanceRestraintListMap['nef_distance_restraint'] = columns

# Dihedral restraint list Map
_DihedralRestraintListMap = OD(tt for tt in _RestraintListMap.items()
                               if not 'tensor' in tt[0])
for tag in _removeCcpnItems:
  del _DihedralRestraintListMap[tag]
columns = OD(tt for tt in _RestraintColumns.items() if tt[0] not in _removeRdcColumns)
_DihedralRestraintListMap['nef_dihedral_restraint'] = columns

# Rdc restraint list Map
_RdcRestraintListMap = _RestraintListMap.copy()
for tag in _removeCcpnItems:
  del _RdcRestraintListMap[tag]
columns = OD(tt for tt in _RestraintColumns.items() if tt[0][-2:] not in ('_3', '_4')
             and tt[0] not in _removeDihedralColumns)
_RdcRestraintListMap['nef_rdc_restraint'] = columns

_RestraintListMap['ccpn_restraint'] = _RestraintColumns


def convert2NefString(project):
  """Convert project ot NEF string"""
  converter = CcpnNefIo(project)
  dataBlock = converter.exportProject()
  return dataBlock.toString()

class CcpnNefIo:
  """CCPN NEF reader/writer"""

  # Saveframes in output order with contained items and loops
  # End-of-line comments show the CCPN object(s) providing the data
  # String item values is a navigation expression to get item value from top l;evel object
  # List item values is the list of columns for a loop.
  Nef2CcpnMap = OD((

    ('nef_nmr_meta_data', OD((                   # Singleton Metadata - from Project or DataSet
      ('format_name', None),
      ('format_version', None),
      ('program_name', None),
      ('program_version', None),
      ('creation_date', None),
      ('uuid', None),
      ('coordinate_file_name', None),
      ('ccpn_dataset_name', 'name'),
      ('ccpn_dataset_comment', None),
      ('nef_related_entries', OD((                         # No Matching class
        ('database_name', None), ('database_accession_code', None),
      ))),
      ('nef_program_script', OD((                          # No Matching class
        ('program_name', None), ('script_name', None), ('script', None),
      ))),
      ('nef_run_history', OD((                             # Matching class: CalculationStep
        ('run_ordinal', 'serial'), ('program_name', 'programName'),
        ('program_version', 'programVersion'),
        ('script_name', 'scriptName'), ('script', 'script'),
        ('ccpn_input_uuid', 'inputDataUuid'), ('ccpn_output_uuid', 'outputDataUuid'),
      ))),
    ))),

    ('nef_molecular_system', OD((                # Singleton (Chains)
      ('nef_sequence', OD((                               # Matching class: Residue
        ('chain_code', 'chain.shortName'), ('sequence_code', 'sequenceCode'),
        ('residue_type', 'residueType'),
        ('linking', 'linking'), ('residue_variant', 'residueVariant'),
       ))),
      ('nef_covalent_links', OD((               # Matching class : Bond
        ('chain_code_1', None), ('sequence_code_1', None),
        ('residue_type_1', None), ('atom_name_1', None),
        ('chain_code_2', None), ('sequence_code_2', None),
        ('residue_type_2', None), ('atom_name_2', None),
        ('ccpn_bond_type', 'bondType'),
      ))),
    ))),

    ('nef_chemical_shift_list', OD((             # Matching class: ChemicalShiftList
      ('atom_chemical_shift_units', 'unit'),
      ('ccpn_serial', 'serial'),
      ('ccpn_name', 'name'),
      ('ccpn_autoUpdate', 'autoUpdate'),
      ('ccpn_isSimulated', 'isSimulated'),
      ('ccpn_comment', 'comment'),
      ('nef_chemical_shift', OD((                # Matching class: ChemicalShift
        ('chain_code', None), ('sequence_code', None), ('residue_type', None), ('atom_name', None),
        ('value', 'value'), ('value_uncertainty', 'valueError'),
        ('ccpn_figure_of_merit', 'figureOfMerit'), ('ccpn_comment', 'comment'),
      ))),
    ))),

    ('nef_distance_restraint_list', _DistanceRestraintListMap),     # Matching class: RestraintList

    ('nef_dihedral_restraint_list', _DihedralRestraintListMap),     # Matching class: RestraintList

    ('nef_rdc_restraint_list', _RdcRestraintListMap),               # Matching class: RestraintList

    # NBNB TBD Add SpectrumReference, ccpn-specific parameters for Spectrum

    ('nef_nmr_spectrum', OD((                    # Matching class: PeakList
      ('num_dimensions', 'spectrum.dimensionCount'),
      ('chemical_shift_list', None),
      ('experiment_classification', 'spectrum.experimentType'),
      ('experiment_type', 'spectrum.experimentName'),
      ('ccpn_peaklist_serial', 'serial'),
      ('ccpn_peaklist_comment', 'comment'),
      ('ccpn_peaklist_name', 'name'),
      ('ccpn_peaklist_is_simulated', 'isSimulated'),
      ('ccpn_spectrum_name', 'spectrum.name'),
      ('ccpn_complete_spectrum_data', None),
      ('nef_spectrum_dimension', OD((            # No Matching class
        ('dimension_id', None), ('axis_unit', None), ('axis_code', None),
        ('spectrometer_frequency', None), ('spectral_width', None), ('value_first_point', None),
        ('folding', None), ('absolute_peak_positions', None), ('is_acquisition', None),
      ))),
      ('nef_spectrum_dimension_transfer', OD((   # No Matching class
        ('dimension_1', None), ('dimension_2', None), ('transfer_type', None), ('is_indirect',None),
      ))),
      ('nef_peak', OD((                          # Matching class: Peak
        ('ordinal', None),
        ('peak_id', 'serial'),
        ('volume', 'volume'),
        ('volume_uncertainty', 'volumeError'),
        ('height', 'height'),
        ('height_uncertainty', 'heightError'),
        ('position_1', None), ('position_uncertainty_1', None),
        ('position_2', None), ('position_uncertainty_2', None),
        ('position_3', None), ('position_uncertainty_3', None),
        ('position_4', None), ('position_uncertainty_4', None),
        ('position_5', None), ('position_uncertainty_5', None),
        ('position_6', None), ('position_uncertainty_6', None),
        ('position_7', None), ('position_uncertainty_7', None),
        ('position_8', None), ('position_uncertainty_8', None),
        ('position_9', None), ('position_uncertainty_9', None),
        ('position_10', None), ('position_uncertainty_10', None),
        ('position_11', None), ('position_uncertainty_11', None),
        ('position_12', None), ('position_uncertainty_12', None),
        ('position_13', None), ('position_uncertainty_13', None),
        ('position_14', None), ('position_uncertainty_14', None),
        ('position_15', None), ('position_uncertainty_15', None),
        ('chain_code_1', None), ('sequence_code_1', None), ('residue_type_1', None),
        ('atom_name_1', None),
        ('chain_code_2', None), ('sequence_code_2', None), ('residue_type_2', None),
        ('atom_name_2', None),
        ('chain_code_3', None), ('sequence_code_3', None), ('residue_type_3', None),
        ('atom_name_3', None),
        ('chain_code_4', None), ('sequence_code_4', None), ('residue_type_4', None),
        ('atom_name_4', None),
        ('chain_code_5', None), ('sequence_code_5', None), ('residue_type_5', None),
        ('atom_name_5', None),
        ('chain_code_6', None), ('sequence_code_6', None), ('residue_type_6', None),
        ('atom_name_6', None),
        ('chain_code_7', None), ('sequence_code_7', None), ('residue_type_7', None),
        ('atom_name_7', None),
        ('chain_code_8', None), ('sequence_code_8', None), ('residue_type_8', None),
        ('atom_name_8', None),
        ('chain_code_9', None), ('sequence_code_9', None), ('residue_type_9', None),
        ('atom_name_9', None),
        ('chain_code_10', None), ('sequence_code_10', None), ('residue_type_10', None),
        ('atom_name_10', None),
        ('chain_code_11', None), ('sequence_code_11', None), ('residue_type_11', None),
        ('atom_name_11', None),
        ('chain_code_12', None), ('sequence_code_12', None), ('residue_type_12', None),
        ('atom_name_12', None),
        ('chain_code_13', None), ('sequence_code_13', None), ('residue_type_13', None),
        ('atom_name_13', None),
        ('chain_code_14', None), ('sequence_code_14', None), ('residue_type_14', None),
        ('atom_name_14', None),
        ('chain_code_15', None), ('sequence_code_15', None), ('residue_type_15', None),
        ('atom_name_15', None),
      ))),
      ('ccpn_spectrum_hit', OD((
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
      ))),
    ))),

    # NB Must be calculated after all PeakLists and RestraintLists:
    ('nef_peak_restraint_links', OD((          # Singleton (RestraintsLists, PeakLists)
      ('nef_peak_restraint_link', OD((
        ('nmr_spectrum_id', None), ('peak_id', None), ('restraint_list_id', None),
        ('restraint_id', None),
      ))),
    ))),

    ('ccpn_spectrum_group', OD()),               # SpectrumGroup

    ('ccpn_sample', OD((                         # Matching class: Sample
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
      ('ccpn_sample_component', OD((
        ('name', 'name'), ('labeling', 'labeling'), ('role', 'role'),
        ('concentration', 'concentration'),
        ('concentration_error', 'concentrationError'), ('concentration_unit', 'concentrationUnit'),
        ('purity', 'purity'), ('comment', 'comment'),
      ))),
    ))),

    ('ccpn_substance', OD((                      # Matching class: Substance
      ('name', 'name'),
      ('labeling', 'labeling'),
      ('substance_type', 'substanceType'),
      ('user_code', 'userCode'),
      ('smiles', 'smiles'),
      ('inchi', 'inChi'),
      ('cas_number', 'casNumber'),
      ('empirical_formula', 'empiricalFormula'),
      ('sequence_string', 'sequenceString'),
      ('molecular_mass', 'molecularMass'),
      ('atom_count', 'atomCount'),
      ('bond_count', 'bondCount'),
      ('ring_count', 'ringCount'),
      ('h_bond_donor_count', 'hBondDonorCount'),
      ('h_bond_acceptor_count', 'hBondAcceptorCount'),
      ('polar_surface_area', 'polarSurfaceArea'),
      ('log_partition_coefficient', 'logPartitionCoefficient'),
      ('comment', 'comment'),
      ('ccpn_substance_synonyms', OD((
        ('synonym', None),
      ))),
    ))),

    ('ccpn_assignments', OD()),                  # Singleton (NmrChains)
    ('ccpn_dataset', OD()),                      # DataSet

    ('ccpn_restraint_list', _RestraintListMap),  # Matching class: RestraintList

    ('ccpn_notes', OD((                          # Singleton (Notes)
      ('ccpn_note', OD((
        ('serial', 'serial'), ('name', 'name'), ('created', 'created'),
        ('last_modified', 'lastModified'), ('text', 'text'),
      ))),
    ))),
  ))

  def __init__(self, project:'ccpn.Project', specificationFile=None, mode='strict',
               programName=None, programVersion=None):
    self.project = project
    self.mode=mode
    if specificationFile is None:
      self.specification = None
    else:
      # NBNB TBD reconsider whether we want the spec summary or something else
      self.specification = Specification.getCcpnSpecification(specificationFile)

    programName = programName or project.programName
    if programVersion is None:
      self.programVersion = ('%s-%s' % (Version.applicationVersion, Version.revision)
                             if appBase is None else project._appBase.applicationVersion)

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

    # NB No attributes cna be set form map here, so we do nto try

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
      result = self._newNefSaveFrame(chains[0].project, category, category)

      loopName = 'nef_sequence'
      loop = result[loopName]

      for chain in chains:
        for residue in chain.residues:
          rowdata = self._loopRowData(category, loopName, residue)
          loop.newRow(rowdata)

      loop = result['nef_covalent_links']
      bonds = chains[0].project.bonds
      if bonds:
        columns = ['chain_code_1', 'sequence_code_1', 'residue_type_1', 'atom_name_1',
                   'chain_code_2', 'sequence_code_2', 'residue_type_2', 'atom_name_2',
                   'ccpn_bond_type']
        for bond in bonds:
          atoms = bond.atoms
          if all(atom.residue.chain in chains for atom in atoms):
            # Bond is between selected chains - add it to the loop
            data = list(atoms[0]._idTuple)
            data.extend(atoms[1]._idTuple)
            data.append(bond.bondType)
            loop.newRow(dict(zip(columns, data)))
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
      rowdata = self._loopRowData(category, loopName, shift)
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
      rowdata = self._loopRowData(category, loopName, contribution)
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
      rowdata = self._loopRowData(category, loopName, peak)

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
          ll =list(zip(x.id.split('.') if x else [None, None, None, None] for x in tt))
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
        loop.newRow(self._loopRowData(category, loopName, spectrumHit))
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
      loop.newRow(self._loopRowData(category, loopName, sampleComponent))
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
        loop.newRow(self._loopRowData(category, loopName, note))
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
    for tag in self.Nef2CcpnMap.keys():
      if tag in dd:
        ll = dd.pop(tag)
        result.extend(ll)
    if dd:
      raise ValueError("Unknown saveframe types in export: %s" % list(dd.keys()))
    #
    return result

  def _loopRowData(self, category:str, loopName:str,
                   wrapperObj:'ccpn.AbstractWrapperObject') -> dict:
    """Fill in a loop row data dictionary from master mapping and wrapperObj.
    Unmapped data to be added afterwards"""

    rowdata = {}
    for neftag,attrstring in self.Nef2CcpnMap[category][loopName].items():
      if attrstring is not None:
        rowdata[neftag] = attrgetter(attrstring)(wrapperObj)
    return rowdata

  def _newNefSaveFrame(self, wrapperObj:'ccpn.AbstractWrapperObject',
                      category:str, name:str) -> StarIo.NmrSaveFrame:
    """Create new NEF saveframe of category for wrapperObj using data from self.Nef2CcpnMap
    The functions will fill in top level items and maek loops, but not
    fill in loop data
    """

    # Set up frame
    if name != category:
      name = '%s_%s' % (category, name)
    result = StarIo.NmrSaveFrame(name=name, category=category)
    result.addItem('sf_category', category)
    result.addItem('sf_framecode', name)

    # Add data
    frameMap = self.Nef2CcpnMap[category]
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


if __name__ == '__main__':
  import sys
  from ccpn import core
  path = sys.argv[1]
  project = core.loadProject(path)
  print(convert2NefString(project))