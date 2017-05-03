"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Base import Base

class ccpnDialog(QtGui.QDialog, Base):
  def __init__(self, parent=None, windowTitle='', setLayout=False, **kw):
    QtGui.QDialog.__init__(self, parent)
    Base.__init__(self, setLayout=setLayout, **kw)

    self.setWindowTitle(windowTitle)

    # self.mainLayout = QtGui.QGridLayout()
    # self.setLayout(self.mainLayout)

  # def setSize(self, x:int, y:int):
  #   pass
  def fixedSize(self):
    self.sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    self.sizePolicy.setHorizontalStretch(0)
    self.sizePolicy.setVerticalStretch(0)
    self.setSizePolicy(self.sizePolicy)
    self.setFixedSize(self.maximumWidth(), self.maximumHeight())
    self.setSizeGripEnabled(False)

    # Dialog->resize(581, 292);
    # QSizePolicy sizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    # sizePolicy.setHorizontalStretch(0);
    # sizePolicy.setVerticalStretch(0);
    # sizePolicy.setHeightForWidth(WaterLevelEditorDialog->sizePolicy().hasHeightForWidth());
    # Dialog->setSizePolicy(sizePolicy);
    # Dialog->setMinimumSize(QSize(581, 292));
    # Dialog->setMaximumSize(QSize(581, 292));
    # Dialog->setSizeGripEnabled(false);