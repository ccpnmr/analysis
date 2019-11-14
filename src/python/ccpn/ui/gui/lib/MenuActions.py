"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
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
from ccpn.core.RestraintList import RestraintList
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning
from ccpn.core.lib.ContextManagers import undoBlock

from ccpn.ui.gui.popups.ChainPopup import ChainPopup
from ccpn.ui.gui.popups.ChemicalShiftListPopup import ChemicalShiftListEditor
from ccpn.ui.gui.popups.ComplexEditorPopup import ComplexEditorPopup
from ccpn.ui.gui.popups.CreateChainPopup import CreateChainPopup
from ccpn.ui.gui.popups.CreateNmrChainPopup import CreateNmrChainPopup
from ccpn.ui.gui.popups.DataSetPopup import DataSetPopup
from ccpn.ui.gui.popups.IntegralListPropertiesPopup import IntegralListPropertiesPopup
from ccpn.ui.gui.popups.MultipletListPropertiesPopup import MultipletListPropertiesPopup
from ccpn.ui.gui.popups.NmrAtomPopup import NmrAtomPopup
from ccpn.ui.gui.popups.NmrChainPopup import NmrChainPopup
from ccpn.ui.gui.popups.NmrResiduePopup import NmrResiduePopup
from ccpn.ui.gui.popups.NotesPopup import NotesPopup
from ccpn.ui.gui.popups.PeakListPropertiesPopup import PeakListPropertiesPopup
from ccpn.ui.gui.popups.RestraintListPopup import RestraintListEditPopup, RestraintListNewPopup
from ccpn.ui.gui.popups.SampleComponentPropertiesPopup import SampleComponentPopup
from ccpn.ui.gui.popups.SamplePropertiesPopup import SamplePropertiesPopup
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpn.ui.gui.popups.StructureEnsemblePopup import StructureEnsemblePopup
from ccpn.ui.gui.popups.SubstancePropertiesPopup import SubstancePropertiesPopup
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
        # store kewyword as attributes and as dict; acts as partial to popupClass
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


class _createNewDataSet(CreateNewObjectABC):
    parentMethodName = 'newDataSet'


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


class _createNewNote(CreateNewObjectABC):
    parentMethodName = 'newNote'


class _createNewIntegralList(CreateNewObjectABC):
    parentMethodName = 'newIntegralList'


class _createNewSample(CreateNewObjectABC):
    parentMethodName = 'newSample'


class _createNewStructureEnsemble(CreateNewObjectABC):
    parentMethodName = 'newStructureEnsemble'


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


class _raiseDataSetPopup(RaisePopupABC):
    popupClass = DataSetPopup
    # objectArgumentName = 'obj'


class _raiseChemicalShiftListPopup(RaisePopupABC):
    popupClass = ChemicalShiftListEditor
    # objectArgumentName = 'chemicalShiftList'


class _raisePeakListPopup(RaisePopupABC):
    popupClass = PeakListPropertiesPopup
    objectArgumentName = 'peakList'


class _raiseMultipletListPopup(RaisePopupABC):
    popupClass = MultipletListPropertiesPopup
    objectArgumentName = 'multipletList'


class _raiseCreateNmrChainPopup(RaisePopupABC):
    popupClass = CreateNmrChainPopup
    objectArgumentName = 'project'


class _raiseNmrChainPopup(RaisePopupABC):
    popupClass = NmrChainPopup
    # objectArgumentName = 'nmrChain'


class _raiseNmrResiduePopup(RaisePopupABC):
    popupClass = NmrResiduePopup
    # objectArgumentName = 'nmrResidue'


class _raiseNmrAtomPopup(RaisePopupABC):
    popupClass = NmrAtomPopup
    # objectArgumentName = 'nmrAtom'


class _raiseNotePopup(RaisePopupABC):
    popupClass = NotesPopup
    # objectArgumentName = 'obj'


class _raiseIntegralListPopup(RaisePopupABC):
    popupClass = IntegralListPropertiesPopup
    objectArgumentName = 'integralList'


