"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import random
import os
import sys
import time
import typing
import itertools
import errno
import re
import collections
try:
  # Python 3
  from itertools import zip_longest
except:
  # python 2.7
  from itertools import izip_longest as zip_longest

from datetime import datetime
from collections import OrderedDict
from ccpn.core.Project import Project

from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Complex import Complex
from ccpn.core.PeakList import PeakList
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Integral import Integral
from ccpn.core.Peak import Peak
from ccpn.core.Sample import Sample
# from ccpn.core.SampleComponent import SampleComponent
from ccpn.core.Substance import Substance
from ccpn.core.Chain import Chain
# from ccpn.core.Residue import Residue
# from ccpn.core.Atom import Atom
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpn.util.Logging import getLogger

sparkyReadingOrder = [
  'sparky_nmr_meta_data',
  'sparky_molecular_system',
  'ccpn_sample',
  'ccpn_substance',
  'ccpn_assignment',
  'sparky_chemical_shift_list',
  'ccpn_dataset',
  'sparky_distance_restraint_list',
  'sparky_dihedral_restraint_list',
  'sparky_rdc_restraint_list',
  'sparky_nmr_spectrum',
  'sparky_peak_restraint_links',
  'ccpn_complex',
  'ccpn_spectrum_group',
  'ccpn_restraint_list',
  'ccpn_notes',
  'ccpn_additional_data'
]

# possibly for later
sparkyWritingOrder = ([x for x in sparkyReadingOrder if x.startswith('sparky_')] +
                         [x for x in sparkyReadingOrder if not x.startswith('sparky_')])

_isALoop = ()

# not sure how to use this yet
sparky2CcpnMap = {
  'sparky_nmr_meta_data':OrderedDict((
    ('format_name',None),
    ('format_version',None),
    ('program_name',None),
    ('program_version',None),
    ('creation_date',None),
    ('uuid',None),
    ('coordinate_file_name',None),
    ('ccpn_dataset_serial', None),
    ('ccpn_dataset_comment',None),
    ('sparky_related_entries',_isALoop),
    ('sparky_program_script',_isALoop),
    ('sparky_run_history',_isALoop),
  )),
  'sparky_related_entries':OrderedDict((
    ('database_name',None),
    ('database_accession_code',None),
  )),
  'sparky_program_script':OrderedDict((
    ('program_name',None),
    ('script_name',None),
    ('script',None),
  ))
}

# STAR parsing REGEX, following International Tables for Crystallography volume G section 2.1
_SPARKY_REGEX = r"""(?xmi) # $Revision$  # No 'u' flag for perl 5.8.8/RHEL5 compatibility
^;([\S\s]*?)(?:\r\n|\s)^;(?:(?=\s)|$)  # Multi-line string
|(?:^|(?<=\s))(\#.*?)\r?$              # Comment
|(?:^|(?<=\s))(?:
  (global_)                            # 
  |(<sparky\S*)                          # Sparky project start
  |(\$\S+)                             # STAR save frame reference
  |(<end\S*)                             # block terminator
  |(<version\S*)                          # block start
  |(<\S*)                             # block header
  |((?:global_\S+)|(?:stop_\S+)|(?:data_)|(?:loop_\S+))  # Invalid privileged construct
  |(_\S+)                              # Data name
  |'(.*?)'                             # Single-quoted string
  |"(.*?)"                             # Double-quoted string
  |(\.)                                # CIF null
  |(\?)                                # CIF unknown/missing
  |([\[\]]\S*)                         # Square bracketed constructs (reserved)
  |((?:[^'";_$\s]|(?<!^);)\S*)         # Non-quoted string
  |(\S+)                               # Catch-all bad token
)
(?:(?=\s)|$)"""

# Compiled form of _REGEX
_sparky_pattern = re.compile(_SPARKY_REGEX, re.UNICODE)

# Token types. NB numbers must be synced to regex - these are used directly!!!
SP_TOKEN_MULTILINE        = 1
SP_TOKEN_COMMENT          = 2
SP_TOKEN_GLOBAL           = 3
SP_TOKEN_SPARKY_PROJECT   = 4
SP_TOKEN_SAVE_FRAME_REF   = 5
SP_TOKEN_END_SPARKY_BLOCK = 6
SP_TOKEN_VERSION          = 7
SP_TOKEN_SPARKY_BLOCK     = 8
SP_TOKEN_BAD_CONSTRUCT    = 9
SP_TOKEN_DATA_NAME        = 10
SP_TOKEN_SQUOTE_STRING    = 11
SP_TOKEN_DQUOTE_STRING    = 12
SP_TOKEN_NULL             = 13
SP_TOKEN_UNKNOWN          = 14
SP_TOKEN_SQUARE_BRACKET   = 15
SP_TOKEN_STRING           = 16
SP_TOKEN_BAD_TOKEN        = 17

SparkyToken = collections.namedtuple('SparkyToken', ('type', 'value'))

