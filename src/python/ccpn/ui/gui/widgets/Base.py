"""
Base class for gridding, optionally setting up size policies and layout,
optionally inserting itself into parent using keyword, grid, gridspan, hAlign, vAlign

The proper way for adding widgets explicitly is:
widget.getLayout().addWidget(row, col, [rowspan, [colspan])
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
__dateModified__ = "$dateModified: 2021-03-01 11:22:52 +0000 (Mon, March 01, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from contextlib import contextmanager
from PyQt5 import QtWidgets, QtCore
from pyqtgraph.dockarea import Dock
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.Font import setWidgetFont
from ccpn.util.AttrDict import AttrDict


HALIGN_DICT = {
    'left'  : QtCore.Qt.AlignLeft,
    'right' : QtCore.Qt.AlignRight,
    'center': QtCore.Qt.AlignHCenter,
    'centre': QtCore.Qt.AlignHCenter,
    'l'     : QtCore.Qt.AlignLeft,
    'r'     : QtCore.Qt.AlignRight,
    'c'     : QtCore.Qt.AlignHCenter,
    }

VALIGN_DICT = {
    'top'   : QtCore.Qt.AlignTop,
    'bottom': QtCore.Qt.AlignBottom,
    'center': QtCore.Qt.AlignVCenter,
    'centre': QtCore.Qt.AlignVCenter,
    't'     : QtCore.Qt.AlignTop,
    'b'     : QtCore.Qt.AlignBottom,
    'c'     : QtCore.Qt.AlignVCenter,
    }

POLICY_DICT = {
    'fixed'           : QtWidgets.QSizePolicy.Fixed,
    'minimal'         : QtWidgets.QSizePolicy.Minimum,
    'minimum'         : QtWidgets.QSizePolicy.Minimum,
    'maximum'         : QtWidgets.QSizePolicy.Maximum,
    'preferred'       : QtWidgets.QSizePolicy.Preferred,
    'expanding'       : QtWidgets.QSizePolicy.Expanding,
    'minimumExpanding': QtWidgets.QSizePolicy.MinimumExpanding,
    'ignored'         : QtWidgets.QSizePolicy.Ignored,
    }

FOCUS_DICT = {
    'no'    : QtCore.Qt.NoFocus,
    'tab'   : QtCore.Qt.TabFocus,
    'click' : QtCore.Qt.ClickFocus,
    'string': QtCore.Qt.StrongFocus
    }


class SignalBlocking():
    """
    Class to add widget blocking methods to a subclass.
    Blocks signals from nested widgets.

    Blocking is applied by a contextManager
    """
    _widgetSignalBlockingLevel = 0

    @property
    def widgetIsBlocked(self):
        """True if widget is blocked, i.e., blocking level > 0
        """
        return self._widgetSignalBlockingLevel > 0

    def _blockEvents(self, root, widgetState, recursive=True, additionalWidgets=None):
        """Block all updates/signals in the widget and children.
        """
        # block all signals on first entry, each instance stores it's own blocking level
        if self._widgetSignalBlockingLevel == 0:

            # 'root' must be a widget, store previous updatesEnabled state
            widgetState.root = root
            widgetState.widgetUpdatesEnabled = root.updatesEnabled()
            root.setUpdatesEnabled(False)

            # create blocker objects to block child widget signals
            widgetState.signalBlockers = [QtCore.QSignalBlocker(root)]
            if recursive:
                # add all the child widgets
                widgetState.signalBlockers += [QtCore.QSignalBlocker(_child) for _child in root.findChildren(QtWidgets.QWidget)]
            if additionalWidgets:
                # add any other widgets
                widgetState.signalBlockers += [QtCore.QSignalBlocker(_child) for _child in additionalWidgets]

        self._widgetSignalBlockingLevel += 1

    def _unblockEvents(self, root, widgetState):
        """Unblock all updates/signals in the widget and children.
        """
        if self._widgetSignalBlockingLevel > 0:
            self._widgetSignalBlockingLevel -= 1

            # unblock all signals on last exit
            if self._widgetSignalBlockingLevel == 0:
                # remove blockers to release widgets
                widgetState.signalBlockers = None

                # restore updatesEnabled state
                root.setUpdatesEnabled(widgetState.widgetUpdatesEnabled)

        else:
            raise RuntimeError('Error: Widget signal blocking already at 0')

    @contextmanager
    def blockWidgetSignals(self, root=None, recursive=True, additionalWidgets=None):
        """Block all signals for the widget.

        root is the widget to be blocked, if no widget specified then self is assumed.
        If recursive=False then only the specified widget is blocked.

        Updates are also blocked for the widget, this should automatically block updates for all nested widgets.

        :param root: widget to be blocked, defaults to self
        :param recursive: bool, defaults to True
        """
        # local widgetState is kept private
        _widgetState = AttrDict()
        _root = root or self
        self._blockEvents(_root, _widgetState, recursive=recursive, additionalWidgets=additionalWidgets)
        try:
            yield  # yield control to the calling process

        except Exception as es:
            raise es
        finally:
            self._unblockEvents(_root, _widgetState)

    @staticmethod
    def _removeWidget(widget, removeTopWidget=False):
        """Destroy a widget and all it's contents
        """

        def deleteItems(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
                        widget.setParent(None)
                        del widget

        if widget and hasattr(widget, 'getLayout'):
            deleteItems(widget.getLayout())
            if removeTopWidget:
                widget.setVisible(False)
                widget.setParent(None)
                del widget

    @staticmethod
    def _setMinimumWidgetSize(widget):
        """Set the minimum widget size of content widgets
        """

        def _setWidgetSize(layout):
            if layout is not None:
                for count in range(layout.count()):
                    item = layout.itemAt(count)
                    widget = item.widget()
                    if widget is not None:
                        hint = widget.sizeHint()
                        if hint.isValid():
                            widget.setMinimumSize(hint)

        if widget and hasattr(widget, 'getLayout'):
            _setWidgetSize(widget.getLayout())
            hint = widget.sizeHint()
            if hint.isValid():
                widget.setMinimumSize(hint)


class Base(DropBase, SignalBlocking):

    # Base._init(**kwds) should be called from every widget
    # We don't use __init__ as it messes up the super() methods resolution and the
    # destroy signal when closing the windows
    def _init(self, isFloatWidget=False,
              tipText=None,
              bgColor=None, fgColor=None,
              enabled=None,

              # keywords related to optional layout
              setLayout=False,
              hPolicy=None, vPolicy=None,
              margins=(0, 0, 0, 0), spacing=(2, 2),

              # keywords for adding to parent
              grid=(None, None), gridSpan=(1, 1), stretch=(0, 0),
              hAlign=None, vAlign=None,
              hidden=False,

              # keywords related to droppable properties
              acceptDrops=False,

              # other keywords
              focusPolicy=None,
              objectName=None
              ):
        """

        :param tipText:  add tiptext to widget
        :param grid:     insert widget at (row,col) of parent layout (if available)
        :param hidden:   hide widget upon creation
        :param gridSpan: extend widget over (rows,cols); default (1,1)
        :param stretch:  stretch factor (row,col) of widget; default (0, 0)
        :param hAlign:   horizontal alignment: (l, left, r, right, c, center, centre)
        :param vAlign:   vertical alignment: (t, top, b, bottom, c, center, centre)
        :param hPolicy:  horizontal policy of widget: (fixed, minimum, maximum, preferred, expanding, minimumExpanding, ignored)
        :param vPolicy:  vertical policy of widget: ( fixed, minimum, maximum, preferred, expanding, minimumExpanding, ignored)
        :param bgColor:  background RGB colour tuple; depreciated: use styleSheet routines instead
        :param fgColor:  foreground RGB colour tuple; depreciated: use styleSheet routines instead
        :param isFloatWidget: indicates widget to be floating
        """

        # print('DEBUG Base %r: acceptDrops=%s, setLayout=%s' % (self, acceptDrops, setLayout))

        # define the 'droppable' methods
        # DropBase._init(self, acceptDrops=acceptDrops)
        DropBase._init(self, acceptDrops=acceptDrops)
        # super().__init__(acceptDrops=acceptDrops)

        # Tool tips
        if tipText:
            self.setToolTip(tipText)

        if isinstance(self, Dock):
            return

        if hPolicy or vPolicy:
            hPolicy = POLICY_DICT.get(hPolicy, 0)
            vPolicy = POLICY_DICT.get(vPolicy, 0)
            self.setSizePolicy(hPolicy, vPolicy)

        # Setup colour overrides (styles used primarily)
        ##3 depreciated
        if bgColor:
            self.setAutoFillBackground(True)
            #rgb = QtGui.QColor(bgColor).getRgb()[:3]
            self.setStyleSheet("background-color: rgb(%d, %d, %d);" % bgColor)

        if fgColor:
            self.setAutoFillBackground(True)
            #rgb = QtGui.QColor(fgColor).getRgb()[:3]
            self.setStyleSheet("foreground-color: rgb(%d, %d, %d);" % fgColor)

        if setLayout:
            self.setGridLayout(margins=margins, spacing=spacing)
            self.setStyleSheet('padding: 0px;')

        if enabled is not None:
            self.setEnabled(enabled)

        # add the widget to parent if it is not a float widget and either grid[0] (horizontal)
        # or grid[1] (vertical) are defined
        self._col = grid[0]
        self._row = grid[1]
        self._grid = grid
        self.__hidden = hidden
        if not isFloatWidget and (grid[0] is not None or grid[1] is not None):
            self._addToParent(grid=grid, gridSpan=gridSpan, stretch=stretch,
                              hAlign=hAlign, vAlign=vAlign)

        # set the focus policy for the widget, if not valid, will default to strongFocus
        if focusPolicy:
            self.setFocusPolicy(FOCUS_DICT.get(focusPolicy, QtCore.Qt.StrongFocus))

        # set the object name of the widget to give unique name for restoring widgets
        if objectName:
            self.setObjectName(objectName)

        setWidgetFont(self, )

        # connect destruction of widget to onDestroyed method,
        # which subsequently can be subclassed
        self.destroyed.connect(partial(self.onDestroyed, self))

    @staticmethod  # has to be a static method
    def onDestroyed(widget):
        # print("DEBUG on destroyed:", widget)
        pass

    def setGridLayout(self, margins=(0, 0, 0, 0), spacing=(0, 0)):
        """Add a QGridlayout to self
        """
        layout = self._getLayout(self)  # use _getLayout as we do not want any message; if there is no
        # layout, we are going to add one
        if layout is None:
            layout = QtWidgets.QGridLayout(self)
            layout.setContentsMargins(*margins)
            layout.setHorizontalSpacing(spacing[0])
            layout.setVerticalSpacing(spacing[1])
            self.setLayout(layout)
        else:
            getLogger().warning('Widget %s already has a layout!' % self)

    def getLayout(self):
        """return the layout of self
        """
        layout = self._getLayout(self)
        if layout is None:
            getLogger().warning('Unable to query layout of %s' % self)
        return layout

    @staticmethod
    def _getLayout(widget):
        """return the layout of widget
        """
        layout = None
        try:
            layout = QtWidgets.QWidget.layout(widget)
        except:
            pass
        return layout

    def _addToParent(self, grid, gridSpan, stretch, hAlign, vAlign):
        """Add widget to parent of self (if can be obtained)
        """
        parent = self.parent() if hasattr(self, 'parent') else None  # Not all Qt objects have a parent
        if parent is None:
            getLogger().warning('No parent: Cannot add widget %s (grid=%s)' % (self, grid))
            return

        # have to use _getLayout() functionality as not all widget descend from Base;
        layout = self._getLayout(parent)
        if layout is None:
            getLogger().warning('No layout for parent widget %s of %s' % (parent, self))
            return

        if isinstance(layout, QtWidgets.QGridLayout):
            row, col = self._getRowCol(layout, grid)
            rowStr, colStr = stretch
            layout.setRowStretch(row, rowStr)
            layout.setColumnStretch(col, colStr)

            rowSpan, colSpan = gridSpan
            hAlign = HALIGN_DICT.get(hAlign, 0)

            vAlign = VALIGN_DICT.get(vAlign, 0)
            align = hAlign | vAlign
            self._col = col
            self._row = row
            layout.addWidget(self, row, col, rowSpan, colSpan, QtCore.Qt.Alignment(align))
            if self.__hidden:
                self.hide()

    @staticmethod
    def _getRowCol(layout, grid):
        """Returns (row, col) tuple from layout, using grid or using current rowCount
        """
        if layout is None:
            getLogger().warning('Layout is None, cannot get (row, col) tuple')
            return (0, 0)
        if grid:
            row, col = grid
            if row is None:
                row = 0
            if col is None:
                col = 0
        else:
            row = layout.rowCount()
            col = 0
        return row, col

    def getParent(self):
        """A method to return the parent of a widget
        """
        return self.parent()

    def addSpacer(self, width, height, grid, gridSpan=(1, 1), expandX=False, expandY=False, parent=None):
        """Convenience to insert spacer
        width, height: in pixels
        grid=(row,col): tuple or list defining row, column
        gridSpan: tuple or list defining grid-span along row, column

        if either expandX or expandY are True, then the corresponding expanding policy is set to 'minimumExpanding' otherwise it is set to 'fixed'

        :returns: Spacer widget
        """
        from ccpn.ui.gui.widgets.Spacer import Spacer

        expandingX = 'minimumExpanding' if expandX else 'fixed'
        expandingY = 'minimumExpanding' if expandY else 'fixed'

        if parent is None:
            parent = self
        return Spacer(parent, width, height, expandingX, expandingY, grid=grid, gridSpan=gridSpan)

    def _getSaveState(self):
        """
        Internal. Called for saving/restoring the widget state.
        Override in the subclass with the desired behaviour
        """
        return

    def _setSavedState(self, value):
        """
        Internal. Called for saving/restoring the widget state.
        Override in the subclass with the desired behaviour
        """
        pass

    def enableWidget(self, flag:bool):
        """Enable or disable widget depending on flag
        """
        if flag:
            self.setEnabled(True)
            # self.setStyleSheet("background:white")
        else:
            self.setDisabled(True)
            # self.setStyleSheet("background:#E8E8E8")  # some light gr
