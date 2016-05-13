from __future__ import unicode_literals, print_function, absolute_import, division

__author__ = 'TJ Ragan'

import unittest

from collections import OrderedDict
from .. import NEFreader
writer =  NEFreader.writer

class Test_nef_write_functions( unittest.TestCase ):
    def setUp(self):
        self.nef = NEFreader.Nef()
        self.populatedNef = NEFreader.Nef()
        self.populatedNef['nef_molecular_system']['nef_sequence'].append(
                OrderedDict((('chain_code', 'A'),
                             ('sequence_code', '1'),
                             ('residue_type', 'ALA'),
                             ('linking', 'middle'),
                             ('residue_variant', '.')
                            )))
        del(self.populatedNef['nef_chemical_shift_list_1'])


    def test_datablock( self ):
        self.nef.datablock = 'TestDataBlockName'
        self.assertEqual('data_TestDataBlockName\n', writer._datablockText(self.nef))

    def test_saveframe_header(self):
        self.assertEqual('save_nef_nmr_meta_data\n',
                         writer._saveframeHeaderText(self.nef, 'nef_nmr_meta_data'))
        self.assertEqual('save_nef_molecular_system\n',
                         writer._saveframeHeaderText(self.nef, 'nef_molecular_system'))
        self.assertEqual('save_nef_chemical_shift_list_1\n',
                         writer._saveframeHeaderText(self.nef, 'nef_chemical_shift_list_1'))

    def test_dataLabel(self):
        self.assertEqual('_nef_nmr_meta_data.sf_category',
                         writer._dataLabelText(self.nef['nef_nmr_meta_data'], 'sf_category'))

    def test_dataValue(self):
        self.assertEqual('nef_nmr_meta_data',
                         writer._dataValueText(self.nef['nef_nmr_meta_data'], 'sf_category'))

    def test_dataItem(self):
        self.assertEqual('  _nef_nmr_meta_data.sf_category\tnef_nmr_meta_data\n',
                         writer._dataItemText(self.nef['nef_nmr_meta_data'], 'sf_category'))

    def test_loop_header(self):
        self.assertEqual('  loop_\n',
                         writer._loopHeaderText(self.nef['nef_molecular_system'], 'nef_sequence'))

    def test_saveframe_footer(self):
        self.assertEqual('save_\n',
                         writer._saveframeFooterText(self.nef, 'nef_molecular_system'))

    def test_loop_footer(self):
        self.assertEqual('  stop_\n',
                         writer._loopFooterText(self.nef['nef_molecular_system'], 'nef_sequence'))

    def test_saveframe_items_no_loop(self):
        saveframeText = writer._saveframeItemsText(self.nef, 'nef_nmr_meta_data').split('\n')
        self.assertEqual('  _nef_nmr_meta_data.sf_category\tnef_nmr_meta_data',
                         saveframeText[0])
        self.assertEqual('  _nef_nmr_meta_data.sf_framecode\tnef_nmr_meta_data',
                         saveframeText[1])
        self.assertIn('  _nef_nmr_meta_data.format_name\tNmr_Exchange_Format', saveframeText)


    def test_saveframe_items(self):
        saveframeText = writer._saveframeItemsText(self.nef, 'nef_molecular_system').split('\n')
        self.assertEqual('  _nef_molecular_system.sf_category\tnef_molecular_system',
                         saveframeText[0])
        self.assertEqual('  _nef_molecular_system.sf_framecode\tnef_molecular_system',
                         saveframeText[1])
        self.assertEqual(3, len(saveframeText))


    def _test_empty_loop_labels(self):
        print(writer._loopLabelsText(self.nef['nef_molecular_system'], 'nef_sequence'))

    def test_loop(self):
        loopText = writer._loopText(self.populatedNef['nef_molecular_system'], 'nef_sequence').split('\n')

        self.assertEqual('  loop_', loopText[0])
        self.assertEqual('    _nef_sequence.chain_code', loopText[1])
        self.assertEqual('    _nef_sequence.sequence_code', loopText[2])
        self.assertEqual('    _nef_sequence.residue_type', loopText[3])
        self.assertEqual('    _nef_sequence.linking', loopText[4])
        self.assertEqual('    _nef_sequence.residue_variant', loopText[5])
        self.assertEqual('', loopText[6])


        self.assertEqual('  stop_', loopText[-3])
        self.assertEqual('', loopText[-2])
        self.assertEqual('', loopText[-1])


    def test_saveframe_text_no_loops(self):
        saveframeText = writer._saveframeText(self.nef, 'nef_nmr_meta_data').split('\n')
        self.assertEqual('save_nef_nmr_meta_data', saveframeText[0])
        self.assertEqual('save_', saveframeText[-3])
        self.assertNotIn('  loop_', saveframeText)


    def test_saveframe_text_empty_loop(self):
        with self.assertRaises(IndexError):
            writer._loopText(self.nef['nef_molecular_system'], 'nef_sequence')

    def test_saveframe_text(self):
        saveframeText = writer._saveframeText(self.populatedNef, 'nef_molecular_system').split('\n')

        self.assertEqual('save_nef_molecular_system', saveframeText[0])
        self.assertEqual('save_', saveframeText[-3])
        self.assertIn('  loop_', saveframeText)

    def test_find_loops_in_saveframe(self):
        self.assertEqual(['nef_sequence',],
                         writer._findLoopsInSaveframe(self.nef['nef_molecular_system']))


    def test_nef_to_text(self):
        self.populatedNef['nef_molecular_system']['nef_sequence'][0]['chain_code'] = 'A\n*'
        nef_text = writer.nefToText(self.populatedNef)
        # TODO: add tests here

    # TODO: add tests for multiline comments
    # TODO: add functionality for multilevel quotes

if __name__ == '__main__':
    unittest.main()
