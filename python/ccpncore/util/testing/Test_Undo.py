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
from ccpncore.util.Undo import Undo
from ccpncore.util import Io as ioUtil

def test_undo_create():
  undoObject = Undo()

def test_undo_create_maxwaypoints():
  undoObject = Undo(maxWaypoints=100)

def test_undo_add_simple_item():

  def func(*args, **kwargs):
    pass

  undoObject = Undo()
  undoObject.addItem(func, func)

def test_undo_add_full_item():

  def func(*args, **kwargs):
    pass

  undoObject = Undo()
  undoObject.addItem(func, func, undoArgs=(1,2), undoKwargs={1:2},
                     redoArgs=(3,4), redoKwargs={3:4})

def test_undo_one_undo():
  undoObject = Undo()
  undoObject.undo()

def _myUndoFunc(*args, **kwargs):
  print('_myUndoFunc:', args, kwargs)

def _myRedoFunc(*args, **kwargs):
  print('_myRedoFunc:', args, kwargs)

def test_undo_add_item_one_undo():
  undoObject = Undo()
  undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(5,))
  undoObject.undo()

def test_undo_add_items_one_undo():
  undoObject = Undo(maxWaypoints=0)
  undoDataList = range(5)
  for undoData in undoDataList:
    undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,))
  undoObject.undo()

def test_undo_add_items_one_undo_one_redo():
  undoObject = Undo(maxWaypoints=0)
  undoDataList = range(5)
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(redoData,))
  undoObject.undo()
  undoObject.redo()

def test_undo_add_items_many_undos_redos():
  undoObject = Undo(maxWaypoints=0)
  undoMethod = _myUndoFunc
  undoDataList = range(5)
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(redoData,))
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
  undoObject = Undo(maxWaypoints=0)
  undoDataList = range(5)
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(redoData,))
  undoObject.undo()
  undoObject.undo()
  undoObject.redo()
  undoObject.redo()

  undoData = 8
  redoData = -undoData
  undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(redoData,))

  undoObject.undo()
  undoObject.undo()
  undoObject.undo()
  undoObject.redo()
  undoObject.redo()
  undoObject.undo()

def test_undo_add_waypoint_one_undo():
  undoObject = Undo()
  undoDataList = range(5)
  undoObject.newWaypoint()
  for undoData in undoDataList:
    undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(-undoData,))
  undoObject.undo()

def test_undo_max_waypoints():
  undoObject = Undo(maxWaypoints=4)
  undoDataList = range(5)
  for ii in range(6):
    undoObject.newWaypoint()
    for undoData in undoDataList:
      undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(-undoData,))

  for ii in range(6):
    undoObject.undo()

def test_undo_max_operations():
  undoObject = Undo(maxOperations=4)
  undoDataList = range(5)
  for ii in range(6):
    for undoData in undoDataList:
      undoObject.addItem(_myUndoFunc, _myRedoFunc, undoArgs=(undoData,), redoArgs=(-undoData,))

  for ii in range(6):
    undoObject.undo()

def test_api_undo_init():
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  project._undo.undo()
  project._undo.redo()

def test_api_undo_set_single():
  testValue = 'TrySomeString'
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  project._undo.newWaypoint()
  nxp.details = testValue
  project._undo.undo()
  assert nxp.details is None, "set undo: details are None after undo"


def test_api_undo_redo_set_single():
  testValue = 'TrySomeString'
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  project._undo.newWaypoint()
  nxp.details = testValue
  project._undo.undo()
  project._undo.redo()
  assert nxp.details == testValue, "set redo: details are back to testValue after redo"

def test_api_undo_set_multiple():
  testValue = ('kw1', 'kw2', 'kw3')
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  project._undo.newWaypoint()
  nxp.keywords = testValue
  project._undo.undo()
  assert not nxp.keywords, "multiple set undo: keywords are empty after undo"

def test_api_undo_redo_set_multiple():
  testValue = ('kw1', 'kw2', 'kw3')
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  project._undo.newWaypoint()
  nxp.keywords = testValue
  project._undo.undo()
  project._undo.redo()
  assert nxp.keywords == testValue, "multiple set redo: details are back to testValue after redo"

def test_api_undo_redo_add():
  testValue = ('kw1', 'kw2', 'kw3')
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  nxp.keywords = testValue
  project._undo.newWaypoint()
  nxp.addKeyword('kw4')
  project._undo.undo()
  project._undo.redo()
  assert nxp.keywords == testValue + ('kw4',), "add redo: keywords should be %s, were %s" % (testValue + ('kw4',), nxp.keywords)

def test_api_undo_add():
  testValue = ('kw1', 'kw2', 'kw3')
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  nxp.keywords = testValue
  project._undo.newWaypoint()
  nxp.addKeyword('kw4')
  project._undo.undo()
  assert nxp.keywords == testValue, "add undo: keywords should be %s, were %s" % (testValue, nxp.keywords)

def test_api_undo_remove():
  testValue = ('kw1', 'kw2', 'kw3')
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  nxp.keywords = testValue
  project._undo.newWaypoint()
  nxp.removeKeyword('kw3')
  project._undo.undo()
  assert nxp.keywords == testValue,"remove undo: keywords should be %s, were %s" % (testValue, nxp.keywords)

def test_api_undo_redo_remove():
  testValue = ('kw1', 'kw2', 'kw3')
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  nxp.keywords = testValue
  project._undo.newWaypoint()
  nxp.removeKeyword('kw3')
  project._undo.undo()
  project._undo.redo()
  assert nxp.keywords == testValue[:2], "remove redo: keywords should be %s, were %s" % (testValue[:2], nxp.keywords)

def test_api_undo_delete():
  project = ioUtil.newProject('UndoTest')
  project._undo = Undo()
  nxp = project.newNmrExpPrototype(name='anything', category='other')
  nxp.delete()
  project._undo.undo()
  project._undo.redo()

