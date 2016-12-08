from PyQt4 import QtGui

# This only works when we have a QtApp instance working; hence it need to go somewhere else.
#from ccpn.framework.PathsAndUrls import fontsPath
#QtGui.QFontDatabase.addApplicationFont(os.path.join(fontsPath, 'open-sans/OpenSans-Regular.ttf'))


class Font(QtGui.QFont):

  def __init__(self, fontName, size, bold=False, italic=False, underline=False, strikeout=False):
    """
    Initialise the font fontName
    :param fontName: font name
    :param size: size of font
    :param bold (optional): make font bold
    :param italic (optional):make fint italic

     to retrieve:
     self.fontName -> fontName
     QFont methods:
     self.pointSize() -> size
     self.italic() -> italic
     self.bold() -> bold
    """

    QtGui.QFont.__init__(self, fontName, size)
    self.fontName = fontName
    self.setBold(bold)
    self.setItalic(italic)
    self.setUnderline(underline)
    self.setStrikeOut(strikeout)

