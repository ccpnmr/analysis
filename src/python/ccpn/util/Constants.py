"""Constants used in the program core, including enumerations of allowed values

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-07-31 16:47:51 +0100 (Mon, July 31, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re

from collections import OrderedDict
from ccpn.util.isotopes import isotopeRecords  # NB also used from here in ccpnmodel/ccpncore/api/ccp/nmr/ExpPrototype.py.


# TODO remove these dependencies


ERRORSTRING = 'BADVALUE'
MOUSEDICTSTRIP = 'strip'
AXIS_MATCHATOMTYPE = 0
AXIS_FULLATOMNAME = 1

POSINFINITY = float('Infinity')
NEGINFINITY = float('-Infinity')
SCALETOLERANCE = 1e-250  # can get very small/large for 1D

# Timestamp formats
stdTimeFormat = "%Y-%m-%d %%H:M:%S.%f"
isoTimeFormat = "%Y-%m-%dT%%H:M:%S.%f"

# CCPNMR data-transfer json mimetype
ccpnmrJsonData = 'ccpnmr-json'
ccpnmrModelDataList = 'ccpnmr-model-datalist'
INTERNALQTDATA = 'application/x-qabstractitemmodeldatalist'

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

# Units allowed for the visible axes
AXISUNIT_PPM = 'ppm'
AXISUNIT_HZ = 'Hz'
AXISUNIT_POINT = 'point'  # Cannot be 'points' because of the v2-model; Grrrr
AXISUNIT_POINTS = 'points'
AXISUNIT_NUMBER = 'number'
AXISUNITS = (AXISUNIT_PPM, AXISUNIT_HZ, AXISUNIT_POINT)
AXISUNITSPLURAL = [AXISUNIT_PPM, AXISUNIT_HZ, AXISUNIT_POINTS]

#  Units allowed for concentrations (e.g. SampleComponents)
concentrationUnits = ('M', 'mM', 'µM', 'nM', 'pM', 'g/L', 'L/L', 'mol/mol', 'g/g', 'eq', 'sec')

#  Units pre-defined for seriesValues
OTHER_UNITS = ('µ', 'm', 'n', 'p')
CONCENTRATION_UNITS = ('M', 'mM', 'µM', 'nM', 'pM')
VOLUME_UNITS = ('L', 'mL', 'µL', 'nL', 'pL')
MASS_UNITS = ('g', 'mg', 'µg', 'ng', 'pg')
TEMPERATURE_UNITS = ('K',)
TIME_UNITS = ('s', 'ms', 'µs', 'ns', 'ps')
DISTANCE_UNITS = ('µm', 'mm', 'm')
VARIOUS_UNITS = ('', 'EQ', 'AU')
ALL_SERIES_UNITS = VARIOUS_UNITS + TEMPERATURE_UNITS + MASS_UNITS + VOLUME_UNITS + CONCENTRATION_UNITS + DISTANCE_UNITS + TIME_UNITS
AMOUNT_UNITS = VOLUME_UNITS + MASS_UNITS
IONICSTRENGTH_UNITS = CONCENTRATION_UNITS
SAMPLE_STATES = ('Liquid', 'Solid', 'Ordered', 'Powder', 'Crystal', 'Other')
SUBSTANCE_TYPES = ('Molecule', 'Cell', 'Material', 'Composite ', 'Other')
ALL_CONCENTRATION_UNITS = tuple('{}/{}'.format(val, MASS_UNITS[0]) for val in MASS_UNITS) + \
                          tuple('{}/{}'.format(val, VOLUME_UNITS[0]) for val in MASS_UNITS) + \
                          tuple('{}/{}'.format(val, CONCENTRATION_UNITS[0]) for val in MASS_UNITS)

# Default name for natural abundance labelling - given as None externally
DEFAULT_LABELLING = '_NATURAL_ABUNDANCE'

# NB also used from here in ccpnmodel/ccpncore/lib/spectrum/NmrExpProtoType.py
# and ccpnmodel/ccpncore/api/ccp/nmr/ExpPrototype.py.
# TODO remove these dependencies
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

PSEUDO_ATOM_NAME = 'Q'
PSEUDO_ATOM_NAMES = {PSEUDO_ATOM_NAME: '1H'}
PSEUDO_ATOMS = ['QA', 'QB', 'QD', 'QE', 'QG', 'QH', 'QH1', 'QH2', 'QR', 'QZ']

SCALE_PERCENT = 'Percentage'
SCALE_CM_UNIT = 'Cms / unit'
SCALE_UNIT_CM = 'Units / cm'
SCALE_INCH_UNIT = 'Inches / unit'
SCALE_UNIT_INCH = 'Units / inch'
SCALING_MODES = [SCALE_PERCENT, SCALE_CM_UNIT, SCALE_UNIT_CM, SCALE_INCH_UNIT, SCALE_UNIT_INCH]

# GWV 210113: moved to Spectrum class
# # Isotope-dependent assignment tolerances (in ppm)
# defaultAssignmentTolerance = 0.03
# isotope2Tolerance = {
#     '1H' : 0.03,
#     '13C': 0.4,
#     '15N': 0.4,
#     }

# GWV 20210803: moved to util/isotopes.py
# # Chosen to be 1) stable. 2) NMR-active, 3)Spin 1/2, 4) abundant
# # NB keys are ALL-UPPER, as used in names,
# # whereas values are titlecase, as standard for isotopeCodes
# DEFAULT_ISOTOPE_DICT = OrderedDict((
#     ('H', '1H'),
#     ('D', '2H'),
#     ('B', '11B'),
#     ('C', '13C'),
#     ('N', '15N'),
#     ('O', '17O'),
#     ('F', '19F'),
#     ('P', '31P'),
#     ('S', '33S'),
#     ('K', '39K'),
#     ('V', '51V'),
#     ('Y', '89Y'),
#     ('I', '127I'),
#     ('W', '183W'),
#     ('U', '235U'),
#     ('HE', '3He'),
#     ('LI', '7Li'),
#     ('BE', '9Be'),
#     ('NE', '21Ne'),
#     ('NA', '23Na'),
#     ('MG', '25Mg'),
#     ('AL', '27Al'),
#     ('SI', '29Si'),
#     ('CL', '35Cl'),
#     ('AR', '40Ar'),
#     ('CA', '43Ca'),
#     ('SC', '45Sc'),
#     ('TI', '47Ti'),
#     ('CR', '53Cr'),
#     ('MN', '55Mn'),
#     ('FE', '57Fe'),
#     ('CO', '59Co'),
#     ('NI', '61Ni'),
#     ('CU', '63Cu'),
#     ('ZN', '67Zn'),
#     ('GA', '69Ga'),
#     ('GE', '73Ge'),
#     ('AS', '75As'),
#     ('SE', '77Se'),
#     ('BR', '79Br'),
#     ('KR', '83Kr'),
#     ('RB', '85Rb'),
#     ('SR', '87Sr'),
#     ('ZR', '91Zr'),
#     ('NB', '93Nb'),
#     ('MO', '95Mo'),
#     ('TC', '99Tc'),
#     ('RU', '99Ru'),
#     ('RH', '103Rh'),
#     ('PD', '105Pd'),
#     ('AG', '107Ag'),
#     ('CD', '111Cd'),
#     ('IN', '115In'),
#     ('SN', '119Sn'),
#     ('SB', '121Sb'),
#     ('TE', '125Te'),
#     ('XE', '129Xe'),
#     ('CS', '133Cs'),
#     ('BA', '137Ba'),
#     ('LA', '139La'),
#     ('CE', '140Ce'),
#     ('PR', '141Pr'),
#     ('ND', '143Nd'),
#     ('PM', '147Pm'),
#     ('SM', '144Sm'),
#     ('EU', '153Eu'),
#     ('GD', '157Gd'),
#     ('TB', '159Tb'),
#     ('DY', '163Dy'),
#     ('HO', '165Ho'),
#     ('ER', '167Er'),
#     ('TM', '169Tm'),
#     ('YB', '171Yb'),
#     ('LU', '175Lu'),
#     ('HF', '177Hf'),
#     ('TA', '181Ta'),
#     ('RE', '187Re'),
#     ('OS', '187Os'),
#     ('IR', '193Ir'),
#     ('PT', '195Pt'),
#     ('AU', '197Au'),
#     ('HG', '199Hg'),
#     ('TL', '205Tl'),
#     ('PB', '207Pb'),
#     ('BI', '209Bi'),
#     ('PO', '209Po'),
#     ('AC', '227Ac'),
#     ('TH', '232Th'),
#     ('NP', '237Np'),
#     ('PU', '239Pu'),
#     ('AM', '243Am'),
#
#     ('J', None),
#     ('MQ', None),
#     ('delay', None),
#     ('RDC', None),
#     ('ANISO', None),
#     ('TROESY', None),
#     ('DIPOLAR', None),
#     ))

# PriorityIsotopeCodes = ['1H', '13C', '15N', '17O', '19F', '31P']

# IsotopeRecord = namedtuple('IsotopeRecord', (
#     'isotopeCode', 'elementNumber', 'massNumber', 'isRadioactive',
#     'symbol', 'name', 'spin', 'gFactor',
#     'abundance', 'quadrupoleMoment'))

# isotopeRecords = OrderedDict((
#     ('1H', IsotopeRecord('1H', 1, 1, False, 'H', 'Hydrogen', 0.5, 5.58569, 0.999885, 0)),
#     ('2H', IsotopeRecord('2H', 1, 2, False, 'H', 'Hydrogen', 1, 0.857438, 0.000115, 0.00286)),
#     ('3H', IsotopeRecord('3H', 1, 3, True, 'H', 'Hydrogen', 0.5, 5.95799, 0, 0)),
#     ('3He', IsotopeRecord('3He', 2, 3, False, 'He', 'Helium', 0.5, -4.255, 1.37e-06, 0)),
#     ('4He', IsotopeRecord('4He', 2, 4, False, 'He', 'Helium', 0, 0, 0.999999, 0)),
#     ('6Li', IsotopeRecord('6Li', 3, 6, False, 'Li', 'Lithium', 1, 0.822047, 0.0759, -0.000806)),
#     ('7Li', IsotopeRecord('7Li', 3, 7, False, 'Li', 'Lithium', 1.5, 2.17095, 0.9241, -0.04)),
#     ('9Be', IsotopeRecord('9Be', 4, 9, False, 'Be', 'Beryllium', 1.5, -0.78495, 1, 0.0529)),
#     ('10B', IsotopeRecord('10B', 5, 10, False, 'B', 'Boron', 3, 0.600215, 0.199, 0.0845)),
#     ('11B', IsotopeRecord('11B', 5, 11, False, 'B', 'Boron', 1.5, 1.79243, 0.801, 0.04059)),
#     ('12C', IsotopeRecord('12C', 6, 12, False, 'C', 'Carbon', 0, 0, 0.9893, 0)),
#     ('13C', IsotopeRecord('13C', 6, 13, False, 'C', 'Carbon', 0.5, 1.40482, 0.0107, 0)),
#     ('14C', IsotopeRecord('14C', 6, 14, True, 'C', 'Carbon', 3, 0.273, 0, None)),
#     ('14N', IsotopeRecord('14N', 7, 14, False, 'N', 'Nitrogen', 1, 0.403761, 0.99632, 0.02044)),
#     ('15N', IsotopeRecord('15N', 7, 15, False, 'N', 'Nitrogen', 0.5, -0.566378, 0.00368, 0)),
#     ('16O', IsotopeRecord('16O', 8, 16, False, 'O', 'Oxygen', 0, 0, 0.99757, 0)),
#     ('17O', IsotopeRecord('17O', 8, 17, False, 'O', 'Oxygen', 2.5, -0.757516, 0.00038, -0.0256)),
#     ('18O', IsotopeRecord('18O', 8, 18, True, 'O', 'Oxygen', 0, 0, 0.00205, 0)),
#     ('19F', IsotopeRecord('19F', 9, 19, False, 'F', 'Fluorine', 0.5, 5.25774, 1, 0)),
#     ('20Ne', IsotopeRecord('20Ne', 10, 20, False, 'Ne', 'Neon', 0, 0, 0.9048, 0)),
#     ('21Ne', IsotopeRecord('21Ne', 10, 21, False, 'Ne', 'Neon', 1.5, -0.441198, 0.0027, 0.102)),
#     ('22Ne', IsotopeRecord('22Ne', 10, 22, False, 'Ne', 'Neon', 0, 0, 0.0925, 0)),
#     ('22Na', IsotopeRecord('22Na', 11, 22, True, 'Na', 'Sodium', 3, 0.582, 0, 0.18)),
#     ('23Na', IsotopeRecord('23Na', 11, 23, False, 'Na', 'Sodium', 1.5, 1.47835, 1, 0.104)),
#     ('24Mg', IsotopeRecord('24Mg', 12, 24, False, 'Mg', 'Magnesium', 0, 0, 0.7899, 0)),
#     ('25Mg', IsotopeRecord('25Mg', 12, 25, False, 'Mg', 'Magnesium', 2.5, -0.34218, 0.1, 0.199)),
#     ('26Mg', IsotopeRecord('26Mg', 12, 26, False, 'Mg', 'Magnesium', 0, 0, 0.1101, 0)),
#     ('27Al', IsotopeRecord('27Al', 13, 27, False, 'Al', 'Aluminium', 2.5, 1.4566, 1, 0.1466)),
#     ('28Si', IsotopeRecord('28Si', 14, 28, False, 'Si', 'Silicon', 0, 0, 0.922297, 0)),
#     ('29Si', IsotopeRecord('29Si', 14, 29, False, 'Si', 'Silicon', 0.5, -1.11058, 0.046832, 0)),
#     ('30Si', IsotopeRecord('30Si', 14, 30, False, 'Si', 'Silicon', 0, 0, 0.030872, 0)),
#     ('31P', IsotopeRecord('31P', 15, 31, False, 'P', 'Phosphorus', 0.5, 2.2632, 1, 0)),
#     ('32S', IsotopeRecord('32S', 16, 32, False, 'S', 'Sulfur', 0, 0, 0.9493, 0)),
#     ('33S', IsotopeRecord('33S', 16, 33, False, 'S', 'Sulfur', 1.5, 0.429214, 0.0076, -0.0678)),
#     ('34S', IsotopeRecord('34S', 16, 34, False, 'S', 'Sulfur', 0, 0, 0.0429, 0)),
#     ('36S', IsotopeRecord('36S', 16, 36, False, 'S', 'Sulfur', 0, 0, 0.0002, 0)),
#     ('35Cl', IsotopeRecord('35Cl', 17, 35, False, 'Cl', 'Chlorine', 1.5, 0.547916, 0.7578, -0.0817)),
#     ('36Cl', IsotopeRecord('36Cl', 17, 36, True, 'Cl', 'Chlorine', 2, 0.642735, 0, -0.0178)),
#     ('37Cl', IsotopeRecord('37Cl', 17, 37, False, 'Cl', 'Chlorine', 1.5, 0.456082, 0.2422, -0.0644)),
#     ('36Ar', IsotopeRecord('36Ar', 18, 36, False, 'Ar', 'Argon', 0, 0, 0.003365, 0)),
#     ('38Ar', IsotopeRecord('38Ar', 18, 38, False, 'Ar', 'Argon', 0, 0, 0.000632, 0)),
#     ('39Ar', IsotopeRecord('39Ar', 18, 39, True, 'Ar', 'Argon', 3.5, -0.4537, 0, -0.12)),
#     ('40Ar', IsotopeRecord('40Ar', 18, 40, False, 'Ar', 'Argon', 0, 0, 0.996003, 0)),
#     ('39K', IsotopeRecord('39K', 19, 39, False, 'K', 'Potassium', 1.5, 0.26098, 0.932581, 0.0585)),
#     ('40K', IsotopeRecord('40K', 19, 40, False, 'K', 'Potassium', 4, -0.324525, 0.000117, -0.073)),
#     ('41K', IsotopeRecord('41K', 19, 41, False, 'K', 'Potassium', 1.5, 0.143247, 0.067302, 0.0711)),
#     ('40Ca', IsotopeRecord('40Ca', 20, 40, False, 'Ca', 'Calcium', 0, 0, 0.96941, 0)),
#     ('41Ca', IsotopeRecord('41Ca', 20, 41, True, 'Ca', 'Calcium', 3.5, -0.455652, 0, -0.0665)),
#     ('42Ca', IsotopeRecord('42Ca', 20, 42, False, 'Ca', 'Calcium', 0, 0, 0.00647, 0)),
#     ('43Ca', IsotopeRecord('43Ca', 20, 43, False, 'Ca', 'Calcium', 3.5, -0.37637, 0.00135, -0.0408)),
#     ('44Ca', IsotopeRecord('44Ca', 20, 44, False, 'Ca', 'Calcium', 0, 0, 0.02086, 0)),
#     ('46Ca', IsotopeRecord('46Ca', 20, 46, False, 'Ca', 'Calcium', 0, 0, 4e-05, 0)),
#     ('48Ca', IsotopeRecord('48Ca', 20, 48, False, 'Ca', 'Calcium', 0, 0, 0.00187, 0)),
#     ('45Sc', IsotopeRecord('45Sc', 21, 45, False, 'Sc', 'Scandium', 3.5, 1.35899, 1, -0.22)),
#     ('46Ti', IsotopeRecord('46Ti', 22, 46, False, 'Ti', 'Titanium', 0, 0, 0.0825, 0)),
#     ('47Ti', IsotopeRecord('47Ti', 22, 47, False, 'Ti', 'Titanium', 2.5, -0.31539, 0.0744, 0.302)),
#     ('48Ti', IsotopeRecord('48Ti', 22, 48, False, 'Ti', 'Titanium', 0, 0, 0.7372, 0)),
#     ('49Ti', IsotopeRecord('49Ti', 22, 49, False, 'Ti', 'Titanium', 3.5, -0.315477, 0.0541, 0.247)),
#     ('50Ti', IsotopeRecord('50Ti', 22, 50, False, 'Ti', 'Titanium', 0, 0, 0.0518, 0)),
#     ('50V', IsotopeRecord('50V', 23, 50, False, 'V', 'Vanadium', 6, 0.557615, 0.0025, 0.21)),
#     ('51V', IsotopeRecord('51V', 23, 51, False, 'V', 'Vanadium', 3.5, 1.47106, 0.9975, -0.043)),
#     ('50Cr', IsotopeRecord('50Cr', 24, 50, False, 'Cr', 'Chromium', 0, 0, 0.04345, 0)),
#     ('52Cr', IsotopeRecord('52Cr', 24, 52, False, 'Cr', 'Chromium', 0, 0, 0.83789, 0)),
#     ('53Cr', IsotopeRecord('53Cr', 24, 53, False, 'Cr', 'Chromium', 1.5, -0.31636, 0.09501, -0.15)),
#     ('54Cr', IsotopeRecord('54Cr', 24, 54, False, 'Cr', 'Chromium', 0, 0, 0.02365, 0)),
#     ('53Mn', IsotopeRecord('53Mn', 25, 53, True, 'Mn', 'Manganese', 3.5, 1.439, 0, 0.17)),
#     ('55Mn', IsotopeRecord('55Mn', 25, 55, False, 'Mn', 'Manganese', 2.5, 1.3813, 1, 0.33)),
#     ('54Fe', IsotopeRecord('54Fe', 26, 54, False, 'Fe', 'Iron', 0, 0, 0.05845, 0)),
#     ('56Fe', IsotopeRecord('56Fe', 26, 56, False, 'Fe', 'Iron', 0, 0, 0.91754, 0)),
#     ('57Fe', IsotopeRecord('57Fe', 26, 57, False, 'Fe', 'Iron', 0.5, 0.1809, 0.02119, 0)),
#     ('58Fe', IsotopeRecord('58Fe', 26, 58, False, 'Fe', 'Iron', 0, 0, 0.00282, 0)),
#     ('59Co', IsotopeRecord('59Co', 27, 59, False, 'Co', 'Cobalt', 3.5, 1.322, 1, 0.42)),
#     ('60Co', IsotopeRecord('60Co', 27, 60, True, 'Co', 'Cobalt', 5, 0.7598, 0, 0.46)),
#     ('58Ni', IsotopeRecord('58Ni', 28, 58, False, 'Ni', 'Nickel', 0, 0, 0.680769, 0)),
#     ('60Ni', IsotopeRecord('60Ni', 28, 60, False, 'Ni', 'Nickel', 0, 0, 0.262231, 0)),
#     ('61Ni', IsotopeRecord('61Ni', 28, 61, False, 'Ni', 'Nickel', 1.5, -0.50001, 0.011399, 0.162)),
#     ('62Ni', IsotopeRecord('62Ni', 28, 62, False, 'Ni', 'Nickel', 0, 0, 0.036345, 0)),
#     ('64Ni', IsotopeRecord('64Ni', 28, 64, False, 'Ni', 'Nickel', 0, 0, 0.009256, 0)),
#     ('63Cu', IsotopeRecord('63Cu', 29, 63, False, 'Cu', 'Copper', 1.5, 1.4824, 0.6917, -0.22)),
#     ('65Cu', IsotopeRecord('65Cu', 29, 65, False, 'Cu', 'Copper', 1.5, 1.5878, 0.3083, -0.204)),
#     ('64Zn', IsotopeRecord('64Zn', 30, 64, False, 'Zn', 'Zinc', 0, 0, 0.4863, 0)),
#     ('66Zn', IsotopeRecord('66Zn', 30, 66, False, 'Zn', 'Zinc', 0, 0, 0.279, 0)),
#     ('67Zn', IsotopeRecord('67Zn', 30, 67, False, 'Zn', 'Zinc', 2.5, 0.350192, 0.041, 0.15)),
#     ('68Zn', IsotopeRecord('68Zn', 30, 68, False, 'Zn', 'Zinc', 0, 0, 0.1875, 0)),
#     ('70Zn', IsotopeRecord('70Zn', 30, 70, False, 'Zn', 'Zinc', 0, 0, 0.0062, 0)),
#     ('69Ga', IsotopeRecord('69Ga', 31, 69, False, 'Ga', 'Gallium', 1.5, 1.34439, 0.60108, 0.171)),
#     ('71Ga', IsotopeRecord('71Ga', 31, 71, False, 'Ga', 'Gallium', 1.5, 1.70818, 0.39892, 0.107)),
#     ('70Ge', IsotopeRecord('70Ge', 32, 70, False, 'Ge', 'Germanium', 0, 0, 0.2084, 0)),
#     ('72Ge', IsotopeRecord('72Ge', 32, 72, False, 'Ge', 'Germanium', 0, 0, 0.2754, 0)),
#     ('73Ge', IsotopeRecord('73Ge', 32, 73, False, 'Ge', 'Germanium', 4.5, -0.195437, 0.0773, -0.19)),
#     ('74Ge', IsotopeRecord('74Ge', 32, 74, False, 'Ge', 'Germanium', 0, 0, 0.3628, 0)),
#     ('76Ge', IsotopeRecord('76Ge', 32, 76, False, 'Ge', 'Germanium', 0, 0, 0.0761, 0)),
#     ('75As', IsotopeRecord('75As', 33, 75, False, 'As', 'Arsenic', 1.5, 0.95965, 1, 0.314)),
#     ('74Se', IsotopeRecord('74Se', 34, 74, False, 'Se', 'Selenium', 0, 0, 0.0089, 0)),
#     ('76Se', IsotopeRecord('76Se', 34, 76, False, 'Se', 'Selenium', 0, 0, 0.0937, 0)),
#     ('77Se', IsotopeRecord('77Se', 34, 77, False, 'Se', 'Selenium', 0.5, 1.07008, 0.0763, 0)),
#     ('78Se', IsotopeRecord('78Se', 34, 78, False, 'Se', 'Selenium', 0, 0, 0.2377, 0)),
#     ('79Se', IsotopeRecord('79Se', 34, 79, True, 'Se', 'Selenium', 3.5, -0.29, 0, 0.8)),
#     ('80Se', IsotopeRecord('80Se', 34, 80, False, 'Se', 'Selenium', 0, 0, 0.4961, 0)),
#     ('82Se', IsotopeRecord('82Se', 34, 82, False, 'Se', 'Selenium', 0, 0, 0.0873, 0)),
#     ('79Br', IsotopeRecord('79Br', 35, 79, False, 'Br', 'Bromine', 1.5, 1.40427, 0.5069, 0.313)),
#     ('81Br', IsotopeRecord('81Br', 35, 81, False, 'Br', 'Bromine', 1.5, 1.51371, 0.4931, 0.262)),
#     ('78Kr', IsotopeRecord('78Kr', 36, 78, False, 'Kr', 'Krypton', 0, 0, 0.0035, 0)),
#     ('80Kr', IsotopeRecord('80Kr', 36, 80, False, 'Kr', 'Krypton', 0, 0, 0.0228, 0)),
#     ('82Kr', IsotopeRecord('82Kr', 36, 82, False, 'Kr', 'Krypton', 0, 0, 0.1158, 0)),
#     ('83Kr', IsotopeRecord('83Kr', 36, 83, False, 'Kr', 'Krypton', 4.5, -0.215704, 0.1149, 0.259)),
#     ('84Kr', IsotopeRecord('84Kr', 36, 84, False, 'Kr', 'Krypton', 0, 0, 0.57, 0)),
#     ('85Kr', IsotopeRecord('85Kr', 36, 85, True, 'Kr', 'Krypton', 4.5, -0.2233, 0, 0.443)),
#     ('86Kr', IsotopeRecord('86Kr', 36, 86, False, 'Kr', 'Krypton', 0, 0, 0.173, 0)),
#     ('85Rb', IsotopeRecord('85Rb', 37, 85, False, 'Rb', 'Rubidium', 2.5, 0.541192, 0.7217, 0.276)),
#     ('87Rb', IsotopeRecord('87Rb', 37, 87, False, 'Rb', 'Rubidium', 1.5, 1.83421, 0.2783, 0.1335)),
#     ('84Sr', IsotopeRecord('84Sr', 38, 84, False, 'Sr', 'Strontium', 0, 0, 0.0056, 0)),
#     ('86Sr', IsotopeRecord('86Sr', 38, 86, False, 'Sr', 'Strontium', 0, 0, 0.0986, 0)),
#     ('87Sr', IsotopeRecord('87Sr', 38, 87, False, 'Sr', 'Strontium', 4.5, -0.24284, 0.07, 0.305)),
#     ('88Sr', IsotopeRecord('88Sr', 38, 88, False, 'Sr', 'Strontium', 0, 0, 0.8258, 0)),
#     ('89Y', IsotopeRecord('89Y', 39, 89, False, 'Y', 'Yttrium', 0.5, -0.274831, 1, 0)),
#     ('90Zr', IsotopeRecord('90Zr', 40, 90, False, 'Zr', 'Zirconium', 0, 0, 0.5145, 0)),
#     ('91Zr', IsotopeRecord('91Zr', 40, 91, False, 'Zr', 'Zirconium', 2.5, -0.521448, 0.1122, -0.176)),
#     ('92Zr', IsotopeRecord('92Zr', 40, 92, False, 'Zr', 'Zirconium', 0, 0, 0.1715, 0)),
#     ('94Zr', IsotopeRecord('94Zr', 40, 94, False, 'Zr', 'Zirconium', 0, 0, 0.1738, 0)),
#     ('96Zr', IsotopeRecord('96Zr', 40, 96, False, 'Zr', 'Zirconium', 0, 0, 0.028, 0)),
#     ('93Nb', IsotopeRecord('93Nb', 41, 93, False, 'Nb', 'Niobium', 4.5, 1.3712, 1, -0.32)),
#     ('92Mo', IsotopeRecord('92Mo', 42, 92, False, 'Mo', 'Molybdenum', 0, 0, 0.1484, 0)),
#     ('94Mo', IsotopeRecord('94Mo', 42, 94, False, 'Mo', 'Molybdenum', 0, 0, 0.0925, 0)),
#     ('95Mo', IsotopeRecord('95Mo', 42, 95, False, 'Mo', 'Molybdenum', 2.5, -0.3657, 0.1592, -0.022)),
#     ('96Mo', IsotopeRecord('96Mo', 42, 96, False, 'Mo', 'Molybdenum', 0, 0, 0.1668, 0)),
#     ('97Mo', IsotopeRecord('97Mo', 42, 97, False, 'Mo', 'Molybdenum', 2.5, -0.3734, 0.0955, 0.255)),
#     ('98Mo', IsotopeRecord('98Mo', 42, 98, False, 'Mo', 'Molybdenum', 0, 0, 0.2413, 0)),
#     ('100Mo', IsotopeRecord('100Mo', 42, 100, False, 'Mo', 'Molybdenum', 0, 0, 0.0963, 0)),
#     ('99Tc', IsotopeRecord('99Tc', 43, 99, True, 'Tc', 'Technetium', 4.5, 1.2632, 0, -0.129)),
#     ('96Ru', IsotopeRecord('96Ru', 44, 96, False, 'Ru', 'Ruthenium', 0, 0, 0.0554, 0)),
#     ('98Ru', IsotopeRecord('98Ru', 44, 98, False, 'Ru', 'Ruthenium', 0, 0, 0.0187, 0)),
#     ('99Ru', IsotopeRecord('99Ru', 44, 99, False, 'Ru', 'Ruthenium', 2.5, -0.256, 0.1276, 0.079)),
#     ('100Ru', IsotopeRecord('100Ru', 44, 100, False, 'Ru', 'Ruthenium', 0, 0, 0.126, 0)),
#     ('101Ru', IsotopeRecord('101Ru', 44, 101, False, 'Ru', 'Ruthenium', 2.5, -0.288, 0.1706, 0.46)),
#     ('102Ru', IsotopeRecord('102Ru', 44, 102, False, 'Ru', 'Ruthenium', 0, 0, 0.3155, 0)),
#     ('104Ru', IsotopeRecord('104Ru', 44, 104, False, 'Ru', 'Ruthenium', 0, 0, 0.1862, 0)),
#     ('103Rh', IsotopeRecord('103Rh', 45, 103, False, 'Rh', 'Rhodium', 0.5, -0.1768, 1, 0)),
#     ('102Pd', IsotopeRecord('102Pd', 46, 102, False, 'Pd', 'Palladium', 0, 0, 0.0102, 0)),
#     ('104Pd', IsotopeRecord('104Pd', 46, 104, False, 'Pd', 'Palladium', 0, 0, 0.1114, 0)),
#     ('105Pd', IsotopeRecord('105Pd', 46, 105, False, 'Pd', 'Palladium', 2.5, -0.257, 0.2233, 0.66)),
#     ('106Pd', IsotopeRecord('106Pd', 46, 106, False, 'Pd', 'Palladium', 0, 0, 0.2733, 0)),
#     ('108Pd', IsotopeRecord('108Pd', 46, 108, False, 'Pd', 'Palladium', 0, 0, 0.2646, 0)),
#     ('110Pd', IsotopeRecord('110Pd', 46, 110, False, 'Pd', 'Palladium', 0, 0, 0.1172, 0)),
#     ('107Ag', IsotopeRecord('107Ag', 47, 107, False, 'Ag', 'Silver', 0.5, -0.22714, 0.51839, 0)),
#     ('109Ag', IsotopeRecord('109Ag', 47, 109, False, 'Ag', 'Silver', 0.5, -0.26112, 0.48161, 0)),
#     ('106Cd', IsotopeRecord('106Cd', 48, 106, False, 'Cd', 'Cadmium', 0, 0, 0.0125, 0)),
#     ('108Cd', IsotopeRecord('108Cd', 48, 108, False, 'Cd', 'Cadmium', 0, 0, 0.0089, 0)),
#     ('110Cd', IsotopeRecord('110Cd', 48, 110, False, 'Cd', 'Cadmium', 0, 0, 0.1249, 0)),
#     ('111Cd', IsotopeRecord('111Cd', 48, 111, False, 'Cd', 'Cadmium', 0.5, -1.18977, 0.128, 0)),
#     ('112Cd', IsotopeRecord('112Cd', 48, 112, False, 'Cd', 'Cadmium', 0, 0, 0.2413, 0)),
#     ('113Cd', IsotopeRecord('113Cd', 48, 113, False, 'Cd', 'Cadmium', 0.5, -1.2446, 0.1222, 0)),
#     ('114Cd', IsotopeRecord('114Cd', 48, 114, False, 'Cd', 'Cadmium', 0, 0, 0.2873, 0)),
#     ('116Cd', IsotopeRecord('116Cd', 48, 116, False, 'Cd', 'Cadmium', 0, 0, 0.0749, 0)),
#     ('113In', IsotopeRecord('113In', 49, 113, False, 'In', 'Indium', 4.5, 1.2286, 0.0429, 0.759)),
#     ('115In', IsotopeRecord('115In', 49, 115, False, 'In', 'Indium', 4.5, 1.2313, 0.9571, 0.77)),
#     ('112Sn', IsotopeRecord('112Sn', 50, 112, False, 'Sn', 'Tin', 0, 0, 0.0097, 0)),
#     ('114Sn', IsotopeRecord('114Sn', 50, 114, False, 'Sn', 'Tin', 0, 0, 0.0066, 0)),
#     ('115Sn', IsotopeRecord('115Sn', 50, 115, False, 'Sn', 'Tin', 0.5, -1.8377, 0.0034, 0)),
#     ('116Sn', IsotopeRecord('116Sn', 50, 116, False, 'Sn', 'Tin', 0, 0, 0.1454, 0)),
#     ('117Sn', IsotopeRecord('117Sn', 50, 117, False, 'Sn', 'Tin', 0.5, -2.00208, 0.0768, 0)),
#     ('118Sn', IsotopeRecord('118Sn', 50, 118, False, 'Sn', 'Tin', 0, 0, 0.2422, 0)),
#     ('119Sn', IsotopeRecord('119Sn', 50, 119, False, 'Sn', 'Tin', 0.5, -2.09456, 0.0859, 0)),
#     ('120Sn', IsotopeRecord('120Sn', 50, 120, False, 'Sn', 'Tin', 0, 0, 0.3258, 0)),
#     ('122Sn', IsotopeRecord('122Sn', 50, 122, False, 'Sn', 'Tin', 0, 0, 0.0463, 0)),
#     ('124Sn', IsotopeRecord('124Sn', 50, 124, False, 'Sn', 'Tin', 0, 0, 0.0579, 0)),
#     ('121Sb', IsotopeRecord('121Sb', 51, 121, False, 'Sb', 'Antimony', 2.5, 1.3454, 0.5721, -0.543)),
#     ('123Sb', IsotopeRecord('123Sb', 51, 123, False, 'Sb', 'Antimony', 3.5, 0.72851, 0.4279, -0.692)),
#     ('125Sb', IsotopeRecord('125Sb', 51, 125, True, 'Sb', 'Antimony', 3.5, 0.751, 0, None)),
#     ('120Te', IsotopeRecord('120Te', 52, 120, False, 'Te', 'Tellurium', 0, 0, 0.0009, 0)),
#     ('122Te', IsotopeRecord('122Te', 52, 122, False, 'Te', 'Tellurium', 0, 0, 0.0255, 0)),
#     ('123Te', IsotopeRecord('123Te', 52, 123, False, 'Te', 'Tellurium', 0.5, -1.4739, 0.0089, 0)),
#     ('124Te', IsotopeRecord('124Te', 52, 124, False, 'Te', 'Tellurium', 0, 0, 0.0474, 0)),
#     ('125Te', IsotopeRecord('125Te', 52, 125, False, 'Te', 'Tellurium', 0.5, -1.77701, 0.0707, 0)),
#     ('126Te', IsotopeRecord('126Te', 52, 126, False, 'Te', 'Tellurium', 0, 0, 0.1884, 0)),
#     ('128Te', IsotopeRecord('128Te', 52, 128, False, 'Te', 'Tellurium', 0, 0, 0.3174, 0)),
#     ('130Te', IsotopeRecord('130Te', 52, 130, False, 'Te', 'Tellurium', 0, 0, 0.3408, 0)),
#     ('127I', IsotopeRecord('127I', 53, 127, False, 'I', 'Iodine', 2.5, 1.12531, 1, -0.696)),
#     ('129I', IsotopeRecord('129I', 53, 129, True, 'I', 'Iodine', 3.5, 0.74886, 0, -0.488)),
#     ('124Xe', IsotopeRecord('124Xe', 54, 124, False, 'Xe', 'Xenon', 0, 0, 0.0009, 0)),
#     ('126Xe', IsotopeRecord('126Xe', 54, 126, False, 'Xe', 'Xenon', 0, 0, 0.0009, 0)),
#     ('128Xe', IsotopeRecord('128Xe', 54, 128, False, 'Xe', 'Xenon', 0, 0, 0.0192, 0)),
#     ('129Xe', IsotopeRecord('129Xe', 54, 129, False, 'Xe', 'Xenon', 0.5, -1.55595, 0.2644, 0)),
#     ('130Xe', IsotopeRecord('130Xe', 54, 130, False, 'Xe', 'Xenon', 0, 0, 0.0408, 0)),
#     ('131Xe', IsotopeRecord('131Xe', 54, 131, False, 'Xe', 'Xenon', 1.5, 0.461, 0.2118, -0.114)),
#     ('132Xe', IsotopeRecord('132Xe', 54, 132, False, 'Xe', 'Xenon', 0, 0, 0.2689, 0)),
#     ('134Xe', IsotopeRecord('134Xe', 54, 134, False, 'Xe', 'Xenon', 0, 0, 0.1044, 0)),
#     ('136Xe', IsotopeRecord('136Xe', 54, 136, False, 'Xe', 'Xenon', 0, 0, 0.0887, 0)),
#     ('133Cs', IsotopeRecord('133Cs', 55, 133, False, 'Cs', 'Caesium', 3.5, 0.737721, 1, -0.00343)),
#     ('134Cs', IsotopeRecord('134Cs', 55, 134, True, 'Cs', 'Caesium', 4, 0.74843, 0, 0.37)),
#     ('135Cs', IsotopeRecord('135Cs', 55, 135, True, 'Cs', 'Caesium', 3.5, 0.78069, 0, 0.048)),
#     ('137Cs', IsotopeRecord('137Cs', 55, 137, True, 'Cs', 'Caesium', 3.5, 0.81466, 0, 0.048)),
#     ('130Ba', IsotopeRecord('130Ba', 56, 130, False, 'Ba', 'Barium', 0, 0, 0.00106, 0)),
#     ('132Ba', IsotopeRecord('132Ba', 56, 132, False, 'Ba', 'Barium', 0, 0, 0.00101, 0)),
#     ('133Ba', IsotopeRecord('133Ba', 56, 133, True, 'Ba', 'Barium', 0.5, -1.5433, 0, 0)),
#     ('134Ba', IsotopeRecord('134Ba', 56, 134, False, 'Ba', 'Barium', 0, 0, 0.02417, 0)),
#     ('135Ba', IsotopeRecord('135Ba', 56, 135, False, 'Ba', 'Barium', 1.5, 0.55863, 0.06592, 0.16)),
#     ('136Ba', IsotopeRecord('136Ba', 56, 136, False, 'Ba', 'Barium', 0, 0, 0.07854, 0)),
#     ('137Ba', IsotopeRecord('137Ba', 56, 137, False, 'Ba', 'Barium', 1.5, 0.62491, 0.11232, 0.245)),
#     ('138Ba', IsotopeRecord('138Ba', 56, 138, False, 'Ba', 'Barium', 0, 0, 0.71698, 0)),
#     ('137La', IsotopeRecord('137La', 57, 137, True, 'La', 'Lanthanum', 3.5, 0.7714, 0, 0.21)),
#     ('138La', IsotopeRecord('138La', 57, 138, False, 'La', 'Lanthanum', 5, 0.742729, 0.0009, 0.39)),
#     ('139La', IsotopeRecord('139La', 57, 139, False, 'La', 'Lanthanum', 3.5, 0.795156, 0.9991, 0.2)),
#     ('136Ce', IsotopeRecord('136Ce', 58, 136, False, 'Ce', 'Cerium', 0, 0, 0.00185, 0)),
#     ('138Ce', IsotopeRecord('138Ce', 58, 138, False, 'Ce', 'Cerium', 0, 0, 0.00251, 0)),
#     ('140Ce', IsotopeRecord('140Ce', 58, 140, False, 'Ce', 'Cerium', 0, 0, 0.8845, 0)),
#     ('142Ce', IsotopeRecord('142Ce', 58, 142, False, 'Ce', 'Cerium', 0, 0, 0.11114, 0)),
#     ('141Pr', IsotopeRecord('141Pr', 59, 141, False, 'Pr', 'Praesodymium', 2.5, 1.7102, 1, -0.077)),
#     ('142Nd', IsotopeRecord('142Nd', 60, 142, False, 'Nd', 'Neodymium', 0, 0, 0.272, 0)),
#     ('143Nd', IsotopeRecord('143Nd', 60, 143, False, 'Nd', 'Neodymium', 3.5, -0.3043, 0.122, -0.61)),
#     ('144Nd', IsotopeRecord('144Nd', 60, 144, False, 'Nd', 'Neodymium', 0, 0, 0.238, 0)),
#     ('145Nd', IsotopeRecord('145Nd', 60, 145, False, 'Nd', 'Neodymium', 3.5, -0.187, 0.083, -0.314)),
#     ('146Nd', IsotopeRecord('146Nd', 60, 146, False, 'Nd', 'Neodymium', 0, 0, 0.172, 0)),
#     ('148Nd', IsotopeRecord('148Nd', 60, 148, False, 'Nd', 'Neodymium', 0, 0, 0.057, 0)),
#     ('150Nd', IsotopeRecord('150Nd', 60, 150, False, 'Nd', 'Neodymium', 0, 0, 0.056, 0)),
#     ('147Pm', IsotopeRecord('147Pm', 61, 147, True, 'Pm', 'Promethium', 3.5, 0.737, 0, 0.74)),
#     ('144Sm', IsotopeRecord('144Sm', 62, 144, False, 'Sm', 'Samarium', 0, 0, 0.0307, 0)),
#     ('147Sm', IsotopeRecord('147Sm', 62, 147, False, 'Sm', 'Samarium', 3.5, -0.232, 0.1499, -0.26)),
#     ('148Sm', IsotopeRecord('148Sm', 62, 148, False, 'Sm', 'Samarium', 0, 0, 0.1124, 0)),
#     ('149Sm', IsotopeRecord('149Sm', 62, 149, False, 'Sm', 'Samarium', 3.5, -0.1908, 0.1382, 0.078)),
#     ('150Sm', IsotopeRecord('150Sm', 62, 150, False, 'Sm', 'Samarium', 0, 0, 0.0738, 0)),
#     ('151Sm', IsotopeRecord('151Sm', 62, 151, True, 'Sm', 'Samarium', 2.5, 0.1444, 0, 0.71)),
#     ('152Sm', IsotopeRecord('152Sm', 62, 152, False, 'Sm', 'Samarium', 0, 0, 0.2675, 0)),
#     ('154Sm', IsotopeRecord('154Sm', 62, 154, False, 'Sm', 'Samarium', 0, 0, 0.2275, 0)),
#     ('151Eu', IsotopeRecord('151Eu', 63, 151, False, 'Eu', 'Europium', 2.5, 1.3887, 0.4781, 0.903)),
#     ('152Eu', IsotopeRecord('152Eu', 63, 152, True, 'Eu', 'Europium', 3, -0.6467, 0, 2.72)),
#     ('153Eu', IsotopeRecord('153Eu', 63, 153, False, 'Eu', 'Europium', 2.5, 0.6134, 0.5219, 2.41)),
#     ('154Eu', IsotopeRecord('154Eu', 63, 154, True, 'Eu', 'Europium', 3, -0.6683, 0, 2.85)),
#     ('155Eu', IsotopeRecord('155Eu', 63, 155, True, 'Eu', 'Europium', 2.5, 0.608, 0, 2.5)),
#     ('152Gd', IsotopeRecord('152Gd', 64, 152, False, 'Gd', 'Gadolinium', 0, 0, 0.002, 0)),
#     ('154Gd', IsotopeRecord('154Gd', 64, 154, False, 'Gd', 'Gadolinium', 0, 0, 0.0218, 0)),
#     ('155Gd', IsotopeRecord('155Gd', 64, 155, False, 'Gd', 'Gadolinium', 1.5, -0.1715, 0.148, 1.27)),
#     ('156Gd', IsotopeRecord('156Gd', 64, 156, False, 'Gd', 'Gadolinium', 0, 0, 0.2047, 0)),
#     ('157Gd', IsotopeRecord('157Gd', 64, 157, False, 'Gd', 'Gadolinium', 1.5, -0.2265, 0.1565, 1.35)),
#     ('158Gd', IsotopeRecord('158Gd', 64, 158, False, 'Gd', 'Gadolinium', 0, 0, 0.2484, 0)),
#     ('160Gd', IsotopeRecord('160Gd', 64, 160, False, 'Gd', 'Gadolinium', 0, 0, 0.2186, 0)),
#     ('157Tb', IsotopeRecord('157Tb', 65, 157, True, 'Tb', 'Terbium', 1.5, 1.34, 0, 1.4)),
#     ('159Tb', IsotopeRecord('159Tb', 65, 159, False, 'Tb', 'Terbium', 1.5, 1.343, 1, 1.432)),
#     ('160Tb', IsotopeRecord('160Tb', 65, 160, True, 'Tb', 'Terbium', 3, 0.5967, 0, 3.85)),
#     ('156Dy', IsotopeRecord('156Dy', 66, 156, False, 'Dy', 'Dysprosium', 0, 0, 0.0006, 0)),
#     ('158Dy', IsotopeRecord('158Dy', 66, 158, False, 'Dy', 'Dysprosium', 0, 0, 0.001, 0)),
#     ('160Dy', IsotopeRecord('160Dy', 66, 160, False, 'Dy', 'Dysprosium', 0, 0, 0.0234, 0)),
#     ('161Dy', IsotopeRecord('161Dy', 66, 161, False, 'Dy', 'Dysprosium', 2.5, -0.192, 0.1891, 2.51)),
#     ('162Dy', IsotopeRecord('162Dy', 66, 162, False, 'Dy', 'Dysprosium', 0, 0, 0.2551, 0)),
#     ('163Dy', IsotopeRecord('163Dy', 66, 163, False, 'Dy', 'Dysprosium', 2.5, 0.269, 0.249, 2.65)),
#     ('164Dy', IsotopeRecord('164Dy', 66, 164, False, 'Dy', 'Dysprosium', 0, 0, 0.2818, 0)),
#     ('165Ho', IsotopeRecord('165Ho', 67, 165, False, 'Ho', 'Holmium', 3.5, 1.668, 1, 3.58)),
#     ('162Er', IsotopeRecord('162Er', 68, 162, False, 'Er', 'Erbium', 0, 0, 0.0014, 0)),
#     ('164Er', IsotopeRecord('164Er', 68, 164, False, 'Er', 'Erbium', 0, 0, 0.0161, 0)),
#     ('166Er', IsotopeRecord('166Er', 68, 166, False, 'Er', 'Erbium', 0, 0, 0.3361, 0)),
#     ('167Er', IsotopeRecord('167Er', 68, 167, False, 'Er', 'Erbium', 3.5, -0.1611, 0.2293, 3.57)),
#     ('168Er', IsotopeRecord('168Er', 68, 168, False, 'Er', 'Erbium', 0, 0, 0.2678, 0)),
#     ('170Er', IsotopeRecord('170Er', 68, 170, False, 'Er', 'Erbium', 0, 0, 0.1493, 0)),
#     ('169Tm', IsotopeRecord('169Tm', 69, 169, False, 'Tm', 'Thulium', 0.5, -0.462, 1, 0)),
#     ('171Tm', IsotopeRecord('171Tm', 69, 171, True, 'Tm', 'Thulium', 0.5, -0.456, 0, 0)),
#     ('168Yb', IsotopeRecord('168Yb', 70, 168, False, 'Yb', 'Ytterbium', 0, 0, 0.0013, 0)),
#     ('170Yb', IsotopeRecord('170Yb', 70, 170, False, 'Yb', 'Ytterbium', 0, 0, 0.0304, 0)),
#     ('171Yb', IsotopeRecord('171Yb', 70, 171, False, 'Yb', 'Ytterbium', 0.5, 0.98734, 0.1428, 0)),
#     ('172Yb', IsotopeRecord('172Yb', 70, 172, False, 'Yb', 'Ytterbium', 0, 0, 0.2183, 0)),
#     ('173Yb', IsotopeRecord('173Yb', 70, 173, False, 'Yb', 'Ytterbium', 2.5, -0.2592, 0.1613, 2.8)),
#     ('174Yb', IsotopeRecord('174Yb', 70, 174, False, 'Yb', 'Ytterbium', 0, 0, 0.3183, 0)),
#     ('176Yb', IsotopeRecord('176Yb', 70, 176, False, 'Yb', 'Ytterbium', 0, 0, 0.1276, 0)),
#     ('173Lu', IsotopeRecord('173Lu', 71, 173, True, 'Lu', 'Lutetium', 3.5, 0.6517, 0, 3.53)),
#     ('174Lu', IsotopeRecord('174Lu', 71, 174, True, 'Lu', 'Lutetium', 1, 1.988, 0, 0.773)),
#     ('175Lu', IsotopeRecord('175Lu', 71, 175, False, 'Lu', 'Lutetium', 3.5, 0.6378, 0.9741, 3.49)),
#     ('176Lu', IsotopeRecord('176Lu', 71, 176, False, 'Lu', 'Lutetium', 7, 0.4517, 0.0259, 4.92)),
#     ('174Hf', IsotopeRecord('174Hf', 72, 174, False, 'Hf', 'Hafnium', 0, 0, 0.0016, 0)),
#     ('176Hf', IsotopeRecord('176Hf', 72, 176, False, 'Hf', 'Hafnium', 0, 0, 0.0526, 0)),
#     ('177Hf', IsotopeRecord('177Hf', 72, 177, False, 'Hf', 'Hafnium', 3.5, 0.2267, 0.186, 3.37)),
#     ('178Hf', IsotopeRecord('178Hf', 72, 178, False, 'Hf', 'Hafnium', 0, 0, 0.2728, 0)),
#     ('179Hf', IsotopeRecord('179Hf', 72, 179, False, 'Hf', 'Hafnium', 4.5, -0.1424, 0.1362, 3.79)),
#     ('180Hf', IsotopeRecord('180Hf', 72, 180, False, 'Hf', 'Hafnium', 0, 0, 0.3508, 0)),
#     ('180Ta', IsotopeRecord('180Ta', 73, 180, False, 'Ta', 'Tantalum', 0, 0, 0.00012, 0)),
#     ('181Ta', IsotopeRecord('181Ta', 73, 181, False, 'Ta', 'Tantalum', 3.5, 0.67729, 0.99988, 3.17)),
#     ('180W', IsotopeRecord('180W', 74, 180, False, 'W', 'Tungsten', 0, 0, 0.0012, 0)),
#     ('182W', IsotopeRecord('182W', 74, 182, False, 'W', 'Tungsten', 0, 0, 0.265, 0)),
#     ('183W', IsotopeRecord('183W', 74, 183, False, 'W', 'Tungsten', 0.5, 0.235569, 0.1431, 0)),
#     ('184W', IsotopeRecord('184W', 74, 184, False, 'W', 'Tungsten', 0, 0, 0.3064, 0)),
#     ('186W', IsotopeRecord('186W', 74, 186, False, 'W', 'Tungsten', 0, 0, 0.2843, 0)),
#     ('185Re', IsotopeRecord('185Re', 75, 185, False, 'Re', 'Rhenium', 2.5, 1.2748, 0.374, 2.18)),
#     ('187Re', IsotopeRecord('187Re', 75, 187, False, 'Re', 'Rhenium', 2.5, 1.2879, 0.626, 2.07)),
#     ('184Os', IsotopeRecord('184Os', 76, 184, False, 'Os', 'Osmium', 0, 0, 0.0002, 0)),
#     ('186Os', IsotopeRecord('186Os', 76, 186, False, 'Os', 'Osmium', 0, 0, 0.0159, 0)),
#     ('187Os', IsotopeRecord('187Os', 76, 187, False, 'Os', 'Osmium', 0.5, 0.129304, 0.0196, 0)),
#     ('188Os', IsotopeRecord('188Os', 76, 188, False, 'Os', 'Osmium', 0, 0, 0.1324, 0)),
#     ('189Os', IsotopeRecord('189Os', 76, 189, False, 'Os', 'Osmium', 1.5, 0.439956, 0.1615, 0.86)),
#     ('190Os', IsotopeRecord('190Os', 76, 190, False, 'Os', 'Osmium', 0, 0, 0.2626, 0)),
#     ('192Os', IsotopeRecord('192Os', 76, 192, False, 'Os', 'Osmium', 0, 0, 0.4078, 0)),
#     ('191Ir', IsotopeRecord('191Ir', 77, 191, False, 'Ir', 'Iridium', 1.5, 0.1005, 0.373, 0.816)),
#     ('193Ir', IsotopeRecord('193Ir', 77, 193, False, 'Ir', 'Iridium', 1.5, 0.1091, 0.627, 0.751)),
#     ('190Pt', IsotopeRecord('190Pt', 78, 190, False, 'Pt', 'Platinum', 0, 0, 0.00014, 0)),
#     ('192Pt', IsotopeRecord('192Pt', 78, 192, False, 'Pt', 'Platinum', 0, 0, 0.00784, 0)),
#     ('194Pt', IsotopeRecord('194Pt', 78, 194, False, 'Pt', 'Platinum', 0, 0, 0.32967, 0)),
#     ('195Pt', IsotopeRecord('195Pt', 78, 195, False, 'Pt', 'Platinum', 0.5, 1.219, 0.33832, 0)),
#     ('196Pt', IsotopeRecord('196Pt', 78, 196, False, 'Pt', 'Platinum', 0, 0, 0.25242, 0)),
#     ('198Pt', IsotopeRecord('198Pt', 78, 198, False, 'Pt', 'Platinum', 0, 0, 0.07163, 0)),
#     ('197Au', IsotopeRecord('197Au', 79, 197, False, 'Au', 'Gold', 1.5, 0.097164, 1, 0.547)),
#     ('196Hg', IsotopeRecord('196Hg', 80, 196, False, 'Hg', 'Mercury', 0, 0, 0.0015, 0)),
#     ('198Hg', IsotopeRecord('198Hg', 80, 198, False, 'Hg', 'Mercury', 0, 0, 0.0997, 0)),
#     ('199Hg', IsotopeRecord('199Hg', 80, 199, False, 'Hg', 'Mercury', 0.5, 1.01177, 0.1687, 0)),
#     ('200Hg', IsotopeRecord('200Hg', 80, 200, False, 'Hg', 'Mercury', 0, 0, 0.231, 0)),
#     ('201Hg', IsotopeRecord('201Hg', 80, 201, False, 'Hg', 'Mercury', 1.5, -0.373484, 0.1318, 0.387)),
#     ('202Hg', IsotopeRecord('202Hg', 80, 202, False, 'Hg', 'Mercury', 0, 0, 0.2986, 0)),
#     ('204Hg', IsotopeRecord('204Hg', 80, 204, False, 'Hg', 'Mercury', 0, 0, 0.0687, 0)),
#     ('203Tl', IsotopeRecord('203Tl', 81, 203, False, 'Tl', 'Thallium', 0.5, 3.24452, 0.29524, 0)),
#     ('204Tl', IsotopeRecord('204Tl', 81, 204, True, 'Tl', 'Thallium', 2, 0.045, 0, None)),
#     ('205Tl', IsotopeRecord('205Tl', 81, 205, False, 'Tl', 'Thallium', 0.5, 3.27643, 0.70476, 0)),
#     ('204Pb', IsotopeRecord('204Pb', 82, 204, False, 'Pb', 'Lead', 0, 0, 0.014, 0)),
#     ('206Pb', IsotopeRecord('206Pb', 82, 206, False, 'Pb', 'Lead', 0, 0, 0.241, 0)),
#     ('207Pb', IsotopeRecord('207Pb', 82, 207, False, 'Pb', 'Lead', 0.5, 1.18512, 0.221, 0)),
#     ('208Pb', IsotopeRecord('208Pb', 82, 208, False, 'Pb', 'Lead', 0, 0, 0.524, 0)),
#     ('207Bi', IsotopeRecord('207Bi', 83, 207, True, 'Bi', 'Bismuth', 4.5, 0.9092, 0, -0.76)),
#     ('209Bi', IsotopeRecord('209Bi', 83, 209, False, 'Bi', 'Bismuth', 4.5, 0.9134, 1, -0.516)),
#     ('209Po', IsotopeRecord('209Po', 84, 209, True, 'Po', 'Polonium', 0.5, 1.5, 0, 0)),
#     ('227Ac', IsotopeRecord('227Ac', 89, 227, True, 'Ac', 'Actinium', 1.5, 0.73, 0, 1.7)),
#     ('229Th', IsotopeRecord('229Th', 90, 229, True, 'Th', 'Thorium', 2.5, 0.18, 0, 4.3)),
#     ('232Th', IsotopeRecord('232Th', 90, 232, False, 'Th', 'Thorium', 0, 0, 1, 0)),
#     ('234U', IsotopeRecord('234U', 92, 234, True, 'U', 'Uranium', 0, 0, 5.5e-05, 0)),
#     ('235U', IsotopeRecord('235U', 92, 235, True, 'U', 'Uranium', 3.5, -0.109, 0.0072, 4.936)),
#     ('238U', IsotopeRecord('238U', 92, 238, True, 'U', 'Uranium', 0, 0, 0.992745, 0)),
#     ('237Np', IsotopeRecord('237Np', 93, 237, True, 'Np', 'Neptunium', 2.5, 1.256, 0, 3.87)),
#     ('239Pu', IsotopeRecord('239Pu', 94, 239, True, 'Pu', 'Plutonium', 0.5, 0.406, 0, 0)),
#     ('243Am', IsotopeRecord('243Am', 95, 243, True, 'Am', 'Americium', 2.5, 0.6, 0, 2.86)),
#     ))

# GWV: now handled by EmptySpectrumDataSource class
# #
# # default isotopes and nucleus codes
# # Default parameters - 10Hz/pt, 0.1ppm/point for 1H; 10 Hz/pt, 1ppm/pt for 13C
# # NB this is in order to give simple numbers. it does NOT match the gyromagnetic ratios
# DEFAULT_SPECTRUM_PARAMETERS = {
#     '1H' : {'numPoints': 12800, 'sf': 100., 'sw': 1280, 'refppm': 11.8, 'refpt': 1, },
#     '2H' : {'numPoints': 12800, 'sf': 100., 'sw': 1280, 'refppm': 11.8, 'refpt': 1, },
#     '3H' : {'numPoints': 12800, 'sf': 100., 'sw': 1280, 'refppm': 11.8, 'refpt': 1, },
#     '13C': {'numPoints': 25600, 'sf': 100., 'sw': 2560, 'refppm': 236., 'refpt': 1, },
#     '19F': {'numPoints': 25600, 'sf': 100., 'sw': 20000,'refppm': -40.4,'refpt': 0, }
#     }
# for isotopCode in isotopeRecords:
#     if isotopCode not in DEFAULT_SPECTRUM_PARAMETERS:
#         DEFAULT_SPECTRUM_PARAMETERS[isotopCode] = DEFAULT_SPECTRUM_PARAMETERS['13C']


DNA_ATOMS = """
Res    Name     Atom     Count        Min.        Max.       Avg.     Std Dev

