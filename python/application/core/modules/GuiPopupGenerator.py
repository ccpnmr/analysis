__author__ = 'simon1'

import json
import os
from functools import partial

from application.core.widgets.Base import Base
from application.core.widgets.Button import Button
from application.core.widgets.Label import Label
from application.core.widgets.LineEdit import LineEdit
from application.core.widgets.PulldownList import PulldownList
import json
from PyQt4 import QtGui


WIDGET_TYPES = ['Button', 'CheckBox', 'DoubleSpinbox', 'LineEdit', 'ListWidget',
                'PulldownList', 'Spinbox', 'None']

class PopupGenerator(QtGui.QDialog, Base):

  def __init__(self, parent=None, **kw):

    super(PopupGenerator, self).__init__(parent)
    Base.__init__(self, **kw)

    self.popupNameLabel = Label(self, text='Popup Name', grid=(0, 0))
    self.popupNameBox = LineEdit(self, grid=(0, 1))

    self.label1 = Label(self, grid=(1, 0), text="Widget Label")
    self.label1 = Label(self, grid=(1, 1), text='Widget Type')
    self.label1 = Label(self, grid=(1, 2), text="Widget Text/Data/Function")
    self.label1 = Label(self, grid=(1, 3), text="Widget Label")
    self.label1 = Label(self, grid=(1, 4), text="Widget Type")
    self.label1 = Label(self, grid=(1, 5), text="Widget Type/Data/Function")

    self.lineEdit_0 = LineEdit(self, grid=(2, 0))
    self.pullDownList_1 = PulldownList(self, grid=(2, 1))
    self.pullDownList_1.setData(WIDGET_TYPES)
    self.lineEdit_1 = LineEdit(self, grid=(2, 2))
    self.label2 = LineEdit(self, grid=(2, 3))
    self.pullDownList_2 = PulldownList(self, grid=(2, 4))
    self.pullDownList_2.setData(WIDGET_TYPES)
    self.lineEdit_2 = LineEdit(self, grid=(2, 5))
    self.addButton_1 = Button(self, '+', grid=(2, 6), callback=self.addWidgetLine)
    self.removeButton_1 = Button(self, '-', grid=(2, 7), callback=partial(self.removeWidgetLine, 1))
    self.i = 3
    self.rowCount = 1
    self.saveToJsonButton = Button(self, "Save To Json", grid=(20, 5), callback=self.saveToJson)
    self.renderPopup = Button(self, "Create Popup", grid=(20, 7), callback=self.renderPopup)
    self.cancelButton = Button(self, "Cancel", grid=(20, 6), callback=self.reject)

  def addWidgetLine(self):
    # self.addButton_1.deleteLater()
    self.lineEdit_1 = LineEdit(self, grid=(self.i, 0))
    self.pullDownList_1 = PulldownList(self, grid=(self.i, 1))
    self.pullDownList_1.setData(WIDGET_TYPES)
    self.lineEdit_2 = LineEdit(self, grid=(self.i, 2))
    self.lineEdit_3 = LineEdit(self, grid=(self.i, 3))
    self.pullDownList_2 = PulldownList(self, grid=(self.i, 4))
    self.pullDownList_2.setData(WIDGET_TYPES)
    self.lineEdit_2 = LineEdit(self, grid=(self.i, 5))
    self.addButton_1 = Button(self, '+', grid=(self.i, 6), callback=self.addWidgetLine)
    self.removeButton_1 = Button(self, '-', grid=(self.i, 7), callback=partial(self.removeWidgetLine, self.i))
    self.rowCount +=1

    self.i+=1

  def removeWidgetLine(self, row):
    if self.rowCount > 1:
      for i in range(6):
        item = self.layout().itemAtPosition(row, i)
        item.widget().deleteLater()
      self.rowCount-=1
    else:
      print("Cannot remove widget line")

  def saveToJson(self):

    jsonData = []

    for j in range(self.rowCount):
      i = j+2
      widgetDict = {'Label_1': [self.layout().itemAtPosition(i, 0).widget().text(), 'grid=(%d, 0)' % i, str(i)+'a'],
                   'widget_1': [self.layout().itemAtPosition(i, 1).widget().currentText(),  'grid=(%d, 1)' % i, str(i)+'a', self.layout().itemAtPosition(i, 2).widget().text()],
                   'Label_2': [self.layout().itemAtPosition(i, 3).widget().text(), 'grid=(%d, 2)' % i, str(i)+ 'b'],
                   'widget_2': [self.layout().itemAtPosition(i, 4).widget().currentText(),  'grid=(%d, 3)' % i, str(i) + 'b', self.layout().itemAtPosition(i, 5).widget().text()]}
      jsonData.append(widgetDict)
      print(jsonData)

    dumpFileName =  os.path.expanduser('~simon1/.ccpn/') +self.lineEdit_0.text()+'.json'
    dumpFile = open(dumpFileName, 'w+')
    dump = json.dump(jsonData, dumpFile, indent=4, separators=(',', ': '))
    dumpFile.close()
    return dumpFileName


  def createPopupFromJson(self, jsonFile):
    jsonData = open(jsonFile)
    widgets = json.load(jsonData)
    pythonFilePath = os.path.expanduser('~simon1/.ccpn/') + '%s.py' % self.popupNameBox.text()
    pythonFile = open(pythonFilePath, 'w')
    pythonFile.write('from PyQt4 import QtGui\n')
    pythonFile.write('from application.core.widgets.Base import Base\n')
    pythonFile.write('from application.core.widgets.Button import Button\n')
    pythonFile.write('from application.core.widgets.CheckBox import CheckBox\n')
    pythonFile.write('from application.core.widgets.ColourDialog import ColourDialog\n')
    pythonFile.write('from application.core.widgets.DoubleSpinbox import DoubleSpinbox\n')
    pythonFile.write('from application.core.widgets.Label import Label\n')
    pythonFile.write('from application.core.widgets.LineEdit import LineEdit\n')
    pythonFile.write('from application.core.widgets.ListWidget import ListWidget\n')
    pythonFile.write('from application.core.widgets.PulldownList import PulldownList\n')
    pythonFile.write('from application.core.widgets.Spinbox import Spinbox\n\n\n')
    pythonFile.write('class %s(QtGui.QDialog, Base):\n  def __init__(self, parent=None, **kw):\n' % self.popupNameBox.text())
    pythonFile.write('    super(%s, self).__init__(parent)\n' % self.popupNameBox.text())
    pythonFile.write('    Base.__init__(self, **kw)\n\n')

    for item in widgets:
      pythonFile.write('    label%s = Label(self, text="%s", %s)\n' % (item['Label_1'][2].lower(), item['Label_1'][0], item['Label_1'][1]))
      if item['widget_1'][0] == 'Button':
        # pythonFile.write('    %s%s = %s(self, %s, text=%s, callback=None)\n' % (item['widget_1'][0].lower(), item['widget_1'][2],item['widget_1'][0],item['widget_1'][1], item['widget_1'][3]))
        # pythonFile.write('    # to connect function to Button, set callback equal to function\n')
        pythonFile.write(self.writeButtonLines(item['widget_1']))
      elif item['widget_1'][0] == 'CheckBox':
        pythonFile.write('    %s%s = %s(self, %s, checked=True)\n' % (item['widget_1'][0].lower(), item['widget_1'][2],item['widget_1'][0],item['widget_1'][1]))
        pythonFile.write('    # when checkbox is checked or unchecked, function will be performed\n')
        pythonFile.write('    %s%s.stateChanged.connect(%s)' % (item['widget_1'][0].lower(), item['widget_1'][2], item['widget_1'][3]))
      pythonFile.write('    label%s = Label(self, text="%s", %s)\n' % (item['Label_2'][2], item['Label_2'][0], item['Label_2'][1]))
      pythonFile.write('    %s%s = %s(self, %s)\n' % (item['widget_2'][0].lower(), item['widget_2'][2],item['widget_2'][0],item['widget_2'][1]))

    pythonFile.close()

    return pythonFilePath





    pythonFile.close()

  def renderPopup(self):
    jsonFile = self.saveToJson()
    pythonFile = self.createPopupFromJson(jsonFile)
    # from shutil import copyfile
    # print('pyFile',pythonFile)
    # copyfile(pythonFile, '/Users/simon1/PycharmProjects/CCPN_V3/trunk/ccpnv3/python/application.core/modules/%s.py' % self.popupNameBox.text() )
    # package = 'application.core.modules.'+self.popupNameBox.text()
    # print(package)
    # popupImport = getattr(__import__(package), self.popupNameBox.text())
    #
    # newPopup = popupImport(self)
    # newPopup.exec_()


  def writeButtonLines(self, widget):
    str = '    %s%s = %s(self, %s, text=%s, callback=None)\n' % (
      widget[0].lower(), widget[2],widget[0],widget[1], widget[3]) + \
          '    # to connect function to Button, set callback equal to function\n'
    return str





