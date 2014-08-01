from PySide import QtGui, QtCore

from ccpncore.util import Translation

HALIGN_DICT = {
  'left': QtCore.Qt.AlignLeft,
  'right': QtCore.Qt.AlignRight,
  'center': QtCore.Qt.AlignHCenter,
  'l': QtCore.Qt.AlignLeft,
  'r': QtCore.Qt.AlignRight,
  'c': QtCore.Qt.AlignHCenter,
}

VALIGN_DICT = {
  'top': QtCore.Qt.AlignTop,
  'bottom': QtCore.Qt.AlignBottom,
  'center': QtCore.Qt.AlignVCenter,
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

class Base:

  def __init__(self, tipText=None, grid=(None, None), gridSpan=(1,1), stretch=(0,0),
               hAlign=None, vAlign=None, hPolicy=None, vPolicy=None,
               bgColor=None, isFloatWidget=False):

    # Tool tips
    if tipText:
      self.setToolTip(tipText)

    parent = self.parent() if hasattr(self, 'parent') else None # Not all Qt objects have a parent
    if parent and not isFloatWidget:
      # Setup gridding within parent
      layout = parent.layout()
 
      if not layout:
        layout = QtGui.QGridLayout(parent)
        layout.setSpacing(2)
        layout.setContentsMargins(2,2,2,2)
        parent.setLayout( layout )
 
      if isinstance(layout, QtGui.QGridLayout): 
        row, col = self._getRowCol(grid)
        rowStr, colStr = stretch
        layout.setRowStretch(row, rowStr)
        layout.setColumnStretch(col, colStr)
 
        rowSpan, colSpan = gridSpan
        hAlign = HALIGN_DICT.get(hAlign, 0)
        vAlign = VALIGN_DICT.get(vAlign, 0)
        align = hAlign | vAlign
        layout.addWidget(self, row, col, rowSpan, colSpan, align)
                
    if hPolicy or vPolicy:
      hPolicy = POLICY_DICT.get(hPolicy, 0)
      vPolicy = POLICY_DICT.get(vPolicy, 0)
      self.setSizePolicy(hPolicy, vPolicy)

    # Setup colour overrides (styles used primarily)
     
    if bgColor:
      self.setAutoFillBackground(True)
      rgb = QtGui.QColor(bgColor).getRgb()[:3]
      self.setStyleSheet("background-color: rgb(%d, %d, %d);" %  rgb)

    Translation.updateTranslationDict(self)
    
  def translate(self, text):
  
    return Translation.getTranslation(text)

  def _getRowCol(self, grid):

    layout = self.parent().layout()

    if grid:
      row, col = grid
      if row is None:
        row = layout.rowCount()

      if col is None:
        col = 0
    else:
      row = layout.rowCount()
      col = 0

    return row, col

 
