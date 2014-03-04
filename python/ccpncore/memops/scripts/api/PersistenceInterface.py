# interface for persistence

class PersistenceInterface(object):

  # elementType is used if this var is defined in this statement (needed for typed languages)
  def getValue(self, owner, element, var=None,  needVarType=True, 
              lenient=True, convertCollection=True, inClass=None, castType=None):
    """ get value, loading data if necessary (normal version) 
    """
    raise NotImplementedError("Should be overwritten")

  def setValue(self, owner, element, value):

    raise NotImplementedError("Should be overwritten")

  def setSerialValue(self, owner, value):
    """ special setValue version for 'serial' attribute
    """

    raise NotImplementedError("Should be overwritten")

  def setIdValue(self, owner, value):
    """ special setValue version for '_ID' attribute
    """

    raise NotImplementedError("Should be overwritten")
