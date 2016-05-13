from __future__ import absolute_import, print_function, unicode_literals
__author__ = 'TJ Ragan'

import unittest
from collections import OrderedDict

from .. import NEFreader


class Test_nef_validators(unittest.TestCase):

    def setUp(self):
        self.nef = NEFreader.Nef()
        self.v = NEFreader.Validator(self.nef)


    def _test_full_validation(self):
        self.assertFalse(self.v.isValid())

        nef_sequence_item = {'chain_code': 'A',
                             'sequence_code': '1',
                             'residue_type': 'ALA',
                             'linking': '.',
                             'residue_variant': '.'}
        self.nef['nef_molecular_system']['nef_sequence'].append(nef_sequence_item)

        self.assertTrue(self.v.isValid())


    def test_missing_mandatory_datablock_label(self):
        self.assertIsNone(self.v._validate_datablock()['DATABLOCK'])

        del(self.nef.datablock)

        self.assertIsNotNone(self.v._validate_datablock()['DATABLOCK'])


    def test_missing_mandatory_saveframe__nef_nmr_meta_data(self):
        del(self.nef['nef_nmr_meta_data'])

        self.assertEqual(['Missing nef_nmr_meta_data label.'],
                      self.v._validate_required_saveframes()['REQUIRED_SAVEFRAMES'])

    def test_missing_mandatory_saveframe__nef_molecular_system(self):
        del(self.nef['nef_molecular_system'])

        self.assertEqual(['Missing nef_molecular_system label.'],
                      self.v._validate_required_saveframes()['REQUIRED_SAVEFRAMES'])

    def test_missing_mandatory_saveframe__nef_chemical_shift_list(self):
        del(self.nef['nef_chemical_shift_list_1'])

        self.assertEqual(['No saveframes with sf_category: nef_chemical_shift_list.'],
                      self.v._validate_required_saveframes()['REQUIRED_SAVEFRAMES'])


    def test_all_saveframes_have_mandatory_fields(self):
        self.nef['generic_saveframe'] = {'sf_framecode': 'generic_saveframe',
                                         'sf_category': 'generic'}

        self.assertEqual(self.v._validate_saveframe_fields()['SAVEFRAMES'], [])

    def test_all_saveframes_have_mandatory_fields__framecode_missing(self):
        self.nef['generic_saveframe'] = {'sf_category': 'generic'}

        self.assertEqual(['generic_saveframe: missing sf_framecode label.'],
                      self.v._validate_saveframe_fields()['SAVEFRAMES'])

    def test_all_saveframes_have_mandatory_fields__category_missing(self):
        self.nef['generic_saveframe'] = {'sf_framecode': 'generic_saveframe'}

        self.assertEqual(['generic_saveframe: missing sf_category label.'],
                      self.v._validate_saveframe_fields()['SAVEFRAMES'])


    def test_missing_mandatory_metadata__sf_framecode(self):
        del(self.nef['nef_nmr_meta_data'])

        self.assertEqual('No nef_nmr_meta_data saveframe.',
                         self.v._validate_metadata()['METADATA'])

    def test_mismatch_metadata__sf_framecode(self):
        self.nef['nef_nmr_meta_data']['sf_framecode'] = 'meta'

        self.assertEqual(['sf_framecode meta must match key nef_nmr_meta_data.'],
                         self.v._validate_metadata()['METADATA'])
        self.assertEqual(['sf_framecode meta must match key nef_nmr_meta_data.'],
                         self.v._validate_saveframe_fields()['SAVEFRAMES'])

    def test_missing_mandatory_metadata__sf_category(self):
        del(self.nef['nef_nmr_meta_data']['sf_category'])

        self.assertEqual(['Missing sf_category label.'],
                         self.v._validate_metadata()['METADATA'])

    def test_mismatch_metadata__sf_category(self):
        self.nef['nef_nmr_meta_data']['sf_category'] = 'category'

        self.assertEqual(['sf_category category must be nef_nmr_meta_data.'],
                         self.v._validate_metadata()['METADATA'])


    def test_missing_mandatory_metadata__format_name(self):
        del(self.nef['nef_nmr_meta_data']['format_name'])

        self.assertEqual(['Missing format_name label.'],
                         self.v._validate_metadata()['METADATA'])

    def test_mismatch_metadata__format_name(self):
        self.nef['nef_nmr_meta_data']['format_name'] = 'format'

        self.assertEqual(["format_name must be 'Nmr_Exchange_Format'."],
                         self.v._validate_metadata()['METADATA'])


    def test_missing_mandatory_metadata__format_version(self):
        del(self.nef['nef_nmr_meta_data']['format_version'])

        self.assertEqual(['Missing format_version label.'],
                         self.v._validate_metadata()['METADATA'])

    def test_mismatch_metadata__format_version(self):
        self.nef['nef_nmr_meta_data']['format_version'] = '999'

        self.assertEqual(["This reader does not support format version 999."],
                         self.v._validate_metadata()['METADATA'])


    def test_missing_mandatory_metadata__program_name(self):
        del(self.nef['nef_nmr_meta_data']['program_name'])

        self.assertEqual(['Missing program_name label.'],
                         self.v._validate_metadata()['METADATA'])


    def test_missing_mandatory_metadata__program_version(self):
        del(self.nef['nef_nmr_meta_data']['program_version'])

        self.assertEqual(['Missing program_version label.'],
                         self.v._validate_metadata()['METADATA'])


    def test_missing_mandatory_metadata__creation_date(self):
        del(self.nef['nef_nmr_meta_data']['creation_date'])

        self.assertEqual(['Missing creation_date label.'],
                         self.v._validate_metadata()['METADATA'])


    def test_missing_mandatory_metadata__uuid(self):
        del(self.nef['nef_nmr_meta_data']['uuid'])

        self.assertEqual(['Missing uuid label.'],
                         self.v._validate_metadata()['METADATA'])


    def test_nonallowed_fields_in_metadata(self):
        self.nef['nef_nmr_meta_data']['test'] = ''

        self.assertEqual(["Field 'test' not allowed in nef_nmr_meta_data."],
                         self.v._validate_metadata()['METADATA'])


    def test_optional_coordinate_file_name_field_in_metadata(self):
        self.nef['nef_nmr_meta_data']['coordinate_file_name'] = ''
        self.assertEqual([], self.v._validate_metadata()['METADATA'])


    def test_optional_nef_related_entries_loop_in_metadata_missing_fields(self):
        self.nef['nef_nmr_meta_data']['nef_related_entries'] = [OrderedDict()]

        self.assertEqual(2, len(self.v._validate_metadata()['METADATA']))
        self.assertIn('nef_nmr_meta_data:nef_related_entries entry 1: missing database_name label.',
                         self.v._validate_metadata()['METADATA'])
        self.assertIn('nef_nmr_meta_data:nef_related_entries entry 1: missing database_accession_code label.',
                         self.v._validate_metadata()['METADATA'])

    def test_optional_nef_related_entries_loop_in_metadata(self):
        self.nef['nef_nmr_meta_data']['nef_related_entries'] = [{'database_name':'test',
                                                                'database_accession_code':'1'},]

        self.assertEqual(self.v._validate_metadata()['METADATA'], [])

    def test_optional_nef_related_entries_loop_nonallowed_field_in_metadata(self):
        self.nef['nef_nmr_meta_data']['nef_related_entries'] = [{'database_name':'test',
                                                                'database_accession_code':'1',
                                                                'test':'test'}]

        self.assertEqual(["Field 'test' not allowed in nef_nmr_meta_data:nef_related_entries entry 1."],
                         self.v._validate_metadata()['METADATA'])


    def test_optional_nef_program_script_loop_in_metadata_missing_fields(self):
        self.nef['nef_nmr_meta_data']['nef_program_script'] = [OrderedDict()]

        self.assertEqual(['nef_nmr_meta_data:nef_program_script entry 1: missing program_name label.'],
                         self.v._validate_metadata()['METADATA'])

    def test_optional_nef_program_script_loop_in_metadata(self):
        self.nef['nef_nmr_meta_data']['nef_program_script'] = [{'program_name':'test'},]

        self.assertEqual(self.v._validate_metadata()['METADATA'], [])

    def test_optional_nef_program_script_loop_inconsistent_keys_in_metadata(self):
        self.nef['nef_nmr_meta_data']['nef_program_script'] = [{'program_name':'test'},
                                                            {'program_name':'test',
                                                             'script_name':'test.script'}
                                                             ]

        self.assertEqual(['nef_nmr_meta_data:nef_program_script item 0: missing script_name label.'],
                         self.v._validate_metadata()['METADATA'])


    def _test_optional_nef_run_history_loop_in_metadata_missing_fields(self):
        self.nef['nef_nmr_meta_data']['nef_run_history'] = [OrderedDict()]

        self.assertEqual(2, len(self.v._validate_metadata()['METADATA']))
        self.assertIn('nef_nmr_meta_data:nef_run_history entry 1: missing run_ordinal label.',
                         self.v._validate_metadata()['METADATA'])
        self.assertIn('nef_nmr_meta_data:nef_run_history entry 1: missing program_name label.',
                         self.v._validate_metadata()['METADATA'])

    def test_optional_nef_run_history_loop_in_metadata(self):
        self.nef['nef_nmr_meta_data']['nef_run_history'] = [{'run_ordinal':'1',
                                                             'program_name':'test',
                                                             'program_version':'1',
                                                             'script_name':'test.script',
                                                             'script':"""do stuff"""}]

        self.assertEqual(self.v._validate_metadata()['METADATA'], [])

    def test_optional_nef_run_history_loop_nonallowed_field_in_metadata(self):
        self.nef['nef_nmr_meta_data']['nef_run_history'] = [{'run_ordinal':'1',
                                                             'program_name':'test',
                                                             'test':'test'}]

        self.assertEqual(["Field 'test' not allowed in nef_nmr_meta_data:nef_run_history entry 1."],
                         self.v._validate_metadata()['METADATA'])

    def test_optional_nef_run_history_loop_inconsistent_keys_in_metadata(self):
        self.nef['nef_nmr_meta_data']['nef_run_history'] = [{'run_ordinal':'1',
                                                             'program_name':'test'},
                                                            {'run_ordinal':'2',
                                                             'program_name':'test',
                                                             'program_version':'1'}
                                                             ]

        self.assertEqual(['nef_nmr_meta_data:nef_run_history item 0: missing program_version label.'],
                         self.v._validate_metadata()['METADATA'])



    def test_missing_mandatory_nef_molecular_system_category_label(self):
        self.assertEqual(self.v._validate_molecular_system()['MOLECULAR_SYSTEM'],
                         ['Empty nef_sequence.'])

        del(self.nef['nef_molecular_system']['sf_category'])

        self.assertIn('Missing sf_category label.', self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])

    def test_missing_mandatory_nef_molecular_system_framecode(self):
        self.assertEqual(self.v._validate_molecular_system()['MOLECULAR_SYSTEM'],
                         ['Empty nef_sequence.'])

        del(self.nef['nef_molecular_system']['sf_framecode'])

        self.assertIn('Missing sf_framecode label.', self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])

    def test_missing_mandatory_nef_molecular_system_nef_sequence(self):
        self.assertEqual(self.v._validate_molecular_system()['MOLECULAR_SYSTEM'],
                         ['Empty nef_sequence.'])

        del(self.nef['nef_molecular_system']['nef_sequence'])

        self.assertIn('Missing nef_sequence label.', self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])


    def test_missing_mandatory_nef_sequence_columns(self):
        seq = self.nef['nef_molecular_system']['nef_sequence']
        seq.append({})

        self.assertIn('nef_molecular_system:nef_sequence entry 1: missing chain_code label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_sequence entry 1: missing sequence_code label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_sequence entry 1: missing residue_type label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_sequence entry 1: missing linking label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_sequence entry 1: missing residue_variant label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])


    def test_mandatory_nef_sequence_in_molecular_system(self):
        nef_sequence_item = {'chain_code': 'A',
                             'sequence_code': '1',
                             'residue_type': 'ALA',
                             'linking': '.',
                             'residue_variant': '.'}
        self.nef['nef_molecular_system']['nef_sequence'].append(nef_sequence_item)

        self.assertEqual(self.v._validate_molecular_system()['MOLECULAR_SYSTEM'],[])


    def test_optional_cross_links_loop_in_molecular_system(self):
        nef_sequence_item_1 = {'chain_code': 'A',
                               'sequence_code': '1',
                               'residue_type': 'ALA',
                               'linking': '.',
                               'residue_variant': '.'}
        self.nef['nef_molecular_system']['nef_sequence'].append(nef_sequence_item_1)
        nef_sequence_item_2 = {'chain_code': 'B',
                               'sequence_code': '2',
                               'residue_type': 'CYS',
                               'linking': '.',
                               'residue_variant': '.'}
        self.nef['nef_molecular_system']['nef_sequence'].append(nef_sequence_item_2)
        self.nef['nef_molecular_system']['nef_covalent_links'] = [{},]

        self.assertIn('nef_molecular_system:nef_covalent_links entry 1: missing chain_code_1 label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_covalent_links entry 1: missing sequence_code_1 label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_covalent_links entry 1: missing residue_type_1 label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_covalent_links entry 1: missing atom_name_1 label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_covalent_links entry 1: missing chain_code_2 label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_covalent_links entry 1: missing sequence_code_2 label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_covalent_links entry 1: missing residue_type_2 label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])
        self.assertIn('nef_molecular_system:nef_covalent_links entry 1: missing atom_name_2 label.',
                      self.v._validate_molecular_system()['MOLECULAR_SYSTEM'])

        nef_covalent_link = {'chain_code_1': 'A',
                             'sequence_code_1': '1',
                             'residue_type_1': 'ALA',
                             'atom_name_1': 'N',
                             'chain_code_2': 'B',
                             'sequence_code_2': '2',
                             'residue_type_2': 'CYS',
                             'atom_name_2': 'SD',
                             }
        self.nef['nef_molecular_system']['nef_covalent_links'] = [nef_covalent_link,]

        self.assertEqual(self.v._validate_molecular_system()['MOLECULAR_SYSTEM'],[])



    def test_missing_mandatory_chemical_shift_lists(self):
        self.assertEqual(self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'], [])

        del(self.nef['nef_chemical_shift_list_1']['sf_category'])

        self.assertEqual(['No saveframes with sf_category: nef_chemical_shift_list.'],
            self.v._validate_required_saveframes()['REQUIRED_SAVEFRAMES'])
        self.assertEqual(['No nef_chemical_shift_list saveframes found.'],
            self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'])


    def test_missing_mandatory_chemical_shift_loop_in_chemical_shift_lists_list(self):
        del(self.nef['nef_chemical_shift_list_1']['nef_chemical_shift'])

        self.assertEqual(['nef_chemical_shift_list_1: missing nef_chemical_shift label.'],
            self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'])

    def test_missing_mandatory_chemical_shift_loop_fields(self):
        self.nef['nef_chemical_shift_list_1']['nef_chemical_shift'] = [{}]

        self.assertIn('nef_chemical_shift_list_1:nef_chemical_shift entry 1: missing chain_code label.',
                      self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'])
        self.assertIn('nef_chemical_shift_list_1:nef_chemical_shift entry 1: missing sequence_code label.',
                      self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'])
        self.assertIn('nef_chemical_shift_list_1:nef_chemical_shift entry 1: missing residue_type label.',
                      self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'])
        self.assertIn('nef_chemical_shift_list_1:nef_chemical_shift entry 1: missing atom_name label.',
                      self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'])
        self.assertIn('nef_chemical_shift_list_1:nef_chemical_shift entry 1: missing value label.',
                      self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'])

    def test_mandatory_chemical_shift_loop_fields(self):
        nef_shift_item = {'chain_code': 'A',
                            'sequence_code': '1',
                            'residue_type': 'ALA',
                            'atom_name': 'HA',
                            'value': '5.0'}
        sl = self.nef['nef_chemical_shift_list_1']['nef_chemical_shift'] = [nef_shift_item,]

        self.assertEqual(self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'], [])

        sl[0]['value_uncertainty'] = '0.2'

        self.assertEqual(self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'], [])



    def test_mismatched_mandatory_chemical_shift_loop_fields(self):
        nef_shift_item_1 = {'chain_code': 'A',
                            'sequence_code': '1',
                            'residue_type': 'ALA',
                            'atom_name': 'HA',
                            'value': '5.0'}
        nef_shift_item_2 = {'chain_code': 'A',
                            'sequence_code': '1',
                            'residue_type': 'ALA',
                            'atom_name': 'N',
                            'value': '120',
                            'value_uncertainty': '0.2'}
        self.nef['nef_chemical_shift_list_1']['nef_chemical_shift'] = [nef_shift_item_1,
                                                                       nef_shift_item_2]

        self.assertEqual(self.v._validate_chemical_shift_lists()['CHEMICAL_SHIFT_LISTS'],
                         ['nef_chemical_shift_list_1:nef_chemical_shift item 0: missing value_uncertainty label.'])



    def test_mandatory_nef_distance_restraint_list(self):
        self.assertEqual(self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'], [])

        drl = self.nef['nef_distance_restraint_list_1'] = OrderedDict()
        drl['sf_category'] = 'nef_distance_restraint_list'

        self.assertIn('nef_distance_restraint_list_1: missing sf_framecode label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1: missing potential_type label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1: missing sf_framecode label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])

        drl['sf_framecode'] = 'nef_distance_restraint_list_1'
        drl['potential_type'] = 'square-well-parabolic-linear'
        drl['nef_distance_restraint'] = []
        self.assertEqual(self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'], [])

        dr = drl['nef_distance_restraint']
        distance_restraint_1 = {'ordinal': '1',
                               'restraint_id': '1',
                               'chain_code_1': 'A',
                               'sequence_code_1': '21',
                               'residue_type_1': 'ALA',
                               'atom_name_1': 'HB%',
                               'chain_code_2': 'A',
                               'sequence_code_2': '17',
                               'residue_type_2': 'VAL',
                               'atom_name_2': 'H',
                               'weight': '1.00'}
        distance_restraint_2 = {'ordinal': '2',
                               'restraint_id': '1',
                               'chain_code_1': 'A',
                               'sequence_code_1': '21',
                               'residue_type_1': 'ALA',
                               'atom_name_1': 'HB%',
                               'chain_code_2': 'A',
                               'sequence_code_2': '18',
                               'residue_type_2': 'VAL',
                               'atom_name_2': 'H',
                               'weight': '1.00'}
        dr.append(distance_restraint_1)
        dr.append(distance_restraint_2)

        self.assertEqual(self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'], [])

        distance_restraint_3 = {'ordinal': '3',
                               'restraint_id': '1',
                               'chain_code_1': 'A',
                               'sequence_code_1': '21',
                               'residue_type_1': 'ALA',
                               'atom_name_1': 'HB%',
                               'chain_code_2': 'A',
                               'sequence_code_2': '18',
                               'residue_type_2': 'VAL',
                               'atom_name_2': 'H',
                               'weight': '1.00',
                               'restraint_combination_id': '.',
                               'target_value': '.',
                               'target_value_uncertainty': '.',
                               'lower_linear_limit': '.',
                               'lower_limit': '.',
                               'upper_limit': '.',
                               'upper_linear_limit': '.'}
        dr.append(distance_restraint_3)

        self.assertEqual(len(self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS']),
                         14)
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 0: missing lower_limit label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 0: missing upper_linear_limit label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 0: missing upper_limit label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 0: missing lower_limit label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 0: missing target_value label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 0: missing restraint_combination_id label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 0: missing target_value_uncertainty label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 1: missing lower_limit label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 1: missing upper_linear_limit label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 1: missing upper_limit label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 1: missing lower_limit label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 1: missing target_value label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 1: missing restraint_combination_id label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])
        self.assertIn('nef_distance_restraint_list_1:nef_distance_restraint item 1: missing target_value_uncertainty label.',
                      self.v._validate_distance_restraint_lists()['DISTANCE_RESTRAINT_LISTS'])


    def test_mandatory_nef_dihedral_restraint_list(self):
        self.assertEqual(self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'], [])

        drl = self.nef['nef_dihedral_restraint_list_1'] = OrderedDict()
        drl['sf_category'] = 'nef_dihedral_restraint_list'

        self.assertIn('nef_dihedral_restraint_list_1: missing sf_framecode label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1: missing potential_type label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1: missing sf_framecode label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])

        drl['sf_framecode'] = 'nef_dihedral_restraint_list_1'
        drl['potential_type'] = 'square-well-parabolic'
        drl['restraint_origin'] = 'talos'
        drl['nef_dihedral_restraint'] = []
        self.assertEqual(self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'], [])

        dr = drl['nef_dihedral_restraint']
        dihedral_restraint_1 = {'ordinal': '1',
                               'restraint_id': '1',
                               'restraint_combination_id': '.',
                               'chain_code_1': 'A',
                               'sequence_code_1': '21',
                               'residue_type_1': 'ALA',
                               'atom_name_1': 'N',
                               'chain_code_2': 'A',
                               'sequence_code_2': '21',
                               'residue_type_2': 'ALA',
                               'atom_name_2': 'CA',
                               'chain_code_3': 'A',
                               'sequence_code_3': '21',
                               'residue_type_3': 'ALA',
                               'atom_name_3': 'C',
                               'chain_code_4': 'A',
                               'sequence_code_4': '22',
                               'residue_type_4': 'THR',
                               'atom_name_4': 'N',
                               'weight': '1.00'}
        dihedral_restraint_2 = {'ordinal': '1',
                               'restraint_id': '1',
                               'restraint_combination_id': '.',
                               'chain_code_1': 'A',
                               'sequence_code_1': '21',
                               'residue_type_1': 'ALA',
                               'atom_name_1': 'N',
                               'chain_code_2': 'A',
                               'sequence_code_2': '21',
                               'residue_type_2': 'ALA',
                               'atom_name_2': 'CA',
                               'chain_code_3': 'A',
                               'sequence_code_3': '21',
                               'residue_type_3': 'ALA',
                               'atom_name_3': 'C',
                               'chain_code_4': 'A',
                               'sequence_code_4': '22',
                               'residue_type_4': 'THR',
                               'atom_name_4': 'N',
                               'weight': '1.00'}
        dr.append(dihedral_restraint_1)
        dr.append(dihedral_restraint_2)

        self.assertEqual(self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'], [])


        dihedral_restraint_3 = {'ordinal': '3',
                                'restraint_id': '2',
                                'restraint_combination_id': '.',
                                'chain_code_1': 'A',
                                'sequence_code_1': '21',
                                'residue_type_1': 'ALA',
                                'atom_name_1': 'C',
                                'chain_code_2': 'A',
                                'sequence_code_2': '22',
                                'residue_type_2': 'THR',
                                'atom_name_2': 'N',
                                'chain_code_3': 'A',
                                'sequence_code_3': '22',
                                'residue_type_3': 'THR',
                                'atom_name_3': 'CA',
                                'chain_code_4': 'A',
                                'sequence_code_4': '22',
                                'residue_type_4': 'THR',
                                'atom_name_4': 'C',
                                'weight': '3.00',
                                'target_value': '-50',
                                'target_value_uncertainty': '8.0',
                                'lower_linear_limit': '.',
                                'lower_limit': '-60.0',
                                'upper_limit': '-40.0',
                                'upper_linear_limit': '.',
                                'name': 'PHI'}
        dr.append(dihedral_restraint_3)
        self.assertEqual(len(self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS']),
                         14)
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 0: missing target_value label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 0: missing target_value_uncertainty label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 0: missing lower_linear_limit label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 0: missing lower_limit label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 0: missing upper_limit label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 0: missing upper_linear_limit label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 0: missing name label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 1: missing target_value label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 1: missing target_value_uncertainty label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 1: missing lower_linear_limit label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 1: missing lower_limit label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 1: missing upper_limit label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 1: missing upper_linear_limit label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])
        self.assertIn('nef_dihedral_restraint_list_1:nef_dihedral_restraint item 1: missing name label.',
                      self.v._validate_dihedral_restraint_lists()['DIHEDRAL_RESTRAINT_LISTS'])


    def test_mandatory_nef_rdc_restraint_list(self):
        self.assertEqual(self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'], [])

        rdcl = self.nef['nef_rdc_restraint_list_1'] = OrderedDict()
        rdcl['sf_category'] = 'nef_rdc_restraint_list'

        self.assertIn('nef_rdc_restraint_list_1: missing sf_framecode label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1: missing potential_type label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1: missing sf_framecode label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])

        rdcl['sf_framecode'] = 'nef_rdc_restraint_list_1'
        rdcl['potential_type'] = 'log-normal'
        rdcl['restraint_origin'] = 'measured'
        rdcl['tensor_magnitude'] = '11.0000'
        rdcl['tensor_rhombicity'] = '0.0670'
        rdcl['tensor_chain_code'] = 'C'
        rdcl['tensor_sequence_code'] = '900'
        rdcl['tensor_residue_type'] = 'TNSR'
        rdcl['nef_rdc_restraint'] = []
        self.assertEqual(self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'], [])

        rdcr = rdcl['nef_rdc_restraint']
        rdc_restraint_1 = {'ordinal': '1',
                           'restraint_id': '1',
                           'restraint_combination_id': '.',
                           'chain_code_1': 'A',
                           'sequence_code_1': '21',
                           'residue_type_1': 'ALA',
                           'atom_name_1': 'H',
                           'chain_code_2': 'A',
                           'sequence_code_2': '21',
                           'residue_type_2': 'ALA',
                           'atom_name_2': 'N',
                           'weight': '1.00'}
        rdcr.append(rdc_restraint_1)

        self.assertEqual(self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'], [])

        rdc_restraint_2 = {'ordinal': '1',
                           'restraint_id': '2',
                           'restraint_combination_id': '.',
                           'chain_code_1': 'A',
                           'sequence_code_1': '22',
                           'residue_type_1': 'THR',
                           'atom_name_1': 'H',
                           'chain_code_2': 'A',
                           'sequence_code_2': '22',
                           'residue_type_2': 'THR',
                           'atom_name_2': 'N',
                           'weight': '1.00',
                           'target_value': '3.1',
                           'target_value_uncertainty': '0.40',
                           'lower_linear_limit': '.',
                           'lower_limit': '.',
                           'upper_limit': '.',
                           'upper_linear_limit': '.',
                           'scale': '1.0',
                           'distance_dependent': 'false'}

        rdcr.append(rdc_restraint_2)
        self.assertEqual(len(self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS']), 8)
        self.assertIn('nef_rdc_restraint_list_1:nef_rdc_restraint item 0: missing target_value label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1:nef_rdc_restraint item 0: missing target_value_uncertainty label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1:nef_rdc_restraint item 0: missing lower_linear_limit label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1:nef_rdc_restraint item 0: missing lower_limit label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1:nef_rdc_restraint item 0: missing upper_limit label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1:nef_rdc_restraint item 0: missing upper_linear_limit label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1:nef_rdc_restraint item 0: missing scale label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])
        self.assertIn('nef_rdc_restraint_list_1:nef_rdc_restraint item 0: missing distance_dependent label.',
                      self.v._validate_rdc_restraint_lists()['RDC_RESTRAINT_LISTS'])


    def _test_nef_peak_list(self):
        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        npl = self.nef['nef_nmr_spectrum_cnoesy1'] = OrderedDict()
        npl['sf_category'] = 'nef_nmr_spectrum'

        self.assertIn('nef_nmr_spectrum_cnoesy1: missing sf_framecode label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1: missing num_dimensions label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1: missing chemical_shift_list label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])

        npl['sf_framecode'] = 'nef_nmr_spectrum_cnoesy1'
        npl['num_dimensions'] = '3'
        npl['chemical_shift_list'] = 'nef_chemical_shift_list_1'
        npl['experiment_classification'] = 'H_H[N].through-space'
        npl['experiment_type'] = '15N-NOESY-HSQC'
        npl['nef_spectrum_dimension'] = []
        npl['nef_spectrum_dimension_transfer'] = []
        npl['nef_peak'] = []

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

    def test_nef_peak_list_missing_chemical_shift_list(self):
        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        npl = self.nef['nef_nmr_spectrum_cnoesy1'] = OrderedDict()
        npl['sf_category'] = 'nef_nmr_spectrum'

        self.assertIn('nef_nmr_spectrum_cnoesy1: missing sf_framecode label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1: missing num_dimensions label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1: missing chemical_shift_list label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])

        npl['sf_framecode'] = 'nef_nmr_spectrum_cnoesy1'
        npl['num_dimensions'] = '3'
        npl['chemical_shift_list'] = 'nef_chemical_shift_list_2'
        npl['experiment_classification'] = 'H_H[N].through-space'
        npl['experiment_type'] = '15N-NOESY-HSQC'
        npl['nef_spectrum_dimension'] = []
        npl['nef_spectrum_dimension_transfer'] = []
        npl['nef_peak'] = []

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'],
                         ['nef_nmr_spectrum_cnoesy1: missing chemical_shift_list nef_chemical_shift_list_2.'])

    def test_nef_peak_list_spectrum_dimension_loop(self):
        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        npl = self.nef['nef_nmr_spectrum_cnoesy1'] = OrderedDict()
        npl['sf_category'] = 'nef_nmr_spectrum'
        npl['sf_framecode'] = 'nef_nmr_spectrum_cnoesy1'
        npl['num_dimensions'] = '3'
        npl['chemical_shift_list'] = 'nef_chemical_shift_list_1'
        npl['experiment_classification'] = 'H_H[N].through-space'
        npl['experiment_type'] = '15N-NOESY-HSQC'
        npl['nef_spectrum_dimension'] = []
        npl['nef_spectrum_dimension_transfer'] = []
        npl['nef_peak'] = []

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        pd = npl['nef_spectrum_dimension']
        spectrum_dimension_1 = {'dimension_id': '1',
                           'axis_unit': 'ppm',
                           'axis_code': '1H'}
        pd.append(spectrum_dimension_1)

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        spectrum_dimension_2 = {'dimension_id': '1',
                           'axis_unit': 'ppm',
                           'axis_code': '1H',
                           'spectrometer_frequency': '500.139',
                           'spectral_width': '10.4',
                           'value_first_point': '9.9',
                           'folding': 'circular',
                           'absolute_peak_positions': 'true',
                           'is_acquisition': 'false',}

        pd.append(spectrum_dimension_2)
        self.assertEqual(len(self.v._validate_peak_lists()['PEAK_LISTS']), 6)
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_spectrum_dimension item 0: missing spectrometer_frequency label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_spectrum_dimension item 0: missing spectral_width label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_spectrum_dimension item 0: missing value_first_point label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_spectrum_dimension item 0: missing folding label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_spectrum_dimension item 0: missing absolute_peak_positions label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_spectrum_dimension item 0: missing is_acquisition label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])

    def test_nef_peak_list_spectrum_dimension_transfer_loop(self):
        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        npl = self.nef['nef_nmr_spectrum_cnoesy1'] = OrderedDict()
        npl['sf_category'] = 'nef_nmr_spectrum'
        npl['sf_framecode'] = 'nef_nmr_spectrum_cnoesy1'
        npl['num_dimensions'] = '3'
        npl['chemical_shift_list'] = 'nef_chemical_shift_list_1'
        npl['experiment_classification'] = 'H_H[N].through-space'
        npl['experiment_type'] = '15N-NOESY-HSQC'
        npl['nef_spectrum_dimension'] = []
        npl['nef_spectrum_dimension_transfer'] = []
        npl['nef_peak'] = []

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        pdt = npl['nef_spectrum_dimension_transfer']
        spectrum_dimension_transfer_1 = {'dimension_1': '1',
                                         'dimension_2': '2',
                                         'transfer_type': 'through-space'}
        pdt.append(spectrum_dimension_transfer_1)

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        spectrum_dimension_transfer_2 = {'dimension_1': '2',
                                         'dimension_2': '3',
                                         'transfer_type': 'onebond',
                                         'is_indirect': 'false'}

        pdt.append(spectrum_dimension_transfer_2)
        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'],
                         ['nef_nmr_spectrum_cnoesy1:nef_spectrum_dimension_transfer item 0: missing is_indirect label.'])


    def test_nef_peak_list_peak_loop(self):
        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        npl = self.nef['nef_nmr_spectrum_cnoesy1'] = OrderedDict()
        npl['sf_category'] = 'nef_nmr_spectrum'
        npl['sf_framecode'] = 'nef_nmr_spectrum_cnoesy1'
        npl['num_dimensions'] = '3'
        npl['chemical_shift_list'] = 'nef_chemical_shift_list_1'
        npl['experiment_classification'] = 'H_H[N].through-space'
        npl['experiment_type'] = '15N-NOESY-HSQC'
        npl['nef_spectrum_dimension'] = []
        npl['nef_spectrum_dimension_transfer'] = []
        npl['nef_peak'] = []

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        pd = npl['nef_spectrum_dimension']
        spectrum_dimension_1 = {'dimension_id': '1',
                                'axis_unit': 'ppm',
                                'axis_code': '1H',
                                'spectrometer_frequency': '500.139',
                                'spectral_width': '10.4',
                                'value_first_point': '9.9',
                                'folding': 'circular',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'false',}
        spectrum_dimension_2 = {'dimension_id': '2',
                                'axis_unit': 'ppm',
                                'axis_code': '15N',
                                'spectrometer_frequency': '98.37',
                                'spectral_width': '30.7',
                                'value_first_point': '127.0',
                                'folding': 'circular',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'false',}
        spectrum_dimension_3 = {'dimension_id': '1',
                                'axis_unit': 'ppm',
                                'axis_code': '1H',
                                'spectrometer_frequency': '500.139',
                                'spectral_width': '14.2',
                                'value_first_point': '11.8',
                                'folding': 'none',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'true',}
        pd.append(spectrum_dimension_1)
        pd.append(spectrum_dimension_2)
        pd.append(spectrum_dimension_3)

        pl = npl['nef_peak']
        peak_1 = {'ordinal': '1',
                  'peak_id': '1',
                  'volume': '7.3E7',
                  'volume_uncertainty': '5.1E6',
                  'height': '3.3E7',
                  'height_uncertainty': '1.1E6',
                  'position_1': '3.2',
                  'position_uncertainty_1': '0.05',
                  'position_2': '119.5',
                  'position_uncertainty_2': '0.5',
                  'position_3': '8.3',
                  'position_uncertainty_3': '0.03',
                  'chain_code_1': 'A',
                  'sequence_code_1': '19',
                  'residue_type_1': 'LEU',
                  'atom_name_1': 'HBY',
                  'chain_code_2': 'A',
                  'sequence_code_2': '17',
                  'residue_type_2': 'GLN',
                  'atom_name_2': 'N',
                  'chain_code_3': 'A',
                  'sequence_code_3': '17',
                  'residue_type_3': 'GLN',
                  'atom_name_3': 'H',}
        pl.append(peak_1)

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

    def test_nef_peak_list_peak_loop_inconsistent_peak_dimensions(self):
        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        npl = self.nef['nef_nmr_spectrum_cnoesy1'] = OrderedDict()
        npl['sf_category'] = 'nef_nmr_spectrum'
        npl['sf_framecode'] = 'nef_nmr_spectrum_cnoesy1'
        npl['num_dimensions'] = '3'
        npl['chemical_shift_list'] = 'nef_chemical_shift_list_1'
        npl['experiment_classification'] = 'H_H[N].through-space'
        npl['experiment_type'] = '15N-NOESY-HSQC'
        npl['nef_spectrum_dimension'] = []
        npl['nef_spectrum_dimension_transfer'] = []
        npl['nef_peak'] = []

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        pd = npl['nef_spectrum_dimension']
        spectrum_dimension_1 = {'dimension_id': '1',
                                'axis_unit': 'ppm',
                                'axis_code': '1H',
                                'spectrometer_frequency': '500.139',
                                'spectral_width': '10.4',
                                'value_first_point': '9.9',
                                'folding': 'circular',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'false',}
        spectrum_dimension_2 = {'dimension_id': '2',
                                'axis_unit': 'ppm',
                                'axis_code': '15N',
                                'spectrometer_frequency': '98.37',
                                'spectral_width': '30.7',
                                'value_first_point': '127.0',
                                'folding': 'circular',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'false',}
        spectrum_dimension_3 = {'dimension_id': '1',
                                'axis_unit': 'ppm',
                                'axis_code': '1H',
                                'spectrometer_frequency': '500.139',
                                'spectral_width': '14.2',
                                'value_first_point': '11.8',
                                'folding': 'none',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'true',}
        pd.append(spectrum_dimension_1)
        pd.append(spectrum_dimension_2)
        pd.append(spectrum_dimension_3)

        pl = npl['nef_peak']
        peak_1 = {'ordinal': '1',
                  'peak_id': '1',
                  'volume': '7.3E7',
                  'volume_uncertainty': '5.1E6',
                  'height': '3.3E7',
                  'height_uncertainty': '1.1E6',
                  'position_1': '3.2',
                  'position_uncertainty_1': '0.05',
                  'position_2': '119.5',
                  'position_uncertainty_2': '0.5',
                  'chain_code_1': 'A',
                  'sequence_code_1': '19',
                  'residue_type_1': 'LEU',
                  'atom_name_1': 'HBY',
                  'chain_code_2': 'A',
                  'sequence_code_2': '17',
                  'residue_type_2': 'GLN',
                  'atom_name_2': 'N',}
        pl.append(peak_1)

        self.assertEqual(len(self.v._validate_peak_lists()['PEAK_LISTS']), 5)
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_peak entry 1: missing position_3 label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_peak entry 1: missing chain_code_3 label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_peak entry 1: missing sequence_code_3 label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_peak entry 1: missing residue_type_3 label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_peak entry 1: missing atom_name_3 label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])

    def test_nef_peak_list_peak_loop_inconsistent_optional_fields(self):
        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        npl = self.nef['nef_nmr_spectrum_cnoesy1'] = OrderedDict()
        npl['sf_category'] = 'nef_nmr_spectrum'
        npl['sf_framecode'] = 'nef_nmr_spectrum_cnoesy1'
        npl['num_dimensions'] = '3'
        npl['chemical_shift_list'] = 'nef_chemical_shift_list_1'
        npl['experiment_classification'] = 'H_H[N].through-space'
        npl['experiment_type'] = '15N-NOESY-HSQC'
        npl['nef_spectrum_dimension'] = []
        npl['nef_spectrum_dimension_transfer'] = []
        npl['nef_peak'] = []

        self.assertEqual(self.v._validate_peak_lists()['PEAK_LISTS'], [])

        pd = npl['nef_spectrum_dimension']
        spectrum_dimension_1 = {'dimension_id': '1',
                                'axis_unit': 'ppm',
                                'axis_code': '1H',
                                'spectrometer_frequency': '500.139',
                                'spectral_width': '10.4',
                                'value_first_point': '9.9',
                                'folding': 'circular',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'false',}
        spectrum_dimension_2 = {'dimension_id': '2',
                                'axis_unit': 'ppm',
                                'axis_code': '15N',
                                'spectrometer_frequency': '98.37',
                                'spectral_width': '30.7',
                                'value_first_point': '127.0',
                                'folding': 'circular',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'false',}
        spectrum_dimension_3 = {'dimension_id': '1',
                                'axis_unit': 'ppm',
                                'axis_code': '1H',
                                'spectrometer_frequency': '500.139',
                                'spectral_width': '14.2',
                                'value_first_point': '11.8',
                                'folding': 'none',
                                'absolute_peak_positions': 'true',
                                'is_acquisition': 'true',}
        pd.append(spectrum_dimension_1)
        pd.append(spectrum_dimension_2)
        pd.append(spectrum_dimension_3)

        pl = npl['nef_peak']
        peak_1 = {'ordinal': '1',
                  'peak_id': '1',
                  'volume': '7.3E7',
                  'volume_uncertainty': '5.1E6',
                  'height': '3.3E7',
                  'height_uncertainty': '1.1E6',
                  'position_1': '3.2',
                  'position_uncertainty_1': '0.05',
                  'position_2': '119.5',
                  'position_uncertainty_2': '0.5',
                  'position_3': '8.3',
                  'position_uncertainty_3': '0.03',
                  'chain_code_1': 'A',
                  'sequence_code_1': '19',
                  'residue_type_1': 'LEU',
                  'atom_name_1': 'HBY',
                  'chain_code_2': 'A',
                  'sequence_code_2': '17',
                  'residue_type_2': 'GLN',
                  'atom_name_2': 'N',
                  'chain_code_3': 'A',
                  'sequence_code_3': '17',
                  'residue_type_3': 'GLN',
                  'atom_name_3': 'H',}
        peak_2 = {'ordinal': '1',
                  'peak_id': '1',
                  'volume': '7.3E7',
                  'volume_uncertainty': '5.1E6',
                  'height': '3.3E7',
                  'height_uncertainty': '1.1E6',
                  'position_1': '3.2',
                  'position_uncertainty_1': '0.05',
                  'position_2': '119.5',
                  'position_uncertainty_2': '0.5',
                  'position_3': '8.3',
                  'chain_code_1': 'A',
                  'sequence_code_1': '20',
                  'residue_type_1': 'CYS',
                  'atom_name_1': 'HBX',
                  'chain_code_2': 'A',
                  'sequence_code_2': '17',
                  'residue_type_2': 'GLN',
                  'atom_name_2': 'N',
                  'chain_code_3': 'A',
                  'sequence_code_3': '17',
                  'residue_type_3': 'GLN',
                  'atom_name_3': 'H',}
        pl.append(peak_1)
        pl.append(peak_2)

        self.assertEqual(len(self.v._validate_peak_lists()['PEAK_LISTS']), 1)
        self.assertIn('nef_nmr_spectrum_cnoesy1:nef_peak item 1: missing position_uncertainty_3 label.',
                      self.v._validate_peak_lists()['PEAK_LISTS'])


    def test_linkage_table(self):
        self.assertEqual(self.v._validate_linkage_table()['LINKAGE_TABLES'], [])

        npl = self.nef['nef_peak_restraint_links'] = OrderedDict()
        npl['sf_category'] = 'nef_peak_restraint_links'
        npl['sf_framecode'] = 'nef_peak_restraint_links'
        npl['nef_peak_restraint_link'] = []

        self.assertEqual(self.v._validate_linkage_table()['LINKAGE_TABLES'], [])

        link_1 = {'nmr_spectrum_id': 'nef_nmr_spectrum_cnoesy1',
                  'peak_id': '1',
                  'restraint_list_id': 'nef_distance_restraint_list_L1',
                  'restraint_id': '73' }
        npl['nef_peak_restraint_link'].append(link_1)
        self.assertEqual(self.v._validate_linkage_table()['LINKAGE_TABLES'], [])


    def test_full_validation(self):
        self.assertFalse(self.v.isValid())

        nef_sequence_item = {'chain_code': 'A',
                             'sequence_code': '1',
                             'residue_type': 'ALA',
                             'linking': '.',
                             'residue_variant': '.'}
        self.nef['nef_molecular_system']['nef_sequence'].append(nef_sequence_item)

        self.assertTrue(self.v.isValid())


if __name__ == '__main__':
    unittest.main()