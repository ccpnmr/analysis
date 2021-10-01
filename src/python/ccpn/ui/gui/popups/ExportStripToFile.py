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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-10-01 18:57:04 +0100 (Fri, October 01, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-06 15:51:11 +0000 (Thu, July 06, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict as OD
from PyQt5 import QtWidgets, QtCore, QtGui
from dataclasses import dataclass
from functools import partial
# from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.guiSettings import getColours, DIVIDER, BORDERFOCUS
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import PrintTreeCheckBoxes
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning
from ccpn.ui.gui.widgets.CompoundWidgets import DoubleSpinBoxCompoundWidget
from ccpn.ui.gui.widgets.HighlightBox import HighlightBox
# from ccpn.ui.gui.widgets.MessageDialog import progressManager
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import GLFILENAME, GLGRIDLINES, \
    GLINTEGRALLABELS, GLINTEGRALSYMBOLS, GLMULTIPLETLABELS, \
    GLMULTIPLETSYMBOLS, GLPEAKLABELS, GLPEAKSYMBOLS, GLPRINTTYPE, GLPAGETYPE, GLSELECTEDPIDS, \
    GLSPECTRUMBORDERS, GLSPECTRUMCONTOURS, \
    GLSPECTRUMDISPLAY, GLSTRIP, \
    GLWIDGET, GLBACKGROUND, GLBASETHICKNESS, GLSYMBOLTHICKNESS, GLFOREGROUND, \
    GLCONTOURTHICKNESS, GLSHOWSPECTRAONPHASE, \
    GLSTRIPDIRECTION, GLSTRIPPADDING, GLEXPORTDPI, \
    GLFULLLIST, GLEXTENDEDLIST, GLDIAGONALLINE, GLCURSORS, GLDIAGONALSIDEBANDS, \
    GLALIASENABLED, GLALIASSHADE, GLALIASLABELSENABLED, GLSTRIPREGIONS
from ccpn.util.Colour import spectrumColours, addNewColour, fillColourPulldown, addNewColourString
from ccpn.util.Colour import hexToRgbRatio, colourNameNoSpace


# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import GLAXISLABELS, GLAXISMARKS, \
#     GLMARKLABELS, GLMARKLINES, GLREGIONS, GLOTHERLINES, GLSPECTRUMLABELS, GLSTRIPLABELLING, GLTRACES, \
#     GLPLOTBORDER, GLAXISLINES, GLAXISTITLES, GLAXISUNITS, GLAXISMARKSINSIDE


EXPORTEXT = 'EXT'
EXPORTFILTER = 'FILTER'
EXPORTPDF = 'PDF'
EXPORTPDFEXTENSION = '.pdf'
EXPORTPDFFILTER = 'pdf files (*.pdf)'
EXPORTSVG = 'SVG'
EXPORTSVGEXTENSION = '.svg'
EXPORTSVGFILTER = 'svg files (*.svg)'
EXPORTPNG = 'PNG'
EXPORTPNGEXTENSION = '.png'
EXPORTPNGFILTER = 'png files (*.png)'
EXPORTPS = 'PS'
EXPORTPSEXTENSION = '.ps'
EXPORTPSFILTER = 'ps files (*.ps)'
EXPORTTYPES = OD(((EXPORTPDF, {EXPORTEXT   : EXPORTPDFEXTENSION,
                               EXPORTFILTER: EXPORTPDFFILTER}),
                  (EXPORTSVG, {EXPORTEXT   : EXPORTSVGEXTENSION,
                               EXPORTFILTER: EXPORTSVGFILTER}),
                  (EXPORTPNG, {EXPORTEXT   : EXPORTPNGEXTENSION,
                               EXPORTFILTER: EXPORTPNGFILTER}),
                  (EXPORTPS, {EXPORTEXT   : EXPORTPSEXTENSION,
                              EXPORTFILTER: EXPORTPSFILTER}),
                  ))
EXPORTFILTERS = EXPORTPDFFILTER
PAGEPORTRAIT = 'portrait'
PAGELANDSCAPE = 'landscape'
PAGETYPES = [PAGEPORTRAIT, PAGELANDSCAPE]
STRIPAXIS = 'Axis'
STRIPMIN = 'Min'
STRIPMAX = 'Max'
STRIPCENTRE = 'Centre'
STRIPWIDTH = 'Width'
STRIPAXISINVERTED = 'AxisInverted'
STRIPBUTTONS = [STRIPAXIS, STRIPMIN, STRIPMAX, STRIPCENTRE, STRIPWIDTH]
STRIPAXES = ['X', 'Y']


@dataclass
class _StripData:
    """Simple class to store strip widget state
    """
    strip = None
    useRegion = False
    minMaxMode = 0
    axes = None

    def _initialise(self):
        """Initialise the new dataclas from the strip
        """
        self.axes = [{STRIPMIN         : 0.0,
                      STRIPMAX         : 0.0,
                      STRIPCENTRE      : 0.0,
                      STRIPWIDTH       : 0.0,
                      STRIPAXISINVERTED: False,  # not sure if this is needed
                      },
                     {STRIPMIN         : 0.0,
                      STRIPMAX         : 0.0,
                      STRIPCENTRE      : 0.0,
                      STRIPWIDTH       : 0.0,
                      STRIPAXISINVERTED: False,
                      }]

        if self.strip:
            for ii in range(len(STRIPAXES)):
                dd = self.axes[ii]
                region = self.strip.getAxisRegion(ii)
                dd[STRIPMIN], dd[STRIPMAX] = min(region), max(region)
                dd[STRIPAXISINVERTED] = True if (region[0] > region[1]) else False  # probably not needed - use setAxisRegion
                dd[STRIPCENTRE] = self.strip.getAxisPosition(ii)
                dd[STRIPWIDTH] = self.strip.getAxisWidth(ii)

    def __repr__(self):
        """Output the string representation
        """
        return f'<{self.strip}: {self.useRegion}, {self.minMaxMode}, {self.axes}>'


class ExportStripToFilePopup(ExportDialogABC):
    """
    Class to handle printing strips to file
    """
    _SAVESTRIPS = '_strips'
    _SAVECURRENTSTRIP = '_currentStrip'
    _SAVECURRENTAXIS = '_currentAxis'

    storeStateOnReject = True

    def __init__(self, parent=None, mainWindow=None, title='Export Strip to File',
                 fileMode='anyFile',
                 acceptMode='export',
                 selectFile=None,
                 fileFilter=EXPORTFILTERS,
                 strips=None,
                 includeSpectrumDisplays=True,
                 **kwds):
        """
        Initialise the widget
        """
        # initialise attributes
        self.strips = strips
        self.objects = {}
        self.includeSpectrumDisplays = includeSpectrumDisplays
        self.strip = None
        self.spectrumDisplay = None
        self.spectrumDisplays = set()
        self.specToExport = None

        self._initialiseStripList()

        super().__init__(parent=parent, mainWindow=mainWindow, title=title,
                         fileMode=fileMode, acceptMode=acceptMode,
                         selectFile=selectFile,
                         fileFilter=fileFilter,
                         **kwds)

        if not strips:
            showWarning(str(self.windowTitle()), 'No strips selected')
            self.reject()

        self.fullList = GLFULLLIST

    def initialise(self, userFrame):
        """Create the widgets for the userFrame
        """
        row = 0
        self.objectPulldown = PulldownListCompoundWidget(userFrame,
                                                         grid=(row, 0), gridSpan=(1, 3), vAlign='top', hAlign='left',
                                                         orientation='left',
                                                         labelText='Strip/SpectrumDisplay',
                                                         callback=self._changePulldown
                                                         )

        # add a spacer to separate from the common save widgets
        row += 1
        HLine(userFrame, grid=(row, 0), gridSpan=(1, 4), colour=getColours()[DIVIDER], height=20)
        row += 1
        topRow = row
        Label(userFrame, text='Print Type', grid=(row, 0), hAlign='left', vAlign='centre')

        # row += 1
        self.exportType = RadioButtons(userFrame, list(EXPORTTYPES.keys()),
                                       grid=(row, 1), direction='h', hAlign='left', spacing=(20, 0),
                                       callback=self._changePrintType)

        row += 1
        Label(userFrame, text='Page orientation', grid=(row, 0), hAlign='left', vAlign='centre')

        # row += 1
        self.pageType = RadioButtons(userFrame, PAGETYPES,
                                     grid=(row, 1), direction='h', hAlign='left', spacing=(20, 0))

        # create a pulldown for the foreground (axes) colour
        row += 1
        foregroundColourFrame = Frame(userFrame, grid=(row, 0), gridSpan=(1, 3), setLayout=True, showBorder=False)
        Label(foregroundColourFrame, text="Foreground Colour", vAlign='c', hAlign='l', grid=(0, 0))
        self.foregroundColourBox = PulldownList(foregroundColourFrame, vAlign='t', grid=(0, 1))
        self.foregroundColourButton = Button(foregroundColourFrame, vAlign='t', hAlign='l', grid=(0, 2), hPolicy='fixed',
                                             callback=self._changeForegroundButton, icon='icons/colours')
        fillColourPulldown(self.foregroundColourBox, allowAuto=False, includeGradients=False)
        self.foregroundColourBox.activated.connect(self._changeForegroundPulldown)

        # create a pulldown for the background colour
        row += 1
        backgroundColourFrame = Frame(userFrame, grid=(row, 0), gridSpan=(1, 3), setLayout=True, showBorder=False)
        Label(backgroundColourFrame, text="Background Colour", vAlign='c', hAlign='l', grid=(0, 0))
        self.backgroundColourBox = PulldownList(backgroundColourFrame, vAlign='t', grid=(0, 1))
        self.backgroundColourButton = Button(backgroundColourFrame, vAlign='t', hAlign='l', grid=(0, 2), hPolicy='fixed',
                                             callback=self._changeBackgroundButton, icon='icons/colours')
        fillColourPulldown(self.backgroundColourBox, allowAuto=False, includeGradients=False)
        self.backgroundColourBox.activated.connect(self._changeBackgroundPulldown)

        row += 1
        self.baseThicknessBox = DoubleSpinBoxCompoundWidget(userFrame, grid=(row, 0), gridSpan=(1, 3), hAlign='left',
                                                            labelText='Line Thickness',
                                                            # value=1.0,
                                                            decimals=2, step=0.05, range=(0.01, 20))
        row += 1
        self.stripPaddingBox = DoubleSpinBoxCompoundWidget(userFrame, grid=(row, 0), gridSpan=(1, 3), hAlign='left',
                                                           labelText='Strip Padding',
                                                           # value=5,
                                                           decimals=0, step=1, range=(0, 50))
        row += 1
        self.exportDpiBox = DoubleSpinBoxCompoundWidget(userFrame, grid=(row, 0), gridSpan=(1, 3), hAlign='left',
                                                        labelText='Image dpi',
                                                        # value=300,
                                                        decimals=0, step=5, range=(36, 2400))

        row += 1

        _rangeRow = self._setupRangeWidget(row, userFrame)
        row += 1

        self.treeView = PrintTreeCheckBoxes(userFrame, project=None, grid=(row, 0), gridSpan=(1, 4))
        userFrame.layout().setRowStretch(row, 100)
        userFrame.addSpacer(5, 5, expandX=True, expandY=True, grid=(row, 3))

    def _setupRangeWidget(self, row, userFrame):
        """Set up the widgets for the range frame
        """
        _rangeFrame = Frame(userFrame, setLayout=True, grid=(row, 0), gridSpan=(1, 8), hAlign='left')
        self._rangeLeft = Frame(_rangeFrame, setLayout=True, grid=(0, 0))
        self._rangeRight = Frame(_rangeFrame, setLayout=True, grid=(0, 1), spacing=(0, 4))

        _rangeRow = 0
        self._useRegion = CheckBoxCompoundWidget(
                self._rangeRight,
                grid=(_rangeRow, 0), hAlign='left', gridSpan=(1, 6),
                orientation='right',
                labelText='Use override region for printing',
                callback=self._useOverrideCallback
                )
        _rangeRow += 1

        # radio buttons for setting mode
        _texts = ['Use Min/Max', 'Use Centre/Width']
        _tipTexts = ['Use minimum/maximum values to define the print region', 'Use centre/width values to define the print region']
        self._rangeRadio = RadioButtons(self._rangeRight, texts=_texts, tipTexts=_tipTexts, direction='h', hAlign='l', selectedInd=1,
                                        grid=(_rangeRow, 0), gridSpan=(1, 8),
                                        callback=self._setModeCallback)
        _rangeRow += 1

        # row of labels
        self._axisLabels = []
        for ii, txt in enumerate(STRIPBUTTONS):
            _label = Label(self._rangeRight, grid=(_rangeRow, ii), text=txt, hAlign='left')
            _label.setVisible(False if ii > 0 else True)
            self._axisLabels.append(_label)
        _rangeRow += 1

        # rows containing spinboxes
        focusColour = getColours()[BORDERFOCUS]
        axes = STRIPAXES
        self._axisSpinboxes = []
        for ii, axis in enumerate(axes):
            _label = Label(self._rangeRight, text=axis, grid=(_rangeRow, 0), hAlign='left')

            # add a box for the selected row
            _colourBox = HighlightBox(self._rangeRight, grid=(_rangeRow, 0), gridSpan=(1, 6), colour=focusColour, lineWidth=1, showBorder=False)
            _colourBox.setFixedHeight(_label.height() + 4)

            _widgets = [_label]
            for bt in range(len(STRIPBUTTONS[1:])):
                _spinbox = DoubleSpinbox(self._rangeRight, grid=(_rangeRow, bt + 1), decimals=2, step=0.1,  # hAlign='left',
                                         callback=partial(self._setSpinbox, ii, STRIPBUTTONS[bt + 1]))
                _spinbox.setFixedWidth(100)
                _spinbox._widgetRow = ii
                _spinbox.installEventFilter(self)
                _spinbox.setVisible(False)

                _widgets.append(_spinbox)

            _widgets.append(_colourBox)
            _rangeRow += 1

            # store the widgets for the callbacks...
            self._axisSpinboxes.append(_widgets)

        # buttons for setting the spinboxes from strip
        _texts = ['Set Print Region', 'Set Min', 'Set Max', 'Set Centre', 'Set Width']
        _tipTexts = ['Set all values for the print region from the selected strip.\nValues are set for the highlighted row',
                     'Set the maximum value for the print region from the selected strip.\nValue is set for the highlighted row',
                     'Set the minimum value for the print region from the selected strip.\nValue is set for the highlighted row',
                     'Set the centre value for the print region from the selected strip.\nValue is set for the highlighted row',
                     'Set the width value for the print region from the selected strip.\nValue is set for the highlighted row']
        _callbacks = [self._setStripRegion, self._setStripMin, self._setStripMax, self._setStripCentre, self._setStripWidth]
        self._setRangeButtons = ButtonList(self._rangeRight, texts=_texts, tipTexts=_tipTexts,
                                           grid=(_rangeRow, 0), gridSpan=(1, 8), hAlign='l',
                                           callbacks=_callbacks,
                                           setMinimumWidth=False, setLastButtonFocus=False,
                                           )
        for _btn in self._setRangeButtons.buttons[1:]:
            _btn.setVisible(False)
        _rangeRow += 1

        self._rangeRight.addSpacer(5, 5, grid=(_rangeRow, 6), expandX=True)
        self._rangeRight.addSpacer(4, 4, grid=(_rangeRow, 5))
        _rangeRow += 1

        # list to hold the current strips
        Label(self._rangeLeft, grid=(0, 0), text='Strips', hAlign='left')
        self._stripLists = ListWidget(self._rangeLeft, grid=(1, 0), callback=self._setRangeState,
                                      multiSelect=False, acceptDrops=False, copyDrop=False,
                                      )
        self._rangeLeft.setFixedSize(130, 180)

        _rangeFrame.getLayout().setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self._rangeRight.getLayout().setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self._rangeRight.layout().setColumnStretch(6, 1000)
        self._rangeRight.getLayout().setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        return _rangeRow

    def _initialiseStripList(self):
        """Setup the lists containing strips.spectrumDisplays before populating
        """
        self.objects = None
        self._currentStrip = None
        self._currentStrips = []  # there may be multiple selected in the stripList
        self._currentAxis = 0
        self._stripDict = {}

        if self.strips:
            self.objects = {strip.id: (strip, strip.pid) for strip in self.strips}
            for strip in self.strips:
                _data = self._stripDict[strip.id] = _StripData()
                _data.strip = strip
                _data._initialise()

            # define the contents for the object pulldown
            if len(self.strips) > 1:
                specDisplays = set()
                if self.includeSpectrumDisplays:

                    # get the list of spectrumDisplays containing the strips
                    for strip in self.strips:
                        if len(strip.spectrumDisplay.strips) > 1:
                            specDisplays.add(strip.spectrumDisplay)

                    # add to the pulldown objects
                    for spec in specDisplays:
                        self.objects['SpectrumDisplay: %s' % spec.id] = (spec, spec.pid)

    def _setStripRegion(self, *args):
        try:
            dd = self._stripDict.get(self._currentStrip)
            ii = self._currentAxis
            ddAxis = dd.axes[ii]
            # set all values for the print region
            region = dd.strip.getAxisRegion(ii)
            ddAxis[STRIPMIN], ddAxis[STRIPMAX] = min(region), max(region)
            ddAxis[STRIPCENTRE] = dd.strip.getAxisPosition(ii)
            ddAxis[STRIPWIDTH] = dd.strip.getAxisWidth(ii)
        except Exception as es:
            pass
        else:
            self._setRangeState(self._currentStrip)
            self._focusButton(self._currentAxis, STRIPMIN)

    def _setStripMinValue(self, ddAxis, value):
        """Set the minimum value
        Update the row values and set the spinbox constraints"""
        ddAxis[STRIPMIN] = value
        # update the centre/width
        ddAxis[STRIPMAX] = max(value, ddAxis[STRIPMAX])
        _centre = (value + ddAxis[STRIPMAX]) / 2.0
        ddAxis[STRIPCENTRE] = _centre
        ddAxis[STRIPWIDTH] = abs(ddAxis[STRIPMAX] - value)

    def _setStripMin(self, *args):
        try:
            dd = self._stripDict.get(self._currentStrip)
            ddAxis = dd.axes[self._currentAxis]
            region = dd.strip.getAxisRegion(self._currentAxis)
            self._setStripMinValue(ddAxis, min(region))

        except Exception as es:
            pass
        else:
            self._setRangeState(self._currentStrip)
            self._focusButton(self._currentAxis, STRIPMIN)

    def _setStripMaxValue(self, ddAxis, value):
        """Set the maximum value
        Update the row values and set the spinbox constraints"""
        ddAxis[STRIPMAX] = value
        # update the centre/width
        ddAxis[STRIPMIN] = min(value, ddAxis[STRIPMIN])
        _centre = (ddAxis[STRIPMIN] + value) / 2.0
        ddAxis[STRIPCENTRE] = _centre
        ddAxis[STRIPWIDTH] = abs(value - ddAxis[STRIPMIN])

    def _setStripMax(self, *args):
        try:
            dd = self._stripDict.get(self._currentStrip)
            ddAxis = dd.axes[self._currentAxis]
            region = dd.strip.getAxisRegion(self._currentAxis)
            self._setStripMaxValue(ddAxis, max(region))

        except Exception as es:
            pass
        else:
            self._setRangeState(self._currentStrip)
            self._focusButton(self._currentAxis, STRIPMAX)

    def _setStripCentreValue(self, ddAxis, centre):
        """Set the centre value
        Update the row values and set the spinbox constraints"""
        ddAxis[STRIPCENTRE] = centre
        # update the min/max
        diff = abs(ddAxis[STRIPWIDTH] / 2.0)
        ddAxis[STRIPMIN] = centre - diff
        ddAxis[STRIPMAX] = centre + diff

    def _setStripCentre(self, *args):
        try:
            dd = self._stripDict.get(self._currentStrip)
            ddAxis = dd.axes[self._currentAxis]
            centre = dd.strip.getAxisPosition(self._currentAxis)
            self._setStripCentreValue(ddAxis, centre)

        except Exception as es:
            pass
        else:
            self._setRangeState(self._currentStrip)
            self._focusButton(self._currentAxis, STRIPCENTRE)

    def _setStripWidthValue(self, ddAxis, width):
        """Set the width value
        Update the row values and set the spinbox constraints"""
        ddAxis[STRIPWIDTH] = width
        # update the min/max
        centre = ddAxis[STRIPCENTRE]
        ddAxis[STRIPMIN] = centre - abs(width / 2.0)
        ddAxis[STRIPMAX] = centre + abs(width / 2.0)

    def _setStripWidth(self, *args):
        try:
            dd = self._stripDict.get(self._currentStrip)
            ddAxis = dd.axes[self._currentAxis]
            width = dd.strip.getAxisWidth(self._currentAxis)
            self._setStripWidthValue(ddAxis, width)

        except Exception as es:
            pass
        else:
            self._setRangeState(self._currentStrip)
            self._focusButton(self._currentAxis, STRIPWIDTH)

    def _setSpinbox(self, row, button, value):
        """Set the value in the storage dict from the spinbox change
        """
        self._setSpinboxAxis(row)
        try:
            _dd = self._stripDict.get(self._currentStrip)

            if button == STRIPMIN:
                self._setStripMinValue(_dd.axes[row], value)
            elif button == STRIPMAX:
                self._setStripMaxValue(_dd.axes[row], value)
            elif button == STRIPCENTRE:
                self._setStripCentreValue(_dd.axes[row], value)
            else:
                self._setStripWidthValue(_dd.axes[row], value)

            self._setRangeState(self._currentStrip)
            self._focusButton(row, button)

        except Exception as es:
            pass

    def _setSpinboxAxis(self, row):
        """Change the current selected row of spinboxes"""
        self._currentAxis = row
        for ii in range(2):
            self._axisSpinboxes[ii][-1].showBorder = (self._currentAxis == ii)

    def eventFilter(self, obj, event):
        """Event filter to handle focus change on spinboxes
        """
        if event.type() in [QtCore.QEvent.WindowActivate, QtCore.QEvent.FocusIn]:
            self._setSpinboxAxis(obj._widgetRow)

        return False

    def _useOverrideCallback(self, value):
        """User has checked/unchecked useOverride
        """
        try:
            _dd = self._stripDict.get(self._currentStrip)
            _dd.useRegion = value
        except Exception as es:
            pass
        else:
            self._setRangeState(self._currentStrip)

    def _setModeCallback(self):
        """User has changed minMax/centreWidth mode
        """
        try:
            _dd = self._stripDict.get(self._currentStrip)
            _dd.minMaxMode = self._rangeRadio.getIndex()
        except Exception as es:
            pass
        else:
            self._setRangeState(self._currentStrip)

    def populate(self, userframe):
        """Populate the widgets with project
        """
        with self.blockWidgetSignals(userframe):
            self._populate(userframe)

    def _populate(self, userframe):
        """Populate the widget
        """
        # define the contents for the object pulldown
        if len(self.strips) > 1:
            pulldownLabel = 'Select Strip:'
            if self.includeSpectrumDisplays:

                # get the list of spectrumDisplays containing the strips
                for strip in self.strips:
                    if len(strip.spectrumDisplay.strips) > 1:
                        pulldownLabel = 'Select Item:'
                        break
        else:
            pulldownLabel = 'Current Strip:'

        self.objectPulldown.setLabelText(pulldownLabel)
        self.objectPulldown.pulldownList.setData(sorted([ky for ky in self.objects.keys()]))

        # set the page types
        self.exportType.set(EXPORTPDF)
        self.pageType.set(PAGEPORTRAIT)

        # populate pulldown from foreground colour
        spectrumColourKeys = list(spectrumColours.keys())
        self.foregroundColour = '#000000'
        self.backgroundColour = '#FFFFFF'

        if self.foregroundColour in spectrumColourKeys:
            self.foregroundColourBox.setCurrentText(spectrumColours[self.foregroundColour])
        else:
            # add new colour to the pulldowns if not defined
            addNewColourString(self.foregroundColour)
            fillColourPulldown(self.foregroundColourBox, allowAuto=False, includeGradients=False)
            fillColourPulldown(self.backgroundColourBox, allowAuto=False, includeGradients=False)
            self.foregroundColourBox.setCurrentText(spectrumColours[self.foregroundColour])

        if self.backgroundColour in spectrumColourKeys:
            self.backgroundColourBox.setCurrentText(spectrumColours[self.backgroundColour])
        else:
            # add new colour to the pulldowns if not defined
            addNewColourString(self.backgroundColour)
            fillColourPulldown(self.foregroundColourBox, allowAuto=False, includeGradients=False)
            fillColourPulldown(self.backgroundColourBox, allowAuto=False, includeGradients=False)
            self.backgroundColourBox.setCurrentText(spectrumColours[self.backgroundColour])

        self.baseThicknessBox.setValue(1.0)
        self.stripPaddingBox.setValue(5)
        self.exportDpiBox.setValue(300)

        # set the pulldown to current strip of selected
        if self.current and self.current.strip:
            self.objectPulldown.select(self.current.strip.id)
            self.strip = self.current.strip
        else:
            if self.strips:
                self.objectPulldown.select(self.strips[0].id)
                self.strip = self.strips[0]
            else:
                self.strip = None

        # fill the range widgets from the strips
        self._populateRange()
        # fill the tree from the current strip
        self._populateTreeView()

        # set the default save name
        exType = self.exportType.get()
        if exType in EXPORTTYPES:
            exportExtension = EXPORTTYPES[exType][EXPORTEXT]
        else:
            raise ValueError('bad export type')

        self.setSave(self.objectPulldown.getText() + exportExtension)

    def _populateRange(self):
        """Populate the list/spinboxes in range widget
        """
        self._rangeLeft.setVisible(self.spectrumDisplay is not None)
        if self.strip:
            self._setRangeState(self.strip.id)

        self._stripLists.clear()
        self._stripLists.addItems(list(strip.id for strip in self.strips))
        self._stripLists.select(self._currentStrip)

    def _setRangeState(self, strip, setButton=None, setRow=None):
        try:
            stripId = strip.text()
        except Exception as es:
            stripId = strip
        finally:
            self._rangeRight.setVisible(False)

            with self.blockWidgetSignals(self._rangeRight):
                # set the current Id for updating range dict
                self._currentStrip = stripId

                self._setSpinboxConstraints(stripId, state=False)

                _dd = self._stripDict.get(stripId, None)
                if _dd:
                    self._useRegion.set(_dd.useRegion)
                    self._rangeRadio.setIndex(_dd.minMaxMode)

                    # change visibility of buttons dependent on minMaxMode
                    for btn in [STRIPMIN, STRIPMAX]:
                        self._axisLabels[STRIPBUTTONS.index(btn)].setVisible(_dd.minMaxMode == 0)
                        for ii in range(len(STRIPAXES)):
                            self._axisSpinboxes[ii][STRIPBUTTONS.index(btn)].setVisible(_dd.minMaxMode == 0)
                        self._setRangeButtons.buttons[STRIPBUTTONS.index(btn)].setVisible(_dd.minMaxMode == 0)
                    for btn in [STRIPCENTRE, STRIPWIDTH]:
                        self._axisLabels[STRIPBUTTONS.index(btn)].setVisible(_dd.minMaxMode == 1)
                        for ii in range(len(STRIPAXES)):
                            self._axisSpinboxes[ii][STRIPBUTTONS.index(btn)].setVisible(_dd.minMaxMode == 1)
                        self._setRangeButtons.buttons[STRIPBUTTONS.index(btn)].setVisible(_dd.minMaxMode == 1)

                    for ii in range(len(STRIPAXES)):
                        axis = _dd.axes[ii]
                        self._axisSpinboxes[ii][STRIPBUTTONS.index(STRIPMIN)].set(axis[STRIPMIN])
                        self._axisSpinboxes[ii][STRIPBUTTONS.index(STRIPMAX)].set(axis[STRIPMAX])
                        self._axisSpinboxes[ii][STRIPBUTTONS.index(STRIPCENTRE)].set(axis[STRIPCENTRE])
                        self._axisSpinboxes[ii][STRIPBUTTONS.index(STRIPWIDTH)].set(axis[STRIPWIDTH])

                        for bb in self._axisSpinboxes[ii]:
                            bb.setEnabled(_dd.useRegion)
                        self._axisSpinboxes[ii][-1].showBorder = (_dd.useRegion and (self._currentAxis == ii))

                    self._rangeRadio.setEnabled(_dd.useRegion)
                    self._setRangeButtons.setEnabled(_dd.useRegion)

                self._setSpinboxConstraints(stripId)

            self._rangeRight.setVisible(True)
            self._rangeRight.update()

    def _focusButton(self, row, button):
        """Set the focus to the selected button
        """
        try:
            self._axisSpinboxes[row][STRIPBUTTONS.index(button)].setFocus()
        except Exception as es:
            pass

    def _setSpinboxConstraints(self, stripId, state=True):
        """Set the min/max/width constraints for the spinboxes associated with the stripId
        """
        try:
            _dd = self._stripDict.get(stripId, None)
            if _dd:
                for ii in range(len(STRIPAXES)):
                    axis = _dd.axes[ii]
                    # set min.max constraints for buttons
                    # not sure if these need to change as the button values are changed
                    # self._axisSpinboxes[ii][STRIPBUTTONS.index(STRIPMIN)].setMaximum(axis[STRIPMAX] if state else None)
                    # self._axisSpinboxes[ii][STRIPBUTTONS.index(STRIPMAX)].setMinimum(axis[STRIPMIN] if state else None)
                    self._axisSpinboxes[ii][STRIPBUTTONS.index(STRIPWIDTH)].setMinimum(0.0)

        except Exception as es:
            pass

    def storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        print(f'  storing {self._stripDict}')
        # NOTE:ED - need to put the other settings in here
        ExportStripToFilePopup._storedState[self._SAVESTRIPS] = self._stripDict.copy()
        ExportStripToFilePopup._storedState[self._SAVECURRENTSTRIP] = self._currentStrip
        ExportStripToFilePopup._storedState[self._SAVECURRENTAXIS] = self._currentAxis

    def restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        print(f'  restoring {self._stripDict}')
        self._stripDict.update(ExportStripToFilePopup._storedState.get(self._SAVESTRIPS, {}))
        print(f'  restoring {self._stripDict}')
        _val = ExportStripToFilePopup._storedState.get(self._SAVECURRENTSTRIP, None)
        if _val:
            self._currentStrip = _val
        self._currentAxis = ExportStripToFilePopup._storedState.get(self._SAVECURRENTAXIS, 0)

    def _changeColourButton(self):
        """Popup a dialog and set the colour in the pulldowns
        """
        dialog = ColourDialog(self)

        newColour = dialog.getColor()
        if newColour:
            addNewColour(newColour)
            fillColourPulldown(self.foregroundColourBox, allowAuto=False, includeGradients=False)
            fillColourPulldown(self.backgroundColourBox, allowAuto=False, includeGradients=False)

            return newColour

    def _changeForegroundPulldown(self, int):
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.foregroundColourBox.currentText()))]
        if newColour:
            self.foregroundColour = newColour

    def _changeForegroundButton(self, int):
        """Change the colour from the foreground colour button
        """
        newColour = self._changeColourButton()
        if newColour:
            self.foregroundColourBox.setCurrentText(spectrumColours[newColour.name()])
            self.foregroundColour = newColour.name()

    def _changeBackgroundPulldown(self, int):
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.backgroundColourBox.currentText()))]
        if newColour:
            self.backgroundColour = newColour

    def _changeBackgroundButton(self, int):
        """Change the colour from the background colour button
        """
        newColour = self._changeColourButton()
        if newColour:
            self.backgroundColourBox.setCurrentText(spectrumColours[newColour.name()])
            self.backgroundColour = newColour.name()

    def _changePulldown(self, int):
        selected = self.objectPulldown.getText()
        exType = self.exportType.get()
        if exType in EXPORTTYPES:
            exportExtension = EXPORTTYPES[exType][EXPORTEXT]
        else:
            raise ValueError('bad export type')

        if 'SpectrumDisplay' in selected:
            self.spectrumDisplay = self.objects[selected][0]
            self.strip = self.spectrumDisplay.strips[0]

            self.setSave(self.spectrumDisplay.id + exportExtension)

        else:
            self.spectrumDisplay = None
            self.strip = self.objects[selected][0]

            self.setSave(self.strip.id + exportExtension)

        self._populateRange()
        selectedList = self.treeView.getCheckStateItems()
        self._populateTreeView(selectedList)

    def _populateTreeView(self, selectList=None):
        self.treeView.clear()

        if not self.strip:
            return

        # add Spectra to the treeView
        if self.strip.spectrumViews:
            item = QtWidgets.QTreeWidgetItem(self.treeView)
            item.setText(0, 'Spectra')
            item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

            for specView in self.strip.spectrumViews:
                child = QtWidgets.QTreeWidgetItem(item)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                child.setData(1, 0, specView.spectrum)
                child.setText(0, specView.spectrum.pid)
                child.setCheckState(0, QtCore.Qt.Checked if specView.isVisible() else QtCore.Qt.Checked)

        # find peak/integral/multiplets attached to the spectrumViews
        peakLists = []
        integralLists = []
        multipletLists = []
        for specView in self.strip.spectrumViews:
            validPeakListViews = [pp for pp in specView.peakListViews]
            validIntegralListViews = [pp for pp in specView.integralListViews]
            validMultipletListViews = [pp for pp in specView.multipletListViews]
            peakLists.extend(validPeakListViews)
            integralLists.extend(validIntegralListViews)
            multipletLists.extend(validMultipletListViews)

        printItems = []
        if peakLists:
            item = QtWidgets.QTreeWidgetItem(self.treeView)
            item.setText(0, 'Peak Lists')
            item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

            for pp in peakLists:
                child = QtWidgets.QTreeWidgetItem(item)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                child.setData(1, 0, pp.peakList)
                child.setText(0, pp.peakList.pid)
                child.setCheckState(0, QtCore.Qt.Checked if pp.isVisible() else QtCore.Qt.Checked)

            printItems.extend((GLPEAKSYMBOLS,
                               GLPEAKLABELS))

        if integralLists:
            item = QtWidgets.QTreeWidgetItem(self.treeView)
            item.setText(0, 'Integral Lists')
            item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

            for pp in integralLists:
                child = QtWidgets.QTreeWidgetItem(item)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                child.setData(1, 0, pp.integralList)
                child.setText(0, pp.integralList.pid)
                child.setCheckState(0, QtCore.Qt.Checked if pp.isVisible() else QtCore.Qt.Checked)

            printItems.extend((GLINTEGRALSYMBOLS,
                               GLINTEGRALLABELS))

        if multipletLists:
            item = QtWidgets.QTreeWidgetItem(self.treeView)
            item.setText(0, 'Multiplet Lists')
            item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

            for pp in multipletLists:
                child = QtWidgets.QTreeWidgetItem(item)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                child.setData(1, 0, pp.multipletList)
                child.setText(0, pp.multipletList.pid)
                child.setCheckState(0, QtCore.Qt.Checked if pp.isVisible() else QtCore.Qt.Checked)

            printItems.extend((GLMULTIPLETSYMBOLS,
                               GLMULTIPLETLABELS))

        # populate the treeview with the currently selected peak/integral/multiplet lists
        self.treeView._uncheckAll()
        pidList = []
        for specView in self.strip.spectrumViews:
            validPeakListViews = [pp.peakList.pid for pp in specView.peakListViews
                                  if pp.isVisible()
                                  and specView.isVisible()]
            validIntegralListViews = [pp.integralList.pid for pp in specView.integralListViews
                                      if pp.isVisible()
                                      and specView.isVisible()]
            validMultipletListViews = [pp.multipletList.pid for pp in specView.multipletListViews
                                       if pp.isVisible()
                                       and specView.isVisible()]
            pidList.extend(validPeakListViews)
            pidList.extend(validIntegralListViews)
            pidList.extend(validMultipletListViews)
            if specView.isVisible():
                pidList.append(specView.spectrum.pid)

        self.treeView.selectObjects(pidList)

        printItems.extend(GLEXTENDEDLIST)

        if selectList is None:
            selectList = {GLSPECTRUMBORDERS   : QtCore.Qt.Checked if self.application.preferences.general.showSpectrumBorder else QtCore.Qt.Unchecked,
                          GLSPECTRUMCONTOURS  : QtCore.Qt.Checked,
                          GLCURSORS           : QtCore.Qt.Unchecked,
                          GLGRIDLINES         : QtCore.Qt.Checked if self.strip.gridVisible else QtCore.Qt.Unchecked,
                          GLDIAGONALLINE      : QtCore.Qt.Checked if self.strip._CcpnGLWidget._matchingIsotopeCodes else QtCore.Qt.Unchecked,
                          GLDIAGONALSIDEBANDS : (QtCore.Qt.Checked if (self.strip._CcpnGLWidget._sideBandsVisible and self.strip._CcpnGLWidget._matchingIsotopeCodes)
                                                 else QtCore.Qt.Unchecked),
                          GLSHOWSPECTRAONPHASE: QtCore.Qt.Checked if self.strip._CcpnGLWidget._showSpectraOnPhasing else QtCore.Qt.Unchecked
                          }
        self.printList = []

        # add Print Options to the treeView
        item = QtWidgets.QTreeWidgetItem(self.treeView)
        item.setText(0, 'Print Options')
        item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

        for itemName in printItems:
            child = QtWidgets.QTreeWidgetItem(item)
            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
            # child.setData(1, 0, obj)
            child.setText(0, itemName)
            child.setCheckState(0, QtCore.Qt.Checked if itemName not in selectList else selectList[itemName])

        item.setExpanded(True)

    def _changePrintType(self):
        selected = self.exportType.get()
        lastPath = self.getSaveTextWidget()

        if selected in EXPORTTYPES:
            ext = EXPORTTYPES[selected][EXPORTEXT]
            filt = EXPORTTYPES[selected][EXPORTFILTER]

            lastPath.assureSuffix(ext)
            self._dialogFilter = filt
            self.updateDialog()
            self._updateButtonText()
            self.updateFilename(lastPath)

        else:
            raise TypeError('bad export type')

    def buildParameters(self):
        """build parameters dict from the user widgets, to be passed to the export method.
        :return: dict - user parameters
        """

        selected = self.objectPulldown.getText()
        if 'SpectrumDisplay' in selected:
            spectrumDisplay = self.objects[selected][0]
            strip = spectrumDisplay.strips[0]
            stripDirection = self.spectrumDisplay.stripArrangement
        else:
            spectrumDisplay = None
            strip = self.objects[selected][0]
            stripDirection = 'Y'

        prType = self.exportType.get()
        pageType = self.pageType.get()
        foregroundColour = hexToRgbRatio(self.foregroundColour)
        backgroundColour = hexToRgbRatio(self.backgroundColour)
        baseThickness = self.baseThicknessBox.getValue()

        # there are now unique per-spectrumDisplay, may differ from preferences
        symbolThickness = strip.symbolThickness
        contourThickness = strip.contourThickness
        aliasEnabled = strip.aliasEnabled
        aliasShade = strip.aliasShade
        aliasLabelsEnabled = strip.aliasLabelsEnabled
        stripPadding = self.stripPaddingBox.getValue()
        exportDpi = self.exportDpiBox.getValue()

        if strip:
            # return the parameters
            params = {GLFILENAME          : self.exitFilename,
                      GLSPECTRUMDISPLAY   : spectrumDisplay,
                      GLSTRIP             : strip,
                      GLWIDGET            : strip._CcpnGLWidget,
                      GLPRINTTYPE         : prType,
                      GLPAGETYPE          : pageType,
                      GLFOREGROUND        : foregroundColour,
                      GLBACKGROUND        : backgroundColour,
                      GLBASETHICKNESS     : baseThickness,
                      GLSYMBOLTHICKNESS   : symbolThickness,
                      GLCONTOURTHICKNESS  : contourThickness,
                      GLALIASENABLED      : aliasEnabled,
                      GLALIASSHADE        : aliasShade,
                      GLALIASLABELSENABLED: aliasLabelsEnabled,
                      GLSTRIPDIRECTION    : stripDirection,
                      GLSTRIPPADDING      : stripPadding,
                      GLEXPORTDPI         : exportDpi,
                      GLSELECTEDPIDS      : self.treeView.getSelectedObjectsPids(),
                      GLSTRIPREGIONS      : self._stripDict,
                      }
            selectedList = self.treeView.getSelectedItems()
            for itemName in self.fullList:
                params[itemName] = True if itemName in selectedList else False

            return params

    def exportToFile(self, filename=None, params=None):
        """Export to file
        :param filename: filename to export
        :param params: dict - user defined parameters for export
        """

        if params:
            filename = params[GLFILENAME]
            glWidget = params[GLWIDGET]
            prType = params[GLPRINTTYPE]

            if prType == EXPORTPDF:
                pdfExport = glWidget.exportToPDF(filename, params)
                if pdfExport:
                    pdfExport.writePDFFile()
            elif prType == EXPORTSVG:
                svgExport = glWidget.exportToSVG(filename, params)
                if svgExport:
                    svgExport.writeSVGFile()
            elif prType == EXPORTPNG:
                pngExport = glWidget.exportToPNG(filename, params)
                if pngExport:
                    pngExport.writePNGFile()
            elif prType == EXPORTPS:
                pngExport = glWidget.exportToPS(filename, params)
                if pngExport:
                    pngExport.writePSFile()

    def actionButtons(self):
        self.setOkButton(callback=self._saveAndCloseDialog, text='Save and Close', tipText='Export the strip and close the dialog')
        self.setCancelButton(callback=self._rejectDialog, text='Close', tipText='Close the dialog')
        self.setCloseButton(callback=self._saveDialog, text='Save', tipText='Export the strip')
        self.setDefaultButton(self.CANCELBUTTON)

    def _saveDialog(self, exitSaveFileName=None):
        """save button has been clicked
        """
        selected = self.exportType.get()
        lastPath = self.getSaveTextWidget()

        if selected in EXPORTTYPES:
            lastPath = lastPath.assureSuffix(EXPORTTYPES[selected][EXPORTEXT])

        self.setSaveTextWidget(lastPath)
        self.exitFilename = lastPath

        if self.pathEdited is False:
            # user has not changed the path so we can accept()
            self._exportToFile()
        else:
            # have edited the path so check the new file
            if self.exitFilename.is_file():
                yes = showYesNoWarning('%s already exists.' % self.exitFilename,
                                       'Do you want to replace it?')
                if yes:
                    self._exportToFile()
            else:
                if self.exitFilename.is_dir():
                    showWarning('Export Error:', 'Filename must be a file.')
                else:
                    self._exportToFile()

    def _saveAndCloseDialog(self, exitSaveFilename=None):
        """save and Close button has been clicked
        """
        selected = self.exportType.get()
        lastPath = self.getSaveTextWidget()

        if selected in EXPORTTYPES:
            lastPath = lastPath.assureSuffix(EXPORTTYPES[selected][EXPORTEXT])

        self.setSaveTextWidget(lastPath)
        self.exitFilename = lastPath

        self._acceptDialog()

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        """Subclass keypress to stop enter/return on default button
        """
        if a0.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            return
        super().keyPressEvent(a0)


if __name__ == '__main__':
    # from sandbox.Geerten.Refactored.framework import Framework
    # from sandbox.Geerten.Refactored.programArguments import Arguments
    #
    #
    # _makeMainWindowVisible = False
    #
    #
    # class MyProgramme(Framework):
    #     "My first app"
    #     pass
    #
    #
    # myArgs = Arguments()
    # myArgs.noGui = False
    # myArgs.debug = True
    #
    # application = MyProgramme('MyProgramme', '3.0.0-beta3', args=myArgs)
    # ui = application.ui
    # ui.initialize()
    #
    # if _makeMainWindowVisible:
    #     ui.mainWindow._updateMainWindow(newProject=True)
    #     ui.mainWindow.show()
    #     QtWidgets.QApplication.setActiveWindow(ui.mainWindow)
    #
    # dialog = ExportStripToFilePopup(parent=application.mainWindow,
    #                                 mainWindow=application.mainWindow,
    #                                 strips=[],
    #                                 preferences=application.preferences)
    # result = dialog.exec_()

    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication


    app = newTestApplication()
    application = getApplication()

    dialog = ExportStripToFilePopup(strips=[])
    result = dialog.exec_()
