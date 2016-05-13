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
"""  Version for python version > 2.1

Operations on the model in memory, adapting the basic model for a 
particular language and implementation. 

Includes general model querying functions the depend on context.
Includes default version of standard information, such as operations data,
variable names, etc.

Does no output.
"""

from ccpncore.memops.metamodel import ModelTraverse_py_2_1
from ccpncore.memops.metamodel.ModelPortal import ModelPortal
from ccpncore.memops.metamodel import MetaModel
MemopsError = MetaModel.MemopsError

class ModelTraverse(ModelTraverse_py_2_1.ModelTraverse_py_2_1, object):

  def __init__(self):
    """Constructor - sets up for future processing
    """

    # class needed within ObjectDomain (version 2.1)  
    super(ModelTraverse, self).__init__()
    
    for tag in ModelTraverse_py_2_1.mandatoryAttributes:
      if not hasattr(self, tag):
        raise MemopsError(" ModelTraverse lacks mandatory %s attribute" % tag)

    # has to be done this way to allow for different initialisation orders
    if not hasattr(self, 'modelFlavours'):
      self.modelFlavours = {}
    
    # input check
    if not isinstance(self.modelPortal, ModelPortal):
      raise MemopsError("ModelTraverse input %s is not a ModelPortal"
                        % self.modelPortal)
    
    # link varNames for easier access, and check modelPortal has been processed.
    if hasattr(self, 'varNames'):
      # this must have been called from ModelAdapt
      pass
    elif hasattr(self.modelPortal, 'varNames'):
      self.varNames = self.modelPortal.varNames
      self.operationData = self.modelPortal.operationData
      
    
  ###########################################################################
  
  ###########################################################################
