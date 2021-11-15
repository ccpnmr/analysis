"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-11-15 16:30:39 +0000 (Mon, November 15, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-06-15 10:06:31 +0000 (Mon, June 15, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from ccpn.util.Logging import getLogger
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Spectrum import Spectrum
from ccpn.core.PeakList import PeakList
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Note import Note
from ccpn.core.Sample import Sample
from ccpn.core.IntegralList import IntegralList
from ccpn.core.NmrChain import NmrChain
from ccpn.core.Chain import Chain
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.core.RestraintTable import RestraintTable
from ccpn.core.DataTable import DataTable
from ccpn.core.Collection import Collection
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning
from ccpn.ui.gui.popups.ChainPopup import ChainPopup
from ccpn.ui.gui.popups.ChemicalShiftListPopup import ChemicalShiftListEditor
from ccpn.ui.gui.popups.ComplexEditorPopup import ComplexEditorPopup
from ccpn.ui.gui.popups.CreateChainPopup import CreateChainPopup
from ccpn.ui.gui.popups.CreateNmrChainPopup import CreateNmrChainPopup
from ccpn.ui.gui.popups.StructureDataPopup import StructureDataPopup
from ccpn.ui.gui.popups.IntegralListPropertiesPopup import IntegralListPropertiesPopup
from ccpn.ui.gui.popups.MultipletListPropertiesPopup import MultipletListPropertiesPopup
from ccpn.ui.gui.popups.NmrAtomPopup import NmrAtomEditPopup, NmrAtomNewPopup
from ccpn.ui.gui.popups.NmrChainPopup import NmrChainPopup
from ccpn.ui.gui.popups.AtomPopup import AtomNewPopup, AtomEditPopup
from ccpn.ui.gui.popups.NmrResiduePopup import NmrResidueEditPopup, NmrResidueNewPopup
from ccpn.ui.gui.popups.NotesPopup import NotesPopup
from ccpn.ui.gui.popups.PeakListPropertiesPopup import PeakListPropertiesPopup
from ccpn.ui.gui.popups.RestraintTablePopup import RestraintTableEditPopup, RestraintTableNewPopup
from ccpn.ui.gui.popups.SampleComponentPropertiesPopup import SampleComponentPopup
from ccpn.ui.gui.popups.SamplePropertiesPopup import SamplePropertiesPopup
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpn.ui.gui.popups.StructureEnsemblePopup import StructureEnsemblePopup
from ccpn.ui.gui.popups.SubstancePropertiesPopup import SubstancePropertiesPopup
from ccpn.ui.gui.popups.DataTablePopup import DataTablePopup
from ccpn.ui.gui.popups.CollectionPopup import CollectionPopup
from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking, \
    undoBlockWithoutSideBar, undoStackBlocking


MAXITEMLOGGING = 2


class CreateNewObjectABC():
    """
    An ABC to implement an abstract callback function to create new object
    The __call__(self, dataPid, node) method acts as the callback function
    """

    # These should be subclassed
    parentMethodName = None  # The name of the method in the parent class

    # This can be subclassed
    def getObj(self):
        """returns obj from node or None"""
        return self.node.obj

    def __init__(self, **kwds):
        # store keyword as attributes and as dict; acts as partial to popupClass
        for key, value in kwds.items():
            setattr(self, key, value)
        self.kwds = kwds
        # these get set upon callback
        self.node = None
        self.dataPid = None

    def __call__(self, mainWindow, dataPid, node):
        self.node = node
        self.dataPid = dataPid
        obj = self.getObj()
        # generate the new object
        func = getattr(obj, self.parentMethodName)
        if func is None:
            raise RuntimeError('Undefined function; cannot create new object (%s)' % dataPid)
        newObj = func(**self.kwds)
        return newObj


class _createNewStructureData(CreateNewObjectABC):
    parentMethodName = 'newStructureData'


class _createNewPeakList(CreateNewObjectABC):
    parentMethodName = 'newPeakList'


class _createNewChemicalShiftList(CreateNewObjectABC):
    parentMethodName = 'newChemicalShiftList'


class _createNewMultipletList(CreateNewObjectABC):
    parentMethodName = 'newMultipletList'


