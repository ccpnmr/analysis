"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-04 17:58:16 +0100 (Fri, June 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from re import finditer
from collections import Counter, OrderedDict
from itertools import zip_longest
import copy
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDataStream, Qt, QVariant
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonBoxList
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Font import getTextDimensionsFromFont
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
from ccpn.ui.gui.lib.ChangeStateHandler import changeState
from ccpn.util.Constants import INTERNALQTDATA
from ccpn.ui.gui.guiSettings import getColours, BORDERFOCUS, BORDERNOFOCUS
import traceback

DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 10, 1)  # l, t, r, b
ZEROMARGINS = (0, 0, 0, 0)  # l, t, r, b


def camelCaseSplit(identifier):
    matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return ' '.join([m.group(0) for m in matches])


class FeedbackFrame(Frame):
    def __init__(self, *args, **kwds):
        super().__init__(setLayout=True, *args, **kwds)
        self.highlight(False)

    def highlight(self, enable):

        if enable:
            # GST rgb(88,88,192) is 'ccpn purple' which I guess should be defined somewhere
            self.setStyleSheet('FeedbackFrame {border: 2px solid rgb(88,88,192)}')
        else:
            # this is background grey which I guess should be defined somewhere
            self.setStyleSheet('FeedbackFrame {border: 2px solid transparent}')


