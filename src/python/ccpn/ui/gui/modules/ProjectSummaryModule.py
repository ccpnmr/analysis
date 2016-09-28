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

# def _testChainData(project):
#
#   result = []
#   result.append(['ID', '#Residue', '#Assignable', '#Assigned', 'Asigned%',
#                  '#AllAtoms', 'SimpleAtoms', '#NmrAtoms', '#AssignedNmrAtoms'])
#   for ii,chain in enumerate(project.chains):
#     result.append([chain.id, len(chain.residues), Summary.assignableAtomCount(chain),
#                    Summary.assignedAtomCount(chain), Summary.assignedAtomPercentage(chain),
#                    len(chain.atoms), len(list(x for x in chain.atoms if not x.componentAtoms)),
#                    len(project.nmrAtoms), len([x for x in project.nmrAtoms if x.atom])])
#
#   data = {}
#
#   for tag in ['names', 'nmrAtom', 'multiple', 'single', 'exchanging', 'inEquivalentGroup',
#               'equivalentEndswith1', 'simple']:
#     data[tag] = []
#
#
#   print ('@~@~ nAssignable', len(list(atom for atom in project.atoms
#                                  if atom.isEquivalentAtomGroup or not atom.componentAtoms)))
#
#   for atom in project.atoms:
#     name = atom.name
#     data['names'].append(name)
#     if atom.nmrAtom:
#       data['nmrAtom'].append(name)
#     if atom.componentAtoms:
#       data['multiple'].append(name)
#     else:
#       data['single'].append(name)
#       if atom.exchangesWithWater:
#         data['exchanging'].append(name)
#       else:
#         if any(x.isEquivalentAtomGroup for x in atom.compoundAtoms):
#           data['inEquivalentGroup'].append(name)
#           if name.endswith('1'):
#             data['equivalentEndswith1'].append(name)
#         else:
#           data['simple'].append(name)
#
#   #
#   return result, data
#
# def _countNmrAtoms(project):
#   data = {}
#   xyWildcards = 'XYxy'
#
#   for tag in ['allAssigned', 'unassigned', 'single', 'equivalent', 'equivalentLost', 'xy', 'double',
#               'other']:
#     data[tag] = []
#
#   data['xyComponents'] = set()
#
#   for nmrAtom in project.nmrAtoms:
#     name = nmrAtom.name
#     atom = nmrAtom.atom
#     if atom is None:
#       data['unassigned'].append(name)
#     else:
#       data['allAssigned'].append(name)
#       componentAtoms = atom.componentAtoms
#       if len(componentAtoms) < 2:
#         data['single'].append(name)
#       elif atom.isEquivalentAtomGroup:
#         # CH3 group or rotating aromatic ring
#         names =sorted(x.name for x in atom.componentAtoms)
#         data['equivalent'].append(names[0])
#         data['equivalentLost'].extend(names[1:])
#
#       elif any(x in xyWildcards for x in name):
#         data['xy'].append(name)
#         for ca in atom.componentAtoms:
#           data['xyComponents'].add(ca)
#
#       elif componentAtoms[0].isEquivalentAtomGroup:
#         # Isopropyl group
#         # NB this will get us to count HG1% twice and HG2% never, but the numbers will add up
#         names =sorted(x.name for x in componentAtoms[0].componentAtoms)
#         data['equivalent'].append(names[0])
#         data['equivalentLost'].extend(names[1:])
#
#       elif len(componentAtoms) == 2:
#         data['double'].append(name)
#       else:
#         data['other'].append(name)
#   #
#   return data
# if __name__ == '__main__':
#
#   import os
#   import time
#   import sys
#   from collections import Counter
#   path = sys.argv[1]
#
#   from ccpn.framework.Framework import getFramework
#   path = os.path.normpath(os.path.abspath(path))
#   time1 = time.time()
#   application = getFramework()
#   application.loadProject(path)
#   project = application.project
#   time2 = time.time()
#   print ("====> Loaded %s from file in seconds %s" % (project.name, time2-time1))
#   result, data = _testChainData(project)
#   print('Summary data')
#   print('Atom counting')
#   for tag, ll in sorted(data.items()):
#     # print ('Count', tag, Counter(ll))
#     print(tag, len(ll))
#   print('NmrAtom counting')
#   for tag, ll in sorted(_countNmrAtoms(project).items()):
#     print(tag, len(ll))
#   for tag, ll in sorted(_countNmrAtoms(project).items()):
#     print ('Count', tag, Counter(ll))
#   time3 = time.time()
#   print ("====> Done test in seconds %s" % (time3-time2))
#
#   # Needed to clean up notifiers
#   project.delete()