class _createNewNmrResidue(CreateNewObjectABC):
    parentMethodName = 'newNmrResidue'


class _createNewNmrAtom(CreateNewObjectABC):
    parentMethodName = 'newNmrAtom'


class _createNewComplex(CreateNewObjectABC):
    parentMethodName = 'newComplex'


class _createNewRestraintTable(CreateNewObjectABC):
    parentMethodName = 'newRestraintTable'


class _createNewNote(CreateNewObjectABC):
    parentMethodName = 'newNote'


class _createNewIntegralList(CreateNewObjectABC):
    parentMethodName = 'newIntegralList'


class _createNewSample(CreateNewObjectABC):
    parentMethodName = 'newSample'


class _createNewSampleComponent(CreateNewObjectABC):
    parentMethodName = 'newSampleComponent'


class _createNewSubstance(CreateNewObjectABC):
    parentMethodName = 'newSubstance'


class _createNewStructureEnsemble(CreateNewObjectABC):
    parentMethodName = 'newStructureEnsemble'


class _createNewDataTable(CreateNewObjectABC):
    parentMethodName = 'newDataTable'


class _createNewCollection(CreateNewObjectABC):
    parentMethodName = 'newCollection'


class RaisePopupABC():
    """
    An ABC to implement an abstract popup class
    The __call__(self, dataPid, node) method acts as the callback function
    """

    # These should be subclassed
    popupClass = None  # a sub-class of CcpNmrDialog; used to generate a popup
    objectArgumentName = 'obj'  # argument name set to obj passed to popupClass instantiation
    parentObjectArgumentName = None  # parent argument name set to obj passed to popupClass instantiation when useParent==True

    # This can be subclassed
    def getObj(self):
        """returns obj from node or None
        """
        obj = None if self.useNone else self.node.obj
        return obj

    def __init__(self, useParent=False, useNone=False, **kwds):
        """store kwds; acts as partial to popupClass
        useParent: use parentObjectArgumentName for passing obj to popupClass
        useNone: set obj to None
        """
        self.useParent = useParent  # Use parent of object
        if useParent and self.parentObjectArgumentName == None:
            raise RuntimeError('useParent==True requires definition of parentObjectArgumentName (%s)' % self)
        self.useNone = useNone
        self.kwds = kwds
        # these get set upon callback
        self.node = None
        self.dataPid = None

    def __call__(self, mainWindow, dataPid, node):
        self.node = node
        self.dataPid = dataPid
        obj = self.getObj()
        if self.useParent:
            self.kwds[self.parentObjectArgumentName] = obj
        else:
            self.kwds[self.objectArgumentName] = obj

        popup = self.popupClass(parent=node.sidebar, mainWindow=mainWindow,
                                **self.kwds)
        popup.exec()
        popup.raise_()


class _raiseNewChainPopup(RaisePopupABC):
    popupClass = CreateChainPopup
    parentObjectArgumentName = 'project'


class _raiseChainPopup(RaisePopupABC):
    popupClass = ChainPopup


class _raiseComplexEditorPopup(RaisePopupABC):
    popupClass = ComplexEditorPopup


class _raiseStructureDataPopup(RaisePopupABC):
    popupClass = StructureDataPopup
    # objectArgumentName = 'obj'


class _raiseChemicalShiftListPopup(RaisePopupABC):
    popupClass = ChemicalShiftListEditor
    # objectArgumentName = 'chemicalShiftList'


class _raisePeakListPopup(RaisePopupABC):
    popupClass = PeakListPropertiesPopup
    objectArgumentName = 'peakList'
    parentObjectArgumentName = 'spectrum'


class _raiseMultipletListPopup(RaisePopupABC):
    popupClass = MultipletListPropertiesPopup
    objectArgumentName = 'multipletList'
    parentObjectArgumentName = 'spectrum'


class _raiseCreateNmrChainPopup(RaisePopupABC):
    popupClass = CreateNmrChainPopup
    objectArgumentName = 'project'


class _raiseNmrChainPopup(RaisePopupABC):
    popupClass = NmrChainPopup
    # objectArgumentName = 'nmrChain'


