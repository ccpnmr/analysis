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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
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

from PyQt5 import QtCore, QtGui, QtWidgets

# import pyqtgraph as pg

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
# from ccpn.core.NmrAtom import NmrAtom
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.util.Logging import getLogger
from ccpn.core.IntegralList import IntegralList


# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import AbstractPeakDimContrib as ApiAbstractPeakDimContrib
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Resonance as ApiResonance
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import NmrChain as ApiNmrChain
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakDim as ApiPeakDim
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataDimRef as ApiDataDimRef
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import FreqDataDim as ApiFreqDataDim

NULL_RECT = QtCore.QRectF()
IDENTITY = QtGui.QTransform()
IDENTITY.reset()


# class PeakLayer(QtWidgets.QGraphicsItem):
#
#   def __init__(self, scene):
#
#     QtWidgets.QGraphicsItem.__init__(self)
#     self.scene = scene
#
#     # self.glWidget = glWidget
#     self.peaks = {}
#     self.setFlag(QtWidgets.QGraphicsItem.ItemHasNoContents, True)
#
#
#   def boundingRect(self):
#
#     return NULL_RECT
#
#   def paint(self, painter, option, widget):

# return
#
# def peakItemNotifier(project, apiPeak):
#   apiPeakListViews = apiPeak.PeakList.PeakListViews
#   for apiPeakListView in apiPeakListViews:
#     for apiStripPeakListView in apiPeakListView._apiStripPeakListViews:

def _getPeakAnnotation(peak):
    peakLabel = []
    for dimension in range(peak.peakList.spectrum.dimensionCount):
        pdNA = peak.dimensionNmrAtoms
        if len(pdNA[dimension]) == 0:
            if len(pdNA) == 1:
                peakLabel.append(peak.id)
            else:
                peakLabel.append('-')
        else:
            peakNmrResidues = [atom[0].nmrResidue.id for atom in pdNA if len(atom) != 0]
            if all(x == peakNmrResidues[0] for x in peakNmrResidues):
                for item in pdNA[dimension]:
                    if len(peakLabel) > 0:
                        peakLabel.append(item.name)
                    else:
                        peakLabel.append(item.pid.id)

            else:
                for item in pdNA[dimension]:
                    label = item.nmrResidue.id + item.name
                    peakLabel.append(label)

    text = ', '.join(peakLabel)
    return text


# def _getShortPeakAnnotation(peak):
#   for dimension in range(peak.peakList.spectrum.dimensionCount):
#     pdNA = peak.dimensionNmrAtoms
#
#     # TODO:ED add a sequence of labels that can be cycled through
#     if pdNA:
#       try:
#         return pdNA[0][0].nmrResidue.sequenceCode
#
#       except:
#         return ''

def _getScreenPeakAnnotation(peak, useShortCode=False):
    def chainLabel(item):
        try:
            chainLabel = item.nmrResidue.nmrChain.id
            assignedOnlyOneChain = len(peak.project.chains) == 1 and item.nmrResidue.residue

            if assignedOnlyOneChain or chainLabel == '@-':
                return ''
            elif chainLabel:
                chainLabel += '_'
        except:
            chainLabel = ''
        return chainLabel

    def shortCode(item):
        try:
            shortCode = item.nmrResidue.residue.shortName
        except:
            shortCode = ''
        return shortCode

    peakLabel = []
    pdNA = peak.dimensionNmrAtoms

    # # create a list for each residue
    # peakNmrDict = {}
    # for atoms in pdNA:
    #   # if len(atom) != 0:
    #   for thisAtom in atoms:
    #     thisID = thisAtom.nmrResidue.id
    #     if thisID not in peakNmrDict.keys():
    #       peakNmrDict[thisID] = [thisAtom]
    #     else:
    #       peakNmrDict[thisID].append(thisAtom)
    #
    # for pdNA in peakNmrDict.values():
    #   resLabel = []
    #   if pdNA:
    #     try:
    #       for item in pdNA:
    #         if len(resLabel) > 0 and useShortCode:
    #           label = item.name
    #         else:
    #           label = chainLabel(item) + shortCode(item) + item.nmrResidue.sequenceCode + item.name
    #         resLabel.append(label)
    #
    #     except:
    #       resLabel.append('-')
    #   else:
    #     if len(pdNA) == 1:
    #       resLabel.append('1H')
    #     else:
    #       resLabel.append('_')
    #
    #   peakLabel.append(', '.join(resLabel))
    #
    # peakLabel = '; '.join(peakLabel)
    # return peakLabel

    for dimension in range(peak.peakList.spectrum.dimensionCount):

        # TODO:ED add a sequence of labels that can be cycled through
        if pdNA[dimension]:
            try:
                peakNmrResidues = [atom[0].nmrResidue.id for atom in pdNA if len(atom) != 0]

                if all(x == peakNmrResidues[0] for x in peakNmrResidues):
                    for item in pdNA[dimension]:
                        if len(peakLabel) > 0 and useShortCode:
                            label = item.name
                        else:
                            label = chainLabel(item) + shortCode(item) + item.nmrResidue.sequenceCode + item.name
                        peakLabel.append(label)

                else:
                    # for item in pdNA[dimension]:
                    #   label = chainLabel(item) + shortCode(item) + item.nmrResidue.sequenceCode + item.name
                    #   peakLabel.append(label)

                    peakNmrDict = {}
                    for atom in pdNA[dimension]:
                        thisID = atom.nmrResidue.id
                        if thisID not in peakNmrDict.keys():
                            peakNmrDict[thisID] = [atom]
                        else:
                            peakNmrDict[thisID].append(atom)

                    resLabels = []
                    for thispdNA in peakNmrDict.values():
                        resLabel = []
                        try:
                            for item in thispdNA:
                                if len(resLabel) > 0 and useShortCode:
                                    label = item.name
                                else:
                                    label = chainLabel(item) + shortCode(
                                            item) + item.nmrResidue.sequenceCode + item.name
                                resLabel.append(label)
                        except:
                            resLabel.append('-')

                        resLabels.append(', '.join(resLabel))

                    peakLabel.append('; '.join(resLabels))

            except:
                peakLabel.append('-')
        else:
            if len(pdNA) == 1:
                peakLabel.append(peak.id)
            else:
                peakLabel.append('_')

    text = ', '.join(peakLabel)
    return text


