"""Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-12-08 13:22:53 +0000 (Thu, December 08, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.widgets.Base import Base
# from ccpn.ui.gui.guiSettings import menuFont
from ccpn.framework.Translation import translator
from ccpn.ui.gui.widgets.Font import setWidgetFont


SHOWMODULESMENU = 'Show/hide Modules'
MACROSMENU = 'User Macros'
CCPNMACROSMENU = 'Run CCPN Macros'
USERMACROSMENU = 'Run User Macros'
TUTORIALSMENU = 'Tutorials'
HOWTOSMENU = 'How-Tos'
PLUGINSMENU = 'User Plugins'
CCPNPLUGINSMENU = 'CCPN Plugins'


class Menu(QtWidgets.QMenu, Base):
    def __init__(self, title, parent, isFloatWidget=False, **kwds):
        super().__init__(parent)
        Base._init(self, isFloatWidget=isFloatWidget, **kwds)

        title = translator.translate(title)
        self.setTitle(title)
        self.isFloatWidget = isFloatWidget

        self.setToolTipsVisible(True)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)


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
        """ this adds a normal QMenu """
        QtWidgets.QMenu.addMenu(self, menu)
        return menu

    def getItems(self):
        dd = {i.text(): i for i in self.actions()}
        return dd

    def getActionByName(self, name):
        """
        Given a name return the menu action
        """
        return self.getItems().get(name, None)

    def moveActionBelowName(self, action, targetActionName):
        """
        Move a action below a pre-existing name
        """
        targetAction = self.getActionByName(targetActionName)
        if targetAction:
            self.insertAction(action, targetAction)

    def moveActionAboveName(self, action, targetActionName):
        """
        Move a action above a pre-existing name
        """
        targetAction = self.getActionByName(targetActionName)
        if targetAction:
            self.insertAction(targetAction, action)


class MenuBar(QtWidgets.QMenuBar):
    def __init__(self, parent):
        QtWidgets.QMenuBar.__init__(self, parent)
