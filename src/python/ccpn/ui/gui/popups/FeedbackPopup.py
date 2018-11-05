"""Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets


Qt = QtCore.Qt

import os
import random

from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil

from ccpn.framework.PathsAndUrls import ccpn2Url

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.TextEditor import TextEditor

from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpn.util import Logging
from ccpn.util import Register
from ccpn.util import Url
from ccpn.ui.gui.popups.Dialog import CcpnDialog


LOG_FILE_TEXT = 'Log file'
PROJECT_DIR_TEXT = 'Project directory'

SCRIPT_URL = ccpn2Url + '/cgi-bin/feedback/submitFeedback.py'


# code below has to be synchronised with code in SCRIPT_URL

class FeedbackPopup(CcpnDialog):
    # parent mandatory and that needs to have attribute application
    def __init__(self, parent=None, title='Feedback Form', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.setContentsMargins(5, 5, 5, 5)
        self._registrationDict = Register.loadDict()

        # frame = Frame(self, setLayout=True)   # ejb - change frame to self below, strange

        row = 0
        message = 'For bug reports please submit precise information, including any error message left on the console'
        label = Label(self, message, grid=(row, 0), gridSpan=(1, 2))

        for key in ('name', 'organisation', 'email'):
            row += 1
            label = Label(self, text='%s: ' % metaUtil.upperFirst(key), grid=(row, 0))
            label = Label(self, text=self._registrationDict.get(key), grid=(row, 1))

        row += 1
        label = Label(self, text='Include: ', grid=(row, 0))
        includeFrame = Frame(self, grid=(row, 1), setLayout=True)
        self.includeLogBox = CheckBox(includeFrame, text=LOG_FILE_TEXT, checked=True, grid=(0, 0))
        self.includeProjectBox = CheckBox(includeFrame, text=PROJECT_DIR_TEXT, checked=False, grid=(0, 1))

        row += 1
        label = Label(self, text='Feedback: ', grid=(row, 0))
        self.textEditor = TextEditor(self, grid=(row, 1))

        row += 1
        button = Button(self, 'Submit', callback=self._submitFeedback, grid=(row, 1))
        self.setMaximumSize(self.maximumWidth(), self.maximumHeight())

    def _submitFeedback(self):
        includeLog = self.includeLogBox.get()
        includeProject = self.includeProjectBox.get()
        feedback = self.textEditor.get().strip()

        if not feedback:
            return

        application = self.parent().application

        if includeProject:
            # cannot use tempfile because that always hands back open object and tarfile needs actual path
            filePrefix = 'feedback%s' % random.randint(1, 10000000)
            project = application.project
            projectPath = project.path
            directory = os.path.dirname(projectPath)
            filePrefix = os.path.join(directory, filePrefix)
            fileName = apiIo.packageProject(project._wrappedData.parent, filePrefix, includeBackups=True, includeLogs=includeLog)
        elif includeLog:
            logger = Logging.getLogger()
            if not hasattr(logger, 'logPath'):
                return
            fileName = logger.logPath
        else:
            fileName = None

        data = {}
        data['version'] = application.applicationVersion
        data['feedback'] = feedback

        for key in ('name', 'organisation', 'email'):
            data[key] = self._registrationDict.get(key, 'None')

        if fileName:
            try:
                response = Url.uploadFile(SCRIPT_URL, fileName, data)
            finally:
                if includeProject:
                    os.remove(fileName)
        else:
            try:
                response = Url.fetchUrl(SCRIPT_URL, data)
            except:
                response = []

        if 'Data successfully uploaded' in response:
            title = 'Success'
            msg = 'Feedback successfully submitted'
        else:
            title = 'Failure'
            msg = 'Problem submitting feedback'

        info = MessageDialog.showInfo(title, msg)

        #print(response)
        self.hide()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication


    app = TestApplication()
    popup = FeedbackPopup()

    popup.show()
    popup.raise_()

    app.start()
