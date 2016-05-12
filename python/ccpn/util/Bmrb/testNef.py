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
from ccpn.util.Bmrb import bmrb

if __name__ == '__main__':
  #entry = bmrb.entry.fromFile('/home/rhf22/rhf22/Git/NEF/specification/Commented_Example.nef')
  #entry = bmrb.entry.fromFile('/home/rhf22/rhf22/Git/NEF/data/original/CCPN_CASD155.nef')

  import sys
  if len(sys.argv) > 1:
    path = sys.argv[1]
  else:
    path = '/home/rhf22/rhf22/Git/NEF/data/original/CCPN_H1GI.nef'
  entry = bmrb.entry.fromFile(path)
  # entry.printTree()
  print(entry)