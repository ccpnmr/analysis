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

from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Table import ObjectTable, Column

def _percentage(count, totalCount, decimalPlaceCount=0):

  if totalCount:
    return int(round((100.0 * count) / totalCount, decimalPlaceCount))
  else:
    return 0

# PEAKLISTS

def _partlyAssignedPeakCount(peakList):

  return len([peak for peak in peakList.peaks if any(peak.dimensionNmrAtoms)])

def _partlyAssignedPeakPercentage(peakList):

  return _percentage(_partlyAssignedPeakCount(peakList), len(peakList.peaks))

def _fullyAssignedPeakCount(peakList):

  return len([peak for peak in peakList.peaks if all(peak.dimensionNmrAtoms)])

def _fullyAssignedPeakPercentage(peakList):

  return _percentage(_fullyAssignedPeakCount(peakList), len(peakList.peaks))

# CHAINS

def _assignableAtomCount(chain):

  # Atoms without a chemAtom are various kinds of pseudoatoms.
  # Water exchangeable atoms are e.g. OH, NH3, guanidine.

  # NB the result is counting rotating aromatic rings as fixed,
  # but it would be too much work to fix that

  count = 0
  for atom in chain.atoms:
    apiAtom = atom._wrappedData
    apiChemAtom = apiAtom.chemAtom
    if apiChemAtom is not None:
      # Real atom, not pseudo
      if not apiChemAtom.waterExchangeable:
        # Not e.g. OH or NH3
        if apiAtom.name.endswith('1') or len(apiAtom.components) != 3:
          # Count only for the first atom in CH3, NH3 groups
          # A bit of a hack, but should be OK i practice
          count += 1
  #
  return count


  # return len([atom for atom in chain.atoms if atom._wrappedData.chemAtom
  #             and not atom._wrappedData.chemAtom.waterExchangeable])

def _assignedAtomCount(chain):

  # NB this is not quite precise
  # You could get miscounting if you have both stereo, non-stereo, and wildcard/pseudo
  # NmrAtoms for the same atoms, and you could in theory get miscounts for nested
  # pairs (like guanidinium C-(NH2)2
  # Also e.g. Tyr/Phe HD% is counted as one resonance, whereas it is counted as
  # two assignable atoms.
  # But I leave the details to someone else - this should be decent.

  count = 0

  # Should be 'xy' eventually, but we shall soon change from 'XY' to 'xy'.
  # During the transition this is safest
  xyWildcards = 'XYxy'

  nmrChain = chain.nmrChain
  if nmrChain is not None:
    for nmrAtom in nmrChain.nmrAtoms:
      atom = nmrAtom.atom
      if atom is not None:
        nComponents = len(atom._wrappedData.components)
        if nComponents == 2:
          name = atom.name
          if name[-1] in xyWildcards:
            # Non-stereospecific, we are only assigning one, not two
            count += 1
          elif name[-1] == '%' and name[-2] in xyWildcards:
            # isopropyl groups and similar
            count += 1
          else:
            # % expressions for CH2, NH2, Val CG2, Tyr side chain, ...
            count += 2
        else:
          # Single atoms count as one, CH3 and NH3 groups too
          count += 1
  #
  return count

  # return len([atom for atom in chain.atoms if atom.nmrAtom])

def _assignedAtomPercentage(chain):

  return _percentage(_assignedAtomCount(chain), _assignableAtomCount(chain))

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
      Column('Partly assigned count', _partlyAssignedPeakCount,
             tipText='Number of peaks in peakList at least partially assigned'),
      Column('Partly assigned %', _partlyAssignedPeakPercentage,
             tipText='Percentage of peaks in peakList at least partially assigned'),
      Column('Fully assigned count', _fullyAssignedPeakCount,
             tipText='Number of peaks in peakList fully assigned'),
      Column('Fully assigned %', _fullyAssignedPeakPercentage,
             tipText='Percentage of peaks in peakList fully assigned'),
    ]

    self.peakListTable = ObjectTable(self.mainWidget, columns=columns, objects=self.peakLists, grid=(row, 0))
    row += 1

    return # TEMP (below code not working and very, very slow)

    # CHAINS

    label = Label(self.mainWidget, text='Chains', grid=(row, 0), hAlign='l')
    row += 1

    columns = [
      Column('#', lambda chain: self.chainNumberDict[chain], tipText='Number'),
      Column('Id', lambda chain: chain.id, tipText='Chain id'),
      Column('Residue count', lambda chain: len(chain.residues), tipText='Number of residues in chain'),
      Column('Assignable atom count', _assignableAtomCount,
             tipText='Number of atoms in chain which are assignable to'),
      Column('Assigned atom count', _assignedAtomCount,
             tipText='Number of atoms in chain which are assigned to'),
      Column('Assigned atom %', _assignedAtomPercentage,
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
                 '#Atoms', '#hasChemAtom', '#NmrAtoms', '#AssignedNmrAtoms',
                 'isWaterExchangeable'])
  for ii,chain in enumerate(project.chains):
    result.append([ii+1, chain.id, len(chain.residues), _assignableAtomCount(chain),
                   _assignedAtomCount(chain), _assignedAtomPercentage(chain),
                   len(chain.atoms), len([x for x in chain.atoms if x._wrappedData.chemAtom],),
                   len(project.nmrAtoms), len([x for x in project.nmrAtoms if x.atom]),
                   len([x for x in chain.atoms if x._wrappedData.chemAtom
                        and x._wrappedData.chemAtom.waterExchangeable])])

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
      if atom._wrappedData.chemAtom.waterExchangeable:
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