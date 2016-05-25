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

import importlib
import sys

# NB Neccessary to force load of graphics classes
# NB TODO Should later be moved to within setup rather than import level
from ccpn import core
from ccpn.ui import _implementation
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project


from ccpn.ui.gui.widgets.Application import Application
from ccpn.ui.gui.widgets.SplashScreen import SplashScreen
from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup

from ccpn.util import Register

# This import initializes relative paths for QT style-sheets.  Do not remove!
from ccpn.ui.gui.widgets import resources_rc


# Map of core classes to equivalent Gui classes
_coreClass2UiClass = {}


class Gui:
  
  def __init__(self, framework):
    
    self.framework = framework
    
    self.application = None
    self.mainWindow = None

    self._initQtApp()


  def _initQtApp(self):
    # On the Mac (at least) it does not matter what you set the applicationName to be,
    # it will come out as the executable you are running (e.g. "python3")
    self.application = Application(self.framework.applicationName,
                                   self.framework.applicationVersion,
                                   organizationName='CCPN', organizationDomain='ccpn.ac.uk')
    self.application.setStyleSheet(self.framework.styleSheet)

  def setUp(self):
    """Set up and connect UI classes before start"""
    _setUp()

  def start(self):
    """Start the program execution"""

    self._checkRegistered()
    Register.updateServer(Register.loadDict(), self.framework.applicationVersion)

    # Set up mainWindow
    self._setupMainWindow()

    self.framework.initGraphics()

    # show splash screen
    splash = SplashScreen()
    self.application.processEvents()  # needed directly after splashScreen show to show something

    sys.stderr.write('==> Gui interface is ready\n' )

    splash.finish(self.mainWindow)
    
    self.application.start()
    
  def _checkRegistered(self):
    """Check if registered and if not popup registration and if still no good then exit"""
    
    # checking the registration; need to have the app running, but before the splashscreen, as it will hang
    # in case the popup is needed.
    # We want to give some feedback; sometimes this takes a while (e.g. poor internet)
    sys.stderr.write('==> Checking registration ... \n')
    sys.stderr.flush()  # It seems to be necessary as without the output comes after the registration screen
    if not self._isRegistered:
      self._showRegisterPopup()
      if not self._isRegistered:
        sys.stderr.write('\n### INVALID REGISTRATION, terminating\n')
        sys.exit(1)
    sys.stderr.write('==> Registered to: %s (%s)\n' %
                     (self.framework.registrationDict['name'],
                      self.framework.registrationDict['organisation']))
                     
  @property
  def _isRegistered(self):
    """return True if registered"""
    return True
    return not Register.isNewRegistration(Register.loadDict())

  def _showRegisterPopup(self):
    """Display registration popup"""

    popup = RegisterPopup(version=self.framework.applicationVersion, modal=True)
    popup.show()
    popup.raise_()
    popup.exec_()
    self.application.processEvents()

  def _setupMainWindow(self):
    # Set up mainWindow

    # NBNB TODO this could do with refactoring - e.g. is this really the way to get to project?
    project = self.framework.current._project


    mainWindow = self.framework.mainWindow
    mainWindow.sideBar.setProject(project)
    mainWindow.sideBar.fillSideBar(project)
    mainWindow.raise_()
    mainWindow.namespace['current'] = self.framework.current

    # # NBNB HACK TODO this must be repaired:
    # self.framework.mainWindow = mainWindow
    # mainWindow._appBase = self.framework

    return mainWindow


#######################################################################################
#
#  Ui classes that map ccpn.ui._implementation
#

## Window class
from ccpn.ui.gui.modules.GuiWindow import GuiWindow
from ccpn.ui.gui.modules.GuiMainWindow import GuiMainWindow
from ccpn.ui._implementation import Window
class GeneralGuiWindow(Window.Window, GuiWindow):
  # Necessary as local superclass of different Window types
  @staticmethod
  def _factoryFunction(project:Project, wrappedData:Window.ApiWindow) ->Window:
    """create Window, dispatching to subtype depending on wrappedData"""
    if wrappedData.title == 'Main':
      return MainWindow(project, wrappedData)
    else:
      return SideWindow(project, wrappedData)

