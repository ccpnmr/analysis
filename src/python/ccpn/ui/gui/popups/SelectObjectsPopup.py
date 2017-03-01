__author__ = 'simon1'



from PyQt4 import QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList



class SelectObjectsPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, dim=None, objects=None, **kw):
    super(SelectObjectsPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    if len(objects)>0:
      if project.getByPid(objects[0]._pluralLinkName) == 'spectra':
        objects = [spectrum.pid for spectrum in project.spectra if len(spectrum.axisCodes) >= dim]
      else:
        objects=[object.pid for object in objects]

      label1a = Label(self, text="Selected %s" % project.getByPid(objects[0])._pluralLinkName, grid=(0, 0))
      objects.insert(0, '  ')
      self.objectPulldown = PulldownList(self, grid=(1, 0), callback=self._selectObject)
      self.objectPulldown.setData(objects)
      self.objectListWidget = ListWidget(self, grid=(2, 0))

      self.buttonBox = ButtonList(self, grid=(3, 0), texts=['Cancel', 'Ok'],
                                  callbacks=[self.reject, self._setObjects])

  def _selectObject(self, item):
    self.objectListWidget.addItem(item)

  def _setObjects(self):
    self.parent.objects = [self.objectListWidget.item(i).text() for i in range(self.objectListWidget.count())]
    self.accept()
    # return [self.objectListWidget.item(i).text() for i in range(self.objectListWidget.count())]