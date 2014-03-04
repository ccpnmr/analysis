from ccpncore.util.Undo import Undo

def test_undo_create():
  undoObject = Undo()

def test_undo_create_maxwaypoints():
  undoObject = Undo(maxWaypoints=100)

def test_undo_add_one_item():
  undoObject = Undo()
  undoMethod = undoData = redoMethod = redoData = None
  undoObject.addItem(undoMethod, undoData, redoMethod, redoData)

def test_undo_one_undo():
  undoObject = Undo()
  undoObject.undo()

def _myUndoFunc(x):
  print('_myUndoFunc:', x)

def _myRedoFunc(x):
  print('_myRedoFunc:', x)

def test_undo_add_item_one_undo():
  undoObject = Undo()
  undoMethod = _myUndoFunc
  undoData = 5
  redoMethod = redoData = None
  undoObject.addItem(undoMethod, undoData, redoMethod, redoData)
  undoObject.undo()

def test_undo_add_items_one_undo():
  undoObject = Undo()
  undoMethod = _myUndoFunc
  undoDataList = range(5)
  redoMethod = redoData = None
  for undoData in undoDataList:
    undoObject.addItem(undoMethod, undoData, redoMethod, redoData)
  undoObject.undo()

def test_undo_add_items_one_undo_one_redo():
  undoObject = Undo()
  undoMethod = _myUndoFunc
  undoDataList = range(5)
  redoMethod = _myRedoFunc
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.addItem(undoMethod, undoData, redoMethod, redoData)
  undoObject.undo()
  undoObject.redo()

def test_undo_add_items_many_undos_redos():
  undoObject = Undo()
  undoMethod = _myUndoFunc
  undoDataList = range(5)
  redoMethod = _myRedoFunc
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.addItem(undoMethod, undoData, redoMethod, redoData)
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
  undoObject = Undo()
  undoMethod = _myUndoFunc
  undoDataList = range(5)
  redoMethod = _myRedoFunc
  for undoData in undoDataList:
    redoData = -undoData
    undoObject.addItem(undoMethod, undoData, redoMethod, redoData)
  undoObject.undo()
  undoObject.undo()
  undoObject.redo()
  undoObject.redo()

  undoData = 8
  redoData = -undoData
  undoObject.addItem(undoMethod, undoData, redoMethod, redoData)

  undoObject.undo()
  undoObject.undo()
  undoObject.undo()
  undoObject.redo()
  undoObject.redo()
  undoObject.undo()

def test_undo_add_waypoint_one_undo():
  undoObject = Undo()
  undoMethod = _myUndoFunc
  undoDataList = range(5)
  redoMethod = redoData = None
  undoObject.newWaypoint()
  for undoData in undoDataList:
    undoObject.addItem(undoMethod, undoData, redoMethod, redoData)
  undoObject.undo()