DA          H2       H        950          2.60         8.64       7.49       0.80       
DA          H61      H        145          2.56        13.40       6.83       1.16       
DA          H62      H        144          5.31        12.90       6.92       1.11       
DA          H8       H        1097         2.35         9.10       8.00       0.83       
DA          H1'      H        1092         4.19         8.50       6.04       0.33       
DA          H2'      H        1083         0.84         4.82       2.66       0.37       
DA          H2''     H        1065         0.56         6.89       2.79       0.37       
DA          H3'      H        1031         4.00         6.04       4.94       0.19       
DA          H4'      H        819          2.08         9.13       4.34       0.34       
DA          H5'      H        449          2.79         5.95       4.06       0.30       
DA          H5''     H        406          2.96         8.41       4.07       0.45       
DA          C2       C        134        151.00       159.33     154.69       1.25       
DA          C4       C        2          150.30       150.60     150.45       0.21       
DA          C5       C        2          119.80       119.90     119.85       0.07       
DA          C6       C        2          157.00       157.40     157.20       0.28       
DA          C8       C        145        138.00       142.79     141.33       0.94       
DA          C1'      C        138         81.50        91.90      85.19       1.26       
DA          C2'      C        123         36.23        42.93      40.58       1.05       
DA          C3'      C        99          72.71        83.26      78.46       1.70       
DA          C4'      C        68          84.43        91.33      87.21       1.19       
DA          C5'      C        45          47.77        70.96      67.18       3.42       
DA          N1       N        3          223.40       227.00     225.20       1.80       
DA          N3       N        3          214.50       216.40     215.73       1.07       
DA          N6       N        9           77.40        81.70      80.22       1.29       
DA          N7       N        2          233.50       234.10     233.80       0.42       
DA          N9       N        1          170.20       170.20     170.20       0.00       
DA          P        P        239        -45.29        35.48      -2.32       5.04       

