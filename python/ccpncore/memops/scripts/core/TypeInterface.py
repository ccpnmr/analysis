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

