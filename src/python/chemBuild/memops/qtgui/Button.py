from PyQt5 import QtCore, QtGui, QtWidgets

from .Base import Base, Icon

CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked

class Button(QtWidgets.QPushButton, Base):

  def __init__(self, parent, text='', callback=None, icon=None,
               toggle=None, command=None, **kw):
    
    QtWidgets.QPushButton.__init__(self, text, parent, parent=None)
    Base.__init__(self, parent, **kw)

    # self.setText(text)

    if icon: # filename or pixmap
      self.setIcon(Icon(icon))
      self.setIconSize(QtCore.QSize(22,22))
    
    if command:
      print("Use of qtgui.Button.command is deprecated")
      callback = command
    
    if toggle is not None:
      self.setCheckable(True)
      self.setSelected(toggle)
      
    self.callback = None
    self.setCallback(callback)

  def setSelected(self, selected):
    
    if self.isCheckable(): 
      if selected:
        self.setChecked(CHECKED)
      else:
        self.setChecked(UNCHECKED)

  def setCallback(self, callback):
  
    if self.callback:
      # self.disconnect(self, QtCore.pyqtSignal('clicked()'), self.callback)
      self.clicked.disconnect(self.callback)

    if callback:
      # self.connect(self, QtCore.pyqtSignal('clicked()'), callback)
      self.clicked.connect(callback)
      # self.clicked.connect doesn't work with lambda, yet...
    
    self.callback = callback

  def disable(self):

    self.setDisabled(True)

  def enable(self):

    self.setEnabled(True)

  def setText(self, text):

    QtWidgets.QPushButton.setText(self, text)

  def setState(self, state):

    self.setEnabled(state)

  def configure(self, **options):

    print("qtgui.Button has no configure()")

  def config(self, **options):
  
    print("qtgui.Button has no config()")

class ButtonMenu(Button):

  def __init__(self, parent, menu, text='Select...',
               callback=None, **kw):
    
    Button.__init__(self, parent, text, **kw)
    
    menu.callback = callback
    
    self.setMenu(menu)   
    # self.connect(menu, QtCore.pyqtSignal('triggered(QAction *)'), self._setText)
    self.triggered.connect(self._setText)

  def _setText(self, action):
    
    text = action.text()
    self.setText(text)


if __name__ == '__main__':

  from .Application import Application
  from .Menu import Menu

  app = Application()

  window = QtWidgets.QWidget()
  
  def click():
    print("Clicked")

  def clickObj(obj):
    print("Selected", obj)
  
  b1 = Button(window, text='Click Me', callback=click,
             tipText='Click for action',
             grid=(0, 0))

  b2 = Button(window, text='I am inactive', callback=click,
             tipText='Cannot click',
             grid=(0, 1), sticky='ns')
  
  b2.disable()

  b3 = Button(window, text='I am green', callback=click,
             tipText='Mmm, green', bgColor='#80FF80',
             grid=(0, 2), sticky='ns')

  b4 = Button(window, icon='icons/system-help.png', callback=click,
             tipText='A toggled icon button', toggle=True, 
             grid=(0, 3), sticky='ns')

  menu = Menu()
  menu.addItem('One', object=1)
  menu.addItem('Five', object=5)
  menu.addItem('Eleven', object=11)
  
  b5 = ButtonMenu(window, menu, callback=clickObj,
                  tipText='A menu button', 
                  grid=(0, 4), sticky='ns')
  
  window.show()
  
  app.start()