DC          H41      H        593         -0.26        12.08       7.40       1.15       
DC          H42      H        576         -0.26        10.62       7.48       1.07       
DC          H5       H        1263        -6.22         8.25       5.40       0.89       
DC          H6       H        1277       -14.72         8.31       7.36       0.98       
DC          H1'      H        1269         2.17         6.60       5.72       0.69       
DC          H2'      H        1251       -29.45         6.93       2.11       1.42       
DC          H2''     H        1235       -20.82         8.48       2.39       1.08       
DC          H3'      H        1177        -7.37         8.62       4.72       0.65       
DC          H4'      H        923        -38.59        28.54       4.18       2.40       
DC          H5'      H        458        -18.35        11.19       4.17       1.81       
DC          H5''     H        381        -41.21        15.96       3.98       3.50       
DC          C2       C        2          158.80       159.20     159.00       0.28       
DC          C4       C        2          167.80       168.00     167.90       0.14       
DC          C5       C        125         84.55        99.90      98.12       2.25       
DC          C6       C        129        133.73       144.70     142.76       1.63       
DC          C1'      C        134         77.90        88.53      86.94       1.65       
DC          C2'      C        105         30.62        42.27      40.34       1.45       
DC          C3'      C        101         66.41        80.30      76.57       2.75       
DC          C4'      C        52          77.80        88.39      85.90       1.93       
DC          C5'      C        33          59.30        71.72      66.28       2.63       
DC          N1       N        1          150.70       150.70     150.70       0.00       
DC          N3       N        1          196.30       196.30     196.30       0.00       
DC          N4       N        16          95.10       100.41      98.29       1.33       
DC          P        P        332        -14.20        52.72      -1.65       6.05       

