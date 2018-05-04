"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
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

      filter = ['*.svg',]
      preferred = ['*.svg',]
      for p in preferred[::-1]:
        if p in filter:
          filter.remove(p)
          filter.insert(0, p)
      self.fileSaveDialog(filter=filter)
      return

    # TODO:ED finish writing code to export SVG using reportlab

    svgExport = self.glWidget.exportToSvg(filename, self.params)
    if svgExport:
      with open(filename, 'wb') as fd:
        fd.write(svgExport)


OpenGLSVGExporter.register()
