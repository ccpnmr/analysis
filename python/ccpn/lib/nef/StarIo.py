"""I/O for NEF and NmrStar formats

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

# NB Assumes that file was parsed with lowercaseTags = True

# Constraints on class hierarchy:
# - all plain tags in a saveframe start with the '<sf_category>.'
# - ALl loop column names start with '<loopcategory>.'
# - loopcategories share a namespace with tags within a saveframe
# - DataBlocks can contain only saveframes.
# - tag prefixes ('_', 'save_', 'data_' are stripped
# - to


# NBNB some longer variable names;

import os
import keyword
from . import GenericStarParser
from ccpncore.util.Types import Union, Sequence, Optional
from ccpncore.util import Common as commonUtil


def parseNmrStar(text:str, mode='standard'):
  """load NMRSTAR file"""
  dataExtent = GenericStarParser.parse(text, mode)
  converter = _StarDataConverter(dataExtent)
  converter.preValidate()
  result = converter.convert()
  #
  return result

def parseNef(text:str, mode='standard'):
  """load NEF from string"""
  dataExtent = GenericStarParser.parse(text, mode)
  converter = _StarDataConverter(dataExtent, fileType='nef')
  converter.preValidate()
  result = converter.convert()
  #
  return result

def parseNmrStarFile(fileName:str, mode:str='standard'):
  """parse NMRSTAR from file"""
  dataExtent = GenericStarParser.parseFile(fileName, mode)
  converter = _StarDataConverter(dataExtent)
  converter.preValidate()
  result = converter.convert()
  #
  return result

def parseNefFile(fileName:str, mode:str='standard'):
  """parse NEF from file"""
  dataExtent = GenericStarParser.parseFile(fileName, mode)
  converter = _StarDataConverter(dataExtent, fileType='nef')
  converter.preValidate()
  result = converter.convert()
  #
  return result

class StarValidationError(ValueError):
  pass

class NmrDataExtent(GenericStarParser.DataExtent):
  """Top level container (OrderedDict) for NMRSTAR/NEF object tree"""
  pass

# We insert these afterwards as we want the functions at the top of the file
# but can only annotate after DataExtent is created
parseNef.__annotations__['return'] = NmrDataExtent
parseNefFile.__annotations__['return'] = NmrDataExtent
parseNmrStar.__annotations__['return'] = NmrDataExtent
parseNmrStarFile.__annotations__['return'] = NmrDataExtent

class NmrLoop(GenericStarParser.Loop):
  """Loop for NMRSTAR/NEF object tree

  The contents, self.data is a list of namedlist objects matching the column names.
  rows can be modified or deleted from data, but adding new rows directly is likely to
  break - use the newRow function."""

  @property
  def category(self) -> str:
    """Loop category tag - synonym for name (unlike the case of SaveFrame)"""
    return self.name

  @property
  def tagPrefix(self) -> str:
    """Prefix to use before item tags on output"""
    return '_%s.' % self.name

class NmrSaveFrame(GenericStarParser.SaveFrame):
  """SaveFrame (OrderedDict)for NMRSTAR/NEF object tree"""

  def __init__(self, name=None, category=None):
    super(NmrSaveFrame, self).__init__(name=name)
    self.category = category

  @property
  def tagPrefix(self) -> str:
    """Prefix to use before item tags on output"""
    return '_%s.' % self.category

  def newLoop(self, name, columns) -> NmrLoop:
    """Make new NmrLoop and add it to the NmrSaveFrame"""
    loop = NmrLoop(name, columns)
    self.addItem(name, loop)
    return loop

class NmrDataBlock(GenericStarParser.DataBlock):
  """DataBlock (OrderedDict)for NMRSTAR/NEF object tree"""

  def newSaveFrame(self, name:str, category:str) -> NmrSaveFrame:
    """Make new NmrSaveFrame and add it to the DataBlock"""
    saveFrame = NmrSaveFrame(name, category=category)
    self.addItem(name, saveFrame)
    saveFrame.addItem('sf_framecode', name)
    saveFrame.addItem('sf_category', category)
    return saveFrame

class NmrLoopRow(GenericStarParser.LoopRow):
  pass


class _StarDataConverter:
  """Converter from output of a GeneralStarParser to a NEF or NMRSTAR nested data structure

  NB Function assumes valid data as output from GeneralStarParser with lowerCaseTags settings
  and does not double check validity."""


  validFileTypes = ('nef', 'star')

  def __init__(self, dataExtent:GenericStarParser.DataExtent, fileType='star',
               specification=None, convertColumnNames=True):

    # Set option settings
    if specification is None:
      self.specification = None
    else:
      raise NotImplementedError("_StarDataConverter specification input not yet implemented")
    fileType = fileType and fileType.lower()
    if fileType not in self.validFileTypes:
      raise StarValidationError("fileType %s must be one of %s" % (fileType, self.validFileTypes))
    self.fileType = fileType

    self.convertColumnNames = convertColumnNames

    self.dataExtent = dataExtent

    # Stack of objects parsed, to give context for error messages
    self.stack = []

  def preValidate(self):
    self.stack = []

    try:
      for dataBlock in self.dataExtent.values():
        self.preValidateDataBlock(dataBlock)
    except StarValidationError:
      raise
    except:
      print(self._errorMessage('System error:'))
      raise

  def convert(self):

    nmrDataExtent = NmrDataExtent(name=self.dataExtent.name)

    self.stack = []

    try:
      for dataBlock in self.dataExtent.values():
        newDataBlock =  self.convertDataBlock(dataBlock)
        nmrDataExtent.addItem(newDataBlock.name, newDataBlock)
    except StarValidationError:
      raise
    except:
      print(self._errorMessage('System error:'))
      raise
    #
    return nmrDataExtent

  def preValidateDataBlock(self, dataBlock):

    self.stack.append(dataBlock)

    name = dataBlock.name
    if name != 'global_' and not name.startswith('data_'):
      self.raiseValidationError("DataBlock name  must be 'global_' or start with 'data_'")

    for tag, saveFrame in dataBlock.items():

      if isinstance(saveFrame, GenericStarParser.SaveFrame):
        self.preValidateSaveFrame(saveFrame)
      else:
        self.raiseValidationError("%s file DataBlock contains non-saveframe element %s:%s"
                         % (self.fileType, tag, saveFrame))

    self.stack.pop()

  def convertDataBlock(self, dataBlock):

    self.stack.append(dataBlock)

    # get NmrDataBlock name
    name = dataBlock.name
    if name.startswith('data_'):
      name = name[5:]
    elif name == 'global_':
      name = 'global'

    # Make NmrDataBlock and connect it
    nmrDataBlock = NmrDataBlock(name=name)

    for saveFrame in dataBlock.values():
      nmrSaveFrame = self.convertSaveFrame(saveFrame)
      nmrDataBlock.addItem(nmrSaveFrame.name, nmrSaveFrame)
    #
    self.stack.pop()
    return nmrDataBlock


  def preValidateSaveFrame(self, saveFrame):

    self.stack.append(saveFrame)
    commonPrefix = os.path.commonprefix([tt[0] for tt in saveFrame.items()
                                         if isinstance(tt[1], str)])
    tt = commonPrefix.split('.', 1)
    if len(tt) == 2:
      prefix = tt[0] + '.'
    else:
      self.raiseValidationError(
        "Saveframe tags do not start with a common dot-separated prefix: %s"
        % [tt[0] for tt in saveFrame.items() if isinstance(tt[1], str)]
      )

    sf_category = saveFrame.get(prefix + 'sf_category')
    if sf_category is None:
      self.raiseValidationError("SaveFrame lacks .sf_category item")
    sf_framecode = saveFrame.get( prefix + 'sf_framecode')
    if sf_framecode is None:
      self.raiseValidationError("SaveFrame lacks .sf_framecode item")

    sf_lowername = saveFrame.name   # NB tags are lower-cased from the parser
    if sf_lowername.startswith('save_'):
      sf_lowername = sf_lowername[5:]
    if sf_lowername != sf_framecode.lower():
      self.raiseValidationError("Saveframe.name %s does not match sf_framecode %s"
                       % (sf_lowername, sf_framecode))

    if self.fileType == 'nef':
      if not sf_framecode.startswith(sf_category):
        self.raiseValidationError("NEF file sf_framecode %s does not start with the sf_category %s" %
                         (sf_framecode, sf_category))
      if prefix[1:-1] != sf_category:
        self.raiseValidationError("NEF file sf_category %s does not match tag prefix %s" %
                         (sf_category, prefix))
    else:
      # NBNB TBD We do not check or store the tag prefix
      pass

    for tag, value in saveFrame.items():
      self.stack.append(tag)
      if isinstance(value, GenericStarParser.Loop):
        if tag == value.name:
          self.preValidateLoop(value)
      elif not isinstance(value, str):
        self.raiseValidationError("Saveframe contains item value of wrong type: %s"
                                  % value)
      self.stack.pop()

    self.stack.pop()

  def convertSaveFrame(self, saveFrame):

    self.stack.append(saveFrame)

    #Get common dot-separated prefix from non-loop items
    commonPrefix = os.path.commonprefix([tt[0] for tt in saveFrame.items()
                                         if isinstance(tt[1], str)])
    tt = commonPrefix.split('.', 1)
    if len(tt) == 2:
      prefix = tt[0] + '.'
    else:
      self.raiseValidationError(
        "Saveframe tags do not start with a common dot-separated prefix: %s"
        % [tt[0] for tt in saveFrame.items() if isinstance(tt[1], str)]
      )

    # get category and framecode
    # The prevalidation has already established that there is exactly one tag for each
    tags = [x for x in saveFrame if x.endswith('.sf_framecode')]
    sf_framecode = saveFrame[tags[0]]
    tags = [x for x in saveFrame if x.endswith('.sf_category')]
    sf_category = saveFrame[tags[0]]

    newSaveFrame = NmrSaveFrame(name=sf_framecode, category=sf_category)

    lowerCaseCategory = newSaveFrame.category.lower()
    for tag, value in saveFrame.items():

      self.stack.append(tag)

      if isinstance(value, str):
        value = self.convertValue(value, category=lowerCaseCategory, tag=tag)
        objname = tag[len(prefix):]
        newSaveFrame.addItem(objname, value)

      elif isinstance(value, GenericStarParser.Loop):
        if tag == value.columns[0]:
          # Only add loop on first appearance
          nmrLoop = self.convertLoop(value)
          newSaveFrame.addItem(nmrLoop.name, nmrLoop)
      self.stack.pop()
    #
    self.stack.pop()
    return newSaveFrame

  def preValidateLoop(self, loop):

    self.stack.append(loop)

    columns = loop.columns
    commonPrefix = os.path.commonprefix(columns)
    if len(commonPrefix.split('.', 1)) != 2:
      self.raiseValidationError(
        "Column names of %s do not start with a common dot-separated prefix: %s" % (loop, columns)
      )

    self.stack.pop()

  def convertLoop(self, loop):

    self.stack.append(loop)

    oldColumns = loop.columns
    commonPrefix = os.path.commonprefix(oldColumns)
    tt = commonPrefix.split('.', 1)
    if len(tt) == 2:
      category = tt[0]
      lenPrefix = len(category) + 1
      if category[0] == '_':
        category = category[1:]
    else:
      self.raiseValidationError(
        "Column names of %s do not start with a common dot-separated prefix: %s" % (loop,
                                                                                    oldColumns)
      )

    columns = []
    for ss in oldColumns:
      tag = ss[lenPrefix:]

      # Check for valid field names
      if tag.startswith('_') or not tag.isidentifier():
        if self.convertColumnNames:
          # make the name valid
          tag = ''.join(x if x.isalnum() else '_' for x in tag)
          while tag.startswith('_'):
            tag = tag[1:]
        else:
          raise ValueError("Invalid column name: %s" % ss)

      if keyword.iskeyword(tag):
        raise ValueError("column name (as modified) clashes with Python keyword: %s" % ss)

      columns.append(tag)

    newLoop = NmrLoop(category, columns)
    ff = self.convertValue #convertValue(value, category=lowerCaseCategory, tag=tag)
    for row in loop.data:
      values = [ff(x, category, columns[ii]) for ii,x in enumerate(row.values()) ]
      newLoop.newRow(values)

    #
    self.stack.pop()
    return newLoop

  def convertValue(self, value, category=None, tag=None):
    """NB category and tag are needed if  we want to use self.specification"""

    if self.specification:
      # Add specification-dependent processing here
      #
      return value

    if isinstance(value, GenericStarParser.UnquotedValue):
      # Convert special values
      if value == GenericStarParser.NULLSTRING :
        # null  value
        value = None
      elif value == GenericStarParser.TRUESTRING:
        # Boolean True
        value = True
      elif value == GenericStarParser.FALSESTRING:
        # Boolean False
        value = False
      elif value == GenericStarParser.UNKNOWNSTRING:
        value = None
      elif value[0] == '$':
        # SaveFrame reference
        value = value[1:]
      else:
        if not tag.startswith('sequence_code'):
          # special case: sequence_code is string even if often (mostly) matching int
          try:
            value = float(value)
          except ValueError:
            try:
              value = int(value)
            except ValueError:
              pass
    #
    return value

  def _errorMessage(self, msg):
    """Make standard error message"""
    template = "Error in context: %s\n%s"
    ll = [(x if isinstance(x, str) else x.name) for x in self.stack]
    return template % (ll, msg)

  def raiseValidationError(self, msg):
    raise StarValidationError(self._errorMessage(msg))

