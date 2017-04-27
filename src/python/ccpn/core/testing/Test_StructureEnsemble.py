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
__dateModified__ = "$dateModified: 2017-04-10 12:56:47 +0100 (Mon, April 10, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-03-30 15:03:06 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy
from unittest import expectedFailure
from ccpn.core.testing.WrapperTesting import WrapperTesting, checkGetSetAttr
from ccpn.framework import Framework


#=========================================================================================
# StructureEnsembleTesting    No loaded project
#=========================================================================================

class StructureEnsembleTesting_None(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def _test_load_structure(self):
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


#=========================================================================================
# StructureEnsembleTesting    Loaded project
#=========================================================================================

class StructureEnsembleTesting_Project(WrapperTesting):
  """
  Test StructureEnsemble with a pre-loaded valid project
  """
  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse3e'


  def _test_haveEnsemble(self):
    # assert len(self.project.structureEnsembles) > 0
    #
    self.assertGreater(len(self.project.structureEnsembles), 0)

    self.project._wrappedData.root.checkAllValid(complete=True)

    models = self.project.structureEnsembles[0].models
    # assert len(models) > 0
    # assert len(models) == 20
    #
    self.assertGreater(len(models), 0)
    self.assertEquals(len(models), 20)

    data = self.project.structureEnsembles[0].data
    self.assertEquals(data.shape, (29680, 17))


  def _test_getModels(self):
    models = self.project.structureEnsembles[0].models
    # assert len(models) > 0
    # assert len(models) == 20
    #
    self.assertGreater(len(models), 0)
    self.assertEquals(len(models), 20)

  def _test_coords(self):
    data = self.project.structureEnsembles[0].data
    self.assertEquals(data.shape, (29680, 17))


#=========================================================================================
# StructureEnsembleTesting      Properties
#=========================================================================================

class StructureEnsembleTesting_Properties(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  #=========================================================================================
  # setUp       initialise a newStructureEnsemble
  #=========================================================================================

  def setUp(self):
    """
    Create a valid empty structureEnsemble
    """
    with self.initialSetup():
      self.ensemble = self.project.newStructureEnsemble()

  #=========================================================================================
  # test_properties_structuresEnsemble
  #=========================================================================================

  def test_properties_structuresEnsemble_Serial(self):
    """
    Test that structureEnsemble attribute .serial is populated.
    Read the attribute, if it not populated then an error is raised.
    """
    self.assertEqual(self.project.structureEnsembles[0].serial, 1)

  def test_properties_structuresEnsemble_Label(self):
    """
    Test that structureEnsemble attribute .label is populated.
    Read the attribute, if it not populated then an error is raised.
    If no error, then test the setter by setting and then getting to check consistent.
    """
    checkGetSetAttr(self, self.project.structureEnsembles[0], 'label', 'ValidName')

  def test_properties_structuresEnsemble_Comment(self):
    """
    Test that structureEnsemble attribute .comment is populated.
    """
    checkGetSetAttr(self, self.project.structureEnsembles[0], 'comment', 'ValidComment')

