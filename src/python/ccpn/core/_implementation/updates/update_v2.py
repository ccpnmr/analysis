
from ccpn.util.Logging import getLogger
from ccpn.framework.Version import applicationVersion

def updateProject_fromV2(project):
    """Update actions for a V2 project
    """

    if project.isUpgradedFromV2:
        # Regrettably this V2 upgrade operation must be done at the wrapper level.
        # No good place except here
        for structureEnsemble in project.structureEnsembles:
            data = structureEnsemble.data
            if data is None:
                getLogger().warning("%s has no data. This should never happen")
            else:
                data._containingObject = structureEnsemble

    project._objectVersion = applicationVersion
