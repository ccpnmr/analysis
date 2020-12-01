"""Constants used in the program core, including enumerations of allowed values

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:58 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re

from collections import namedtuple
from collections import OrderedDict

from ccpn.util.isotopes import isotopeRecords  # NB also import from here in ccpnmodel/ccpncore/lib/spectrum/NmrExpProtoType.py
                                               # and ccpnmodel/ccpncore/api/ccp/nmr/ExpPrototype.py. TODO remove these dependencies

MOUSEDICTSTRIP = 'strip'
AXIS_MATCHATOMTYPE = 0
AXIS_FULLATOMNAME = 1
AXIS_ACTIVEAXES = 'activeAxes'
DOUBLEAXIS_MATCHATOMTYPE = 2
DOUBLEAXIS_FULLATOMNAME = 3
DOUBLEAXIS_ACTIVEAXES = 'doubleActiveAxes'

POSINFINITY = float('Infinity')
NEGINFINITY = float('-Infinity')

# Timestamp formats
stdTimeFormat = "%Y-%m-%d %%H:M:%S.%f"
isoTimeFormat = "%Y-%m-%dT%%H:M:%S.%f"

# CCPNMR data-transfer json mimetype
ccpnmrJsonData = 'ccpnmr-json'

# sequenceCode parsing expression
# A sequenceCOde is combined (without whitespace) of:
#   an optional integer
#   an optional text field, as short as possible
#   an optional field of the form +ii of -ii, where ii is an integer
#
# The expression below has one error:
# a string of the form '+12' is parsed as (None, '', '+12'}
# whereas it should be interpreted as (None, '+12', None), but that cannot be helped
sequenceCodePattern = re.compile('(\-?\d+)?(.*?)(\+\d+|\-\d+)?$')

# Units allowed for amounts (e.g. Sample)
amountUnits = ('L', 'g', 'mole')

#  Units allowed for concentrations (e.g. SampleComponents)
concentrationUnits = ('Molar', 'g/L', 'L/L', 'mol/mol', 'g/g', 'eq')

# Default name for natural abundance labelling - given as None externally
DEFAULT_LABELLING = '_NATURAL_ABUNDANCE'

# Map of (lower-cased) NmrExpPrototype.measurementType to element type code
measurementType2ElementCode = {
    'shift'          : 'shift',
    'jcoupling'      : 'J',
    'mqshift'        : 'MQ',
    'rdc'            : 'RDC',
    'shiftanisotropy': 'ANISO',
    'troesy'         : 'TROESY',
    'dipolarcoupling': 'DIPOLAR',
    't1'             : 'delay',
    't2'             : 'delay',
    't1rho'          : 'delay',
    't1zz'           : 'delay'
    }

# Isotope-dependent assignment tolerances (in ppm)
defaultAssignmentTolerance = 0.03
isotope2Tolerance = {
    '1H' : 0.03,
    '13C': 0.4,
    '15N': 0.4,
    }

# Chosen to be 1) stable. 2) NMR-active, 3)Spin 1/2, 4) abundant
# NB keys are ALL-UPPER, as used in names,
# whereas values are titlecase, as standard for isotopeCodes
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

    ('J', None),
    ('MQ', None),
    ('delay', None),
    ('RDC', None),
    ('ANISO', None),
    ('TROESY', None),
    ('DIPOLAR', None),
    ))


# GWV: now handled by EmptySpectrumDataSource class

# Default parameters - 10Hz/pt, 0.1ppm/point for 1H; 10 Hz/pt, 1ppm/pt for 13C
# NB this is in order to give simple numbers. it does NOT match the gyromagnetic ratios
DEFAULT_SPECTRUM_PARAMETERS = {
    '1H' : {'numPoints': 128, 'sf': 100., 'sw': 1280, 'refppm': 11.8, 'refpt': 1, },
    '2H' : {'numPoints': 128, 'sf': 100., 'sw': 1280, 'refppm': 11.8, 'refpt': 1, },
    '3H' : {'numPoints': 128, 'sf': 100., 'sw': 1280, 'refppm': 11.8, 'refpt': 1, },
    '13C': {'numPoints': 256, 'sf': 10., 'sw': 2560, 'refppm': 236., 'refpt': 1, }
}
# set other isotopes (including 15N) to match carbon 13
for isotopCode in isotopeRecords:
    if isotopCode not in DEFAULT_SPECTRUM_PARAMETERS:
        DEFAULT_SPECTRUM_PARAMETERS[isotopCode] = DEFAULT_SPECTRUM_PARAMETERS['13C']


if __name__ == '__main__':
    for iso, record in isotopeRecords.items():
        symbol = record.symbol
        ll = list(record)
        if len(symbol) > 1:
            symbol = symbol.title()
            iso = iso[:-2] + symbol
            ll[0] = iso
            ll[4] = symbol
        print("  ('%s', IsotopeRecord%s)," % (iso, tuple(ll)))
