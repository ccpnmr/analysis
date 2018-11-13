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
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from pyqtgraph.graphicsItems.UIGraphicsItem import UIGraphicsItem
import numpy as np
from pyqtgraph.Point import Point
from pyqtgraph import functions as fn

# from ccpn.util.Colour import hexToRgb

__all__ = ['CcpnGridItem']

class CcpnGridItem(UIGraphicsItem):

    def __init__(self, gridColour):
        UIGraphicsItem.__init__(self)
        self.picture = None
        self.gridColour = gridColour

    def viewRangeChanged(self):
        UIGraphicsItem.viewRangeChanged(self)
        self.picture = None

    def viewTransformChanged(self):                 # ejb - causes a redraw when new strip added
        UIGraphicsItem.viewTransformChanged(self)
        self.picture = None

    def paint(self, p, opt, widget):
        if self.picture is None:
            self.generatePicture()
        p.drawPicture(QtCore.QPointF(0, 0), self.picture)

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter()
        p.begin(self.picture)

        dt = fn.invertQTransform(self.viewTransform())
        vr = self.getViewWidget().rect()
        unit = self.pixelWidth(), self.pixelHeight()
        dim = [vr.width(), vr.height()]
        lvr = self.boundingRect()
        ul = np.array([lvr.left(), lvr.top()])
        br = np.array([lvr.right(), lvr.bottom()])

        texts = []

        if ul[1] > br[1]:
            x = ul[1]
            ul[1] = br[1]
            br[1] = x
        for i in [1,0]:   ## Draw three different scales of grid
            dist = br-ul
            nlTarget = 10.**i
            d = 10. ** np.floor(np.log10(abs(dist/nlTarget))+0.5)
            ul1 = np.floor(ul / d) * d
            br1 = np.ceil(br / d) * d
            dist = br1-ul1
            nl = (dist / d) + 0.5

            for ax in range(0,2):  ## Draw grid for both axes
                ppl = np.array( dim[ax] / nl[ax] )                      # ejb
                c = np.clip(3.*(ppl-3), 0., 30.)
                if self.gridColour == '#f7ffff':
                  linePen = QtGui.QPen(QtGui.QColor(247, 255, 255, c))
                else:
                  linePen = QtGui.QPen(QtGui.QColor(8, 0, 0, c))

                bx = (ax+1) % 2
                for x in range(0, int(nl[ax])):
                    linePen.setCosmetic(False)
                    if ax == 0:
                        linePen.setWidthF(self.pixelWidth())
                        #print "ax 0 height", self.pixelHeight()
                    else:
                        linePen.setWidthF(self.pixelHeight())
                        #print "ax 1 width", self.pixelWidth()
                    p.setPen(linePen)
                    p1 = np.array([0.,0.])
                    p2 = np.array([0.,0.])
                    p1[ax] = ul1[ax] + x * d[ax]
                    p2[ax] = p1[ax]
                    p1[bx] = ul[bx]
                    p2[bx] = br[bx]
                    if p1[ax] < np.min(ul[ax], br[ax]) or p1[ax] > np.max(ul[ax], br[ax]):
                        continue
                    p.drawLine(QtCore.QPointF(p1[0], p1[1]), QtCore.QPointF(p2[0], p2[1]))

        tr = self.deviceTransform()
        p.setWorldTransform(fn.invertQTransform(tr))
        for t in texts:
            x = tr.map(t[0]) + Point(0.5, 0.5)
            p.drawText(x, t[1])
        p.end()
