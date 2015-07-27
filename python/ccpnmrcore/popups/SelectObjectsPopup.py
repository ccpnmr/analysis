__author__ = 'simon1'



from PyQt4 import QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label
from ccpncore.gui.ListWidget import ListWidget
from ccpncore.gui.PulldownList import PulldownList



class SelectObjectsPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, dim=None, objects=None, **kw):
    super(SelectObjectsPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    if project.getById(objects[0]._pluralLinkName) == 'spectra':
      objects = [spectrum.pid for spectrum in project.spectra if len(spectrum.axisCodes) >= dim]
    else:
      objects=[object.pid for object in objects]

    label1a = Label(self, text="Selected %s" % project.getById(objects[0])._pluralLinkName, grid=(0, 0))
    objects.insert(0, '  ')
    self.objectPulldown = PulldownList(self, grid=(1, 0), callback=self.selectObject)
    self.objectPulldown.setData(objects)
    self.objectListWidget = ListWidget(self, grid=(2, 0))

    self.buttonBox = ButtonList(self, grid=(3, 0), texts=['Cancel', 'Ok'],
                           callbacks=[self.reject, self.setObjects])

  def selectObject(self, item):
    self.objectListWidget.addItem(item)

  def setObjects(self):
    self.parent.objects = [self.objectListWidget.item(i).text() for i in range(self.objectListWidget.count())]
    self.accept()
    # return [self.objectListWidget.item(i).text() for i in range(self.objectListWidget.count())]