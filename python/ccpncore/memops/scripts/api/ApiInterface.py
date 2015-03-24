from ccpncore.memops.metamodel import MetaModel
MemopsError = MetaModel.MemopsError

# interface for language and/or implementation specific parts of Api Generation

class ApiInterface(object):

  ###########################################################################

  ###########################################################################

  def getOverride(self, op, inClass):

    raise MemopsError("getOverride should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def checkComparableInstance(self, inClass, var, element, inCollection=None):
    """checks that value of var is compatible with element.
    Casts value if necessary, and enters cast value in original
    collection (inCollection) where appropriate.
    """
    raise MemopsError("checkComparableInstance should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeUndoCode(self, op, inClass):

    raise MemopsError("writeUndoCode should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeNotifyCode(self, op, inClass):

    raise MemopsError("writeNotifyCode should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def shouldDoNotifies(self, op, inClass):

    raise MemopsError("shouldDoNotifies should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def shouldDoUndos(self, op, inClass):

    raise MemopsError("shouldDoUndos should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def shouldDoInitChecks(self, op, inClass):

    raise MemopsError("shouldDoInitChecks should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  # writeInitConstructor is implementation dependent
  # it initialises implementation specific details at top of constructor
  def writeInitConstructor(self, op, inClass):

    raise MemopsError("writeInitConstructor should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeSetAttrLinks(self, op, inClass):

    raise MemopsError("writeSetAttrLinks should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeInitSerial(self, op, inClass):

    raise MemopsError("writeInitSerial should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeAddChildToParent(self, childVar, parentVar, parentRole, 
                            inClass=None):

    raise MemopsError("writeInitSerial should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeInitPreDelete(self, op, inClass):

    raise MemopsError("writeInitPreDelete should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeImplPreDelete(self, op, inClass, role=None):

    raise MemopsError("writeImplPreDelete should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def setCheckLinkKey(self, keyVar, objVar, role):

    raise MemopsError("setCheckLinkKey should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeImplDoDelete(self, op, inClass):

    raise MemopsError("writeImplDoDelete should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeGetParent(self, op, inClass):

    raise MemopsError("writeGetParent should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def checkFindFirst(self, op, inClass):

    raise MemopsError("checkFindFirst should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def checkFindAll(self, op, inClass):

    raise MemopsError("checkFindAll should be overridden in subclass")

  ###########################################################################

  ###########################################################################
  
  def writeGetByKey(self, op, inClass):

    raise MemopsError("writeGetByKey should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def checkChildKeysUnique(self, op, inClass, role):

    raise MemopsError("checkChildKeysUnique should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def callConstructor(self, op, inClass, params):

    raise MemopsError("callConstructor should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeSortedValue(self, op, inClass):

    raise MemopsError("writeSortedValue should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def getImplLink(self, owner, linkName, var, ownerClass, castType=None):

    raise MemopsError("getImplLink should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def setImplLink(self, owner, linkName, var, ownerClass):

    raise MemopsError("setImplLink should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def getImplAttr(self, owner, attrName, inClass=None):

    raise MemopsError("getImplAttr should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def setImplAttr(self, owner, attrName, value, inClass=None):

    raise MemopsError("setImplAttr should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeGetAttr(self, op, inClass):

    raise MemopsError("writeGetAttr should be overridden in subclass")

  ###########################################################################

  ###########################################################################

  def writeSetAttr(self, op, inClass):

    raise MemopsError("writeSetAttr should be overridden in subclass")

  ###########################################################################