class _raiseNmrResiduePopup(RaisePopupABC):
    popupClass = NmrResidueEditPopup
    # objectArgumentName = 'nmrResidue'


class _raiseNmrResidueNewPopup(RaisePopupABC):
    popupClass = NmrResidueNewPopup
    # objectArgumentName = 'nmrResidue'


class _raiseNmrAtomPopup(RaisePopupABC):
    popupClass = NmrAtomEditPopup
    # objectArgumentName = 'nmrAtom'


class _raiseNmrAtomNewPopup(RaisePopupABC):
    popupClass = NmrAtomNewPopup
    # objectArgumentName = 'nmrAtom'


class _raiseAtomPopup(RaisePopupABC):
    popupClass = AtomEditPopup
    # objectArgumentName = 'Atom'


class _raiseAtomNewPopup(RaisePopupABC):
    popupClass = AtomNewPopup
    # objectArgumentName = 'Atom'


class _raiseNotePopup(RaisePopupABC):
    popupClass = NotesPopup
    # objectArgumentName = 'obj'


class _raiseIntegralListPopup(RaisePopupABC):
    popupClass = IntegralListPropertiesPopup
    objectArgumentName = 'integralList'
    parentObjectArgumentName = 'spectrum'


class _raiseRestraintTableEditPopup(RaisePopupABC):
    popupClass = RestraintTableEditPopup
    # objectArgumentName = 'restraintTable'
    parentObjectArgumentName = 'structureData'


class _raiseRestraintTableNewPopup(_raiseRestraintTableEditPopup):
    popupClass = RestraintTableNewPopup


class _raiseSamplePopup(RaisePopupABC):
    popupClass = SamplePropertiesPopup
    objectArgumentName = 'sample'


class _raiseSampleComponentPopup(RaisePopupABC):
    popupClass = SampleComponentPopup
    # NB This popup is structured slightly different, passing in different arguments
    objectArgumentName = 'sampleComponent'
    parentObjectArgumentName = 'sample'


class _raiseSpectrumPopup(RaisePopupABC):
    popupClass = SpectrumPropertiesPopup
    objectArgumentName = 'spectrum'


class _raiseSpectrumGroupEditorPopup(RaisePopupABC):
    popupClass = SpectrumGroupEditor

    def _execOpenItem(self, mainWindow):
        """Acts as the entry point for opening items in ccpnModuleArea
        """
        popup = self.popupClass(parent=mainWindow, mainWindow=mainWindow,
                                **self.kwds)
        popup.exec()
        popup.raise_()


class _raiseStructureEnsemblePopup(RaisePopupABC):
    popupClass = StructureEnsemblePopup
    # objectArgumentName = 'obj'


class _raiseSubstancePopup(RaisePopupABC):
    popupClass = SubstancePropertiesPopup
    objectArgumentName = 'substance'


class _raiseDataTablePopup(RaisePopupABC):
    popupClass = DataTablePopup
    # objectArgumentName = 'obj'


class _raiseCollectionPopup(RaisePopupABC):
    popupClass = CollectionPopup
    # objectArgumentName = 'obj'


