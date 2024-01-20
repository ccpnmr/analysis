#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2024-01-20 13:42:29 +0000 (Sat, January 20, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from typing import Tuple, Optional, Union, Sequence, Iterable
import re
from ccpn.util.Logging import getLogger
import textwrap

# definitions as they appear in the dataframe and in the underlining objects
CODE1LETTER =  'code1Letter'
CODE3LETTER = 'code3Letter'
CCPCODE = 'ccpCode'
MOLTYPE = 'molType'
ISSTANDARD = 'isStandard'
OBJ = 'obj'

class SequenceHandler():
    """ A  tool designed for converting compound codes between 1-letter, 3-letter and ccpCode representations.
    It also includes parser and validator for ensuring the sequence contains valid entries prior creation of the Chain Core object.
    The underlining objects that make these routine possible are ChemComps definitions.
    Note, not every Chemical Compound has a 1Letter or 3Letter code representation, so conversions are not always possible.
    DNA and RNA have 2 and 1 characters for the 3-Letter Code

    """

    def __init__(self, project, moleculeType:str):
        self.project = project
        self._chemCompsData = self.project._chemCompsData.copy() # needs to be a copy to ensure we don't modify the original dataframe
        availableMolTypes = self._chemCompsData[MOLTYPE].values
        self.moleculeType = moleculeType

        if moleculeType not in availableMolTypes:
            raise ValueError(f'Molecule Type {moleculeType} is not recognised. Use one of:  {availableMolTypes}')

    @property
    def data(self):
        return  self._getDataForMolType(self.moleculeType)

    def getAvailableCode3Letter(self):
        """
        :return: A list of all available Code3Letter from the loaded ChemComps in the project for the defined MoleculeType
        """
        return list(self.data[CODE3LETTER].values)

    def getAvailableCode1Letter(self):
        """
        :return: A list of all available Code1Letter from the loaded ChemComps in the project for the defined MoleculeType
        """
        return list(self.data[CODE1LETTER].values)

    def getAvailableCcpCodes(self):
        """
        :return: A list of all available CcpCode from the loaded ChemComps in the project for the defined MoleculeType
        """
        return list(self.data[CCPCODE].values)

    def _covertCodes(self, df, inputList, columnOrigin,  columnTarget ):
        result = [df.loc[df[columnOrigin] == item, columnTarget].values[0] for item in inputList]
        return result

    def _getInvalidItemIndex(self, inputList, columnType):
        invalidIndex = []
        available = self.data[columnType].values
        for i, item in enumerate(inputList):
            if item not in available:
                invalidIndex.append(i)
        return invalidIndex

    def oneToThreeCode(self, sequence1Letter) -> list:
        """ Convert one To ThreeCode for Standard residuals only/ """
        sequence = sequence1Letter
        if isinstance(sequence, str):
            sequence = self._strSequenceToList(sequence)
        df = self.data[self.data[ISSTANDARD]]
        result = self._covertCodes(df, sequence, CODE1LETTER,  CODE3LETTER )
        return result

    def oneToCcpCode(self, sequence1Letter) -> list:
        """ Convert one To CcpCode for Standard residuals only/ """
        sequence = sequence1Letter
        if isinstance(sequence, str):
            sequence = self._strSequenceToList(sequence)
        df = self.data[self.data[ISSTANDARD]]
        result = self._covertCodes(df, sequence, CODE1LETTER, CCPCODE)
        return result

    def ccpCodeToOneCode(self, sequence3Letters) -> list:
        """ Convert CcpCodes To OneCode for Standard residuals only/ """
        sequence = sequence3Letters
        if isinstance(sequence, str):
            sequence = self._strSequenceToList(sequence)
        df = self.data[self.data[ISSTANDARD]]
        result = self._covertCodes(df, sequence, CCPCODE, CODE1LETTER)
        return result

    def threeToCcpCode(self, sequence3Letters) -> list:
        """ Convert  Three to CcpCode """
        sequence = sequence3Letters
        if isinstance(sequence, str):
            sequence = self._strSequenceToList(sequence)
        # df = self.data[self.data[ISSTANDARD]]
        df = self.data
        result = self._covertCodes(df, sequence, CODE3LETTER, CCPCODE)
        return result

    def ccpCodeToThreeCode(self, sequence3Letters) -> list:
        """ Convert CcpCodes To Three Code for Standard residuals only. """
        sequence = sequence3Letters
        if isinstance(sequence, str):
            sequence = self._strSequenceToList(sequence)
        df = self.data[self.data[ISSTANDARD]]
        result = self._covertCodes(df, sequence, CCPCODE, CODE3LETTER)
        return result

    def threeToOneCode(self, sequence3Letters) -> list:
        """ Convert ThreeCodes To OneCode for Standard residuals only/ """
        sequence = sequence3Letters
        if isinstance(sequence, str):
            sequence = self._strSequenceToList(sequence)
        df = self.data[self.data[ISSTANDARD]]
        result = self._covertCodes(df, sequence, CODE3LETTER, CODE1LETTER)
        return result

    def isValidSequence(self, sequence):
        return self._isValidSequence(sequence)

    def _updateData(self):
        """ Run this if you uploaded new ChemComps and you have an instance opened of this class"""
        self._chemCompsData = self.project._chemCompsData.copy()

    def _parseSequence(self, sequence):
        """
        Parse a generic formatted sequence used when creating a Chain.
        ALLOWED sequence format:
        As a string:
            sequence =  'AAAAAA'                # string of un-separated 1-Code
            sequence =  'A A A A A A'           # string of space-separated 1-Code
            sequence =  'A, A, A, A, A, A'      # string of comma-separated 1-Code

            sequence =  'ALA ALA ALA ALA'     # string of space-separated 3-Code (Standard Protein residues)
            sequence =  'ALA, ALA, ALA, ALA'  # string of comma-separated 3-Code

            sequence =  'Ala Ala Ala Ala'        # string of space-separated CcpCode (any ChemComp)
            sequence =  'Ala, Ala, Ala, Ala'    # string of comma-separated CcpCode

        As a List
            sequence =  ['A', 'A', 'A', 'A', 'A']
            sequence =  ['ALA', 'ALA', 'ALA']
            sequence =  ['Ala', 'Ala', 'Ala']

        ~~~~~~~~~~~
        Ambiguities:
        - 1CodeLetter is not unique for non-Standard. Conversions 1 to 3 and 1 to CcpCode is not allowed if the sequence contains non standards.
            - Solution, allow sequence argument as 1Code only for standard Residues for Single molType.
        - 1Code and 3Code is not always available for non-standards.
            Conversions CcpCode to 1 to 3Code letter is not allowed if the sequence contains non standards.

        - 3-Code or CcpCode as a single string un-separated
            sequence =  'ALAALAALAALA'
            we can handle only for codeThreeLetter if we know the expected length

        NOT ALLOWED / not supported will Raise Value Error:
        - List with items containing spaces or commas
            sequence = [
                                'A, A, A, A, A, A',
                                'A',
                                'ALA'
                                ]

        - Mix and match of the formats or Types:
            sequence = 'ALA', 'A'
            sequence = ['ALA', ], 'A'
            sequence = 'ALA Ala ALA'

        Problems:
        what is this:
            sequence = 'CSS' (or ALA!)
            is a Code3Letter?
            is three times a Code1Letter?
            is a CcpCode for a single non-standard which we need to create an nmrChain?

        what is this:
            sequence = 'ALA'
            is a Code3Letter?
            is three Code1Letter?
            Raise Value error?

        :param sequence: str or list
        :return: dict
        """
        result = {
            'input': sequence,
            CODE3LETTER: [],
            CODE1LETTER: [],
            CCPCODE: [],
            'molType': self.moleculeType,
            'error': None,
            }

        # ~~~~ error checking ~~~~ #

        if isinstance(sequence, str):
            # Convert to a list of string to allow a unified handling
            sequence = self._strSequenceToList(sequence)

        if not isinstance(sequence, list):
            error = 'Sequence must be a List to be parsed at this point.'
            result['error'] = error
            return result

        if len(sequence) == 0:
            error = 'Sequence must be a List to be parsed at this point.'
            result['error'] = error
            getLogger().warn(error)
            return result

        allSameLength = all([len(i) for i in sequence])
        if not allSameLength:
            error = 'Sequence contains items of different length. Ensure sequence is made by either 1Code or 3Code letter elements.'
            result['error'] = error
            getLogger().warn(error)
            return result

        # ~~~~ error checking done ~~~~ #

        ##  deal with 1CodeLetter
        is1Code = self._isCode1LetterSequence(sequence)
        if is1Code:
            # All conversions should be safe.
            result[CODE1LETTER] = sequence
            result[CODE3LETTER] = self.oneToThreeCode(sequence)
            result[CCPCODE] = self.oneToCcpCode(sequence)
            return result

        ##  deal with 3CodeLetter
        is3Code = self._isCode3LetterSequence(sequence)
        if is3Code:
            # Conversions should be safe.
            result[CODE1LETTER] = self.threeToOneCode(sequence)
            result[CODE3LETTER] = sequence
            result[CCPCODE] = self.threeToCcpCode(sequence)
            return result

        ##  deal with a CcpCode format.
        if self._isCcpCodeSequence(sequence):
            code1Letter = self.ccpCodeToOneCode(sequence)
            code3Letter = self.ccpCodeToThreeCode(sequence)
            result[CODE1LETTER] = code1Letter
            result[CODE3LETTER] = code3Letter
            result[CCPCODE] = sequence
            return result
        return result

    def _isCode1LetterSequence(self, sequence: list):
        """
       it is a Code1Letter  sequence  if all the codes are present in the list of available Code1Letter
        :param sequence: a list of strings
        :return: bool
        """
        code1LetterCount = 0
        availableCodes = self.getAvailableCode1Letter()
        for item in sequence:
            if item in availableCodes:
                code1LetterCount += 1
        return code1LetterCount == len(sequence)

    def _isCode3LetterSequence(self, sequence: list):
        """
       it is a Code3Letter  sequence  if all the codes are present in the list of available Code3Letter
        :param sequence: a list of strings
        :return: bool
        """
        code3LetterCount = 0
        availableCodes = self.getAvailableCode3Letter()
        for item in sequence:
            if item in availableCodes:
                code3LetterCount += 1
        return code3LetterCount == len(sequence)

    def _isCcpCodeSequence(self, sequence:list):
        """
       it is a CcpCode sequence  if at least one code is present in the list of available CcpCodes
        :param sequence: a list of strings
        :return: bool
        """
        availableCcpCodes = self.getAvailableCcpCodes()
        for item in sequence:
            if item in availableCcpCodes:
                return True
        return False

    def _strContainsSpacesCommas(self, string):
        """
        Regex pattern to match spaces or commas
        :param string:
        :return:
        """
        pattern = re.compile(r'[ ,]')
        return pattern.search(string)

    def _strSequenceToList(self, sequence, splitByLength=1):
        """
        Convert a string to a list.
        If contains a separator, then we split by the separator, e.g.: commas or spaces,
        if is a single long string, we split by the requested length. Default is 1.
        :param sequence:
        :param splitByLength:
        :return:
        """
        if self._strContainsSpacesCommas(sequence):
            tokens = re.split(r'[,\s]+', sequence)  # just splitting by space and/or comma
            sequence = [token.strip() for token in tokens if token.strip()]  # remove any unwanted spaces/commas
        else:
            sequence = textwrap.wrap(sequence, width=splitByLength)
        return sequence

    def _getDataForMolType(self, molType):
        data = self._chemCompsData
        data = data[data['molType'] == molType]
        return data

    def _getAvailableCodes(self):
        """ Get all available Codes needed for validating a sequence"""
        codes = self.data[[CCPCODE, CODE3LETTER, CODE1LETTER]].values.flatten()
        codes = list(set([i for i in codes if i is not None]))
        return codes

    def _isValidSequence(self, sequence):
        """Check if the single element in a sequence are known.
        :return bool, list of indexes for the invalid elements"""
        availableCodes = self._getAvailableCodes()
        invalidPositions = []
        for i, element in enumerate(sequence):
            isValid = element in availableCodes
            if not isValid:
                invalidPositions.append(i)
        isValidSequence = len(invalidPositions)>0
        return isValidSequence, invalidPositions
