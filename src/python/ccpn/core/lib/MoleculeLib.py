"""Library functions for Molecule-related data

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:32 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
from collections import OrderedDict
from ccpn.util import Common as commonUtil
from ccpn.core.Atom import Atom
from ccpn.core.Chain import Chain
from ccpn.core.Project import Project


def _incrementedSequenceCode(sequenceCode, seqOffset):
    """get sequenceCode of Residue or NmrResidue incremented by seqOffset.

    Will raise ValueError if residue.seqCode is not set (i.e. there is no sequence number"""
    code, ss, offset = commonUtil.parseSequenceCode(sequenceCode)
    sequenceCode = None
    if code is not None:
        code += seqOffset
        if offset is None:
            sequenceCode = '%s%s' % (code, ss or '')
        else:
            sequenceCode = '%s%s%+d' % (code, ss or '', offset)
    #
    return sequenceCode


def duplicateAtomBonds(chainMap: typing.Dict[Chain, Chain]):
    """Duplicate atom-atom bonds within source chains to target chains,
    skipping those that already exist.

    Input is a map from source chains to corresponding target chains.

    Atoms are mapped on matching Pids (with different chain codes"""
    if not chainMap:
        return
    project = list(chainMap.keys())[0]._project
    apiMolSystem = project._wrappedData.molSystem

    # Make source -> target ApiAtom map and remove target atoms with no match in source
    apiAtomMap = {}
    for source, target in chainMap.items():
        cutat = 3 + len(target.shortName)  # Cut after e.g. 'MA:B' for chain B
        prefix = 'MA:' + source.shortName  # New prefix - e.g. 'MA:E' for chain E

        for atom2 in target.atoms:
            # Get equivalent atom in source
            apid = prefix + atom2.pid[cutat:]
            atom1 = project.getByPid(apid)

            if atom1 is None:
                # Atom missing, presumably removed from original chain manually
                atom2.delete()
            else:
                # Make self-other api atom map
                apiAtomMap[atom1._wrappedData] = atom2._wrappedData

    # Make target bonds if not already present
    for genericBond in apiMolSystem.genericBonds:
        bondType = genericBond.bondType
        apiAtoms = genericBond.atoms
        fs = frozenset(apiAtomMap.get(x) for x in apiAtoms)
        if None not in fs:
            # Both atoms matched an atom on target side'
            gBond = apiMolSystem.findFirstGenericBond(atoms=fs)
            if gBond is None:
                # There is no bond in 'other' that matches the bond. Make it
                apiMolSystem.newGenericBond(atoms=fs, bondType=bondType)


def extraBoundAtomPairs(project: Project, selectSequential: bool = None) -> typing.List[typing.Tuple[Atom, Atom]]:
    """Get pairs of bound Atoms whose bonds are NOT defined through the residue topology.
    The result and each individual atom pair are both sorted

    Returns sequential bond pairs if selectSequential is True,
    non-sequential bond pairs if selectSequential is False,
    and both if selectSequential is None"""

    result = []

    # TODO NBNB extend to non-protein atoms. This is a HACK!!
    refAtomNames = {
        ('protein',): {'first': ['N'], 'last': ['C']},
        ('DNA',)    : {'first': ['P'], 'last': ["O3'"]},
        }
    refAtomNames[('RNA',)] = refAtomNames[('DNA', 'RNA',)] = refAtomNames[('DNA',)]

    getData2Obj = project._data2Obj.get

    apiAtomPairs = [tuple(x.atoms) for x in project._wrappedData.molSystem.genericBonds]
    atomPairs = [tuple(getData2Obj(y) for y in x) for x in apiAtomPairs]

    for atom1, atom2 in atomPairs:

        isSequential = False

        molTypes = tuple(sorted(set((atom1._wrappedData.residue.molType,
                                     atom2._wrappedData.residue.molType))))
        refdd = refAtomNames.get(molTypes)
        if refdd is not None:
            # molTypes match, this could be sequential
            atomName1 = atom1.name
            atomName2 = atom2.name
            if (atomName1 in refdd['last'] and atomName2 in refdd['first'] and
                    atom1.residue.nextResidue is atom2.residue):
                isSequential = True
            elif (atomName2 in refdd['last'] and atomName1 in refdd['first'] and
                  atom2.residue.nextResidue is atom1.residue):
                isSequential = True

        if selectSequential is None or bool(selectSequential) == isSequential:
            result.append(tuple(sorted((atom1, atom2))))
    #
    result.sort()
    return result


.0


def sequenceMatchOffset(reference: OrderedDict, sequence: OrderedDict) -> typing.Optional[int]:
    """Check if residues in sequence match those in reference, directly or with an offset.
    Reference and sequence are OrderedDict(sequenceCode:residueType)
    Both integer and string sequenceCodes (or a mixture) will give correct results
    - other types of key will not.

    Returns 0 if all(reference.get(key) == val for key, val in sequence.items())

    Otherwise tries to convert keys in sequence and reference to integers
    and checks if all (reference.get(key+offset) == val for key, val in sequence.items())
    for some offset.

    Returns the offset is a match is found,, None if no match is found
    """

    if not reference or not sequence:
        return None

    if None in reference.values() or None in sequence.values():
        raise ValueError("Input sequence contained residueType None")

    if all(reference.get(key) == val for key, val in sequence.items()):
        # matches sequence with zero offset correction
        return 0

    else:
        # No luck. Convert to integers and try with an offset
        try:
            reference2 = OrderedDict(((int(key), val) for key, val in reference.items()))
            sequence2 = OrderedDict(((int(key), val) for key, val in sequence.items()))
        except ValueError:
            # Could not convert to integer. Failure
            return None

        minOffset = min(reference2.keys()) - min(sequence2.keys())
        maxOffset = max(reference2.keys()) - max(sequence2.keys())
        for offset in range(minOffset, maxOffset + 1):
            if all(reference2.get(key + offset) == val for key, val in sequence2.items()):
                return offset

        # No offset matched. Result is failure
        return None
