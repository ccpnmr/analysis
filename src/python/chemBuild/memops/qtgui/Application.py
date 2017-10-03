from PyQt5 import QtGui, QtWidgets

import sys

class Application(QtWidgets.QApplication):

  def __init__(self, argv=None):

    if not argv:
      argv = []

    QtWidgets.QApplication.__init__(self, argv)

  def start(self):

    sys.exit(self.exec_())

if __name__ == '__main__':

  app = Application()
  # normally have next line but nothing will stop this here except to kill job
  #app.start()
