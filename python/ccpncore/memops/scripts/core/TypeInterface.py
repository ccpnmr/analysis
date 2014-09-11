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
# interface for language types

class TypeInterface(object):

  ###########################################################################

  ###########################################################################
  #
  # Functions which must be implemented in subclasses
  #
  ###########################################################################

  ###########################################################################

  # Functions return real language-specific types

  def elementVarType(self, element):

    raise NotImplementedError("Should be overwritten")

  ###########################################################################

  ###########################################################################

  def collectionType(self, elementOrString=None, isUnique=None, isOrdered=None,
                     useCollection=False):

    raise NotImplementedError("Should be overwritten")

  ###########################################################################

  ###########################################################################

  def implementationType(self, element):

    raise NotImplementedError("Should be overwritten")

  ###########################################################################

  ###########################################################################

  def interfaceType(self, element):

    raise NotImplementedError("Should be overwritten")

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def dictInterfaceType(self, keyType = None, valueType = None):

    raise NotImplementedError("Should be overwritten")

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def listInterfaceType(self, listType = None):

    raise NotImplementedError("Should be overwritten")

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def collectionInterfaceType(self, collectionType = None):

    raise NotImplementedError("Should be overwritten")

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def stackInterfaceType(self, stackType = None):

    raise NotImplementedError("Should be overwritten")

  ###########################################################################

  ###########################################################################

  # implements TypeInterface
  def fileInterfaceType(self, mode = 'r'):

    raise NotImplementedError("Should be overwritten")

