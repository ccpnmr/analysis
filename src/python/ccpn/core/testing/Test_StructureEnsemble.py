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


class StructureEnsembleTesting2(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_load_structure(self):
    self.loadData('../structures/2CPP.pdb')
    ensemble = self.project.structureEnsembles[0]
    self.assertEqual( len(ensemble.models), 1)
    self.assertEqual( len(ensemble.atomIds), 3462)
    self.assertEqual( ensemble.coordinateData.shape, (1,3462,3))
    self.assertEqual( ensemble.atomIds[:8], ['A.10.ASN. N', 'A.10.ASN. CA', 'A.10.ASN. C',
                                            'A.10.ASN. O', 'A.10.ASN. CB', 'A.10.ASN. CG',
                                            'A.10.ASN. OD1', 'A.10.ASN. ND2'])
    self.assertTrue(self.project.save())
    # loadedProject = core.loadProject(self.project.path)
    loadedProject = Framework.createFramework(projectPath=self.project.path).project
    try:
      ensemble = loadedProject.structureEnsembles[0]
      self.assertEqual( len(ensemble.models), 1)
      self.assertEqual( len(ensemble.atomIds), 3462)
      self.assertEqual( ensemble.coordinateData.shape, (1,3462,3))
      self.assertEqual( ensemble.atomIds[:8], ['A.10.ASN. N', 'A.10.ASN. CA', 'A.10.ASN. C',
                                              'A.10.ASN. O', 'A.10.ASN. CB', 'A.10.ASN. CG',
                                              'A.10.ASN. OD1', 'A.10.ASN. ND2'])
    finally:
      loadedProject.delete()

  def test_modify_ensemble(self):
    atomIds2 = ['A.1.ALA.H', 'A.2b.TYR.N', 'B.5.GLX.CA', 'A.-1.VAL.HG2%']
    atomIds = ['@-.1.ALA.CA', '@-.2.VAL.CB', '@-.3.ASP.CG', '@-.4.LYS.CD']
    ensemble = self.project.newStructureEnsemble()
    ensemble.addAtomIds(atomIds)
    mod1 = ensemble.newModel(title='blah3', comment='hah', occupancyData=range(4), coordinateData=range(12))
    mod2 = ensemble.newModel(title='blah1', comment='hah2', occupancyData=range(4), bFactorData=range(4))
    mod3 = ensemble.newModel(title='blah2', comment='hah3', occupancyData=range(4), coordinateData=range(12))
    self.assertEqual(ensemble.atomIds, atomIds)
    data = ensemble.coordinateData
    flat = [x for x in data.flat]
    self.assertEqual( data.shape, (3,4,3))
    self.assertEqual(len(flat), 36)
    self.assertEqual(flat[:12], list(range(12)))
    self.assertEqual(flat[-12:], list(range(12)))
    self.assertTrue(numpy.isnan(flat[18]))
    self.assertEqual([x for x in ensemble.occupancyData.flat], [0,1,2,3]*3)
    self.assertTrue(numpy.isnan(ensemble.bFactorData.flat[2]))
    self.assertTrue(numpy.isnan(ensemble.bFactorData.flat[-3]))
    self.assertEqual([x for x in ensemble.bFactorData.flat][4:-4], [0,1,2,3])
    self.assertEqual([x.title for x in ensemble.models], ['blah3','blah1','blah2' ])

    ensemble.replaceAtomIds(atomIds2)
    self.assertEqual(ensemble.atomIds, atomIds2)

    ensemble.addAtomId('B.2.TRP.CE2')
    self.assertRaises(ValueError, ensemble.addAtomId, 'B.2.GLN.CE2')
    ll = atomIds2.copy()
    ll.insert(2, 'B.2.TRP.CE2')
    self.assertEqual(ensemble.atomIds, ll)
    self.assertEqual(ensemble.coordinateData.shape, (3,5,3))

    ensemble.removeAtomIds(('A.2b.TYR.N',))
    self.assertEqual(ensemble.coordinateData.shape, (3,4,3))
    ll.remove('A.2b.TYR.N')
    self.assertEqual(ensemble.atomIds, ll)

    mod2.delete()
    self.assertEqual(ensemble.coordinateData.shape, (2,4,3))

    ensemble.setAtomCoordinates('B.2.TRP.CE2', numpy.full((2,3), 9.))
    ensemble.setAtomBFactors('A.-1.VAL.HG2%', [0]*2)
    mod3.occupancyData = list(range(4))
    mod1.coordinateData =  numpy.full((4,3), -1.)
    self.assertEqual(ensemble.atomIds, ['A.1.ALA.H', 'B.2.TRP.CE2', 'B.5.GLX.CA', 'A.-1.VAL.HG2%'])
    self.assertEqual(ensemble.coordinateData.shape, (2, 4, 3))
    self.assertEqual(list(ensemble.coordinateData.flat), [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                                          -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                                          0.0, 1.0, 2.0, 9.0, 9.0, 9.0,
                                                          6.0, 7.0, 8.0, 9.0, 10.0, 11.0])

    self.assertEqual(ensemble.occupancyData.shape, (2, 4))
    self.assertEqual(ensemble.bFactorData.flat[3], 0.0)
    self.assertEqual(ensemble.bFactorData.flat[-1], 0.0)
    self.assertTrue(all(numpy.isnan(x) for x in ensemble.bFactorData.flat[4:-1]))
    self.assertEqual(list(ensemble.occupancyData.flat[2:]), [2.0, 3.0, 0.0, 1.0, 2.0, 3.0])
    self.assertTrue(numpy.isnan(ensemble.occupancyData.flat[1]))

    self.assertTrue(self.project.save())
    # loadedProject = core.loadProject(self.project.path)
    loadedProject = Framework.createFramework(projectPath=self.project.path).project
    try:
      ensemble = loadedProject.structureEnsembles[0]
      self.assertEqual(ensemble.atomIds, ['A.1.ALA.H', 'B.2.TRP.CE2', 'B.5.GLX.CA', 'A.-1.VAL.HG2%'])
      self.assertEqual(ensemble.coordinateData.shape, (2, 4, 3))
      self.assertEqual(list(ensemble.coordinateData.flat), [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                                            -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                                            0.0, 1.0, 2.0, 9.0, 9.0, 9.0,
                                                            6.0, 7.0, 8.0, 9.0, 10.0, 11.0])

      self.assertEqual(ensemble.occupancyData.shape, (2, 4))
      self.assertEqual(ensemble.bFactorData.flat[3], 0.0)
      self.assertEqual(ensemble.bFactorData.flat[-1], 0.0)
      self.assertTrue(all(numpy.isnan(x) for x in ensemble.bFactorData.flat[4:-1]))
      self.assertEqual(list(ensemble.occupancyData.flat[2:]), [2.0, 3.0, 0.0, 1.0, 2.0, 3.0])
      self.assertTrue(numpy.isnan(ensemble.occupancyData.flat[1]))
    finally:
      loadedProject.delete()
