import bmrb
import json

if __name__ == '__main__':
  #entry = bmrb.entry.fromFile('/home/rhf22/rhf22/Git/NEF/specification/Commented_Example.nef')
  #entry = bmrb.entry.fromFile('/home/rhf22/rhf22/Git/NEF/data/original/CCPN_CASD155.nef')
  entry = bmrb.entry.fromFile('/home/rhf22/rhf22/Git/NEF/data/original/CCPN_H1GI.nef')
  entry.printTree()
