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
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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

NULL_RECT = QtCore.QRectF()
IDENTITY = QtGui.QTransform()
IDENTITY.reset()


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

    for dimension in range(peak.peakList.spectrum.dimensionCount):

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
                                    label = chainLabel(item) + shortCode(item) + item.nmrResidue.sequenceCode + item.name
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


class GuiPeakListView(GuiListViewABC):
    """peakList is the CCPN wrapper object
    """

    def __init__(self):
        super().__init__()
