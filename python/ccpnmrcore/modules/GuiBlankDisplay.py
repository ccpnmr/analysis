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
from PyQt4 import QtCore

# from pyqtgraph.dockarea import Dock

from ccpn import Spectrum

from ccpncore.util.Pid import Pid
from ccpncore.gui.Dock import CcpnDockLabel, CcpnDock
from ccpncore.gui.Label import Label
# from ccpncore.lib.Io.Fasta import parseFastaFile, isFastaFormat

from ccpnmrcore.DropBase import DropBase


# def _findPpmRegion(spectrum, axisDim, spectrumDim):
#
#   pointCount = spectrum.pointCounts[spectrumDim]
#   if axisDim < 2: # want entire region
#     region = (0, pointCount)
#   else:
#     n = pointCount // 2
#     region = (n, n+1)
#
#   firstPpm, lastPpm = spectrum.getDimValueFromPoint(spectrumDim, region)
#
#   return 0.5*(firstPpm+lastPpm), abs(lastPpm-firstPpm)

class GuiBlankDisplay(DropBase, CcpnDock): # DropBase needs to be first, else the drop events are not processed

  def __init__(self, dockArea):
    
    self.dockArea = dockArea

    CcpnDock.__init__(self, name='Blank Display')
    dockArea.addDock(self, 'right')
    # self.setStyleSheet("""
    # QWidget { background-color: #2a3358;
    # }
    # """)
    # self.labelhidden = True
    # self.label.hide()
    # self.label = DockLabel('Blank Display', self)
    # self.label.show()

    self.label2 = Label(self, text='Drag Spectrum Here', textColor='#bec4f3')
    self.label2.setAlignment(QtCore.Qt.AlignCenter)
    self.layout.addWidget(self.label2)
    # self.label2.dropEvent = self.dropCallback
    # self.layout.addWidget(self.label)


    DropBase.__init__(self, dockArea.guiWindow._appBase)

  def setOrientation(self, o='vertical', force=True):
        """
        Sets the orientation of the title bar for this Dock.
        Must be one of 'auto', 'horizontal', or 'vertical'.
        By default ('auto'), the orientation is determined
        based on the aspect ratio of the Dock.
        """
        #print self.name(), "setOrientation", o, force
        if o == 'auto' and self.autoOrient:
            if self.container().type() == 'tab':
                o = 'horizontal'
            elif self.width() > self.height()*1.5:
                o = 'vertical'
            else:
                o = 'horizontal'
        if force or self.orientation != o:
            self.orientation = o
            self.label.setOrientation(o)
            self.updateStyle()

  def processSpectrum(self, spectrum:(Spectrum,Pid)):
    """Process dropped spectrum"""
    spectrumDisplay = self.dockArea.guiWindow.createSpectrumDisplay(spectrum)
    self.dockArea.guiWindow.deleteBlankDisplay()
    msg = 'window.createSpectrumDisplay(project.getByPid("%s"))\n' % spectrum
    self.dockArea.window().pythonConsole.write(msg)
