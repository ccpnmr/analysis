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
from ccpn.ui.gui.widgets.MessageDialog import showInfo
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

from ccpn.ui.gui.popups.ChainPopup import ChainPopup
from ccpn.ui.gui.popups.ChemicalShiftListPopup import ChemicalShiftListPopup
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
from ccpn.ui.gui.popups.RestraintListPopup import RestraintListPopup
from ccpn.ui.gui.popups.SampleComponentPropertiesPopup import SampleComponentPopup
from ccpn.ui.gui.popups.SamplePropertiesPopup import SamplePropertiesPopup
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpn.ui.gui.popups.StructureEnsemblePopup import StructureEnsemblePopup
from ccpn.ui.gui.popups.SubstancePropertiesPopup import SubstancePropertiesPopup


# OPEN_ITEM_DICT = {
#     Spectrum.className         : _openSpectrumDisplay,
#     PeakList.className         : showPeakTable,
#     IntegralList.className     : showIntegralTable,
#     MultipletList.className    : showMultipletTable,
#     NmrChain.className         : showNmrResidueTable,
#     Chain.className            : showResidueTable,
#     SpectrumGroup.className    : _openSpectrumGroup,
#     Sample.className           : _openSampleSpectra,
#     ChemicalShiftList.className: showChemicalShiftTable,
#     RestraintList.className    : showRestraintTable,
#     Note.lastModified          : showNotesEditor,
#     StructureEnsemble.className: showStructureTable
#     }


# def _openNote(mainWindow, note, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showNotesEditor(note=note, position=position, relativeTo=relativeTo)


# def _openIntegralList(mainWindow, integralList, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showIntegralTable(integralList=integralList, position=position, relativeTo=relativeTo)


# def _openPeakList(mainWindow, peakList, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showPeakTable(peakList=peakList, position=position, relativeTo=relativeTo)


# def _openMultipletList(mainWindow, multipletList, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showMultipletTable(multipletList=multipletList, position=position, relativeTo=relativeTo)


# def _openChemicalShiftList(mainWindow, chemicalShiftList, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showChemicalShiftTable(chemicalShiftList=chemicalShiftList, position=position, relativeTo=relativeTo)


# def _openRestraintList(mainWindow, restraintList, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showRestraintTable(restraintList=restraintList, position=position, relativeTo=relativeTo)


# def _openStructureTable(mainWindow, structureEnsemble, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showStructureTable(structureEnsemble=structureEnsemble, position=position, relativeTo=relativeTo)


# def _openNmrResidueTable(mainWindow, nmrChain, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showNmrResidueTable(nmrChain=nmrChain, position=position, relativeTo=relativeTo)


# def _openResidueTable(mainWindow, chain, position=None, relativeTo=None):
#     application = mainWindow.application
#     application.showResidueTable(chain=chain, position=position, relativeTo=relativeTo)


OpenObjAction = {
    Spectrum         : _openSpectrumDisplay,
    PeakList         : _openPeakList,
    MultipletList    : _openMultipletList,
    NmrChain         : _openNmrResidueTable,
    Chain            : _openResidueTable,
    SpectrumGroup    : _openSpectrumGroup,
    Sample           : _openSampleSpectra,
    ChemicalShiftList: _openChemicalShiftList,
    RestraintList    : _openRestraintList,
    Note             : _openNote,
    IntegralList     : _openIntegralList,
    StructureEnsemble: _openStructureTable
    }


def _openItemObject(mainWindow, objs, **kwds):
    """
    Abstract routine to activate a module to display objs
    Builds on OpenObjAction dict, generated below, which defines the handling for the various
    obj classes
    """
    spectrumDisplay = None

    for obj in objs:
        if obj:
            try:
                if obj.__class__ in OpenObjAction:

                    # if a spectrum object has already been opened then attach to that spectrumDisplay
                    if isinstance(obj, Spectrum) and spectrumDisplay:
                        spectrumDisplay.displaySpectrum(obj)

                    else:

                        # process objects to open
                        returnObj = OpenObjAction[obj.__class__](mainWindow, obj, **kwds)

                        # if the first spectrum then set the spectrumDisplay
                        if isinstance(obj, Spectrum):
                            spectrumDisplay = returnObj

                else:
                    info = showInfo('Not implemented yet!',
                                    'This function has not been implemented in the current version')
            except Exception as e:
                getLogger().warning('Error: %s' % e)
                # raise e


