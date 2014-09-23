import os
from ccpncore.util import ApiFunc

thisDirectory = os.path.dirname(__file__)
for subDirectory in ('memops', 'ccp',):
  directory = os.path.join(thisDirectory, subDirectory)
  ApiFunc.addDirectoryFunctionsToApi(directory, rootDirectory=thisDirectory)
