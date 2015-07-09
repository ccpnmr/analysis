"""Test code for NmrResidue

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
from ccpn.testing.Testing import Testing

class NmrResidueTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse2c', *args, **kw)

  # def test_printchains(self):
  #   print("Residues: %s" % [x.pid for x in self.project.chains[0].residues])
  #   for ch in self.project.nmrChains:
  #     print("NmrResidues: %s: %s" % (ch.pid, [x.pid for x in ch.nmrResidues]))

  def test_reassign1(self):
    nchain = self.project.getById('NC:A')
    nr1, nr2 = nchain.nmrResidues[:2]
    res1 = nr1.residue
    res2 = nr2.residue
    res3 = self.project.chains[0].residues[2]
    print(nr1,nr2,res1,res2,res3)
    nr2.residue = None
    print (nr2, nr2.residue)
    nr2.sequenceCode = '2'
    print (nr2, nr2.residue)
    
  # def test_fetchNmrResidue(self):
  #   nmrChain = self.project.fetchNmrChain(shortName='@1')
  #   res1 = nmrChain.fetchNmrResidue(sequenceCode="127B", name="ALA")
  #   res2 = nmrChain.fetchNmrResidue(sequenceCode="127B", name="ALA")
  #   assert res1 is res2, "fetchNmrResidue takes existing NmrResidue if possible"
  #
  # def test_fetchEmptyNmrResidue(self):
  #   nmrChain = self.project.fetchNmrChain(shortName='@1')
  #   res1 = nmrChain.fetchNmrResidue(sequenceCode=None, name="ALA")
  #   sequenceCode = '@%s' % res1._wrappedData.serial
  #   assert res1.sequenceCode == sequenceCode
  #   res2 = nmrChain.fetchNmrResidue(sequenceCode=sequenceCode)
  #   assert res1 is res2, "empty NmrResidue: fetchNmrResidue takes existing NmrResidue if possible"
  #
  # def test_offsetNmrResidue(self):
  #   nmrChain = self.project.fetchNmrChain(shortName='@1')
  #   res1 = nmrChain.fetchNmrResidue(sequenceCode="127B", name="ALA")
  #   res2 = nmrChain.fetchNmrResidue(sequenceCode="127B-1", name="ALA")
  #   assert res2._wrappedData.mainResonanceGroup is res1._wrappedData
  #   res3 = nmrChain.fetchNmrResidue(sequenceCode="127B-1", name="ALA")
  #   assert res2 is res3, "fetchNmrResidue with offset takes existing NmrResidue if possible"
  #   res1.delete()
  #   assert res2._wrappedData.isDeleted, "Deleting main NmrResidue also deletes satellites"
  #
  # def test_get_by_serialName(self):
  #   nmrChain = self.project.fetchNmrChain(shortName='@1')
  #   res1 = nmrChain.fetchNmrResidue(sequenceCode=None, name="ALA")
  #   serialName = '@%s' % res1._wrappedData.serial
  #   res2 = nmrChain.fetchNmrResidue(sequenceCode=serialName)
  #   assert res1 is res2
  #   res3 = nmrChain.fetchNmrResidue(sequenceCode=serialName + '+0')
  #   assert res3._wrappedData.mainResonanceGroup is res1._wrappedData