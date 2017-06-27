"""
List widget

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.util.Constants import ccpnmrJsonData

class ListWidget(QtGui.QListWidget, Base):

  # To be done more rigeriously later
  _styleSheet = """
  QListWidget {background-color: #f7ffff; 
               color: #122043; 
               font-weight: normal;
               margin: 0px 0px 0px 0px;
               padding: 2px 2px 2px 2px;
               border: 1px solid #182548;
               }
  """
  def __init__(self, parent=None, objects=None, callback=None
               , rightMouseCallback=None
               , contextMenu=True
               , multiSelect=True
               , acceptDrops=False, **kw):

    QtGui.QListWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)

    self.setAcceptDrops(acceptDrops)
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
    self.currentContextMenu = self.getContextMenu

    self.setStyleSheet(self._styleSheet)

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


  def select(self, name):
    for index in range(self.count()):
      item = self.item(index)
      if item.text() == name:
        self.setCurrentItem(item)

  def clearSelection(self):
    for i in range(self.count()):
      item = self.item(i)
      self.setItemSelected(item, False)

  def getTexts(self):
    items = []
    for index in range(self.count()):
      items.append(self.item(index))
    return [i.text() for i in items]

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
    for selectedItem in self.selectedItems():
      self.takeItem(self.row(selectedItem))
        # self.takeItem(self.currentRow())

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
    menu = self.currentContextMenu()
    if menu:
      menu.move(event.globalPos().x(), event.globalPos().y() + 10)
      menu.exec()

  def getContextMenu(self):
    # FIXME this context menu must be more generic and editable
    contextMenu = Menu('', self, isFloatWidget=True)
    if self.rightMouseCallback is None:
      contextMenu.addItem("Delete", callback=self.removeItem)
      contextMenu.addItem("Delete All", callback=self._deleteAll)
    else:
      contextMenu.addItem("Delete", callback=self.contextCallback)
    return contextMenu

  # TODO:ED these are not very generic yet
  def setSelectContextMenu(self):
    self.currentContextMenu = self._getSelectContextMenu

  def _getSelectContextMenu(self):
    # FIXME this context menu must be more generic and editable
    contextMenu = Menu('', self, isFloatWidget=True)
    contextMenu.addItem("Select All", callback=self._selectAll)
    contextMenu.addItem("Clear Selection", callback=self._selectNone)
    return contextMenu

  def setSelectDeleteContextMenu(self):
    self.currentContextMenu = self._getSelectDeleteContextMenu

  def _getSelectDeleteContextMenu(self):
    # FIXME this context menu must be more generic and editable
    contextMenu = Menu('', self, isFloatWidget=True)
    contextMenu.addItem("Select All", callback=self._selectAll)
    contextMenu.addItem("Clear Selection", callback=self._selectNone)
    contextMenu.addItem("Delete", callback=self.removeItem)
    return contextMenu

  def _selectAll(self):
    """
    Select all items in the list
    """
    for i in range(self.count()):
      item = self.item(i)
      self.setItemSelected(item, True)

  def _selectNone(self):
    """
    Clear item selection
    """
    self.clearSelection()

  def _deleteAll(self):
    self.clear()

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
      if event.source() != self:  # otherwise duplicates
        event.setDropAction(QtCore.Qt.CopyAction)
        self.emit(QtCore.SIGNAL("dropped"), items)
        super(ListWidget, self).dropEvent(event)

      # ejb - tried to fix transfer of CopyAction, but intermittent
      # encodedData = event.mimeData().data(ccpnmrJsonData)
      # stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.ReadOnly)
      # eventData = stream.readQVariantHash()
      #
      # items = []
      # if event.source() != self: #otherwise duplicates
      #   actionType = QtCore.Qt.CopyAction
      #   if 'dragAction' in eventData.keys():        # put these strings somewhere else
      #     if eventData['dragAction'] == 'copy':
      #       actionType = QtCore.Qt.CopyAction             # ejb - changed from Move
      #     elif eventData['dragAction'] == 'move':
      #       actionType = QtCore.Qt.MoveAction             # ejb - changed from Move
      #
      #   event.setDropAction(actionType)
      #   self.emit(QtCore.SIGNAL("dropped"), items)
      #   super(ListWidget, self).dropEvent(event)
      # else:
      #   event.ignore()



from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Spacer import Spacer

class ListWidgetPair(Frame):
  """
  Define a pair of listWidgets such that informaiton can be cpoied from one side
  to the other and vise-versa
  """
  def __init__(self, parent=None, objects=None, callback=None
               , rightMouseCallback=None
               , contextMenu=True
               , multiSelect=True
               , acceptDrops=False
               , title='Copy Items', **kw):
    """
    Initialise the pair of listWidgets
    :param parent:
    :param objects:
    :param callback:
    :param rightMouseCallback:
    :param contextMenu:
    :param multiSelect:
    :param acceptDrops:
    :param pairName:
    :param kw:
    """
    Frame.__init__(self, parent, **kw)

    self.title = Label(self, text=title, setLayout=True, grid=(0,0))
    self.leftList = ListWidget(self, setLayout=True, grid=(1,0), gridSpan=(5,1))
    self.rightList = ListWidget(self, setLayout=True, grid=(1,5), gridSpan=(5,1))
    self.leftList.setSelectContextMenu()
    self.rightList.setSelectContextMenu()
    # self.rightList.setSelectDeleteContextMenu()

    self.leftList.itemDoubleClicked.connect(self._moveRight)
    self.rightList.itemDoubleClicked.connect(self._moveLeft)

    self.leftIcon = Icon('icons/previous')    # stylesheet error for these
    self.rightIcon = Icon('icons/next')

    self.buttons = ButtonList(self, texts=['', '']
                             , icons=[self.leftIcon, self.rightIcon]
                             , callbacks=[self._moveLeft, self._moveRight]
                             , direction='v'
                             , grid=(3,3), hAlign='c')
    self.buttons.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

    # self.button = Button(self, text=''
    #                          , icon=self.rightIcon
    #                          , callback=self._copyRight
    #                          , grid=(3,3))
    # self.button.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

    self.spacer1 = Spacer(self, 10, 10
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(2,2), gridSpan=(1,1))
    self.spacer2 = Spacer(self, 10, 10
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(4,4), gridSpan=(1,1))

    # self.showBorder=True
    # self.leftList.setContentsMargins(15,15,15,15)
    # self.rightList.setContentsMargins(15,15,15,15)

  def setListObjects(self, left):
    # self.leftObjects = left
    # self._populate(self.leftList, self.objects)

    self.objects = left
    self._populate(self.rightList, self.objects)

  def _populate(self, list, objs):
    """
    List the Pids of the objects in the listWidget
    :param list: target listWidget
    :param objs: list of objects with Pids
    """
    list.clear()
    if objs:
      for item in objs:
        item = QtGui.QListWidgetItem(str(item.pid))
        list.addItem(item)
    list.sortItems()

  def _moveLeft(self):    # not needed now
    """
    Move contents of the right window to the left window
    """
    for item in self.rightList.selectedItems():
      leftItem = QtGui.QListWidgetItem(item)
      self.leftList.addItem(leftItem)
      self.rightList.takeItem(self.rightList.row(item))
    self.leftList.sortItems()

  def _moveRight(self):  # not needed now
    """
    Move contents of the left window to the right window
    """
    for item in self.leftList.selectedItems():
      rightItem = QtGui.QListWidgetItem(item)
      self.rightList.addItem(rightItem)
      self.leftList.takeItem(self.leftList.row(item))
    self.rightList.sortItems()

  def _moveItemLeft(self):
    """
    Move contents of the right window to the left window
    """
    rightItem = QtGui.QListWidgetItem(self.rightList.selectedItems())
    self.leftList.addItem(rightItem)
    self.rightList.takeItem(self.rightList.row(rightItem))
    self.leftList.sortItems()

  def _moveItemRight(self):
    """
    Move contents of the left window to the right window
    """
    leftItem = QtGui.QListWidgetItem(self.leftList.selectedItem)
    self.rightList.addItem(leftItem)
    self.leftList.takeItem(self.leftList.row(leftItem))
    self.rightList.sortItems()

  def _copyRight(self):
    """
    Copy selection of the left window to the right window
    """
    for item in self.leftList.selectedItems():
      rightItem = QtGui.QListWidgetItem(item)
      self.rightList.addItem(rightItem)
    self.rightList.sortItems()

  def getLeftList(self):
    return self.leftList.getTexts()

  def getRightList(self):
    return self.rightList.getTexts()

#===================================================================================================
# __main__
#===================================================================================================

if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup
  from ccpn.ui.gui.widgets.Icon import Icon

  app = TestApplication()

  texts = ['Int', 'Float', 'String', 'icon']
  objects = [int, float, str, 'Green']
  icons = [None, None, None, Icon(color='#008000')]

  def callback(object):
    print('callback', object)

  def callback2(object):
    print('callback2', object)

  popup = BasePopup(title='Test PulldownList')

  # policyDict = dict(
  #   vAlign='top',
  #   hPolicy='expanding',
  # )
  # policyDict = dict(
  #   vAlign='top',
  #   # hAlign='left',
  # )
  # policyDict = dict(
  #   hAlign='left',
  # )
  policyDict = {}

  app.start()
