"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting

class ChainTest(WrapperTesting):

  # Path of project to load (None for new project
  projectPath = None
    
  def test_rename_chain(self):

    chain = self.project.createChain('ACDC', shortName='A', molType='protein' )
    nmrChain = self.project.newNmrChain(shortName='A')
    undo = self.project._undo
    undo.newWaypoint()
    chain.rename('B')
    self.assertEqual(chain.shortName, 'B')
    self.assertEqual(nmrChain.shortName, 'B')
    undo.undo()
    self.assertEqual(chain.shortName, 'A')
    self.assertEqual(nmrChain.shortName, 'A')
    undo.redo()
    self.assertEqual(chain.shortName, 'B')
    self.assertEqual(nmrChain.shortName, 'B')
