"""Module Documentation here

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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:35 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
from collections import OrderedDict

import numpy
import pandas

from ccpn import core
from ccpn.core.lib import CcpnSorting
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.util import Sorting


class SortingData(WrapperTesting):

  # Path of project to load (None for new project
  projectPath = None

  # Data for sorting tests.
  # All data are in correct sorting order as given here
  specials = [None, False, True, ]

  reals = [float('NaN'),float('-Infinity'), -12, -2, -1, -0.1, 0, 1.1e-1,
    1, 2, 12, float('Infinity'),]

  negstrings = ['', 'NaN', '-Infinity', '-12', '-2', '-1', '-0.1',]

  zerostrings = ['+0', '+0.', '+0.0', '-.0', '-0', '-0.0', '.0', '0', '0.0', '0.0 ', ]

  posstrings = ['1.1e-12', ' 1', '+1', '1', '1.', '1.0', '2', '12', 'Infinity', ]

  strings2 = [' ', ' z', ' z.', '#', '+ 0.0', '.0-','@', 'A', 'B',
    'Z', 'Z.', 'a',  'blah', 'blah2', 'blahblah', 'z',  ]

  chainCodes = ['1', '2', '15', '#1', '@-2', '@1',
                '@1', '@2', '@12', '@-', '@A', '@a', 'A', 'A2', 'Z', 'a', 'z', ]

  sequenceCodes = ['-1', ' 1', '+1', '1',  '1b', '1.', '2b', '2b-11', '2b-2.', '2b-1', '2b+0', '2b-0',
                   '2b0', '2b+1', '2b+2', '2b2', '2b.', '2b@11', '2ba', '15.',  '#1', '#2', '#11', '#11-1',
                   '#11+1',  '#105', '@-11', '@-2', '@-1', '@0', '@1', '@2', '@11', '@-', '@@a',
                   '@A']

  sequenceCodes2 = ['-1', '+1', '1', '1b', '2b', '2b-11', '2b-2.', '2b-1', '2b+0', '2b-0',
                   '2b0', '2b+1', '2b+2', '2b2', '2b@11', '2ba',  '#1', '#2', '#11', '#11-1',
                   '#11+1',  '#105', '@-11', '@-2', '@-1', '@0', '@1', '@2', '@11', '@-', '@@a',
                   '@A']

  atomNames =  ['C', 'C@2', 'CA', 'CB', 'CD', 'CD1', 'CD2', 'CD%', 'CD*','CDx', 'CDy',
                'H', 'H1', 'H2', 'H3', 'H#', 'H%', 'H*',  'H@1', 'H@2', 'H@15', 'HG', 'HG1', 'HG1%',
                'HG2', 'HG3', 'HG%', 'HG*', 'HGx', 'HGy', ]

  tuples = [(1,'a'), ('1', 'b')]

  lists = [[1,'a'], ['1', 'b']]

  dicts = [
      {float('NaN'):None, 1:1, 'a':'b', False:True, ():(), ():[],},
      {float('NaN'):None, 1:1, 'a':'b', False:True, ():(), ():[], frozenset():{}},
      {float('NaN'):None, 1:1, 'a':'b', False:True, ():(), ():(), frozenset():{}},
      { False:True, 1:1, 'a':'b', 2:None,():(), ():[], frozenset():{}},
      {'a':'a', 1:3},
      OrderedDict((('a',''), (1,0))),
      ]

  bytes = [ b' 124', b'absd', ]

  mixed = [pandas.DataFrame(), pandas.Series(), complex(1,2), complex(11,0), complex(1),
           frozenset(()), lambda: 1, Sorting.stringSortKey,  Sorting.universalSortKey,
           core, Sorting, math, numpy,
           numpy.array([1.,2.]), numpy.array([[1,2],[3,4]]), numpy.array(['a', 'b', 'c', 'd'],),
           set(), set((1,)), set((1,9,11)),  set((2,1)),
          ]

  pids = [ 'NR:@-.@1', 'NR:@-.@1-1.', 'NR:@-.@1+0.', 'NR:@-.@1+1.', 'NR:@-.@1.', ]


  data1 = (
    ['1st place', '2nd place', '10th place'],
    ['127.0.0.55', '127.0.0.100'],
    ['0.01', '0.1', '1'],
    ['0.501', '0.55'],
    ['CASE', 'SENSITIVE', 'case', 'sensitive'],
    ['image1.jpg', 'image3.jpg', 'image12.jpg', 'image15.jpg'],
    ['Elm2',  'Elm11', 'Elm12', 'elm0', 'elm1', 'elm9', 'elm10','elm13'],
    ['@1.127b..H@2', '@1.127b..H@15', ],
    ['', 'NaN', '-1',  '-1A', '0.0', '1', '2', '15', '3.2e12',  'Inf', 'Ahh', 'b', 'b2', 'bb', 'ciao']
  )

  data2 = (
    [0.01, 0.1, 1],
    [0.501, 0.55],
    [[1,'a'], ['1', 'b'], (1,'a'), ('1', 'b'), b' 124', b'absd', ],
    [0, 1.0, 1.0, lambda:1, ],
    [
      {1:1, 'a':'b', None:None, False:True, ():(), ():{}, frozenset():{}},
      {1:1, 'a':'b', None:None, False:True, ():(), ():[], frozenset():{}},
      {1:1, 'a':'b', None:None, False:True, ():(), ():(), frozenset():{}},
      {1:1, 'a':'b', 2:None, False:True, ():(), ():[], frozenset():{}},
      {'a':'a', 1:3},
      OrderedDict((('a',''), (1,0))),
    ]
  )

  data3 = [0.0, 1, (1+0j), False, (2+3j)]

  data4 = [ None, False, True, float('NaN'), float('-inf'),0.1,  1.0,  float('inf'), '',
     'NaN', '-1', '-1.', '0.0.',  '0.01.', '0.1e-7.', '0.0','0.1e-7', '0.01', '1', '1.0.', '1.','1.0',
      'Infinity', '-Infinity.',  'NaN.',
     ]

  data5 = ['', 'NaN', '-1', '-1A', '0.0', '1', '2', '15', '3.2e12', 'Inf',
           'Ahh', 'b', 'b2', 'b12', 'bb', 'ciao']

  data6 = ['2,500 items', '2,500.1 items', '2.5 items', '3.5 items', '15 items']

  data7 = ['@1.127b-1..H@2', '@1.127b+0..H@2','@1.127b-0..H@2','@1.127b+1..H@2',
           '@1.127b1..H@2', '@1.127b..H@15',]



class StdSortingTest(SortingData):
  
  sortKeys = {
    'universal':Sorting.universalNaturalSortKey,
    'string':Sorting.stringSortKey
  }

  def test_string_sorting_1(self):
    for ll in self.data1:
      ll2 = sorted(list(reversed(ll)), key=self.sortKeys['string'])
      self.assertEqual(ll2, ll)

  def test_string_sorting_5(self):
    ll = self.data5
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['string'])
    self.assertEqual(ll2, ll)

  def test_string_sorting_6(self):
    ll = self.data6
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['string'])
    self.assertEqual(ll2, ll)

  def test_string_sorting_7(self):
    ll = self.data7
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['string'])
    self.assertEqual(ll2, ll)


  def test_mixed_sorting_1(self):
    for ll in self.data1:
      ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
      self.assertEqual(ll2, ll)


  def test_mixed_sorting_2(self):
    for ll in self.data2:
      ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
      self.assertEqual(ll2, ll)

  def test_mixed_sorting_3(self):
    self.assertEqual(sorted(self.data3, key=self.sortKeys['universal'])[:3], [False, 0.0, 1])

  def test_mixed_sorting_4(self):

    ll = self.data4
    ll2 = sorted(list(reversed(self.data4)), key=self.sortKeys['universal'])
    self.assertEqual(ll2[:3], ll[:3])
    self.assertEqual(ll2[4:], ll[4:])
    self.assertTrue(math.isnan(ll2[3]))

  def test_sort_pids(self):
    ll = self.pids
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_specials(self):
    ll = self.specials
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_reals(self):
    ll = self.reals
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_negstrings(self):
    ll = self.negstrings
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_zerostrings(self):
    ll = self.zerostrings
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_posstrings(self):
    ll = self.posstrings
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_strings2(self):
    ll = self.strings2
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_chainCodes(self):
    ll = self.chainCodes
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_sequenceCodes(self):
    ll = self.sequenceCodes
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_sequenceCodes2(self):
    ll = self.sequenceCodes2
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_atomNames(self):
    ll = self.atomNames
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_tuples(self):
    ll = self.tuples
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_lists(self):
    ll = self.lists
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_dicts(self):
    ll = self.dicts
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_mixed(self):
    ll = [float('NaN')] + self.mixed
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])

      # NB the skipped parts sort by id and so cannot be tested properly
    self.assertTrue(math.isnan(ll2[0]))
    self.assertEqual(ll2[7:-7], ll[7:-7])
    testClassNames = ['DataFrame', 'Series', 'complex', 'complex', 'complex', 'frozenset']
    self.assertTrue(tt[0].__class__.__name__ == tt[1] for tt in zip(ll2[1:7], testClassNames))
    self.assertTrue(all(x.__class__.__name__ == 'set' for x in ll2[-4:]))
    self.assertTrue(all(x.__class__.__name__ == 'ndarray' for x in ll2[-7:-4]))



  def test_sort_all_1(self):
    ll = (self.specials + self.reals + self.negstrings + self.zerostrings + self.posstrings
          + self.strings2 + self.dicts + self.lists + self.tuples + self.bytes)
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertTrue(math.isnan(ll2[3]))
    self.assertEqual(ll2[:3], ll[:3])
    self.assertEqual(ll2[4:], ll[4:])

  def test_sort_all_2(self):
    ll = (self.specials + self.reals + self.negstrings + self.zerostrings + self.posstrings
          + self.strings2 + self.dicts + self.lists + self.tuples + self.bytes + self.mixed)
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2[:3], ll[:3])
    self.assertEqual(ll2[4:-len(self.mixed)], ll[4:-len(self.mixed)])
    self.assertTrue(math.isnan(ll2[3]))





class CcpnSortingTest(SortingData):
  
  sortKeys = {
    'universal':CcpnSorting.universalSortKey,
    'string':CcpnSorting.stringSortKey
  }

  # Different sorting order for these examples
  data6 = ['2.5 items', '2,500.1 items', '2,500 items', '3.5 items', '15 items']
  data7 = ['@1.127b-1..H@2', '@1.127b..H@15', '@1.127b+0..H@2','@1.127b-0..H@2','@1.127b+1..H@2',
           '@1.127b1..H@2',]
  pids = [ 'NR:@-.@1-1.', 'NR:@-.@1', 'NR:@-.@1.', 'NR:@-.@1+0.', 'NR:@-.@1+1.',]
  sequenceCodes = ['-1', ' 1', '+1', '1',  '1b', '1.', '2b-11', '2b-2.', '2b-1', '2b', '2b.',
                   '2b+0', '2b-0','2b0',
                   '2b+1', '2b+2', '2b2', '2b@11', '2ba', '15.',  '#1', '#2', '#11-1','#11',
                   '#11+1',  '#105', '@-11', '@-2', '@-1', '@0', '@1', '@2', '@11', '@-', '@@a',
                   '@A']

  sequenceCodes2 = ['-1', '+1', '1', '1b', '2b-11', '2b-2.', '2b-1', '2b', '2b+0', '2b-0',
                   '2b0', '2b+1', '2b+2', '2b2', '2b@11', '2ba',  '#1', '#2', '#11-1', '#11',
                   '#11+1',  '#105', '@-11', '@-2', '@-1', '@0', '@1', '@2', '@11', '@-', '@@a',
                   '@A']

  def test_string_sorting_1(self):
    for ll in self.data1:
      ll2 = sorted(list(reversed(ll)), key=self.sortKeys['string'])
      self.assertEqual(ll2, ll)

  def test_string_sorting_5(self):
    ll = self.data5
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['string'])
    self.assertEqual(ll2, ll)

  def test_string_sorting_6(self):
    ll = self.data6
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['string'])
    self.assertEqual(ll2, ll)

  def test_string_sorting_7(self):
    ll = self.data7
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['string'])
    self.assertEqual(ll2, ll)


  def test_mixed_sorting_1(self):
    for ll in self.data1:
      ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
      self.assertEqual(ll2, ll)


  def test_mixed_sorting_2(self):
    for ll in self.data2:
      ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
      self.assertEqual(ll2, ll)

  def test_mixed_sorting_3(self):
    self.assertEqual(sorted(self.data3, key=self.sortKeys['universal'])[:3], [False, 0.0, 1])

  def test_mixed_sorting_4(self):

    ll = self.data4
    ll2 = sorted(list(reversed(self.data4)), key=self.sortKeys['universal'])
    self.assertEqual(ll2[:3], ll[:3])
    self.assertEqual(ll2[4:], ll[4:])
    self.assertTrue(math.isnan(ll2[3]))

  def test_sort_pids(self):
    ll = self.pids
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_specials(self):
    ll = self.specials
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_reals(self):
    ll = self.reals
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_negstrings(self):
    ll = self.negstrings
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_zerostrings(self):
    ll = self.zerostrings
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_posstrings(self):
    ll = self.posstrings
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_strings2(self):
    ll = self.strings2
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_chainCodes(self):
    ll = self.chainCodes
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_sequenceCodes(self):
    ll = self.sequenceCodes
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_sequenceCodes2(self):
    ll = self.sequenceCodes2
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_atomNames(self):
    ll = self.atomNames
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_tuples(self):
    ll = self.tuples
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_lists(self):
    ll = self.lists
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_dicts(self):
    ll = self.dicts
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2, ll)

  def test_sort_mixed(self):
    ll = [float('NaN')] + self.mixed
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])

      # NB the skipped parts sort by id and so cannot be tested properly
    self.assertTrue(math.isnan(ll2[0]))
    self.assertEqual(ll2[7:-7], ll[7:-7])
    testClassNames = ['DataFrame', 'Series', 'complex', 'complex', 'complex', 'frozenset']
    self.assertTrue(tt[0].__class__.__name__ == tt[1] for tt in zip(ll2[1:7], testClassNames))
    self.assertTrue(all(x.__class__.__name__ == 'set' for x in ll2[-4:]))
    self.assertTrue(all(x.__class__.__name__ == 'ndarray' for x in ll2[-7:-4]))


  def test_sort_all_1(self):
    ll = (self.specials + self.reals + self.negstrings + self.zerostrings + self.posstrings
          + self.strings2 + self.dicts + self.lists + self.tuples + self.bytes)
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertTrue(math.isnan(ll2[3]))
    self.assertEqual(ll2[:3], ll[:3])
    self.assertEqual(ll2[4:], ll[4:])

  def test_sort_all_2(self):
    ll = (self.specials + self.reals + self.negstrings + self.zerostrings + self.posstrings
          + self.strings2 + self.dicts + self.lists + self.tuples + self.bytes + self.mixed)
    ll2 = sorted(list(reversed(ll)), key=self.sortKeys['universal'])
    self.assertEqual(ll2[:3], ll[:3])
    self.assertEqual(ll2[4:-len(self.mixed)], ll[4:-len(self.mixed)])
    self.assertTrue(math.isnan(ll2[3]))