class OpenItemABC():
    """
    An ABC to implement an abstract openItem in moduleArea class
    The __call__(self, dataPid, node) method acts as the callback function
    """

    # These should be subclassed
    openItemMethod = None  # a method to open the item in ccpnModuleArea
    objectArgumentName = 'obj'  # argument name set to obj passed to openItemClass instantiation
    openItemDirectMethod = None  # parent argument name set to obj passed to openItemClass instantiation when useParent==True
    useApplication = True
    hasOpenMethod = True
    contextMenuText = 'Open as a Module'

    validActionTargets = (Spectrum, PeakList, MultipletList, IntegralList,
                          NmrChain, Chain, SpectrumGroup, Sample, ChemicalShiftList,
                          RestraintTable, Note, StructureEnsemble, DataTable, Collection
                          )

    # This can be subclassed
    def getObj(self):
        """returns obj from node or None
        """
        obj = None if self.useNone else self.node.obj
        return obj

    def __init__(self, useNone=False, **kwds):
        """store kwds; acts as partial to openItemClass
        useApplication: if true, use the method attached to application
                     : if false, use openItemDirectMethod for opening object in ccpnModuleArea
        useNone: set obj to None
        """
        if self.useApplication is False and self.openItemDirectMethod is None:
            raise RuntimeError('useApplication==False requires definition of openItemDirectMethod (%s)' % self)
        self.useNone = useNone
        self.kwds = kwds
        # these get set upon callback
        self.node = None
        self.dataPid = None
        self.mainWindow = None
        self.openAction = None

    def __call__(self, mainWindow, dataPid, node, position, objs):
        """__Call__ acts is the execute entry point for the callback.
        """
        self.node = node
        self.dataPid = dataPid
        obj = self.getObj()
        self.kwds[self.objectArgumentName] = obj
        self.mainWindow = mainWindow

        self._initialise(dataPid, objs)
        self._openContextMenu(node.sidebar, position, objs)

    def _execOpenItem(self, mainWindow, obj):
        """Acts as an entry point for opening items in ccpnModuleArea
        """
        self.node = None
        self.dataPid = obj.pid
        self.kwds[self.objectArgumentName] = obj
        self.mainWindow = mainWindow

        self._initialise(obj.pid, [obj])
        return self.openAction()

    def _initialise(self, dataPid, objs):
        """Initialise settings for the object.
        """
        self.application = self.mainWindow.application
        openableObjs = [obj for obj in objs if isinstance(obj, self.validActionTargets)]

        if self.hasOpenMethod and len(openableObjs) > 0:
            if self.useApplication:
                func = getattr(self.application, self.openItemMethod)
            else:
                func = self.openItemDirectMethod

            if func is None:
                raise RuntimeError('Undefined function; cannot open object (%s)' % dataPid)

            self.openAction = partial(func, **self.kwds)

    def _openContextMenu(self, parentWidget, position, objs):
        """Open a context menu.
        """
        contextMenu = Menu('', parentWidget, isFloatWidget=True)
        if self.openAction:
            contextMenu.addAction(self.contextMenuText, self.openAction)

        spectra = [obj for obj in objs if isinstance(obj, Spectrum)]
        if len(spectra) > 0:
            contextMenu.addAction('Make SpectrumGroup From Selected',
                                  partial(_raiseSpectrumGroupEditorPopup(useNone=True, editMode=False, defaultItems=spectra),
                                          self.mainWindow, self.getObj(), self.node))

        contextMenu.addAction('Copy Pid to clipboard', partial(self._copyPidsToClipboard, objs))
        self._addCollectionMenu(contextMenu, objs)
        contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))
        canBeCloned = True
        for obj in objs:
            if not hasattr(obj, 'clone'):  # TODO: possibly should check that is a method...
                canBeCloned = False
                break
        if canBeCloned:
            contextMenu.addAction('Clone', partial(self._cloneObject, objs))

        contextMenu.addSeparator()
        contextMenu.addAction('Edit Properties', partial(parentWidget._raiseObjectProperties, self.node.widget))

        contextMenu.move(position)
        contextMenu.exec()

    def _cloneObject(self, objs):
        """Clones the specified objects.
        """
        for obj in objs:
            obj.clone()

    def _deleteItemObject(self, objs):
        """Delete items from the project.
        """

        try:
            if len(objs) > 0:
                getLogger().info('Deleting: %s' % ', '.join(map(str, objs)))
                project = objs[-1].project
                with undoBlockWithoutSideBar():
                    with notificationEchoBlocking():
                        project.deleteObjects(*objs)
            # with undoBlock():
            #     for obj in objs:
            #         if obj:
            #             # just delete the object
            #             obj.delete()
        except Exception as es:
            showWarning('Delete', str(es))

    def _copyPidsToClipboard(self, objs):
        """
        :param objs:
        Copy to clipboard quoted pids
        """
        from ccpn.util.Common import copyToClipboard

        copyToClipboard(objs)

    def _addCollectionMenu(self, menu, objs):
        """Add a quick submenu containing a list of collections
        """
        # create subMenu for adding selected items to a single collection
        subMenu = menu.addMenu('Add to Collection')
        collections = self.mainWindow.application.project.collections
        for col in collections:
            # only select items that are in the collection
            _objs = [obj for obj in objs if obj not in col.items]
            if _objs:
                # add action to add to the collection
                subMenu.addAction(col.pid, partial(col.addItems, _objs))
        if not len(subMenu.actions()):
            # disable menu if empty
            subMenu.setEnabled(False)

        # create subMenu for removing selected items from a single collection - items are not deleted
        subMenu = menu.addMenu('Remove from Collection')
        collections = self.mainWindow.application.project.collections
        for col in collections:
            # only select items that are in the collection
            _objs = [obj for obj in objs if obj in col.items]
            if _objs:
                # add action to remove from the collection
                subMenu.addAction(col.pid, partial(col.removeItems, _objs))
        if not len(subMenu.actions()):
            # disable menu if empty
            subMenu.setEnabled(False)

    def _addToCollection(self, objs):
        """Add the objects to a collection
        Show popup to allow adding objects to specified collection
        For later when a more complex selector is required

        :param objs: list of sidebar objects
        """
        collectionPopup = AddToCollectionPopup(mainWindow=self.mainWindow, project=None, on_top=True)
        collectionPopup.hide()

        # show the collection popup
        pos = QtGui.QCursor().pos()
        mouse_screen = None
        for screen in QtGui.QGuiApplication.screens():
            if screen.geometry().contains(pos):
                mouse_screen = screen
                break
        collectionPopup.showAt(pos, preferred_side=Side.RIGHT,
                              side_priority=(Side.TOP, Side.BOTTOM, Side.RIGHT, Side.LEFT),
                              target_screen=mouse_screen)