def _openSpectrumDisplay(mainWindow, spectrum, position=None, relativeTo=None):
    spectrumDisplay = mainWindow.createSpectrumDisplay(spectrum)

    if len(spectrumDisplay.strips) > 0:
        mainWindow.current.strip = spectrumDisplay.strips[0]
        # if spectrum.dimensionCount == 1:
        spectrumDisplay._maximiseRegions()
        # mainWindow.current.strip.plotWidget.autoRange()

    mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)

    # TODO:LUCA: the mainWindow.createSpectrumDisplay should do the reporting to console and log
    # This routine can then be ommitted and the call above replaced by the one remaining line
    mainWindow.pythonConsole.writeConsoleCommand(
            "application.createSpectrumDisplay(spectrum)", spectrum=spectrum)
    getLogger().info('spectrum = project.getByPid(%r)' % spectrum.id)
    getLogger().info('application.createSpectrumDisplay(spectrum)')

    return spectrumDisplay


def _openSpectrumGroup(mainWindow, spectrumGroup, position=None, relativeTo=None):
    '''displays spectrumGroup on spectrumDisplay. It creates the display based on the first spectrum of the group.
    Also hides the spectrumToolBar and shows spectrumGroupToolBar '''

    if len(spectrumGroup.spectra) > 0:
        spectrumDisplay = mainWindow.createSpectrumDisplay(spectrumGroup.spectra[0])
        mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)
        for spectrum in spectrumGroup.spectra:  # Add the other spectra
            spectrumDisplay.displaySpectrum(spectrum)

        spectrumDisplay.isGrouped = True
        spectrumDisplay.spectrumToolBar.hide()
        spectrumDisplay.spectrumGroupToolBar.show()
        spectrumDisplay.spectrumGroupToolBar._addAction(spectrumGroup)
        mainWindow.application.current.strip = spectrumDisplay.strips[0]
        # if any([sp.dimensionCount for sp in spectrumGroup.spectra]) == 1:
        spectrumDisplay._maximiseRegions()


def _openSampleSpectra(mainWindow, sample, position=None, relativeTo=None):
    """
    Add spectra linked to sample and sampleComponent. Particularly used for screening
    """
    if len(sample.spectra) > 0:
        spectrumDisplay = mainWindow.createSpectrumDisplay(sample.spectra[0])
        mainWindow.moduleArea.addModule(spectrumDisplay, position=position, relativeTo=relativeTo)
        for spectrum in sample.spectra:
            spectrumDisplay.displaySpectrum(spectrum)
        for sampleComponent in sample.sampleComponents:
            if sampleComponent.substance is not None:
                for spectrum in sampleComponent.substance.referenceSpectra:
                    spectrumDisplay.displaySpectrum(spectrum)
        mainWindow.application.current.strip = spectrumDisplay.strips[0]
        if all(sample.spectra[0].dimensionCount) == 1:
            mainWindow.application.current.strip.autoRange()


