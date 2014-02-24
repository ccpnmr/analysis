"""interface for language specific parts of File Api
"""

from memops.metamodel import MetaModel
MemopsError = MetaModel.MemopsError

class FileApiInterface(object):

  ###########################################################################

  ###########################################################################

  def getImplLink(self, owner, linkName, var, ownerClass):
    """ Get implementation link value
    """

    raise MemopsError("getImplLink should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def setImplLink(self, owner, linkName, value, ownerClass):
    """ Set implementation link value
    """

    raise MemopsError("setImplLink should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def getImplAttr(self, owner, attrName, inClass = None):
    """ Get implementation attr value
    """

    raise MemopsError("getImplAttr should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def setImplAttr(self, owner, attrName, value, inClass = None):
    """ Set implementation attr value
    """

    raise MemopsError("setImplAttr should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def getMemoryValue(self, owner, element):
    """ Return raw attr/link value currently in memory
    """

    raise MemopsError("getMemoryValue should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeClassVars(self, complexDataType):
    """ Write class variables (for languages / implementations where needed)
    """

    raise MemopsError("writeClassVars should be overridden in subclass")

  ###########################################################################

  ###########################################################################
