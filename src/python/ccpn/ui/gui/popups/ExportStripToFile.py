"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-01 11:22:51 +0000 (Mon, March 01, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-06 15:51:11 +0000 (Thu, July 06, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict as OD
from ccpn.ui.gui.widgets.Spacer import Spacer
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes, PrintTreeCheckBoxes
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.util.Colour import spectrumColours, addNewColour, fillColourPulldown, addNewColourString
from ccpn.util.Colour import rgbRatioToHex, hexToRgbRatio, colourNameNoSpace
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning
from ccpn.ui.gui.widgets.CompoundWidgets import DoubleSpinBoxCompoundWidget
from ccpn.ui.gui.widgets.MessageDialog import progressManager


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

from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import GLFILENAME, GLGRIDLINES, GLAXISLABELS, GLAXISMARKS, \
    GLINTEGRALLABELS, GLINTEGRALSYMBOLS, GLMARKLABELS, GLMARKLINES, GLMULTIPLETLABELS, GLREGIONS, \
    GLMULTIPLETSYMBOLS, GLOTHERLINES, GLPEAKLABELS, GLPEAKSYMBOLS, GLPRINTTYPE, GLPAGETYPE, GLSELECTEDPIDS, \
    GLSPECTRUMBORDERS, GLSPECTRUMCONTOURS, GLSPECTRUMLABELS, \
    GLSPECTRUMDISPLAY, GLSTRIP, GLSTRIPLABELLING, GLTRACES, \
    GLWIDGET, GLPLOTBORDER, GLAXISLINES, GLBACKGROUND, GLBASETHICKNESS, GLSYMBOLTHICKNESS, GLFOREGROUND, \
    GLCONTOURTHICKNESS, GLSHOWSPECTRAONPHASE, \
    GLAXISTITLES, GLAXISUNITS, GLAXISMARKSINSIDE, GLSTRIPDIRECTION, GLSTRIPPADDING, GLEXPORTDPI, \
    GLFULLLIST, GLEXTENDEDLIST, GLDIAGONALLINE, GLCURSORS, GLDIAGONALSIDEBANDS


