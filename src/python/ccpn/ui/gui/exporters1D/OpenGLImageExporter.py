"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2018-12-20 15:53:11 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.b4 $"
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

__all__ = ['OpenGLImageExporter']


Quality = OrderedDict([('low',1), ('medium',50), ('high',100)])

class OpenGLImageExporter(Exporter):
  Name = "Image File (PNG, TIF, JPG, ...)"
  allowCopy = True

  def __init__(self, item):
    Exporter.__init__(self, item)
    self.glWidget = item
    bg = self.glWidget.background
    qtColour = QtGui.QColor(*[i*255 for i in bg])
    self.params = Parameter(name='params', type='group', children=[
                          # {'name': 'width', 'type': 'int', 'value': 0, 'limits': (0, None)},
                          # {'name': 'height', 'type': 'int', 'value': 0, 'limits': (0, None)},
                          {'name': 'quality', 'type': 'list', 'values': Quality.keys()},
                          {'name': 'background', 'type': 'color', 'value': qtColour},
                                                                  ])
    # self.params.param('width').sigValueChanged.connect(self.widthChanged)
    # self.params.param('height').sigValueChanged.connect(self.heightChanged)


  def parameters(self):
   return self.params

  def export(self, filename=None, toBytes=False, copy=False):
    if filename is None and not toBytes and not copy:

      filter = ["*." + bytes(f).decode('utf-8') for f in QtGui.QImageWriter.supportedImageFormats()]
      preferred = ['*.png', '*.tif', '*.jpg']
      for p in preferred[::-1]:
        if p in filter:
          filter.remove(p)
          filter.insert(0, p)
      self.fileSaveDialog(filter=filter)
      return

    quality = Quality.get(self.params['quality'])
    bgColorObj = self.params['background']
    bgRgb = bgColorObj.getRgb()
    originalBackground = self.glWidget.background
    self.glWidget.setBackgroundColour([i/255 for i in bgRgb], silent=True)
    self.image = self.glWidget.grabFramebuffer()

    if copy:
      QtWidgets.QApplication.clipboard().setImage(self.image)
    elif toBytes:
      return self.image
    else:
      self.image.save(filename, quality=quality)
    self.glWidget.setBackgroundColour(originalBackground, silent=True)

OpenGLImageExporter.register()
