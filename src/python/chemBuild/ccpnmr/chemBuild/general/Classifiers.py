import os
from os.path import join

from ccpnmr.chemBuild.model.Compound import loadCompoundPickle 

def getCcpnMolTypeFragments(classifierDir='./classifiers/ccpn/'):
  searchOrder = {'protein':1,
                 'RNA':2,
                 'DNA':3,
                 'carbohydrate':4 }

  fileNames = os.listdir(classifierDir)
  filePaths = [join(classifierDir, fn) for fn in fileNames if fn.endswith('.pickle')]
  fragments = [loadCompoundPickle(fp) for fp in filePaths]
  sortList = [(searchOrder[f.ccpMolType], f) for f in fragments]
  sortList.sort()
  
  return [x[1] for x in sortList] 

if __name__ == '__main__':
  ccpnMolTypeFragments = getCcpnMolTypeFragments()