class UnquotedValue(str):
  """A plain string - the only difference is the type: 'UnquotedValue'.
  Used to distinguish values from STAR files that were not quoted.
  STAR special values (like null,  unknown, ...) are only recognised if unquoted strings"""
  pass

# Constants for I/O of standard values
NULLSTRING = UnquotedValue('.')
UNKNOWNSTRING = UnquotedValue('?')
TRUESTRING = UnquotedValue('true')
FALSESTRING = UnquotedValue('false')
NANSTRING = UnquotedValue('NaN')
PLUSINFINITYSTRING = UnquotedValue('Infinity')
MINUSINFINITYSTRING = UnquotedValue('-Infinity')


def getSparkyTokenIterator(text):
  """Iterator that returns an iterator over all STAR tokens in a generic STAR file"""
  return (SparkyToken(x.lastindex, x.group(x.lastindex))
          for x in _sparky_pattern.finditer(text))

class SparkySyntaxError(ValueError):
  pass

class NamedOrderedDict(OrderedDict):
  def __init__(self, name=None):
    super(NamedOrderedDict, self).__init__()
    self.name = name

  def __str__(self):
    return '%s(name=%s)' % (self.__class__.__name__, self.name)

  def __repr__(self):
    return '%s(%s, name=%s)' % (self.__class__.__name__, list(tt for tt in self.items()), self.name)

  def addItem(self, tag, value):
    if tag in self:
      raise ValueError("%s: duplicate key name %s" % (self, tag))
    else:
      self[tag] = value


class SparkyBlock(NamedOrderedDict):
  """Top level container for general STAR object tree"""
  def __init__(self, name='Root'):
    super(SparkyBlock, self).__init__(name=name)


class SparkyProjectBlock(NamedOrderedDict):
  """Top level container for general STAR object tree"""
  def __init__(self, name='Root'):
    super(SparkyProjectBlock, self).__init__(name=name)


