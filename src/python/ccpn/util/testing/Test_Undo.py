"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:03 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.Undo import Undo
from ccpnmodel.ccpncore.testing.CoreTesting import CoreTesting


def test_undo_create():
  undoObject = Undo()

def test_undo_create_maxwaypoints():
  undoObject = Undo(maxWaypoints=100)

def test_undo_add_simple_item():

  def func(*args, **kwargs):
    pass

  undoObject = Undo(debug=True)
  undoObject.newItem(func, func)

def test_undo_add_full_item():

  def func(*args, **kwargs):
    pass

  undoObject = Undo(debug=True)
  undoObject.newItem(func, func, undoArgs=(1,2), undoKwargs={1:2},
                     redoArgs=(3,4), redoKwargs={3:4})

def test_undo_one_undo():
  undoObject = Undo(debug=True)
  undoObject.undo()

def _myUndoFunc(*args, **kwargs):
  print('_myUndoFunc:', args, kwargs)

def _myRedoFunc(*args, **kwargs):
  print('_myRedoFunc:', args, kwargs)

def test_undo_add_item_one_undo():
  undoObject = Undo(debug=True)
  undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(5,))
  undoObject.undo()

def test_undo_add_items_one_undo():
  undoObject = Undo(maxWaypoints=0)
  undoDataList = range(5)
  for undoData in undoDataList:
    undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,))
  undoObject.undo()

def test_undo_add_items_one_undo_one_redo():
  undoObject = Undo(maxWaypoints=0)
  undoDataList = range(5)
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(redoData,))
  undoObject.undo()
  undoObject.redo()

def test_undo_add_items_many_undos_redos():
  undoObject = Undo(maxWaypoints=0, debug=True)
  undoMethod = _myUndoFunc
  undoDataList = range(5)
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(redoData,))
  undoObject.undo()
  undoObject.undo()
  undoObject.redo()
  undoObject.redo()

  undoObject.undo()
  undoObject.undo()
  undoObject.undo()
  undoObject.redo()
  undoObject.redo()
  undoObject.undo()

def test_undo_add_items_many_undos_redos_add_another_item_undos_redos():
  undoObject = Undo(maxWaypoints=0, debug=True)
  undoDataList = range(5)
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(redoData,))
  undoObject.undo()
  undoObject.undo()
  undoObject.redo()
  undoObject.redo()

  undoData = 8
  redoData = -undoData
  undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(redoData,))

  undoObject.undo()
  undoObject.undo()
  undoObject.undo()
  undoObject.redo()
  undoObject.redo()
  undoObject.undo()

def test_undo_add_waypoint_one_undo():
  undoObject = Undo(debug=True)
  undoDataList = range(5)
  undoObject.newWaypoint()
  for undoData in undoDataList:
    undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(-undoData,))
  undoObject.undo()

def test_undo_max_waypoints():
  undoObject = Undo(maxWaypoints=4, debug=True)
  undoDataList = range(5)
  for ii in range(6):
    undoObject.newWaypoint()
    for undoData in undoDataList:
      undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(-undoData,))

  for ii in range(6):
    undoObject.undo()

def test_undo_max_operations():
  undoObject = Undo(maxOperations=4, debug=True)
  undoDataList = range(5)
  for ii in range(6):
    for undoData in undoDataList:
      undoObject.newItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(-undoData,))

  for ii in range(6):
    undoObject.undo()


class Test_Undo(CoreTesting):


  # Path of project to load (None for new project)
  projectPath = None

  def test_api_undo_init(self):
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    project._undo.undo()
    project._undo.redo()

  def test_api_undo_set_single(self):
    testValue = 'TrySomeString'
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    project._undo.newWaypoint()
    nxp.details = testValue
    project._undo.undo()
    assert nxp.details is None, "set undo: details are None after undo"


  def test_api_undo_redo_set_single(self):
    testValue = 'TrySomeString'
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    project._undo.newWaypoint()
    nxp.details = testValue
    project._undo.undo()
    project._undo.redo()
    assert nxp.details == testValue, "set redo: details are back to testValue after redo"

  def test_api_undo_set_multiple(self):
    testValue = ('kw1', 'kw2', 'kw3')
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    project._undo.newWaypoint()
    nxp.keywords = testValue
    project._undo.undo()
    assert not nxp.keywords, "multiple set undo: keywords are empty after undo"

  def test_api_undo_redo_set_multiple(self):
    testValue = ('kw1', 'kw2', 'kw3')
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    project._undo.newWaypoint()
    nxp.keywords = testValue
    project._undo.undo()
    project._undo.redo()
    assert nxp.keywords == testValue, "multiple set redo: details are back to testValue after redo"

  def test_api_undo_redo_add(self):
    testValue = ('kw1', 'kw2', 'kw3')
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    nxp.keywords = testValue
    project._undo.newWaypoint()
    nxp.addKeyword('kw4')
    project._undo.undo()
    project._undo.redo()
    assert nxp.keywords == testValue + ('kw4',), "add redo: keywords should be %s, were %s" % (testValue + ('kw4',), nxp.keywords)

  def test_api_undo_add(self):
    testValue = ('kw1', 'kw2', 'kw3')
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    nxp.keywords = testValue
    project._undo.newWaypoint()
    nxp.addKeyword('kw4')
    project._undo.undo()
    assert nxp.keywords == testValue, "add undo: keywords should be %s, were %s" % (testValue, nxp.keywords)

  def test_api_undo_remove(self):
    testValue = ('kw1', 'kw2', 'kw3')
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    nxp.keywords = testValue
    project._undo.newWaypoint()
    nxp.removeKeyword('kw3')
    project._undo.undo()
    assert nxp.keywords == testValue,"remove undo: keywords should be %s, were %s" % (testValue, nxp.keywords)

  def test_api_undo_redo_remove(self):
    testValue = ('kw1', 'kw2', 'kw3')
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    nxp.keywords = testValue
    project._undo.newWaypoint()
    nxp.removeKeyword('kw3')
    project._undo.undo()
    project._undo.redo()
    assert nxp.keywords == testValue[:2], "remove redo: keywords should be %s, were %s" % (testValue[:2], nxp.keywords)

  def test_api_undo_delete(self):
    project = self.project
    project._undo = Undo(debug=True)
    nxp = project.newNmrExpPrototype(name='anything', category='other')
    nxp.delete()
    project._undo.undo()
    project._undo.redo()

  def test_make_molecule_undo(self):
    from ccpnmodel.ccpncore.lib.molecule import MoleculeModify
    project = self.project
    project._undo = Undo(debug=True)
    sequence = ['Gln', 'Trp', 'Glu', 'Arg', 'Thr', 'Tyr', 'Ile', 'Pro', 'Ala']
    molecule = MoleculeModify.createMolecule(project, sequence, 'protein')
    project._undo.undo()
    project.checkAllValid()

  def test_make_molecule_undo_redo(self):
    from ccpnmodel.ccpncore.lib.molecule import MoleculeModify
    project = self.project
    project._undo = Undo(debug=True)
    sequence = ['Gln', 'Trp', 'Glu', 'Arg', 'Thr', 'Tyr', 'Ile', 'Pro', 'Ala']
    molecule = MoleculeModify.createMolecule(project, sequence, 'protein')
    project._undo.undo()
    project._undo.redo()
    project.checkAllValid()
