"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
import operator
import typing
import os
from collections import OrderedDict
from ccpn.util.Logging import getLogger
from ccpn.core.Chain import Chain
from ccpn.core.Residue import Residue
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.core.Sample import Sample
from ccpn.core.Spectrum import Spectrum
from ccpn.core.Substance import Substance
from ccpn.core.Integral import Integral
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.SpectrumHit import SpectrumHit
from ccpn.core.Peak import Peak
from ccpn.core.Multiplet import Multiplet
# from ccpn.core.Integral import Integral
from ccpn.ui._implementation.Strip import Strip


# from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay


SingularOnly = 'singularOnly'
Remove = 'remove'
PCAcomponents = 'pcaComponents'

_currentClasses = {
    SpectrumGroup    : {SingularOnly: True},
    Peak             : {},
    Integral         : {},
    NmrChain         : {},
    NmrResidue       : {},
    NmrAtom          : {},
    Strip            : {SingularOnly: True},
    Chain            : {},
    Residue          : {},
    ChemicalShiftList: {},
    ChemicalShift    : {},
    Sample           : {},
    SpectrumHit      : {SingularOnly: True},
    Substance        : {},
    Multiplet        : {}
    }

_currentExtraFields = {
    'positions'      : {'docTemplate': "last cursor %s"},
    'cursorPositions': {'singularOnly': True, 'docTemplate': 'last cursor %s - (posX,posY) tuple'},
    'axisCodes'      : {'singularOnly': True, 'docTemplate': 'last selected %s'},
    PCAcomponents    : {'docTemplate': 'last selected %s, of any obj kind'},
    }

# Fields in current (there is a current.xyz attribute with related functions
# for every 'xyz' in fields
_fields = [x._pluralLinkName for x in _currentClasses] + list(_currentExtraFields.keys())


def noCap(string):
    """return de-capitalised string"""
    if len(string) <= 0: return string
    return string[0].lower() + string[1:]