# @profile
# def _getPeakAnnotation(peak):
#
#   peakLabel = []
#   for dimension in range(peak.peakList.spectrum.dimensionCount):
#     if len(peak.dimensionNmrAtoms[dimension]) == 0:
#       if len(peak.dimensionNmrAtoms) == 1:
#         peakLabel.append('1H')
#       else:
#         peakLabel.append('-')
#     else:
#       peakNmrResidues = [atom[0].nmrResidue.id for atom in peak.dimensionNmrAtoms if len(atom) != 0]
#       if all(x==peakNmrResidues[0] for x in peakNmrResidues):
#         for item in peak.dimensionNmrAtoms[dimension]:
#           if len(peakLabel) > 0:
#             peakLabel.append(item.name)
#           else:
#             peakLabel.append(item.pid.id)
#
#       else:
#         for item in peak.dimensionNmrAtoms[dimension]:
#           label = item.nmrResidue.id+item.name
#           peakLabel.append(label)
#
#   text = ', '.join(peakLabel)
#   return text

class GuiMultipletListView(QtWidgets.QGraphicsItem):

    def __init__(self):
        """ peakList is the CCPN wrapper object
        """
        #FIXME: apparently it gets passed an object which already has crucial attributes
        # A big NONO!!!
        strip = self.spectrumView.strip
        # scene = strip.plotWidget.scene()
        QtWidgets.QGraphicsItem.__init__(self)  # ejb - need to remove, scene=scene from here
        # self.scene = scene

        ###self.strip = strip
        ###self.peakList = peakList
        self.peakItems = {}  # CCPN peak -> Qt peakItem
        self.setFlag(QtWidgets.QGraphicsItem.ItemHasNoContents, True)
        self.application = self.spectrumView.application

        # strip.viewBox.addItem(self)
        ###self._parent = parent
        # self.displayed = True
        # self.symbolColour = None
        # self.symbolStyle = None
        # self.isSymbolDisplayed = True
        # self.textColour = None
        # self.isTextDisplayed = True
        # self.regionChanged()

        # ED - added to allow rebuilding of GLlists
        self.buildSymbols = True
        self.buildLabels = True
        # self.buildSymbols = True

        # if isinstance(self.peakList, IntegralList):
        #     self.setVisible(False)

        # attach a notifier to the peaks
        from ccpn.core.lib.Notifiers import Notifier

        Notifier(self.multipletList, ['observe'], Notifier.ANY,
                 callback=self._propagateAction,
                 onceOnly=True, debug=True)


    # def _printToFile(self, printer):
    #     # CCPN INTERNAL - called in _printToFile method of GuiSpectrumViewNd
    #
    #     # NOTE: only valid for ND so far
    #
    #     if not self.isVisible():
    #         return
    #
    #     width = printer.width
    #     height = printer.height
    #     xCount = printer.xCount
    #     yCount = printer.yCount
    #     scale = 0.01
    #     peakHalfSize = scale * max(width, height)
    #     strip = self.spectrumView.strip
    #     plotWidget = strip.plotWidget
    #     viewRegion = plotWidget.viewRange()
    #     # dataDims = self.spectrumView._wrappedData.spectrumView.orderedDataDims
    #     spectrumIndices = self.spectrumView._displayOrderSpectrumDimensionIndices
    #     xAxisIndex = spectrumIndices[0]
    #     yAxisIndex = spectrumIndices[1]
    #
    #     x1, x0 = viewRegion[0]  # TBD: relies on axes being backwards
    #     xScale = width / (x1 - x0) / xCount
    #     xTranslate = printer.x0 - x0 * xScale
    #
    #     y1, y0 = viewRegion[1]  # TBD: relies on axes being backwards
    #     yScale = height / (y1 - y0) / yCount
    #     yTranslate = printer.y0 - y0 * yScale
    #
    #     for peak in self.peakList.peaks:
    #         if strip.peakIsInPlane(peak):
    #             # xPpm = xScale*peak.position[dataDims[0].dimensionIndex] + xTranslate
    #             # yPpm = yScale*peak.position[dataDims[1].dimensionIndex] + yTranslate
    #             xPpm = xScale * peak.position[xAxisIndex] + xTranslate
    #             yPpm = yScale * peak.position[yAxisIndex] + yTranslate
    #             a0 = xPpm - peakHalfSize
    #             b0 = height - (yPpm - peakHalfSize)
    #             a1 = xPpm + peakHalfSize
    #             b1 = height - (yPpm + peakHalfSize)
    #             printer.writeLine(a0, b0, a1, b1)
    #             printer.writeLine(a0, b1, a1, b0)
    #
    #             text = _getPeakAnnotation(peak)
    #             if text:
    #                 offset = 0.5 * peakHalfSize
    #                 printer.writeText(text, a1 + offset, b1 - offset)

    def boundingRect(self):

        return NULL_RECT

    def paint(self, painter, option, widget):

        return

    # For notifiers - moved from core MultipletListView
    def _createdMultipletListView(self):
        spectrumView = self.spectrumView
        spectrum = spectrumView.spectrum
        # NBNB TBD FIXME we should get rid of this API-level access
        # But that requires refactoring the spectrumActionDict
        action = spectrumView.strip.spectrumDisplay.spectrumActionDict.get(spectrum._wrappedData)
        if action:
            action.toggled.connect(self.setVisible)  # TBD: need to undo this if multipletListView removed

        if not self.scene:  # this happens after an undo of a spectrum/multipletList deletion
            spectrumView.strip.plotWidget.scene().addItem(self)
            spectrumView.strip.viewBox.addItem(self)

        strip = spectrumView.strip
        for multipletList in spectrum.multipletLists:
            strip.showMultiplets(multipletList)

    # For notifiers - moved from core MultipletListView
    def _deletedStripMultipletListView(self):
        spectrumView = self.spectrumView
        strip = spectrumView.strip
        spectrumDisplay = strip.spectrumDisplay

        try:
            multipletItemDict = spectrumDisplay.activeMultipletItemDict[self]
            multipletItems = set(spectrumDisplay.inactiveMultipletItemDict[self])
            for apiMultiplet in multipletItemDict:
                # NBNB TBD FIXME change to get rid of API multiplets here
                multipletItem = multipletItemDict[apiMultiplet]
                multipletItems.add(multipletItem)

            # TODO:ED should really remove all references at some point
            # if strip.plotWidget:
            #   scene = strip.plotWidget.scene()
            #   for multipletItem in multipletItems:
            #     scene.removeItem(multipletItem.annotation)
            #     if spectrumDisplay.is1D:
            #       scene.removeItem(multipletItem.symbol)
            #     scene.removeItem(multipletItem)
            #   self.scene.removeItem(self)

            del spectrumDisplay.activeMultipletItemDict[self]
            del spectrumDisplay.inactiveMultipletItemDict[self]
        except Exception as es:
            getLogger().warning('Error: multipletList does not exist in spectrum')

    def _changedMultipletListView(self):

        pass
        # for multipletItem in self.multipletItems.values():
        #     if isinstance(multipletItem, MultipletNd):
        #         peakItem.update()  # ejb - force a repaint of the peakItem
        #         peakItem.annotation.setupPeakAnnotationItem(peakItem)

    def setVisible(self, visible):
        super().setVisible(visible)

        # repaint all displays - this is called for each spectrumView in the spectrumDisplay
        # all are attached to the same click
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()


