"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-02-02 13:23:41 +0000 (Thu, February 02, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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
from collections import OrderedDict

from ccpn.core.Project import Project
from ccpn.ui._implementation.PeakListView import PeakListView as _CoreClassPeakListView


NULL_RECT = QtCore.QRectF()
IDENTITY = QtGui.QTransform()
IDENTITY.reset()


class GuiPeakListView(GuiListViewABC):
    """peakList is the CCPN wrapper object
    """

    def __init__(self):
        super().__init__()


class PeakListView(_CoreClassPeakListView, GuiPeakListView):
    """Peak List View for 1D or nD PeakList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripPeakListView'):
        """Local override init for Qt subclass"""
        _CoreClassPeakListView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        GuiPeakListView.__init__(self)
        self._init()

#=========================================================================================
# Registering
#=========================================================================================

def _factoryFunction(project: Project, wrappedData):
    """create PeakListView
    """
    return PeakListView(project, wrappedData)

# _CoreClassPeakListView._registerCoreClass(factoryFunction=_factoryFunction)

#=========================================================================================

#GWV: moved to core.lib.peakUtils

# def _getPeakId(peak):
#     """Get the current id for the peak
#     """
#     return peak.id
#
# def _getPeakAnnotation(peak):
#     """Get the current annotation for the peak
#     """
#     return peak.annotation
#
# def _getPeakClusterId(peak):
#     """Get the current clusterId for the peak
#     """
#     v = peak.clusterId
#     return str(v) if v else None
#
# def _getPeakLabelling(peak):
#     """Create the labelling for Pids method
#     """
#     peakLabel = []
#
#     for dimension in range(peak.peakList.spectrum.dimensionCount):
#         pdNA = peak.dimensionNmrAtoms
#
#         pdNADim = [atom for atom in pdNA[dimension] if not atom.isDeleted]
#
#         if not pdNADim:  # len(pdNA[dimension]) == 0:
#             if len(pdNA) == 1:
#                 peakLabel.append(peak.id)
#             else:
#                 peakLabel.append('-')
#         else:
#             peakNmrResidues = [atom[0].nmrResidue.id for atom in pdNA if len(atom) != 0 and not atom[0].isDeleted]
#             if all(x == peakNmrResidues[0] for x in peakNmrResidues):
#
#                 for item in pdNADim:  # pdNA[dimension]:
#                     if len(peakLabel) > 0:
#                         peakLabel.append(item.name)
#                     else:
#                         peakLabel.append(item.pid.id)
#
#             else:
#                 pdNADim = [atom for atom in pdNA[dimension] if not atom.isDeleted]
#                 for item in pdNADim:  # pdNA[dimension]:
#                     label = '.'.join((item.nmrResidue.id, item.name))
#                     # label = item.nmrResidue.id + '.' + item.name
#                     peakLabel.append(label)
#
#     text = ', '.join(peakLabel)
#     return text
#
#
# def _getScreenPeakAnnotation(peak, useShortCode=False, useMinimalCode=False, usePid=False):
#     """Create labelling for short, long, minimal
#     """
#
#     def chainLabel(item):
#         try:
#             chainLabel = item.nmrResidue.nmrChain.id
#             assignedOnlyOneChain = len(peak.project.chains) == 1 and item.nmrResidue.residue
#
#             if assignedOnlyOneChain or chainLabel == '@-':
#                 return ''
#             elif chainLabel:
#                 chainLabel += '_'
#         except:
#             chainLabel = ''
#         return chainLabel
#
#     def shortCode(item):
#         try:
#             shortCode = item.nmrResidue.residue.shortName
#         except:
#             shortCode = ''
#         return shortCode
#
#     peakLabel = []
#     pdNA = peak.dimensionNmrAtoms
#     numDims = peak.peakList.spectrum.dimensionCount
#
#     # list all the unique nmrResidues in the peakList
#
#     # ids = [OrderedDict((atom.nmrResidue.id, []) for atom in pdNAs) for pdNAs in pdNA]
#     ids = OrderedDict((atom.nmrResidue.id, []) for pdNAs in pdNA for atom in pdNAs)
#
#     for dimension in range(peak.peakList.spectrum.dimensionCount):
#         pdNADim = [atom for atom in pdNA[dimension] if not atom.isDeleted]
#
#         for atom in pdNADim:
#             nmrRes = ids[atom.nmrResidue.id]
#
#             if nmrRes and (useShortCode or usePid):
#
#                 if useMinimalCode:
#                     continue
#
#                 label = atom.name
#             else:
#                 if useMinimalCode:
#                     label = shortCode(atom) + atom.nmrResidue.sequenceCode
#                 elif usePid:
#                     label = '.'.join((atom.nmrResidue.id, atom.name))
#                 else:
#                     label = chainLabel(atom) + shortCode(atom) + atom.nmrResidue.sequenceCode + atom.name
#
#             nmrRes.append(label)
#
#     text = '; '.join(', '.join(atoms) for atoms in ids.values())
#     return text if text else ','.join(['_'] * numDims)