from ccpn.ui.gui.widgets.SpeechBalloon import SpeechBalloon, Side
from PyQt5 import QtCore, QtGui
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label


class AddToCollectionPopup(SpeechBalloon):
    """Balloon to hold the collection list
    For later when a more complex selector is required
    """

    def __init__(self, mainWindow=None, project=None, *args, **kwds):
        super().__init__(*args, **kwds)

        # simplest way to make the popup function as modal and disappear as required
        self.setWindowFlags(int(self.windowFlags()) | QtCore.Qt.Popup)
        self._mainWindow = mainWindow
        self._project = project

        # hide the speech pointer
        self._metrics.pointer_height = 0
        self._metrics.pointer_width = 0
        self._metrics.corner_radius = 2

        # add a small widget to the centre
        fr = Frame(self, setLayout=True)
        Label(fr, text='Test collection popup', grid=(0, 0))
        self.setCentralWidget(fr)


class _openItemChemicalShiftListTable(OpenItemABC):
    openItemMethod = 'showChemicalShiftTable'
    objectArgumentName = 'chemicalShiftList'

    def _openContextMenu(self, parentWidget, position, objs):
        """Open a context menu.
        """
        contextMenu = Menu('', parentWidget, isFloatWidget=True)
        if self.openAction:
            contextMenu.addAction(self.contextMenuText, self.openAction)
        contextMenu.addAction('Copy Pid to clipboard', partial(self._copyPidsToClipboard, objs))
        self._addCollectionMenu(contextMenu, objs)
        contextMenu.addAction('Duplicate', partial(self._duplicateAction, objs))
        contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))

        contextMenu.addSeparator()
        contextMenu.addAction('Edit Properties', partial(parentWidget._raiseObjectProperties, self.node.widget))

        contextMenu.move(position)
        contextMenu.exec()

    def _duplicateAction(self, objs):
        for obj in objs:
            obj.duplicate()


class _openItemPeakListTable(OpenItemABC):
    openItemMethod = 'showPeakTable'
    objectArgumentName = 'peakList'


class _openItemIntegralListTable(OpenItemABC):
    openItemMethod = 'showIntegralTable'
    objectArgumentName = 'integralList'


class _openItemMultipletListTable(OpenItemABC):
    openItemMethod = 'showMultipletTable'
    objectArgumentName = 'multipletList'


class _openItemNmrChainTable(OpenItemABC):
    openItemMethod = 'showNmrResidueTable'
    objectArgumentName = 'nmrChain'


