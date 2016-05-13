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
from ccpncore.memops.scripts.core.TypeInterface import TypeInterface

repositoryTag = '$Name: not supported by cvs2svn $'
repositoryId  = '$Id: PyType.py,v 1.13 2007-12-11 16:47:30 wb104 Exp $'

class PyType(TypeInterface):

  ###########################################################################
  
  ###########################################################################

  # implements TypeInterface
  def elementVarType(self, element):

    return ''

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def collectionType(self, elementOrString=None, isUnique=None, isOrdered=None,
                     useCollection=False):

    return ''

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def implementationType(self, element):

    return ''

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def interfaceType(self, element):

    return ''

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def dictInterfaceType(self, keyType = None, valueType = None):

    return ''

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def listInterfaceType(self, listType = None):

    return ''

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def collectionInterfaceType(self, collectionType = None):

    return ''

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def stackInterfaceType(self, stackType = None):

    return ''

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def fileInterfaceType(self, mode = 'r'):

    return ''