DG          H1       H        1299        -2.91        13.94      11.62       2.06       
DG          H21      H        322        -26.86        18.44       7.46       3.00       
DG          H22      H        309        -26.86        18.44       6.36       3.02       
DG          H8       H        1975         6.07         9.31       7.78       0.25       
DG          H1'      H        1979         2.53        12.45       5.90       0.45       
DG          H2'      H        1932         1.43         8.23       2.67       0.41       
DG          H2''     H        1902         1.16        11.50       2.72       0.42       
DG          H3'      H        1863         0.00        13.24       4.97       0.68       
DG          H4'      H        1547         0.00        13.26       4.46       0.98       
DG          H5'      H        885          0.00         7.82       4.12       0.36       
DG          H5''     H        761          0.00         7.76       4.10       0.35       
DG          C2       C        2          156.50       156.70     156.60       0.14       
DG          C4       C        2          153.10       154.00     153.55       0.64       
DG          C5       C        2          117.40       117.60     117.50       0.14       
DG          C6       C        2          161.00       161.40     161.20       0.28       
DG          C8       C        182        134.38       142.93     138.20       1.62       
DG          C1'      C        166         74.90        91.82      85.07       2.02       
DG          C2'      C        128         32.64        49.00      40.23       2.00       
DG          C3'      C        124         67.72        81.41      77.69       2.27       
DG          C4'      C        77          75.27        90.64      86.92       2.19       
DG          C5'      C        57          58.50        71.42      67.06       2.21       
DG          N1       N        33         142.74       147.70     145.74       1.96       
DG          N2       N        5           75.10        76.10      75.52       0.38       
DG          N7       N        4          236.90       238.30     237.28       0.68       
DG          N9       N        1          168.50       168.50     168.50       0.00       
DG          P        P        406        -20.92        47.10      -1.39       6.34       

