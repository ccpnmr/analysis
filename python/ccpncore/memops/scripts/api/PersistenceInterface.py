# interface for persistence

class PersistenceInterface(object):

  # elementType is used if this var is defined in this statement (needed for typed languages)
  def getValue(self, owner, element, var=None,  needVarType=True, 
              lenient=True, convertCollection=True, inClass=None):
    """ get value, loading data if necessary (normal version) 
    """
    raise 'should be overridden'

  def setValue(self, owner, element, value):

    raise 'should be overridden'

  def setSerialValue(self, owner, element, value):
    """ special setValue versin for 'serial' attribute
    """

    raise 'should be overridden'
