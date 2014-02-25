# interface for transactions

class TransactionInterface(object):

  def startTransaction(self, op, inClass):

    raise NotImplementedError("Should be overwritten")

  def endTransaction(self, op, inClass):

    raise NotImplementedError("Should be overwritten")
