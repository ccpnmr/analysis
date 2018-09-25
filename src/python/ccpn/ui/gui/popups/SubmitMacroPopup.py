"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets


Qt = QtCore.Qt

import os
import urllib

from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil

from ccpn.framework.PathsAndUrls import ccpn2Url

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Entry import Entry
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb

from ccpn.util import Register
from ccpn.util import Url


SCRIPT_URL = ccpn2Url + '/cgi-bin/macros/submitMacro.py'


# code below has to be synchronised with code in SCRIPT_URL

class SubmitMacroPopup(CcpnDialog):
    def __init__(self, parent=None, title='Submit Macro Form', **kw):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

        self.setContentsMargins(5, 5, 5, 5)
        self._registrationDict = Register.loadDict()

        # frame = Frame(self, setLayout=True)     # ejb

        row = 0
        for key in ('name', 'organisation', 'email'):
            label = Label(self, text='%s: ' % metaUtil.upperFirst(key), grid=(row, 0))
            label = Label(self, text=self._registrationDict.get(key), grid=(row, 1))
            row += 1

        button = Button(self, 'Macro path:', callback=self._selectMacro, grid=(row, 0))
        self.pathEntry = Entry(self, maxLength=200, grid=(row, 1))
        row += 1

        label = Label(self, text='Keywords: ', grid=(row, 0))
        self.keywordsEntry = Entry(self, grid=(row, 1))
        row += 1

        label = Label(self, text='Description: ', grid=(row, 0))
        self.textEditor = TextEditor(self, grid=(row, 1))
        row += 1

        button = Button(self, 'Submit', callback=self._submitMacro, grid=(row, 1))

        self.setMinimumSize(400, 400)

    def _selectMacro(self):

        dialog = FileDialog(parent=self.parent(), fileMode=FileDialog.ExistingFile, text='Select Macro',
                            preferences=self.parent().application.preferences.general)
        path = dialog.selectedFile()
        if path:
            self.pathEntry.set(path)

    def _submitMacro(self):

        application = self.parent().application
        logger = application.project._logger

        filePath = self.pathEntry.get()
        if not filePath or not os.path.exists(filePath) or not os.path.isfile(filePath):
            dialog = MessageDialog.showError('Error',
                                             'Path does not exist or is not file')
            logger.error('Path specified for macro does not exist or is not file: %s' % filePath)
            return

        keywords = self.keywordsEntry.get()
        description = self.textEditor.get()

        if not keywords or not description:
            dialog = MessageDialog.showError('Error',
                                             'Both keywords and description required')
            logger.error('Both keywords and description required for macro')
            return

        keywords = keywords.strip()
        description = description.strip()

        data = {}
        data['version'] = application.applicationVersion
        data['keywords'] = keywords
        data['description'] = description

        for key in ('name', 'organisation', 'email'):
            data[key] = self._registrationDict.get(key, 'None')

        try:
            response = Url.uploadFile(SCRIPT_URL, filePath, data)
        except urllib.error.HTTPError as e:
            response = str(e)

        if response and 'Macro successfully uploaded' in response:
            title = 'Success'
            msg = loggerMsg = 'Macro successfully submitted'
        else:
            title = 'Failure'
            msg = 'Problem submitting macro, see log for details'
            loggerMsg = 'Problem submitting macro: %s' % response

        logger.info(loggerMsg)
        info = MessageDialog.showInfo(title, msg)

        self.hide()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication


    app = TestApplication()
    popup = SubmitMacroPopup()

    popup.show()
    popup.raise_()

    app.start()