class _raiseRestraintListEditPopup(RaisePopupABC):
    popupClass = RestraintListEditPopup
    # objectArgumentName = 'restraintList'
    parentObjectArgumentName = 'dataSet'


class _raiseRestraintListNewPopup(_raiseRestraintListEditPopup):
    popupClass = RestraintListNewPopup


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
                          RestraintList, Note, StructureEnsemble
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

        contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))
        canBeCloned = True
        for obj in objs:
            if not hasattr(obj, 'clone'):  # TODO: possibly should check that is a method...
                canBeCloned = False
                break
        if canBeCloned:
            contextMenu.addAction('Clone', partial(self._cloneObject, objs))

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
            with undoBlock():
                for obj in objs:
                    if obj:
                        # just delete the object
                        obj.delete()

        except Exception as es:
            showWarning('Delete', str(es))


class _openItemChemicalShiftListTable(OpenItemABC):
    openItemMethod = 'showChemicalShiftTable'
    objectArgumentName = 'chemicalShiftList'


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


class _openItemChainTable(OpenItemABC):
    openItemMethod = 'showResidueTable'
    objectArgumentName = 'chain'


class _openItemResidueTable(OpenItemABC):
    objectArgumentName = 'residue'
    hasOpenMethod = False


class _openItemNoteTable(OpenItemABC):
    openItemMethod = 'showNotesEditor'
    objectArgumentName = 'note'


class _openItemRestraintListTable(OpenItemABC):
    openItemMethod = 'showRestraintTable'
    objectArgumentName = 'restraintList'


class _openItemDataSetTable(OpenItemABC):
    objectArgumentName = 'dataSet'
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
        if len(sample.spectra) > 0:
            for spectrum in sample.spectra:
                spectrumDisplay.displaySpectrum(spectrum)
            for sampleComponent in sample.sampleComponents:
                if sampleComponent.substance is not None:
                    for spectrum in sampleComponent.substance.referenceSpectra:
                        spectrumDisplay.displaySpectrum(spectrum)
            if autoRange:
                spectrumDisplay.autoRange()

    def _openSampleSpectra(self, sample, position=None, relativeTo=None):
        """Add spectra linked to sample and sampleComponent. Particularly used for screening
        """
        mainWindow = self.mainWindow

        if len(sample.spectra) > 0:
            spectrumDisplay = mainWindow.createSpectrumDisplay(sample.spectra[0])
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

        # check whether a new spectrumDisplay is needed, and check axisOrdering
        from ccpn.ui.gui.popups.AxisOrderingPopup import checkSpectraToOpen
        checkSpectraToOpen(mainWindow, [spectrum])

        # with undoBlockWithoutSideBar():

        spectrumDisplay = mainWindow.createSpectrumDisplay(spectrum, position=position, relativeTo=relativeTo)

            # with undoStackBlocking() as addUndoItem:
            #     # disable all notifiers in spectrumDisplays
            #     addUndoItem(undo=partial(_setSpectrumDisplayNotifiers, spectrumDisplay, True))
            #
            # if len(spectrumDisplay.strips) > 0:
            #     mainWindow.current.strip = spectrumDisplay.strips[0]
            #     # if spectrum.dimensionCount == 1:
            #     spectrumDisplay.autoRange()
            #     # mainWindow.current.strip.plotWidget.autoRange()
            #
            # mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)
            #
            # with undoStackBlocking() as addUndoItem:
            #     # disable all notifiers in spectrumDisplays
            #     addUndoItem(redo=partial(_setSpectrumDisplayNotifiers, spectrumDisplay, False))
            #
            #     # add/remove spectrumDisplay from module Area
            #     addUndoItem(undo=partial(mainWindow._hiddenModules.addModule, spectrumDisplay),
            #                 redo=partial(mainWindow.moduleArea.addModule, spectrumDisplay, position=position, relativeTo=relativeTo))


        # # TODO:LUCA: the mainWindow.createSpectrumDisplay should do the reporting to console and log
        # # This routine can then be omitted and the call above replaced by the one remaining line
        # mainWindow.pythonConsole.writeConsoleCommand(
        #         "application.createSpectrumDisplay(spectrum)", spectrum=spectrum)
        # getLogger().info('spectrum = project.getByPid(%r)' % spectrum.id)
        # getLogger().info('application.createSpectrumDisplay(spectrum)')

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

        if len(spectrumGroup.spectra) > 0:

            # check whether a new spectrumDisplay is needed, and check axisOrdering
            from ccpn.ui.gui.popups.AxisOrderingPopup import checkSpectraToOpen
            checkSpectraToOpen(mainWindow, [spectrumGroup])

            spectrumDisplay = mainWindow.createSpectrumDisplay(spectrumGroup.spectra[0])
            mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)

            with undoBlockWithoutSideBar():
                with notificationEchoBlocking:
                    for spectrum in spectrumGroup.spectra:  # Add the other spectra
                        spectrumDisplay.displaySpectrum(spectrum)

                    spectrumDisplay.isGrouped = True
                    spectrumDisplay.spectrumToolBar.hide()
                    spectrumDisplay.spectrumGroupToolBar.show()
                    spectrumDisplay.spectrumGroupToolBar._addAction(spectrumGroup)

            mainWindow.application.current.strip = spectrumDisplay.strips[0]
            # if any([sp.dimensionCount for sp in spectrumGroup.spectra]) == 1:
            spectrumDisplay.autoRange()

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
            contextMenu.addSeparator()

        contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))
        canBeCloned = True
        for obj in objs:
            if not hasattr(obj, 'clone'):  # TODO: possibly should check that is a method...
                canBeCloned = False
                break
        if canBeCloned:
            contextMenu.addAction('Clone', partial(self._cloneObject, objs))

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

            with undoBlock():
                for obj in objs:
                    if obj in spectra:
                        spectra.remove(obj)
                specGroup.spectra = tuple(spectra)

        except Exception as es:
            showWarning('Remove object from spectra', str(es))


