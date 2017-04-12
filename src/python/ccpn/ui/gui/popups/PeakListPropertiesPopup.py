

from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.widgets.MessageDialog import MessageDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList

from ccpn.util.Colour import spectrumColours

# def _getColour(peakList, peakListViews, attr):
#
#   if peakListViews:
#     colour = getattr(peakListViews[0], attr)
#   else:
#     colour = getattr(peakList, attr)
#
#   if not colour:
#     colour = peakList.spectrum.positiveContourColour
#
#   return colour

# FIXME   Notifiers are not triggered correctly when changing colours.
# TODO
# Make it working for all the display and not for the one currently opened.
# Add apply, cancel button.
# 1D.




class PeakListPropertiesPopup(QtGui.QDialog):
  def __init__(self, parent=None, peakList=None, **kw):
    super(PeakListPropertiesPopup, self).__init__(parent)
    self.peakList = peakList

    if not self.peakList:
      MessageDialog.showWarning('No PeakList Found','')
      self.close()

    else:
      self.peakListViews = [peakListView for peakListView in peakList.project.peakListViews if peakListView.peakList == peakList]

      # NOTE: below is not sorted in any way, but if we change that, we also have to change loop in _fillColourPulldown
      spectrumColourKeys = list(spectrumColours.keys())
      if not self.peakList.symbolColour:
          self.peakList.symbolColour = spectrumColourKeys[0]  # default
      if not self.peakList.textColour:
        self.peakList.textColour = spectrumColourKeys[1]   # default*

      self.peakListLabel = Label(self, "PeakList Name ", grid=(0, 0))
      self.peakListLabel = Label(self, peakList.id, grid=(0, 1))

      # does nothing.
      # self.symbolLabel = Label(self, 'Peak Symbol', grid=(2, 0))
      # self.symbolPulldown = PulldownList(self, grid=(2, 1))
      # self.symbolPulldown.setData(['x'])
      self.symbolColourLabel = Label(self, 'Peak Symbol Colour', grid=(3, 0))
      self.symbolColourPulldownList = PulldownList(self, grid=(3, 1))
      self._fillColourPulldown(self.symbolColourPulldownList)
      self.symbolColourPulldownList.setCurrentIndex(spectrumColourKeys.index(peakList.symbolColour))
      self.symbolColourPulldownList.currentIndexChanged.connect(self._changeSymbolColour)

      self.textColourLabel = Label(self, 'Peak Text Colour', grid=(4, 0))
      self.textColourPulldownList = PulldownList(self, grid=(4, 1))
      self._fillColourPulldown(self.textColourPulldownList)
      self.textColourPulldownList.setCurrentIndex(spectrumColourKeys.index(peakList.textColour))
      self.textColourPulldownList.currentIndexChanged.connect(self._changeTextColour)

      self.closeButton = Button(self, text='Close', grid=(6, 1), callback=self.accept)
      ## Broken.
      # self.minimalAnnotationLabel = Label(self, 'Minimal Annotation', grid=(5, 0))
      # self.minimalAnnotationCheckBox = CheckBox(self, grid=(5, 1))

      ## Broken. If you close and reopen a display, it doesn't care about the checkbox.
      # self.displayedLabel = Label(self, 'Is displayed', grid=(1, 0))
      # self.displayedCheckBox = CheckBox(self, grid=(1, 1))
      # if(any([peakListView.isVisible() for peakListView in self.peakListViews])):
      #   self.displayedCheckBox.setChecked(True)
      #
      # for peakListView in self.peakListViews:
      #   self.displayedCheckBox.toggled.connect(peakListView.setVisible)

  def _changeSymbolColour(self, value):
    colour = list(spectrumColours.keys())[value]
    self.peakList.symbolColour = colour
    for peakListView in self.peakListViews:
      peakListView.symbolColour = colour


  def _changeTextColour(self, value):
    colour = list(spectrumColours.keys())[value]
    self.peakList.textColour = colour
    for peakListView in self.peakListViews:
      peakListView.textColour = colour

  def _fillColourPulldown(self, pulldown):
    for item in spectrumColours.items():
      pix=QtGui.QPixmap(QtCore.QSize(20, 20))
      pix.fill(QtGui.QColor(item[0]))
      pulldown.addItem(icon=QtGui.QIcon(pix), text=item[1])

