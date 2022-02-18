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
__dateModified__ = "$dateModified: 2022-02-18 12:43:30 +0000 (Fri, February 18, 2022) $"
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

    @property
    def chemicalShifts(self) ->list :
        """:return a list of chemical shift """
        if (_loop := self.get(self._LOOP_KEY)) is None:
            return []

        return _loop.data

    def _newChemicalShift(self, chemShift:LoopRow, chemShiftList):
        """Use chemShift to make a new (v3) chemicalShift in chemShiftList
        """
        project = chemShiftList.project
        chainCode = chemShiftList.name
        nmrChain = project.fetchNmrChain(chainCode)

        sequenceCode = str(chemShift.get(self._SEQUENCE_CODE_TAG))
        residueType = chemShift.get(self._RESIDUE_TYPE_TAG)
        nmrResidue = nmrChain.fetchNmrResidue(residueType=residueType, sequenceCode=sequenceCode)

        isotopeCode = '%s%s' % (chemShift.get(self._ISOTOPE_TAG_1), chemShift.get(self._ISOTOPE_TAG_2))
        atomName = str(chemShift.get(self._ATOM_NAME_TAG))
        ambiguityCode = chemShift.get(self._AMBIGUITY_CODE)
        # TODO: handle ambiguity codes
        nmrAtom = nmrResidue.newNmrAtom(name=atomName, isotopeCode=isotopeCode)

        value = chemShift.get(self._VALUE_TAG)
        valueError = chemShift.get(self._VALUE_ERROR_TAG)
        figureOfMerit = chemShift.get(self._FIGURE_OF_MERIT_TAG)
        if figureOfMerit is None:
            figureOfMerit = 1.0

        comment = chemShift.get(self._COMMENT_TAG)

        chemShiftList.newChemicalShift(nmrAtom=nmrAtom,
                                       value=value, valueError=valueError, figureOfMerit=figureOfMerit,
                                       comment=comment)

    def importIntoProject(self, project) -> list:
        """Import the data of self into project.
        :param project: a Project instance
        :return list of imported V3 objects
        """
        chemShiftList = project.newChemicalShiftList(name = self.entry_id,
                                                     autoUpdate = False,
                                                     comment = f'from BMRB entry {self.entry_id}; {self.name}'
                                                     )
        for chemShift in self.chemicalShifts:
            self._newChemicalShift(chemShift, chemShiftList)

        return [chemShiftList]

ChemicalShiftSaveFrame._registerSaveFrame()

