#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-07-28 16:36:55 +0100 (Fri, July 28, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import ccpn.core
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label


class MyModule(CcpnModule):
    """
    This is example of CCPN module Usage. See below how to run it alone for graphical testing purposes.
    """
    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'top'

    className = 'MyModule'

    def __init__(self, mainWindow, name):
        super().__init__(mainWindow=mainWindow, name=name)

        # mainWidget
        self.aLabel = Label(parent=self.mainWidget, text='Testing my module', grid=(0, 0))

        # settingsWidget
        self.testingLabel = Label(parent=self.settingsWidget, text='Testing my settings space', grid=(0, 0), hAlign='c')


'''
To test a ccpn Module graphic :
Copy and past this script at the botton of the CcpnModule file you want to run. 

>> change CcpnModule with the Module to test  
>> module = YourModule(mainWindow=None)
'''

def main():
    from PyQt5 import QtGui, QtWidgets
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    from ccpn.ui.gui.widgets.CheckBox import EditableCheckBox, CheckBox


    app = TestApplication()
    win = QtWidgets.QMainWindow()

    moduleArea = CcpnModuleArea(mainWindow=None)

    module = MyModule(mainWindow=None, name='My Module')
    module.cb = cb = CheckBox(module.settingsWidget, text='HELLO', checked=False, grid=(0, 0), objectName='CHECKCHECK')

    state = module.widgetsState
    cb.setChecked(True)
    module.restoreWidgetsState(**state)

    moduleArea.addModule(module)

    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.setWindowTitle('Testing %s' % module.moduleName)
    win.show()

    app.start()
    win.close()


if __name__ == '__main__':
    main()
