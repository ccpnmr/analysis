"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.RadioButton import RadioButton
from ccpncore.gui.Spinbox import Spinbox

from application.core.modules.GuiTableGenerator import GuiTableGenerator
from application.core.modules.PeakTable import PeakListSimple

import pyqtgraph as pg

from functools import partial

class SpectrumGroupsWidget(QtGui.QWidget, Base):
  def __init__(self, parent=None, project=None, strip=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.button = Button(self, 'Setup SpectrumGroup Display', grid=(0, 0), callback=self.showSpectrumGroupPopup)
    self.project = project
    self.strip = strip

  def showSpectrumGroupPopup(self):
    popup = SpectrumGroupsPopup(project=self.project, strip=self.strip)
    popup.exec_()
    popup.raise_()



class SpectrumGroupsPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, strip=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.strip = strip
    self.checkBoxes = []
    self.project = project
    for i, group in enumerate(project.spectrumGroups):
      newCheckbox = CheckBox(self, grid=(i, 0))
      newLabel = Label(self, group.pid, grid=(i, 1))
      newCheckbox.toggled.connect(partial(self.toggleSpectrumGroups, group, i))
      self.checkBoxes.append(newCheckbox)
      views = [spectrumView for spectrumView in self.strip.spectrumViews if spectrumView.spectrum in group.spectra]
      newCheckbox.setChecked(all(view.isVisible() for view in views))
        # group.isVisible = True
      # else:
      #   group.isVisible = False
      # if group.isVisible:
      #   (True)
      # else:
      #   newCheckbox.setChecked(False)
      newCheckbox.toggled.connect(partial(self.toggleSpectrumGroups, group, i))

  def toggleSpectrumGroups(self, spectrumGroup, index):

    views = [spectrumView for spectrumView in self.strip.spectrumViews if spectrumView.spectrum in spectrumGroup.spectra]
    if self.checkBoxes[index].isChecked():
      for view in views:
        view.setVisible(True)
        view.plot.show()
    else:
      for view in views:
        view.setVisible(False)
        view.plot.hide()