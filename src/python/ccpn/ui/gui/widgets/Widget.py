"""
The module implements widget and scrollable widget class

Widget(parent=None, setLayout=False, **kwds)

ScrollableWidget(parent=None, setLayout=False,
                 minimumSizes=(50,50), scrollBarPolicies=('asNeeded','asNeeded'), **kwds)


"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:57 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea


class Widget(QtWidgets.QWidget, Base):

    def __init__(self, parent=None, setLayout=False, acceptDrops=False, **kwds):
        """General widget; default accepts drops (for now)
        """

        # print('DEBUG Widget: acceptDrops=%s, setLayout=%s, **kwds=%s' % (setLayout, acceptDrops, kwds))

        super().__init__(parent=parent)
        Base._init(self, acceptDrops=acceptDrops, setLayout=setLayout, **kwds)

        self.setContentsMargins(0, 0, 0, 0)

    # def clearWidget(self):
    #     """Delete all the contents of the widget
    #     """
    #     layout = self.getLayout()
    #     if layout:
    #         rowCount = layout.rowCount()
    #         colCount = layout.columnCount()
    #
    #         for r in range(rowCount):
    #             for m in range(colCount):
    #                 item = layout.itemAtPosition(r, m)
    #                 if item and item.widget():
    #                     item.widget().deleteLater()


class ScrollableWidget(Widget):
    "A scrollable Widget"

    def __init__(self, parent=None, setLayout=False,
                 minimumSizes=(50, 50), scrollBarPolicies=('asNeeded', 'asNeeded'), **kwds):

        # define a scroll area; check kwds if these apply to gridding
        kw1 = {}
        for key in 'grid gridSpan stretch hAlign vAlign'.split():
            if key in kwds:
                kw1[key] = kwds[key]
                del (kwds[key])
        kw1['setLayout'] = True  ## always assure a layout for the scrollarea

        self.scrollArea = ScrollArea(parent=parent,
                                     scrollBarPolicies=scrollBarPolicies, minimumSizes=minimumSizes,
                                     **kw1
                                     )
        # initialise the frame
        Widget.__init__(self, parent=self.scrollArea, setLayout=setLayout, **kwds)
        # self.setMinimumSizes(minimumSizes) ## This make things go wrong!?
        # add it to the _sequenceGraphScrollArea
        self.scrollArea.setWidget(self)
        #self._sequenceGraphScrollArea.getLayout().addWidget(self)

        # configure the scroll area to allow all available space without margins
        self.scrollArea.setContentsMargins(0, 0, 0, 0)
        self.scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.scrollArea.setWidgetResizable(True)
        self.setScrollBarPolicies(scrollBarPolicies)

    def setMinimumSizes(self, minimumSizes):
        "Set (minimumWidth, minimumHeight)"
        self.setMinimumWidth(minimumSizes[0])
        self.setMinimumHeight(minimumSizes[1])

    def getScrollArea(self):
        "return scroll area (for external usage)"
        return self.scrollArea

    def setScrollBarPolicies(self, scrollBarPolicies=('asNeeded', 'asNeeded')):
        "Set the scrolbar policy: always, never, asNeeded"
        self.scrollArea.setScrollBarPolicies(scrollBarPolicies)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.BasePopup import BasePopup
    from ccpn.ui.gui.widgets.Label import Label
    from ccpn.ui.gui.widgets.Widget import Widget


    class TestPopup(BasePopup):
        def body(self, parent):
            widget = Widget(parent, grid=(0, 0))
            policyDict = dict(
                    hAlign='c',
                    stretch=(1, 0),
                    #hPolicy = 'center',
                    #vPolicy = 'center'
                    )

            #TODO: find the cause of the empty space between the widgets
            #frame3 = ScrollableFrame(parent=parent, showBorder=True, bgColor=(255, 0, 255), grid=(2,0))
            frame1 = Widget(parent=widget, grid=(0, 0), bgColor=(255, 255, 0), **policyDict)
            label1 = Label(parent=frame1, grid=(0, 0), text="WIDGET-1", bold=True, textColour='black', textSize='32')

            frame2 = Widget(parent=widget, grid=(1, 0), bgColor=(255, 0, 0), **policyDict)
            label2 = Label(parent=frame2, grid=(0, 0), text="WIDGET-2", bold=True, textColour='black', textSize='32')

            scroll4 = ScrollableWidget(parent=widget, grid=(2, 0))
            label4 = Label(parent=scroll4, text="ScrollableWidget", grid=(1, 0), **policyDict,
                           bold=True, textColour='black', textSize='32')


    app = TestApplication()
    popup = TestPopup(title='Test Frame')
    popup.resize(200, 400)
    app.start()
