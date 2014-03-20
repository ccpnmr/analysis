from PySide import QtGui

import sys

class Application(QtGui.QApplication):

  def __init__(self, applicationName, applicationVersion, organizationName='CCPN', organizationDomain='ccpn.ac.uk'):

    QtGui.QApplication.__init__(self, (applicationName,))

    self.setApplicationVersion(applicationVersion)
    self.setOrganizationName(organizationName)
    self.setOrganizationDomain(organizationDomain)

  def start(self):

    sys.exit(self.exec_())

class TestApplication(Application):
  
  def __init__(self):

    Application.__init__(self, 'testApplication', '1.0')
    
if __name__ == '__main__':

  app = TestApplication()
  app.start()
