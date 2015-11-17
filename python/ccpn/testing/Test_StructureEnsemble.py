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
from ccpn.testing.WrapperTesting import WrapperTesting

from ccpncore.util import Path



class StructureEnsembleTesting(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse3e'


  def test_haveEnsemble(self):
    assert len(self.project.structureEnsembles) > 0

  def test_getModels(self):
    models = self.project.structureEnsembles[0].models
    assert len(models) > 0
    assert len(models) == 20

  def test_coords(self):
    coordData = self.project.structureEnsembles[0].coordinateData
    record = coordData[0][0]
    assert record.size == 3
    assert record.shape == (3, )

  def test_setCoordData(self):
    x = self.project.structureEnsembles[0].coordinateData
    self.project.structureEnsembles[0].coordinateData = x


  def test_getResType(self):
    atomId = self.project.structureEnsembles[0].atomIds[0]
    residueType = atomId.split('.')[2]
    print('@~@~', atomId)
    assert residueType != 'None'

  def test_replaceAtomIds(self):
    oldAtomIds = self.project.structureEnsembles[0].atomIds
    newAtomId = 'A.1.LYS.N'
    oldAtomIds[0] = newAtomId
    self.project.structureEnsembles[0].replaceAtomIds(oldAtomIds)
    assert self.project.structureEnsembles[0].atomIds[0] == newAtomId

  def test_createEnsemble(self):
    newEnsemble = self.project.newStructureEnsemble(ensembleId=1)
    self.assertIsNotNone(newEnsemble)


  def test_addAtomsToEnsemble(self):
    newEnsemble = self.project.newStructureEnsemble(ensembleId=1)
    atomIds = [atom.id for atom in self.project.nmrAtoms][10:13]
    newEnsemble.addAtomIds(atomIds)