"""
NTdb-related info; adapted from the cing code and NTdb2Json.py script

CingDefs(dict)
    - name, ResidueDef(dict)
            - contains list of AtomDef(dict)'s
              .atoms -> (name, AtomDef) dict

            - contains list of DihedralsDef(dict)'s
              .dihedrals -> (name, DihedralDef) dict

"""
import json

from ccpn.util.Path import Path, aPath
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import singleton


class DihedralDef(dict):
    """
    Simple class to store Dihedral definitions
    """
    # These definitions come from cing NTdb
    saveKeys = 'convention name aliases atoms karplus'.split()

    ATOMS = 'atoms'
    # List of atoms: (i, name) tuple
    # i:  -1=previous residue
    #      0=current residue
    #      1=next residue

    def __init__(self):
        for k in self.saveKeys:
            self[k] = None
        self.parent = None

    @property
    def name(self) -> str:
        """:return the name of self
        """
        return self['name']

    @property
    def id(self) -> str:
        """:return a 'id' string, that can be used to for lookup
        """
        return f'{self.parent.name}.{self.name}'

    def __str__(self):
        return '<DihedralDef: (%s)>' % self.id

    __repr__ = __str__
#end class


class AtomDef(dict):
    """
    Simple class to store Atom definitions
    """
    # These definitions come from cing NTdb
    saveKeys = 'convention name nameDict aliases canBeModified topology  NterminalTopology CterminalTopology ' \
               'spinType shift hetatm properties'.split()

    def __init__(self):
        for k in self.saveKeys + 'pseudoAtom hasPseudoAtom isPseudoAtom realAtoms'.split():
            self[k] = None
        self.parent = None

    @property
    def name(self) -> str:
        """:return the name of self
        """
        return self['name']

    @property
    def id(self) -> str:
        """:return a 'id' string, that can be used to for lookup
        """
        return f'{self.parent.name}.{self.name}'

    @property
    def nameTuple(self):
        "Return (residueDef.name, atomDef.name) tuple"
        return (self.parent.name, self.name)

    @property
    def properties(self) -> list:
        "Return the properties of the ArtomDef"
        return self['properties']

    @property
    def isPseudoAtom(self) -> bool:
        "Return True if it is pseudoAtom"
        return self['isPseudoAtom']

    @property
    def hasPseudoAtom(self) -> bool:
        "Return True if atom has a one or more pseudoAtoms"
        return self['hasPseudoAtom']

    def getPseudoAtom(self) :
        """:return the pseudoAtom AtomDef instance or None is self does not have a pseudoAtom
        """
        if not self.hasPseudoAtom:
            return None
        _pseudo = self.get('pseudoAtom')
        if _pseudo is None:
            raise RuntimeError(f'getPseudoAtom: Something has gone wrong; undefined pseudoAtom')
        return self.parent.atomDefsDict.get(_pseudo)

    def getRealAtoms(self) -> list:
        """:return the real atoms AtomDef instances or [] is self is not a pseudoAtom
        """
        if not self.isPseudoAtom:
            return []
        _realAtoms = self.get('realAtoms')
        if _realAtoms is None:
            raise RuntimeError(f'getRealAtoms: Something has gone wrong; undefined realAtoms')
        return [self.parent.atomDefsDict.get(aName) for aName in _realAtoms]

    @property
    def isProton(self) -> bool:
        """:return True if it is a proton or pseudoAtom
        """
        return self['name'][0] == 'H' or (self['isPseudoAtom'] and self['realAtoms'][0][0] == 'H')

    @property
    def isBackbone(self) -> bool:
        """:return True if it is backbone Atom
        """
        return 'isBackbone' in self.properties and not 'isSidechain' in self.properties

    @property
    def attachedHeavyAtom(self):
        """:return the attached heavyAtom (AtomDef instance) if self is a proton, else None
        """
        if not self.isProton:
            return  None
        _cName = self['topology'][0][1]
        return self.parent.atomDefsDict.get(_cName)

    @property
    def otherAttachedProtons(self) -> list:
        """:return a list of all other protons (AtomDef instances) also attached to
                   the attachedHeavyAtom of self if self is a proton, else None
        """
        if not self.isProton:
            return None
        return [p for p in self.attachedHeavyAtom.attachedProtons if p is not self]

    @property
    def attachedProtons(self) -> list:
        """:return a list of the attached protons (AtomDef instances) of self if self is a non-proton, i.e.
                   carbon, nitrogen, else None
        """
        if self.isProton:
            return  None
        _aDefs = [self.parent.atomDefsDict.get(aName) for _offset, aName in self['topology'] if _offset == 0]
        return [aDef for aDef in _aDefs if aDef.isProton]

    @property
    def isCarbon(self):
        "Return True if it is a cabon"
        return self['name'][0] == 'C'

    @property
    def isNitrogen(self):
        "Return True if it is a Nitrogen"
        return self['name'][0] == 'N'

    @property
    def isMethyl(self) -> bool:
        """:return True if self is a methyl"""
        return 'isMethyl' in self.properties

    @property
    def isMethylene(self) -> bool:
        """:return True if self is a methylene"""
        return 'isMethylene' in self.properties

    @property
    def isAromatic(self) -> bool:
        """:return True if self is a aromatic"""
        return 'isAromatic' in self.properties

    def __str__(self):
        return '<AtomDef: (%s)>' % self.id

    __repr__ = __str__