DT          H3       H        575          2.12        14.53      12.85       1.97       
DT          H6       H        1420         1.61         8.10       7.36       0.32       
DT          H7       H        8            1.46         1.79       1.65       0.13       
DT          H71      H        1249         0.18         7.53       1.60       0.41       
DT          H72      H        1248         0.18         7.53       1.60       0.41       
DT          H73      H        1248         0.18         7.53       1.60       0.41       
DT          H1'      H        1412         1.65         6.72       5.88       0.54       
DT          H2'      H        1402         0.50         6.21       2.16       0.47       
DT          H2''     H        1383         0.78         4.87       2.39       0.36       
DT          H3'      H        1337         3.79        14.11       4.80       0.47       
DT          H4'      H        997          2.00        14.15       4.16       0.55       
DT          H5'      H        608          2.54        14.20       4.20       1.56       
DT          H5''     H        547          0.98         7.19       3.97       0.40       
DT          C2       C        2          152.90       153.40     153.15       0.35       
DT          C4       C        2          168.50       169.10     168.80       0.42       
DT          C5       C        9           14.30       113.60      36.43      43.64       
DT          C6       C        229        135.80       143.60     139.24       0.92       
DT          C7       C        59          11.96        14.90      14.19       0.62       
DT          C1'      C        215         80.60        92.22      86.88       1.37       
DT          C2'      C        195         34.38        42.96      39.99       0.88       
DT          C3'      C        176         71.58        80.10      77.49       1.64       
DT          C4'      C        64          78.80        89.31      86.04       1.46       
DT          C5'      C        41          59.40        68.40      66.36       1.91       
DT          N1       N        1          142.90       142.90     142.90       0.00       
DT          N3       N        41         156.40       160.50     159.27       0.71       
DT          P        P        261         -5.65        47.79      -1.36       7.03       
"""
RNA_ATOMS = """
Res    Name     Atom     Count        Min.        Max.       Avg.     Std Dev

