"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
import collections

from ccpn.core.testing.WrapperTesting import WrapperTesting


class ParameterTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None


  def test_parameters(self):

    project = self.project
    spectrum = self.loadData('spectra/hsqc.spc')[0]
    undo = self.project._undo
    undo.newWaypoint()
    window = project.getWindow('Main')
    display = window.createSpectrumDisplay(spectrum)
    undo.undo()
    undo.redo()

    dd = {'pid':'GD:user.View.HN', 'axisCodes':('H', 'N'), 'units':('ppm', 'ppm'),
          'stripDirection':'Y', 'is1D':False, 'name':'HN'}

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
