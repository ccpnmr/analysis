"""Module Documentation here

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

from ccpn.core.testing.WrapperTesting import WrapperTesting

class ChemicalShiftTest(WrapperTesting):

  # Path of project to load (None for new project
  projectPath = 'CcpnCourse2b'
    
  def test_rename_list(self):

    self.project._wrappedData.root.checkAllValid(complete=True)

    shiftList = self.project.chemicalShiftLists[0]

    self.assertEqual(shiftList.pid,'CL:ShiftList_2')
    self.assertEqual(sorted(shiftList.chemicalShifts)[5].pid,'CS:ShiftList_2.A.3.GLU.CA')
    shiftList.rename('RenamedList')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(shiftList.pid,'CL:RenamedList')
    self.assertEqual(sorted(shiftList.chemicalShifts)[5].pid,'CS:RenamedList.A.3.GLU.CA')
