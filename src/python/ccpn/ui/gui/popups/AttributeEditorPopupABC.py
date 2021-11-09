"""
Abstract base class to easily implement a popup to edit attributes of V3 layer objects
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
__dateModified__ = "$dateModified: 2021-11-09 14:00:22 +0000 (Tue, November 09, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from PyQt5 import QtCore
from functools import partial
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, _verifyPopupApply
from ccpn.core.lib.ContextManagers import queueStateChange
from ccpn.util.Common import makeIterableList, stringToCamelCase
from ccpn.ui.gui.lib.ChangeStateHandler import changeState
from ccpn.util.OrderedSet import OrderedSet
from ccpn.ui.gui.widgets.Font import getTextDimensionsFromFont


ATTRGETTER = 0
ATTRSETTER = 1
ATTRSIGNAL = 2
ATTRPRESET = 3


def getAttributeTipText(klass, attr):
    """Generate a tipText from the attribute of the given class.
     tipText is of the form:
      klass.attr

      Type: <type of the attribute>

      DocString: <string read from klass.attr.__doc__>

    :param klass: klass containing the attribute
    :param attr: attribute name
    :return: tipText string
    """
    try:
        attrib = getattr(klass, attr)
        at = attr
        ty = type(attrib).__name__
        st = attrib.__str__()
        dc = attrib.__doc__

        if ty == 'property':
            return '{}.{}\n' \
                   'Type:   {}\n' \
                   'DocString:  {}'.format(klass.__name__, at, ty, dc)
        else:
            return '{}.{}\n' \
                   'Type:   {}\n' \
                   'String form:    {}\n' \
                   'DocString:  {}'.format(klass.__name__, at, ty, st, dc)
    except:
        return None


class AttributeEditorPopupABC(CcpnDialogMainWidget):
    """
    Abstract base class to implement a popup for editing properties
    """

    klass = None  # The class whose properties are edited/displayed
    attributes = []  # A list of (attributeName, getFunction, setFunction, kwds) tuples;

    # get/set-Function have getattr, setattr profile
    # if setFunction is None: display attribute value without option to change value
    # kwds: optional kwds passed to LineEdit constructor

    # the width of the first column for compound widgets
    # hWidth = 100

    EDITMODE = True
    WINDOWPREFIX = 'Edit '

    ENABLEREVERT = True

    hWidth = None
    FIXEDWIDTH = True
    FIXEDHEIGHT = True

    def __init__(self, parent=None, mainWindow=None, obj=None, editMode=None, **kwds):
        """
        Initialise the widget
        """
        if editMode is not None:
            self.EDITMODE = editMode
            self.WINDOWPREFIX = 'Edit ' if editMode else 'New '

        super().__init__(parent, setLayout=True,
                         windowTitle=self.WINDOWPREFIX + self.klass.className, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        if self.EDITMODE:
            self.obj = obj
        else:
            self.obj = self._newContainer()
            self._populateInitialValues()

        # create the list of widgets and set the callbacks for each
        self._setAttributeWidgets()

        # set up the required buttons for the dialog
        self.setOkButton(callback=self._okClicked, enabled=False)
        self.setCancelButton(callback=self._cancelClicked)
        self.setHelpButton(callback=self._helpClicked, enabled=False)
        if self.ENABLEREVERT:
            self.setRevertButton(callback=self._revertClicked, enabled=False)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

        # populate the widgets
        self._populate()

        # set the links to the buttons
        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)
        self._cancelButton = self.dialogButtons.button(self.CANCELBUTTON)
        self._helpButton = self.dialogButtons.button(self.HELPBUTTON)
        self._revertButton = self.dialogButtons.button(self.RESETBUTTON)

    def _setAttributeWidgets(self):
        """Create the attributes in the main widget area
        """
        from ccpn.ui.gui.modules.CcpnModule import CommonWidgetsEdits

        self.edits = {}  # An (attributeName, widgetType) dict

        if self.hWidth is None:
            # set the hWidth for the popup
            optionTexts = [attr for attr, _, _, _, _, _, _ in self.attributes]
            _, maxDim = getTextDimensionsFromFont(textList=optionTexts)
            self.hWidth = maxDim.width()

        # create the list of widgets and set the callbacks for each
        row = 0
        for _label, attrType, getFunction, setFunction, presetFunction, callback, kwds in self.attributes:

            # remove whitespaces to give the attribute name in the class
            attr = stringToCamelCase(_label)
            tipText = getAttributeTipText(self.klass, attr)

            editable = setFunction is not None
            newWidget = attrType(self.mainWidget, mainWindow=self.mainWindow, labelText=_label, editable=editable,
                                 grid=(row, 0), fixedWidths=(self.hWidth, None),
                                 tipText=tipText, compoundKwds=kwds)  #, **kwds)

            # connect the signal
            if attrType and attrType.__name__ in CommonWidgetsEdits:
                attrSignalTypes = CommonWidgetsEdits[attrType.__name__][ATTRSIGNAL]

                for attrST in makeIterableList(attrSignalTypes):
                    this = newWidget

                    # iterate through the attributeName to get the signals to connect to (for compound widgets)
                    if attrST:
                        for th in attrST.split('.'):
                            this = getattr(this, th, None)
                            if this is None:
                                break
                        else:
                            if this is not None:
                                # attach the connect signal and store in the widget
                                queueCallback = partial(self._queueSetValue, attr, attrType, getFunction, setFunction, presetFunction, callback, row)
                                this.connect(queueCallback)
                                newWidget._queueCallback = queueCallback

                if callback:
                    newWidget.setCallback(callback=partial(callback, self))

            self.edits[attr] = newWidget

            setattr(self, attr, newWidget)
            row += 1

    def _populate(self):
        """Populate the widgets in the popup
        """
        from ccpn.ui.gui.modules.CcpnModule import CommonWidgetsEdits

        self._changes.clear()
        with self._changes.blockChanges():
            for _label, attrType, getFunction, _, _presetFunction, _, _ in self.attributes:
                # remove whitespaces to give the attribute name in the class
                attr = stringToCamelCase(_label)

                # populate the widget
                if attr in self.edits and attrType and attrType.__name__ in CommonWidgetsEdits:
                    thisEdit = CommonWidgetsEdits[attrType.__name__]
                    attrSetter = thisEdit[ATTRSETTER]

                    if _presetFunction:
                        # call the preset function for the widget (e.g. populate pulldowns with modified list)
                        _presetFunction(self, self.obj)

                    if getFunction:     # and self.EDITMODE:
                        # set the current value
                        value = getFunction(self.obj, attr, None)
                        attrSetter(self.edits[attr], value)

    def _populateInitialValues(self):
        """Populate the initial values for an empty object
        """
        self.obj.name = self.klass._nextAvailableName(self.klass, self.project)

    def _newContainer(self):
        """Make a new container to hold attributes for objects not created yet
        """
        return _attribContainer(self)

    def _getChangeState(self):
        """Get the change state from the _changes dict
        """
        if not self._changes.enabled:
            return None

        applyState = True
        revertState = False
        allChanges = True if self._changes else False

        return changeState(self, allChanges, applyState, revertState, self._okButton, None, self._revertButton, 0)

    @queueStateChange(_verifyPopupApply)
    def _queueSetValue(self, attr, attrType, getFunction, setFunction, presetFunction, callback, dim, _value=None):
        """Queue the function for setting the attribute in the calling object (dim needs to stay for the decorator)
        """
        # _value needs to be None because this is also called by widget.callBack which does not add the extra parameter
        from ccpn.ui.gui.modules.CcpnModule import CommonWidgetsEdits

        if attrType and attrType.__name__ in CommonWidgetsEdits:
            attrGetter = CommonWidgetsEdits[attrType.__name__][ATTRGETTER]
            value = attrGetter(self.edits[attr])

            if getFunction: # and self.EDITMODE:
                oldValue = getFunction(self.obj, attr, None)
                if (value or None) != (oldValue or None):
                    return partial(self._setValue, attr, setFunction, value)

    def _setValue(self, attr, setFunction, value):
        """Function for setting the attribute, called by _applyAllChanges

        This can be subclassed to completely disable writing to the object
        as maybe required in a new object
        """
        setFunction(self.obj, attr, value)

    def _refreshGLItems(self):
        """emit a signal to rebuild any required GL items
        Not required here
        """
        pass


NEWHIDDENGROUP = '_NEWHIDDENGROUP'
CLOSEHIDDENGROUP = '_CLOSEHIDDENGROUP'
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame
from ccpn.util.LabelledEnum import LabelledEnum
from collections import namedtuple
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.AttrDict import AttrDict


AttributeItem = namedtuple('AttributeItem', ('attr', 'attrType', 'getFunction', 'setFunction', 'presetFunction', 'callback', 'kwds',))


class AttributeListType(LabelledEnum):
    VERTICAL = 0, 'vertical'
    HORIZONTAL = 1, 'horizontal'
    MORELESS = 2, 'moreLess'
    TABFRAME = 3, 'tabFrame'
    TAB = 4, 'tab'
    EMPTYFRAME = 5, 'frame'


class AttributeABC():
    ATTRIBUTELISTTYPE = AttributeListType.VERTICAL

    def __init__(self, attributeList, queueStates=True, newContainer=True, hWidth=100, group=None, **kwds):
        self._attributes = attributeList
        self._row = 0
        self._col = 0
        self._queueStates = queueStates
        self._newContainer = newContainer
        self._container = None
        self._kwds = kwds
        self._hWidth = hWidth
        self._group = group

    def createContainer(self, parent, attribParent, grid=None, gridSpan=(1, 1)):
        # create the new container here, including gridSpan?
        if attribParent:
            grid = attribParent.nextGridPosition()
            attribParent.nextPosition()
        else:
            grid = (0, 0)

        self._container = Frame(parent, setLayout=True, grid=grid, **self._kwds)
        self._container.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self.nextPosition()
        return self._container

    def addAttribItem(self, parentRoot, attribItem):
        # add a new widget to the current container
        if not self._container:
            raise RuntimeError('Container not instantiated')

        from ccpn.ui.gui.modules.CcpnModule import CommonWidgetsEdits

        # add widget here
        _label, attrType, getFunction, setFunction, presetFunction, callback, kwds = attribItem

        # remove whitespaces to give the attribute name in the class
        attr = stringToCamelCase(_label)
        tipText = getAttributeTipText(parentRoot.klass, attr)

        editable = setFunction is not None
        newWidget = attrType(self._container, mainWindow=parentRoot.mainWindow,
                             labelText=_label, editable=editable,
                             grid=(self._row, self._col),
                             fixedWidths=(self._hWidth, None),
                             tipText=tipText, compoundKwds=kwds)  #, **kwds)

        # connect the signal
        if attrType and attrType.__name__ in CommonWidgetsEdits:
            attrSignalTypes = CommonWidgetsEdits[attrType.__name__][ATTRSIGNAL]

            for attrST in makeIterableList(attrSignalTypes):
                this = newWidget

                # iterate through the attributeName to get the signals to connect to (for compound widgets)
                if attrST:
                    for th in attrST.split('.'):
                        this = getattr(this, th, None)
                        if this is None:
                            break
                    else:
                        if this is not None:
                            # attach the connect signal and store in the widget
                            queueCallback = partial(parentRoot._queueSetValue, attr, attrType, getFunction, setFunction, presetFunction, callback, self._row)
                            this.connect(queueCallback)
                            newWidget._queueCallback = queueCallback

            if callback:
                newWidget.setCallback(callback=partial(callback, self))

        parentRoot.edits[attr] = newWidget
        if self._queueStates:
            parentRoot._VALIDATTRS.add(attr)

        # add the popup attribute corresponding to attr
        setattr(parentRoot, attr, newWidget)
        self.nextPosition()

    def nextPosition(self):
        """Move the pointer to the next position
        """
        self._row += 1

    def nextGridPosition(self):
        return (self._row, self._col)


class VList(AttributeABC):
    # contains everything from the baseClass
    pass


class HList(AttributeABC):
    ATTRIBUTELISTTYPE = AttributeListType.HORIZONTAL

    def nextPosition(self):
        """Move the pointer to the next position
        """
        self._col += 1


class MoreLess(AttributeABC):
    ATTRIBUTELISTTYPE = AttributeListType.MORELESS

    def createContainer(self, parent, attribParent, grid=None, gridSpan=(1, 1)):
        # create the new container here, including gridSpan?
        if attribParent:
            grid = attribParent.nextGridPosition()
            attribParent.nextPosition()
        else:
            grid = (0, 0)

        _frame = MoreLessFrame(parent, showMore=False, grid=grid, **self._kwds)
        self._container = _frame.contentsFrame
        self._container.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self.nextPosition()
        return self._container


class ComplexAttributeEditorPopupABC(AttributeEditorPopupABC):
    """
    Abstract base class to implement a popup for editing complex properties
    """
    attributes = VList([])  # A container holding a list of attributes/containers

    # each attribute is of type (attributeName, getFunction, setFunction, kwds) tuples;
    # or a container type VList/HList/MoreLess

    def _setAttributeSet(self, parentWidget, attribParent, attribContainer):

        # start by making new container
        attribContainer.createContainer(parentWidget, attribParent)

        for attribItem in attribContainer._attributes:
            if isinstance(attribItem, AttributeABC):
                # recurse into the list
                self._setAttributeSet(attribContainer._container, attribContainer, attribItem)

            elif isinstance(attribItem, tuple):
                # add widget
                attribContainer.addAttribItem(self, attribItem)

            else:
                raise RuntimeError('Container not type defined')

    def _setAttributeWidgets(self):
        """Create the attributes in the main widget area
        """
        # raise an error if the top object is not a container
        if not isinstance(self.attributes, AttributeABC):
            raise RuntimeError('Container not type defined')

        self.edits = {}  # An (attributeName, widgetType) dict
        self._VALIDATTRS = OrderedSet()

        attribGroups = {}
        self._defineMinimumWidthSet(self.attributes, attribGroups)
        self._linkAttributeGroups(attribGroups)

        # create the list of widgets and set the callbacks for each
        self._setAttributeSet(self.mainWidget, None, self.attributes)

    def _linkAttributeGroups(self, attribGroups):
        if attribGroups and len(attribGroups):
            for groupNum, groups in attribGroups.items():
                widths = [klass._hWidth for klass in groups]
                if widths and len(widths) > 1:
                    maxHWidth = np.max(widths)
                    for klass in groups:
                        klass._hWidth = maxHWidth

    def _defineMinimumWidthSet(self, attribContainer, attribGroups):

        if attribContainer._group is not None:
            if attribContainer._group not in attribGroups:
                attribGroups[attribContainer._group] = (attribContainer,)
            else:
                attribGroups[attribContainer._group] += (attribContainer,)

        if not attribContainer._hWidth:
            # calculate a new _hWidth if undefined
            optionTexts = [attribItem[0] for attribItem in attribContainer._attributes if isinstance(attribItem, tuple)]
            _, maxDim = getTextDimensionsFromFont(textList=optionTexts)
            attribContainer._hWidth = maxDim.width()

        for attribItem in attribContainer._attributes:
            if isinstance(attribItem, AttributeABC):
                # recurse into the list
                self._defineMinimumWidthSet(attribItem, attribGroups)

    def _populateIterator(self, attribList):
        from ccpn.ui.gui.modules.CcpnModule import CommonWidgetsEdits

        for attribItem in attribList._attributes:

            if isinstance(attribItem, AttributeABC):
                # must be another subgroup of attributes - AttributeABC
                self._populateIterator(attribItem)

            elif isinstance(attribItem, tuple):
                # these are now in the containerList
                attr, attrType, getFunction, _, _presetFunction, _, _ = attribItem

                # remove whitespaces to give the attribute name in the class, make first letter lowercase
                attr = stringToCamelCase(attr)

                # populate the widget
                if attr in self.edits and attrType and attrType.__name__ in CommonWidgetsEdits:
                    thisEdit = CommonWidgetsEdits[attrType.__name__]
                    attrSetter = thisEdit[ATTRSETTER]

                    if _presetFunction:
                        # call the preset function for the widget (e.g. populate pulldowns with modified list)
                        _presetFunction(self, self.obj)

                    if getFunction:     # and self.EDITMODE:
                        # set the current value
                        value = getFunction(self.obj, attr, None)
                        attrSetter(self.edits[attr], value)

            else:
                raise RuntimeError('Container type not defined')

    def _populate(self):

        self._changes.clear()
        with self._changes.blockChanges():
            # start with the top object - must be a container class
            self._populateIterator(self.attributes)

    def _setValue(self, attr, setFunction, value):
        """Function for setting the attribute, called by _applyAllChanges

        This can be subclassed to completely disable writing to the object
        as maybe required in a new object
        """
        if attr in self._VALIDATTRS:
            setFunction(self.obj, attr, value)

    def _newContainer(self):
        """Make a new container to hold attributes for objects not created yet
        """
        return _complexAttribContainer(self)


class _complexAttribContainer(AttrDict):
    """
    Class to simulate a blank object in new/edit popup.
    """

    def _setAttributes(self, attribList):
        for attribItem in attribList._attributes:

            if isinstance(attribItem, AttributeABC):
                # must be another subgroup of attributes - AttributeABC
                self._setAttributes(attribItem)

            elif isinstance(attribItem, tuple):
                _label = stringToCamelCase(attribItem[0])
                self[_label] = None

            else:
                raise RuntimeError('Container type not defined')

    def __init__(self, popupClass):
        """Create a list of attributes from the container class
        """
        super().__init__()
        # self._popupClass = popupClass

        self._setAttributes(popupClass.attributes)


class _attribContainer(AttrDict):
    """
    Class to simulate a simple blank object in new/edit popup.
    """

    def __init__(self, popupClass):
        """Create a list of attributes from the container class
        """
        super().__init__()
        for attribItem in popupClass.attributes:
            _label = stringToCamelCase(attribItem[0])
            self[_label] = None
