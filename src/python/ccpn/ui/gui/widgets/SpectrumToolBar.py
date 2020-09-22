"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-09-22 09:33:24 +0100 (Tue, September 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from contextlib import contextmanager
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from functools import partial
from ccpn.core.lib.Notifiers import Notifier
from collections import OrderedDict
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Font import setWidgetFont, getFontHeight
from ccpn.ui._implementation.PeakListView import PeakListView
from ccpn.ui._implementation.IntegralListView import IntegralListView
from ccpn.ui._implementation.MultipletListView import MultipletListView
from ccpn.core.PeakList import PeakList
from ccpn.core.IntegralList import IntegralList
from ccpn.core.MultipletList import MultipletList
from ccpn.ui.gui.lib.GuiSpectrumView import _spectrumViewHasChanged
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpn.core.lib import Pid
from ccpn.ui.gui.lib.GuiStripContextMenus import _SCMitem, ItemTypes, ITEM, _addMenuItems, _createMenu, _separator


TOOLBAR_EXTENSIONNAME = 'qt_toolbar_ext_button'


class SpectrumToolBar(ToolBar):

    def __init__(self, parent=None, widget=None, **kwds):

        super().__init__(parent=parent, **kwds)
        self.widget = widget
        self._parent = parent
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

        self.setMouseTracking(True)
        self._spectrumToolBarBlockingLevel = 0

        for child in self.children():
            if child.objectName() == TOOLBAR_EXTENSIONNAME:
                self._extButton = child

        self._firstButton = 0

    @property
    def isBlocked(self):
        """True if spectrumToolBar is blocked
        """
        return self._spectrumToolBarBlockingLevel > 0

    def _blockSpectrumToolBarEvents(self):
        """Block all updates/signals/notifiers on the spectrumToolBar
        """
        self.setUpdatesEnabled(False)
        self.blockSignals(True)

    def _unblockSpectrumToolBarEvents(self):
        """Unblock all updates/signals/notifiers on the spectrumToolBar
        """
        self.blockSignals(False)
        self.setUpdatesEnabled(True)

    @contextmanager
    def spectrumToolBarBlocking(self, node=None):
        """Context manager to handle blocking of the spectrumToolBar events.
        """
        self.increaseSpectrumToolBarBlocking(node)
        try:
            # pass control to the calling function
            yield

        finally:
            self.decreaseSpectrumToolBarBlocking(node)

    def increaseSpectrumToolBarBlocking(self, node=None):
        """increase level of blocking
        """
        if self._spectrumToolBarBlockingLevel == 0:
            self._blockSpectrumToolBarEvents()
        self._spectrumToolBarBlockingLevel += 1

    def decreaseSpectrumToolBarBlocking(self, node=None):
        """Reduce level of blocking - when level reaches zero, SpectrumToolBar is unblocked
        """
        if self._spectrumToolBarBlockingLevel > 0:
            self._spectrumToolBarBlockingLevel -= 1
            # check if level at zero; if so call post-blocking update
            if self._spectrumToolBarBlockingLevel == 0:
                self._unblockSpectrumToolBarEvents()
        else:
            raise RuntimeError('Error: cannot decrease spectrumToolBar blocking below 0')

    def _paintButtonToMove(self, button):
        pixmap = button.grab()  # makes a "ghost" of the button as we drag
        # below makes the pixmap half transparent
        painter = QtGui.QPainter(pixmap)
        painter.setCompositionMode(painter.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), QtGui.QColor(0, 0, 0, 127))
        painter.end()
        return pixmap

    def _updateSpectrumViews(self, newIndex):
        newSpectrumViewsOrder = []

        for action in self.actions():
            spectrumView = self.widget.project.getByPid(action.spectrumViewPid)
            newSpectrumViewsOrder.append(spectrumView)

        # self.widget.project.blankNotification()
        # newIndex = [newIndex.index(ii) for ii in self.widget.getOrderedSpectrumViewsIndex()]
        newIndex = tuple(self.widget.getOrderedSpectrumViewsIndex()[ii] for ii in newIndex)
        self.widget.setOrderedSpectrumViewsIndex(newIndex)

        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=None)

        # GLSignals.emitPaintEvent()
        GLSignals._emitAxisUnitsChanged(source=None, strip=self.widget.strips[0], dataDict={})

    def _addSubMenusToContext(self, contextMenu, button):

        with self.spectrumToolBarBlocking():
            dd = OrderedDict([(PeakList, PeakListView), (IntegralList, IntegralListView), (MultipletList, MultipletListView)])
            spectrum = self.widget.project.getByPid(button.actions()[0].objectName())
            if spectrum:
                for coreObj, viewObj in dd.items():
                    smenu = contextMenu.addMenu(coreObj.className)
                    allViews = []
                    vv = getattr(self.widget, viewObj._pluralLinkName)
                    if vv:
                        for view in vv:
                            s = coreObj.className
                            o = getattr(view, s[0].lower() + s[1:])
                            if o:
                                if o._parent == spectrum:
                                    allViews.append(view)
                    views = list(set(allViews))
                    smenu.setEnabled(len(views) > 0)

                    menuItems = [_SCMitem(name='Show All',
                                          typeItem=ItemTypes.get(ITEM), icon='icons/null',
                                          callback=partial(self._setVisibleAllFromList, True, smenu, views)),
                                 _SCMitem(name='Hide All',
                                          typeItem=ItemTypes.get(ITEM), icon='icons/null',
                                          callback=partial(self._setVisibleAllFromList, False, smenu, views)),
                                 ]

                    _addMenuItems(self.widget, smenu, menuItems)

                    # smenu.addAction('Show All', partial(self._setVisibleAllFromList, True, smenu, views))
                    # smenu.addAction('Hide All', partial(self._setVisibleAllFromList, False, smenu, views))

                    smenu.addSeparator()
                    for view in sorted(views, reverse=False):
                        ccpnObj = view._childClass
                        strip = view._parent._parent
                        toolTip = 'Toggle {0} {1} on strip {2}'.format(coreObj.className, ccpnObj._key, strip.id)
                        if ccpnObj:
                            if len(self.widget.strips) > 1:  #add shows in which strips the view is
                                currentTxt = ''  # add in which strip is current
                                if self.widget.current.strip == strip:
                                    currentTxt = ' Current'
                                action = smenu.addItem('{0} ({1}{2})'.format(ccpnObj.id, strip.id, currentTxt), toolTip=toolTip)
                            else:
                                action = smenu.addItem(ccpnObj.id, toolTip=toolTip)

                            action.setCheckable(True)
                            if view.isVisible():
                                action.setChecked(True)
                            action.toggled.connect(view.setVisible)
                            action.toggled.connect(self._updateGl)

    def _spectrumToolBarItem(self, button):
        spectrum = self.widget.project.getByPid(button.actions()[0].objectName())
        specViews = [spv for spv in self.widget.spectrumViews
                     if spv.spectrum == spectrum]

        if len(specViews) >= 1:
            return _SCMitem(name='Contours',
                            typeItem=ItemTypes.get(ITEM), toolTip='Toggle Spectrum Contours On/Off',
                            callback=partial(self._toggleSpectrumContours, button.actions()[0], specViews[0]),
                            checkable=True,
                            checked=specViews[0]._showContours)

    def _toggleSpectrumContours(self, buttonAction, specView):
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        specView._showContours = not specView._showContours
        _spectrumViewHasChanged({Notifier.OBJECT: specView})

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()

    def _createToolBarContextMenu(self):
        """
        Creates a context menu for the toolbar with general actions.
        """

        contextMenu = Menu('', self.widget, isFloatWidget=True)
        dd = OrderedDict([(PeakList, PeakListView), (IntegralList, IntegralListView), (MultipletList, MultipletListView)])
        for coreObj, viewObj in dd.items():
                smenuItems = []
                smenu = contextMenu.addMenu(coreObj.className)
                labelsBools = OrderedDict([('Show All',True),
                                           ('Hide All',False)])
                for label, abool in labelsBools.items():
                    item = _SCMitem(name=label,
                                    typeItem=ItemTypes.get(ITEM), icon='icons/null',
                                    callback=partial(self._toggleAllViews,viewObj._pluralLinkName,abool))
                    smenuItems.append(item)
                _addMenuItems(self.widget, smenu, smenuItems)

        return contextMenu

    def _toggleAllViews(self, viewPluralLinkName, abool=True):
        """
        :param viewPluralLinkName: peakListViews etc which is defined in the self.widget
        :param abool: True or False
        :return: Toggles all Views on display
        """
        for view in getattr(self.widget,viewPluralLinkName):
            view.setVisible(abool)


    def _createContextMenu(self, button: QtWidgets.QToolButton):
        """
        Creates a context menu containing a command to delete the spectrum from the display and its
        button from the toolbar.
        """
        if not button:
            return None
        if len(button.actions()) < 1:
            return None

        contextMenu = Menu('', self.widget, isFloatWidget=True)

        _addMenuItems(self.widget, contextMenu, [self._spectrumToolBarItem(button)])

        contextMenu.addSeparator()

        self._addSubMenusToContext(contextMenu, button)
        contextMenu.addSeparator()

        menuItems = [_SCMitem(name='Jump on SideBar',
                              typeItem=ItemTypes.get(ITEM), icon='icons/null',
                              callback=partial(self._jumpOnSideBar, button)),
                     _SCMitem(name='Properties...',
                              typeItem=ItemTypes.get(ITEM), icon='icons/null',
                              callback=partial(self._showSpectrumProperties, button)),
                     _SCMitem(name='Remove Spectrum',
                              typeItem=ItemTypes.get(ITEM), icon='icons/null',
                              callback=partial(self._removeSpectrum, button)),
                     ]

        _addMenuItems(self.widget, contextMenu, menuItems)

        return contextMenu

    def _jumpOnSideBar(self, button):
        spectrum = self.widget.project.getByPid(button.actions()[0].objectName())
        if spectrum:
            sideBar = self.widget.application.ui.mainWindow.sideBar
            sideBar.selectPid(spectrum.pid)

    def _showSpectrumProperties(self, button):
        spectrum = self.widget.project.getByPid(button.actions()[0].objectName())
        mainWindow = self.widget.application.ui.mainWindow
        if spectrum:  #not sure why It needs parent = mainWindow. copied from SideBar
            popup = SpectrumPropertiesPopup(parent=mainWindow, mainWindow=mainWindow, spectrum=spectrum)
            popup.exec_()
            popup.raise_()

    def _updateGl(self, ):
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)

        # GLSignals.emitPaintEvent()
        GLSignals._emitAxisUnitsChanged(source=None, strip=self.widget.strips[0], dataDict={})

    def _getSpectrumViewFromButton(self, button):
        spvs = []
        key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]

        for spectrumView in self.widget.spectrumViews:
            if spectrumView._apiDataSource == key:
                spvs.append(spectrumView)
        if len(spvs) == 1:
            return spvs[0]

    def _setVisibleAllFromList(self, abool, menu, views):
        """
        :param abool: T or F
        :param menu:
        :param views: any of Views obj _pluralLinkName
        :return:
        """
        if views:
            for view in views:
                view.setVisible(abool)
                for action in menu.actions():
                    if action.text() == view.pid:
                        action.setChecked(abool)

    def _spectrumRename(self, data):
        """Rename the spectrum name in the toolbar from a notifier callback
        """
        spectrum = data[Notifier.OBJECT]
        trigger = data[Notifier.TRIGGER]

        if spectrum and trigger in [Notifier.RENAME]:
            oldPid = Pid.Pid(data[Notifier.OLDPID])
            oldId = oldPid.id

            validActions = [action for action in self.actions() if action.text() == oldId]
            for action in validActions:
                action.setText(spectrum.id)
                action.setObjectName(spectrum.pid)
                # setWidgetFont(action, size='SMALL')

    def _removeSpectrum(self, button: QtWidgets.QToolButton):
        """
        Removes the spectrum from the display and its button from the toolbar.
        """
        # TODO:ED this needs patching in to the spectrumView.delete()
        # remove the item from the toolbar
        self.removeAction(button.actions()[0])

        # and delete the spectrumView from the V2
        key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
        stripUpdateList = []
        for spectrumView in self.widget.spectrumViews:
            if spectrumView._apiDataSource == key:
                index = self.widget.spectrumViews.index(spectrumView)
                break
        else:
            showWarning('Spectrum not found in toolbar')
            return

        # found value is spectrumView, index

        spectrumView.delete()
        # self.widget.removeOrderedSpectrumView(index)

        # spawn a redraw of the GL windows
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=None)
        GLSignals.emitPaintEvent()

    def _dragButton(self, event):

        toolButton = self.childAt(event.pos())
        self._buttonBeingDragged = toolButton
        allActionsTexts = []

        if toolButton:
            pixmap = self._paintButtonToMove(toolButton)

            mimeData = QtCore.QMimeData()
            mimeData.setText('%d,%d' % (event.x(), event.y()))
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            # start the drag operation

            allActionsTexts = [action.text() for action in self.actions()]
            if drag.exec_(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:

                point = QtGui.QCursor.pos()
                nextButton = QtWidgets.QApplication.widgetAt(point)

                if isinstance(nextButton, QtWidgets.QToolButton) \
                        and nextButton.actions() \
                        and nextButton.actions()[0] in self.actions():

                    # don't need to move
                    if nextButton == toolButton:
                        return

                    if allActionsTexts.index(toolButton.text()) > allActionsTexts.index(nextButton.text()):

                        # move button to the left
                        self.insertAction(nextButton.actions()[0], toolButton.actions()[0])
                    else:

                        # move button to the right
                        startInd = allActionsTexts.index(toolButton.text())
                        endInd = allActionsTexts.index(nextButton.text())
                        moveleftlist = [action for action in self.actions()]
                        for act in moveleftlist[startInd + 1:endInd + 1]:
                            self.insertAction(toolButton.actions()[0], act)

                    actionIndex = [allActionsTexts.index(act.text()) for act in self.actions() if act.text() in allActionsTexts]
                    self._updateSpectrumViews(actionIndex)
                    for action in self.actions():
                        self._setSizes(action)

                else:
                    event.ignore()
            else:
                event.ignore()

    def event(self, event: QtCore.QEvent) -> bool:
        """
        Use the event handler to process events
        """
        if event.type() == QtCore.QEvent.MouseButtonPress:
            # if event.button() == QtCore.Qt.LeftButton: Can't make it working!!!

            if event.button() == QtCore.Qt.RightButton:
                toolButton = self.childAt(event.pos())
                if toolButton:
                    menu = self._createContextMenu(toolButton)
                    if menu:
                        menu.move(event.globalPos().x(), event.globalPos().y() + 10)
                        menu.exec_()
                else:
                    menu = self._createToolBarContextMenu()
                    if menu:
                        menu.move(event.globalPos().x(), event.globalPos().y() + 10)
                        menu.exec_()

            if event.button() == QtCore.Qt.MiddleButton:
                self._dragButton(event)

        elif event.type() == QtCore.QEvent.Resize:
            self._processToolBarExtension()

        return super(SpectrumToolBar, self).event(event)

    def _toolbarAddSpectrum(self, data):
        """Respond to a new spectrum being added to the spectrumDisplay; add new toolbar Icon
        """
        trigger = data[Notifier.TRIGGER]
        spectrum = data[Notifier.OBJECT]
        self._addSpectrumViewToolButtons(spectrum.spectrumViews)

    def _addSpectrumViewToolButtons(self, spectrumView):
        spectrumDisplay = spectrumView.strip.spectrumDisplay
        if spectrumDisplay.isGrouped:
            return

        with self.spectrumToolBarBlocking():
            spectrumDisplay = spectrumView.strip.spectrumDisplay
            spectrum = spectrumView.spectrum
            apiDataSource = spectrum._wrappedData
            action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
            if not action:
                # add toolbar action (button)
                spectrumName = spectrum.name
                # This is a bug, it changes the name of button and crashes when moving them across
                # if len(spectrumName) > 12:
                #   spectrumName = spectrumName[:12]+'.....'

                actionList = self.actions()
                try:
                    # try and find the spectrumView in the orderedlist - for undo function
                    oldList = spectrumDisplay.spectrumViews
                    oldList = spectrumDisplay.orderedSpectrumViews(oldList)
                    if spectrumView in oldList:
                        oldIndex = oldList.index(spectrumView)
                    else:
                        oldIndex = len(oldList)

                    if actionList and oldIndex < len(actionList):
                        nextAction = actionList[oldIndex]

                        # create a new action and move it to the correct place in the list
                        action = self.addAction(spectrumName)
                        action.setObjectName(spectrum.pid)
                        self.insertAction(nextAction, action)
                    else:
                        action = self.addAction(spectrumName)
                        action.setObjectName(spectrum.pid)

                except Exception as es:
                    action = self.addAction(spectrumName)
                    action.setObjectName(spectrum.pid)

                action.setCheckable(True)
                action.setChecked(True)
                action.setToolTip(spectrum.name)
                widget = self.widgetForAction(action)

                _height1 = max(getFontHeight(size='SMALL') or 12, 12)
                widget.setIconSize(QtCore.QSize(_height1 * 10, _height1))
                # widget.setIconSize(QtCore.QSize(120, 10))
                self._setSizes(action)
                # WHY _wrappedData and not spectrumView?
                widget.spectrumView = spectrumView._wrappedData
                action.spectrumViewPid = spectrumView.pid

                spectrumDisplay.spectrumActionDict[apiDataSource] = action
                # The following call sets the icon colours:
                _spectrumViewHasChanged({Notifier.OBJECT: spectrumView})

        # if spectrumDisplay.is1D:
        #     action.toggled.connect(spectrumView.plot.setVisible)
        action.toggled.connect(spectrumView.setVisible)
        setWidgetFont(action, size='SMALL')
        return action

    def _setSizes(self, action):

        widget = self.widgetForAction(action)
        _height1 = max(getFontHeight(size='SMALL') or 12, 12)
        _height2 = max(getFontHeight(size='VLARGE') or 30, 30)
        widget.setIconSize(QtCore.QSize(_height1 * 10, _height1))
        widget.setFixedSize(_height2 * 2.5, _height2)
        # widget.setIconSize(QtCore.QSize(120, 10))
        # widget.setFixedSize(75, 30)

    def _toolbarChange(self, spectrumViews):

        with self.spectrumToolBarBlocking():
            actionList = self.actions()
            # self.clear()
            for specView in spectrumViews:

                # self._addSpectrumViewToolButtons(specView)
                spectrum = specView.spectrum
                spectrumName = spectrum.name
                # if len(spectrumName) > 12:
                #     spectrumName = spectrumName[:12] + '.....'

                for act in actionList:
                    if act.text() == spectrumName:
                        self.addAction(act)

                        widget = self.widgetForAction(act)
                        _height1 = max(getFontHeight(size='SMALL') or 12, 12)
                        widget.setIconSize(QtCore.QSize(_height1 * 10, _height1))
                        # widget.setIconSize(QtCore.QSize(120, 10))
                        self._setSizes(act)
        self.update()

    def _processToolBarExtension(self):
        # paint event sets visibility of actions...
        return

        # kept for the minute, but can be removed when the toolbar is changed to a tab bar

        # self.removeChild(self._extButton)
        # return
        #
        # # can hide the widgets inside a temporary frame if needed
        # self._extButton.setParent(None)
        # return
        #
        # if self._extButton.isVisible():
        #     # toolbar does not fit, so need to process the buttons
        #
        #     actionList = self.actions()
        #     if len(actionList) > 2:
        #         for action in actionList[:2]:
        #             widget = self.widgetForAction(action)
        #             # widget.setParent(None)
