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
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

class Spacer(QtGui.QSpacerItem):
  """
  Widget used to put spaces into modules and popups.
  """
  def __init__(self, parent=None, *args, **kw):
    """

    :param parent:
    :param args:
    :param kw:
    """
    QtGui.QSpacerItem.__init__(self, *args)

    parent.layout().addItem(self, kw['grid'][0], kw['grid'][1], kw['gridSpan'][0], kw['gridSpan'][1])
