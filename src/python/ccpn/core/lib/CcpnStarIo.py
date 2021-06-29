# Temporary Framework before fixing NEF style Reader


import pandas as pd
import os
import glob
import numpy as np
from collections import OrderedDict as od
from ccpn.util.isotopes import name2IsotopeCode
from ccpn.core.lib.AxisCodeLib import getAxisCodeMatchIndices
from ccpn.framework.PathsAndUrls import macroPath as mp
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import notificationEchoBlocking
from ccpn.core.ChemicalShiftList import ChemicalShiftList

NMRSTARVersion = '3.2.1.32'
NMRSTARV3GROUPS = od([
                    ("citations",
                                (
                                "Citation",
                                "Citation_author",
                                "Citation_editor",
                                "Citation_keyword"
                                )),
                    ("Entry_information", (
                                "deposited_data_files",
                                "entry_information",
                                "entry_interview",
                                "study_list",
                                )),
                    ("Experimental_descriptions",
                                (
                                "applied_software",
                                "applied_software_history",
                                "chromatographic_column",
                                "chromatographic_system",
                                "computer",
                                "EMR_expt",
                                "EMR_instrument",
                                "experiment_list",
                                "fluorescence_instrument",
                                "FRET_expt",
                                "Mass_spec_ref_compd",
                                "Mass_spectrometer",
                                "Mass_spectrometer_list",
                                "method",
                                "molecule_purity",
                                "MS_expt",
                                "NMR_spectral_processing",
                                )),
                    ("Kinetic_data",
                                (
                                "auto_relaxation",
                                "chemical_rates",
                                "dipole_CSA_cross_correlations",
                                "dipole_dipole_cross_correlations",
                                "dipole_dipole_relaxation",
                                "heteronucl_NOEs",
                                "heteronucl_T1_relaxation",
                                "heteronucl_T1rho_relaxation",
                                "heteronucl_T2_relaxation",
                                "H_exch_protection_factors",
                                "H_exch_rates",
                                "homonucl_NOEs",
                                "theoretical_auto_relaxation",
                                "theoretical_dipole_dipole_cross_correlations",
                                "theoretical_heteronucl_NOEs",
                                "theoretical_heteronucl_T1_relaxation",
                                "theoretical_heteronucl_T2_relaxation",
                                )),
                    ("Molecular_assembly",
                                (
                                "assembly",
                                "assembly_annotation",
                                "assembly_subsystems",
                                "chem_comp",
                                "entity",
                                "experimental_source",
                                "natural_source",
                                )),
                    ("NMR_parameters",
                                (
                                "assigned_chemical_shifts",
                                "chem_shift_anisotropy",
                                "chem_shift_isotope_effect",
                                "chem_shift_perturbation",
                                "chem_shift_reference",
                                "chem_shifts_calc_type",
                                "coupling_constants",
                                "dipolar_couplings",
                                "other_data_types",
                                "RDCs",
                                "resonance_linker",
                                "spectral_density_values",
                                "spectral_peak_list",
                                "theoretical_chem_shifts",
                                "theoretical_coupling_constants",
                                )),
                    ("Structure",
                                (
                                "angular_order_parameters",
                                "bond_annotation",
                                "CA_CB_chem_shift_constraints",
                                "conformer_family_coord_set",
                                "conformer_statistics",
                                "constraint_statistics",
                                "deduced_hydrogen_bonds",
                                "deduced_secd_struct_features",
                                "distance_constraints",
                                "floating_chiral_stereo_assign",
                                "force_constants",
                                "general_distance_constraints",
                                "H_chem_shift_constraints",
                                "interatomic_distance",
                                "J_three_bond_constraints",
                                "MS_chromatogram",
                                "MS_MZ_data",
                                "org_constr_file_comment",
                                "other_constraints",
                                "other_struct_features",
                                "peak_constraint_links",
                                "RDC_constraints",
                                "representative_conformer",
                                "SAXS_constraints",
                                "secondary_structs",
                                "structure_annotation",
                                "structure_interactions",
                                "tensor",
                                "tertiary_struct_elements",
                                "torsion_angle_constraints"
                                )),
                    ("Thermodynamic_data",
                        (
                        "binding_data",
                        "binding_param_list",
                        "D_H_fractionation_factors",
                        "order_parameters",
                        "pH_param_list",
                        "pH_titration",
                    ))
                    ])



