"""Module Documentation here

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:37 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
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

    def test_Chinese_translation(self):
        t = Translation.getTranslator('Chinese')
        self.assertNotEqual(t('New'), 'New')
        self.assertEqual(t('New'), '新的')
