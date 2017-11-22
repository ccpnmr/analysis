"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
from functools import partial

from PyQt4 import QtGui, QtCore

from ccpn.core.lib import Util as ccpnUtil

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.popups.ExperimentTypePopup import  _getExperimentTypes
from ccpn.util.Colour import spectrumColours
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger

SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']


class SpectrumDisplayPropertiesPopup(CcpnDialog):
  # The values on the 'General' and 'Dimensions' tabs are queued as partial functions when set.
  # The apply button then steps through each tab, and calls each function in the _changes dictionary
  # in order to set the parameters.

  def __init__(self, parent=None, mainWindow=None, spectrumView=None
               , title='Spectrum Display Properties', **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current
    self.spectrumView = spectrumView

    # self.tabWidget = QtGui.QTabWidget()
    #
    # self.tabWidget.addTab(self._contoursTab, "Contours")

    self._contoursTab = ContoursTab(spectrumView=spectrumView, parent=self, mainWindow=mainWindow)
    self.layout().addWidget(self._contoursTab, 0, 0, 2, 4)

    Button(self, grid=(2, 1), callback=self.reject, text='Cancel',vPolicy='fixed')
    self.applyButton = Button(self, grid=(2, 2), callback=self._applyChanges, text='Apply', vPolicy='fixed')
    # self.applyButton.setEnabled(False)
    Button(self, grid=(2, 3), callback=self._okButton, text='Ok', vPolicy='fixed')

    # if sys.platform.lower() == 'linux':
    #   if spectrum.project._appBase.colourScheme == 'dark':
    #     self.setStyleSheet("QTabWidget > QWidget{ background-color:  #2a3358; color: #f7ffff; padding:4px;}")
    #   elif spectrum.project._appBase.colourScheme == 'light':
    #     self.setStyleSheet("QTabWidget > QWidget { background-color: #fbf4cc;} QTabWidget { background-color: #fbf4cc;}")

  def _keyPressEvent(self, event):
    if event.key() == QtCore.Qt.Key_Enter:
      pass

  def _repopulate(self):
    if self._contoursTab:
      self._contoursTab._repopulate()

  def _applyAllChanges(self, changes):
    for v in changes.values():
      v()

  def _applyChanges(self):
    """
    The apply button has been clicked
    Define an undo block for setting the properties of the object
    If there is an error setting any values then generate an error message
      If anything has been added to the undo queue then remove it with application.undo()
      repopulate the popup widgets
    """
    # tabs = self.tabWidget.findChildren(QtGui.QStackedWidget)[0].children()
    # tabs = [t for t in tabs if not isinstance(t, QtGui.QStackedLayout)]

    # ejb - error above, need to set the tabs explicitly
    tabs = (self._contoursTab, )

    applyAccept = False
    oldUndo = self.project._undo.numItems()

    self.project._startCommandEchoBlock('_applyChanges')
    try:
      for t in tabs:
        if t is not None:
          changes = t._changes
          self._applyAllChanges(changes)

      applyAccept = True
    except Exception as es:
      showWarning(str(self.windowTitle()), str(es))
    finally:
      self.project._endCommandEchoBlock()

    if applyAccept is False:
      # should only undo if something new has been added to the undo deque
      # may cause a problem as some things may be set with the same values
      # and still be added to the change list, so only undo if length has changed
      errorName = str(self.__class__.__name__)
      if oldUndo != self.project._undo.numItems():
        self.project._undo.undo()
        getLogger().debug('>>>Undo.%s._applychanges' % errorName)
      else:
        getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

      # repopulate popup
      self._repopulate()
      return False
    else:
      return True

  def _okButton(self):
    if self._applyChanges() is True:
      self.accept()


class ContoursTab(QtGui.QWidget, Base):
  def __init__(self, spectrumView=None, parent=None, mainWindow=None):
    super(ContoursTab, self).__init__(parent)
    Base.__init__(self, setLayout=True)      # ejb

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    self.spectrumView = spectrumView

    spectrum = self.current.strip.spectra[0]
    self.spectrum = spectrum

    if self.spectrum.project._appBase.ui.mainWindow is not None:
      mainWindow = self.spectrum.project._appBase.ui.mainWindow
    else:
      mainWindow = self.spectrum.project._appBase._mainWindow

    self.pythonConsole = mainWindow.pythonConsole
    self.logger = self.spectrum.project._logger

    # TODO self._changes looks unused, as do all the functions put in it
    # Check if the lot can be removed
    self._changes = dict()

    positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(1, 0), vAlign='t', hAlign='l')
    positiveContoursCheckBox = CheckBox(self, grid=(1, 1), checked=True, vAlign='t', hAlign='l')
    for spectrumView in self.spectrum.spectrumViews:
      if spectrumView.displayPositiveContours:
        positiveContoursCheckBox.setChecked(True)
      else:
        positiveContoursCheckBox.setChecked(False)
    self.layout().addItem(QtGui.QSpacerItem(0, 10), 0, 0)
    positiveContoursCheckBox.stateChanged.connect(self._queueChangePositiveContourDisplay)

    positiveBaseLevelLabel = Label(self, text="Positive Base Level", grid=(2, 0), vAlign='c', hAlign='l')
    positiveBaseLevelData = DoubleSpinbox(self, grid=(2, 1), vAlign='t')
    positiveBaseLevelData.setMaximum(1e12)
    positiveBaseLevelData.setMinimum(0.1)
    positiveBaseLevelData.setValue(spectrum.positiveContourBase)
    positiveBaseLevelData.valueChanged.connect(partial(self._queueChangePositiveBaseLevel, spectrum))
    # positiveBaseLevelData.setSingleStep(positiveBaseLevelData.value()*(positiveMultiplierData.value()-1))
    # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
    positiveBaseLevelData.setSingleStep(positiveBaseLevelData.value()*0.1)

    positiveMultiplierLabel = Label(self, text="Positive Multiplier", grid=(3, 0), vAlign='c', hAlign='l')
    positiveMultiplierData = DoubleSpinbox(self, grid=(3, 1), vAlign='t')
    positiveMultiplierData.setSingleStep(0.1)
    positiveMultiplierData.setValue(float(spectrum.positiveContourFactor))
    positiveMultiplierData.valueChanged.connect(partial(self._queueChangePositiveContourMultiplier, spectrum))

    positiveContourCountLabel = Label(self, text="Number of positive contours", grid=(4, 0), vAlign='c', hAlign='l')
    positiveContourCountData = Spinbox(self, grid=(4, 1), vAlign='t')
    positiveContourCountData.setValue(int(spectrum._apiDataSource.positiveContourCount))
    positiveContourCountData.valueChanged.connect(partial(self._queueChangePositiveContourCount, spectrum))
    positiveContourColourLabel = Label(self, text="Positive Contour Colour", grid=(5, 0), vAlign='c', hAlign='l')

    self.positiveColourBox = PulldownList(self, grid=(5, 1), vAlign='t')
    for item in spectrumColours.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      indx = list(spectrumColours.keys()).index(spectrum.positiveContourColour)
    except ValueError:
      # Set to default (colour 0)
      indx = 0
      spectrum.positiveContourColour = list(spectrumColours.keys())[indx]
    self.positiveColourBox.setCurrentIndex(indx)
    self.positiveColourBox.currentIndexChanged.connect(partial(self._queueChangePosColourComboIndex, spectrum))

    self.positiveColourButton = Button(self, grid=(5, 2), vAlign='t', hAlign='l',
                                       icon='icons/colours', hPolicy='fixed')
    self.positiveColourButton.clicked.connect(partial(self._queueChangePosSpectrumColour, spectrum))

    negativeContoursLabel = Label(self, text="Show Negative Contours", grid=(6 ,0), vAlign='c', hAlign='l')
    negativeContoursCheckBox = CheckBox(self, grid=(6, 1), checked=True, vAlign='t', hAlign='l')
    for spectrumView in self.spectrum.spectrumViews:
      if spectrumView.displayNegativeContours:
        negativeContoursCheckBox.setChecked(True)
      else:
        negativeContoursCheckBox.setChecked(False)
    negativeContoursCheckBox.stateChanged.connect(self._queueChangeNegativeContourDisplay)

    negativeBaseLevelLabel = Label(self, text="Negative Base Level", grid=(7, 0), vAlign='c', hAlign='l')
    negativeBaseLevelData = DoubleSpinbox(self, grid=(7, 1), vAlign='t')
    negativeBaseLevelData.setMaximum(-0.1)
    negativeBaseLevelData.setMinimum(-1e12)
    negativeBaseLevelData.setValue(spectrum.negativeContourBase)
    negativeBaseLevelData.valueChanged.connect(partial(self._queueChangeNegativeBaseLevel, spectrum))
    # negativeBaseLevelData.setSingleStep((negativeBaseLevelData.value()*-1)*negativeMultiplierData.value()-1)
    # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
    negativeBaseLevelData.setSingleStep((negativeBaseLevelData.value()*-1)*0.1)

    negativeMultiplierLabel = Label(self, text="Negative Multiplier", grid=(8, 0), vAlign='c', hAlign='l')
    negativeMultiplierData = DoubleSpinbox(self, grid=(8, 1), vAlign='t')
    negativeMultiplierData.setValue(spectrum.negativeContourFactor)
    negativeMultiplierData.setSingleStep(0.1)
    negativeMultiplierData.valueChanged.connect(partial(self._queueChangeNegativeContourMultiplier, spectrum))

    negativeContourCountLabel = Label(self, text="Number of negative contours", grid=(9, 0), vAlign='c', hAlign='l')
    negativeContourCountData = Spinbox(self, grid=(9, 1), vAlign='t')
    negativeContourCountData.setValue(spectrum.negativeContourCount)
    negativeContourCountData.valueChanged.connect(partial(self._queueChangeNegativeContourCount, spectrum))
    negativeContourColourLabel = Label(self, text="Negative Contour Colour",grid=(10, 0), vAlign='c', hAlign='l')

    self.negativeColourBox = PulldownList(self, grid=(10, 1), vAlign='t')
    for item in spectrumColours.items():
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(item[0]))
      self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      indx = list(spectrumColours.keys()).index(spectrum.negativeContourColour)
    except ValueError:
      # Set to default (colour 1)
      indx = 1
      spectrum.negativeContourColour = list(spectrumColours.keys())[indx]
    self.negativeColourBox.setCurrentIndex(indx)
    self.negativeColourBox.currentIndexChanged.connect(
      partial(self._queueChangeNegColourComboIndex, spectrum)
    )
    self.negativeColourButton = Button(self, grid=(10, 2), icon='icons/colours', hPolicy='fixed',
                                       vAlign='t', hAlign='l')
    self.negativeColourButton.clicked.connect(partial(self._queueChangeNegSpectrumColour, spectrum))

  def _repopulate(self):
    # don't need anything here as can't generate any errors
    pass

  def _writeLoggingMessage(self, command):
    self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
    self.logger.info(command)


  def _queueChangePositiveContourDisplay(self, state):
    self._changes['positiveContourDisplay'] = partial(self._changePositiveContourDisplay, state)

  def _changePositiveContourDisplay(self, state):
    if state == QtCore.Qt.Checked:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayPositiveContours = True
        self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
        self.logger.info("spectrumView.displayPositiveContours = True")
    else:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayPositiveContours = False
        self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
        self.logger.info("spectrumView.displayPositiveContours = False")


  def _queueChangeNegativeContourDisplay(self, state):
    self._changes['negativeContourDisplay'] = partial(self._changeNegativeContourDisplay, state)

  def _changeNegativeContourDisplay(self, state):
    if state == QtCore.Qt.Checked:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayNegativeContours = True
        self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
        self.logger.info("spectrumView.displayNegativeContours = True")
    else:
      for spectrumView in self.spectrum.spectrumViews:
        spectrumView.displayNegativeContours = False
        self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
        self.logger.info("spectrumView.displayNegativeContours = False")

  def _queueChangePositiveBaseLevel(self, spectrum, value):
    self._changes['positiveContourBaseLevel'] = partial(self._changePositiveBaseLevel, spectrum, value)

  def _changePositiveBaseLevel(self, spectrum, value):
    spectrum.positiveContourBase = float(value)
    self._writeLoggingMessage("spectrum.positiveContourBase = %f" % float(value))
    self.pythonConsole.writeConsoleCommand("spectrum.positiveContourBase = %f" % float(value), spectrum=spectrum)


  def _queueChangePositiveContourMultiplier(self, spectrum, value):
    self._changes['positiveContourMultiplier'] = partial(self._changePositiveContourMultiplier, spectrum, value)

  def _changePositiveContourMultiplier(self, spectrum, value):
    spectrum.positiveContourFactor = float(value)
    self._writeLoggingMessage("spectrum.positiveContourFactor = %f" % float(value))
    self.pythonConsole.writeConsoleCommand("spectrum.positiveContourFactor = %f" % float(value), spectrum=spectrum)


  def _queueChangePositiveContourCount(self, spectrum, value):
    self._changes['positiveContourCount'] = partial(self._changePositiveContourCount, spectrum, value)

  def _changePositiveContourCount(self, spectrum, value):
    spectrum.positiveContourCount = int(value)
    self._writeLoggingMessage("spectrum.positiveContourCount = %d" % int(value))
    self.pythonConsole.writeConsoleCommand("spectrum.positiveContourCount = %d" % int(value), spectrum=spectrum)

    # TODO:ED implement changing all of the spectra in the view
    # for spectrumView in self.spectrum.spectrumViews:
    #   spectrumView.displayNegativeContours = True
    #   self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
    #   self.logger.info("spectrumView.displayNegativeContours = True")

  def _queueChangeNegativeBaseLevel(self, spectrum, value):
    self._changes['negativeContourBaseLevel'] = partial(self._changeNegativeBaseLevel, spectrum, value)

  def _changeNegativeBaseLevel(self, spectrum, value):
    spectrum.negativeContourBase = float(value)
    self._writeLoggingMessage("spectrum.negativeContourBase = %f" % float(value))
    self.pythonConsole.writeConsoleCommand("spectrum.negativeContourBase = %f" % float(value), spectrum=spectrum)


  def _queueChangeNegativeContourMultiplier(self, spectrum, value):
    self._changes['negativeContourMultiplier'] = partial(self._changeNegativeContourMultiplier, spectrum, value)

  def _changeNegativeContourMultiplier(self, spectrum, value):
    spectrum.negativeContourFactor = float(value)
    self._writeLoggingMessage("spectrum.negativeContourFactor = %f" % float(value))
    self.pythonConsole.writeConsoleCommand("spectrum.negativeContourFactor = %f" % float(value), spectrum=spectrum)


  def _queueChangeNegativeContourCount(self, spectrum, value):
    self._changes['negativeContourCount'] = partial(self._changeNegativeContourCount, spectrum, value)

  def _changeNegativeContourCount(self, spectrum, value):
    spectrum.negativeContourCount = int(value)
    self._writeLoggingMessage("spectrum.negativeContourCount = %d" % int(value))
    self.pythonConsole.writeConsoleCommand("spectrum.negativeContourCount = %d" % int(value), spectrum=spectrum)

  # change colours using comboboxes and colour buttons
  def _queueChangePosSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    if newColour is not None:
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(newColour))
      newIndex = str(len(spectrumColours.items())+1)
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
      self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
      spectrumColours[newColour.name()] = 'Colour %s' % newIndex

      # spawns combobox change event below
      self.positiveColourBox.setCurrentIndex(int(newIndex)-1)

  def _queueChangeNegSpectrumColour(self, spectrum):
    dialog = ColourDialog()
    newColour = dialog.getColor()
    if newColour is not None:
      pix=QtGui.QPixmap(QtCore.QSize(20,20))
      pix.fill(QtGui.QColor(newColour))
      newIndex = str(len(spectrumColours.items())+1)
      self.negativeColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' %newIndex)
      self.positiveColourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' %newIndex)
      spectrumColours[newColour.name()] = 'Colour %s' % newIndex

      # spawns combobox change event below
      self.negativeColourBox.setCurrentIndex(int(newIndex)-1)

  def _queueChangePosColourComboIndex(self, spectrum, value):
    self._changes['positiveColourComboIndex'] = partial(self._changePosColourComboIndex, spectrum, value)

  def _changePosColourComboIndex(self, spectrum, value):
    newColour = list(spectrumColours.keys())[value]
    spectrum.positiveContourColour = newColour
    self._writeLoggingMessage("spectrum.positiveContourColour = '%s'" % newColour)
    self.pythonConsole.writeConsoleCommand("spectrum.positiveContourColour = '%s'" % newColour, spectrum=spectrum)


  def _queueChangeNegColourComboIndex(self, spectrum, value):
    self._changes['negativeColourComboIndex'] = partial(self._changeNegColourComboIndex, spectrum, value)

  def _changeNegColourComboIndex(self, spectrum, value):
    newColour = list(spectrumColours.keys())[value]
    spectrum._apiDataSource.negativeContourColour = newColour
    self._writeLoggingMessage("spectrum.negativeContourColour = %s" % newColour)
    self.pythonConsole.writeConsoleCommand("spectrum.negativeContourColour = '%s'" % newColour, spectrum=spectrum)