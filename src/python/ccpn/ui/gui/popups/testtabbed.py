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
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb


class TabDialog(CcpnDialog):
    def __init__(self, fileName, parent=None, title='Tab Dialog', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        fileInfo = QtCore.QFileInfo(fileName)

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(GeneralTab(fileInfo), "General")
        tabWidget.addTab(PermissionsTab(fileInfo), "Permissions")
        tabWidget.addTab(ApplicationsTab(fileInfo), "Applications")

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Tab Dialog")


class GeneralTab(QtWidgets.QWidget):
    def __init__(self, fileInfo, parent=None):
        super(GeneralTab, self).__init__(parent)

        fileNameLabel = QtWidgets.QLabel("File Name:")
        fileNameEdit = QtWidgets.QLineEdit(fileInfo.fileName())

        pathLabel = QtWidgets.QLabel("Path:")
        pathValueLabel = QtWidgets.QLabel(fileInfo.absoluteFilePath())
        pathValueLabel.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)

        sizeLabel = QtWidgets.QLabel("Size:")
        size = fileInfo.size() // 1024
        sizeValueLabel = QtWidgets.QLabel("%d K" % size)
        sizeValueLabel.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)

        lastReadLabel = QtWidgets.QLabel("Last Read:")
        lastReadValueLabel = QtWidgets.QLabel(fileInfo.lastRead().toString())
        lastReadValueLabel.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)

        lastModLabel = QtWidgets.QLabel("Last Modified:")
        lastModValueLabel = QtWidgets.QLabel(fileInfo.lastModified().toString())
        lastModValueLabel.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(fileNameLabel)
        mainLayout.addWidget(fileNameEdit)
        mainLayout.addWidget(pathLabel)
        mainLayout.addWidget(pathValueLabel)
        mainLayout.addWidget(sizeLabel)
        mainLayout.addWidget(sizeValueLabel)
        mainLayout.addWidget(lastReadLabel)
        mainLayout.addWidget(lastReadValueLabel)
        mainLayout.addWidget(lastModLabel)
        mainLayout.addWidget(lastModValueLabel)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)


class PermissionsTab(QtWidgets.QWidget):
    def __init__(self, fileInfo, parent=None):
        super(PermissionsTab, self).__init__(parent)

        permissionsGroup = QtWidgets.QGroupBox("Permissions")

        readable = QtWidgets.QCheckBox("Readable")
        if fileInfo.isReadable():
            readable.setChecked(True)

        writable = QtWidgets.QCheckBox("Writable")
        if fileInfo.isWritable():
            writable.setChecked(True)

        executable = QtWidgets.QCheckBox("Executable")
        if fileInfo.isExecutable():
            executable.setChecked(True)

        ownerGroup = QtWidgets.QGroupBox("Ownership")

        ownerLabel = QtWidgets.QLabel("Owner")
        ownerValueLabel = QtWidgets.QLabel(fileInfo.owner())
        ownerValueLabel.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)

        groupLabel = QtWidgets.QLabel("Group")
        groupValueLabel = QtWidgets.QLabel(fileInfo.group())
        groupValueLabel.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)

        permissionsLayout = QtWidgets.QVBoxLayout()
        permissionsLayout.addWidget(readable)
        permissionsLayout.addWidget(writable)
        permissionsLayout.addWidget(executable)
        permissionsGroup.setLayout(permissionsLayout)

        ownerLayout = QtWidgets.QVBoxLayout()
        ownerLayout.addWidget(ownerLabel)
        ownerLayout.addWidget(ownerValueLabel)
        ownerLayout.addWidget(groupLabel)
        ownerLayout.addWidget(groupValueLabel)
        ownerGroup.setLayout(ownerLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(permissionsGroup)
        mainLayout.addWidget(ownerGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)


class ApplicationsTab(QtWidgets.QWidget):
    def __init__(self, fileInfo, parent=None):
        super(ApplicationsTab, self).__init__(parent)

        topLabel = QtWidgets.QLabel("Open with:")

        applicationsListBox = QtWidgets.QListWidget()
        applications = []

        for i in range(1, 31):
            applications.append("Application %d" % i)

        applicationsListBox.insertItems(0, applications)

        alwaysCheckBox = QtWidgets.QCheckBox()

        if fileInfo.suffix():
            alwaysCheckBox = QtWidgets.QCheckBox("Always use this application to "
                    "open files with the extension '%s'" % fileInfo.suffix())
        else:
            alwaysCheckBox = QtWidgets.QCheckBox("Always use this application to "
                    "open this type of file")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(topLabel)
        layout.addWidget(applicationsListBox)
        layout.addWidget(alwaysCheckBox)
        self.setLayout(layout)


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)

    if len(sys.argv) >= 2:
        fileName = sys.argv[1]
    else:
        fileName = "."

    tabdialog = TabDialog(fileName)
    sys.exit(tabdialog.exec_())
