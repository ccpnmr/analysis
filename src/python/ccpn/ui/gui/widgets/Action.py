"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:51 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.framework.Translation import translator
from ccpn.framework.Translation import getTranslator


class Action(QtGui.QAction, Base):
  def __init__(self, parent, text, callback=None, shortcut=None, checked=True, checkable=False,
               icon=None, translate=True, enabled=True, **kw):
    # tr = getTranslator('Dutch')
    # title = tr(title)
    if translate:
      text = translator.translate(text)

    if shortcut:
      if type(shortcut) == type(''):
        shortcut = QtGui.QKeySequence(", ".join(tuple(shortcut)))
      QtGui.QAction.__init__(self, text, parent, shortcut=shortcut, checkable=checkable)
      self.setShortcutContext(QtCore.Qt.ApplicationShortcut)
    # elif icon:
    #   QtGui.QAction.__init__(self, icon, text, parent, triggered=callback, checkable=checkable)

    else:
      QtGui.QAction.__init__(self, text, parent, checkable=checkable)

    if checkable:
      self.setChecked(checked)
      
    if callback:
      # PyQt4 always seems to add a checked argument for Action callbacks
      self.triggered.connect(lambda checked, *args, **kw: callback(*args, **kw))

    self.setEnabled(enabled)
    # Base.__init__(self, **kw)
