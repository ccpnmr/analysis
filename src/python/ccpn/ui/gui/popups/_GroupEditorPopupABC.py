"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonBoxList
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Menu import Menu

from ccpn.core.lib.ContextManagers import undoBlock


from re import finditer

from collections import Counter
import copy



def camelCaseSplit(identifier):
    matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return ' '.join([m.group(0) for m in matches])


class FeedbackFrame(Frame):
    def __init__(self, *args, **kwds):
        super().__init__(setLayout=True,*args,**kwds)
        self.highlight(False)


    def highlight(self,enable):

        if enable:
            # GST rgb(88,88,192) is 'ccpn purple' which I guess should be defined somewhere
            self.setStyleSheet('FeedbackFrame {border: 2px solid rgb(88,88,192)}')
        else:
            # this is background grey which I guess should be defined somewhere
            self.setStyleSheet('FeedbackFrame {border: 2px solid rgb(235,235,235)}')


class _ListWidget(ListWidget):
    """Subclassed for dropEvent"""

    ROLES = ('Left','Right')
    def __init__(self, *args, dragRole=None, feedbackWidget = None, rearrangeable=False,  emptyText=None, **kwds):

        super().__init__(*args, **kwds)


        if dragRole.capitalize() not in self.ROLES:
            raise Exception('position must be one of left or right')

        self._rearrangeable = rearrangeable
        self.setDropIndicatorShown(self._rearrangeable)

        self._dragRole = dragRole
        clonedRoles = list(self.ROLES)
        clonedRoles.remove(self._dragRole.capitalize())
        self._oppositeRole =  clonedRoles[0]

        self._emptyText = emptyText


        self._feedbackWidget = feedbackWidget
        self._partner = None

        self.itemDoubleClicked.connect(self._itemDoubleClickedCallback)

        # GST seems to be missing a border, why?
        self.setStyleSheet('ListWidget { border: 1px solid rgb(207,207,207)}')

        self._feedbackWidget.highlight(False)

    def setPartner(self,partner):
        self._partner=partner

    
    def paintEvent(self,event):
        super().paintEvent(event)
        if self.count() == 0:
            self.paintEmpty(event)

    def paintEmpty(self,event):

         p = QtGui.QPainter(self.viewport())
         pen = QtGui.QPen(QtGui.QColor("grey"))
         oldPen = p.pen()
         p.setPen(pen)
         p.drawText(self.rect(), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop , " " + self._emptyText)
         p.setPen(oldPen)
         p.end()

    def _isAcceptableDrag(self,event):
        data = self.parseEvent(event)
        result = False

        if 'source' in data and data['source'] != None:
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


    def dropEvent(self, event):
        if self._isAcceptableDrag(event):

            data = self.parseEvent(event)
            if self._rearrangeable and data['source'] == self:
                QtWidgets.QListWidget.dropEvent(self,event)
            else:
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
        enabledAll=True
        if self.count() == 0:
            enabledAll = False

        contextMenu.addItem("Move %s" % self._oppositeRole, callback=self.move, enabled=enabled)
        contextMenu.addItem("Move All %s" % self._oppositeRole, callback=self.moveAll,enabled=enabledAll)

        return contextMenu

    def _itemsAvailable(self):
        result = False
        count = self.count()
        if count > 0 and self._partner != None:
            selected =  self.selectedItems()
            if len(selected) > 0:
                result = True
            else:
                item = self.itemAt(self._currentMousePos)
                if item:
                    result = True
        return result

    
    def move(self):
        count = self.count()
        if count > 0 and self._partner != None:
            rows = []
            selected =  self.selectedItems()
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
        count = self.count()
        if count > 0 and self._partner is not None:
            for i in reversed(range(count)):
                item = self.takeItem(i)
                self._partner.addItem(item)

    
    def mousePressEvent(self,event):
        self._currentMousePos = event.pos()
        super().mousePressEvent(event)

    def _itemDoubleClickedCallback(self,item):
        if self._partner != None:
            row = self.row(item)
            taken = self.takeItem(row)
            self._partner.addItem(item)

