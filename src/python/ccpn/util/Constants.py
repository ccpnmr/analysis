"""Constants used in the program core, including enumerations of allowed values

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca G Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

# Units allowed for amounts (e.g. Sample)
amountUnits = ('L', 'g', 'mole')

#  Units allowed for concentrations (e.g. SampleComponents)
concentrationUnits = ('Molar', 'g/L', 'L/L', 'mol/mol', 'g/g')

# Default name for natural abundance labelling - given as None externally
DEFAULT_LABELLING = '_NATURAL_ABUNDANCE'

# Default parameters - 10Hz/pt, 0.1ppm/point for 1H; 10 Hz/pt, 1ppm/pt for 13C
# NB this is in order to give simple numbers. it does NOT match the gyromagnetic ratios
DEFAULT_SPECTRUM_PARAMETERS = {
  '1H':{'numPoints':128, 'sf':100., 'sw':1280, 'refppm':11.8, 'refpt':1, },
  '13C':{'numPoints':256, 'sf':10., 'sw':2560, 'refppm':236., 'refpt':1, }
}


DEFAULT_ISOTOPE_DICT = {
  'H':'1H',
  'C':'13C',
  'N':'15N',
  'P':'31P',
  'Si':'29Si',
  'F':'19F',
  'O':'17O',
  'Br':'79Br',
  'D':'2H',
  'T':'3H',
  'J':None,
  'MQ':None,
  'delay':None,
  'ALT':None,
}

# default isotopes and nucleus codes
for tag, val in list(DEFAULT_ISOTOPE_DICT.items()):

  # Add lower-case versions of single-letter codes
  if val and len(tag) == 1:
    DEFAULT_ISOTOPE_DICT[tag.lower()] = val

  # Without additional info, set other one-letter isotopes (including 15N) to match carbon 13
  if len(tag) == 1 and val and val not in DEFAULT_SPECTRUM_PARAMETERS:
    DEFAULT_SPECTRUM_PARAMETERS[val] = DEFAULT_SPECTRUM_PARAMETERS['13C']