class CcpnSparkyReader:
  def __init__(self, application:str, specificationFile:str=None, mode:str='standard',
               testing:bool=False):

    # just copied from Rasmus for the minute
    self.application = application
    self.mode=mode
    self.saveFrameName = None
    self.warnings = []
    self.errors = []
    self.testing = testing
    self.text = None
    self.tokeniser = None
    self.allowSquareBracketStrings = False
    self.lowerCaseTags = True
    self.enforceSaveFrameStop = False
    self.enforceLoopStop = False

    self.stack = []
    self.globalsCounter = 0

  def _processVersion(self, value):
    # next token must be version
    return

  def _processComment(self, value):
    # Comments are ignored
    return

  def processValue(self, value):
    stack = self.stack
    last = stack[-1]
    if isinstance(last, str):
      # Value half of tag, value pair
      stack.pop()
      stack[-1].addItem(last, value)
    else:
      try:
        func = last.append
      except AttributeError:
        raise SparkySyntaxError(self._errorMessage("Data value %s must be in item or loop_" % value,
                                                 value))
      func(value)

  def _processBadToken(self, value, typ):
    raise SparkySyntaxError(self._errorMessage("Illegal token of type% s:  %s" % (typ, value), value))

  def _addSparkyBlock(self, name):
    container = self.stack[-1]
    obj = SparkyBlock(name)
    container.addItem(name, obj)
    self.stack.append(obj)

  def _closeSparkyBlock(self, value):

    stack =  self.stack

    lowerValue = value.lower()

    # Terminate loop
    if isinstance(stack[-1], list):
      if self.enforceLoopStop:
        raise SparkySyntaxError(
          self._errorMessage("Loop terminated by %s instead of stop_" % value, value)
        )
      else:
        # Close loop and pop it off the stack
        self._closeLoop(value)

    # terminate SparkyBlock
    if isinstance(stack[-1], SparkyBlock):
      if lowerValue.startswith('<end '):
        # Simple terminator. Close save frame
          stack.pop()#

      elif self.enforceSaveFrameStop:
        self._errorMessage("SaveFrame terminated by %s instead of save_" % value, value)

      else:
        # New saveframe start. We are missing the terminator, but close and continue anyway
        stack.pop()

    if not isinstance((stack[-1]), SparkyBlock):
      if lowerValue.startswith('<end '):
        raise SparkySyntaxError(self._errorMessage("'%s' found out of context" % value, value))

  def _openSparkyBlock(self, value):
    # start a new sparky block, which is everything
    stack = self.stack

    # Add new SparkyBlock
    if self.lowerCaseTags:
      value = value.lower()
    if isinstance(stack[-1], SparkyBlock):
      self._addSparkyBlock(value)
    else:
      raise SparkySyntaxError(
        self._errorMessage("SparkyBlock start out of context: %s" % value, value)
      )

  def _closeLoop(self, value):

    stack = self.stack
    data = stack.pop()
    loop = stack.pop()
    if not isinstance(loop, SparkyBlock):
      if isinstance(data, SparkyBlock):
        raise TypeError("Implementation error, loop not correctly put on stack")
      else:
        raise SparkySyntaxError(self._errorMessage("Loop stop_ %s outside loop" % value, value))

    columnCount = len(loop._columns)
    if not columnCount:
      raise SparkySyntaxError(self._errorMessage(" loop lacks column names" , value))

    if data:

      if len(data) % columnCount:
        if self.padIncompleteLoops:
          print("WARNING Token %s: %s in %s is missing %s values. Last row was: %s"
                % (self.counter, loop, self.stack[-2],
                   columnCount - (len(data) % columnCount), data[-1]))
        else:
          raise SparkySyntaxError(
            self._errorMessage("loop %s is missing %s values"
                               % (loop, (columnCount - (len(data) % columnCount))), value)
          )

      # Make rows:
      args = [iter(data)] * columnCount
      for tt in zip_longest(*args, fillvalue=NULLSTRING):
        loop.newRow(values=tt)

    else:
      # empty loops appear here. We allow them, but that could change
      pass

  def parseSparkyFile(self, path):

    with open(path, 'r') as fileName:
      self.text = fileName.read()

    self.tokeniser = getSparkyTokenIterator(self.text)

    processValue = self.processValue
    processFunctions = [None] * 20
    processFunctions[SP_TOKEN_SQUOTE_STRING] = self.processValue
    processFunctions[SP_TOKEN_DQUOTE_STRING] = self.processValue
    processFunctions[SP_TOKEN_MULTILINE] = self.processValue
    processFunctions[SP_TOKEN_VERSION] = self._processVersion
    processFunctions[SP_TOKEN_COMMENT] = self._processComment


    # processFunctions[SP_TOKEN_LOOP] = self._openLoop
    # processFunctions[SP_TOKEN_LOOP_STOP] = self._closeLoop
    # processFunctions[SP_TOKEN_GLOBAL] = self._processGlobal
    # processFunctions[SP_TOKEN_DATA_BLOCK] = self._processDataBlock

    unquotedValueTags = (SP_TOKEN_STRING, SP_TOKEN_NULL, SP_TOKEN_UNKNOWN, SP_TOKEN_SAVE_FRAME_REF)
    # quotedValueTags = (TOKEN_SQUOTE_STRING, TOKEN_DQUOTE_STRING, TOKEN_MULTILINE)

    stack = self.stack

    name = os.path.splitext(os.path.basename(path))[0]
    # result = SparkyProjectBlock(name=name)
    # stack.append(result)

    # now process the file

    value = None
    self.counter = 0   # Token counter
    try:
      for tk in self.tokeniser:
        self.counter += 1
        typ, value = tk

        if typ in unquotedValueTags:
          value = UnquotedValue(value)
          # processValue(value)

        else:
          func = processFunctions[typ]

          if func is None:

            if typ == SP_TOKEN_SPARKY_PROJECT:
              # put the first element on the stack
              result = SparkyProjectBlock(name=name)
              stack.append(result)

            elif typ == SP_TOKEN_SPARKY_BLOCK:
              # save_ string
              self._openSparkyBlock(value)

            elif typ == SP_TOKEN_END_SPARKY_BLOCK:
                self._closeSparkyBlock(value)

            elif typ in (SP_TOKEN_BAD_CONSTRUCT, SP_TOKEN_BAD_TOKEN):
              self._processBadToken(value, typ)

            elif typ == SP_TOKEN_SQUARE_BRACKET:
              if self.allowSquareBracketStrings:
                processValue(UnquotedValue(value))
              else:
                self._processBadToken(value, typ)

            else:
              raise SparkySyntaxError("Unknown token type: %s" % typ)
          else:
            func(value)


      # End of data - clean up stack
      if isinstance(stack[-1], str):
        raise SparkySyntaxError(self._errorMessage("File ends with item name", value))

      if isinstance(stack[-1], list):
        self._closeLoop('<End-of-File>')

      if isinstance(stack[-1], SparkyBlock):
        stack.pop()

      if isinstance(stack[-1], SparkyProjectBlock):
        stack.pop()

      if stack:
        raise RuntimeError(self._errorMessage("stack not empty at end of file", value))
    except Exception as es:
      print("ERROR at token %s" % self.counter)
      raise
    #
    return result

  def _errorMessage(self, msg, value):
    """Make standard error message"""
    template = "Error in context: %s, at token %s, line: %s\n%s"
    tags = [(x if isinstance(x, str) else x.name) for x in self.stack[1:]] + [value]

    lines = self.text.splitlines()
    lineCount = len(lines)
    ii = 0
    if tags:
      jj = 0
      tag = tags[jj]
      while ii < lineCount:
        if tag in lines[ii].lower().split():
          # This line contains the current tag - go to the next tag
          jj += 1
          if jj < len(tags):
            tag = tags[jj]
          else:
            # This line contains the last of the tags - it is the line we want
            break
        else:
          # nothing found here - try next line
          ii += 1
    #
    return template % (tags[:-1], tags[-1], ii+1, msg)#

class CcpnSparkyWriter:
  # ejb - won't be implemented yet
  def __init__(self, project:Project, specificationFile:str=None, mode:str='strict',
               programName:str=None, programVersion:str=None):
    self.project = project
    self.mode=mode