# Variable definitions from NmrStar 3.1
ID = 'ID'
Assembly_atom_ID = 'Assembly_atom_ID'
Entity_assembly_ID = 'Entity_assembly_ID'
Entity_ID = 'Entity_ID'
Comp_index_ID = 'Comp_index_ID'
Seq_ID = 'Seq_ID'
Comp_ID =  'Comp_ID'
Atom_ID = 'Atom_ID'
Atom_type = 'Atom_type'
Atom_isotope_number = 'Atom_isotope_number'
Val = 'Val'
Val_err = 'Val_err'
Assign_fig_of_merit = 'Assign_fig_of_merit'
Ambiguity_code = 'Ambiguity_code'
Occupancy = 'Occupancy'
Resonance_ID = 'Resonance_ID'
Auth_entity_assembly_ID = 'Auth_entity_assembly_ID'
Auth_asym_ID = 'Auth_asym_ID'
Auth_seq_ID = 'Auth_seq_ID'
Auth_comp_ID = 'Auth_comp_ID'
Auth_atom_ID = 'Auth_atom_ID'
Details = 'Details'
Entry_ID = 'Entry_ID'
Assigned_chem_shift_list_ID = 'Assigned_chem_shift_list_ID'

STOP = "stop_"
_Atom_chem_shift = "_Atom_chem_shift." # used to find the loop of interest in the BMRB and shorten the column header name on the DataFrame
Atom_chem_shift = _Atom_chem_shift+ID


def _getTitles(filePath):
    lines = []
    with open(filePath, "r") as bmrbFileText:
        for line in bmrbFileText:
            if '#' in line:
                lines.append(line)
                break
    return lines

def _getCSListLinesFromBmrbFile(filePath):
    # HardCoded bit to find just the Chemical Shifts, Replace with NEF Style
    lines = []
    with open (filePath, "r") as bmrbFileText:
        for line in bmrbFileText:
            if Atom_chem_shift in line:
                lines.append(line)
                break
        for line in bmrbFileText:
            if STOP in line:
                break
            lines.append(line)
    return lines

def makeCSLDataFrame(bmrbLines):
    ## create dataframe of interest using the same names as appear in the BMRB.
    # NB Columns are not always the same in number (E.G. fileA=10columns, fileB=12columns).
    table = []
    columns = []
    for i in [sub.splitlines() for sub in bmrbLines]:
        vv = [j.strip() for j in i if j]
        columns += [j for j in [i for i in vv if i.startswith('_')]]
        row = [j for i in [i.split(' ') for i in vv if not i.startswith('_')] for j in i if j]
        if len(row)>0:
            table.append(row)
    shortColumns = [c.replace(_Atom_chem_shift,'') for c in columns]
    return pd.DataFrame(table, columns=shortColumns)

def _connectNmrResidues(nmrChain):
    updatingNmrChain = None
    nrs = nmrChain.nmrResidues
    for i in range(len(nrs) - 1):
        currentItem, nextItem = nrs[i], nrs[i + 1]
        if currentItem and nextItem:

            # check that the sequence codes are consecutive
            if int(nextItem.sequenceCode) == int(currentItem.sequenceCode) + 1:
                updatingNmrChain = currentItem.connectNext(nextItem, )
    return updatingNmrChain

def _isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def _isValidValue(row, header):
    if row[header] != '.':
        return True
    else:
        return False

