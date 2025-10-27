import statistics
from PyQt5 import QtCore

from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CompoundWidgets import DoubleSpinBoxCompoundWidget
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox as DoubleSpinBox # Consistent Camel case
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Widget import Widget


class DefaultLineWidthPopup(CcpnDialog):
    def __init__(self, pbr, parent=None, title='Default Line Widths', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)
        self.pbr = pbr
        self.regions = {'tsp (0.0ppm)': (0.1, -0.1),
                        'glucose (5.24ppm)': (5.3, 5.2),
                        'chloroform (7.26ppm)': (7.3, 7.2),
                        'formic_acid (8.0ppm)': (8.1, 7.9)}
        self.regionToExport = self.pbr.defaultLineWidthRegion
        referenceRegionFrame = Widget(self,
                                      setLayout=True,
                                      grid=(0, 0))
        labelWidget = Label(referenceRegionFrame,
                            grid=(0, 0),
                            text='Region:')
        self.referenceRegionPullDown = PulldownList(referenceRegionFrame,
                                                    grid=(0, 1),
                                                    texts=list(self.regions.keys()))
        self.widthReestimateButtonViaPreset = Button(referenceRegionFrame,
                                                     grid=(0, 2),
                                                     text='re-estimate widths',
                                                     callback=self.reestimateWidthViaPreset)
        labelWidget = Label(referenceRegionFrame,
                            grid=(1, 0),
                            text='Custom Region:')
        customRegionSpinboxesFrame = Widget(referenceRegionFrame,
                                            setLayout=True,
                                            grid=(1, 1))
        self.regionSpinbox1 = DoubleSpinBox(customRegionSpinboxesFrame,
                                            grid=(0, 2),
                                            value=self.regionToExport[0],
                                            decimals=4,
                                            step=0.0001,
                                            min=-10,
                                            max=15,
                                            suffix='ppm')
        self.regionSpinbox2 = DoubleSpinBox(customRegionSpinboxesFrame,
                                            grid=(0, 1),
                                            value=self.regionToExport[1],
                                            decimals=4,
                                            step=0.0001,
                                            min=-10,
                                            max=15,
                                            suffix='ppm')
        self.widthReestimateButtonViaCustom = Button(referenceRegionFrame,
                                                     grid=(1, 2),
                                                     text='re-estimate widths',
                                                     callback=self.reestimateWidthViaCustom)
        widthSpinboxesFrame = Frame(None, setLayout=True)
        scrollArea = ScrollArea(self, grid=(1, 0))
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(widthSpinboxesFrame)
        self.widthSpinboxes = {}
        labelWidget = Label(widthSpinboxesFrame,
                            text='Peak Width at half height (Hz)',
                            grid=(0, 0),
                            hAlign='right')
        for index, spectrum in enumerate(pbr.spectrumGroupWidget.getSpectra()):
            if spectrum.pid in self.pbr.defaultLineWidths.keys():
                value = self.pbr.defaultLineWidths[spectrum.pid]
            else:
                value = 1.0
            self.widthSpinboxes[spectrum.pid] = DoubleSpinBoxCompoundWidget(widthSpinboxesFrame,
                                                                            grid=(index + 1, 0),
                                                                            labelText=f'{spectrum.pid}:',
                                                                            value=value,
                                                                            decimals=2,
                                                                            step=0.01,
                                                                            min=0.01,
                                                                            max=5,
                                                                            callback=self.widthWidgetCallback)
            self.widthSpinboxes[spectrum.pid].label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.widthSpinboxes[spectrum.pid].doubleSpinBox.setAutoFillBackground(True)
        self.widthWidgetCallback()
        self.widthReestimateButtonViaCustom.setMinimumHeight(list(self.widthSpinboxes.values())[0].height())
        Spacer(self,
               width=1,
               height=10,
               grid=(2, 0),
               hPolicy='ignored')
        self.buttons = ButtonList(self, texts=['Close', 'Ok'],
                                  callbacks=[self.accept, self.applyDefaultWidths],
                                  tipTexts=['Close window', 'Confirm default line widths'],
                                  grid=(3, 0), hAlign='r')
        if len(self.pbr.defaultLineWidths) == 0:
            self.reestimateWidthViaPreset()
        self.setFixedWidth(500)
        self.setBaseSize(500, 350)

    def widthWidgetCallback(self):
        widths = [spinbox.doubleSpinBox.value() for spinbox in self.widthSpinboxes.values()]
        widthMean = statistics.mean(widths)
        widthStdev = statistics.pstdev(widths)
        for spinBox in self.widthSpinboxes.values():
            if not widthMean - widthStdev < spinBox.doubleSpinBox.value() < widthMean + widthStdev:
                p = spinBox.doubleSpinBox.palette()
                p.setColor(spinBox.doubleSpinBox.backgroundRole(), QtCore.Qt.red)
                spinBox.doubleSpinBox.setPalette(p)
                spinBox.doubleSpinBox.setToolTip('Width value is outside one standard deviation of the peak width estimates.')
            else:
                p = spinBox.doubleSpinBox.palette()
                p.setColor(spinBox.doubleSpinBox.backgroundRole(), QtCore.Qt.transparent)
                spinBox.doubleSpinBox.setPalette(p)
                spinBox.doubleSpinBox.setToolTip(None)

    def reestimateWidthViaPreset(self):
        region = self.regions[self.referenceRegionPullDown.getText()]
        for index, spectrum in enumerate(self.pbr.spectrumGroupWidget.getSpectra()):
            width = self.pbr._getSpectrumLineWidth(spectrum, region)
            self.widthSpinboxes[spectrum.pid].doubleSpinBox.setValue(width)
        self.regionToExport = region

    def reestimateWidthViaCustom(self):
        region = (max([self.regionSpinbox1.value(), self.regionSpinbox2.value()]), min([self.regionSpinbox1.value(), self.regionSpinbox2.value()]))
        for index, spectrum in enumerate(self.pbr.spectrumGroupWidget.getSpectra()):
            width = self.pbr._getSpectrumLineWidth(spectrum, region)
            self.widthSpinboxes[spectrum.pid].doubleSpinBox.setValue(width)
        self.regionToExport = region

    def applyDefaultWidths(self):
        for key, spinBox in self.widthSpinboxes.items():
            self.pbr.defaultLineWidths[key] = spinBox.doubleSpinBox.value()
        self.pbr._defaultLineWidthsRecordWidget.setText(str(self.pbr.defaultLineWidths))
        self.pbr.defaultLineWidthRegion = self.regionToExport
        self.pbr._defaultLineWidthsRegionRecordWidget.setText(str(self.regionToExport))
        self.accept()
