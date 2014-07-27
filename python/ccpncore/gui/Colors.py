import sys
from PySide import QtGui

class ColorDialog(QtGui.QColorDialog):

  def __init__(self, parent=None, doAlpha=False, **kw):

    QtGui.QColorDialog.__init__(self, parent)

    self.setOption(self.ShowAlphaChannel, doAlpha)
    self.setOption(QtGui.QColorDialog.DontUseNativeDialog,  True)
    self.aborted = False
    self.rejected.connect(self.quit)

  def set(self, color):

    self.setColor(color)


  def getColor(self, initialColor=None):

    if initialColor is not None:
      self.setColor(initialColor)

    self.exec_()

    color = self.currentColor()

    if self.aborted:
      return None
    else:
      return color

  def setColor(self, color):
    # color can be name, #hex, (r,g,b) or (r,g,b,a)

    if isinstance(color, (list, tuple)) and color:

      if isinstance(color[0], float):
        color = [int(255*c) for c in color]

      qColor = QtGui.QColor(*color)
      color = color.upper()

    elif isinstance(color, QtGui.QColor):
      qColor = QtGui.QColor(color)

    elif color[0] == '#':
      if isinstance(color[0], float):
        color = [int(255*c) for c in color]

      qColor = QtGui.QColor(*color)
      color = color.upper()

      if len(color) == 9:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        a = int(color[7:9], 16)
        color = (r, g, b, a)

      else:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        color = (r, g, b)

      qColor = QtGui.QColor(*color)

    self.setCurrentColor(qColor)

  def quit(self):

    self.aborted = True