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

import os

from ccpn.core.testing.WrapperTesting import WrapperTesting

class TestPandasData(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_float_column_1(self):
    ensemble = self.project.newStructureEnsemble()
    data = ensemble.data
    data['x'] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    print ('--->', data)
    data['y'] = 1
    print ('--->', data)
    data['z'] = [None]
    for key,val in sorted(data.items()):
      print ('@~@~', key, list(val), [type(x) for x in val])


  def test_float_column_2(self):
    ensemble = self.project.newStructureEnsemble()
    data = ensemble.data
    data['x'] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    print('--->', data)
    data['y'] = [1,2.0,None,'4', '5.0', 'NaN']
    print('--->', data)
    data['z'] = (7, 9)
    for key, val in sorted(data.items()):
      print('@~@~', key, list(val), [type(x) for x in val])

  def test_float_column_3(self):
    ensemble = self.project.newStructureEnsemble()
    data = ensemble.data
    data['x'] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    print ('--->', data)
    data['x'] = 11
    print ('--->', data)
    data['z'] = None
    for key,val in sorted(data.items()):
      print ('@~@~', key, list(val), [type(x) for x in val])
