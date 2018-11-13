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
__dateModified__ = "$dateModified: 2017-07-07 16:32:57 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
import collections

from ccpn.core.testing.WrapperTesting import WrapperTesting


class ParameterTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None


  def test_parameters(self):

    project = self.project
    spectrum = self.loadData('spectra/hsqc.spc')[0]
    undo = self.project._undo
    self.project.newUndoPoint()
    window = project.getWindow('Main')
    display = window.createSpectrumDisplay(spectrum)
    undo.undo()
    undo.redo()

    dd = {'pid':'GD:HN', 'axisCodes':('H', 'N'), 'units':('ppm', 'ppm'),
          'stripDirection':'Y', 'is1D':False, 'title':'HN'}

    for tag, val in dd.items():
      self.assertEqual(val, getattr(display, tag))

    testpars = collections.OrderedDict()
    for key,val in [
      ('bbb',1), ('ccc',[1,2,3]), ('ddd',True), ('aaa',()), ('xxx','xxx'), ('dict', {1:1}),
      ('odict', collections.OrderedDict(((2,100), (1,10))))
    ]:
      testpars[key] = val


    self.assertEqual(display.parameters, {})
    display.setParameter('aaa', 1)
    self.assertEqual(display.parameters, {'aaa':1})
    display.updateParameters(testpars)
    self.assertEqual(display.parameters, testpars)
    display.deleteParameter('ccc')
    del testpars['ccc']
    self.assertEqual(display.parameters, testpars)
    display.setParameter('ddd', 11)
    testpars['ddd'] = 11
    self.assertEqual(display.parameters, testpars)
    undo.undo()
    undo.redo()
    self.assertEqual(display.parameters, testpars)
    display.clearParameters()
    self.assertEqual(display.parameters, {})
