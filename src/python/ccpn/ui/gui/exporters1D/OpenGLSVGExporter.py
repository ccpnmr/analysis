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
__dateModified__ = "$dateModified: 2022-02-15 16:20:03 +0000 (Tue, February 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

# the code below is from PyQtGraph


from pyqtgraph.parametertree import Parameter
from ccpn.ui.gui.exporters1D.Exporter import Exporter
from PyQt5 import QtGui, QtWidgets, QtCore
from collections import OrderedDict

__all__ = ['OpenGLSVGExporter']


Quality = OrderedDict([('low',1), ('medium',50), ('high',100)])

class OpenGLSVGExporter(Exporter):
  Name = "SVG Format"
  allowCopy = True

  def __init__(self, item):
    Exporter.__init__(self, item)
    self.glWidget = item
    bg = self.glWidget.background
    qtColour = QtGui.QColor(*[i*255 for i in bg])
    self.params = Parameter(name='params', type='group', children=[])
    #                       # {'name': 'width', 'type': 'int', 'value': 0, 'limits': (0, None)},
    #                       # {'name': 'height', 'type': 'int', 'value': 0, 'limits': (0, None)},
    #                       {'name': 'quality', 'type': 'list', 'values': Quality.keys()},
    #                       {'name': 'background', 'type': 'color', 'value': qtColour},
    #                                                               ])
    # # self.params.param('width').sigValueChanged.connect(self.widthChanged)
    # # self.params.param('height').sigValueChanged.connect(self.heightChanged)


  def parameters(self):
   return self.params

  def export(self, filename=None, toBytes=False, copy=False):
    if filename is None and not toBytes and not copy:

      _filter = ['*.svg',]
      preferred = ['*.svg',]
      for p in preferred[::-1]:
        if p in _filter:
          _filter.remove(p)
          _filter.insert(0, p)
      self.fileSaveDialog(fileFilter=_filter)
      return

    # TODO:ED finish writing code to export SVG using reportlab

    svgExport = self.glWidget.exportToSVG(filename, self.params)
    if svgExport:
      svgExport.writeSVGFile()


OpenGLSVGExporter.register()