def _createSpectrumGroup(mainWindow, spectra=None or []):
    """This needs to be put into a more generic place.
    """
    popup = SpectrumGroupEditor(parent=mainWindow, mainWindow=mainWindow, editMode=False, defaultItems=spectra)
    popup.exec_()
    popup.raise_()


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

    def __call__(self, dataPid, node):
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

    def __call__(self, dataPid, node):
        self.node = node
        self.dataPid = dataPid
        obj = self.getObj()
        if self.useParent:
            self.kwds[self.parentObjectArgumentName] = obj
        else:
            self.kwds[self.objectArgumentName] = obj

        popup = self.popupClass(parent=node.sidebar, mainWindow=node.sidebar.mainWindow,
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


class _raiseChemicalShifListPopup(RaisePopupABC):
    popupClass = ChemicalShiftListPopup
    objectArgumentName = 'chemicalShiftList'


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
    objectArgumentName = 'nmrResidue'


class _raiseNmrAtomPopup(RaisePopupABC):
    popupClass = NmrAtomPopup
    objectArgumentName = 'nmrAtom'


class _raiseNotePopup(RaisePopupABC):
    popupClass = NotesPopup
    # objectArgumentName = 'obj'


class _raiseIntegralListPopup(RaisePopupABC):
    popupClass = IntegralListPropertiesPopup
    objectArgumentName = 'integralList'


class _raiseRestraintListPopup(RaisePopupABC):
    popupClass = RestraintListPopup
    objectArgumentName = 'restraintList'
    parentObjectArgumentName = 'dataSet'


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

    validActionTargets = (Spectrum, PeakList, MultipletList,
                          NmrChain, Chain, SpectrumGroup, Sample, ChemicalShiftList,
                          RestraintList, Note, IntegralList, StructureEnsemble
                          )

    # This can be subclassed
    def getObj(self):
        """returns obj from node or None
        """
        obj = None if self.useNone else self.node.obj
        return obj

    def __init__(self, useApplication=True, useNone=False, **kwds):
        """store kwds; acts as partial to openItemClass
        useApplication: if true, use the method attached to application
                     : if false, use openItemDirectMethod for opening object in ccpnModuleArea
        useNone: set obj to None
        """
        self.useApplication = useApplication  # Use parent of object
        if useApplication is False and self.openItemDirectMethod is None:
            raise RuntimeError('useApplication==False requires definition of openItemDirectMethod (%s)' % self)
        self.useNone = useNone
        self.kwds = kwds
        # these get set upon callback
        self.node = None
        self.dataPid = None

    def __call__(self, dataPid, node, position, objs):
        """Call acts is the execute entry point for the callback.
        """
        self.node = node
        self.dataPid = dataPid
        obj = self.getObj()
        self.kwds[self.objectArgumentName] = obj

        self.mainWindow = node.sidebar.mainWindow
        self.application = self.mainWindow.application

        openableObjs = [obj for obj in objs if isinstance(obj, self.validActionTargets)]

        if len(openableObjs) > 0:
            contextMenu = Menu('', node.sidebar, isFloatWidget=True)

            if self.useApplication:
                func = getattr(self.application, self.openItemMethod)
            else:
                func = self.openItemDirectMethod

            if func is None:
                raise RuntimeError('Undefined function; cannot open object (%s)' % dataPid)

            openAction = partial(func, **self.kwds)
            contextMenu.addAction('Open as a module', openAction)

            # spectra = [o for o in openableObjs if isinstance(o, Spectrum)]
            # if len(spectra) > 0:
            #     contextMenu.addAction('Make SpectrumGroup From Selected', partial(_createSpectrumGroup, self.mainWindow, spectra))
            #
            # contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))
            # canBeCloned = True
            # for obj in objs:
            #     if not hasattr(obj, 'clone'):  # TODO: possibly should check that is a method...
            #         canBeCloned = False
            #         break
            # if canBeCloned:
            #     contextMenu.addAction('Clone', partial(self._cloneObject, objs))

            contextMenu.move(position)
            contextMenu.exec()

    def _openItemObject(self, objs):
        """Open the object.
        """
        pass

    def _cloneObject(self, objs):
        """Clones the specified objects.
        """
        for obj in objs:
            obj.clone()

    def _deleteItemObject(self, objs):
        """Delete items from the project.
        """
        pass


# class _openItemNewChainItem(OpenItemABC):
#     openItemMethod = 'showNotesEditor'
#     parentObjectArgumentName = 'project'
#
#
# class _openItemChainItem(OpenItemABC):
#     openItemMethod = 'showNotesEditor'
#     objectArgumentName = 'note'
#
#
# class _openItemComplexEditorItem(OpenItemABC):
#     openItemMethod = 'showNotesEditor'
#     objectArgumentName = 'note'
#
#
# class _openItemDataSetItem(OpenItemABC):
#     openItemMethod = 'showNotesEditor'
#     objectArgumentName = 'note'


class _openItemChemicalShifListTable(OpenItemABC):
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


# class _openItemCreateNmrChainTable(OpenItemABC):
#     openItemMethod = 'showNotesEditor'
#     objectArgumentName = 'project'


class _openItemNmrResidueTable(OpenItemABC):
    openItemMethod = 'showNmrResidueTable'
    objectArgumentName = 'nmrChain'


class _openItemResidueTable(OpenItemABC):
    openItemMethod = 'showResidueTable'
    objectArgumentName = 'chain'


# class _openItemNmrAtomItem(OpenItemABC):
#     openItemMethod = NmrAtomItem
#     objectArgumentName = 'nmrAtom'


class _openItemNoteTable(OpenItemABC):
    openItemMethod = 'showNotesEditor'
    objectArgumentName = 'note'


class _openItemRestraintListItem(OpenItemABC):
    openItemMethod = 'showRestraintTable'
    objectArgumentName = 'restraintList'


# class _openItemSampleItem(OpenItemABC):
#     openItemMethod = SamplePropertiesItem
#     objectArgumentName = 'sample'
#
#
# class _openItemSampleComponentItem(OpenItemABC):
#     openItemMethod = SampleComponentItem
#     # NB This popup is structured slightly different, passing in different arguments
#     objectArgumentName = 'sampleComponent'
#     parentObjectArgumentName = 'sample'
#
#
# class _openItemSpectrumItem(OpenItemABC):
#     openItemMethod = SpectrumPropertiesItem
#     objectArgumentName = 'spectrum'
#
#
# class _openItemSpectrumGroupEditorItem(OpenItemABC):
#     openItemMethod = SpectrumGroupEditor
#
#
class _openItemStructureEnsembleItem(OpenItemABC):
    openItemMethod = 'showStructureTable'
    objectArgumentName = 'structureEnsemble'

# class _openItemSubstanceItem(OpenItemABC):
#     openItemMethod = SubstancePropertiesItem
#     objectArgumentName = 'substance'
