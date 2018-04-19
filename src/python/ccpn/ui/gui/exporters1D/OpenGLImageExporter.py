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

  def export(self, fileName=None, toBytes=False, copy=False):
    if fileName is None and not toBytes and not copy:

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
      self.image.save(fileName, quality=quality)
    self.glWidget.setBackgroundColour(originalBackground, silent=True)

OpenGLImageExporter.register()