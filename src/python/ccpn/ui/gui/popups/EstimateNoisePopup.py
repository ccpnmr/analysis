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
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-04 09:28:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog


class EstimateNoisePopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, strip=None, title='EstimateNoise', **kw):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        self.strip = strip
        self.stripLabel = Label(self, "Current strip: %s" % strip.id, grid=(0, 0))

        # estimate noise function here

        ButtonList(self, ['Cancel', 'OK'], [self.reject, self._accept], grid=(1, 1))

    def _accept(self):
        """OK button pressed
        """
        self.accept()

    def _cleanupWidget(self):
        """Cleanup the notifiers that are left behind after the widget is closed
        """
        self.close()