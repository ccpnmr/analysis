"""
Base class for gridding, optionally setting up size policies and layout,
optionally inserting itself into parent using keyword, grid, gridspan, hAlign, vAlign

The proper way for adding widgets explicitly is:
widget.getLayout().addWidget(row, col, [rowspan, [colspan])
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:42 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtGui, QtCore

from pyqtgraph.dockarea import Dock
from ccpn.ui.gui.widgets.DropBase import DropBase

from ccpn.util.Logging import getLogger

HALIGN_DICT = {
  'left': QtCore.Qt.AlignLeft,
  'right': QtCore.Qt.AlignRight,
  'center': QtCore.Qt.AlignHCenter,
  'centre': QtCore.Qt.AlignHCenter,
  'l': QtCore.Qt.AlignLeft,
  'r': QtCore.Qt.AlignRight,
  'c': QtCore.Qt.AlignHCenter,
}

VALIGN_DICT = {
  'top': QtCore.Qt.AlignTop,
  'bottom': QtCore.Qt.AlignBottom,
  'center': QtCore.Qt.AlignVCenter,
  'centre': QtCore.Qt.AlignVCenter,
  't': QtCore.Qt.AlignTop,
  'b': QtCore.Qt.AlignBottom,
  'c': QtCore.Qt.AlignVCenter,
}

POLICY_DICT = {
  'fixed': QtGui.QSizePolicy.Fixed,
  'minimum': QtGui.QSizePolicy.Minimum,
  'maximum': QtGui.QSizePolicy.Maximum,
  'preferred': QtGui.QSizePolicy.Preferred,
  'expanding': QtGui.QSizePolicy.Expanding,
  'minimumExpanding': QtGui.QSizePolicy.MinimumExpanding,
  'ignored': QtGui.QSizePolicy.Ignored,
}


class Base(DropBase):

  def __init__(self, tipText=None,
                     setLayout=False,
                     hPolicy=None, vPolicy=None,
                     bgColor=None, fgColor=None,
                     isFloatWidget=False,
                     acceptDrops=False,
                     grid=(None, None), gridSpan=(1,1), stretch=(0,0),
                     hAlign=None, vAlign=None,
               ):
    """
    
    :param tipText:  add tiptext to widget
    :param grid:     insert widget at (row,col) of parent layout (if available)
    :param gridSpan: extend widget over (rows,cols); default (1,1)
    :param stretch:  stretch (row,col) of widget (True/False); default (False,False)
    :param hAlign:   horizontal alignment: left, right, centre (center, l, r, c)
    :param vAlign:   vertical alignment: top, bottom, centre (center, t, b. c)
    :param hPolicy:  horizontal policy of widget: fixed, minimum, maximum, preferred, expanding, minimumExpanding, ignored
    :param vPolicy:  vertical policy of widget: fixed, minimum, maximum, preferred, expanding, minimumExpanding, ignored
    :param bgColor:  background RGB colour tuple; depreciated: use styleSheet routines instead
    :param fgColor:  foreground RGB colour tuple; depreciated: use styleSheet routines instead
    :param isFloatWidget: indicates widget to be floating
    """

    # define the 'droppable' methods
    DropBase.__init__(self, acceptDrops=acceptDrops)

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
      self.setStyleSheet("background-color: rgb(%d, %d, %d);" %  bgColor)

    if fgColor:
      self.setAutoFillBackground(True)
      #rgb = QtGui.QColor(fgColor).getRgb()[:3]
      self.setStyleSheet("foreground-color: rgb(%d, %d, %d);" %  fgColor)

    if setLayout:
      self.setGridLayout()

    # add the widget to parent if it is not a float widget and either grid[0] (horizontal)
    # or grid[1] (vertical) are defined
    if not isFloatWidget and (grid[0] is not None or grid[1] is not None):
      self._addToParent(grid=grid, gridSpan=gridSpan, stretch=stretch,
                        hAlign=hAlign, vAlign=vAlign)

  def setGridLayout(self):
    "Add a QGridlayout to self"
    layout = self._getLayout(self)  # use _getLayout as we do not want any message; if there is no
                                    # layout, we are going to add one
    if layout is None:
      layout = QtGui.QGridLayout(self)
      layout.setContentsMargins(0, 0, 0, 0)
      layout.setSpacing(0)
      self.setLayout(layout)
    else:
      getLogger().warning('Widget %s already has a layout!' % self)

  def getLayout(self):
    "return the layout of self"
    layout = self._getLayout(self)
    if layout is None:
      getLogger().warning('Unable to query layout of %s', self)
    return layout

  @staticmethod
  def _getLayout(widget):
    "return the layout of widget"
    layout = None
    try:
      layout = QtGui.QWidget.layout(widget)
    except:
      pass
    return layout

  def _addToParent(self, grid, gridSpan, stretch, hAlign, vAlign):
    "Add widget to parent of self (if can be obtained)"

    parent = self.parent() if hasattr(self, 'parent') else None # Not all Qt objects have a parent
    if parent is None:
      getLogger().warning('Cannot add widget %s to parent (grid=%s)' % (self,grid))
      return

    # have to use _getLayout() functionality as not all widget descend from Base;
    layout = self._getLayout(parent)
    if layout is None:
      getLogger().warning('No layout for parent widget %s of %s', (parent,self))
      return

    if isinstance(layout, QtGui.QGridLayout):
      row, col = self._getRowCol(layout, grid)
      rowStr, colStr = stretch
      layout.setRowStretch(row, rowStr)
      layout.setColumnStretch(col, colStr)

      rowSpan, colSpan = gridSpan
      hAlign = HALIGN_DICT.get(hAlign, 0)

      vAlign = VALIGN_DICT.get(vAlign, 0)
      align = hAlign | vAlign
      layout.addWidget(self, row, col, rowSpan, colSpan, QtCore.Qt.Alignment(align))

  @staticmethod
  def _getRowCol(layout, grid):
    "Returns (row, col) tuple from layout, using grid or using current rowCount"
    if layout is None:
      getLogger().warning('Layout of widget %s is None, cannot get (row, col) tuple', self)
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


 
