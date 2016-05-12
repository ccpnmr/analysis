from __future__ import absolute_import, print_function, unicode_literals
__author__ = 'TJ Ragan'

import unittest

from .. import NEFreader


class Test_bare_nef(unittest.TestCase):

    def setUp(self):
        self.nef = NEFreader.Nef()


    def test_bare_nef_data_block(self):
        self.assertEqual(self.nef.datablock, 'DEFAULT')

    def test_bare_nef_metadata_structure(self):
        metadata = self.nef['nef_nmr_meta_data']
        self.assertIn('sf_category', metadata)
        self.assertIn('sf_framecode', metadata)
        self.assertEqual(metadata['sf_category'], metadata['sf_framecode'])
        self.assertIn('format_name', metadata)
        self.assertIn('format_version', metadata)
        self.assertIn('program_name', metadata)
        self.assertIn('program_version', metadata)
        self.assertIn('creation_date', metadata)
        self.assertIn('uuid', metadata)

    def test_bare_nef_molecular_system_structure(self):
        molecularSystem = self.nef['nef_molecular_system']
        self.assertIn('sf_category', molecularSystem)
        self.assertIn('sf_framecode', molecularSystem)
        self.assertEqual(molecularSystem['sf_category'], molecularSystem['sf_framecode'])

    def test_bare_chemical_shift_list_structure(self):
        chemicalShiftList = self.nef['nef_chemical_shift_list_1']
        self.assertIn('sf_category', chemicalShiftList)
        self.assertIn('sf_framecode', chemicalShiftList)
        self.assertEqual(chemicalShiftList['sf_category']+'_1',
                         chemicalShiftList['sf_framecode'])


