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
