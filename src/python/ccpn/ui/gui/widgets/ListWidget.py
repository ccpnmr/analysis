
from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList


class ListCompoundWidget(Frame):
  """
  Compound class comprising a Label and a PulldownList, and a ListWidget, combined in a Frame
  """
  def __init__(self, parent, showBorder=False, orientation='left', minimumWidths=None, labelText='',
                             texts=None, callback=None, **kwds):
    """
    :param parent: parent widget
    :param showBorder: flag to display the border of Frame (True, False)
    :param orientation: flag to determine the orientation of the labelText relative to the Pulldown/ListWidget.
                        Allowed values: 'left', 'right', 'top', 'bottom', 'centreLeft, centreRight, horizontal
    :param minimumWidths: tuple of three values specifying the minimum width of the Label, Pulldown and ListWidget, 
                          respectively
    :param labelText: Text for the Label
    :param texts: list of text values for the Pulldown
    :param callback: callback for the ListWidget
    :param kwds: (optional) keyword, value pairs for the gridding
    
    left:
    Label       PullDown         
                ListWidget
           
    centreLeft:
                PullDown         
    Label       ListWidget
    
    right:
    PullDown    Label   
    ListWidget
    
    centreRight:
    PullDown       
    ListWidget  Label

    top:
    Label
    PullDown       
    ListWidget
    
    bottom:
    PullDown       
    ListWidget
    Label
    
    horizontal:
    Label       PullDown  ListWidget

    """

    Frame.__init__(self, parent=parent, showBorder=showBorder, **kwds)

    self.label = Label(parent=self, text=labelText, vAlign='center')
    self.pulldownList = PulldownList(parent=self, texts=[' > select-to-add <']+texts, callback=self._addListWidget, index=0)
    self.listWidget = ListWidget(parent=self, callback=callback)

    if minimumWidths is not None and len(minimumWidths) == 3:
      self.label.setMinimumWidth(minimumWidths[0])
      self.pulldownList.setMinimumWidth(minimumWidths[1])
      self.listWidget.setMinimumWidth(minimumWidths[2])

    layoutDict = dict(
      # grid positions for label, pulldown and listWidget
      left =        [(0, 0), (0, 1), (1, 1)],
      centreLeft =  [(1, 0), (0, 1), (1, 1)],
      right =       [(0, 1), (0, 0), (1, 0)],
      centreRight = [(1, 1), (0, 0), (1, 0)],
      top =         [(0, 0), (1, 0), (2, 0)],
      bottom =      [(2, 0), (0, 0), (1, 0)],
      horizontal =  [(0, 0), (0, 1), (0, 2)],
    )
    if orientation in layoutDict:
      lbl, pld, lst = layoutDict[orientation]
      self.layout().addWidget(self.label, lbl[0], lbl[1])
      self.layout().addWidget(self.pulldownList, pld[0], pld[1])
      self.layout().addWidget(self.listWidget, lst[0], lst[1])

    else:
      raise RuntimeError('Invalid parameter "orientation" (%s)' % orientation)

  def _addListWidget(self, item):
    "Callback for Pulldown"

    texts = [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
    #print('>>', texts)
    if item is not None and \
       self.pulldownList.getSelectedIndex()!=0 and \
       len(item)>0 and \
       item not in texts:
      self.listWidget.addItem(item)
    # reset to first > select-to-add < entry
    self.pulldownList.setIndex(0)


class ListWidget(QtGui.QListWidget, Base):

  def __init__(self, parent, objects=None, callback=None, rightMouseCallback=None, contextMenu=True, multiSelect=True, **kw):

    QtGui.QListWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)

    self.setAcceptDrops(False)
    self.contextMenu = contextMenu
    self.callback = callback
    self.objects = list(objects or [])
    self.items = list(objects or [])
    self.multiSelect = multiSelect

    self.rightMouseCallback = rightMouseCallback
    if callback is not None:
      self.itemClicked.connect(callback)

    if self.multiSelect:
      self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    else:
      self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

    self.contextMenuItem = 'Delete'

  def contextCallback(self, remove=True):

    if remove:
      self.removeItem()
    self.rightMouseCallback()

  def setObjects(self, objects, name='pid'):
    self.clear()
    self.objects = list(objects)
    for obj in objects:
      if hasattr(obj, name):
        item = QtGui.QListWidgetItem(getattr(obj, name), self)
        item.setData(QtCore.Qt.UserRole, obj)
        self.addItem(item)
        self.items.append(item)

      else:
        item = QtGui.QListWidgetItem(str(obj))
        item.setData(QtCore.Qt.UserRole, obj)
        self.addItem(item)

  def getObjects(self):
     return list(self.objects)

  def getSelectedObjects(self):
    indexes =  self.selectedIndexes()
    objects = []
    for item in indexes:
      obj = item.data(QtCore.Qt.UserRole)
      if obj is not None:
        objects.append(obj)
    return objects

  def selectObject(self, obj):
    for item in self.items:
      itemObject = item.data(QtCore.Qt.UserRole)
      if obj == itemObject:
        item.setSelected(True)

  def selectObjects(self, objs):
    self.clearSelection()
    for obj in objs:
      self.selectObject(obj)

  def removeItem(self):
    self.takeItem(self.currentRow())

  def mousePressEvent(self, event):
    self._mouse_button = event.button()
    if event.button() == QtCore.Qt.RightButton:
      if self.contextMenu:
        self.raiseContextMenu(event)
    elif event.button() == QtCore.Qt.LeftButton:
      if self.itemAt(event.pos()) is None:
        self.clearSelection()
      else:
        super(ListWidget, self).mousePressEvent(event)

  def raiseContextMenu(self, event):
    """
    Raise the context menu
    """
    menu = self.getContextMenu()
    menu.popup(event.globalPos())

  def getContextMenu(self):
    contextMenu = Menu('', self, isFloatWidget=True)
    if self.rightMouseCallback is None:
      contextMenu.addItem("Delete", callback=self.removeItem)
    else:
      contextMenu.addItem("Delete", callback=self.contextCallback)
    return contextMenu

  def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
      event.accept()
    else:
      super(ListWidget, self).dragEnterEvent(event)

  def dragMoveEvent(self, event):
    if event.mimeData().hasUrls():
      event.setDropAction(QtCore.Qt.CopyAction)
      event.accept()
    else:
      super(ListWidget, self).dragMoveEvent(event)

  def dropEvent(self, event):
    if event.mimeData().hasUrls():
      event.setDropAction(QtCore.Qt.CopyAction)
      event.accept()
      links = []
      for url in event.mimeData().urls():
        links.append(str(url.toLocalFile()))
      self.emit(QtCore.SIGNAL("dropped"), links)
    else:
      items = []
      event.setDropAction(QtCore.Qt.MoveAction)
      self.emit(QtCore.SIGNAL("dropped"), items)
      super(ListWidget, self).dropEvent(event)


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup
  from ccpn.ui.gui.widgets.Icon import Icon

  app = TestApplication()

  texts = ['Int', 'Float', 'String', '']
  objects = [int, float, str, 'Green']
  icons = [None, None, None, Icon(color='#008000')]


  def callback(object):
    print('callback', object)


  def callback2(object):
    print('callback2', object)


  popup = BasePopup(title='Test PulldownList')
  # popup.setSize(250,50)
  policyDict = dict(
    vAlign='top',
    hPolicy='expanding',
  )
  policyDict = dict(
    vAlign='top',
    # hAlign='left',
  )
  # policyDict = dict(
  #   hAlign='left',
  # )
  policyDict = {}


  widget = ListCompoundWidget(parent=popup, orientation='left', showBorder=True,
                              labelText='test-label', texts=texts,
                              callback=callback2, grid=(0,0),
                                **policyDict)
  widget2 = ListCompoundWidget(parent=popup, orientation='top', showBorder=True,
                              labelText='test-label2', texts=texts,
                              callback=callback2, grid=(1,0),
                                **policyDict)

  app.start()
