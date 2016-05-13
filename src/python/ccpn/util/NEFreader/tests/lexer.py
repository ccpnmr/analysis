from __future__ import absolute_import, print_function, unicode_literals
__author__ = 'TJ Ragan'

import unittest

from .. import NEFreader


class Test_Tokenizer_util_functions(unittest.TestCase):
 
    def setUp(self):
        self.t = NEFreader.Lexer()

    # def test_uncommented_newline_reset_state(self):
    #     self.t._state = 'invalid state for testing only'
    #     self.t._token = ''
    #     self.t._uncommented_newline()
    #     self.assertEquals( self.t._state, 'start' )
    #
    # def test_uncommented_newline_empty_token(self):
    #     self.t._token = ''
    #     self.t._uncommented_newline()
    #     self.assertEquals( self.t.tokens, ['\n'] )
    #
    # def test_uncommented_newline_nonempty_token(self):
    #     self.t._state = 'in token'
    #     self.t._token = ['t','e','s','t']
    #     self.t._uncommented_newline()
    #     self.assertEquals( self.t.tokens, ['test','\n'] )


class Test_Tokenizer_tokenize(unittest.TestCase):

    def setUp(self):
        self.l = NEFreader.Lexer()

    def test_tokenizer_setup_with_chars(self):
        t = NEFreader.Lexer('test')
        self.assertEquals(t.chars, 'test')

    def test_tokenizer_tokenize_with_predefined_chars(self):
        t = NEFreader.Lexer('test')
        tokens = t.tokenize()
        self.assertEquals(tokens, ['test'])

    def test_tokenize_noncomment_without_newline(self):
        self.l.tokenize('5.324')
        self.assertEquals(self.l.tokens, ['5.324'])

    def test_tokenize_noncomment2_without_newline(self):
        self.l.tokenize('light_blue')
        self.assertEquals( self.l.tokens, ['light_blue'] )

    def test_tokenize_noncomment_with_newline(self):
        self.l.tokenize('test\n')
        self.assertEquals( self.l.tokens, ['test', '\n'] )


    def test_tokenize_quoted_string(self):
        self.l.tokenize("""'low melting point' """)
        self.assertEquals( self.l.tokens, ["'low melting point'"] )

    def test_tokenize_quoted_string_with_internal_quote(self):
        self.l.tokenize("""'classed as 'unknown """)
        self.assertEquals( self.l.tokens, ["'classed as 'unknown"] )

    def test_tokenize_single_quoted_string_with_tab(self):
        self.l.tokenize("""'test string'\t""")
        self.assertEquals( self.l.tokens, ["'test string'"] )

    def test_tokenize_single_quoted_string_with_newline(self):
        self.l.tokenize("""'test string'\n""")
        self.assertEquals( self.l.tokens, ["'test string'", '\n'] )


    def test_tokenize_double_quoted_string(self):
        self.l.tokenize('''"low melting point" ''')
        self.assertEquals( self.l.tokens, ['"low melting point"'] )

    def test_tokenize_double_quoted_string_with_internal_quote(self):
        self.l.tokenize('''"classed as 'unknown" ''')
        self.assertEquals( self.l.tokens, ['''"classed as 'unknown"'''] )

    def test_tokenize_double_quoted_string_with_tab(self):
        self.l.tokenize('''"test string"\t''')
        self.assertEquals( self.l.tokens, ['"test string"'] )

    def test_tokenize_double_quoted_string_with_newline(self):
        self.l.tokenize('''"test string"\n''')
        self.assertEquals( self.l.tokens, ['"test string"', '\n'] )


    def test_tokenize_semicolon_quoted_string(self):
        s = """;\nDepartment of Computer Science\nUniversity of Western Australia\n;"""
        t_s = """\nDepartment of Computer Science\nUniversity of Western Australia\n"""
        self.l.tokenize(s)
        self.assertEquals(self.l.tokens, [s] )

    def test_tokenize_semicolon_quoted_string2(self):
        s = """;Department of Computer Science\nUniversity of Western Australia\n;"""
        t_s = """Department of Computer Science\nUniversity of Western Australia\n"""
        self.l.tokenize(s)
        self.assertEquals(self.l.tokens, [s] )

    def test_tokenize_semicolon_quoted_string3(self):
        s = """;\nDepartment of Computer Science\nUniversity of Western Australia\n;test"""
        t_s = """;\nDepartment of Computer Science\nUniversity of Western Australia\n;"""
        self.l.tokenize(s)
        self.assertEquals(self.l.tokens, [t_s, 'test'] )

    def test_tokenize_string_with_semicolon(self):
        s = """Department of Computer Science;University of\nWestern Australia"""
        self.l.tokenize(s)
        self.assertEquals(self.l.tokens, ['Department', 'of', 'Computer', 'Science;University',
                                          'of', '\n', 'Western', 'Australia'] )

    def test_tokenize_semicolons_following_spaces(self):
        s = """ ;\n rmsdrange:=1-93\n ;\n"""
        self.l.tokenize(s)
        self.assertEquals(self.l.tokens, [';', '\n','rmsdrange:=1-93', '\n', ';','\n'])

    def test_tokenize_semicolons_following_spaces_in_semicolon_quoted_block(self):
        s = """; ;\n rmsdrange:=1-93\n ;\n;"""
        self.l.tokenize(s)
        self.assertEquals(self.l.tokens, ['; ;\n rmsdrange:=1-93\n ;\n;'])

    def test_tokenize_general_string(self):
        self.l.tokenize('nef_nmr_meta_data')
        self.assertEquals( self.l.tokens, ['nef_nmr_meta_data'] )

    def test_tokenize_string_with_period(self):
        self.l.tokenize('_nef_nmr_meta_data.sf_category')
        self.assertEquals( self.l.tokens, ['_nef_nmr_meta_data.sf_category'] )

    def test_tokenize_string_with_leading_underscore(self):
        self.l.tokenize('_nef_nmr_meta_data.sf_category')
        self.assertEquals( self.l.tokens, ['_nef_nmr_meta_data.sf_category'] )


    def test_tokenize_bare_newline(self):
        self.l.tokenize('\n')
        self.assertEquals( self.l.tokens, ['\n'] )

    def test_tokenize_bare_newlines(self):
        self.l.tokenize('\n\n\n')
        self.assertEquals( self.l.tokens, ['\n']*3 )


    def test_tokenize_tab(self):
        self.l.tokenize('\t')
        self.assertEquals( self.l.tokens, [] )


    def test_tokenize_space(self):
        self.l.tokenize(' ')
        self.assertEquals( self.l.tokens, [] )


    def test_tokenize_comment_with_newline(self):
        self.l.tokenize('#=\n')
        self.assertEquals( self.l.tokens, ['#=','\n'] )

    def test_tokenize_comment_without_newline(self):
        self.l.tokenize('#=')
        self.assertEquals( self.l.tokens, ['#='] )
