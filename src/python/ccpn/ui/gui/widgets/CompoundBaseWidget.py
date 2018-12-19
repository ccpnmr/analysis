"""
Base class for compound widgets

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:52 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.core.lib.Notifiers import Notifier

from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.TextEditor import TextEditor


NULL = object()

NOTIFIERS = '_notifiers'


class CompoundBaseWidget(Frame):
    """
    Base widget for Compound classes; inherits from Frame (and hence Base)
    Implements the addNotifier and deleteNotifiers methods
    """

    def __init__(self, parent, layoutDict, orientation, showBorder, **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param layoutDict: dictionary of orientation, griddingList key,value pairs; griddingList should
                           contain a (x,y) tuple for each widget to be added later-on
        :param orientation: orientation keyword
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """
        super().__init__(parent=parent, showBorder=showBorder, setLayout=True, **kwds)

        if not orientation in layoutDict:
            raise RuntimeError('Invalid parameter "orientation" (%s)' % orientation)
        self._orientation = orientation
        self._gridding = layoutDict[orientation]  # list of grid tuples for all succesive widgets
        self._widgets = []  # list of all the widgets; use addWidget to add using the layoutDict

        # notifiers
        #TODO:GEERTEN: poor design?; rethink this over
        if not hasattr(self, NOTIFIERS):
            setattr(self, NOTIFIERS, [])  # list of all notifiers for this widget
        nf = getattr(self, NOTIFIERS)
        if not isinstance(nf, list):
            raise RuntimeError('Invalid notifiers attribute (%s)' % nf)

    def _addWidget(self, widget):
        "Add widget, using the layout as defined previously by layoutDict and orientation"
        if len(self._gridding) < len(self._widgets) + 1:
            raise RuntimeError('Cannot add widget; invalid gridding')
        gx, gy = self._gridding[len(self._widgets)]
        self._widgets.append(widget)
        self.layout().addWidget(widget, gx, gy)

    def setMinimumWidths(self, minimumWidths):
        "Set minimumwidths of widgets"
        if len(minimumWidths) < len(self._widgets):
            raise RuntimeError('Not enough values to set minimum widths of all widgets')
        for i, width in enumerate(minimumWidths[0:len(self._widgets)]):
            if width is not None:
                self._widgets[i].setMinimumWidth(width)

    def setMaximumWidths(self, maximumWidths):
        "Set maximumWidths of widgets"
        if len(maximumWidths) < len(self._widgets):
            raise RuntimeError('Not enough values to set maximum widths of all widgets')
        for i, width in enumerate(maximumWidths[0:len(self._widgets)]):
            if width is not None:
                self._widgets[i].setMaximumWidth(width)

    def setFixedWidths(self, fixedWidths):
        "Set maximumWidths of widgets"
        if len(fixedWidths) < len(self._widgets):
            raise RuntimeError('Not enough values to set fixed widths of all widgets')
        for i, width in enumerate(fixedWidths[0:len(self._widgets)]):
            if width is not None:
                self._widgets[i].setFixedWidth(width)

    def setFixedHeights(self, fixedHeights):
        "Set fixed heights of widgets"
        if len(fixedHeights) < len(self._widgets):
            raise RuntimeError('Not enough values to set fixed heights of all widgets')
        for i, height in enumerate(fixedHeights[0:len(self._widgets)]):
            if height is not None:
                self._widgets[i].setFixedHeight(height)

    def addObjectNotifier(self, theObject, triggers, targetName, func, *args, **kwds):
        """
        Add and store a notifier with widget;

        :param theObject: A valid V3 core or current object
        :param triggers: any of the triggers, as defined in Notifier class
        :param targetName: a valid target for theObject, as defined in the Notifier class
        :param func: callback function on triggering
        :param args: optional arguments to func
        :param kwds: optional keyword arguments to func
        :return: Notifier instance
        """
        notifier = Notifier(theObject, triggers, targetName, func, *args, **kwds)
        self.addNotifier(notifier)
        return notifier

    def addNotifier(self, notifier):
        "add a notifer to the widget"
        if not hasattr(self, NOTIFIERS):
            raise RuntimeError('Widget has no notifiers attribute')
        nf = getattr(self, NOTIFIERS)
        nf.append(notifier)
        getLogger().debug('Added notifier %s to widget %s' % (notifier, self))

    def deleteNotifiers(self):
        "Delete all notifiers associated with the widget"
        while len(self._notifiers) > 0:
            notifier = self._notifiers.pop()
            #print('>deleteNotifier>', notifier)
            notifier.unRegister()
            del (notifier)

    def __del__(self):
        # The project and all its things are already disassembled when closing the program;
        # hence, the deregistering of notifiers fails and needs to be caught
        try:
            self.deleteNotifiers()
        except:
            pass
