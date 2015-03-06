__author__ = 'simon'

from PySide import QtCore, QtGui

class ToolButton(QtGui.QToolButton):

  def __init__(self, parent=None, colour=None, spectrumView=None):
    
    QtGui.QToolButton.__init__(self, parent.spectrumToolBar)
    self.colour = colour
    self.spectrumView = spectrumView
    pix=QtGui.QPixmap(60,10)
    pix.fill(QtGui.QColor(spectrumView.spectrum.sliceColour))
    # spectrumItem.newAction = self.spectrumToolbar.addAction(spectrumItem.name, QtGui.QToolButton)
    spectrumView.newAction = parent.spectrumToolBar.addAction(spectrumView.spectrum.name)#, self)
    newIcon = QtGui.QIcon(pix)
    spectrumView.newAction.setIcon(newIcon)
    spectrumView.newAction.setCheckable(True)
    spectrumView.newAction.setChecked(True)

    for spectrumView in parent.spectrumViews:
      if spectrumView.spectrum.dimensionCount < 2:
        spectrumView.newAction.toggled.connect(spectrumView.plot.setVisible)
      else:
        spectrumView.newAction.toggled.connect(spectrumView.setVisible)
    spectrumView.widget = parent.spectrumToolBar.widgetForAction(spectrumView.newAction)
    spectrumView.widget.setFixedSize(60,30)