class _openItemNmrResidueItem(OpenItemABC):
    objectArgumentName = 'nmrResidue'
    hasOpenMethod = False


class _openItemNmrAtomItem(OpenItemABC):
    objectArgumentName = 'nmrAtom'
    hasOpenMethod = False


class _openItemAtomItem(OpenItemABC):
    objectArgumentName = 'Atom'
    hasOpenMethod = False

    def _openContextMenu(self, parentWidget, position, objs):
        """Open a context menu.
        """
        contextMenu = Menu('', parentWidget, isFloatWidget=True)
        if self.openAction:
            contextMenu.addAction(self.contextMenuText, self.openAction)
        contextMenu.addAction('Copy Pid to clipboard', partial(self._copyPidsToClipboard, objs))
        self._addCollectionMenu(contextMenu, objs)

        contextMenu.addSeparator()
        contextMenu.addAction('Edit Properties', partial(parentWidget._raiseObjectProperties, self.node.widget))

        contextMenu.move(position)
        contextMenu.exec()


class _openItemChainTable(OpenItemABC):
    openItemMethod = 'showResidueTable'
    objectArgumentName = 'chain'


class _openItemResidueTable(OpenItemABC):
    objectArgumentName = 'residue'
    hasOpenMethod = False

    def _openContextMenu(self, parentWidget, position, objs):
        """Open a context menu.
        """
        contextMenu = Menu('', parentWidget, isFloatWidget=True)
        if self.openAction:
            contextMenu.addAction(self.contextMenuText, self.openAction)
        contextMenu.addAction('Copy Pid to clipboard', partial(self._copyPidsToClipboard, objs))
        self._addCollectionMenu(contextMenu, objs)

        contextMenu.addSeparator()
        contextMenu.addAction('Edit Properties', partial(parentWidget._raiseObjectProperties, self.node.widget))

        contextMenu.move(position)
        contextMenu.exec()


class _openItemNoteTable(OpenItemABC):
    openItemMethod = 'showNotesEditor'
    objectArgumentName = 'note'


class _openItemRestraintTable(OpenItemABC):
    openItemMethod = 'showRestraintTable'
    objectArgumentName = 'restraintTable'


class _openItemStructureDataTable(OpenItemABC):
    objectArgumentName = 'structureData'
    hasOpenMethod = False


class _openItemComplexTable(OpenItemABC):
    objectArgumentName = 'complex'
    hasOpenMethod = False


class _openItemSubstanceTable(OpenItemABC):
    objectArgumentName = 'substance'
    hasOpenMethod = False


class _openItemSampleComponentTable(OpenItemABC):
    objectArgumentName = 'sampleComponent'
    hasOpenMethod = False


class _openItemSampleDisplay(OpenItemABC):
    openItemMethod = None
    useApplication = False
    objectArgumentName = 'sample'
    contextMenuText = 'Open linked spectra'

    @staticmethod
    def _openSampleSpectraOnDisplay(sample, spectrumDisplay, autoRange=False):
        # with undoBlockWithoutSideBar():
        with undoStackBlocking() as _:  # Do not add to undo/redo stack
            with notificationEchoBlocking():
                if len(sample.spectra) > 0:
                    if len(spectrumDisplay.strips) > 0:
                        spectrumDisplay.clearSpectra()
                        for sampleComponent in sample.sampleComponents:
                            if sampleComponent.substance is not None:
                                for spectrum in sampleComponent.substance.referenceSpectra:
                                    spectrumDisplay.displaySpectrum(spectrum)
                        for spectrum in sample.spectra:
                            spectrumDisplay.displaySpectrum(spectrum)
                        if autoRange:
                            spectrumDisplay.autoRange()

    def _openSampleSpectra(self, sample, position=None, relativeTo=None):
        """Add spectra linked to sample and sampleComponent. Particularly used for screening
        """
        mainWindow = self.mainWindow

        if len(sample.spectra) > 0:
            spectrumDisplay = mainWindow.newSpectrumDisplay(sample.spectra[0])
            mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)
            self._openSampleSpectraOnDisplay(sample, spectrumDisplay, autoRange=True)
            mainWindow.application.current.strip = spectrumDisplay.strips[0]

    openItemDirectMethod = _openSampleSpectra