# Notifiers for assignment annotation change
# Needed for:
# AbstractPeakDimContrib init and delete
# Resonance.setImplName, setResonanceGroup
# ResonanceGroup.setResonances, .setAssignedResidue, .setSequenceCode, .setResidueType
#   .setNmrChain
# NmrChain.setCode - NOT setResonanceGroups, as this calls setNmrChain on the other side.

def _refreshPeakAnnotation(peak: Peak):
    for peakListView in peak.peakList.peakListViews:
        peakItem = peakListView.peakItems.get(peak)
        if peakItem:
            peakItem.annotation.setupPeakAnnotationItem(peakItem)


Peak._refreshPeakAnnotation = _refreshPeakAnnotation


def _deletePeakAnnotation(peak: Peak):
    for peakListView in peak.peakList.peakListViews:
        peakItem = peakListView.peakItems.get(peak)
        if peakItem:
            peakItem.annotation.clearPeakAnnotationItem(peakItem)


Peak._deletePeakAnnotation = _deletePeakAnnotation


def _updateAssignmentsNmrAtom(data):  # oldPid:str):
    """Update Peak assignments when NmrAtom is reassigned"""
    nmrAtom = data['object']
    for peak in nmrAtom.assignedPeaks:
        peak._refreshPeakAnnotation()


