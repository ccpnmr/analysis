"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:49 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets


Qt = QtCore.Qt

from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil
from functools import partial
import re

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Entry import Entry
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.MessageDialog import showError
from ccpn.framework.PathsAndUrls import ccpnUrl
###from ccpn.ui.gui.widgets.WebView import WebViewPanel
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util import Register


licenseUrl = ccpnUrl + '/license'
validEmailRegex = re.compile(r'^[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-_]+\.)+[A-Za-z]{2,63}$')


# class RegisterPopup(QtWidgets.QDialog):
class RegisterPopup(CcpnDialog):
    def __init__(self, parent=None, trial:int=0,  version='3', title='Register with CCPN', modal=False, **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.version = version
        self.trial = trial

        if modal:  # Set before visible
            modality = QtCore.Qt.ApplicationModal
            self.setWindowModality(modality)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 350)

        frame = Frame(self, setLayout=True, grid=(0, 0))

        message = '''To keep track of our users, which is important for grant applications,
we would like you to register your contact details with us.
This needs to be done once on every computer you use the programme on.
'''
        label = Label(frame, message, grid=(0, 0), gridSpan=(1, 2))

        row = 1
        self.entries = []
        self.validateEntries = []
        registrationDict = Register.loadDict()
        for attr in Register.userAttributes:
            label = Label(frame, metaUtil.upperFirst(attr), grid=(row, 0))
            text = registrationDict.get(attr, '')
            entry = Entry(frame, text=text, grid=(row, 1), maxLength=60)
            self.entries.append(entry)

            if 'email' in attr:
                currentBaseColour = entry.palette().color(QtGui.QPalette.Base)
                entry.textChanged.connect(partial(self._checkEmailValid, entry, currentBaseColour))
                self.validateEntries.append(entry)
            row += 1

        from ccpn.util import Data
        label = Label(frame, 'Build For:', grid=(row, 0))
        text = getattr(Data, ''.join([c for c in map(chr, (98, 117, 105, 108, 100, 70, 111, 114))]), '')
        entry = Entry(frame, text=text, grid=(row, 1), maxLength=60)
        entry.setEnabled(False)
        row += 1

        licenseFrame = Frame(frame, setLayout=True, grid=(row, 0), gridSpan=(1, 2))
        row += 1

        self.licenseCheckBox = CheckBox(licenseFrame,
                                        text='I have read and agree to the terms and conditions of the licence',
                                        callback=self._toggledCheckBox, grid=(0, 0))
        self.licenseCheckBox.setChecked(False)
        button = Button(licenseFrame, text='Show Licence', callback=self._showLicense, grid=(0, 1))

        buttonFrame = Frame(frame, setLayout=True, grid=(row, 0), gridSpan=(1, 2))
        ##self.licenseButton = Button(buttonFrame, 'Show License', callback=self.toggleLicense, grid=(0,0))
        txt = 'Later (%s day(s) left)' % self.trial
        self.laterButton = Button(buttonFrame, txt, callback=self.reject, grid=(0,0))
        self.registerButton = Button(buttonFrame, 'Register', callback=self._register, grid=(0, 1))
        self.registerButton.setEnabled(False)
        self.laterButton.setEnabled(False)
        row += 1

        ##self.licensePanel = WebViewPanel(frame, url=licenseUrl, grid=(row,0), gridSpan=(1,2))
        ##self.licensePanel.hide()
        #self.resize(300,200)

    def _checkEmailValid(self, entryBox, baseColour):
        palette = entryBox.palette()

        regIn = entryBox.text()
        validEmail = True if validEmailRegex.match(regIn) else False
        if validEmail:
            palette.setColor(QtGui.QPalette.Base, baseColour)
        else:
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor('lightpink'))

        entryBox.setPalette(palette)

    def _toggledCheckBox(self):
        self.registerButton.setEnabled(self.licenseCheckBox.isChecked())
        self.laterButton.setEnabled(False if self.trial < 1 else self.licenseCheckBox.isChecked())

    def _showLicense(self):
        self.getParent().application.showLicense()

    # def _toggleLicense(self):
    #
    #   if self.licensePanel.isVisible():
    #     self.licensePanel.hide()
    #     self.resize(300,200)
    #     self.licenseButton.setText('Show License')
    #   else:
    #     self.licensePanel.show()
    #     self.resize(700,700)
    #     self.licenseButton.setText('Hide License')


    def _register(self):

        allValid = all([True if validEmailRegex.match(entry.text()) else False for entry in self.validateEntries])

        if allValid:
            from ccpn.framework.PathsAndUrls import licensePath
            from ccpn.util.Update import calcHashCode, TERMSANDCONDITIONS

            registrationDict = {}
            for n, attr in enumerate(Register.userAttributes):
                entry = self.entries[n]
                registrationDict[attr] = entry.get() or ''

            currentHashCode = calcHashCode(licensePath)
            registrationDict[TERMSANDCONDITIONS] = currentHashCode

            Register.setHashCode(registrationDict)
            Register.saveDict(registrationDict)
            Register.updateServer(registrationDict, self.version)

            if self.isModal():
                self.close()
        else:
            showWarning('', 'Please check all entries are valid')


