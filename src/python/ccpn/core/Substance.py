"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:31 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
# from typing import Tuple, Optional, Sequence, Dict
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
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger


_apiClassNameMap = {
    'MolComponent': 'Molecule',
    'Substance': 'Material'
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

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiRefComponent._metaclass.qualifiedName()

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
    def comment(self) -> str:
        """Free-form text comment"""
        return self._wrappedData.details

    @comment.setter
    def comment(self, value: str):
        self._wrappedData.details = value

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
        """Reference Spectra acquired for Substance.
        There should be only one reference spectrum for each experiment type"""

        name = self.name
        data2Obj = self._project._data2Obj
        return tuple(sorted(data2Obj[y] for x in self._project._apiNmrProject.experiments
                            for y in x.dataSources
                            if x.refComponentName == name))

    @referenceSpectra.setter
    def referenceSpectra(self, value):
        name = self.name
        for spectrum in self.referenceSpectra:
            spectrum._apiDataSource.experiment.refComponentName = None
        for spectrum in value:
            spectrum._apiDataSource.experiment.refComponentName = name

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

    def rename(self, name: str = None, labelling: str = None):
        """Rename Substance, changing its name and/or labelling and Pid, and rename
        SampleComponents and SpectrumHits with matching names. If name is None, the existing value w
        ill be used. Labelling 'None'  means 'Natural abundance'"""

        # ejb - name should always be passed in, strange not to

        oldName = self.name
        if name is None:  # ejb - stupid renaming in substancePopup
            name = oldName
        if not isinstance(name, str):
            raise TypeError("ccpn.Substance.name must be a string")  # ejb
        elif not name:
            raise ValueError("ccpn.Substance.name must be set")  # ejb
        elif Pid.altCharacter in name:
            raise ValueError("Character %s not allowed in ccpn.Substance.name" % Pid.altCharacter)

        oldLabelling = self.labelling
        apiLabeling = labelling
        if labelling is None:
            apiLabeling = DEFAULT_LABELLING
        elif not isinstance(labelling, str):
            raise TypeError("ccpn.Substance.labelling must be a string")
        elif not labelling:
            # raise ValueError("ccpn.Substance.labelling must be set")

            #TODO:ED testing
            apiLabeling = DEFAULT_LABELLING

        elif Pid.altCharacter in labelling:
            raise ValueError("Character %s not allowed in ccpn.Substance.labelling" % Pid.altCharacter)

        self._startCommandEchoBlock('rename', name, labelling)
        undo = self._project._undo
        if undo is not None:
            undo.increaseBlocking()

        try:
            renamedObjects = [self]
            for sampleComponent in self.sampleComponents:
                for spectrumHit in sampleComponent.spectrumHits:
                    coreUtil._resetParentLink(spectrumHit._wrappedData, 'spectrumHits',
                                              OrderedDict((('substanceName', name),
                                                           ('sampledDimension', spectrumHit.pseudoDimensionNumber),
                                                           ('sampledPoint', spectrumHit.pointNumber)))
                                              )
                    renamedObjects.append(spectrumHit)

                # NB this must be done AFTER the spectrumHit loop to avoid breaking links
                coreUtil._resetParentLink(sampleComponent._wrappedData, 'sampleComponents',
                                          OrderedDict((('name', name), ('labeling', apiLabeling)))
                                          )
                renamedObjects.append(sampleComponent)

            # NB this must be done AFTER the sampleComponent loop to avoid breaking links
            coreUtil._resetParentLink(self._wrappedData, 'components',
                                      OrderedDict((('name', name), ('labeling', apiLabeling)))
                                      )
            for obj in renamedObjects:
                obj._finaliseAction('rename')
                obj._finaliseAction('change')

        finally:
            if undo is not None:
                undo.decreaseBlocking()
            self._endCommandEchoBlock()

        undo.newItem(self.rename, self.rename, undoArgs=(oldName, oldLabelling),
                     redoArgs=(name, labelling,))

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

#=========================================================================================
# Connections to parents:
#=========================================================================================

def _newSubstance(self: Project, name: str = None, labelling: str = None, substanceType: str = 'Molecule',
                  userCode: str = None, smiles: str = None, inChi: str = None, casNumber: str = None,
                  empiricalFormula: str = None, molecularMass: float = None, comment: str = None,
                  synonyms: typing.Sequence[str] = (), atomCount: int = 0, bondCount: int = 0,
                  ringCount: int = 0, hBondDonorCount: int = 0, hBondAcceptorCount: int = 0,
                  polarSurfaceArea: float = None, logPartitionCoefficient: float = None, serial: int = None
                  ) -> Substance:
    """Create new substance WITHOUT storing the sequence internally
    (and hence not suitable for making chains). SubstanceType defaults to 'Molecule'.

    ADVANCED alternatives are 'Cell' and 'Material'"""

    if labelling is None:
        apiLabeling = DEFAULT_LABELLING
    else:
        apiLabeling = labelling

    # Default values for 'new' function, as used for echoing to console
    defaults = OrderedDict(
            (('labelling', None), ('substanceType', 'Molecule'),
             ('userCode', None), ('smiles', None), ('inChi', None),
             ('casNumber', None), ('empiricalFormula', None), ('molecularMass', None),
             ('comment', None), ('synonyms', ()), ('atomCount', 0),
             ('bondCount', 0), ('ringCount', 0), ('hBondDonorCount', 0),
             ('hBondAcceptorCount', 0), ('polarSurfaceArea', None), ('logPartitionCoefficient', None)
             )
            )

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # for ss in (name, labelling):
    #   if ss and Pid.altCharacter in ss:
    #     raise ValueError("Character %s not allowed in ccpn.Substance id: %s.%s" %
    #                      (Pid.altCharacter, name, labelling))
    #
    if not isinstance(name, str):
        raise TypeError("ccpn.Substance name must be a string")  # ejb
    elif not name:
        raise ValueError("ccpn.Substance name must be set")  # ejb
    elif Pid.altCharacter in name:
        raise ValueError("Character %s not allowed in ccpn.Substance id: %s.%s" %
                         (Pid.altCharacter, name, labelling))

    if labelling is not None:  # 'None' caught by below as default
        if not isinstance(labelling, str):
            raise TypeError("ccpn.Substance 'labelling' name must be a string")  # ejb
        elif not labelling:
            raise ValueError("ccpn.Substance 'labelling' name must be set")  # ejb
        elif Pid.altCharacter in labelling:
            raise ValueError("Character %s not allowed in ccpn.Substance labelling, id: %s.%s" %
                             (Pid.altCharacter, name, labelling))
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

    apiNmrProject = self._wrappedData
    apiComponentStore = apiNmrProject.sampleStore.refSampleComponentStore

    if apiComponentStore.findFirstComponent(name=name, labeling=apiLabeling) is not None:
        raise ValueError("Substance %s.%s already exists" % (name, labelling))

    else:
        oldSubstance = apiComponentStore.findFirstComponent(name=name)

    params = {
        'name': name, 'labeling': apiLabeling, 'userCode': userCode, 'synonyms': synonyms,
        'details': comment
        }

    self._startCommandEchoBlock('newSubstance', name, values=locals(), defaults=defaults,
                                parName='newSubstance')
    try:
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
    finally:
        self._endCommandEchoBlock()
    #
    return self._data2Obj[apiResult]


Project.newSubstance = _newSubstance
del _newSubstance


def _fetchNefSubstance(self: Project, sequence: typing.Sequence[dict], name: str = None):
    """Fetch Substance that matches sequence of NEF rows and/or name"""

    defaults = {'name': None}

    # TODO add sequence matching and name matching to avoid unnecessary duplicates
    apiNmrProject = self._wrappedData

    self._startCommandEchoBlock('fetchNefSubstance', values=locals(), defaults=defaults,
                                parName='newSubstance')
    self._project.blankNotification()
    try:

        name = name or 'Molecule_1'
        while apiNmrProject.root.findFirstMolecule(name=name) is not None:
            name = commonUtil.incrementName(name)

        apiMolecule = MoleculeModify.createMoleculeFromNef(apiNmrProject.root, name, sequence)

        result = self._data2Obj[
            apiNmrProject.sampleStore.refSampleComponentStore.fetchMolComponent(apiMolecule)
        ]
    finally:
        self._endCommandEchoBlock()
        self._project.unblankNotification()
    #
    result._finaliseAction('create')
    return result


Project.fetchNefSubstance = _fetchNefSubstance
del _fetchNefSubstance


def _createPolymerSubstance(self: Project, sequence: typing.Sequence[str], name: str,
                            labelling: str = None, userCode: str = None, smiles: str = None,
                            synonyms: typing.Sequence[str] = (), comment: str = None,
                            startNumber: int = 1, molType: str = None, isCyclic: bool = False) -> Substance:
    """Make new Substance from sequence of residue codes, using default linking and variants

    NB: For more complex substances, you must use advanced, API-level commands.

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

    """

    if labelling is None:
        apiLabeling = DEFAULT_LABELLING
    else:
        apiLabeling = labelling

    defaults = OrderedDict(
            (
                ('labelling', None), ('userCode', None), ('smiles', None),
                ('synonyms', ()), ('comment', None), ('startNumber', 1), ('molType', None),
                ('isCyclic', False)
                )
            )

    apiNmrProject = self._wrappedData

    if not sequence:
        raise ValueError("createPolymerSubstance requires non-empty sequence")

    elif apiNmrProject.sampleStore.refSampleComponentStore.findFirstComponent(name=name,
                                                                              labeling=apiLabeling) is not None:
        raise ValueError("Substance %s.%s already exists" % (name, labelling))

    elif apiNmrProject.root.findFirstMolecule(name=name) is not None:
        raise ValueError("Molecule name %s is already in use for API Molecule")

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    if labelling is not None:
        if not isinstance(labelling, str):
            raise TypeError("ccpn.Substance 'labelling' name must be a string")
        elif not labelling:
            raise ValueError("ccpn.Substance 'labelling' name must be set")
        elif Pid.altCharacter in labelling:
            raise ValueError("Character %s not allowed in ccpn.Substance labelling, id: %s.%s" %
                             (Pid.altCharacter, name, labelling))
    #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

    self._startCommandEchoBlock('createPolymerSubstance', sequence, name,
                                values=locals(), defaults=defaults,
                                parName='newPolymerSubstance')
    self._project.blankNotification()
    try:
        apiMolecule = MoleculeModify.createMolecule(apiNmrProject.root, sequence, molType=molType,
                                                    name=name, startNumber=startNumber,
                                                    isCyclic=isCyclic)
        apiMolecule.commonNames = synonyms
        apiMolecule.smiles = smiles
        apiMolecule.details = comment

        result = self._data2Obj[apiNmrProject.sampleStore.refSampleComponentStore.fetchMolComponent(
                apiMolecule, labeling=apiLabeling)]
        result.userCode = userCode
    finally:
        self._endCommandEchoBlock()
        self._project.unblankNotification()

    # DO creation notifications
    result._finaliseAction('create')
    #
    return result


Project.createPolymerSubstance = _createPolymerSubstance
del _createPolymerSubstance


def _fetchSubstance(self: Project, name: str, labelling: str = None) -> Substance:
    """get or create Substance with given name and labelling."""

    if labelling is None:
        apiLabeling = DEFAULT_LABELLING
    else:
        apiLabeling = labelling

    values = {'labelling': labelling}

    apiRefComponentStore = self._apiNmrProject.sampleStore.refSampleComponentStore
    apiResult = apiRefComponentStore.findFirstComponent(name=name, labeling=apiLabeling)

    self._startCommandEchoBlock('fetchSubstance', name, values=values, parName='newSubstance')
    try:
        if apiResult:
            result = self._data2Obj[apiResult]
        else:
            result = self.newSubstance(name=name, labelling=labelling)
    finally:
        self._endCommandEchoBlock()
    return result


#
Project.fetchSubstance = _fetchSubstance
del _fetchSubstance


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


def getter(self: Spectrum) -> Substance:
    apiRefComponent = self._apiDataSource.experiment.refComponent
    # return apiRefComponent and self._project._data2Obj[apiRefComponent]

    return None if apiRefComponent is None else self._project._data2Obj.get(apiRefComponent)


def setter(self: Spectrum, value: Substance):
    # apiRefComponent = value and value._apiSubstance

    apiRefComponent = None if value is None else value._apiSubstance

    self._apiDataSource.experiment.refComponent = apiRefComponent


#
Spectrum.referenceSubstance = property(getter, setter, None,
                                       "Substance that has this Spectrum as a reference spectrum")
del getter
del setter

# Notifiers:

# Substance - SampleComponent link is derived through the keys of the linked objects
# There is therefore no need to monitor the link, and notifiers should be put
# on object creation and renaming
className = Nmr.Experiment._metaclass.qualifiedName()
Project._apiNotifiers.append(
        ('_modifiedLink', {'classNames': ('Spectrum', 'Substance')}, className, 'setRefComponentName'),
        )
