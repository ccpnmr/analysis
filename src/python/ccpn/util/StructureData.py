"""Structure Data Matrix

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import math
import numbers
import typing
import copy
import numpy
import pandas as pd
from ccpn.util import Sorting
from ccpn.util.ListFromString import listFromString
from json import dumps

# Pid.IDSEP - but we do not want to import from ccpn.core here
IDSEP = '.'
NaN = math.nan

class EnsembleData(pd.DataFrame):
  """
  Structure Ensemble data - as a Pandas DataFrame

  The structure ensemble is based on a Pandas DataFrame.  All of the functionality of DataFrames
  is available, but we have added a number of convenience methods for working with the data.

  In general, there are three things you may want to do with an ensemble:

    1.	 Select a sub-set of atoms within the ensemble

    2.	 Access the data within the ensemble

    3.	 Write data to the ensemble

  We will cover each of these in turn below.

  1.	Selecting sub-sets of atoms within the ensemble:
    Subsets of atoms can be extracted by creating a selector, which is nothing more than a Pandas
    Series object. These can be thought of as a table with the same number of rows as the ensemble
    you want to select from, and containing a single column of True/False values, where True
    represents a value to be included in the selection. We provide a .selector() function that will
    return a selector based on criteria you provide.  Please note that
    although the criteria names are plural, single values are also allowed.

    The following criteria are currently supported:

      * chainCodes
        allowed values: ‘A’; ‘A,C’; ‘A, C’; [‘A’, ‘C’]
        not allowed: ‘A-C’ (currently); [‘A, B’, ‘C’] (currently)
        Note that this is case sensitive, so ‘a’ will likely not select anything

      * residueNames
        allowed values: ‘MET’; ‘MET,ALA’; ‘MET, ALA’; [‘MET’, ’ALA’]
        not allowed: ‘MET-ALA’; [‘MET, ALA’, ‘GLU’] (currently)
        Note that this is case sensitive, so ‘met’ will likely not select anything

      * sequenceIds
        allowed values: 1; ‘1’; ‘1,2’; ‘1, 2’; ‘4-7’; ‘1, 2, 4-7’; [‘1’, ‘2’]; [1, 2]
        not allowed: [1, 2, ‘4-7’] (currently);

      * atomNames
        allowed values: ‘H’; ‘H,N’; ‘H, N’; [‘H’, ‘N’]
        not allowed: ‘H-N’; [‘H, N’, ‘CA’] (currently)

      * modelNumbers
        allowed values: 1; ‘1’; ‘1,2’; ‘1, 2’; ‘4-7’; ‘1, 2, 4-7’; [‘1’, ‘2’]; [1, 2]
        not allowed: [1, 2, ‘4-7’] (currently);

      * ids
        allowed values: ‘A.3.LEU.N’; ‘A.3.LEU.N, A.3.LEU.CA’;
                        ‘A.3.LEU.N, A.3.LEU.CA’; [‘A.3.LEU.N’, ‘A.3.LEU.CA’]
        not allowed: ‘A.3.LEU.N-‘A.3.LEU.CA’; ‘A.3.LEU.N, CA’; [‘A.3.LEU.N, A.3.LEU.CA’, ‘A.3.LEU.CB’]

      * elements
        allowed values: ‘H’; ‘H,C’; ‘H, C’; [‘H’, ‘C’]
        not allowed: ‘H-N’; [‘H, N’, ‘C’]

    In addition to these criteria, functions taking a record and returning True or False can
    be supplied via the func keyword argument.

    For example:
      ensemble.selector(func=lambda r: (r[‘bFactor’]< 70) and (r[‘bFactor’]>60))
      which will select everything with a bFactor between 60 and 70 exclusive.
      The selector can be converted to a filter by setting the inverse keyword to True, so that
      any record that matches the criteria are excluded from the selection.

    Finally, selectors can be combined using Boolean operations.  The following statement:

      s = ensemble.selector(atomNames=’N, CA’)

    is equivalent to:

      s1 = ensemble.selector(atomNames=’CA’)
      s2 = ensemble.selector(atomNames=’N’)
      s = s1 | s2  # Matches either s1 OR s2

    While this statement:
      .. code-block::
      s = ensemble.selector(atomNames=’N, CA’, modelNumbers = ‘1-3’)

    is equivalent to:

      s1 = ensemble.selector(atomNames=’N, CA’)
      s2 = ensemble.selector(modelNumbers = ‘1-3’)
      s = s1 & s2  # Matches both s1 AND s2

    Because certain selections are quite common, we provide several pre-packaged selections,
    these include:
      ensemble.backboneSelector
      ensemble.amideProtonSelector
      ensemble.amideNitrogenSelector
      ensemble.methylSelector

    Note that selection on chains, residues and atoms, including the pre-packaged selectors
     refer to the names that match the coordinates, which may *not* match the data in the rest
     of your project.
    There is a separate set of columns ('nmrChainCode', 'nmrSequenceCode', 'nmrResidueName',
    'nmrAtomName' that do match the data in the rest of the project.

    Once you have a selector, you can use it to extract a copy of the rows you want from the
    ensemble via ensemble.extract(). extract() accepts a selector and a list of columns to extract.
    If no selector is provided, extract() will use any criteria provided to generate a selector
    on-the-fly for selection (in fact, this is the recommended usage pattern.)

    The extract() method has some important caveats:
    1. It is very important to remember that extract() gives a COPY of the data, not the original
        data. If you change the data in the extracted ensemble, the original data will remain
        unaltered.
    2. If you use a selector created from one ensemble on a different ensemble, it will fail if they
       don’t have exactly the same number of records.  If they do have the same number of records,
       you will get the records with the corresponding numbers, which is probably not what you want.
    3. In order to avoid the problem in 2., the recommended usage pattern is to let extract()
       create the selector on-the-fly.
    4. If you must create complex selectors, please make sure that you create the selector from the
       exact ensemble you wish to extract from.

  2.	There are several ways to access the data within the ensemble (or an extracted subset
    thereof.) If your ensemble has multiple records, copies of the columns can be accessed by name.
    For example:
      occupancies = ensemble['occupancy']  # Gives a Pandas Series; for a list use list(occupancies)
    Alternatively, you can convert the records into a tuple of namedTuples using the
    as_namedTuples() method.

    If you have a single record, the values can be accessed by column name.
    For example:
      atomName = singleRecordEnsemble[‘atomName’]

    Instead, it’s often better to loop over copies of all the records in a subset using the
    iterrecords() iterator:
      for record in ensemble.iterrecords():
        print(record[‘x’], record[‘y’], record[‘z’])

    or the itertuples() iterator:
      for record in ensemble.itertuples():
        print(record.x, record.y, record.z)

    Finally, all of the standard Pandas methods for accessing the data are still available.
    We leave it to the interested coder to investigate that.

    3. Writing data to the ensemble is by far the most tricky operation.  There are two primary
       issues to be dealt with:  putting data in the right place within the ensemble, and making
       sure you’re writing to the ensemble and not a copy of the ensemble.

    The easiest case is probably the least common for users: creating an ensemble from scratch.
    In this case, the best way to create the ensemble is to assign several equal-length lists or
    tuples to columns within the ensemble:
      ensemble = EnsembleData()
      ensemble[‘modelNumber’] = [1,1,1,2,2,2]
      ensemble[‘chainCode’] = [‘A’, ‘A’, ‘A’, ‘A’, ‘A’, ‘A’]
      # Etc,…
      ensemble = ensemble.reset_index(drop=True)  # Cleanup the indexing

    More commonly, users may want to alter values in a pre-existing ensemble.  The method
    setValues() can be used for this.  The first parameter to setValues() tells setValues() which
    record to change, and can be an index, a single record selector or a single record ensemble
    (this last option is easily achieved with the iterrecords() method.)
    Any subsequent keyword parameters passed to setValues() are the column names and values to set.
    For example:
      extracted = ensemble.extract(residueNames='MET', atomNames='CB')
      for record in extracted.iterrecords():
        if record[‘x’] > 999:
          ensemble.setValues(record, x=999, y=999, z=999)

    Just like extract(), exactly matching the source of your selector/selecting ensemble and the
    ensemble you call setValues() on is vital to prevent unpredictable behavior.
    You have been warned!

    There are currently no insert functions.  You can, if you wish, append a row to the ensemble
    using setValues and passing an index value not currently in the ensemble:
      maxEnsembleIndexValue = ensemble.index.max()
      ensemble.setValues(maxEnsembleIndexValue+1, x=0, y=1, z=2)


  ADVANCED: Pandas experts should note that we override __setattr__, __setitem__, and __str__,
  so some behaviours will be different. Specifically columns with reserved names are type-checked,
  and you cannot add new columns with data that match only part of the existing rows.
  """

  # Key is column name, value is (type, customSetterName) tuple
  _reservedColumns = collections.OrderedDict((
    ('modelNumber', (int, '_modelNumberConversion')),
    ('chainCode', (str, None)),
    ('sequenceId', (int, None)),
    ('insertionCode', (str, None)),
    ('residueName', (str, None)),
    ('atomName', (str, None)),
    ('altLocationCode', (str, None)),
    ('element', (str, None)),
    ('x', (float, None)),
    ('y', (float, None)),
    ('z', (float, None)),
    ('occupancy', (float, '_occupancyConversion')),
    ('bFactor', (float, None)),
    ('nmrChainCode', (str, None)),
    ('nmrSequenceCode', (str, '_nmrSequenceCodeConversion')),
    ('nmrResidueName', (str, None)),
    ('nmrAtomName', (str, None))
  ))

  @property
  def _containingObject(self) -> typing.Optional[typing.Union['StructureEnsemble', 'Model']]:
    """CCPN wrapper object containing instance. """
    return self.__containingObject

  @_containingObject.setter
  def _containingObject(self, value):
    """Get containing object"""
    if (value is None
        or (hasattr(value, 'className') and value.className in ('StructureEnsemble', 'Model'))):
      self.__containingObject = value
    else:
      raise ValueError(
        "EnsembleData._containingObject must be None, StructureEnsemble or Model, was %s"
        % value
      )

  @property
  def _structureEnsemble(self) -> typing.Optional['StructureEnsemble']:
    """Get containing StructureEnsemble, whether container is StructureEnsemble or Model"""
    result = self.__containingObject
    if hasattr(result, 'className') and result.className == 'Model':
      result = result.structureEnsemble

    return result


  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)

    # Link to containing StructureEnsemble - to allow logging, echoing, and undo
    # NB ModelData temporarily resets this to a Model object
    self.__containingObject = None

  ### Making selections

  # def drop(self, labels, axis = 0, level = None, inplace = False, errors = 'raise'):    # ejb
  #   """
  #   Overload the Pandas drop to reset the indexing after items have been removed
  #   :param labels:
  #   :param axis:
  #   :param level:
  #   :param inplace:
  #   :param errors:
  #   :return:
  #   """
  #   super().drop(labels, axis, level, inplace, errors)
  #   # self.reset_index(drop=True, inplace=True)

  def selector(self, index=None, chainCodes=None, residueNames=None, sequenceIds=None,
               atomNames=None, modelNumbers=None, ids=None,
               elements=None, func=None, inverse=False) -> pd.Series:
    """
    Make a boolean selector restricted to rows matching the parameters specified.

    NB Incompatible values of the selection parameters may raise various errors.

    Returns Pandas Series of booleans
    """
    s = pd.Series((True,) * self.shape[0], index=self.index) #range(1,self.shape[0]+1))      # ejb
    # s = pd.Series((True,) * self.shape[0], index=range(1,self.shape[0]+1))      # ejb
    if index is not None:
      s = s & self._indexSelector(index)
    if chainCodes is not None:
      s = s & self._stringSelector(chainCodes, 'chainCode')
    if residueNames is not None:
      s = s & self._stringSelector(residueNames, 'residueName')
    if sequenceIds is not None:
      s = s & self._sequenceIdsSelector(sequenceIds)
    if atomNames is not None:
      s = s & self._stringSelector(atomNames, 'atomName')
    if modelNumbers is not None:
      s = s & self._modelsSelector(modelNumbers)
    if ids is not None:
      s = s & self._idsSelector(ids)
    if func is not None:
      s = s & self._funcSelector(func)
    if elements is not None:
      s = s & self._stringSelector(elements, 'element')
    if inverse:
      return ~s
    return s

  def _stringSelector(self, expression:typing.Union[str, typing.Iterable[str]],
                      columnName:str) -> pd.Series:
    """Select column 'columnName' based on 'expression',
    which must either be or convert to a sequence of strings
    """
    if isinstance(expression, str):
      expression = listFromString(expression)
    return self[columnName].isin(expression)

  def _sequenceIdsSelector(self, expression:typing.Union[str, int, typing.Iterable]) -> pd.Series:
    """Select column sequenceId based on 'expression'
    """
    if isinstance(expression, str):
      expression = listFromString(expression)
      expression = [int(ii) for ii in expression]       # ejb - check for the other _selectors
    elif isinstance(expression, int):
      expression = [expression,]
    expression = [int(x) for x in expression]
    return self['sequenceId'].isin(expression)

  def _modelsSelector(self, expression:typing.Union[str, int, typing.Iterable]) -> pd.Series:
    """Select column modelNumber based on 'expression'
    """
    if isinstance(expression, str):
      expression = listFromString(expression)
      expression = [int(ii) for ii in expression]       # ejb - check for the other _selectors
    elif isinstance(expression, int):
      expression = [expression,]
    return self['modelNumber'].isin(expression)

  def _indexSelector(self, expression:typing.Union[str, int, typing.Iterable]) -> pd.Series:
    """Select index based on 'expression'
    """
    if isinstance(expression, str):
      expression = listFromString(expression)
      expression = [int(ii) for ii in expression]       # ejb - check for the other _selectors
    elif isinstance(expression, int):
      expression = [expression,]
    return self.index.isin(expression)

  def _idsSelector(self, expression: typing.Union[str, typing.Iterable[str]]) -> pd.Series:
    """Select records based on 'expression',
    which must either be or convert to a sequence of string atom IDs
    """
    s = pd.Series((False,) * self.shape[0], index=self.index)    # ejb
    if isinstance(expression, str):
      expression = listFromString(expression)
    for i in expression:
      chain, seqId, name, atom = i.split(IDSEP)
      s = s | self.selector(chainCodes=[chain, ], sequenceIds=[int(seqId), ], residueNames=[name, ],
                            atomNames=[atom, ])
    return s

  def _funcSelector(self, func:callable) -> pd.Series:
    return self.apply(func, axis=1)


  ### Protein specific automatically generated selectors

  @property
  def backboneSelector(self) -> pd.Series:
    """
    Return a selector that selects backbone atoms.

    The selector is specific for:
      Ca, C', O, Nh, Hn
    """
    return self.selector(atomNames=['CA', 'C', 'N', 'O', 'H'])


  @property
  def amideProtonSelector(self) -> pd.Series:
    """
    Return a selector that selects only the amide proton.
    """
    return self.selector(atomNames=['H'])


  @property
  def amideNitrogenSelector(self) -> pd.Series:
    """
    Return a selector that selects only the amide nitrogen.
    """
    return self.selector(atomNames=['N'])


  @property
  def methylSelector(self) -> pd.Series:
    """
    Return a selector that selects atoms in methyl groups.

    The selector is specific for:
      Ala: Cb and attached protons
      Leu: Both Cd's and attached protons
      Met: Ce and attached protons
      Thr: Cg and attached protons
      Val: Both Cg's and attached protons
    """
    s = self.selector(residueNames=['ALA'], atomNames=['CB', 'HB1', ' HB2', 'HB3'])
    s = s | self.selector(residueNames=['LEU'],
                          atomNames=['CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23'])
    s = s | self.selector(residueNames=['MET'], atomNames=['CE', 'HE1', 'HE2', 'HE3'])
    s = s | self.selector(residueNames=['THR'], atomNames=['CG', 'HG1', 'HG2', 'HG3'])
    s = s | self.selector(residueNames=['VAL'],
                          atomNames=['CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23'])
    return s


  ### extracting selections

  def extract(self, selector:pd.Series=None, *columnNames:str, **kwargs) -> 'EnsembleData':
    """
    Extracts a copy of a subset of atoms from the EnsembleData

    Params:

      selector : Boolean Pandas series the same length as the number of rows in the ensemble
                  If no selector is given, the keyword arguments are passed on to the selector
                  function and used to make a selector to use.

      *columnNames: All positional arguments indicate the columns to extract.
                    If there are no columnNames, all columns are extracted.

      **kwargs: All keyword-value arguments are passed to the selector function.

    Returns a new EnsembleData
    """
    if not columnNames:
      columnNames = self.columns

    if selector is None:
      return self.extract(self.selector(**kwargs), *columnNames)   # ejb

    else:
      try:
        if self.shape[0] == selector.shape[0]:
          newEx = self.ix[selector, columnNames]
          return newEx

        else:
          raise ValueError('Selectors must be the same length as the number of atom records.')
      except AttributeError:
        raise ValueError("selector must be a Pandas series or None")


  ### Record-wise access

  def iterrecords(self) -> 'EnsembleData':
    """
    An iterator over the records (atoms) in the ensemble
    """
    for idx, record in self.iterrows():
      yield EnsembleData(record.to_frame().T)

  def records(self) -> typing.Tuple['EnsembleData', ...]:
    return tuple(self.iterrecords())

  def as_namedtuples(self)-> typing.Tuple[typing.Tuple, ...]:
    """
    An tuple of namedtuples containing the records (atoms) in the ensemble
    """
    return tuple(self.itertuples(name='AtomRecord'))


  ### Record-wise assignment of values

  def addRow(self, **kwargs):
    """
    Add row with values matching kwargs, setting index to next available index
    See setValues for details
    """
    nextIndex =  max(self.index) + 1 if self.shape[0] else 1
    self.setValues(nextIndex, **kwargs)

  def _insertSelectedRows(self, **kwargs):    # ejb
    """
    Re-insert rows that have been deleted with deleteSelectedRows below
    This is for use by undo/redo only
    """
    containingObject = self._containingObject
    if containingObject is not None:
      undo = containingObject._project._undo      # check that this is valid
      undo.increaseBlocking()

    try:
      insertSet = kwargs['iSR']
      for thisInsertSet in insertSet:
        for rowInd in thisInsertSet:
          self._insertRow(int(rowInd), **thisInsertSet[rowInd])

      self._structureEnsemble._finaliseAction('change')       # spawn a change event in StructureEnsemble

    finally:
      if containingObject is not None:
        undo.decreaseBlocking()

  def deleteSelectedRows(self, **kwargs):
    """
    Delete rows identified by selector.
    For example (index='1, 2, 6-7, 9')
                (modelNumbers='1, 2') or
                (residueNames='LEU, THR')

    In the cases of the reserved columns, the name may need to be plural for deletion

    e.g. above, the column headed modelNumberm ay be accessed as 'modelNumbers'

    **kwargs: All keyword-value arguments are passed to the selector function.

    Selector created, e.g. by self.selector)
    """

    # TODO NBNB add echo handling,undo, notifier, index handling

    rowSelector = self.selector(**kwargs)

    selection = self.extract(rowSelector)
    if not selection.shape[0]:
      # nothing to delete
      return

    deleteRows = selection.as_namedtuples()

    containingObject = self._containingObject
    if containingObject is not None:
      # undo and echoing
      containingObject._startCommandEchoBlock('deleteSelectedRows')

    try:
      colData = []
      for rows in deleteRows:
        colInd = getattr(rows, 'Index')
        colData.append({str(colInd):dict((x, self.loc[colInd].get(x)) for x in self.columns)})

      self.drop(self[rowSelector].index, inplace=True)
      self.reset_index(drop=True, inplace=True)

      if containingObject is not None:
        undo = containingObject._project._undo

        if undo is not None:
          undo.newItem(self._insertSelectedRows, self.deleteSelectedRows,
                       undoArgs=(), undoKwargs={'iSR':colData},
                       redoArgs=(), redoKwargs=kwargs)

        self._structureEnsemble._finaliseAction('change')

    finally:
        if containingObject is not None:
          containingObject._endCommandEchoBlock()

  def _insertRow(self, *args, **kwargs):    # ejb
    """
    Currently called by undo to re-insert a row.
    Add the **kwargs to new element at the bottom of each column.
    Modify the index and sort the new row into the correct position.
    Only for use by deleteCol for undo/redo functionality

    :param *args: index in args[0]
    :param kwargs: dict of items to reinsert
    """
    containingObject = self._containingObject
    if containingObject is not None:
      undo = containingObject._project._undo      # check that this is valid
      undo.increaseBlocking()

    try:
      index = int(args[0])
      len = self.shape[0]                         # current rows
      for key in kwargs:
        self.loc[len+1, key] = kwargs[key]     # force an extra row

      neworder = [x for x in range(1,index)]+[x for x in range(index+1,len+2)]+[index]
      self.index = neworder                       # set the new index
      self.sort_index(inplace=True)                     # and re-sort the table

      self._structureEnsemble._finaliseAction('change')

    finally:
      if containingObject is not None:
        undo.decreaseBlocking()

  def deleteRow(self, rowNumber):    # ejb - *args, **kwargs):
    """
    Delete a numbered row of the table.
    Row must be an integer and exist in the table.

    :param rowNumber: row to delete
    """
    if not isinstance(rowNumber, int):
      raise TypeError('deleteRow: Row is not an int')

    rowExists = False
    if rowNumber in self.index:       # the index must exist
      rowExists = True
    else:
      raise ValueError('deleteRow: Row does not exist')

    index = rowNumber
    containingObject = self._containingObject
    if containingObject is not None:
      # undo and echoing
      containingObject._startCommandEchoBlock('deleteRow', rowNumber)

    try:
      colData = dict((x, self.loc[index].get(x)) for x in self.columns)  # grab the original values

      self.drop(index, inplace=True)                # delete the row
      self.reset_index(drop=True, inplace=True)     # ejb - reset the index

      if containingObject is not None:
        undo = containingObject._project._undo
        if undo is not None:                        # add the undo event
            undo.newItem(self._insertRow, self.deleteRow,
                         undoArgs=(index,), undoKwargs=colData,
                         redoArgs=(index,), redoKwargs={})
        # assert  self._structureEnsemble is not None # given that containingObject exists
        self._structureEnsemble._finaliseAction('change')

    finally:
      if containingObject is not None:
        containingObject._endCommandEchoBlock()

  def _insertCol(self, *args, **kwargs):     # ejb
    """
    Currently called by undo to re-insert a column.
    Add the **kwargs to the column across the index.
    Currently *args are not checked for multiple values
    Only for use by deleteCol for undo/redo functionality
    :param *args: colIndex in args[0]
    :param kwargs: items to reinsert as a Dict
    """
    containingObject = self._containingObject
    if containingObject is not None:
      undo = containingObject._project._undo      # check that this is valid
      undo.increaseBlocking()                     # not sure that this is needed here
                                                  # I think it is all handled by undo
    try:
      colIndex = str(args[0])       # get the index from the first arg value
      for sInd in kwargs:
        self.loc[int(sInd), colIndex] = kwargs[sInd]

      structureEnsemble = self._structureEnsemble
      if structureEnsemble is not None:
        structureEnsemble._finaliseAction('change')

      self._structureEnsemble._finaliseAction('change')

    finally:
      if containingObject is not None:
        undo.decreaseBlocking()

  def deleteCol(self, columnName):    # ejb -, *args, **kwargs):
    """
    Delete a named column from the table, the columnName must be a string and exist in the table.

    :param columnName:  name of the column
    """
    if not isinstance(columnName, str):
      raise TypeError('deleteCol: Column is not a string')

    colExists = False
    if columnName in self.columns:       # the index must exist
      colExists = True
    else:
      raise ValueError('deleteCol: Column does not exist.')

    colIndex = columnName
    containingObject = self._containingObject
    if containingObject is not None:
      # undo and echoing
      containingObject._startCommandEchoBlock('deleteCol', columnName)     # ejb, values=kwargs)

    try:
      colData = dict((str(sInd), self.loc[sInd].get(colIndex)) for sInd in self.index)  # grab the original values

      self.drop(colIndex, axis=1, inplace=True)

      if containingObject is not None:
        undo = containingObject._project._undo
        if undo is not None:                        # add the undo event
            undo.newItem(self._insertCol, self.deleteCol,
                         undoArgs=(colIndex,), undoKwargs=colData,
                         redoArgs=(colIndex,))
        # assert  self._structureEnsemble is not None # given that containingObject exists
        self._structureEnsemble._finaliseAction('change')

    finally:
      if containingObject is not None:
        containingObject._endCommandEchoBlock()

  def setValues(self, accessor:typing.Union[int, 'EnsembleData', pd.Series], **kwargs) -> None:
    """
    Allows you to easily set values (in place) for fields in the EnsembleData

    Params:
      accessor : int, EnsembleData, Selector
                 If an integer is given, the value will be set on the row at that index,
                 a new row will be added if the value is the next free index,
                 or ValueError will be raised.

                 If a single row EnsembleData is given, the value will be set on the matching row.

                 If a selector that matches a single row is given, the value will be set on that
                 matching row

                 Multi-row EnsembleData or selectors are not allowed.
                 (consider using EnsembleData.iterrecords() to iterate)

      kwargs : columns on which to set the values

    """

    # Row selection:
    Real= numbers.Real

    rowExists = True
    if isinstance(accessor, pd.Int64Index):
      accessor = int(accessor[0])             # ejb - accessor becomes the wrong type on undo

    if isinstance(accessor, (int, numpy.integer)):
      # This is utter shit! Why are numpy.integers not ints, or at least with a common superclass?
      # Shows again that numpy is an alien growth within python.
      index = accessor
      if index in self.index:
        rowExists = True
      else:
        rowExists = False
        nextIndex = max(self.index) + 1 if self.shape[0] else 1
        if index != nextIndex:
          raise ValueError("setValues cannot create a new row, "
                           "unless accessor is the next free integer index")

      if kwargs:
        # ejb - only get those values that have the correct index

        sl = self.loc[index]
        # nt = sl._asdict()
        oldKw = dict((x, sl[x]) for x in kwargs)
      else:
        oldKw = dict((x, self[x]) for x in kwargs)    # get everything, as no kwargs specified

    elif isinstance(accessor, EnsembleData):
      assert accessor.shape[0] == 1, "Only single row ensembles can be used for setting."
      index = accessor.index
      #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
      #
      # global _indexOverride
      # _indexOverride = True  # ejb - just need existence
      aant = accessor.as_namedtuples()      # testing for below
      slan = self.loc[index].as_namedtuples()
      # del _indexOverride

      # tsit = tuple(self.itertuples(name='AtomRecord'))[index[0]]
      #tuple(self.itertuples(name='AtomRecord'))

      assert (index[0] in self.index and aant == slan), (
        "Ensembles used for selection must be (or match) row in current ensemble")

      sl = self.loc[index].as_namedtuples()   # ensemble get
      nt = sl[0]._asdict()
      oldKw = dict((x, nt[x]) for x in kwargs)

      # assert (index[0] in self.index
      #         and accessor.as_namedtuples() == self.loc[index].as_namedtuples()), (
      #   "Ensembles used for selection must be (or match) row in current ensemble"
      # )
      #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    elif isinstance(accessor, pd.Series): # selector
      rows = accessor[accessor == True]
      assert rows.shape[0] == 1, "Boolean selector must select a single row."
      index = rows.index
      assert index[0] in self.index, "Boolean selector must select an existing row"   # ejb

      try:
        sl = self.loc[index].as_namedtuples()  # ensemble get
        nt = sl[0]._asdict()
        oldKw = dict((x, nt[x]) for x in kwargs)
      except KeyError:
        raise ValueError("Attempt to set columns not present in DataFrame: %s"
                         % list(kwargs))

    else:
      raise TypeError('accessor must be index, ensemble row, or selector.')

    if rowExists and not kwargs:
      # No changes - and setting with an empty dictionary gives an error
      return

    # input data and columns
    values = {}
    kwargsCopy = kwargs.copy()
    for col in self.columns:

      # dataType, typeConverterName = self._reservedColumns.get(col) or (None, None)

      if col in kwargsCopy:
        value = kwargsCopy.pop(col)

        values[col] = value

      elif not rowExists:
        # For new rows we want None rather than NaN as the default values
        # For existing rows we leave the existing value
        values[col] = None

    if kwargsCopy:
      # Some input did not match columns
      raise ValueError("Attempt to set columns not present in DataFrame: %s"
                       % list(kwargsCopy))

    containingObject = self._containingObject
    if containingObject is not None:
      # undo and echoing
      containingObject._startCommandEchoBlock('setValues', values=kwargs)
      undo = containingObject._project._undo      # ejb
      undo.increaseBlocking()       # ejb

    try:
      # We must do this one by one - passing in the dictionary
      # gives you a series, and coerces None to NaN.

      # Internally this calls self.__setitem__.
      # Type handling is done there and can be skipped here.
      # NB, various obvious alternatives, like just setting the row, do NOT work.

      # tempkw = dict((x, self.loc[index].get(x)) for x in kwargs)  # ejb - grab the original values
      # tempkw = dict((x, getattr(self.loc[index], x)) for x in kwargs)  # ejb - grab the original values
      # tempkw = {t.__name__: t for t in slan[0]}
      # tempkw = vars(slan[0])

      # sl = self.loc[index].as_namedtuples()   # ensemble get
      # nt = sl[0]._asdict()
      # tempkw = dict((x, nt[x]) for x in kwargs)

      # nt = slan[0]._asdict()
      # tempkw = dumps(nt)
      for key,val in values.items():
        self.loc[index, key] = val

    finally:
      if containingObject is not None:
        undo.decreaseBlocking()  # ejb
        containingObject._endCommandEchoBlock()

    # ejb/Rasmus removed here, should be covered by __setItem__
    # must be this way around, otherwise setValues with new column gets transposed
    if containingObject is not None:
      undo = containingObject._project._undo
      if undo is not None:
        # set up undo functions
        if rowExists:
          # Undo modification of existing row
          # undo.newItem(self.setValues, self.setValues,
          #              undoArgs=(index,), undoKwargs=dict((x, self.loc[index].get(x))
          #                                                    for x in kwargs),
          #              redoArgs=(index,), redoKwargs=kwargs)
          undo.newItem(self.setValues, self.setValues,
                       undoArgs=(index,), undoKwargs=oldKw,
                       redoArgs=(index,), redoKwargs=kwargs)
        else:
          # undo addition of new row
          undo.newItem(self.drop, self.setValues,
                       undoArgs=(index,), undoKwargs={'inplace':True},
                       redoArgs=(index,), redoKwargs=kwargs)
      # assert  self._structureEnsemble is not None # given that containingObject exists
      self._structureEnsemble._finaliseAction('change')


  ### PDB mapping

  @classmethod
  def from_pdb(cls, filename: str) -> pd.DataFrame:
    """
    Create an EnsembleData from a pdb file.
    """
    dfs = pdb2df(filename)

    ensemble = cls()

    ensemble['modelNumber'] = dfs['model']
    ensemble['chainCode'] = dfs['chainID']
    ensemble['sequenceId'] = dfs['resSeq']
    ensemble['insertionCode'] = dfs['iCode']
    ensemble['residueName'] = dfs['resName']
    ensemble['atomName'] = dfs['name']
    ensemble['altLocationCode'] = dfs['altLoc']
    ensemble['element'] = dfs['element']
    ensemble['x'] = dfs['x']
    ensemble['y'] = dfs['y']
    ensemble['z'] = dfs['z']
    ensemble['occupancy'] = dfs['occupancy']
    ensemble['bFactor'] = dfs['tempFactor']
    ensemble['nmrChainCode'] = None
    ensemble['nmrSequenceCode'] = None
    ensemble['nmrResidueName'] = None
    ensemble['nmrAtomName'] = None
    return cls(ensemble)


  ### Pandas compatibility methods

  @property
  def _constructor(self) -> 'EnsembleData':
    return self.__class__


  def __setattr__(self, name:str, value:typing.Any) -> None:
    if name in self._reservedColumns:
      # notification done at the __setitem__ level
      self[name] = value
    else:
      super().__setattr__(name, value)

      structureEnsemble = self._structureEnsemble
      if structureEnsemble is not None:
        structureEnsemble._finaliseAction('change')


  ### Property type checking

  def _ccpnUnSort(self, oldIndex):
    """Custom Unsort: revert the table to its presorted state"""
    self.index = oldIndex
    self.sort_index(inplace=True)
    self.reset_index(drop=True, inplace=True)  # use the correct reset_index

    pass

  def ccpnSort(self, *columns:str):
    """Custom sort. Sorts mixed-type columns by type, sorting None and NaN at the start

    If nmrSequenceCode or nmrAtomName or nmrChainCode are included in columns
    uses custom sort *for all strings* so that e.g. '@3' comes before '@12' and '7b' before '22a' """
    cols = list(self[x] for x in columns)
    cols.append(self.index)

    # Set sorting key for sorting mixed incompatible types
    if ('nmrSequenceCode' in columns or 'nmrAtomName' in columns
        or 'nmrChainCode' in columns):
      # Sort so that all strings containing integers are sorted by the integer
      # E.g. '@9' before '@12', and '3' before '21b'
      # Basically a heuristic to sort nmrSequenceCode or nmrAtomName in sensible order
      sortKey = Sorting.universalNaturalSortKey
    else:
      # sort strings normally
      sortKey = Sorting.universalSortKey

    # old index in sorted order
    reordered = list(tt[-1] for tt in sorted(zip(*cols), key=sortKey))
    ll = list((prev, new + 1) for new,prev in enumerate(reordered))
    newIndex = list(tt[1] for tt in sorted(ll))

    containingObject = self._containingObject
    if containingObject is not None:
      # undo and echoing
      containingObject._startCommandEchoBlock('ccpnSort', columns)
      undo = containingObject._project._undo      # ejb
      undo.increaseBlocking()       # ejb

    try:
      # do the sort here

      self.index = newIndex
      self.sort_index(inplace=True)

      # reset index to one-origin successive integers
      # self.index = range(1, len(reordered) + 1)   # old indexing
      self.reset_index(drop=True, inplace=True)     # use the correct reset_index

    finally:
      if containingObject is not None:
        undo.decreaseBlocking()  # ejb
        containingObject._endCommandEchoBlock()

    if containingObject is not None:
      undo = containingObject._project._undo
      if undo is not None:
        # set up undo functions
        undo.newItem(self._ccpnUnSort, self.ccpnSort,
                     undoArgs=(reordered,), redoArgs=columns)

    structureEnsemble = self._structureEnsemble
    if structureEnsemble is not None:
      structureEnsemble._finaliseAction('change')

  def reset_index(self, *args, inplace=False, **kwargs):
    """reset_index - overridden to generate index starting at one."""
    if inplace:
      new_obj = self
    else:
      new_obj = self.copy()
    new_obj.__class__.__bases__[0].reset_index(new_obj, *args, inplace=inplace, **kwargs)
    # new_obj.index = range(1, self.shape[0] + 1)
    new_obj.index = new_obj.index + 1

    if inplace:
      structureEnsemble = self._structureEnsemble
      if structureEnsemble is not None:
        structureEnsemble._finaliseAction('change')
    else:
      return new_obj


  def __setitem__(self, key:str, value:typing.Any) -> None:
    """If the key is a single string with a reserved column name
    the value(s) must be of the right type, and the operation is echoed and undoable.
    Other keys are treated like native Pandas operations: no echoing, no undoing,
    and no type checking.
    """

    firstData = not(self.shape[0])

    columnTypeData = self._reservedColumns.get(key)
    if columnTypeData is None:
      # Not a reserved column name - set the value. No echoing or undo.
      super().__setitem__(key, value)

    else:
      # Reserved column name (which must be a plain string)

      containingObject = self._containingObject
      if containingObject is not None:
        # echoing
        # NB using '__setitem__' does not look nice, but it is what we do.
        # We can make a nice-looking synonym later, if we want.
        # NB with large objects the echo will be huge and ugly.
        # But it is almost impossible to compress the great variety of value types Pandas allow.

        containingObject._startCommandEchoBlock('data.__setitem__', key, value)
        project = containingObject._project
        project.blankNotification()
        undo = project._undo
        # undo.increaseBlocking()       # ejb

      # WE need a copy, not a view, as this is used for undoing etc.
      oldValue = self.get(key)
      if oldValue is not None:
        oldValue = oldValue.copy()
      # NBNB copy.copy returns a VIEW!!!

      # Set the value using normal pandas behaviour.
      # Anyway it is impossible to modify the input, as it could take so many forms
      # We clean up the type castings etc. lower down
      super().__setitem__(key, value)

      dataType, typeConverterName = columnTypeData
      try:

        if typeConverterName:
          if hasattr(self, typeConverterName):
            # get typeConverter and call it. It modifies self in place.
            getattr(self, typeConverterName)()
          else:
            raise RuntimeError("Code Error. Invalid type converter name %s for column %s"
                               % (typeConverterName, key))
        else:
          # We set again to make sure of the dataType
          ll = fitToDataType(self[key], dataType)
          if dataType is int and None in ll:
            super().__setitem__(key, pd.Series(ll, self.index, dtype=object))
          else:
            super().__setitem__(key, pd.Series(ll, self.index, dtype=dataType))

        if firstData:
          self.reset_index(drop=True, inplace=True)

        if containingObject is not None:
          # WARNING This code is also called when you do ModelData.__setitem__
          # In those cases containingObject is temporarily rest to the Model object
          # Any bugs/modifications that arise in this code must consider ModelData as well
          undo = containingObject._project._undo
          if undo is not None:
            # set up undo functions
            if oldValue is None:
              # undo addition of new column
              undo.newItem(self.drop, self.__setitem__,
                           undoArgs=(key,), undoKwargs={'axis':1, 'inplace':True},
                           redoArgs=(key, value))
            else:
              # Undo overwrite of existing column
              undo.newItem(super().__setitem__, self.__setitem__,
                           undoArgs=(key, oldValue), redoArgs=(key, value))

          # assert  self._structureEnsemble is not None # given that containingObject exists
          self._structureEnsemble._finaliseAction('change')

      except:
        # We set the new value before the try:, so we need to go back to the previous state
        if oldValue is None:
          self.drop(key, axis=1, inplace=True)
        else:
          super().__setitem__(key, oldValue)
        raise
      finally:
        if containingObject is not None:
          project._endCommandEchoBlock()
          project.unblankNotification()
          # undo.decreaseBlocking()          # ejb

  def _modelNumberConversion(self, force:bool=False):
    """Convert modelNumber series to valid data, changing value *in place*
    and update containingObject - or raise an error"""

    key = 'modelNumber'

    ll = fitToDataType(self[key], int, force=force)
    if force:
      ll = [(x if (x and x > 0) else None) for x in ll]
    else:
      if any((x is not None and x < 1) for x in ll):
        raise ValueError("Model numbers must be integers >= 1 or None")
    if None in ll:
      super().__setitem__(key, pd.Series(ll, self.index, dtype=object))
    else:
      super().__setitem__(key, pd.Series(ll, self.index, dtype=int))

    # Reset models to match model numbers in data
    # NBNB resetModels currently removes rows with modelNumber == None. To change??
    containingObject = self._containingObject
    if containingObject is not None:
      if hasattr(containingObject, 'resetModels'):
        # assert(containingObject.className == 'StructureEnsemble')
        containingObject.resetModels()
      else:
        # assert(containingObject.className == 'Model')
        containingObject.structureEnsemble.resetModels()

  def _nmrSequenceCodeConversion(self, force:bool=False):
    """Convert nmrSequenceCode series to valid data, changing value *in place*

    NB this is needed to convert integers and integer-valued floats
    (which could easily be created during setting) to str(int)"""

    key = 'nmrSequenceCode'
    Real = numbers.Real
    fmod = math.fmod
    isnan = math.isnan
    ll = []
    appnd = ll.append
    for val in self[key]:
      if val is None or isinstance(val,str):
        appnd(val)
      elif isinstance(val, (int, numpy.integer)):
        appnd(str(val))
      elif isinstance(val, Real):
        if isnan(val):
          appnd(None)
        elif not fmod(val, 1):
          appnd(str(int(val)))
        elif force:
          appnd(str(val))
        else:
          raise ValueError("nmrSequenceCode must have integer values if entered as numbers")
      elif force:
        appnd(str(val))
      else:
        raise ValueError("nmrSequenceCode must be set as strings or integer values")
    #
    super().__setitem__(key, pd.Series(ll, self.index, dtype=str))

  def _occupancyConversion(self, force:bool=False) -> typing.Optional[pd.Series]:
    """Convert occupancy series to valid data, changing value *in place*"""

    key = 'occupancy'
    NaN = float('NaN')

    ll = fitToDataType(self[key], float, force=force)
    if force:
      ll = [(x if 0 <= x <= 1 else NaN) for x in ll]
    else:
      if any((x < 0 or x > 1) for x in ll):
        raise ValueError("Occupancies must be in the range 0 <= x <= 1")
    super().__setitem__(key, pd.Series(ll, self.index, dtype=float))

  # Custom string representation
  def __str__(self) -> str:
    d = dict()
    try:
      d['models'] = len(self['modelNumber'].unique())
    except KeyError:
      d['models'] = '?'
    try:
      d['chains'] = len(self['chainCode'].unique())
    except KeyError:
      d['chains'] = '?'
    try:
      d['residues'] = self.groupby(['chainCode', 'sequenceId']).count().shape[0]
    except KeyError:
      d['residues'] = '?'
    try:
      d['atoms'] = self.groupby(['chainCode', 'sequenceId', 'atomName']).count().shape[0]
    except KeyError:
      d['atoms'] = self.shape[0]
    # Just count atoms...?

    return '<EnsembleData (M:{models},C:{chains},R:{residues},A:{atoms})>'.format(**d)


# NBNB TODO this should be Collection, not Sequence (from python 3.6 only)
def fitToDataType(data:collections.Sequence, dataType:type, force:bool=False) -> list:
  """Convert any data sequence to a list of dataType.

  If force will convert all values to type, if possible, and set None otherwise.
  Otherwise will check that all values are of correct type or None,
  and raise ValueError otherwise.

  force=True will work for types int, float, or str; it may or may not work for other types
  """

  # TODO NBNB This should be moved to util/ - probably when util/Common is refactored

  Real = numbers.Real

  if dataType is float:
    if force:
      # Convert all convertible to float (including e.g. '3.7')
      return list(pd.to_numeric(data, errors='coerce'))
    else:
      # Convert None to NaN and return if all-float
      dd = {None:float('NaN')}
      try:
        return list(x if isinstance(x, Real) else dd[x] for x in data)
      except KeyError:
        raise ValueError("Data contain non-float values")

  elif dataType is int:
    # NB, the data may have been upcasted to float previously
    # See valueToOptionalInt function for details
    return list(valueToOptionalInt(x, force=force) for x in data)

  else:
    # This certainly works for str and may mostly work for other types
    # (e.g. bool will fail for numpy arrays)
    return list(valueToOptionalType(x,  dataType, force=force) for x in data)


def valueToOptionalType(x, dataType:type, force=False) -> typing.Optional['dataType']:
  """Converts  None and NaN to None, and returns list of optional dataType

  if force is True tries to coerce value to dataType"""

  if x is None:
    return None

  elif isinstance(x, numbers.Real) and math.isnan(x):
    return None

  elif isinstance(x, dataType):
    return x

  elif force:
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # return dataType(x)
    try:
      return dataType(x)
    except:
      raise TypeError("Value %s does not correspond to type %s" % (x, dataType))
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

  else:
    raise TypeError("Value %s does not correspond to type %s" % (x, dataType))


def valueToOptionalInt(x, force:bool=False) -> typing.Optional[int]:
  """Converts  None and NaN to None, and integer-valued floats to their int value

  if force is True calls float(x) before testing"""
  if x is None or isinstance(x, numbers.Real) and math.isnan(x):
    return None

  if force:
    try:
      x = float(x)
    except:
      return None
    if math.fmod(x, 1):
      # assert bool(math.fmod(float('NaN'))) is True
      return None
    else:
      return int(x)

  elif isinstance(x, numbers.Real) and not math.fmod(x, 1):
      # value equal to integer
      return int(x)

  elif isinstance(x, str):
    try:
      return int(x)
    except ValueError:
      raise TypeError("Value %s does not correspond to an integer" % x)

  else:
    raise TypeError("Value %s does not correspond to an integer" % x)


def pdb2df(filename:str) -> pd.DataFrame:
  """
  Create a Pandas dataframe from a pdb file.
  """
  with open(filename) as f:
    pdbString = []
    modelNumber = 1
    dfs = None
    for l in f:
      if l.startswith('MODEL'):
        if len(pdbString) > 0:
          df = _pdbStringToDf(pdbString, modelNumber)
          if dfs is None:
            dfs = df
          else:
            dfs = dfs.append(df)
          pdbString = []
        modelNumber = l.split()[1]
      elif l.startswith('ATOM'):
        pdbString.append(l)
    df = _pdbStringToDf(pdbString, modelNumber)
    if dfs is None:
      # print('new dfs')
      dfs = df
    else:
      dfs = dfs.append(df)
  dfs['idx'] = pd.np.arange(dfs.shape[0]) +1
  dfs.set_index('idx', inplace=True)
  return dfs


def _pdbStringToDf(modelLines:list, modelNumber=1):
  from io import StringIO

  colspecs = [(0, 6), (6, 11), (12, 16), (16, 17), (17, 20), (21, 22), (22, 26), (26, 27),
              (30, 38), (38, 46), (46, 54), (54, 60), (60, 66), (76, 78), (78, 80)]
  colnames = ['ATOM', 'serial', 'name', 'altLoc', 'resName', 'chainID', 'resSeq', 'iCode',
              'x', 'y', 'z', 'occupancy', 'tempFactor', 'element', 'charge']

  pdbString = ''.join(modelLines)

  df = pd.read_fwf(StringIO(pdbString), header=None, colspecs=colspecs, names=colnames)
  df['model'] = modelNumber
  df = df[df['ATOM'] == 'ATOM']
  return df


def averageStructure(ensemble:EnsembleData) -> EnsembleData:
  """
  Calculate the average structure from all the models in an EnsembleData object.
  """
  identifierColumns = ['chainCode', 'sequenceId', 'atomName']  # Still need to include altLocationCode
  dataColumns = ['x', 'y', 'z', 'occupancy', 'bFactor']
  dataColumns = [c for c in dataColumns if c in ensemble.columns]
  allColumns = identifierColumns + ['residueName', 'element'] + dataColumns

  ddEnsemble = ensemble.drop_duplicates(identifierColumns).copy()
  ddEnsemble['_idx'] = ddEnsemble.index
  ddEnsemble = ddEnsemble.sort_values(['chainCode', 'sequenceId', '_idx'])

  # Have pandas do the calculation for us:
  df = ensemble.groupby(identifierColumns)
  df = df[dataColumns].mean()
  df = df.reset_index()  # Flatten the multi-index
  df = df.merge(ddEnsemble, on=identifierColumns, how='left', suffixes=['', '_ensemble'])
  df = df.sort_values(['chainCode', 'sequenceId', '_idx'])
  df = df.reset_index()

  df = EnsembleData(df)
  df = df[allColumns]
  df = df.reset_index()
  return df
