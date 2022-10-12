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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-10-12 15:27:08 +0100 (Wed, October 12, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2020-02-17 10:28:41 +0000 (Thu, February 17, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
from ccpn.util.Logging import getLogger
from ccpn.util.nef.GenericStarParser import LoopRow
from ccpn.framework.lib.ccpnNmrStarIo.SaveFrameABC import SaveFrameABC

# from sandbox.Geerten.NTdb.NTdbLib import getNefName
from ccpn.framework.lib.NTdb.NTdbDefs import getNTdbDefs


class ChemicalShiftSaveFrame(SaveFrameABC):
    """A class to manage chemicalShift saveFrame
    Creates a new (static) ChemicalShift Table and NmrChain/Residues/Atoms
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

    def _getNefName(self, aDef) -> str:
        """Construct the nefName from aDef.name; account for the different possibilities
        """
        if aDef is None:
            return ''

        # all methyls
        if aDef.isMethyl and aDef.isProton:
            _nefName = aDef.name[:-1] + '%'

        # Asn, Gln amine groups
        elif aDef.parent.name in ('ASN','GLN') and aDef.name in 'HD21 HD22 HE21 HE22'.split():
            _nefName = aDef.name[:-1] + aDef.name[-1:].replace('1','x').replace('2','y')

        # Ade, Gua amine groups
        elif aDef.parent.name in ('A','DA','G','DG') and aDef.name in 'H61 H62 H21 H22'.split():
            _nefName = aDef.name[:-1] + aDef.name[-1:].replace('1','x').replace('2','y') \

        # amino acids methylenes
        elif aDef.parent.isAminoAcid and aDef.isMethylene and aDef.isProton:
            _nefName = aDef.name[:-1] + aDef.name[-1:].replace('2','x').replace('3','y')

        # nucleic acids methylenes
        elif aDef.parent.isNucleicAcid and aDef.isMethylene and aDef.isProton:
            _nefName = aDef.name.replace("''",'x').replace("'",'y')

        # Phe, Tyr aromatic sidechains
        elif aDef.parent.name in ('PHE','TYR') and aDef.name in 'HD1 CD1 HD2 CD2  HE1 CE1 HE2 CE2'.split():
            _nefName = aDef.name.replace('1','x').replace('2','y')

        else:
            _nefName = aDef.name

        return _nefName

    def _parseChemicalShiftRow(self, csRow:LoopRow):
        """
        Parse the chemical shift row and assign attributes for subsequent processing
        :param csRow: a LoopRow instance
        """
        csRow.value = float(csRow.get(self._VALUE_TAG)) if csRow.get(self._VALUE_TAG) is not None else None
        csRow.valueError = float(csRow.get(self._VALUE_ERROR_TAG)) if csRow.get(self._VALUE_ERROR_TAG) is not None else None
        figureOfMerit = csRow.get(self._FIGURE_OF_MERIT_TAG)
        csRow.figureOfMerit = float(figureOfMerit) if figureOfMerit is not None else 1.0

        csRow.sequenceCode = str(csRow.get(self._SEQUENCE_CODE_TAG))
        csRow.residueType = str(csRow.get(self._RESIDUE_TYPE_TAG))
        csRow.isotopeCode = '%s%s' % (csRow.get(self._ISOTOPE_TAG_1), csRow.get(self._ISOTOPE_TAG_2))
        csRow.atomName = str(csRow.get(self._ATOM_NAME_TAG))
        csRow.ambiguityCode = int(csRow.get(self._AMBIGUITY_CODE)) if csRow.get(self._AMBIGUITY_CODE) is not None else None

        csRow.comment = csRow.get(self._COMMENT_TAG)

        # (try to) get the NTdb definition for this residue, atom
        csRow.ntDef = self._ntDefs.getDef((csRow.residueType, csRow.atomName))

        # convert atomName to NEF;
        csRow.nefAtomName = self._getNefName(csRow.ntDef)

        csRow.skip = False

        dd = self._seqResDict.setdefault((csRow.residueType, csRow.sequenceCode), [])
        dd.append(csRow)

    def _newChemicalShift(self, csRow:LoopRow, nmrChain, chemShiftList):
        """Use chemShift to make a new (v3) chemicalShift in chemShiftList
        If need be: look back or look ahead into other rows
        :param csRow: the row to process
        :param nmrChain: a NmrChain instance for the generated NmrAtoms
        :param chemShiftList: ChemicalShifList instance to generate new ChemicalShift
        :return a ChemicalShift instance
        """
        _row = csRow

        if _row.skip:
            return None

        project = chemShiftList.project
        # chainCode = self.parent.chainCode if self.parent.chainCode else \
        #             chemShiftList.name
        atomName = _row.atomName

        if _row.ntDef is not None:
            if _row.ambiguityCode == 1:
                # unfortunately:

                # - methyl protons have identical chemical shifts with ambiguity code 1
                if _row.ntDef.isMethyl and _row.ntDef.isProton:
                    atomName = _row.nefAtomName
                    # We can skip all other methyl protons
                    for _aDef in _row.ntDef.otherAttachedProtons:
                        if (_aRow := self._lookupDict.get( (_row.residueType, _row.sequenceCode, _aDef.name) )):
                            _aRow.skip = True

                # - methylene protons with identical chemical shifts have ambiguity code 1
                elif _row.ntDef.isMethylene and _row.ntDef.isProton:
                    _aDef = _row.ntDef.otherAttachedProtons[0]
                    if (_aRow := self._lookupDict.get( (_row.residueType, _row.sequenceCode, _aDef.name) )):
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
                    if (_aRow := self._lookupDict.get( (_row.residueType, _row.sequenceCode, _aName) )):
                        if _row.value == _aRow.value:
                            _aRow.skip = True
                            atomName = _row.atomName.replace('1','%').replace('2','%')

            elif _row.ambiguityCode == 2:
                #  (Val, Leu NEF xy rules propagation; i.e. HDx% connected to CDx)
                if _row.ntDef.parent.name in ('VAL', 'LEU') and _row.ntDef.isMethyl and _row.ntDef.isProton:
                    atomName = _row.nefAtomName.replace('1','x').replace('2','y')
                    # We can skip all other methyl protons
                    for _aDef in _row.ntDef.otherAttachedProtons:
                        if (_aRow := self._lookupDict.get( (_row.residueType, _row.sequenceCode, _aDef.name) )):
                            _aRow.skip = True
                    # propagate xy to carbon; fortunately, these rows appear follow the proton ones so we
                    # can adjust the attributes
                    _cName = _row.ntDef.attachedHeavyAtom.name
                    if (_cRow := self._lookupDict.get( (_row.residueType, _row.sequenceCode, _cName) )):
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
                    if (_cRow := self._lookupDict.get( (_row.residueType, _row.sequenceCode, _cName) )):
                        _cRow.nefAtomName = _cRow.atomName.replace('1','x').replace('2','y')
                        _cRow.ambiguityCode = 3
                else:
                    atomName = _row.nefAtomName

            else:
                getLogger().warning(f'No provisions for ({_row.residueType},{_row.atomName}) with ambiguity code {_row.ambiguityCode}')

        # get the NmrAtom object
        # nmrChain = project.fetchNmrChain(chainCode)
        nmrResidue = nmrChain.fetchNmrResidue(residueType=_row.residueType, sequenceCode=_row.sequenceCode)
        try:
            nmrAtom = nmrResidue.newNmrAtom(name=atomName, isotopeCode=_row.isotopeCode)

            # create the ChemicalShift
            chemShift = chemShiftList.newChemicalShift(nmrAtom=nmrAtom,
                                                       value=_row.value,
                                                       valueError=_row.valueError,
                                                       figureOfMerit=_row.figureOfMerit,
                                                       comment=_row.comment)
            chemShift._static = False if chemShiftList.spectra else True

            return chemShift
        except Exception as es:
            getLogger().warning(f' ERROR  {es}')

    def _checkMissingCodes(self):
        """
        Check for matching or missing ambiguity codes.
        :return:
        """
        for _res, vals in self._seqResDict.items():
            matches = OrderedDict()
            for ll in range(4, 1, -1):
                for lInner in range(ll, 1, -1):
                    for _row in vals:
                        atomName = _row.atomName
                        if len(atomName) == ll and atomName[-1].isdigit():
                            name = atomName[:lInner] + '%'  # %%%'[0:ll-lInner] - only need a single hash
                            rowSet = matches.setdefault(name, [])
                            rowSet.append(_row)

            # remove all the short matches
            _matches = {k:v for k, v in matches.items() if len(v) > 1}

            # remove any sets that are duplicated, e.g., HG1% may be the same as HG% if HG2% is missing
            matches = OrderedDict()
            ssFound = []
            for group, rowSet in _matches.items():
                ss = set(id(rr) for rr in rowSet)
                if len(ss) != len(rowSet):
                    getLogger().warning(f'Duplicate values {group}  {[rr.atomName for rr in rowSet]}')

                # allSet = [set(id(rr) for rr in _rSet) for _rSet in matches.values()]
                if ss not in ssFound:
                    matches[group] = rowSet
                    ssFound.append(ss)

            for group, rowSet in list(matches.items()):
                # check matching ambiguity codes
                ambCodes = set()

                for _row in rowSet:
                    ambCodes.add(_row.ambiguityCode)
                # ambCodes -= {None}

                if len(ambCodes) > 1:
                    getLogger().warning(f'multiple ambiguity codes for matching atomNames - {_res}:{group}:{list(ambCodes)}')
                    for _row in rowSet:
                        _row.ambiguityCode = 2

                elif len(ambCodes) == 1 and ambCodes == {None}:
                    # may require special cases here
                    getLogger().warning(f'missing ambiguity codes for matching atomNames - {_res}:{group}:{list(ambCodes)}')
                    for _row in rowSet:
                        _row.ambiguityCode = 2

                vals = set(_row.value for _row in rowSet) - {None}
                if vals and len(vals) == 1:
                    # atoms need to be merged if they are all the same value
                    for _row in rowSet[1:]:
                        _row.skip = True

                else:
                    # group can be discarded
                    del matches[group]

            assert 1==1  # just for a breakpoint

    def importIntoProject(self, project) -> list:
        """Import the data of self into project.
        :param project: a Project instance.
        :return: list with the created ChemicalShiftList and NmrChain V3 objects.
        """
        # Create a new ChemicalShiftList and a new NmrChain
        comment = f'created from {self.entryName}'
        chemShiftList = project.newChemicalShiftList(name = self.entryName,
                                                     autoUpdate = False,
                                                     comment = comment
                                                     )
        chainCode = self.parent.chainCode if self.parent.chainCode else \
                    self.entryName
        #TODO isConnected should be True; after ficing the model issues
        nmrChain = project.newNmrChain(shortName=chainCode, isConnected=False, comment=comment)

        # A two-stage conversion, as sometimes we need to look back or forward
        # 'parse'/convert the rows, assigning the attributes; create a lookupDict
        self._lookupDict = {}
        self._seqResDict = {}
        for _row in self.chemicalShifts:
            self._parseChemicalShiftRow(_row)
            self._lookupDict[(_row.residueType, _row.sequenceCode, _row.atomName)] = _row

        # Loop again to check that pairs don't have any missing ambiguity codes
        # self._checkMissingCodes()

        # Loop again to create the V3 chemicalShift objects
        for _row in self.chemicalShifts:
            self._newChemicalShift(_row, nmrChain=nmrChain, chemShiftList=chemShiftList)

        text = f'\n==> saveFrame "{self.name}"\n'
        text += f'Imported as {chemShiftList}  ({len(chemShiftList.chemicalShifts)} shifts)\n'
        text += f'Created {nmrChain}  ({len(nmrChain.nmrResidues)} NmrResidues, {len(nmrChain.nmrAtoms)} NmrAtoms)\n'
        self.parent.note.appendText(text)

        return [chemShiftList, nmrChain]

ChemicalShiftSaveFrame._registerSaveFrame()

