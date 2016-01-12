"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================


from ccpncore.testing.CoreTesting import CoreTesting
import os
from ccpncore.util import Path
from ccpncore.util import Io
TEST_PROJECTS_PATH = os.path.join(Path.getTopDirectory(), 'data/testProjects')
from ccpncore.memops.ApiError import ApiError

class NaNtest(CoreTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def testNaN(self):
    spectrum = self.nmrProject.createDummySpectrum(name='nanTest', axisCodes=('Hn', 'Nh', 'CO'))
    self.assertEqual(spectrum.scale, 1.0)
    self.assertEqual(spectrum.name, 'nanTest')

    # test NaN
    self.assertRaises(ApiError,setattr, spectrum, 'scale', float('NaN'))

class CrosslinkUndoTest(CoreTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_many_to_one(self):
    root = self.nmrProject.root
    nmrProjects = [root.newNmrProject(name=str(x)) for x in range(6)]
    ms0, ms1, ms2 = [root.newMolSystem(code=str(x)) for x in range(3)]
    ms0.nmrProjects = nmrProjects[:2]
    ms1.nmrProjects = nmrProjects[2:4]
    self.undo.newWaypoint()
    ms1.nmrProjects = nmrProjects[1:3]
    self.assertEquals(ms0.nmrProjects, frozenset((nmrProjects[0],)))
    self.assertEquals(ms1.nmrProjects, frozenset(nmrProjects[1:3]))
    self.assertEquals(set(x for x in nmrProjects if x.molSystem is None), set(nmrProjects[3:]))
    self.undo.undo()
    self.assertEquals(ms0.nmrProjects, frozenset(nmrProjects[:2]))
    self.assertEquals(ms1.nmrProjects, frozenset(nmrProjects[2:4]))
    self.assertEquals(set(x for x in nmrProjects if x.molSystem is None), set(nmrProjects[4:]))

  def test_many_to_one_deletion(self):
    root = self.nmrProject.root
    nmrProjects = [root.newNmrProject(name=str(x)) for x in range(6)]
    ms0 = root.newMolSystem(code='0')
    ms0.nmrProjects = nmrProjects[:4]
    self.undo.newWaypoint()
    ms1 = root.newMolSystem(code='1', nmrProjects=nmrProjects[2:])
    self.assertEquals(ms0.nmrProjects, frozenset(nmrProjects[:2]))
    self.assertEquals(ms1.nmrProjects, frozenset(nmrProjects[2:]))
    self.undo.undo()
    self.assertTrue(ms1.isDeleted)
    self.assertEquals(set(x for x in nmrProjects if x.molSystem is None), set(nmrProjects[4:]))
    self.assertEquals(ms0.nmrProjects, frozenset(nmrProjects[:4]))

  # NB you could have a similar problem with 0..1 <-> 0..1 links, but the only underived,
  # unfrozen example is ccp.molecule.MolStructure.StructureEnsemble.structureGeneration,
  # Which is not in use, so it is not worth teh hassle


