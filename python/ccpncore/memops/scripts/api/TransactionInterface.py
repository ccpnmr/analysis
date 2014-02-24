# interface for transactions

class TransactionInterface(object):

  def startTransaction(self, op, inClass):

    raise 'should be overridden'

  def endTransaction(self, op, inClass):

    raise 'should be overridden'
