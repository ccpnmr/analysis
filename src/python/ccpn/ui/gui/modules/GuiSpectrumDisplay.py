"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:39 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import importlib, os

from PyQt4 import QtGui, QtCore

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpn.core.PeakList import PeakList
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.SpectrumGroupsToolBarWidget import SpectrumGroupsWidget
from ccpn.ui.gui.widgets.ToolBar import ToolBar

import typing

from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.PhasingFrame import PhasingFrame
from ccpn.ui.gui.widgets.SpectrumToolBar import SpectrumToolBar
from ccpn.ui.gui.widgets.Widget import ScrollableWidget, Widget
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea

from ccpn.ui.gui.widgets.MessageDialog import showWarning, showInfo
from ccpn.ui.gui.widgets.BasePopup import BasePopup
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier

from ccpn.util.Logging import getLogger


class GuiSpectrumDisplay(CcpnModule):
  """
  Main spectrum display Module object.

  This module inherits the following attributes from the SpectrumDisplay wrapper class:

  title             Name of spectrumDisplay;
                      :return <str>
  stripDirection    Strip axis direction
                      :return <str>:('X', 'Y', None) - None only for non-strip plots
  stripCount        Number of strips
                      :return <str>.
  comment           Free-form text comment
                      comment = <str>
                      :return <str>
  axisCodes         Fixed string Axis codes in original display order
                      :return <tuple>:(X, Y, Z1, Z2, ...)
  axisOrder         String Axis codes in display order, determine axis display order
                      axisOrder = <sequence>:(X, Y, Z1, Z2, ...)
                      :return <tuple>:(X, Y, Z1, Z2, ...)
  is1D              True if this is a 1D display
                      :return <bool>
  window            Gui window showing SpectrumDisplay
                      window = <Window>
                      :return <Window>
  nmrResidue        NmrResidue attached to SpectrumDisplay
                      nmrResidue = <NmrResidue>
                      :return <NmrResidue>
  positions         Axis centre positions, in display order
                      positions = <Tuple>
                      :return <Tuple>
  widths            Axis display widths, in display order
                      widths = <Tuple>
                      :return <Tuple>
  units             Axis units, in display order
                      :return <Tuple>

  parameters        Keyword-value dictionary of parameters.
                      NB the value is a copy - modifying it will not modify the actual data.
                      Values can be anything that can be exported to JSON,
                      including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
                      or pandas DataFrame, Series, or Panel
                      :return <dict>
  setParameter      Add name:value to parameters, overwriting existing entries
                      setParameter(name:str, value)
                        :param name:<str> name of parameter
                        :param value: value to set
  deleteParameter   Delete parameter
                      deleteParameter(name:str)
                        :param name:<str> name of parameter to delete
  clearParameters   Delete all parameters
  updateParameters  Update list of parameters
                      updateParameters(value:dict)
                        :param value:<dict> parameter list

  resetAxisOrder    Reset display to original axis order
  findAxis          Find axis
                      findAxis(axisCode)
                        :param axisCode:
                        :return axis
  """

  # overide in specific module implementations
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsOnTop = True
  settingsMinimumSizes = (250, 50)

  def __init__(self, mainWindow, name, useScrollArea=False):
    """
    Initialise the Gui spectrum display object
    
    :param mainWindow: MainWindow instance
    :param name: Title-bar name for the Module
    :param useScrollArea: Having a scrolled widget containing OpenGL and PyQtGraph widgets does not seem to work.
                          The leftmost strip is full of random garbage if it's not completely visible.
                          So for now add option below to have it turned off (False) or on (True).
    """

    print('GuiSpectrumDisplay>> mainWindow, name:', mainWindow, name)
    super(GuiSpectrumDisplay, self).__init__(mainWindow=mainWindow, name=name,
                                             size=(1100, 1300), autoOrientation=False
                                             )
    # print('GuiSpectrumDisplay>> self.layout:', self.layout)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    # derive current from application
    self.current = mainWindow.application.current
    # cannot set self.project because self is a wrapper object
    # self.project = mainWindow.application.project

    # self.mainWidget will be the parent of all the subsequent widgets
    qtParent = self.mainWidget

    # GWV: Not sure what the widget argument is for
    self.spectrumToolBar = SpectrumToolBar(parent=qtParent, widget=self,
                                           grid=(0, 0), gridSpan=(1, 6))
    self.spectrumToolBar.setFixedHeight(30)

    # Utilities Toolbar; filled in Nd/1d classes
    self.spectrumUtilToolBar = ToolBar(parent=qtParent, iconSizes=(24,24),
                                       grid=(0, 6), gridSpan=(1, 1),
                                       hPolicy='minimal', hAlign='right')
    #self.spectrumUtilToolBar.setFixedWidth(150)
    self.spectrumUtilToolBar.setFixedHeight(self.spectrumToolBar.height())
    if self.application.preferences.general.showToolbar:
      self.spectrumUtilToolBar.show()
    else:
      self.spectrumUtilToolBar.hide()

    self.stripFrame = Frame(setLayout=True, showBorder=True)

    if useScrollArea:
      # scroll area for strips
      # This took a lot of sorting-out; better leave as is or test thoroughly
      self._stripFrameScrollArea = ScrollArea(parent=qtParent, setLayout=False,
                                              scrollBarPolicies = ('always', 'asNeeded'),
                                              acceptDrops=True
                                              )
      self._stripFrameScrollArea.setWidget(self.stripFrame)
      self._stripFrameScrollArea.setWidgetResizable(True)
      qtParent.getLayout().addWidget(self._stripFrameScrollArea, 1, 0, 1, 7)
    else:
      qtParent.getLayout().addWidget(self.stripFrame, 1, 0, 1, 7)

    includeDirection = not self.is1D
    self.phasingFrame = PhasingFrame(parent=qtParent,
                                     showBorder=True,
                                     includeDirection=includeDirection,
                                     callback=self._updatePhasing,
                                     returnCallback=self._updatePivot,
                                     directionCallback=self._changedPhasingDirection,
                                     grid=(2, 0), gridSpan=(1, 7), hAlign='top')
    self.phasingFrame.setVisible(False)

    self.stripFrame.setAcceptDrops(True)
    self.droppedNotifier = GuiNotifier(self.stripFrame,
                                       [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                       self._processDroppedItems)

    # GWV: This assures that a 'hoverbar' is visible over the strip when dragging
    # the module to another location
    self.hoverEvent = self._hoverEvent

  def _hoverEvent(self, event):
    event.accept()

  def _processDroppedItems(self, data):
    """
    CallBack for Drop events
    
    CCPN INTERNAL: Also called from GuiStrip
    """
    for ii, pid in enumerate(data.get('pids',[])):
      print('GuiSpectrumDisplay._processDroppedItems>>> dropped:', pid)
      self._handlePid(pid)

  #TODO:LUCA: add handling for SpectrumGroup Pids; also do so in BlankDisplay
  def _handlePid(self, pid):
    "handle a; return True in case it is a Spectrum or a SpectrumGroup"
    success = False
    obj = self.project.getByPid(pid)
    if obj is not None and isinstance(obj, Spectrum):
      self.displaySpectrum(obj)
      success = True
    elif obj is not None and isinstance(obj, PeakList):
      self._handlePeakList(obj)
    elif obj is not None and isinstance(obj, SpectrumGroup):
      self._handleSpectrumGroup(obj)
    else:
      showWarning('Dropped item "%s"' % obj.pid, 'Wrong kind; drop Spectrum, SpectrumGroup or PeakList')
    return success

  def _handlePeakList(self, peakList):
    "See if peaklist can be copied"
    spectrum = peakList.spectrum
    #TODO:GEERTEN: Ask rasmus how to match axis codes
    if spectrum.dimensionCount != self.strips[0].spectra[0].dimensionCount or \
      not True: # peakList.spectrum.axisCodes match
      showWarning('Dropped PeakList "%s"' % peakList.pid, 'Cannot copy: Axes do not match')
      return
    #TODO:implement
    showInfo(title='Copy PeakList "%s"' % peakList.pid, message='Copy to selected spectra')

  def _handleSpectrumGroup(self, spectrumGroup):
    '''
    Plots spectrumGroups in a grouped display if not already plotted and create its button on spectrumGroups toolBar.
    If a spectrum is already plotted in a display and a group is dropped, all its spectra will be displayed except the
    one already in.
    '''
    if len(spectrumGroup.spectra)>0:
      for spectrumView in self.spectrumViews:
        if len(spectrumView.spectrum.spectrumGroups)>0:
          displayedSpectrumGroups = [spectrumView.spectrum.spectrumGroups[0]
                                     for spectrumView in self.spectrumViews]

          spectrumGroups = [spectrumGroup for spectrumGroup in self._appBase.project.spectrumGroups
                       if spectrumGroup not in displayedSpectrumGroups and spectrumGroup.pid == pids[0]]

        else:
          for spectrum in spectrumGroup.spectra:
            self.displaySpectrum(spectrum)

        if hasattr(self, 'isGrouped'):
          if self.isGrouped:
            if len(spectrumGroups)>0:

              spectrumGroupsToolBar = self.strips[0].spectrumViews[0].spectrumGroupsToolBar
              spectrumGroupButton = SpectrumGroupsWidget(self, self._appBase.project, self.strips[0], pids[0])
              spectrumGroupsToolBar.addWidget(spectrumGroupButton)
              for spectrum in spectrumGroups[0].spectra:
                self.displaySpectrum(spectrum)
          else:
            print("SpectrumGroups cannot be displayed in a display with already spectra in it."
                  "\nSpectrumGroup's spectra are added as single item in the display  ")


  def setScrollbarPolicies(self, horizontal='asNeeded', vertical='asNeeded'):
    "Set the scrolbar policies; convenience to expose to the user"
    from ccpn.ui.gui.widgets.Frame import SCROLLBAR_POLICY_DICT

    if horizontal not in SCROLLBAR_POLICY_DICT or \
       vertical not in SCROLLBAR_POLICY_DICT:
      getLogger().warning('Invalid scrollbar policy (%s, %s)' %(horizontal, vertical))
    self.stripFrame.setScrollBarPolicies((horizontal, vertical))

  def _updatePivot(self):
    """Updates pivot in all strips contained in the spectrum display."""
    for strip in self.strips:
      strip._updatePivot()
    
  def _updatePhasing(self):
    """Updates phasing in all strips contained in the spectrum display."""
    for strip in self.strips:
      strip._updatePhasing()
    
  def _changedPhasingDirection(self):
    """Changes direction of phasing from horizontal to vertical or vice versa."""
    for strip in self.strips:
      strip._changedPhasingDirection()
    
  def togglePhaseConsole(self):
    """Toggles whether phasing console is displayed.
    """
    isVisible = not self.phasingFrame.isVisible()
    self.phasingFrame.setVisible(isVisible)
    for strip in self.strips:
      if isVisible:
        strip.turnOnPhasing()
      else:
        strip.turnOffPhasing()
    self._updatePhasing()

  def showToolbar(self):
    """show the toolbar"""
    # showing the toolbar, but we need to update the checkboxes of all strips as well.
    self.spectrumUtilToolBar.show()
    for strip in self.strips:
      strip.toolbarAction.setChecked(True)

  def hideToolbar(self):
    """hide the toolbar"""
    # hiding the toolbar, but we need to update the checkboxes of all strips as well.
    self.spectrumUtilToolBar.hide()
    for strip in self.strips:
      strip.toolbarAction.setChecked(False)

  def toggleToolbar(self):
    """Toggle the toolbar """
    if not self.spectrumUtilToolBar.isVisible():
      self.showToolbar()
    else:
      self.hideToolbar()

  def _closeModule(self):
    """
    Closes spectrum display and deletes it from the project.
    """
    for strip in self.strips:
      strip._unregisterStrip()
    # self.module.close()
    #self.delete()
    CcpnModule._closeModule(self)

  def removeStrip(self, strip):
    "Remove strip if it belongs to self"

    if strip is None:
      showWarning('Remove strip', 'Invalid strip' )
      return

    if strip not in self.strips:
      showWarning('Remove strip', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
                  % (strip.pid, self.pid))
      return

    if len(self.orderedStrips) == 1:
      showWarning('Remove strip', 'Last strip of SpectrumDisplay "%s" cannot be removed' \
                  % (self.pid,))
      return
    strip._unregisterStrip()
    strip.delete()

  def removeCurrentStrip(self):
    "Remove current.strip if it belongs to self"
    if self.current.strip is None:
      showWarning('Remove current strip', 'Select first in SpectrumDisplay by clicking')
      return
    self.removeStrip(self.current.strip)

  # def duplicateStrip(self):
  #   """
  #   Creates a new strip identical to the last one created and adds it to right of the display.
  #   """
  #   newStrip = self.strips[-1].clone()

  def addStrip(self, stripIndex=-1) -> 'GuiStripNd':
    """
    Creates a new strip by cloning strip with index (default the last) in the display.
    """
    newStrip = self.strips[stripIndex].clone()
    mainWindow = self.mainWindow
    mainWindow.pythonConsole.writeConsoleCommand("strip.clone()", strip=newStrip)
    getLogger().info("spectrumDisplay = ui.getByGid(%r); spectrumDisplay.addStrip(%d)" \
                     % (self.pid, stripIndex))
    return newStrip

  def resetYZooms(self):
    """Zooms Y axis of current strip to show entire region"""
    for strip in self.strips:
      strip.resetYZoom()

  def resetXZooms(self):
    """Zooms X axis of current strip to show entire region"""
    for strip in self.strips:
      strip.resetXZoom()

  def _restoreZoom(self):
    """Restores last saved zoom of current strip."""
    try:
      if not self.current.strip:
        showWarning('Restore Zoom', 'No strip selected')
        return
      if self.current.strip not in self.strips:
        showWarning('Restore Zoom', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
                    % (self.current.strip.pid, self.pid))
        return
      else:
        self.current.strip._restoreZoom()         # ejb - could be empty strip
    except:
      pass

  def _storeZoom(self):
    """Saves zoomed region of current strip."""
    try:
      if not self.current.strip:
        showWarning('Store Zoom', 'No strip selected')
        return
      if self.current.strip not in self.strips:
        showWarning('Store Zoom', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
                    % (self.current.strip.pid, self.pid))
        return
      else:
        self.current.strip._storeZoom()         # ejb - could be empty strip
    except:
      pass

  def toggleCrossHair(self):
    """Toggles whether cross hair is displayed in all strips of spectrum display."""
    # toggle crosshairs for strips in this spectrumDisplay
    for strip in self.strips:
      strip._toggleCrossHair()
    
  def toggleGrid(self):
    """Toggles whether grid is displayed in all strips of spectrum display."""
    # toggle grid for strips in this spectrumDisplay
    for strip in self.strips:
      strip.toggleGrid()

  def _deletedPeak(self, peak):
    apiPeak = peak._wrappedData
    # NBNB TBD FIXME rewrite this to not use API peaks
    # ALSO move this machinery from subclasses to this class.
    for peakListView in self.activePeakItemDict:
      peakItemDict = self.activePeakItemDict[peakListView]
      peakItem = peakItemDict.get(apiPeak)
      if peakItem:
        peakListView.spectrumView.strip.plotWidget.scene().removeItem(peakItem)
        del peakItemDict[apiPeak]
        inactivePeakItems = self.inactivePeakItemDict.get(peakListView)
        if inactivePeakItems:
          inactivePeakItems.add(peakItem)

  # def _resetRemoveStripAction(self):
  #   """
  #   # CCPNINTERNAL - called from GuiMainWindow and from GuiStrip to manage removeStrip button enabling,
  #   and from Framework to set up initial state
  #   """
  #   #TODO:WAYNE: FrameWork should not have anything to do with this
  #   strip = self.current.strip
  #   # # Rasmus HACK!
  #   # # This code broke because it got triggered (via a current notifier) when strips
  #   # # were deleted but self was not. A bigger fix is needed (TODO), but for now try this
  #   myStrips = [self.project._data2Obj.get(x) for x in self._wrappedData.strips]
  #   if len(myStrips) <= 1 or not strip in myStrips:
  #     # current.strip not in display, or only 1 strip in display, so disable removeStrip button
  #     enabled = False
  #   else:
  #     enabled = True
  #   self.removeStripAction.setEnabled(enabled)
  #
  #   # strips = set(self._appBase.current.strips)
  #   # # Rasmus HACK!
  #   # # This code broke because it got triggered (via a current notifier) when strips
  #   # # were deleted but self was not. A bigger fix is needed, but for now try this
  #   # myStrips = [self._project._data2Obj.get(x) for x in self._wrappedData.strips]
  #   # myStrips = [x for x in myStrips if x is not None]
  #   # if len(myStrips) <= 1 or not strips.intersection(myStrips):
  #   # # if not strips.intersection(self.strips) or len(self.strips) == 1:
  #   #   # no strip in display is in current.strips, or only 1 strip in display, so disable removeStrip button
  #   #   enabled = False
  #   # else:
  #   #   enabled = True
  #   # self.removeStripAction.setEnabled(enabled)

  def displaySpectrum(self, spectrum, axisOrder:(str,)=()):
    """Display additional spectrum, with spectrum axes ordered according ton axisOrder
    """
    spectrum = self.getByPid(spectrum) if isinstance(spectrum, str) else spectrum

    self._startCommandEchoBlock('displaySpectrum', spectrum, values=locals(),
                                defaults={'axisOrder':()})
    try:
      self.strips[0].displaySpectrum(spectrum, axisOrder=axisOrder)
    finally:
      self._endCommandEchoBlock()

def _deletedPeak(peak:Peak):
  """Function for notifiers.
  #CCPNINTERNAL """

  for spectrumView in peak.peakList.spectrum.spectrumViews:
    spectrumView.strip.spectrumDisplay._deletedPeak(peak)

def _spectrumHasChanged(spectrum:Spectrum):
  project = spectrum.project
  apiDataSource = spectrum._wrappedData
  for spectrumDisplay in project.spectrumDisplays:
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
    if action: # spectrum might not be in all displays
      # update toolbar button name
      action.setText(spectrum.name)

def _deletedSpectrumView(project:Project, apiSpectrumView):
  """tear down SpectrumDisplay when new SpectrumView is deleted - for notifiers"""
  spectrumDisplay = project._data2Obj[apiSpectrumView.spectrumDisplay]
  apiDataSource = apiSpectrumView.dataSource

  # remove toolbar action (button)
  # NBNB TBD FIXME get rid of API object from code
  action = spectrumDisplay.spectrumActionDict.get(apiDataSource)  # should always be not None
  if action:
    spectrumDisplay.spectrumToolBar.removeAction(action)
    del spectrumDisplay.spectrumActionDict[apiDataSource]

GuiSpectrumDisplay.processSpectrum = GuiSpectrumDisplay.displaySpectrum   # ejb - from SpectrumDisplay
