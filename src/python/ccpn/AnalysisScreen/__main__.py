__author__ = 'TJ'

from ccpn.framework import Framework
from ccpn.AnalysisScreen.AnalysisScreen import Screen as Application

if __name__ == '__main__':

  # argument parser
  parser = Framework.defineProgramArguments()

  # add any additional commandline argument here
  commandLineArguments = parser.parse_args()

  application = Application('AnalysisScreen', 'ALPHA-1', commandLineArguments)
  Framework._getApplication = lambda: application
  application.start()

