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
from application.core.widgets.Base import Base as CoreBase

class Base(CoreBase):
  
  def __init__(self, appBase, *args, **kw):
    
    self._appBase = appBase
    
    CoreBase.__init__(self, *args, **kw)
    
  def getByPid(self, pid):
  
    return self._appBase.project.getByPid(pid)

  def getObject(self, pidOrObject):
  
    return self.getByPid(pidOrObject) if isinstance(pidOrObject, str) else pidOrObject
  
  # Already defined in AbstractWrapperObject - duplicate not needed
  # def getWrapperObject(self, apiObject):
  #
  #  return self._appBase.project._data2Obj[apiObject]
