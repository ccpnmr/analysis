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
__dateModified__ = "$dateModified: 2017-07-07 16:32:33 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib.AssignmentLib import getNmrAtomPrediction, CCP_CODES
from ccpn.core.testing.WrapperTesting import WrapperTesting


class Test_getNmrAtomPrediction(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def setUp(self):

        with self.initialSetup():
            self.ThrCBShift = 70
            self.AlaCBShift = 19
            self.CACBShift = 44
            self.CAShift = 60
            self.CBShift = 35

    def test_nmrAtomPrediction(self):
        predictedAtomThrCB = [getNmrAtomPrediction(ccpCode, self.ThrCBShift, '13C', strict=True) for ccpCode in CCP_CODES]
        refinedPreds = [[type[0][0][1], type[0][1]] for type in predictedAtomThrCB if len(type) > 0]
        thrCBatomPredictions = set()

        for pred in refinedPreds:
            if pred[1] > 90:
                thrCBatomPredictions.add(pred[0])
        predictedAtomAlaCB = [getNmrAtomPrediction(ccpCode, self.AlaCBShift, '13C', strict=True) for ccpCode in CCP_CODES]
        refinedPreds = [[type[0][0][1], type[0][1]] for type in predictedAtomAlaCB if len(type) > 0]
        alaCBatomPredictions = set()
        for pred in refinedPreds:
            if pred[1] > 90:
                alaCBatomPredictions.add(pred[0])
        predictedAtomCACB = [getNmrAtomPrediction(ccpCode, self.CACBShift, '13C', strict=True) for ccpCode in CCP_CODES]
        refinedPreds = [[type[0][0][1], type[0][1]] for type in predictedAtomCACB if len(type) > 0]
        CACBatomPredictions = set()
        for pred in refinedPreds:
            if pred[1] > 90:
                CACBatomPredictions.add(pred[0])
        predictedAtomCAShift = [getNmrAtomPrediction(ccpCode, self.CAShift, '13C', strict=True) for ccpCode in CCP_CODES]
        refinedPreds = [[type[0][0][1], type[0][1]] for type in predictedAtomCAShift if len(type) > 0]
        CAatomPredictions = set()
        for pred in refinedPreds:
            if pred[1] > 90:
                CAatomPredictions.add(pred[0])

        predictedAtomCBShift = [getNmrAtomPrediction(ccpCode, self.CBShift, '13C', strict=True) for ccpCode in CCP_CODES]
        refinedPreds = [[type[0][0][1], type[0][1]] for type in predictedAtomCBShift if len(type) > 0]
        # print(refinedPreds)
        CBatomPredictions = set()
        for pred in refinedPreds:
            if pred[1] > 90:
                CBatomPredictions.add(pred[0])
        #
        # # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()

        self.assertIn('CB', list(thrCBatomPredictions))
        self.assertIn('CA', list(thrCBatomPredictions))
        self.assertIn('CB', list(alaCBatomPredictions))
        self.assertNotIn('CA', list(alaCBatomPredictions))
        self.assertNotIn('CA', list(alaCBatomPredictions))
        self.assertIn('CA', list(CACBatomPredictions))
        self.assertIn('CB', list(CACBatomPredictions))
        self.assertIn('CA', list(CAatomPredictions))
        self.assertNotIn('CB', list(CAatomPredictions))
        self.assertIn('CB', list(CBatomPredictions))
        self.assertNotIn('CA', list(CBatomPredictions))
