"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
from ccpn.util.Translation import Translation

def test_setLanguageDefault():
  tr = Translation()
  tr.setLanguage()

def test_setLanguageEnglish():
  tr = Translation()
  tr.setLanguage('English-UK')

def test_setLanguageFrench():
  tr = Translation()
  tr.setLanguage('French')

def test_setLanguageGerman():
  tr = Translation()
  tr.setLanguage('German')

def test_translateDefaultText():
  tr = Translation()
  assert tr.translate('Help') == 'Help'

def test_translateEnglishText():
  tr = Translation()
  tr.setLanguage('English-UK')
  assert tr.translate('Help') == 'Help'

def test_translateFrenchText1():
  tr = Translation()
  tr.setLanguage('French')
  assert tr.translate('Help') == 'Aidez'

def test_translateChineseText1():
  tr = Translation()
  tr.setLanguage('Chinese')
  assert tr.translate('New') == '新的'

def test_translateChineseText2():
  tr = Translation()
  tr.setLanguage('Chinese')
  assert tr.translate('Help Me') == 'Help Me'

