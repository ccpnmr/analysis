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
    pix=QtGui.QPixmap(60,10)
    if spectrumView.spectrum.dimensionCount < 2:
      pix.fill(QtGui.QColor(spectrumView.spectrum.sliceColour))
    else:
      pix.fill(QtGui.QColor(spectrumView.spectrum.positiveContourColour))
    # spectrumItem.newAction = self.spectrumToolbar.addAction(spectrumItem.name, QtGui.QToolButton)
    spectrumView.newAction = parent.spectrumToolBar.addAction(spectrumView.spectrum.name)#, self)
    newIcon = QtGui.QIcon(pix)
    spectrumView.newAction.setIcon(newIcon)
    spectrumView.newAction.setCheckable(True)
    spectrumView.newAction.setChecked(True)

    for spectrumView in parent.spectrumViews:
      if spectrumView.spectrum.dimensionCount < 2:
        spectrumView.newAction.toggled.connect(spectrumView.plot.setVisible)
      else:
        for strip in spectrumView.strips:
         item = spectrumView.spectrumItems[strip]
         spectrumView.newAction.toggled.connect(item.setVisible)
    spectrumView.widget = parent.spectrumToolBar.widgetForAction(spectrumView.newAction)
    spectrumView.widget.setFixedSize(60,30)

