"""
Module for generic merging of data model objects

Transfers simple and link attributes from the source object to target object
Does not transfer derived, automatic or immutable attributes
Links will be transferred where possible
Where necessary the Api is bypassed

Logical analysis and design by R.H. Fogh

Coding and testing by T.J. Stevens

Definitions:
Objects targetObj and sourceObj of class O
link O.a (a) to class A, with backlink A.o ( o)

A note on checks:
Where the API is bypassed, the function does validity checks at each step,
and rolls back the last step if the checks fail.
The checks are done on sourceObj, targetObj, objects on the other end of
links, and the parents of the latter. The check on parents is done because
this includes a check on the keys of the children - the merge cannot change
the keys of either source or target, but can change the key of linked-to objects.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-09-06 17:58:20 +0100 (Mon, September 06, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2020-07-22 08:30:58 +0000 (Wed, July 22, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from ccpnmodel.ccpncore.memops.metamodel import Constants as metaConstants
from ccpnmodel.ccpncore.memops.ApiError import ApiError
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil
from ccpn.core.lib.ContextManagers import undoStackBlocking

_OVERRIDE = 'override'


def _setDict(dd, oldKey, newKey, attrObj):
    """Undo/redo method to delete/recover item from dict
    """
    del dd[oldKey]
    dd[newKey] = attrObj


def _setOverride(root, value):
    root.__dict__['override'] = value


def _changeDict(targetObj, attrName, sourceObj, parentName, topObj):
    """Function to undo/redo dict changes in api
    """
    targetObj.__dict__[attrName] = oo = sourceObj.__dict__[attrName]
    sourceObj.__dict__[attrName] = None
    oo.__dict__[parentName] = targetObj
    oo.__dict__['topObject'] = topObj


def _changeDictDel(targetDd, nextSerial, oo, sourceDd, parentName, targetObj, topObj):
    """Function to undo/redo dict changes in api with delete
    """
    targetDd[nextSerial] = oo
    del sourceDd[nextSerial]
    oo.__dict__[parentName] = targetObj
    oo.__dict__['topObject'] = topObj


def _setSerial(targetObj, attrName, nextSerial):
    """Function to undo/redo dict serial changes in api
    """
    targetObj.__dict__['_serialDict'][attrName] = nextSerial


def mergeObjects(project, sourceObj, targetObj, _useV3Delete=False, _mergeFunc=None):
    """Merges sourceObj into targetObj, deleting sourceObj.
    Attributes and links from sourceObj are added to targetObj
    provided 1) that they are not there already, and
    2) that there is room.

    WARNING this function bypasses the API.

    WARNING Merging objects with child links or frozen links is NOT undoable
     and undo stack is cleared

    WARNING, integrated update operations, e.g. Chemical Shift averaging
    and notifiers are NOT reliably performed during merging and must be
    handled by the callign function

    WARNING This function just might leave the data in an illegal state
    The function performs a number of checks for each individual change.
    If a check fails, the latest change is undone before the error exit,
    in an attempt to leave the data in a state that is legal. Note that only
    the latest change is undone - in case of error the data state will not be
    brought back to the state from before the execution of the command.
    Note that sourceObj is likely to be in an illegal state during execution,
    so that an error may well leave sourceObj in an illegal state. If this happens,
    deleting sourceObj may bring the data back to a legal state, and is unlikely
    to cause further problems.
    In spite of the checks, some objects (not limited to sourceObj and targetObj)
    may be left in an illegal state, even if no error is raised.
    It is recommended to use this function with caution,
    and to run checkAllValid after it has been used.  """

    #same class check
    if sourceObj.qualifiedName != targetObj.qualifiedName:
        return

    #ATTRIBUTES:
    #Objects targetObj, sourceObj, with attribute a

    # with undoStackBlocking() as addUndoItem:

    objClass = targetObj.metaclass

    for a in objClass.getAllAttributes():
        attrName = a.name

        if a.isDerived or a.isAutomatic or a.changeability == metaConstants.frozen:
            continue

        elif a.hicard == a.locard:
            continue

        elif a.hicard == 1:
            if targetObj.__dict__[attrName] is None:
                # undo/redo
                _newVal = sourceObj.__dict__[attrName]
                if _newVal != None:
                    # addUndoItem(undo=partial(setattr, targetObj, attrName, None),
                    #             redo=partial(setattr, targetObj, attrName, _newVal))
                    setattr(targetObj, attrName, _newVal)

        else:
            # find add operation
            addfunc = getattr(targetObj, 'add' + metaUtil.upperFirst(a.baseName))
            # _removefunc = getattr(targetObj, 'remove' + metaUtil.upperFirst(a.baseName))

            # This is OK, as we iterate over list2 but modify list1
            attrList1 = targetObj.__dict__[attrName]
            attrList2 = sourceObj.__dict__[attrName]

            if a.isUnique:
                # no duplicates = might be list or set
                if a.hicard > 1:
                    nSpaces = max(0, a.hicard - len(attrList1))
                else:
                    nSpaces = -1

                for aVal in attrList2:
                    if nSpaces == 0:
                        break
                    else:
                        nSpaces -= 1
                        addfunc(aVal)
                        # # undo/redo
                        # addUndoItem(undo=partial(_removefunc, aVal),
                        #             redo=partial(addfunc, aVal))

            else:
                # might have duplicates (and must be an internal list)
                for aVal in attrList2:
                    if len(attrList1) >= a.hicard and a.hicard != metaConstants.infinity:
                        break
                    # keep adding while there is room
                    if attrList1.count(aVal) < attrList2.count(aVal):
                        addfunc(aVal)
                        # # undo/redo
                        # addUndoItem(undo=partial(_removefunc, aVal),
                        #             redo=partial(addfunc, aVal))

    #LINKS:
    niceLinks = []
    nastyLinks = []
    childLinks = []
    for a in objClass.getAllRoles():

        # select links and how to treat them

        if a.hicard == a.locard or a.isDerived or a.isAutomatic:
            continue

        if a.changeability == metaConstants.frozen:
            continue
            # This is probably right; it could be changed if we bypassed the API.

        o = a.otherRole

        if a.hierarchy == metaConstants.child_hierarchy:
            childLinks.append(a)

        elif o is None or o.changeability != metaConstants.frozen:
            # links that can be handled without bypassing API
            niceLinks.append(a)
        else:
            # links that require bypassing API
            nastyLinks.append(a)

    for a in niceLinks:
        # links that can be handled without bypassing API

        linkName = a.name
        o = a.otherRole
        if o is not None:
            backName = o.name
            #print linkName, a.locard, a.hicard, o.locard, o.hicard

        if o is None or o.hicard != o.locard:
            #
            #print "C3", linkName
            #
            # NB this does NOT break API
            #
            # We are setting/adding/removing from the .a side.
            # if o is None there will be no problems.
            # If o.hicard == 1, attrObj.o can be overwritten
            # Otherwise, as o.hicard != o.locard it will always be possible either to
            # remove sourceObj from attrObj or to add targetObj to attrObj
            # regardless of the exact cardinalities and of len(attrObj.o)

            if a.hicard == 1:
                #assert a.locard == 0
                #
                # there will be no problems on the source/target side as we only
                # make changes when the link is unset in the target

                # Whatever the number of objects, you will either be able to
                # remove sourceObj from attrObj or to add targetObj.
                #
                if getattr(targetObj, linkName) is None:
                    attrObj = getattr(sourceObj, linkName)
                    try:
                        setattr(sourceObj, linkName, None)
                        # # undo/redo
                        # addUndoItem(undo=partial(setattr, sourceObj, linkName, attrObj),
                        #             redo=partial(setattr, sourceObj, linkName, None))
                    except:
                        pass
                    setattr(targetObj, linkName, attrObj)
                    # # undo/redo
                    # addUndoItem(undo=partial(setattr, targetObj, linkName, None),
                    #             redo=partial(setattr, targetObj, linkName, attrObj))

            else:
                # There will be no problems on the attrObj side (see above).
                # On the source/target side we will get the desired result as
                # the API simply passes if you try to add an existing object,
                # It also deletes the old link to sourceObj where appropriate

                # find add operation
                ss = metaUtil.upperFirst(a.baseName)
                addfunc = getattr(targetObj, 'add' + ss)
                removefunc = getattr(sourceObj, 'remove' + ss)
                # _addfunc = getattr(sourceObj, 'add' + ss)
                # _removefunc = getattr(targetObj, 'remove' + ss)

                # NB we cannot use the raw list as we modify it during the loop
                for attrObj in getattr(sourceObj, linkName):

                    try:
                        removefunc(attrObj)
                        # # undo/redo
                        # addUndoItem(redo=partial(removefunc, attrObj),
                        #             undo=partial(_addfunc, attrObj))
                    except ApiError:
                        pass
                        #print 'Failed to remove %s for %s' % (linkName,sourceObj.className)

                    try:
                        # Adds objects to targetObj.a as long as there is room
                        # (a.hicard could be e.g. 2)
                        addfunc(attrObj)
                        # # undo/redo
                        # addUndoItem(redo=partial(addfunc, attrObj),
                        #             undo=partial(_removefunc, attrObj))
                    except ApiError:
                        pass
                        #print 'Failed to add %s for %s' % (linkName,targetObj.className)
                        break

        elif o.hicard == 1 and o.locard == 1:

            if a.hicard == 1:
                #assert a.locard == 0
                oldVal = getattr(targetObj, linkName)
                if oldVal is None:
                    newVal = getattr(sourceObj, linkName)
                    # _old = getattr(newVal, backName)
                    setattr(newVal, backName, targetObj)
                    # # undo/redo
                    # addUndoItem(undo=partial(setattr, newVal, backName, _old),
                    #             redo=partial(setattr, newVal, backName, targetObj))

            else:
                # assert a.hicard != a.locard
                # asser a.hicard != 1
                for attrObj in getattr(sourceObj, linkName):
                    try:
                        # _old = getattr(attrObj, backName)
                        setattr(attrObj, backName, targetObj)
                        # # undo/redo
                        # addUndoItem(undo=partial(setattr, attrObj, backName, _old),
                        #             redo=partial(setattr, attrObj, backName, targetObj))
                    except ApiError:
                        pass

        else:
            #
            #print "C4", linkNam
            #
            # NB this does NOT break API
            #
            # we know that o.hicard == o.locard > 1
            # The trick is that since o.hicard == o.locard > 1 and a.changeability != frozen,
            # it must be possible to set attrObj.o to an appropriate tuple without
            # getting into trouble.
            if a.hicard == 1:
                #assert a.locard == 0
                attrObj = getattr(sourceObj, linkName)
                linkList = list(getattr(attrObj, backName))
                # _old = list(linkList)
                linkList[linkList.index(sourceObj)] = targetObj
                setattr(attrObj, backName, linkList)
                # # undo/redo
                # addUndoItem(undo=partial(setattr, attrObj, backName, _old),
                #             redo=partial(setattr, attrObj, backName, linkList))

            else:
                # assert a.hicard != a.locard
                # asser a.hicard != 1
                for attrObj in getattr(sourceObj, linkName):
                    linkList = list(getattr(attrObj, backName))
                    # _old = list(linkList)
                    linkList[linkList.index(sourceObj)] = targetObj
                    setattr(attrObj, backName, linkList)
                    # # undo/redo
                    # addUndoItem(undo=partial(setattr, attrObj, backName, _old),
                    #             redo=partial(setattr, attrObj, backName, linkList))

    # make sure we are valid before going into the tough part
    targetObj.checkValid()

    # undo = sourceObj.root._undo
    if nastyLinks or childLinks:

        with undoStackBlocking() as addUndoItem:

            if nastyLinks:
                root = targetObj.root
                try:
                    root.override = True
                    # undo/redo
                    addUndoItem(undo=partial(setattr, root, _OVERRIDE, False),
                                redo=partial(setattr, root, _OVERRIDE, True))

                    for a in nastyLinks:
                        # links that can *NOT* be handled without bypassing API

                        linkName = a.name
                        o = a.otherRole
                        backName = o.name
                        keyNames = o.container.keyNames
                        attrObjClass = a.valueType
                        downlink = attrObjClass.parentRole.otherRole.name
                        #print linkName, a.locard, a.hicard, o.locard, o.hicard

                        if a.hicard == 1:
                            #print "C1", linkName

                            if getattr(targetObj, linkName) is None:

                                attrObj = getattr(sourceObj, linkName)

                                # NOTE:ED - skip if no change
                                if attrObj is None:
                                    continue

                                #do
                                childDict = {}
                                oldKey = None
                                newKey = None
                                if backName in keyNames:
                                    # must be before the setattr
                                    oldKey = attrObj.getLocalKey()

                                setattr(sourceObj, linkName, None)
                                setattr(targetObj, linkName, attrObj)
                                # undo/redo
                                addUndoItem(undo=partial(setattr, sourceObj, linkName, attrObj),
                                            redo=partial(setattr, sourceObj, linkName, None))
                                addUndoItem(undo=partial(setattr, targetObj, linkName, None),
                                            redo=partial(setattr, targetObj, linkName, attrObj))

                                if backName in keyNames:
                                    newKey = attrObj.getLocalKey()
                                    # this changes key for attrObj - fix it.
                                    childDict = attrObj.parent.__dict__[downlink]
                                    if newKey in childDict:
                                        # key already taken - undo
                                        setattr(targetObj, linkName, None)
                                        setattr(sourceObj, linkName, attrObj)
                                        # NOTE:ED - shouldn't need undo/redo here as error trap
                                        raise ApiError("Merge failure: %s key %s already in use"
                                                       % (attrObj.qualifiedName(), newKey))
                                    else:
                                        _oldVal = childDict[oldKey]
                                        _setDict(childDict, oldKey, newKey, attrObj)
                                        # undo/redo
                                        addUndoItem(undo=partial(_setDict, childDict, newKey, oldKey, _oldVal),
                                                    redo=partial(_setDict, childDict, oldKey, newKey, attrObj))

                                # test
                                try:
                                    attrObj.checkValid()
                                    targetObj.checkValid()

                                # undo
                                except:
                                    setattr(targetObj, linkName, None)
                                    setattr(sourceObj, linkName, attrObj)
                                    # NOTE:ED - shouldn't need undo/redo here as error trap - check rollback of undo after raise
                                    if backName in keyNames:
                                        del childDict[newKey]
                                        childDict[oldKey] = attrObj
                                    print("Merge failure: %s, %s result is not valid"
                                          % (targetObj, attrObj))
                                    raise

                        else:
                            #
                            # assert a.hicard != 1
                            #
                            # NB if a.locard > 0 the code below could create an illegal
                            # sourceObj. Which would not be a problem if all went well,
                            # but would render the final state illegal if the merge ran into an
                            # error somewhere else later
                            # We ignore this as links that are locard>0 in one direction and
                            # frozen in the other direction would make both objects impossible
                            # to create except under override conditions. The problem is *very*
                            # unlikely ever to arise.

                            #
                            #print "C2", linkName
                            # set up
                            keepList = list(getattr(targetObj, linkName))
                            ll = list(getattr(sourceObj, linkName))

                            if a.hicard == metaConstants.infinity:
                                moveList = ll
                                ignoreList = []
                            else:
                                nSpaces = a.hicard - len(keepList)
                                if nSpaces > 0:
                                    moveList = ll[:nSpaces]
                                    ignoreList = ll[nSpaces:]
                                else:
                                    continue

                            # skip if no change
                            if not moveList:
                                continue

                            # do
                            oldKeys = []
                            newKeys = []
                            if backName in keyNames:
                                oldKeys = [x.getLocalKey() for x in moveList]

                            _ll = list(ll)
                            _ignoreList = list(ignoreList)
                            _keepList = list(keepList)
                            _moveList = list(keepList + moveList)

                            setattr(sourceObj, linkName, ignoreList)
                            setattr(targetObj, linkName, keepList + moveList)
                            # undo/redo
                            addUndoItem(undo=partial(setattr, sourceObj, linkName, _ll),
                                        redo=partial(setattr, sourceObj, linkName, _ignoreList))
                            addUndoItem(undo=partial(setattr, targetObj, linkName, _keepList),
                                        redo=partial(setattr, targetObj, linkName, _moveList))

                            if backName in keyNames:
                                newKeys = []
                                for ii, attrObj in enumerate(moveList):

                                    childDict = attrObj.parent.__dict__[downlink]
                                    newKey = attrObj.getLocalKey()
                                    if newKey in childDict:
                                        # key already taken - undo
                                        setattr(targetObj, linkName, None)
                                        setattr(sourceObj, linkName, attrObj)
                                        # NOTE:ED - shouldn't need undo/redo here as error trap - check rollback of undo after raise
                                        for jj, nk in enumerate(newKeys):
                                            ao = moveList[jj]
                                            cd = ao.parent.__dict__[downlink]
                                            cd[oldKeys[jj]] = ao
                                            del cd[nk]
                                        raise ApiError("Merge failure: %s key %s already in use"
                                                       % (attrObj.qualifiedName(), newKey))
                                    else:
                                        newKeys.append(newKey)
                                        # del childDict[oldKey]
                                        # TJS edit: to be checked
                                        _oldVal = childDict[oldKeys[ii]]
                                        _setDict(childDict, oldKeys[ii], newKey, attrObj)
                                        # undo/redo
                                        addUndoItem(undo=partial(_setDict, childDict, newKey, oldKeys[ii], _oldVal),
                                                    redo=partial(_setDict, childDict, oldKeys[ii], newKey, attrObj))

                            # test
                            try:
                                targetObj.checkValid()
                                for attrObj in moveList:
                                    attrObj.checkValid()

                            # undo
                            except:
                                setattr(targetObj, linkName, keepList)
                                setattr(sourceObj, linkName, moveList + ignoreList)
                                # NOTE:ED - shouldn't need undo/redo here as error trap - check rollback of undo after raise
                                if backName in keyNames:
                                    for jj, nk in enumerate(newKeys):
                                        ao = moveList[jj]
                                        cd = ao.parent.__dict__[downlink]
                                        cd[oldKeys[jj]] = ao
                                        del cd[nk]
                                raise


                finally:
                    root.override = False
                    # undo/redo
                    addUndoItem(undo=partial(setattr, root, _OVERRIDE, True),
                                redo=partial(setattr, root, _OVERRIDE, False))

        with undoStackBlocking() as addUndoItem:

            if childLinks:

                # now move children. This is a full bypass, no overrides
                for a in childLinks:
                    parentName = a.otherRole.name
                    sourceDd = sourceObj.__dict__[a.name]
                    targetDd = targetObj.__dict__[a.name]
                    topObj = targetObj.topObject

                    if a.hicard == 1:
                        # single kid (rare case)
                        _changeDict(targetObj, a.name, sourceObj, parentName, topObj)
                        # undo/redo
                        addUndoItem(undo=partial(_changeDict, sourceObj, a.name, targetObj, parentName, topObj),
                                    redo=partial(_changeDict, targetObj, a.name, sourceObj, parentName, topObj))

                    elif a.valueType.keyNames == ['serial']:
                        # multiple kid with serial key
                        nextSerial = targetObj.__dict__['_serialDict'][a.name] + 1
                        for junk, oo in sorted(sourceDd.items()):

                            _changeDictDel(targetDd, nextSerial, oo, sourceDd, parentName, targetObj, topObj)
                            # undo/redo
                            addUndoItem(undo=partial(_changeDictDel, sourceDd, nextSerial - 1, oo, targetDd, parentName, sourceObj, topObj),
                                        redo=partial(_changeDictDel, targetDd, nextSerial, oo, sourceDd, parentName, targetObj, topObj))

                        _setSerial(targetObj, a.name, nextSerial)
                        # undo/redo
                        addUndoItem(undo=partial(_setSerial, targetObj, a.name, nextSerial - 1),
                                    redo=partial(_setSerial, targetObj, a.name, nextSerial))

                    else:
                        # multiple kid with normal key
                        for localKey, oo in sorted(sourceDd.items()):
                            if localKey in targetDd:
                                # key is taken - skip object
                                continue
                            else:

                                _changeDictDel(targetDd, localKey, oo, sourceDd, parentName, targetObj, topObj)
                                # undo/redo
                                addUndoItem(undo=partial(_changeDictDel, sourceDd, localKey, oo, targetDd, parentName, sourceObj, topObj),
                                            redo=partial(_changeDictDel, targetDd, localKey, oo, sourceDd, parentName, targetObj, topObj))

        targetObj.checkValid()
        if _useV3Delete:
            if _mergeFunc:
                _mergeFunc(sourceObj, targetObj)
            _deleteFromV3(sourceObj)
            _notifyChangeV3(targetObj)

            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(_notifyChangeV3, targetObj))

        else:
            sourceObj.delete()

    else:
        targetObj.checkValid()
        if _useV3Delete:
            if _mergeFunc:
                _mergeFunc(sourceObj, targetObj)
            _deleteFromV3(sourceObj)
            _notifyChangeV3(targetObj)

            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(_notifyChangeV3, targetObj))

        else:
            sourceObj.delete()

    return targetObj


def _deleteFromV3(obj):
    """Method to delete an object from the v3 identifier
    Required because v3 notifiers are missed otherwise
    """
    from ccpn.framework.Application import getApplication

    getApp = getApplication()
    if getApp:
        project = getApp.project
        if project and obj in project._data2Obj:
            v3obj = project._data2Obj[obj]
            v3obj.delete()
            return

    obj.delete()
    # raise RuntimeError('trying to delete object {}'.format(obj))


def _notifyChangeV3(obj):
    """Method to notify an object from the v3 identifier
    Required because v3 notifiers are missed otherwise
    """
    from ccpn.framework.Application import getApplication

    getApp = getApplication()
    if getApp:
        project = getApp.project
        if project and obj in project._data2Obj:
            v3obj = project._data2Obj[obj]
            v3obj._finaliseAction('change')
            return

    # raise RuntimeError('trying to notify object {}'.format(obj))

# def _notifyChangeV3List(objList):
#     """Method to notify change to a list of objects
#     """
#     for obj in objList:
#         _notifyChangeV3(obj)


# def _mergeResonances(sourceObj, targetObj):
#     from ccpn.framework.Application import getApplication
#
#     getApp = getApplication()
#     if getApp:
#         project = getApp.project
#         if project and sourceObj in project._data2Obj and targetObj in project._data2Obj:
#
#             # v3 update of chemicalShift ids
#             for shift in project._data2Obj[targetObj].oldChemicalShifts:
#                 shift._refreshPid()
#             return
#
#     raise RuntimeError('trying to merge objects {} -> {}'.format(sourceObj, targetObj))
