"""Class to implement the updater routine;
decorator to populate with data

Objects can be initialised pre-object-initialisation (ie. modifying the v2 api data),
post-object-initialisation (i.e. after it is generated, but potentially before other objects
are present, such as the children, or post-project-initialisation (i.e. after the project
and its children have been fully initialised.

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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-11-29 12:01:53 +0000 (Mon, November 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2021-11-10 10:28:41 +0000 (Wed, November 10, 2021) $"
#=========================================================================================
# Start of code
#========================================================================================

from ccpn.util.decorators import singleton
from collections import defaultdict

from ccpn.util.Logging import getLogger
from ccpn.framework.Version import applicationVersion


UPDATE_PRE_OBJECT_INITIALISATION = 'update_pre_object_initialisation'
UPDATE_POST_OBJECT_INITIALISATION = 'update_post_object_initialisation'
UPDATE_POST_PROJECT_INITIALISATION = 'update_post_project_initialisation'


@singleton
class Updater(object):
    """The updater class; only one instance is initiated, owned by AbstractWrapperObject
    """
    # As there is only one instance; we make these attributes class attributes
    preObjectUpdateFunctions = defaultdict(list)
    postObjectUpdateFunctions = defaultdict(list)
    postProjectUpdateFunctions = defaultdict(list)

    functionsByType = {}
    functionsByType[UPDATE_PRE_OBJECT_INITIALISATION] = preObjectUpdateFunctions
    functionsByType[UPDATE_POST_OBJECT_INITIALISATION] = postObjectUpdateFunctions
    functionsByType[UPDATE_POST_PROJECT_INITIALISATION] = postProjectUpdateFunctions

    def _updateApiObject(self, apiObj, updateFunctions):
        """Updates obj using the _updateFunctions stack for obj.className;
        """
        # update the object
        raise NotImplementedError('Not yet implemented')

    def _updateV3Object(self, obj, updateFunctions):
        """Updates obj using the updateFunctions stack for obj.className;
        """
        logger = getLogger()
        for fromVersion, toVersion, func in updateFunctions:
            currentVersion = obj._objectVersion

            if fromVersion is not None and currentVersion < fromVersion:
                raise RuntimeError('Error trying to update %s from version %s to version %s; invalid current version %s' % \
                                   (obj, fromVersion, toVersion, currentVersion))
            if currentVersion < toVersion:
                logger.debug('Updating %s: fromVersion: %s, currentVersion: %s, toVersion: %s, func: %s' %
                         (obj, fromVersion, currentVersion, toVersion, func)
                )
                func(obj)
            obj._objectVersion = toVersion

    def update(self, updateMethod, obj, klass=None):
        """Updates obj using the various updateFunctions stacks for
        klass.className or obj.className;
        """

        if updateMethod == UPDATE_PRE_OBJECT_INITIALISATION:
            self._updateApiObject(obj, self.preObjectUpdateFunctions[klass.className])

        elif updateMethod == UPDATE_POST_OBJECT_INITIALISATION:
            self._updateV3Object(obj, self.postObjectUpdateFunctions[obj.className])

        elif updateMethod == UPDATE_POST_PROJECT_INITIALISATION:
            self._updateV3Object(obj, self.postProjectUpdateFunctions[obj.className])
            # The object is by definition now at the current application version state
            obj._objectVersion = applicationVersion

        else:
            raise RuntimeError('updateObject: invalid updateMethod "%s"' % (updateMethod))

    def __str__(self):
        return'<Updater>'


def updateObject(fromVersion, toVersion, updateFunction, updateMethod):
    """Class decorator to register updateFunction for a core-class for one of the
    the three update methods

    updateFunction updates the objects -objectVersion attribute from "fromVersion"
    to the (next) higher version "toVersion";
    fromVersion can be None, in which case no initial check on objectVersion is done

    def updateFunction(obj)
        obj: object that is being updated

    or

    def updateFunction(apiObj)
        apiObj: apiObject that is being updated

    """

    def theDecorator(cls):
        """This function will decorate cls with _update, _updateHandler list and registers the updateHandler
        """
        if not hasattr(cls, '_updater'):
            raise RuntimeError('class %s does not have the attribute _updater')
        updater = cls._updater

        if updateMethod == UPDATE_PRE_OBJECT_INITIALISATION:
            updater.preObjectUpdateFunctions[cls.className].append( (fromVersion, toVersion, updateFunction) )

        elif updateMethod == UPDATE_POST_OBJECT_INITIALISATION:
            updater.postObjectUpdateFunctions[cls.className].append( (fromVersion, toVersion, updateFunction) )

        elif updateMethod == UPDATE_POST_PROJECT_INITIALISATION:
            updater.postProjectUpdateFunctions[cls.className].append( (fromVersion, toVersion, updateFunction) )

        else:
            raise RuntimeError('updateObject class %s, invalid updateMethod "%s"' % (cls, updateMethod))

        return cls

    return theDecorator


