
"""
Alpha version of a popup for setting up a structure calculation using Xplor-NIH calculations.
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
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown, ChemicalShiftListPulldown, ChainPulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
import os
import datetime
from distutils.dir_util import copy_tree
from ccpn.ui.gui.widgets.FileDialog import OtherFileDialog
from ccpn.framework.Application import getApplication

application = getApplication()
if application:
    # Path for Xplor NIH executable. Those calculations are
    # Local Mac:
    #xplorPath='/Users/eliza/Projects/xplor-nih-3.2/bin/xplor'
    xplorPath = application.preferences.externalPrograms.get('xplor')

    # This is an example folder from Xplor NIH distribution with scripts necessary for running calculations
    pathToXplorFiles = '/Users/eliza/Projects/xplor-nih-3.2/eginput/pasd/nef'

    # Path for TalosN executable (depending where the calculation is run).
    #talosnPath='/home/eapa2/applications/talos-n/talosn'
    talosnPath=application.preferences.externalPrograms.get('talos')


def setupDirForXplorRun(project, path, name, peakLists, chemShiftList):
    dir = os.path.join(path, name+'_'+str(datetime.date.today()))

    if os.path.isdir(dir) == False:
        os.mkdir(dir)

    # generate a list of the necessary nef pids needed for xplor
    pidList = []
    for item in project.chains:
        pidList.append(item.pid)

    for item in project.chemicalShiftLists:
        if item.pid in chemShiftList:
            pidList.append(item.pid)


    for item in project.peakLists:
        if item.pid in peakLists:
            pidList.append(item.pid)

    project.exportNef(path=os.path.join(dir, name+'.nef'), overwriteExisting=True,
                      skipPrefixes=['ccpn'], expandSelection=False,
                      pidList=pidList)

    # copy xplor run files into the working directory
    copy_tree(pathToXplorFiles, dir)

    return dir, pidList


def writeXplorReadme( projectName, projectSpectra, dir, xplorRunName):

    with open(os.path.join(dir, 'README'), 'r') as file:
        # read a list of lines into data
        readmeFile = file.readlines()

    talosn = "alias talosn='" + talosnPath + "'\n"
    xplor = "alias xplor='" + xplorPath + "'\n"

    # and write everything back
    with open(os.path.join(dir, xplorRunName), 'w') as file:
        for i, line in enumerate(readmeFile):
            if i == 1:
                file.write(talosn)
                file.write(xplor)
            if "name=CCPN_H1GI_clean" in line:
                line = line.replace('CCPN_H1GI_clean', projectName)
            if 'CNOESY-173`3` 3dNOESY-182`3`' in line:
                line = line.replace('CNOESY-173`3` 3dNOESY-182`3`', projectSpectra)
            file.write(line)

    file.close()
    return


def editTalosSH(pathDir):

    with open(os.path.join(pathDir, 'runTalos.sh'), 'r') as file:
        data = file.read()
        file.close()

    data = data.replace('TALOSN=talosn',"TALOSN="+talosnPath)

    with open(os.path.join(pathDir, 'runTalos.sh'), 'w') as file:
        file.write(data)
        file.close()

def xplorRunDirectorySetUp(project, pathToXplorRunDirectory, peakLists, chemShiftList):
    name = project.name
    dir, pidList = setupDirForXplorRun(project, pathToXplorRunDirectory, name, peakLists, chemShiftList)

    spectra = ''
    for i, p in enumerate(peakLists):
        if i>0: spectra = spectra + ' '
        p = p.replace('PL:','')
        p = p.split('.')
        spectra = spectra + p[0]+'`'+p[1]+'`'
    #print(spectra)
    xplorRunName = 'runxplor_'+name+'_'+str(datetime.date.today())+'.sh'
    writeXplorReadme(projectName=name,
                     projectSpectra=spectra,
                     dir=dir, xplorRunName=xplorRunName)
    editTalosSH(dir)

    os.system('chmod 777 '+os.path.join(dir, xplorRunName))
    print('Setup complete in directory: ', dir)
    print('To run Xplor NIH got to the folder and execute in terminal: \n./'+xplorRunName)

    return dir

# print('Paths for Xplor NIH and TalosN executables loaded.\nTo prepare Xplor NIH run directory type in Python Console with updated names (EXAMPLE): \nxplorRunDirectorySetUp(pathToXplorRunDirectory = \'/Users/user1/Documents/xplorNIH/protein1\', peakLists=[\'PL:N-NOESY.1\',\'PL:C-NOESY.1\'], chemShiftList=[\'CL:list1\'])')


class SetupXplorStructureCalculationPopup(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    title = 'Setup Xplor-NIH Structure Calculation (Alpha)'
    def __init__(self, parent=None, mainWindow=None, title=title,  **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title,
                         size=(500, 10), minimumSize=None, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project

        else:
            self.mainWindow = None
            self.application = None
            self.current = None
            self.project = None

        self._createWidgets()

        # enable the buttons
        self.tipText = ''
        self.setOkButton(callback=self._okCallback, tipText =self.tipText, text='Setup', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)

    def _createWidgets(self):

        row = 0
        self.pathLabel = Label(self.mainWidget, text="Xplor Run Directory", grid=(row, 0))
        self.pathData = PathEdit(self.mainWidget, grid=(row, 1), vAlign='t', )
        self.pathDataButton = Button(self.mainWidget, grid=(row, 2), callback=self._getPathFromDialog,
                                           icon='icons/directory', hPolicy='fixed')
        row += 1
        self.plsLabel = Label(self.mainWidget, text='Select PeakLists', grid=(row, 0),  vAlign='l')
        self.plsWidget = ListWidgetPair(self.mainWidget, grid=(row, 1), gridSpan=(1,3), hAlign='l')

        row += 1
        self.cslWidget = ChemicalShiftListPulldown(parent=self.mainWidget,
                                         mainWindow=self.mainWindow,
                                         grid=(row, 0), gridSpan=(1,3),
                                         showSelectName=True,
                                         minimumWidths=(0, 100),
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=None)
        row += 1
        self.mcWidget = ChainPulldown(parent=self.mainWidget,
                                         mainWindow=self.mainWindow,
                                         grid=(row, 0), gridSpan=(1,3),
                                         showSelectName=True,
                                         minimumWidths=(0, 100),
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=None)

        self._populateWsFromProjectInfo()

    def _populateWsFromProjectInfo(self):
        if self.project:
            self.cslWidget.selectFirstItem()
            self.mcWidget.selectFirstItem()
            self.plsWidget._populate(self.plsWidget.rightList, self.project.peakLists)

    def _getPathFromDialog(self):
        dialog = OtherFileDialog(parent=self.mainWindow, _useDirectoryOnly=True,)
        dialog._show()
        path = dialog.selectedFile()
        if path:
            self.pathData.setText(str(path))

    def _okCallback(self):
        if self.project:
            csl = self.cslWidget.getSelectedObject()
            chain = self.mcWidget.getSelectedObject()
            plsPids = self.plsWidget.rightList.getTexts()
            pathRun = self.pathData.get()
            if not csl:
                MessageDialog.showWarning('', 'Select a ChemicalShift List')
                return
            if not chain:
                MessageDialog.showWarning('', 'Select a ChemicalShift List')
                return
            if not plsPids:
                MessageDialog.showWarning('', 'Include at list a PeakList')
                return
            # run the calculation
            print('Running with peakLists: %s, chain: %s, CSL: %s. Run Dir: %s' %(plsPids, chain.pid, csl.pid, pathRun))
            xplorRunDirectorySetUp(self.project,
                                   pathToXplorRunDirectory = pathRun,
                                   peakLists = plsPids,
                                   chemShiftList = csl.pid)
        self.accept()

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    # app = TestApplication()
    popup = SetupXplorStructureCalculationPopup(mainWindow=mainWindow)
    popup.show()
    popup.raise_()
    # app.start()

