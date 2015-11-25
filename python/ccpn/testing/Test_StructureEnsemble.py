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
import numpy
from ccpn.testing.WrapperTesting import WrapperTesting
import ccpn

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
    print ('@~@~1', len(ensemble.models), len(ensemble.atomIds), ensemble.coordinateData.shape,
           ensemble.atomIds[:8])
    self.project.save()
    loadedProject = ccpn.loadProject(self.project.path)
    print ('@~@~2', len(ensemble.models), len(ensemble.atomIds), ensemble.coordinateData.shape,
           ensemble.atomIds[:8])

  def test_modify_ensemble(self):
    ensemble = self.project.newStructureEnsemble()
    ensemble.addAtomIds(('A.1.ALA.H', 'A.2b.TYR.N', 'B.5.GLX.CA', 'A.-1.VAL.HG2%'))
    mod1 = ensemble.newModel(name='blah', comment='hah', occupancyData=range(4), coordinateData=range(12))
    mod2 = ensemble.newModel(name='blah2', comment='hah2', occupancyData=range(4))
    mod3 = ensemble.newModel(name='blah', comment='hah3', bFactorData=range(4), coordinateData=range(12))
    data = ensemble.coordinateData
    print ('@~@~ coords-2', ensemble._wrappedData.nAtoms, data.shape,len(data.flat), list(data.flat))

    print ('@~@~1 coordinateData', ensemble.coordinateData.shape,list(ensemble.coordinateData.flat))
    print ('@~@~1 occupancyData', ensemble.occupancyData.shape,list(ensemble.occupancyData.flat))
    print ('@~@~1b coordinateData', ensemble.coordinateData.shape,list(ensemble.coordinateData.flat))
    ensemble.replaceAtomIds(('@1.1.ALA.CA', '@1.2.VAL.CB', '@1.3.ASP.CG', '@1.4.LYS.CD'))
    print ('@~@~2 coordinateData', ensemble.coordinateData.shape,list(ensemble.coordinateData.flat))
    print ('@~@~2 occupancyData', ensemble.occupancyData.shape, list(ensemble.occupancyData.flat))
    data = ensemble.coordinateData
    print ('@~@~ coords-1', ensemble._wrappedData.nAtoms, data.shape,len(data.flat), list(data.flat))
    print ('@~@~ atomIds0',ensemble.atomIds, [(x.name, x.index) for x in ensemble._wrappedData.orderedAtoms])
    ensemble.addAtomId('@1.5.TRP.CE2')
    data = ensemble.coordinateData
    print ('@~@~ coords0', ensemble._wrappedData.nAtoms, data.shape,len(data.flat), list(data.flat))
    print ('@~@~ atomIds1',ensemble.atomIds, [(x.name, x.index) for x in ensemble._wrappedData.orderedAtoms])
    ensemble.removeAtomIds(('@1.2.VAL.CB',))
    data = ensemble.coordinateData
    print ('@~@~ coords1', ensemble._wrappedData.nAtoms, data.shape,len(data.flat), list(data.flat))
    print(ensemble.occupancyData.shape, list(ensemble.occupancyData.flat))
    mod2.delete()
    print ('@~@~ atomIds2',ensemble.atomIds, [(x.name, x.index) for x in ensemble._wrappedData.orderedAtoms])
    data = ensemble.coordinateData
    print ('@~@~ coords2', ensemble._wrappedData.nAtoms, data.shape,len(data.flat), list(data.flat))
    print(ensemble.occupancyData.shape, list(ensemble.occupancyData.flat))
    ensemble.setAtomCoordinates('@1.5.TRP.CE2', numpy.full((2,3), 9.))
    ensemble.setAtomBFactors('@1.4.LYS.CD', [0]*2)
    mod3.occupancyData = list(range(4))
    mod1.coordinateData =  numpy.full((4,3), -1.)
    print (ensemble.coordinateData.shape,list(ensemble.coordinateData.flat))
    print(ensemble.occupancyData.shape, list(ensemble.occupancyData.flat))
    print(ensemble.bFactorData.shape, list(ensemble.bFactorData.flat))
    self.project.save()
    loadedProject = ccpn.loadProject(self.project.path)
    ensemble = loadedProject.structureEnsembles[0]
    print (ensemble.atomIds)
    print (ensemble.atomIds)
    print (ensemble.coordinateData.shape,list(ensemble.coordinateData.flat))
    print(ensemble.occupancyData.shape, list(ensemble.occupancyData.flat))
    print(ensemble.bFactorData.shape, list(ensemble.bFactorData.flat))

