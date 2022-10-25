"""
This module defines base classes for Series Analysis
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-10-24 15:07:24 +0100 (Mon, October 24, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


import warnings
import numpy as np
import pandas as pd
from collections import defaultdict, OrderedDict
from abc import ABC, abstractmethod
from copy import deepcopy
from pandas import Series, isnull
from lmfit import Model, Parameter
from lmfit.model import ModelResult, _align
from ccpn.core.DataTable import TableFrame
from ccpn.util.Logging import getLogger
from ccpn.util.OrderedSet import OrderedSet
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import SeriesFrameBC
from ccpn.framework.Application import getApplication, getProject
from ccpn.core.lib.CcpnSorting import stringSortKey

pd.set_option('display.max_columns', None)  # or 1\000
pd.set_option('display.max_rows', 50)  # or 1000

class FittingModelABC(ABC):

    ModelName       = 'ModelName'       # The Model name.
    Info            = ''                # A brief description of the fitting model.
    Description     = ''                # A simplified representation of the used equation(s).
    MaTex           = r''               # MaTex representation of the used equation(s). see https://matplotlib.org/3.5.0/tutorials/text/mathtext.html
    References      = ''                # A list of journal article references. E.g.: DOIs or title/authors/year/journal; web-pages.
    Minimiser       = None              # The fitting minimiser model object (initiated)
    FullDescription = f'{Info} \n {Description}\nSee References: {References}'
    PeakProperty    = sv._HEIGHT        # The peak property to fit. One of ['height', 'lineWidth', 'volume', 'ppmPosition']
    isEnabled       = True              # True to enable on the GUI and be selected/used

    def __init__(self, *args, **kwargs):

        self.application = getApplication()
        self.project = getProject()
        self._applyScaleMinMax = False
        self._applyStandardScaler = False
        self._modelArgumentNames = []
        self._rawDataHeaders = [] # strings of columnHeaders
        self.xSeriesStepHeader = sv.SERIES_STEP_X
        self.ySeriesStepHeader = sv.SERIES_STEP_Y
        self._ySeriesLabel = self.PeakProperty # this is only used in the Plot Y Axis label.

    @property
    def rawDataHeaders(self):
        """ The list of rawData Column headers to appear in output frames and tables."""
        return self._rawDataHeaders

    @property
    def modelArgumentNames(self):
        """ The list of parameters as str used in the minimiser fitting function or calculation models.
          These names will be used in the models and will appear as column headers in the output result frames. """
        if self.Minimiser:
            return self.Minimiser.getParamNames(self.Minimiser)
        return []

    @property
    def modelStatsNames(self):
        """ The list of statistical names used in the minimiser fitting function .
          These names will be used in the models and will appear as column headers in the output result frames. """
        if self.Minimiser:
            return self.Minimiser.getStatParamNames(self.Minimiser)
        return []

    @abstractmethod
    def fitSeries(self, inputData:TableFrame, *args, **kwargs) -> TableFrame:
        """
        :param inputData: a TableFrame containing all necessary data for the fitting calculations
        :return: an output TableFrame with fitted data
        """
        pass

    def getRawData(self, inputData:TableFrame, dimensionSeparator='F') -> TableFrame:
        """

        :param inputData: TableFrame.
        :param dimensionSeparator: String to separate DimensionColumns for ppmPosition or linewidth.
        :return: TableFrame
        Transform an inputData frame to a minimal Frame containing only the rawData and common assignment columns.
        Sorted by CollectionPid and series values.
        Note: this resulting table is NOT used as input for calculation or fitting models.
        """
        outputFrame = SeriesFrameBC()
        self._rawDataHeaders = OrderedSet()
        if self.PeakProperty in [sv._HEIGHT, sv._VOLUME]:
            inputData = inputData[inputData[sv.ISOTOPECODE] == inputData[sv.ISOTOPECODE].iloc[0]]
        commonHeaders = sv.MERGINGHEADERS
        grouppedByCollectionsId = inputData.groupby([sv.COLLECTIONID])
        for collectionId, groupDf in grouppedByCollectionsId:
            groupDf.sort_values([self.xSeriesStepHeader], inplace=True)
            seriesSteps = groupDf[self.xSeriesStepHeader]
            ## Build columns
            for ix, row in groupDf.iterrows():
                pid = row[sv.COLLECTIONPID]
                for commonHeader in commonHeaders:
                    outputFrame.loc[pid, commonHeader] = row[commonHeader]
                for xValue in seriesSteps.values:
                    if xValue == row[self.xSeriesStepHeader]:
                        valueHeader = f'{dimensionSeparator}{int(row[sv.DIMENSION])}_{xValue}'
                        if self.PeakProperty in [sv._HEIGHT, sv._VOLUME]:
                            valueHeader = f'{self.PeakProperty}_{xValue}'
                        outputFrame.loc[pid, valueHeader] = row[self.PeakProperty]
                        self._rawDataHeaders.add(valueHeader)
        self._rawDataHeaders = list(self._rawDataHeaders)
        outputFrame.columns = commonHeaders + self._rawDataHeaders
        outputFrame.set_index(sv.COLLECTIONPID, drop=False, inplace=True)

        return outputFrame


    @staticmethod
    def getFittingFunc(cls):
        """Get the Fitting Function used by the Minimiser """
        if cls.Minimiser is not None:
            return cls.Minimiser.FITTING_FUNC

    def scaleMinMax(self, data):
        return lf._scaleMinMaxData(data)


    def __str__(self):
        return f'<{self.__class__.__name__}: {self.ModelName}>'

    __repr__ = __str__


class CalculationModel(FittingModelABC):
    """
    Calculation model for Series Analysis
    """

    ModelName   = 'Calculation'     ## The Model name.
    Info        = 'the info'        ## A brief description of the fitting model.
    Description = 'Description'     ## A simplified representation of the used equation(s).
    MaTex       = r''               ## MaTex representation of the used equation(s). see https://matplotlib.org/3.5.0/tutorials/text/mathtext.html
    References  = 'References'      ## A list of journal article references that help to identify the employed calculation equations. E.g.: DOIs or title/authors/year/journal; web-pages.

    @abstractmethod
    def calculateValues(self, inputData: TableFrame) -> TableFrame:
        """
        Calculate the required values for an input SeriesTable.
        This method must be overridden in subclass'.
        Return one row for each collection pid. Index by collection pid
        :param inputData: InputFrame
        :return: outputFrame
        """
        raise RuntimeError('This method must be overridden in subclass')

    def fitSeries(self, inputData:TableFrame, *args, **kwargs) -> TableFrame:
        raise RuntimeError('This method cannot be used in this class. Use calculateValues instead ')


class MinimiserModel(Model):
    """
    The lower base class for the fitting minimisation routines.
    Based on the package LMFIT.
    Called for each row in the input SeriesDataTable.


    Parameters
    ----------
    independent_vars : :obj:`list` of :obj:`str`, optional
        Arguments to the model function that are independent variables
        default is ['x']).
    prefix : str, optional
        String to prepend to parameter names, needed to add two Models
        that have parameter names in common.
    nan_policy : {'raise', 'propagate', 'omit'}, optional
        How to handle NaN and missing values in data. See Notes below.
    **kwargs : optional
        Keyword arguments to pass to :class:`Model`.
    Notes
    -----
    1. `nan_policy` sets what to do when a NaN or missing value is seen in
    the data. Should be one of:
        - `'raise'` : raise a `ValueError` (default)
        - `'propagate'` : do nothing
        - `'omit'` : drop missing data

    ----- ccpn internal ----

     _defaultParams must be set.
        It is a dict containing as key the fitting func argument to be optimised (excluding x)
        and an initial default value. (Arbitrary at this stage or None. Initial values are calculated separately in the "guess" method).

        Also, these arguments as a string must be exactly as they are defined in the FITTING_FUNC arguments!
        Example fitFunc with args decay and amplitude:

            def expDecay(x, decay, amplitude):...
            defaultParams = {
                            'decay'    : 0.3,
                            'amplitude': 1
                            }
            (note x is not necessary to be defined here, it is part of the "independent_vars" set automatically)
        This because there is a clever signature inspection that sets on-the-fly args as class attributes,
        and they are used throughout the code.  <is an odd behaviour but too hard/dangerous to change!>
        defaultParams are also used to autogenerate Gui definitions in tables and widget entries.

    """
    FITTING_FUNC  = None
    MODELNAME     = 'Minimiser'
    method        = 'leastsq'
    label         = ''
    defaultParams = {} # N.B Very important. see docs above.


    def fit(self, data, params=None, weights=None, method='leastsq',
            iter_cb=None, scale_covar=True, verbose=False, fit_kws=None,
            nan_policy=None, calc_covar=True, max_nfev=None, **kwargs):
        """Fit the model to the data using the supplied Parameters.

        Parameters
        ----------
        data : array_like
            Array of data to be fit.
        params : Parameters, optional
            Parameters to use in fit (default is None).
        weights : array_like, optional
            Weights to use for the calculation of the fit residual
            (default is None). Must have the same size as `data`.
        method : str, optional
            Name of fitting method to use (default is `'leastsq'`).
        iter_cb : callable, optional
            Callback function to call at each iteration (default is None).
        scale_covar : bool, optional
            Whether to automatically scale the covariance matrix when
            calculating uncertainties (default is True).
        verbose : bool, optional
            Whether to print a message when a new parameter is added
            because of a hint (default is True).
        fit_kws : dict, optional
            Options to pass to the minimizer being used.
        nan_policy : {'raise', 'propagate', 'omit'}, optional
            What to do when encountering NaNs when fitting Model.
        calc_covar : bool, optional
            Whether to calculate the covariance matrix (default is True)
            for solvers other than `'leastsq'` and `'least_squares'`.
            Requires the ``numdifftools`` package to be installed.
        max_nfev : int or None, optional
            Maximum number of function evaluations (default is None). The
            default value depends on the fitting method.
        **kwargs : optional
            Arguments to pass to the model function, possibly overriding
            parameters.

        Returns
        -------
        ModelResult

        Notes
        -----
        1. if `params` is None, the values for all parameters are expected
        to be provided as keyword arguments. If `params` is given, and a
        keyword argument for a parameter value is also given, the keyword
        argument will be used.

        2. all non-parameter arguments for the model function, **including
        all the independent variables** will need to be passed in using
        keyword arguments.

        3. Parameters (however passed in), are copied on input, so the
        original Parameter objects are unchanged, and the updated values
        are in the returned `ModelResult`.

        Examples
        --------
        Take ``t`` to be the independent variable and data to be the curve
        we will fit. Use keyword arguments to set initial guesses:

        """

        if params is None:
            params = self.make_params(verbose=verbose)
        else:
            params = deepcopy(params)
        with warnings.catch_warnings():
            warnings.filterwarnings(action='ignore', category=RuntimeWarning)
            # If any kwargs match parameter names, override params.
            param_kwargs = set(kwargs.keys()) & set(self.param_names)
            for name in param_kwargs:
                p = kwargs[name]
                if isinstance(p, Parameter):
                    p.name = name  # allows N=Parameter(value=5) with implicit name
                    params[name] = deepcopy(p)
                else:
                    params[name].set(value=p)
                del kwargs[name]

            # All remaining kwargs should correspond to independent variables.
            for name in kwargs:
                if name not in self.independent_vars:
                    getLogger.warn(f"The keyword argument {name} does not " +
                                  "match any arguments of the model function. " +
                                  "It will be ignored.", UserWarning)

            # If any parameter is not initialized raise a more helpful error.
            missing_param = any(p not in params.keys() for p in self.param_names)
            blank_param = any((p.value is None and p.expr is None)
                              for p in params.values())
            if missing_param or blank_param:
                msg = ('Assign each parameter an initial value by passing '
                       'Parameters or keyword arguments to fit.\n')
                missing = [p for p in self.param_names if p not in params.keys()]
                blank = [name for name, p in params.items()
                         if p.value is None and p.expr is None]
                msg += f'Missing parameters: {str(missing)}\n'
                msg += f'Non initialized parameters: {str(blank)}'
                raise ValueError(msg)

            # Handle null/missing values.
            if nan_policy is not None:
                self.nan_policy = nan_policy

            mask = None
            if self.nan_policy == 'omit':
                mask = ~isnull(data)
                if mask is not None:
                    data = data[mask]
                if weights is not None:
                    weights = _align(weights, mask, data)

            # If independent_vars and data are alignable (pandas), align them,
            # and apply the mask from above if there is one.
            for var in self.independent_vars:
                if not np.isscalar(kwargs[var]):
                    kwargs[var] = _align(kwargs[var], mask, data)

            # Make sure `dtype` for data is always `float64` or `complex128`
            if np.isrealobj(data):
                data = np.asfarray(data)
            elif np.iscomplexobj(data):
                data = np.asarray(data, dtype='complex128')

            # Coerce `dtype` for independent variable(s) to `float64` or
            # `complex128` when the variable has one of the following types: list,
            # tuple, numpy.ndarray, or pandas.Series
            for var in self.independent_vars:
                var_data = kwargs[var]
                if isinstance(var_data, (list, tuple, np.ndarray, Series)):
                    if np.isrealobj(var_data):
                        kwargs[var] = np.asfarray(var_data)
                    elif np.iscomplexobj(var_data):
                        kwargs[var] = np.asarray(var_data, dtype='complex128')

            if fit_kws is None:
                fit_kws = {}

            result = MinimiserResult(self, params, method=method, iter_cb=iter_cb,
                                 scale_covar=scale_covar, fcn_kws=kwargs,
                                 nan_policy=self.nan_policy, calc_covar=calc_covar,
                                 max_nfev=max_nfev, **fit_kws)
            result.fit(data=data, weights=weights)
            result.components = self.components
            self.method = method
            if result.redchi is not None:
                result.r2 = lf.r2_func(redchi=result.redchi, y=data)
        return result

    def guess(self, data, x, **kws):
        pass

    @staticmethod
    def getParamNames(cls):
        """ get the list of parameters as str used in the fitting function  """
        return list(cls.defaultParams.keys())

    def getStatParamNames(self):
        """
        Get the common statistical ParamNames .
        :return: list
        """
        stats =  [sv.R2, sv.CHISQR, sv.REDCHI, sv.AIC, sv.BIC]
        return stats


class MinimiserResult(ModelResult):
    """Result from the Model fit.

       This has many attributes and methods for viewing and working with the
       results of a fit using Model. It inherits from Minimizer, so that it
       can be used to modify and re-run the fit for the Model.

       """

    def __init__(self, model, params, data=None, weights=None, scaleMinMax=False,
                 method=sv.LEASTSQ, fcn_args=None, fcn_kws=None,
                 iter_cb=None, scale_covar=True, nan_policy=sv.OMIT_MODE,
                 calc_covar=True, max_nfev=None, **fit_kws):
        """
        Parameters
        ----------
        model : Model
            Model to use.
        params : Parameters
            Parameters with initial values for model.
        data : array_like, optional
            Data to be modeled.
        weights : array_like, optional
            Weights to multiply ``(data-model)`` for fit residual.
        scaleMinMax: bool, True to scale data 0-1

        method : str, optional
            Name of minimization method to use (default is `'leastsq'`).
        fcn_args : sequence, optional
            Positional arguments to send to model function.
        fcn_dict : dict, optional
            Keyword arguments to send to model function.
        iter_cb : callable, optional
            Function to call on each iteration of fit.
        scale_covar : bool, optional
            Whether to scale covariance matrix for uncertainty evaluation.
        nan_policy : {'raise', 'propagate', 'omit'}, optional
            What to do when encountering NaNs when fitting Model.
        calc_covar : bool, optional
            Whether to calculate the covariance matrix (default is True)
            for solvers other than `'leastsq'` and `'least_squares'`.
            Requires the ``numdifftools`` package to be installed.
        max_nfev : int or None, optional
            Maximum number of function evaluations (default is None). The
            default value depends on the fitting method.
        **fit_kws : optional
            Keyword arguments to send to minimization routine.

        """
        self.r2 = None
        self.scaleMinMax = scaleMinMax

        super().__init__( model, params, data=data, weights=weights,
                 method=method, fcn_args=fcn_args, fcn_kws=fcn_kws,
                 iter_cb=iter_cb, scale_covar=scale_covar, nan_policy=nan_policy,
                 calc_covar=calc_covar, max_nfev=max_nfev, **fit_kws)

    def getStatisticalResult(self):
        """
        Get the common statistical results from the fit.
        :return: dict
        """
        dd = {}
        mappingNames = {sv.MINIMISER_METHOD :'method',
                       sv.R2                :'r2',
                       sv.CHISQR         : 'chisqr',
                       sv.REDCHI  : 'redchi',
                       sv.AIC            : 'aic',
                       sv.BIC          : 'bic',
                       }
        for nn, vv in mappingNames.items():
            dd[nn] = getattr(self, vv, None)
        return dd

    def getParametersResult(self):
        """
        Get the parameter results from the fit. E.g.: amplitude, decay and errors for a T1 fitting model
        :return: dict
        """
        dd = {}
        for paramName, paramObj in self.params.items():
            error = f'{paramName}{sv._ERR}'
            dd[paramName] = None
            dd[error] = None
            if paramObj is not None:
                dd.update({paramName:paramObj.value})
                dd[error] = paramObj.stderr
        return dd

    def getAllResultsAsDict(self):
        """
        :return: A dict with all minimiser results
        """
        outputDict = {}
        for key, value in self.getParametersResult().items():
            outputDict[key] = value
        for key, value in self.getStatisticalResult().items():
            outputDict[key] = value
        return outputDict

    def getAllResultsAsDataFrame(self):
        """
        :return: A dataFrame with all minimiser results
        """
        outputDict = self.getAllResultsAsDict()
        df = pd.DataFrame(outputDict, index=[0])
        return df

    def plot(self, datafmt='o', fitfmt='-', initfmt='--', showPlot=True, xlabel=None,
             ylabel=None, yerr=None, numpoints=None, fig=None, data_kws=None,
             fit_kws=None, init_kws=None, ax_res_kws=None, ax_fit_kws=None,
             fig_kws=None, show_init=False, parse_complex='abs', title=None):
        """Plot the fit results and residuals using matplotlib.

        The method will produce a matplotlib figure (if package available)
        with both results of the fit and the residuals plotted. If the fit
        model included weights, errorbars will also be plotted. To show
        the initial conditions for the fit, pass the argument
        ``show_init=True``.

        Parameters
        ----------
        datafmt : str, optional
            Matplotlib format string for data points.
        fitfmt : str, optional
            Matplotlib format string for fitted curve.
        initfmt : str, optional
            Matplotlib format string for initial conditions for the fit.
        xlabel : str, optional
            Matplotlib format string for labeling the x-axis.
        ylabel : str, optional
            Matplotlib format string for labeling the y-axis.
        yerr : numpy.ndarray, optional
            Array of uncertainties for data array.
        numpoints : int, optional
            If provided, the final and initial fit curves are evaluated
            not only at data points, but refined to contain `numpoints`
            points in total.
        fig : matplotlib.figure.Figure, optional
            The figure to plot on. The default is None, which means use
            the current pyplot figure or create one if there is none.
        data_kws : dict, optional
            Keyword arguments passed to the plot function for data points.
        fit_kws : dict, optional
            Keyword arguments passed to the plot function for fitted curve.
        init_kws : dict, optional
            Keyword arguments passed to the plot function for the initial
            conditions of the fit.
        ax_res_kws : dict, optional
            Keyword arguments for the axes for the residuals plot.
        ax_fit_kws : dict, optional
            Keyword arguments for the axes for the fit plot.
        fig_kws : dict, optional
            Keyword arguments for a new figure, if a new one is created.
        show_init : bool, optional
            Whether to show the initial conditions for the fit (default is
            False).
        parse_complex : {'abs', 'real', 'imag', 'angle'}, optional
            How to reduce complex data for plotting. Options are one of:
            `'abs'` (default), `'real'`, `'imag'`, or `'angle'`, which
            correspond to the NumPy functions with the same name.
        title : str, optional
            Matplotlib format string for figure title.

        Returns
        -------
        matplotlib.figure.Figure

        See Also
        --------
        ModelResult.plot_fit : Plot the fit results using matplotlib.
        ModelResult.plot_residuals : Plot the fit residuals using matplotlib.

        Notes
        -----
        The method combines `ModelResult.plot_fit` and
        `ModelResult.plot_residuals`.

        If `yerr` is specified or if the fit model included weights, then
        `matplotlib.axes.Axes.errorbar` is used to plot the data. If
        `yerr` is not specified and the fit includes weights, `yerr` set
        to ``1/self.weights``.

        If model returns complex data, `yerr` is treated the same way that
        weights are in this case.

        If `fig` is None then `matplotlib.pyplot.figure(**fig_kws)` is
        called, otherwise `fig_kws` is ignored.

        """
        from matplotlib import pyplot as plt
        if data_kws is None:
            data_kws = {}
        if fit_kws is None:
            fit_kws = {}
        if init_kws is None:
            init_kws = {}
        if ax_res_kws is None:
            ax_res_kws = {}
        if ax_fit_kws is None:
            ax_fit_kws = {}

        # make a square figure with side equal to the default figure's x-size
        figxsize = plt.rcParams['figure.figsize'][0]
        fig_kws_ = dict(figsize=(figxsize, figxsize))
        if fig_kws is not None:
            fig_kws_.update(fig_kws)

        if len(self.model.independent_vars) != 1:
            print('Fit can only be plotted if the model function has one '
                  'independent variable.')
            return False

        if not isinstance(fig, plt.Figure):
            fig = plt.figure(**fig_kws_)

        gs = plt.GridSpec(nrows=3, ncols=1, height_ratios=[1, 4, 1])
        ax_res = fig.add_subplot(gs[0], **ax_res_kws)
        ax_fit = fig.add_subplot(gs[1], sharex=ax_res, **ax_fit_kws)
        ax_table = fig.add_subplot(gs[2], **ax_fit_kws)

        self.plot_fit(ax=ax_fit, datafmt=datafmt, fitfmt=fitfmt, yerr=yerr,
                      initfmt=initfmt, xlabel=xlabel, ylabel=ylabel,
                      numpoints=numpoints, data_kws=data_kws,
                      fit_kws=fit_kws, init_kws=init_kws, ax_kws=ax_fit_kws,
                      show_init=show_init, parse_complex=parse_complex,
                      title=title)
        self.plot_residuals(ax=ax_res, datafmt=datafmt, yerr=yerr,
                            data_kws=data_kws, fit_kws=fit_kws,
                            ax_kws=ax_res_kws, parse_complex=parse_complex,
                            title=title)
        plt.setp(ax_res.get_xticklabels(), visible=False)
        ax_fit.set_title(self.model.label)
        # make a table with stats
        fig.patch.set_visible(False)
        ax_table.axis('off')
        ax_table.axis('tight')

        df = self.getAllResultsAsDataFrame()

        table = ax_table.table(cellText=df.values, colLabels=df.columns,  loc='center')
        table.auto_set_font_size(False) #or plots very tiny
        table.set_fontsize(5)
        fig.tight_layout()

        if showPlot:
            plt.show()
        return fig
