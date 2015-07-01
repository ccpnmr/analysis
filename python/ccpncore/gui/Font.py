from PyQt4 import QtGui

import os

FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')

class Font(QtGui.QFont):

  def __init__(self, colour=None, size=None, bold=None, italic=None, normal=None, semiBold=None):
    self.colour = colour
    self.size = size
    self.bold = bold
    self.italic = normal
    self.normal = normal


    if self.bold is True:
      font = 'Lucida Grande -Bold'

    if self.normal is True:
      font = 'OpenSans-Regular'

    if self.italic is True:
      font = 'OpenSans-Italic'

    if semiBold is True:
      font = 'OpenSans-Semibold'

    QtGui.QFont.__init__(self, font)

    if size is None:
      self.setPointSize(8)
    else:
      self.setPointSize(size)
