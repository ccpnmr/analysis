from __future__ import absolute_import, print_function, unicode_literals
__author__ = 'TJ Ragan'

import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
from collections import OrderedDict

from .. import NEFreader


class Test_Parser(unittest.TestCase):

    def setUp(self):
        self.d = OrderedDict()
        self.p = NEFreader.Parser(target=self.d)


    def test_parser_setup_without_target(self):
        p = NEFreader.Parser()
        self.assertEqual(type(p.target), OrderedDict)

    def test_parser_parse_with_predefined_tokens(self):
        p = NEFreader.Parser(tokens=['data_nef_my_nmr_project'])
        d = p.parse()
        self.assertEquals(d.datablock, 'nef_my_nmr_project')

    def test_parse_whitespace(self):
        self.p.parse(['\n'])
        self.assertEquals(self.d, dict())


    def test_parse_comments(self):
        self.p.parse(['#  Nmr Exchange Format\n'])
        self.assertEquals(self.d, dict())

    def test_parse_comments_with_key(self):
        self.p.parse(['# key: d'])
        self.assertEquals(self.p._loop_key, '# key: d')


    def test_parse_data_block_declaration(self):
        self.p.parse(['data_nef_my_nmr_project'])
        self.assertTrue(hasattr(self.d, 'datablock'))

    def test_parse_multiple_data_blocks(self):
        self.assertRaises(Exception, self.p.parse,
                          ['data_nef_my_nmr_project','data_nef_my_nmr_project_2'])

    def test_parse_without_data_block_declaration(self):
        self.assertRaises(Exception, self.p.parse, ['save_nef_nmr_meta_data'])


    def test_parse_saveframe(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('save_')

        self.p.parse(tokens)

        self.assertTrue('nef_nmr_meta_data' in self.p.target.keys())
        self.assertEquals(type(self.p.target['nef_nmr_meta_data']), OrderedDict)

    def test_parse_saveframes(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('save_')
        tokens.append('save_cyana_additional_data_1')
        tokens.append('save_')

        self.p.parse(tokens)

        self.assertTrue('nef_nmr_meta_data' in self.p.target.keys())
        self.assertEquals(type(self.p.target['nef_nmr_meta_data']), OrderedDict)
        self.assertTrue('cyana_additional_data_1' in self.p.target.keys())
        self.assertEquals(type(self.p.target['cyana_additional_data_1']), OrderedDict)


    def test_parse_nested_saveframes(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('save_cyana_additional_data_1')
        tokens.append('save_')
        tokens.append('save_')

        self.assertRaises(Exception, self.p.parse, tokens)

    def test_parse_unnamed_saveframes(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_')

        self.assertRaises(Exception, self.p.parse, tokens)

    def test_parse_loop(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('loop_')
        tokens.append('_nef_related_entries.database_name')
        tokens.append('BMRB')
        tokens.append('stop_')
        tokens.append('save_')

        self.p.parse(tokens)

        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_related_entries']
                                       [0]['database_name'], 'BMRB')


    def test_parse_loop_with_quoted_data_value_with_starting_underscore(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('loop_')
        tokens.append('_nef_related_entries.database_name')
        tokens.append('"_BMRB"')
        tokens.append('stop_')
        tokens.append('save_')

        self.p.parse(tokens)

        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_related_entries']
                                       [0]['database_name'], '_BMRB')


    def test_parse_loops(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('loop_')
        tokens.append('_nef_related_entries.database_name')
        tokens.append('BMRB')
        tokens.append('stop_')
        tokens.append('loop_')
        tokens.append('_nef_program_script.program_name')
        tokens.append('CYANA')
        tokens.append('stop_')
        tokens.append('save_')

        self.p.parse(tokens)

        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_related_entries']
                                       [0]['database_name'], 'BMRB')

        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_program_script']
                                       [0]['program_name'], 'CYANA')


    def test_parse_loop_without_stop(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('loop_')
        tokens.append('_nef_related_entries.database_name')
        tokens.append('BMRB')
        tokens.append('save_')

        self.p.parse(tokens)


        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_related_entries']
                                       [0]['database_name'], 'BMRB')


    def test_parse_loops_last_without_stop(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('loop_')
        tokens.append('_nef_related_entries.database_name')
        tokens.append('BMRB')
        tokens.append('stop_')
        tokens.append('loop_')
        tokens.append('_nef_program_script.program_name')
        tokens.append('CYANA')
        tokens.append('save_')

        self.p.parse(tokens)

        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_related_entries']
                                       [0]['database_name'], 'BMRB')


        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_program_script']
                                       [0]['program_name'], 'CYANA')

    def test_parse_loops_without_stop(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('loop_')
        tokens.append('_nef_related_entries.database_name')
        tokens.append('BMRB')

        tokens.append('loop_')
        tokens.append('_nef_program_script.program_name')
        tokens.append('CYANA')
        tokens.append('save_')

        self.assertRaises(Exception, self.p.parse, tokens)

    def test_parse_loops_without_stop_non_strict(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('loop_')
        tokens.append('_nef_related_entries.database_name')
        tokens.append('BMRB')

        tokens.append('loop_')
        tokens.append('_nef_program_script.program_name')
        tokens.append('CYANA')
        tokens.append('save_')

        self.p.strict = False
        self.p.parse(tokens)

        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_related_entries']
                                       [0]['database_name'], 'BMRB')

        self.assertEquals(self.p.target['nef_nmr_meta_data']
                                       ['nef_program_script']
                                       [0]['program_name'], 'CYANA')


    def test_parse_close_loop_without_opening_loop_first(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('stop_')

        self.assertRaises(Exception, self.p.parse, tokens)


    def test_parse_loops_mismatched_column_names(self):
        tokens = ['data_nef_my_nmr_project']
        tokens.append('save_nef_nmr_meta_data')
        tokens.append('loop_')
        tokens.append('_nef_related_entries.database_name')
        tokens.append('_nef_related_entrys.database_accession_code')
        tokens.append('BMRB')
        tokens.append('12345')
        tokens.append('stop_')
        tokens.append('save_')

        self.assertRaises(Exception, self.p.parse, tokens)

    def test_parse_loops_mismatched_column_names_non_strict(self):
        with patch('NEFreader.parser.logger') as l:
            tokens = ['data_nef_my_nmr_project']
            tokens.append('save_nef_nmr_meta_data')
            tokens.append('loop_')
            tokens.append('_nef_related_entries.database_name')
            tokens.append('_nef_related_entrys.database_accession_code')
            tokens.append('BMRB')
            tokens.append('12345')
            tokens.append('stop_')
            tokens.append('save_')

            self.p.strict = False
            self.p.parse(tokens)

            self.assertTrue(l.warning.called)
            self.assertEquals(self.p.target['nef_nmr_meta_data']['nef_related_entries']
                                           [0]['database_name'], 'BMRB')
            self.assertEquals(self.p.target['nef_nmr_meta_data']['nef_related_entries']
                                           [0]['database_accession_code'], '12345')




if __name__ == '__main__':
    unittest.main()