#end class


class ResidueDef(dict):
    """
    Simple class to store Residue definitions
    """
    # These definitions come from cing NTdb
    saveKeys = 'convention name commonName shortName nameDict canBeModified shouldBeSaved cingDefinition ' \
               'comment properties'.split()

    # These keys define the recursive structure
    ATOM_DEFS = 'atomDefs'
    DIHEDRAL_DEFS = 'dihedralDefs'

    def __init__(self):
        self[self.ATOM_DEFS] = []
        self[self.DIHEDRAL_DEFS] = []
        for k in self.saveKeys:
            self[k] = None

        self.path = None  # path saved or restored from

    @property
    def name(self) -> str:
        """:return the name of self
        """
        return self['name']

    @property
    def id(self) -> str:
        """:return a 'id' string, that can be used to for lookup
        """
        return f'{self.name}'

    @property
    def properties(self) -> list:
        "Return the properties of the ResidueDef"
        return self['properties']

    def addAtomDef(self, atomDef):
        "Add an atomDef to the list"
        self[self.ATOM_DEFS].append(atomDef)
        atomDef.parent = self

    def addDihedralDef(self, dihedralDef):
        "Add an dihedralDef to the list"
        self[self.DIHEDRAL_DEFS].append(dihedralDef)
        dihedralDef.parent = self

    #------------------------------------------------------------------------------------------------------
    # atom-related properties
    #------------------------------------------------------------------------------------------------------
    @property
    def atomDefs(self) -> list:
        """:return list of AtomDefs
        """
        return self[self.ATOM_DEFS]

    @property
    def atomDefsDict(self) -> dict:
        """:return (atomName, atomsDefs) as a dict
        """
        return dict([(a['name'], a) for a in self[self.ATOM_DEFS]])

    @property
    def atomNames(self) -> list:
        """:return a list of atoms names
        """
        return list[self.atomDefsDict.keys()]

    @property
    def realAtoms(self) -> list:
        """:return all real atoms atomsDefs as a list
        """
        return [a for a in self.atomDefs if not a.isPseudoAtom]

    @property
    def realAtomsDict(self) -> dict:
        """:return all real atoms as a (atomName, atomsDefs) dict
        """
        return dict([(a['name'], a) for a in self.realAtoms])

    @property
    def pseudoAtoms(self) -> list:
        """:return all pseudo atoms atomsDefs as a list
        """
        return [a for a in self.atomDefs if a.isPseudoAtom]

    @property
    def pseudoAtomsDict(self) -> dict:
        """:return all pseudo atoms as a (atomName, atomsDefs) dict
        """
        return dict([(a['name'], a) for a in self.pseudoAtoms])

    @property
    def protons(self) -> list:
        """:return all proton atomsDefs as a list
        """
        return [a for a in self.atomDefs if a.isProton]

    @property
    def carbons(self) -> list:
        """:return all carbon atomsDefs as a list
        """
        return [a for a in self.atomDefs if a.isCarbon]

    @property
    def nitrogens(self) ->list:
        """:return all nitrogen atomsDefs as a list
        """
        return [a for a in self.atomDefs if a.isNitrogen]

    @property
    def isAminoAcid(self) -> bool:
        """:return True is residue defines a amino acid
        """
        return 'protein' in self.properties

    @property
    def isNucleicAcid(self) -> bool:
        """:return True is residue defines a Nucleic acid
        """
        return 'nucleic' in self.properties

    #------------------------------------------------------------------------------------------------------
    # dihedral-related properties
    #------------------------------------------------------------------------------------------------------
    @property
    def dihedralDefs(self) -> list:
        """Return list of dihedralDefs
        """
        return self[self.DIHEDRAL_DEFS]

    @property
    def dihedralDefsDict(self) -> dict:
        """Return (dihedralName, dihedralDefs) as a dict
        """
        return dict([(a['name'], a) for a in self.dihedralDefs])


    #------------------------------------------------------------------------------------------------------
    # Json save and restore
    #------------------------------------------------------------------------------------------------------
    def toJson(self, path=None):
        "Convert self to json string; optionally save to path"
        if path is None:
            return json.dumps(self, indent=4, sort_keys=True)
        else:
            with open(path, 'w') as fp:
                json.dump(self, fp, indent=4, sort_keys=True)
        self.path = path

    def fromJson(self, path):
        "Restore self from json file path"
        logger = getLogger()
        logger.debug2('Restoring ResidueDef from %s' % path)

        with open(path, 'r') as fp:
            tmp = json.load(fp)
            self.update(tmp)

        # restore child objects
        self[self.ATOM_DEFS] = []
        for theDict in tmp[self.ATOM_DEFS]:
            #print('>> name:', theDict['name'], theDict)
            aDef = AtomDef()
            aDef.update(theDict)
            self.addAtomDef(aDef)

        # restore child objects
        self[self.DIHEDRAL_DEFS] = []
        for theDict in tmp[self.DIHEDRAL_DEFS]:
            #print('>> name:', theDict['name'], theDict)
            aDef = DihedralDef()
            aDef.update(theDict)
            self.addDihedralDef(aDef)

        self.path = path

    #------------------------------------------------------------------------------------------------------
    # others
    #------------------------------------------------------------------------------------------------------

    def __str__(self):
        return '<ResidueDef: %s>' % self.id

    __repr__ = __str__

