__author__ = 'simon'

import importlib, os

from PySide import QtGui, QtCore

from ccpncore.gui.Label import Label
from ccpncore.gui.ToolBar import ToolBar

from ccpnmrcore.modules.GuiModule import GuiModule

class GuiSpectrumDisplay(GuiModule):

  def __init__(self, dockArea, apiSpectrumDisplay):
    GuiModule.__init__(self, dockArea, apiSpectrumDisplay)
    self.guiSpectrumViews = []
    self.guiStrips = []
    for apiStrip in apiSpectrumDisplay.strips:   ### probably need orderedStrips() here ?? ask Rasmus
      className = apiStrip.className
      classModule = importlib.import_module('ccpnmrcore.modules.Gui' + className)
      print("I'm here", classModule)
      clazz = getattr(classModule, 'Gui'+className)
      guiStrip = clazz(self, apiStrip)
      self.guiStrips.append(guiStrip)  ##needs looking at
      print("Here again", guiStrip)

    # self.spectrumToolBar = ToolBar(self, grid=(0, 0), gridSpan=(2, 6))
    # self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    # self.spectrumToolBar.setMinimumHeight(44)
    # self.spectrumToolBar.setMaximumWidth(550)
    #
    # self.spectrumUtilToolBar = ToolBar(self, grid=(0, 6), gridSpan=(2, 3))
    # toolBarColour = QtGui.QColor(214,215,213)
    # palette = QtGui.QPalette(self.spectrumUtilToolBar.palette())
    # palette2 = QtGui.QPalette(self.spectrumToolBar.palette())
    # palette.setColor(QtGui.QPalette.Button,toolBarColour)
    # palette2.setColor(QtGui.QPalette.Button,toolBarColour)

    self.positionBox = Label(self, grid=(0, 9), gridSpan=(2, 2))

  def addStrip(self):
    pass

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self,event):
    event.accept()
    # self.current.pane = self
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():

      filePaths = [url.path() for url in event.mimeData().urls()]
      if len(filePaths) == 1:
        for dirpath, dirnames, filenames in os.walk(filePaths[0]):
          if dirpath.endswith('memops') and 'Implementation' in dirnames:
            self.appBase.openProject(filePaths[0])
            self.addSpectra(self.project.spectra)

        else:
          print(filePaths[0])
          self.appBase.mainWindow.loadSpectra(filePaths[0])


      elif len(filePaths) > 1:
        [self.appBase.mainWindow.loadSpectra(filePath) for filePath in filePaths]


    else:
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      #data = event.mimeData().text()
      print('RECEIVED mimeData: "%s"' % data)

      pidData = str(data.data(),encoding='utf-8')
      WHITESPACE_AND_NULL = ['\x01', '\x00', '\n','\x1e','\x02','\x03','\x04','\x0e','\x12', '\x0c', '\x05', '\x10', '\x14']
      pidData2 = [s for s in pidData if s not in WHITESPACE_AND_NULL]
      actualPid = ''.join(map(str, pidData2))
      print(list(actualPid))


      spectrum = self.getObject(actualPid)
      print(spectrum)
      self.addSpectrum(spectrum)
