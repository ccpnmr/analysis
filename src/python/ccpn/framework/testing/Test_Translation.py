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

import unittest

from ccpn.framework import Translation


class Test_Translation(unittest.TestCase):

  def test_getLanguages(self):
    self.assertIn('Dutch', Translation._get_languages())
    self.assertIn('Italian', Translation._get_languages())
    self.assertIn('Chinese', Translation._get_languages())

  def test_getDutch_translationDictionary(self):
    tDict = Translation._get_translation_dictionary('Dutch')
    self.assertEqual(tDict['New'], 'Nieuw')

  def test_Dutch_translation(self):
    t = Translation.getTranslator('Dutch')
    self.assertEqual(t('New'), 'Nieuw')


  def test_UnknownWord_translation(self):
    t = Translation.getTranslator('Dutch')
    self.assertEqual(t('TestUnknownWord'), 'TestUnknownWord')
