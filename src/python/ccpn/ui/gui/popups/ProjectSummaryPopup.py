"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-09-20 10:10:24 +0100 (Tue, September 20, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2016-09-07 12:42:52 +0100 (Wed, 07 Sep 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import datetime
import pandas as pd
from PyQt5 import QtGui, QtCore, QtPrintSupport
from collections import OrderedDict
from ccpn.core.lib import Summary
from ccpn.util import Logging
from ccpn.util import Path

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.table.Table import Table
from ccpn.ui.gui.widgets.Column import ColumnClass


MINHEIGHT = 100


class ProjectSummaryPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, title='Project Summary', modal=False, **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project

        # self.setContentsMargins(15,15,15,15)
        # QtWidgets.QDialog.__init__(self, parent=parent)
        if modal:  # Set before visible
            modality = QtCore.Qt.ApplicationModal
            self.setWindowModality(modality)
        self.setWindowTitle(title)
        self.resize(700, self.height())

        self._setupData()

        self.mainFrame = frame = Frame(self, grid=(0, 0), setLayout=True)

        row = 0
        self.pathFrame = Frame(self.mainFrame, grid=(row, 0), setLayout=True)

        self.pathLabel = Label(self.pathFrame, text='Path', grid=(row, 0), hAlign='l', bold=True)
        self.pathPathLabel = Label(self.pathFrame, text=self.project.path, grid=(row, 1), hAlign='l', bold=False)
        self.pathPathButton = Button(self.pathFrame, text='Copy', grid=(row, 2), hAlign='r',
                                     callback=self._pathToClipboard)

        row += 1
        # SPECTRA

        self.spectrumFrame = Frame(self.mainFrame, grid=(row, 0), setLayout=True)
        self.spectrumLabel = Label(self.spectrumFrame, text='Spectra', grid=(0, 0), hAlign='l', bold=True)
        row += 1

        columnsSpectrum = ColumnClass([
            ('#', lambda spectrum: self.spectrumNumberDict[spectrum], 'Number', None, None),
            ('Pid', lambda spectrum: spectrum.pid, 'Pid of NmrResidue', None, None),
            ('_object', lambda spectrum: spectrum, 'Object', None, None),
            ('Id', lambda spectrum: spectrum.id, 'Spectrum id', None, None),
            ('Dimension count', lambda spectrum: spectrum.dimensionCount, 'Spectrum dimension count', None, None),
            ('Chemical shiftList',
             lambda spectrum: spectrum.chemicalShiftList.id, 'Spectrum chemical shiftList', None, None),
            ('File path', lambda spectrum: spectrum.filePath, 'Spectrum data file path', None, None),
            ])
        self._hiddenColumnsSpectrum = ['Pid']
        self.dataFrameSpectrum = None

        # initialise the table
        self.spectrumTable = Table(parent=self.spectrumFrame,
                                   mainWindow=self.mainWindow,
                                   grid=(1, 0), gridSpan=(1, 1)
                                   )
        self._setTableOptions(self.spectrumTable)
        row += 1

        # PEAKLISTS

        self.peakListFrame = Frame(self.mainFrame, grid=(row, 0), setLayout=True)
        self.peakListLabel = Label(self.peakListFrame, text='PeakLists', grid=(0, 0), hAlign='l', bold=True)
        row += 1

        columnsPeakList = ColumnClass([
            ('#', lambda peakList: self.peakListNumberDict[peakList], 'Number', None, None),
            ('Pid', lambda peakList: peakList.pid, 'Pid of NmrResidue', None, None),
            ('_object', lambda peakList: peakList, 'Object', None, None),
            ('Id', lambda peakList: peakList.id, 'PeakList id', None, None),
            ('Peak count', lambda peakList: len(peakList.peaks), 'Number of peaks in peakList', None, None),
            ('Partly assigned count', Summary.partlyAssignedPeakCount,
             'Number of peaks in peakList at least partially assigned', None, None),
            ('Partly assigned %', Summary.partlyAssignedPeakPercentage,
             'Percentage of peaks in peakList at least partially assigned', None, None),
            ('Fully assigned count', Summary.fullyAssignedPeakCount,
             'Number of peaks in peakList fully assigned', None, None),
            ('Fully assigned %', Summary.fullyAssignedPeakPercentage,
             'Percentage of peaks in peakList fully assigned', None, None),
            ])
        self._hiddenColumnsPeakList = ['Pid']
        self.dataFramePeakList = None

        # initialise the table
        self.peakListTable = Table(parent=self.peakListFrame,
                                   mainWindow=self.mainWindow,
                                   grid=(1, 0), gridSpan=(1, 1)
                                   )
        self._setTableOptions(self.peakListTable)
        row += 1

        # CHAINS

        self.chainFrame = Frame(self.mainFrame, grid=(row, 0), setLayout=True)
        self.chainLabel = Label(self.chainFrame, text='Chains', grid=(0, 0), hAlign='l', bold=True)
        row += 1

        columnsChain = ColumnClass([
            ('#', lambda chain: self.chainNumberDict[chain], 'Number', None, None),
            ('Pid', lambda chain: chain.pid, 'Pid of NmrResidue', None, None),
            ('_object', lambda chain: chain, 'Object', None, None),
            ('Id', lambda chain: chain.id, 'Chain id', None, None),
            ('Residue count', lambda chain: len(chain.residues), 'Number of residues in chain', None, None),
            ('Assignable atom count', Summary.assignableAtomCount,
             'Number of atoms in chain which are assignable to', None, None),
            ('Assigned atom count', Summary.assignedAtomCount,
             'Number of atoms in chain which are assigned to', None, None),
            ('Assigned atom %', Summary.assignedAtomPercentage,
             'Percentage of atoms in chain which are assigned to', None, None),
            ])
        self._hiddenColumnsChains = ['Pid']
        self.dataFrameChains = None

        # initialise the table
        self.chainTable = Table(parent=self.chainFrame,
                                mainWindow=self.mainWindow,
                                grid=(1, 0), gridSpan=(1, 1)
                                )
        self._setTableOptions(self.chainTable)
        row += 1

        self.mainFrame.addSpacer(10, 10, grid=(row, 0))
        row += 1

        # Buttons
        buttonFrame = Frame(self, grid=(1, 0), setLayout=True)
        button = Button(buttonFrame, 'Save to Excel', callback=self._saveToExcel, grid=(0, 0))
        # button = Button(buttonFrame, 'Save to PDF', callback=self._saveToPdf, grid=(0, 1))
        button = Button(buttonFrame, 'Close', callback=self.accept, grid=(0, 2))

        row += 1

        self.dataFrameSpectrum = self.getDataFrameFromList(buildList=self.spectra,
                                                           colDefs=columnsSpectrum)
        self.dataFramePeakList = self.getDataFrameFromList(buildList=self.peakLists,
                                                           colDefs=columnsPeakList)
        self.dataFrameChains = self.getDataFrameFromList(buildList=self.chains,
                                                         colDefs=columnsChain)

        self.spectrumTable.updateDf(df=self.dataFrameSpectrum)
        self.peakListTable.updateDf(df=self.dataFramePeakList)
        self.chainTable.updateDf(df=self.dataFrameChains)

    @staticmethod
    def _setTableOptions(table):
        """Set options for a table
        """
        table.setEditable(False)
        table.setDeleteEnabled(False)
        table.setSearchEnabled(False)
        table._enableActionCallback = False
        table._enableSelectionCallback = False
        table.setMinimumHeight(MINHEIGHT)

    @staticmethod
    def getDataFrameFromList(buildList=None, colDefs=None):
        """
        Return a Pandas dataFrame from an internal list of objects
        The columns are based on the 'func' functions in the columnDefinitions

        :param buildList:
        :param colDefs:
        :return pandas dataFrameObject:
        """
        allItems = []
        objects = []

        if buildList:
            for col, obj in enumerate(buildList):
                listItem = OrderedDict()
                for header in colDefs.columns:
                    try:
                        listItem[header.headerText] = header.getValue(obj)
                    except Exception as es:
                        # NOTE:ED - catch any nasty surprises in tables
                        listItem[header.headerText] = None

                allItems.append(listItem)
                objects.append(obj)

        return pd.DataFrame(allItems, columns=colDefs.headings)

    def _setupData(self):

        # SPECTRA

        self.spectra = self.project.spectra
        self.spectrumNumberDict = {}
        for n, spectrum in enumerate(self.spectra):
            self.spectrumNumberDict[spectrum] = n + 1

        # PEAKLISTS

        self.peakLists = []
        self.peakListNumberDict = {}
        n = 1
        for spectrum in self.spectra:
            self.peakLists.extend(spectrum.peakLists)
            for peakList in spectrum.peakLists:
                self.peakListNumberDict[peakList] = n
                n += 1

        # CHAINS

        self.chains = self.project.chains
        self.chainNumberDict = {}
        for n, chain in enumerate(self.chains):
            self.chainNumberDict[chain] = n + 1

    def _pathToClipboard(self, *args):
        from ccpn.util.Common import copyToClipboard

        copyToClipboard([self.pathPathLabel.get()])

    def _getPathPrefix(self):

        directory = os.path.join(self.project.path, Path.CCPN_SUMMARIES_DIRECTORY)
        if not os.path.exists(directory):
            os.mkdir(directory)

        now = datetime.datetime.now()
        filePrefix = 'summary_%s_%02d%02d%02d_%02d%02d%02d' % \
                     (self.project.name, now.year, now.month, now.day, now.hour, now.minute, now.second)

        return os.path.join(directory, filePrefix)

    def _showMessage(self, path):

        message = 'Project summary written to file %s' % path

        logger = Logging.getLogger()
        logger.info(message)

        self.getParent().statusBar().showMessage(message)

    def _saveToPdf(self):

        path = self._getPathPrefix() + '.pdf'

        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.ScreenResolution)
        printer.setPaperSize(QtPrintSupport.QPrinter.A4)
        printer.setOrientation(QtPrintSupport.QPrinter.Landscape)
        printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        painter = QtGui.QPainter(printer)
        self.spectrumFrame.render(painter)
        printer.newPage()
        self.peakListFrame.render(painter)
        printer.newPage()
        self.chainFrame.render(painter)
        painter.end()

        self._showMessage(path)

    def _saveToExcel(self):

        path = self._getPathPrefix() + '.xlsx'

        writer = pd.ExcelWriter(path, engine='xlsxwriter')

        for (table, name) in ((self.spectrumTable, 'spectrum'),
                              (self.peakListTable, 'peakList'),
                              (self.chainTable, 'chain')):
            df = table._df
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=name, index=False)

            # table.findExportFormats(path, sheet_name=name)

        writer.save()

        self._showMessage(path)
