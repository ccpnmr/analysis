from ccpn.framework.lib.NTdb.NTdbDefs import getNTdbDefs

ISMETHYL = 'isMethyl'
ISMETHYLENE = 'isMethylene'
ISAROMATIC = 'isAromatic'


def isBetaMethylene(atmDef):
    "Return True if atmDef defines a protein b-methylene"
    return ISMETHYLENE in atmDef.properties and atmDef.isProton and ('protein' in atmDef.parent.properties)


def isMethyl(atmDef):
    "Return True if atmDef defines a protein methyl, but not VAL, LEU"
    return ISMETHYL in atmDef.properties and atmDef.isProton and 'protein' in atmDef.parent.properties and \
           atmDef.parent.name not in ('VAL', 'LEU')


def isStereoMethyl(atmDef):
    "Return True if atmDef defines a protein methyl proton or carbon and VAL, LEU"
    return ISMETHYL in atmDef.properties and 'protein' in atmDef.parent.properties and \
           atmDef.parent.name in ('VAL', 'LEU')

def isAromatic(atmDef):
    "Return True if atmDef defines a aromatic-sidechain Phe, Tyr"
    return ISAROMATIC in atmDef.properties and 'protein' in atmDef.parent.properties and \
           atmDef.parent.name in ('PHE', 'TYR')

# def getNefName(aDef) -> str:
#     """Construct the nefName from atomDef.name; account for the different possibilities
#     """
#     # all methyls
#     if aDef.isMethyl and aDef.isProton:
#         _nefName = aDef.name[:-1] + '%'
#
#     # Asn, Gln amine groups
#     elif aDef.parent.name in ('ASN','GLN') and aDef.name in 'HD21 HD22 HE21 HE22'.split():
#         _nefName = aDef.name[:-1] + aDef.name[-1:].replace('1','x').replace('2','y')
#
#     # Ade, Gua amine groups
#     elif aDef.parent.name in ('A','DA','G','DG') and aDef.name in 'H61 H62 H21 H22'.split():
#         _nefName = aDef.name[:-1] + aDef.name[-1:].replace('1','x').replace('2','y') \
#
#     # amino acids methylenes
#     elif aDef.parent.isAminoAcid and aDef.isMethylene and aDef.isProton:
#         _nefName = aDef.name[:-1] + aDef.name[-1:].replace('2','x').replace('3','y')
#
#     # nucleic acids methylenes
#     elif aDef.parent.isNucleicAcid and aDef.isMethylene and aDef.isProton:
#         _nefName = aDef.name.replace("''",'x').replace("'",'y')
#
#     # Phe, Tyr aromatic sidechains
#     elif aDef.parent.name in ('PHE','TYR') and aDef.name in 'HD1 CD1 HD2 CD2  HE1 CE1 HE2 CE2'.split():
#         _nefName = aDef.name.replace('1','x').replace('2','y')
#
#     else:
#         _nefName = aDef.name
#
#     return _nefName


def getNefMappingDict() -> dict:
    """:return a dict with key=(residueName, atomName) and value=(residueName, NefName, specialType) pairs.
    Currently only for proteins
    """
    ntDefs = getNTdbDefs()

    # define some atom sets
    realAtoms = [atm for res in ntDefs.residueDefs for atm in res.realAtoms]

    betaMethylenes = [atm for atm in realAtoms if isBetaMethylene(atm)]
    #print(betaMethylenes)

    methyls = [atm for atm in realAtoms if isMethyl(atm)]
    #print(methyls)

    stereoMethyls = [atm for atm in realAtoms if isStereoMethyl(atm)]
    #print(stereoMethyls)

    aromatics = [atm for atm in realAtoms if isAromatic(atm)]
    #print(aromatics)

    nefMapping = []  # A list of source (residueName, atomName) and target (residueName, NefName, specialType) tuples
                  # target (residueName, None) indicates the entry to be removed (e.g. redundant methyl protons in
                  # chemicalShift saveframe

    for atm in betaMethylenes:
        nefName = atm.name.replace('2', 'x').replace('3', 'y')
        nefMapping.append(((atm.parent.name, atm.name), (atm.parent.name, nefName, ISMETHYLENE)))

    for atm in methyls:
        if atm.isProton and atm.name.endswith('1'):
            nefName = atm.name[:-1] + '%'
        else:
            nefName = None
        nefMapping.append(((atm.parent.name, atm.name), (atm.parent.name, nefName, ISMETHYL)))

    for atm in stereoMethyls:
        if atm.isProton:
            if atm.name.endswith('1'):
                nefName = atm.name[:-1] + '%'
                nefName = nefName.replace('1', 'x').replace('2', 'y')
            else:
                nefName = None
        elif atm.isCarbon:
            nefName = atm.name.replace('1', 'x').replace('2', 'y')
        nefMapping.append(((atm.parent.name, atm.name), (atm.parent.name, nefName, ISMETHYL)))

    for atm in aromatics:
        if atm.name.endswith('1') or atm.name.endswith('2'):
            nefName = atm.name.replace('1', 'x').replace('2', 'y')
            nefMapping.append(((atm.parent.name, atm.name), (atm.parent.name, nefName, ISAROMATIC)))

    return dict(nefMapping)

# nefMappingDict = getNefMappingDict()
# print(nefMappingDict)
