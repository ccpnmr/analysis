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
__dateModified__ = "$dateModified: 2024-01-19 18:30:10 +0000 (Fri, January 19, 2024) $"
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


CODE1LETTER =  'code1Letter'
CODE3LETTER = 'code3Letter'
CCPCODE = 'ccpCode'
MOLTYPE = 'molType'

class SequenceHandler():
    """ A  tool designed for converting compound codes between 1-letter, 3-letter and ccpCode representations.
    It also includes parser and validator for ensuring the sequence contains valid entries prior creation of the Chain Core object.
    The underlining objects that make these routine possible are ChemComps definitions.
    Note, not every Chemical Compound has a 1Letter or 3Letter code representation, so conversions are not always possible.
    DNA and RNA have 2 and 1 characters for the 3-Letter Code

    """
    def __init__(self, project, moleculeType:str):
        self.project = project
        self.moleculeType = moleculeType
        self._chemCompsData = self.project._chemCompsData.copy()

    @property
    def data(self):
        return  self._getDataForMolType(self.moleculeType)

    def oneToThreeCode(self, sequence1Letter) -> list:
        df = self.data
        sequence = sequence1Letter
        if isinstance(sequence, str):
            sequence = self._strToList(sequence)
        result = df[df[CODE1LETTER].isin(sequence)][CODE3LETTER].tolist()
        return result

    def oneToCcpCode(self, sequence1Letter) -> list:
        return []

    def ccpCodeToOneCode(self, sequence3Letters) -> list:
        return []

    def threeToCcpCode(self, sequence3Letters) -> list:
        return []

    def ccpCodeToThreeCode(self, sequence3Letters) -> list:
        return []

    def threeToOneCode(self, sequence3Letters) -> list:
        return []

    def sequenceToCcpCode(self, sequence) -> list:
        return []

    def isValidSequence(self, sequence):
        return self._isValidSequence(sequence)

    def _parseSequence(self, sequence):
        """
        Convert a sequence to a list of CcpCodes for internal handling

        Parse the old style of sequence used when creating a Chain prior V3.2.
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
        NOT ALLOWED / not supported will Raise Value Error:
        - 3-Code or CcpCode as a single string un-separated
            sequence =  'ALAALAALAALA'

        - List with items containing spaces or commas
            sequence = ['A, A, A, A, A, A', 'A']

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
            sequence = self._strToList(sequence)

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
        is1Code = all([len(i)==1 for i in sequence])
        if is1Code:
            # All conversions should be safe.
            result[CODE1LETTER] = sequence
            result[CODE3LETTER] = self.oneToThreeCode(sequence)
            result[CCPCODE] = self.oneToCcpCode(sequence)
            return result

        ##  deal with 3CodeLetter
        is3Code = all([i.isupper for i in sequence])
        if is3Code:
            # Conversions should be safe.
            result[CODE1LETTER] = self.threeToOneCode(sequence)
            result[CODE3LETTER] = sequence
            result[CCPCODE] = self.threeToCcpCode(sequence)
            return result

        ##  deal with a CcpCode format.
        if self._isCcpCodeSequence(sequence):
            result[CCPCODE] = sequence
            try:
                code1Letter = self.threeToOneCode(sequence)
                result[CODE1LETTER] = code1Letter
            except Exception as _error:
                error = f'Could not convert to 1CodeLetter. Failed with error: {_error} '
                result['error'] = error
                getLogger().warn(error)
            return result

        return result


    def _isCcpCodeSequence(self, sequence:list):
        """
       it is a CcpCode if at least any of the sequence item meets the CcpCode pattern.
        CcpCodes are case-sensitive and user-defined, project specific. E.G.: CcpCode 'AsP' might not be 'ASP' as 3CodeLetter
        DO NOT simply convert to upper and check if matches any of  the standard 3LetterCodes of any know Protein/DNA/RNA/SmallMolecules
        :param sequence: a list of strings
        :return: bool
        """
        allCodes = []
        for item in sequence:
            allCodes.append(self._isCcpCodeLike(item))
        return any(allCodes)

    @staticmethod
    def _isCcpCodeLike(ccpCode):
        """Check if a string matches a CcpCode pattern.
            Note CcpCodes can be user defined, and be of any format.
            As in V3.2, CcpCodes for standard and known non-standard residues, are simply a Title case of the Code3 letters.
            E.g.: ccpCode Ala is ALA in code3Letter.
            Standard RNA , CcpCode and Code3 and Code1 letter are identical.
        """

        patterns = {
            'All Lowercase'                                           : re.compile(r'^[a-z]*$'),
            'All Lowercase with Numbers'                    : re.compile(r'^[a-z0-9]*$'),
            'All Uppercase with Numbers'                    : re.compile(r'^[A-Z0-9]*$'),
            'Mixed Lower and Upper'                           : re.compile(r'^[a-zA-Z]*$'),
            'Mixed Lower and Upper with Numbers'    : re.compile(r'^[a-zA-Z0-9]*$'),
            'All of the Above Plus Extra Characters'     : re.compile(r'^[a-zA-Z0-9!@#$%^&*()]*$'),
            }

        if not ccpCode or len(ccpCode) == 0:
            return False
        for condition, pattern in patterns.items():
            if bool(pattern.match(ccpCode)):
                return True
        return False

    def _strToList(self, sequence):
        tokens = re.split(r'[,\s]+', sequence)  # just splitting by space and/or comma
        sequence = [token.strip() for token in tokens if token.strip()]  # remove any unwanted spaces/commas
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