class Test_nef_convenience_functions(unittest.TestCase):

    def setUp(self):
        self.nef = NEFreader.Nef()


    def test_add_chemical_shift_list(self):
        self.nef.add_chemical_shift_list(name='cs_list', cs_units='ppm')

        self.assertEqual(self.nef['cs_list']['sf_framecode'], 'cs_list')
        self.assertEqual(self.nef['cs_list']['sf_category'], 'nef_chemical_shift_list')
        self.assertEqual(self.nef['cs_list']['atom_chem_shift_units'], 'ppm')
        self.assertEqual(self.nef['cs_list']['nef_chemical_shift'], [])


    def test_add_distance_restraint_list_minimal(self):
        self.nef.add_distance_restraint_list(name='dist_list',
                                             potential_type='square-well-parabolic-linear')

        self.assertEqual(self.nef['dist_list']['sf_framecode'], 'dist_list')
        self.assertEqual(self.nef['dist_list']['sf_category'], 'nef_distance_restraint_list')
        self.assertEqual(self.nef['dist_list']['potential_type'], 'square-well-parabolic-linear')
        self.assertEqual(self.nef['dist_list']['nef_distance_restraint'], [])

    def test_add_distance_restraint_list_all_optional_fields(self):
        self.nef.add_distance_restraint_list(name='dist_list',
                                             potential_type='square-well-parabolic-linear',
                                             restraint_origin='noe')

        self.assertEqual(self.nef['dist_list']['sf_framecode'], 'dist_list')
        self.assertEqual(self.nef['dist_list']['sf_category'], 'nef_distance_restraint_list')
        self.assertEqual(self.nef['dist_list']['potential_type'], 'square-well-parabolic-linear')
        self.assertEqual(self.nef['dist_list']['restraint_origin'], 'noe')
        self.assertEqual(self.nef['dist_list']['nef_distance_restraint'], [])


    def test_add_dihedral_restraint_list_minimal(self):
        self.nef.add_dihedral_restraint_list(name='dih_list',
                                             potential_type='square-well-parabolic')

        self.assertEqual(self.nef['dih_list']['sf_framecode'], 'dih_list')
        self.assertEqual(self.nef['dih_list']['sf_category'], 'nef_dihedral_restraint_list')
        self.assertEqual(self.nef['dih_list']['potential_type'], 'square-well-parabolic')
        self.assertEqual(self.nef['dih_list']['nef_dihedral_restraint'], [])

    def test_add_dihedral_restraint_list_all_optional_fields(self):
        self.nef.add_dihedral_restraint_list(name='dih_list',
                                             potential_type='square-well-parabolic',
                                             restraint_origin='talos')

        self.assertEqual(self.nef['dih_list']['sf_framecode'], 'dih_list')
        self.assertEqual(self.nef['dih_list']['sf_category'], 'nef_dihedral_restraint_list')
        self.assertEqual(self.nef['dih_list']['potential_type'], 'square-well-parabolic')
        self.assertEqual(self.nef['dih_list']['restraint_origin'], 'talos')
        self.assertEqual(self.nef['dih_list']['nef_dihedral_restraint'], [])


    def test_add_rdc_restraint_list_minimal(self):
        self.nef.add_rdc_restraint_list(name='rdc_list',
                                             potential_type='log-normal')

        self.assertEqual(self.nef['rdc_list']['sf_framecode'], 'rdc_list')
        self.assertEqual(self.nef['rdc_list']['sf_category'], 'nef_rdc_restraint_list')
        self.assertEqual(self.nef['rdc_list']['potential_type'], 'log-normal')
        self.assertEqual(self.nef['rdc_list']['nef_rdc_restraint'], [])

    def test_add_rdc_restraint_list_all_optional_fields(self):
        self.nef.add_rdc_restraint_list(name='rdc_list',
                                        potential_type='log-normal',
                                        restraint_origin='measured',
                                        tensor_magnitude='11.0000',
                                        tensor_rhombicity='0.0670',
                                        tensor_chain_code='C',
                                        tensor_sequence_code='900',
                                        tensor_residue_type='TNSR')

        self.assertEqual(self.nef['rdc_list']['sf_framecode'], 'rdc_list')
        self.assertEqual(self.nef['rdc_list']['sf_category'], 'nef_rdc_restraint_list')
        self.assertEqual(self.nef['rdc_list']['potential_type'], 'log-normal')
        self.assertEqual(self.nef['rdc_list']['restraint_origin'], 'measured')
        self.assertEqual(self.nef['rdc_list']['tensor_magnitude'], '11.0000')
        self.assertEqual(self.nef['rdc_list']['tensor_rhombicity'], '0.0670')
        self.assertEqual(self.nef['rdc_list']['tensor_chain_code'], 'C')
        self.assertEqual(self.nef['rdc_list']['tensor_sequence_code'], '900')
        self.assertEqual(self.nef['rdc_list']['tensor_residue_type'], 'TNSR')
        self.assertEqual(self.nef['rdc_list']['nef_rdc_restraint'], [])


    def test_add_peak_list_minimal(self):
        self.nef.add_chemical_shift_list('cs_list')
        self.nef.add_peak_list(name='peak_list',
                               num_dimensions='3',
                               chemical_shift_list='cs_list')

        self.assertEqual(self.nef['peak_list']['sf_framecode'], 'peak_list')
        self.assertEqual(self.nef['peak_list']['sf_category'], 'nef_nmr_spectrum')
        self.assertEqual(self.nef['peak_list']['num_dimensions'], '3')
        self.assertEqual(self.nef['peak_list']['chemical_shift_list'], 'cs_list')
        self.assertEqual(self.nef['peak_list']['nef_spectrum_dimension'], [])

    def test_add_peak_list_all_optional_fields(self):
        self.nef.add_chemical_shift_list('cs_list')
        self.nef.add_peak_list(name='peak_list',
                               num_dimensions='3',
                               chemical_shift_list='cs_list',
                               experiment_classification='H_H[N].through-space',
                               experiment_type='15N-NOESY-HSQC')

        self.assertEqual(self.nef['peak_list']['sf_framecode'], 'peak_list')
        self.assertEqual(self.nef['peak_list']['sf_category'], 'nef_nmr_spectrum')
        self.assertEqual(self.nef['peak_list']['num_dimensions'], '3')
        self.assertEqual(self.nef['peak_list']['chemical_shift_list'], 'cs_list')
        self.assertEqual(self.nef['peak_list']['experiment_classification'], 'H_H[N].through-space')
        self.assertEqual(self.nef['peak_list']['experiment_type'], '15N-NOESY-HSQC')
        self.assertEqual(self.nef['peak_list']['nef_spectrum_dimension'], [])


    def test_add_linkage_table(self):
        self.nef.add_linkage_table()

        self.assertEqual(self.nef['nef_peak_restraint_links']['sf_framecode'], 'nef_peak_restraint_links')
        self.assertEqual(self.nef['nef_peak_restraint_links']['sf_category'], 'nef_peak_restraint_links')


    def test_add_nonNEF_saveframe(self):
        self.nef.add_saveframe(name='arbitrary_name', category='arbitrary_category')

        self.assertEqual(self.nef['arbitrary_name']['sf_framecode'], 'arbitrary_name')
        self.assertEqual(self.nef['arbitrary_name']['sf_category'], 'arbitrary_category')


if __name__ == '__main__':
    unittest.main()