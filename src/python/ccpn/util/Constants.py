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

# Default name for natural abundance labeling - given as None externally
DEFAULT_LABELING = '_NATURAL_ABUNDANCE'