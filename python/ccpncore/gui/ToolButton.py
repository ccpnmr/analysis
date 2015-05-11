"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

from PyQt4 import QtCore, QtGui

class ToolButton(QtGui.QToolButton):

  def __init__(self, parent=None, spectrumView=None):
    
    QtGui.QToolButton.__init__(self, parent.spectrumToolBar)
    self.spectrumView = spectrumView
    pix=QtGui.QPixmap(60, 10)
    if spectrumView.spectrum.dimensionCount < 2:
      pix.fill(QtGui.QColor(spectrumView.spectrum.sliceColour))
    else:
      pix.fill(QtGui.QColor(spectrumView.spectrum.positiveContourColour))
    # spectrumItem.newAction = self.spectrumToolbar.addAction(spectrumItem.name, QtGui.QToolButton)
    self.spaction = parent.spectrumToolBar.addAction(spectrumView.spectrum.name)#, self)
    newIcon = QtGui.QIcon(pix)
    self.spaction.setIcon(newIcon)
    self.spaction.setCheckable(True)
    self.spaction.setChecked(True)

    # for spectrumView in parent.spectrumViews:
    #   if spectrumView.spectrum.dimensionCount < 2:
    #     self.spaction.toggled.connect(spectrumView.plot.setVisible)
    #   else:
    for strip in spectrumView.strips:
      print(strip)
      item = spectrumView.spectrumItems[strip]
      print(strip, item, spectrumView, self.spaction, 'you name it!')
      self.spaction.toggled.connect(item.setVisible)
      print(self.spaction)
         # for peakListView in spectrumView.peakListViews:
         #   spectrumView.newAction.toggled.connect(peakListView.setVisible)
    # spectrumView.widget = parent.spectrumToolBar.widgetForAction(self.spaction)
    # spectrumView.widget.setFixedSize(60,30)

