"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpncore.util import Translation

def test_setLanguageDefault():
  Translation.setTranslationLanguage()

def test_setLanguageEnglish():
  Translation.setTranslationLanguage('English')

def test_setLanguageFrench():
  Translation.setTranslationLanguage('French')

def test_setLanguageGerman():
  Translation.setTranslationLanguage('German')

def test_translateDefaultText():
  Translation.setTranslationLanguage()
  assert Translation.getTranslation('Help') == 'Help'

def test_translateEnglishText():
  Translation.setTranslationLanguage('English')
  assert Translation.getTranslation('Help') == 'Help'

def test_translateFrenchText1():
  Translation.setTranslationLanguage('French')
  assert Translation.getTranslation('Help') == 'Aidez'

def test_translateFrenchText1():
  Translation.setTranslationLanguage('French')
  assert Translation.getTranslation('Help Me') == 'Help Me'
