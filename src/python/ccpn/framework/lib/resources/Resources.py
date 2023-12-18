"""
A module to handle resources loaded from disk as JSON files.
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-09-06 14:28:31 +0100 (Wed, September 06, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-08-30 15:14:00 +0100 (Wed, August 30, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.resources.ReferenceChemicalShifts import ReferenceChemicalShifts
from ccpn.util.isotopes import IsotopeRecords

class Resources():

    def __init__(self, application):
        super().__init__()
        self.application = application
        self._referenceChemicalShifts = ReferenceChemicalShifts()

    @property
    def referenceChemicalShifts(self):
        return self._referenceChemicalShifts

    @property
    def referenceMolecules(self):
        return ''

    @property
    def isotopeRecords(self):
        return IsotopeRecords()

    @property
    def referenceExperimentTypes(self):
        return ''

    # ------ Private Methods ---------

    def _initProjectResources(self):
        """ Init the Resources that defined by users only at a Project level.
        This operation can be done only at run-time"""
        self.referenceChemicalShifts._initProjectReferenceChemicalShifts()


    def _deregisterProjectResources(self):
        """ Remove/unload the resources when closing/switching projects"""
        self.referenceChemicalShifts._deregisterProjectReferenceChemicalShifts()