class MainWindow(GeneralGuiWindow, GuiMainWindow):
  """GUI main window, corresponds to OS window"""

  def __init__(self, project: core.Project.Project, wrappedData: Window.ApiWindow):
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiMainWindow.__init__(self)

class SideWindow(GeneralGuiWindow, GuiWindow):
  """GUI side window, corresponds to OS window"""

  def __init__(self, project:core.Project, wrappedData:Window.ApiWindow):
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiWindow.__init__(self)

# NB GuiMainWindow is a subclass of GuiWindow
_coreClass2UiClass[Window.Window] = GeneralGuiWindow


## Task class
# There is no special GuiTask, so nothing needs to be done


## Mark class
# There is no special GuiMark, so nothing needs to be done


## SpectrumDisplay class
from ccpn.ui.gui.modules.GuiStripDisplay1d import GuiStripDisplay1d
from ccpn.ui.gui.modules.GuiStripDisplayNd import GuiStripDisplayNd
from ccpn.ui.gui.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui._implementation import SpectrumDisplay
class GeneralGuiSpectrumDisplay(SpectrumDisplay.SpectrumDisplay, GuiSpectrumDisplay):
  # Necessary as local superclass of different SpectrumDisplay types
  @staticmethod
  def _factoryFunction(project:Project,
                       wrappedData:SpectrumDisplay.ApiBoundDisplay) -> SpectrumDisplay:
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
    if wrappedData.is1d:
      return StripDisplay1d(project, wrappedData)
    else:
      return StripDisplayNd(project, wrappedData)

class StripDisplay1d(GeneralGuiSpectrumDisplay, GuiStripDisplay1d):
  """1D bound display"""

  def __init__(self, project:Project, wrappedData:SpectrumDisplay.ApiBoundDisplay):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiStripDisplay1d.__init__(self)


class StripDisplayNd(GeneralGuiSpectrumDisplay, GuiStripDisplayNd):
  """ND bound display"""

  def __init__(self, project:Project, wrappedData:SpectrumDisplay.ApiBoundDisplay):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiStripDisplayNd.__init__(self)

# NB GuiStripDisplay1d and StripDisplayNd are subclasses of GuiSpectrumDisplay
_coreClass2UiClass[SpectrumDisplay.SpectrumDisplay] = GeneralGuiSpectrumDisplay


## Strip class
from ccpn.ui.gui.modules.GuiStrip1d import GuiStrip1d
from ccpn.ui.gui.modules.GuiStripNd import GuiStripNd
from ccpn.ui.gui.modules.GuiStrip import GuiStrip
from ccpn.ui._implementation import Strip
class GeneralGuiStrip(Strip.Strip, GuiStrip):
  # Necessary as local superclass of different SpectrumDisplay types
  @staticmethod
  def _factoryFunction(project:Project, wrappedData:Strip.ApiBoundStrip):
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
    apiSpectrumDisplay = wrappedData.spectrumDisplay
    if apiSpectrumDisplay.is1d:
      return Strip1d(project, wrappedData)
    else:
      return StripNd(project, wrappedData)

class Strip1d(GeneralGuiStrip, GuiStrip1d):
  """1D strip"""

  def __init__(self, project:Project, wrappedData:Strip.ApiBoundStrip):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiStrip1d.__init__(self)

class StripNd(GeneralGuiStrip, GuiStripNd):
  """ND strip """

  def __init__(self, project:Project, wrappedData:Strip.ApiBoundStrip):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiStripNd.__init__(self)

# NB GuiStripDisplay1d and StripDisplayNd are subclasses of GuiSpectrumDisplay
_coreClass2UiClass[Strip.Strip] = GeneralGuiStrip


