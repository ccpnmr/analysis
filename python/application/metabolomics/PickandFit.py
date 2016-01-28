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
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from application.core.modules.PeakTable import PeakListSimple


class PickandFit(QtGui.QWidget, Base):

  def __init__(self, parent=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.pickingLabel = Label(self, 'Picking', grid=(0, 0), hAlign='l')
    self.pickingButton = Button(self, 'Pick', grid=(0, 1))
    self.autoPickingLabel = Label(self, 'Autopicking', grid=(1, 0), gridSpan=(1, 2))
    self.methodPulldown = PulldownList(self, grid=(2, 0))
    self.methodBox1 = DoubleSpinbox(self, grid=(2, 1))
    self.methodBox1 = DoubleSpinbox(self, grid=(3, 0))
    self.methodBox1 = DoubleSpinbox(self, grid=(3, 1))
    self.methodBox1 = DoubleSpinbox(self, grid=(2, 2))
    self.methodBox1 = DoubleSpinbox(self, grid=(3, 2))
    self.fitLabel = Label(self, 'Fit', grid=(0, 3), hAlign='l')
    self.lineShapeLabel = Label(self, 'Lineshape ', grid=(0, 5))
    self.lineShapePulldown = PulldownList(self, grid=(0, 6), gridSpan=(1, 3))
    self.ppmLabel1 = Label(self, 'ppm', grid=(1, 3))
    self.ppmLabel2 = Label(self, 'ppm', grid=(2, 3))
    self.ppmLabel3 = Label(self, 'ppm', grid=(3, 3))
    self.ppmBox1 = DoubleSpinbox(self, grid=(1, 4))
    self.ppmBox2 = DoubleSpinbox(self, grid=(2, 4))
    self.ppmBox3 = DoubleSpinbox(self, grid=(3, 4))
    self.lineWidthLabel1 = Label(self, 'Linewidth', grid=(1, 5))
    self.lineWidthLabel2 = Label(self, 'Linewidth', grid=(2, 5))
    self.lineWidthLabel3 = Label(self, 'Linewidth', grid=(3, 5))
    self.lineWidthBox1 = DoubleSpinbox(self, grid=(1, 6))
    self.lineWidthBox2 = DoubleSpinbox(self, grid=(2, 6))
    self.lineWidthBox3 = DoubleSpinbox(self, grid=(3, 6))
    self.intensityLabel1 = Label(self, 'Intensity', grid=(1, 7))
    self.intensityLabel1 = Label(self, 'Intensity', grid=(2, 7))
    self.intensityLabel1 = DoubleSpinbox(self, grid=(1, 8))
    self.intensityLabel1 = DoubleSpinbox(self, grid=(2, 8))
    self.fitSelectedButton = Button(self, 'Fit Selected', grid=(3, 7), gridSpan=(1, 2))


class PickandFitTable(QtGui.QWidget, Base):

  def __init__(self, parent=None, project=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.peakList = PeakListSimple
