"""
CheckBox widget

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base

class CheckBox(QtGui.QCheckBox, Base):

  def __init__(self, parent, checked=False, text='', callback=None, **kw):

    QtGui.QCheckBox.__init__(self, parent)
    self.setChecked(checked)
    if text:
      self.setText(text)
    Base.__init__(self, **kw)
    if callback:
      self.setCallback(callback)

  def get(self):
    return self.isChecked()

  def setCallback(self, callback):
    self.connect(self, QtCore.SIGNAL('clicked()'), callback)


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup

  app = TestApplication()

  def callback():
    print('callback')

  popup = BasePopup(title='Test CheckBox')

  checkBox1 = CheckBox(parent=popup, text="test", callback=callback, grid=(0, 0)
                      )
  app.start()
