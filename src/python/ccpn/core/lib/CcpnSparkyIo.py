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

import os
import time
import re
import collections
import pandas as pd

try:
  # Python 3
  from itertools import zip_longest
except:
  # python 2.7
  from itertools import izip_longest as zip_longest

# from datetime import datetime
from collections import OrderedDict
from ccpn.core.Project import Project
from ccpn.util.Logging import getLogger

sparkyReadingOrder = []
# possibly for later
sparkyWritingOrder = ([x for x in sparkyReadingOrder if x.startswith('sparky_')] +
                         [x for x in sparkyReadingOrder if not x.startswith('sparky_')])
_isALoop = ()

# not sure how to use this yet
sparky2CcpnMap = {}

# STAR parsing REGEX, following International Tables for Crystallography volume G section 2.1
_SPARKY_REGEX = r"""(?xmi) # $Revision$  # No 'u' flag for perl 5.8.8/RHEL5 compatibility
  ^;([\S\s]*?)(?:\r\n|\s)^;(?:(?=\s)|$)  # 1  Multi-line string
  |(?:^|(?<=\s))(\#.*?)\r?$              # 2  Comment
  |(?:^|(?<=\s))(?:(global_)             # 3  something?
  |<sparky\s(.*?)>                       # 4  Sparky project start
  |(\$\S+)                               # 5  STAR save frame reference
  |<end\s(.*?)>                          # 6  block terminator
  |<(version\s.*?)>                      # 7  block start
  |<(.*?)>                               # 8  block header   - shouldn't need the leading whitespace
  |type\s(.*?)                           # 9  type header
  |([\[]\S*)                             # 10  type subheader
  |([\]]\S*)                             # 11  type subblock terminator
  |((?:global_\S+)|(?:stop_\S+)|(?:data_)|(?:loop_\S+))  # 12 Invalid privileged construct
  |(_\S+)                                # 13 Data name
  |'(.*?)'                               # 14 Single-quoted string
  |"(.*?)"                               # 15 Double-quoted string
  |(\.)                                  # 16 CIF null
  |(\?)                                  # 17 CIF unknown/missing
  |((?:[^'";_$\s]|(?!^);).*)(?<![ ])     # 18 Non-quoted string - exclude pre/post whitespace
  |([\[\]]\S*)                           # 19 Square bracketed constructs (reserved)
  |(\S+)                                 # 20 Catch-all bad token
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
SP_TOKEN_TYPE_BLOCK       = 9
SP_TOKEN_TYPE_NESTED      = 10
SP_TOKEN_END_NESTED       = 11
SP_TOKEN_BAD_CONSTRUCT    = 12
SP_TOKEN_DATA_NAME        = 13
SP_TOKEN_SQUOTE_STRING    = 14
SP_TOKEN_DQUOTE_STRING    = 15
SP_TOKEN_NULL             = 16
SP_TOKEN_UNKNOWN          = 17
SP_TOKEN_STRING           = 18
SP_TOKEN_SQUARE_BRACKET   = 19
SP_TOKEN_BAD_TOKEN        = 20

SparkyToken = collections.namedtuple('SparkyToken', ('type', 'value'))

PEAK_TYPE = 'type'
PEAK_PEAK = 'peak'
PEAK_MAXSEARCH = 10
PEAK_POS = 'pos'
PEAK_RESONANCE = 'rs'
PEAK_POSNUM = 1
PEAK_RESONANCENUM = 2
PEAK_ALLFOUND = PEAK_POSNUM | PEAK_RESONANCENUM

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

SPARKY_ROOT = 'root'
SPARKY_DATA = 'data'
SPARKY_VERSION = 'version'
SPARKY_ENDBLOCK = '<end'
SPARKY_PATHNAME = 'pathname'
SPARKY_SPECTRUM = 'spectrum'
SPARKY_NAME = 'name'
SPARKY_ATTACHEDDATA = 'attached data'
SPARKY_ORNAMENT = 'ornament'
SPARKY_SPARKY = 'sparky'
SPARKY_SAVEFILES = 'savefiles'
SPARKY_PROJECT = 'project file'
SPARKY_SAVE = 'save file'
SPARKY_MOLECULE = 'molecule'
SPARKY_RESONANCES = 'resonances'
SPARKY_DEFAULTCHAIN = '@-'
SPARKY_SEQUENCE = 'sequence'
SPARKY_FIRSTRESIDUENUM = 'first_residue_number'
SPARKY_CONDITION = 'condition'
SPARKY_NESTED = 'local'
SPARKY_PEAK = 'peak'


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
  def __init__(self, name=SPARKY_ROOT):
    super(SparkyBlock, self).__init__(name=name)

  def getData(self, name=SPARKY_DATA, firstOnly=False):
    dataBlocks = [self[db] for db in self.keys() if name in db]
    dataBlocks = [ll for x in dataBlocks for ll in x]     # concaternate data lists
    if dataBlocks:
      if firstOnly:
        return dataBlocks[0]
      else:
        return dataBlocks
    else:
      return None

  def getDataValues(self, value, firstOnly=False):
    dataBlocks = [self[db] for db in self.keys() if SPARKY_DATA in db]
    spList = []
    for spType in dataBlocks:
      if spType:
        spType = [re.findall(r'%s\s?(.*)\s*' % value, sT) for sT in spType]
        spList.extend([ll for x in spType for ll in x])

    if spList:
      if firstOnly:
        return spList[0]
      else:
        return spList
    else:
      return None

  def _getBlocks(self, value, list=[]):
    if value in self.name:
      list.append(self)

    for ky in self.keys():
      if isinstance(self[ky], SparkyBlock):
        self[ky]._getBlocks(value, list)

    return list

  def getBlocks(self, value, firstOnly=False):
    list = self._getBlocks(value, list=[])
    if list:
      if firstOnly:
        return list[0]
      else:
        return list
    else:
      return None


class TypeBlock(SparkyBlock):
  # cheat and just copy the SparkyBlock under a new name
  def __init__(self, name=SPARKY_ROOT):
    super(SparkyBlock, self).__init__(name=name)


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
    self.columns = ['ResidueType', 'ResidueCode', 'FirstAtomName', 'SecondAtomName']

  def _processVersion(self, value):
    # next token must be version
    stack = self.stack
    last = stack[-1]

    if isinstance(last, SparkyBlock):
      try:
        func = last
      except AttributeError:
        raise SparkySyntaxError(self._errorMessage("Error inserting version num" % value,
                                                 value))
      func[SPARKY_VERSION] = value

    elif isinstance(last, list):
      try:
        func = last.append
      except AttributeError:
        raise SparkySyntaxError(self._errorMessage("Error inserting version num" % value,
                                                   value))
      func(value)

    return

  def _processComment(self, value):
    # Comments are ignored
    return

  def processValue(self, value):
    stack = self.stack
    last = stack[-1]

    # if isinstance(last, SparkyProjectBlock):
    #   # currently ignore until we have a SparkyBlock
    #   return

    if isinstance(last, TypeBlock):   # assume in a type block for now
      try:
        # parse the line again and add to the dictionary
        typeList = self._getTokens(value, str)
        last[typeList[0]] = typeList[1:]

      except AttributeError:
        raise SparkySyntaxError(self._errorMessage('Error processing typeList',
                                                 value))

    if isinstance(last, SparkyBlock):
      return

    if isinstance(last, str):
      # Value half of tag, value pair
      stack.pop()
      stack[-1].addItem(last, value)

    elif isinstance(last, OrderedDict):   # assume in a type block for now
      try:
        # parse the line again and add to the dictionary
        typeList = self._getTokens(value, str)
        last[typeList[0]] = typeList[1:]

      except AttributeError:
        raise SparkySyntaxError(self._errorMessage('Error processing typeList',
                                                 value))

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

    currentNames = [ky for ky in container.keys() if name in ky]
    if currentNames:
      name = name+str(len(currentNames))   # add an incremental number to the name

    # name is the new named block
    obj = SparkyBlock(name)
    container.addItem(name, obj)
    self.stack.append(obj)
    self.stack.append(list())     # put a list on as well

  def _addTypeBlock(self, name):
    container = self.stack[-1]

    # currentNames = [ky for ky in container.keys() if name in ky]
    # if currentNames:
    #   name = name+str(len(currentNames))   # add an incremental number to the name

    # name is the new named block
    obj = TypeBlock(name)

    if name not in container:
      container.addItem(name, list())     # add a list inside the parent block

    self.stack.append(obj)                  # and add a new block to the end
    # self.stack.append(OrderedDict())      # put a list on as well?

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
        self._closeList(value)

    if isinstance(stack[-1], TypeBlock):
      stack.pop()

    # terminate SparkyBlock
    if isinstance(stack[-1], SparkyBlock):
      if stack[-1].name.startswith(value):
        # Simple terminator. Close sparky block
        stack.pop()

      elif self.enforceSaveFrameStop:
        self._errorMessage("SaveFrame terminated by %s instead of save_" % value, value)

      else:
        # New saveframe start. We are missing the terminator, but close and continue anyway
        getLogger().warning('Closing sparkyBlock with missing terminator')
        stack.pop()

    stack.append(list())          # in case there are more data items to add

    if not isinstance((stack[-1]), SparkyBlock):
      if lowerValue.startswith(SPARKY_ENDBLOCK):
        raise SparkySyntaxError(self._errorMessage("'%s' found out of context" % value, value))

  def _openSparkyBlock(self, value):
    # start a new sparky block, which is everything
    stack = self.stack

    # Add new SparkyBlock
    if self.lowerCaseTags:
      value = value.lower()
    if isinstance(stack[-1], SparkyBlock):
      self._addSparkyBlock(value)

    elif isinstance(stack[-1], list):
      self._closeList(value)                                  # close the list and store
      self._addSparkyBlock(value)

    else:
      raise SparkySyntaxError(
        self._errorMessage("SparkyBlock start out of context: %s" % value, value)
      )

  def _openTypeBlock(self, value):
    # start a new sparky block, which is everything
    stack = self.stack

    # Add new SparkyBlock
    if self.lowerCaseTags:
      value = value.lower()

    if isinstance(stack[-1], TypeBlock):
      if value != SPARKY_NESTED:      # fix for the minute
        self._closeDict(value)                                  # close the list and store
      self._addTypeBlock(value)

    elif isinstance(stack[-1], SparkyBlock):
      self._addTypeBlock(value)

    elif isinstance(stack[-1], list):
      self._closeList(value)                                  # close the list and store
      self._addTypeBlock(value)

    # elif isinstance(stack[-1], OrderedDict):
    #   self._closeDict(value)                                  # close the list and store
    #   self._addTypeBlock(value)

    else:
      raise SparkySyntaxError(
        self._errorMessage("SparkyBlock start out of context: %s" % value, value)
      )

  def _closeDict(self, value):
    stack = self.stack
    data = stack.pop()        # remove the dict from the end
    block = stack[-1]         # point to the last block
    if not isinstance(block, SparkyBlock):
      if isinstance(data, SparkyBlock):
        raise TypeError("Implementation error, loop not correctly put on stack")
      else:
        raise SparkySyntaxError(self._errorMessage("Error: %s outside list" % value, value))

    if data:
      dataName = data.name
      block[dataName].append(data)    # SHOULD be in the block

  def _closeList(self, value):

    stack = self.stack
    data = stack.pop()        # remove the list from the end
    block = stack[-1]         # point to the last block
    if not isinstance(block, SparkyBlock):
      if isinstance(data, SparkyBlock):
        raise TypeError("Implementation error, loop not correctly put on stack")
      else:
        raise SparkySyntaxError(self._errorMessage("Error: %s outside list" % value, value))

    # columnCount = len(loop._columns)
    # if not columnCount:
    #   raise SparkySyntaxError(self._errorMessage(" loop lacks column names" , value))

    if data:

      dataName = SPARKY_DATA
      currentNames = [ky for ky in block.keys() if SPARKY_DATA in ky]
      if currentNames:
        dataName = SPARKY_DATA + str(len(currentNames))  # add an incremental number to the name

      block[dataName] = data

      # if len(data) % columnCount:
      #   if self.padIncompleteLoops:
      #     print("WARNING Token %s: %s in %s is missing %s values. Last row was: %s"
      #           % (self.counter, loop, self.stack[-2],
      #              columnCount - (len(data) % columnCount), data[-1]))
      #   else:
      #     raise SparkySyntaxError(
      #       self._errorMessage("loop %s is missing %s values"
      #                          % (loop, (columnCount - (len(data) % columnCount))), value)
      #     )
      #
      # # Make rows:
      # args = [iter(data)] * columnCount
      # for tt in zip_longest(*args, fillvalue=NULLSTRING):
      #   loop.newRow(values=tt)

    else:
      # empty loops appear here. We allow them, but that could change
      pass

  def _getToken(self, text, value):
    # return the value'th token from a string
    # just simple string NOT containing whitespace or '|' pipe character
    vals = re.findall(r"""(?:\|\s*|\s*)([a-zA-Z0-9,._^'";$!^/-]+)""", text)
    try:
      return vals[value]
    except:
      return None

  def _getTokens(self, text, funcType, start=0, end=0):
    # returns the list cast as funcType
    # just simple string NOT containing whitespace or '|' pipe character
    vals = re.findall(r"""(?:\|\s*|\s*)([a-zA-Z0-9,._^'";$!^/-]+)""", text)
    try:
      valEnd = len(vals)-1
      if start >= end:
        end = len(vals)-1
      else:
        end = min(end, valEnd)

      return [funcType(val) for val in vals[start:end+1]]
    except:
      return None

  def parseSparkyFile(self, path):

    with open(path, 'r') as fileName:
      self.text = fileName.read()

    self.tokeniser = getSparkyTokenIterator(self.text)

    processValue = self.processValue
    processFunctions = [None] * 21
    processFunctions[SP_TOKEN_SQUOTE_STRING] = self.processValue
    processFunctions[SP_TOKEN_DQUOTE_STRING] = self.processValue
    # processFunctions[SP_TOKEN_MULTILINE] = self.processValue
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
          processValue(value)

        else:
          func = processFunctions[typ]

          if func is None:

            if typ == SP_TOKEN_SPARKY_PROJECT:
              # put the first element on the stack
              result = SparkyBlock(name=name)           # result is the actually object, which SHOULD contain all
              stack.append(result)
              stack.append(list())  # put an empty list on the stack

              processValue("sparky %s" % value)     # put the type on the stack
              processValue("name %s" % name)
              processValue("pathname %s" % os.path.dirname(path))

            elif typ == SP_TOKEN_SPARKY_BLOCK:
              self._openSparkyBlock(value)

            elif typ == SP_TOKEN_TYPE_BLOCK:
              self._openTypeBlock(value)

            elif typ == SP_TOKEN_TYPE_NESTED:
              self._openTypeBlock(SPARKY_NESTED)

            elif typ == SP_TOKEN_END_NESTED:
              self._closeDict(SPARKY_NESTED)

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
        self._closeList('<End-of-File>')

      if isinstance(stack[-1], SparkyBlock):
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

  def _getSparkyDataList(self, sparkyBlock, value):
    if SPARKY_DATA in sparkyBlock and sparkyBlock[SPARKY_DATA]:
      spType = sparkyBlock[SPARKY_DATA]
      if spType:
        spType = [re.findall(r'%s\s?(.*)\s*' % value, sT) for sT in spType]
        spType = [ll for x in spType for ll in x]
        if spType:
          return spType

    return None

  def _getSparkyBlock(self, sparkyBlock, name, list=[]):
    if name in sparkyBlock.name:
      list.append(sparkyBlock)

    for ky in sparkyBlock.keys():
      if isinstance(sparkyBlock[ky], SparkyBlock):
        self._getSparkyBlock(sparkyBlock[ky], name, list)

    return list

  def importSpectra(self, project, saveBlock):
    getLogger().info('Importing Sparky spectra: %s' % saveBlock.name)
    # process the save files to get the spectra
    pathName = saveBlock.getDataValues(SPARKY_PATHNAME, firstOnly=True)

    spectra = saveBlock.getBlocks(SPARKY_SPECTRUM, firstOnly=True)
    fileName = spectra.getDataValues(SPARKY_NAME, firstOnly=True)
    filePath = spectra.getDataValues(SPARKY_PATHNAME, firstOnly=True)

    spectrumPath = os.path.abspath(os.path.join(pathName, filePath))
    workshopPath = os.path.abspath(
      os.path.join(pathName, '../lists/' + fileName + '.list.workshop'))

    self.project.loadData(spectrumPath)  # load the spectrum

    spectrumName = saveBlock.name
    spectrum = project.getObjectsByPartialId(className='Spectrum', idStartsWith=spectrumName)
    if spectrum:

      spectrumShift = spectra.getDataValues('shift', firstOnly=True)
      spectrumShiftVals = self._getTokens(spectrumShift, float)

      assignRelation = spectra.getDataValues('assignRelation', firstOnly=False)
      axes = [None] * len(assignRelation)

      for ax in assignRelation:
        axisNum = int(self._getToken(ax, 0))
        axisType = int(self._getToken(ax, 1))
        axisName = self._getToken(ax, 2)
        if axisNum:
          axes[axisNum-1] = (axisType, axisName)

      # generate the mapping of sparky axes to Ccpn axes
      specAxes = spectrum[0].axisCodes
      reorder = self._reorderAxes(axes, specAxes)

      if reorder:
        # apply the sparky spectrum shift to the Ccpn reference values
        # TODO:ED check which axis needs to be negative
        currentRefValues = list(spectrum[0].referenceValues)

        # assume that first is always negative
        currentRefValues[0] = currentRefValues[0] + spectrumShiftVals[reorder[0]]
        # and the rest are the other way
        for specInd in range(1, len(spectrumShiftVals)):
          currentRefValues[specInd] = currentRefValues[specInd] + spectrumShiftVals[reorder[specInd]]

        spectrum[0].referenceValues = currentRefValues

  def _reorderAxes(self, axes, newAxes):
    renameAxes = [None] * len(axes)
    for ai, axis in enumerate(axes):
      if axis[1]:
        ax2 = [aj for aj in axes[0:ai] if axis[1] in aj[1]]
        if ax2:
          renameAxes[ai] = (axis[0], axis[1] + str(len(ax2)))

    outAxes = [ai for aj, axisj in enumerate(newAxes) for ai, axis in enumerate(axes) if axisj == axis[1]]
    for ii in range(len(newAxes)):    # add any numbers that are missing from the list
      if ii not in outAxes:
        outAxes.insert(0, ii)
    return outAxes

  def importPeakLists(self, project, saveBlock, sparkyBlock):
    # process the save files to get the spectra
    pathName = saveBlock.getDataValues(SPARKY_PATHNAME, firstOnly=True)

    spectra = saveBlock.getBlocks(SPARKY_SPECTRUM, firstOnly=True)
    molName = spectra.getDataValues(SPARKY_MOLECULE, firstOnly=True)
    condName = spectra.getDataValues(SPARKY_CONDITION, firstOnly=True)

    nmrChainName = self._buildName([molName, condName])

    attachedPeak = spectra.getBlocks(SPARKY_ATTACHEDDATA, firstOnly=True)
    spectrumName = saveBlock.name

    # current test to decide whether to import a peak list
    peakAxes = attachedPeak.getDataValues('peak_pattern_axes', firstOnly=True)
    peakName = attachedPeak.getDataValues('peak_pattern_name', firstOnly=True)
    peakPatternAxes = None

    if peakAxes is not None and peakName is not None or True:
      # assume that we have to import a peaklist

      if peakAxes:
        peakPatternAxes = self._getTokens(peakAxes, int)

      assignRelation = spectra.getDataValues('assignRelation', firstOnly=False)
      axes = [None] * len(assignRelation)

      # not correct...
      for ax in assignRelation:
        axisNum = int(self._getToken(ax, 0))
        axisType = int(self._getToken(ax, 1))
        axisName = self._getToken(ax, 2)
        if axisNum:
          axes[axisNum-1] = (axisType, axisName)

      errorLine = 0
      # try:

      if len(assignRelation) != len([ax for ix, ax in enumerate(axes) if axes[ix]]):
        getLogger().info('assignRelation not found: %s' % saveBlock.name)

      else:

        # read in the peak list
        peakBlock = spectra.getBlocks(SPARKY_ORNAMENT, firstOnly=True)
        if peakBlock:
          peakData = peakBlock.getData(name=SPARKY_PEAK)

          if peakData:
            spectrum = project.getObjectsByPartialId(className='Spectrum', idStartsWith=spectrumName)
            if spectrum:
              newPeakList = spectrum[0].peakLists[0]         # get the first one .newPeakList()

              if not peakPatternAxes:
                spectrumAxes = spectrum[0].axisCodes
                peakPatternAxes = self._reorderAxes(axes, spectrumAxes)

              # TODO:ED need to remove hard coding for search of properties
              # ii=0
              # while ii<len(peakData)-PEAK_MAXSEARCH:

              for thisPeak in peakData:

                # if self._getToken(peakData[ii], 0) == PEAK_TYPE\
                #     and self._getToken(peakData[ii], 1) == PEAK_PEAK:

                  # TODO:ED put some more error checking in here - need to parse properly

                found = 0
                line = thisPeak.getData(PEAK_POS)
                if line:
                  found = found | PEAK_POSNUM
                  posList = [float(val) for val in line]

                line = thisPeak.getData(PEAK_RESONANCE)
                if line:
                  found = found | PEAK_RESONANCENUM
                  resList = line

                if found == PEAK_POSNUM:    # test without residue
                  peak = newPeakList.newPeak(position=[posList[i] for i in peakPatternAxes])

                elif found == PEAK_ALLFOUND:
                  # TODO:ED check with specta other than N-H, multidimensional etc.

                  peak = newPeakList.newPeak(position=[posList[i] for i in peakPatternAxes])

                  # TODO:ED check that the molName matches molecule/condition
                  nmrChain = project.fetchNmrChain(nmrChainName)

                  ri=0
                  while ri < len(resList):
                    resName = resList[ri][1:]     # clip the chain type from the head
                    axisCode = resList[ri+1]
                    nmrResidue = nmrChain.fetchNmrResidue(sequenceCode=resName)
                    self._fetchAndAssignNmrAtom(peak, nmrResidue, axisCode)
                    ri += 2

              #     else:
              #       getLogger().warning('Missing peakList information: %s %i' % (saveBlock.name, ii+jj))
              #     ii += jj
              #   else:
              #     ii += 1
              #
              # errorLine = ii

      # except Exception as es:
      #   getLogger().warning('Error importing peakList: %s %i' % (saveBlock.name, errorLine))

  def importSparkyProject(self, project, sparkyBlock):
    """Import entire project from dataBlock into empty Project"""
    t0 = time.time()

    self.warnings = []
    self.project = project

    # traverse the sparkyBlock and insert into project
    sparkyType = sparkyBlock.getDataValues(SPARKY_SPARKY, firstOnly=True)

    if sparkyType == SPARKY_PROJECT:
      # load project file
      fileName = sparkyBlock.getDataValues(SPARKY_NAME, firstOnly=True)
      filePath = sparkyBlock.getDataValues(SPARKY_PATHNAME, firstOnly=True)

      saveFiles = sparkyBlock.getBlocks(SPARKY_SAVEFILES, firstOnly=True)
      loadedBlocks = []
      for sp in saveFiles.getData():
        savefilePath = os.path.abspath(os.path.join(filePath, sp))
        loadedBlocks.append(self.parseSparkyFile(savefilePath))

      # now import the molecule from the main project file
      self.importSparkyMolecule(project, sparkyBlock)

      # load spectrum data
      for isf in loadedBlocks:
        self.importSpectra(project, isf)   # modify to load from the project

      # load spectrum data
      for isf in loadedBlocks:
        self.importPeakLists(project, isf, sparkyBlock)   # modify to load from the project

    elif sparkyType == SPARKY_SAVE:
      self.importSpectra(project, sparkyBlock)
      self.importPeakLists(project, sparkyBlock, sparkyBlock)  # modify to load from the project

    else:
        getLogger().warning('Unknown Sparky File Type')

    t2 = time.time()
    getLogger().debug('Imported Sparky file into project, time = %.2fs' %(t2-t0))

    for msg in self.warnings:
      print ('====> ', msg)
    self.project = None

  def _createDataFrame(self, input_path):
    return pd.read_table(input_path, delim_whitespace=True, )

  def _splitAssignmentColumn(self, dataFrame):
    ''' parses the assignment column.
    Splits the column assignment in  four columns: ResidueName ResidueCode AtomName1 AtomName2.
    '''
    assignments = [re.findall('\d+|\D+', s) for s in dataFrame.iloc[:, 0]]
    assignmentsColumns = []
    for a in assignments:
      try:
        i,j,*args = a
        atoms = (''.join(args)).split('-')
        if len(atoms) == 2:
            firstAtom, secondAtom = atoms
            assignmentsColumns += ((i,j,firstAtom, secondAtom),)
      except:
        getLogger().warning('Undefined atom assignment %s' % str(a))

    return pd.DataFrame(assignmentsColumns,columns=self.columns)

  def _mergeDataFrames(self, generalDF, assignmentDF):
    '''
    :param generalDF: first dataframe with assignments all in on column
    :param assignmentDF: assignments dataframe  in  4 columns
    :return: new dataframe with four assignment columns + the original without the first column
    '''
    partialDf = generalDF.drop(generalDF.columns[0], axis=1)
    return pd.concat([assignmentDF, partialDf], axis=1, join_axes=[partialDf.index])

  def _correctChainResidueCodes(self, chain, ccpnDataFrame):
    ''' renames Chain residueCodes correctly according with the dataFrame, if duplicates, deletes them.
    '''
    for residue,resNumber, in zip(chain.residues, ccpnDataFrame.ResidueCode):
      try:
        residue.rename(str(resNumber))
      except:
        residue.delete()
    return chain

  def _createCcpnChain(self, project, ccpnDataFrame):
    '''makes a chain from the ResidueTypes.
    CCPN wants a long list of  one Letter Codes without spaces'''
    residueTypes = ''.join([i for i in ccpnDataFrame.ResidueType])
    newChain = project.createChain(residueTypes,molType='protein')
    self._correctChainResidueCodes(newChain, ccpnDataFrame)
    return newChain

  def _createNewCcpnChain(self, project, chainList, resList):
    newChain = project.createChain(chainList, molType='protein')
    for residue,resNumber, in zip(newChain.residues, resList):
      try:
        residue.rename(str(resNumber))
      except:
        residue.delete()
    return newChain

  def _fetchAndAssignNmrAtom(self, peak, nmrResidue, atomName):
    atom = nmrResidue.fetchNmrAtom(name=str(atomName))
    peak.assignDimension(axisCode=atomName[0], value=[atom])

  def _connectNmrResidues(self, nmrChain):
    updatingNmrChain = None
    nrs = nmrChain.nmrResidues
    for i in range(len(nrs) - 1):
      currentItem, nextItem = nrs[i], nrs[i + 1]
      if currentItem or nextItem is not None:
        updatingNmrChain = currentItem.connectNext(nextItem, )
    return updatingNmrChain

  def _assignNmrResiduesToResidues(self, connectedNmrChain, ccpnChain):
    for nmrResidue, residue in zip(connectedNmrChain.nmrResidues, ccpnChain.residues):
      nmrResidue.residue = residue

  def _parseDataFrame(self, ccpnDataFrame, spectrum, nmrChain):

    lastNmrResidue = None
    newPeakList = spectrum.newPeakList()
    foundResNumber = list(ccpnDataFrame.iloc[:,1])
    for i, resType, resNumber, atom1, atom2, pos1, pos2, in zip(range(len(ccpnDataFrame.iloc[:,0]) -1), ccpnDataFrame.iloc[:,0],
                                                              ccpnDataFrame.iloc[:,1], ccpnDataFrame.iloc[:,2],
                                                              ccpnDataFrame.iloc[:,3], ccpnDataFrame.iloc[:,4],
                                                              ccpnDataFrame.iloc[:,5]):

      peak = newPeakList.newPeak(position=(float(pos2), float(pos1)))

      if resNumber in foundResNumber[:i]:  # in case of duplicated Residues Eg sideChain W2023N-H H and W2023NE1-HE1, don't need to create a new nmrResidue, just add the atoms to the previous one.
        nmrResidue = lastNmrResidue
        if nmrResidue:
          self._fetchAndAssignNmrAtom(peak, nmrResidue, atom2)
          self._fetchAndAssignNmrAtom(peak, nmrResidue, atom1)

      else:
        nmrResidue = nmrChain.fetchNmrResidue(sequenceCode=str(resNumber))
        lastNmrResidue = nmrResidue
        if nmrResidue:
          self._fetchAndAssignNmrAtom(peak, nmrResidue, atom2)
          self._fetchAndAssignNmrAtom(peak, nmrResidue, atom1)

    return nmrChain

  def _buildName(self, names, default=SPARKY_DEFAULTCHAIN):
    import string

    name = ''
    for nm in names:
      if nm:
        exclude = ' ,.'
        regex = re.compile('[%s]' % re.escape(exclude))
        name = name + regex.sub('', nm)

    return name if name else default

  def initParser(self, project, input_path, spectrum):
    generalDF = self._createDataFrame(input_path)
    assignmentDF = self._splitAssignmentColumn(generalDF)
    ccpnDataFrame = self._mergeDataFrames(generalDF, assignmentDF)
    ccpnChain = self._createCcpnChain(project, ccpnDataFrame)
    nmrChain = project.fetchNmrChain('A')
    newNmrChain = self._parseDataFrame(ccpnDataFrame, spectrum, nmrChain)
    connectedNmrChain = self._connectNmrResidues(newNmrChain)
    self._assignNmrResiduesToResidues(connectedNmrChain, ccpnChain)

  def importSparkyMolecule(self, project, sparkyBlock):
    # read the molecules from the sparky project and load the resonances
    getLogger().info('Importing Sparky molecular chains: %s' % sparkyBlock.name)

    molecules = sparkyBlock.getBlocks(SPARKY_MOLECULE)

    for mol in molecules:
      molName = self._buildName([mol.getDataValues(SPARKY_NAME, firstOnly=True)])

      attData = mol.getBlocks(SPARKY_ATTACHEDDATA, firstOnly=True)    # should be only one

      seq = attData.getDataValues(SPARKY_SEQUENCE, firstOnly=True)
      firstRes = attData.getDataValues(SPARKY_FIRSTRESIDUENUM, firstOnly=True)
      if seq and firstRes:
        newChain = project.createChain(sequence=seq
                                       , molType='protein'
                                       , startNumber=int(firstRes)
                                       , compoundName=molName)

      conditions = mol.getBlocks(SPARKY_CONDITION)

      for condition in conditions:
        conditionName = condition.getDataValues(SPARKY_NAME, firstOnly=True)

        nmrChainName = self._buildName([molName, conditionName], molName)

        # assume only one block in each condition
        resBlock = condition.getBlocks(SPARKY_RESONANCES, firstOnly=True)

        if resBlock:
          getLogger().info('  Importing Sparky molecular chain: %s' % resBlock.name)
          resList = resBlock.getData()
          chain = ''
          nmrResList = []
          nmrAtomList = []
          for res in resList:

            try:
              # vals = re.findall(r"""(?:\|\s*|\s*)([a-zA-Z0-9,._^'";$!^]+)""", res)
              chainCode = self._getToken(res, 0)[0]       # str(vals[0][0])
              resName = self._getToken(res, 0)[1:]        # str(vals[0][1:])
              atomType = self._getToken(res, 1)           # str(vals[1])
              chemShift = float(self._getToken(res, 2))           # float(vals[2])
              atomIsotopeCode = self._getToken(res, 3)           # str(vals[3])

              if resName not in nmrResList:
                nmrResList.append(resName)
                chain = chain+chainCode

              nmrAtomList.append((chainCode, resName, atomType, chemShift, atomIsotopeCode))

            except Exception as es:
              getLogger().warning('Incorrect resonance.')

          # rename to the nmrResidue names in the project
          nmrChain = project.fetchNmrChain(nmrChainName)
          for chainCode, resName, atomType, chemShift, atomIsotopeCode in nmrAtomList:
            nmrResidue = nmrChain.fetchNmrResidue(sequenceCode=resName)
            if nmrResidue:
              newAtom = nmrResidue.newNmrAtom(name=atomType, isotopeCode=atomIsotopeCode)

          # connect the nmrResidues and assignTo
          # connectedNmrChain = self._connectNmrResidues(nmrChain)
          # self._assignNmrResiduesToResidues(connectedNmrChain, ccpnChain)

      # now need to check the save files and find any peak lists that need to be created

class CcpnSparkyWriter:
  # ejb - won't be implemented yet
  def __init__(self, project:Project, specificationFile:str=None, mode:str='strict',
               programName:str=None, programVersion:str=None):
    self.project = project
    self.mode=mode

if __name__ == '__main__':
    axes = [(1, 'n')
            , (2, 'h')
            , (3, 'n')
            , (4, 'h')
            , (5, 'h')
            , (6, 'ca')
            , (7, 'ca')
            , (8, 'cb')
            , (9, 'h')
            , (10, 'cb')]

    newAxes = ['h1', 'h3', 'n', 'cb1', 'ca', 'cb', 'n1', 'h', 'ca1', 'h2']

    axes = [(1, 'n')
            , (2, 'n')
            , (3, 'h')]
    newAxes = ['h', 'n', 'n1']

    for ai, axis in enumerate(axes):
      ax2 = [aj for aj in axes[0:ai] if axis[1] in aj[1]]
      if ax2:
        axes[ai] = (axis[0], axis[1] + str(len(ax2)))

    out2 = [ai for aj, axisj in enumerate(newAxes) for ai, axis in enumerate(axes) if axisj == axis[1]]

    print (axes)
    print (out2)