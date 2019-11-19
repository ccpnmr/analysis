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
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.guiSettings import menuFont
from ccpn.framework.Translation import translator

SHOWMODULESMENU = 'Show/hide Modules'
MACROSMENU = 'User Macros'
CCPNMACROSMENU = 'Run CCPN Macros'
TUTORIALSMENU = 'Tutorials'
PLUGINSMENU = 'User Plugins'
CCPNPLUGINSMENU = 'CCPN Macros'


class Menu(QtWidgets.QMenu, Base):
    def __init__(self, title, parent, isFloatWidget=False, **kwds):
        super().__init__(parent)
        Base._init(self, isFloatWidget=isFloatWidget, **kwds)

        title = translator.translate(title)
        self.setTitle(title)
        self.isFloatWidget = isFloatWidget
        self.setFont(menuFont)
        self.setToolTipsVisible(True)

    def addItem(self, text, shortcut=None, callback=None, checked=True, checkable=False, icon=None, toolTip=None, **kwargs):
        action = Action(self.getParent(), text, callback=callback, shortcut=shortcut,
                        checked=checked, checkable=checkable, icon=icon, toolTip=toolTip, isFloatWidget=self.isFloatWidget, **kwargs)
        self.addAction(action)
        return action
        # print(shortcut)

    def _addSeparator(self, *args, **kwargs):
        separator = self.addSeparator()
        return separator

    def addMenu(self, title, **kwargs):
        menu = Menu(title, self)
        QtWidgets.QMenu.addMenu(self, menu)
        return menu

    def _addQMenu(self, menu):
        ''' this adds a normal QMenu '''
        QtWidgets.QMenu.addMenu(self, menu)
        return menu


class MenuBar(QtWidgets.QMenuBar):
    def __init__(self, parent):
        QtWidgets.QMenuBar.__init__(self, parent)
        self.setFont(menuFont)
