"""Module Documentation here

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
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
from ccpn.ui._implementation.PeakListView import PeakListView
from ccpn.ui._implementation.IntegralListView import IntegralListView
from ccpn.ui._implementation.MultipletListView import MultipletListView
from ccpn.core.PeakList import PeakList
from ccpn.core.IntegralList import IntegralList
from ccpn.core.MultipletList import MultipletList
from ccpn.ui.gui.lib.GuiSpectrumView import _spectrumViewHasChanged
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup


class SpectrumToolBar(ToolBar):

    def __init__(self, parent=None, widget=None, **kwds):

        super().__init__(parent=parent, **kwds)
        self.widget = widget
        self._parent = parent
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.eventFilter = self._eventFilter
        self.installEventFilter(self)
        self.setMouseTracking(True)
        self._spectrumToolBarBlockingLevel = 0

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
                    smenu.addAction('Show All', partial(self._setVisibleAllFromList, True, smenu, views))
                    smenu.addAction('Hide All', partial(self._setVisibleAllFromList, False, smenu, views))
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

    def _createContextMenu(self, button: QtWidgets.QToolButton):
        """
        Creates a context menu containing a command to delete the spectrum from the display and its
        button from the toolbar.
        """
        from collections import OrderedDict

        if not button:
            return None
        if len(button.actions()) < 1:
            return None

        contextMenu = Menu('', self, isFloatWidget=True)
        self._addSubMenusToContext(contextMenu, button)

        contextMenu.addSeparator()
        contextMenu.addAction('Jump on SideBar', partial(self._jumpOnSideBar, button))
        contextMenu.addAction('Properties...', partial(self._showSpectrumProperties, button))
        contextMenu.addAction('Remove Spectrum', partial(self._removeSpectrum, button))
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

    # old to be deleted
    # def _createContextMenuOld(self, button:QtWidgets.QToolButton):
    #   """
    #   Creates a context menu containing a command to delete the spectrum from the display and its
    #   button from the toolbar.
    #   """
    #   if not button:
    #     return None
    #   contextMenu = Menu('', self, isFloatWidget=True)
    #   plMenu =  contextMenu.addMenu('PeakList')
    #   ilMenu =  contextMenu.addMenu('IntegralList')
    #   mlMenu =  contextMenu.addMenu('MultipletList')
    #
    #   peakListViews = self.widget.peakListViews
    #   integralListViews = self.widget.integralListViews
    #   multipletListViews = self.widget.multipletListViews
    #
    #   action = button.actions()[0]
    #   # keys = [key for key, value in self.widget.spectrumActionDict.items() if value is action]
    #   # if not keys: # if you click on >> button which shows more spectra
    #   #   return None
    #   # key = keys[0]
    #
    #   plMenu.setEnabled(len(peakListViews)>0)
    #   plMenu.addAction('Show All', partial(self._setVisibleAllFromList,True, plMenu, peakListViews))
    #   plMenu.addAction('Hide All', partial(self._setVisibleAllFromList,False, plMenu, peakListViews))
    #   plMenu.addSeparator()
    #   for peakListView in peakListViews:
    #     # if peakListView.spectrumView._apiDataSource == key:
    #       if peakListView.peakList:
    #         action = plMenu.addAction(peakListView.peakList.pid)
    #         action.setCheckable(True)
    #         if peakListView.isVisible():
    #           action.setChecked(True)
    #         # else:
    #         #   allPlAction.setChecked(False)
    #         action.toggled.connect(peakListView.setVisible)
    #         # TODO:ED check this is okay for each spectrum
    #         action.toggled.connect(partial(self._updateVisiblePeakLists, peakListView.spectrumView))
    #
    #
    #   ilMenu.setEnabled(len(integralListViews)>0)
    #   ilMenu.addAction('Show All', partial(self._setVisibleAllFromList,True, ilMenu, integralListViews))
    #   ilMenu.addAction('Hide All', partial(self._setVisibleAllFromList,False, ilMenu, integralListViews))
    #   ilMenu.addSeparator()
    #   for integralListView in integralListViews:
    #     # if integralListView.spectrumView._apiDataSource == key:
    #       if integralListView.integralList:
    #         action = ilMenu.addAction(integralListView.integralList.pid)
    #         action.setCheckable(True)
    #         if integralListView.isVisible():
    #           action.setChecked(True)
    #         # else:
    #         #   allPlAction.setChecked(False)
    #         action.toggled.connect(integralListView.setVisible)
    #
    #         # TODO:ED check this is okay for each spectrum
    #         action.toggled.connect(partial(self._updateVisibleIntegralLists, integralListView.spectrumView))
    #
    #   mlMenu.setEnabled(len(multipletListViews)>0)
    #   mlMenu.addAction('Show All', partial(self._setVisibleAllFromList,True, mlMenu, multipletListViews))
    #   mlMenu.addAction('Hide All', partial(self._setVisibleAllFromList,False, mlMenu, multipletListViews))
    #   mlMenu.addSeparator()
    #   for multipletListView in multipletListViews:
    #     # if multipletListView.spectrumView._apiDataSource == key:
    #       if multipletListView.multipletList:
    #         action = mlMenu.addAction(multipletListView.multipletList.pid)
    #         action.setCheckable(True)
    #         if multipletListView.isVisible():
    #           action.setChecked(True)
    #         # else:
    #         #   allPlAction.setChecked(False)
    #         action.toggled.connect(multipletListView.setVisible)
    #
    #         # TODO:ED check this is okay for each spectrum
    #         action.toggled.connect(partial(self._updateVisibleMultipletLists, multipletListView.spectrumView))
    #
    #   contextMenu.addSeparator()
    #   contextMenu.addAction('Remove Spectrum', partial(self._removeSpectrum, button))
    #   return contextMenu

    def _updateGl(self, ):
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()

    # Triplicated Code?
    # def _updateVisiblePeakLists(self, spectrumView=None, visible=True):
    #   from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
    #   GLSignals = GLNotifier(parent=self)
    #   GLSignals.emitPaintEvent()
    #
    # def _updateVisibleIntegralLists(self, spectrumView=None, visible=True):
    #   from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
    #   GLSignals = GLNotifier(parent=self)
    #   GLSignals.emitPaintEvent()
    #
    # def _updateVisibleMultipletLists(self, spectrumView=None, visible=True):
    #   from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
    #   GLSignals = GLNotifier(parent=self)
    #   GLSignals.emitPaintEvent()

    def _getSpectrumViewFromButton(self, button):
        spvs = []
        key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]

        for spectrumView in self.widget.spectrumViews:
            if spectrumView._apiDataSource == key:
                spvs.append(spectrumView)
        if len(spvs) == 1:
            return spvs[0]

    # def _allPeakLists(self, contextMenu, button):
    #   key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    #   for peakListView in self.widget.peakListViews:
    #     if peakListView.spectrumView._apiDataSource == key:
    #       for action in contextMenu.actions():
    #         if action is not self.sender():
    #           if not action.isChecked():
    #             action.setChecked(True)
    #             action.toggled.connect(peakListView.setVisible)
    #   self._updateVisiblePeakLists()
    #
    # def _noPeakLists(self, contextMenu, button):
    #   key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    #   for peakListView in self.widget.peakListViews:
    #     if peakListView.spectrumView._apiDataSource == key:
    #       for action in contextMenu.actions():
    #         if action is not self.sender():
    #           if action.isChecked():
    #             action.setChecked(False)
    #             action.toggled.connect(peakListView.setVisible)
    #   self._updateVisiblePeakLists()

    def _setVisibleAllFromList(self, abool, menu, views):
        '''

        :param abool: T or F
        :param menu:
        :param views: any of Views obj _pluralLinkName
        :return:
        '''
        if views:
            for view in views:
                view.setVisible(abool)
                for action in menu.actions():
                    if action.text() == view.pid:
                        action.setChecked(abool)

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

    def _eventFilter(self, obj, event):
        """
        Replace all the events with a single filter process

        """

        if event.type() == QtCore.QEvent.MouseButtonPress:
            # if event.button() == QtCore.Qt.LeftButton: Can't make it working!!!

            if event.button() == QtCore.Qt.RightButton:
                toolButton = self.childAt(event.pos())

                menu = self._createContextMenu(toolButton)
                if menu:
                    menu.move(event.globalPos().x(), event.globalPos().y() + 10)
                    menu.exec()
            if event.button() == QtCore.Qt.MiddleButton:
                self._dragButton(event)

        return super(SpectrumToolBar, self).eventFilter(obj, event)  # do the rest

    def _toolbarAddSpectrum(self, data):
        """Respond to a new spectrum being added to the spectrumDisplay; add new toolbar Icon
        """
        trigger = data[Notifier.TRIGGER]
        spectrum = data[Notifier.OBJECT]
        self._addSpectrumViewToolButtons(spectrum.spectrumViews)

    def _addSpectrumViewToolButtons(self, spectrumView):

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
                widget.setIconSize(QtCore.QSize(120, 10))
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

    def _setSizes(self, action):

        widget = self.widgetForAction(action)
        widget.setIconSize(QtCore.QSize(120, 10))
        widget.setFixedSize(75, 30)

    def _toolbarChange(self, spectrumViews):

        with self.spectrumToolBarBlocking():
            actionList = self.actions()
            # self.clear()
            for specView in spectrumViews:

                # self._addSpectrumViewToolButtons(specView)
                spectrum = specView.spectrum
                spectrumName = spectrum.name
                if len(spectrumName) > 12:
                    spectrumName = spectrumName[:12] + '.....'

                for act in actionList:
                    if act.text() == spectrumName:
                        self.addAction(act)

                        widget = self.widgetForAction(act)
                        widget.setIconSize(QtCore.QSize(120, 10))
                        self._setSizes(act)
        self.update()
