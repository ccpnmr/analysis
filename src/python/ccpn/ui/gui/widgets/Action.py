"""
Module Documentation here
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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-08-12 20:31:51 +0100 (Fri, August 12, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.lib.Shortcuts import storeShortcut
from ccpn.framework.Translation import translator
from ccpn.framework.Application import getApplication
from ccpn.framework.Translation import getTranslator
from ccpn.util.Logging import getLogger


class Action(Base, QtWidgets.QAction):
    def __init__(self, parent, text, callback=None, shortcut=None, checked=True, checkable=False,
                 icon=None, translate=True, enabled=True, toolTip=None, **kwds):
        # tr = getTranslator('Dutch')
        # title = tr(title)
        if translate:
            text = translator.translate(text)

        if shortcut:
            if isinstance(shortcut, str):

                if shortcut.startswith('⌃'):  # Unicode U+2303, NOT the carrot on your keyboard.

                    # may need to add extras for alt and option
                    shortcut = QtGui.QKeySequence('Ctrl+{}'.format(shortcut[1]))

                else:
                    shortcut = QtGui.QKeySequence(", ".join(tuple(shortcut)))

            elif not isinstance(shortcut, QtGui.QKeySequence):
                raise TypeError('Shortcut type must be a string or a keySequence')

            QtWidgets.QAction.__init__(self, text, parent)
            self.setShortcut(shortcut)
            self.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            self.setShortcutVisibleInContextMenu(True)

            # NOTE:ED - store the keySequence in the shortcuts dict
            storeShortcut(shortcut, parent)

        # elif icon:
        #   QtGui.QAction.__init__(self, icon, text, parent, triggered=callback, checkable=checkable)

        else:
            QtWidgets.QAction.__init__(self, text, parent)

        self.setCheckable(checkable)

        if checkable:
            self.setChecked(checked)

        if callback:
            def _actionCallback(*args, **kwds):
                try:
                    # let the shortcut update the statusbar
                    keys = ''.join(self.shortcut().toString().split(', '))
                    app = getApplication()
                    app.ui.mainWindow._setStatusBarKeys(keys)
                except Exception as es:
                    getLogger().debug2(f'Error updating _lastKeyStatus - {es}')
                callback(*args, **kwds)

            # PyQt5 always seems to add a checked argument for Action callbacks
            self.triggered.connect(lambda checked, *args, **kwds: _actionCallback(*args, **kwds))

        if toolTip:
            self.setToolTip(toolTip)

        # cannot have checkable and icon at the same time
        if icon is not None:
            ic = Icon(icon)
            self.setIcon(ic)

        self.setEnabled(enabled)
