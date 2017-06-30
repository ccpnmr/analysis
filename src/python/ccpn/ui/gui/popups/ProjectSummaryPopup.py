"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Wayne Boucher $"
__dateModified__ = "$dateModified: 2017-04-11 16:20:50 +0100 (Tue, April 11, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: skinnersp $"
__date__ = "$Date: 2016-09-07 12:42:52 +0100 (Wed, 07 Sep 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import datetime

import pandas as pd

from PyQt4 import QtGui, QtCore

from ccpn.core.lib import Summary
from ccpn.util import Logging
from ccpn.util import Path

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb


class ProjectSummaryPopup(CcpnDialog):
  def __init__(self, project, parent=None, title='Project Summary', modal=False, **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.project = project

    # self.setContentsMargins(15,15,15,15)
    # QtGui.QDialog.__init__(self, parent=parent)
    if modal:  # Set before visible
      modality = QtCore.Qt.ApplicationModal
      self.setWindowModality(modality)
    self.setWindowTitle(title)
    self.resize(700, self.height())

    self._setupData()

    self.mainFrame = frame = Frame(self, grid=(0,0), setLayout=True)

    row = 0

    # SPECTRA

    self.spectrumFrame = Frame(self.mainFrame, grid=(row,0), setLayout=True)
    self.spectrumLabel = Label(self.spectrumFrame, text='Spectra', grid=(0, 0), hAlign='l')
    row += 1

    columns = [
      Column('#', lambda spectrum: self.spectrumNumberDict[spectrum], tipText='Number'),
      Column('Id', lambda spectrum: spectrum.id, tipText='Spectrum id'),
      Column('Dimension count', lambda spectrum: spectrum.dimensionCount, tipText='Spectrum dimension count'),
      Column('Chemical shiftList',
             lambda spectrum: spectrum.chemicalShiftList.id, tipText='Spectrum chemical shiftList'),
      Column('File path', lambda spectrum: spectrum.filePath, tipText='Spectrum data file path'),
    ]
    self.spectrumTable = ObjectTable(self.spectrumFrame, columns=columns, objects=self.spectra, grid=(1, 0))
    row += 1

    # PEAKLISTS

    self.peakListFrame = Frame(self.mainFrame, grid=(row,0), setLayout=True)
    self.peakListLabel = Label(self.peakListFrame, text='PeakLists', grid=(0, 0), hAlign='l')
    row += 1

    columns = [
      Column('#', lambda peakList: self.peakListNumberDict[peakList], tipText='Number'),
      Column('Id', lambda peakList: peakList.id, tipText='PeakList id'),
      Column('Peak count', lambda peakList: len(peakList.peaks), tipText='Number of peaks in peakList'),
      Column('Partly assigned count', Summary.partlyAssignedPeakCount,
             tipText='Number of peaks in peakList at least partially assigned'),
      Column('Partly assigned %', Summary.partlyAssignedPeakPercentage,
             tipText='Percentage of peaks in peakList at least partially assigned'),
      Column('Fully assigned count', Summary.fullyAssignedPeakCount,
             tipText='Number of peaks in peakList fully assigned'),
      Column('Fully assigned %', Summary.fullyAssignedPeakPercentage,
             tipText='Percentage of peaks in peakList fully assigned'),
    ]

    self.peakListTable = ObjectTable(self.peakListFrame, columns=columns, objects=self.peakLists, grid=(1, 0))
    row += 1

    # CHAINS

    self.chainFrame = Frame(self.mainFrame, grid=(row,0), setLayout=True)
    self.chainLabel = Label(self.chainFrame, text='Chains', grid=(0, 0), hAlign='l')
    row += 1

    columns = [
      Column('#', lambda chain: self.chainNumberDict[chain], tipText='Number'),
      Column('Id', lambda chain: chain.id, tipText='Chain id'),
      Column('Residue count', lambda chain: len(chain.residues), tipText='Number of residues in chain'),
      Column('Assignable atom count', Summary.assignableAtomCount,
             tipText='Number of atoms in chain which are assignable to'),
      Column('Assigned atom count', Summary.assignedAtomCount,
             tipText='Number of atoms in chain which are assigned to'),
      Column('Assigned atom %', Summary.assignedAtomPercentage,
             tipText='Percentage of atoms in chain which are assigned to'),
    ]

    self.chainTable = ObjectTable(self.chainFrame, columns=columns, objects=self.chains, grid=(1, 0))
    row += 1

    # buttons

    buttonFrame = Frame(self, grid=(1, 0), setLayout=True)
    button = Button(buttonFrame, 'Save to Excel', callback=self._saveToExcel, grid=(0, 0))
    button = Button(buttonFrame, 'Save to PDF', callback=self._saveToPdf, grid=(0, 1))
    button = Button(buttonFrame, 'Close', callback=self.accept, grid=(0, 2))

    row += 1

  def _setupData(self):

    # SPECTRA

    self.spectra = self.project.spectra
    self.spectrumNumberDict = {}
    for n, spectrum in enumerate(self.spectra):
      self.spectrumNumberDict[spectrum] = n+1

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
      self.chainNumberDict[chain] = n+1

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

    self.parent().statusBar().showMessage(message)

  def _saveToPdf(self):

    path = self._getPathPrefix() + '.pdf'

    printer = QtGui.QPrinter(QtGui.QPrinter.ScreenResolution)
    printer.setPaperSize(QtGui.QPrinter.A4)
    printer.setOrientation(QtGui.QPrinter.Landscape)
    printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
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
      dataFrame = table.tableToDataFrame()
      dataFrame.to_excel(writer, sheet_name=name, index=False)

    writer.save()

    self._showMessage(path)