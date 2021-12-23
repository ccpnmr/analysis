"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-12-23 15:18:25 +0000 (Thu, December 23, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip


class ZoomToPositionPopup(CcpnDialog):


  def __init__(self, parent=None, mainWindow=None, strip=None, title='Zoom To Position', **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)
    self.strip = None
    if mainWindow:
      self.mainWindow = mainWindow
      self.application = mainWindow.application
      self.project = mainWindow.application.project
      self.current = mainWindow.application.current
      self.strip = strip or self.current.strip
      if not self.strip:
        showWarning('No Strip', 'Select a strip first')
        self.reject()

    self._dictValues = {}
    self._createWidget()

  def _createWidget(self):
    n=0
    pLabel = Label(self, text="Positions", grid=(0,0))
    rLabel = Label(self, text="Width Region", grid=(0,1))
    if self.strip:
      for i, axis in enumerate(self.strip.axisCodes):
        n=+i
        positionBoxWidget = ScientificDoubleSpinBox(self, prefix=axis, step=0.01, decimals=4, grid=(n,0))
        widthWidget = ScientificDoubleSpinBox(self, prefix='Width',
                                              step=0.01, decimals=4, tipText='Width of the zoom in ppm',grid=(n, 1))
        self._dictValues[axis]=[positionBoxWidget,widthWidget]
      n+=1
      buttonList = ButtonList(self, ['Cancel', 'Go'], [self.reject, self._okButton], grid=(n, 1))

  def _okButton(self):
    """

    """
    positions = []
    axisCodes = []
    widths = []

    for axisCode, listWidgets in self._dictValues.items():
      axisCodes.append(axisCode)
      positions.append(listWidgets[0].value())
      widths.append(listWidgets[1].value())
    if self.strip:
      navigateToPositionInStrip(self.strip, positions, axisCodes, widths)
    else:
      showWarning('No Strip', 'Select a strip first')
    self.accept()


if __name__ == "__main__":
    from ccpn.ui.gui.widgets.Application import TestApplication
    app = TestApplication()

    popup = ZoomToPositionPopup()
    popup.show()
    popup.raise_()
    app.start()
