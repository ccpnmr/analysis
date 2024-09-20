"""
This file contains the SpectrumView classes (1D and nD versions)
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-09-20 15:02:11 +0100 (Fri, September 20, 2024) $"
__version__ = "$Revision: 3.2.7 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-01-24 10:28:48 +0000 (Tue, January 24, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui._implementation.SpectrumView import SpectrumView as _CoreClassSpectrumView
from ccpn.ui.gui.lib.GuiSpectrumView1d import GuiSpectrumView1d as _GuiSpectrumView1d
from ccpn.ui.gui.lib.GuiSpectrumViewNd import GuiSpectrumViewNd as _GuiSpectrumViewNd
from ccpn.ui.gui.guiSettings import _styleBlue

from ccpn.core.Project import Project
from ccpn.util.Logging import getLogger


_DEBUG = False


class SpectrumView(_CoreClassSpectrumView):

    @classmethod
    def _newInstanceFromApiData(cls, apiObj, project=None):
        """Return a new instance of cls, initialised with data from apiObj.
        Checks for existence, and potential factory function.
        """
        from ccpn.framework.Application import getProject

        # override cls-type - 1D/nD display
        klass = SpectrumView1d if ('intensity' in apiObj.strip.spectrumDisplay.axisCodes) else SpectrumViewNd
        if project is None:
            project = getProject()
        if apiObj in project._data2Obj:
            # This happens with Window, as it get initialised by the Window-Store and then once
            # more as child of Project
            newInstance = project._data2Obj[apiObj]
            if _DEBUG:
                getLogger().debug(_styleBlue(f'==> found  {id(newInstance)}  {newInstance}'
                                             f'\n                     {apiObj}'
                                             ))
        elif (_factoryFunction := klass._factoryFunction) is not None:
            newInstance = _factoryFunction(project, apiObj)
        else:
            newInstance = klass(project, apiObj)

        if newInstance is None:
            raise RuntimeError(f'Error creating new instance of class "{klass.__name__}"')

        return newInstance


class SpectrumView1d(SpectrumView, _GuiSpectrumView1d):
    """1D Spectrum View
    """

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):
        # _CoreClassSpectrumView.__init__(self, project, wrappedData)
        SpectrumView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application

        getLogger().debug('SpectrumView1d>> %s' % self)
        _GuiSpectrumView1d.__init__(self)


class SpectrumViewNd(SpectrumView, _GuiSpectrumViewNd):
    """nD Spectrum View
    """

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):
        # _CoreClassSpectrumView.__init__(self, project, wrappedData)
        SpectrumView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application

        getLogger().debug('SpectrumViewNd>> self=%s strip=%s' % (self, self.strip))
        _GuiSpectrumViewNd.__init__(self)
