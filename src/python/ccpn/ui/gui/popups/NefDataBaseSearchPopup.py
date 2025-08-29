import statistics
import pandas as pd
from PyQt5 import QtCore

from ccpn.AnalysisMetabolomics.lib.simulationTools import createSimulatedSpectrum, spectrumFromScratch, buildCcpnSubstance, buildCcpnSample, flatSpectrumFromSpectrum, restoreSimulationLink
from ccpn.AnalysisMetabolomics.ui.gui.modules.ProfileByReference import getNefDatabase, simulationColumns
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CompoundWidgets import DoubleSpinBoxCompoundWidget
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox as DoubleSpinBox  # Consistent Camel case
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.table.Table import Table
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.util.Logging import getLogger


class NefDatabaseSearchPopup(CcpnDialog):
    def __init__(self, project, caller, spectrum, parent=None, title='Default Line Widths', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)
        self.project = project
        self.caller = caller
        self.spectrum = spectrum
        self.simulatedSpectrum = None
        df = self.caller.metaData
        # popupLayoutFrame = Widget(self,
        #                           setLayout=True,
        #                           grid=(0, 0))
        self.metabolitesTableWidget = Table(self,
                                            multiSelect=False,
                                            df=df,
                                            grid=(0, 0),
                                            selectionCallback=self._metaboliteTableSelection,
                                            # selectionCallbackEnabled=False,
                                            actionCallbackEnabled=False,
                                            borderWidth=4,
                                            minimumHeight=20,
                                            enableSearch=True)

        self.metabolitesTableWidget.setEditable(False)
        # self.metabolitesTableWidget.clicked.connect(self._selectMetabolite)

        self.simulationTableWidget = Table(self,
                                           df=pd.DataFrame(data=None, columns=simulationColumns),
                                           grid=(1, 0),
                                           selectionCallback=self._simulationTableSelection,
                                           borderWidth=4,
                                           minimumHeight=200,
                                           minimumWidth=self.width(),
                                           setHeightToRows=True,
                                           multiSelect=False)
        self.simulationTableWidget.setEditable(False)
        self.buttons = ButtonList(self, texts=['Close', 'Ok'],
                                  callbacks=[self.accept, self.accept],
                                  tipTexts=['Close window', 'Confirm simulation choice'],
                                  grid=(2, 0), hAlign='r')
        # self.setFixedWidth(500)
        self.setBaseSize(500, 750)

    def _metaboliteTableSelection(self, newRow, previousRow, selectedRow, lastRow):
        # selectedRow = self.metabolitesTableWidget.selectedRows()
        metaboliteName = selectedRow['name'].iloc[0]
        fileData = self.caller.getFileData(metaboliteName)
        data = self.caller.getSpectraData(fileData)
        self.spectrumData = data
        tableData = data[list(simulationColumns)]
        self.simulationTableWidget.updateDf(tableData)

    def _simulationTableSelection(self, newRow, previousRow, selectedRow, lastRow):
        simTableRow = selectedRow.iloc[0]
        simulatedSpectrumId = simTableRow['simulation_id']
        fileName = simTableRow['file_name']
        origin = simTableRow['simulation_origin']
        simulationType = simTableRow['simulation_type']
        self.sampleName = simTableRow["sample_name"]
        metaboliteName = fileName.removesuffix('.nef')
        fileData = self.caller.getFileData(metaboliteName)
        self.simulatedSpectrumId = simulatedSpectrumId
        self.fileData = fileData
        # if fileData is None:
        #     return None
        # # Check for the target simulation.
        # try:
        #     multiplets, signals, ssm = self.caller.getSimulationData(fileData, simulatedSpectrumId)
        # except Exception as es:
        #     getLogger().warning(f'Could not load spectrum parameter data for simulation: {es}')
        #     return None
        # # Make the substance object.
        # try:
        #     self.substance = self.caller.nefReader.load_ccpn_substance(self.project, self.caller.getMetaboliteData(fileData))
        # except Exception as es:
        #     getLogger().warning(f'Could not load substance data for simulation: {es}')
        #     return None
        # # Make the sample object.
        # try:
        #     if sampleName is None:
        #         sampleName = fileData[simulatedSpectrumId].get('ccpn_sample').removeprefix('ccpn_sample_')
        #     self.sample = self.caller.nefReader.load_ccpn_sample(self.project, fileData[f'ccpn_sample_{sampleName}'])
        # except Exception as es:
        #     getLogger().warning(f'Could not load sample data for simulation: {es}')
        #     return None
        # simulationType = fileData[simulatedSpectrumId]['ccpn_spectrum_type']
        # if simulationType != 'spin_system' and origin != 'unknown_substance':
        #     frequency = round(float(fileData[simulatedSpectrumId]['nef_spectrum_dimension'].data[0]['spectrometer_frequency']) / 10) * 10
        # points = self.spectrum.pointCounts[0]
        # referenceValue = self.spectrum.referenceValues[0]
        # spectralWidth = self.spectrum.spectralWidths[0]
        # limits = (referenceValue, referenceValue - spectralWidth)
        # simulatedSpectrum = createSimulatedSpectrum(self.project,
        #                                             name=simulatedSpectrumId,
        #                                             multiplets=multiplets,
        #                                             signals=signals,
        #                                             ssm=ssm,
        #                                             widthScale=1.0,
        #                                             referenceOffset=0.0,
        #                                             frequency=frequency,
        #                                             temperature=None,
        #                                             points=points,
        #                                             limits=limits,
        #                                             noiseLevel=self.spectrum.noiseLevel,
        #                                             spectrum=None,
        #                                             origin=origin)
        # self.simulatedSpectrum = simulatedSpectrum

