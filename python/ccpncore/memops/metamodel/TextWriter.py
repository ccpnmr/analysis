"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
""" Version for Python version > 2.1
"""

from ccpncore.memops.metamodel import MetaModel
MemopsError = MetaModel.MemopsError
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.util import Path

from ccpncore.memops.metamodel import TextWriter_py_2_1

settings = TextWriter_py_2_1.settings

class TextWriter(TextWriter_py_2_1.TextWriter_py_2_1, object):
  """
  """

  def __init__(self):
    """ parameters are mandatoryInitParams, optionalInitParams
    and the special optional
    """   
    
    for tag in TextWriter_py_2_1.mandatoryAttributes:
      if not hasattr(self, tag):
        raise MemopsError(" TextWriter lacks mandatory %s attribute" % tag)
    
    super(TextWriter, self).__init__()
      
    # special parameters: optional with default values
    if self.rootFileName is None:
      self.rootFileName = metaConstants.rootPackageDirName
      
    if self.rootDirName is None:
      self.rootDirName = Path.getTopDirectory()
      

    self.fp = None
    self.fileName = ''
    self.indent = 0
    self.indents = []
    self.errorMsg = ''

    self.previousLineEmpty = False # used so that do not print out two '\n' in a row
    
  ###########################################################################

  ###########################################################################
