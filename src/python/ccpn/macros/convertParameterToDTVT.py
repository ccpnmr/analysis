
from ccpn.core.lib.Pid import Pid, createId

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
                dt = project.newDataTable(name=k)
                dt.data = val.copy()
                dd.deleteDataParameter(name=k)
                
                dt.setMetadata('restraintTable', rtPid)
                dt.setMetadata('violationResult', True)
                itms.add(st)
                itms.add(dt)
                rt = project.getByPid(rtPid)
                if rt:
                    itms.add(rt)
                    
            elif 'run' in k:
                # if a run dataFrame - move to a violationTable in the same structureData
                print(f'   found run {k}')

                # make new violationTable
                vt = st.newViolationTable(name=k)
                vt.data = val.copy()
                dd.deleteDataParameter(name=k)
                
                vt.setMetadata('restraintTable', rtPid)
                itms.add(st)
                itms.add(vt)
                rt = project.getByPid(rtPid)
                if rt:
                    itms.add(rt)
        
        if itms:
            # create a collection of the group
            project.newCollection(items=itms)