def _deleteAssignmentsNmrAtom(data):
    """Update Peak assignments when NmrAtom is reassigned"""
    nmrAtom = data['object']

    if nmrAtom.assignedPeaks:
        project = data['theObject']

        # # TODO:ED not correct, will rename all
        # for peak in project.peaks:
        #   for peakListView in peak.peakList.peakListViews:
        #     peakItem = peakListView.peakItems.get(peak)
        #     if peakItem:
        #       peakItem.annotation.setupPeakAnnotationItem(peakItem, deleteLabel=True)


def _editAssignmentsNmrAtom(data):
    """Update Peak assignments when NmrAtom is reassigned"""
    # callback in Gui.py currently disabled
    nmrAtom = data['object']

    if nmrAtom.assignedPeaks:
        project = data['theObject']

        # TODO:ED not correct, will rename all
        for peak in project.peaks:
            for peakListView in peak.peakList.peakListViews:
                peakItem = peakListView.peakItems.get(peak)
                if peakItem:
                    peakItem.annotation.setupPeakAnnotationItem(peakItem, deleteLabel=True)

            # thisRestraintList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the restraintList
    # if self.restraintList in thisRestraintList:


# NB We could replace this with something like the following line,
# But that would trigger _refreshPeakAnnotation also when the position changes
# Better to keep it like this.
# Peak.setupCoreNotifier('change', _refreshPeakAnnotation)
def _upDateAssignmentsPeakDimContrib(project: Project,
                                     apiPeakDimContrib: Nmr.AbstractPeakDimContrib):
    peak = project._data2Obj[apiPeakDimContrib.peakDim.peak]
    peak._refreshPeakAnnotation()


def _deleteAssignmentsNmrAtomDelete(project: Project,
                                    apiPeakDimContrib: Nmr.AbstractPeakDimContrib):
    peak = project._data2Obj[apiPeakDimContrib.peakDim.peak]
    if not peak.assignedNmrAtoms:
        peak._deletePeakAnnotation()


# NB, This will be triggered whenever anything about the peak (assignment or position) changes
def _refreshPeakPosition(peak: Peak):
    if peak.isDeleted:
        return
    if peak.peakList.isDeleted:
        return
    for peakListView in peak.peakList.peakListViews:
        if peakListView.isDeleted:
            continue
        peakItem = peakListView.peakItems.get(peak)
        if peakItem:
            spectrumIndices = peakListView.spectrumView._displayOrderSpectrumDimensionIndices
            xAxisIndex = spectrumIndices[0]
            yAxisIndex = spectrumIndices[1]
            # dataDims = peakListView.spectrumView._wrappedData.spectrumView.orderedDataDims
            # xPpm = peak.position[dataDims[0].dimensionIndex]
            xPpm = peak.position[xAxisIndex]
            if peakListView.spectrumView.spectrum.dimensionCount > 1:
                # yPpm = peak.position[dataDims[1].dimensionIndex]
                yPpm = peak.position[yAxisIndex]
                peakItem.setPos(xPpm, yPpm)
            else:
                peakItem.setPos(xPpm, peak.height or 0)


Peak._refreshPeakPosition = _refreshPeakPosition
