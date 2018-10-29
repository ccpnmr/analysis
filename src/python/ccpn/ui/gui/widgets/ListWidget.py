"""
List widget

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.util.Constants import ccpnmrJsonData


class ListWidget(QtWidgets.QListWidget, Base):
    # # To be done more rigeriously later
    # _styleSheet = """
    # QListWidget {background-color: #f7ffff;
    #              color: #122043;
    #              font-weight: normal;
    #              margin: 0px 0px 0px 0px;
    #              padding: 2px 2px 2px 2px;
    #              border: 1px solid #182548;
    #              }
    # """

    dropped = pyqtSignal(list)
    cleared = pyqtSignal()

    def __init__(self, parent=None, objects=None, callback=None,
                 rightMouseCallback=None,
                 contextMenu=True,
                 multiSelect=True,
                 acceptDrops=False,
                 sortOnDrop=False,
                 copyDrop=True,
                 **kw):

        QtWidgets.QListWidget.__init__(self, parent)
        Base.__init__(self, **kw)

        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)

        self.setAcceptDrops(acceptDrops)
        self.contextMenu = contextMenu
        self.callback = callback
        self.objects = list(objects or [])
        self.items = list(objects or [])
        self.multiSelect = multiSelect
        self.dropSource = None
        self.sortOnDrop = sortOnDrop
        self.copyDrop = copyDrop
        if not self.copyDrop:
            self.setDefaultDropAction(QtCore.Qt.MoveAction)

        self.rightMouseCallback = rightMouseCallback
        if callback is not None:
            self.itemClicked.connect(callback)

        if self.multiSelect:
            self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        else:
            self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.contextMenuItem = 'Remove'
        self.currentContextMenu = self.getContextMenu

        # self.setStyleSheet(self._styleSheet)

    def contextCallback(self, remove=True):

        if remove:
            self.removeItem()
        self.rightMouseCallback()

    def setTexts(self, texts, clear=True):
        if clear:
            self.clear()
            self.cleared.emit()

            self.items = []
        for text in texts:
            item = QtWidgets.QListWidgetItem(str(text))
            self.addItem(item)

    def setObjects(self, objects, name='pid'):
        self.clear()
        self.cleared.emit()

        self.objects = list(objects)
        for obj in objects:
            if hasattr(obj, name):
                item = QtWidgets.QListWidgetItem(getattr(obj, name), self)
                item.setData(QtCore.Qt.UserRole, obj)
                obj.item = item
                self.addItem(item)
                self.items.append(item)

            else:
                item = QtWidgets.QListWidgetItem(str(obj))
                item.setData(QtCore.Qt.UserRole, obj)
                self.addItem(item)

    def getObjects(self):
        return list(self.objects)

    def _getDroppedObjects(self, project):
        '''This will return obj if the items text is a ccpn pid. This is used when the objects inside a listWidget are being dragged and dropped across widgets'''
        items = []
        objs = []

        for index in range(self.count()):
            items.append(self.item(index))
        for item in items:
            obj = project.getByPid(item.text())
            objs.append(obj)
        return objs

    def getSelectedObjects(self):
        indexes = self.selectedIndexes()
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
            # self.setItemSelected(item, False)
            item.setSelected(False)

    def getTexts(self):
        items = []
        for index in range(self.count()):
            items.append(self.item(index))
        return [i.text() for i in items]

    def selectObject(self, obj):
        try:
            obj.item.setSelected(True)
        except Exception as e:
            # Error wrapped C/C++ object of type QListWidgetItem has been deleted
            pass

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
            contextMenu.addItem("Remove", callback=self.removeItem)
            contextMenu.addItem("Remove All", callback=self._deleteAll)
        else:
            contextMenu.addItem("Remove", callback=self.contextCallback)
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
        contextMenu.addItem("Remove", callback=self.removeItem)
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
        self.cleared.emit()

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
            # self.emit(QtCore.SIGNAL("dropped"), links)
            self.dropped.emit(links)
            if self.sortOnDrop is True:
                self.sortItems()
        else:
            items = []
            if event.source() != self:  # otherwise duplicates

                if self.dropSource is None:  # allow event drops from anywhere
                    if self.copyDrop:
                        event.setDropAction(QtCore.Qt.CopyAction)
                    else:
                        event.setDropAction(QtCore.Qt.MoveAction)
                    # self.emit(QtCore.SIGNAL("dropped"), items)
                    self.dropped.emit(items)
                    super(ListWidget, self).dropEvent(event)
                    if self.sortOnDrop is True:
                        self.sortItems()
                else:

                    if event.source() is self.dropSource:  # check that the drop comes
                        event.setDropAction(QtCore.Qt.MoveAction)  # from only the permitted widget
                        # self.emit(QtCore.SIGNAL("dropped"), items)
                        self.dropped.emit(items)
                        super(ListWidget, self).dropEvent(event)
                        if self.sortOnDrop is True:
                            self.sortItems()
                    else:
                        event.accept()

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
            #   # self.emit(QtCore.SIGNAL("dropped"), items)
            #   self.dropped.emit(items)
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
    Define a pair of listWidgets such that information can be cpoied from one side
    to the other and vise-versa
    """

    def __init__(self, parent=None, objects=None, callback=None,
                 rightMouseCallback=None,
                 contextMenu=True,
                 multiSelect=True,
                 acceptDrops=False,
                 showMoveArrows=True,
                 showMoveText=False,
                 title='Copy Items', **kw):
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

        self.title = Label(self, text=title, setLayout=True, grid=(0, 0), gridSpan=(1, 7), hAlign='l')
        self.leftList = ListWidget(self, setLayout=True, grid=(1, 1), gridSpan=(5, 1), acceptDrops=True,
                                   sortOnDrop=True)
        self.rightList = ListWidget(self, setLayout=True, grid=(1, 5), gridSpan=(5, 1), acceptDrops=True,
                                    sortOnDrop=True)

        # set the drop source
        self.leftList.dropSource = self.rightList
        self.rightList.dropSource = self.leftList

        self.leftList.setSelectContextMenu()
        self.rightList.setSelectContextMenu()
        # self.rightList.setSelectDeleteContextMenu()

        self.leftList.itemDoubleClicked.connect(self._moveRight)
        self.rightList.itemDoubleClicked.connect(self._moveLeft)

        self.leftIcon = Icon('icons/yellow-arrow-left')
        self.rightIcon = Icon('icons/yellow-arrow-right')

        if showMoveArrows:
            moveText = ['', '']
            if showMoveText:
                moveText = ['move left', 'move right']

            self.buttons = ButtonList(self, texts=moveText,
                                      icons=[self.leftIcon, self.rightIcon],
                                      callbacks=[self._moveLeft, self._moveRight],
                                      direction='v',
                                      grid=(3, 3), hAlign='c')
            self.buttons.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            transparentStyle = "background-color: transparent; border: 0px solid transparent"
            self.buttons.setStyleSheet(transparentStyle)

        # self.button = Button(self, text='',
        #                           icon=self.rightIcon,
        #                           callback=self._copyRight,
        #                           grid=(3,3))
        # self.button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.spacer1 = Spacer(self, 5, 5,
                              QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                              grid=(0, 2), gridSpan=(1, 1))
        self.spacer2 = Spacer(self, 5, 5,
                              QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                              grid=(2, 2), gridSpan=(1, 1))
        self.spacer3 = Spacer(self, 5, 5,
                              QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                              grid=(4, 4), gridSpan=(1, 1))
        self.spacer4 = Spacer(self, 5, 5,
                              QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                              grid=(6, 4), gridSpan=(1, 1))

        for i, cs in enumerate([2, 8, 1, 1, 1, 8, 2]):
            self.getLayout().setColumnStretch(i, cs)

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
                item = QtWidgets.QListWidgetItem(str(item.pid))
                list.addItem(item)
        list.sortItems()

    def _moveLeft(self):  # not needed now
        """
        Move contents of the right window to the left window
        """
        for item in self.rightList.selectedItems():
            leftItem = QtWidgets.QListWidgetItem(item)
            self.leftList.addItem(leftItem)
            self.rightList.takeItem(self.rightList.row(item))
        self.leftList.sortItems()

    def _moveRight(self):  # not needed now
        """
        Move contents of the left window to the right window
        """
        for item in self.leftList.selectedItems():
            rightItem = QtWidgets.QListWidgetItem(item)
            self.rightList.addItem(rightItem)
            self.leftList.takeItem(self.leftList.row(item))
        self.rightList.sortItems()

    def _moveItemLeft(self):
        """
        Move contents of the right window to the left window
        """
        rightItem = QtWidgets.QListWidgetItem(self.rightList.selectedItems())
        self.leftList.addItem(rightItem)
        self.rightList.takeItem(self.rightList.row(rightItem))
        self.leftList.sortItems()

    def _moveItemRight(self):
        """
        Move contents of the left window to the right window
        """
        leftItem = QtWidgets.QListWidgetItem(self.leftList.selectedItem)
        self.rightList.addItem(leftItem)
        self.leftList.takeItem(self.leftList.row(leftItem))
        self.rightList.sortItems()

    def _copyRight(self):
        """
        Copy selection of the left window to the right window
        """
        for item in self.leftList.selectedItems():
            rightItem = QtWidgets.QListWidgetItem(item)
            self.rightList.addItem(rightItem)
        self.rightList.sortItems()

    def getLeftList(self):
        return self.leftList.getTexts()

    def getRightList(self):
        return self.rightList.getTexts()

        # RESIDUE                     ABBREVIATION                SYNONYM
        # -----------------------------------------------------------------------------
        # Alanine                     ALA                         A
        # Arginine                    ARG                         R
        # Asparagine                  ASN                         N
        # Aspartic acid               ASP                         D
        # ASP/ASN ambiguous           ASX                         B
        # Cysteine                    CYS                         C
        # Glutamine                   GLN                         Q
        # Glutamic acid               GLU                         E
        # GLU/GLN ambiguous           GLX                         Z
        # Glycine                     GLY                         G
        # Histidine                   HIS                         H
        # Isoleucine                  ILE                         I
        # Leucine                     LEU                         L
        # Lysine                      LYS                         K
        # Methionine                  MET                         M
        # Phenylalanine               PHE                         F
        # Proline                     PRO                         P
        # Serine                      SER                         S
        # Threonine                   THR                         T
        # Tryptophan                  TRP                         W
        # Tyrosine                    TYR                         Y
        # Unknown                     UNK
        # Valine                      VAL                         V


class ListWidgetSelector(Frame):
    """
    Define a pair of listWidgets such that information can be cpoied from one side
    to the other and vise-versa
    """
    residueTypes = [('Alanine', 'ALA', 'A'),
                    ('Arginine', 'ARG', 'R'),
                    ('Asparagine', 'ASN', 'N'),
                    ('Aspartic acid', 'ASP', 'D'),
                    ('ASP/ASN ambiguous', 'ASX', 'B'),
                    ('Cysteine', 'CYS', 'C'),
                    ('Glutamine', 'GLN', 'Q'),
                    ('Glutamic acid', 'GLU', 'E'),
                    ('GLU/GLN ambiguous', 'GLX', 'Z'),
                    ('Glycine', 'GLY', 'G'),
                    ('Histidine', 'HIS', 'H'),
                    ('Isoleucine', 'ILE', 'I'),
                    ('Leucine', 'LEU', 'L'),
                    ('Lysine', 'LYS', 'K'),
                    ('Methionine', 'MET', 'M'),
                    ('Phenylalanine', 'PHE', 'F'),
                    ('Proline', 'PRO', 'P'),
                    ('Serine', 'SER', 'S'),
                    ('Threonine', 'THR', 'T'),
                    ('Tryptophan', 'TRP', 'W'),
                    ('Tyrosine', 'TYR', 'Y'),
                    ('Unknown', 'UNK', ''),
                    ('Valine', 'VAL', 'V')]

    def __init__(self, parent=None, objects=None, callback=None,
                 rightMouseCallback=None,
                 contextMenu=True,
                 multiSelect=True,
                 acceptDrops=False,
                 title='Copy Items', **kw):
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

        self.title = Label(self, text=title, setLayout=True, grid=(0, 0), gridSpan=(1, 7), hAlign='l')
        self.leftList = ListWidget(self, setLayout=True, grid=(1, 1), gridSpan=(5, 1), acceptDrops=True,
                                   sortOnDrop=True)
        self.rightList = ListWidget(self, setLayout=True, grid=(1, 5), gridSpan=(5, 1), acceptDrops=True,
                                    sortOnDrop=True)

        # set the drop source
        self.leftList.dropSource = self.rightList
        self.rightList.dropSource = self.leftList

        self.leftList.setSelectContextMenu()
        self.rightList.setSelectContextMenu()
        # self.rightList.setSelectDeleteContextMenu()

        self.leftList.itemDoubleClicked.connect(self._moveRight)
        self.rightList.itemDoubleClicked.connect(self._moveLeft)

        # self.leftIcon = Icon('icons/yellow-arrow-left')
        # self.rightIcon = Icon('icons/yellow-arrow-right')
        #
        # self.buttons = ButtonList(self, texts=['move left', 'move right']
        #                          , icons=[self.leftIcon, self.rightIcon]
        #                          , callbacks=[self._moveLeft, self._moveRight]
        #                          , direction='v'
        #                          , grid=(3,3), hAlign='c')
        # self.buttons.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # transparentStyle = "background-color: transparent; border: 0px solid transparent"
        # self.buttons.setStyleSheet(transparentStyle)

        # self.button = Button(self, text=''
        #                          , icon=self.rightIcon
        #                          , callback=self._copyRight
        #                          , grid=(3,3))
        # self.button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.spacer1 = Spacer(self, 5, 5,
                              QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                              grid=(0, 2), gridSpan=(1, 1))
        self.spacer2 = Spacer(self, 10, 10,
                              QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                              grid=(2, 2), gridSpan=(1, 1))
        self.spacer3 = Spacer(self, 10, 10,
                              QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                              grid=(4, 4), gridSpan=(1, 1))
        self.spacer4 = Spacer(self, 5, 5,
                              QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                              grid=(6, 4), gridSpan=(1, 1))

        for i, cs in enumerate([2, 6, 1, 1, 1, 6, 2]):
            self.getLayout().setColumnStretch(i, cs)

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
                item = QtWidgets.QListWidgetItem(str(item.pid))
                list.addItem(item)
        list.sortItems()

    def _moveLeft(self):  # not needed now
        """
        Move contents of the right window to the left window
        """
        for item in self.rightList.selectedItems():
            leftItem = QtWidgets.QListWidgetItem(item)
            self.leftList.addItem(leftItem)
            self.rightList.takeItem(self.rightList.row(item))
        self.leftList.sortItems()

    def _moveRight(self):  # not needed now
        """
        Move contents of the left window to the right window
        """
        for item in self.leftList.selectedItems():
            rightItem = QtWidgets.QListWidgetItem(item)
            self.rightList.addItem(rightItem)
            self.leftList.takeItem(self.leftList.row(item))
        self.rightList.sortItems()

    def _moveItemLeft(self):
        """
        Move contents of the right window to the left window
        """
        rightItem = QtWidgets.QListWidgetItem(self.rightList.selectedItems())
        self.leftList.addItem(rightItem)
        self.rightList.takeItem(self.rightList.row(rightItem))
        self.leftList.sortItems()

    def _moveItemRight(self):
        """
        Move contents of the left window to the right window
        """
        leftItem = QtWidgets.QListWidgetItem(self.leftList.selectedItem)
        self.rightList.addItem(leftItem)
        self.leftList.takeItem(self.leftList.row(leftItem))
        self.rightList.sortItems()

    def _copyRight(self):
        """
        Copy selection of the left window to the right window
        """
        for item in self.leftList.selectedItems():
            rightItem = QtWidgets.QListWidgetItem(item)
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
