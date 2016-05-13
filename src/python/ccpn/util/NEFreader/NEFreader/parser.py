from __future__ import absolute_import, unicode_literals
__author__ = 'TJ Ragan'
__version__ = '0.1'

from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class Lexer(object):

    def __init__(self, chars=None):
        """
        :type chars: iterable
        """
        self.chars = chars
        self.tokens = []
        self._state = None
        self._newline = True
        self._token = None


    def tokenize(self, chars=None):
        if chars is None:
            chars = self.chars

        self._state = 'start'
        self._newline = True

        self.tokens = []
        self._token = []

        for c in chars:

            ### Newline whitespace
            if c == '\n':
                self._newline_char()

            ### Multi-line semicolon based strings
            elif (c == ';') and self._newline and (self._state == 'semicolon comment'):
                self._finish_semicolon_comment()
            elif (c == ';') and self._newline and (self._state != 'semicolon comment'):
                self._start_semicolon_comment()
            elif self._state == 'semicolon comment':
                self._continue_semicolon_comment(c)

            ### Comments
            elif c == '#':
                self._start_comment()
            elif self._state == 'comment':
                self._continue_comment(c)

            ### Quotes
            elif c in ('"', "'"):
                self._quote(c)
            ### Non-newline whitespace
            elif c in (' ', '\t'):
                self._whitespace(c)

            ### Actual characters
            else:
                self._actual_character(c)
        self._finish_token()

        return self.tokens

    def _quote(self, c):
        if self._state is 'start':
            self._start_quote(c)
        elif self._state is 'quoted':
            self._continue_quote(c)

    def _newline_char(self):
        self._newline = True
        if self._state != 'semicolon comment':
            self._uncommented_newline()
        else:
            self._semicolon_commented_newline()

    def _continue_quote(self, c):
        self._token.append(c)
        if c == self._quote_char:
            self._state = 'potential unquote'

    def _start_quote(self, c):
        self._quote_char = c
        self._token = [c]
        self._state = 'quoted'

    def _actual_character(self, c):
        self._newline = False
        if self._state == 'start':
            self._state = 'in token'
        elif self._state == 'potential unquote':
            self._state = 'quote'
        self._token.append(c)


    def _whitespace(self, c):
        self._newline = False
        if self._state == 'quoted':
            self._quoted_whitespace(c)
        elif self._state == 'potential unquote':
            self._potential_unquote()
        else:
            self._unquoted_whitespace()


    def _unquoted_whitespace(self):
        self._finish_token()
        self._state = 'start'


    def _finish_token(self):
        if len(self._token) > 0:
            self.tokens.append(''.join(self._token))
            self._token = []
        self._state = 'start'


    def _potential_unquote(self):
        self._token = self._token
        self._finish_token()
        self._state = 'start'


    def _quoted_whitespace(self, c):
        self._token.append(c)


    def _continue_comment(self, c):
        self._token.append(c)


    def _start_comment(self):
        self._state = 'comment'
        self._newline = False
        self._token = ['#']


    def _start_semicolon_comment(self):
        self._state = 'semicolon comment'
        self._newline = False
        self._token = [';']

    def _continue_semicolon_comment(self, c):
        self._newline = False
        self._token.append(c)


    def _finish_semicolon_comment(self):
        self._token.append(';')
        self._finish_token()
        self._state = 'start'


    def _semicolon_commented_newline(self):
        self._token.append('\n')


    def _uncommented_newline(self):
        if len(self._token) > 0:
            if self._state == 'potential unquote':
                self._token = self._token
        self._finish_token()
        self.tokens.append('\n')
        self._token = []





