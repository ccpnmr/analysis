"""
Layout class and routines for saving/restoring module layouts

There are several Try except due to the fragility of Pyqtgraph layouts (containers) and
nested hierarchy of docks/areas etc.
The state is saved in a Json file.

Original code by Luca Mureddu
Fully refactored by Geerten Vuister; second version for 3.1.0 release

IN_PROGRESS
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                 )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-02-07 17:13:53 +0000 (Mon, February 07, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import pkgutil
import inspect

from ccpn.framework.Application import applicationNames
from ccpn.framework.PathsAndUrls import projectStateLayoutFileName, ccpnPythonPath

from ccpn.ui.gui.lib.GuiSpectrumDisplay import GuiSpectrumDisplay

from ccpn.util.traits.CcpNmrJson import Constants, update, CcpNmrJson
from ccpn.util.traits.CcpNmrTraits import Unicode, Dict, List
# from sandbox.Geerten.Refactored.decorators import debug2Enter
from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath


APPLICATION_NAME = 'applicationName'
APPLICATION_VERSION = 'applicationVersion'


#--------------------------------------------------------------------------------------------
# Update old-style layout
#--------------------------------------------------------------------------------------------

def _updateLayout(obj, dataDict):
    """Update the layout from old-style if needed
    """

    if not Constants.METADATA in dataDict:
        # ok, we did not have a CcpNmrJson type dict with metadata ==> old-style layout
        getLogger().debug('_updateLayout')

        # check for some essential keys to be there:
        if not 'general' in dataDict or not 'layoutState' in dataDict:
            raise RuntimeError('_updateLayout: invalid dataDict; cannot update')

        # add the default metadata
        dataDict[Constants.METADATA] = getattr(obj, Constants.METADATA)

        # Convert some of the data into the new format
        if 'general' in dataDict:
            dataDict[Constants.METADATA][APPLICATION_NAME] = dataDict['general'][APPLICATION_NAME]
            dataDict[Constants.METADATA][APPLICATION_VERSION] = dataDict['general'][APPLICATION_VERSION]
            del( dataDict['general'])
        # if 'guiModules' in dataDict:
        #     dataDict['modules'] = []
        #     for moduleName, moduleClassName in dataDict['guiModules']:
        #         dataDict['modules'].append((moduleName, moduleClassName))
        #     del dataDict['guiModules']
        # if 'fileNames' in dataDict:
        #     del dataDict['fileNames']

        return dataDict

    if dataDict[Constants.METADATA][Constants.CLASSNAME] != obj.__class__.__name__:
        getLogger().debug2('skipping _updateLayout; different class')
        return dataDict
    else:
        getLogger().debug2('skipping _updateLayout; nothing to update')
        return dataDict


#--------------------------------------------------------------------------------------------

# update needs to be at front of stack as old-style do not have metadata
@update(_updateLayout, push=True)
class LayoutManager(CcpNmrJson):
    """
    Class that maintains layout settings and save/restore functionality
    """
    classVersion = 3.1

    WARNING = Unicode('This is a layout file; it will be automatically overwritten').tag(saveToJson=True)
    guiModules = List(default_value=[]).tag(saveToJson=True)  # list of (moduleName, moduleClassName) tuples
    SpectrumDisplays = List(default_value=[]).tag(saveToJson=True)  # list of dict's with SpectrunDisplay properties    SpectrumDisplays = List(default_value=[]).tag(saveToJson=True)  # list of dict's with SpectrunDisplay properties
    fileNames = List(default_value=[]).tag(saveToJson=True)  # list of filenames GWV???
    layoutState = Dict(default_value={}).tag(saveToJson=True)  # data structure as returned by saveState()

    def __init__(self, mainWindow):
        super().__init__()
        if mainWindow is None:
            raise RuntimeError('Undefined mainWindow')
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.moduleClassMap = dict([(module.className, module) for module in _getCcpnModules()])

    @property
    def path(self):
        """Path of layout json file in the current project"""
        return self.application.statePath / projectStateLayoutFileName

    def _updateSpectrumDisplaysState(self):
        """Update the SpectrumDisplays attribute with a list of dict with serialisable
        attributes needed to restore the SpectrumDisplay status
        AbstractWrapperClasses will be converted as pid, EG spectrumDisplay.spectra
        """
        ll = []
        for spectrumDisplay in self.mainWindow.spectrumDisplays:
            dd = spectrumDisplay.getAsDict()
            stripDirection = dd.get("stripArrangement")
            axisCodes = dd.get("axisCodes")
            spectrumDisplayKeys = ["longPid", "axisOrder", "title", "positions", "widths", "units", "is1D"]
            fd = {i: dd.get(i) for i in spectrumDisplayKeys}
            fd.update({'stripDirection': stripDirection})
            fd.update({'displayAxisCodes': axisCodes})
            fd.update({'spectra': [sp.pid for sp in spectrumDisplay._getSpectra()]})
            # strips informations
            stripsZoomStates = [strip.zoomState for strip in spectrumDisplay.strips]
            fd.update({"stripsZoomStates": stripsZoomStates})
            ll.append(fd)
        self.SpectrumDisplays = ll

    def _updateFileNames(self):
        """updates the fileNames needed for importing the module. list of file name from the full path
        :param mainWindow:
        :param layout:
        :return: #
        """
        guiModules = self.mainWindow.moduleArea.ccpnModules
        names = set()
        for guiModule in guiModules:
            if not isinstance(guiModule, GuiSpectrumDisplay):  #Don't Save spectrum Displays
                pyModule = sys.modules[guiModule.__module__]
                if pyModule:
                    file = pyModule.__file__
                    if file:
                        names.add(aPath(file).basename)

        if len(names) > 0:
            self.fileNames = list(names)

    def _updateSettings(self):
        """Update the various setting to current values
        """
        # list of (moduleName, moduleClassName) tuples
        self.modules = [(str(module.name()), module.className) \
                                  for module in self.mainWindow.modules]
        self._updateSpectrumDisplaysState()
        self._updateFileNames()
        self.layoutState = self.mainWindow.moduleArea.saveState()

    # @debug2Enter()
    def saveState(self, path=None):
        """get the state of mainWindow and save to json-file
        """
        if path is None:
            path = self.path
        else:
            path = aPath(path).assureSuffix('.json')
        self._updateSettings()
        self.setJsonMetadata(APPLICATION_NAME, self.application.applicationName)
        self.setJsonMetadata(APPLICATION_VERSION, self.application.applicationVersion)
        self.save(path.asString())

    def _restoreState(self):
        """The actual restore action
        Adapted from previous Layout.restoreState code
        """

        # if FileNames in layout:
        #     neededModules = layout.get(FileNames)  # getattr(layout, FileNames)
        neededModules = self.fileNames
        if len(self.fileNames) > 0:

            # if GuiModules in layout:
            #     # if ClassNameModuleName in layout.guiModules:
            #     #   classNameGuiModuleNameList = getattr(layout.guiModules, ClassNameModuleName)
            #
                classNameGuiModuleNameList = self.guiModules  # getattr(layout, GuiModules)
                # Checks if  modules  are present in the layout file. If not stops it
                if not list(_traverse(classNameGuiModuleNameList)):
                    return

                try:
                    ccpnModules = _getAvailableModules(mainWindow, layout, neededModules)
                    for classNameGuiModuleName in classNameGuiModuleNameList:
                        if len(classNameGuiModuleName) == 2:
                            guiModuleName, className = classNameGuiModuleName

                            # move the 'skip' to here, instead of in the saveState
                            if className in ['SpectrumDisplay']:
                                continue

                            neededModules.append(className)
                            _openCcpnModule(mainWindow, ccpnModules, className, moduleName=guiModuleName)

                except Exception as e:
                    getLogger().debug2("Failed to restore Layout %s" % str(e))

        if LayoutState in layout:
            # Very important step:
            # Checks if the all the modules opened are present in the layout state. If not, will not restore the geometries
            state = layout.get(LayoutState)  # getattr(layout, LayoutState)

            if not state:
                return
            namesFromState = _getModuleNamesFromState(state)
            openedModulesName = [i.name() for i in mainWindow.moduleArea.ccpnModules]
            compare = list(set(namesFromState) & set(openedModulesName))

            if len(openedModulesName) > 0:
                if len(compare) == len(openedModulesName):
                    try:
                        mainWindow.moduleArea.restoreState(state, restoreSpectrumDisplay=restoreSpectrumDisplay)
                    except Exception as e:
                        getLogger().debug2("Layout error: %s" % e)
                else:
                    getLogger().debug2("Layout error: Some of the modules are missing. Geometries could not be restored")

    # @debug2Enter()
    def restoreState(self, path=None):
        """Restore the settings from json-file path (defaults to the one in Project/state
        and use this to restore the mainWindow state
        """
        if path is None:
            path = self.path
        else:
            path = aPath(path)
        self.restore(path.asString())  # This restores the data from path

        from ccpn.ui.gui.Layout import restoreLayout
        restoreLayout(self.mainWindow, self.mainWindow.moduleLayouts, restoreSpectrumDisplay=False)

        # # restore the modules that were open before
        # moduleClassMap = self.moduleClassMap
        # openModules = [module.name for module in self.mainWindow.modules]
        #
        # for moduleName, moduleClassName in self.modules:
        #     if moduleClassName in ['SpectrumDisplay']:
        #         pass  # initiated by other means
        #     elif moduleName in openModules:
        #         pass  # already open
        #     elif moduleClassName not in moduleClassMap:
        #         getLogger().warning('Module "%s" of type "%s" not found' % (moduleName, moduleClassName))
        #     else:
        #         try:
        #             moduleInstance = moduleClassMap[moduleClassName](mainWindow=self.mainWindow, name=moduleName)
        #             self.mainWindow.moduleArea.addModule(moduleInstance)
        #         except Exception as es:
        #             getLogger().warning('Restoring "%s" of type "%s" failed' % (moduleName, moduleClassName))
        #
        # # compare the openModules with those from the layoutState and determine if we can restore
        # openModules = [module.name() for module in self.mainWindow.modules]
        # stateModules = self._getModuleNamesFromState()
        #
        # # get the lowest serial number of the opened modules, put into openDict
        # openDict = {}
        # for name in openModules:
        #     splitName = name.split(':')
        #     lhs = splitName[0]
        #     if lhs not in ['Spectrum Display', 'SpectrumDisplay']:
        #         if len(splitName) > 1:
        #             rhs = splitName[1]
        #             if lhs not in openDict:
        #                 openDict[lhs] = int(rhs)
        #             else:
        #                 openDict[lhs] = min(int(rhs), openDict[lhs])
        #
        # # get the lowest serial number of the state modules (those that require opening from
        # # layout), put into stateDict
        # stateDict = {}
        # for name in stateModules:
        #     splitName = name.split(':')
        #     lhs = splitName[0]
        #     if lhs not in ['Spectrum Display', 'SpectrumDisplay']:
        #         if len(splitName) > 1:
        #             rhs = splitName[1]
        #             if lhs not in stateDict:
        #                 stateDict[lhs] = int(rhs)
        #             else:
        #                 stateDict[lhs] = min(int(rhs), stateDict[lhs])
        #
        # # rename the serial numbers of the opened modules to match the required modules
        # for module in self.mainWindow.modules:
        #     splitName = module.name().split(':')
        #     lhs = splitName[0]
        #     if len(splitName) > 1:
        #         if lhs not in ['Spectrum Display', 'SpectrumDisplay', 'Python Console']:
        #             rhs = splitName[1]
        #             diff = stateDict[lhs] - openDict[lhs]
        #             module.rename(lhs + ':' + str(int(rhs)+diff))
        #
        # # check that the updated names are now correct
        # openModules = [module.name() for module in self.mainWindow.modules]
        # compare = list(set(stateModules) & set(openModules))
        #
        # if len(openModules) > 0:
        #     if len(compare) == len(openModules):
        #         try:
        #             self.mainWindow.moduleArea.restoreState(self.layoutState)
        #         except Exception as e:
        #             getLogger().debug2("Layout error: %s" % e)
        #     else:
        #         getLogger().debug2("Layout error: Some of the modules are missing; failed to restore")

    def _getModuleNamesFromState(self) -> list:
        """get list of names of modules contained the layoutState data structure (as returned by
         mainWindow.moduleArea.saveState()
        """
        names = []
        if not self.layoutState:
            return names

        layoutState = self.layoutState
        lls = []

        if 'main' in layoutState:
            mains = layoutState['main']
            # lls += list(_traverse(mains))
            lls.extend(_traverse(mains))

        if 'float' in layoutState:
            flts = layoutState['float']
            _floats = _traverse(flts)
            # lls += list(_traverse(flts))
            lls.extend(_floats)
            for itm in _floats:
                if isinstance(itm, dict) and 'main' in itm:
                    lls.extend(_traverse(itm['main']))

        excludeList = ['vertical', 'dock', 'horizontal', 'tab', 'main', 'sizes', 'float']
        names = [i for i in lls if i not in excludeList if isinstance(i, str)]
        return names

    def __str__(self):
        return '<%s: of "%s">' % (self.__class__.__name__, self.application.project.name)


def _traverse(obj, tree_types=(list, tuple)):
    """used to flat the state in a long list"""
    if isinstance(obj, tree_types):
        for value in obj:
            for subvalue in _traverse(value, tree_types):
                yield subvalue
    else:
        yield obj


def _getCcpnModules() -> list:
    """Return a list of ccpn modules defined by the codebase
    """
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule


    _ccpnModules = []
    for app in applicationNames + ['ui/gui']:
        path = ccpnPythonPath / app / 'modules'
        for loader, name, isPpkg in pkgutil.walk_packages([path.asString()]):
            try:
                findModule = loader.find_module(name)
                module = findModule.load_module(name)
            except Exception as es:
                getLogger().debug('Error loading module %r: %s' %
                                  (name, str(es))
                                  )
                continue

            obj=None # to satisfy code inspection error
            try:
                for i, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and \
                            issubclass(obj, CcpnModule) and \
                            hasattr(obj, 'className'):
                        _ccpnModules.append(obj)
            except Exception as es:
                getLogger().debug('Error inspecting module %r, obj=%r: %s' %
                                  (name, obj, str(es))
                                  )
    return _ccpnModules
