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
__dateModified__ = "$dateModified: 2017-07-07 16:32:49 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb


class SelectObjectsPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None,
                 dim=None, objects=None,
                 title='Select Objects', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.project = self.mainWindow.project
        self.application = self.mainWindow.application

        self._parent = parent
        if len(objects) > 0:
            if self.project.getByPid(objects[0]._pluralLinkName) == 'spectra':
                objects = [spectrum.pid for spectrum in self.project.spectra if len(spectrum.axisCodes) >= dim]
            else:
                objects = [object.pid for object in objects]

            label1a = Label(self, text="Selected %s" % self.project.getByPid(objects[0])._pluralLinkName, grid=(0, 0))
            objects.insert(0, '  ')
            self.objectPulldown = PulldownList(self, grid=(1, 0), callback=self._selectObject)
            self.objectPulldown.setData(objects)
            self.objectListWidget = ListWidget(self, grid=(2, 0))

            self.buttonBox = ButtonList(self, grid=(3, 0), texts=['Cancel', 'Ok'],
                                        callbacks=[self.reject, self._setObjects])

    def _selectObject(self, item):
        self.objectListWidget.addItem(item)

    def _setObjects(self):
        self._parent.objects = [self.objectListWidget.item(i).text() for i in range(self.objectListWidget.count())]
        self.accept()
        # return [self.objectListWidget.item(i).text() for i in range(self.objectListWidget.count())]
