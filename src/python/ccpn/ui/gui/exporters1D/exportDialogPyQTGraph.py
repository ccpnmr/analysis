"""
Reimplementation of PyQtGraph
"""

from PyQt5 import QtCore, QtGui, QtWidgets

try:
    _fromUtf8 = str
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class UiForm(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(241, 367)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)
        self.itemTree = QtWidgets.QTreeWidget(Form)
        self.itemTree.setObjectName(_fromUtf8("itemTree"))
        self.itemTree.headerItem().setText(0, _fromUtf8("1"))
        self.itemTree.header().setVisible(False)
        self.gridLayout.addWidget(self.itemTree, 1, 0, 1, 3)
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 3)
        self.formatList = QtWidgets.QListWidget(Form)
        self.formatList.setObjectName(_fromUtf8("formatList"))
        self.gridLayout.addWidget(self.formatList, 3, 0, 1, 3)
        self.exportBtn = QtWidgets.QPushButton(Form)
        self.exportBtn.setObjectName(_fromUtf8("exportBtn"))
        self.gridLayout.addWidget(self.exportBtn, 6, 1, 1, 1)
        self.closeBtn = QtWidgets.QPushButton(Form)
        self.closeBtn.setObjectName(_fromUtf8("closeBtn"))
        self.gridLayout.addWidget(self.closeBtn, 6, 2, 1, 1)
        self.paramTree = ParameterTree(Form)
        self.paramTree.setObjectName(_fromUtf8("paramTree"))
        self.paramTree.headerItem().setText(0, _fromUtf8("1"))
        self.paramTree.header().setVisible(False)
        self.gridLayout.addWidget(self.paramTree, 5, 0, 1, 3)
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 3)
        self.copyBtn = QtWidgets.QPushButton(Form)
        self.copyBtn.setObjectName(_fromUtf8("copyBtn"))
        self.gridLayout.addWidget(self.copyBtn, 6, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Export", None))
        self.label.setText(_translate("Form", "Item to export:", None))
        self.label_2.setText(_translate("Form", "Export format", None))
        self.exportBtn.setText(_translate("Form", "Export", None))
        self.closeBtn.setText(_translate("Form", "Close", None))
        self.label_3.setText(_translate("Form", "Export options", None))
        self.copyBtn.setText(_translate("Form", "Copy", None))

from pyqtgraph.parametertree import ParameterTree
