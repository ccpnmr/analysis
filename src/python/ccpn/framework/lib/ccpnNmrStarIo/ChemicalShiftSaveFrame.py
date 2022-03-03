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
__dateModified__ = "$dateModified: 2022-03-03 16:36:26 +0000 (Thu, March 03, 2022) $"
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

from sandbox.Geerten.NTdb.NTdbLib import ISMETHYL, ISMETHYLENE, ISAROMATIC, getNefMappingDict
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

    _nefMappingDict = getNefMappingDict()
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

        # convert atomName to NEF;
        csRow.nefResidueName, csRow.nefAtomName, csRow.specialType = self._nefMappingDict.get((csRow.residueType, csRow.atomName), (None, None, None))

        csRow.comment = csRow.get(self._COMMENT_TAG)

        # (try to) get the NTdb definition for this residue, atom
        csRow.ntDef = self._ntDefs.getDef((self.residueType, self.atomName))

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
        If need be: look back or look ahead
        :param rowIndx: index of row to process
        :param chemShiftList: ChemicalShifList instance to generate new ChemicalShift
        :return index of next row to process
        """
        _previousRow = self.chemicalShifts[rowIndx-1] if rowIndx > 0 else None

        _row = self.chemicalShifts[rowIndx]

        nextRowIndx = rowIndx + 1 # Now points to next row; in some case incremented further, i.e. skipping a row
        _nextRow = self.chemicalShifts[nextRowIndx] if nextRowIndx < len(self.chemicalShifts) else None

        project = chemShiftList.project

        chainCode = chemShiftList.name
        atomName = _row.atomName

        # process the ambiguityCode and see if atomName needs changing
        if _row.specialType is None and _row.ambiguityCode > 1:
            getLogger().warning(f'No provisions for ({_row.residueType},{_row.atomName}) with ambiguity code {_row.ambiguityCode}')

        elif _row.specialType == ISMETHYL:
            if _row.nefAtomName is None:
                # This is the second or third proton of a methyl; just skip as we handled it for the first one
                return nextRowIndx  # already pointing to the next row
            atomName = _row.nefAtomName

        elif _row.specialType == ISMETHYLENE:
            if _row.ambiguityCode == 1:
                # unfortunately:
                # - methylenes with identical chemical shifts have ambiguity code 1
                if _nextRow is not None and \
                        self._isSameResidue(_row, _nextRow) and \
                        _nextRow.specialType == ISMETHYLENE and \
                        _nextRow.value == _row.value:
                    atomName = _row.nefAtomName.replace('x','%').replace('y','%')
                    nextRowIndx += 1  # We skip the next row

                # # - methylenes with only one chemical shift listed can have ambiguity code 1
                # elif _nextRow is not None and \
                #          self._isSameResidue(_row, _nextRow) and \
                #          _nextRow.specialType != ISMETHYLENE and \
                #     _previousRow is not None and \
                #          self._isSameResidue(_row, _previousRow) and \
                #          _previousRow.specialType != ISMETHYLENE:
                #     atomName = _row.nefAtomName.replace('x','%').replace('y','%')

            elif _row.ambiguityCode == 2:
                atomName = _row.nefAtomName

            else:
                getLogger().warning(f'No provisions for methylenes ({_row.residueType},{_row.atomName}) with ambiguity code {_row.ambiguityCode}')

        elif _row.specialType == ISAROMATIC:
            if _row.ambiguityCode == 1:
            # TODO: implement this, as the aromatic protons do not appear on successive lines
            #
            #     # unfortunately:
            #     # - aromatic ring protons with identical chemical shifts have ambiguity code 1
            #     if _nextRow is not None and \
            #             self._isSameResidue(_row, _nextRow) and \
            #             _nextRow.specialType == ISMETHYLENE and \
            #             _nextRow.value == _row.value:
            #         atomName = _row.nefAtomName.replace('x','%').replace('y','%')
            #         nextRowIndx += 1  # We skip the next row
                pass

            elif _row.ambiguityCode == 3:
                atomName = _row.nefAtomName
            else:
                getLogger().warning(f'No provisions for aromatic sidechain ({_row.residueType},{_row.atomName}) with ambiguity code {_row.ambiguityCode}')

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
        # 'parse'/convert the rows, assigning the attributes
        for csRow in self.chemicalShifts:
            self._parseChemicalShiftRow(csRow)

        # Loop again to create the V3 chemcialShift objects
        # We need a 'dynamic' row indexing, as sometimes we will skip a row; e.g for methyls and degenerate
        # methylenes
        rowIndx = 0
        while rowIndx < len(self.chemicalShifts):
            rowIndx = self._newChemicalShift(rowIndx, chemShiftList)

        return [chemShiftList]

ChemicalShiftSaveFrame._registerSaveFrame()