class Parser(object):

    def __init__(self, target=None, tokens=None, strict=True):
        """
        :type target: OrderedDict or Nef
        :type tokens: iterable[str]
        :type strict: bool
        """
        self.tokens = tokens
        self.strict = strict
        self._loop_key = None
        self._saveframe_name = None
        self._data_name = None
        if target is None:
            self.target = OrderedDict()
            self.no_target = True
        else:
            self.target = target
            self.no_target = False


    def read(self, file_like, strict=True):
        """
        Populate the NEF object from a file-like object

        :param file_like:
        :param strict: bool
        """
        tokenizer = Lexer()

        self.strict = strict
        self.parse(tokenizer.tokenize(file_like))

        return self.target


    def load(self, filename=None, strict=True):
        """
        Open a file on disk and use it to populate the NEF object.

        :param filename: str
        :param strict: bool
        """

        if filename is None:
            filename = self.input_filename
        else:
            self.input_filename = filename

        with open(filename, 'r') as f:
            self.read(f.read(), strict=strict)
        return self.target


    def parse(self, tokens=None):
        """
        Parse the token stream

        :type tokens: iterable or None
        :return: dict
        """
        if tokens is None:
            tokens = self.tokens

        self._loop_key = None
        self._saveframe_name = None
        self._data_name = None

        for i, t in enumerate(tokens):
            ### Newlines
            if t == '\n':
                pass

            ### Comments
            elif t.startswith(';') or t.startswith('"') or t.startswith("'"):
                self._quoted_data_value_token(i, t)

            ### Comments
            elif t.startswith('#'):
                self._comment_token(t)

            ### Required datablock declaration
            elif t.lower().startswith('data_'):
                self._datablock_token(t)
            elif not hasattr(self.target, 'datablock'):
                self._noncomment_token_outside_data_block(i)

            ### Globals (Are we using these?)
            elif t.lower().startswith('global_'):
                self._global_statement(t)

            ### Saveframes
            elif t.lower().startswith('save_'):
                self._save_token(i, t)

            ### Loops
            elif t.lower() == 'loop_':
                self._loop_token(i)
            elif t.lower() == 'stop_':
                self._stop_token(i)

            ### Data Names
            elif t.startswith('_'):
                self._data_name_token(i, t)

            ### Data Values
            else:
                self._data_value_token(i, t)

        if self.no_target:
            return self.target



    def _comment_token(self, t):
        """
        Begin line comment token

        Extract the key information if present

        :type t: str    # Token
        """
        if 'key:' in t.lower():
            self._loop_key = t


    def _datablock_token(self, t):
        """
        Data block name declaration

        Only one datablock is allowed per file

        :type t: str    # Token
        :raise Exception:
        """
        if not hasattr(self.target, 'datablock'):
            self.target.datablock = t[5:]
            self._state = 'start'
        else:
            raise Exception('Multiple datablocks not allowed.')

    def _noncomment_token_outside_data_block(self, i):
        """
        Non-commented text found (generally before) the data block is declared

        Other than comments, everything in the NEF must be inside the file's data block

        :type i: int    # Token number
        :raise Exception:
        """
        if self.strict:
            raise Exception('Token {}: NEF format requires all non-comments exist in a datablock.'
                            .format(i))
        else:
            self.target.datablock = 'data_nef_default'


    def _global_statement(self, t):
        raise NotImplementedError('Globals not allowed in NEF.')


    def _save_token(self, i, t):
        """
        save_* token, marking the begining or end of a saveframe

        Saveframes are declared with a `save_foo` token, and closed with a `save_` token.  This
          method dispatches to either open or close the save frame appropriately.

        :type i: int    # Token number
        :type t: str    # Token
        :raise Exception:
        """
        if t.lower() == 'save_':
            self._end_saveframe_token(i)
        else:
            self._start_saveframe_token(i, t)

    def _loop_token(self, i):
        """
        `loop_` token, marking the beginning of a loop

        Loops are opened a `loop_` token.  This method opens a loop, or throws an exception if one
          is already open and strict parsing is set.  If strict parsing is not set, it tries to
          deal with the problem by closing and finishing the current loop and opening a new one.

        :type i: int    # Token number
        :raise Exception:
        """
        if self._state.startswith('in loop'):
            if self.strict:
                raise Exception('Token {}: Nested loops are not allowed.'.format(i))
            else:
                self._finish_loop(i)
                self._start_loop()
        else:
            self._start_loop()

    def _stop_token(self, i):
        """
        `stop_` token, marking the end of a loop.

        Loops are closed with a `stop_` token.  This method closes and finishes a loop, or throws
          an exception if one isn't open and strict parsing is set.  If strict parsing is not set,
          it deals with the problem by simply raises a warning.

        :type i: int    # Token number
        :type t: str    # Token
        :raise Exception:
        """
        if self._state.startswith('in loop'):
            self._finish_loop(i)
        else:
            error_message = 'Token {}: Trying to close a loop without being in a loop.'.format(i)
            if self.strict:
                raise Exception(error_message)
            else:
                logger.warning(error_message)


    def _data_name_token(self, i, t):
        """
        `_foo` token, indicating a data name.

        Data names are indicated by a single leading underscore.  If they occur at the beginning of
          a loop, they represent the column names in that loop.  If they occur in a loop following
          data values, they close the loop.

        :type i: int    # Token number
        :type t: str    # Token
        :raise Exception:
        """
        self._data_name = t[1:]

        if self._state == 'in loop columns specification':
            self._loop_column_name_token(i)
        elif self._state == 'in loop data':
            self._finish_loop(i)


    def _quoted_data_value_token(self, i, t):
        """
        Any token starting with a single quote, double quote, or semicolon is a data value.

        :type i: int    # Token number
        :type t: str    # Token
        """
        quote_char = t[0]
        self._data_value_token(i, t[1:-1])


    def _data_value_token(self, i, t):
        """
        `foo` token, indicating a data value.

        Data values are always associated with a data name.  Outside a loop, they are pared with the
          previous data name, and inside a loop they are associated with a loop column.  The first
          data name encountered in a loop marks the end of the column declarations for that loop.

        :type i: int    # Token number
        :type t: str    # Token
        """
        if self._state == 'in loop columns specification':
            self._state = 'in loop data'
            self._loop_column_number = 0

        if self._state == 'in saveframe':
            self._add_to_saveframe(i, t)
        elif self._state == 'in loop data':
            if self._loop_column_number >= len(self._loop_columns):
                self._loop_column_number = 0
                self._loop_data.append(self._loop_row)
                self._loop_row = OrderedDict()
            self._loop_row[self._loop_columns[self._loop_column_number]] = t
            self._loop_column_number += 1

    def _add_to_saveframe(self, i, t):
        """
        Add a data name-value pair to a saveframe.

        Full data name tokens should have the format `saveframe_type.data_name`, and all the
          saveframe_type's should match.

        :type i: int    # Token number
        :type t: str    # Token
        """
        if 'sf_category' in self.target[self._saveframe_name]:
            self._check_saveframe_category(i)
        self.target[self._saveframe_name][self._data_name.split('.')[1]] = t

    def _check_saveframe_category(self, i):
        """
        Check that the first part of the data name token matches the saveframe type.  Raise an
          exception if they don't match and strict parsing is set.  If strict parsing is not set,
          it simply raises a warning

        :type i: int    # Token number
        :raise Exception:
        """
        if self._data_name.split('.')[0] != self.target[self._saveframe_name]['sf_category']:
            error_message = 'Token {}: Mismatch data name type {} in saveframe {}' \
                .format(i, self._data_name, self._saveframe_name)
            if self.strict:
                raise Exception(error_message)
            else:
                logger.warning(error_message)

    def _end_saveframe_token(self, i):
        """
        `save_` token, which closes a saveframe.

        :type i: int    # Token number
        """
        if self._state == 'in saveframe' or self._state.startswith('in loop'):
            self._finish_saveframe(i)
        else:
            self._unnamed_saveframe(i)

    def _start_saveframe_token(self, i, t):
        """
        `save_foo` token, which opens a saveframe called `foo`.

        :type i: int    # Token number
        :type t: str    # Token
        :raise Exception:
        """
        if self._saveframe_name is not None:
                raise Exception('Token {}: Nested saveframes are not allowed.'.format(i))
        self._state = 'in saveframe'
        self._saveframe_name = t[5:]
        self.target[self._saveframe_name] = OrderedDict()


    def _start_loop(self):
        """
        `loop_` token, marking the beginning of a loop

        :type i: int    # Token number
        """
        self._state = 'in loop columns specification'
        self._loop_name = None
        self._loop_columns = []
        self._loop_data = []
        self._loop_row = OrderedDict()


    def _finish_loop(self, i):
        """
        Finish processing a loop.

        Loops are a series of data names followed by data values and can be though of as a table of
          data.  The number of data values should be an exact multiple of the number of data names.

        :type i: int    # Token number
        :raise Exception:
        """

        if self._loop_column_number != len(self._loop_columns):
            error_message = 'Token {}: Number of data values is not a multiple of number of'
            error_message += ' column names in loop {}'
            error_message = error_message.format(i, self._loop_name)
            if self.strict:
                raise Exception(error_message)
            else:
                logger.warning(error_message)
        self._loop_data.append(self._loop_row)
        self.target[self._saveframe_name][self._loop_name] = self._loop_data

        if self._saveframe_name is None:
            self._state = 'start'
        else:
            self._state = 'in saveframe'

        self._loop_name = None
        self._loop_columns = []
        del self._loop_column_number


    def _loop_column_name_token(self, i):
        """
        data name token while specifying loop column names

        :type i: int    # Token number
        :raise Exception:
        """
        if self._loop_name is None:
            self._loop_name = self._data_name.split('.')[0]
        elif self._loop_name != self._data_name.split('.')[0]:
            error_message = 'Token {}: Mismatch column name {} in loop {}'.format(i,
                                                                                  self._data_name,
                                                                                  self._loop_name)
            if self.strict:
                raise Exception(error_message)
            else:
                logger.warning(error_message)
        self._loop_columns.append(self._data_name.split('.')[1])


    def _finish_saveframe(self, i):
        """
        save_ tag inside saveframe

        :type i: int    # Token number
        """
        if self._state.startswith('in loop'):
            self._finish_loop(i)
        self._saveframe_name = None
        self._state = 'start'

    def _unnamed_saveframe(i):
        """
        save_ tag outside saveframe

        :type i: int    # Token number
        :raise Exception:
        """
        error_message = 'Token {}: Trying to declare saveframe without a name or '
        error_message += 'close a saveframe without being in a saveframe.'

        raise Exception(error_message.format(i))


