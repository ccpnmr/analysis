"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-09-07 12:42:52 +0100 (Wed, 07 Sep 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: skinnersp $"
__date__ = "$Date: 2016-09-07 12:42:52 +0100 (Wed, 07 Sep 2016) $"
__version__ = "$Revision: 9852 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

from ccpn.core.lib import Summary

from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Table import ObjectTable, Column

class ProjectSummaryModule(CcpnModule):

  def __init__(self, project):

    CcpnModule.__init__(self, name='Project Summary')

    self.project = project
    self._setupData()

    row = 0

    # SPECTRA

    label = Label(self.mainWidget, text='Spectra', grid=(row, 0), hAlign='l')
    row += 1

    columns = [
      Column('#', lambda spectrum: self.spectrumNumberDict[spectrum], tipText='Number'),
      Column('Id', lambda spectrum: spectrum.id, tipText='Spectrum id'),
      Column('Dimension count', lambda spectrum: spectrum.dimensionCount, tipText='Spectrum dimension count'),
      Column('Chemical shiftList',
             lambda spectrum: spectrum.chemicalShiftList.id, tipText='Spectrum chemical shiftList'),
      Column('File path', lambda spectrum: spectrum.filePath, tipText='Spectrum data file path'),
    ]
    self.spectrumTable = ObjectTable(self.mainWidget, columns=columns, objects=self.spectra, grid=(row, 0))
    row += 1

    # PEAKLISTS

    label = Label(self.mainWidget, text='PeakLists', grid=(row, 0), hAlign='l')
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

    self.peakListTable = ObjectTable(self.mainWidget, columns=columns, objects=self.peakLists, grid=(row, 0))
    row += 1

    # CHAINS

    label = Label(self.mainWidget, text='Chains', grid=(row, 0), hAlign='l')
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

    self.chainTable = ObjectTable(self.mainWidget, columns=columns, objects=self.chains, grid=(row, 0))
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

def _testChainData(project):

  result = []
  result.append(['#', 'ID', '#Residue', '#Assignable', '#Assigned', 'Asigned%',
                 '#Atoms', '#NmrAtoms', '#AssignedNmrAtoms',
                 'isWaterExchangeable'])
  for ii,chain in enumerate(project.chains):
    result.append([ii+1, chain.id, len(chain.residues), _assignableAtomCount(chain),
                   _assignedAtomCount(chain), _assignedAtomPercentage(chain),
                   len(chain.atoms),
                   len(project.nmrAtoms), len([x for x in project.nmrAtoms if x.atom]),
                   len([x for x in chain.atoms if x.exchangesWithWater])])

  data = {'nuclei':[], 'names':[], 'assigned':[], 'chemAtom':[], 'NOchemAtom':[],
          'exchangeable':[], 'non-exchangeable':[]}

  for atom in project.atoms:
    name = atom.name
    data['nuclei'].append(name[0])
    data['names'].append(name)
    if atom.nmrAtom:
      data['assigned'].append(name)
    if atom._wrappedData.chemAtom:
      data['chemAtom'].append(name)
      if atom.exchangesWithWater:
        data['exchangeable'].append(name)
      else:
        data['non-exchangeable'].append(name)
    else:
      data['NOchemAtom'].append(name)

  #
  return result, data

if __name__ == '__main__':

  import os
  import time
  import sys
  from collections import Counter
  path = sys.argv[1]

  from ccpn.framework.Framework import getFramework
  path = os.path.normpath(os.path.abspath(path))
  time1 = time.time()
  application = getFramework()
  application.loadProject(path)
  project = application.project
  time2 = time.time()
  print ("====> Loaded %s from file in seconds %s" % (project.name, time2-time1))
  result, data = _testChainData(project)
  for ll in result:
    print ('  '.join(str(x) for x in ll))
  for tag, ll in data.items():
    print ('Count', tag, Counter(ll))
  time3 = time.time()
  print ("====> Done test in seconds %s" % (time3-time2))

  # Needed to clean up notifiers
  project.delete()