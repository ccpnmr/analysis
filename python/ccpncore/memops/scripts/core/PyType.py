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
