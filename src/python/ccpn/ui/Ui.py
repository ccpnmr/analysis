"""Default application no-user-interface UI implementation
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:40 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-03-22 13:00:57 +0000 (Wed, March 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import typing
import re

from ccpn.core.Project import Project
from ccpn.ui._implementation import _uiImportOrder
from ccpn.core import _coreClassMap
from ccpn.core.lib.Notifiers import NotifierBase

from ccpn.util import Register
from ccpn.util.Update import installUpdates, UpdateAgent
from ccpn.util.Logging import getLogger


class Ui(NotifierBase):
    """Superclass for all user interface classes"""

    # Factory functions for UI-specific instantiation of wrapped graphics classes
    _factoryFunctions = {}

    def __init__(self, application):

        self.application = application
        self.mainWindow = None
        self.pluginModules = []

    def addMenu(self, name, position=None):
        '''
        Add a menu specification for the top menu bar.
        '''
        if position is None:
            position = len(self._menuSpec)
        self._menuSpec.insert(position, (str(name), []))

    @classmethod
    def setUp(cls):
        """Set up graphics data classes, cleaning up previous settings"""

        for className in _uiImportOrder:
            # Remove ui-specific settings. Will be reset as necessary in subclasses
            _coreClassMap[className]._factoryFunction = cls._factoryFunctions.get(className)

    def initialize(self, mainWindow):
        """UI operations done after every project load/create"""
        pass

    def start(self):
        """Start the program execution"""

        # self._checkRegistered()
        # Register.updateServer(Register.loadDict(), self.application.applicationVersion)

        sys.stderr.write('==> %s interface is ready\n' % self.__class__.__name__)

    def _checkRegistration(self):
        """Check if registered and if not popup registration and if still no good then exit"""

        # checking the registration; need to have the app running, but before the splashscreen, as it will hang
        # in case the popup is needed.
        # We want to give some feedback; sometimes this takes a while (e.g. poor internet)
        # sys.stderr.write('==> Checking registration ... \n')
        sys.stderr.flush()  # It seems to be necessary as without the output comes after the registration screen

        # check local registration details
        if not self._isRegistered:
            # call the subclassed register method
            self._registerDetails()
            if not self._isRegistered:
                days = Register._graceCounter(Register._fetchGraceFile(self.application))
                if days > 0:
                    sys.stderr.write('\n### Please register within %s day(s)\n' %days)
                    return True
                else:
                    sys.stderr.write('\n### INVALID REGISTRATION, terminating\n')
                    return False

        #     # sys.stderr.write('==> Registered to: %s (%s)\n' %
        #     #                  (self.application._registrationDict.get('name'),
        #     #                   self.application._registrationDict.get('organisation')))
        #       return Register.updateServer(self.application._registrationDict, self.application.applicationVersion)
        #
        # else:

        # check whether your registration details are on the server (and match)
        check = Register.checkServer(self.application._registrationDict, self.application.applicationVersion)
        if check is None:
            return True
        if check is False:
            self._registerDetails()
            check = Register.checkServer(self.application._registrationDict, self.application.applicationVersion)

        return check if check is not None else True

    def echoCommands(self, commands: typing.List[str]):
        """Echo commands strings, one by one, to logger.
        Overwritten in subclasses to handle e.g. console putput
        """
        logger = getLogger()
        for command in commands:
            logger.info(command)

    def _execUpdates(self):
        raise ('ERROR: ..to be subclassed by ui types')

    def _checkUpdates(self):
        from ccpn.framework.Version import applicationVersion
        # applicationVersion = __version__.split()[1]  # ejb - read from the header

        updateAgent = UpdateAgent(applicationVersion, dryRun=False)
        numUpdates = updateAgent.checkNumberUpdates()
        # sys.stderr.write('==> Updates available: %s\n' % str(numUpdates))

        if numUpdates:
            self._execUpdates()

        return True

    @property
    def _isRegistered(self):
        """return True if registered"""
        self.application._registrationDict = Register.loadDict()
        return not Register.isNewRegistration(self.application._registrationDict)


class NoUi(Ui):

    def _registerDetails(self):
        """Display registration information
        """

        # check valid internet connection first
        if not Register.checkInternetConnection():
            sys.stderr.write('Could not connect to the registration server, please check your internet connection.')
            sys.exit(0)

        from ccpn.framework.Version import applicationVersion
        # applicationVersion = __version__.split()[1]

        # sys.stderr.write('\n### Please register, using another application, or in Gui Mode\n')

        from ccpn.framework.PathsAndUrls import licensePath

        try:
            self.application.showLicense()
        except:
            sys.stderr.write('The licence file can be found at %s\n' % licensePath)

        validEmailRegex = re.compile(r'^[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-_]+\.)+[A-Za-z]{2,63}$')

        sys.stderr.write('Please take a moment to read the licence\n')
        agree = None
        while agree is None:
            agreeIn = input('Do you agree to the terms and conditions of the Licence? [Yes/No]')
            if agreeIn.lower() in ['y', 'yes']:
                agree = True
            elif agreeIn.lower() in ['n', 'no']:
                agree = False
            else:
                sys.stderr.write("Enter 'yes' or 'no'\n")

        if agree:
            registrationDict = {}

            sys.stderr.write("Please enter registration details:\n")

            # ('name', 'organisation', 'email')

            for n, attr in enumerate(Register.userAttributes):
                if 'email' in attr:
                    validEmail = False
                    while validEmail is False:
                        regIn = input(attr + ' >')
                        registrationDict[attr] = regIn or ''

                        validEmail = True if validEmailRegex.match(regIn) else False
                        if not validEmail:
                            sys.stderr.write(attr + ' is invalid, please try again\n')

                else:
                    regIn = input(attr + ' >')
                    registrationDict[attr] = regIn or ''

            Register.setHashCode(registrationDict)
            Register.saveDict(registrationDict)
            Register.updateServer(registrationDict, applicationVersion)

        else:
            sys.stderr.write('You must agree to the licence to continue')
            sys.exit(0)

    def _execUpdates(self):
        sys.stderr.write('==> NoUi update\n')

        from ccpn.framework.Version import applicationVersion
        # applicationVersion = __version__.split()[1]  # ejb - read from the header
        installUpdates(applicationVersion, dryRun=False)

        sys.stderr.write('Please restart the program to apply the updates\n')
        sys.exit(1)


class TestUi(NoUi):

    def __init__(self, application):
        Ui.__init__(self, application)
        application._consoleOutput = []

    def echoCommands(self, commands: typing.List[str]):
        """Echo commands strings, one by one, to logger
        and store them in internal list for perusal
        """
        self.application._consoleOutput.extend(commands)
        logger = getLogger()
        for command in commands:
            logger.info(command)
