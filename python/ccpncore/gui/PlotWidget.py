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

from ccpncore.gui.Base import Base
from ccpncore.gui import ViewBox
from ccpnmrcore.DropBase import DropBase

import pyqtgraph as pg

class PlotWidget(DropBase, pg.PlotWidget, Base):

  def __init__(self, parent=None, appBase=None, dropCallback=None, **kw):


    pg.PlotWidget.__init__(self, parent=parent, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True)
    Base.__init__(self, **kw)
    DropBase.__init__(self, appBase, dropCallback)

    self.setInteractive(True)
    self.plotItem.setAcceptHoverEvents(True)

    self.plotItem.setAcceptDrops(True)
    self.plotItem.axes['left']['item'].hide()
    self.plotItem.axes['right']['item'].show()


  def addItem(self, item):
    self.scene().addItem(item)
    # # self.plotItem.axes['top']['item'].hide()
    # self.plotItem.axes['bottom']['item'].show()
    # self.plotItem.axes['right']['item'].show()



