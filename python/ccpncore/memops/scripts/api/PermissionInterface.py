# interface for permissions

class PermissionInterface(object):

  def checkPermission(self, op, inClass):

    raise 'should be overridden'
