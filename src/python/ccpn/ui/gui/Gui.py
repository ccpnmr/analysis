"""Module Documentation here
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license "
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__version__ = "$Revision: 9315 $"

#=========================================================================================
# Start of code
#=========================================================================================

import sys
import typing

from ccpn.core import _coreClassMap
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib.SpectrumLib import getExperimentClassifications
from ccpn.ui.Ui import Ui
from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup
from ccpn.ui.gui.widgets.Application import Application


# This import initializes relative paths for QT style-sheets.  Do not remove!

class Gui(Ui):

  # Factory functions for UI-specific instantiation of wrapped graphics classes
  _factoryFunctions = {}
  
  def __init__(self, application):
    
    Ui.__init__(self, application)

    self._initQtApp()


  def _initQtApp(self):
    # On the Mac (at least) it does not matter what you set the applicationName to be,
    # it will come out as the executable you are running (e.g. "python3")
    self.qtApp = Application(self.application.applicationName,
                                   self.application.applicationVersion,
                                   organizationName='CCPN', organizationDomain='ccpn.ac.uk')
    self.qtApp.setStyleSheet(self.application.styleSheet)


  def initialize(self, mainWindow):
    """UI operations done after every project load/create"""

    # Set up mainWindow
    self.mainWindow = self._setupMainWindow(mainWindow)

    self.application.initGraphics()

    project = self.application.project

    # Wrapper Notifiers
    from ccpn.ui.gui.modules import GuiStrip
    notifier = project.registerNotifier('Strip', 'create', GuiStrip.GuiStrip._resetRemoveStripAction)
    project.duplicateNotifier('Strip', 'delete', notifier)

    project.registerNotifier('Axis', 'change', GuiStrip._axisRegionChanged)

    from ccpn.ui.gui.modules import GuiSpectrumDisplay
    project.registerNotifier('Peak', 'delete', GuiSpectrumDisplay._deletedPeak)
    project.registerNotifier('Spectrum', 'change', GuiSpectrumDisplay._spectrumHasChanged)

    from ccpn.ui.gui.modules.GuiSpectrumView import GuiSpectrumView
    project.registerNotifier('SpectrumView', 'delete', GuiSpectrumView._deletedSpectrumView)
    project.registerNotifier('SpectrumView', 'create', GuiSpectrumView._createdSpectrumView)
    project.registerNotifier('SpectrumView', 'change', GuiSpectrumView._spectrumViewHasChanged)

    from ccpn.ui.gui.modules.spectrumItems import GuiPeakListView
    project.registerNotifier('PeakListView', 'create',
                             GuiPeakListView.GuiPeakListView._createdPeakListView)
    project.registerNotifier('PeakListView', 'delete',
                             GuiPeakListView.GuiPeakListView._deletedStripPeakListView)
    project.registerNotifier('PeakListView', 'change',
                             GuiPeakListView.GuiPeakListView._changedPeakListView)

    project.registerNotifier('NmrAtom', 'rename', GuiPeakListView._updateAssignmentsNmrAtom)

    project.registerNotifier('Peak', 'change', _coreClassMap['Peak']._refreshPeakPosition)

    from ccpn.ui.gui.widgets import SpinSystemLabel
    project.registerNotifier('NmrResidue', 'rename', SpinSystemLabel._renameNmrResidueForGraphics)


    # API notifiers - see functions for comments on why this is done this way
    project._registerApiNotifier(GuiPeakListView._upDateAssignmentsPeakDimContrib,
                                 'ccp.nmr.Nmr.AbstractPeakDimContrib', 'postInit')
    project._registerApiNotifier(GuiPeakListView._upDateAssignmentsPeakDimContrib,
                                'ccp.nmr.Nmr.AbstractPeakDimContrib', 'preDelete')

    from ccpn.ui.gui.modules import GuiStripDisplayNd
    project._registerApiNotifier(GuiStripDisplayNd._changedBoundDisplayAxisOrdering,
                                 GuiStripDisplayNd.ApiBoundDisplay, 'axisOrder')


    from ccpn.ui.gui.modules import GuiStripDisplay1d
    project._registerApiNotifier(GuiStripDisplay1d._updateSpectrumPlotColour,
                                 GuiStripDisplay1d.ApiDataSource, 'setSliceColour')

    project._registerApiNotifier(GuiStripDisplay1d._updateSpectrumViewPlotColour,
                                 GuiStripDisplay1d.ApiSpectrumView, 'setSliceColour')

    project._registerApiNotifier(GuiStrip._rulerCreated, 'ccpnmr.gui.Task.Ruler', 'postInit')
    project._registerApiNotifier(GuiStrip._rulerDeleted, 'ccpnmr.gui.Task.Ruler', 'preDelete')
    project._registerApiNotifier(GuiStrip._setupGuiStrip, 'ccpnmr.gui.Task.Strip', 'postInit')

    project._registerApiNotifier(GuiSpectrumDisplay._deletedSpectrumView,
                                 'ccpnmr.gui.Task.SpectrumView', 'preDelete')

  def start(self):

    # show splash screen
    # GWV comment out to speed up loading and reduce memory footprint
    #splash = SplashScreen()
    #self.qtApp.processEvents()  # needed directly after splashScreen show to show something
    #splash.close()
    #splash.finish(self.mainWindow)

    self.mainWindow._fillMacrosMenu()
    self.mainWindow.setUserShortcuts(self.mainWindow._appBase.preferences)
    project = self.application.project
    self.application.experimentClassifications = getExperimentClassifications(project)

    sys.stderr.write('==> Gui interface is ready\n' )
    self.qtApp.start()


  def _showRegisterPopup(self):
    """Display registration popup"""

    popup = RegisterPopup(version=self.application.applicationVersion, modal=True)
    popup.show()
    popup.raise_()
    popup.exec_()
    self.qtApp.processEvents()

  def _setupMainWindow(self, mainWindow):
    # Set up mainWindow

    project = self.application.project

    # mainWindow = self.application.mainWindow
    mainWindow.sideBar.setProject(project)
    mainWindow.sideBar.fillSideBar(project)
    mainWindow.raise_()
    mainWindow.namespace['current'] = self.application.current
    return mainWindow


  def echoCommands(self, commands:typing.List[str]):
    """Echo commands strings, one by one, to logger
    and store them in internal list for perusal
    """

    console = self.application.ui.mainWindow.pythonConsole
    logger = self.application.project._logger

    for command in commands:
      console._write(command + '\n')
      logger.info(command)


  def getByGid(self, gid):
    return self.application.project.getByPid(gid)


  def addBlankDisplay(self, position='right', relativeTo=None):
    logParametersString = "position={position}, relativeTo={relativeTo}".format(
      position="'"+position+"'" if isinstance(position, str) else position,
      relativeTo="'"+relativeTo+"'" if isinstance(relativeTo, str) else relativeTo)
    self.application._startCommandBlock('application.ui.addBlankDisplay({})'.format(logParametersString))

    from ccpn.ui.gui.modules.GuiBlankDisplay import GuiBlankDisplay
    try:
      if 'BLANK DISPLAY' in self.mainWindow.moduleArea.findAll()[1]:
        blankDisplay = self.mainWindow.moduleArea.findAll()[1]['BLANK DISPLAY']
        if blankDisplay.isVisible():
          return
        else:
          self.mainWindow.moduleArea.moveModule(blankDisplay, position, None)
      else:
        blankDisplay = GuiBlankDisplay(self.mainWindow.moduleArea)
        self.mainWindow.moduleArea.addModule(blankDisplay, position, None)
      return blankDisplay
    finally:
      self.application._endCommandBlock()


  from ccpn.core.IntegralList import IntegralList
  from ccpn.ui.gui.modules.CcpnModule import CcpnModule
  def showIntegralTable(self, position:str='bottom', relativeTo:CcpnModule=None, selectedList:IntegralList=None):
    logParametersString = "position={position}, relativeTo={relativeTo}, selectedList={selectedList}".format(
      position="'" + position + "'" if isinstance(position, str) else position,
      relativeTo="'" + relativeTo + "'" if isinstance(relativeTo, str) else relativeTo,
      selectedList="'" + selectedList + "'" if isinstance(selectedList, str) else selectedList)
    # log = False
    # import inspect
    # i0, i1 = inspect.stack()[0:2]
    # if i0.function != i1.function:  # Caller function name matches, we don't log...
    #   code_context = i1.code_context[0]
    #   if 'ui.{}('.format(i0.function) in code_context:
    #     log = True
    # if log:
    #   self.application._startCommandBlock(
    #     'application.ui.showIntegralTable({})'.format(logParametersString))
    # try:
    #   from ccpn.ui.gui.modules.IntegralTable import IntegralTable
    #
    #   if 'INTEGRAL TABLE' in self.mainWindow.moduleArea.findAll()[1]:
    #     integralTable = self.mainWindow.moduleArea.findAll()[1]['INTEGRAL TABLE']
    #     if integralTable.isVisible():
    #       return
    #     else:
    #       self.mainWindow.moduleArea.moveModule(integralTable, position=position,
    #                                                 relativeTo=relativeTo)
    #   else:
    #    integralTable = IntegralTable(project=self.application.project, selectedList=selectedList)
    #    self.mainWindow.moduleArea.addModule(integralTable, position=position,
    #                                         relativeTo=relativeTo)
    #
    #   return integralTable
    #
    # finally:
    #   if log:
    #     self.application._endCommandBlock()


########################################################
#
#  Wrapper notifier functions



#######################################################################################
#
#  Ui classes that map ccpn.ui._implementation
#

## Window class
coreClass = _coreClassMap['Window']

from ccpn.ui.gui.modules.GuiMainWindow import GuiMainWindow as _GuiMainWindow
class MainWindow(coreClass, _GuiMainWindow):
  """GUI main window, corresponds to OS window"""
  def __init__(self, project: Project, wrappedData:'ApiWindow'):
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiMainWindow.__init__(self)

from ccpn.ui.gui.modules.GuiWindow import GuiWindow as _GuiWindow
class SideWindow(coreClass, _GuiWindow):
  """GUI side window, corresponds to OS window"""
  def __init__(self, project:Project, wrappedData:'ApiWindow'):
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiWindow.__init__(self)

def _factoryFunction(project:Project, wrappedData) -> coreClass:
  """create Window, dispatching to subtype depending on wrappedData"""
  if wrappedData.title == 'Main':
    return MainWindow(project, wrappedData)
  else:
    return SideWindow(project, wrappedData)

Gui._factoryFunctions[coreClass.className] = _factoryFunction


## Task class
# There is no special GuiTask, so nothing needs to be done


## Mark class - put in namespace for documentation
Mark = _coreClassMap['Mark']


## SpectrumDisplay class
coreClass = _coreClassMap['SpectrumDisplay']
from ccpn.ui.gui.modules.GuiStripDisplay1d import GuiStripDisplay1d as _GuiStripDisplay1d
class StripDisplay1d(coreClass, _GuiStripDisplay1d):
  """1D bound display"""
  def __init__(self, project:Project, wrappedData:'ApiBoundDisplay'):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiStripDisplay1d.__init__(self)

from ccpn.ui.gui.modules.GuiStripDisplayNd import GuiStripDisplayNd as _GuiStripDisplayNd
class StripDisplayNd(coreClass, _GuiStripDisplayNd):
  """ND bound display"""
  def __init__(self, project:Project, wrappedData:'ApiBoundDisplay'):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiStripDisplayNd.__init__(self)

def _factoryFunction(project:Project, wrappedData) -> coreClass:
  """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
  if wrappedData.is1d:
    return StripDisplay1d(project, wrappedData)
  else:
    return StripDisplayNd(project, wrappedData)

