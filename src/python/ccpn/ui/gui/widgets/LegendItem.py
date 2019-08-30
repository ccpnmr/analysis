"""
Module Documentation Here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph.graphicsItems.LegendItem import ItemSample
import pyqtgraph.functions as fn
from pyqtgraph.graphicsItems.ScatterPlotItem import drawSymbol

class LegendItem(pg.LegendItem):
    def __init__(self, plot, size=None, offset=None):
        super().__init__(size, offset)
        self.setParentItem(plot.vb)
        self.plot = plot
        plot.legend = self

    
    def clearLegend(self):
        "Removes all items from the legend"
        while self.layout.count() > 0:
            self.layout.removeAt(0)
        self.items = []
        self.setGeometry(0, 0, 0, 0)

    def paint(self, p, *args):
        p.setPen(pg.functions.mkPen(255,255,255,50))
        p.setBrush(pg.functions.mkBrush(100,100,100,10))
        p.drawRect(self.boundingRect())

    def addItem(self, item, name, showLine=True):
        """

        """
        label = pg.LabelItem(name)
        sample = CustomItemSample(item, showLine)
        row = self.layout.rowCount()
        self.items.append((sample, label))
        self.layout.addItem(sample, row, 0)
        self.layout.addItem(label, row, 1)
        self.updateSize()

    def updateSize(self):
        if self.size is not None:
            return

        height = 0
        width = 0
        # print("-------")
        for sample, label in self.items:
            height += max(sample.height(), label.height()) + 1
            width = max(width, sample.width() + label.width())
            # print(width, height)
        # print width, height
        self.setGeometry(0, 0, width + 5, height)



class CustomItemSample(ItemSample):
    def __init__(self, item, showLine):
        super().__init__(item)
        self.showLine = showLine
        #### symbols are: ['o', 's', 't', 't1', 't2', 't3','d', '+', 'x', 'p', 'h', 'star']

    def paint(self, p, *args):
        # p.setRenderHint(p.Antialiasing)  # only if the data is antialiased.
        opts = self.item.opts
        pen = fn.mkPen(opts['pen'])

        if opts.get('fillLevel', None) is not None and opts.get('fillBrush', None) is not None:
            p.setBrush(fn.mkBrush(opts['fillBrush']))
            p.setPen(fn.mkPen(None))
            p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(2, 18), QtCore.QPointF(18, 2), QtCore.QPointF(18, 18)]))

        if self.showLine:
            if not isinstance(self.item, pg.ScatterPlotItem):
                p.setPen(fn.mkPen(opts['pen'],))
                p.drawLine(30, 0 , 0, 0)

        symbol = opts.get('symbol', None)
        if symbol is not None:
            if isinstance(self.item, pg.PlotDataItem):
                opts = self.item.scatter.opts

            brush = fn.mkBrush(opts['brush'])
            size = opts['size']
            p.translate(0, 10) # moves away from the label
            path = drawSymbol(p, symbol, size, pen, brush)

