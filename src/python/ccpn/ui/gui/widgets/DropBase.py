"""
Define routines for a dropable widget
This module is subclassed by widgets.Base and should not be used directly

GWV April-2017: Drived from an earlier version of DropBase

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:53 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from ccpn.core.lib.Pid import Pid
from ccpn.util.Logging import getLogger
from PyQt5 import QtGui


class DropBase:
    """
    Class to implement drop and drag
    Callback signature on drop: dropEventCallback(dataDict)
    """

    # drop targets
    URLS = 'urls'
    TEXT = 'text'
    PIDS = 'pids'
    IDS = 'ids'
    _dropTargets = (URLS, TEXT, PIDS, IDS)

    from ccpn.util.Constants import ccpnmrJsonData as JSONDATA

    def _init(self, acceptDrops=False, **kwds):

        # print('DEBUG DropBase %r: acceptDrops=%s' % (self, acceptDrops))

        self._dropEventCallback = None
        self._enterEventCallback = None
        self._dragMoveEventCallback = None
        self.setAcceptDrops(acceptDrops)

    def setDropEventCallback(self, callback):
        """Set the callback function for drop event."""
        self._dropEventCallback = callback

    def dragEnterEvent(self, event):
        dataDict = self.parseEvent(event)
        if dataDict is not None and len(dataDict) > 1:
            event.accept()
            if self._dragMoveEventCallback is not None:
                self._dragMoveEventCallback(dataDict)
        event.accept()

    def setDragMoveEventCallback(self, callback):
        self._dragMoveEventCallback = callback

    def setDragEnterEventCallback(self, callback):
        self._enterEventCallback = callback

    # def dragMoveEvent(self, event):
    #   dataDict = self.parseEvent(event)
    #   if dataDict is not None and len(dataDict) > 1:
    #     if self._dragMoveEventCallback is not None:
    #       self._dragMoveEventCallback(dataDict)
    #       event.accept()
    #       return
    #
    #   event.ignore()
    #   print('>>>dragMoveEvent')

    # super().dragMoveEvent(event)

    def dropEvent(self, event):
        """
        Catch dropEvent and dispatch to processing callback
        'Native' treatment of CcpnModule instances
        """
        inModuleOverlay = self._callModuleDrop(event)

        if inModuleOverlay:
            inModuleOverlay.dropEvent(event)
            self._clearOverlays()
            return

        if self.acceptDrops():

            dataDict = self.parseEvent(event)
            getLogger().debug('Accepted drop with data:%s' % dataDict)
            getLogger().debug('DropBase-event>: %s callback: %s data: %s' % (self, self._dropEventCallback, dataDict))

            if dataDict is not None and len(dataDict) > 1:
                event.accept()
                if self._dropEventCallback is not None:
                    self._dropEventCallback(dataDict)

        else:
            getLogger().debug('Widget not droppable')

        # call to clear the overlays
        self._clearOverlays()

    def parseEvent(self, event) -> dict:
        """
        Interpret drop event; extract urls, text or JSONDATA dicts
        convert PIDS to Pid object's
        return a dict with
          - event, source key,values pairs
          - (type, data) key,value pairs,
        """
        data = dict(
                event=event,
                source=event.source()
                )
        mimeData = event.mimeData()

        if mimeData.hasFormat(DropBase.JSONDATA):
            data['isCcpnJson'] = True
            jsonData = json.loads(mimeData.text())
            if jsonData is not None and len(jsonData) > 0:
                data.update(jsonData)
            if self.PIDS in data:
                newPids = [Pid(pid) for pid in data[self.PIDS]]
                data[self.PIDS] = newPids

        elif event.mimeData().hasUrls():
            filePaths = [url.path() for url in event.mimeData().urls()]
            data[self.URLS] = filePaths

        elif event.mimeData().hasText():
            data[self.TEXT] = event.mimeData().text()

        return data

    def dragMoveEvent(self, ev):
        """drag move event that propagates through all the widgets
        """
        parentModule = self._findModule()
        if parentModule:
            data = self.parseEvent(ev)

            from ccpn.ui.gui.widgets.CcpnModuleArea import MODULEAREA_IGNORELIST

            # ignore dropAreas if the source of the event is in the list
            if isinstance(data['source'], MODULEAREA_IGNORELIST):
                return

            p = parentModule.mapFromGlobal(QtGui.QCursor().pos())

            ld = p.x()  # ev.pos().x()
            rd = parentModule.width() - ld
            td = p.y()  # ev.pos().y()
            bd = parentModule.height() - td

            mn = min(ld, rd, td, bd)
            if mn > 30:
                parentModule.dropArea = "center"
            elif (ld == mn or td == mn) and mn > parentModule.height() / 3.:
                parentModule.dropArea = "center"
            elif (rd == mn or ld == mn) and mn > parentModule.width() / 3.:
                parentModule.dropArea = "center"

            elif rd == mn:
                parentModule.dropArea = "right"
            elif ld == mn:
                parentModule.dropArea = "left"
            elif td == mn:
                parentModule.dropArea = "top"
            elif bd == mn:
                parentModule.dropArea = "bottom"

            if ev.source() is parentModule and parentModule.dropArea == 'center':
                #print "  no self-center"
                parentModule.dropArea = None
                # ev.ignore()

            elif parentModule.dropArea not in parentModule.allowedAreas:
                #print "  not allowed"
                parentModule.dropArea = None
                # ev.ignore()

            # else:
            #     #print "  ok"
            #     ev.accept()
            parentModule.overlay.setDropArea(parentModule.dropArea)

    def _clearOverlays(self):
        """Clear the overlays for the containing CcpnModule
        """
        par = self._findModule()
        if par:
            par.dragLeaveEvent(None)

    def _callModuleDrop(self, ev):
        """Return true if the containing CcpnModule has been activated in one of the dropAreas
        """
        par = self._findModule()
        if par and par.dropArea:
            return par

    def dragLeaveEvent(self, ev):
        """Clear the overlays when leaving the widgetArea
        """
        par = self._findModule()
        if par:
            par.dragLeaveEvent(ev)

    def _findModule(self):
        """Find the CcpnModule containing this widget
        """
        from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModule

        par = self
        while par:
            par = par.parent()  # getParent() may be used for CCPN widgets, not for other QWidgets
            if isinstance(par, CcpnModule):
                return par
