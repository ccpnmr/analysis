"""
This file contains NMR isotope related functionalities
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
__dateModified__ = "$dateModified: 2017-07-07 16:33:14 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:48 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
from collections import Counter
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
    version = VERSION

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


@singleton
class IsotopeRecords(CcpnJsonDirectoryABC):
    """Singleton class to contain all isotopeRecords as (isotopeCode, IsotopeRecord) key,value pairs
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
isotopeRecords = IsotopeRecords()


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
