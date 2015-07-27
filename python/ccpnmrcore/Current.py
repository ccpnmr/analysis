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
from ccpncore.gui import MessageDialog
from ccpn import Project
from ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak

_fields = ['project','spectrum','spectra','peak','peaks','region','position', 'strip', 'assigner']

class Current:

  def __init__(self):
    for field in _fields:
      setattr(self,field,None)

    # Special case - plural attributes must be initialised to list
    self.peaks = []

  def deleteSelected(self, parent=None):
    # TBD: more general deletion
    if self.peaks:
      n = len(self.peaks)
      title = 'Delete Peak%s' % ('' if n == 1 else 's')
      msg ='Delete %sselected peak%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
      if MessageDialog.showYesNo(title, msg, parent):
        for peak in self.peaks[:]:
          peak.delete()
        #self.peaks = [] # not needed since _deletedPeak notifier will clear this out
      
def _cleanupCurrentPeak(project, apiPeak):
    
  current = project._appBase.current
  if current:
    peak = project._data2Obj[apiPeak]
    if peak is current.peak:
      current.peak = None
    if peak in current.peaks:
      current.peaks.remove(peak)

Project._cleanupCurrentPeak = _cleanupCurrentPeak
# Register notifier for registering/unregistering
Project._apiNotifiers.append(('_cleanupCurrentPeak', {},
                              ApiPeak._metaclass.qualifiedName(), 'preDelete'))
Project._apiNotifiers.append(('_cleanupCurrentPeak', {},
                              ApiPeak._metaclass.qualifiedName(), 'preDelete'))