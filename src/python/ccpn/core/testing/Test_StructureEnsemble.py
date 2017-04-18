"""Module Documentation here

"""
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
__dateModified__ = "$dateModified: 2017-04-07 11:41:01 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
import numpy

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.framework import Framework


class StructureEnsembleTesting(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse3e'


  def test_haveEnsemble(self):
    assert len(self.project.structureEnsembles) > 0

    self.project._wrappedData.root.checkAllValid(complete=True)

  def test_getModels(self):
    models = self.project.structureEnsembles[0].models
    assert len(models) > 0
    assert len(models) == 20

  def test_coords(self):
    data = self.project.structureEnsembles[0].data
    self.assertEquals(data.shape, (29680, 17))


class StructureEnsembleTesting2(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_load_structure(self):
    self.loadData('../structures/2CPP.pdb')
    ensemble = self.project.structureEnsembles[0]
    self.assertEqual( len(ensemble.models), 1)
    self.assertEqual( len(ensemble.data), 3462)
    self.assertEqual( ensemble.data.shape, (3462, 17))
    self.assertTrue(self.project.save())
    loadedProject = Framework.createFramework(projectPath=self.project.path).project
    try:
      ensemble = loadedProject.structureEnsembles[0]
      data = ensemble.data
      self.assertEqual( len(ensemble.models), 1)
      self.assertEqual( len(data), 3462)
      self.assertEqual( data.shape, (3462, 17))
      self.assertTrue(all(x == 'A' for x in data['chainCode']))
      tags = [
        'modelNumber', 'chainCode', 'sequenceId', 'insertionCode',
        'residueName', 'atomName', 'altLocationCode', 'element',
        'occupancy', 'bFactor',
        'nmrChainCode', 'nmrSequenceCode', 'nmrResidueName', 'nmrAtomName',
      ]
      print ('@~@~ columns', data.columns)
      print ('@~@~ dtypes', data.dtypes)
      for tag in tags:
        print ('\n\n@~@~', tag, '\n', data[tag].value_counts())
    finally:
      loadedProject.delete()