class NewTermsConditionsPopup(RegisterPopup):
    def __init__(self, parent=None, trial:int=0,  version='3', title='Agree to Terms and Conditions', modal=False, **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.version = version
        self.trial = trial

        if modal:  # Set before visible
            modality = QtCore.Qt.ApplicationModal
            self.setWindowModality(modality)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 350)

        frame = Frame(self, setLayout=True, grid=(0, 0))

        message = '''The terms and conditions of the licence have been amended.
Please read and accept to continue using the software.
'''
        label = Label(frame, message, grid=(0, 0), gridSpan=(1, 2))

        row = 1
        self.entries = []
        self.validateEntries = []
        registrationDict = Register.loadDict()
        for attr in Register.userAttributes:
            label = Label(frame, metaUtil.upperFirst(attr), grid=(row, 0))
            text = registrationDict.get(attr, '')
            entry = Entry(frame, text=text, grid=(row, 1), maxLength=60)
            self.entries.append(entry)

            if 'email' in attr:
                currentBaseColour = entry.palette().color(QtGui.QPalette.Base)
                entry.textChanged.connect(partial(self._checkEmailValid, entry, currentBaseColour))
                self.validateEntries.append(entry)
            row += 1
            entry.setEnabled(False)

        from ccpn.util import Data
        label = Label(frame, 'Build For:', grid=(row, 0))
        text = getattr(Data, ''.join([c for c in map(chr, (98, 117, 105, 108, 100, 70, 111, 114))]), '')
        entry = Entry(frame, text=text, grid=(row, 1), maxLength=60)
        entry.setEnabled(False)
        row += 1

        licenseFrame = Frame(frame, setLayout=True, grid=(row, 0), gridSpan=(1, 2))
        row += 1

        self.licenseCheckBox = CheckBox(licenseFrame,
                                        text='I have read and agree to the terms and conditions of the licence',
                                        callback=self._toggledCheckBox, grid=(0, 0))
        self.licenseCheckBox.setChecked(False)
        button = Button(licenseFrame, text='Show Licence', callback=self._showLicense, grid=(0, 1))

        buttonFrame = Frame(frame, setLayout=True, grid=(row, 0), gridSpan=(1, 2))
        ##self.licenseButton = Button(buttonFrame, 'Show License', callback=self.toggleLicense, grid=(0,0))
        txt = 'Later (%s day(s) left)'%self.trial
        self.laterButton = Button(buttonFrame, txt, callback=self.reject, grid=(0,0))
        self.registerButton = Button(buttonFrame, 'Accept Amendments', callback=self._register, grid=(0, 1))
        self.registerButton.setEnabled(False)
        self.laterButton.setEnabled(False)
        row += 1

    def _toggledCheckBox(self):
        self.registerButton.setEnabled(self.licenseCheckBox.isChecked())

    def _register(self):

        allValid = all([True if validEmailRegex.match(entry.text()) else False for entry in self.validateEntries])

        if allValid:
            from ccpn.framework.PathsAndUrls import licensePath
            from ccpn.util.Update import calcHashCode, TERMSANDCONDITIONS

            regDict = Register.loadDict()

            # write the updated md5
            currentHashCode = calcHashCode(licensePath)
            regDict[TERMSANDCONDITIONS] = currentHashCode
            Register.saveDict(regDict)

            if self.isModal():
                self.close()
        else:
            showWarning('', 'Please check all entries are valid')


if __name__ == '__main__':
    import sys
    import os

    qtApp = QtWidgets.QApplication(['Test Register'])

    #QtCore.QCoreApplication.setApplicationName('TestRegister')
    #QtCore.QCoreApplication.setApplicationVersion('0.1')

    popup = RegisterPopup()
    popup.show()
    popup.raise_()

    os._exit(qtApp.exec_())
