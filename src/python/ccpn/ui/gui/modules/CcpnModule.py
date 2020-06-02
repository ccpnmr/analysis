"""
This file contains CcpnModule base class
modified by Geerten 1-12/12/2016
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-06-02 09:52:52 +0100 (Tue, June 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util import Logging
from ccpn.util.Logging import getLogger
import itertools
import collections
from functools import partial
from pyqtgraph.dockarea.Container import Container
from pyqtgraph.dockarea.DockDrop import DockDrop
from pyqtgraph.dockarea.Dock import DockLabel, Dock
from pyqtgraph.dockarea.DockArea import DockArea
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.guiSettings import getColours, CCPNMODULELABEL_BACKGROUND, CCPNMODULELABEL_FOREGROUND, \
    CCPNMODULELABEL_BACKGROUND_ACTIVE, CCPNMODULELABEL_FOREGROUND_ACTIVE, CCPNMODULELABEL_BORDER, CCPNMODULELABEL_BORDER_ACTIVE, \
    BORDERNOFOCUS_COLOUR
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.ToolButton import ToolButton
from ccpn.ui.gui.widgets.Icon import Icon
# from ccpn.ui.gui.guiSettings import moduleLabelFont
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.SideBar import SideBar
from ccpn.ui.gui.widgets.PythonEditor import QCodeEditor
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget, CheckBoxCompoundWidget, \
    DoubleSpinBoxCompoundWidget, SelectorWidget, InputPulldown, \
    ColourSelectionWidget, LineEditPopup, ListCompoundWidget
from ccpn.ui.gui.widgets.PulldownListsForObjects import _PulldownABC
from ccpn.core.lib.Notifiers import NotifierBase
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, RadioButtonsCompoundWidget, ScientificSpinBoxCompoundWidget, SpinBoxCompoundWidget
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown
from ccpn.ui.gui.widgets.Entry import Entry


CommonWidgets = {
    CheckBox.__name__                   : (CheckBox.get, CheckBox.setChecked),
    ColourDialog.__name__               : (ColourDialog.getColor, ColourDialog.setColour),
    DoubleSpinbox.__name__              : (DoubleSpinbox.value, DoubleSpinbox.setValue),
    # Label.__name__:                   (Label.get,                   Label.setText),
    LineEdit.__name__                   : (LineEdit.get, LineEdit.setText),
    LineEditButtonDialog.__name__       : (LineEditButtonDialog.get, LineEditButtonDialog.setText),
    PulldownList.__name__               : (PulldownList.currentText, PulldownList.set),
    RadioButtons.__name__               : (RadioButtons.get, RadioButtons.set),
    RadioButton.__name__                : (RadioButton.isChecked, RadioButton.setChecked),

    Slider.__name__                     : (Slider.get, Slider.setValue),
    Spinbox.__name__                    : (Spinbox.value, Spinbox.set),
    TextEditor.__name__                 : (TextEditor.get, TextEditor.setText),
    GLTargetButtonSpinBoxes.__name__    : (GLTargetButtonSpinBoxes.get, GLTargetButtonSpinBoxes.setValues),

    PulldownListCompoundWidget.__name__ : (PulldownListCompoundWidget.getText, PulldownListCompoundWidget.select),  #PulldownList
    ListCompoundWidget.__name__         : (ListCompoundWidget.getTexts, ListCompoundWidget.setTexts),  #PulldownList based
    CheckBoxCompoundWidget.__name__     : (CheckBoxCompoundWidget.get, CheckBoxCompoundWidget.set),
    DoubleSpinBoxCompoundWidget.__name__: (DoubleSpinBoxCompoundWidget.getValue, DoubleSpinBoxCompoundWidget.setValue),  #D oubleSpinbox
    SelectorWidget.__name__             : (SelectorWidget.getText, SelectorWidget.select),  #PulldownList
    InputPulldown.__name__              : (InputPulldown.currentText, InputPulldown.set),  #PulldownList
    ColourSelectionWidget.__name__      : (ColourSelectionWidget.currentText, ColourSelectionWidget.setColour),  #PulldownList
    LineEditPopup.__name__              : (LineEditPopup.get, LineEditPopup.set),
    QCodeEditor.__name__                : (QCodeEditor.get, QCodeEditor.set),

    EntryCompoundWidget.__name__        : (EntryCompoundWidget.getText, EntryCompoundWidget.setText),
    NmrChainPulldown.__name__           : (NmrChainPulldown.getText, NmrChainPulldown.select),

    # ADD TABLES
    # ADD Others
    }

CommonWidgetsEdits = {
    CheckBox.__name__                       : (CheckBox.get, CheckBox.setChecked, None),
    ColourDialog.__name__                   : (ColourDialog.getColor, ColourDialog.setColour, None),
    DoubleSpinbox.__name__                  : (DoubleSpinbox.value, DoubleSpinbox.setValue, None),

    LineEdit.__name__                       : (LineEdit.get, LineEdit.setText, None),
    LineEditButtonDialog.__name__           : (LineEditButtonDialog.get, LineEditButtonDialog.setText, None),
    PulldownList.__name__                   : (PulldownList.currentText, PulldownList.set, None),
    RadioButtons.__name__                   : (RadioButtons.get, RadioButtons.set, None),
    RadioButton.__name__                    : (RadioButton.isChecked, RadioButton.setChecked, None),

    Slider.__name__                         : (Slider.get, Slider.setValue, None),
    Spinbox.__name__                        : (Spinbox.value, Spinbox.set, None),
    TextEditor.__name__                     : (TextEditor.get, TextEditor.setText, None),
    GLTargetButtonSpinBoxes.__name__        : (GLTargetButtonSpinBoxes.get, GLTargetButtonSpinBoxes.setValues, None),

    PulldownListCompoundWidget.__name__     : (PulldownListCompoundWidget.getText, PulldownListCompoundWidget.select,
                                               ('pulldownList.activated', 'pulldownList.pulldownTextEdited')),

    ListCompoundWidget.__name__             : (ListCompoundWidget.getTexts, ListCompoundWidget.setTexts, None),
    CheckBoxCompoundWidget.__name__         : (CheckBoxCompoundWidget.get, CheckBoxCompoundWidget.set, None),
    DoubleSpinBoxCompoundWidget.__name__    : (DoubleSpinBoxCompoundWidget.getValue, DoubleSpinBoxCompoundWidget.setValue,
                                               ('doubleSpinBox.valueChanged')),
    ScientificSpinBoxCompoundWidget.__name__: (ScientificSpinBoxCompoundWidget.getValue, ScientificSpinBoxCompoundWidget.setValue,
                                               ('scientificSpinBox.valueChanged')),
    SpinBoxCompoundWidget.__name__          : (SpinBoxCompoundWidget.getValue, SpinBoxCompoundWidget.setValue,
                                               ('spinBox.valueChanged')),

    SelectorWidget.__name__                 : (SelectorWidget.getText, SelectorWidget.select, None),
    InputPulldown.__name__                  : (InputPulldown.currentText, InputPulldown.set, None),
    ColourSelectionWidget.__name__          : (ColourSelectionWidget.currentText, ColourSelectionWidget.setColour, None),
    LineEditPopup.__name__                  : (LineEditPopup.get, LineEditPopup.set, None),
    QCodeEditor.__name__                    : (QCodeEditor.get, QCodeEditor.set, None),

    EntryCompoundWidget.__name__            : (EntryCompoundWidget.getText, EntryCompoundWidget.setText, 'entry.textEdited'),
    NmrChainPulldown.__name__               : (NmrChainPulldown.getText, NmrChainPulldown.select, 'pulldownList.activated'),
    RadioButtonsCompoundWidget.__name__     : (RadioButtonsCompoundWidget.getIndex, RadioButtonsCompoundWidget.setIndex,
                                               'radioButtons.buttonGroup.buttonClicked'),

    # ADD TABLES
    # ADD Others
    }

settingsWidgetPositions = {
    'top'   : {'settings': (0, 0), 'widget': (1, 0)},
    'bottom': {'settings': (1, 0), 'widget': (0, 0)},
    'left'  : {'settings': (0, 0), 'widget': (0, 1)},
    'right' : {'settings': (0, 1), 'widget': (0, 0)},
    }
ALL = '<all>'
DoubleUnderscore = '__'


class CcpnModule(Dock, DropBase, NotifierBase):
    """
    Base class for CCPN modules
    sets self.application, self.current, self.project and self.mainWindow

    Overide parameters for settings widget as needed

    Usage:
      __init__    initialises the module according to the settings given below:

      _closeModule    closing of the module.

                      If addition functionality is required, the correct
                      procedure is to override this method within your class
                      and end your method with super()._closeModule()

                      e.q.
                            def _closeModule(self):
                              # your functions here
                              super(<YourModule>, self)._closeModule()

                      OR __init__ with closeFunc=<your close function>
    """
    moduleName = ''
    className = ''

    HORIZONTAL = 'horizontal'
    VERTICAL = 'vertical'
    labelOrientation = HORIZONTAL  # toplabel orientation

    # overide in specific module implementations
    includeSettingsWidget = False
    maxSettingsState = 3  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    defaultSettingsState = 0  # default state of the settings widget
    settingsPosition = 'top'
    settingsMinimumSizes = (100, 50)
    _restored = False

    # _instances = set()

    def __init__(self, mainWindow, name, closable=True, closeFunc=None, settingsScrollBarPolicies=('asNeeded', 'asNeeded'), **kwds):

        self.maximised = False
        self.maximiseRestoreState = None

        #TODO:GEERTEN: make mainWindow actually do something
        self.area = None
        if mainWindow is not None:
            self.area = mainWindow.moduleArea

        super().__init__(name=name, area=self.area,
                         autoOrientation=False,
                         closable=closable)
        DropBase._init(self, acceptDrops=True)

        self.hStyle = """
                  
                  Dock > QWidget {
                      border: 1px solid #a9a9a9;
                      border-radius: 2px;
                      border-top-left-radius: 0px;
                      border-top-right-radius: 0px;
                      border-top-width: 0px;
                  }"""
        self.vStyle = """
                  Dock > QWidget {
                      border: 1px solid #000;
                      border-radius: 0px;
                      border-top-left-radius: 0px;
                      border-bottom-left-radius: 0px;
                      border-left-width: 0px;
                  }"""
        self.nStyle = """
                  Dock > QWidget {
                      border: 0px solid #000;
                      border-radius: 0px;
                  }"""
        self.dragStyle = """
                  Dock > QWidget {
                      border: 0px solid #00F;
                      border-radius: 0px;
                  }"""
        self._selectedOverlay = DropAreaSelectedOverlay(self)
        self._selectedOverlay.raise_()

        Logging.getLogger().debug('CcpnModule>>> %s %s' % (type(self), mainWindow))

        # Logging.getLogger().debug('module:"%s"' % (name,))
        self.mainWindow = mainWindow
        self.closeFunc = closeFunc
        self._nameSplitter = ':'  #used to create the serial
        self._serial = None
        self._titleName = None  # name without serial
        CcpnModule.moduleName = name

        self.widgetArea.setContentsMargins(0, 0, 0, 0)

        # remove old label, so it can be redefined
        self.topLayout.removeWidget(self.label)
        # GST this wasn't deleting the widget it was leaving it still attached to the qt hierrchy which was causing all
        # sorts of graphical hickups later on
        self.label.deleteLater()
        del self.label

        # GST other way to do this would be to
        # 1. replace the super class init with our own and not call it 2. replace the methods of DockLabel we have
        # problems with 3. ask the pyqtgraph guys to add a factory method...
        self.label = CcpnModuleLabel(name, self,
                                     showCloseButton=closable, closeCallback=self._closeModule,
                                     showSettingsButton=self.includeSettingsWidget,
                                     settingsCallback=self._settingsCallback
                                     )
        self.topLayout.addWidget(self.label, 0, 1)  # ejb - swap out the old widget, keeps hierarchy
        # except it doesn't work properly
        self.setOrientation(o='horizontal')
        self.setAutoFillBackground(True)

        # main widget area
        self.mainWidget = Frame(parent=None, setLayout=True, acceptDrops=True)

        # optional settings widget area
        self.settingsWidget = None
        if self.includeSettingsWidget:

            # self._settingsScrollArea = ScrollArea(parent=self.widgetArea, scrollDirections=settingsScrollDirections)
            # self.settingsWidget = Widget(parent=None, acceptDrops=True)
            # self._settingsScrollArea.setWidget(self.settingsWidget)
            # self.settingsWidget.setGridLayout()
            # self._settingsScrollArea.setWidgetResizable(True)

            self.settingsWidget = ScrollableFrame(parent=self.widgetArea,
                                                  showBorder=False, setLayout=True,
                                                  scrollBarPolicies=settingsScrollBarPolicies)
            self._settingsScrollArea = self.settingsWidget._scrollArea

            # set the new borders for the settings scroll area - border not needed at the top
            self._settingsScrollArea.setStyleSheet('ScrollArea { border-left: 1px solid %s;'
                                                   'border-right: 1px solid %s;'
                                                   'border-bottom: 1px solid %s;'
                                                   'background: transparent; }' % (BORDERNOFOCUS_COLOUR, BORDERNOFOCUS_COLOUR, BORDERNOFOCUS_COLOUR))
            self.settingsWidget.insertCornerWidget()

            if self.settingsPosition in settingsWidgetPositions:
                hSettings, vSettings = settingsWidgetPositions[self.settingsPosition]['settings']
                hWidget, vWidget = settingsWidgetPositions[self.settingsPosition]['widget']
                self.addWidget(self._settingsScrollArea, hSettings, vSettings)
                self.addWidget(self.mainWidget, hWidget, vWidget)
            else:  #default as settings on top and widget below
                self.addWidget(self._settingsScrollArea, 0, 0)
                self.addWidget(self.mainWidget, 1, 0)

            self._settingsScrollArea.hide()

            self.layout.removeWidget(self._settingsScrollArea)
            self.layout.removeWidget(self.mainWidget)

            if self.settingsPosition == 'left':
                self._splitter = Splitter(setLayout=True, horizontal=True)
                self._splitter.addWidget(self._settingsScrollArea)
                self._splitter.addWidget(self.mainWidget)
            elif self.settingsPosition == 'right':
                self._splitter = Splitter(setLayout=True, horizontal=True)
                self._splitter.addWidget(self.mainWidget)
                self._splitter.addWidget(self._settingsScrollArea)
            elif self.settingsPosition == 'top':
                self._splitter = Splitter(setLayout=True, horizontal=False)
                self._splitter.addWidget(self._settingsScrollArea)
                self._splitter.addWidget(self.mainWidget)
            elif self.settingsPosition == 'bottom':
                self._splitter = Splitter(setLayout=True, horizontal=False)
                self._splitter.addWidget(self.mainWidget)
                self._splitter.addWidget(self._settingsScrollArea)

            self.addWidget(self._splitter)
            # self._splitter.setStretchFactor(1, 5)

        else:
            self.settingsWidget = None
            self.addWidget(self.mainWidget, 0, 0)

        # set the flag so that the gearbox settings widget expands to the required size on the first click
        self.setExpandSettingsFlag(True)

        # add an event filter to check when the dock has been floated - it needs to have a callback
        # that fires when the window has been maximised
        self._maximiseFunc = None
        self._closeFunc = None
        CcpnModule._lastActionWasDrop = False

        # always explicitly show the mainWidget and/or settings widget
        # default state (increased by one by settingsCallback)
        self.settingsState = self.defaultSettingsState - 1
        self.mainWidget.show()
        self._settingsCallback()

        # set parenting relations
        if self.mainWindow is not None:
            self.setParent(self.mainWindow.moduleArea)  # ejb
        self.widgetArea.setParent(self)

        # stop the blue overlay popping up when dragging over a spectrum (no central region)
        self.allowedAreas = ['top', 'left', 'right', 'bottom']

        self._updateStyle()
        self.update()  # make sure that the widgetArea starts the correct size

        self._allChildren = set()

    # Leave this in so I remember ShortcutOverride
    # def event(self, event):
    #     if event.type() == QtCore.QEvent.ShortcutOverride:
    #         event.accept()
    #         print('>>>Override')
    #     else:
    #         super(CcpnModule, self).event(event)

    # @property
    # def titleBarHidden(self):
    #     return self.labelHidden
    #
    # @titleBarHidden.setter
    # def titleBarHidden(self, hidden):
    #     if hidden:
    #         self.hideTitleBar()
    #     else:
    #         self.showTitleBar()
    #
    # #GST super class show and hide titlebar have central as an allowed area we don't use it
    # #    so remove it as a choice
    # def hideTitleBar(self):
    #     """
    #     Hide the title bar for this Dock.
    #     This will prevent the Dock being moved by the user.
    #     """
    #     self.label.hide()
    #     self.labelHidden = True
    #     self.updateStyle()
    #
    # def showTitleBar(self):
    #     """
    #     Show the title bar for this Dock.
    #     """
    #     self.label.show()
    #     self.labelHidden = False
    #     self.updateStyle()

    def getDockArea(self, target=None):
        if target is None:
            current = self
        else:
            current = target

        while current.parent() != None:
            if isinstance(current, DockArea):
                break
            current = current.parent()
        return current

    # def getDock(self, target=None):
    #     if target is None:
    #         current = self
    #     else:
    #         current = target
    #
    #     while current.parent() != None:
    #         if isinstance(current, Dock):
    #             break
    #         current = current.parent()
    #
    #     if not isinstance(current, Dock):
    #         current = None
    #     return current
    #
    # def docksByDockArea(self):
    #     result = {}
    #     docks = list(self.area.docks.values())
    #     for dock in docks:
    #         parent = dock.getDockArea()
    #         result.setdefault(parent, []).append(dock)
    #     return result
    #
    # def float(self):
    #     if self.maximised:
    #         self.toggleMaximised()
    #     super().float()
    #
    # def mergeState(self, state):
    #     result = self.getHome().saveState(docksOnly=True)
    #
    #     if state['main'] != None:
    #         result['main'] = state['main']
    #
    #     if len(state['floats']) != 0:
    #         toMerge = state['floats'][0]
    #         mergeId = toMerge[2]['id']
    #
    #         for i, currentState in enumerate(result['floats']):
    #             currentId = currentState[2]['id']
    #
    #             if currentId == mergeId:
    #                 result['floats'][i] = toMerge
    #
    #     return result
    #
    # def filterState(self, state, id_):
    #
    #     result = {'main': None, 'floats': []}
    #
    #     if state['main'][2]['id'] == id_:
    #         result['main'] = state['main']
    #
    #     for float in state['floats']:
    #         if float[2]['id'] == id_:
    #             result['floats'].append(float)
    #
    #     return result
    #
    # def getDocksInParentArea(self):
    #     return self.docksByDockArea()[self.getDockArea()]
    #
    # def getHome(self):
    #     result = self.area
    #     if self.area.home != None:
    #         result = self.area.home
    #     return result
    #
    # def toggleMaximised(self):
    #
    #     docks = self.getDocksInParentArea()
    #
    #     if len(docks) < 2:
    #         self.maximised = False
    #         self.maximiseRestoreState = None
    #     elif self.maximised:
    #         dockArea = self.getDockArea()
    #         dockAreaId = id(dockArea)
    #         state = self.mergeState(self.maximiseRestoreState)
    #         if (self.area.home):
    #             self.area.home.restoreState(state)
    #         else:
    #             self.area.restoreState(state)
    #         for dock in docks:
    #             dock.showTitleBar()
    #         self.maximised = False
    #         self.maximiseRestoreState = None
    #     else:
    #         state = self.getHome().saveState(docksOnly=True)
    #         dockArea = self.getDockArea()
    #         dockAreaId = id(dockArea)
    #         state = self.filterState(state, dockAreaId)
    #         self.maximiseRestoreState = state
    #
    #         docks = self.docksByDockArea()[self.getDockArea()]
    #         docks.remove(self)
    #         for dock in docks:
    #             dock.hideTitleBar()
    #             self.area.moveDock(dock, 'below', self)
    #
    #         self._container.raiseDock(self)
    #
    #         self.maximised = True

    def _findChildren(self, widget):
        for i in widget.children():
            self._allChildren.update({i})
            self._findChildren(i)

    @property
    def titleName(self):
        'module name without serial'
        moduleName = self.name()
        splits = moduleName.split(self._nameSplitter)
        if len(splits) > 1:
            title = splits[0]
            return title
        else:
            return moduleName

    @property
    def serial(self):
        return self._serial

    @serial.setter
    def serial(self, value):
        if isinstance(value, str):
            try:
                value = int(value)
                return
            except Exception as e:
                getLogger().warnig('Cannot set attribute %s' % e)
        if isinstance(value, int):
            self._serial = value
            return
        else:
            getLogger().warning('Cannot set attribute. Serial must be an Int type')

    @property
    def widgetsState(self):
        return self._widgetsState

    # @widgetsState.setter
    # def widgetsState(self, value):
    #   self._widgetsState = value

    def _setNestedWidgetsAttrToModule(self):
        '''
        :return: nestedWidgets
        '''
        allStorableWidgets = []
        self._findChildren(self)
        for num, w in enumerate(self._allChildren):
            if w.__class__.__name__ in CommonWidgets:
                allStorableWidgets.append(w)
        widgetsWithinSelf = []
        for varName, varObj in vars(self).items():
            if varObj.__class__.__name__ in CommonWidgets.keys():
                widgetsWithinSelf.append(varObj)

        nestedWidgets = [widget for widget in allStorableWidgets if widget not in widgetsWithinSelf]
        nestedWidgs = []
        for widg in nestedWidgets:
            try:
                if widg.parent() not in widgetsWithinSelf:
                    nestedWidgs.append(widg)
            except Exception as es:
                getLogger().debug2('ignoring bad widget %s - %s' % (str(widg), str(es)))

        nestedWidgs.sort(key=lambda x: str(type(x)), reverse=False)
        groupednestedWidgets = [list(v) for k, v in itertools.groupby(nestedWidgs, lambda x: str(type(x)), )]
        for widgetsGroup in groupednestedWidgets:
            for count, widget in enumerate(widgetsGroup):
                if widget.objectName():
                    setattr(self, DoubleUnderscore + widget.objectName(), widget)
                else:
                    setattr(self, DoubleUnderscore + widget.__class__.__name__ + str(count), widget)

    @widgetsState.getter
    def widgetsState(self):
        '''return  {"variableName":"value"}  of all gui Variables  '''
        widgetsState = {}
        self._setNestedWidgetsAttrToModule()
        for varName, varObj in vars(self).items():
            if isinstance(varObj, _PulldownABC):
                widgetsState[varName] = varObj.getText()
                continue
            if varObj.__class__.__name__ in CommonWidgets.keys():
                try:  # try because widgets can be dinamically deleted
                    widgetsState[varName] = getattr(varObj, CommonWidgets[varObj.__class__.__name__][0].__name__)()
                except Exception as e:
                    getLogger().debug('Error %s', e)
        # self._kwargs = collections.OrderedDict(sorted(widgetsState.items()))

        return collections.OrderedDict(sorted(widgetsState.items()))

    def restoreWidgetsState(self, **widgetsState):
        """
        Restore the gui params. To Call it: _setParams(**{"variableName":"value"})

        This is automatically called after every restoration and after the module has been initialised.
        Subclass this for a custom behaviour. for example custom callback after the widgets have been restored.
        Subclass like this:
               def restoreWidgetsState(self, **widgetsState):
                  super(TheModule, self).restoreWidgetsState(**widgetsState) #First restore as default
                  #  do some stuff

        :param widgetsState:
        """

        self._setNestedWidgetsAttrToModule()
        widgetsState = collections.OrderedDict(sorted(widgetsState.items()))
        for variableName, value in widgetsState.items():
            try:
                widget = getattr(self, str(variableName))
                if isinstance(widget, _PulldownABC):
                    widget.select(value)
                    continue
                if widget.__class__.__name__ in CommonWidgets.keys():
                    setWidget = getattr(widget, CommonWidgets[widget.__class__.__name__][1].__name__)
                    setWidget(value)

            except Exception as e:
                getLogger().debug('Impossible to restore %s value for %s. %s' % (variableName, self.name(), e))

    def rename(self, newName):
        self.label.setText(newName)
        self._name = newName

    def event(self, event):
        """
        CCPNInternal
        Handle events for switching transparency of modules
        Modules become transparent when dragging to another module.
        Ensure that the dropAreas become active
        """
        if event.type() == QtCore.QEvent.ParentChange and self._maximiseFunc:
            try:
                found = False
                searchWidget = self.parent()

                # while searchWidget is not None and not found:
                #   # print (searchWidget)
                #   if isinstance(searchWidget, TempAreaWindow):
                #     searchWidget.eventFilter = self._tempAreaWindowEventFilter
                #     searchWidget.installEventFilter(searchWidget)
                #     found = True
                #   else:
                #     searchWidget = searchWidget.parent()

            except Exception as es:
                getLogger().warning('Error setting maximiseFunc', str(es))

        return super(CcpnModule, self).event(event)

    def installMaximiseEventHandler(self, maximiseFunc, closeFunc):
        """
        Attach a maximise function to the parent window.
        This is called when the WindowStateChanges to maximises

        :param maximiseFunc:
        """
        return

        # self._maximiseFunc = maximiseFunc
        # self._closeFunc = closeFunc

    def removeMaximiseEventHandler(self):
        """
        Clear the attached maximise function
        :return:
        """
        self._maximiseFunc = None
        self._closeFunc = None

    def _tempAreaWindowEventFilter(self, obj, event):
        """
        Window manager event filter to call the attached maximise function.
        This is required to re-populate the window when it has been maximised
        """
        try:
            if event.type() == QtCore.QEvent.WindowStateChange:
                if event.oldState() & QtCore.Qt.WindowMinimized:

                    if self._maximiseFunc:
                        self._maximiseFunc()

            elif event.type() == QtCore.QEvent.Close:

                # catch whether the close event is from closing the tempWindow or moving back to a different module area
                if self._closeFunc and not CcpnModule._lastActionWasDrop:
                    self._closeFunc()
                else:
                    CcpnModule._lastActionWasDrop = False

        except Exception as es:
            getLogger().debug('TempWindow Error %s; %s; %s', obj, event, str(es))
        finally:
            return False

    def _settingsCallback(self):
        """
        Toggles display of settings widget in module.
        """
        if self.includeSettingsWidget:
            self.settingsState = (self.settingsState + 1) % self.maxSettingsState
            if self.settingsState == 0:
                self.mainWidget.show()
                # self.settingsWidget._sequenceGraphScrollArea.hide()
                self._settingsScrollArea.hide()
            elif self.settingsState == 1:
                self.mainWidget.show()
                # self.settingsWidget._sequenceGraphScrollArea.hide()
                self._settingsScrollArea.show()
                self._setSettingsWidgetSize()
            elif self.settingsState == 2:
                # self.settingsWidget._sequenceGraphScrollArea.hide()
                self._settingsScrollArea.hide()
                self.mainWidget.hide()
        else:
            RuntimeError('Settings widget inclusion is false, please set includeSettingsWidget boolean to True at class level ')

    def setExpandSettingsFlag(self, value):
        """Set the expand flag to the True/False
        """
        self._expandSettingsFlag = value

    def _setSettingsWidgetSize(self):
        """Set the size of the gearbox settings to the sizeHint if the flag is True
        Size is stored for next open/close unless flag is reset to True
        """
        if self._expandSettingsFlag:
            self._expandSettingsFlag = False

            sizes = self._splitter.sizes()
            total = sizes[0] + sizes[1]

            if self.settingsPosition == 'left':
                settingsSize = self._settingsScrollArea.sizeHint().width()
                sizes[0] = settingsSize
                sizes[1] = total - settingsSize
            elif self.settingsPosition == 'right':
                settingsSize = self._settingsScrollArea.sizeHint().width()
                sizes[0] = total - settingsSize
                sizes[1] = settingsSize
            elif self.settingsPosition == 'top':
                settingsSize = self._settingsScrollArea.sizeHint().height()
                sizes[0] = settingsSize
                sizes[1] = total - settingsSize
            elif self.settingsPosition == 'bottom':
                settingsSize = self._settingsScrollArea.sizeHint().height()
                sizes[0] = total - settingsSize
                sizes[1] = settingsSize

            self._splitter.setSizes(sizes)

    def _closeModule(self):
        """Close the module
        """
        try:
            if self.closeFunc:
                self.closeFunc()
        except:
            pass

        # delete any notifiers initiated with this Module
        self.deleteAllNotifiers()

        # GWV 20181201: diabled; bad idea (I put it here!)
        # # Try de-registering any notifiers or object with unRegister() method for notifiers
        # try:
        #     notifiers = [n for n in self.__dict__.values()
        #                    if (isinstance(n, Notifier) or
        #                        isinstance(n, GuiNotifier) or
        #                        isinstance(n, _PulldownABC)
        #                        )]
        #     logger = getLogger()
        #     logger.debug3('>>> notifiers of %s: %s' % (self, notifiers))
        #     for notifier in notifiers:
        #         logger.debug3('>>> unregistering: %s' % notifier)
        #         notifier.unRegister()
        # except:
        #     pass

        getLogger().debug('Closing %s' % str(self.container()))

        if self.maximised:
            self.toggleMaximised()

        if not self._container:
            area = self.mainWindow.moduleArea
            if area:
                if area._container is None:
                    for i in area.children():
                        if isinstance(i, Container):
                            self._container = i

        super().close()

    def enterEvent(self, event):
        if self.mainWindow:
            if self.mainWindow.application.preferences.general.focusFollowsMouse:
                self.setFocus()
                self.label.setModuleHighlight(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.mainWindow:
            if self.mainWindow.application.preferences.general.focusFollowsMouse:
                self.label.setModuleHighlight(False)
        super().enterEvent(event)

    def dragMoveEvent(self, *args):
        ev = args[0]
        if self.isDragToMaximisedModule(ev):
            self.handleDragToMaximisedModule(ev)
            return

        DockDrop.dragMoveEvent(self, *args)

    def dragLeaveEvent(self, *args):
        ev = args[0]
        DockDrop.dragLeaveEvent(self, *args)

    def dragEnterEvent(self, *args):
        ev = args[0]

        if self.isDragToMaximisedModule(ev):
            self.handleDragToMaximisedModule(ev)
            return

        if args:

            # print ('>>>', ev.source())
            data = self.parseEvent(ev)
            if DropBase.PIDS in data and isinstance(data['event'].source(), SideBar):  #(SideBar, SideBar)):
                if self.widgetArea:

                    ld = ev.pos().x()
                    rd = self.width() - ld
                    td = ev.pos().y()
                    bd = self.height() - td

                    mn = min(ld, rd, td, bd)
                    if mn > 30:
                        self.dropArea = "center"
                        self.area._dropArea = "center"

                    elif (ld == mn or td == mn) and mn > self.height() / 3.:
                        self.dropArea = "center"
                        self.area._dropArea = "center"
                    elif (rd == mn or ld == mn) and mn > self.width() / 3.:
                        self.dropArea = "center"
                        self.area._dropArea = "center"

                    elif rd == mn:
                        self.dropArea = "right"
                        self.area._dropArea = "right"
                        ev.accept()
                    elif ld == mn:
                        self.dropArea = "left"
                        self.area._dropArea = "left"
                        ev.accept()
                    elif td == mn:
                        self.dropArea = "top"
                        self.area._dropArea = "top"
                        ev.accept()
                    elif bd == mn:
                        self.dropArea = "bottom"
                        self.area._dropArea = "bottom"
                        ev.accept()

                    if ev.source() is self and self.dropArea == 'center':
                        # print "  no self-center"
                        self.dropArea = None
                        ev.ignore()
                    elif self.dropArea not in self.allowedAreas:
                        # print "  not allowed"
                        self.dropArea = None
                        ev.ignore()
                    else:
                        # print "  ok"
                        ev.accept()
                    self.overlay.setDropArea(self.dropArea)

                    # self.widgetArea.setStyleSheet(self.dragStyle)
                    self.update()
                    # # if hasattr(self, 'drag'):
                    # self.raiseOverlay()
                    # self.updateStyle()
                    # ev.accept()

            src = ev.source()
            if hasattr(src, 'implements') and src.implements('dock'):
                DockDrop.dragEnterEvent(self, *args)

    def dropEvent(self, event):
        if self.inDragToMaximisedModule:
            return

        if event:
            source = event.source()
            data = self.parseEvent(event)
            if hasattr(source, 'implements') and source.implements('dock'):
                CcpnModule._lastActionWasDrop = True
                DockDrop.dropEvent(self, event)
            elif DropBase.PIDS in data and len(data[DropBase.PIDS]) > 0:
                # process Pids
                self.mainWindow._processPids(data, position=self.dropArea, relativeTo=self)
                event.accept()

                # reset the dock area
                self.dropArea = None
                self.overlay.setDropArea(self.dropArea)
                self._selectedOverlay.setDropArea(self.dropArea)
            else:
                event.ignore()
                return

    def _fillDisplayWidget(self):
        ll = ['> select-to-add <'] + [ALL] + [display.pid for display in self.mainWindow.spectrumDisplays]
        self.displaysWidget.pulldownList.setData(texts=ll)

    def _getDisplays(self):
        """
        Return list of displays to navigate - if needed
        """
        displays = []
        # check for valid displays
        gids = self.displaysWidget.getTexts()
        if len(gids) == 0: return displays
        if ALL in gids:
            displays = self.application.ui.mainWindow.spectrumDisplays
        else:
            displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
        return displays

    def _updateStyle(self):
        """
        Copied from the parent class to allow for modification in StyleSheet
        However, that appears not to work (fully);

        GWV: many calls to the updateStyle are triggered during initialization
             probably from paint event
        """

        # Padding apears not to work; overriden somewhere else?
        colours = getColours()

        tempStyle = """CcpnModule {
                      border: 0px;
                   }"""
        self.setStyleSheet(tempStyle)

    def findWindow(self):
        current = self
        while current.parent() != None:
            current = current.parent()
        return current

    def flashMessage(self, message):
        def center(window, rect):
            # https://wiki.qt.io/How_to_Center_a_Window_on_the_Screen

            window.setGeometry(
                    QtWidgets.QStyle.alignedRect(
                            QtCore.Qt.LeftToRight,
                            QtCore.Qt.AlignCenter,
                            window.size(),
                            rect,
                            )
                    )

        messageBox = QtWidgets.QMessageBox(self)
        messageBox.setText(message)
        messageBox.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        for button in messageBox.findChildren(QtWidgets.QDialogButtonBox):
            button.setVisible(False)

        messageBox.update()

        globalRect = QtCore.QRect(self.mapToGlobal(self.rect().topLeft()), self.rect().size())
        wrapper = partial(center, messageBox, globalRect)
        QtCore.QTimer.singleShot(0, wrapper)

        timer = QtCore.QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(messageBox.close)
        timer.start(1500)

        messageBox.exec()

    def startDrag(self):

        self.drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        self.drag.setMimeData(mime)
        dragPixmap = self.grab()
        self.drag.setPixmap(dragPixmap.scaledToWidth(128) if dragPixmap.width() < dragPixmap.height() else dragPixmap.scaledToHeight(128))
        self.widgetArea.setStyleSheet(self.dragStyle)
        self._raiseSelectedOverlay()
        self.updateStyle()
        self.update()

        self.drag.destroyed.connect(self._destroyed)

        # GST doesn't work in the current version but should work in 5.13
        forbiddenCursorPixmap = QtGui.QCursor(QtCore.Qt.ForbiddenCursor).pixmap()
        self.drag.setDragCursor(forbiddenCursorPixmap, QtCore.Qt.IgnoreAction)

        dragResult = self.drag.exec_()
        endPosition = QtGui.QCursor.pos()

        self.updateStyle()

        # GST we have to assume the drag succeeded currently as we don't get any events
        # that report on whether the drag has failed. Indeed this effectivley a failed drag...
        globalDockRect = self.getDockArea().frameGeometry()

        targetWidget = QtWidgets.QApplication.instance().widgetAt(endPosition)
        if (self.drag.target() is None) and (not globalDockRect.contains(endPosition)):
            if targetWidget == None:
                self.float()
                window = self.findWindow()
                window.move(endPosition)

                # this is because we could have have dragged into another application
                # this may not work under windows
                originalWindow = self.findWindow()
                originalWindow.raise_()
                originalWindow.show()
                originalWindow.activateWindow()

                window.raise_()
                window.show()
                window.activateWindow()

    def _destroyed(self, ev):
        self._selectedOverlay.setDropArea(None)

    def _raiseSelectedOverlay(self):
        self._selectedOverlay.setDropArea(True)
        self._selectedOverlay.raise_()

    def resizeEvent(self, ev):
        self._selectedOverlay._resize()
        super().resizeEvent(ev)

    #=========================================================================================
    # CCPN Properties
    #=========================================================================================

    def __repr__(self):
        return "<Module:%s>" % self.name()

    @property
    def pid(self) -> str:
        """Identifier for the object, unique within the project - added to give label to ccpnModules
        """
        return "Module:%s" % self.name()


class CcpnModuleLabel(DockLabel):
    """
    Subclassing DockLabel to modify appearance and functionality
    """

    labelSize = 16
    TOP_LEFT = 'TOP_LEFT'
    TOP_RIGHT = 'TOP_RIGHT'

    # TODO:GEERTEN check colours handling
    # defined here, as the updateStyle routine is called from the
    # DockLabel instanciation; changed later on

    sigDragEntered = QtCore.Signal(object, object)

    def getMaxIconSize(self, icon):
        iconSizes = [max((size.height(), size.width())) for size in icon.availableSizes()]
        return max(iconSizes)

    def __init__(self, name, module, showCloseButton=True, closeCallback=None, showSettingsButton=False, settingsCallback=None):

        self.buttonBorderWidth = 1
        self.buttonIconMargin = 1
        self.buttonCornerRadius = 3
        self.labelRadius = 3

        super(CcpnModuleLabel, self).__init__(name, module, showCloseButton=showCloseButton)

        self.module = module
        self.fixedWidth = True

        from ccpn.framework.Application import getApplication

        getApp = getApplication()
        if getApp:
            self.setFont(getApp._fontSettings.moduleLabelFont)
            self.labelSize = QtGui.QFontMetrics(getApp._fontSettings.moduleLabelFont).height() + 4
        else:
            self.labelSize = 16
        self.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.closeButton.setStyleSheet('''border: 0px solid #a9a9a9;
                                          border-radius: 1px;
                                          background-color: transparent; ''')

        # self.setStyleSheet('margin : 2')

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLineWidth(0)

        if showCloseButton:
            # button is already there because of the DockLabel init
            self.closeButton.setIconSize(QtCore.QSize(self.labelSize, self.labelSize))

            if closeCallback is None:
                raise RuntimeError('Requested closeButton without callback')
            else:
                self.closeButton.clicked.connect(closeCallback)
            self.setupLabelButton(self.closeButton, 'close_cross', CcpnModuleLabel.TOP_RIGHT)

        # Settings
        if showSettingsButton:
            self.settingsButton = ToolButton(self)
            self.setupLabelButton(self.settingsButton, 'settings_cog', CcpnModuleLabel.TOP_LEFT)

            if settingsCallback is None:
                raise RuntimeError('Requested settingsButton without callback')
            else:
                self.settingsButton.clicked.connect(settingsCallback)

        self.updateStyle()

        # flag to disable dragMoveEvent during a doubleClick
        self._inDoubleClick = False

    def setupLabelButton(self, button, iconName, position):
        icon = Icon('icons/%s' % iconName)

        button.setIcon(icon)
        retinaIconSize = self.getMaxIconSize(icon) // 2
        retinaIconSize = self.labelSize - 4

        button.setIconSize(QtCore.QSize(retinaIconSize, retinaIconSize))

        if position == CcpnModuleLabel.TOP_RIGHT:
            styleInfo = (self.buttonBorderWidth, 0, self.buttonCornerRadius)
        elif position == CcpnModuleLabel.TOP_LEFT:
            styleInfo = (self.buttonBorderWidth, self.buttonCornerRadius, 0)
        else:
            raise Exception('button position must be one of %s' % ', '.join(CcpnModule.TOP_LEFT, CcpnModule.TOP_RIGHT))

        # GST colours are hard coded... help please I need  a central source for
        # these presumably a color palette or scheme
        button.setStyleSheet(''' border: %ipx solid #a9a9a9 ;
                                 border-top-left-radius: %ipx;
                                 border-top-right-radius: %ipx;
                                 border-bottom-left-radius: 0px;
                                 border-bottom-right-radius: 0px;
                                 background-color: #ececec ;  ''' % styleInfo)
        buttonSize = retinaIconSize + (self.buttonBorderWidth * 2) + (self.buttonIconMargin * 2)
        button.setMinimumSize(QtCore.QSize(buttonSize, buttonSize))
        button.setMaximumSize(QtCore.QSize(buttonSize, buttonSize))
        button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def setModuleHighlight(self, hightlighted=False):
        self.setDim(hightlighted)

    def updateStyle(self):

        # get the colours from the colourScheme
        if self.dim:
            fg = getColours()[CCPNMODULELABEL_FOREGROUND]
            bg = getColours()[CCPNMODULELABEL_BACKGROUND]
            border = getColours()[CCPNMODULELABEL_BORDER]
        else:
            fg = getColours()[CCPNMODULELABEL_FOREGROUND_ACTIVE]
            bg = getColours()[CCPNMODULELABEL_BACKGROUND_ACTIVE]
            border = getColours()[CCPNMODULELABEL_BORDER_ACTIVE]

        if self.orientation == 'vertical':
            self.vStyle = """DockLabel {
                background-color : %s;
                color : %s;
                border-top-right-radius: 2px;
                border-top-left-radius: %s;
                border-bottom-right-radius: 2px;
                border-bottom-left-radius: %s;
            }""" % (bg, fg, self.labelRadius, self.labelRadius)
            self.setStyleSheet(self.vStyle)
        else:
            self.hStyle = """DockLabel {
                background-color : %s;
                color : %s;
                border-top-right-radius: %s;
                border-top-left-radius: %s;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 0px;
            }""" % (bg, fg, self.labelRadius, self.labelRadius)
            self.setStyleSheet(self.hStyle)

    def _createContextMenu(self):

        contextMenu = Menu('', self, isFloatWidget=True)
        contextMenu.addAction('Close', self.module._closeModule)
        if len(self.module.mainWindow.moduleArea.ccpnModules) > 1:
            contextMenu.addAction('Close Others', partial(self.module.mainWindow.moduleArea._closeOthers, self.module))
            contextMenu.addAction('Close All', self.module.mainWindow.moduleArea._closeAll)

        # numDocks = len(self.module.getDocksInParentArea())
        #
        # if not self.module.maximised and numDocks > 1:
        #     contextMenu.addAction('Maximise', self.module.toggleMaximised)
        # elif self.module.maximised:
        #     contextMenu.addAction('Restore', self.module.toggleMaximised)
        #
        # contextMenu.addAction('Float', self.module.float)

        return contextMenu

    def _modulesMenu(self, menuName, module):

        menu = Menu(menuName.title(), self, isFloatWidget=True)
        if module:
            toAll = menu.addAction('All', partial(module.mainWindow.moduleArea.moveModule, module, menuName, None))
            for availableModule in module.mainWindow.moduleArea.ccpnModules:
                if availableModule != module:
                    toModule = menu.addAction(str(availableModule.name()),
                                              partial(module.mainWindow.moduleArea.moveModule, module, menuName, availableModule))
            return menu

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """
        Re-implementation of the  mouse event so a right mouse context menu can be raised.
        """
        if event.button() == QtCore.Qt.RightButton:
            menu = self._createContextMenu()
            if menu:
                menu.move(event.globalPos().x(), event.globalPos().y() + 10)
                menu.exec()
        else:
            super(CcpnModuleLabel, self).mousePressEvent(event)

    def paintEvent(self, ev):
        """
        Copied from the parent VerticalLabel class to allow for modification in StyleSheet
        """
        p = QtGui.QPainter(self)

        # GWV: this moved the label in vertical mode and horizontal, after some trial and error
        # NOTE: A QRect can be constructed with a set of left, top, width and height integers
        if self.orientation == 'vertical':
            added = 2
            p.rotate(-90)
            rgn = QtCore.QRect(-self.height(), 0, self.height(), self.width() + added)
        else:
            rgn = self.contentsRect()
            added = 4
            rgn = QtCore.QRect(rgn.left(), rgn.top(), rgn.width(), rgn.height() + added)

        #align = self.alignment()
        # GWV adjusted
        align = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter

        self.hint = p.drawText(rgn, align, self.text())
        p.end()

        if self.orientation == 'vertical':
            self.setMinimumWidth(self.labelSize)
            self.setMaximumWidth(self.labelSize)
        else:
            self.setMinimumHeight(self.labelSize)
            self.setMaximumHeight(self.labelSize)

    def mouseMoveEvent(self, ev):
        """Handle the mouse move event to spawn a drag event
        """
        if hasattr(self, 'pressPos') and not self._inDoubleClick:
            if not self.startedDrag and (ev.pos() - self.pressPos).manhattanLength() > QtWidgets.QApplication.startDragDistance():
                # emit a drag started event
                self.sigDragEntered.emit(self.parent(), ev)
                self.dock.startDrag()

            ev.accept()

    def mouseDoubleClickEvent(self, ev):
        """Handle the double click event
        """
        # start a small timer when doubleClicked
        # disables the dragMoveEvent whilst in a doubleClick
        self._inDoubleClick = True
        QtCore.QTimer.singleShot(QtWidgets.QApplication.instance().doubleClickInterval() * 2,
                                 self._resetDoubleClick)

        super(CcpnModuleLabel, self).mouseDoubleClickEvent(ev)

        # if ev.button() == QtCore.Qt.LeftButton:
        #     self.dock.toggleMaximised()

    def _resetDoubleClick(self):
        """reset the double click flag
        """
        self._inDoubleClick = False

    def resizeEvent(self, ev):
        if hasattr(self, 'closeButton') and self.closeButton:
            if self.orientation == 'vertical':
                self.layout().addWidget(self.closeButton, 0, 0, alignment=QtCore.Qt.AlignTop)
            else:
                self.layout().addWidget(self.closeButton, 0, 3, alignment=QtCore.Qt.AlignRight)

        if hasattr(self, 'settingsButton') and self.settingsButton:
            if self.orientation == 'vertical':
                self.layout().addWidget(self.settingsButton, 0, 0, alignment=QtCore.Qt.AlignBottom)
            else:
                self.layout().addWidget(self.settingsButton, 0, 0, alignment=QtCore.Qt.AlignLeft)

        super(DockLabel, self).resizeEvent(ev)


class DropAreaSelectedOverlay(QtWidgets.QWidget):
    """Overlay widget that draws highlight over the current module during a drag-drop operation
    """

    def __init__(self, parent):
        """Initialise widget
        """
        QtWidgets.QWidget.__init__(self, parent)
        self.dropArea = None
        self.hide()
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

    def setDropArea(self, area):
        """Set the widget coverage, either hidden, or a rectangle covering the module
        """
        self.dropArea = area
        if area is None:
            self.hide()
        else:
            prgn = self.parent().rect()
            rgn = QtCore.QRect(prgn)

            self.setGeometry(rgn)
            self.show()

        self.update()

    def _resize(self):
        """Resize the overlay, sometimes the overlay is temporarily visible while the module is moving
        """
        # called from ccpnModule during resize to update rect()
        self.setDropArea(self.dropArea)

    def paintEvent(self, ev):
        """Paint the overlay to the screen
        """
        if self.dropArea is None:
            return

        # create a transparent rectangle and painter over the widget
        p = QtGui.QPainter(self)
        rgn = self.rect()

        p.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 255, 50)))
        p.setPen(QtGui.QPen(QtGui.QColor(50, 50, 150), 3))
        p.drawRect(rgn)
