__author__ = 'simon'


from pyqtgraph.dockarea import DockArea

from ccpn.lib.Project import loadSpectrum

from ccpncore.gui.Action import Action
from ccpncore.gui.Console import PythonConsole
from ccpncore.gui.SideBar import SideBar
from ccpncore.gui.TextEditor import TextEditor

from ccpncore.lib.spectrum import Util as specUtil

from ccpnmrcore.Base import Base as GuiBase

from ccpnmrcore.popups.PreferencesPopup import PreferencesPopup
# from ccpnmrcore.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup

from PySide import QtGui, QtCore

import os, json, sys, importlib
from functools import partial
from ccpncore.api.ccpnmr.gui.Task import SpectrumDisplay

class GuiWindow(GuiBase):

  def __init__(self, appBase, apiWindow):
    self.appBase = appBase
    self.apiWindow = apiWindow
    self.dockArea = DockArea()
    self.dockArea.guiWindow = self
    self.dockArea.setGeometry(0, 0, 1100, 1300)
    for apiModule in apiWindow.sortedModules():
      if isinstance(apiModule, SpectrumDisplay):
        className = apiModule.className
        classModule = importlib.import_module('ccpnmrcore.modules.Gui' + className)
        clazz = getattr(classModule, 'Gui'+className)
        guiModule = clazz(self.dockArea, apiModule)
      else:
        raise Exception("Don't know how to deal with this yet")
    appBase.guiWindows.append(self)

  def loadSpectra(self, directory=None):
    if directory == None:
      directory = QtGui.QFileDialog.getOpenFileName(self, 'Open Spectra')
      spectrum = loadSpectrum(self.project,directory[0])

    else:
      spectrum = loadSpectrum(self.project,directory)
      # self.leftWidget.addItem(self.leftWidget.spectrumItem,spectrum)

    msg = spectrum.name+' loaded'
    mainWindow = self.appBase.mainWindow
    mainWindow.leftWidget.addItem(mainWindow.leftWidget.spectrumItem,spectrum)
    mainWindow.statusBar().showMessage(msg)
    if len(directory) == 1:
      mainWindow.pythonConsole.write("project.loadSpectrum('"+directory+"')\n")
    else:
      mainWindow.pythonConsole.write("project.loadSpectrum('"+directory[0]+"')\n")

  def addSpectrum1dDisplay(self):
      pass
    # #newModule = Spectrum1dPane(parent=self, title='Module %s' % str(self.moduleCount+1),
    # newModule = Spectrum1dDisplay(title='Module %s_1D' % str(self.moduleCount+1),
    #                            current=self.current, pid='QP:%s' % str(self.moduleCount+1),
    #                            preferences=self.preferences, mainWindow=self)
    # self.panes[newModule.pid] = newModule
    # newModule.project = self.project
    # newModule.current = self.current
    # self.moduleCount+=1
    #
    # self.dockArea.addDock(newModule.dock)
    # return newModule

  def addSpectrumNdDisplay(self):
    pass
    # #newModule = SpectrumNdPane(parent=self, title='Module %s' % str(self.moduleCount+1),
    # newModule = SpectrumNdDisplay(title='Module %s_Nd' % str(self.moduleCount+1),
    #                            current=self.current, pid='QP:%s' % str(self.moduleCount+1),
    #                            preferences=self.preferences, mainWindow=self)
    # self.panes[newModule.pid] = newModule
    # newModule.project = self.project
    # newModule.current = self.current
    # self.moduleCount+=1
    #
    # self.dockArea.addDock(newModule.dock)
    # return newModule

  def setShortcuts(self):
    toggleConsoleShortcut = QtGui.QShortcut(QtGui.QKeySequence("p, y"), self, self.toggleConsole)
    toggleCrossHairShortcut = QtGui.QShortcut(QtGui.QKeySequence("c, h"), self, self.toggleCrossHair)
    toggleGridShortcut = QtGui.QShortcut(QtGui.QKeySequence("g, s"), self, self.toggleGrid)


  def dropEvent(self, event):
    '''if object can be dropped into this area, accept dropEvent, otherwise throw an error
        spectra, projects and peak lists can be dropped into this area but nothing else
        if project is dropped, it is loaded,
        if spectra/peak lists are dropped, these are displayed in the side bar but not displayed in
        spectrumPane
        '''

    event.accept()
    data = event.mimeData()
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():


      filePaths = [url.path() for url in event.mimeData().urls()]

      if filePaths:

        if len(filePaths) == 1:
          global project
          currentProjectDir = filePaths[0]

          self.openProject(projectDir=filePaths[0])
                # peakListItem.setData(0, QtCore.Qt.UserRole + 1, peakList)
                # peakListItem.setData(1, QtCore.Qt.DisplayRole, str(peakList))
          # self.statusBar().showMessage(msg)
          # self.pythonConsole.write("openProject('"+currentProjectDir.name+"')\n")
          # list1 = self.spectrumItem.takeChildren()
          # for item in list1:

        else:
          spectrumFormat = specUtil.getSpectrumFileFormat(filePaths[0])

          if spectrumFormat:
            event.acceptProposedAction()
            dataSource = loadSpectrum(self.project,filePaths[0])


          # if dataSource.numDim == 1:
          #   data = Spectrum1dItem(self.current.pane,dataSource).spectralData
          #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
          # elif dataSource.numDim > 1:
          #   data = SpectrumNdItem(self.spectrumPane,dataSource).spectralData
          #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
            msg = dataSource.name+' loaded'
            self.statusBar().showMessage(msg)
            self.pythonConsole.write("loadSpectrum('"+filePaths[0]+"')\n")

          # peakListFormat = getPeakListFileFormat(filePaths[0])
          # if peakListFormat:
          #   event.acceptProposedAction()
          #   self.mainApp.openPeakList(filePaths[0])
          #   return

          else:
            event.ignore()

      else:
        event.ignore()

    else:
      event.ignore()