def makeCSLfromDF(project, df):
    """
    :param df: Pandas dataFrame from parsing an NmrStar 3 File.
    :return: ChemicalShiftList Object

    Creates a V3 ChemicalShiftList and associated V3 objects from a dataFrame created parsing an NmrStar 3 File.
    The reader assumes the dataframe contains tags as specified in the bmrb dictionary. See reference.
    TAGs reference: https://bmrb.io/dictionary/tag.php?tagcat=Atom_chem_shift

    +------------------------------|-----------------------------------------+
    + CCPN V3 Object/property      |  BMRB *.TAG (*prefix: _Atom_chem_shift) +
    +------------------------------|-----------------------------------------+
    chemicalShiftList:
                    name           => Entry_ID
    nmrChain(s):
                    name           => Entity_assembly_ID
    NmrResidue(s):
                    sequenceCode   => seq_ID  or Auth_seq_ID (if present)
                    residueType    => Comp_ID
    NmrAtom(s):
                    name           => Atom_ID
                    isotopeCode    => Atom_isotope_number + Atom_type
    ChemicalShift(s):
                    value          => Val
                    valueError     => Val_er
                    comment        => Details

    Others not stored. Maybe save in ChemicalShift internal?
                                   Assembly_atom_ID
                                   Assign_fig_of_merit
                                   Assigned_chem_shift_list_ID
                                   Ambiguity_code
                                   Ambiguity_set_ID
                                   Auth_asym_ID
                                   Occupancy_ID
                                   Resonance_ID
    # TODO: NmrAtom Name => use Auth_atom_ID and Ambiguity_code to create an NEF-compliant nomenclature
    """
    ## check if the required columns are present.
    requiredColumns = [Entry_ID, Entity_assembly_ID, Seq_ID, Auth_seq_ID, Comp_ID, Val, Val_err, Details]
    if not set(requiredColumns).issubset(df.columns):
        missingColumns = [c for c in requiredColumns if not c in df.columns]
        getLogger().warn('Creating ChemicalShiftList failed. Missing some of the required Tags (%s) in the NmrStar file.' %', '.join(missingColumns))
        return
    ## check if the Auth_seq_ID is present (not as '.'). Use the author value as preferred option.
    useAuthSeqID = True if not df[Auth_seq_ID].eq('.').all() else False
    nmrChains = set()
    with notificationEchoBlocking():
        chemicalShiftListName = df[Entry_ID].astype(str, errors='ignore').unique()[-1] #Mandatory tag. Values always present
        # chemicalShiftListName = _incrementObjectName(project, ChemicalShiftList._pluralLinkName, chemicalShiftListName)
        chemicalShiftList = project.newChemicalShiftList(name=chemicalShiftListName)
        for index, row in df.iterrows():
            nmrChain = project.fetchNmrChain(row[Entity_assembly_ID])
            sequenceCode = row[Auth_seq_ID] if useAuthSeqID else row[Seq_ID]
            nmrResidue = nmrChain.fetchNmrResidue(residueType=row[Comp_ID], sequenceCode=sequenceCode)
            nmrAtom = nmrResidue.fetchNmrAtom(row[Atom_ID])
            isotopeCode = row[Atom_isotope_number] + row[Atom_type]
            try:
                nmrAtom._setIsotopeCode(isotopeCode)
            except Exception as icError:
                getLogger().warn('Error setting the IsotopeCode: %s for the nmrAtom %s. %s.' %(isotopeCode, nmrAtom.pid, icError))
            try:
                if _isfloat(row[Val]):
                    cs = chemicalShiftList.newChemicalShift(value=float(row[Val]), nmrAtom=nmrAtom)
                    cs.comment = cs.comment+ ' Imported: '+row[Details]
                    valueErr = row[Val_err]
                    if _isfloat(valueErr):
                        cs.valueError = float(valueErr)
            except Exception as e:
                getLogger().warn('Error creating a new ChemicalShift: %s' %e)
            nmrChains.add(nmrChain)
        # for nmrChain in nmrChains:
        #     nmrChain._connectNmrResidues()

    return chemicalShiftList

