"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-22 15:13:45 +0000 (Wed, March 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui
from ccpn.ui.gui.lib.GuiListView import GuiListViewABC
from ccpn.util.OrderedSet import OrderedSet

NULL_RECT = QtCore.QRectF()
IDENTITY = QtGui.QTransform()
IDENTITY.reset()


def _getPeakAnnotationMinimal(peak):
    text = 'TEMP'
    return text


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
                    label = '.'.join((item.nmrResidue.id, item.name))
                    # label = item.nmrResidue.id + '.' + item.name
                    peakLabel.append(label)

    text = ', '.join(peakLabel)
    return text


def _getScreenPeakAnnotation(peak, useShortCode=False, useMinimalCode=False):
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

    for dimension in range(peak.peakList.spectrum.dimensionCount):

        if pdNA[dimension]:
            try:
                peakNmrResidues = [atom[0].nmrResidue.id for atom in pdNA if len(atom) != 0]

                if all(x == peakNmrResidues[0] for x in peakNmrResidues):
                    for item in pdNA[dimension]:
                        if len(peakLabel) > 0 and useShortCode:

                            if useMinimalCode:
                                continue

                            label = item.name
                        else:
                            if useMinimalCode:
                                label = shortCode(item) + item.nmrResidue.sequenceCode
                            else:
                                label = chainLabel(item) + shortCode(item) + item.nmrResidue.sequenceCode + item.name

                        peakLabel.append(label)

                else:

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

                                    if useMinimalCode:
                                        continue

                                    label = item.name
                                else:
                                    if useMinimalCode:
                                        label = shortCode(item) + item.nmrResidue.sequenceCode
                                    else:
                                        label = chainLabel(item) + shortCode(item) + item.nmrResidue.sequenceCode + item.name
                                resLabel.append(label)

                            if useMinimalCode:
                                resLabel = list(OrderedSet(resLabel))

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

    if useMinimalCode:
        peakLabel = list(OrderedSet(peakLabel))

    text = ', '.join(peakLabel)
    return text


class GuiPeakListView(GuiListViewABC):
    """peakList is the CCPN wrapper object
    """

    def __init__(self):
        super().__init__()
