"""
This file contains NMR isotope related functionalities

Use getIsotopeRecords() to get access to the IsotopeRecords data structure (an OrderedDict)
e.g., to make a mapping dict for massNumber --> isotopeCode:

isotopeRecords = getIsotopeRecords()
mappingDict = dict( [rec.massNumber, rec.isotopeCode) for rec in isotopeRecords.values()] )
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-08-25 10:25:19 +0100 (Thu, August 25, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:48 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
from collections import Counter, OrderedDict

from ccpn.util.traits.CcpNmrJson import CcpNmrJson, CcpnJsonDirectoryABC
from ccpn.util.traits.CcpNmrTraits import Unicode, Int, Float, Bool

from ccpn.framework.PathsAndUrls import ccpnConfigPath
from ccpn.util.Path import aPath
from ccpn.util.decorators import singleton

#=========================================================================================
# Definitions for findMostLikelyFieldFromSpectrometerFrequencies
# The default isotopes checked:
defaultIsotopes = '1H 13C 15N 19F 31P'.split()
# The default fields (defined in MHz; checked in range Field.validRange):
fieldsInMHz = (300.0, 360.0, 400.0, 500.0, 600.0, 700.0, 750.0, 800.0, 850.0, 900.0, 950.0,
               1000.0, 1100.0, 1200.0)
#=========================================================================================

VERSION = 1.0

class IsotopeRecord(CcpNmrJson):
    """Class to store isotope information
    """
    classVersion = VERSION
    saveAllTraitsToJson = True

    isotopeCode =      Unicode(allow_none=False, default_value='??').tag(info='The isotope code identifier, e.g. 1H, 13C, etc')
    elementNumber =    Int(allow_none=False, default_value=0).tag(info='The element number')
    massNumber =       Int(allow_none=False, default_value=0).tag(info='The mass number')
    isRadioactive =    Bool(allow_none=True, default_value=None).tag(info='Flag identifying if isotope is radioactive')
    symbol =           Unicode(allow_none=False, default_value='?').tag(info='The symbol identifying the isotope; eg. H for 1H, C for 13C, etc')
    name =             Unicode(allow_none=True, default_value=None).tag(info='The name of the isotop; e.g. hydrogen')
    spin =             Float(allow_none=False, default_value=0.0).tag(info='The spin of the isotope')
    gFactor =          Float(allow_none=False, default_value=0.0).tag(info='The g-factor of the isotope')
    abundance =        Float(allow_none=True, default_value=None).tag(info='The abundance of the isotope')
    quadrupoleMoment = Float(allow_none=True, default_value=None).tag(info='The quadrupoleMoment of the isotope')

    # to allow them to be sorted
    def __le__(self, other):
        return self.massNumber <= other.massNumber

    def __lt__(self, other):
        return self.massNumber < other.massNumber

    def __str__(self):
        return '<IsotopeRecord %s>' % self.isotopeCode

    def __repr__(self):
        return 'IsotopeRecord(%s)' % ', '.join(['%s=%r'%(k,v) for k,v in self.items()])
#end class
# register the class for restoring
IsotopeRecord.register()


def getIsotopeRecords():
    """Covenience function to return the isotopeRecords Instance
    """
    return IsotopeRecords()


@singleton
class IsotopeRecords(CcpnJsonDirectoryABC):
    """Singleton class to contain all isotopeRecords as (isotopeCode, IsotopeRecord) (key,value) pairs
    """
    attributeName = 'isotopeCode'
    directory = aPath(ccpnConfigPath) / 'isotopeRecords'
    sorted = True

    def isotopesWithSpin(self, minValue=0.5, maxValue=None):
        """Return list of all isotopeRecords that have spin between minValue and maxValue (inclusive)
        """
        if maxValue is None: maxValue = 1000.0  # Some rediculus high number
        result = []
        for record in self.values():
            if minValue <= record.spin <= maxValue:
                result.append(record)
        return result

    def isotopesWithSpinHalf(self):
        return self.isotopesWithSpin(minValue=0.5, maxValue=0.5)
#end class

# create an instance
isotopeRecords = getIsotopeRecords()


class Nucleus(str):
    """
    Class that behaves as a string, but holds the information about a particular nucleus and has usefull (!?)
    conversion methods
    """
    muDivHbar = 7.62259328547  # MHz/T (from https://en.wikipedia.org/wiki/Gyromagnetic_ratio)

    def __init__(self, isotopeCode):
        super().__init__()
        self.isotopeCode = isotopeCode
        self.isotopeRecord = isotopeRecords.get(self)

    @property
    def gamma(self):
        """return gamma in MHz/T; NB the isotopeRecord for 1H has the shielded g-value; most likely also for
        the other nuclei (if available)
        """
        if not self.isotopeRecord:
            raise RuntimeError('Undefined isotopeRecord for %s' % self)

        gFac = self.isotopeRecord.gFactor
        return gFac * self.muDivHbar

    def frequencyAtField(self, field):
        """Return absolute frequency (MHz) at field (T)
        """
        if not self.isotopeRecord:
            raise RuntimeError('Undefined isotopeRecord for %s' % self)
        freq = self.gamma * field
        return math.fabs(freq)

    def fieldAtFrequency(self, frequency):
        """Return field (T) at absolute frequency (MHz)
        """
        if not self.isotopeRecord:
            raise RuntimeError('Undefined isotopeRecord for %s' % self)
        field = frequency / self.gamma
        return math.fabs(field)

    @property
    def axisCode(self):
        """Return axis code string
        """
        if not self.isotopeRecord:
            raise RuntimeError('Undefined isotopeRecord for %s' % self)
        return self.isotopeRecord.symbol

    def __str__(self):
        return '<Nucleus %s>' % super().__str__()


class Field(dict):
    """Class to hold the frequencies of various nuclei for a given field
    """
    validRange = (-1.0, 0.5)  # Variation in spectrometer frequences (MHz); accommodate Agilent/Varian and Bruker

    def __init__(self, field):
        super().__init__()
        self.field = field
        # add the default nuclei and their frequencies that will be tried
        for isotope in defaultIsotopes:
            self.addNucleus(isotope)

    def addNucleus(self, isotopeCode):
        """Add a Nucleus instance defined by isotopeCode
        """
        if isotopeCode not in isotopeRecords:
            raise ValueError('Undefined isotope "%s"' % isotopeCode)
        nuc = Nucleus(isotopeCode)
        self[nuc] = nuc.frequencyAtField(self.field)

    @property
    def nuclei(self):
        """return a tuple of Nucleus instances for this field
        """
        return tuple([n for n, f in self.items()])

    @property
    def frequencies(self):
        """return a tuple of frequencies for this field
        """
        return tuple([f for n, f in self.items()])

    def isInRange(self, nucleus, freq):
        """return True in freq is withing validRange
        """
        if nucleus not in self:
            raise ValueError('frequency of nucleus "%s" is not defined' % nucleus)
        lower, upper = (self[nucleus] + self.validRange[0], self[nucleus] + self.validRange[1])
        #print('>', lower, freq, upper)
        return (lower <= freq <= upper)

    def findNucleus(self, freq):
        """Find nucleus corresponding with freq; return None if not found
        """
        for nucleus in self.nuclei:
            if self.isInRange(nucleus, freq):
                return nucleus
        return None

    def __le__(self, other):
        return self.field <= other.field

    def __lt__(self, other):
        return self.field < other.field

    def __str__(self):
        return '<Field %.4fT>' % self.field

    def __repr__(self):
        return 'Field(%f)' % self.field


def findMostLikelyFieldFromSpectrometerFrequencies(spectrometerFrequencies):
    """Return the most likely field corresponding to spectrometerFrequencies, or None if it cannot be determined
    """
    # list of fields to check
    field500 = 11.7433073413584267  # 500.0 MHz reference; tweaked in 14+ th digit to minimize rounding
    fieldList = [Field(freq / 500.0 * field500) for freq in fieldsInMHz]  # list of Field instances

    fieldsFound = []
    for sf in spectrometerFrequencies:
        for indx, field in enumerate(fieldList):
            nucleus = field.findNucleus(sf)
            if nucleus is not None:
                fieldsFound.append(indx)
                #print('Found>>', field.field, sf, nucleus)

    counter = Counter(fieldsFound)
    mostCommon = counter.most_common()
    #print('mostCommon', mostCommon)
    if len(mostCommon) > 0:
        return fieldList[mostCommon[0][0]]
    else:
        return None


def findNucleiFromSpectrometerFrequencies(spectrometerFrequencies):
    """return a tuple of Nuclei instances corresponding to spectrometerFrequencies or None if not identified
    """
    theField = findMostLikelyFieldFromSpectrometerFrequencies(spectrometerFrequencies)
    if theField is None:
        return None

    nuclei = [theField.findNucleus(sf) for sf in spectrometerFrequencies]
    return tuple(nuclei)


def isotopeCode2Nucleus(isotopeCode):
    """:return the nucleus symbol for isotopeCode or None if not found
    """
    if not isotopeCode:
        return None

    record = isotopeRecords.get(isotopeCode)
    if record is None:
        return None
    else:
        return record.symbol.upper()

#=================================================================================================
# This routines were copied/adapted from util.Common
#=================================================================================================

# A translation dict
DEFAULT_ISOTOPE_DICT = OrderedDict((
    ('H', '1H'),
    ('D', '2H'),
    ('B', '11B'),
    ('C', '13C'),
    ('N', '15N'),
    ('O', '17O'),
    ('F', '19F'),
    ('P', '31P'),
    ('S', '33S'),
    ('K', '39K'),
    ('V', '51V'),
    ('Y', '89Y'),
    ('I', '127I'),
    ('W', '183W'),
    ('U', '235U'),
    ('HE', '3He'),
    ('LI', '7Li'),
    ('BE', '9Be'),
    ('NE', '21Ne'),
    ('NA', '23Na'),
    ('MG', '25Mg'),
    ('AL', '27Al'),
    ('SI', '29Si'),
    ('CL', '35Cl'),
    ('AR', '40Ar'),
    ('CA', '43Ca'),
    ('SC', '45Sc'),
    ('TI', '47Ti'),
    ('CR', '53Cr'),
    ('MN', '55Mn'),
    ('FE', '57Fe'),
    ('CO', '59Co'),
    ('NI', '61Ni'),
    ('CU', '63Cu'),
    ('ZN', '67Zn'),
    ('GA', '69Ga'),
    ('GE', '73Ge'),
    ('AS', '75As'),
    ('SE', '77Se'),
    ('BR', '79Br'),
    ('KR', '83Kr'),
    ('RB', '85Rb'),
    ('SR', '87Sr'),
    ('ZR', '91Zr'),
    ('NB', '93Nb'),
    ('MO', '95Mo'),
    ('TC', '99Tc'),
    ('RU', '99Ru'),
    ('RH', '103Rh'),
    ('PD', '105Pd'),
    ('AG', '107Ag'),
    ('CD', '111Cd'),
    ('IN', '115In'),
    ('SN', '119Sn'),
    ('SB', '121Sb'),
    ('TE', '125Te'),
    ('XE', '129Xe'),
    ('CS', '133Cs'),
    ('BA', '137Ba'),
    ('LA', '139La'),
    ('CE', '140Ce'),
    ('PR', '141Pr'),
    ('ND', '143Nd'),
    ('PM', '147Pm'),
    ('SM', '144Sm'),
    ('EU', '153Eu'),
    ('GD', '157Gd'),
    ('TB', '159Tb'),
    ('DY', '163Dy'),
    ('HO', '165Ho'),
    ('ER', '167Er'),
    ('TM', '169Tm'),
    ('YB', '171Yb'),
    ('LU', '175Lu'),
    ('HF', '177Hf'),
    ('TA', '181Ta'),
    ('RE', '187Re'),
    ('OS', '187Os'),
    ('IR', '193Ir'),
    ('PT', '195Pt'),
    ('AU', '197Au'),
    ('HG', '199Hg'),
    ('TL', '205Tl'),
    ('PB', '207Pb'),
    ('BI', '209Bi'),
    ('PO', '209Po'),
    ('AC', '227Ac'),
    ('TH', '232Th'),
    ('NP', '237Np'),
    ('PU', '239Pu'),
    ('AM', '243Am'),

    ))


def checkIsotope(isotopeCode) -> str:
    """Convert isotopeCode string to most probable isotope code - defaulting to '1H'

    This function is intended for external format isotope specifications; mostly in SpectrumSource parameter
    reading routines
    """
    defaultIsotope = '1H'

    if not isotopeCode:
        raise ValueError('Invalid isotopeCode (%r)' % isotopeCode)

    isotopeCode = isotopeCode.strip().upper()
    if isotopeCode in isotopeRecords:
        # Superfluous but should speed things up
        return isotopeCode

    for ic in isotopeRecords.keys():
        # NB checking this first means that e.g. 'H13C' returns '13C' rather than '1H'
        if ic.upper() in isotopeCode:
            return ic

    # NB order of checking means that e.g. 'CA' returns Calcium rather than Carbon
    result = (DEFAULT_ISOTOPE_DICT.get(isotopeCode[:2]) or
              DEFAULT_ISOTOPE_DICT.get(isotopeCode[0]))

    if result is None:
       result = defaultIsotope

    return result


def name2IsotopeCode(name=None):
    """Get standard isotope code matching atom name or axisCode string
    """
    if not name:
        return None

    result = DEFAULT_ISOTOPE_DICT.get(name[0])
    if result is None:
        if name[0].isdigit():
            ss = name.title()
            for key in isotopeRecords:
                if ss.startswith(key):
                    if name[:len(key)].isupper():
                        result = key
                    break
        else:
            result = DEFAULT_ISOTOPE_DICT.get(name[:2])
    #
    return result


def name2ElementSymbol(name):
    """Get standard element symbol matching name or axisCode

    NB, the first letter takes precedence, so e.g. 'CD' returns 'C' (carbon)
    rather than 'CD' (Cadmium)"""

    # NB, We deliberately do NOT use 'value in Constants.DEFAULT_ISOTOPE_DICT'
    # We want to avoid elements that are in the dict but have value None.
    if not name:
        return None
    elif DEFAULT_ISOTOPE_DICT.get(name[0]) is not None:
        return name[0]
    elif DEFAULT_ISOTOPE_DICT.get(name[:2]) is not None:
        return name[:2]
    elif name[0].isdigit():
        ss = name.title()
        for key, record in isotopeRecords.items():
            if ss.startswith(key):
                if name[:len(key)].isupper():
                    return record.symbol.upper()
                break
    #
    return None