Gui._factoryFunctions[coreClass.className] = _factoryFunction

## Strip class
coreClass = _coreClassMap['Strip']
from ccpn.ui.gui.modules.GuiStrip1d import GuiStrip1d as _GuiStrip1d
class Strip1d(coreClass, _GuiStrip1d):
  """1D strip"""
  def __init__(self, project:Project, wrappedData:'ApiBoundStrip'):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiStrip1d.__init__(self)

from ccpn.ui.gui.modules.GuiStripNd import GuiStripNd as _GuiStripNd
class StripNd(coreClass, _GuiStripNd):
  """ND strip """
  def __init__(self, project:Project, wrappedData:'ApiBoundStrip'):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiStripNd.__init__(self)

def _factoryFunction(project:Project, wrappedData) -> coreClass:
  """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
  apiSpectrumDisplay = wrappedData.spectrumDisplay
  if apiSpectrumDisplay.is1d:
    return Strip1d(project, wrappedData)
  else:
    return StripNd(project, wrappedData)

Gui._factoryFunctions[coreClass.className] = _factoryFunction


## Axis class - put in namespace for documentation
Axis = _coreClassMap['Axis']


## SpectrumView class
coreClass = _coreClassMap['SpectrumView']
from ccpn.ui.gui.modules.GuiSpectrumView1d import GuiSpectrumView1d as _GuiSpectrumView1d
class _SpectrumView1d(coreClass, _GuiSpectrumView1d):
  """1D Spectrum View"""
  def __init__(self, project:Project, wrappedData:'ApiStripSpectrumView'):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiSpectrumView1d.__init__(self)

from ccpn.ui.gui.modules.GuiSpectrumViewNd import GuiSpectrumViewNd as _GuiSpectrumViewNd
class _SpectrumViewNd(coreClass, _GuiSpectrumViewNd):
  """ND Spectrum View"""
  def __init__(self, project:Project, wrappedData:'ApiStripSpectrumView'):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiSpectrumViewNd.__init__(self)

def _factoryFunction(project:Project, wrappedData) -> coreClass:
  """create SpectrumView, dispatching to subtype depending on wrappedData"""
  if 'intensity' in wrappedData.strip.spectrumDisplay.axisCodes:
    # 1D display
    return _SpectrumView1d(project, wrappedData)
  else:
    # ND display
    return  _SpectrumViewNd(project, wrappedData)

Gui._factoryFunctions[coreClass.className] = _factoryFunction

## PeakListView class
coreClass = _coreClassMap['PeakListView']
from ccpn.ui.gui.modules.spectrumItems.GuiPeakListView import GuiPeakListView as _GuiPeakListView
class _PeakListView(coreClass, _GuiPeakListView):
  """Peak List View for 1D or nD PeakList"""
  def __init__(self, project:Project, wrappedData:'ApiStripPeakListView'):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    _GuiPeakListView.__init__(self)

Gui._factoryFunctions[coreClass.className] = _PeakListView

# Delete what we do not want in namespace
del _factoryFunction
del coreClass
