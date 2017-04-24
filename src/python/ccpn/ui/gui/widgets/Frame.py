"""

This module implemented a Frame and a ScrollableFrame

Frame(parent=None, showBorder=False, fShape=None, fShadow=None, **kwds)
  NB: Until now: fShape and fShadow do not seem to alter the appearance on OSX
  
ScrollableFrame(parent=None, showBorder=False, fShape=None, fShadow=None,
                minimumSizes=(50,50), scrollBarPolicies=('asNeeded','asNeeded'), **kwds)

  From: http://pyqt.sourceforge.net/Docs/PyQt4/qframe.html#details

  The QFrame class is the base class of widgets that can have a frame. More...

  Inherits QWidget.

  Inherited by QAbstractScrollArea, QLabel, QLCDNumber, QSplitter, QStackedWidget and QToolBox.

  Types

  enum Shadow { Plain, Raised, Sunken }
  enum Shape { NoFrame, Box, Panel, WinPanel, ..., StyledPanel }
  enum StyleMask { Shadow_Mask, Shape_Mask }
  Methods

  __init__ (self, QWidget parent = None, Qt.WindowFlags flags = 0)
  changeEvent (self, QEvent)
  drawFrame (self, QPainter)
  bool event (self, QEvent e)
  QRect frameRect (self)
  Shadow frameShadow (self)
  Shape frameShape (self)
  int frameStyle (self)
  int frameWidth (self)
  int lineWidth (self)
  int midLineWidth (self)
  paintEvent (self, QPaintEvent)
  setFrameRect (self, QRect)
  setFrameShadow (self, Shadow)
  setFrameShape (self, Shape)
  setFrameStyle (self, int)
  setLineWidth (self, int)
  setMidLineWidth (self, int)
  QSize sizeHint (self)

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:05 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.ScrollArea import SCROLLBAR_POLICY_DICT


class Frame(QtGui.QFrame, Base):

  FRAME_DICT = {
      # Shadow
      'plain':       QtGui.QFrame.Plain,
      'raised':      QtGui.QFrame.Raised,
      'sunken':      QtGui.QFrame.Sunken,
      # Shapes
      'noFrame':     QtGui.QFrame.NoFrame,
      'box':         QtGui.QFrame.Box,
      'panel':       QtGui.QFrame.Panel,
      'styledPanel': QtGui.QFrame.StyledPanel,
      'hLine':       QtGui.QFrame.HLine,
      'vLine':       QtGui.QFrame.VLine,
  }

  def __init__(self, parent=None, showBorder=False, fShape=None, fShadow=None, **kwds):
    """
    Initialise a Frame with optional border and layout

    :param fShape:   frame shape options: noFrame, box, styledPanel, hLine, vLine
    :param fShadow:  frame shadow options: plain, raised, sunken

    """

    QtGui.QFrame.__init__(self, parent)

    #TODO: replace with proper stylesheet routines once inplemented
    styleSheet = ''
    if 'bgColor' in kwds:
      #rgb = QtGui.QColor(kwds["bgColor"]).getRgb()[:3]
      styleSheet += "background-color: rgb(%d, %d, %d); " % kwds["bgColor"]
      del(kwds['bgColor'])
    if 'fgColor' in kwds:
      styleSheet += "foreground-color: rgb(%d, %d, %d); " % kwds["fgColor"]
      del (kwds['fgColor'])
    if showBorder:
      styleSheet += "border: 1px solid black; "
    else:
      styleSheet += "border: 0px; "
    if len(styleSheet) > 0:
      #print('>>', styleSheet)
      self.setStyleSheet('QFrame {' + styleSheet + '}')

    Base.__init__(self, **kwds)

    # define frame styles
    if fShape or fShadow:
      """
      Define frame properties:
      """
      #TODO:GEERTEN: routine is called but appears not to change much in the appearance on OSX
      shape = self.FRAME_DICT.get(fShape, QtGui.QFrame.NoFrame)
      shadow = self.FRAME_DICT.get(fShadow, 0)
      #print('>>', shape, shadow)
      #print('Frame.framestyle>', shape | shadow)
      #self.setFrameStyle(shape | shadow)
      self.setFrameShape(shape)
      self.setFrameShadow(shadow)
      #self.setLineWidth(3)
      self.setMidLineWidth(3)


class ScrollableFrame(Frame):
  "A scrollable frame"

  def __init__(self, parent=None, showBorder=False, fShape=None, fShadow=None,
                     minimumSizes=(50,50), scrollBarPolicies=('asNeeded','asNeeded'), **kwds):

    # define a scroll area
    self.scrollArea = ScrollArea(parent=parent,
                                 scrollBarPolicies=scrollBarPolicies, minimumSizes=minimumSizes,
                                 **kwds
                                )
    self.scrollArea.setWidgetResizable(True)
    # initialise the frame
    super(ScrollableFrame, self).__init__(parent=self.scrollArea, showBorder=showBorder,
                                          fShape = fShape, fShadow = fShadow,
                                         )
    # add it to the scrollArea
    self.scrollArea.setWidget(self)
    self.scrollArea.getLayout().addWidget(self)

  def setScrollBarPolicies(self, policies=('asNeeded','asNeeded')):
    "Set the scrolbar policy: always, never, asNeeded"
    self.scrollArea.setScrollBarPolicies(policies)

if __name__ == '__main__':

  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup
  from ccpn.ui.gui.widgets.Label import Label
  from ccpn.ui.gui.widgets.Widget import Widget

  class TestPopup(BasePopup):
    def body(self, parent):
      widget = Widget(parent, grid=(0,0))
      policyDict = dict(
        hAlign='c',
        stretch=(1,0),
        #hPolicy = 'center',
        #vPolicy = 'center'
      )

      #TODO: find the cause of the empty space between the widgets
      #frame3 = ScrollableFrame(parent=parent, showBorder=True, bgColor=(255, 0, 255), grid=(2,0))
      frame1 = Frame(parent=widget, grid=(0,0), showBorder=False, bgColor=(255, 255, 0), **policyDict)
      label1 = Label(parent=frame1, grid=(0,0), text="FRAME-1", bold=True,textColour='black', textSize='32')

      frame2 = Frame(parent=widget, grid=(1,0), showBorder=True, bgColor=(255, 0, 0),
                     fShape='styledPanel', fShadow='raised', **policyDict)
      label2 = Label(parent=frame2, grid=(0,0), text="FRAME-2", bold=True,textColour='black', textSize='32')

      scroll4 = ScrollableFrame(parent=widget, grid=(4,0))
      label4 = Label(parent=scroll4, text="ScrollableFrame", grid=(1,0), **policyDict,
                    bold=True,textColour='black', textSize='32')

  app = TestApplication()
  popup = TestPopup(title='Test Frame')
  popup.resize(200, 400)
  app.start()