A          H2       H        1617         0.00         9.39       7.63       0.47       
A          H61      H        298          0.00        10.85       7.41       1.18       
A          H62      H        265          0.00         9.98       6.78       1.11       
A          H8       H        1592         7.00         9.20       8.01       0.27       
A          H1'      H        1616         4.56         7.16       5.88       0.21       
A          HO2'     H        44           4.27         7.75       5.75       1.18       
A          H2'      H        1414         3.61         5.91       4.59       0.22       
A          H3'      H        1213         3.91         5.45       4.63       0.21       
A          H4'      H        1042         0.00         5.29       4.46       0.25       
A          H5'      H        803          0.00         5.03       4.30       0.27       
A          H5''     H        786          0.00       153.90       4.37       5.35       
A          C2       C        1015         0.00       167.71     151.71       8.98       
A          C4       C        35           0.00       151.89     131.04      47.78       
A          C5       C        35           0.00       153.63     104.96      39.80       
A          C6       C        37           0.00       159.60     139.05      49.16       
A          C8       C        993          0.00       145.80     138.18       9.80       
A          C1'      C        944         84.23       130.39      91.64       3.57       
A          C2'      C        703          4.75        99.00      75.25       5.81       
A          C3'      C        640          0.00       101.40      73.68       4.97       
A          C4'      C        629          0.00        92.60      82.53       4.09       
A          C5'      C        540          0.00       109.20      66.22       6.79       
A          N1       N        253          0.00       229.70     216.11      30.52       
A          N3       N        203          0.00       231.08     210.51      30.33       
A          N6       N        157          0.00        97.01      79.33      13.30       
A          N7       N        151          0.00       237.10     224.40      37.21       
A          N9       N        189          0.00       176.80     166.48      24.64       
A          P        P        176         -5.96         2.43      -2.97       1.64       

