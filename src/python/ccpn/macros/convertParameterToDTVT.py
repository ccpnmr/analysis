"""
Move parameters from structureData to violationTables
"""
from ccpn.core.lib.Pid import Pid, createId


_RESTRAINTTABLE = 'restraintTable'
_VIOLATIONTABLE = 'violationTable'
_VIOLATIONRESULT = 'violationResult'
_RUNNAME = 'runName'
DEFAULT_RUNNAME = 'output'

# loop through the structureData
for st in project.structureData:

    # loop through the data list
    for dd in st.data:
        print(f' found data {dd.name}')
        itms = set()
        rtPid = Pid._join('RT', st.name, dd.name)

        # loop throught the data parameters containing the dataFrames
        for k, val in dd.dataParameters.items():

            if 'results' in k:
                # if a results dataFrame - move to a dataTable
                print(f'   found results {k}')

                # make new dataTable
                vTable = project.newDataTable(name=k)
                vTable.data = val.copy()
                dd.deleteDataParameter(name=k)

                vTable.setMetadata(_RESTRAINTTABLE, rtPid)
                vTable.setMetadata(_VIOLATIONRESULT, True)
                itms.add(st)
                itms.add(vTable)
                rt = project.getByPid(rtPid)
                if rt:
                    itms.add(rt)

            elif 'run' in k:
                # if a run dataFrame - move to a violationTable in the same structureData
                print(f'   found run {k}')

                # make new violationTable
                vTable = st.newViolationTable(name=k)
                vTable.data = val.copy()
                dd.deleteDataParameter(name=k)

                vTable.setMetadata(_RESTRAINTTABLE, rtPid)
                itms.add(st)
                itms.add(vTable)
                rt = project.getByPid(rtPid)
                if rt:
                    itms.add(rt)

        if itms:
            # create a collection of the group
            project.newCollection(items=itms)
