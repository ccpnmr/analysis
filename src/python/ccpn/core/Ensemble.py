from typing import Tuple
from typing import Union
from typing import Iterable
from typing import Any
from typing import Optional

import pandas as pd

from ccpn.util.ListFromString import listFromString
from ccpn.util.ListFromString import ListOrString



class Ensemble(pd.DataFrame):
  '''
  A structure Ensemble

  The structure ensemble is based on a Pandas Dataframe.  All of the functionality of Dataframes is available,
  but we have added a number of convenience methods for working with the data.

  In general, there are three things you may want to do with an ensemble:
  1.	 Select a sub-set of atoms within the ensemble
  2.	 Access the data within the ensemble
  3.	 Write data to the ensemble
  We will cover each of these in turn below.

  1.	Selecting sub-sets of atoms within the ensemble:
    Subsets of atoms can be extracted by creating a selector, which is nothing more than a Pandas Series object.
    These can be thought of as a table with the same number of rows as the ensemble you want to select from,
    and containing a single column of True/False values, where True represents a value to be included in the selection.
    We provide a .selector() function that will return a selector based on criteria you provide.  Please note that
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

    In addition to these criteria, functions taking a record and returning True or False can be supplied
    via the func keyword argument.
    For example:
      ensemble.selector(func=lambda r: (r[‘tempFactor’]< 70) and (r[‘tempFactor’]>60))
    which will select everything with a tempFactor between 60 and 70 exclusive.
        The selector can be converted to a filter by setting the inverse keyword to True, so that any record
    that matches the criteria are excluded from the selection.

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

    Because certain selections are quite common, we provide several pre-packaged selections, these include:
      ensemble.backboneSelector
      ensemble.amideProtonSelector
      ensemble.amideNitrogenSelector
      ensemble.methylSelector


    Once you have a selector, you can use it to extract a copy of the rows you want from the ensemble
    via ensemble.extract(). extract() accepts a selector and a list of columns to extract.  If no selector
    is provided, extract() will use any criteria provided to generate a selector on-the-fly for selection (in fact,
    this is the recommended usage pattern.)

    The extract() method has some important caveats:
    1. It is very important to remember that extract() gives a COPY of the data, not the original data.
       If you change the data in the extracted ensemble, the original data will remain unaltered.
    2. If you use a selector created from one ensemble on a different ensemble, it will fail if they don’t
       have exactly the same number of records.  If they do have the same number of records, you will get
      the corresponding record numbers, which is probably not what you want.
    3. In order to avoid the problem in 2., the recommended usage pattern is to let extract() create the selector
       on-the-fly.
    4. If you must create complex selectors, please make sure that you create the selector from the exact ensemble
       you wish to extract from.

  2.	There are several ways to access the data within the ensemble (or an extracted subset thereof.)
    If your ensemble has multiple records, copies of the columns can be accessed by name.
    For example:
      occupancies = ensemble['occupancy']  # Gives a Pandas Series
      occupancies = ensemble['occupancy'].tolist()  # Gives a Python List
    Alternatively, you can convert the records into a tuple of namedTuples using the as_namedTuples() method.

    If you have a single record, the values can be accessed by column name.
    For example:
      atomName = singleRecordEnsemble[‘atomName’]
      atomName, sequenceId = singleRecordEnsemble[[‘atomName’, ‘sequenceId’]]
    but beware: selecting multiple columns when you don’t have a single record ensemble can lead to very
    confusing error messages.

    Instead, it’s often better to step over copies of all the records in a subset using the iterrecords() iterator:
      for record in ensemble.iterrecords():
        print(record[[‘x’, ‘y’, ‘z’]])

    or the itertuples() iterator:
      for record in ensemble.itertuples():
        print(record.x, record.y, record.z)

    Finally, all of the standard Pandas methods for accessing the data are still available.  We leave it to the
    interested coder to investigate that.

    3. Writing data to the ensemble is by far the most tricky operation.  There are two primary issues to be dealt
       with:  putting data in the right place within the ensemble, and making sure you’re writing to the ensemble
       and not a copy of the ensemble.

    The easiest case is probably the least common for users: creating an ensemble from scratch.  In this case, the
    best way to create the ensemble is to assign several equal-length lists or tuples to columns within the ensemble:
      ensemble = Ensemble()
      ensemble[‘modelNumber’] = [1,1,1,2,2,2]
      ensemble[‘chainCode’] = [‘A’, ‘A’, ‘A’, ‘A’, ‘A’, ‘A’]
      # Etc,…
      ensemble = ensemble.reset_index(drop=True)  # Cleanup the indexing

    More commonly, users may want to alter values in a pre-existing ensemble.  The method setValues() can be used
    for this.  The first parameter to setValues() tells setValues() which record to change, and can be an index, a
    single record selector or a single record ensemble (this last option is easily achieved with the iterrecords()
    method.)  Any subsequent parameters passed to setValues() are the column names and values to set.
    For example:
      extracted = ensemble.extract(residueNames='MET', atomNames='CB')
      for record in extracted.iterrecords():
        if record[‘x’] > 999:
          ensemble.setValues(record, x=999, y=999, z=999)

    Just like extract(), exactly matching the source of your selector/selecting ensemble and the ensemble you
    call setValues() on is vital to prevent unpredictable behavior.  You have been warned!

    There are currently no insert functions.  You can, if you wish, append a row to the ensemble using setValues
    and passing an index value not currently in the ensemble:
      maxEnsembleIndexValue = ensemble.index.max()
      ensemble.setValues(maxEnsembleIndexValue+1, x=0, y=1, z=2)
  '''

  _metadata = ['name']
  _reservedColumns = ['atomSerial', 'modelNumber', 'chainCode', 'sequenceId', 'insertionCode',
                      'residueName', 'atomName', 'nmrChainCode', 'nmrSequenceCode',
                      'nmrResidueName',
                      'nmrAtomName', 'x', 'y', 'z', 'occupancy', 'bFactor', 'element', 'atomId']


  def __init__(self, *args, name:Optional[str]=None, **kwargs) -> None:
    self.name = name
    super().__init__(*args, **kwargs)
    self.__columnSetters = {'modelNumber': self.__modelNumberSetter,
                            'chainCode': self.__chainCodeSetter,
                            'element': self.__elementSetter,
                            'bFactor': self.__bFactorSetter,
                            'occupancy': self.__occupancySetter,
                            'x': self.__xCoordSetter,
                            'y': self.__yCoordSetter,
                            'z': self.__zCoordSetter,
                            'nmrAtomName': self.__nmrAtomNameSetter,
                            'nmrResidueName': self.__nmrResidueNameSetter,
                            'nmrSequenceCode': self.__nmrSequenceCodeSetter,
                            'nmrChainCode': self.__nmrChainCodeSetter,
                            'atomName': self.__atomNameSetter,
                            'atomSerial': self.__atomSerialSetter,
                            'residueName': self.__residueNameSetter,
                            'insertionCode': self.__insertionCodeSetter,
                            'sequenceId': self.__sequenceIdSetter,
                           }


  ### Making selections

  def selector(self, chainCodes=None, residueNames=None, sequenceIds=None, atomNames=None,
               modelNumbers=None, ids=None,
               elements=None, func=None, inverse=False) -> pd.Series:
    '''
    Make a boolean selector restricted to rows matching the parameters specified

    Returns Pandas Series
    '''
    s = pd.Series((True,) * self.shape[0])
    if chainCodes is not None:
      s = s & self._chainsSelector(chainCodes)
    if residueNames is not None:
      s = s & self._residuesSelector(residueNames)
    if sequenceIds is not None:
      s = s & self._sequenceIdsSelector(sequenceIds)
    if atomNames is not None:
      s = s & self._atomsSelector(atomNames)
    if modelNumbers is not None:
      s = s & self._modelsSelector(modelNumbers)
    if ids is not None:
      s = s & self._idsSelector(ids)
    if func is not None:
      s = s & self._funcSelector(func)
    if elements is not None:
      s = s & self._elementsSelector(elements)
    if inverse:
      return ~s
    return s


  def _chainsSelector(self, chains:ListOrString) -> pd.Series:
    if isinstance(chains, str):
      chains = listFromString(chains)
    return self['chainCode'].isin(chains)


  def _residuesSelector(self, residues:ListOrString) -> pd.Series:
    if isinstance(residues, str):
      residues = listFromString(residues)
    return self['residueName'].isin(residues)


  def _sequenceIdsSelector(self, sequenceIds:ListOrString) -> pd.Series:
    if isinstance(sequenceIds, int):
      sequenceIds = [sequenceIds, ]
    if isinstance(sequenceIds, str):
      sequenceIds = listFromString(sequenceIds)
    sequenceIds = [int(r) for r in sequenceIds]
    return self['sequenceId'].isin(sequenceIds)


  def _atomsSelector(self, atomNames:ListOrString) -> pd.Series:
    if isinstance(atomNames, str):
      atomNames = listFromString(atomNames)
    return self['atomName'].isin(atomNames)


  def _modelsSelector(self, modelNumbers:ListOrString) -> pd.Series:
    if isinstance(modelNumbers, str):
      modelNumbers = listFromString(modelNumbers)
    if isinstance(modelNumbers, int):
      modelNumbers = [modelNumbers, ]
    return self['modelNumber'].isin(modelNumbers)


  def _idsSelector(self, ids:ListOrString) -> pd.Series:
    if isinstance(ids, str):
      ids = listFromString(ids)
    s = pd.Series((False,) * self.shape[0])
    for i in ids:
      chain, seqId, name, atom = i.split('.')
      s = s | self.selector(chainCodes=[chain, ], sequenceIds=[int(seqId), ], residueNames=[name, ],
                            atomNames=[atom, ])
    return s


  def _elementsSelector(self, elements:ListOrString) -> pd.Series:
    if isinstance(elements, str):
      elements = listFromString(elements)
    s = pd.Series((False,) * self.shape[0])
    for e in elements:
      s = s | self['atomName'].str.startswith(e)
    return s


  def _funcSelector(self, func:callable) -> pd.Series:
    return self.apply(func, axis=1)


  ### Protein specific automatically generated selectors

  @property
  def backboneSelector(self) -> pd.Series:
    '''
    Return a selector that selects backbone atoms.

    The selector is specific for:
      Ca, C', O, Nh, Hn
    '''
    return self.selector(atomNames=['CA', 'C', 'N', 'O', 'H'])


  @property
  def amideProtonSelector(self) -> pd.Series:
    '''
    Return a selector that selects only the amide proton.
    '''
    return self.selector(atomNames=['H'])


  @property
  def amideNitrogenSelector(self) -> pd.Series:
    '''
    Return a selector that selects only the amide nitrogen.
    '''
    return self.selector(atomNames=['N'])


  @property
  def methylSelector(self) -> pd.Series:
    '''
    Return a selector that selects atoms in methyl groups.

    The selector is specific for:
      Ala: Cb and attached protons
      Leu: Both Cd's and attached protons
      Met: Ce and attached protons
      Thr: Cg and attached protons
      Val: Both Cg's and attached protons
    '''
    s = self.selector(residueNames=['ALA'], atomNames=['CB', 'HB1', ' HB2', 'HB3'])
    s = s | self.selector(residueNames=['LEU'],
                          atomNames=['CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23'])
    s = s | self.selector(residueNames=['MET'], atomNames=['CE', 'HE1', 'HE2', 'HE3'])
    s = s | self.selector(residueNames=['THR'], atomNames=['CG', 'HG1', 'HG2', 'HG3'])
    s = s | self.selector(residueNames=['VAL'],
                          atomNames=['CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23'])
    return s


  ### extracting selections

  def extract(self, selector:Union[int, pd.Series]=None,
              columns:ListOrString=None, **kwargs) -> 'Ensemble':
    '''
    Extracts a copy of a subset of atoms from the Ensemble

    Params:
      selector : Boolean Pandas series the same length as the number of rows in the ensemble
                  If no selector is given,  pass the keyword args on to the selector function
                  and use the resulting selector to extract a sub-ensemble.

    Returns a new Ensemble
    '''
    if columns is None:
      columns = self.columns
    else:
      if isinstance(columns, str):
        columns = listFromString(columns)
    try:
      if self.shape[0] == selector.shape[0]:
        return self.ix[selector, columns]
      else:
        raise ValueError('Selectors must be the same length as atom count * model count.')
    except AttributeError:
      s = self.selector(**kwargs)
      return self.extract(s, columns)


  ### Record-wise access

  def iterrecords(self) -> 'Ensemble':
    '''
    An iterator over the rows (atoms) in the ensemble
    '''
    for idx, record in self.iterrows():
      yield Ensemble(record.to_frame().T)

  def records(self) -> Tuple['Ensemble']:
    return tuple(self.iterrecords())

  def as_namedTuples(self)-> Tuple['namedTuple']:
    '''
    An tuple of named tuples over the records (atoms) in the ensemble
    '''
    return tuple(self.itertuples())


  ### Record-wise assignment of values

  def setValues(self, accessor:Union[int, 'Ensemble', pd.Series], **kwargs) -> None:
    '''
    Allows you to easily set values (in place) for fields in the Ensemble

    Params:
      accessor : int, Ensemble, Selector
                 If an integer is given, the value will be set on the row at that index
                 If an single row Ensemble is given, the value will be set on the row that matches.
                 If a selector that matches a single row is given, the value will be set on that matching row

                 Multi-row Ensembles or selectors are not allowed. (consider using Ensemble.iterrecords() to iterate)
      kwargs : columns on which to set the values

    '''
    columns = []
    values = []
    for k, v in kwargs.items():
      columns.append(k)
      values.append(v)
    if len(columns) == 1:
      columns, values = columns[0], values[0]

    if type(accessor) is int:  # passed an index
      self.loc[accessor, columns] = values
    elif type(accessor) is Ensemble:
      assert accessor.shape[0] == 1, "Only single row ensembles can be used for setting."
      self.loc[accessor.index, columns] = values
    elif type(accessor) is pd.Series:  # selector
      assert accessor.sum() == 1, "Boolean selectors must select a single row"
      self.loc[accessor[accessor == True].index, columns] = values
    else:
      raise TypeError('accessor must be index, ensemble row, or selector.')


  ### PDB mapping

  @classmethod
  def from_pdb(cls, filename: str) -> pd.DataFrame:
    '''
    Create an Ensemble from a Pandas dataframe representing a pdb file
    '''
    dfs = pdb2df(filename)
    pdbName = '.'.join(filename.split('.')[:-1])
    ensemble = cls(name=pdbName)
    ensemble['modelNumber'] = dfs['model']
    ensemble['chainCode'] = dfs['chainID']
    ensemble['residueName'] = dfs['resName']
    ensemble['sequenceId'] = dfs['resSeq']
    ensemble['insertionCode'] = dfs['iCode']
    ensemble['atomName'] = dfs['name']
    ensemble[['x', 'y', 'z']] = dfs[['x', 'y', 'z']]
    ensemble['occupancy'] = dfs['occupancy']
    ensemble['bFactor'] = dfs['tempFactor']
    ensemble['element'] = dfs['element']
    ensemble['atomSerial'] = dfs['serial']
    ensemble['nmrAtomName'] = None
    ensemble['nmrResidueName'] = None
    ensemble['nmrSequenceCode'] = None
    ensemble['nmrChainCode'] = None
    ensemble = ensemble.reset_index(drop=True)
    return ensemble


  ### Pandas compatability methods

  @property
  def _constructor(self) -> 'Ensemble':
    return self.__class__


  def __setattr__(self, name:str, value:Any) -> None:
    if name in self._reservedColumns:
      self[name] = value
    else:
      super().__setattr__(name, value)


  ### Property type checking

  def __setitem__(self, key:str, value:Any) -> None:
    if key in self._reservedColumns:
      if (value is not None) and (not hasattr(value, 'astype')):
        value = pd.Series([value,])
      self.__columnSetters[key](value)
    else:
      super().__setitem__(key, value)


  def __modelNumberSetter(self, value:Union[str, float, int, Iterable]) -> None:
    try:
      if value is not None:
        value = value.astype(int)
      super().__setitem__('modelNumber', value)
    except ValueError:
      raise ValueError('modelNumber must be castable to integer.')


  def __chainCodeSetter(self, value:Union[str, Iterable]) -> None:
    if value is not None:
      value = value.astype(str)
      # for v in value:
      #   if not v.isupper():
      #     raise ValueError('chainCode must be upper case')
    super().__setitem__('chainCode', value)


  def __elementSetter(self, value:Union[str, Iterable]) -> None:
    if value is not None:
      value = value.astype(str)
      # for v in value:
      #   if len(v) > 3:
      #     raise ValueError('element must have at most three letters')
    super().__setitem__('element', value)


  def __bFactorSetter(self, value:Union[str, float, int, Iterable]) -> None:
    try:
      if value is not None:
        value = value.astype(float)
      super().__setitem__('tempFactor', value)
    except ValueError:
      raise ValueError('tempFactor must be castable to float.')


  def __occupancySetter(self, value:Union[str, float, int, Iterable]) -> None:
    try:
      if value is not None:
        value = value.astype(float)
        for v in value:
          if not (0 <= v <= 1):
            raise(ValueError)
      super().__setitem__('occupancy', value)
    except ValueError:
      raise ValueError('occupancy must be castable to float between 0 and 1 (inclusive).')


  def __xCoordSetter(self, value:Union[str, float, int, Iterable]) -> None:
    try:
      if value is not None:
        value = value.astype(float)
      super().__setitem__('x', value)
    except ValueError:
      raise ValueError('x must be castable to float.')


  def __yCoordSetter(self, value:Union[str, float, int, Iterable]) -> None:
    try:
      if value is not None:
        value = value.astype(float)
      super().__setitem__('y', value)
    except ValueError:
      raise ValueError('y must be castable to float.')


  def __zCoordSetter(self, value:Union[str, float, int, Iterable]) -> None:
    try:
      if value is not None:
        value = value.astype(float)
      super().__setitem__('z', value)
    except ValueError:
      raise ValueError('z must be castable to float.')


  def __nmrAtomNameSetter(self, value:Union[str, Iterable]) -> None:
    if value is not None:
      value = value.astype(str)
      # for v in value:
      #   if not v.isupper():
      #     raise ValueError('nmrAtomName must be upper case')
    super().__setitem__('nmrAtomName', value)


  def __nmrResidueNameSetter(self, value:Union[str, Iterable]) -> None:
    if value is not None:
      value = value.astype(str)
      # for v in value:
      #   if not v.isupper():
      #     raise ValueError('nmrResidueName must be upper case')
    super().__setitem__('nmrResidueName', value)


  def __nmrSequenceCodeSetter(self, value:Union[str, float, int, Iterable]) -> None:
    if value is not None:
      value = value.astype(str)
      # for v in value:
      #   if not v.isupper():
      #     raise ValueError('nmrSequenceCode must be upper case')
    super().__setitem__('nmrSequenceCode', value)


  def __nmrChainCodeSetter(self, value:Union[str, Iterable]) -> None:
    if value is not None:
      value = value.astype(str)
      # for v in value:
      #   if not v.isupper():
      #     raise ValueError('nmrChainCode must be upper case')
    super().__setitem__('nmrChainCode', value)


  def __atomNameSetter(self, value:Union[str, Iterable]) -> None:
    if value is not None:
      value = value.astype(str)
      # for v in value:
      #   if not v.isupper():
      #     raise ValueError('atomName must be upper case')
    super().__setitem__('atomName', value)


  def __residueNameSetter(self, value:Union[str, Iterable]) -> None:
    if value is not None:
      value = value.astype(str)
      # for v in value:
      #   if not v.isupper():
      #     raise ValueError('residueName must be upper case')
    super().__setitem__('residueName', value)


  def __insertionCodeSetter(self, value) -> None:
    if value is not None:
      value = pd.Series(value)
      #  value.fillna('.', inplace=True)
      value = value.astype(str)
    super().__setitem__('insertionCode', value)


  def __sequenceIdSetter(self, value:Union[str, float, int, Iterable]) -> None:
    try:
      if value is not None:
        value = value.astype(int)
      super().__setitem__('sequenceId', value)
    except ValueError:
      raise ValueError('sequenceId must be castable to integer.')


  def __atomSerialSetter(self, value:Union[str, float, int, Iterable]) -> None:
    try:
      if value is not None:
        value = value.astype(int)
      super().__setitem__('atomSerial', value)
    except ValueError:
      raise ValueError('atomSerial must be castable to integer.')


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
      d['models'] = len(self['modelNumber'].unique())
    except KeyError:
      d['models'] = '?'
    try:
      d['atoms'] = self.groupby(['chainCode', 'sequenceId', 'atomName']).count().shape[0]
    except KeyError:
      d['atoms'] = self.shape[0]
    # Just count atoms...?

    return '<{klass}:{name} (M:{models},C:{chains},R:{residues},A:{atoms})>'.format(klass=self.__class__.__name__,
                                                                                    name=self.name,
                                                                                    **d)