class ExportStripToFilePopup(ExportDialogABC):
    """
    Class to handle printing strips to file
    """

    def __init__(self, parent=None, mainWindow=None, title='Export Strip to File',
                 fileMode='anyFile',
                 acceptMode='export',
                 selectFile=None,
                 fileFilter=EXPORTFILTERS,
                 strips=None,
                 includeSpectumDisplays=True,
                 **kwds):
        """
        Initialise the widget
        """
        # initialise attributes
        self.strips = strips
        self.objects = {}
        self.includeSpectumDisplays = includeSpectumDisplays
        self.strip = None
        self.spectrumDisplay = None
        self.spectrumDisplays = set()
        self.specToExport = None

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
        self.treeView = PrintTreeCheckBoxes(userFrame, project=None, grid=(row, 0), gridSpan=(1, 4))
        Spacer(userFrame, 0, 0, hPolicy='expanding', vPolicy='expanding', grid=(row, 3))

    def populate(self, userframe):
        """Populate the widgets with project
        """

        with self.blockWidgetSignals(userframe):
            self._populate(userframe)

    def _populate(self, userframe):
        """Populate the widget
        """
        self.objects = {strip.id: (strip, strip.pid) for strip in self.strips}

        # define the contents for the object pulldown
        if len(self.strips) > 1:
            specDisplays = set()
            if self.includeSpectumDisplays:

                # get the list of spectrumDisplays containing the strips
                for strip in self.strips:
                    if len(strip.spectrumDisplay.strips) > 1:
                        specDisplays.add(strip.spectrumDisplay)

                # add to the pulldown objects
                for spec in specDisplays:
                    self.objects['SpectrumDisplay: %s' % spec.id] = (spec, spec.pid)

            pulldownLabel = 'Select Item:' if specDisplays else 'Select Strip:'

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

        # fill the tree from the current strip
        self._populateTreeView()

        # set the default save name
        exType = self.exportType.get()
        if exType in EXPORTTYPES:
            exportExtension = EXPORTTYPES[exType][EXPORTEXT]
        else:
            raise ValueError('bad export type')

        self.setSave(self.objectPulldown.getText() + exportExtension)

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

            self.updateFilename(self.spectrumDisplay.id + exportExtension)
        else:
            self.spectrumDisplay = None
            self.strip = self.objects[selected][0]

            self.updateFilename(self.strip.id + exportExtension)

        selectedList = self.treeView.getCheckStateItems()
        self._populateTreeView(selectedList)

    # def _changeSpectrumDisplay(self):
    #     selected = self.specToExport.get()
    #     # if selected != self.strip.id:
    #     #     self.strip = self.strips[self.stripIds.index(selected)]
    #     self.spectrumDisplay = self.objects[selected][0]
    #     self.strip = self.spectrumDisplay.strips[0]
    #
    #     selectedList = self.treeView.getItems()
    #     self._populateTreeView(selectedList)
    #     self.stripToExport.deselectAll()
    #
    # def _changeStrip(self):
    #     selected = self.stripToExport.get()
    #     # if selected != self.strip.id:
    #     # self.strip = self.strips[self.stripIds.index(selected)]
    #     self.strip = self.objects[selected][0]
    #
    #     selectedList = self.treeView.getItems()
    #     self._populateTreeView(selectedList)
    #     if self.specToExport:
    #         self.specToExport.deselectAll()

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
                child.setCheckState(0, QtCore.Qt.Checked if specView.isVisible() else QtCore.Qt.Checked)

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
                child.setCheckState(0, QtCore.Qt.Checked if specView.isVisible() else QtCore.Qt.Checked)

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
                child.setCheckState(0, QtCore.Qt.Checked if specView.isVisible() else QtCore.Qt.Checked)

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

            # if not lastPath.endswith(ext):
            #     # remove other extension
            #     lastPath = os.path.splitext(lastPath)[0]
            #     lastPath += ext
            lastPath.assureSuffix(ext)
            self._dialogFilter = filt
            self.updateDialog()
            self._updateButtonText()
            self.updateFilename(lastPath)

        else:
            raise TypeError('bad export type')

        # if selected == EXPORTPDF:
        #     if not lastPath.endswith(EXPORTPDFEXTENSION):
        #         # remove other extension
        #         if lastPath.endswith(EXPORTSVGEXTENSION):
        #             lastPath = os.path.splitext(lastPath)[0]
        #         lastPath += EXPORTPDFEXTENSION
        #     self._dialogFilter = EXPORTPDFFILTER
        #     self.updateDialog()
        #     self.updateFilename(lastPath)
        #
        # elif selected == EXPORTSVG:
        #     if not lastPath.endswith(EXPORTSVGEXTENSION):
        #         # remove other extension
        #         if lastPath.endswith(EXPORTPDFEXTENSION):
        #             lastPath = os.path.splitext(lastPath)[0]
        #         lastPath += EXPORTSVGEXTENSION
        #     self._dialogFilter = EXPORTSVGFILTER
        #     self.updateDialog()
        #     self.updateFilename(lastPath)

    def buildParameters(self):
        """build parameters dict from the user widgets, to be passed to the export method.
        :return: dict - user parameters
        """

        # build the export dict and flags
        # if self.specToExport and self.specToExport.isChecked:
        #     selected = self.specToExport.get()
        #     # thisPid = self.objects[pIndex][1]
        #     spectrumDisplay = self.objects[selected][0]
        #     strip = spectrumDisplay.strips[0]
        # else:
        #     selected = self.stripToExport.get()
        #     # thisPid = self.stripPids[pIndex]
        #     spectrumDisplay = None
        #     strip = self.objects[selected][0]     #self.project.getByPid(thisPid)

        selected = self.objectPulldown.getText()
        if 'SpectrumDisplay' in selected:
            spectrumDisplay = self.objects[selected][0]
            strip = spectrumDisplay.strips[0]
            stripDirection = self.spectrumDisplay.stripArrangement
        else:
            spectrumDisplay = None
            strip = self.objects[selected][0]
            stripDirection = 'Y'

        # prIndex = self.exportType.getIndex()
        # prType = EXPORTTYPES[prIndex]
        prType = self.exportType.get()
        pageType = self.pageType.get()
        foregroundColour = hexToRgbRatio(self.foregroundColour)
        backgroundColour = hexToRgbRatio(self.backgroundColour)
        baseThickness = self.baseThicknessBox.getValue()
        symbolThickness = self.application.preferences.general.symbolThickness
        contourThickness = self.application.preferences.general.contourThickness
        stripPadding = self.stripPaddingBox.getValue()
        exportDpi = self.exportDpiBox.getValue()

        if strip:
            # return the parameters
            params = {GLFILENAME        : self.exitFilename,
                      GLSPECTRUMDISPLAY : spectrumDisplay,
                      GLSTRIP           : strip,
                      GLWIDGET          : strip._CcpnGLWidget,
                      GLPRINTTYPE       : prType,
                      GLPAGETYPE        : pageType,
                      GLFOREGROUND      : foregroundColour,
                      GLBACKGROUND      : backgroundColour,
                      GLBASETHICKNESS   : baseThickness,
                      GLSYMBOLTHICKNESS : symbolThickness,
                      GLCONTOURTHICKNESS: contourThickness,
                      GLSTRIPDIRECTION  : stripDirection,
                      GLSTRIPPADDING    : stripPadding,
                      GLEXPORTDPI       : exportDpi,
                      GLSELECTEDPIDS    : self.treeView.getSelectedObjectsPids()
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
        self.setDefaultButton(ExportDialogABC.CANCELBUTTON)

        # self.buttonFrame.addSpacer(0, 10, grid=(0, 1))
        # self.buttons = ButtonList(self.buttonFrame, ['Close', 'Save', 'Save and Close'], [self._rejectDialog, self._saveDialog, self._saveAndCloseDialog],
        #                           tipTexts=['Close the export dialog',
        #                                     'Export the strip to a file, dialog will remain open',
        #                                     'Export the strip and close the dialog'],
        #                           grid=(1, 0), gridSpan=(1, 3))

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
