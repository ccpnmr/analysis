"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CheckBoxes import CheckBoxes
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget, DoubleSpinBoxCompoundWidget
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpn.ui.gui.lib.GuiSpectrumView import GuiSpectrumView
from functools import partial


ALL = '<all>'

STRIPPLOT_PEAKS = 'peaks'
STRIPPLOT_NMRRESIDUES = 'nmrResidues'


class StripPlot(Widget):

    def __init__(self, parent=None,
                 mainWindow=None,
                 callback=None,
                 returnCallback=None,
                 applyCallback=None,
                 includePeakLists=True, includeNmrChains=True,
                 includeSpectrumTable=True,
                 **kw):
        Widget.__init__(self, parent, setLayout=True, **kw)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            displayText = [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
        else:
            self.application = None
            self.project = None
            self.current = None
            displayText = []

        self.callback = callback
        self.returnCallback = returnCallback if returnCallback else self.doCallback
        self.applyCallback = applyCallback

        self.includePeakLists = includePeakLists
        self.includeNmrChains = includeNmrChains
        self.includeSpectrumTable = includeSpectrumTable

        # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
        # underpinning the addNotifier call do not allow for it either
        row = 0
        colwidth = 140
        self.displaysWidget = ListCompoundWidget(self,
                                                 grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                                                 vPolicy='minimal',
                                                 #minimumWidths=(colwidth, 0, 0),
                                                 fixedWidths=(colwidth, colwidth, colwidth),
                                                 orientation='left',
                                                 labelText='Display(s):',
                                                 tipText='SpectrumDisplay modules to respond to double-click',
                                                 texts=[ALL] + displayText,
                                                 callback=self._selectDisplayInList)
        self.displaysWidget.setFixedHeights((None, None, 40))
        self.displaysWidget.pulldownList.set(ALL)
        self.displaysWidget.setPreSelect(self._fillDisplayWidget)

        # handle signals when the items in the displaysWidget have changed
        model = self.displaysWidget.listWidget.model()
        model.rowsInserted.connect(self._displayWidgetChanged)
        model.rowsRemoved.connect(self._displayWidgetChanged)
        self.displaysWidget.listWidget.cleared.connect(self._displayWidgetChanged)

        row += 1
        self.sequentialStripsWidget = CheckBoxCompoundWidget(
                self,
                grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Show sequential strips:',
                checked=False
                )

        row += 1
        self.markPositionsWidget = CheckBoxCompoundWidget(
                self,
                grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Mark positions:',
                checked=True
                )

        row += 1
        self.autoClearMarksWidget = CheckBoxCompoundWidget(
                self,
                grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Auto clear marks:',
                checked=True
                )

        row += 1
        texts = []
        tipTexts = []
        callbacks = []
        if includePeakLists:
            texts += ['use Peak selection']
            tipTexts += ['Use current selected peaks']
            callbacks += [partial(self._buttonClick, STRIPPLOT_PEAKS)]
        if includeNmrChains:
            texts += ['use nmrResidue selection']
            tipTexts += ['Use current selected nmrResidues']
            callbacks += [partial(self._buttonClick, STRIPPLOT_NMRRESIDUES)]

        self.listButtons = RadioButtons(self, texts=texts, tipTexts=tipTexts, callback=self._buttonClick,
                                      grid=(row, 0), direction='v') if texts else None

        self._spectraWidget = None

        if includeSpectrumTable:
            # create row's of spectrum information
            self._spectrRows = row+len(texts)
            self._fillSpectrumFrame()

        # add a spacer in the bottom-right corner to stop everything moving
        rows = self.getLayout().rowCount()
        cols = self.getLayout().columnCount()
        Spacer(self, 5, 5,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(rows, cols), gridSpan=(1, 1))

        self._registerNotifiers()

    def _selectDisplayInList(self):
        """Handle clicking items in display selection
        """
        pass

    def _displayWidgetChanged(self):
        """Handle adding/removing items from display selection
        """
        if self.includeSpectrumTable:
            self._fillSpectrumFrame()

    def _changeAxisCode(self):
        """Handle clicking the axis code buttons
        """
        pass

    def _buttonClick(self):
        """Handle clicking the peak/nmrChain buttons
        """
        pass

    def _fillDisplayWidget(self):
        """Fill the display box with the currently available spectrumDisplays
        """
        list = ['> select-to-add <'] + [ALL]
        if self.mainWindow:
            list += [display.pid for display in self.mainWindow.spectrumDisplays]
        self.displaysWidget.pulldownList.setData(texts=list)

    def _getDisplays(self):
        """Return list of displays to navigate - if needed
        """
        if not self.application:
            return []

        displays = []
        # check for valid displays
        gids = self.displaysWidget.getTexts()
        if len(gids) == 0: return displays
        if ALL in gids:
            displays = self.application.ui.mainWindow.spectrumDisplays
        else:
            displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
        return displays

    def _getSpectraFromDisplays(self):
        """Get the list of active spectra from the spectrumDisplays
        """
        if not self.application:
            return 0, None, None, None

        from ccpn.util.Common import _axisCodeMapIndices, axisCodeMapping

        # get the valid displays
        displays = self._getDisplays()
        validSpectrumViews = {}

        # loop through all the selected displays/spectrumViews that are visible
        for dp in displays:
            if dp.strips:
                for sv in dp.strips[0].spectrumViews:

                    if sv.spectrum not in validSpectrumViews:
                        validSpectrumViews[sv.spectrum] = sv.isVisible()
                    else:
                        validSpectrumViews[sv.spectrum] = validSpectrumViews[sv.spectrum] or sv.isVisible()

                    # for plv in sv.peakListViews:
                    #     if plv.isVisible() and sv.isVisible():
                    #         if plv.peakList not in validSpectrumViews:
                    #             validSpectrumViews[plv.peakList] = (sv.spectrum, plv)
                    #         else:
                    #
                    #             # skip for now, only one valid peakListView needed per peakList
                    #             # validSpectrumViews[plv.peakList] += (plv,)
                    #             pass

        if validSpectrumViews:
            maxLen = 0
            refAxisCodes = None

            for spectrum, visible in validSpectrumViews.items():

                if len(spectrum.axisCodes) > maxLen:
                    maxLen = len(spectrum.axisCodes)
                    refAxisCodes = list(spectrum.axisCodes)

            if not maxLen:
                return 0, None, None, None

            mappings = {}
            for spectrum, visible in validSpectrumViews.items():

                matchAxisCodes = spectrum.axisCodes

                for refAxisCode in refAxisCodes:
                    for matchAxisCode in matchAxisCodes:
                        mapping = axisCodeMapping([matchAxisCode], [refAxisCode])
                        for k, v in mapping.items():
                            if v not in mappings:
                                mappings[v] = set([k])
                            else:
                                mappings[v].add(k)

                # for matchAxisCode in matchAxisCodes:
                #     mapping = axisCodeMapping(matchAxisCode, refAxisCodes)
                #     if len(mapping.keys()) > 0:
                #         for k, v in mapping.items():
                #             if v not in mappings:
                #                 mappings[v] = set([k])
                #             else:
                #                 mappings[v].add(k)
                #     else:
                #         if matchAxisCode not in mappings.keys():
                #             mappings[matchAxisCode] = set([matchAxisCode])

                # mapping = axisCodeMapping(matchAxisCodes, refAxisCodes)
                # for k, v in mapping.items():
                #     if v not in mappings:
                #         mappings[v] = set([k])
                #     else:
                #         mappings[v].add(k)

            # example of mappings dict
            # ('Hn', 'C', 'Nh')
            # {'Hn': {'Hn'}, 'Nh': {'Nh'}, 'C': {'C'}}
            # {'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'C'}}
            # {'CA': {'C'}, 'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'CA', 'C'}}
            # {'CA': {'C'}, 'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'CA', 'C'}}

            axisLabels = [set() for ii in range(len(mappings))]

            spectrumIndex = {}
            # go through the spectra again
            for spectrum, visible in validSpectrumViews.items():

                spectrumIndex[spectrum] = [0 for ii in range(len(spectrum.axisCodes))]

                # get the spectrum dimension axisCode, nd see if is already there
                for spectrumDim, spectrumAxis in enumerate(spectrum.axisCodes):

                    axisTestCodes = tuple(mappings.keys())
                    if spectrumAxis in axisTestCodes:
                        spectrumIndex[spectrum][spectrumDim] = axisTestCodes.index(spectrumAxis)
                        axisLabels[spectrumIndex[spectrum][spectrumDim]].add(spectrumAxis)

                    else:
                        # if the axisCode is not in the reference list then find the mapping from the dict
                        for k, v in mappings.items():
                            if spectrumAxis in v:
                                # refAxisCodes[dim] = k
                                spectrumIndex[spectrum][spectrumDim] = axisTestCodes.index(k)
                                axisLabels[axisTestCodes.index(k)].add(spectrumAxis)

            axisLabels = [', '.join(ax) for ax in axisLabels]

            return maxLen, axisLabels, spectrumIndex, validSpectrumViews
            # self.axisCodeOptions.setCheckBoxes(texts=axisLabels, tipTexts=axisLabels)

        else:
            return 0, None, None, None

    def _fillSpectrumFrame(self):
        """Populate then spectrumFrame with the selectable spectra
        """
        if self._spectraWidget:
            self._spectraWidget.hide()
            self._spectraWidget.deleteLater()

        self._spectraWidget = Widget(parent=self, setLayout=True, hPolicy='minimal',
                                     grid=(0, 1), gridSpan=(self._spectrRows, 1), vAlign='top', hAlign='left')

        # calculate the maximum number of axes
        self.maxLen, self.axisLabels, self.spectrumIndex, self.validSpectrumViews = self._getSpectraFromDisplays()

        if not self.maxLen:
            return

        # modifier for atomCode
        spectraRow = 0
        self.atomCodeFrame = Frame(self._spectraWidget, setLayout=True, showBorder=False, fShape='noFrame',
                                   grid=(spectraRow, 0), gridSpan=(1, self.maxLen + 1),
                                   vAlign='top', hAlign='left')
        self.axisCodeLabel = Label(self.atomCodeFrame, 'Restricted Axes:', grid=(0, 0))
        self.axisCodeOptions = CheckBoxes(self.atomCodeFrame, selectedInd=None, texts=[],
                                          callback=self._changeAxisCode, grid=(0, 1))

        self.axisCodeOptions.setCheckBoxes(texts=self.axisLabels, tipTexts=self.axisLabels)

        # put in a divider
        spectraRow += 1
        HLine(self._spectraWidget, grid=(spectraRow, 0), gridSpan=(1, 4),
              colour=getColours()[DIVIDER], height=15)

        # add labels for the columns
        spectraRow += 1
        Label(self._spectraWidget, 'Spectrum', grid=(spectraRow, 0))
        for ii in range(self.maxLen):
            Label(self._spectraWidget, 'Tolerance', grid=(spectraRow, ii + 1))
        self.spectraStartRow = spectraRow + 1

        if self.application:
            spectraWidgets = {}  # spectrum.pid, frame dict to show/hide
            for row, spectrum in enumerate(self.validSpectrumViews.keys()):
                spectraRow += 1
                f = _SpectrumRow(parent=self._spectraWidget,
                                 row=spectraRow, col=0,
                                 setLayout=True,
                                 spectrum=spectrum, visible=self.validSpectrumViews[spectrum])

                spectraWidgets[spectrum.pid] = f

    def _registerNotifiers(self):
        """Notifiers for responding to spectrumViews
        """
        self._spectrumViewNotifier = Notifier(self.project,
                                            [Notifier.CREATE, Notifier.DELETE],
                                            SpectrumView.__name__,
                                            self._spectrumViewChanged,
                                            onceOnly=True)

        self._registerMonitors()

    def _unRegisterNotifiers(self):
        """Unregister all notifiers
        """
        if self._spectrumViewNotifier:
            self._spectrumViewNotifier.unRegister()

    def _registerMonitors(self):
        """Register monitors of spectrumView visibleChanged
        """
        self._spectrumMonitors = []

        # get the valid displays
        displays = self._getDisplays()

        # loop through all the selected displays/spectrumViews that are visible
        for dp in displays:
            if dp.strips:
                for sv in dp.strips[0].spectrumViews:
                    self._spectrumMonitors.append(sv)

        for sv in self._spectrumMonitors:
            sv.visibleChanged.connect(self._spectrumViewVisibleChanged)

    def _unregisterMonitors(self):
        """Unregister monitors of spectrumView visibleChanged
        """
        for sv in self._spectrumMonitors:
            sv.visibleChanged.disconnect(self._spectrumViewVisibleChanged)

    def _spectrumViewChanged(self, data):
        """Respond to spectrumViews being created/deleted, update contents of the spectrumWidgets frame
        """
        if self.includeSpectrumTable:
            self._fillSpectrumFrame()

        # clear the old monitors and reregister new ones
        self._unregisterMonitors()
        self._registerMonitors()

    def _spectrumViewVisibleChanged(self):
        """Respond to a visibleChanged in one of the spectrumViews, don't know which though
        """
        if self.includeSpectrumTable:
            self._fillSpectrumFrame()

    def doCallback(self):
        """Handle the user callback
        """
        if self.callback:
            self.callback()

    def _returnCallback(self):
        """Handle the return from widget callback
        """
        pass

    def _cleanupWidget(self):
        """Cleanup the notifiers that are left behind after the widget is closed
        """
        self._unRegisterNotifiers()
        self._unregisterMonitors()

class _SpectrumRow(Frame):
    "Class to make a spectrum row"

    def __init__(self, parent, spectrum, row=0, col=0, visible=True, **kwds):
        super(_SpectrumRow, self).__init__(parent, **kwds)

        # col = 0
        # self.checkbox = CheckBoxCompoundWidget(self, grid=(0, col), gridSpan=(1, 1), hAlign='left',
        #                                        checked=True, labelText=spectrum.pid,
        #                                        fixedWidths=[100, 50])

        self.checkbox = Label(parent, spectrum.pid, grid=(row, col), gridSpan=(1, 1), hAlign='left')
        self.checkbox.setEnabled(visible)

        self.spinBoxes = []
        for ii, axisCode in enumerate(spectrum.axisCodes):
            decimals, step = (2, 0.01) if axisCode[0:1] == 'H' else (1, 0.1)
            col += 1
            ds = DoubleSpinBoxCompoundWidget(
                    parent, grid=(row, col), gridSpan=(1, 1), hAlign='left',
                    fixedWidths=(30, 50),
                    labelText=axisCode,
                    value=spectrum.assignmentTolerances[ii],
                    decimals=decimals, step=step, range=(0, None))
            ds.setObjectName(str(spectrum.pid + axisCode))
            self.spinBoxes.append(ds)

            ds.setEnabled(visible)

if __name__ == '__main__':
    import os
    import sys
    from PyQt5 import QtGui, QtWidgets


    def myCallback(ph0, ph1, pivot, direction):
        print(ph0, ph1, pivot, direction)


    qtApp = QtWidgets.QApplication(['Test Phase Frame'])

    #QtCore.QCoreApplication.setApplicationName('TestPhasing')
    #QtCore.QCoreApplication.setApplicationVersion('0.1')

    widget = QtWidgets.QWidget()
    frame = StripPlot(widget, callback=myCallback)
    widget.show()
    widget.raise_()

    sys.exit(qtApp.exec_())
