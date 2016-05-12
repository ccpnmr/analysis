from __future__ import absolute_import, print_function, unicode_literals
__author__ = 'TJ Ragan'

import unittest
import os
from collections import OrderedDict

from .. import NEFreader

# Done this way to make sure it works whatever teh current directory
test_file_dir =  os.path.join(NEFreader.__path__[0], '..', 'tests', 'test_files')


class Test_files(unittest.TestCase):

    def setUp(self):
        self.d = OrderedDict()
        self.t = NEFreader.Lexer()
        self.p = NEFreader.Parser(target=self.d)

    def test_annotated(self):
        # f_name = 'tests/test_files/Commented_Example.nef'
        f_name = os.path.join(test_file_dir, 'Commented_Example.nef')


        with open(f_name, 'r') as f:
            nef = f.read()

        tokens = self.t.tokenize(nef)
        self.p.parse(tokens)

    def test_read_file(self):
        # f_name = 'tests/test_files/Commented_Example.nef'
        f_name = os.path.join(test_file_dir, 'Commented_Example.nef')

        nef = NEFreader.Nef.from_file(f_name)

        self.assertEqual(nef.datablock, 'nef_my_nmr_project_1')
        self.assertIn('nef_nmr_meta_data', nef)
        self.assertIn('cyana_additional_data_1', nef)
        self.assertIn('nef_molecular_system', nef)
        self.assertIn('nef_chemical_shift_list_1', nef)
        self.assertIn('nef_distance_restraint_list_L1', nef)
        self.assertIn('nef_dihedral_restraint_list_L2', nef)
        self.assertIn('nef_rdc_restraint_list_1', nef)
        self.assertIn('nef_nmr_spectrum_cnoesy1', nef)
        self.assertIn('nef_nmr_spectrum_dummy15d', nef)
        self.assertIn('nef_peak_restraint_links', nef)


if __name__ == '__main__':
    unittest.main()