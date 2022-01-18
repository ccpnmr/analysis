"""
This file contains the Spectrum-related traits; to isolate them from the Spectrum class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-01-18 15:09:17 +0000 (Tue, January 18, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.traits.CcpNmrJson import CcpNmrJson, jsonHandler
from ccpn.util.traits.CcpNmrTraits import Int, Float, Instance, Any

from ccpn.core.lib.DataStore import DataStore, DataStoreTrait
from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import DataSourceTrait
from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerTrait
from ccpn.core.lib.SpectrumLib import SpectrumDimensionTrait


class SpectrumTraits(CcpNmrJson):
    """Spectrum related traits
    """
    saveAllTraitsToJson = True
    classVersion = 1.0  # for json saving

    # References to DataStore / DataSource instances for filePath manipulation and (binary) data reading;
    dataStore = DataStoreTrait(default_value=None).tag(
                               info="""
                               A DataStore instance encoding the path and dataFormat of the (binary) spectrum data.
                               None indicates no spectrum data file path has been defined"""
    )

    dataSource = DataSourceTrait(default_value=None).tag(
                                 info="""
                                 A SpectrumDataSource instance for reading (writing) of the (binary) spectrum data.
                                 None indicates no valid spectrum data file has been defined"""
    )

    peakPicker = PeakPickerTrait(default_value=None).tag(
                                  info="A PeakPicker instance"
    )

    def __init__(self, spectrum):
        super().__init__()
        self.spectrum = spectrum

    # @property
    # def _metadata
