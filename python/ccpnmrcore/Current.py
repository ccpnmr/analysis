"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

from ccpncore.memops import Notifiers

_fields = ['project','spectrum','spectra','peak','peaks','region','position', 'strip', 'assigner']

class Current:

  def __init__(self):
    for field in _fields:
      setattr(self,field,None)

    Notifiers.registerNotify(self.deletedPeak, 'ccp.nmr.Nmr.Peak', 'delete')
    
  def deletedPeak(self, apiPeak):
    
    peak = self.project._data2Obj[apiPeak]
    if peak in self.peaks:
      self.peaks.remove(peak)