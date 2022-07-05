"""Structure Data Matrix

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-07-05 13:20:42 +0100 (Tue, July 05, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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
import numpy
import pandas as pd
# from ccpn.util import Sorting
from ccpn.util.ListFromString import listFromString
# from functools import partial
# from ccpn.core.lib.ContextManagers import undoStackBlocking, undoBlock, notificationBlanking
from ccpn.core._implementation.DataFrameABC import DataFrameABC, fitToDataType

# Pid.IDSEP - but we do not want to import from ccpn.core here
IDSEP = '.'
NaN = math.nan


class EnsembleData(DataFrameABC):
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
          Note that this is case-sensitive, so ‘a’ will likely not select anything

        * residueNames
          allowed values: ‘MET’; ‘MET,ALA’; ‘MET, ALA’; [‘MET’, ’ALA’]
          not allowed: ‘MET-ALA’; [‘MET, ALA’, ‘GLU’] (currently)
          Note that this is case-sensitive, so ‘met’ will likely not select anything

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

      Finally, all the standard Pandas methods for accessing the data are still available.
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

    RECORDNAME = 'Atom'

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
        ('nmrAtomName', (str, None)),
        ))

    #=========================================================================================
    # Making selections
    #=========================================================================================

    def selector(self, index=None, chainCodes=None, residueNames=None, sequenceIds=None,
                 atomNames=None, modelNumbers=None, ids=None,
                 elements=None, func=None, inverse=False) -> pd.Series:
        """
        Make a boolean selector restricted to rows matching the parameters specified.

        Incompatible values of the selection parameters may raise various errors.

        Returns Pandas Series of booleans
        """
        s = pd.Series((True,) * self.shape[0], index=self.index)  #range(1,self.shape[0]+1))
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

    def _sequenceIdsSelector(self, expression: typing.Union[str, int, typing.Iterable]) -> pd.Series:
        """Select column sequenceId based on 'expression'
        """
        if isinstance(expression, str):
            expression = listFromString(expression)
            expression = [int(ii) for ii in expression]  # ejb - check for the other _selectors
        elif isinstance(expression, int):
            expression = [expression, ]
        expression = [int(x) for x in expression]
        return self['sequenceId'].isin(expression)

    def _modelsSelector(self, expression: typing.Union[str, int, typing.Iterable]) -> pd.Series:
        """Select column modelNumber based on 'expression'
        """
        if isinstance(expression, str):
            expression = listFromString(expression)
            expression = [int(ii) for ii in expression]  # ejb - check for the other _selectors
        elif isinstance(expression, int):
            expression = [expression, ]
        return self['modelNumber'].isin(expression)

    def _idsSelector(self, expression: typing.Union[str, typing.Iterable[str]]) -> pd.Series:
        """Select records based on 'expression',
        which must either be or convert to a sequence of string atom IDs
        """
        s = pd.Series((False,) * self.shape[0], index=self.index)
        if isinstance(expression, str):
            expression = listFromString(expression)
        for i in expression:
            chain, seqId, name, atom = i.split(IDSEP)
            s = s | self.selector(chainCodes=[chain, ], sequenceIds=[int(seqId), ], residueNames=[name, ],
                                  atomNames=[atom, ])
        return s

    #=========================================================================================
    # Protein specific automatically generated selectors
    #=========================================================================================

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

    #=========================================================================================
    # PDB mapping
    #=========================================================================================

    @classmethod
    def from_pdb(cls, filename: str) -> pd.DataFrame:
        """
        Create an EnsembleData from a pdb file.
        """
        dfs = pdb2df(filename)

        ensemble = cls()

        ensemble['index'] = [ii for ii in range(1, dfs.shape[0] + 1)]
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
        ensemble['comment'] = None

        return cls(ensemble)

    #=========================================================================================
    # Pandas compatibility methods
    #=========================================================================================

    #=========================================================================================
    # Property type checking
    #=========================================================================================


    def _modelNumberConversion(self, force: bool = False):
        """Convert modelNumber series to valid data, changing value *in place*
        and update containingObject - or raise an error
        """
        key = 'modelNumber'

        ll = fitToDataType(self[key], int, force=force)
        if force:
            ll = [(x if (x and x > 0) else None) for x in ll]
        else:
            if any((x is not None and x < 1) for x in ll):
                raise ValueError("Model numbers must be integers >= 1 or None")
        if None in ll:
            pd.DataFrame.__setitem__(self, key, pd.Series(ll, self.index, dtype=object))
        else:
            pd.DataFrame.__setitem__(self, key, pd.Series(ll, self.index, dtype=int))

        # Reset models to match model numbers in data
        # NBNB resetModels currently removes rows with modelNumber == None. To change??
        containingObject = self._containingObject
        if containingObject is not None:
            if hasattr(containingObject, 'resetModels'):
                containingObject.resetModels()
            else:
                containingObject.structureEnsemble.resetModels()

    def _nmrSequenceCodeConversion(self, force: bool = False):
        """Convert nmrSequenceCode series to valid data, changing value *in place*

        This is needed to convert integers and integer-valued floats
        (which could easily be created during setting) to str(int)
        """
        key = 'nmrSequenceCode'
        Real = numbers.Real
        fmod = math.fmod
        isnan = math.isnan
        ll = []
        appnd = ll.append
        for val in self[key]:
            if val is None or isinstance(val, str):
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
        pd.DataFrame.__setitem__(self, key, pd.Series(ll, self.index, dtype=str))

    def _occupancyConversion(self, force: bool = False):
        """Convert occupancy series to valid data, changing value *in place*"""

        key = 'occupancy'
        NaN = float('NaN')

        ll = fitToDataType(self[key], float, force=force)
        if force:
            ll = [(x if 0 <= x <= 1 else NaN) for x in ll]
        else:
            if any((x < 0 or x > 1) for x in ll):
                raise ValueError("Occupancies must be in the range 0 <= x <= 1")
        pd.DataFrame.__setitem__(self, key, pd.Series(ll, self.index, dtype=float))

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

    __repr__ = __str__


def pdb2df(filename: str) -> pd.DataFrame:
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
            dfs = df
        else:
            dfs = dfs.append(df)
    dfs['idx'] = numpy.arange(dfs.shape[0]) + 1
    dfs.set_index('idx', inplace=True)
    return dfs


def _pdbStringToDf(modelLines: list, modelNumber=1):
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


def averageStructure(ensemble: EnsembleData) -> EnsembleData:
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