## Axis class
# There is no special GuiAxis
from ccpn.ui._implementation import Axis


## SpectrumView class
from ccpn.ui.gui.modules.GuiSpectrumView1d import GuiSpectrumView1d
from ccpn.ui.gui.modules.GuiSpectrumViewNd import GuiSpectrumViewNd
from ccpn.ui.gui.modules.GuiSpectrumView import GuiSpectrumView
from ccpn.ui._implementation import _SpectrumView
class GeneralGuiSpectrumView(_SpectrumView.SpectrumView, GuiSpectrumView):
  # Necessary as local superclass of different SpectrumDisplay types
  @staticmethod
  def _factoryFunction(project:Project,
                       wrappedData:_SpectrumView.ApiStripSpectrumView) -> GuiSpectrumView:
    """create SpectrumView, dispatching to subtype depending on wrappedData"""
    if 'intensity' in wrappedData.strip.spectrumDisplay.axisCodes:
      # 1D display
      return SpectrumView1d(project, wrappedData)
    else:
      # ND display
      return  SpectrumViewNd(project, wrappedData)

class SpectrumView1d(GeneralGuiSpectrumView, GuiSpectrumView1d):
  """1D Spectrum View"""

  def __init__(self, project:Project, wrappedData:_SpectrumView.ApiStripSpectrumView):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiSpectrumView1d.__init__(self)

class SpectrumViewNd(GeneralGuiSpectrumView, GuiSpectrumViewNd):
  """ND Spectrum View"""

  def __init__(self, project:Project, wrappedData:_SpectrumView.ApiStripSpectrumView):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiSpectrumViewNd.__init__(self)

# NB GuiSpectrumView1d and GuiSpectrumViewNd are subclasses of GuiSpectrumView
_coreClass2UiClass[_SpectrumView.SpectrumView] = GeneralGuiSpectrumView

## PeakListView class
from ccpn.ui.gui.modules.spectrumItems.GuiPeakListView import GuiPeakListView
from ccpn.ui._implementation import _PeakListView
# Define subtypes and factory function
class PeakListView(_PeakListView.PeakListView, GuiPeakListView):
  """Peak List View for 1D or nD PeakList"""

  def __init__(self, project:Project, wrappedData:_PeakListView.ApiStripPeakListView):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiPeakListView.__init__(self)
_coreClass2UiClass[_PeakListView.PeakListView] = PeakListView


def _setUp():
  """Set up and connect UI classes before start

  #CCPNINTERNAL  Used in AppBse"""

  class2file = _implementation._class2file

  for className in _implementation._importOrder:
    module = importlib.import_module('ccpn.ui._implementation.%s'
                                      % class2file.get(className, className))
    cls = getattr(module, className)
    cls = _coreClass2UiClass.get(cls, cls)
    parentClass = cls._parentClass
    if parentClass is not None:
      parentClass._childClasses.append(cls)

  # Link in classes
  Project._linkWrapperClasses()

  # Notifiers
  Strip.Strip.setupCoreNotifier('create', GuiStrip._resetRemoveStripAction)
  Strip.Strip.setupCoreNotifier('delete', GuiStrip._resetRemoveStripAction)

  from ccpn.ui.gui.modules.GuiStrip import _axisRegionChanged
  Axis.Axis.setupCoreNotifier('change', _axisRegionChanged)

  _SpectrumView.SpectrumView.setupCoreNotifier('delete', GuiSpectrumView._deletedSpectrumView)
  _SpectrumView.SpectrumView.setupCoreNotifier('create', GuiSpectrumView._createdSpectrumView)
  _SpectrumView.SpectrumView.setupCoreNotifier('change', GuiSpectrumView._spectrumViewHasChanged)

  _PeakListView.PeakListView.setupCoreNotifier('create', GuiPeakListView._createdPeakListView)
  _PeakListView.PeakListView.setupCoreNotifier('delete',
                                               GuiPeakListView._deletedStripPeakListView)
