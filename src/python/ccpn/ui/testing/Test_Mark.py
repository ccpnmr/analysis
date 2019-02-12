"""Module Documentation here

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
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting

# NBNB These two imports are NECESSARY,
# as  ccpn.ui.gui.core MUST be imported to register the Gui classes
from ccpn.ui._implementation import Mark


class MarkTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'CcpnCourse1a'

    axisCodes = ('H', 'Hn', 'C', 'C')
    positions = (4.33, 7.92, 49.65, 17.28)
    units = ('ppm', 'ppm', 'ppm', 'Hz')
    labels = ('Proton', 'NHproton', 'carbon', 'carbonhz')

    def test_create_mark(self):
        mark1 = self.project.newMark('red', positions=self.positions, axisCodes=self.axisCodes,
                                     units=self.units, labels=self.labels)
        assert mark1.positions == self.positions
        assert mark1.axisCodes == self.axisCodes
        assert mark1.units == self.units
        assert mark1.labels == self.labels

        mark1.delete()

    # GWV 20181127: not used
    # def test_extend_mark(self):
    #   data = (1.27, 'Hc', None, None)
    #   mark1 = self.project.newMark('red', positions=self.positions, axisCodes=self.axisCodes,
    #                               units=self.units, labels=self.labels)
    #   mark1.newLine(*data)
    #
    #   ll = list(zip(self.positions, self.axisCodes, self.units, self.labels))
    #   ll.append((1.27, 'Hc', 'ppm', None))
    #
    #   assert mark1.rulerData == tuple(Mark.RulerData(*x) for x in ll)
    #
    #   mark1.delete()

    # GWV 20181127: not used
    # def test_create_single_mark(self):
    #   data = (1.27, 'Hc', None, None)
    #   mark1 = self.project.newSimpleMark('red', data[0], data[1])
    #   assert  mark1.rulerData == (Mark.RulerData(1.27, 'Hc', 'ppm', None),)
