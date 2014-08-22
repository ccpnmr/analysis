import os
import sys

from ccpn import openProject

from ccpncore.gui.Application import Application

from ccpnmrcore.gui.MainWindow import MainWindow

applicationName = 'Assign'
applicationVersion = '1.0'

def usage():

  print('Correct syntax: %s [projectPath]' % sys.argv[0])

if __name__ == '__main__':
  if len(sys.argv) == 2:
    projectPath = sys.argv[1]
    project = openProject(projectPath)
  elif len(sys.argv) != 1:
    usage()
    sys.exit(1)
  else:
    project = None

  app = Application(applicationName, applicationVersion)
  window = MainWindow(project)
  window.raise_()
  app.start()

