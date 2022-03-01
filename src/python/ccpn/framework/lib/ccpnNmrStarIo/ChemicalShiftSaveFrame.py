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
__dateModified__ = "$dateModified: 2022-03-01 18:02:32 +0000 (Tue, March 01, 2022) $"
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

from sandbox.Geerten.NTdb.NTdbLib import ISMETHYL, ISMETHYLENE, getNefMappingDict


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

    @property
    def chemicalShifts(self) ->list :
        """:return a list of chemical shift LoopRow's
        """
        if (_loop := self.get(self._LOOP_KEY)) is None:
            return []
        return _loop.data

    def _newChemicalShift(self, rowIndx, chemShiftList):
        """Use chemShift to make a new (v3) chemicalShift in chemShiftList
        """
        _row = self.chemicalShifts[rowIndx]
        rowIndx += 1 # Now points to next row; in some case incremented further, i.e. skipping a row
        _nextRow = self.chemicalShifts[rowIndx] if rowIndx < len(self.chemicalShifts) else None

        project = chemShiftList.project

        value = float(_row.get(self._VALUE_TAG))
        valueError = float(_row.get(self._VALUE_ERROR_TAG))
        figureOfMerit = _row.get(self._FIGURE_OF_MERIT_TAG)
        figureOfMerit = float(figureOfMerit) if figureOfMerit is not None else 1.0

        chainCode = chemShiftList.name
        sequenceCode = str(_row.get(self._SEQUENCE_CODE_TAG))
        residueType = str(_row.get(self._RESIDUE_TYPE_TAG))
        isotopeCode = '%s%s' % (_row.get(self._ISOTOPE_TAG_1), _row.get(self._ISOTOPE_TAG_2))
        atomName = str(_row.get(self._ATOM_NAME_TAG))
        ambiguityCode = int(_row.get(self._AMBIGUITY_CODE))

        # convert atomName to NEF; handle ambiguity code
        residueName, nefName, specialType = self._nefMappingDict.get((residueType, atomName), (None, None, None))
        if specialType is None and ambiguityCode > 1:
            getLogger().warning(f'No provisions for ({sequenceCode},{atomName}) with ambiguity code {ambiguityCode}')

        elif specialType == ISMETHYL:
            if nefName is None:
                return rowIndx
            atomName = nefName

        elif specialType == ISMETHYLENE:
            if ambiguityCode == 1:
                # unfortunately, methylenes with identical chemical shifts have ambiguity code 1
                if _nextRow is not None:
                    nextValue = float(_nextRow.get(self._VALUE_TAG))
                    if nextValue == value:
                        atomName = nefName.replace('x','%').replace('y','%')
                        rowIndx += 1
            elif ambiguityCode == 2 and nefName is not None:
                atomName = nefName
            else:
                getLogger().warning(f'No provisions for methylenes ({sequenceCode},{atomName}) with ambiguity code {ambiguityCode}')

        comment = _row.get(self._COMMENT_TAG)

        # get the NmrAtom object
        nmrChain = project.fetchNmrChain(chainCode)
        nmrResidue = nmrChain.fetchNmrResidue(residueType=residueType, sequenceCode=sequenceCode)
        nmrAtom = nmrResidue.newNmrAtom(name=atomName, isotopeCode=isotopeCode)

        # create the ChemicalShift
        chemShiftList.newChemicalShift(nmrAtom=nmrAtom,
                                       value=value, valueError=valueError, figureOfMerit=figureOfMerit,
                                       comment=comment)

        return rowIndx

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
        # We need to do a 'dynamic' row indexing, as sometimes we will skip a row; e.g for methyls and degenerate
        # methylenes
        rowIndx = 0
        while rowIndx < len(self.chemicalShifts):
            rowIndx = self._newChemicalShift(rowIndx, chemShiftList)

        return [chemShiftList]

ChemicalShiftSaveFrame._registerSaveFrame()

