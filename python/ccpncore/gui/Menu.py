"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtGui

from ccpncore.gui.Action import Action
from ccpncore.gui.Base import Base
from ccpncore.gui.Font import Font


class Menu(QtGui.QMenu, Base):
  def __init__(self, title, parent, isFloatWidget=False, **kw):
    QtGui.QMenu.__init__(self, self.translate(title), parent)
    Base.__init__(self, isFloatWidget=isFloatWidget, **kw)
    self.isFloatWidget = isFloatWidget
    # self.setStyleSheet("""
    # QMenu {background-color: #424a71;
    # }
    # QMenu::item {background-color: #424a71;
    #                   color: #bec4f3;
    #           }
    #   QMenu::item::selected { color: #f7ffff;
    #                              background: #666e98;
    #   }
    #   QMenu::item::hover {
    #   background-color: #e4e15b;
    #   }
    # """)

  def addItem(self, text, shortcut=None, callback=None, checkable=False):
    action = Action(self.parent(), text, callback=callback, shortcut=shortcut,
                         checkable=checkable, isFloatWidget=self.isFloatWidget)
    self.addAction(action)
    return action
    # print(shortcut)
    
  def addMenu(self, title):
    menu = Menu(title, self)
    QtGui.QMenu.addMenu(self, menu)
    return menu

class MenuBar(QtGui.QMenuBar):
  def __init__(self, parent):

    QtGui.QMenuBar.__init__(self, parent)
    import os
    FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')

    # font = Font(normal=True, size=16)
    QtGui.QFontDatabase.addApplicationFont(os.path.join(FONT_DIR, 'open-sans/OpenSans-Regular.ttf'))
    # self.setFont(font)
    # self.setStyleSheet("""
    #   QMenuBar {
    #           background-color: #424a71;
    #           font-family: Open-Sans;
    #           font-size: 16pt;
    #           }
    #   QMenuBar::item {background-color: #424a71;
    #                   color: #bec4f3;
    #           }
    #   QMenuBar::item::selected { color: #f7ffff;
    #                              background: #666e98;
    #   }
    #   QMenuBar::item::hover {
    #   background-color: #e4e15b;
    #   }
    #   """)