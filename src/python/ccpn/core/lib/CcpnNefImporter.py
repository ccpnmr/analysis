
from ccpn.framework.Application import getApplication
from ccpn.core.lib.CcpnNefIo import CcpnNefReader

from ccpn.util.Logging import getLogger
from ccpn.util.nef.NefImporter import NefImporter
from ccpn.util.nef.ErrorLog import NEF_STANDARD, NEF_STRICT, NEF_SILENT
from ccpn.core.lib.ContextManagers import catchExceptions, undoBlockWithoutSideBar, notificationEchoBlocking


class CcpnNefImporter(NefImporter):
    """A class for cutimization of the general NefImporter class
    """

    def __init__(self, errorLogging=NEF_STANDARD, hidePrefix = True):

        _app = getApplication()
        super().__init__(programName=_app.applicationName,
                         programVersion=_app.applicationVersion,
                         errorLogging=errorLogging,
                         hidePrefix=hidePrefix)

        # set the ccpn logger
        _logger = getLogger().error if errorLogging == NEF_STRICT else getLogger().warning
        self.logger = _logger

        self._reader = None
        self._application = _app

    def importToProject(self, project):
        """Import the data of self into the project, using a previously attached
        reader (auto-generated if None).

        :param project: a Project instance
        """
        if self._reader is None:
            _reader = CcpnNefReader(application=self._application)
        else:
            _reader = self._reader

        with catchExceptions(errorStringTemplate='Error importing Nef data: %s',
                             printTraceBack=True):
            with undoBlockWithoutSideBar():
                with notificationEchoBlocking():
                    _reader.importExistingProject(project, self.data)

        getLogger().info('==> Imported Nef data %r into %s' % (self.getName(), project))