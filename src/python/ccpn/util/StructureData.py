"""Structure Data Matrix

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca G Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import collections
import math
import typing
import pandas as pd
from ccpn.util.ListFromString import listFromString

# Pid.IDSEP - but we do not want to import from ccpn.core here
IDSEP = '.'


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

  # Maximum length of series to print in full when echoing commands
  MAX_PRINT_SERIES_LENGTH = 4

  _reservedColumns = collections.OrderedDict((
    ('modelNumber', '_modelNumberSetter'), # int attribute, requiring custom setter
    ('chainCode', str),
    ('sequenceId', int),
    ('insertionCode', str),
    ('residueName', str),
    ('atomName', str),
    ('altLocationCode', str),
    ('element', str),
    ('x', float),
    ('y', float),
    ('z', float),
    ('occupancy', '_occupancySetter'),  # float attribute, requiring custom setter
    ('bFactor', float),
    ('nmrChainCode', str),
    ('nmrSequenceCode', str),
    ('nmrResidueName', str),
    ('nmrAtomName', str),
  ))

  @property
  def _containingObject(self) -> typing.Optional[typing.Union['StructureEnsemble', 'Model']]:
    """CCPN wrapper object containing instance. """
    return self.__containingObject

  @_containingObject.setter
  def _containingObject(self, value):
    if (value is None
        or (hasattr(value, 'className') and value.className in ('StructureEnsemble', 'Model'))):
      self.__containingObject = value
    else:
      raise ValueError(
        "EnsembleData._containingObject must be None, StructureEnsemble or Model, was %s"
        % value
      )

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)

    # Link to containing StructureEnsemble - to allow logging, echoing, and undo
    # NB ModelData temporarily resets this to a Model object
    self.__containingObject = None

    # self.__columnSetters = {'modelNumber': self.__modelNumberSetter,
    #                         'chainCode': self.__chainCodeSetter,
    #                         'element': self.__elementSetter,
    #                         'bFactor': self.__bFactorSetter,
    #                         'occupancy': self.__occupancySetter,
    #                         'x': self.__xCoordSetter,
    #                         'y': self.__yCoordSetter,
    #                         'z': self.__zCoordSetter,
    #                         'nmrAtomName': self.__nmrAtomNameSetter,
    #                         'nmrResidueName': self.__nmrResidueNameSetter,
    #                         'nmrSequenceCode': self.__nmrSequenceCodeSetter,
    #                         'nmrChainCode': self.__nmrChainCodeSetter,
    #                         'atomName': self.__atomNameSetter,
    #                         'atomSerial': self.__atomSerialSetter,
    #                         'residueName': self.__residueNameSetter,
    #                         'insertionCode': self.__insertionCodeSetter,
    #                         'sequenceId': self.__sequenceIdSetter,
    #                        }


  ### Making selections

  def selector(self, index=None, chainCodes=None, residueNames=None, sequenceIds=None,
               atomNames=None, modelNumbers=None, ids=None,
               elements=None, func=None, inverse=False) -> pd.Series:
    """
    Make a boolean selector restricted to rows matching the parameters specified.

    NB Incompatible values of the selection parameters may raise various errors.

    Returns Pandas Series of booleans
    """
    s = pd.Series((True,) * self.shape[0])
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
    which must wither be or convert to a sequence of strings
    """
    if isinstance(expression, str):
      expression = listFromString(expression)
    return self[columnName].isin(expression)

  def _sequenceIdsSelector(self, expression:typing.Union[str, int, typing.Iterable]) -> pd.Series:
    """Select column sequenceId based on 'expression'
    """
    if isinstance(expression, str):
      expression = listFromString(expression)
    elif isinstance(expression, int):
      expression = [expression,]
    expression = [int(x) for x in expression]
    return self['sequenceId'].isin(expression)

  def _modelsSelector(self, expression:typing.Union[str, int, typing.Iterable]) -> pd.Series:
    """Select column modelNumber based on 'expression'
    """
    if isinstance(expression, str):
      expression = listFromString(expression)
    elif isinstance(expression, int):
      expression = [expression,]
    return self['modelNumber'].isin(expression)

  def _indexSelector(self, expression:typing.Union[str, int, typing.Iterable]) -> pd.Series:
    """Select index based on 'expression'
    """
    if isinstance(expression, str):
      expression = listFromString(expression)
    elif isinstance(expression, int):
      expression = [expression,]
    return self.index.isin(expression)

  def _idsSelector(self, expression: typing.Union[str, typing.Iterable[str]]) -> pd.Series:
    """Select records based on 'expression',
    which must either be or convert to a sequence of string atom IDs
    """
    s = pd.Series((False,) * self.shape[0])
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

      **kwargs: ALl keyword-value arguments are passed to the selector function.

    Returns a new EnsembleData
    """
    if not columnNames:
      columnNames = self.columns

    if selector is None:
      return self.extract(self.selector(**kwargs), columnNames)

    try:
      if self.shape[0] == selector.shape[0]:
        print ('@~@~', self.shape. selector, selector.shape)
        return self.ix[selector, columnNames]
      else:
        raise ValueError('Selectors must be the same length as the number of atom records.')
    except AttributeError:
      # raise ValueError("selector must be an integer, a Pandas series, or None")
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

  def setValues(self, accessor:typing.Union[int, 'EnsembleData', pd.Series], **kwargs) -> None:
    """
    Allows you to easily set values (in place) for fields in the EnsembleData

    Params:
      accessor : int, EnsembleData, Selector
                 If an integer is given, the value will be set on the row at that index
                 If a single row EnsembleData is given, the value will be set on the matching row.
                 If a selector that matches a single row is given, the value will be set on that
                 matching row

                 Multi-row EnsembleData or selectors are not allowed.
                 (consider using EnsembleData.iterrecords() to iterate)

      kwargs : columns on which to set the values

    """

    if len(kwargs) == 1:
      # This gives two elements, not two lists. Deliberate.
      columns, values = kwargs.popitem()
    else:
      columns, values = list(zip(*kwargs.items()))

    if isinstance(accessor, int):
      index = accessor
    elif isinstance(accessor, EnsembleData):
      assert accessor.shape[0] == 1, "Only single row ensembles can be used for setting."
      index = accessor.index
    elif isinstance(accessor, pd.Series): # selector
      assert accessor.sum() == 1, "Boolean selectors must select a single row"
      index = accessor[accessor == True].index
    else:
      raise TypeError('accessor must be index, ensemble row, or selector.')

    rowExists = index in self.index

    containingObject = self._containingObject
    if containingObject is not None:
      # undo and echoing
      containingObject._startFunctionCommandBlock('data.setValues', values=kwargs)

    try:
      self.loc[index, columns] = values

    finally:
      if containingObject is not None:
        modelNumber = kwargs.get('modelNumber')
        if modelNumber is not None:
          # NBNB The following 'if' could surely be done better in Pandas.
          # Meanwhile the 'list' should guard against possible pandas weirdness
          if modelNumber not in list(self['modelNumber'].unique()):
            # Add new model, since new modelNumber is introduced
            # NB no need for special undo-work. The creation is put on undo stack automatically.
            ss =  containingObject.className
            if ss == 'StructureEnsemble':
              containingObject.newModel(serial=modelNumber)
            else:
              # assert containingObject.className == 'Model'
              containingObject.structureEnsemble.newModel(serial=modelNumber)
        containingObject._project._appBase._endCommandBlock()

    if containingObject is not None:
      undo = containingObject._project._undo
      if undo is not None:
        # set up undo functions
        if rowExists:
          # Undo modification of existing row
          undo.newItem(self.setValues, self.setValues,
                       undoArgs=(accessor,), undoKwargs=dict((x, self.loc[index].get(x))
                                                             for x in kwargs),
                       redoArgs=(accessor,), redoKwargs=kwargs)
        else:
          # undo addition of new row
          undo.newItem(self.drop, self.setValues,
                       undoArgs=(index,), undoKwargs={'inplace':True},
                       redoArgs=(accessor, ), redoKwargs=kwargs)

  ### PDB mapping

  @classmethod
  def from_pdb(cls, filename: str) -> pd.DataFrame:
    """
    Create an EnsembleData from a Pandas DataFrame representing a pdb file
    """
    dfs = pdb2df(filename)
    # pdbName = '.'.join(filename.split('.')[:-1])
    # ensemble = cls(name=pdbName)
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
    ensemble = ensemble.reset_index(drop=True)
    return ensemble


  ### Pandas compatability methods

  @property
  def _constructor(self) -> 'EnsembleData':
    return self.__class__


  def __setattr__(self, name:str, value:typing.Any) -> None:
    if name in self._reservedColumns:
      self[name] = value
    else:
      super().__setattr__(name, value)


  ### Property type checking

  def __setitem__(self, key:str, value:typing.Any) -> None:
    """Values are type checked in calculation. For reserved columns accepted values are:

      - A sequence, Pandas.Series or 1D Pandas.DataFrame of the same length as the data

      - An atomic value (int, float, str, ...) including None

      - For reserved columns the value(s) must be castable to the right type"""

    if hasattr(value, 'astype'):
      # This is a pandas object.
      # If it is not a series or a one-column dataframe, we will get an error later
      series = value
    else:
      # Convert single values and non-Series sequences to pd.Series
      # Single values become length-one series (which are broadcast to longer data)
      # None becomes a length-one series containing NaN, which works with the type casting below.
      series = pd.Series(value)

    # Check for valid length, and set the value to echo later
    if series.shape[0] == 1:
      echoValue = series[0]
    elif series.shape[0] == self.shape[0] or self.columns.shape[0] == 0:
      if len(series) <= self.MAX_PRINT_SERIES_LENGTH:
        echoValue =  value
      else:
        # NB FIXME with the right syntax this list should not be needed
        ll = list(series)
        echoValue = ("pd.Series([%s, %s, %s, ..., %s], dtype: %s, length: %s)"
                      % (ll[0], ll[1], ll[2], ll[-1], series.dtypes,
                         series.shape[0]))
    else:
      # Only value length either 1 or identical to data length is compatible with DataFrame
      raise ValueError("%s value of length %s incompatible with data shape %s"
                       % (key, series.shape[0], self.shape))

    setterType = self._reservedColumns.get(key)
    if setterType is None:
      # Not a reserved column name - pass to superclass. No echoing or undo.
      super().__setitem__(key, value)

    else:
      # Reserved column name

      containingObject = self._containingObject
      if containingObject is not None:
        # echoing
        # NB using '__setitem__' does not look nice, but it is what we do.
        # We can make a nice-looking synonym later, if we want
        if key in self.columns:
          oldValue = list(self[key])
        else:
          oldValue = None
        containingObject._startFunctionCommandBlock('data.__setitem__', key, echoValue)

      # Dispatch to appropriate setter
      try:
        if setterType is str:
          self.__strSetter(series, key)
        elif setterType is int:
          self.__intSetter(series, key)
        elif setterType is float:
          self.__floatSetter(series, key)
        else:
          # setterType is a method name
          getattr(self, setterType)(series)
      finally:
        if containingObject is not None:
          containingObject._project._appBase._endCommandBlock()

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
            undo.newItem(self.__setitem__, self.__setitem__,
                         undoArgs=(key, oldValue), redoArgs=(key, value,))


  def __intSetter(self, value:pd.Series, columnName:str) -> None:
    try:
      super().__setitem__(columnName, value.astype(int))
    except ValueError:
      raise ValueError('%s values must be castable to integer.' % columnName)

  def __strSetter(self, value:pd.Series, columnName:str) -> None:
    super().__setitem__(columnName, value.astype(str))

  def __floatSetter(self, value:pd.Series, columnName:str) -> None:
    try:
      print ('@~@~', value, type(value))
      print ('@~@~', value.astype(float))
      super().__setitem__(columnName, value.astype(float))
    except ValueError:
      raise ValueError('%s values must be castable to float.' % columnName)

  def _modelNumberSetter(self, value:pd.Series) -> None:
    columnName = 'modelNumber'
    try:
      super().__setitem__(columnName, value.astype(int))
    except ValueError:
      raise ValueError('%s values must be castable to integer.' % columnName)

    # Reset models to match model numbers in data
    containingObject = self._containingObject
    if containingObject is not None:
      if hasattr(containingObject, 'resetModels'):
        # This is a StructureEnsemble
        containingObject.resetModels()
      else:
        # assert(containingObject.className == 'Model')
        containingObject.structureEnsemble.resetModels()

  def _occupancySetter(self, value:pd.Series) -> None:
    try:
      if value is not None:
        value = value.astype(float)
        for v in value:
          if not (0 <= v <= 1) and not math.isnan(v):
            # NB this allows NaN t go through. If we want to make occupancy mandatory
            # we can remove the second part of the 'if' statement.
            raise(ValueError)
      super().__setitem__('occupancy', value)
    except ValueError:
      raise ValueError('occupancy values must be castable to float between 0 and 1 (inclusive).')

  # def __modelNumberSetter(self, value:pd.Series) -> None:
  #   try:
  #     super().__setitem__('modelNumber', value.astype(int))
  #   except ValueError:
  #     raise ValueError('modelNumber values must be castable to integer.')
  #
  # def __chainCodeSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('chainCode', value.astype(str))
  #
  # def __elementSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('element', value.astype(str))
  #
  # def __bFactorSetter(self, value:pd.Series) -> None:
  #   try:
  #     super().__setitem__('bFactor', value.astype(float))
  #   except ValueError:
  #     raise ValueError('bFactor values must be castable to float.')
  #
  # def __xCoordSetter(self, value:pd.Series) -> None:
  #   try:
  #     super().__setitem__('x', value.astype(float))
  #   except ValueError:
  #     raise ValueError('x values must be castable to float.')
  #
  # def __yCoordSetter(self, value:pd.Series) -> None:
  #   try:
  #     super().__setitem__('y', value.astype(float))
  #   except ValueError:
  #     raise ValueError('y values must be castable to float.')
  #
  # def __zCoordSetter(self, value:pd.Series) -> None:
  #   try:
  #     super().__setitem__('z', value.astype(float))
  #   except ValueError:
  #     raise ValueError('z values must be castable to float.')
  #
  # def __nmrAtomNameSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('nmrAtomName', value.astype(str))
  #
  # def __nmrResidueNameSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('nmrResidueName', value.astype(str))
  #
  # def __nmrSequenceCodeSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('nmrSequenceCode', value.astype(str))
  #
  # def __nmrChainCodeSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('nmrChainCode', value.astype(str))
  #
  # def __atomNameSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('atomName', value.astype(str))
  #
  # def __altLocationCodeSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('altLocationCode', value.astype(str))
  #
  # def __residueNameSetter(self, value:pd.Series) -> None:
  #   super().__setitem__('residueName', value.astype(str))
  #
  # def __insertionCodeSetter(self, value) -> None:
  #   super().__setitem__('insertionCode', value.astype(str))
  #
  # def __sequenceIdSetter(self, value:pd.Series) -> None:
  #   try:
  #     super().__setitem__('sequenceId', value.astype(int))
  #   except ValueError:
  #     raise ValueError('sequenceId values must be castable to integer.')


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

    # return '<{klass}:{name} (M:{models},C:{chains},R:{residues},A:{atoms})>'.format(
    #   klass=self.__class__.__name__, name=self.name, **d
    # )

    return '<EnsembleData (M:{models},C:{chains},R:{residues},A:{atoms})>'.format(**d)


def pdb2df(filename:str) -> pd.DataFrame:
  """
  Create a Pandas dataframe from a pdb file.
  """
  from io import StringIO
  colspecs = [(0, 6), (6, 11), (12, 16), (16, 17), (17, 20), (21, 22), (22, 26), (26, 27),
              (30, 38), (38, 46), (46, 54), (54, 60), (60, 66), (76, 78), (78, 80)]
  colnames = ['ATOM', 'serial', 'name', 'altLoc', 'resName', 'chainID', 'resSeq', 'iCode',
              'x', 'y', 'z', 'occupancy', 'tempFactor', 'element', 'charge']
  with open(filename) as f:
    dfs = None
    i = None
    pdb = []
    for l in f:
      if l.startswith('ATOM'):
        pdb.append(l)
      elif l.startswith('MODEL'):
        if i is not None:
          df = pd.read_fwf(StringIO(''.join(pdb)), header=None, colspecs=colspecs, names=colnames)
          df['model'] = i
          df = df[df['ATOM'] == 'ATOM']
          if dfs is None:
            dfs = df
          else:
            dfs = dfs.append(df)
        i = l.split()[1]
        pdb = []
  return dfs