# def _setSpectrumDisplayNotifiers(spectrumDisplay, value):
#     """Blank all spectrumDisplay and contained strip notifiers
#     """
#     spectrumDisplay.setBlankingAllNotifiers(value)
#     for strip in spectrumDisplay.strips:
#         strip.setBlankingAllNotifiers(value)


class _openItemSpectrumDisplay(OpenItemABC):
    openItemMethod = None
    useApplication = False
    objectArgumentName = 'spectrum'

    def _openSpectrumDisplay(self, spectrum=None, position=None, relativeTo=None):
        mainWindow = self.mainWindow
        current = mainWindow.application.current

        # check whether a new spectrumDisplay is needed, and check axisOrdering
        from ccpn.ui.gui.popups.AxisOrderingPopup import checkSpectraToOpen

        checkSpectraToOpen(mainWindow, [spectrum])

        spectrumDisplay = mainWindow.newSpectrumDisplay(spectrum, position=position, relativeTo=relativeTo)
        if spectrumDisplay and len(spectrumDisplay.strips) > 0:
            current.strip = spectrumDisplay.strips[0]

        return spectrumDisplay

    openItemDirectMethod = _openSpectrumDisplay


class _openItemSpectrumGroupDisplay(OpenItemABC):
    openItemMethod = None
    useApplication = False
    objectArgumentName = 'spectrumGroup'

    def _openSpectrumGroup(self, spectrumGroup, position=None, relativeTo=None):
        """Displays spectrumGroup on spectrumDisplay. It creates the display based on the first spectrum of the group.
        Also hides the spectrumToolBar and shows spectrumGroupToolBar.
        """
        mainWindow = self.mainWindow
        current = mainWindow.application.current

        if len(spectrumGroup.spectra) > 0:

            # check whether a new spectrumDisplay is needed, and check axisOrdering
            from ccpn.ui.gui.popups.AxisOrderingPopup import checkSpectraToOpen

            checkSpectraToOpen(mainWindow, [spectrumGroup])

            # with undoBlockWithoutSideBar():
            with undoStackBlocking() as _:  # Do not add to undo/redo stack
                with notificationEchoBlocking():

                    spectrumDisplay = mainWindow.newSpectrumDisplay(spectrumGroup, position=position, relativeTo=relativeTo)

                    # set the spectrumView colours
                    # spectrumDisplay._colourChanged(spectrumGroup)
                    if len(spectrumDisplay.strips) > 0:

                        # with undoBlockWithoutSideBar():
                        #     with notificationEchoBlocking():
                        for spectrum in spectrumGroup.spectra[1:]:  # Add the other spectra
                            spectrumDisplay.displaySpectrum(spectrum)

                        current.strip = spectrumDisplay.strips[0]
                    # if any([sp.dimensionCount for sp in spectrumGroup.spectra]) == 1:
                    spectrumDisplay.autoRange()
            return spectrumDisplay

    openItemDirectMethod = _openSpectrumGroup


class _openItemSpectrumInGroupDisplay(_openItemSpectrumDisplay):
    """Modified class for spectra that are in sideBar under a spectrumGroup
    """

    def _openContextMenu(self, parentWidget, position, objs):
        """Open a context menu.
        """
        contextMenu = Menu('', parentWidget, isFloatWidget=True)
        if self.openAction:
            contextMenu.addAction(self.contextMenuText, self.openAction)

        spectra = [obj for obj in objs if isinstance(obj, Spectrum)]
        if len(spectra) > 0:
            contextMenu.addAction('Make SpectrumGroup From Selected',
                                  partial(_raiseSpectrumGroupEditorPopup(useNone=True, editMode=False, defaultItems=spectra),
                                          self.mainWindow, self.getObj(), self.node))

            contextMenu.addAction('Remove from SpectrumGroup', partial(self._removeSpectrumObject, objs))
            self._addCollectionMenu(contextMenu, objs)
            contextMenu.addSeparator()

        contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))
        canBeCloned = True
        for obj in objs:
            if not hasattr(obj, 'clone'):  # TODO: possibly should check that is a method...
                canBeCloned = False
                break
        if canBeCloned:
            contextMenu.addAction('Clone', partial(self._cloneObject, objs))

        contextMenu.addSeparator()
        contextMenu.addAction('Edit Properties', partial(parentWidget._raiseObjectProperties, self.node.widget))

        contextMenu.move(position)
        contextMenu.exec()

    def _removeSpectrumObject(self, objs):
        """Remove spectrum from spectrumGroup.
        """
        if not isinstance(objs, list):
            return

        try:
            # get parent spectrumGroup from current node
            specGroup = self.node._parent.obj
            spectra = list(specGroup.spectra)

            with undoBlockWithoutSideBar():
                for obj in objs:
                    if obj in spectra:
                        spectra.remove(obj)
                specGroup.spectra = tuple(spectra)

        except Exception as es:
            showWarning('Remove object from spectra', str(es))