#end class


@singleton
class NTdbDefs(dict):
    """
    Class to contain the NTdbDef (Cing) residue definitions
    """

    @property
    def residueDefs(self) -> list:
        "Return list of residueDefs"
        return list(self.values())

    @property
    def allRealAtoms(self) -> list:
        "Return all real atoms as a AtomsDefs list"
        return [atm for res in self.residueDefs for atm in res.realAtoms]

    def addDef(self, rDef):
        "Add ResidueDef instance to self"
        self[rDef.name] = rDef

    #------------------------------------------------------------------------------------------------------
    # Json save and restore
    #------------------------------------------------------------------------------------------------------
    def toJson(self, path=None):
        "Convert content of self to json files; path should be a directory"

        logger = getLogger()
        if path is None:
            logger.error('Saving NTdb definitions to json: path is None')
            return

        path = aPath(path)
        if not path.exists():
            path.mkdir(parents=True)

        if not path.is_dir():
            logger.error('Saving NTdb definitions to json; invalid path %s' % path)

        for name, rDef in self.items():
            p = path / rDef.name + '.json'
            rDef.toJson(str(p))
            # rDef.toJson(path + rDef.name + '.json')

    def fromJson(self, path):
        "Restore self from json files in path"

        logger = getLogger()
        if path is None:
            logger.error('restoring NTdb definitions from json: path is None')
            return

        path = aPath(path)
        if not path.exists() or not path.is_dir():
            logger.error(f'Restoring NTdb definitions; invalid path "{path}"')

        logger.debug(f'Restoring NTdb definitions from "{path}" directory')
        for p in path.glob('*.json'):
            rDef = ResidueDef()
            rDef.fromJson(str(p))
            self.addDef(rDef)

    def getDef(self, item, default=None):
        """Routine to get a definitions as 'resName.atomName' or ('resName', 'atomName') or
        'resName.dihedralName' or ('resName', 'dihedralName')
        """
        if isinstance(item, str):
            _items = item.split('.')
        elif isinstance(item, (list, tuple)):
            _items = item
        else:
            raise ValueError(f'Invalid item "{item}"')

        if len(_items) == 0 or len(_items) > 2:
            raise ValueError(f'Invalid item "{item}"; expected length of 1 or 2')

        key = _items[0]
        _result = super().get(key, None)

        if _result is not None and len(_items) > 1:
            key = _items[1]
            _itemsDict = _result.atomDefsDict
            _itemsDict.update(_result.dihedralDefsDict)
            _result = _itemsDict.get(key, None)

        if _result is None:
            _result = default

        return  _result

#end class


def getNTdbDefs() -> dict:
    """:return the NTdbDefs (i.e. NTdbDefs) instance (singleton)
    """
    from ccpn.framework.PathsAndUrls import ccpnConfigPath
    defs = NTdbDefs()
    _path = ccpnConfigPath / 'NTdb_json'
    defs.fromJson(_path)
    return defs



