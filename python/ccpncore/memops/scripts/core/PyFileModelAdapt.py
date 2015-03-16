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
""" Python-specific version of ModelAdapt
"""

from ccpncore.memops.scripts.core.PyModelAdapt import PyModelAdapt
from ccpncore.memops.scripts.core.FileModelAdapt import FileModelAdapt


def processModel(modelPortal, **kw):
  """process model to adapt it for Python
  
  Only function that should be called directly by 'make' scripts etc.
  """
  pyFileModelAdapt = PyFileModelAdapt(modelPortal=modelPortal, **kw)
  pyFileModelAdapt.processModel()


class PyFileModelAdapt(PyModelAdapt, FileModelAdapt):
  """ Python-specific version of ModelAdapt
  """
  def __init__(self, **kw):
    """Class constructor.
    Automatically processes model.
    """
    
    for (tag, val) in kw.items():
      if not hasattr(self, tag):
        setattr(self, tag, val)
    
    # superclass init call
    super(PyFileModelAdapt, self).__init__()
