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
