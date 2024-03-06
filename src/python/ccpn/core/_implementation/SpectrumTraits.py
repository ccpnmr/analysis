"""
This file contains the Spectrum-related traits; to isolate them from the Spectrum class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-03-06 17:48:09 +0000 (Wed, March 06, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-01-18 10:28:48 +0000 (Tue, January 18, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.traits.CcpNmrJson import CcpNmrJson, jsonHandler
from ccpn.util.traits.CcpNmrTraits import Int, Float, Instance, Any, default, Bool
from ccpn.core.lib.CoreTraits import PeakPickerTrait, DataStoreTrait, DataSourceTrait

from ccpn.core.lib.DataStore import DataStore
# from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import DataSourceTrait
# from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerTrait

from ccpn.util.Logging import getLogger


class SpectrumTraits(CcpNmrJson):
    """Spectrum related traits
    """
    saveAllTraitsToJson = True
    classVersion = '1.0.0'  # for json saving

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

    def _storeToSpectrum(self):
        """Store the various traits to the spectrum internal data
        """
        if (spectrum := self.spectrum) is None:
            getLogger().warning(f'SpectrumTraits: undefined spectrum, cannot store values')
            return

        # Store the dataStore info
        if (dataStore := self.dataStore) is None:
            getLogger().warning(f'{self}: undefined dataStore: cannot store values')
        else:
            dataStore._saveInternal()

        # Store the peakPicker info
        if (peakPicker := self.peakPicker) is None:
            getLogger().warning(f'{self}: undefined peakPicker: cannot store values')
        else:
            peakPicker._storeAttributes()

    def _restoreFromSpectrum(self):
        """Restore the various traits from the spectrum internal data
        """
        from ccpn.core.lib.SpectrumLib import fetchPeakPicker

        if (spectrum := self.spectrum) is None:
            getLogger().warning(f'SpectrumTraits: undefined spectrum, cannot restore values')
            return

        # Restore the dataStore info
        dataStore = None
        try:
            dataStore = DataStore()._importFromSpectrum(self.spectrum)
        except (ValueError, RuntimeError) as es:
            getLogger().warning('Error restoring valid data store for %s (%s)' % (spectrum, es))
        finally:
            self.dataStore =  dataStore

        # Get a dataSource object
        dataSource = None
        try:
            dataSource = spectrum._getDataSource(dataStore)
        except (ValueError, RuntimeError) as es:
            getLogger().warning('Error restoring valid data source for %s (%s)' % (spectrum, es))
        finally:
            self.dataSource = dataSource

        # Get a peak picker
        try:
            peakPicker = spectrum._getPeakPicker()
        except (ValueError, RuntimeError) as es:
            # GWV: Log this in the debugger, as it might get lost and cause confusion
            getLogger().debug(f'restoring peakPicker raised error: {es}')
            getLogger().warning(f'Error restoring valid peak picker for {spectrum}')
            peakPicker = None
        except Exception as es:
            raise RuntimeError(f'While restoring Spectrum traits; {es}')
        finally:
            self.peakPicker = peakPicker
#end class

# Register for Json restoring
SpectrumTraits.register()