class _openItemStructureEnsembleTable(OpenItemABC):
    openItemMethod = 'showStructureTable'
    objectArgumentName = 'structureEnsemble'


class _openItemDataTable(OpenItemABC):
    openItemMethod = 'showDataTable'
    objectArgumentName = 'dataTable'


class _openItemCollectionModule(OpenItemABC):
    openItemMethod = 'showCollectionModule'
    objectArgumentName = 'collection'


OpenObjAction = {
    Spectrum         : _openItemSpectrumDisplay,
    PeakList         : _openItemPeakListTable,
    MultipletList    : _openItemMultipletListTable,
    NmrChain         : _openItemNmrChainTable,
    Chain            : _openItemChainTable,
    SpectrumGroup    : _openItemSpectrumGroupDisplay,
    Sample           : _openItemSampleDisplay,
    ChemicalShiftList: _openItemChemicalShiftListTable,
    RestraintTable   : _openItemRestraintTable,
    Note             : _openItemNoteTable,
    IntegralList     : _openItemIntegralListTable,
    StructureEnsemble: _openItemStructureEnsembleTable,
    DataTable        : _openItemDataTable,
    Collection       : _openItemCollectionModule,
    }


def _openItemObject(mainWindow, objs, **kwds):
    if len(objs) > 0:
        with undoBlockWithoutSideBar():

            # if 5 or more then don't log, otherwise log may be overloaded
            if len(objs) > MAXITEMLOGGING:
                getLogger().info('Opening items...')
                with notificationEchoBlocking():
                    _openItemObjects(mainWindow, objs, **kwds)
            else:
                _openItemObjects(mainWindow, objs, **kwds)


def _openItemObjects(mainWindow, objs, **kwds):
    """
    Abstract routine to activate a module to display objs
    Builds on OpenObjAction dict, defined above, which defines the handling for the various
    obj classes
    """
    spectrumDisplay = None
    with undoBlockWithoutSideBar():
        for obj in objs:
            if obj:

                if obj.__class__ in OpenObjAction:

                    # if a spectrum object has already been opened then attach to that spectrumDisplay
                    if isinstance(obj, Spectrum) and spectrumDisplay:
                        try:
                            spectrumDisplay.displaySpectrum(obj)

                        except RuntimeError:
                            # process objects to open
                            func = OpenObjAction[obj.__class__](useNone=True, **kwds)
                            returnObj = func._execOpenItem(mainWindow, obj)

                    elif isinstance(obj, SpectrumGroup) and spectrumDisplay:
                        try:
                            spectrumDisplay._handleSpectrumGroup(obj)

                        except RuntimeError:
                            # process objects to open
                            func = OpenObjAction[obj.__class__](useNone=True, **kwds)
                            returnObj = func._execOpenItem(mainWindow, obj)
                    else:
                        # process objects to open
                        func = OpenObjAction[obj.__class__](useNone=True, **kwds)
                        returnObj = func._execOpenItem(mainWindow, obj)

                        # if the first spectrum then set the spectrumDisplay
                        if isinstance(obj, (Spectrum, SpectrumGroup)):
                            spectrumDisplay = returnObj

                else:
                    showInfo('Not implemented yet!',
                             'This function has not been implemented in the current version')
