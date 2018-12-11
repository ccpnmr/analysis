"""
Notifiers
=========

To keep some system in a large and complex program, the CcpNmr suite is divided between
the data layer and the presentation layer. All changes happen in the data layer, and the
presentation layer simply reflects them. And since the data can be changed in many different
ways, we have a mechanism to pass information about the change to presentation code that needs
to change:   Notifiers.


API level notifiers
====================

The lowest level of notifiers are attached to the API data layer and pass information up
to the wrapper layer of objects that we normally interact with. These functions make sure
that entries for the wrapper objects are created and removed as necessary, that child
objects are renamed when parent objects are, etc. The API notifiers form a
separate system, that allows very detailed control over what changes cause what effects.
Only the people who implement the wrapper layer need to interact with API notifiers.
Examples can be found in many of the ccpn wrappeer classes.


Normal notifiers
================

When a wrapper object is created, deleted, undeleted, renamed or changed, the housekeeping code that
keeps things consistent also executes a list of notifier functions. To make something happen in
these cases, you must write a function to be notified and register it so that it is executed at the
appropriate time

Notifiers of type 'create', 'delete', and 'change' are called with one parameter, namely the object
that is created/undeleted/deleted/changed. 'delete' notifiers are called after the object is deleted
but you can still access the object id and pid in the normal manner.

Notifiers of type 'rename' are called with two parameters: the object renamed, and the pid before
renaming.

There is one more type of notifier, that is called when an object-to-object crosslink is changed.
One example is the Spectrum <-> SpectrumGroup crosslink. These notifiers are called with only
one parameter: the project (so all you know is that a spectrum-spectrumGroup link somewhere has
changed. NB: Crosslink notifiers are only called when a crosslink is changed *directly*. Changes
in the link caused by deletion or creation of objects on either side do not trigger the notifiers.
It is up to the programmer to set the appropriate notifiers.


Registering notifiers
=====================

There are two ways of registering notifiers:

If the notifier does not need to know about specific objects, e.g. if it just says "When a spectrum
changes colour, find and refresh all displays that show the spectrum", you can use the
setupCoreNotifier() function, that is defined in the AbstractWrapperObject class and so is
accessible for any object (see  the function definition for details). This function MUST be called
from text of the python file (i.e. NOT from inside a function), so that it is executed only once,
when the file is loaded. Notifiers defined in this way remain registered and can not be removed.
This is actually the simplest way of registering notifiers, but because of this property this
option is mainly for  systems programmers. Examples can be found in many of the wrapper classes.

If you want to make refresh operations on one of your own objects - e.g. if you make your own peak
table and want to  make sure it is kept up to date, you must use the other notifier system by
calling the project.registerNotifier() function (see documentation for details). These require a
little more upkeep. If your personal peak table is deleted, notifiers that refresh it can no longer
be executed without causing errors. It is therefore your responsibility to keep track of the
notifier, and to remove the it when it is no longer relevant, using the project.removeNotifier()
function. As part of this you must make sure (using popup close functions, try-finally statements,
etc.) that the notifier is removed even if the program throws an error. The notifiers are
automatically removed when you close the project, though. For examples of this kind of notifier
see the ccpn/testing/Test_Notifier module, or the SideBar.setProject() function.


Multiple notifiers
==================

Because the notifier system is relatively imprecise, you may need to call the same refresh function
from different starting points, and you may often end up refreshing a lot of things every time
(e.g.) a single peak changes. That can end up slowing things down a lot. In order to avoid this,
we have a mechanism for grouping notifier calls. The registerNotifier() function returns a unique
object that identifies the notifier (actually the function object). If you want to call the same
function in other circumstances, you can use the project.duplicateNotifier() to register the same
notifier in several places. This is especially useful if you register the notifier with
onceOnly=True. When people start an activity that is likely to trigger a lot of notifiers -
peak picking, say - you can suspend notifier execution with the project.suspendNotification()
command. Notifiers are then accumulated in a list, and executed once you give the
project.resumeNotification() command. But notifiers that are registered as onceOnly=True are only
executed once when notification is resumed, no matter how many times they have been triggered.
In that way you need only refresh your peak table once, even when you pick 500 peaks at a time.


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
__dateModified__ = "$dateModified: 2017-07-07 16:32:34 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import unittest
from ccpn.core.testing.WrapperTesting import WrapperTesting

def notifyfunc(obj, value=None, ll=None):
  if not hasattr(obj, '_test_notifier_list'):
     obj._test_notifier_list = ll
  obj._test_notifier_list.append(value)
  # print('TestFunc', len(ll), ll[-1], value)

def notifyrenamefunc(obj, oldPid, value=None, ll=None):
  if not hasattr(obj, '_test_notifier_list'):
     obj._test_notifier_list = ll
  obj._test_notifier_list.append(value)
  # print('TestFunc', len(ll), ll[-1], value, oldPid)


class NotificationTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_notifiers_1(self):
    project = self.project
    ll = []
    not1 = project.registerNotifier('Note','create',  notifyfunc,
                              parameterDict={'value':'createx', 'll':ll})
    not2 = project.registerNotifier('Note','delete',  notifyfunc,
                              parameterDict={'value':'deletex', 'll':ll})
    not3 = project.registerNotifier('Note','change',  notifyfunc,
                              parameterDict={'value':'changex', 'll':ll})

    registered = project._context2Notifiers
    self.assertEqual(registered.get(('Note','create')), {not1:False})
    self.assertEqual(registered.get(('Note','delete')), {not2:False})
    self.assertEqual(registered.get(('Note','change')), {not3:False})

    project.newUndoPoint()

    note1 = project.newNote(name='test1')
    note2 = project.newNote(name='test2')

    project._undo.undo()
    project._undo.undo()
    project._undo.redo()
    project._undo.redo()
    self.assertEqual(ll, ['createx', 'createx', 'deletex', 'deletex', 'createx', 'createx'])
    project.newUndoPoint()
    note1.text = 'Wauuhhhw'
    note2.text = 'Howwwll!'
    project._undo.undo()
    self.assertIsNone(note1.text)
    self.assertIsNone(note2.text)
    project._undo.redo()
    self.assertEqual(note1.text, 'Wauuhhhw')
    self.assertEqual(note2.text, 'Howwwll!')
    self.assertEqual(ll,['createx', 'createx', 'deletex', 'deletex', 'createx', 'createx',
                         'changex', 'changex', 'changex', 'changex', 'changex', 'changex'])

    project.removeNotifier(not1)
    project.unRegisterNotifier('Note','change', not3)
    project.unRegisterNotifier('Note','delete', not2)
    self.assertEqual(registered.get(('Note','create')), {})
    self.assertEqual(registered.get(('Note','delete')), {})
    self.assertEqual(registered.get(('Note','change')), {})


  def test_notifiers_multiple(self):
    project = self.project
    ll = []
    not1 = project.registerNotifier('Note','create',  notifyfunc,
                              parameterDict={'value':'createx', 'll':ll}, onceOnly=True)
    not2 = project.registerNotifier('Note','delete',  notifyfunc,
                              parameterDict={'value':'deletex', 'll':ll}, onceOnly=True)
    registered = project._context2Notifiers
    self.assertEqual(registered.get(('Note','create')), {not1:True})
    self.assertEqual(registered.get(('Note','delete')), {not2:True})

    project.newUndoPoint()

    note1 = project.newNote(name='test1')
    note2 = project.newNote(name='test2')

    project._undo.undo()
    project._undo.undo()
    project._undo.redo()
    project._undo.redo()
    self.assertEqual(ll, ['createx', 'createx', 'deletex', 'deletex', 'createx', 'createx'])
    project.newUndoPoint()
    note1.text = 'Wauuhhhw'
    note2.text = 'Howwwll!'
    project._undo.undo()
    self.assertIsNone(note1.text)
    self.assertIsNone(note2.text)
    project._undo.redo()
    self.assertEqual(note1.text, 'Wauuhhhw')
    self.assertEqual(note2.text, 'Howwwll!')
    self.assertEqual(ll,['createx', 'createx', 'deletex', 'deletex', 'createx', 'createx',
                         'createx', 'createx', 'createx', 'createx', 'createx', 'createx'])

    project.removeNotifier(not1)
    self.assertEqual(registered.get(('Note','create')), {})
    self.assertEqual(registered.get(('Note','delete')), {not2:True})
    self.assertEqual(registered.get(('Note','change')), {})
    project.unRegisterNotifier('Note','delete', not2)
    self.assertEqual(registered.get(('Note','create')), {})
    self.assertEqual(registered.get(('Note','delete')), {})
    self.assertEqual(registered.get(('Note','change')), {})

  # NOtifier suspension has been temporarily disabled,
  # due to problems with suspended delete notifiers.
  # This test should be reinstated, and the supension should be reinstated and fixed
  @unittest.skip
  def test_notifiers_suspend(self):
    project = self.project
    ll = []
    not1 = project.registerNotifier('Note','create',  notifyfunc,
                              parameterDict={'value':'createx', 'll':ll}, onceOnly=True)
    not2 = project.registerNotifier('Note','delete',  notifyfunc,
                              parameterDict={'value':'deletex', 'll':ll}, onceOnly=True)
    registered = project._context2Notifiers
    project.suspendNotification()
    project.newUndoPoint()

    note1 = project.newNote(name='test1')
    note2 = project.newNote(name='test2')

    project._undo.undo()
    project._undo.redo()
    project.newUndoPoint()
    note1.text = 'Wauuhhhw'
    note2.text = 'Howwwll!'
    project._undo.undo()
    project._undo.redo()

    # NBNB This currently fails, because we have temporarily disabled notification suspension
    self.assertEqual(ll, [])
    project.resumeNotification()
    self.assertEqual(ll, ['deletex',  'createx'])

    project.removeNotifier(not1)
    project.unRegisterNotifier('Note','delete', not2)
    self.assertEqual(registered.get(('Note','create')), {})
    self.assertEqual(registered.get(('Note','delete')), {})



  def test_notifiers_rename(self):

    project = self.project
    ll = []

    not1 = project.registerNotifier('Spectrum','create',  notifyfunc,
                              parameterDict={'value':'newSpectrum', 'll':ll})
    not2 = project.registerNotifier('Spectrum','delete',  notifyfunc,
                              parameterDict={'value':'delSpectrum', 'll':ll})
    not3 = project.registerNotifier('Spectrum','change',  notifyfunc,
                              parameterDict={'value':'modSpectrum', 'll':ll})
    not4 = project.registerNotifier('PeakList','create',  notifyfunc,
                              parameterDict={'value':'newPeakList', 'll':ll})
    not5 = project.registerNotifier('PeakList','delete',  notifyfunc,
                              parameterDict={'value':'delPeakList', 'll':ll})
    not6 = project.registerNotifier('PeakList','change',  notifyfunc,
                              parameterDict={'value':'modPeakList', 'll':ll})
    not7 = project.registerNotifier('Peak','create',  notifyfunc,
                              parameterDict={'value':'newPeak', 'll':ll})
    not8 = project.registerNotifier('Peak','delete',  notifyfunc,
                              parameterDict={'value':'delPeak', 'll':ll})
    not9 = project.registerNotifier('Peak','change',  notifyfunc,
                              parameterDict={'value':'modPeak', 'll':ll})
    not10 = project.registerNotifier('Spectrum','rename',  notifyrenamefunc,
                              parameterDict={'value':'renameSpectrum', 'll':ll})
    not11 = project.registerNotifier('PeakList','rename',  notifyrenamefunc,
                              parameterDict={'value':'renamePeakList', 'll':ll})
    not12 = project.registerNotifier('Peak','rename',  notifyrenamefunc,
                              parameterDict={'value':'renamePeak', 'll':ll})
    not1 = project.registerNotifier('Spectrum','create',  notifyfunc,
                              parameterDict={'value':'newSpectrum2', 'll':ll})

    spectrum = project.createDummySpectrum(axisCodes=('Fn', 'Nf'), name='HF-hsqc')
    peakList = spectrum.peakLists[0]
    peak1 = peakList.newPeak(ppmPositions=(1.0,2.0))
    self.assertEqual(ll, ['newSpectrum', 'newSpectrum2', 'newPeakList', 'newPeak'])
    self.assertEqual(peak1.pid, 'PK:HF-hsqc.1.1')
    spectrum.rename('HF-copy')
    self.assertEqual(ll, ['newSpectrum', 'newSpectrum2', 'newPeakList', 'newPeak',
                          'modSpectrum', 'renameSpectrum', 'renamePeakList', 'renamePeak'])
    self.assertEqual(spectrum.pid, 'SP:HF-copy')
    self.assertEqual(peakList.pid, 'PL:HF-copy.1')
    self.assertEqual(peak1.pid, 'PK:HF-copy.1.1')
    self.assertEqual(peak1.position, (1.0,2.0))
    self.assertEqual(spectrum.referencePoints, (1.0,1.0))
    spectrum.referencePoints = (11.,11.)
    self.assertEqual(peak1.position, (11.0,12.0))
    spectrum.delete()

    self.assertEqual(ll[:-3],['newSpectrum', 'newSpectrum2', 'newPeakList', 'newPeak',
                         'modSpectrum', 'renameSpectrum', 'renamePeakList', 'renamePeak',
                         'modPeak', 'modSpectrum', 'modPeak', 'modSpectrum',])
    # NB cascading object deletions do not happen in reproducible order
    self.assertEqual(set(ll[-3:]), {'delSpectrum','delPeak', 'delPeakList'})
    self.assertEqual(spectrum.pid, 'SP:HF-copy-Deleted')
    self.assertEqual(peakList.pid, 'PL:HF-copy.1-Deleted')
    self.assertEqual(peak1.pid, 'PK:HF-copy.1.1-Deleted')


  def test_notifiers_crosslink(self):

    project = self.project
    ll = []

    not1 = project.registerNotifier('Spectrum','change',  notifyfunc,
                              parameterDict={'value':'modSpectrum', 'll':ll})
    not2 = project.registerNotifier('SpectrumGroup','change',  notifyfunc,
                              parameterDict={'value':'modSpectrumGroup', 'll':ll})
    not3 = project.registerNotifier('Spectrum','rename',  notifyrenamefunc,
                              parameterDict={'value':'renameSpectrum', 'll':ll})
    not4 = project.registerNotifier('SpectrumGroup','rename',  notifyrenamefunc,
                              parameterDict={'value':'renameSpectrumGroup', 'll':ll})
    not5 = project.registerNotifier('SpectrumGroup','Spectrum',  notifyfunc,
                              parameterDict={'value':'modLink', 'll':ll})
    spectrum = project.createDummySpectrum(axisCodes=('Fn', 'Nf'), name='HF-hsqc')
    spectrum2 = project.createDummySpectrum(axisCodes=('Hc', 'Ch'), name='HC-hsqc')
    spectrumGroup = project.newSpectrumGroup(name='Groupie')
    spectrumGroup2 = project.newSpectrumGroup(name='Sloupie')
    spectrumGroup.spectra = (spectrum,)
    self.assertEquals(ll, ['modSpectrumGroup', 'modLink'])
    spectrumGroup.spectra = ()
    self.assertEquals(ll, ['modSpectrumGroup', 'modLink', 'modSpectrumGroup', 'modLink'])
    del ll[:]
    self.assertFalse(bool(spectrum.spectrumGroups))
    tt = (spectrumGroup,)
    spectrum.spectrumGroups = tt
    self.assertEquals(ll, ['modSpectrum', 'modLink'])
    spectrum.rename('HF-copy')
    self.assertEquals(ll, ['modSpectrum', 'modLink', 'modSpectrum', 'renameSpectrum'])
    del ll[:]
    spectrum.spectrumGroups = (spectrumGroup, spectrumGroup2)
    self.assertEquals(ll, ['modSpectrum', 'modLink'])
    spectrumGroup.delete()
    self.assertEquals(ll, ['modSpectrum', 'modLink'])
    spectrum.spectrumGroups = ()
    self.assertEquals(ll, ['modSpectrum', 'modLink', 'modSpectrum', 'modLink'])
    spectrumGroup3 = project.newSpectrumGroup(name='Heapie', spectra=(spectrum, spectrum2))
    self.assertEquals(ll, ['modSpectrum', 'modLink', 'modSpectrum', 'modLink'])

