import os
import sys

# hack to get v2 code to work in v3
# so stick chemBuild on sys.path so old ccpnmr (etc.) imports work
### now do it in bin/chemBuild script instead
###sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

sys.setrecursionlimit(10000)

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpnmr.chemBuild.gui.ChemBuildMain import ChemBuildMain

from ccpnmr.chemBuild.Version import version

# Snap to hex grid function
# Rotate about bond

# # # # # # #   N E X T   # # # # # 
#
# Storage format - json?
# Deduce smiles string
# Searchable library?
# Huckel rule (4n+2) pi e- - set ring check and imports (PDB etc)
# Fragment icons? - small view - white bg, bigger atoms
# Align, distribute - arrangement panel?
#
# H A R D 
#
# InCHI libs
#   - default names
#   - rename atoms, handles: equiv/prochiral groups
# Auto keywords and moltype with subgraph
#   - Make ccpn classifiers

# # # # # #  F O R  L A T E R  # # # # # # 
#
# Check all ChemComps
# Alt names under different systems
# 3D display - becomes residue viewer
# Chemical shift labels
# Chem comp import double linkAtoms

# # # # # #  P O S S I B L E  # # # # # # 
# Charges into rings?
# Shadow after static?
# Modify ChemComps in-place?.
# Common redox states?
# Continuous dynamics

def _ccpnExceptionhook(type, value, tback):
  '''This because PyQT raises and catches exceptions,
  but doesn't pass them along instead makes the program crashing miserably.'''
  sys.__excepthook__(type, value, tback)

sys.excepthook = _ccpnExceptionhook


if __name__ == '__main__':

  import sys, os

  sys.path.append(os.getcwd())

  qtApp = QtWidgets.QApplication(['CcpNmr ChemBuild'])
  
  QtWidgets.QApplication.setStartDragDistance(4)
  QtWidgets.QApplication.setStartDragTime(400)
  QtCore.QCoreApplication.setOrganizationName("CCPN")
  QtCore.QCoreApplication.setOrganizationDomain("ccpn.ac.uk")
  QtCore.QCoreApplication.setApplicationName("ChemBuild")
  QtCore.QCoreApplication.setApplicationVersion(version)

  if len(sys.argv) > 1:
    fileName = sys.argv[1]
  else:
    fileName = None

  chemBuild = ChemBuildMain(None, fileName)
  chemBuild.show()
  
  # sys.exit(qtApp.exec_())
  os._exit(qtApp.exec_())
  