C          H41      H        973          5.64        10.38       7.91       0.72       
C          H42      H        951          5.07         9.06       7.25       0.69       
C          H5       H        1865         4.20         7.09       5.48       0.29       
C          H6       H        1915         5.62         8.46       7.68       0.21       
C          H1'      H        1871         3.42         6.42       5.55       0.24       
C          HO2'     H        66           3.96         9.70       5.82       1.49       
C          H2'      H        1578         0.00         5.07       4.32       0.24       
C          H3'      H        1389         0.00         5.63       4.41       0.23       
C          H4'      H        1135         0.00        12.58       4.33       0.37       
C          H5'      H        850          0.00         7.17       4.26       0.38       
C          H5''     H        871          0.00         5.04       4.10       0.46       
C          C2       C        65           0.00       189.36     136.58      59.06       
C          C4       C        78           0.00       169.52     147.08      53.62       
C          C5       C        1101         0.00       141.05      97.28       4.33       
C          C6       C        1132        93.40       145.02     139.71       7.35       
C          C1'      C        1076        84.00       118.95      92.68       2.10       
C          C2'      C        839          0.00        99.40      75.76       5.32       
C          C3'      C        780          0.00       104.90      73.18       6.41       
C          C4'      C        735          0.00        92.60      81.94       5.86       
C          C5'      C        609          0.00       110.20      64.72       9.47       
C          N1       N        229          0.00       178.83     145.28      30.98       
C          N3       N        181          0.00       204.30     184.53      43.16       
C          N4       N        390          0.00       104.50      96.67      10.21       
C          P        P        186         -5.13         0.62      -3.15       1.65       

