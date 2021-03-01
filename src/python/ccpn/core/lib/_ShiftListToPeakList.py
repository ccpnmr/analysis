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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-01 11:22:50 +0000 (Mon, March 01, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2021-02-22 15:44:00 +0000 (Mon, February 22, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================


###### WARNING: Private routines
##     Many routines are directly ported from V2 and intput/output API objects.



import re, operator
from ccpn.core.lib._DistanceRestraintsLib import _getDataDimRefFromPeakDim, _areAtomsBound, \
    _getBoundAtoms, _getBoundResonances, _pnt2ppm, _ppm2pnt, _hz2pnt, _pnt2hz, unit_converter, _areResonancesBound, \
    longRangeTransfers, _newAtomAndResonanceSets


DEFAULT_ISOTOPES = {'H':'1H','C':'13C','N':'15N','P':'31P','Si':'29Si',
                    'F':'19F','O':'16O'}

STEREO_PREFIX = 'stereo_'
CARBOHYDRATE_MOLTYPE = 'carbohydrate'
PROTEIN_MOLTYPE = 'protein'
OTHER_MOLTYPE = 'other'
DNA_MOLTYPE = 'DNA'
RNA_MOLTYPE = 'RNA'
DNARNA_MOLTYPE = 'DNA/RNA'



def _getIsotopomerSingleAtomFractions(isotopomers, atomName, subType=1):
    """Descrn: Get the isotope proportions for a names atom in over a set
               of isotopomers. Fractions normalised to 1.0
       Inputs: List of ChemCompLabel.Isotopomers, Word (ChemAtom.name), Word (ChemAtom.subType)
       Output: Dict of Word:Float - IsotopeCode:fraction
    """

    fractionDict = {}
    isoWeightSum = sum([x.weight for x in isotopomers])

    for isotopomer in isotopomers:
        atomLabels = isotopomer.findAllAtomLabels(name=atomName, subType=subType)
        atWeightSum = sum([x.weight for x in atomLabels])
        atFactor = isotopomer.weight / isoWeightSum

        for atomLabel in atomLabels:
            isotopeCode = atomLabel.isotopeCode
            contrib = atFactor * atomLabel.weight / atWeightSum
            fractionDict[isotopeCode] = fractionDict.get(isotopeCode, 0.0) + contrib

    return fractionDict

def _molLabelFractionsDict(resLabel, atName, subType, elementName):
    """get the isotopeCode:fraction dictionary for a single molLabel

    molLabel: molLabel object
    resid residue serial
    atName, subType, elementName: atom name subType and element name for atom

    Returns isotopeCode:fraction dictionary with fractions normalised to 1.0
    """
    # set up
    result = {}

    # get atomLabels, if any
    atomLabels = resLabel.findAllAtomLabels(atomName=atName)
    if not atomLabels:
        atomLabels = resLabel.findAllAtomLabels(elementName=elementName)

    # calculate fractions for AtomLabels
    if atomLabels:
        atWeightSum = sum([x.weight for x in atomLabels])
        for atomLabel in atomLabels:
            isotopeCode = '%s%s' % (atomLabel.massNumber, elementName)
            result[isotopeCode] = (result.get(isotopeCode, 0.0) +
                                   atomLabel.weight / atWeightSum)


    else:
        # calculate fractions for ResLabelFractions
        resLabelFractions = resLabel.resLabelFractions
        rlfWeightSum = sum([x.weight for x in resLabelFractions])

        for rlf in resLabelFractions:
            isotopomers = rlf.isotopomers
            isoFactor = rlf.weight / rlfWeightSum

            fractionDict = _getIsotopomerSingleAtomFractions(isotopomers, atName, subType)

            for isotopeCode in fractionDict.keys():
                contrib = fractionDict[isotopeCode]
                result[isotopeCode] = result.get(isotopeCode, 0.0) + (isoFactor * contrib)

    #
    return result

def _singleAtomFractions(labeledMixture, resId, atName):
    """get the isotopeCode:fraction dictionary for a labeledMixture

    labeledMixture:  LabeledMixture object
    resid, atName, residue serial and atom name for atom
    Returns isotopeCode:fraction dictionary with fractions normalised to 1.0
    """

    # set up
    molResidue = labeledMixture.labeledMolecule.molecule.findFirstMolResidue(
        serial=resId)
    if molResidue is None:
        return None

    chemAtom = molResidue.chemCompVar.findFirstChemAtom(name=atName)
    if chemAtom is None:
        return None
    elementName = chemAtom.elementSymbol
    subType = chemAtom.subType

    # get MolLabelFractions
    molLabelFractions = []
    useLabel = labeledMixture.averageComposition
    if not useLabel:
        molLabelFractions = list(labeledMixture.molLabelFractions)
        if len(molLabelFractions) == 1:
            useLabel = molLabelFractions[0]

    if useLabel:
        # average composition
        resLabel = useLabel.molLabel.findFirstResLabel(resId=resId)
        result = _molLabelFractionsDict(resLabel, atName, subType, elementName)

    else:
        # average over multiple molLabels
        molWeightSum = sum([x.weight for x in molLabelFractions])
        result = {}

        for mlf in molLabelFractions:
            resLabel = mlf.molLabel.findFirstResLabel(resId=resId)
            partResult = _molLabelFractionsDict(resLabel, atName, subType, elementName)
            for key, val in partResult.items():
                result[key] = result.get(key, 0.0) + val * mlf.weight / molWeightSum

    #
    return result

def _getExperimentAtomFractions(experiment, atom):
    """Descrn: Get the isotope proportions for an atom
               in a given experiment (label mixture)
       Inputs: Nmr.Experiment, MolSystem.Atom
       Output: Dict of Word:Float - IsotopeCode:fraction
    """

    labelledMixtures = experiment.labeledMixtures
    molResidue = atom.residue.molResidue
    molecule = molResidue.molecule

    fractionDict = {}

    for mixture in labelledMixtures:
        if mixture.labeledMolecule.molecule is molecule:
            resId = molResidue.serial
            atomName = atom.name
            fractionDict = _singleAtomFractions(mixture, resId, atom.name)
            break

    return fractionDict


def _getIsotopomerAtomPairFractions(isotopomers, atomNames, subTypes):
    """Descrn: Get the combined isotope proportions for a given pair of named
               atoms within a set of isotopomers. Fractions normalised to 1.0
       Inputs: List of ChemCompLabel.Isotopomers, 2-Tuple of Words (ChemAtom.name), 2-Tuple of Words (ChemAtom.subType)
       Output: Dict of Tuple:Float - (IsotopeCode,IsotopeCode):fraction
    """

    fractionDict = {}

    isoWeightSum = sum([x.weight for x in isotopomers])

    atLabels = [None, None]
    sumWeights = [None, None]

    for isotopomer in isotopomers:
        for i in (0, 1):
            atLabels[i] = isotopomer.findAllAtomLabels(name=atomNames[i],
                                                       subType=subTypes[i])
            sumWeights[i] = sum([x.weight for x in atLabels[i]])

        # Done this way to guard against the divisor becoming zero
        factor = isotopomer.weight / isoWeightSum
        divisor = sumWeights[0] * sumWeights[1]

        for atl0 in atLabels[0]:
            for atl1 in atLabels[1]:

                if atl0 is atl1:
                    contrib = atl0.weight * factor / sumWeights[0]
                else:
                    contrib = atl0.weight * atl1.weight * factor / divisor

                key = (atl0.isotopeCode, atl1.isotopeCode)
                fractionDict[key] = fractionDict.get(key, 0.0) + contrib

    return fractionDict

def _atomPairFractions(labeledMixture, resIds, atNames, ):
    """get the isotope pair : fraction dictionary for a labeledMixture

    labeledMixture:  LabeledMixture object
    resIds: length-two tuple of residue serials
    atNames: length-two tuple of atom names

    Returns (isotopeCode1, isotopeCode2):fraction dictionary
    with fractions normalised to 1.0
    """

    result = {}

    if len(resIds) != 2:
        raise ("Error: length of resIds %s must be 2" % resIds)
    if len(atNames) != 2:
        raise ("Error: length of atNames %s must be 2"
               % atNames)

    # calculate starting parameters
    elementNames = []
    subTypes = []
    for ii in (0, 1):
        molResidue = labeledMixture.labeledMolecule.molecule.findFirstMolResidue(
            serial=resIds[ii])
        if molResidue is None:
            return None

        chemAtom = molResidue.chemCompVar.findFirstChemAtom(name=atNames[ii])
        if chemAtom is None:
            return None
        elementName = chemAtom.elementSymbol
        elementNames.append(elementName)
        subTypes.append(chemAtom.subType)

    # get MolLabelFractions
    avLabel = labeledMixture.averageComposition
    if avLabel:
        molLabelFractions = [avLabel]
    else:
        molLabelFractions = labeledMixture.molLabelFractions
    molWeightSum = sum([x.weight for x in molLabelFractions])

    # calculate result
    for mlf in molLabelFractions:
        molFactor = mlf.weight / molWeightSum
        molLabel = mlf.molLabel

        uncorrelatedAtoms = True
        if resIds[0] == resIds[1]:
            oneResLabel = molLabel.findFirstResLabel(resId=resIds[0])
            for ii in (0, 1):
                if (oneResLabel.findAllAtomLabels(atomName=atNames[ii]) or
                        oneResLabel.findAllAtomLabels(elementName=elementNames[ii])):
                    uncorrelatedAtoms = False

        if uncorrelatedAtoms:
            # isotope frequencies are uncorrelated at the residue level
            dds = []
            for ii in (0, 1):
                resLabel = molLabel.findFirstResLabel(resId=resIds[ii])
                dds.append(_molLabelFractionsDict(resLabel, atNames[ii],
                                                  subTypes[ii], elementNames[ii]))

            for iso0 in dds[0]:
                for iso1 in dds[1]:
                    key = (iso0, iso1)
                    contrib = dds[0][iso0] * dds[1][iso1] * molFactor
                    result[key] = result.get(key, 0.0) + contrib

        else:
            # isotope frequencies are correlated at the residue level
            # Only happens if both are from the same residue and neither has
            # any AtomLabels. Loop over ResLabelFractions only
            resLabelFractions = oneResLabel.resLabelFractions
            rlfWeightSum = sum([x.weight for x in resLabelFractions])
            for rlf in resLabelFractions:
                partResult = _getIsotopomerAtomPairFractions(rlf.iotopomers, atNames, subTypes)
                for key, val in partResult.items():
                    contrib = val * rlf.weight * molFactor / rlfWeightSum
                    result[key] = result.get(key, 0.0) + contrib

    #
    return result

def _getExperimentAtomPairFractions(experiment, atom1, atom2):
    """Descrn: Get the combined isotope proportions for a given pair of molecular
               system atoms for a given experiment (label mixture).
       Inputs: Nmr.Experiment, MolSystem.Atom, MolSystem.Atom
       Output: Dict of Word:Float - IsotopeCode:fraction
    """
    residue1 = atom1.residue
    residue2 = atom2.residue
    molResidue1 = residue1.molResidue
    molResidue2 = residue2.molResidue
    molecule1 = molResidue1.molecule
    molecule2 = molResidue2.molecule

    resIds = (molResidue1.serial, molResidue2.serial)
    atomNames = (atom1.name, atom2.name)
    labelledMixtures = experiment.labeledMixtures

    fractionDict = {}

    if molecule1 is molecule2:
        for mixture in labelledMixtures:
            if mixture.labeledMolecule.molecule is molecule1:
                fractionDict = _atomPairFractions(mixture, resIds, atomNames)
                break

    else:
        fractionDict1 = _getExperimentAtomFractions(experiment, atom1)
        fractionDict2 = _getExperimentAtomFractions(experiment, atom2)

        for isotope1 in fractionDict1.keys():
            fraction1 = fractionDict1[isotope1]

            for isotope2 in fractionDict2.keys():
                fraction2 = fractionDict2[isotope2]
                key = (isotope1, isotope2)
                fractionDict[key] = fraction1 * fraction2

    return fractionDict

def _warnChempCompLabelFailure(ccpCode, molType, scheme):
  """Descrn: Display a general warning for not being able to find a chemComplLabel
     Inputs: Word, Word, ChemCompLabel.LabelingScheme, MolSystem.Atom
     Output: None
  """

  data = (ccpCode,molType,scheme.name)
  msg  = 'Could not find chemp comp labelling information for %s(%s) in scheme %s'
  print('Failure',msg % data)

def _getSchemeAtomFractions(scheme, atom):
    """Descrn: Get the isotope proportions for a given molecular
               system atom within a labelling scheme.
       Inputs: ChemCompLabel.LabelingScheme, MolSystem.Atom
       Output: Dict of Word:Float - IsotopeCode:fraction
    """

    fractionDict = {}

    residue = atom.residue
    ccpCode = residue.ccpCode
    molType = residue.molResidue.molType

    atomName = atom.name
    subType = atom.chemAtom.subType

    chemCompLabel = scheme.findFirstChemCompLabel(ccpCode=ccpCode,
                                                  molType=molType)

    if chemCompLabel:
        isotopomers = chemCompLabel.isotopomers
        fractionDict = _getIsotopomerSingleAtomFractions(isotopomers,
                                                         atomName,
                                                         subType)
    else:
        _warnChempCompLabelFailure(ccpCode, molType, scheme)

    return fractionDict


def _getSchemeAtomPairFractions(scheme, atom1, atom2):
    """Descrn: Get the combined isotope proportions for a given pair of molecular
               system atoms within a labelling scheme.
       Inputs: ChemCompLabel.LabelingScheme, MolSystem.Atom, MolSystem.Atom
       Output:
    """

    fractionDict = {}

    residue1 = atom1.residue
    ccpCode1 = residue1.ccpCode
    molType1 = residue1.molResidue.molType

    atomName1 = atom1.name
    subType1 = atom1.chemAtom.subType

    residue2 = atom2.residue
    ccpCode2 = residue2.ccpCode
    molType2 = residue2.molResidue.molType

    atomName2 = atom2.name
    subType2 = atom2.chemAtom.subType

    if residue1 is residue2:
        # Abundances are correlated by isotopomer site incorporation
        chemCompLabel = scheme.findFirstChemCompLabel(ccpCode=ccpCode1,
                                                      molType=molType1)

        if chemCompLabel:
            atomNames = (atomName1, atomName2)
            subTypes = (subType1, subType2)
            isotopomers = chemCompLabel.isotopomers
            fractionDict = _getIsotopomerAtomPairFractions(isotopomers, atomNames, subTypes)
        else:
            _warnChempCompLabelFailure(ccpCode1, molType1, scheme)

    else:
        # Abundances are independent, and presumably equilibrium, for the two sites
        chemCompLabel1 = scheme.findFirstChemCompLabel(ccpCode=ccpCode1,
                                                       molType=molType1)
        chemCompLabel2 = scheme.findFirstChemCompLabel(ccpCode=ccpCode2,
                                                       molType=molType2)

        if chemCompLabel1 and chemCompLabel2:
            isotopomers1 = chemCompLabel1.isotopomers
            fractionDict1 = _getIsotopomerSingleAtomFractions(isotopomers1,
                                                              atomName1,
                                                              subType1)
            isotopomers2 = chemCompLabel2.isotopomers
            fractionDict2 = _getIsotopomerSingleAtomFractions(isotopomers2,
                                                              atomName2,
                                                              subType2)

            for isotope1 in fractionDict1.keys():
                fraction1 = fractionDict1[isotope1]

                for isotope2 in fractionDict2.keys():
                    fraction2 = fractionDict2[isotope2]

                    key = (isotope1, isotope2)

                    fractionDict[key] = fraction1 * fraction2

        elif not chemCompLabel1:
            _warnChempCompLabelFailure(ccpCode1, molType1, scheme)

        elif not chemCompLabel2:
            _warnChempCompLabelFailure(ccpCode2, molType2, scheme)

    return fractionDict


def _getPrimaryDataDimRef(freqDataDim):
    """
    get dataDimRef child with lowest expDimRef.serial

    .. describe:: Input

    freqDataDim

    .. describe:: Output

    dataDimRef or None
    """
    dataDimRefs = freqDataDim.dataDimRefs
    if dataDimRefs:
        ll = [(x.expDimRef.serial, x) for x in dataDimRefs]
        ll.sort()
        return ll[0][1]
    else:
        return None


def _getDataDimRefFullRange(dataDimRef):
    """
    Get the full range of freq values for a data dimension reference
    taking into account spectral width and min/max unaliased freqs

    .. describe:: Input

    ccp.nmr.Nmr.DataDimRef

    .. describe:: Output

    2-List of Floats (min, max)
    """

    expDimRef = dataDimRef.expDimRef
    converter = unit_converter[('point', expDimRef.unit)]

    valRange = [converter(1, dataDimRef),
                converter(dataDimRef.dataDim.numPoints, dataDimRef)]
    valRange.sort()

    valueMin = expDimRef.minAliasedFreq  # Could be 0.0
    if valueMin is None:
        valueMin = valRange[0]

    valueMax = expDimRef.maxAliasedFreq
    if valueMax is None:
        valueMax = valRange[1]

    return [valueMin, valueMax]


def _areAtomsTocsyLinked(atom1, atom2):
    """
    Determine if two atoms have a connectivity that may be observable in a TOCSY experiment

    .. describe:: Input

    MolSystem.Atom, MolSystem.atom

    .. describe:: Output

    Boolean
    """

    if not hasattr(atom1, 'tocsyDict'):
        atom1.tocsyDict = {}
    elif atom1.tocsyDict.get(atom2):
        return atom1.tocsyDict[atom2]

    if not hasattr(atom2, 'tocsyDict'):
        atom2.tocsyDict = {}
    elif atom2.tocsyDict.get(atom1):
        return atom2.tocsyDict[atom1]

    chemAtom1 = atom1.chemAtom
    chemAtom2 = atom2.chemAtom
    element1 = chemAtom1.elementSymbol
    element2 = chemAtom2.elementSymbol

    if element1 != element2:
        boolean = False

    elif _areAtomsBound(atom1, atom2):
        boolean = True

    else:

        residue1 = atom1.residue
        residue2 = atom2.residue

        if residue1 is not residue2:
            boolean = False

        else:
            atomsA = set([atom1,])
            boolean = True
            while atom2 not in atomsA:
                atomsB = atomsA.copy()

                for atomB in atomsB:
                    for atom3 in _getBoundAtoms(atomB):
                        if atom3.residue is not residue1:
                            continue

                        if element1 == 'H':
                            if atom3.chemAtom.elementSymbol != 'H':
                                for atom4 in _getBoundAtoms(atom3):
                                    if atom4.chemAtom.elementSymbol == 'H':
                                        break
                                else:
                                    continue

                        if atom3.chemAtom.elementSymbol == element1:
                            if not hasattr(atom3, 'tocsyDict'):
                                atom3.tocsyDict = {}

                            atom1.tocsyDict[atom3] = True
                            atom3.tocsyDict[atom1] = True

                        atomsA.add(atom3)

                if atomsA == atomsB:  # Nothing more to add and atom2 not in linked set
                    boolean = False
                    break

    atom1.tocsyDict[atom2] = boolean
    atom2.tocsyDict[atom1] = boolean
    return boolean


def _getLinkedResidue(residue, linkCode='prev'):
    """Find a residue, if it exists, that is linked to the
               input residue by a given type of molResidue link.
    .. describe:: Input

    MolSystem.Residue

    .. describe:: Output

    MolSystem.Residue
    """

    if not hasattr(residue, 'linkedResidueDict'):
        residue.linkedResidueDict = {}
    else:
        if residue.linkedResidueDict.get(linkCode):
            return residue.linkedResidueDict[linkCode]

    residue2 = None
    chain = residue.chain
    molResidue = residue.molResidue
    linkEnd = molResidue.findFirstMolResLinkEnd(linkCode=linkCode)

    if linkEnd:
        molResLink = linkEnd.molResLink
        if molResLink:
            for linkEnd2 in molResLink.molResLinkEnds:
                if linkEnd2 is not linkEnd:
                    residue2 = chain.findFirstResidue(molResidue=linkEnd2.molResidue)

    residue.linkedResidueDict[linkCode] = residue2
    return residue2

def _getNumConnectingBonds(atom1, atom2, limit=5):
    """
    Get the minimum number of binds that connect two atoms.
    Stops at a specified limit (and returns None if not within it)

    .. describe:: Input

    MolSystem.Atom, MolSystem.atom, Int

    .. describe:: Output

    Int
    """

    num = 0
    atoms = set([atom1, ])

    while atom2 not in atoms:
        if num > limit:
            return None

        atoms2 = atoms.copy()

        for atom in atoms2:
            atoms.update(_getBoundAtoms(atom))
        num += 1

    return num


def _getChemAtomNmrRef(project, atomName, ccpCode, molType=PROTEIN_MOLTYPE, sourceName='BMRB'):
    """
    Retrieve an NMR chemical shift reference atom record

    .. describe:: Input

    Implementation.Project, Word (ChemAtom.name), Word (ChemComp.ccpCode),
    Word, (chemComp.molType), Word

    .. describe:: Output

    Float
    """


    # key = '%s:%s:%s:%s' % (atomName, ccpCode, molType, sourceName)
    # if not hasattr(project, 'chemAtomNmrRefDict'):
    #  project.chemAtomNmrRefDict = {}
    # else:

    nmrRefStore = project.findFirstNmrReferenceStore(molType=molType, ccpCode=ccpCode)

    chemAtomNmrRef = None
    if nmrRefStore:
        chemCompNmrRef = nmrRefStore.findFirstChemCompNmrRef(sourceName=sourceName)

        if chemCompNmrRef:
            chemCompVarNmrRef = chemCompNmrRef.findFirstChemCompVarNmrRef(linking='any',
                                                                          descriptor='any')

            if chemCompVarNmrRef:
                for chemAtomNmrRef1 in chemCompVarNmrRef.chemAtomNmrRefs:
                    if atomName == chemAtomNmrRef1.name:
                        chemAtomNmrRef = chemAtomNmrRef1

                        break
            else:
                data = (molType, ccpCode)
                msg = 'Could not load reference NMR data for'
                msg += 'general chem comp variant %s:%s' % data
                print('Warning', msg)
                return

        else:
            data = (molType, ccpCode, sourceName)
            print('Warning',
                        'Could not load reference NMR data for %s:%s source=%s' % data)
            return

    else:
        data = (molType, ccpCode)
        print('Warning',
                    'Could not load reference NMR data for %s:%s' % data)
        return

    if not chemAtomNmrRef:
        atomName2 = atomName[:-1]
        for chemAtomNmrRef1 in chemCompVarNmrRef.chemAtomNmrRefs:
            if atomName2 == chemAtomNmrRef1.name:
                chemAtomNmrRef = chemAtomNmrRef1
                break

    return chemAtomNmrRef

def _getChemicalShiftBounds(chemAtom, threshold=0.001, sourceName='BMRB'):
    """
    Return the min and max chemical shifts for a
    given atom type observed in the databases

    .. describe:: Input

    ChemComp.ChemAtom, Float, Word

    .. describe:: Output

    Float
    """

    key = '%s:%s' % (sourceName, threshold)
    if not hasattr(chemAtom, 'chemicalShiftBounds'):
        chemAtom.chemicalShiftBounds = {}

    else:
        region = chemAtom.chemicalShiftBounds.get(key)
        if region:
            return region

    chemComp = chemAtom.chemComp
    ccpCode = chemComp.ccpCode
    molType = chemComp.molType

    chemAtomNmrRef = _getChemAtomNmrRef(chemAtom.root, chemAtom.name, ccpCode,
                                        molType=molType, sourceName=sourceName)

    if chemAtomNmrRef:
        distribution = chemAtomNmrRef.distribution
        refPoint = chemAtomNmrRef.refPoint
        refValue = chemAtomNmrRef.refValue
        valuePerPoint = chemAtomNmrRef.valuePerPoint
        n = len(distribution)

        minPt = 0
        maxPt = n - 1

        for v in distribution:
            if v < threshold:
                minPt += 1
            else:
                break

        for v in distribution[::-1]:
            if v < threshold:
                maxPt -= 1
            else:
                break

        maxPpm = ((maxPt - refPoint) * valuePerPoint) + refValue
        minPpm = ((minPt - refPoint) * valuePerPoint) + refValue
        region = (minPpm, maxPpm)
        chemAtom.chemicalShiftBounds[key] = region

    return region



def _getRandomCoilShiftCorrectionsDict():
    """

    Citation

    Schwarzinger, S., Kroon, G. J. A., Foss, T. R., Chung, J., Wright, P. E., Dyson, H. J.
    "Sequence-Dependent Correlation of Random Coil NMR Chemical Shifts",
    J. Am. Chem. Soc. 123, 2970-2978 (2001)

    Values obtained from a GGXGG sequence pentapeptide.

    """

    data = """
          Ala    H     H   -0.01  -0.05   0.07  -0.10
          Ala    HA    H   -0.02  -0.03  -0.03   0.00
          Ala    C     C   -0.11  -0.77  -0.07  -0.02
          Ala    CA    C   -0.02  -0.17   0.06   0.01
          Ala    N     N   -0.12  -0.33  -0.57  -0.15
          Asn    H     H   -0.01  -0.03   0.13  -0.07
          Asn    HA    H   -0.01  -0.01  -0.02  -0.01
          Asn    C     C   -0.09  -0.66  -0.10  -0.03
          Asn    CA    C   -0.06  -0.03   0.23   0.01
          Asn    N     N   -0.18  -0.26   0.87  -0.17
          Asp    H     H   -0.02  -0.03   0.14  -0.11
          Asp    HA    H   -0.02  -0.01  -0.02  -0.01
          Asp    C     C   -0.08  -0.58  -0.13  -0.04
          Asp    CA    C   -0.03   0.00   0.25  -0.01
          Asp    N     N   -0.12  -0.20   0.86  -0.29
          Arg    H     H    0.00  -0.02   0.15  -0.06
          Arg    HA    H   -0.02  -0.02  -0.02   0.00
          Arg    C     C   -0.06  -0.49  -0.19  -0.03
          Arg    CA    C    0.00  -0.07  -0.01   0.02
          Arg    N     N   -0.06  -0.14   1.62  -0.06
          Cys    H     H    0.00  -0.02   0.20  -0.07
          Cys    HA    H   -0.01   0.02   0.00   0.00
          Cys    C     C   -0.08  -0.51  -0.28  -0.07
          Cys    CA    C   -0.03  -0.07   0.10  -0.01
          Cys    N     N   -0.06  -0.26   3.07   0.00
          Gln    H     H   -0.01  -0.02   0.15  -0.06
          Gln    HA    H   -0.01  -0.02  -0.01   0.00
          Gln    C     C   -0.05  -0.48  -0.18  -0.03
          Gln    CA    C   -0.02  -0.06   0.04   0.01
          Gln    N     N   -0.06  -0.14   1.62  -0.06
          Glu    H     H   -0.01  -0.03   0.15  -0.07
          Glu    HA    H   -0.02  -0.02  -0.02   0.00
          Glu    C     C   -0.09  -0.48  -0.20  -0.03
          Glu    CA    C   -0.01  -0.08   0.05   0.01
          Glu    N     N   -0.06  -0.20   1.51  -0.12
          Gly    H     H    0.00   0.00   0.00   0.00
          Gly    HA    H    0.00   0.00   0.00   0.00
          Gly    C     C    0.00   0.00   0.00   0.00
          Gly    CA    C    0.00   0.00   0.00   0.00
          Gly    N     N    0.00   0.00   0.00   0.00
          His    H     H   -0.01  -0.04   0.20   0.00
          His    HA    H   -0.03  -0.06   0.01   0.01
          His    C     C   -0.10  -0.65  -0.22  -0.07
          His    CA    C   -0.05  -0.09   0.02   0.01
          His    N     N   -0.12  -0.55   1.68   0.17
          Ile    H     H   -0.01  -0.06   0.17  -0.09
          Ile    HA    H   -0.03  -0.02  -0.02  -0.01
          Ile    C     C   -0.20  -0.58  -0.18  -0.02
          Ile    CA    C   -0.07  -0.20  -0.01   0.02
          Ile    N     N   -0.18  -0.14   4.87   0.00
          Leu    H     H    0.00  -0.03   0.14  -0.08
          Leu    HA    H   -0.04  -0.03  -0.05  -0.01
          Leu    C     C   -0.13  -0.50  -0.13  -0.01
          Leu    CA    C   -0.01  -0.10   0.03   0.02
          Leu    N     N   -0.06  -0.14   1.05  -0.06
          Lys    H     H    0.00  -0.03   0.14  -0.06
          Lys    HA    H   -0.02  -0.02  -0.01   0.00
          Lys    C     C   -0.08  -0.50  -0.18  -0.03
          Lys    CA    C   -0.01  -0.11  -0.02   0.02
          Lys    N     N   -0.06  -0.20   1.57  -0.06
          Met    H     H    0.00  -0.02   0.15  -0.06
          Met    HA    H   -0.02  -0.01  -0.01   0.00
          Met    C     C   -0.08  -0.41  -0.18  -0.02
          Met    CA    C    0.00   0.10  -0.06   0.01
          Met    N     N   -0.06  -0.20   1.57  -0.06
          Phe    H     H   -0.03  -0.12   0.10  -0.37
          Phe    HA    H   -0.06  -0.09  -0.08  -0.04
          Phe    C     C   -0.27  -0.83  -0.25  -0.10
          Phe    CA    C   -0.07  -0.23   0.06   0.01
          Phe    N     N   -0.18  -0.49   2.78  -0.46
          Pro    H     H   -0.04  -0.18   0.19  -0.12
          Pro    HA    H   -0.01   0.11  -0.03  -0.01
          Pro    C     C   -0.47  -2.84  -0.09  -0.02
          Pro    CA    C   -0.22  -2.00   0.02   0.04
          Pro    N     N   -0.18  -0.32   0.87  -0.17
          Ser    H     H    0.00  -0.03   0.16  -0.08
          Ser    HA    H   -0.01   0.02   0.00  -0.01
          Ser    C     C   -0.08  -0.40  -0.15  -0.06
          Ser    CA    C    0.00  -0.08   0.13   0.00
          Ser    N     N   -0.06  -0.03   2.55  -0.17
          Thr    H     H    0.01   0.00   0.14  -0.06
          Thr    HA    H   -0.01   0.05   0.00  -0.01
          Thr    C     C   -0.08  -0.19  -0.13  -0.05
          Thr    CA    C   -0.01  -0.04   0.12   0.00
          Thr    N     N   -0.06  -0.03   2.78  -0.12
          Trp    H     H   -0.08  -0.13   0.04  -0.62
          Trp    HA    H   -0.08  -0.10  -0.15  -0.16
          Trp    C     C   -0.26  -0.85  -0.30  -0.17
          Trp    CA    C   -0.02  -0.17   0.03  -0.08
          Trp    N     N    0.00  -0.26   3.19  -0.64
          Tyr    H     H   -0.04  -0.11   0.09  -0.42
          Tyr    HA    H   -0.05  -0.10  -0.08  -0.04
          Tyr    C     C   -0.28  -0.85  -0.24  -0.13
          Tyr    CA    C   -0.07  -0.22   0.06  -0.01
          Tyr    N     N   -0.24  -0.43   3.01  -0.52
          Val    H     H   -0.01  -0.05   0.17  -0.08
          Val    HA    H   -0.02  -0.01  -0.02  -0.01
          Val    C     C   -0.20  -0.57  -0.18  -0.03
          Val    CA    C   -0.07  -0.21  -0.02   0.01
          Val    N     N   -0.24  -0.14   4.34  -0.06
          """

    rcsDict = {}
    offsets = [-2, -1, 1, 2]
    for o in offsets:
        rcsDict[o] = {}

    lines = data.split('\n')
    for line in lines:
        array = line.split()
        if array:
            tlc = array[0]
            atom = array[1]
            values = [float(v) for v in array[3:]]

            for i in range(4):
                offset = offsets[i]
                if rcsDict[offset].get(tlc) is None:
                    rcsDict[offset][tlc] = {}

                rcsDict[offset][tlc][atom] = values[i]

    return rcsDict


def _getRandomCoilShift(chemAtom, context=None, sourceName='BMRB'):
    """
    Get the random coil chemical shift value of a chemAtom

    .. describe:: Input

    ChemComp.ChemAtom

    .. describe:: Output

    Float
    """

    value = None
    if not hasattr(chemAtom, 'randomCoilShiftDict'):
        chemAtom.randomCoilShiftDict = {}

    elif chemAtom.randomCoilShiftDict.get(sourceName):
        value = chemAtom.randomCoilShiftDict[sourceName]

        if not context:
            return value

    if value is None:
        chemComp = chemAtom.chemComp
        ccpCode = chemComp.ccpCode
        molType = chemComp.molType
        chemAtomNmrRef = _getChemAtomNmrRef(chemAtom.root, chemAtom.name, ccpCode,
                                            molType=molType, sourceName=sourceName)

        if not chemAtomNmrRef and chemAtom.chemAtomSet:
            chemAtomNmrRef = _getChemAtomNmrRef(chemAtom.root, chemAtom.chemAtomSet.name, ccpCode,
                                                molType=molType, sourceName=sourceName)

        if chemAtomNmrRef:
            value = chemAtomNmrRef.randomCoilValue
            if value is None:
                value = chemAtomNmrRef.meanValue

        chemAtom.randomCoilShiftDict[sourceName] = value

    if context and (value is not None):
        correctionDict = _getRandomCoilShiftCorrectionsDict()

        atomName = chemAtom.name

        if atomName in ('HA2', 'HA3'):
            atomName = 'HA'

        offsets = [2, 1, -1, -2]
        indices = [0, 1, 3, 4]

        for i in range(4):
            residue = context[indices[i]]

            if residue is not None:
                ccpCode = residue.ccpCode
                atomDict = correctionDict[offsets[i]].get(ccpCode, {})
                value += atomDict.get(atomName, 0.0)

    return value


def _getResidueObservableAtoms(residue, refExperiment=None, labelling=None,
                               minFraction=0.1, jCouplingBonds=(1, 2, 3),
                               usePermissiveShifts=False,
                               chemElements=('H', 'C', 'N', 'F', 'P')):
    """
    Determine which atoms of a chem comp varient would give rise to
    observable resonances considering a given reference experiment
    and/or an isotope labelling scheme. Can specify minimum fraction of
    an isotope to consider something observable and the chemical elements which
    you are observing. Boolean option to match database min and max
    chemical shift bounds to atom sites, rather than randon coil shift
    values (default).

    .. describe:: Input

    MolSystem.Residue, NmrExpPrototype.RefExperiment,
    ChemCompLabel.LabelingScheme or LabeledMolecule.LabeledMixture,
    Float, Boolean, List of Words

    .. describe:: Output

    List of ChemComp.ChemAtoms
    """

    if not jCouplingBonds:
        jCouplingBonds = (0,)

    atomSiteDict = {}
    isotopomerDict = {}
    atomSitesAll = {}

    if refExperiment:
        for atomSite in refExperiment.nmrExpPrototype.atomSites:
            isotope = atomSite.isotopeCode
            if not atomSitesAll.get(isotope):
                atomSitesAll[isotope] = []

            atomSitesAll[isotope].append(atomSite)

    isotopeDict = {}

    if atomSitesAll:
        isotopes = atomSitesAll.keys()

    else:
        isotopes = []
        for element in chemElements:
            isotope = DEFAULT_ISOTOPES.get(element)

            if isotope:
                isotopes.append(isotope)

    for isotope in isotopes:
        element = isotope

        while element[0] in '0123456789':
            element = element[1:]

        isotopeDict[element] = isotope

    filteredAtoms = []
    prevResidue = _getLinkedResidue(residue, linkCode='prev')
    nextResidue = _getLinkedResidue(residue, linkCode='next')

    natAbundance = residue.root.findFirstLabelingScheme(name='NatAbun')

    # print residue.seqCode, residue.ccpCode, refExperiment.name
    for residue0 in (prevResidue, residue, nextResidue):
        isotopomers = None

        if residue0:
            resId = residue0.molResidue.serial
            atoms = residue0.atoms

            # Compile isotopomers for this residue
            if labelling and (labelling.className == 'LabelingScheme'):
                chemComp = residue0.chemCompVar.chemComp
                ccpCode = chemComp.ccpCode
                molType = chemComp.molType
                chemCompLabel = labelling.findFirstChemCompLabel(ccpCode=ccpCode,
                                                                 molType=molType)

                if not chemCompLabel:
                    chemCompLabel = natAbundance.findFirstChemCompLabel(ccpCode=ccpCode,
                                                                        molType=molType)

                if chemCompLabel:
                    isotopomers = chemCompLabel.isotopomers
                    isotopomerDict[residue0] = isotopomers


        else:
            atoms = []

            # atoms0 = [] # Those which make it through the filter
        for atom in atoms:
            chemAtom = atom.chemAtom
            isotope = isotopeDict.get(chemAtom.elementSymbol)

            if not isotope:
                continue

            if chemAtom.waterExchangeable:
                continue

            if isotopomers:
                fractionDict = _getIsotopomerSingleAtomFractions(isotopomers, atom.name, chemAtom.subType)
                # Exclude if no isotope incorporation above threshold
                fraction = fractionDict.get(isotope, minFraction)
                if fraction < minFraction:
                    continue

            elif labelling:
                fractionDict = _singleAtomFractions(labelling, resId, atom.name)
                if not fractionDict:
                    continue

                fraction = fractionDict.get(isotope, minFraction)
                if fraction < minFraction:
                    continue

            atomSitesIsotope = atomSitesAll.get(isotope)
            if atomSitesIsotope:
                setSize = None

                if usePermissiveShifts:
                    shifts = _getChemicalShiftBounds(chemAtom)
                    if not shifts:
                        shifts = [_getRandomCoilShift(chemAtom), ]

                else:
                    shifts = [_getRandomCoilShift(chemAtom), ]

                for atomSite in atomSitesIsotope:

                    maxShift = atomSite.maxShift
                    if (maxShift is not None) and (shifts[0] > maxShift):
                        continue

                    minShift = atomSite.minShift
                    if (minShift is not None) and (shifts[-1] < minShift):
                        continue

                    if setSize is None:
                        setSize = 1
                        chemAtomSet = chemAtom.chemAtomSet

                        if chemAtomSet:
                            setSize = len(chemAtomSet.chemAtoms)

                    minNumber = atomSite.minNumber
                    if setSize < minNumber:
                        continue

                    maxNumber = atomSite.maxNumber
                    if maxNumber and (setSize > maxNumber):
                        continue

                    numberStep = atomSite.numberStep
                    if (setSize - minNumber) % numberStep != 0:
                        continue

                    if atomSiteDict.get(atomSite) is None:
                        atomSiteDict[atomSite] = []
                    atomSiteDict[atomSite].append(atom)

                    # print 'AS', atomSite.name, atom.name

            filteredAtoms.append(atom)

    if refExperiment:
        # print refExperiment.name

        # Atom sites which are possibly visible given dims
        observableAtomSites = {}
        for refExpDim in refExperiment.refExpDims:
            for refExpDimRef in refExpDim.refExpDimRefs:
                for atomSite in refExpDimRef.expMeasurement.atomSites:
                    observableAtomSites[atomSite] = True

        # Get prototype graph atomSite routes

        graphRoutes = []
        for expGraph in refExperiment.nmrExpPrototype.expGraphs:
            expSteps = [(es.stepNumber, es) for es in expGraph.expSteps]
            expSteps.sort()
            routes = []
            stepNumber, expStep = expSteps[0]

            for atomSite in expStep.expMeasurement.atomSites:
                route = [(atomSite, None, stepNumber)]
                routes.append(route)

            while True:
                routes2 = []

                for route in routes:
                    atomSiteA, null, stepA = route[-1]
                    # print atomSiteA.name, step

                    for expTransfer in atomSiteA.expTransfers:
                        atomSites = list(expTransfer.atomSites)
                        atomSites.remove(atomSiteA)
                        atomSiteB = atomSites[0]

                        if not expTransfer.transferToSelf:
                            if atomSiteB is atomSiteA:
                                continue

                        for stepB, expStepB in expSteps:
                            if stepA > stepB:
                                continue

                            if atomSiteB in expStepB.expMeasurement.atomSites:
                                routes2.append(route[:] + [(atomSiteB, expTransfer, stepB)])
                                # print ['%s %d' % (a[0].name, a[2]) for a in routes2[-1]]
                                break

                if routes2:
                    routes = routes2
                else:
                    break

            for route in routes:
                atomRoutes = []
                lastAtomSite = route[-1][0]

                for i in range(len(route) - 1):
                    atomSiteA, null, stepA = route[i]
                    atomSiteB, expTransfer, stepB = route[i + 1]
                    transferType = expTransfer.transferType

                    # print stepA, atomSiteA.name, stepB, atomSiteB.name, transferType

                    if atomRoutes:
                        atomsA = [r[-1][0] for r in atomRoutes]
                    else:
                        atomsA = atomSiteDict[atomSiteA]

                    atomRoutes2 = []
                    for atomA in atomsA:
                        for atomB in atomSiteDict[atomSiteB]:
                            if isotopomerDict:
                                chemAtomA = atomA.chemAtom
                                chemAtomB = atomB.chemAtom
                                subTypeA = chemAtomA.subType
                                subTypeB = chemAtomB.subType
                                isotopeA = isotopeDict[chemAtomA.elementSymbol]
                                isotopeB = isotopeDict[chemAtomB.elementSymbol]
                                residueA = atomA.residue
                                residueB = atomB.residue

                                if residueA is residueB:
                                    isotopomersA = isotopomerDict.get(residueA)
                                    atomNames = (atomA.name, atomB.name)
                                    subTypes = (subTypeA, subTypeB)
                                    pairDict = _getIsotopomerAtomPairFractions(isotopomersA, atomNames, subTypes)
                                    fraction = pairDict.get((isotopeA, isotopeB), minFraction)

                                    if fraction < minFraction:
                                        continue

                                else:
                                    isotopomersA = isotopomerDict.get(residueA)
                                    isotopomersB = isotopomerDict.get(residueB)

                                    if isotopomersB and isotopomersA:
                                        fractionDictA = _getIsotopomerSingleAtomFractions(isotopomersA, atomA.name,
                                                                                          subTypeA)
                                        fractionDictB = _getIsotopomerSingleAtomFractions(isotopomersB, atomB.name,
                                                                                          subTypeB)
                                        fraction = fractionDictA.get(isotopeA, 1.0) * fractionDictB.get(isotopeB, 1.0)

                                        if fraction < minFraction:
                                            continue

                            elif labelling:
                                chemAtomA = atomA.chemAtom
                                chemAtomB = atomB.chemAtom
                                isotopeA = isotopeDict[chemAtomA.elementSymbol]
                                isotopeB = isotopeDict[chemAtomB.elementSymbol]
                                residueA = atomA.residue
                                residueB = atomB.residue
                                molResidueA = residueA.molResidue
                                molResidueB = residueB.molResidue
                                resIds = (molResidueA.serial, molResidueB.serial)
                                atomNames = (atomA.name, atomB.name)

                                pairDict = _atomPairFractions(labelling, resIds, atomNames)
                                fraction = pairDict.get((isotopeA, isotopeB), minFraction)

                                if fraction < minFraction:
                                    continue

                            addAtom = False
                            if transferType in longRangeTransfers:
                                addAtom = True

                            elif transferType in ('onebond', 'CP') and _areAtomsBound(atomA, atomB):
                                addAtom = True

                            elif transferType == 'TOCSY' and _areAtomsTocsyLinked(atomA, atomB):
                                addAtom = True

                            elif transferType == 'Jcoupling':
                                numBonds = _getNumConnectingBonds(atomA, atomB, limit=max(jCouplingBonds))
                                if numBonds in jCouplingBonds:
                                    addAtom = True

                            elif transferType == 'Jmultibond' and not _areAtomsBound(atomA, atomB):
                                numBonds = _getNumConnectingBonds(atomA, atomB, limit=max(jCouplingBonds))
                                if numBonds in jCouplingBonds:
                                    addAtom = True

                            if addAtom:
                                grown = True
                                # print 'AB', atomA.name, atomA.residue.seqCode,'+', atomB.name, atomB.residue.seqCode
                                if not atomRoutes:
                                    atomRoutes2.append([(atomA, atomSiteA), (atomB, atomSiteB), ])
                                    # print atomA.name, atomB.name

                                else:
                                    for atomRoute in atomRoutes:
                                        atomRoutes2.append(atomRoute[:] + [(atomB, atomSiteB), ])
                                    # print '+', atomB.name

                    atomRoutes = []
                    for atomRoute in atomRoutes2:
                        if atomRoute[-1][1] is lastAtomSite:
                            atomRoutes.append(atomRoute)

                graphRoutes.append(atomRoutes)

        observableAtoms = set()
        for routes in graphRoutes:
            for route in routes:

                for atomB, atomSiteB in route:
                    if atomB.residue is residue:  # Must have one atom from this residue
                        for atomA, atomSiteA in route:
                            if observableAtomSites.get(atomSiteA):
                                observableAtoms.add(atomA)
                        break

    else:
        observableAtoms = filteredAtoms

    return list(observableAtoms)

def makePeakListFromShifts(spectrum, chemicalShiftList, useUnassigned=True, chain=None, bondLimit=6,
                           residueLimit=1, labelling=None, labellingThreshold=0.1):
    """
    This routine has been ported from Version 2.4 (.python.ccpnmr.analysis.core.PeakBasic.makePeakListFromShifts)
    
    Make an artificial peak list using shift intersections from a shift list
    Boolean option to consider only shifts with atom assigned resonances. Option
    to filter on a specific molSystem. Option to limit through-space transfers to a
    limited number of bonds and a given residue range.
    Optional labelling scheme/mixture and threshold to filter according to isotopomers.

    """
    apiSpectrum = spectrum._wrappedData
    shiftList = chemicalShiftList._wrappedData
    molSystem = None
    if chain:
        molSystem = chain._wrappedData

    if not (shiftList and apiSpectrum):
        return

    peakList = None
    experiment = apiSpectrum.experiment
    refExperiment = experiment.refExperiment
    refType = refExperiment.name
    observableAtoms = {}
    if labelling is True:
        labelling = apiSpectrum.experiment

        if labelling.labeledMixtures:
            getLabelAtomFractions = _getExperimentAtomFractions
            getLabelAtomPairFractions = _getExperimentAtomPairFractions
        else:
            labelling = None

    elif labelling and labelling.className == 'LabelingScheme':
        getLabelAtomFractions = _getSchemeAtomFractions
        getLabelAtomPairFractions = _getSchemeAtomPairFractions

    N = apiSpectrum.numDim
    isotopes = []
    fullRegion = []
    transferDims = {}

    atomSiteDims = {}
    dimAtomSites = []

    for dim, dataDim in enumerate(apiSpectrum.sortedDataDims()):
        atomSites = set()
        expDim = dataDim.expDim
        for expDimRef in expDim.expDimRefs:
            if not expDimRef.refExpDimRef:
                continue

            measurement = expDimRef.refExpDimRef.expMeasurement
            for atomSite in measurement.atomSites:
                if atomSite not in atomSiteDims:
                    atomSiteDims[atomSite] = []

                atomSiteDims[atomSite].append(dim)
                atomSites.add(atomSite)

        dimAtomSites.append(atomSites)

    for dim, dataDim in enumerate(apiSpectrum.sortedDataDims()):

        dataDimRef = _getPrimaryDataDimRef(dataDim)
        expDimRef = dataDimRef.expDimRef
        fullRange = _getDataDimRefFullRange(dataDimRef)
        fullRegion.append(fullRange)
        isotopes.append(list(expDimRef.isotopeCodes))
        expTransfers = expDimRef.expTransfers

        if expTransfers:
            for expTransfer in expTransfers:
                transferType = expTransfer.transferType
                expDimRefs2 = list(expTransfer.expDimRefs)
                expDimRefs2.remove(expDimRef)
                dim2 = expDimRefs2[0].expDim.dim - 1
                transferDims[frozenset([dim, dim2])] = transferType

        else:
            refExpDimRef = expDimRef.refExpDimRef

            expDimRef2 = None
            atomSites2 = set()
            for atomSite in refExpDimRef.expMeasurement.atomSites:
                for expTransfer in atomSite.expTransfers:
                    if expTransfer.transferType not in ('onebond', 'Jcoupling'):
                        continue

                    atomSites2.update(expTransfer.atomSites)

            for atomSite in atomSites2:
                if atomSite in atomSiteDims:
                    continue

                for expTransfer in atomSite.expTransfers:
                    if expTransfer.transferType not in ('onebond', 'Jcoupling'):
                        continue

                    for atomSite2 in expTransfer.atomSites:
                        if atomSite2 not in atomSiteDims:
                            continue

                        for dim2 in atomSiteDims[atomSite2]:
                            if dim2 == dim:
                                continue

                            transferDims[frozenset([dim, dim2])] = 'twostep'

    dims = range(N)
    dimResonances = []
    for i in dims:
        dimResonances.append([])

    measurements = shiftList.measurements
    minDimShifts = []
    maxDimShifts = []
    for i in dims:
        minShifts = [aSite.minShift for aSite in dimAtomSites[i]]
        maxShifts = [aSite.maxShift for aSite in dimAtomSites[i]]

        if minShifts:
            minDimShifts.append(min(minShifts))
        else:
            minDimShifts.append(None)

        if maxShifts:
            maxDimShifts.append(max(maxShifts))
        else:
            maxDimShifts.append(None)

    for j, shift in enumerate(measurements):

        ppm = shift.value
        resonance = shift.resonance
        isotopeCode = resonance.isotopeCode

        atoms = []
        resonanceSet = resonance.resonanceSet

        if resonanceSet:
            for atomSet in resonanceSet.atomSets:
                if labelling:
                    for atom in atomSet.atoms:
                        frac = getLabelAtomFractions(labelling, atom).get(resonance.isotopeCode)

                        if frac > labellingThreshold:
                            atoms.append(atom)
                else:
                    atoms.extend(atomSet.atoms)

        elif not useUnassigned:
            continue

        if molSystem:
            if atoms:
                molSystem2 = atoms[0].topObject
                if molSystem2 is not molSystem:
                    continue

            else:
                continue

        if labelling and not atoms:
            continue

        for i in dims:
            if isotopeCode in isotopes[i]:
                if (ppm > fullRegion[i][0]) and (ppm < fullRegion[i][1]):
                    if (minDimShifts[i] is not None) and (ppm < minDimShifts[i]):
                        continue

                    if (maxDimShifts[i] is not None) and (ppm > maxDimShifts[i]):
                        continue

                    if useUnassigned or resonanceSet:
                        if atoms:
                            name = atoms[0].name

                        dimResonances[i].append((resonance, frozenset(atoms)))

    correlations = {}
    for pair in transferDims:
        dimA, dimB = pair
        transferType = transferDims[pair]

        usedA = set()
        usedB = set()
        for resonanceA, atomsA in dimResonances[dimA]:
            keyA = (dimA, resonanceA)

            for resonanceB, atomsB in dimResonances[dimB]:
                keyB = (dimB, resonanceB)
                correlate = False

                if (transferType == 'onebond') and _areResonancesBound(resonanceA, resonanceB):
                    if labelling:
                        if atomsA and atomsB:
                            isotopes = (resonanceA.isotopeCode, resonanceB.isotopeCode)

                            atomPairs = []
                            for atomA in atomsA:
                                for atomB in atomsB:
                                    atomPairs.append((atomA, atomB))

                            for atomA, atomB in atomPairs:
                                fracDict = getLabelAtomPairFractions(labelling, atomA, atomB)
                                frac = fracDict.get(isotopes)

                                if (frac is not None) and (frac >= labellingThreshold):
                                    break

                            else:
                                # No labelled possibility; skip
                                continue

                        else:
                            # No possible pairs; skip
                            continue

                    correlate = True

                for atomB in atomsB:
                    for atomA in atomsA:
                        if labelling:
                            isotopes = (resonanceA.isotopeCode, resonanceB.isotopeCode)
                            fracDict = getLabelAtomPairFractions(labelling, atomA, atomB)
                            frac = fracDict.get(isotopes)

                            if (frac is None) or (frac < labellingThreshold):
                                continue

                        if transferType == 'relayed':
                            if _areAtomsTocsyLinked(atomA, atomB):
                                correlate = True
                                break

                        elif transferType in longRangeTransfers:

                            if atomB is atomA:
                                # Not diagonal
                                break

                            if atomA.residue is atomB.residue:
                                if bondLimit:
                                    numBonds = _getNumConnectingBonds(atomA, atomB)
                                    if numBonds and (numBonds <= bondLimit):
                                        correlate = True
                                        break

                                else:
                                    correlate = True
                                    break

                            elif residueLimit:
                                prevA = _getLinkedResidue(atomA.residue, linkCode='prev')
                                prevB = _getLinkedResidue(atomB.residue, linkCode='prev')
                                if (prevA and (atomB.residue is prevA)) or \
                                        (prevB and (atomA.residue is prevB)):
                                    if bondLimit:
                                        numBonds = _getNumConnectingBonds(atomA, atomB)
                                        if numBonds and (numBonds <= bondLimit):
                                            correlate = True
                                            break

                                    else:
                                        correlate = True
                                        break

                                if residueLimit == 2:
                                    if prevA:
                                        prevA2 = _getLinkedResidue(prevA, linkCode='prev')
                                    else:
                                        prevA2 = None

                                    if prevB:
                                        prevB2 = _getLinkedResidue(prevB, linkCode='prev')
                                    else:
                                        prevB2 = None

                                    if (prevA2 and (atomB.residue is prevA2)) or \
                                            (prevB2 and (atomA.residue is prevB2)):
                                        if bondLimit:
                                            numBonds = _getNumConnectingBonds(atomA, atomB)
                                            if numBonds and (numBonds <= bondLimit):
                                                correlate = True
                                                break
                                        else:
                                            correlate = True
                                            break


                        elif transferType == 'twostep':
                            if refType in ('H[N[co[CA]]]', 'H[N[co[{CA|ca[C]}]]]'):

                                if refType == 'H[N[co[CA]]]':
                                    atomNames = ('CA',)
                                else:
                                    atomNames = ('CA', 'CB',)

                                if (atomB.name in atomNames) and (atomA.name == 'N'):
                                    prev = _getLinkedResidue(atomA.residue, linkCode='prev')
                                    if prev and (atomB.residue is prev):
                                        correlate = True
                                        break

                                elif (atomA.name in atomNames) and (atomB.name == 'N'):
                                    prev = _getLinkedResidue(atomB.residue, linkCode='prev')
                                    if prev and (atomA.residue is prev):
                                        correlate = True
                                        break

                            elif refType == 'H[N[ca[CO]]]':
                                atomNames = ('C',)

                                if (atomB.name in atomNames) and (atomA.name == 'N'):
                                    if atomB.residue is atomA.residue:
                                        correlate = True
                                        break

                                    prev = _getLinkedResidue(atomA.residue, linkCode='prev')
                                    if prev and (atomB.residue is prev):
                                        correlate = True
                                        break

                                elif (atomA.name in atomNames) and (atomB.name == 'N'):
                                    if atomB.residue is atomA.residue:
                                        correlate = True
                                        break

                                    prev = _getLinkedResidue(atomB.residue, linkCode='prev')
                                    if prev and (atomA.residue is prev):
                                        correlate = True
                                        break

                        elif transferType in ('Jcoupling', 'Jmultibond'):
                            if refType in ('H[N[{CA|ca[Cali]}]]',
                                           'h{CA|Cca}NH', 'H[N[CA]]'):

                                if refType == 'H[N[CA]]':
                                    atomNames = ('CA',)
                                else:
                                    atomNames = ('CA', 'CB',)

                                if (atomB.name in atomNames) and (atomA.name == 'N'):
                                    if atomB.residue is atomA.residue:
                                        correlate = True
                                        break

                                    prev = _getLinkedResidue(atomA.residue, linkCode='prev')
                                    if prev and (atomB.residue is prev):
                                        correlate = True
                                        break

                                elif (atomA.name in atomNames) and (atomB.name == 'N'):
                                    if atomB.residue is atomA.residue:
                                        correlate = True
                                        break

                                    prev = _getLinkedResidue(atomB.residue, linkCode='prev')
                                    if prev and (atomA.residue is prev):
                                        correlate = True
                                        break


                            elif refType in ('H{[N]+[HA]}', 'H[N[ca[HA]]]'):
                                if atomB.name in ('HA', 'HA2', 'HA3') and (atomA.name == 'H'):
                                    if atomB.residue is atomA.residue:
                                        correlate = True
                                        break

                                if atomA.name in ('HA', 'HA2', 'HA3') and (atomB.name == 'H'):
                                    if atomB.residue is atomA.residue:
                                        correlate = True
                                        break

                            else:
                                residue = atomA.residue
                                observable = observableAtoms.get(residue)
                                if observable is None:
                                    observable = _getResidueObservableAtoms(residue,
                                                                            refExperiment)
                                    observableAtoms[residue] = observable

                                if atomB in observable:
                                    correlate = True
                                    break

                    else:
                        continue
                    break

                if correlate:
                    usedA.add((resonanceA, atomsA))
                    usedB.add((resonanceB, atomsB))

                    if keyA in correlations:
                        correlations[keyA].append(keyB)
                    else:
                        correlations[keyA] = [keyB]

                    if keyB in correlations:
                        correlations[keyB].append(keyA)
                    else:
                        correlations[keyB] = [keyA]

        dimResonances[dimA] = usedA
        dimResonances[dimB] = usedB

    stack = [set([key, ]) for key in correlations if key[0] == 0]
    intersections = set()

    while stack:
        intersection = stack.pop()
        dimNums = set([x[0] for x in intersection])

        for keyA in intersection:
            for keyB in correlations[keyA]:
                if keyB in intersection:
                    continue

                if keyB[0] in dimNums:
                    continue

                intersection2 = set(intersection)
                intersection2.add(keyB)

                if len(intersection2) == N:
                    intersections.add(frozenset(intersection2))

                else:
                    stack.append(intersection2)

    if intersections:
        I = len(intersections)
        peakList = spectrum.newPeakList(isSimulated=True)
        peakList.details = 'Synthetic peak list made with shift list "%s"' % shiftList.name

        unit = shiftList.unit
        for intersection in intersections:
            resonances = list(intersection)
            resonances.sort()
            resonances = [x[1] for x in resonances]

            position = []
            figOfMerit = 1.0
            for resonance in resonances:
                shift = resonance.findFirstShift(parentList=shiftList)
                figOfMerit *= shift.figOfMerit
                position.append(shift.value)

            peak = peakList.newPeak(position)
            apiPeak = peak._wrappedData
            peakDims = apiPeak.sortedPeakDims()

            for dim, res in enumerate(resonances):
                atom = peak.project._data2Obj[res]
                axisCode = spectrum.axisCodes[dim]
                peak.assignDimension(axisCode=axisCode, value=[atom])

    else:
        msg = 'Experiment type not supported or '
        msg += 'cannot find resonance intersections to make any peaks'
        print('Failure', msg)

    return peakList


# Move this to the spectrum core class or anyother more direct object ....:
def newPeakListFromChemicalShiftList(self, chemicalShiftList, useUnassigned=True, chain=None,
                                              bondLimit=6, residueLimit=1):
    # from ccpn.core.lib.ChemicalShiftListLib import makePeakListFromShifts
    # As now to get this working we need to set AtomAndResonanceSets: _newAtomAndResonanceSets
    # needs to have a nmrChain assigned to a chain
    with undoBlock():
        with notificationEchoBlocking():
            peakList = makePeakListFromShifts(self, chemicalShiftList,
                                              useUnassigned=useUnassigned, chain=chain,
                                              bondLimit=bondLimit, residueLimit=residueLimit)
            return peakList