class _openItemStructureEnsembleTable(OpenItemABC):
    openItemMethod = 'showStructureTable'
    objectArgumentName = 'structureEnsemble'


OpenObjAction = {
    Spectrum         : _openItemSpectrumDisplay,
    PeakList         : _openItemPeakListTable,
    MultipletList    : _openItemMultipletListTable,
    NmrChain         : _openItemNmrChainTable,
    Chain            : _openItemChainTable,
    SpectrumGroup    : _openItemSpectrumGroupDisplay,
    Sample           : _openItemSampleDisplay,
    ChemicalShiftList: _openItemChemicalShiftListTable,
    RestraintList    : _openItemRestraintListTable,
    Note             : _openItemNoteTable,
    IntegralList     : _openItemIntegralListTable,
    StructureEnsemble: _openItemStructureEnsembleTable
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
    Builds on OpenObjAction dict, generated below, which defines the handling for the various
    obj classes
    """
    spectrumDisplay = None
    with undoBlockWithoutSideBar():

        for obj in objs:
            if obj:
                try:
                    if obj.__class__ in OpenObjAction:

                        # if a spectrum object has already been opened then attach to that spectrumDisplay
                        if isinstance(obj, Spectrum) and spectrumDisplay:
                            spectrumDisplay.displaySpectrum(obj)

                        else:

                            # process objects to open
                            func = OpenObjAction[obj.__class__](useNone=True, **kwds)
                            returnObj = func._execOpenItem(mainWindow, obj)

                            # if the first spectrum then set the spectrumDisplay
                            if isinstance(obj, Spectrum):
                                spectrumDisplay = returnObj

                    else:
                        info = showInfo('Not implemented yet!',
                                        'This function has not been implemented in the current version')
                except Exception as e:
                    getLogger().warning('Error: %s' % e)
                    # raise e