class _GroupEditorPopupABC(CcpnDialog):
    """
    An abstract base class to create and manage popups for KLASS
    """
    # These need sub-classing
    KLASS = None  # e.g. SpectrumGroup
    KLASS_ITEM_ATTRIBUTE = None  # e.g. 'spectra' # Attribute in KLASS containing items
    KLASS_PULLDOWN = None  # SpectrumGroupPulldown

    PROJECT_NEW_METHOD = None  # e.g. 'newSpectrumGroup'  # Method of Project to create new KLASS instance
    PROJECT_ITEM_ATTRIBUTE = None # e.g. 'spectra'  # Attribute of Project containing items

    BUTTON_FILTER = 'Filter by:'
    BUTTON_CANCEL = 'Cancel'

    FIXEDWIDTH = 120

    def __init__(self, parent=None, mainWindow=None, editMode=True, obj=None, defaultItems=None, **kwds):
        """
        Initialise the widget, note defaultItems is only used for create
        """
        print(editMode)

        self.GROUP_NAME = camelCaseSplit(self.KLASS.className)

        title = 'Edit ' + self.GROUP_NAME if editMode else 'New ' + self.GROUP_NAME

        self.LEFT_EMPTY_TEXT = 'Drag or double click %s to add here' % self.PROJECT_ITEM_ATTRIBUTE
        self.RIGHT_EMPTY_TEXT = "No %s: try 'Filter by' settings" % self.PROJECT_ITEM_ATTRIBUTE


        if editMode:
            self._acceptButtonText = 'Apply Changes'
        else:
            self._acceptButtonText = 'Create %s' % self.GROUP_NAME

        CcpnDialog.__init__(self, parent=parent, windowTitle=title, setLayout=True, margins=(0,0,0,0),
                            spacing=(5,5),  **kwds)

        # GST how to get the icon using a relative path?
        self.errorIcon = QtGui.QPixmap('/Users/garythompson/Dropbox/git/ccpnmr/AnalysisV3/src/python/ccpn/ui/gui/widgets/icons/exclamation_small.png')

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.obj = obj
        self.editMode = editMode
        self.defaultItems = defaultItems  #open popup with these items already added to left ListWidget. Ready to create the group.

        self._setLeftWidgets()
        self._setRightWidgets()
        self._setApplyButtons()
        self._addWidgetsToLayout()
        self._connectLists()

        # one cannot be a copy of the other unless its a deep copy...
        # this is easier
        self._previousState = self._getPreviousState()
        self._updatedState = copy.deepcopy(self._getPreviousState())

        self._previousNames = {key : key for key in self._previousState}
        self._updatedNames = dict(self._previousNames)

        self.connectModels()

        self._updateStateOnSelection()


    def _getPreviousState(self):
        result = {}
        beforeKeys = self.project._pid2Obj.get(self.GROUP_PID_KEY)
        if beforeKeys != None:
            for key in beforeKeys:

                #GST do I need to filter object in an undo state, if so could we add some interface for this...
                object = self.project._pid2Obj.get(self.GROUP_PID_KEY)[key]
                items = [elem.pid for elem in getattr(object, self.PROJECT_ITEM_ATTRIBUTE)]
                result[key] = items
        return result

    def _setLeftWidgets(self):

        self.leftTopLabel = Label(self, '', bold=True)

        if not self.editMode:
            labelName = 'New %s Name' % self.GROUP_NAME
        else:
            labelName = 'Name'

        self.nameLabel = Label(self, labelName)
        self.nameEdit = LineEdit(self, backgroundText='%s Name' % self.GROUP_NAME, textAlignment='left')



        self.nameEdit.setFixedWidth(self.FIXEDWIDTH)

        if self.editMode:
            self.leftPullDownLabel = Label(self, self.GROUP_NAME)
            self.leftPullDown = self.KLASS_PULLDOWN(parent=self.mainWindow,
                                                      project = self.project,
                                                      showSelectName=False,
                                                      default=self.obj,
                                                      callback=self._leftPullDownCallback,
                                                      fixedWidths=[0, self.FIXEDWIDTH]
                                                  )

        self.selectionLabel = Label(self,'Selection')
        self.leftItemsLabel = Label(self, self.KLASS_ITEM_ATTRIBUTE.capitalize())
        self.leftListFeedbackWidget = FeedbackFrame(self)
        self.leftListWidget = _ListWidget(self.leftListFeedbackWidget, feedbackWidget = self.leftListFeedbackWidget,
                                          grid=(0,0),dragRole='right',acceptDrops=True, sortOnDrop=False, copyDrop=False,
                                          emptyText=self.LEFT_EMPTY_TEXT,rearrangeable=True)



    def connectModels(self):
        self.nameEdit.textChanged.connect(self._updateModelsOnEdit)
        self.leftListWidget.model().dataChanged.connect(self._updateModelsOnEdit)
        self.leftListWidget.model().rowsRemoved.connect(self._updateModelsOnEdit)
        self.leftListWidget.model().rowsInserted.connect(self._updateModelsOnEdit)
        self.leftListWidget.model().rowsMoved.connect(self._updateModelsOnEdit)

    def disconnectModels(self):
        self.nameEdit.textChanged.disconnect(self._updateModelsOnEdit)
        self.leftListWidget.model().dataChanged.disconnect(self._updateModelsOnEdit)
        self.leftListWidget.model().rowsRemoved.disconnect(self._updateModelsOnEdit)
        self.leftListWidget.model().rowsInserted.disconnect(self._updateModelsOnEdit)
        self.leftListWidget.model().rowsMoved.disconnect(self._updateModelsOnEdit)

    def _setRightWidgets(self):

        self.rightItemsLabel = Label(self, self.GROUP_NAME)
        self.rightPullDown = self.KLASS_PULLDOWN(parent=self.mainWindow,
                                                   project = self.project,
                                                   showSelectName=True,
                                                   selectNoneText='none',
                                                   callback=self._rightPullDownCallback,
                                                   fixedWidths=[0, self.FIXEDWIDTH],
                                                   filterFunction =  self._rightPullDownFilter
                                                   )

        self.rightListFeedbackWidget = FeedbackFrame(self)
        self.rightListWidget = _ListWidget(self.rightListFeedbackWidget, feedbackWidget = self.rightListFeedbackWidget,
                                           grid=(0,0),dragRole='left',acceptDrops=True, sortOnDrop=False, copyDrop=False,
                                           emptyText=self.RIGHT_EMPTY_TEXT)
        self.rightFilterLabel = Label(self, self.BUTTON_FILTER)
        self.errorFrame = Frame(self,setLayout=True)
        # self.rightListWidget.setFixedWidth(2*self.FIXEDWIDTH)

    def _rightPullDownFilter(self,pids):
        if self._editedObject and self._editedObject.pid in pids:
            pids.remove(self._editedObject.pid)
        return pids

    def _setApplyButtons(self):
        self.applyButtons = ButtonBoxList(self, texts=[self.BUTTON_CANCEL, self._acceptButtonText],
                                             callbacks=[self._cancel, self._applyAndClose],
                                             tipTexts=['Cancel the New/Edit operation',
                                                       'Apply according to current settings and close'],
                                             direction='h', hAlign='r',ok=self._acceptButtonText,cancel = self.BUTTON_CANCEL)

    def _addWidgetsToLayout(self):
        # Add left Widgets on Main layout
        layout = self.getLayout()

        label_column = 0
        left_column = 1

        layout.setColumnStretch(label_column,0)
        layout.setColumnStretch(left_column,1000)

        row=0
        if self.editMode:

            layout.addWidget(self.leftPullDownLabel, row, label_column)
            self.leftPullDownLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)


            layout.addWidget(self.leftPullDown, row, left_column, QtCore.Qt.AlignLeft)

            row+=1 #2


        layout.addWidget(self.nameLabel, row, label_column)
        self.nameLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Preferred)

        self.nameEditBorder = Frame(self,setLayout=True)
        layout.addWidget(self.nameEditBorder, row, left_column)
        self.nameEditBorder.layout().addWidget(self.nameEdit,0,0)
        self.nameEditBorder.layout().setContentsMargins(2, 0,0,0)
        self.nameEditBorder.layout().setAlignment(self.nameEdit,QtCore.Qt.AlignLeft)
        self.nameEditBorder.setFocusProxy(self.nameEdit)
        # layout.addWidget(self.nameEdit, row, left_column)
        row+=1

        self.addSpacer(0,5, grid=(row,0), gridSpan=(1,3))

        row+=1
        layout.setRowStretch(row,1000)
        layout.addWidget(self.selectionLabel, row, label_column)
        layout.setAlignment(self.selectionLabel,QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        self._doublePane =  Widget(self,setLayout=True)
        self._doublePane.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)

        layout.addWidget(self._doublePane,row, left_column,1,1)
        self.rightListWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        self._doublePane.getLayout().addWidget(self.leftItemsLabel,0,0)
        layout.setAlignment(self.leftItemsLabel,QtCore.Qt.AlignLeft)
        self._doublePane.getLayout().addWidget(self.rightItemsLabel,0,1)
        layout.setAlignment(self.rightItemsLabel,QtCore.Qt.AlignLeft)
        self._doublePane.getLayout().addWidget(self.rightListFeedbackWidget,1,0)
        self._doublePane.getLayout().addWidget(self.leftListFeedbackWidget,1,1)
        self.leftListWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)


        row+=2
        self._selectionFrame = Widget(self,setLayout=True,)
        layout.addWidget(self._selectionFrame,row,left_column)
        filterLayout = self._selectionFrame.getLayout()
        # filterLayout.addWidget(self.rightRadioButtons, 0, 0)
        filterLayout.addWidget(self.rightFilterLabel, 0, 0)
        filterLayout.addWidget(self.rightPullDown, 0, 1)
        filterLayout.setColumnStretch(2,1)

        row+=1

        layout.addWidget(self.errorFrame,row,left_column,1,1)

        row+=1
        self.addSpacer(0,10, grid=(row,0), gridSpan=(1,1))

        row+=1
        layout.addWidget(self.applyButtons, row, label_column, 1, 2, QtCore.Qt.AlignRight)

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
        result  = self.leftListWidget.getTexts()
        if self.LEFT_EMPTY_TEXT in result:
            result.remove(self.LEFT_EMPTY_TEXT)
        return result


    @property
    def _editedObjectItems(self) -> list:
        """Convenience to get the list of items we are editing for object (e.g. spectra for SpectrumGroup)
        Returns list or None on error
        """
        obj = self._editedObject
        if obj is None:
            return None
        return self._updatedState[obj.name]

    @property
    def _projectObjectItems(self) -> list:
        """Convenience to get the list from project of items we are editing for object (e.g. spectra
        in case of SpectrumGroup)
        Returns list or None on error
        """
        if not hasattr(self.project, self.PROJECT_ITEM_ATTRIBUTE):
            return None
        return getattr(self.project, self.PROJECT_ITEM_ATTRIBUTE)

    def _setAcceptButtonState(self):
        if self.self.editMode and self._dirty:
            self.applyButtons.setButtonEnabled(self._acceptButtonText, True)

    def _currentEditorState(self):
        result = {}
        if self.editMode and self._editedObject:
            key = self._editedObject.name
            items = self._groupedObjects
        else:
            key = self.nameEdit.text()
            items = self._groupedObjects

        if len(key) > 0:
            result = {key : items}

        return result

    def _updateModelsOnEdit(self, *args, **kwargs):

        currentEdits = self._currentEditorState()

        if self.editMode and self._editedObject != None:
            for id,selections in currentEdits.items():
                self._updatedState[id] = selections

            editedObjectName = self._editedObject.name
            newName = self.nameEdit.text()
            self._updatedNames[editedObjectName] = newName

        self._updateButton()

    def _checkForTrailingSpacesOnGroupName(self):
        result =  False
        resultString = ''
        badNames = []
        for name in self._updatedState.keys():
            if len(name.strip()) != 0:
                if len(name.strip()) != len(name):
                    result  = True
                    badNames.append(name.strip())

        if result:
            joinedNames = ', '.join(badNames)
            resultString = 'Some %s have names with leading or trailing spaces %s' % (self.PLURAL_GROUPED_NAME,  joinedNames)

        return result, resultString

    def _checkForEmptyNames(self):
        result = False
        badKeys  = []
        for name in self._updatedState.keys():
            if len(name.strip()) == 0:
                raise Exception('unexpected')
                # result  = True

        for key,name in self._updatedNames.items():
            if len(name.strip()) == 0:
                badKeys.append(key)
                result = True

        resultString = ''
        if result:
            badKeys.sort()
            resultString = 'Some %s have an empty name (original names: %s)' % (self.PLURAL_GROUPED_NAME,','.join(badKeys))

        return result, resultString

    def _checkForDuplicatetNames(self):
        nameCount  = Counter(self._updatedNames.values())
        duplicateNameCounts = list(filter(lambda i: i[1] > 1, nameCount.items()))
        result = len(duplicateNameCounts) > 0

        resultString = ''
        if result:
            duplicateNames = [item[0] for item in duplicateNameCounts]
            duplicateNameString = ','.join(duplicateNames)
            resultString = 'Duplicate Names: %s' % duplicateNameString

        return result, resultString

    def _checkForEmptyGroups(self):

        badKeys = []
        for key,values in self._updatedState.items():
            values = self.filterEmptyText(values)
            if len(values) == 0:
                badKeys.append(key)

        result = False
        resultString =''
        if len(badKeys) > 0:
            result = True
            resultString = 'Empty %s: %s' % (self.PLURAL_GROUPED_NAME,','.join(badKeys))

        return result,resultString

    def _checkForTrailingSpacesName(self):

        result = False
        badKeys = []
        for key,name in self._updatedNames.items():
            if len(name.strip()) != len(name):
                badKeys.append(key)
                result = True

        msg = 'Some %s names have leading or tailings spaces\n (original names are: %s)'
        resultString = msg % (self.PLURAL_GROUPED_NAME,','.join(badKeys))

        return result, resultString

    def _checkForExistingName(self):
        currentEdits = self._currentEditorState()
        result=False
        resultString = ''

        if currentEdits != {}:
            name = list(currentEdits.keys())[0]
            if name in self._previousState.keys():
                result=True

                # GST when i used 'The Spectrum Group %s already exists' % name igot an odd effect
                # the space and a in already were deleted...
                resultString = 'The ' + self.SINGULAR_GROUP_NAME + ' ' + name + ' already exists'

        return result, resultString


    def filterEmptyText(self,items):
        if self.LEFT_EMPTY_TEXT in items:
            items.remove(self.LEFT_EMPTY_TEXT)
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

        return result,resultString

    def _checkForTrailingSpaceOnName_New(self):
        result = False
        resultString = ''

        spacesString = 'The %s name has leading or trailing spaces' % self.PLURAL_GROUPED_NAME

        currentEdits = self._currentEditorState()
        if currentEdits != {}:
            name = list(currentEdits.keys())[0]
            if len(name.strip()) != len(name):
                result = True
                resultString = spacesString

        return result,resultString


    def _checkForEmptyGroup_New(self):
        result = False
        resultString = ''

        if len(self._groupedObjects) ==  0:
            result = True
            resultString = 'The %s is empty' % self.SINGULAR_GROUP_NAME

        return result,resultString

    def _updateButton(self):


        self.errors = []

        if not self.editMode :

            enabled = True

            check,message = self._checkForNoName_New()
            if check:
                enabled = False
                self.errors.append(message)


            check,message = self._checkForEmptyGroup_New()
            if check:
                enabled = False
                self.errors.append(message)

            check,message = self._checkForTrailingSpaceOnName_New()
            if check:
                enabled = False
                self.errors.append(message)

            check,message = self._checkForExistingName()
            if check:
                enabled = False
                self.errors.append(message)

        elif self.editMode:

            enabled =  False

            if self._updatedState != self._previousState:
                enabled = True

            if self._updatedNames != self._previousNames:
                enabled = True

            check,message = self._checkForEmptyNames()
            if check:
                enabled = False
                self.errors.append(message)

            check,message = self._checkForDuplicatetNames()
            if check:
                enabled = False
                self.errors.append(message)

            check,message = self._checkForEmptyGroups()
            if check:
                enabled = False
                self.errors.append(message)

            check,message = self._checkForTrailingSpacesName()
            if check:
                enabled = False
                self.errors.append(message)


        self.applyButtons.setButtonEnabled(self._acceptButtonText, enabled)


        self._emptyErrorFrame()

        if len(self.errors) != 0:
            self.errorFrame.layout().setColumnStretch(0,0)
            self.errorFrame.layout().setColumnStretch(1,1000)
            for i,error in enumerate(self.errors):
                label =  Label(self.errorFrame,error)
                iconLabel = Label(self.errorFrame)
                iconLabel.setPixmap(self.errorIcon) #.scaled(20,20,QtCore.Qt.KeepAspectRatio
                self.errorFrame.layout().addWidget(label,i,1)
                self.errorFrame.layout().setAlignment(label,QtCore.Qt.AlignLeft)
                self.errorFrame.layout().addWidget(iconLabel,i,0)
                self.errorFrame.layout().setAlignment(iconLabel,QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

    def _emptyErrorFrame(self):
        for child in self.errorFrame.findChildren(QtGui.QWidget):
            self.errorFrame.getLayout().removeWidget(child)
            child.setParent(None)
            del child

    def _updateStateOnSelection(self):
        """Update state
        """

        # Note well model updates must be off while the selected
        # group to edit is being changed else the changes applied
        # will trigger model changes
        self.disconnectModels()
        self._updateLeft()
        self._updateRight()
        self._updateButton()
        self.rightPullDown._updatePulldownList()
        if len(self.rightPullDown.getObjects()) < 2:
            self.rightPullDown.setEnabled(False)
        else:
            self.rightPullDown.setEnabled(True)
        self.connectModels()


    def _updateLeft(self):
        """Update Left
        """

        if self.editMode:

            self.leftPullDownLabel.show()
            self.leftPullDown.show()
            self.rightPullDown.setEnabled(len(self.leftPullDown.getObjects()) > 0)
            obj = self._editedObject
            if obj is not None:
                name = self._updatedNames[obj.name]
                self.nameEdit.setText(name)
                self._setLeftListWidgetItems(self._editedObjectItems)
                self.nameEdit.setEnabled(True)
                self.leftListWidget.setEnabled(True)
                self.rightListWidget.setEnabled(True)
            else:
                self.nameEdit.setText('')
                self.leftListWidget.clear()
                self.nameEdit.setEnabled(False)
                self.leftListWidget.setEnabled(False)
                self.rightListWidget.setEnabled(False)

        else:
            self.leftListWidget.clear()
            if self.defaultItems is not None:
                self._setLeftListWidgetItems(self.defaultItems)
            self.nameEdit.setText('')



    def _updateRight(self):
        """Update Right
        """
        if self.rightPullDown.getSelectedObject() is None:
            self._setRightListWidgetItems(self._projectObjectItems)
        else:
            self.rightListWidget.clear()
            group = self.rightPullDown.getSelectedObject()
            if group is not None:
                self._setRightListWidgetItems(group.spectra)



    def _setLeftListWidgetItems(self, pids: list):
        """Convenience to set the items in the left ListWidget
        """
        # convert items to pid's
        self.leftListWidget.setTexts(pids, clear=True)

    def _setRightListWidgetItems(self, items: list):
        """Convenience to set the items in the right ListWidget
        """
        # convert items to pid's
        pids = [s.pid for s in items]
        # filter for those pid's already on the left hand side
        leftPids = self.leftListWidget.getTexts()
        pids = [s for s in pids if s not in leftPids]
        self.rightListWidget.setTexts(pids, clear=True)

    def _leftPullDownCallback(self, value=None):
        """Callback when selecting the left spectrumGroup pulldown item"""
        self._updateStateOnSelection()

    def _rightPullDownCallback(self, value=None):
        """Callback when selecting the right spectrumGroup pulldown item"""
        self._updateRight()

    def _updatedStateToObjects(self):
        result = {}
        for key,state in self._updatedState.items():
            previousState = self._previousState[key]
            if state == previousState:
                continue
            result[key] = [self.project.getByPid(pid) for pid in state]
        return result

    def _getRenames(self):
        result = {}

        for name,rename in self._updatedNames.items():
            if name != rename:
                result[name]=rename

        return result

    def _applyChanges(self):
        """
        The apply button has been clicked
        Return True on success; False on failure
        """

        updateList = self._updatedStateToObjects()
        renameList = self._getRenames()

        with undoBlock():
            try:
                if self.editMode:
                    # edit mode
                    for name,items in updateList.items():
                        pid = '%s:%s' % (self.GROUP_PID_KEY,name)
                        obj =  self.project.getByPid(pid)

                        setattr(obj, self.KLASS_ITEM_ATTRIBUTE, items)

                    for name in renameList:
                        pid = '%s:%s' % (self.GROUP_PID_KEY,name)

                        obj =  self.project.getByPid(pid)
                        newName = renameList[name]
                        obj.rename(newName)

                else:
                    # new mode
                    newState = self._currentEditorState()
                    name = list(newState.keys())[0]
                    items = list(newState.values())[0]
                    func = getattr(self.project, self.PROJECT_NEW_METHOD)
                    func(name, items)


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
        self.disconnectModels()
        self.reject()

    def _applyAndClose(self):
        if self._applyChanges() is True:
            if self.editMode:
                self.leftPullDown.unRegister()
            self.rightPullDown.unRegister()
            self.disconnectModels()
            self.accept()