class Model:
  """
  A view of a single model within an ensemble.

  Once created, a Model *should* behave exactly like an Ensemble.  If it doesn't, pleast report it as a bug.
  """

  def __init__(self, ensemble, modelNumber) -> None:
    self._modelNumber = modelNumber
    self._ensemble = ensemble


  @property
  def _modelNumberIndices(self) -> Tuple[int, int]:
    modelFilter = self._ensemble[self._ensemble['modelNumber'] == self._modelNumber]
    modelStart = modelFilter.index[0]
    modelEnd = modelFilter.index[-1]
    return (modelStart, modelEnd)


  def __str__(self) -> str:
    s = str(self._ensemble)[9:]
    return '<{}:{}'.format(self.__class__.__name__, s)


  def __getattr__(self, attr:str) -> Any:
    if hasattr(self._ensemble, attr):
      mni = self._modelNumberIndices
      e = self._ensemble[mni[0]:mni[1]]
      e.reset_index(inplace=True, drop=True)
      return ChainedAssignmentWarningSuppressor(getattr(e, attr))

    raise AttributeError("'Model' object has no attribute '{}'".format(attr))


  def __getitem__(self, key:str) -> Any:
    mni = self._modelNumberIndices
    e = self._ensemble[mni[0]:mni[1]]
    e.reset_index(inplace=True, drop=True)
    return e[key]


  def __setitem__(self, key:str, value:Any) -> None:
    mni = self._modelNumberIndices
    e = self._ensemble[mni[0]:mni[1]]
    e.reset_index(inplace=True, drop=True)
    pd.set_option('chained_assignment', None)
    e[key] = value
    pd.set_option('chained_assignment', 'warn')



class ChainedAssignmentWarningSuppressor:
  """
  Suppress Pandas' warnings about chained assignment when using an assignment strategy known to not suffer from chained assignment.
  """
  def __init__(self, f:Any) -> None:
    self.__f = f

  def __call__(self, *args, **kwargs) -> Any:
    pd.set_option('chained_assignment', None)
    o = self.__f(*args, **kwargs)
    pd.set_option('chained_assignment', 'warn')
    return o

  def __getitem__(self, key:str) -> Any:
    return self.__f[key]

  def __setitem__(self, key:str, value:Any):
    pd.set_option('chained_assignment', None)
    self.__f[key] = value
    pd.set_option('chained_assignment', 'warn')

  def __get__(self, obj:Any) -> Any:
    return self.__f

  def __set__(self, obj:Any, value:Any) -> None:
    self.__f = value

  def __repr__(self) -> Any:
    return self.__f.__repr__()

  def __str__(self) -> str:
    return self.__f.__str__()



def pdb2df(filename:str) -> pd.DataFrame:
  '''
  Create a Pandas dataframe from a pdb file.
  '''
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