def _simulatedSpectrumFromCSL(project, csl, axesCodesMap):
    """

    key= NmrAtom name as appears in the CSL ; value = AxisCode name to Assign to the Spectrum AxisCode
    E.G. use NmrAtom Ca from CSL (imported from BMRB) and assign to a peak with axisCode named C

    :param csl: chemicalShiftList Object
    :param axesCodesMap: Ordered Dict containing Atoms of interest and parallel Spectrum Axes Codes
    :return:
    """
    success = False
    if csl is None:
        getLogger().warn("Provide a Chemical Shift List")
        return success
    if axesCodesMap is None:
        getLogger().warn("Select NmrAtom to use and axis codes")
        return success
    with notificationEchoBlocking():
        nmrAtomNames = list(axesCodesMap.keys())
        isotopeCodes = [name2IsotopeCode(x) for x in list(axesCodesMap.values())]
        targetSpectrum =  project.newEmptySpectrum(isotopeCodes=isotopeCodes, name=csl.name)
        targetSpectrum.chemicalShiftList = csl
        peakList = targetSpectrum.peakLists[-1]

        # filter by NmrAtom of interest
        nmrResiduesOD = od()
        for chemicalShift in csl.chemicalShifts:
            na = chemicalShift.nmrAtom
            if na.name in nmrAtomNames:
                try:
                    nmrResiduesOD[na.nmrResidue].append([na, chemicalShift.value])
                except KeyError:
                    nmrResiduesOD[na.nmrResidue] = [(na, chemicalShift.value)]

        incompleteNmrResiduesAssignments = []
        for nmrResidue in nmrResiduesOD:
            shifts = []
            atoms = []
            for v in nmrResiduesOD[nmrResidue]:
                atoms.append(v[0])
                shifts.append(v[1])

            targetSpectrumAxCodes = targetSpectrum.axisCodes
            axisCodes = [n.name for n in atoms]
            i = getAxisCodeMatchIndices(axisCodes,targetSpectrumAxCodes) # get the correct order.
            if len(i) != len(nmrAtomNames): #if not all the NmrAtoms are found for a specific CSL cannot make the peak, incomplete assignment/shifts
                incompleteNmrResiduesAssignments.append(nmrResidue.pid)
                continue

            i = np.array(i)
            shifts = np.array(shifts)
            atoms = np.array(atoms)
            try: # trap unknown issues
                peak = peakList.newPeak(list(shifts[i]))
                for na, sa in zip(atoms[i],targetSpectrumAxCodes) :
                    peak.assignDimension(sa, [na])
            except Exception as e:
                getLogger().warn('Error assigning NmrResidue %s , NmrAtoms: %s, Spectrum Axes: %s, Shifts: %s . Error: %s'
                      %(nmrResidue,atoms,targetSpectrumAxCodes,shifts, e))
        if len(incompleteNmrResiduesAssignments)>0:
            message = 'Could not fully assign peaks for NmrResidue(s): %s. ' \
                      'Not enough nmrAtom information.' %', '.join(incompleteNmrResiduesAssignments)
            getLogger().warn(message)
    success = True
    return success


def _importAndCreateV3Objs(project, file, acMap, simulateSpectra=False):
    getLogger().info('NmrStar file import started...')
    success = False
    lines = _getCSListLinesFromBmrbFile(file)
    df = makeCSLDataFrame(lines)
    with undoBlock():
        csl = makeCSLfromDF(project, df)
        if csl is not None:
            success = True
            if simulateSpectra:
                success = _simulatedSpectrumFromCSL(project, csl, axesCodesMap=acMap)
        else:
            getLogger().warn('NmrStar file import aborted.')
            return success
    getLogger().info('NmrStar file import completed.')
    return success

