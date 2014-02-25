# interface for permissions

class PermissionInterface(object):

  def checkPermission(self, op, inClass):

    raise NotImplementedError("Should be overwritten")
