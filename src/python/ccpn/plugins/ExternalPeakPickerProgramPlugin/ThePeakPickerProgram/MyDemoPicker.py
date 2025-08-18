#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notice

This program is only a demonstration used to showcase how an external program can be launched, communicate via files, and update a display in real time.
It is not:
	•	a general-purpose NMR data visualisation tool,
	•	a reliable or maintained application,
	•	an example of best practices for GUI or scientific programming, or
	•	a recommended approach for peak picking, data processing, or file watching.

All code is hard-coded for demonstration purposes and may lack error handling, flexibility, or performance optimisations.
It is not actively maintained, and functionality may break without warning.

If you need a production-ready NMR viewer or peak picker, please use specialised, well-maintained software.

"""

import sys, time, argparse
from pathlib import Path

import numpy as np
import pandas as pd
import nmrglue as ng

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5.QtCore import Qt, QFileSystemWatcher, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QLabel, QMessageBox, QPushButton, QRadioButton, QCheckBox
)

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(constrained_layout=True)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)

class PeakPickerUCSF(QMainWindow):
    def __init__(self, ucsf_path: Path, csv_path: Path):
        super().__init__()
        self.csv_path = csv_path
        self.data, (self.y_axis, self.x_axis), self.is_ppm = self._load_ucsf_2d(ucsf_path)

        # guard to suspend reload around internal writes
        self._reload_suspended_until = 0.0  # monotonic seconds

        # Window
        self.setWindowTitle("[DEMO] UCSF 2D Peak Picker")
        self.resize(1150, 760)

        # Central + canvas
        central = QWidget(self); self.setCentralWidget(central)
        vbox = QVBoxLayout(central)
        self.canvas = MplCanvas()
        self.toolbar = NavigationToolbar(self.canvas, self)
        vbox.addWidget(self.toolbar); vbox.addWidget(self.canvas)

        # Controls (grid layout)
        grid = QGridLayout(); vbox.addLayout(grid)

        # Row 1: Pick mode + label + show labels
        self.pick_radio = QRadioButton("Pick mode")
        self.pick_radio.setChecked(True)
        self.pick_radio.toggled.connect(self.toggle_picking)
        grid.addWidget(self.pick_radio, 0, 0)

        self.mode_label = QLabel("Mode: Picking — click on the spectrum to record peaks.")
        grid.addWidget(self.mode_label, 0, 1)

        self.show_labels_box = QCheckBox("Show Labels")
        self.show_labels_box.setChecked(True)
        self.show_labels_box.toggled.connect(self.toggle_labels_visibility)
        grid.addWidget(self.show_labels_box, 0, 2)

        # Row 2: Auto-reload + Reload button
        self.auto_reload_enabled = True
        self.auto_reload_box = QCheckBox("Auto-reload")
        self.auto_reload_box.setChecked(True)
        self.auto_reload_box.setToolTip("Reload picks from CSV when the file changes externally")
        self.auto_reload_box.toggled.connect(self._on_auto_reload_toggled)
        grid.addWidget(self.auto_reload_box, 1, 0)

        btn_reload = QPushButton("Reload")
        btn_reload.setToolTip("Force reload picks from CSV file")
        btn_reload.clicked.connect(self.force_reload)
        grid.addWidget(btn_reload, 1, 1)

        # Row 3: Clear All, Clear Last
        btn_all = QPushButton("Clear All")
        btn_all.clicked.connect(self.clear_all_picks)
        grid.addWidget(btn_all, 2, 0)

        btn_last = QPushButton("Clear Last")
        btn_last.clicked.connect(self.clear_last_pick)
        grid.addWidget(btn_last, 2, 1)

        # Row 4: Close
        # Row 4: Pick All, Close
        btn_pick_all = QPushButton("Pick All Peaks")
        btn_pick_all.setToolTip("Automatically pick peaks using nmrglue peak picking")
        btn_pick_all.clicked.connect(lambda: self.pick_all_peaks_nmrglue())
        grid.addWidget(btn_pick_all, 3, 0)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        grid.addWidget(btn_close, 3, 1)

        # Info label (below grid)
        vbox.addWidget(QLabel(f"Input Spectrum: {ucsf_path}"))
        vbox.addWidget(QLabel(f"Output CSV: {csv_path}"))

        # State
        self.pick_artists = []     # list of tuples (square,line,label)
        self.picking_enabled = True

        # Events
        self.cid_click = self.canvas.mpl_connect("button_press_event", self.on_click)

        # Init
        self._draw()
        self._ensure_csv_header()
        self._setup_csv_watcher()
        self.force_reload()


    # ---------------------- Load 2D UCSF ----------------------
    def _load_ucsf_2d(self, path: Path):
        if path.suffix.lower() != ".ucsf":
            raise RuntimeError("Only UCSF (.ucsf) files are supported.")
        dic, data = ng.sparky.read(str(path))
        data = np.asarray(data).astype(float)
        if data.ndim != 2:
            raise RuntimeError("This build supports 2D UCSF only.")

        # --- extract nuclei labels (robust across possible keys) ---
        def _nuc(d, key, default):
            v = d.get(key, {}) if isinstance(d.get(key), dict) else {}
            v = v.get("nucleus")
            if isinstance(v, (bytes, bytearray)): v = v.decode(errors="ignore")
            return (v or default).strip()

        self.nuc_f1 = _nuc(dic, "w1", "F1")  # F1 (y axis)
        self.nuc_f2 = _nuc(dic, "w2", "F2")  # F2 (x axis)

        # y (rows, F1), x (cols, F2)
        def axis_vals(dim):
            try:
                return np.asarray(ng.sparky.make_uc(dic, data, dim=dim).ppm_scale(), dtype=float)
            except Exception:
                return None

        y = axis_vals(0)
        x = axis_vals(1)
        is_ppm = (y is not None) and (x is not None)
        if y is None: y = np.arange(data.shape[0], dtype=float)
        if x is None: x = np.arange(data.shape[1], dtype=float)
        return data, (y, x), is_ppm


    # ---------------------- CSV (pandas) ----------------------
    def _ensure_csv_header(self):
        if (not self.csv_path.exists()) or self.csv_path.stat().st_size == 0:
            pd.DataFrame(columns=["x", "y", "height"]).to_csv(self.csv_path, index=False)

    def _append_row(self, x_val, y_val, height):
        # suspend reload briefly to avoid races
        self._reload_suspended_until = time.monotonic() + 0.6
        pd.DataFrame([[x_val, y_val, height]], columns=["x", "y", "height"])\
          .to_csv(self.csv_path, mode="a", index=False, header=False)

    # ---------------------- Watcher ----------------------
    def _setup_csv_watcher(self):
        self.watcher = QFileSystemWatcher([str(self.csv_path.parent)])
        if self.csv_path.exists():
            self.watcher.addPath(str(self.csv_path))
        def trigger():
            if self.auto_reload_enabled and time.monotonic() >= self._reload_suspended_until:
                QTimer.singleShot(200, self._reload_csv_and_rewatch)
        self.watcher.fileChanged.connect(lambda _: trigger())
        self.watcher.directoryChanged.connect(lambda _: trigger())

    def toggle_labels_visibility(self, checked):
        """Toggle visibility of coordinate labels without deleting them."""
        for pick in self.pick_artists:
            # pick is (square, cross, label)
            if len(pick) >= 3:
                label = pick[2]
                try:
                    label.set_visible(checked)
                except Exception:
                    pass
        self.canvas.draw_idle()

    def _on_auto_reload_toggled(self, checked: bool):
        self.auto_reload_enabled = bool(checked)
        if self.auto_reload_enabled and time.monotonic() >= self._reload_suspended_until:
            self._reload_csv_and_rewatch()

    def _reload_csv_and_rewatch(self, force: bool = False):
        if not force:
            if not self.auto_reload_enabled or time.monotonic() < self._reload_suspended_until:
                return
        if self.csv_path.exists() and str(self.csv_path) not in self.watcher.files():
            try: self.watcher.addPath(str(self.csv_path))
            except Exception: pass
        self.reload_picks_from_csv(force=force)

    def reload_picks_from_csv(self, force: bool = False):
        if not force and (not self.auto_reload_enabled or time.monotonic() < self._reload_suspended_until):
            return
        if not self.csv_path.exists() or self.csv_path.stat().st_size == 0:
            if force:
                self._clear_all_markers(); self.canvas.draw_idle()
            return
        try:
            df = pd.read_csv(self.csv_path)
        except Exception:
            return
        df = df.iloc[:, :3].apply(pd.to_numeric, errors="coerce").dropna()
        if df.empty and not force:
            return

        self._clear_all_markers()
        ax = self.canvas.ax
        for _, row in df.iterrows():
            x_val, y_val, h = float(row.iloc[0]), float(row.iloc[1]), float(row.iloc[2])
            sq, = ax.plot([x_val], [y_val], marker="s", markersize=10, mfc="none", mec="red")
            cr, = ax.plot([x_val], [y_val], marker="+", markersize=10, color="red")
            lbl = ax.annotate(f"({x_val:.3f}, {y_val:.3f}, {h:.2f})",
                              (x_val, y_val), xytext=(5, 5), textcoords="offset points")
            self.pick_artists.append((sq, cr, lbl))
            lbl.set_visible(self.show_labels_box.isChecked())
        self.canvas.draw_idle()

    def force_reload(self):
        self._reload_csv_and_rewatch(force=True)

    # ---------------------- Plot ----------------------
    def _draw(self):
        ax = self.canvas.ax; ax.clear()
        y_axis, x_axis = self.y_axis, self.x_axis
        std = float(np.nanstd(self.data))
        if not np.isfinite(std) or std <= 0: std = 1.0
        pos_levels = [3*std, 5*std, 8*std, 12*std, 20*std]
        neg_levels = sorted([-lv for lv in pos_levels])
        X, Y = np.meshgrid(x_axis, y_axis)
        try:
            ax.contour(X, Y, self.data, levels=pos_levels)
            ax.contour(X, Y, self.data, levels=neg_levels, linestyles='dashed')
        except Exception:
            ax.imshow(self.data,
                      extent=[x_axis.min(), x_axis.max(), y_axis.min(), y_axis.max()],
                      origin='lower', aspect='auto')
        ax.set_xlabel(f"{self.nuc_f2} (ppm)" if self.is_ppm else f"{self.nuc_f2}")
        ax.set_ylabel(f"{self.nuc_f1} (ppm)" if self.is_ppm else f"{self.nuc_f1}")
        ax.yaxis.tick_right()  # Move ticks to the right
        ax.yaxis.set_label_position("right")  # Move label to the right
        if self.is_ppm:
            ax.set_xlim(x_axis.max(), x_axis.min())  # F2 high ppm left → low ppm right
            ax.set_ylim(y_axis.max(), y_axis.min())  # F1 high ppm bottom → low ppm top
        self.canvas.draw_idle()

    # ---------------------- Manual picking ----------------------
    def toggle_picking(self, checked: bool):
        self.picking_enabled = bool(checked)
        self.canvas.setCursor(Qt.CrossCursor if self.picking_enabled else Qt.ArrowCursor)
        self.mode_label.setText(
            "Mode: Picking — click on the spectrum to record peaks."
            if self.picking_enabled else
            "Mode: Viewing — turn on 'Pick mode' to pick peaks."
        )

    def on_click(self, event):
        if not self.picking_enabled or event.inaxes != self.canvas.ax: return
        ix = int(np.argmin(np.abs(self.x_axis - event.xdata)))
        iy = int(np.argmin(np.abs(self.y_axis - event.ydata)))
        x_val, y_val, h = float(self.x_axis[ix]), float(self.y_axis[iy]), float(self.data[iy, ix])
        sq, = self.canvas.ax.plot([x_val], [y_val], marker="s", markersize=10, mfc="none", mec="red")
        cr, = self.canvas.ax.plot([x_val], [y_val], marker="+", markersize=10, color="red")
        lbl = self.canvas.ax.annotate(f"({x_val:.3f}, {y_val:.3f}, {h:.2f})",
                                      (x_val, y_val), xytext=(5, 5), textcoords="offset points")
        self.pick_artists.append((sq, cr, lbl)); self.canvas.draw_idle()
        self._append_row(x_val, y_val, h)
        lbl.set_visible(self.show_labels_box.isChecked())

    # ---------------------- Clear / markers ----------------------
    def _clear_all_markers(self):
        while self.pick_artists:
            for a in self.pick_artists.pop():
                try: a.remove()
                except Exception: pass
        self.canvas.draw_idle()

    def clear_last_pick(self):
        """Remove last pick from plot and drop last row from CSV."""
        if self.pick_artists:
            for a in self.pick_artists.pop():
                try: a.remove()
                except Exception: pass
            self.canvas.draw_idle()
        if self.csv_path.exists() and self.csv_path.stat().st_size > 0:
            try:
                self._reload_suspended_until = time.monotonic() + 0.6
                df = pd.read_csv(self.csv_path)
                if not df.empty:
                    df = df.iloc[:-1]
                    df.to_csv(self.csv_path, index=False)
            except Exception as e:
                QMessageBox.warning(self, "CSV Error", f"Could not remove last row: {e}")

    def clear_all_picks(self):
        """Remove all picks from plot and clear the CSV (keep header)."""
        self._clear_all_markers()
        try:
            self._reload_suspended_until = time.monotonic() + 0.6
            pd.DataFrame(columns=["x", "y", "height"]).to_csv(self.csv_path, index=False)
        except Exception as e:
            QMessageBox.warning(self, "CSV Error", f"Could not clear CSV: {e}")

    # ---------------------- Auto pick all (nmrglue) ----------------------
    def pick_all_peaks_nmrglue(self, pthres=None, nthres=None, cluster=True):
        """
        Use nmrglue peak picking to detect 2D peaks, dump full CSV, then clean+reload.

        pthres : float or None  Positive threshold (defaults to ~5*std if None)
        nthres : float or None  Negative threshold (defaults to -pthres if None)
        cluster: bool           Cluster voxels into single peaks
        """
        d = self.data
        sig = float(np.nanstd(d));  sig = sig if np.isfinite(sig) and sig > 0 else 1.0
        if pthres is None: pthres = 5.0 * sig
        if nthres is None: nthres = -float(pthres)

        # Try to use nmrglue peak picker
        locations = []; amps = []
        try:
            try:
                from nmrglue.analysis import peakpick as ng_pp
                picker = getattr(ng_pp, "pick", ng_pp)
            except Exception:
                from nmrglue import peakpick as picker
            locs, _cids, _scales, amps = picker(data=d, pthres=pthres, nthres=nthres, cluster=cluster, table=False)
            # locs are nD points (… , iy, ix)
            for loc in locs:
                iy, ix = int(loc[-2]), int(loc[-1])
                locations.append((iy, ix))
        except Exception:
            # Fallback: naive neighborhood max
            for iy in range(1, d.shape[0]-1):
                for ix in range(1, d.shape[1]-1):
                    val = d[iy, ix]
                    if val > pthres and val == np.max(d[iy-1:iy+2, ix-1:ix+2]):
                        locations.append((iy, ix)); amps.append(val)

        # Build DataFrame in physical axes (x,y,height)
        xs, ys, hs = [], [], []
        for (iy, ix) in locations:
            if 0 <= iy < len(self.y_axis) and 0 <= ix < len(self.x_axis):
                xs.append(float(self.x_axis[ix]))
                ys.append(float(self.y_axis[iy]))
                hs.append(float(d[iy, ix]))
        df = pd.DataFrame({"x": xs, "y": ys, "height": hs})

        # Overwrite CSV with the DF, then clean markers and force reload
        try:
            self._reload_suspended_until = time.monotonic() + 0.8
            df.to_csv(self.csv_path, index=False)
        except Exception as e:
            QMessageBox.warning(self, "CSV Error", f"Could not write peaks CSV: {e}")
            return
        self._clear_all_markers()
        self.force_reload()

def main():
    p = argparse.ArgumentParser(description="UCSF 2D Peak Picker → CSV ")
    p.add_argument("ucsf", help="Path to 2D UCSF (.ucsf) file")
    p.add_argument("csv", help="Output CSV file path")
    a = p.parse_args()
    app = QApplication(sys.argv)
    try:
        win = PeakPickerUCSF(Path(a.ucsf), Path(a.csv))
    except Exception as e:
        QMessageBox.critical(None, "Load Error", str(e)); sys.exit(2)
    win.show(); sys.exit(app.exec_())

if __name__ == "__main__":
    main()