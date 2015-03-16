"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
from ccpnmrcore.testing.Testing import Testing

from ccpnmrcore.modules.SpectrumNdPane import SpectrumNdPane

import json
import os
from ccpncore.util.AttrDict import AttrDict


class SpectrumPaneTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)
    self.spectrumName = 'HSQC'
    preferencesPath = os.path.expanduser('~/.ccpn/v3settings.json')
    self.preferences = json.load(open(preferencesPath), object_hook=AttrDict)

  def test_spectrumNdPane(self):

    spectrumPane = SpectrumNdPane(project=self.project, parent=self.frame, preferences=self.preferences)
    spectrum = self.getSpectrum()
    spectrumPane.addSpectrum(spectrum)
