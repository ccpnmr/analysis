__author__ = 'tjr22'

from collections import OrderedDict

from .parser import Lexer, Parser
from .writer import nefToText

MAJOR_VERSION = '0'
MINOR_VERSION = '8'
PATCH_LEVEL = '4'
__nef_version__ = '.'.join( (MAJOR_VERSION, MINOR_VERSION) )
__version__ = '.'.join( (__nef_version__, PATCH_LEVEL) )

class Nef(OrderedDict):
    """
    An in-memory representation of the NEF format

    Notes:
    Saveframes are modeled as OrderedDict's
    Loops are modeled as a size 2 list of lists (potentially to become pandas saveframes).  The
    first list is a list of loop 'column' names, and the second is a list of values.  This can then
    be accessed by setting the stepsize to the length of the 'column'.
    ie: for a list of all the values in the third column do: l[1][2::len(l[0])]

    """
    NEF_REQUIRED_SAVEFRAME_BY_FRAMECODE = ['nef_nmr_meta_data',
                                           'nef_molecular_system']
    NEF_REQUIRED_SAVEFRAME_BY_CATEGORY = ['nef_chemical_shift_list',]

    NEF_ALL_SAVEFRAME_REQUIRED_FIELDS = ['sf_category',
                                         'sf_framecode',]

    MD_REQUIRED_FIELDS = ['sf_category',
                          'sf_framecode',
                          'format_name',
                          'format_version',
                          'program_name',
                          'program_version',
                          'creation_date',
                          'uuid']
    MD_OPTIONAL_FIELDS = ['coordinate_file_name',]
    MD_OPTIONAL_LOOPS = ['nef_related_entries',
                         'nef_program_script',
                         'nef_run_history']
    MD_RE_REQUIRED_FIELDS = ['database_name',
                             'database_accession_code']
    MD_PS_REQUIRED_FIELDS = ['program_name',]
    MD_RH_REQUIRED_FIELDS = ['run_ordinal',
                             'program_name']
    MD_RH_OPTIONAL_FIELDS = ['program_version',
                             'script_name',
                             'script']

    MS_REQUIRED_FIELDS = ['sf_category',
                          'sf_framecode']
    MS_REQUIRED_LOOPS = ['nef_sequence']
    MS_OPTIONAL_LOOPS = ['nef_covalent_links']
    MS_NS_REQUIRED_FIELDS = ['chain_code',
                             'sequence_code',
                             'residue_type',
                             'linking',
                             'residue_variant']
    MS_CL_REQUIRED_FIELDS = ['chain_code_1',
                             'sequence_code_1',
                             'residue_type_1',
                             'atom_name_1',
                             'chain_code_2',
                             'sequence_code_2',
                             'residue_type_2',
                             'atom_name_2']

    CSL_REQUIRED_FIELDS = ['sf_category',
                           'sf_framecode',
                           'atom_chem_shift_units']
    CSL_REQUIRED_LOOPS = ['nef_chemical_shift']
    CSL_CS_REQUIRED_FIELDS = ['chain_code',
                              'sequence_code',
                              'residue_type',
                              'atom_name',
                              'value']
    CSL_CS_OPTIONAL_FIELDS = ['value_uncertainty',]

    DRL_REQUIRED_FIELDS = ['sf_category',
                           'sf_framecode',
                           'potential_type']
    DRL_REQUIRED_LOOPS = ['nef_distance_restraint']
    DRL_OPTIONAL_FIELDS = ['restraint_origin',]
    DRL_DR_REQUIRED_FIELDS = ['ordinal',
                              'restraint_id',
                              'chain_code_1',
                              'sequence_code_1',
                              'residue_type_1',
                              'atom_name_1',
                              'chain_code_2',
                              'sequence_code_2',
                              'residue_type_2',
                              'atom_name_2',
                              'weight']
    DRL_DR_OPTIONAL_FIELDS = ['restraint_combination_id',
                              'target_value',
                              'target_value_uncertainty',
                              'lower_linear_limit',
                              'lower_limit',
                              'upper_limit',
                              'upper_linear_limit']

    DIHRL_REQUIRED_FIELDS = ['sf_category',
                             'sf_framecode',
                             'potential_type']
    DIHRL_REQUIRED_LOOPS = ['nef_dihedral_restraint']
    DIHRL_OPTIONAL_FIELDS = ['restraint_origin',]
    DIHRL_DIHR_REQUIRED_FIELDS = ['ordinal',
                                  'restraint_id',
                                  'restraint_combination_id',
                                  'chain_code_1',
                                  'sequence_code_1',
                                  'residue_type_1',
                                  'atom_name_1',
                                  'chain_code_2',
                                  'sequence_code_2',
                                  'residue_type_2',
                                  'atom_name_2',
                                  'chain_code_3',
                                  'sequence_code_3',
                                  'residue_type_3',
                                  'atom_name_3',
                                  'chain_code_4',
                                  'sequence_code_4',
                                  'residue_type_4',
                                  'atom_name_4',
                                  'weight']
    DIHRL_DIHR_OPTIONAL_FIELDS = ['target_value',
                                  'target_value_uncertainty',
                                  'lower_linear_limit',
                                  'lower_limit',
                                  'upper_limit',
                                  'upper_linear_limit',
                                  'name']

    RRL_REQUIRED_FIELDS = ['sf_category',
                           'sf_framecode',
                           'potential_type']
    RRL_REQUIRED_LOOPS = ['nef_rdc_restraint']
    RRL_OPTIONAL_FIELDS = ['restraint_origin',
                           'tensor_magnitude',
                           'tensor_rhombicity',
                           'tensor_chain_code',
                           'tensor_sequence_code',
                           'tensor_residue_type',]
    RRL_RR_REQUIRED_FIELDS = ['ordinal',
                              'restraint_id',
                              'chain_code_1',
                              'sequence_code_1',
                              'residue_type_1',
                              'atom_name_1',
                              'chain_code_2',
                              'sequence_code_2',
                              'residue_type_2',
                              'atom_name_2',
                              'weight']
    RRL_RR_OPTIONAL_FIELDS = ['restraint_combination_id',
                              'target_value',
                              'target_value_uncertainty',
                              'lower_linear_limit',
                              'lower_limit',
                              'upper_limit',
                              'upper_linear_limit',
                              'scale',
                              'distance_dependent',]

    PL_REQUIRED_FIELDS = ['sf_category',
                          'sf_framecode',
                          'num_dimensions',
                          'chemical_shift_list']
    PL_REQUIRED_LOOPS = ['nef_spectrum_dimension',
                         'nef_spectrum_dimension_transfer',
                         'nef_peak']
    PL_OPTIONAL_FIELDS = ['experiment_classification',
                          'experiment_type']
    PL_SD_REQUIRED_FIELDS = ['dimension_id',
                             'axis_unit',
                             'axis_code']
    PL_SD_OPTIONAL_FIELDS = ['spectrometer_frequency',
                             'spectral_width',
                             'value_first_point',
                             'folding',
                             'absolute_peak_positions',
                             'is_acquisition',]
    PL_SDT_REQUIRED_FIELDS = ['dimension_1',
                              'dimension_2',
                              'transfer_type']
    PL_SDT_OPTIONAL_FIELDS = ['is_indirect',]
    PL_P_REQUIRED_FIELDS = ['ordinal',
                            'peak_id']
    PL_P_REQUIRED_ALTERNATE_FIELDS = [['height', 'volume'],]
    PL_P_REQUIRED_FIELDS_PATTERN = ['position_{}',
                                    'chain_code_{}',
                                    'sequence_code_{}',
                                    'residue_type_{}',
                                    'atom_name_{}',]
    PL_P_OPTIONAL_ALTERNATE_FIELDS = {r'(height)': ['{}_uncertainty',],
                                      r'(volume)': ['{}_uncertainty',],
                                      r'position_([0-9]+)': ['position_uncertainty_{}',],
                                      }
    PL_P_OPTIONAL_FIELDS_PATTERN = ['position_uncertainty_{}',]

    PRLS_REQUIRED_FIELDS = ['sf_category',
                            'sf_framecode']
    PRLS_REQUIRED_LOOPS = ['nef_peak_restraint_link']
    PRLS_PRL_REQUIRED_FIELDS = ['nmr_spectrum_id',
                                'peak_id',
                                'restraint_list_id',
                                'restraint_id']


    def __init__(self, input_filename=None, initialize=True):
        super(Nef, self).__init__()

        self.input_filename = input_filename

        self.datablock = 'DEFAULT'

        if initialize:
            self.initialize()


    def initialize(self):
        self['nef_nmr_meta_data'] = OrderedDict()
        self['nef_nmr_meta_data'].update({k:'' for k in Nef.MD_REQUIRED_FIELDS})
        self['nef_nmr_meta_data']['sf_category'] = 'nef_nmr_meta_data'
        self['nef_nmr_meta_data']['sf_framecode'] = 'nef_nmr_meta_data'
        self['nef_nmr_meta_data']['format_name'] = 'Nmr_Exchange_Format'
        self['nef_nmr_meta_data']['format_version'] = __nef_version__
        # for l in Nef.MD_REQUIRED_LOOPS:
        #     self['nef_nmr_meta_data'][l] = []

        self['nef_molecular_system'] = OrderedDict()
        self['nef_molecular_system'].update({k:'' for k in Nef.MS_REQUIRED_FIELDS})
        self['nef_molecular_system']['sf_category'] = 'nef_molecular_system'
        self['nef_molecular_system']['sf_framecode'] = 'nef_molecular_system'
        for l in Nef.MS_REQUIRED_LOOPS:
            self['nef_molecular_system'][l] = []

        self.add_chemical_shift_list('nef_chemical_shift_list_1', 'ppm')

    @staticmethod
    def from_text(text, strict=True):
        nef = Nef()

        tokenizer = Lexer()
        parser = Parser(nef)
        parser.strict = strict

        del nef.datablock
        del nef['nef_nmr_meta_data']
        del nef['nef_molecular_system']
        del nef['nef_chemical_shift_list_1']

        parser.parse(tokenizer.tokenize(text))

        return nef


    @staticmethod
    def from_file(filename, strict=True):
        with open(filename, 'r') as f:
            nef = Nef.from_text(f.read(), strict=strict)
        return nef


    def write(self, file_like):
        import time
        import random

        self['nef_nmr_meta_data']['format_version'] = __nef_version__
        if self['nef_nmr_meta_data']['program_name'] == '':
            self['nef_nmr_meta_data']['program_name'] = 'NEFreader'
            self['nef_nmr_meta_data']['program_version'] = __version__
        self['nef_nmr_meta_data']['creation_date'] = time.strftime('%Y-%m-%dT%H:%M:%s')
        self['nef_nmr_meta_data']['uuid'] = '-'.join((self['nef_nmr_meta_data']['program_name'],
                                                      self['nef_nmr_meta_data']['creation_date'],
                                                      str(hash(self))[:7]
                                                     ))
        file_like.write(nefToText(self))


    def save(self, filename):
        with open(filename, 'w') as f:
            self.write(f)


    ### Convenience Functions ###

    def add_saveframe(self, name, category, required_fields=None, required_loops=None):
        self[name] = OrderedDict()
        if required_fields is not None:
            self[name].update({k: '' for k in required_fields})
        self[name]['sf_category'] = category
        self[name]['sf_framecode'] = name
        if required_loops is not None:
            for l in required_loops:
                self[name][l] = []
        return self[name]



    def add_chemical_shift_list(self, name, cs_units='ppm'):
        category = 'nef_chemical_shift_list'
        self.add_saveframe(name=name, category=category,
                           required_fields=Nef.CSL_REQUIRED_FIELDS,
                           required_loops=Nef.CSL_REQUIRED_LOOPS)
        self[name]['atom_chem_shift_units'] = cs_units
        return self[name]


    def add_distance_restraint_list(self, name, potential_type,
                                    restraint_origin=None):
        category = 'nef_distance_restraint_list'
        self.add_saveframe(name=name, category=category,
                           required_fields=Nef.DRL_REQUIRED_FIELDS,
                           required_loops=Nef.DRL_REQUIRED_LOOPS)
        self[name]['potential_type'] = potential_type
        if restraint_origin is not None:
            self[name]['restraint_origin'] = restraint_origin

        return self[name]


    def add_dihedral_restraint_list(self, name, potential_type,
                                    restraint_origin=None):
        category = 'nef_dihedral_restraint_list'
        self.add_saveframe(name=name, category=category,
                           required_fields=Nef.DIHRL_REQUIRED_FIELDS,
                           required_loops=Nef.DIHRL_REQUIRED_LOOPS)
        self[name]['potential_type'] = potential_type
        if restraint_origin is not None:
            self[name]['restraint_origin'] = restraint_origin

        return self[name]


    def add_rdc_restraint_list(self, name, potential_type,
                               restraint_origin=None, tensor_magnitude=None,
                               tensor_rhombicity=None, tensor_chain_code=None,
                               tensor_sequence_code=None, tensor_residue_type=None):
        category = 'nef_rdc_restraint_list'
        self.add_saveframe(name=name, category=category,
                           required_fields=Nef.DIHRL_REQUIRED_FIELDS,
                           required_loops=Nef.RRL_REQUIRED_LOOPS)
        self[name]['potential_type'] = potential_type
        if restraint_origin is not None:
            self[name]['restraint_origin'] = restraint_origin
        if tensor_magnitude is not None:
            self[name]['tensor_magnitude'] = tensor_magnitude
        if tensor_rhombicity is not None:
            self[name]['tensor_rhombicity'] = tensor_rhombicity
        if tensor_chain_code is not None:
            self[name]['tensor_chain_code'] = tensor_chain_code
        if tensor_sequence_code is not None:
            self[name]['tensor_sequence_code'] = tensor_sequence_code
        if tensor_residue_type is not None:
            self[name]['tensor_residue_type'] = tensor_residue_type

        return self[name]


    def add_peak_list(self, name, num_dimensions, chemical_shift_list,
                      experiment_classification=None,
                      experiment_type=None):
        category = 'nef_nmr_spectrum'
        if chemical_shift_list in self:
            if self[chemical_shift_list]['sf_category'] == 'nef_chemical_shift_list':
                self.add_saveframe(name=name, category=category,
                                   required_fields=Nef.PL_REQUIRED_FIELDS,
                                   required_loops=Nef.PL_REQUIRED_LOOPS)
                self[name]['num_dimensions'] = num_dimensions
                self[name]['chemical_shift_list'] = chemical_shift_list
                if experiment_classification is not None:
                    self[name]['experiment_classification'] = experiment_classification
                if experiment_type is not None:
                    self[name]['experiment_type'] = experiment_type

                return self[name]
            raise Exception('{} is not a nef_chemical_shift_list.'.format(chemical_shift_list))
        raise Exception('{} does not exist.'.format(chemical_shift_list))


    def add_linkage_table(self):
        name = category = 'nef_peak_restraint_links'
        return self.add_saveframe(name=name, category=category,
                                  required_fields=Nef.PRLS_REQUIRED_FIELDS,
                                  required_loops=Nef.PL_REQUIRED_LOOPS)

