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
__dateModified__ = "$dateModified: 2017-07-07 16:33:00 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
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
