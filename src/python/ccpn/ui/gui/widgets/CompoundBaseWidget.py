"""
Base class for compound widgets
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-10-31 18:46:56 +0000 (Mon, October 31, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import contextlib
from PyQt5 import QtCore
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.Base import SignalBlocking


NULL = object()


class CompoundBaseWidget(Frame, SignalBlocking):
    """
    Base widget for Compound classes; inherits from Frame (and hence Base)
    Implements the addNotifier and deleteNotifiers methods
    """
    def __init__(self, parent, layoutDict, orientation, showBorder, **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param layoutDict: dictionary of orientation, griddingList key,value pairs; griddingList should
                           contain a (x,y) tuple for each widget to be added later-on
        :param orientation: orientation keyword
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """
        super().__init__(parent=parent, showBorder=showBorder, setLayout=True, **kwds)

        if orientation not in layoutDict:
            raise RuntimeError('Invalid parameter "orientation" (%s)' % orientation)
        self._orientation = orientation
        self._gridding = layoutDict[orientation]  # list of grid tuples for all successive widgets
        self._widgets = []  # list of all the widgets; use addWidget to add using the layoutDict
        self._blockingLevel = 0

        self._notifiers = []

    def _addWidget(self, widget):
        """Add widget, using the layout as defined previously by layoutDict and orientation"""
        if len(self._gridding) < len(self._widgets) + 1:
            raise RuntimeError('Cannot add widget; invalid gridding')
        gx, gy = self._gridding[len(self._widgets)]
        self._widgets.append(widget)
        self.layout().addWidget(widget, gx, gy)

    def setMinimumWidths(self, minimumWidths):
        """Set minimumwidths of widgets"""
        if len(minimumWidths) < len(self._widgets):
            raise RuntimeError('Not enough values to set minimum widths of all widgets')
        for i, width in enumerate(minimumWidths[:len(self._widgets)]):
            if width is not None:
                self._widgets[i].setMinimumWidth(width)

    def setMaximumWidths(self, maximumWidths):
        """Set maximumWidths of widgets"""
        if len(maximumWidths) < len(self._widgets):
            raise RuntimeError('Not enough values to set maximum widths of all widgets')
        for i, width in enumerate(maximumWidths[:len(self._widgets)]):
            if width is not None:
                self._widgets[i].setMaximumWidth(width)

    def setFixedWidths(self, fixedWidths):
        """Set maximumWidths of widgets"""
        if len(fixedWidths) < len(self._widgets):
            raise RuntimeError('Not enough values to set fixed widths of all widgets')
        for i, width in enumerate(fixedWidths[:len(self._widgets)]):
            if width is not None:
                self._widgets[i].setFixedWidth(width)

    def setFixedHeights(self, fixedHeights):
        """Set fixed heights of widgets"""
        if len(fixedHeights) < len(self._widgets):
            raise RuntimeError('Not enough values to set fixed heights of all widgets')
        for i, height in enumerate(fixedHeights[:len(self._widgets)]):
            if height is not None:
                self._widgets[i].setFixedHeight(height)

    def addObjectNotifier(self, theObject, triggers, targetName, func, *args, **kwds):
        """
        Add and store a notifier with widget;

        :param theObject: A valid V3 core or current object
        :param triggers: any of the triggers, as defined in Notifier class
        :param targetName: a valid target for theObject, as defined in the Notifier class
        :param func: callback function on triggering
        :param args: optional arguments to func
        :param kwds: optional keyword arguments to func
        :return: Notifier instance
        """
        notifier = Notifier(theObject, triggers, targetName, func, *args, **kwds)
        self.addNotifier(notifier)
        return notifier

    def addNotifier(self, notifier):
        """add a notifier to the widget"""
        self._notifiers.append(notifier)

    def deleteNotifiers(self):
        """Delete all notifiers associated with the widget"""
        while len(self._notifiers) > 0:
            if notifier := self._notifiers.pop():
                notifier.unRegister()
                del (notifier)

    def __del__(self):
        # The project and all its things are already disassembled when closing the program;
        # hence, the de-registering of notifiers fails and needs to be caught
        with contextlib.suppress(Exception):
            self.deleteNotifiers()

    def setPreSelect(self, callBack=None):
        """
        Add a user callback to the pulldown that fires on a mouse click.
        facilitates populating the pulldown list just before it opens
        :param callBack: method to call on click
        """
        if callBack:
            self.pulldownList.installEventFilter(self)
            self._preSelectCallBack = callBack

    def eventFilter(self, target, event):
        """
        call the user callback when the pulldown has been clicked
        """
        if target == self.pulldownList and event.type() == QtCore.QEvent.MouseButtonPress:
            self._preSelectCallBack()
        return False
