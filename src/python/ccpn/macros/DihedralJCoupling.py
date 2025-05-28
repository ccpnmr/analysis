from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.PulldownListsForObjects import MultipletListPulldown, RestraintTablePulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets import CheckBox, LineEdit
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.framework.Application import getApplication
import pandas as pd
from math import radians, cos, sqrt
from pandas import DataFrame
from ccpn.core.NmrAtom import NmrAtom

class DihedralRestraintPopup(CcpnDialogMainWidget):
    FIXEDWIDTH = True
    title = 'Generate Dihedral Restraints from J Couplings'

    def __init__(self, parent=None, mainWindow=None, title=title, **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, size=(500, 300), **kwds)
        self.mainWindow = mainWindow
        self.application = getApplication()
        self.project = self.application.project if self.application else None
        self._dataframe = None  # To store analysis results

        self._createWidgets()


    def calculate_average_coupling(self, multiplet, spectrum, y_threshold=0.01, scalingFactor=1):
        """Calculate average J-coupling constant from multiplet peaks.

        Args:
            multiplet: NMR multiplet object containing peaks
            spectrum: NMR spectrum object containing acquisition parameters
            y_threshold: Maximum ppm difference for considering peaks aligned in Y-dimension
            fudge: Empirical factor to scale final coupling values

        Returns:
            Tuple of (average coupling in Hz, measurement error)
        """

        # Extract and validate peaks
        peaks = list(multiplet.peaks)
        if not peaks:
            return 0.0, 0.0  # Handle case with no peaks

        # Sort peaks by Y-position (second element in ppmPositions tuple)
        peaks_sorted = sorted(peaks, key=lambda pk: pk.ppmPositions[1])

        # Cluster peaks based on Y-position proximity
        clusters = []
        current_cluster = [peaks_sorted[0]]
        for pk in peaks_sorted[1:]:
            # Check if current peak is within threshold of previous cluster member
            if abs(pk.ppmPositions[1] - current_cluster[-1].ppmPositions[1]) <= y_threshold:
                current_cluster.append(pk)
            else:
                clusters.append(current_cluster)
                current_cluster = [pk]
        clusters.append(current_cluster)  # Add final cluster

        # Get spectrometer frequency for X-dimension (converts ppm to Hz)
        try:
            sf_x = spectrum.spectrometerFrequencies[0]  # X-axis frequency in MHz
        except AttributeError:
            raise ValueError("Spectrometer frequency could not be retrieved.")

        # Calculate coupling constants from peak pairs
        coupling_values = []
        for cluster in clusters:
            # Sort cluster by X-position to pair adjacent peaks
            cluster_sorted = sorted(cluster, key=lambda pk: pk.ppmPositions[0])

            # Process peak pairs (step through sorted list in steps of 2)
            for i in range(0, len(cluster_sorted) - 1, 2):
                pk1 = cluster_sorted[i]
                pk2 = cluster_sorted[i + 1]

                # Calculate coupling from X-position difference
                delta_ppm = abs(pk1.ppmPositions[0] - pk2.ppmPositions[0])
                coupling_hz = delta_ppm * sf_x  # Convert ppm to Hz
                coupling_values.append(coupling_hz)

        # Handle case with no valid couplings
        if not coupling_values:
            return 0.0, 0.0

        # Calculate statistics
        average_coupling = sum(coupling_values) / len(coupling_values)
        std_dev = sqrt(sum((x - average_coupling)**2 for x in coupling_values) / len(coupling_values))
        error = 2 * std_dev  # 2-sigma error (~95% confidence interval)

        return average_coupling / scalingFactor, error / scalingFactor  # Apply empirical scaling factor

    def calculate_dihedral_angles(self, j, ka=6.51, kb=-1.76, kc=1.60, tolerance=0.1, likelyPhiOnly=True):
        """Calculate possible dihedral angles from coupling constant using Karplus equation.

        Args:
            j: Measured coupling constant (Hz)
            ka, kb, kc: Karplus equation coefficients
            tolerance: Acceptable deviation from calculated J-value

        Returns:
            Tuple of (list of angle ranges, list of associated errors)
        """

        angles = []
        # Test all possible angles from -180 to 0 degrees
        # left hand helices are rare and B sheets and Right handed helices have negative phi
        maxPhi = 0
        if likelyPhiOnly == False: maxPhi = 180
        for phi in range(-180, maxPhi):
            theta = radians(phi - 60)  # Karplus equation uses θ = φ - 60
            cos_theta = cos(theta)
            computed_j = (ka * (cos_theta**2)) + (kb * cos_theta) + kc

            if abs(computed_j - j) <= tolerance:
                angles.append(phi)

        # Handle case where no angles match
        if not angles:
            return [], []

        # Group consecutive angles into continuous ranges
        grouped = []
        current_group = [angles[0]]
        for a in angles[1:]:
            if a == current_group[-1] + 1:  # Check for consecutive numbers
                current_group.append(a)
            else:
                grouped.append(current_group)
                current_group = [a]
        grouped.append(current_group)  # Add final group

        # Calculate statistics for each angle range
        results = []
        errors = []
        for group in grouped:
            avg = sum(group) / len(group)
            error_val = (max(group) - min(group)) / 2  # Half-range error
            results.append(avg)
            errors.append(error_val)

        return results, errors

    def analyze_multiplets(self, mpl, tolerance=0.1, likelyPhiOnly=True, scalingFactor=1):
        """Main analysis function processing all multiplets in a spectrum.

        Args:
            mpl: Multiplet list object from NMR spectrum
            tolerance: Minimum acceptable error for angle calculations
            likelyPhiOnly: Only return negative phi angles (true for all but rare left handed helices)
            scalingFactor: scaling factor for coupling constants

        Returns:
            pandas.DataFrame containing analysis results
        """

        spectrum = mpl.spectrum
        multiplet_list = mpl.multiplets
        data = []
        restraints = []

        for multiplet in multiplet_list:
            # Calculate coupling statistics
            avg_coupling, error = self.calculate_average_coupling(multiplet, spectrum, scalingFactor=scalingFactor)

            # Calculate angles using maximum of user tolerance or measurement error
            angles, angles_errors = self.calculate_dihedral_angles(avg_coupling, tolerance=max(tolerance, error),
                                                              likelyPhiOnly=likelyPhiOnly)

            # Format results for output
            data.append({
                'MultipletPID': multiplet.pid,
                '3J'          : avg_coupling,
                'Error3J'     : error,
                'Angle'       : ', '.join(map(str, angles)) if angles else 'None',
                #'DihedralAngleError': max(angles_errors) if angles_errors else 1  # Default error if none found
                })

        return pd.DataFrame(data)

    def create_angle_restraints_from_dataframe(self, df: DataFrame, restraintTable) -> list:
        """Create angle restraints from dataframe with multiplet and angle information

        Args:
            df: Input dataframe containing:
                - MultipletPID: PID of the multiplet (e.g. 'MT:L6A_DQF_COSY.1.1')
                - Angle: Comma-separated angle strings (e.g. '-179.0, -61.0')
                - 3J: Coupling constant values
                - Error3J: Coupling constant errors
            restraintTable: CCPN RestraintTable to add restraints to

        Returns:
            List of created Restraint objects
        """
        created_restraints = []

        # Expand angles into separate rows
        df = df.copy()
        df['Angle'] = df['Angle'].apply(lambda x: [float(a.strip()) for a in x.split(',')])
        exploded_df = df.explode('Angle')

        for _, row in exploded_df.iterrows():
            try:
                # Get multiplet and peaks
                multiplet = self.project.getByPid(row['MultipletPID'])
                peaks = list(multiplet.peaks)

                # Get assigned atoms from first peak (assuming same assignment for all peaks)
                assigned_atoms = multiplet.peaks[0].assignedNmrAtoms[0]
                current_h, current_ha = assigned_atoms  # H and HA of current residue

                # Get previous residue through H atom's nmrResidue
                nmr_residue = current_h.nmrResidue
                prev_nmr_residue = nmr_residue.previousNmrResidue
                #print(prev_nmr_residue)
                # Skip if no previous residue
                if prev_nmr_residue is None:
                    continue

                # Build restraint items using previous residue C and current residue atoms

                na = f"{prev_nmr_residue.pid.replace('NR:', 'NA:')}.C"
                if self.project.getByPid(na) is None:
                    prev_nmr_residue.fetchNmrAtom('C')

                for na in ["N", "CA", "C"]:
                    if self.project.getByPid(f"{nmr_residue.pid.replace('NR:', 'NA:')}.{na}") is None:
                        nmr_residue.fetchNmrAtom(na)

                restraint_items = [[
                    f"{prev_nmr_residue.pid.replace('NR:', '')}.C",
                    f"{nmr_residue.pid.replace('NR:', '')}.N",
                    f"{nmr_residue.pid.replace('NR:', '')}.CA",
                    f"{nmr_residue.pid.replace('NR:', '')}.C"
                    ]]

                # print(restraint_items)
                # Validate all atoms exist
                if any(a is None for a in restraint_items):
                    continue

                # Create angle restraint with ±20 degree limits
                target_angle = row['Angle']
                comment = f"Dihedral from {prev_nmr_residue.sequenceCode}{prev_nmr_residue.sequenceCode} to {nmr_residue.sequenceCode}{nmr_residue.residueType}"

                restraint = restraintTable.createSimpleRestraint(
                        comment=comment,
                        targetValue=target_angle,
                        error=row['Error3J'],
                        upperLimit=target_angle + 20,
                        lowerLimit=target_angle - 20,
                        restraintItems=restraint_items,
                        peaks=peaks,
                        weight=1.0
                        )

                created_restraints.append(restraint)

            except Exception as e:
                print(f"Failed processing row {_}: {e}")
                continue

        return created_restraints

    def _createWidgets(self):
        row = 0
        Label(self.mainWidget, text="Multiplet List:", grid=(row, 0))
        self.multipletPulldown = MultipletListPulldown(self.mainWidget, grid=(row, 1), project=self.project)

        row += 1
        Label(self.mainWidget, text="Scaling Factor:", grid=(row, 0))
        self.scalingEdit = LineEdit.LineEdit(self.mainWidget, grid=(row, 1), text="4")

        row += 1
        Label(self.mainWidget, text="Tolerance (Hz):", grid=(row, 0))
        self.toleranceEdit = LineEdit.LineEdit(self.mainWidget, grid=(row, 1),
                                               text="0.1")

        row += 1
        self.likelyPhiCheck = CheckBox.CheckBox(self.mainWidget, grid=(row, 0),
                                                text="Likely Phi Only", checked=True)

        row += 1
        Label(self.mainWidget, text="Restraint Table:", grid=(row, 0))
        self.restraintPulldown = RestraintTablePulldown(self.mainWidget, grid=(row, 1), project=self.project)

        row += 1
        self.ButtonFrame = Frame(parent=self.mainWidget, setLayout=True, grid=(row, 0), gridSpan=(1, 2))

        # Use keyword arguments to avoid parameter confusion
        self.okButton = Button(
                parent=self.ButtonFrame,
                text="Analyse Multiplets",
                callback=self._runAnalysis,
                grid=(0, 0)
                )
        self.applyButton = Button(
                parent=self.ButtonFrame,
                text="Create Restraints",
                callback=self._createRestraints,
                grid=(0, 3),
                enabled=False  # Start disabled; enable after analysis
                )
        self.closeButton = Button(
                parent=self.ButtonFrame,
                text="Close",
                callback=self.reject,
                grid=(0, 4)
                )

    def _validateInputs(self):
        try:
            float(self.scalingEdit.text())
            float(self.toleranceEdit.text())
            return True
        except ValueError:
            MessageDialog.showWarning("Invalid Input", "Scaling and Tolerance must be numbers")
            return False

    def _runAnalysis(self):
        if not self._validateInputs():
            return

        multipletListText = self.multipletPulldown.getText()
        if not multipletListText:
            MessageDialog.showWarning("No Selection", "Select a Multiplet List")
            return

        multipletList = self.project.getByPid(multipletListText)

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                try:
                    self._dataframe = self.analyze_multiplets(
                            multipletList,
                            scalingFactor=float(self.scalingEdit.text()),
                            tolerance=float(self.toleranceEdit.text()),
                            likelyPhiOnly=self.likelyPhiCheck.isChecked()
                            )
                    self.project.newDataTable(name="DihedralFromJ", data=self._dataframe)

                    MessageDialog.showInfo("Analysis Complete", f"Created {len(self._dataframe)} entries")
                    self.applyButton.setEnabled(True)
                    self.okButton.setEnabled(False)

                except Exception as e:
                    MessageDialog.showWarning("Error", str(e))

    def _createRestraints(self):
        if self._dataframe is None or self._dataframe.empty:
            MessageDialog.showWarning("No Data", "Run analysis first")
            return

        restraintTabletext = self.restraintPulldown.getText()
        if not restraintTabletext:
            MessageDialog.showWarning("No Selection", "Select a Restraint List")
            return
        restraintTable = self.project.getByPid(restraintTabletext)

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                try:
                    created = self.create_angle_restraints_from_dataframe(self._dataframe, restraintTable)
                    MessageDialog.information("Success", f"Created {len(created)} restraints")
                except Exception as e:
                    MessageDialog.showWarning("Error", str(e))



if __name__ == '__main__':
    # from ccpn.ui.gui.widgets.Application import TestApplication
    # app = TestApplication()
    popup = DihedralRestraintPopup()
    # popup.show()
    popup.exec_()
    # app.start()