class Current:
    # create the doc-string dynamically from definitions above;
    # cannot do newlines as Python console falls over when querying using the current? syntax (too many newlines?)

    #: Short class name, for PID.
    shortClassName = 'CU'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Current'

    _parentClass = None  # For now, setting to Framework generates cyclic imports

    #: Name of plural link to instances of class
    _pluralLinkName = None

    #: List of child classes.
    _childClasses = []

    ll = []
    for cls in sorted(_currentClasses.keys(), key=operator.attrgetter('className')):
        ss = noCap(cls.className)
        ll.append('\n%s (last selected %s)' % (ss, ss))
        if not _currentClasses[cls].get('singularOnly'):
            ss = noCap(cls._pluralLinkName)
            ll.append('%s (all selected %s)' % (ss, ss))

    for field in sorted(_currentExtraFields.keys()):
        ss = field[:-1]
        dd = _currentExtraFields[field]
        ll.append('\n%s (%s)' % (ss, dd['docTemplate'] % ss))
        if not dd.get('singularOnly'):
            ss = field
            ll.append('%s (%s)' % (ss, dd['docTemplate'] % ss))

    # Have the doc string reflect all defined curent attributes
    __doc__ = (
            """The current object gives access to the collection of active or selected objects and values.
          
          Currently implemented:
          %s
          
          Use print(current) to get a list of attribute, value pairs')
          """ % '; '.join(ll)
    )

    def __init__(self, project):
        # initialise non-=auto fields
        self._project = project
        self._pid = '%s:current' % self.shortClassName

        for field in _fields:
            setattr(self, '_' + field, [])

        # The notifiers the Current instance sets to be updated on project changes
        self._notifiers = None
        self._registerNotifiers()

        # The Current notifier mechanism
        notifies = self._notifies = {}  # The notifier mechanism of current: a dict of (field, list-of-functions) pairs
        for field in _fields:
            notifies[field] = []
        self._blanking = 0  # Notifier blanking

        # GWV 20181122: deactivated
        # self.registerNotify(self._updateSelectedPeaks, 'peaks')  # Optimization; see below

    @property
    def pid(self):
        return self._pid

    @property
    def project(self):
        """Project attached to current"""
        return self._project

    def registerNotify(self, notify, field):
        """Register notifier function 'notify' to be called on field 'field'

        Return notify

        E.g. current.registerNotify(highlightSelectedPeaks, 'peaks')
        Where highlightSelectedPeaks is a function that takes a list of peaks as its only input

        Notifiers are attached to the Current OBJECT, not to the class
        They are therefore removed when a new project is created/loaded
        Otherwise it is the responsibility of the adder to remove them when no longer relevant
        for which the notifier function object must be kept around.
        The function is attached to the field and is executed after the field value changes
        In practice this goes through the setter for (the equivalent of) Current.spectra
        The notifier function is passed the new value of the field as its only parameter.
        If you need a graphics object (e.g. a module) you must make and register a bound method
        on the module.
        """

        self._notifies[field].append(notify)
        return notify

    def unRegisterNotify(self, notify, field):
        """Remove notifier for field"""
        try:
            callbacks = self._notifies[field]
        except:
            KeyError('field "%s" not found; unable to unRegister from current' % field)

        try:
            callbacks.remove(notify)
        except:
            IndexError('callback not found; unable to unRegister from current')

    def increaseBlanking(self):
        self._blanking += 1

    def decreaseBlanking(self):
        if self._blanking > 0:
            self._blanking -= 1
        else:
            raise RuntimeError('Error decreasing blanking; already at 0')

    # GWV 20181122: deactivated
    # def _updateSelectedPeaks(self, currentPeaks):
    #     """ Update selected status of peaks.
    #     This attribute is redundant information but is done for time efficiency in drawing,
    #     so you don't have to check whether a peak is in a list / set but just check the attribute.
    #     """
    #     for peakList in self.project.peakLists:
    #         for peak in peakList.peaks:
    #             peak._isSelected = False
    #
    #     for peak in currentPeaks:
    #         peak._isSelected = True

    def __str__(self):
        return '<Current>'

    def asString(self):
        """
        Return string representation of self listing all attribute, value pairs
        """
        ll = []
        for cls in sorted(_currentClasses.keys(), key=operator.attrgetter('className')):
            ss = noCap(cls.className)
            ll.append((ss, getattr(self, ss)))
            if not _currentClasses[cls].get('singularOnly'):
                ss = noCap(cls._pluralLinkName)
                ll.append((ss, getattr(self, ss)))

        for field in sorted(_currentExtraFields.keys()):
            ss = field[:-1]
            ll.append((ss, getattr(self, ss)))
            if not _currentExtraFields[field].get('singularOnly'):
                ss = field
                ll.append((ss, getattr(self, ss)))

        maxlen = max((len(tt[0]) for tt in ll))
        fmt = 'current.%-' + str(maxlen) + 's : %s'
        # fmt = "current.%%-%s : %%s" % maxlen
        return '\n'.join(fmt % tt for tt in ll)

    @property
    def state(self):
        """
        Returns a storable representation of current objs in a ordered Dict.
        Keys the class name, values: pids, float/int or Nones. [] for plural cases.
        Used to dump in json file to save a restore the state when opening/closing a project
        """
        return self._state

    @state.getter
    def _state(self):
        """
        Return a storable representation of self listing all attribute, value pairs
        """
        ll = []
        for cls in sorted(_currentClasses.keys(), key=operator.attrgetter('className')):
            ss = noCap(cls.className)
            item = getattr(self, ss)
            if item is not None:
                pid = item.pid
                ll.append((ss, pid))
            else:
                ll.append((ss, item))

            if not _currentClasses[cls].get('singularOnly'):
                ss = noCap(cls._pluralLinkName)
                objs = getattr(self, ss)
                pids = []
                for obj in objs:
                    if obj is not None:
                        pids.append(obj.pid)
                ll.append((ss, pids))

        # for field in sorted(_currentExtraFields.keys()):
        #   ss = field[:-1]
        #   ll.append((ss, getattr(self, ss)))
        #   if not _currentExtraFields[field].get('singularOnly'):
        #     ss = field
        #     ll.append((ss, getattr(self, ss)))

        return OrderedDict(ll)

    def _restoreFromState(self, state):
        '''

        :param state: current state as dict.
        :return: Restores first the singular classes if
        '''
        sortedState = OrderedDict(state)
        try:
            pluralClasses = [cls._pluralLinkName for cls in _currentClasses if
                             not _currentClasses[cls].get(SingularOnly)]
            singularClasses = [cls.className.lower() for cls in _currentClasses if
                               _currentClasses[cls].get(SingularOnly)]
            for attName, values in sortedState.items():
                if values is None:
                    continue
                if attName in singularClasses:
                    if isinstance(values, str):
                        obj = self.project.getByPid(values)
                        setattr(self, attName, obj)
                if attName in pluralClasses:
                    if isinstance(values, (list, tuple)):
                        objs = [self.project.getByPid(value) for value in values]
                        for value in values:
                            if isinstance(value, str):
                                obj = self.project.getByPid(value)
                                if obj is not None:
                                    objs.append(obj)
                        setattr(self, attName, objs)
        except Exception as e:
            getLogger().debug('Impossible to restore current. %s' % e)

    @classmethod
    def _addClassField(cls, param):
        """Add new 'current' field with necessary function for input
        param (wrapper class or field name)"""

        if isinstance(param, str):
            plural = param
            singular = param[:-1]  # It is assumed that param ends in plural 's'
            singularOnly = _currentExtraFields[param].get('singularOnly')
            enforceType = None
        else:
            # param is a wrapper class
            plural = param._pluralLinkName
            singular = param.className
            singular = singular[0].lower() + singular[1:]
            singularOnly = _currentClasses[param].get('singularOnly')
            enforceType = param

        # getter function for _field; getField(obj) returns obj._field:
        getField = operator.attrgetter('_' + plural)

        # getFieldItem(obj) returns obj[field]
        getFieldItem = operator.itemgetter(plural)

        def setField(self, value, plural=plural, enforceType=enforceType):
            # setField(obj, value) sets obj._field = value and calls notifiers

            if len(set(value)) != len(value):
                # ejb - remove duplicates here
                tempList = []
                for inL in value:
                    if inL not in tempList:
                        tempList.append(inL)
                value = tempList
                set(value)
                # raise ValueError( "Current %s contains duplicates: %s" % (plural, value))

            attributeName = '_' + plural
            oldValue = getattr(self, attributeName)

            if value != oldValue:
                if enforceType and any(x for x in value if not isinstance(x, enforceType)):
                    raise ValueError("Current values for %s must be of type %s" % (plural, enforceType))
                setattr(self, attributeName, value)

                # Trigger the notifiers
                if self._blanking == 0:
                    funcs = getFieldItem(self._notifies) or ()  # getFieldItem(obj) returns obj[field]
                    for func in funcs:
                        func(value)

        # define singular properties
        def getter(self):
            ll = getField(self)
            return ll[-1] if ll else None

        def setter(self, value):
            setField(self, [value])

        setattr(cls, singular, property(getter, setter, None, "Current %s" % singular))

        if not singularOnly:
            # define the plural properties
            def getter(self):
                return tuple(getField(self))

            def setter(self, value):
                setField(self, list(value))

            setattr(cls, plural, property(getter, setter, None, "Current %s" % plural))

            # define the add'Field' method
            def adder(self, value):
                """Add %s to current.%s""" % (singular, plural)
                values = getField(self)
                if value not in values:
                    setField(self, values + [value])

            setattr(cls, 'add' + singular[0].upper() + singular[1:], adder)

            # define the remove'Field' method
            def remover(self, value):
                """Remove %s from current.%s""" % (singular, plural)
                values = getField(self)
                if value in values:
                    values.remove(value)
                setField(self, values)

            setattr(cls, 'remove' + singular[0].upper() + singular[1:], remover)

            # define the clear'Field' method
            def clearer(self):
                """Clear current.%s""" % plural
                setField(self, [])

            setattr(cls, 'clear' + plural[0].upper() + plural[1:], clearer)

        # if not isinstance(param, str):
        #     # param is a class - Add notifiers for deleted objects
        #     def cleanup(self: AbstractWrapperObject):
        #         current = self._project._appBase.current
        #         if current:
        #             fieldData = getField(current)
        #             if self in fieldData:
        #                 fieldData.remove(self)
        #
        #     cleanup.__name__ = 'current_%s_deletion_cleanup' % singular
        #     #
        #     param._setupCoreNotifier('delete', cleanup)

    def _cleanUp(self, cDict, fieldName):
        "Callback for deletion of an object in the project"
        from ccpn.core.lib.Notifiers import Notifier  ## needs to be local to avoid circular imports

        self.increaseBlanking()
        obj = cDict[Notifier.OBJECT]
        values = getattr(self, fieldName)
        if values and obj in values:
            values.remove(obj)
        self.decreaseBlanking()

    def _registerNotifiers(self):
        """Registers the notifiers to cleanup current.fieldName on deletion of an object
        """
        from ccpn.core.lib.Notifiers import Notifier  ## needs to be local to avoid circular imports

        self._notifiers = []
        for cls in _currentClasses:
            fieldName = '_' + cls._pluralLinkName
            ntf = Notifier(self.project, triggers=[Notifier.DELETE], targetName=cls.className,
                           callback=self._cleanUp, debug=False, fieldName=fieldName)  # fieldName is passed on to the callback function
            self._notifiers.append(ntf)

    def _unregisterNotifiers(self):
        """Unregisters the notifiers
        CCPNINTERNAL: used in Framework._closeProject
        """
        for ntf in self._notifiers:
            ntf.unRegister()

    def _dumpStateToFile(self, statePath):
        try:
            path = os.path.join(statePath, self.className)
            file = open(path, "w")
            json.dump(self.state, file, sort_keys=False, indent=2, )
            file.close()
        except Exception as e:
            getLogger().debug('Impossible to create a Current File.', e)

    def _createStateFile(self, statePath):
        path = os.path.join(statePath, self.className)
        if not os.path.exists(path):
            self._dumpStateToFile(statePath)

        return path

    def _restoreStateFromFile(self, statePath):
        """
        restore current from the default File in the project directory
        """
        try:
            path = self._createStateFile(statePath)
            if path:
                with open(path) as fp:
                    state = json.load(fp)
                    if state:
                        self._restoreFromState(state)

        except Exception as e:
            getLogger().debug('No state found. %s' % e)


# Add fields to current
for cls in _currentClasses:
    Current._addClassField(cls)
for field in _currentExtraFields:
    Current._addClassField(field)
