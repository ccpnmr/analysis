"""
Module to manage Star files in ccpn context
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                 )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-03-04 11:09:42 +0000 (Fri, March 04, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2020-02-17 10:28:41 +0000 (Thu, February 17, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Path import aPath, Path
from ccpn.util.Logging import getLogger
from ccpn.util.nef.StarIo import NmrDataBlock, NmrSaveFrame, NmrLoop, parseNmrStarFile
from ccpn.util.nef.GenericStarParser import PARSER_MODE_STANDARD, LoopRow
from ccpn.framework.lib.ccpnNmrStarIo.SaveFrameABC import SaveFrameABC

from sandbox.Geerten.NTdb.NTdbLib import getNefName
from sandbox.Geerten.NTdb.NTdbDefs import getNTdbDefs


class ChemicalShiftSaveFrame(SaveFrameABC):
    """A class to manage chemicalShift saveFrame
    """
    _sf_category = 'assigned_chemical_shifts'

    # this key contains the NmrLoop with the chemical-shift data
    _LOOP_KEY = 'atom_chem_shift'

    # These keys map the row onto the V3 ChemicalShift object
    _SEQUENCE_CODE_TAG = 'seq_id'
    _RESIDUE_TYPE_TAG = 'comp_id'
    _ATOM_NAME_TAG = 'atom_id'
    _AMBIGUITY_CODE = 'ambiguity_code'

    _ISOTOPE_TAG_1 = 'atom_isotope_number'
    _ISOTOPE_TAG_2 = 'atom_type'

    _VALUE_TAG = 'val'
    _VALUE_ERROR_TAG = 'val_err'
    _FIGURE_OF_MERIT_TAG = 'assign_fig_of_merit'

    _COMMENT_TAG = 'details'

    _ntDefs = getNTdbDefs()

    @property
    def chemicalShifts(self) ->list :
        """:return a list of chemical shift LoopRow's
        """
        if (_loop := self.get(self._LOOP_KEY)) is None:
            return []
        return _loop.data

    def _parseChemicalShiftRow(self, csRow:LoopRow):
        """
        Parse the chemical shift row and assign attributes for subsequent processing
        :param csRow: a LoopRow instance
        """
        csRow.value = float(csRow.get(self._VALUE_TAG))
        csRow.valueError = float(csRow.get(self._VALUE_ERROR_TAG))
        figureOfMerit = csRow.get(self._FIGURE_OF_MERIT_TAG)
        csRow.figureOfMerit = float(figureOfMerit) if figureOfMerit is not None else 1.0

        csRow.sequenceCode = str(csRow.get(self._SEQUENCE_CODE_TAG))
        csRow.residueType = str(csRow.get(self._RESIDUE_TYPE_TAG))
        csRow.isotopeCode = '%s%s' % (csRow.get(self._ISOTOPE_TAG_1), csRow.get(self._ISOTOPE_TAG_2))
        csRow.atomName = str(csRow.get(self._ATOM_NAME_TAG))
        csRow.ambiguityCode = int(csRow.get(self._AMBIGUITY_CODE))

        csRow.comment = csRow.get(self._COMMENT_TAG)

        # (try to) get the NTdb definition for this residue, atom
        csRow.ntDef = self._ntDefs.getDef((csRow.residueType, csRow.atomName))

        # convert atomName to NEF;
        csRow.nefAtomName = getNefName(csRow.ntDef)

        csRow.skip = False

    def _isSameResidue(self, row1, row2) -> bool:
        """
        :param row1:
        :param row2:
        :return: True if row1 and row2 relate to the same residue
        """
        return row1.residueType == row2.residueType and \
               row1.sequenceCode == row2.sequenceCode

    def _newChemicalShift(self, rowIndx, chemShiftList) -> int:
        """Use chemShift to make a new (v3) chemicalShift in chemShiftList
        If need be: look back or look ahead into other rows
        :param rowIndx: index of row to process
        :param chemShiftList: ChemicalShifList instance to generate new ChemicalShift
        :return index of next row to process
        """
        # _previousRow = self.chemicalShifts[rowIndx-1] if rowIndx > 0 else None

        _row = self.chemicalShifts[rowIndx]
        nextRowIndx = rowIndx + 1 # Now points to next row

        # _nextRow = self.chemicalShifts[nextRowIndx] if nextRowIndx < len(self.chemicalShifts) else None

        if _row.skip:
            return nextRowIndx

        project = chemShiftList.project
        chainCode = chemShiftList.name
        atomName = _row.atomName

        if _row.ambiguityCode == 1:
            # unfortunately:

            # - methyl protons have identical chemical shifts with ambiguity code 1
            if _row.ntDef.isMethyl and _row.ntDef.isProton:
                atomName = _row.nefAtomName
                # We can skip all other methyl protons
                for _aDef in _row.ntDef.otherAttachedProtons:
                    _aRow = self._lookupDict.get( (_row.residueType, _row.sequenceCode, _aDef.name) )
                    _aRow.skip = True

            # - methylene protons with identical chemical shifts have ambiguity code 1
            elif _row.ntDef.isMethylene and _row.ntDef.isProton:
                _aDef = _row.ntDef.otherAttachedProtons[0]
                _aRow = self._lookupDict.get( (_row.residueType, _row.sequenceCode, _aDef.name) )
                if _row.value == _aRow.value:
                    _aRow.skip = True
                    atomName = _row.atomName.replace('2','%').replace('3','%')

            # - Phe, Tyr aromatic protons/carbons (e.g. HD1/HD2) with identical chemical shifts have ambiguity code 1
            # these occur on non-sequential rows;
            elif _row.ntDef.parent.name in ('PHE', 'TYR') and _row.atomName in 'HD1 CD1 HD2 CD2 HE1 CE1 HE2 CE2'.split():
                if atomName.endswith('1'):
                    _aName = _row.atomName.replace('1','2')
                elif atomName.endswith('2'):
                    _aName = _row.atomName.replace('2','1')
                _aRow = self._lookupDict.get( (_row.residueType, _row.sequenceCode, _aName) )
                if _row.value == _aRow.value:
                    _aRow.skip = True
                    atomName = _row.atomName.replace('1','%').replace('2','%')

        elif _row.ambiguityCode == 2:
            #  (Val, Leu NEF xy rules propagation; i.e. HDx% connected to CDx)
            if _row.ntDef.parent.name in ('VAL', 'LEU') and _row.ntDef.isMethyl and _row.ntDef.isProton:
                atomName = _row.nefAtomName.replace('1','x').replace('2','y')
                # We can skip all other methyl protons
                for _aDef in _row.ntDef.otherAttachedProtons:
                    _aRow = self._lookupDict.get( (_row.residueType, _row.sequenceCode, _aDef.name) )
                    _aRow.skip = True
                # propagate xy to carbon
                _cName = _row.ntDef.attachedHeavyAtom.name
                _cRow = self._lookupDict.get( (_row.residueType, _row.sequenceCode, _cName) )
                _cRow.nefAtomName = _cRow.atomName.replace('1','x').replace('2','y')
                _cRow.ambiguityCode = 2
            else:
                atomName = _row.nefAtomName

        elif _row.ambiguityCode == 3:
            #  (Phe, Tyr NEF xy rules propagation; i.e. HDx connected to CDx)
            if _row.ntDef.parent.name in ('PHE', 'TYR') and _row.atomName in 'HD1 HD2 HE1 HE2'.split():
                atomName = _row.nefAtomName
                # propagate to Carbon
                _cName = _row.ntDef.attachedHeavyAtom.name
                _cRow = self._lookupDict.get( (_row.residueType, _row.sequenceCode, _cName) )
                _cRow.nefAtomName = _cRow.atomName.replace('1','x').replace('2','y')
                _cRow.ambiguityCode = 3
            else:
                atomName = _row.nefAtomName

        else:
            getLogger().warning(f'No provisions for ({_row.residueType},{_row.atomName}) with ambiguity code {_row.ambiguityCode}')

        # get the NmrAtom object
        nmrChain = project.fetchNmrChain(chainCode)
        nmrResidue = nmrChain.fetchNmrResidue(residueType=_row.residueType, sequenceCode=_row.sequenceCode)
        nmrAtom = nmrResidue.newNmrAtom(name=atomName, isotopeCode=_row.isotopeCode)

        # create the ChemicalShift
        chemShiftList.newChemicalShift(nmrAtom=nmrAtom,
                                       value=_row.value, valueError=_row.valueError, figureOfMerit=_row.figureOfMerit,
                                       comment=_row.comment)

        return nextRowIndx

    def importIntoProject(self, project) -> list:
        """Import the data of self into project.
        :param project: a Project instance
        :return list of imported V3 objects
        """
        name = f'entry{self.entry_id}'
        chemShiftList = project.newChemicalShiftList(name = name,
                                                     autoUpdate = False,
                                                     comment = f'from BMRB entry {self.entry_id}; {self.name}'
                                                     )
        # A two-stage conversion, as sometimes we need to look back or forward
        # 'parse'/convert the rows, assigning the attributes; create a lookupDict
        self._lookupDict = {}
        for _row in self.chemicalShifts:
            self._parseChemicalShiftRow(_row)
            self._lookupDict[(_row.residueType, _row.sequenceCode, _row.atomName)] = _row

        # Loop again to create the V3 chemcialShift objects
        rowIndx = 0
        while rowIndx < len(self.chemicalShifts):
            rowIndx = self._newChemicalShift(rowIndx, chemShiftList)

        return [chemShiftList]

ChemicalShiftSaveFrame._registerSaveFrame()

