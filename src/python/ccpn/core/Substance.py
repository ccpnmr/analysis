"""
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
__dateModified__ = "$dateModified: 2021-04-07 16:22:20 +0100 (Wed, April 07, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
import typing

from ccpn.util import Common as commonUtil
from ccpn.core.Project import Project
from ccpn.core.Sample import Sample
from ccpn.core.SampleComponent import SampleComponent
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.util.Constants import DEFAULT_LABELLING
from ccpnmodel.ccpncore.api.ccp.lims.RefSampleComponent import AbstractComponent as ApiRefComponent
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.lib import Util as coreUtil
from ccpnmodel.ccpncore.lib.molecule import MoleculeModify
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, renameObject, undoBlock
from ccpn.util.Logging import getLogger
from contextlib import contextmanager


_apiClassNameMap = {
    'MolComponent': 'Molecule',
    'Substance'   : 'Material'
    }


class Substance(AbstractWrapperObject):
    """A Substance is a chemical entity or material that can be added to a Sample.
    Substances are defined by their name and labelling attributes (labelling defaults to None).
    Renaming a Substance will also rename all SampleComponents and SpectrumHits associated with
    it, so as to preserve the link between the objects.

    The most common case (by far) is substanceType 'Molecule', which corresponds to a chemical entity,
    such as Calmodulin, ATP, or NaCl. This type of Substance will have Smiles strings, sequence,
    and other molecular attributes as appropriate. Such a Substance may be associated with one
    or more Chains, and can be used as a starting point to generate new Chains, using the
    Project.createPolymerSubstance() function.

    ADVANCED: It is also possible to create Substances with substanceType 'Material' or 'Cell'.
    Materials are used to describe chemical mixtures, such as fetal calf serum, algal lysate, or
    'standard experiment buffer number 3'.
     """

    #: Short class name, for PID.
    shortClassName = 'SU'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Substance'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'substances'

    # the attribute name used by current
    _currentAttributeName = 'substances'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiRefComponent._metaclass.qualifiedName()

    # CCPN internal
    _linkedSpectraPids = '_linkedSpectraPids'

    # CCPN properties
    @property
    def _apiSubstance(self) -> ApiRefComponent:
        """ API RefSampleComponent matching Substance"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - name.labelling"""
        obj = self._wrappedData

        name = obj.name
        labelling = obj.labeling
        if labelling == DEFAULT_LABELLING:
            labelling = ''
        return Pid.createId(name, labelling)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        obj = self._wrappedData
        labelling = obj.labeling
        return (obj.name, '' if labelling == DEFAULT_LABELLING else labelling)

    @property
    def name(self) -> str:
        """name of Substance"""
        return self._wrappedData.name

    @property
    def labelling(self) -> str:
        """labelling descriptor of Substance (default is 'std')"""
        result = self._wrappedData.labeling
        if result == DEFAULT_LABELLING:
            result = None
        #
        return result

    @property
    def _parent(self) -> Sample:
        """Project containing Substance."""
        return self._project

    @property
    def substanceType(self) -> str:
        """Category of substance: Molecule, Cell, Material, or Composite

        - Molecule is a single molecule, including plasmids

        - Cell is a cell,

        - Material is a mixture, like fetal calf serum, growth medium, or standard buffer,

        - Composite is multiple components in fixed ratio, like a protein-ligand or multiprotein
          complex, or (technically) a Cell containing a particular plasmid.

        """
        result = self._wrappedData.className
        return _apiClassNameMap.get(result, result)

    @property
    def synonyms(self) -> typing.Tuple[str, ...]:
        """Synonyms for Substance name"""
        return self._wrappedData.synonyms

    @synonyms.setter
    def synonyms(self, value):
        """Synonyms for Substance name"""
        self._wrappedData.synonyms = value

    @property
    def userCode(self) -> typing.Optional[str]:
        """User-defined compound code"""
        return self._wrappedData.userCode

    @userCode.setter
    def userCode(self, value: str):
        self._wrappedData.userCode = value

    @property
    def smiles(self) -> typing.Optional[str]:
        """Smiles string - for substances that have one"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.smiles if hasattr(apiRefComponent, 'smiles') else None

    @smiles.setter
    def smiles(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'smiles'):
            apiRefComponent.smiles = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'smiles'" % _apiClassNameMap.get(ss, ss))

    @property
    def inChi(self) -> typing.Optional[str]:
        """inChi string - for substances that have one"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.inChi if hasattr(apiRefComponent, 'inChi') else None

    @inChi.setter
    def inChi(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'inChi'):
            apiRefComponent.inChi = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'inChi'" % _apiClassNameMap.get(ss, ss))

    @property
    def casNumber(self) -> typing.Optional[str]:
        """CAS number string - for substances that have one"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.casNum if hasattr(apiRefComponent, 'casNum') else None

    @casNumber.setter
    def casNumber(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'casNum'):
            apiRefComponent.casNum = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'casNumber'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def empiricalFormula(self) -> typing.Optional[str]:
        """Empirical molecular formula string - for substances that have one"""
        apiRefComponent = self._wrappedData
        return (apiRefComponent.empiricalFormula if hasattr(apiRefComponent, 'empiricalFormula')
                else None)

    @empiricalFormula.setter
    def empiricalFormula(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'empiricalFormula'):
            apiRefComponent.empiricalFormula = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'empiricalFormula'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def sequenceString(self) -> typing.Optional[str]:
        """Molecular sequence string - set by the createPolymerSubstance function. Substances
        created by this function can be used to generate matching chains with the
        substance.createChain function

        For standard polymers defaults to a string of one-letter codes;
        for other molecules to a comma-separated tuple of three-letter codes"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.seqString if hasattr(apiRefComponent, 'seqString') else None

    @sequenceString.setter
    def sequenceString(self, value):
        self._wrappedData.seqString = value

    @property
    def molecularMass(self) -> typing.Optional[float]:
        """Molecular mass - for substances that have one"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.molecularMass if hasattr(apiRefComponent, 'molecularMass') else None

    @molecularMass.setter
    def molecularMass(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'molecularMass'):
            apiRefComponent.molecularMass = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'molecularMass'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def atomCount(self) -> int:
        """Number of atoms in the molecule - for Molecular substances"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.atomCount if hasattr(apiRefComponent, 'atomCount') else None

    @atomCount.setter
    def atomCount(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'atomCount'):
            apiRefComponent.atomCount = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'atomCount'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def bondCount(self) -> int:
        """Number of bonds in the molecule - for Molecular substances"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.bondCount if hasattr(apiRefComponent, 'bondCount') else None

    @bondCount.setter
    def bondCount(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'bondCount'):
            apiRefComponent.bondCount = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'bondCount'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def ringCount(self) -> int:
        """Number of rings in the molecule - for Molecular substances"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.ringCount if hasattr(apiRefComponent, 'ringCount') else None

    @ringCount.setter
    def ringCount(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'ringCount'):
            apiRefComponent.ringCount = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'ringCount'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def hBondDonorCount(self) -> int:
        """Number of hydrogen bond donors in the molecule - for Molecular substances"""
        apiRefComponent = self._wrappedData
        return apiRefComponent.hBondDonorCount if hasattr(apiRefComponent, 'hBondDonorCount') else None

    @hBondDonorCount.setter
    def hBondDonorCount(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'hBondDonorCount'):
            apiRefComponent.hBondDonorCount = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'hBondDonorCount'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def hBondAcceptorCount(self) -> int:
        """Number of hydrogen bond acceptors in the molecule - for Molecular substances"""
        apiRefComponent = self._wrappedData
        return (apiRefComponent.hBondAcceptorCount if hasattr(apiRefComponent, 'hBondAcceptorCount')
                else None)

    @hBondAcceptorCount.setter
    def hBondAcceptorCount(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'hBondAcceptorCount'):
            apiRefComponent.hBondAcceptorCount = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'hBondAcceptorCount'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def polarSurfaceArea(self) -> typing.Optional[float]:
        """Polar surface area (in square Angstrom) of the molecule - for Molecular substances"""
        apiRefComponent = self._wrappedData
        return (apiRefComponent.polarSurfaceArea if hasattr(apiRefComponent, 'polarSurfaceArea')
                else None)

    @polarSurfaceArea.setter
    def polarSurfaceArea(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'polarSurfaceArea'):
            apiRefComponent.polarSurfaceArea = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'polarSurfaceArea'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def logPartitionCoefficient(self) -> typing.Optional[float]:
        """Logarithm of the octanol-water partition coefficient (logP) - for Molecular substances"""
        apiRefComponent = self._wrappedData
        return (apiRefComponent.logPartitionCoefficient
                if hasattr(apiRefComponent, 'logPartitionCoefficient') else None)

    @logPartitionCoefficient.setter
    def logPartitionCoefficient(self, value):
        apiRefComponent = self._wrappedData
        if hasattr(apiRefComponent, 'logPartitionCoefficient'):
            apiRefComponent.logPartitionCoefficient = value
        else:
            ss = apiRefComponent.className
            raise TypeError("%s type Substance has no attribute 'logPartitionCoefficient'"
                            % _apiClassNameMap.get(ss, ss))

    @property
    def specificAtomLabelling(self) -> typing.Dict[str, typing.Dict[str, float]]:
        """Site-specific labelling for all chains matching Substance
        in the form of (atomId:{isotopeCode:fraction}} dictionary.
        Note that changing the labelling for a site in one chain
        simultaneously affects the matching site in other matching chains.
        To modify this attribute use the functions setSpecificAtomLabelling,
        removeSpecificAtomLabelling, clearSpecificAtomLabelling,
        updateSpecificAtomLabelling

        Example value (for two chains where the numbering of B is offset 200 from chain A):

          | {'A.11.ALA.CB':{'12C':0.32, '13C':0.68},
          | 'B.211.ALA.CB':{'12C':0.32, '13C':0.68},}"""

        result = {}
        dd = self._ccpnInternalData.get('_specificAtomLabelling')
        if dd:
            for chain in self.chains:
                # NBNB this relies on residues being sorted by seqId, and so being
                # in sequence order
                residues = chain.residues
                for tt, labellingDict in dd.items():
                    residueIndex, atomName = tt
                    residue = residues[residueIndex]
                    atom = residue.getAtom(atomName)
                    result[atom._id] = labellingDict.copy()
        #
        return result

    def setSpecificAtomLabelling(self, atom: typing.Union[str, 'Atom'], isotopeLabels: dict):
        """Set isotopeLabels dict as labelling for atom designated by atomId.

        NBNB labelling is set for the matching atom in all chains that match the Substance
        also if the other chains have a different numbering.

        isotopeLabels must be a dictionary of the form (e.g.) {'12C':0.32, '13C':0.68}
        where the atom fractions add up to 1.0 and the isotope Codes cover the possibilities
        for the atom."""

        if isinstance(atom, str):
            # Get Atom from id or Pid
            ll = atom.split(Pid.PREFIXSEP, 1)
            atom = self._project.getAtom(ll[-1])
        if atom is None:
            raise ValueError("Atom with ID %s does not exist" % atom)

        if atom.residue.chain not in self.chains:
            raise ValueError("%s and its chain do not match the Substance" % atom.longPid)

        dd = self._ccpnInternalData.get('_specificAtomLabelling')

        if dd is None:
            dd = self._ccpnInternalData['_specificAtomLabelling'] = {}
        residue = atom.residue
        residueIndex = residue.chain.residues.index(residue)
        dd[(residueIndex, atom.name)] = isotopeLabels

    def removeSpecificAtomLabelling(self, atom: typing.Union[str, 'Atom']):
        """Remove specificAtomLabelling for atom designated by atomId

        NBNB labelling is removed for the matching atom in all chains that match the Substance
        also if the other chains have a different numbering."""

        if isinstance(atom, str):
            # Get Atom from id or Pid
            ll = atom.split(Pid.PREFIXSEP, 1)
            atom = self._project.getAtom(ll[-1])
        if atom is None:
            raise ValueError("Atom with ID %s does not exist" % atom)

        if atom.residue.chain not in self.chains:
            raise ValueError("%s and its chain do not match the Substance" % atom.longPid)

        dd = self._ccpnInternalData.get('_specificAtomLabelling')

        if dd is None:
            raise ValueError("Cannot remove - no atom labelling data present.")

        # if dd:
        residue = atom.residue
        residueIndex = residue.chain.residues.index(residue)
        tt = (residueIndex, atom.name)
        if tt in dd:
            del dd[(residueIndex, atom.name)]
        else:
            raise ValueError("Cannot remove - no atom labelling data for %s." % atom.longPid)

    def getSpecificAtomLabelling(self, atom: typing.Union[str, 'Atom']) -> typing.Dict[str, float]:
        """Get specificAtomLabelling dictionary for atom.
        atom may be an Atom object, an atomId or an atom Pid

        returns dictionary of the form e.g.
        {'12C':0.32, '13C':0.68}"""

        if isinstance(atom, str):
            # Get Atom from id or Pid
            ll = atom.split(Pid.PREFIXSEP, 1)
            atom = self._project.getAtom(ll[-1])
        if atom is None:
            raise ValueError("Atom with ID %s does not exist" % atom)

        if atom.residue.chain not in self.chains:
            raise ValueError("Atom %s and its chain do not match the Substance" % atom)

        dd = self._ccpnInternalData.get('_specificAtomLabelling')
        if dd:
            residue = atom.residue
            residueIndex = residue.chain.residues.index(residue)
            return dd.get((residueIndex, atom.name))

    def clearSpecificAtomLabelling(self):
        """Clear specificAtomLabelling"""
        self._ccpnInternalData['_specificAtomLabelling'] = {}

    def updateSpecificAtomLabelling(self, dictionary: typing.Dict[str, typing.Dict[str, float]]):
        """Update Site-specific labelling for all chains matching Substance.
        The input must be an (atomId:{isotopeCode:fraction}} dictionary.
        Note that changing the labelling for a site in one chain
        simultaneously affects the matching site in other matching chains,
        So you should only update teh labeling for one chain.

        Example value (for two chains where the numbering of B is offset 200 from chain A):

          {'A.11.ALA.CB':{'12C':0.32, '13C':0.68},}

          which will also affect 'B.211.ALA.CB' (if it exists)"""

        for atomId, dd in dictionary.items():
            self.setSpecificAtomLabelling(atomId, dd)

    def _getChemComps(self):
        """
        CCPN internal
        :param substance:
        :return: a ChemComp Obj if available
        """
        chemComps = []
        molecule = self._wrappedData.getMolecule()
        if molecule:
            for molResidue in molecule.findAllMolResidues():
                if molResidue.chemComp:
                    chemComps.append(molResidue.chemComp)
        return chemComps

    @property
    def sampleComponents(self) -> typing.Tuple[SampleComponent, ...]:
        """SampleComponents that correspond to Substance"""
        relativeId = self._key
        return tuple(x for x in self._project.sampleComponents if x._key == relativeId)

        # name = self.name
        # apiLabeling = self.labelling
        # if apiLabeling is None:
        #   apiLabeling = DEFAULT_LABELLING
        # apiSampleStore = self._project._apiNmrProject.sampleStore
        # data2Obj = self._project._data2Obj
        # return tuple(data2Obj[x]
        #              for y in apiSampleStore.sortedSamples()
        #              for x in y.sortedSampleComponents()
        #              if x.name == name and x.labeling == apiLabeling)

    @property
    def referenceSpectra(self) -> typing.Tuple[Spectrum, ...]:
        """Reference Spectra acquired for Substance"""
        _referenceSpectra = []
        for spectum in self.project.spectra:
            if self in spectum.referenceSubstances:
                _referenceSpectra.append(spectum)
        return tuple(_referenceSpectra)

    @referenceSpectra.setter
    def referenceSpectra(self, spectra):

        for spectrum in spectra:
            spectrum.referenceSubstances = [self]

    @property
    def _molecule(self):
        """Get the attached molecule
        """
        return self._wrappedData.molecule

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (SampleComponent) for all SampleComponent children of parent Sample"""
        componentStore = parent._wrappedData.sampleStore.refSampleComponentStore
        if componentStore is None:
            return []
        else:
            return componentStore.sortedComponents()

    def _finaliseAction(self, action: str):
        """Subclassed to notify changes to associated integralListViews
        """
        if not super()._finaliseAction(action):
            return

        try:
            if action in ['rename']:
                for sampleComponent in self.sampleComponents:
                    for spectrumHit in sampleComponent.spectrumHits:
                        spectrumHit._finaliseAction(action)
                    sampleComponent._finaliseAction(action)

        except Exception as es:
            raise RuntimeError('Error _finalising Substance.spectrumHits: %s' % str(es))

    @renameObject()
    @logCommand(get='self')
    def rename(self, name: str = None, labelling: str = None):
        """Rename Substance, changing its name and/or labelling and Pid, and rename
        SampleComponents and SpectrumHits with matching names. If name is None, the existing value
        will be used. Labelling 'None'  means 'Natural abundance'"""

        # ejb - name should always be passed in, strange not to
        if name is None:
            name = self.name
        oldName = self.name
        name = self._uniqueName(project=self.project, name=name)

        oldLabelling = self.labelling
        apiLabeling = labelling = labelling or DEFAULT_LABELLING
        self._validateStringValue(attribName='labelling', value=labelling, allowNone=True)

        apiNmrProject = self.project._wrappedData
        _molComponent = apiNmrProject.sampleStore.refSampleComponentStore.findFirstComponent(name=name, labeling=apiLabeling)
        if _molComponent is not None and _molComponent != self._wrappedData:
            raise ValueError("%s.%s already exists" % (name, labelling if labelling != DEFAULT_LABELLING else ''))

        # rename functions from here
        for sampleComponent in self.sampleComponents:
            for spectrumHit in sampleComponent.spectrumHits:
                coreUtil._resetParentLink(spectrumHit._wrappedData, 'spectrumHits',
                                          OrderedDict((('substanceName', name),
                                                       ('sampledDimension', spectrumHit.pseudoDimensionNumber),
                                                       ('sampledPoint', spectrumHit.pointNumber)))
                                          )
                # renamedObjects.append(spectrumHit)

            # NB this must be done AFTER the spectrumHit loop to avoid breaking links
            coreUtil._resetParentLink(sampleComponent._wrappedData, 'sampleComponents',
                                      OrderedDict((('name', name), ('labeling', apiLabeling)))
                                      )
            # renamedObjects.append(sampleComponent)

        # NB this must be done AFTER the sampleComponent loop to avoid breaking links
        coreUtil._resetParentLink(self._wrappedData, 'components',
                                  OrderedDict((('name', name), ('labeling', apiLabeling)))

                                  )

        return (oldName, oldLabelling,)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def createChain(self, shortName: str = None, role: str = None,
                    comment: str = None, expandFromAtomSets: bool = True,
                    addPseudoAtoms: bool = True, addNonstereoAtoms: bool = True,
                    **kwds):
        """Create new Chain that matches Substance

        See the Chain class for details.

        Optional keyword arguments can be passed in; see Chain._createChainFromSubstance for details.

        :param shortName:
        :param role:
        :param comment: optional comment string
        :return: a new Chain instance.
        """
        from ccpn.core.Chain import _createChainFromSubstance

        return _createChainFromSubstance(self, shortName=shortName, role=role, comment=comment,
                                         expandFromAtomSets=expandFromAtomSets, addPseudoAtoms=addPseudoAtoms,
                                         addNonstereoAtoms=addNonstereoAtoms,
                                         **kwds)

    @logCommand('project.')
    def getChain(self, shortName: str = None, role: str = None,
                    comment: str = None, **kwds):
        """Get existing Chain that matches Substance

        See the Chain class for details.

        Optional keyword arguments can be passed in; see Chain._createChainFromSubstance for details.

        :param shortName:
        :param role:
        :param comment: optional comment string
        :return: a new Chain instance.
        """
        from ccpn.core.Chain import _getChainFromSubstance

        return _getChainFromSubstance(self, shortName=shortName, role=role, comment=comment, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Substance)
def _newSubstance(self: Project, name: str = None, labelling: str = None, substanceType: str = 'Molecule',
                  userCode: str = None, smiles: str = None, inChi: str = None, casNumber: str = None,
                  empiricalFormula: str = None, molecularMass: float = None, comment: str = None,
                  synonyms: typing.Sequence[str] = (), atomCount: int = 0, bondCount: int = 0,
                  ringCount: int = 0, hBondDonorCount: int = 0, hBondAcceptorCount: int = 0,
                  polarSurfaceArea: float = None, logPartitionCoefficient: float = None, serial: int = None
                  ) -> Substance:
    """Create new substance WITHOUT storing the sequence internally
    (and hence not suitable for making chains). SubstanceType defaults to 'Molecule'.

    ADVANCED alternatives are 'Cell' and 'Material'

    See the Substance class for details.

    :param name:
    :param labelling:
    :param substanceType:
    :param userCode:
    :param smiles:
    :param inChi:
    :param casNumber:
    :param empiricalFormula:
    :param molecularMass:
    :param comment:
    :param synonyms:
    :param atomCount:
    :param bondCount:
    :param ringCount:
    :param hBondDonorCount:
    :param hBondAcceptorCount:
    :param polarSurfaceArea:
    :param logPartitionCoefficient:
    :param serial: optional serial number.
    :return: a new Substance instance.
    """

    apiLabeling = _labelling = labelling or DEFAULT_LABELLING

    if isinstance(name, int):
        name = str(name)
    name = Substance._uniqueName(project=self, name=name)
    self._validateStringValue(attribName='labelling', value=_labelling, allowNone=True)

    apiNmrProject = self._wrappedData
    apiComponentStore = apiNmrProject.sampleStore.refSampleComponentStore
    if apiComponentStore.findFirstComponent(name=name, labeling=apiLabeling) is not None:
        # name = commonUtil._incrementObjectName(self.project, Substance._pluralLinkName, name)
        # oldSubstance = apiComponentStore.findFirstComponent(name=name)
        raise ValueError('{}.{} already exists'.format(name, _labelling if _labelling != DEFAULT_LABELLING else ''))

    else:
        oldSubstance = apiComponentStore.findFirstComponent(name=name)

    params = {
        'name'   : name, 'labeling': apiLabeling, 'userCode': userCode, 'synonyms': synonyms,
        'details': comment
        }

    if substanceType == 'Material':
        if oldSubstance is not None and oldSubstance.className != 'Substance':
            raise ValueError("Substance name %s clashes with substance of different type: %s"
                             % (name, oldSubstance.className))
        else:
            apiResult = apiComponentStore.newSubstance(**params)
    elif substanceType == 'Cell':
        if oldSubstance is not None and oldSubstance.className != 'Cell':
            raise ValueError("Substance name %s clashes with substance of different type: %s"
                             % (name, oldSubstance.className))
        else:
            apiResult = apiComponentStore.newCell(**params)
    elif substanceType == 'Composite':
        if oldSubstance is not None and oldSubstance.className != 'Composite':
            raise ValueError("Substance name %s clashes with substance of different type: %s"
                             % (name, oldSubstance.className))
        else:
            apiResult = apiComponentStore.newComposite(**params)
    elif substanceType == 'Molecule':
        if oldSubstance is not None and oldSubstance.className != 'MolComponent':
            raise ValueError("Substance name %s clashes with substance of different type: %s"
                             % (name, oldSubstance.className))
        else:
            apiResult = apiComponentStore.newMolComponent(smiles=smiles, inChi=inChi, casNum=casNumber,
                                                          empiricalFormula=empiricalFormula, molecularMass=molecularMass, atomCount=atomCount,
                                                          bondCount=bondCount, ringCount=ringCount, hBondDonorCount=hBondDonorCount,
                                                          hBondAcceptorCount=hBondAcceptorCount, polarSurfaceArea=polarSurfaceArea,
                                                          logPartitionCoefficient=logPartitionCoefficient, **params)
    else:
        raise ValueError("Substance type %s not recognised" % substanceType)

    result = self._data2Obj[apiResult]
    if result is None:
        raise RuntimeError('Unable to generate new Substance item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    return result


#EJB 20181206: moved to Project
# Project.newSubstance = _newSubstance
# del _newSubstance


@newObject(Substance)
def _fetchNefSubstance(self: Project, sequence: typing.Sequence[dict], name: str = None, serial: int = None):
    """Fetch Substance that matches sequence of NEF rows and/or name

    :param self:
    :param sequence:
    :param name:
    :return: a new Nef Substance instance.
    """

    # TODO add sequence matching and name matching to avoid unnecessary duplicates
    apiNmrProject = self._wrappedData

    name = name or 'Molecule_1'
    while apiNmrProject.root.findFirstMolecule(name=name) is not None:
        name = commonUtil.incrementName(name)

    apiMolecule = MoleculeModify.createMoleculeFromNef(apiNmrProject.root, name, sequence)

    result = self._data2Obj[
        apiNmrProject.sampleStore.refSampleComponentStore.fetchMolComponent(apiMolecule)
    ]
    if result is None:
        raise RuntimeError('Unable to generate new Nef Substance item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))
    return result


def _getNefSubstance(self: Project, sequence: typing.Sequence[dict], name: str = None, serial: int = None):
    """Get existing Substance that matches sequence of NEF rows and/or name

    :param self:
    :param sequence:
    :param name:
    :return: an existing Nef Substance instance or None.
    """

    apiNmrProject = self._wrappedData

    name = name or 'Molecule_1'
    apiMolecule = apiNmrProject.root.findFirstMolecule(name=name)
    if apiMolecule:
        apiMolComponent = apiNmrProject.sampleStore.refSampleComponentStore.getMolComponent(apiMolecule)
        if apiMolComponent in self._data2Obj:
            return self._data2Obj[apiMolComponent]
        else:
            raise RuntimeError('Error getting Nef Substance {}'.format(name))


#EJB 20181206: moved to Project
# Project.fetchNefSubstance = _fetchNefSubstance
# del _fetchNefSubstance


@newObject(Substance)
def _createPolymerSubstance(self: Project, sequence: typing.Sequence[str], name: str,
                            labelling: str = None, userCode: str = None, smiles: str = None,
                            synonyms: typing.Sequence[str] = (), comment: str = None,
                            startNumber: int = 1, molType: str = None, isCyclic: bool = False,
                            serial: int = None) -> Substance:
    """Make new Substance from sequence of residue codes, using default linking and variants

    NB: For more complex substances, you must use advanced, API-level commands.

    See the Substance class for details.

    :param Sequence sequence: string of one-letter codes or sequence of residueNames
    :param str name: name of new substance
    :param str labelling: labelling for new substance. Optional - None means 'natural abundance'
    :param str userCode: user code for new substance (optional)
    :param str smiles: smiles string for new substance (optional)
    :param Sequence[str] synonyms: synonyms for Substance name
    :param str comment: comment for new substance (optional)
    :param int startNumber: number of first residue in sequence
    :param str molType: molType ('protein','DNA', 'RNA'). Required only if sequence is a string.
    :param bool isCyclic: Should substance created be cyclic?
    :return: a new Substance instance.
    """

    apiLabeling = labelling = labelling or DEFAULT_LABELLING

    if isinstance(name, int):
        name = str(name)
    name = Substance._uniqueName(project=self, name=name)

    self._validateStringValue(attribName='labelling', value=labelling, allowNone=True)

    if not sequence:
        raise ValueError("createPolymerSubstance requires non-empty sequence")

    apiNmrProject = self._wrappedData
    if apiNmrProject.sampleStore.refSampleComponentStore.findFirstComponent(name=name, labeling=apiLabeling) is not None:
        raise ValueError("%s.%s already exists" % (name, labelling if labelling != DEFAULT_LABELLING else ''))

    elif apiNmrProject.root.findFirstMolecule(name=name) is not None:
        raise ValueError("Molecule name %s is already in use for API Molecule" % name)

    # NOTE: ED I need to open the undoStack here so this adds to the list
    apiMolecule = MoleculeModify.createMolecule(apiNmrProject.root, sequence, molType=molType,
                                                name=name, startNumber=startNumber,
                                                isCyclic=isCyclic)
    _addUndoApiObject(self.project, apiMolecule)

    apiMolecule.commonNames = synonyms
    apiMolecule.smiles = smiles
    apiMolecule.details = comment

    mol = apiNmrProject.sampleStore.refSampleComponentStore.fetchMolComponent(apiMolecule, labeling=apiLabeling)
    result = self._data2Obj[mol]

    if result is None:
        raise RuntimeError('Unable to generate new PolymerSubstance item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    result.userCode = userCode

    return result


@contextmanager
def _addUndoApiObject(project, apiObject):

    def _getApiObjectTree(apiObject) -> tuple:
        """Retrieve the apiObject tree contained by this object

        CCPNINTERNAL   used for undo's, redo's
        """
        #EJB 20181127: taken from memops.Implementation.DataObject.delete
        #                   should be in the model??
        #EJB 20190926: taken from AbstractWrapperObject - needed for apiObjects that do not have a v3 object

        from ccpn.util.OrderedSet import OrderedSet

        apiObjectlist = OrderedSet()
        # objects still to be checked
        objsToBeChecked = list()
        # counter keyed on (obj, roleName) for how many objects at other end of link
        linkCounter = {}

        # topObjects to check if modifiable
        topObjectsToCheck = set()

        objsToBeChecked.append(apiObject)
        while len(objsToBeChecked) > 0:
            obj = objsToBeChecked.pop()
            if obj:
                obj._checkDelete(apiObjectlist, objsToBeChecked, linkCounter, topObjectsToCheck)  # This builds the list/set

        for topObjectToCheck in topObjectsToCheck:
            if (not (topObjectToCheck.__dict__.get('isModifiable'))):
                raise ValueError("""%s.delete:
           Storage not modifiable""" % apiObject.qualifiedName
                                 + ": %s" % (topObjectToCheck,)
                                 )

        return tuple(apiObjectlist)

    from ccpn.core.lib.ContextManagers import BlankedPartial
    from ccpn.core.lib import Undo
    undo = project._undo
    undo.decreaseBlocking()

    apiObjectsCreated = _getApiObjectTree(apiObject)
    undo._newItem(undoPartial=BlankedPartial(Undo._deleteAllApiObjects,
                                             obj=None, trigger='delete', preExecution=True,
                                             objsToBeDeleted=apiObjectsCreated),
                  redoPartial=BlankedPartial(apiObject.root._unDelete,
                                             topObjectsToCheck=(apiObject.topObject,),
                                             obj=None, trigger='create', preExecution=False,
                                             objsToBeUnDeleted=apiObjectsCreated)
                  )

    undo.increaseBlocking()


#EJB 20181206: moved to Project
# Project.createPolymerSubstance = _createPolymerSubstance
# del _createPolymerSubstance


def _fetchSubstance(self: Project, name: str, labelling: str = None) -> Substance:
    """Get or create Substance with given name and labelling.

    :param self:
    :param name:
    :param labelling:
    :return: new or existing Substance instance.
    """

    if labelling is None:
        apiLabeling = DEFAULT_LABELLING
    else:
        apiLabeling = labelling

    apiRefComponentStore = self._apiNmrProject.sampleStore.refSampleComponentStore
    apiResult = apiRefComponentStore.findFirstComponent(name=name, labeling=apiLabeling)

    with undoBlock():
        if apiResult:
            result = self._data2Obj[apiResult]
        else:
            result = self.newSubstance(name=name, labelling=labelling)

    return result


#EJB 20181206: moved to Project
# Project.fetchSubstance = _fetchSubstance
# del _fetchSubstance


def getter(self: SampleComponent) -> typing.Optional[Substance]:
    return self._project.getSubstance(self._key)

    # relativeId = '.'.join(Pid.remapSeparators(self.na) for x in (self))
    # apiRefComponentStore = self._parent._apiSample.sampleStore.refSampleComponentStore
    # apiComponent = apiRefComponentStore.findFirstComponent(name=self.name,
    #                                                        labeling=self.labelling or DEFAULT_LABELLING)
    # if apiComponent is None:
    #   return None
    # else:
    #   return self._project._data2Obj[apiComponent]


#
SampleComponent.substance = property(getter, None, None,
                                     "Substance corresponding to SampleComponent")


####### Moved to spectrum as referenceSubstances.
####### ReferenceSubstance is Deprecated from 3.0.3.

# def getter(self: Spectrum) -> Substance:
#     apiRefComponent = self._apiDataSource.experiment.refComponent
#     # return apiRefComponent and self._project._data2Obj[apiRefComponent]
#
#     return None if apiRefComponent is None else self._project._data2Obj.get(apiRefComponent)
#
#
# def setter(self: Spectrum, value: Substance):
#     # apiRefComponent = value and value._apiSubstance
#
#     apiRefComponent = None if value is None else value._apiSubstance
#
#     self._apiDataSource.experiment.refComponent = apiRefComponent
#
#
# #
# Spectrum.referenceSubstance = property(getter, setter, None,
#                                        "Substance that has this Spectrum as a reference spectrum")
# del getter
# del setter
####### End referenceSubstance link ####

# Notifiers:

# Substance - SampleComponent link is derived through the keys of the linked objects
# There is therefore no need to monitor the link, and notifiers should be put
# on object creation and renaming
className = Nmr.Experiment._metaclass.qualifiedName()
Project._apiNotifiers.append(
        ('_modifiedLink', {'classNames': ('Spectrum', 'Substance')}, className, 'setRefComponentName'),
        )
