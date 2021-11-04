"""
Create random restraints for testing violations table
Prints the list for inserting into a nef saveFrame
"""

import random
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

print('Create random restraints for testing violations table')

with undoBlockWithoutSideBar():
    for rs in project.restraints:
        rs.delete()
    
    _index = 0
    for rl in project.restraintTables:
        for rsCount in range(8):
    
            pks = ()
            for pl in project.peakLists:
                ll = len(pl.peaks) - 1
                pks += tuple(set(pl.peaks[random.randint(0, ll)] for ii in range(3)))
    
            rs = rl.newRestraint(peaks=pks)
            
            at = len(project.atoms) - 1
            rc = rs.newRestraintContribution()
    
            for riCount in range(random.randint(1, 3)):
                _index += 1
                atms = tuple(project.atoms[random.randint(0, at)].id for ii in range(4))
                try:
                    rc.addRestraintItem(atms)
                    atOut = '   '.join([st for atm in atms for st in atm.split('.')])
                    vv = round(random.random(), 3)
                    print(f' {_index}   1   {rs.serial}   {riCount+1}   {atOut}  1.0   .   1.8   3.2   3.275   {vv}   .   .   .   id{_index}   comment{_index}')
                except Exception as es:        
                    try:
                        rc.addRestraintItem(atms[:2])
                        atOut = '   '.join([st for atm in atms[:2] for st in atm.split('.')])
                        vv = round(random.random(), 3)
                        print(f' {_index}   1   {rs.serial}   {riCount+1}   {atOut}  1.0   .   1.8   3.2   3.275   {vv}   .   .   .   id{_index}   comment{_index}')
                    except Exception as es:
                        try:
                            rc.addRestraintItem(atms[:4])
                            atOut = '   '.join([st for atm in atms[:4] for st in atm.split('.')])
                            vv = round(random.random(), 3)
                            print(f' {_index}   1   {rs.serial}   {riCount+1}   {atOut}  1.0   .   1.8   3.2   3.275   {vv}   .   .   .   id{_index}   comment{_index}')
                        except Exception as es:
                            pass
                        
# # just list some restraints for the minute
# for restraint in project.restraints:
#     for rc in restraint.restraintContributions:
#         print(f'     {rc.serial}')
#         for ri in list(rc._wrappedData.items):
#             print(f'     {ri}')