G          H1       H        1527         6.09        14.32      12.35       0.98       
G          H21      H        444          0.00         9.39       7.37       1.42       
G          H22      H        402          0.00         9.06       6.31       1.22       
G          H8       H        2293         0.00         8.63       7.60       0.39       
G          H1'      H        2257         3.41         7.62       5.66       0.33       
G          HO2'     H        53           4.40         7.10       5.77       1.16       
G          H2'      H        1931         3.26         6.30       4.58       0.25       
G          H3'      H        1724         3.80         5.78       4.56       0.26       
G          H4'      H        1405         0.00         5.11       4.43       0.22       
G          H5'      H        1187         2.89         5.42       4.28       0.23       
G          H5''     H        1157         2.55         5.11       4.18       0.23       
G          C2       C        59           0.00       162.50     131.48      56.36       
G          C4       C        44           0.00       158.62     120.73      61.96       
G          C5       C        78           0.00       167.24     106.95      40.80       
G          C6       C        86           0.00       162.74     142.40      49.29       
G          C8       C        1429         0.00       146.73     135.38       8.27       
G          C1'      C        1244        79.80        95.05      91.50       1.97       
G          C2'      C        975          0.00        99.40      75.27       4.88       
G          C3'      C        887          0.00       102.20      73.85       5.27       
G          C4'      C        855         72.08        96.10      82.65       2.63       
G          C5'      C        758         50.36       108.20      66.41       6.34       
G          N1       N        891          0.00       166.07     145.58      13.10       
G          N2       N        151          0.00        83.38      71.00      17.00       
G          N3       N        25           0.00       234.10      97.88      80.79       
G          N7       N        184          0.00       240.99     221.87      50.58       
G          N9       N        280          0.00       176.40     164.01      30.01       
G          P        P        208         -6.00         0.56      -2.86       1.59       

U          H3       H        898          1.20       154.54      13.24       4.89       
U          H5       H        1524         4.20         7.83       5.47       0.31       
U          H6       H        1590         5.81         8.52       7.75       0.20       
U          H1'      H        1559         3.69         6.59       5.61       0.26       
U          HO2'     H        45           4.08         9.74       6.06       1.51       
U          H2'      H        1357         0.00         6.63       4.37       0.27       
U          H3'      H        1117         0.00         7.83       4.48       0.25       
U          H4'      H        949          0.00         4.82       4.36       0.23       
U          H5'      H        697          0.00         4.85       4.24       0.30       
U          H5''     H        713          0.00         4.86       4.15       0.29       
U          C2       C        80           0.00       183.20     144.31      38.05       
U          C4       C        86           0.00       169.70     157.82      39.47       
U          C5       C        944          0.00       154.13     102.90       6.62       
U          C6       C        975          0.00       169.95     140.14       8.53       
U          C1'      C        990         80.62        96.30      91.90       2.14       
U          C2'      C        737          0.00        99.80      75.04       4.49       
U          C3'      C        656          0.00       102.50      73.74       5.43       
U          C4'      C        643          0.00        94.42      82.70       4.14       
U          C5'      C        525          0.00       106.60      65.07       5.67       
U          N1       N        209          0.00       192.14     147.96      25.60       
U          N3       N        553          0.00       167.30     158.99      16.67       
U          O4       O        5            0.00         0.00       0.00       0.00       
U          P        P        149         -5.30         1.58      -2.99       1.78       
"""
DNA_ATOM_NAMES = {
    'DT': ['H3', 'H6', 'H7', 'H71', 'H72', 'H73', "H1'", "H2'", "H2''", "H3'", "H4'", "H5'", "H5''",
           'C2', 'C4', 'C5', 'C6', 'C7', "C1'", "C2'", "C3'", "C4'", "C5'",
           'N1', 'N3',
           'P'],
    'DC': ['H41', 'H42', 'H5', 'H6', "H1'", "H2'", "H2''", "H3'", "H4'", "H5'", "H5''",
           'C2', 'C4', 'C5', 'C6', "C1'", "C2'", "C3'", "C4'", "C5'",
           'N1', 'N3', 'N4',
           'P'],
    'DA': ['H2', 'H61', 'H62', 'H8', "H1'", "H2'", "H2''", "H3'", "H4'", "H5'", "H5''",
           'C2', 'C4', 'C5', 'C6', 'C8', "C1'", "C2'", "C3'", "C4'", "C5'",
           'N1', 'N3', 'N6', 'N7', 'N9', 'P'],
    'DG': ['H1', 'H21', 'H22', 'H8', "H1'", "H2'", "H2''", "H3'", "H4'", "H5'", "H5''",
           'C2', 'C4', 'C5', 'C6', 'C8', "C1'", "C2'", "C3'", "C4'", "C5'",
           'N1', 'N2', 'N7', 'N9',
           'P']
    }
RNA_ATOM_NAMES = {
    'G': ['H1', 'H21', 'H22', 'H8', "H1'", "HO2'", "H2'", "H3'", "H4'", "H5'", "H5''",
          'C2', 'C4', 'C5', 'C6', 'C8', "C1'", "C2'", "C3'", "C4'", "C5'",
          'N1', 'N2', 'N3', 'N7', 'N9',
          'P'],
    'U': ['H3', 'H5', 'H6', "H1'", "HO2'", "H2'", "H3'", "H4'", "H5'", "H5''",
          'C2', 'C4', 'C5', 'C6', "C1'", "C2'", "C3'", "C4'", "C5'",
          'N1', 'N3', 'O4',
          'P'],
    'A': ['H2', 'H61', 'H62', 'H8', "H1'", "HO2'", "H2'", "H3'", "H4'", "H5'", "H5''",
          'C2', 'C4', 'C5', 'C6', 'C8', "C1'", "C2'", "C3'", "C4'", "C5'",
          'N1', 'N3', 'N6', 'N7', 'N9',
          'P'],
    'C': ['H41', 'H42', 'H5', 'H6', "H1'", "HO2'", "H2'", "H3'", "H4'", "H5'", "H5''",
          'C2', 'C4', 'C5', 'C6', "C1'", "C2'", "C3'", "C4'", "C5'",
          'N1', 'N3', 'N4',
          'P']
    }
ALL_DNARNA_ATOMS_SORTED = OrderedDict([
    ('O', ["HO2'"]),
    ('1', ["C1'", 'H1', "H1'", 'N1']),
    ('2', ['C2', "C2'", 'H2', "H2'", "H2''", 'H21', 'H22', 'N2']),
    ('3', ["C3'", 'H3', "H3'", 'N3']),
    ('4', ['C4', "C4'", "H4'", 'H41', 'H42', 'N4', 'O4']),
    ('5', ['C5', "C5'", 'H5', "H5'", "H5''"]),
    ('6', ['C6', 'H6', 'H61', 'H62', 'N6']),
    ('7', ['C7', 'H7', 'H71', 'H72', 'H73', 'N7']),
    ('8', ['C8', 'H8']),
    ('9', ['N9']),
    ('P', ['P'])
    ])


def main():
    for iso, record in isotopeRecords.items():
        symbol = record.symbol
        ll = list(record)
        if len(symbol) > 1:
            symbol = symbol.title()
            iso = iso[:-2] + symbol
            ll[0] = iso
            ll[4] = symbol
        print("  ('%s', IsotopeRecord%s)," % (iso, tuple(ll)))


if __name__ == '__main__':
    main()
