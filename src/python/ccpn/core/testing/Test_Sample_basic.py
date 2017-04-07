#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:35 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.memops.ApiError import ApiError


class TestSampleCreation(WrapperTesting):

  def test_newSampleWithoutName(self):
    # Creation function changed to provide default name
    # self.assertRaises(TypeError, self.project.newSample)
    newSample =  self.project.newSample()
    self.assertEqual(newSample.name, 'Sample_1')
    self.assertEqual(len(self.project.samples), 1)

  def test_newSampleEmptyName(self):
    self.assertRaises(ApiError, self.project.newSample, '')
    self.assertEqual(len(self.project.samples), 0)

  def test_newSample(self):
    s = self.project.newSample('test sample')

    self.assertEqual(s.pid, 'SA:test sample')
    self.assertEqual(len(self.project.samples), 1)
    self.assertIs(self.project.samples[0], s)


  def test_rename_sample(self):
    obj = self.project.newSample(name='patty')
    undo = self.project._undo
    undo.newWaypoint()
    obj.rename('cake')
    self.assertEqual(obj.name, 'cake')
    undo.undo()
    self.assertEqual(obj.name, 'patty')
    undo.redo()
    self.assertEqual(obj.name, 'cake')
