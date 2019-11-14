# Temporary Framework before fixing NEF style Reader


import pandas as pd
import os
import glob
import numpy as np
from collections import OrderedDict as od
from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.framework.PathsAndUrls import macroPath as mp
from ccpn.core.lib.ContextManagers import undoBlock
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



_Atom_chem_shift = "_Atom_chem_shift." # used to find the loop of interest in the BMRB and shorten the column header name on the DataFrame

# only the entries of interest to map to CcpNmr V3 objects. Can be increased as needed
ID = "ID"
Seq_ID = "Seq_ID"
Comp_ID = "Comp_ID"
Atom_ID = "Atom_ID"
Atom_type = "Atom_type"
Val = "Val"
Val_err = "Val_err"
Details = "Details"
STOP = "stop_"
Atom_chem_shift = _Atom_chem_shift+ID

def _getTitles(filePath):
    lines = []
    with open(filePath, "r") as bmrbFileText:
        for line in bmrbFileText:
            if '#' in line:
                lines.append(line)
                break
    return lines

def _openBmrb(filePath):
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

def makeDataFrame(bmrbLines):
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

def makeCSLfromDF(project, df, chemicalShiftListName=None):
    """

    :param df: Pandas dataFrame
    :param chemicalShiftListName: str, default if None
    :return: Chemical Shift List Object
    """

    chemicalShiftList = project.newChemicalShiftList(name=chemicalShiftListName)

    nmrChain = project.fetchNmrChain()
    for index, row in df.iterrows():
        nmrResidue = nmrChain.fetchNmrResidue(residueType=row[Comp_ID], sequenceCode=row[Seq_ID])
        nmrAtom = nmrResidue.fetchNmrAtom(row[Atom_ID])
        if chemicalShiftList:
            try:
                if row[Val] is not None:
                    cs = chemicalShiftList.newChemicalShift(value=float(row[Val]), nmrAtom=nmrAtom)
                    if row[Val_err] is not None:
                        cs.valueError = float(row[Val_err])
            except Exception as e:
                print('Error in creating new shift.', e)
    return chemicalShiftList


def _simulatedSpectrumFromCSL(project, csl, axesCodesMap):
    """

    key= NmrAtom name as appears in the CSL ; value = AxisCode name to Assign to the Spectrum AxisCode
    E.G. use NmrAtom Ca from CSL (imported from BMRB) and assign to a peak with axisCode named C

    :param csl: chemicalShiftList Object
    :param axesCodesMap: Ordered Dict containing Atoms of interest and parallel Spectrum Axes Codes
    :return:
    """
    if csl is None:
        print("Provide a Chemical Shift List")
        return
    if axesCodesMap is None:
        print("Select NmrAtom to use and axis codes")
        return

    nmrAtomNames = list(axesCodesMap.keys())
    targetSpectrumAxCodes = list(axesCodesMap.values())
    targetSpectrum = project.createDummySpectrum(axisCodes=targetSpectrumAxCodes, name=None)#, chemicalShiftList=csl)
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
            print('Skipping, not enough information to create and assign peak for NmrResidue: %s' %nmrResidue)
            continue

        i = np.array(i)
        shifts = np.array(shifts)
        atoms = np.array(atoms)
        try: # trap unknown issues
            peak = peakList.newPeak(list(shifts[i]))
            for na, sa in zip(atoms[i],targetSpectrumAxCodes) :
                peak.assignDimension(sa, [na])
        except Exception as e:
            print('Error assigning NmrResidue %s , NmrAtoms: %s, Spectrum Axes: %s, Shifts: %s . Error: %s'
                  %(nmrResidue,atoms,targetSpectrumAxCodes,shifts, e))

def _importAndCreateV3Objs(project, file, acMap, simulateSpectra=False):
    lines = _openBmrb(file)
    df = makeDataFrame(lines)
    with undoBlock():
        csl = makeCSLfromDF(project, df)
        if simulateSpectra:
            _simulatedSpectrumFromCSL(project, csl, axesCodesMap=acMap)

