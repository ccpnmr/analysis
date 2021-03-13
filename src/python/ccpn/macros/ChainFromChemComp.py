"""
This macro opens a popup for creating a chain from a ChemComp saved as xml file.
A new chain containing only one residue corresponding to the small molecule and its atoms.
Atoms are named as defined in the ChemComp file.
Residue name is set from the chemComp ccpCode.
Note. Also a substance will be added in the project.

ChemComps are available from
    - https://github.com/VuisterLab/CcpNmr-ChemComps/tree/master/data/pdbe/chemComp/archive/ChemComp
    or
    - build your own using ChemBuild:
        - open chembuild
        - new compound
        - export CCPN ChemComp XML File

Run the macro and select the Xml file.

Alpha released in Version 3.0.3
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-03-13 15:32:10 +0000 (Sat, March 13, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-03-05 11:01:32 +0000 (Fri, March 05, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.Chain import _fetchChemCompFromFile, _newChainFromChemComp
from ccpn.ui.gui.widgets.FileDialog import ChemCompFileDialog
from ccpn.util.Logging import getLogger

dial = ChemCompFileDialog(mainWindow, acceptMode='select')
dial._show()
filePath = dial.selectedFile()

if filePath:
    chemComp = _fetchChemCompFromFile(project, filePath)
    chain = _newChainFromChemComp(project, chemComp, chainCode='LIG', includePseudoAtoms=False)
    getLogger().info("New Chain available from SideBar")
else:
    getLogger().warning('No selected file. Chain from ChemComp Aborted')
