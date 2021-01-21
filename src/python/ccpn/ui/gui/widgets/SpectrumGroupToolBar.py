"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-01-21 18:46:44 +0000 (Thu, January 21, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui
from functools import partial
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Font import setWidgetFont, getFontHeight
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib import Pid
from ccpn.util.OrderedSet import OrderedSet


class SpectrumGroupToolBar(ToolBar):
    def __init__(self, parent=None, spectrumDisplay=None, **kwds):
        super().__init__(parent=parent, **kwds)
        self.spectrumDisplay = spectrumDisplay
        self._project = self.spectrumDisplay.project
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

        # self._spectrumGroups = []

    # def _getSpectrumGroups(self):
    #     from ccpn.ui.gui.lib.GuiSpectrumDisplay import SPECTRUMGROUPS, SPECTRUMGROUPLIST
    #
    #     _spectrumGroups = AbstractWrapperObject.getParameter(self.spectrumDisplay,
    #                                                          SPECTRUMGROUPS, SPECTRUMGROUPLIST)
    #     if _spectrumGroups is not None:
    #         return _spectrumGroups
    #
    #     AbstractWrapperObject.setParameter(self.spectrumDisplay,
    #                                        SPECTRUMGROUPS, SPECTRUMGROUPLIST, ())
    #     return ()
    #
    # def _setSpectrumGroups(self, groups):
    #     from ccpn.ui.gui.lib.GuiSpectrumDisplay import SPECTRUMGROUPS, SPECTRUMGROUPLIST
    #
    #     AbstractWrapperObject.setParameter(self.spectrumDisplay,
    #                                        SPECTRUMGROUPS, SPECTRUMGROUPLIST, groups)

    def _addAction(self, spectrumGroup, oldAction=None):

        _spectrumGroups = self.spectrumDisplay._getSpectrumGroups()

        if spectrumGroup.pid not in _spectrumGroups:
            # _spectrumGroups.append(spectrumGroup)
            _spectrumGroups += (spectrumGroup.pid,)

            if oldAction:
                self.addAction(oldAction)
                oldAction.setEnabled(True)
            else:
                action = self.addAction(spectrumGroup.pid, partial(self._toggleSpectrumGroup, spectrumGroup))
                action.setCheckable(True)
                action.setChecked(True)
                action.setText(spectrumGroup.pid)
                setWidgetFont(action, size='SMALL')

                action.setToolTip(spectrumGroup.name)
                action.setObjectName(spectrumGroup.pid)
                self._setupButton(action, spectrumGroup)

            self.spectrumDisplay._setSpectrumGroups(_spectrumGroups)

    def _removeAction(self, action, spectrumGroup):
        _spectrumGroups = OrderedSet(self.spectrumDisplay._getSpectrumGroups())
        if spectrumGroup.pid in _spectrumGroups:
            _spectrumGroups = _spectrumGroups - {spectrumGroup.pid,}

            self.removeAction(action)
            action.setEnabled(False)

            self.spectrumDisplay._setSpectrumGroups(list(_spectrumGroups))

    def _forceAddAction(self, spectrumGroup):

        action = self.addAction(spectrumGroup.pid, partial(self._toggleSpectrumGroup, spectrumGroup))
        action.setCheckable(True)
        action.setChecked(True)
        action.setText(spectrumGroup.pid)
        setWidgetFont(action, size='SMALL')

        action.setToolTip(spectrumGroup.name)
        action.setObjectName(spectrumGroup.pid)
        self._setupButton(action, spectrumGroup)

    def _setupButton(self, action, spectrumGroup):
        widget = self.widgetForAction(action)
        _height1 = max(getFontHeight(size='SMALL') or 12, 12)
        _height2 = max(getFontHeight(size='VLARGE') or 30, 30)
        widget.setIconSize(QtCore.QSize(_height1 * 10, _height1))
        widget.setFixedSize(_height2 * 2.5, _height2)
        # widget.setIconSize(QtCore.QSize(120, 10))
        # widget.setFixedSize(75, 30)

        from ccpn.ui.gui.lib.GuiSpectrumView import _addActionIcon
        _addActionIcon(action, spectrumGroup, self.spectrumDisplay)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """
        Re-implementation of the Toolbar mouse event so a right mouse context menu can be raised.
        """
        if event.button() == QtCore.Qt.RightButton:
            button = self.childAt(event.pos())
            if button:
                sg = self._project.getByPid(button.text())
                if sg is not None:
                    if len(button.actions()) > 0:
                        menu = self._setupContextMenu(button.actions()[0], sg)
                        if menu:
                            menu.move(event.globalPos().x(), event.globalPos().y() + 10)
                            menu.exec()

    def _setupContextMenu(self, action, spectrumGroup):

        popMenu = Menu('', self)
        removeAction = popMenu.addAction('Remove', partial(self._deleteSpectrumGroup, action, spectrumGroup))
        peakListAction = popMenu.addAction('PeakLists')
        peakListAction.setCheckable(True)
        peakListAction.toggled.connect(partial(self._showHidePeakListView, spectrumGroup))
        return popMenu

    def _getStrip(self):
        strips = self.spectrumDisplay.strips
        if len(strips) > 0:
            return strips[0]

    def _toggleSpectrumGroup(self, spectrumGroup):
        spectrumGroupPeakLists = [spectrum.peakLists[0] for spectrum in spectrumGroup.spectra]
        peakListViews = [peakListView for peakListView in self.spectrumDisplay.peakListViews]

        strip = self._getStrip()
        if strip is not None:
            spectrumViews = [spectrumView for spectrumView in strip.spectrumViews
                             if spectrumView.spectrum in spectrumGroup.spectra]

            widget = self.widgetForAction(self.sender())
            if widget.isChecked():
                for spectrumView in spectrumViews:
                    spectrumView.setVisible(True)
                    if hasattr(spectrumView, 'plot'):
                        spectrumView.plot.show()
                    self._showPeakList(spectrumGroupPeakLists, peakListViews)
            else:
                for spectrumView in spectrumViews:
                    spectrumView.setVisible(False)
                    if hasattr(spectrumView, 'plot'):
                        spectrumView.plot.hide()
                self._hidePeakLists(spectrumGroupPeakLists, peakListViews)

    def _deleteSpectrumGroup(self, action, spectrumGroup):
        strip = self._getStrip()
        if strip is not None:
            from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, undoStackBlocking

            with undoBlockWithoutSideBar():

                _spectra = [sp for group in [strip.project.getByPid(gr) for gr in strip.spectrumDisplay._getSpectrumGroups() if strip.project.getByPid(gr)]
                            for sp in group.spectra
                            if not (sp.isDeleted or sp._flaggedForDelete)]

                self._removeAction(action, spectrumGroup)

                with undoStackBlocking() as addUndoItem:
                    # need to undo the removal of action
                    addUndoItem(undo=strip._CcpnGLWidget.updateVisibleSpectrumViews,
                                redo=partial(self._removeAction, action, spectrumGroup))

                for spectrumView in strip.spectrumViews:
                    # NOTE:ED - can only delete those that are not duplicated
                    #           need count in all spectrumDisplay._getSpectrumGroups
                    if spectrumView.spectrum in spectrumGroup.spectra and _spectra.count(spectrumView.spectrum) == 1:
                        spectrumView.delete()

                with undoStackBlocking() as addUndoItem:
                    # keep a handle to the action for reinserting
                    addUndoItem(undo=partial(self._addAction, spectrumGroup, oldAction=action),
                                redo=strip._CcpnGLWidget.updateVisibleSpectrumViews)

                # if spectrumGroup in self._spectrumGroups:
                #     self._spectrumGroups.remove(spectrumGroup)
                # if len(strip.spectra) == 0:
                #     self.spectrumDisplay._closeModule()

    def _spectrumGroupRename(self, data):
        """Rename the spectrumGroup in the toolbar from a notifier callback
        """
        spectrumGroup = data[Notifier.OBJECT]
        trigger = data[Notifier.TRIGGER]

        if spectrumGroup and trigger in [Notifier.RENAME]:
            oldPid = Pid.Pid(data[Notifier.OLDPID])

            validActions = [action for action in self.actions() if action.text() == oldPid]
            for action in validActions:
                action.setText(spectrumGroup.pid)
                action.setToolTip(spectrumGroup.name)
                action.setObjectName(spectrumGroup.pid)
                # setWidgetFont(action, size='SMALL')

    # LM: Fixme the code for peakList views below needs refactoring

    def _showHidePeakListView(self, spectrumGroup):
        for plv in self._getPeakListViews(spectrumGroup):
            if plv is not None:
                if plv.isVisible():
                    plv.setVisible(False)
                else:
                    plv.setVisible(True)

    def _hidePeakLists(self, spectrumGroupPeakLists, peakListViews):
        for peakList in spectrumGroupPeakLists:
            if self.spectrumDisplay is not None:
                for peakListView in peakListViews:
                    if peakList == peakListView.peakList:
                        peakListView.setVisible(False)

    def _showPeakList(self, spectrumGroupPeakLists, peakListViews):
        for peakList in spectrumGroupPeakLists:
            if self.spectrumDisplay is not None:
                for peakListView in peakListViews:
                    if peakList == peakListView.peakList:
                        peakListView.setVisible(True)

    def _getPeakListViews(self, spectrumGroup):
        spectrumGroupPeakLists = [peakList for spectrum in spectrumGroup.spectra for peakList in spectrum.peakLists]
        return [plv for peakList in spectrumGroupPeakLists for plv in peakList.peakListViews]


def _spectrumGroupViewHasChanged(data):
    self = data[Notifier.OBJECT]

    if self.isDeleted:
        return

    from ccpn.ui.gui.lib.GuiSpectrumView import _addActionIcon
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    specDisplays = [sd for sd in self.project.spectrumDisplays if sd and sd.isGrouped and not (sd.isDeleted or sd._flaggedForDelete)]

    for specDisplay in specDisplays:
        _actions = [action for action in specDisplay.spectrumGroupToolBar.actions() if action.text() == self.pid]

        for action in _actions:
            # add spectrum action for grouped action
            _addActionIcon(action, self, specDisplay)

    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=self)

    self.buildContoursOnly = True

    # repaint
    GLSignals.emitPaintEvent()
