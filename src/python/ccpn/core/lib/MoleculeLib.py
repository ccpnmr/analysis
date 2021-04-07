"""Library functions for Molecule-related data

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-04-07 16:27:55 +0100 (Wed, April 07, 2021) $"
__version__ = "$Revision: 3.0.3 $"
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


NamingSystems = [
    'PDB_REMED',
    'DIANA',
    'MOLMOL',
    'UCSF',
    'MSI',
    'CING',
    'PDB',
    'MSD',
    'DISMAN',
    'GROMOS',
    'CYANA2.1',
    'BMRB',
    'XPLOR',
    'SYBYL',
    'CIF',
    'IUPAC',
    'DISGEO',
    'AQUA'
    ]

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


def expandChainAtoms(chain,
                     replaceStarWithPercent = True,
                     addPseudoAtoms = True,
                     addNonstereoAtoms = True,
                     setBoundsForAtomGroups = True,
                     atomNamingSystem = 'PDB_REMED',
                     pseudoNamingSystem = 'AQUA'
                     ):
    """
    Called after creating a new chain.
    
    Create new atoms corresponding to the ChemComp AtomSets.
    Eg.
        -  A simple AtomSet named H1% consisting of H1, H2, H3 atoms
        will give a new V3 Atom called H1% of atomType='equivalent' and its components are the atomSet.atoms.

        -  A nested atomSets such as H% consisting of H1%, H2%, H3% atomSets
        will give a new V3 Atom called H% of atomType='equivalent' and its components are the V3 atoms H1%, H2%, H3%

    Use atom.componentAtoms to get the children atoms as a tuple:
        H1% --> (H1, H2, H3)
        HG% --> (HG1%, HG2%)

    From any "real" atom, use atom.compoundAtoms to get the parent atoms as a tuple.
         H1 --> (H1%)

    :param chain:  V3 Chain object,
    :return extended chain
    
    Extra arguments:
        :param replaceStarWithPercent: bool: True. Default
                Replace * with % if the char is in the atom name.
                E.g. H1* to become H1%.

        :param addPseudoAtoms: bool: True. Default
                Add new atoms with alternative names to the one derived from the atomSets.
                E.g.  MD, QG, MG. This will create a atom with same atom components
                as the standard from the chemComp atomSet. Therefore it's a duplicated!
                These atoms might not be present in the original ChemComp definitions

        :param addNonstereoAtoms: bool: True. Default
                Add new atoms for Non-stereoAtoms E.g. for a VAL, HGx%, HGy%
                These atoms might not be present in the original ChemComp definition

        :param setBoundsForAtomGroups: bool: True. Default
                set the newly created atoms from the AtomSets to be "bound" as the real atoms
                E.g. H1%-C1 to be like H1-C1
                and atoms derived from nested AtomSet like HG*-CG* etc.

        :param atomNamingSystem: str: 'PDB_REMED'. Default
                To be deprecated. Will be only NEF atomNamingSystem

        :param pseudoNamingSystem: str: 'AQUA'. Default
                To be deprecated. Will be only NEF atomNamingSystem

    """

    apiChain = chain._wrappedData
    molSystem = apiChain.molSystem

    if not atomNamingSystem in NamingSystems:
        atomNamingSystem = 'PDB_REMED'

    if not pseudoNamingSystem in NamingSystems:
        pseudoNamingSystem = 'AQUA'

    # Set elementSymbol and add missing atoms (lest something breaks lower down)
    for residue in apiChain.sortedResidues():
        chemCompVar = residue.chemCompVar
        namingSystem = chemCompVar.chemComp.findFirstNamingSystem(name=atomNamingSystem)
        for chemAtom in chemCompVar.findAllChemAtoms(className='ChemAtom'):
            atom = residue.findFirstAtom(name=chemAtom.name)
            if atom is None and namingSystem:
                # Special case - atoms may be named after PDB_REMED sysNAme rather than name
                atomSysName = namingSystem.findFirstAtomSysName(atomName=chemAtom.name)
                if atomSysName:
                    atom = residue.findFirstAtom(name=atomSysName.sysName)
            if atom is None:
                residue.newAtom(name=chemAtom.name, atomType='single',
                                elementSymbol=chemAtom.elementSymbol)
            else:
                atom.elementSymbol = chemAtom.elementSymbol

    # Add boundAtoms for MolResLinks - Now add as GenericBond
    for molResLink in apiChain.molecule.molResLinks:
        ff = apiChain.findFirstResidue
        atoms = frozenset(
                ff(seqId=x.molResidue.serial).findFirstAtom(name=x.linkEnd.boundChemAtom.name)
                for x in molResLink.molResLinkEnds
                )
        if molSystem.findFirstGenericBond(atoms=atoms) is None:
            molSystem.newGenericBond(atoms=atoms)
    #     if atoms[1] not in atoms[0].boundAtoms:
    #       atoms[0].addBoundAtom(atoms[1])

    # Set boundAtoms for existing atoms within residue
    for residue in apiChain.sortedResidues():
        chemCompVar = residue.chemCompVar
        namingSystem = chemCompVar.chemComp.findFirstNamingSystem(name=atomNamingSystem)
        for atom in residue.atoms:
            chemAtom = chemCompVar.findFirstChemAtom(name=atom.name, className='ChemAtom')
            atomSysName = boundChemAtoms = None
            if chemAtom is None and namingSystem:
                # Check for ChemAtom where match is in PDB_REMED rather than atom name (e.g. OXT, HXT)
                atomSysName = namingSystem.findFirstAtomSysName(sysName=atom.name)
                if atomSysName:
                    chemAtom = chemCompVar.findFirstChemAtom(name=atomSysName.atomName, className='ChemAtom')
            if chemAtom is not None:
                boundChemAtoms = set(x for y in chemAtom.chemBonds for x in y.chemAtoms)
                for boundChemAtom in boundChemAtoms:
                    if boundChemAtom is not chemAtom and boundChemAtom.className == 'ChemAtom':
                        boundAtom = residue.findFirstAtom(name=boundChemAtom.name)
                        if boundAtom is None and namingSystem:
                            # Check for ChemAtom where match is in PDB_REMED rather than atom name (e.g. OXT, HXT)
                            atomSysName = namingSystem.findFirstAtomSysName(atomName=boundChemAtom.name)
                            if atomSysName:
                                boundAtom = residue.findFirstAtom(name=atomSysName.sysName)
                        if boundAtom is not None and boundAtom not in atom.boundAtoms:
                            atom.addBoundAtom(boundAtom)
                #
        # Add boundAtoms for MolSystemLinks - Now add as GenericBond
        for linkEnd in residue.sortedMolSystemLinkEnds():
            molSystemLink = linkEnd.molSystemLink
            atoms = frozenset(x.residue.findFirstAtom(name=x.linkEnd.boundChemAtom.name)
                              for x in molSystemLink.molSystemLinkEnds)
            if molSystem.findFirstGenericBond(atoms=atoms) is None:
                molSystem.newGenericBond(atoms=atoms)
        #   if atoms[1] not in  atoms[0].boundAtoms:
        #     atoms[0].addBoundAtom(atoms[1])

        # NB we do NOT add boundAtoms for NonCovalentBonds

        # Add extra atoms corresponding to ChemAtomSets
        chemCompVar = residue.chemCompVar

        pseudoNamingSystem = chemCompVar.chemComp.findFirstNamingSystem(name=pseudoNamingSystem)

        # Map from chemAtomSet to equivalent Atom
        casMap = {}

        # map from chemAtomSet.name to nonStereo names
        nonStereoNames = {}

        for chemAtomSet in chemCompVar.chemAtomSets:

            # get nests of connected chemAtomSets
            if not chemAtomSet.chemAtomSet:
                # get nested chemAtomSets, starting at topmost set
                localSets = [chemAtomSet]
                for cas in localSets:
                    localSets.extend(cas.chemAtomSets)

                # Process in reverse order, guaranteeing that contained sets are always ready
                for cas in reversed(localSets):
                    chemContents = cas.sortedChemAtoms()
                    # NB the fact that chemAtoms and chemAtomSets are sorted (by name) is used lower down
                    if chemContents:
                        # contents are real atoms
                        components = [residue.findFirstAtom(name=x.name) for x in chemContents]
                    else:
                        chemContents = cas.sortedChemAtomSets()
                        components = [casMap[x] for x in chemContents]
                    elementSymbol = chemContents[0].elementSymbol

                    commonBound = frozenset.intersection(*(x.boundAtoms for x in components))

                    # Add 'equivalent' atom
                    if replaceStarWithPercent:
                        newName = cas.name.replace('*', '%')
                    else:
                        newName = cas.name
                    newAtom = residue.newAtom(name=newName, atomType='equivalent',
                                              elementSymbol=elementSymbol, atomSetName=cas.name,
                                              components=components, boundAtoms=commonBound)
                    casMap[cas] = newAtom

                    # NBNB the test on '#' count is a hack to exclude Tyr/Phe HD#|HE#
                    hackExclude = newName.count('%') >= 2

                    # Add 'pseudo' atom for proton
                    if addPseudoAtoms:
                        if elementSymbol == 'H':
                            newName = None
                            if pseudoNamingSystem:
                                atomSysName = pseudoNamingSystem.findFirstAtomSysName(atomName=cas.name,
                                                                                      atomSubType=cas.subType)
                                if atomSysName:
                                    newName = atomSysName.sysName

                            if newName is None:
                                # No systematic pseudoatom name found - make one.
                                # NBNB this will give names like MD1, QG1, MD2 for cases like Ile delta,
                                # where the standard says MD, QG, MG.
                                # But all the standard cases are covered by the pseudoNamingSystem (pseudoNamingSystem)
                                # Can we get away with this, or do we have to rename on a per-residue basis
                                # for the special cases?
                                startChar = 'Q'
                                if (len(cas.chemAtoms) == 3 and cas.isEquivalent
                                        and components[0].findFirstBoundAtom().elementSymbol == 'C'):
                                    if len(set(x.findFirstBoundAtom() for x in components)) == 1:
                                        # This is a methyl group
                                        # The second 'if' is likely unnecessary in practice, but let us be correct here
                                        startChar = 'M'

                                newName = startChar + cas.name.strip('*')[1:]

                            if len(newName) > 1:
                                # Make pseudoatom, except for 'H*'
                                residue.newAtom(name=newName, atomType='pseudo', elementSymbol=elementSymbol,
                                                atomSetName=cas.name, components=components, boundAtoms=commonBound)

                    # Add 'nonstereo atoms
                    if addNonstereoAtoms:
                        if not cas.isEquivalent and len(components) == 2 and not hackExclude:
                            # NB excludes cases with more than two non-equivalent components
                            # But then I do not think there are any in practice.
                            # and anyway we do not have a convention for them.
                            nonStereoNames[cas.name] = newNames = []
                            starpos = cas.name.find('*')
                            for ii, component in enumerate(components):
                                # NB components are sorted by key, which means by name
                                newChar = 'xy'[ii]
                                ll = list(component.name)
                                if len(ll) > starpos:
                                    ll[starpos] = newChar
                                else:
                                    # Necessary for cases like H2'/H2''
                                    ll.append(newChar)
                                newName = ''.join(ll)
                                newNames.append(newName)
                                if residue.findFirstAtom(name=newName) is not None:
                                    print("WARNING, new atom already exists: %s %s %s %s"
                                          % (residue.chain.code, residue.seqId, residue.ccpCode, newName))
                                else:
                                    residue.newAtom(name=newName, atomType='nonstereo', elementSymbol=elementSymbol,
                                                    atomSetName=cas.name, components=components, boundAtoms=commonBound)
        if setBoundsForAtomGroups:
            # NBNB Now we need to set boundAtoms for non-single Atoms.
            # We need to set:
            # HG*-CG* etc.
            # HGX*-CGX etc. - can be done from previous by char substitution
            eqvTypeAtoms = [x for x in residue.sortedAtoms() if x.atomType == 'equivalent']
            for ii, eqvAtom in enumerate(eqvTypeAtoms):
                components = eqvAtom.sortedComponents()
                for eqvAtom2 in eqvTypeAtoms:
                    components2 = eqvAtom2.sortedComponents()
                    if len(components) == len(components2):
                        if all((x in components2[jj].boundAtoms) for jj, x in enumerate(components)):
                            # All components of one are bound to a component of the other
                            # NB this relies on the sorted components being ordered to match the bonds
                            # but you should expect that both cases are sorted by branch index
                            # CG1,CG2 matching HG1*,HG2* etc.

                            # Add bond between equivalent atoms
                            if eqvAtom2 not in eqvAtom.boundAtoms:
                                eqvAtom.addBoundAtom(eqvAtom2)

                            nsNames1 = nonStereoNames.get(eqvAtom.atomSetName)
                            nsNames2 = nonStereoNames.get(eqvAtom2.atomSetName)
                            if nsNames1 and nsNames2:
                                # Non-stereoAtoms are defined for both - add x,y bonds
                                # NB We rely on names being sorted (x then y in both cases)
                                for kk, name in enumerate(nsNames1):
                                    atom1 = residue.findFirstAtom(name=name)
                                    atom2 = residue.findFirstAtom(name=nsNames2[kk])
                                    if atom2 not in atom1.boundAtoms:
                                        atom1.addBoundAtom(atom2)
                            break