class OrderedListWidgetItem(QtWidgets.QListWidgetItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __lt__(self, other):
        self_data = self.data(_ListWidget._searchRoleIndex)
        other_data = other.data(_ListWidget._searchRoleIndex)
        if not all([self_data, other_data]):
            return False
        return self_data < other_data


class DefaultItemFactory:

    def __init__(self, roleMap=None):

        self._roleMap = {}

        if roleMap is not None:
            for role in roleMap.values():
                if role == QtCore.Qt.UserRole:
                    raise Exception('role QtCore.Qt.UserRole is reserved for ccpn use a value > QtCore.Qt.UserRole ')

            self._roleMap.update(roleMap)

        self._roleMap['USER_ROLE'] = QtCore.Qt.UserRole

    def instantiateItem(self, item, parent):

        if not isinstance(item, QtWidgets.QListWidgetItem):
            result = QtWidgets.QListWidgetItem(item, parent)
        else:
            result = None

        return result

    def ensureItem(self, item, parent=None):

        result = self.instantiateItem(item, parent)

        if result is None:
            result = item

            if parent is not None:
                result.setParent(parent)

        return result

    # GST from https://wiki.python.org/moin/PyQt/Handling%20Qt%27s%20internal%20item%20MIME%20type
    # note the original has a bug! the items {} is declared too high and is aliased, this only appears
    # when multiple items are dragged
    def decodeDragData(self, bytearray):

        data = OrderedDict()

        ds = QDataStream(bytearray)
        while not ds.atEnd():
            item = {}
            row = ds.readInt32()
            column = ds.readInt32()
            key = (row, column)

            data[key] = item
            map_items = ds.readInt32()
            for i in range(map_items):
                key = ds.readInt32()

                value = QVariant()
                ds >> value
                item[Qt.ItemDataRole(key)] = value

        return data

    def createItemsFromMimeData(self, data):
        data = self.decodeDragData(data)

        result = []
        for i, item in enumerate(data.values()):
            string = item[0].value()
            del item[0]
            result.append(self.createItem(string, data=item))

        return result

    def createItem(self, string, data=[], parent=None):
        result = self.ensureItem(string, parent=parent)
        for role, value in data.items():
            result.setData(role, value)

        return result


class OrderedListWidgetItemFactory(DefaultItemFactory):

    def __init__(self):
        super().__init__({_ListWidget._searchRole: _ListWidget._searchRoleIndex})

    def instantiateItem(self, item, parent):

        if not isinstance(item, OrderedListWidgetItem):
            result = OrderedListWidgetItem(item, parent)
        else:
            result = None

        return result


class _ListWidget(ListWidget):
    """Subclassed for dropEvent"""

    _roles = ('Left', 'Right')

    _searchRole = 'SEARCH'
    _searchRoleIndex = QtCore.Qt.UserRole + 1

    def __init__(self, *args, dragRole=None, feedbackWidget=None, rearrangeable=False, itemFactory=None,
                 sorted=False, emptyText=None, **kwds):

        super().__init__(*args, **kwds)

        if dragRole.capitalize() not in self._roles:
            raise Exception('position must be one of left or right')

        self._rearrangeable = rearrangeable
        self.setDropIndicatorShown(self._rearrangeable)

        self._dragRole = dragRole
        clonedRoles = list(self._roles)
        clonedRoles.remove(self._dragRole.capitalize())
        self._oppositeRole = clonedRoles[0]

        self._emptyText = emptyText

        self._feedbackWidget = feedbackWidget
        self._partner = None

        self.itemDoubleClicked.connect(self._itemDoubleClickedCallback)

        self._setFocusColour()

        self.setSortingEnabled(sorted)

        self._itemFactory = itemFactory
        if self._itemFactory is None:
            self._itemFactory = DefaultItemFactory()

        self._feedbackWidget.highlight(False)

    def _setFocusColour(self, focusColour=None, noFocusColour=None):
        """Set the focus/noFocus colours for the widget
        """
        focusColour = getColours()[BORDERFOCUS]
        noFocusColour = getColours()[BORDERNOFOCUS]
        styleSheet = "ListWidget { " \
                     "border: 1px solid;" \
                     "border-radius: 1px;" \
                     "border-color: %s;" \
                     "} " \
                     "ListWidget:focus { " \
                     "border: 1px solid %s; " \
                     "border-radius: 1px; " \
                     "}" % (noFocusColour, focusColour)
        self.setStyleSheet(styleSheet)

    def startDrag(self, *args, **kwargs):
        super().startDrag(*args, **kwargs)

    def setTexts(self, texts, clear=True, data=[]):

        if clear:
            self.clear()
            self.cleared.emit()

        if len(texts) < len(data):
            raise Exception('more data than items!')


        self.insertItems(0, texts) #this avoids the notification leakage of adding one at the time

        # for text, datum in zip_longest(texts, data, fillvalue={}):
        #     item = self._itemFactory.createItem(str(text), datum)
        #     self.addItem(item)

    def _buildItemData(self, objects, data):

        data = copy.deepcopy(data)
        for i, object in enumerate(objects):

            if i < len(data):
                data[i]['USER_ROLE'] = id(object)
            else:
                data.append({'USER_ROLE': id(object)})

        return data

    def setObjects(self, objects, name='pid', data=[]):
        self.clear()
        self.cleared.emit()

        self.objects = {id(obj): obj for obj in objects}  # list(objects)

        if len(objects) < len(data):
            raise Exception('more data than items!')

        data = self._buildItemData(objects, data)
        for obj, datum in zip_longest(objects, data, fillvalue={}):
            if hasattr(obj, name):
                item = self._itemFactory.createItem(getattr(obj, name), data=datum, parent=self)
                # GST why does each object need to have an item associated with it?
                # this associates data with 'model items' which 'isn't good'
                obj.item = item
                self.addItem(item)
                self._items.append(item)

            else:
                item = self._itemFactory.createItem(str(obj), data=datum, parent=self)
                self.addItem(item)

    def setPartner(self, partner):
        self._partner = partner

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            self.paintEmpty(event)

    def paintEmpty(self, event):

        p = QtGui.QPainter(self.viewport())
        pen = QtGui.QPen(QtGui.QColor("grey"))
        oldPen = p.pen()
        p.setPen(pen)
        p.drawText(self.rect(), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, " " + self._emptyText)
        p.setPen(oldPen)
        p.end()

    def _isAcceptableDrag(self, event):
        data = self.parseEvent(event)
        result = False

        if 'source' in data and data['source'] is not None:
            source = data['source']
            okEvent = 'GroupEditorPopupABC' in str(data['source'])
            okSide = False
            if self._rearrangeable and source == self:
                okSide = True
            elif source == self._partner:
                okSide = True

            result = okEvent and okSide
        return result

    def dragEnterEvent(self, event):
        if self._isAcceptableDrag(event):
            event.accept()
            if self._feedbackWidget:
                self._feedbackWidget.highlight(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        event.accept()
        self._dragReset()

    def dropMimeData(self, index, data, action):

        mimeData = data.data(INTERNALQTDATA)
        _data = self._itemFactory.decodeDragData(mimeData)
        strings = [item[0].value() for item in _data.values()]
        self.insertItems(index, strings) #multi insert item or nofications leakage
        return True

    def dropEvent(self, event):

        if self._isAcceptableDrag(event):

            data = self.parseEvent(event)
            if self._rearrangeable and data['source'] == self:
                QtWidgets.QListWidget.dropEvent(self, event)
            else:
                data = self.parseEvent(event)
                super().dropEvent(event=event)

            self._dragReset()
        else:
            event.ignore()

    def _dragReset(self):
        if self._feedbackWidget:
            self._feedbackWidget.highlight(False)

    def getContextMenu(self):

        # FIXME this context menu must be more generic and editable
        contextMenu = Menu('', self, isFloatWidget=True)

        enabled = self._itemsAvailable()
        enabledAll = True
        if self.count() == 0:
            enabledAll = False

        # Context temporarly disabled. Need to fix the signal block or risk of a massive signal-leakage
        # contextMenu.addItem("Move %s" % self._oppositeRole, callback=self.move, enabled=enabled)
        # contextMenu.addItem("Move All %s" % self._oppositeRole, callback=self.moveAll, enabled=enabledAll)

        return contextMenu

    def _itemsAvailable(self):
        result = False
        count = self.count()
        if count > 0 and self._partner is not None:
            selected = self.selectedItems()
            if len(selected) > 0:
                result = True
            else:
                item = self.itemAt(self._currentMousePos)
                if item:
                    result = True
        return result

    def move(self):
        # this needs to be handled with a context manager to disable the signals leakage
        count = self.count()
        if count > 0 and self._partner is not None:
            rows = []
            selected = self.selectedItems()
            if len(selected) > 0:
                for item in selected:
                    rows.append(self.row(item))
                for i in reversed(sorted(rows)):
                    item = self.takeItem(i)
                    self._partner.addItem(item)
            else:
                item = self.itemAt(self._currentMousePos)
                if item:
                    row = self.row(item)
                    self.takeItem(row)
                    self._partner.addItem(item)

    def moveAll(self):
        # this needs to be handled with a context manager to disable the signals leakage
        count = self.count()
        if count > 0 and self._partner is not None:
            for i in reversed(range(count)):
                item = self.takeItem(i)
                self._partner.addItem(item)

    def mousePressEvent(self, event):
        self._currentMousePos = event.pos()
        super().mousePressEvent(event)

    def _itemDoubleClickedCallback(self, item):
        if self._partner is not None:
            row = self.row(item)
            taken = self.takeItem(row)
            self._partner.addItem(item)


class _GroupEditorPopupABC(CcpnDialogMainWidget):
    """
    An abstract base class to create and manage popups for _class
    """
    # These need sub-classing
    _class = None  # e.g. SpectrumGroup
    _classItemAttribute = None  # e.g. 'spectra' # Attribute in _class containing items
    _classPulldown = None  # SpectrumGroupPulldown

    _projectNewMethod = None  # e.g. 'newSpectrumGroup'  # Method of Project to create new _class instance
    _projectItemAttribute = None  # e.g. 'spectra'  # Attribute of Project containing items
    _groupEditorInitMethod = None

    _buttonFilter = 'Filter by:'
    _buttonCancel = 'Cancel'
    _setRevertButton = True

    _useTab = None
    _numberTabs = 0

    FIXEDWIDTH = False
    FIXEDHEIGHT = False
    _FIXEDWIDTH = 120

    # leftListChanged = pyqtSignal(tuple)
    # rightListChanged = pyqtSignal(tuple)

    def __init__(self, parent=None, mainWindow=None, editMode=True, obj=None, defaultItems=None, size=(600, 350), **kwds):
        """
        Initialise the widget, note defaultItems is only used for create
        """

        self._groupName = camelCaseSplit(self._class.className)

        title = 'Edit ' + self._groupName if editMode else 'New ' + self._groupName

        self._leftEmptyText = 'Drag or double click %s to add here' % self._projectItemAttribute
        self._rightEmptyText = "No %s: try 'Filter by' settings" % self._projectItemAttribute

        self._acceptButtonText = 'Save changes to %s' % self._pluralGroupName

        super().__init__(parent=parent, windowTitle=title, setLayout=True, margins=(0, 0, 0, 0),
                         spacing=(5, 5), size=size, **kwds)

        self.errorIcon = Icon('icons/exclamation_small')

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.obj = obj
        self.editMode = editMode
        self._modelsConnected = False

        # open popup with these items already added to left ListWidget. Ready to create the group.
        # assumes that defaultItems is a list of core objects (with pid)
        self.defaultItems = [itm.pid for itm in defaultItems] if defaultItems else None

        if self._useTab is None:
            # define the destination for the widgets - Dialog has mainWidget, will change for tabbed widgets
            self._dialogWidget = self.mainWidget
        else:
            # hPolicy='expanding' gives weird results
            self._tabWidget = Tabs(self.mainWidget, grid=(0, 0))

            # define the new tab widget
            self._tabWidget.setContentsMargins(*ZEROMARGINS)
            for tabNum in range(self._numberTabs):
                fr = ScrollableFrame(self.mainWidget, setLayout=True, spacing=DEFAULTSPACING,
                                     scrollBarPolicies=('asNeeded', 'asNeeded'), margins=TABMARGINS)
                self._tabWidget.addTab(fr.scrollArea, str(tabNum))

            if isinstance(self._useTab, int) and self._useTab < self._tabWidget.count():
                self._dialogWidget = (self._tabWidget.widget(self._useTab))._scrollContents
            else:
                raise RuntimeError('self._tabWidget: invalid _useTab setting')

        self._setLeftWidgets()
        self._setRightWidgets()

        # enable the buttons
        self.setOkButton(callback=self._applyAndClose, text=self._acceptButtonText, tipText='Apply according to current settings and close')
        self.setCancelButton(callback=self._cancel, text=self._buttonCancel, tipText='Cancel the New/Edit operation')
        self.setRevertButton(callback=self._revertClicked, enabled=False)

        self.setDefaultButton(CcpnDialogMainWidget.OKBUTTON)

        self.__postInit__()
        self._applyButton = self.getButton(self.OKBUTTON)
        self._cancelButton = self.getButton(self.CANCELBUTTON)
        self._revertButton = self.getButton(self.RESETBUTTON)

        # self._setApplyButtons()
        # self._addWidgetsToLayout()
        self._connectLists()
        self._populateLists()

        self._applyButton.setEnabled(False)
        self._revertButton.setEnabled(False)

        # # one cannot be a copy of the other unless its a deep copy...
        # # this is easier
        # self._previousState = self._getPreviousState()
        # self._updatedState = copy.deepcopy(self._getPreviousState())
        #
        # self._previousNames = {key: key for key in self._previousState}
        # self._updatedNames = dict(self._previousNames)
        #
        # self.connectModels()
        # self._updateStateOnSelection()
        # self.setMinimumSize(self.sizeHint())
        # self.resize(500, 350)  # change to a calculation rather than a guess

    def _populateLists(self):
        # one cannot be a copy of the other unless its a deep copy...
        # this is easier
        self._previousState = self._getPreviousState()
        self._updatedState = copy.deepcopy(self._previousState)

        self._previousNames = {key: key for key in self._previousState}
        self._updatedNames = dict(self._previousNames)

        self._connectModels()
        self._updateStateOnSelection()

    def _populate(self):
        self._populateLists()

    def _getChangeState(self):
        """Get the change state from the _changes dict
        """
        # changes not required here, just need to define which buttons to disable after revert
        return changeState(self, False, False, False, None, self._applyButton, self._revertButton, 0)

    def _getPreviousState(self):
        result = {}
        beforeKeys = self.project._pid2Obj.get(self._groupPidKey)
        if beforeKeys is not None:
            for key in beforeKeys:
                #GST do I need to filter object in an undo state, if so could we add some interface for this...
                object = self.project._pid2Obj.get(self._groupPidKey)[key]
                items = [elem.pid for elem in getattr(object, self._projectItemAttribute)]
                comment = object.comment or None
                result[key] = {'spectra': items,
                               'comment': comment}
        return result

    def _setLeftWidgets(self):

        # self.leftTopLabel = Label(self._dialogWidget, '', bold=True, grid=(0, 0), gridSpan=(1, 3))

        if not self.editMode:
            labelName = 'New %s Name' % self._groupName
        else:
            labelName = 'Name'

        optionTexts = [labelName, 'Comment', self._groupName, 'Selection']
        _, maxDim = getTextDimensionsFromFont(textList=optionTexts)
        self._FIXEDWIDTH = maxDim.width()

        row = 1
        self.nameLabel = Label(self._dialogWidget, labelName, grid=(row, 0))
        self._nameEditFrame = Frame(self._dialogWidget, setLayout=True, showBorder=False, grid=(row, 1), gridSpan=(1, 2))
        self.nameEdit = LineEdit(self._nameEditFrame, backgroundText='%s Name' % self._groupName, hAlign='l', textAlignment='left', grid=(row, 1))

        row += 1
        self.commentLabel = Label(self._dialogWidget, 'Comment', grid=(row, 0))
        self.commentEdit = LineEdit(self._dialogWidget, backgroundText='> Optional <', textAlignment='left', grid=(row, 1), gridSpan=(1, 2))

        # GST need something better than this..!
        # self.nameEdit.setFixedWidth(self._FIXEDWIDTH * 1.5)
        self.nameEdit.setFixedWidth(self._FIXEDWIDTH * 2)
        # self.nameEdit.setVisible(True)

        row += 1
        if self.editMode:
            self._leftPullDownLabel = Frame(self._dialogWidget, setLayout=True, showBorder=False, grid=(row, 1), gridSpan=(1, 2))
            self.leftPullDownLabel = Label(self._dialogWidget, self._groupName, grid=(row, 0))

            self.leftPullDown = self._classPulldown(parent=self._leftPullDownLabel,
                                                    mainWindow=self.mainWindow,
                                                    showSelectName=False,
                                                    default=self.obj,
                                                    callback=self._leftPullDownCallback,
                                                    fixedWidths=[0, None],
                                                    hAlign='l', grid=(row, 1),
                                                    )
            self.leftPullDown.setEnabled(False) ## Editing of different SG from the same popup is disabled.
            ## It is confusing and error-prone in notifying changes to the other tabs.
        row += 2
        self.selectionLabel = Label(self._dialogWidget, self._classItemAttribute.capitalize(), grid=(row, 0))
        self.leftItemsLabel = Label(self._dialogWidget, 'Not Included', grid=(row, 1))

        row += 1
        self.leftListFeedbackWidget = FeedbackFrame(self._dialogWidget, grid=(row, 2))
        self.leftListWidget = _ListWidget(self.leftListFeedbackWidget, feedbackWidget=self.leftListFeedbackWidget,
                                          grid=(0, 0), dragRole='right', acceptDrops=True, sortOnDrop=False, copyDrop=False,
                                          emptyText=self._leftEmptyText, rearrangeable=True, itemFactory=OrderedListWidgetItemFactory())

        self.leftListFeedbackWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        # self.leftListWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

    def _connectModels(self):
        if not self._modelsConnected:
            self.nameEdit.textChanged.connect(self._updateNameOnEdit)
            self.commentEdit.textChanged.connect(self._updateCommentOnEdit)
            self.leftListWidget.model().dataChanged.connect(self._updateModelsOnEdit)
            self.leftListWidget.model().rowsRemoved.connect(self._updateModelsOnEdit)
            self.leftListWidget.model().rowsInserted.connect(self._updateModelsOnEdit)
            self.leftListWidget.model().rowsMoved.connect(self._updateModelsOnEdit)
            self._modelsConnected = True

    def _disconnectModels(self):
        if self._modelsConnected:
            self.nameEdit.textChanged.disconnect(self._updateNameOnEdit)
            self.commentEdit.textChanged.disconnect(self._updateCommentOnEdit)
            self.leftListWidget.model().dataChanged.disconnect(self._updateModelsOnEdit)
            self.leftListWidget.model().rowsRemoved.disconnect(self._updateModelsOnEdit)
            self.leftListWidget.model().rowsInserted.disconnect(self._updateModelsOnEdit)
            self.leftListWidget.model().rowsMoved.disconnect(self._updateModelsOnEdit)
            self._modelsConnected = False

    def _setRightWidgets(self):

        row = 4
        self.addSpacer(0, 5, grid=(row, 0), gridSpan=(1, 3), parent=self._dialogWidget)

        row += 1
        self.rightItemsLabel = Label(self._dialogWidget, 'Included', grid=(row, 2))

        row += 1
        self.rightListFeedbackWidget = FeedbackFrame(self._dialogWidget, grid=(row, 1))
        self.rightListWidget = _ListWidget(self.rightListFeedbackWidget, feedbackWidget=self.rightListFeedbackWidget,
                                           grid=(0, 0), dragRole='left', acceptDrops=True, sortOnDrop=False, copyDrop=False,
                                           emptyText=self._rightEmptyText, sorted=True, itemFactory=OrderedListWidgetItemFactory())

        self.rightListFeedbackWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        # self.rightListWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

        # small frame for holding the pulldown list
        row += 1
        self.rightListFilterFrame = Frame(self._dialogWidget, setLayout=True, showBorder=False, grid=(row, 1), gridSpan=(1, 2))
        self.rightFilterLabel = Label(self.rightListFilterFrame, self._buttonFilter, hAlign='l', grid=(0, 0))
        self.rightPullDown = self._classPulldown(parent=self.rightListFilterFrame,
                                                 mainWindow=self.mainWindow,
                                                 showSelectName=True,
                                                 selectNoneText='none',
                                                 callback=self._rightPullDownCallback,
                                                 fixedWidths=[0, None],
                                                 filterFunction=self._rightPullDownFilter,
                                                 hAlign='l', grid=(0, 1)
                                                 )
        self.rightListFilterFrame.getLayout().setColumnStretch(2, 1)

        row += 1
        self.addSpacer(0, 5, grid=(row, 0), gridSpan=(1, 3), parent=self._dialogWidget)

        row += 1
        self.errorFrame = Frame(self._dialogWidget, setLayout=True, grid=(row, 1), gridSpan=(1, 2))

        row += 1
        self.addSpacer(0, 10, grid=(row, 0), gridSpan=(1, 3), parent=self._dialogWidget)

        # self.rightListWidget.setFixedWidth(2*self.FIXEDWIDTH)

    def _rightPullDownFilter(self, pids):
        if self._editedObject and self._editedObject.pid in pids:
            pids.remove(self._editedObject.pid)
        return pids

    def _connectLists(self):
        self.leftListWidget.setPartner(self.rightListWidget)
        self.rightListWidget.setPartner(self.leftListWidget)

    @property
    def _editedObject(self):
        "Convenience to get the edited object"
        result = None
        if self.editMode:
            result = self.leftPullDown.getSelectedObject()
        return result

    @property
    def _groupedObjects(self) -> list:
        result = self.leftListWidget.getTexts()
        if self._leftEmptyText in result:
            result.remove(self._leftEmptyText)
        return result

    @_groupedObjects.setter
    def _groupedObjects(self, vv):
        self.leftListWidget.setTexts(vv)

    @property
    def _editedObjectItems(self) -> list:
        """Convenience to get the list of items we are editing for object (e.g. spectra for SpectrumGroup)
        Returns list or None on error
        """
        obj = self._editedObject
        if obj is None:
            return None
        state = self._updatedState[obj.name]
        return state.get('spectra')

    @property
    def _projectObjectItems(self) -> list:
        """Convenience to get the list from project of items we are editing for object (e.g. spectra
        in case of SpectrumGroup)
        Returns list or None on error
        """
        if not hasattr(self.project, self._projectItemAttribute):
            return None
        return getattr(self.project, self._projectItemAttribute)

    @property
    def _editedObjectComment(self) -> str:
        """Convenience to get the comment
        Returns list or None on error
        """
        obj = self._editedObject
        if obj is None:
            return None
        state = self._updatedState[obj.name]
        return state.get('comment')

    def _setAcceptButtonState(self):
        if self.editMode and self._dirty:
            # self.applyButtons.setButtonEnabled(self._acceptButtonText, True)
            self._applyButton.setEnabled(True)

    def _currentEditorState(self):
        result = {}
        if self.editMode and self._editedObject:
            key = self._editedObject.name
            items = self._groupedObjects
            comment = self.commentEdit.text() or None
        else:
            key = self.nameEdit.text()
            items = self._groupedObjects
            comment = self.commentEdit.text() or None
        if len(key) > 0:
            result = {key: {'spectra': items,
                            'comment': comment}
                      }

        return result

    def _updateNameOnEdit(self):
        if self.editMode and self._editedObject is not None:
            editedObjectName = self._editedObject.name
            newName = self.nameEdit.text()
            self._updatedNames[editedObjectName] = newName

        self._updateButton()

    def _updateModelsOnEdit(self, *args, **kwargs):

        currentEdits = self._currentEditorState()

        if self.editMode and self._editedObject is not None:
            for id, selections in currentEdits.items():
                self._updatedState[id] = selections

            editedObjectName = self._editedObject.name
            newName = self.nameEdit.text()
            self._updatedNames[editedObjectName] = newName

        self._updateButton()

    def _updateCommentOnEdit(self, *args, **kwargs):

        currentEdits = self._currentEditorState()

        if self.editMode and self._editedObject is not None:
            for id, selections in currentEdits.items():
                self._updatedState[id] = selections

        self._updateButton()

    def _checkForTrailingSpacesOnGroupName(self):
        result = False
        resultString = ''
        badNames = []
        for name in self._updatedState.keys():
            if len(name.strip()) != 0:
                if len(name.strip()) != len(name):
                    result = True
                    badNames.append(name.strip())

        if result:
            joinedNames = ', '.join(badNames)
            resultString = 'Some %s have names with leading or trailing spaces %s' % (self._pluralGroupName, joinedNames)

        return result, resultString

    def _checkForEmptyNames(self):
        result = False
        badKeys = []
        for name in self._updatedState.keys():
            if len(name.strip()) == 0:
                raise Exception('unexpected')
                # result  = True

        for key, name in self._updatedNames.items():
            if len(name.strip()) == 0:
                badKeys.append(key)
                result = True

        resultString = ''
        if result:
            badKeys.sort()
            resultString = 'Some %s have an empty name (original names: %s)' % (self._pluralGroupName, ','.join(badKeys))

        return result, resultString

    def _checkForDuplicatetNames(self):
        nameCount = Counter(self._updatedNames.values())
        duplicateNameCounts = list(filter(lambda i: i[1] > 1, nameCount.items()))
        result = len(duplicateNameCounts) > 0

        resultString = ''
        if result:
            duplicateNames = [item[0] for item in duplicateNameCounts]
            duplicateNameString = ','.join(duplicateNames)
            resultString = 'Duplicate Names: %s' % duplicateNameString

        return result, resultString

    # def _checkForEmptyGroups(self):
    #
    #     badKeys = []
    #     for key, selection in self._updatedState.items():
    #         values = selection.get('spectra')
    #         values = self.filterEmptyText(values)
    #         if len(values) == 0:
    #             badKeys.append(key)
    #
    #     result = False
    #     resultString = ''
    #     if len(badKeys) > 0:
    #         result = True
    #         resultString = 'Empty %s: %s' % (self._pluralGroupName, ','.join(badKeys))
    #
    #     return result, resultString

    def _checkForTrailingSpacesName(self):

        result = False
        badKeys = []
        for key, name in self._updatedNames.items():
            if len(name.strip()) != len(name):
                badKeys.append(key)
                result = True

        msg = 'Some %s names have leading or tailings spaces\n (original names are: %s)'
        resultString = msg % (self._pluralGroupName, ','.join(badKeys))

        return result, resultString

    def _checkForExistingName(self):
        currentEdits = self._currentEditorState()
        result = False
        resultString = ''

        if currentEdits != {}:
            name = list(currentEdits.keys())[0]
            if name in self._previousState.keys():
                result = True

                # GST when i used 'The Spectrum Group %s already exists' % name igot an odd effect
                # the space and a in already were deleted...
                resultString = 'The ' + self._singularGroupName + ' ' + name + ' already exists'

        return result, resultString

    def filterEmptyText(self, items):
        if self._leftEmptyText in items:
            items.remove(self._leftEmptyText)
        return items

    def _checkForNoName_New(self):
        result = False
        resultString = ''

        noNameString = 'Name not set'

        currentEdits = self._currentEditorState()
        if currentEdits == {}:
            result = True
            resultString = noNameString
        else:
            name = list(currentEdits.keys())[0]
            if len(name.strip()) == 0:
                result = True
                resultString = noNameString

        return result, resultString

    def _checkForTrailingSpaceOnName_New(self):
        result = False
        resultString = ''

        spacesString = 'The %s name has leading or trailing spaces' % self._pluralGroupName

        currentEdits = self._currentEditorState()
        if currentEdits != {}:
            name = list(currentEdits.keys())[0]
            if len(name.strip()) != len(name):
                result = True
                resultString = spacesString

        return result, resultString

    # def _checkForEmptyGroup_New(self):
    #     result = False
    #     resultString = ''
    #
    #     if len(self._groupedObjects) == 0:
    #         result = True
    #         resultString = 'The %s is empty' % self._singularGroupName
    #
    #     return result, resultString

    def _updateButton(self):

        self.errors = []

        if not self.editMode:

            enabled = True

            check, message = self._checkForNoName_New()
            if check:
                enabled = False
                self.errors.append(message)

            # check, message = self._checkForEmptyGroup_New()
            # if check:
            #     enabled = False
            #     self.errors.append(message)

            check, message = self._checkForTrailingSpaceOnName_New()
            if check:
                enabled = False
                self.errors.append(message)

            check, message = self._checkForExistingName()
            if check:
                enabled = False
                self.errors.append(message)

        elif self.editMode:

            enabled = False

            if self._updatedState != self._previousState:
                enabled = True

            if self._updatedNames != self._previousNames:
                enabled = True

            check, message = self._checkForEmptyNames()
            if check:
                enabled = False
                self.errors.append(message)

            check, message = self._checkForDuplicatetNames()
            if check:
                enabled = False
                self.errors.append(message)

            # check, message = self._checkForEmptyGroups()
            # if check:
            #     enabled = False
            #     self.errors.append(message)

            check, message = self._checkForTrailingSpacesName()
            if check:
                enabled = False
                self.errors.append(message)

        # self.applyButtons.setButtonEnabled(self._acceptButtonText, enabled)
        self._applyButton.setEnabled(enabled)

        if self._setRevertButton:
            self._revertButton.setEnabled(True)

        self._emptyErrorFrame()

        if len(self.errors) != 0:
            self.errorFrame.layout().setColumnStretch(0, 0)
            self.errorFrame.layout().setColumnStretch(1, 1000)
            for i, error in enumerate(self.errors):
                label = Label(self.errorFrame, error)
                iconLabel = Label(self.errorFrame)
                iconLabel.setPixmap(self.errorIcon.pixmap(16, 16))
                self.errorFrame.layout().addWidget(label, i, 1)
                self.errorFrame.layout().setAlignment(label, QtCore.Qt.AlignLeft)
                self.errorFrame.layout().addWidget(iconLabel, i, 0)
                self.errorFrame.layout().setAlignment(iconLabel, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

    def _emptyErrorFrame(self):
        for child in self.errorFrame.findChildren(QtWidgets.QWidget):
            self.errorFrame.getLayout().removeWidget(child)
            child.setParent(None)
            child.hide()
            del child

    def _updateStateOnSelection(self):
        """Update state
        """

        # Note well model updates must be off while the selected
        # group to edit is being changed else the changes applied
        # will trigger model changes

        self._disconnectModels()
        self._updateLeft()
        self._updateRight()
        self._updateButton()
        self.rightPullDown._updatePulldownList()
        if len(self.rightPullDown.getObjects()) < 2:
            self.rightPullDown.setEnabled(False)
        else:
            self.rightPullDown.setEnabled(True)
        self._connectModels()

    def _getItemPositions(self, items):

        result = []

        orderedPids = [elem.pid for elem in getattr(self.project, self._projectItemAttribute)]
        for item in items:
            result.append({_ListWidget._searchRoleIndex: orderedPids.index(item)})

        return result

    def _updateLeft(self):
        """Update Left
        """

        # block widget signals to stop feedback loops
        with self.blockWidgetSignals(recursive=False):
            if self.editMode:

                self.leftPullDownLabel.show()
                self.leftPullDown.show()
                self.rightPullDown.setEnabled(len(self.leftPullDown.getObjects()) > 0)
                obj = self._editedObject
                if obj is not None:
                    name = self._updatedNames[obj.name]
                    self.nameEdit.setText(name)
                    self.commentEdit.setText(self._editedObjectComment)
                    self._setLeftListWidgetItems(self._editedObjectItems)
                    self.nameEdit.setEnabled(True)
                    self.leftListWidget.setEnabled(True)
                    self.rightListWidget.setEnabled(True)
                else:
                    self.nameEdit.setText('')
                    self.commentEdit.setText('')
                    self.leftListWidget.clear()
                    self.nameEdit.setEnabled(False)
                    self.leftListWidget.setEnabled(False)
                    self.rightListWidget.setEnabled(False)

            else:
                self.leftListWidget.clear()
                if self.defaultItems is not None:
                    self._setLeftListWidgetItems(self.defaultItems)
                self.nameEdit.setText('')
                self.commentEdit.setText('')

    def _updateRight(self):
        """Update Right
        """
        if self.rightPullDown.getSelectedObject() is None:
            self._setRightListWidgetItems(self._projectObjectItems)
        else:
            self.rightListWidget.clear()
            group = self.rightPullDown.getSelectedObject()
            if group is not None:
                self._setRightListWidgetItems(getattr(group, self._projectItemAttribute))

    def _setLeftListWidgetItems(self, pids: list):
        """Convenience to set the items in the left ListWidget
        """
        # convert items to pid's
        data = self._getItemPositions(pids)
        self.leftListWidget.setTexts(pids, clear=True, data=data)

    def _setRightListWidgetItems(self, items: list):
        """Convenience to set the items in the right ListWidget
        """
        # convert items to pid's
        pids = [s.pid for s in items]
        # filter for those pid's already on the left hand side
        leftPids = self.leftListWidget.getTexts()
        pids = [s for s in pids if s not in leftPids]
        data = self._getItemPositions(pids)
        self.rightListWidget.setTexts(pids, clear=True, data=data)

    def _leftPullDownCallback(self, value=None):
        """Callback when selecting the left spectrumGroup pulldown item"""
        obj = self.project.getByPid(value)
        if obj:
            # set the new object
            self.obj = obj
        self._updateStateOnSelection()

    def _rightPullDownCallback(self, value=None):
        """Callback when selecting the right spectrumGroup pulldown item"""
        self._updateRight()

    def _updatedStateToObjects(self):
        result = {}
        for key, state in self._updatedState.items():
            previousState = self._previousState[key]
            if state == previousState:
                continue
            result[key] = {'spectra': [self.project.getByPid(pid) for pid in (state.get('spectra') or [])],
                           'comment': state.get('comment')}
        return result

    def _getRenames(self):
        result = {}

        for name, rename in self._updatedNames.items():
            if name != rename:
                result[name] = rename

        return result

    # def _revertClicked(self):
    #     super()._revertClicked()
    #     self._populate()

    def _applyChanges(self):
        """
        The apply button has been clicked
        Return True on success; False on failure
        """

        updateList = self._updatedStateToObjects()
        renameList = self._getRenames()

        with undoBlockWithoutSideBar():
            try:
                if self.editMode:
                    # edit mode
                    for name, state in updateList.items():
                        items = state.get('spectra')
                        pid = '%s:%s' % (self._groupPidKey, name)
                        obj = self.project.getByPid(pid)

                        setattr(obj, self._classItemAttribute, items)
                        obj.comment = state.get('comment')

                    for name in renameList:
                        pid = '%s:%s' % (self._groupPidKey, name)

                        obj = self.project.getByPid(pid)
                        newName = renameList[name]
                        obj.rename(newName)

                    # call the post init routine to populate any new values as necessary
                    if self._groupEditorInitMethod:
                        # for name, state in updateList.items():
                        #     pid = '%s:%s' % (self._groupPidKey, name)
                        #     obj = self.project.getByPid(pid)
                        #     if obj == self.obj:
                        self._groupEditorInitMethod()

                else:
                    # new mode
                    newState = self._currentEditorState()
                    if newState:
                        name = list(newState.keys())[0]
                        state = list(newState.values())[0]
                        items = state.get('spectra')
                        comment = state.get('comment')

                        func = getattr(self.project, self._projectNewMethod)
                        self.obj = func(name, items, comment=comment)

                        # call the post init routine to populate any new values as necessary - only the current object
                        if self._groupEditorInitMethod:
                            self._groupEditorInitMethod()

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))
                if self.application._isInDebugMode:
                    raise es
                return False

        return True

    def _cancel(self):
        if self.editMode:
            self.leftPullDown.unRegister()
        self.rightPullDown.unRegister()
        self._disconnectModels()
        self.reject()

    def _applyAndClose(self):
        if self._applyChanges() is True:
            if self.editMode:
                self.leftPullDown.unRegister()
            self.rightPullDown.unRegister()
            self._disconnectModels()
            self.accept()

    def _updateGl(self, spectra):
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()
