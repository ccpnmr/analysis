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
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.core.SpectrumGroup import SpectrumGroup

from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.PulldownListsForObjects import SpectrumGroupPulldown

from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import undoBlockManager

class _LeftListWidget(ListWidget):
    """Subclassed for dropEvent"""

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def dropEvent(self, event):
        data = self.parseEvent(event)
        super().dropEvent(event=event)
        self.parent()._removeFromRight()

class _RightListWidget(ListWidget):
    """Subclassed for dropEvent"""

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def dropEvent(self, event):
        data = self.parseEvent(event)
        super().dropEvent(event=event)
        self.parent()._removeFromLeft()


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

    BUTTON_ALL = 'All'
    BUTTON_FILTER = 'Filter by:'
    RIGHT_RADIOBUTTONS = [BUTTON_ALL, BUTTON_FILTER]

    FIXEDWIDTH = 120

    def __init__(self, parent=None, mainWindow=None, editMode=True, obj=None, defaultItems=None, **kwds):
        """
        Initialise the widget
        """
        title = 'Edit ' + self.KLASS.className if editMode else 'New ' + self.KLASS.className
        CcpnDialog.__init__(self, parent=parent, windowTitle=title, setLayout=True, margins=(10,10,10,10),
                            spacing=(5,5), **kwds)

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

        self._updateState()

    def _setLeftWidgets(self):

        self.leftTopLabel = Label(self, '', bold=True)

        self.nameLabel = Label(self, 'Name')
        self.nameEdit = LineEdit(self, backgroundText='> Enter name <', textAlignment='left')
        # self.nameEdit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.nameEdit.setFixedWidth(self.FIXEDWIDTH)

        self.leftPullDownLabel = Label(self, self.KLASS.className)
        self.leftPullDown = self.KLASS_PULLDOWN(parent=self.mainWindow,
                                                  project = self.project,
                                                  showSelectName=True,
                                                  default=self.obj,
                                                  callback=self._leftPullDownCallback,
                                                  fixedWidths=[0, self.FIXEDWIDTH]
                                                  )

        self.leftItemsLabel = Label(self, self.KLASS_ITEM_ATTRIBUTE.capitalize())
        self.leftListWidget = _LeftListWidget(self, acceptDrops=True, sortOnDrop=False, copyDrop=False)
        self.leftListWidget.setFixedWidth(self.FIXEDWIDTH)

    def _setRightWidgets(self):
        self.rightTopLabel = Label(self, 'Sources', bold=True)

        self.rightRadioButtons = RadioButtons(self, texts=self.RIGHT_RADIOBUTTONS,
                                                      selectedInd=0,
                                                      callback=self._updateRight,
                                                      direction='h',
                                                      tipTexts=None, gridSpan=(1, 2))
        self.rightPullDown = SpectrumGroupPulldown(parent=self.mainWindow,
                                                   project = self.project,
                                                   showSelectName=True,
                                                   callback=self._rightPullDownCallback,
                                                   fixedWidths=[0, self.FIXEDWIDTH]
                                                   )

        self.rightListWidget = _RightListWidget(self, acceptDrops=True, sortOnDrop=False, copyDrop=False)
        self.rightListWidget.setFixedWidth(2*self.FIXEDWIDTH)

    def _setApplyButtons(self):
        self.applyButtons = ButtonList(self, texts=['Cancel', 'Apply and Close'],
                                             callbacks=[self._cancel, self._applyAndClose],
                                             tipTexts=['Cancel the New/Edit operation',
                                                       'Apply according to current settings and close'],
                                             direction='h', hAlign='r')

    def _addWidgetsToLayout(self):
        # Add left Widgets on Main layout
        layout = self.getLayout()

        layout.addWidget(self.leftTopLabel, 0, 0)
        layout.addWidget(self.leftPullDownLabel, 1, 0)
        layout.addWidget(self.leftPullDown, 1, 1)
        layout.addWidget(self.nameLabel, 2, 0)
        layout.addWidget(self.nameEdit, 2, 1)
        layout.addWidget(self.leftItemsLabel, 3, 0)
        layout.addWidget(self.leftListWidget, 3, 1, 1, 1)

        # Add Right Widgets on Main layout
        layout.addWidget(self.rightTopLabel, 0, 2)
        layout.addWidget(self.rightRadioButtons, 2, 2)
        layout.addWidget(self.rightPullDown, 2, 3)
        layout.addWidget(self.rightListWidget, 3, 2, 1, 2)

        # Add Buttons Widgets on Main layout
        self.addSpacer(0,10, grid=(4,0), gridSpan=(1,4))
        layout.addWidget(self.applyButtons, 4, 0, 1, 4)

    @property
    def _editedObject(self):
        "Convenience to get the edited object"
        result = None
        if self.editMode:
            result = self.leftPullDown.getSelectedObject()
        return result

    @property
    def _editedObjectItems(self) -> list:
        """Convenience to get the list of items we are editing for object (e.g. spectra for SpectrumGroup)
        Returns list or None on error
        """
        obj = self._editedObject
        if obj is None:
            return None
        if not hasattr(obj, self.KLASS_ITEM_ATTRIBUTE):
            return None
        return getattr(obj, self.KLASS_ITEM_ATTRIBUTE)

    @property
    def _projectObjectItems(self) -> list:
        """Convenience to get the list from project of items we are editing for object (e.g. spectra
        in case of SpectrumGroup)
        Returns list or None on error
        """
        if not hasattr(self.project, self.PROJECT_ITEM_ATTRIBUTE):
            return None
        return getattr(self.project, self.PROJECT_ITEM_ATTRIBUTE)

    def _updateState(self):
        """Update state
        """
        self._updateLeft()
        self._updateRight()

    def _updateLeft(self):
        """Update Left
        """
        # self.leftRadioButtons.hide()

        if self.editMode:
            self.leftTopLabel.setText('Edit ')
            self.leftPullDownLabel.show()
            self.leftPullDown.show()
            obj = self._editedObject
            if obj is not None:
                self.nameEdit.setText(obj.name)
                self._setLeftListWidgetItems(self._editedObjectItems)
            else:
                self.nameEdit.setText('')
                self.leftListWidget.clear()

        else:
            self.leftTopLabel.setText('New ' + self.KLASS.className)
            self.leftPullDownLabel.hide()
            self.leftPullDown.hide()
            self.leftListWidget.clear()
            if self.defaultItems is not None:
                self._setLeftListWidgetItems(self.defaultItems)
            self.nameEdit.setText('')

        self._addEmptyDescriptions()

    def _updateRight(self):
        """Update Right
        """
        selected = self.rightRadioButtons.get()
        if selected == self.BUTTON_ALL:
            self.rightPullDown.hide()
            self._setRightListWidgetItems(self._projectObjectItems)
        else:
            self.rightPullDown.show()
            self.rightListWidget.clear()
            spectrumGroup = self.rightPullDown.getSelectedObject()
            if spectrumGroup is not None:
                self._setRightListWidgetItems(spectrumGroup.spectra)
        self._addEmptyDescriptions()

    def _addDescription(self, widget, text):
        item = QtWidgets.QListWidgetItem(text)
        item.setFlags(QtCore.Qt.NoItemFlags)
        widget.addItem(item)

    LEFT_EMPTY_TEXT = 'Drag item(s) from Sources to here'
    RIGHT_EMPTY_TEXT = "No (more) Sources; change 'All' or 'Filter' settings"

    def _addEmptyDescriptions(self):
        "Add descriptions to empty ListWidgets"
        leftPids = self.leftListWidget.getTexts()
        rightPids = self.rightListWidget.getTexts()

        if len(leftPids) == 0:
            self._addDescription(self.leftListWidget, self.LEFT_EMPTY_TEXT)

        if len(rightPids) == 0:
            self._addDescription(self.rightListWidget, self.RIGHT_EMPTY_TEXT)

    def _setLeftListWidgetItems(self, items: list):
        """Convenience to set the items in the left ListWidget
        """
        # convert items to pid's
        pids = [s.pid for s in items]
        self.leftListWidget.setTexts(pids, clear=True)
        self._addEmptyDescriptions()

    def _setRightListWidgetItems(self, items: list):
        """Convenience to set the items in the right ListWidget
        """
        # convert items to pid's
        pids = [s.pid for s in items]
        # filter for those pid's already on the left hand side
        leftPids = self.leftListWidget.getTexts()
        pids = [s for s in pids if s not in leftPids]
        self.rightListWidget.setTexts(pids, clear=True)
        self._addEmptyDescriptions()

    def _leftPullDownCallback(self, value=None):
        """Callback when selecting the left spectrumGroup pulldown item"""
        self._updateState()

    def _rightPullDownCallback(self, value=None):
        """Callback when selecting the right spectrumGroup pulldown item"""
        self._updateRight()

    def _removeFromLeft(self):
        """
        Handle EMPTY_TEXT from left list widget; called when dropped onto right widget
        QT has handled the drop from left to right (or vice versa)
        """

        # remove empty text
        items = self.rightListWidget.findItems(self.RIGHT_EMPTY_TEXT, QtCore.Qt.MatchExactly)
        for item in items:
            self.rightListWidget.takeItem(self.rightListWidget.row(item))

        # add empty text message to the other group
        leftPids = self.leftListWidget.count() - len(self.leftListWidget.selectedItems())
        if not leftPids:
            self._addDescription(self.leftListWidget, self.LEFT_EMPTY_TEXT)

    def _removeFromRight(self):
        """
        Handle EMPTY_TEXT from left list widget; called when dropped onto right widget
        QT has handled the drop from left to right (or vice versa)
        """
        # remove empty text
        items = self.leftListWidget.findItems(self.LEFT_EMPTY_TEXT, QtCore.Qt.MatchExactly)
        for item in items:
            self.leftListWidget.takeItem(self.leftListWidget.row(item))

        # add empty text message to the other group
        rightPids = self.rightListWidget.count() - len(self.rightListWidget.selectedItems())
        if not rightPids:
            self._addDescription(self.rightListWidget, self.RIGHT_EMPTY_TEXT)

    def _applyChanges(self):
        """
        The apply button has been clicked
        Return True on success; False on failure
        """
        name = self.nameEdit.get()
        if len(name) == 0:
            msg = 'Undefined name'
            getLogger().warning(msg)
            showWarning(str(self.windowTitle()), msg)
            return False

        items = [self.project.getByPid(itm) for itm in self.leftListWidget.getTexts()]
        if None in items:
            msg = 'Could not convert all pids to objects'
            getLogger().warning(msg)
            showWarning(str(self.windowTitle()), msg)
            return False

        with undoBlockManager():
            try:
                if self.editMode:
                    # edit mode
                    obj = self._editedObject
                    if obj.name != name:
                        obj.rename(name)
                    setattr(obj, self.KLASS_ITEM_ATTRIBUTE, items)
                else:
                    # new mode
                    func = getattr(self.project, self.PROJECT_NEW_METHOD)
                    obj = func(name=name)
                    setattr(obj, self.KLASS_ITEM_ATTRIBUTE, items)

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))
                if self.application._isInDebugMode:
                    raise es
                return False

        return True

    def _cancel(self):
        self.leftPullDown.unRegister()
        self.rightPullDown.unRegister()
        self.reject()

    def _applyAndClose(self):
        if self._applyChanges() is True:
            self.leftPullDown.unRegister()
            self.rightPullDown.unRegister()
            self.accept()
