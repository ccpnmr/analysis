/*
======================COPYRIGHT/LICENSE START==========================

npy_peak.c: Part of the CcpNmr Analysis program

Copyright (C) 2011 Wayne Boucher and Tim Stevens (University of Cambridge)

=======================================================================

The CCPN license can be found in ../../../license/CCPN.license.

======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)

- email: ccpn@bioc.cam.ac.uk

- contact the authors: wb104@bioc.cam.ac.uk, tjs23@cam.ac.uk
=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
R. Fogh, J. Ionides, E. Ulrich, W. Boucher, W. Vranken, J.P. Linge, M.
Habeck, W. Rieping, T.N. Bhat, J. Westbrook, K. Henrick, G. Gilliland,
H. Berman, J. Thornton, M. Nilges, J. Markley and E. Laue (2002). The
CCPN project: An interim report on a data model for the NMR community
(Progress report). Nature Struct. Biol. 9, 416-418.

Wim F. Vranken, Wayne Boucher, Tim J. Stevens, Rasmus
H. Fogh, Anne Pajon, Miguel Llinas, Eldon L. Ulrich, John L. Markley, John
Ionides and Ernest D. Laue (2005). The CCPN Data Model for NMR Spectroscopy:
Development of a Software Pipeline. Proteins 59, 687 - 696.

===========================REFERENCE END===============================

*/
#include <math.h>

#include "Python.h"

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION  // so that warnings avoided
#include "arrayobject.h"

#include "npy_defns.h"
#include "nonlinear_model.h"

#define  MAX_NDIM  10

#define GAUSSIAN_METHOD  0
#define LORENTZIAN_METHOD  1
//#define PARABOLIC_METHOD  2

#define LARGE_NUMBER 1.0e20

typedef struct _FitPeak
{
    int ndim;
    int npeaks;
    int *region_offset;
    int *region_end;
    int *cumul_region;
    int method;
}   FitPeak;

static PyObject *ErrorObject;   /* locally-raised exception */

static float get_value_at_point(PyArrayObject *data_array, npy_intp *point)
{
    int i, ndim = PyArray_NDIM(data_array);
    npy_intp reversed_point[MAX_NDIM];
    for (i = 0; i < ndim; i++)
        reversed_point[i] = point[ndim-1-i];

    //return *((float *) PyArray_GetPtr(data_array, point));
    return *((float *) PyArray_GetPtr(data_array, reversed_point));
}

static CcpnBool point_within_peak_buffer(int ndim, npy_intp *point, PyObject *peak_obj, long *buffer)
{
    int i, d, p;
    double posn;

    for (i = 0; i < ndim; i++)
    {
        posn = PyFloat_AsDouble(PyTuple_GetItem(peak_obj, i));
        p = NEAREST_INTEGER(posn);

        d = ABS(point[i] - p);
        if (d > buffer[i])
            return CCPN_FALSE;
    }

    return CCPN_TRUE;
}

static float fit_position_parabolic(float vm, float v, float vp)
{
    float c, d;
    CcpnBool is_positive;

    if (v > 0)
        is_positive = CCPN_TRUE;
    else
        is_positive = CCPN_FALSE;

    d = 0.5 * ABS(2*v - vm - vp);

    if (d > 1.0e-4)
    {
        c = 0.25 * ABS(vp-vm) / d;
        c = MIN(c, 0.49999);

        if (is_positive)
        {
            if (vp < vm)
                c = -c;
        }
        else
        {
            if (vp > vm)
                c = -c;
        }
    }
    else
    {
        c = 0;
    }

    return c;
}

static CcpnBool fit_position_x(float vm, float v, float vp, float *peakPos, float *height, float *lineFit)
{
    float a, b, c, x, halfX;
    CcpnBool is_positive;

    c = v;
    a = 0.5*(vm+vp-2.0*v);

    if (ABS(a) > 1e-6)
    {
        b = vp-0.5*(vp+vm);

        x = -b / (2.0*a);
        *peakPos = x;
        *height = a*x*x+b*x+c;
        halfX = (sqrt(b*b-4.0*a*(c-0.5*(*height))) - b) / (2.0*a);
        *lineFit = 2.0*ABS(x - halfX);
    }
    else
    {
        *peakPos = 0.0;
        *height = v;
        *lineFit = 0.0;

        return CCPN_ERROR;
    }

    return CCPN_OK;
}

static CcpnBool check_buffer(PyArrayObject *data_array,
                             PyObject *peak_list, long *buffer,
                             float value, npy_intp *point)
{
    int i, ndim = PyArray_NDIM(data_array);
    PyObject *point_obj;

    /* check that not within buffer */
    /* could do this first if implement efficient way of doing so */

    for (i = 0; i < PyList_Size(peak_list); i++)
    {
        point_obj = PyTuple_GetItem(PyList_GetItem(peak_list, i), 0);
        if (point_within_peak_buffer(ndim, point, point_obj, buffer))
            return CCPN_FALSE;
    }

    return CCPN_TRUE;
}

static PyObject *peak_volume(PyArrayObject *data_array, float value, npy_intp *point)
{
    float volume;

    return PyFloat_FromDouble(volume);
}

static CcpnStatus new_peak(PyArrayObject *data_array, PyObject *peak_list,
                           float value, npy_intp *point, int *points, char *error_msg)
{
    long i, ndim = PyArray_NDIM(data_array);
    npy_intp pnt[MAX_NDIM];
    float posn, vm, vp;
    PyObject *peak_obj, *point_obj;

    peak_obj = PyTuple_New(2);  /* point, height */
    if (!peak_obj)
        RETURN_ERROR_MSG("allocating peak memory");

    point_obj = PyTuple_New(ndim);
    if (!point_obj)
        RETURN_ERROR_MSG("allocating peak point memory");

    PyTuple_SetItem(peak_obj, 0, point_obj);
    PyTuple_SetItem(peak_obj, 1, PyFloat_FromDouble((double) value));

    for (i = 0; i < ndim; i++)
        PyTuple_SetItem(point_obj, i, PyLong_FromLong((long) point[i]));

    if (PyList_Append(peak_list, peak_obj))
        RETURN_ERROR_MSG("appending peak data to peak list");
    Py_DECREF(peak_obj);

    return CCPN_OK;
}

/* TBD: ignores aliasing so does not work correctly on boundaries */
static CcpnBool check_nonadjacent_points(PyArrayObject *data_array,
        CcpnBool find_maximum, long *buffer, float v, npy_intp *point,
        int *points, int npoints, int *cumulative)
{
    int i, n, zero_index, ndim = PyArray_NDIM(data_array);
    npy_intp p[MAX_NDIM];
    CcpnBool do_point;
    float v2;

    zero_index = 1;
    for (i = 0; i < ndim; i++)
        zero_index *= 3;
    zero_index = (zero_index - 1) / 2;

    /* check that local extremum */

    // npoints is now the number of adjacent points to any in the array
    // i.e. 3d is 27, so will only check these elements offset from the current, ignoring the middle
    // this is all the elements in the encompassing cube

    do_point = CCPN_TRUE;
    for (n = 0; n < npoints; n++)
    {
        if (n == zero_index) /* this is the central point */
            continue;

        ARRAY_OF_INDEX(p, n, cumulative, ndim);

        for (i = 0; i < ndim; i++)
        {
            // can't test points on the border
            if ((point[i] == 0) || (point[i] == points[i]-1))
                return CCPN_FALSE;

            /* would have been more efficient to do this before this function called... */
            p[i] += point[i] - 1;
            /* p initially goes 0, 1, 2 so extra -1 makes it -1, 0, 1 */

            if ((p[i] < 0) || (p[i] >= points[i]))
                return CCPN_FALSE;
        }

        //printf("              against: %i => %i, %i, %i\n", n, p[0], p[1], p[2]);

        v2 = get_value_at_point(data_array, p);

        if (find_maximum)
        {
            if (v2 > v)
                return CCPN_FALSE;
        }
        else
        {
            if (v2 < v)
                return CCPN_FALSE;
        }
    }

    return CCPN_TRUE;
}

/* TBD: ignores aliasing so does not work correctly on boundaries */
static CcpnBool check_adjacent_points(PyArrayObject *data_array, CcpnBool find_maximum,
                                      long *buffer, float v, npy_intp *point, int *points)
{
    int i, ndim = PyArray_NDIM(data_array);
    npy_intp pnt[MAX_NDIM];
    float v2;

    /* check that local extremum */

    // only check the adjacent elements in the directions of the axes
    COPY_VECTOR(pnt, point, ndim);
    for (i = 0; i < ndim; i++)
    {
        if (point[i] > 0)
        {
            pnt[i] = point[i] - 1;
            v2 = get_value_at_point(data_array, pnt);

            if (find_maximum)
            {
                if (v2 > v)
                    return CCPN_FALSE;
            }
            else
            {
                if (v2 < v)
                    return CCPN_FALSE;
            }
        }

        if (point[i] < (points[i] - 1))
        {
            pnt[i] = point[i] + 1;
            v2 = get_value_at_point(data_array, pnt);

            if (find_maximum)
            {
                if (v2 > v)
                    return CCPN_FALSE;
            }
            else
            {
                if (v2 < v)
                    return CCPN_FALSE;
            }
        }

        pnt[i] = point[i];
    }

    return CCPN_TRUE;
}

static CcpnBool drops_in_direction(PyArrayObject *data_array, CcpnBool find_maximum,
                                   float drop, float v, npy_intp *point, int *points, int dim, int dirn)
{
    int i, i_start, i_end, i_step, ndim = PyArray_NDIM(data_array);
    float v_prev = v, v_this;
    npy_intp q[MAX_NDIM];

    if (dirn == 1)
    {
        i_start = point[dim] + 1;
        i_end = points[dim];
        i_step = 1;
    }
    else
    {
        i_start = point[dim] - 1;
        i_end = -1;
        i_step = -1;
    }

    COPY_VECTOR(q, point, ndim);

    for (i = i_start; i != i_end; i += i_step)
    {
        q[dim] = i;
        v_this = get_value_at_point(data_array, q);

        if (find_maximum)
        {
            if (v_this > v_prev)
                return CCPN_FALSE;
            else if ((v-v_this) >= drop)
                return CCPN_TRUE;
        }
        else
        {
            if (v_this < v_prev)
                return CCPN_FALSE;
            else if ((v_this-v) >= drop)
                return CCPN_TRUE;
        }

        v_prev = v_this;
    }

    return CCPN_TRUE;
}

static CcpnBool check_drop(PyArrayObject *data_array, CcpnBool find_maximum,
                           float drop_factor, float v, npy_intp *point, int *points)
{
    int i, ndim = PyArray_NDIM(data_array);
    float drop = drop_factor * ABS(v);

    if (drop_factor <= 0)
        return CCPN_TRUE;

    for (i = 0; i < ndim; i++)
    {
        if (!drops_in_direction(data_array, find_maximum, drop, v, point, points, i, 1))
            return CCPN_FALSE;

        if (!drops_in_direction(data_array, find_maximum, drop, v, point, points, i, -1))
            return CCPN_FALSE;
    }

    return CCPN_TRUE;
}

static float half_max_position(PyArrayObject *data_array, CcpnBool find_maximum,
                               float v, npy_intp *point, int *points, int dim, int dirn)
{
    int i, i_start, i_end, i_step, ndim = PyArray_NDIM(data_array);
    float v_half = 0.5 * v, v_prev = v, v_this, half_max;
    npy_intp q[MAX_NDIM];

    if (dirn == 1)
    {
        i_start = point[dim] + 1;
        i_end = points[dim];
        i_step = 1;
    }
    else
    {
        i_start = point[dim] - 1;
        i_end = -1;
        i_step = -1;
    }

    COPY_VECTOR(q, point, ndim);

    for (i = i_start; i != i_end; i += i_step)
    {
        q[dim] = (i + points[dim]) % points[dim];
        v_this = get_value_at_point(data_array, q);

        if (find_maximum)
        {
            if (v_this < v_half)
                return i - i_step*(v_half-v_this)/(v_prev-v_this);
        }
        else
        {
            if (v_this > v_half)
                return i - i_step*(v_half-v_this)/(v_prev-v_this);
        }

        v_prev = v_this;
    }

    if (dirn == 1)
        return points[dim] - 1.0;
    else
        return 1.0;
}

static float half_max_linewidth(PyArrayObject *data_array, CcpnBool have_maximum,
                                float v, npy_intp *point, int *points, int dim)
{
    float linewidth, a, b;

    a = half_max_position(data_array, have_maximum, v, point, points, dim, 1);
    b = half_max_position(data_array, have_maximum, v, point, points, dim, -1);

    linewidth = a - b;

    return linewidth;
}

static CcpnBool fitParabolicToNDim(PyArrayObject *data_array,
                                    float *v, npy_intp *point, int *points,
                                    float *peakFit, float *lineWidth, int dim)
{
    int ndim = PyArray_NDIM(data_array);
    npy_intp pnt[MAX_NDIM];
    float vl, vr, vm;
    float height, lineFit, peak;
    CcpnBool status;

    /* check that local extremum */

    // only check the adjacent elements in the directions of the axes
    COPY_VECTOR(pnt, point, ndim);

    if ((point[dim] > 0) && (point[dim] < (points[dim] - 1)))
    {
        pnt[dim] = point[dim];
        vm = get_value_at_point(data_array, pnt);

        pnt[dim] = point[dim] - 1;
        vl = get_value_at_point(data_array, pnt);

        pnt[dim] = point[dim] + 1;
        vr = get_value_at_point(data_array, pnt);

//        *v = fit_position_parabolic(vl, vm, vr);
        status = fit_position_x(vl, vm, vr, &peak, &height, &lineFit)+point[dim];
        if (status == CCPN_OK)
            *peakFit = peak;
        else
            *peakFit = point[dim];

        *v = height;
        *lineWidth = lineFit;

        return CCPN_OK;
    }

    return CCPN_ERROR;
}

static CcpnBool check_dim_linewidth(PyArrayObject *data_array, CcpnBool have_maximum,
                                    float min_linewidth, float v, npy_intp *point, int *points, int dim)
{
    float linewidth = half_max_linewidth(data_array, have_maximum, v, point, points, dim);

    if (linewidth < min_linewidth)
        return CCPN_FALSE;

    return CCPN_TRUE;
}

static CcpnBool check_linewidth(PyArrayObject *data_array, CcpnBool find_maximum,
                                float *min_linewidth, float v, npy_intp *point, int *points)
{
    int i, ndim = PyArray_NDIM(data_array);

    for (i = 0; i < ndim; i++)
    {
        if (min_linewidth[i] <= 0)
            continue;

        if (!check_dim_linewidth(data_array, find_maximum, min_linewidth[i], v, point, points, i))
            return CCPN_FALSE;
    }

    return CCPN_TRUE;
}

static CcpnStatus find_peaks(PyArrayObject *data_array,
                             CcpnBool have_low, CcpnBool have_high, float low, float high,
                             long *buffer, CcpnBool nonadjacent, float drop_factor,
                             float *min_linewidth, PyObject *peak_list,
                             PyObject *excluded_regions_obj, PyObject *diagonal_exclusion_dims_obj,
                             PyObject *diagonal_exclusion_transform_obj, char *error_msg)
{
    int i, j, k, npoints, nadj_points, ndim, dim1, dim2;
    int cum_points[MAX_NDIM], cumulative[MAX_NDIM], points[MAX_NDIM];
    npy_intp point[MAX_NDIM];
    float v, a1, a2, b12, d, delta;
    CcpnBool find_maximum, ok_extreme, ok_drop, ok_linewidth, ok_buffer;
    PyArrayObject *excluded_regions_array, *diagonal_exclusion_dims_array, *diagonal_exclusion_transform_array;

    ndim = PyArray_NDIM(data_array);

    if (!have_low && !have_high)
        return CCPN_OK;

    if (nonadjacent)
    {
        nadj_points = 1;
        for (i = 0; i < ndim; i++)
        {
            cumulative[i] = nadj_points;
            nadj_points *= 3;
        }
        //printf("nadj_points %i\n"nadj_points);
    }

    npoints = 1;
    for (i = 0; i < ndim; i++)
    {
        cum_points[i] = npoints;
        points[i] = PyArray_DIM(data_array, ndim-1-i);
        npoints *= points[i];

        //printf("%i, %i, %i\n", i, points[i], cum_points[i]);
    }

    // iterate over all points in the dataArray
    //printf("num of points: %i\n", npoints);
    for (i = 0; i < npoints; i++)
    {

        // get the index of the point in the array
        ARRAY_OF_INDEX(point, i, cum_points, ndim);

        for (j = 0; j < PyList_Size(diagonal_exclusion_dims_obj); j++)
        {
            diagonal_exclusion_dims_array = (PyArrayObject *) PyList_GetItem(diagonal_exclusion_dims_obj, j);
            diagonal_exclusion_transform_array = (PyArrayObject *) PyList_GetItem(diagonal_exclusion_transform_obj, j);
            dim1 = *((int *) PyArray_GETPTR1(diagonal_exclusion_dims_array, 0));
            dim2 = *((int *) PyArray_GETPTR1(diagonal_exclusion_dims_array, 1));
            a1 = *((float *) PyArray_GETPTR1(diagonal_exclusion_transform_array, 0));
            a2 = *((float *) PyArray_GETPTR1(diagonal_exclusion_transform_array, 1));
            b12 = *((float *) PyArray_GETPTR1(diagonal_exclusion_transform_array, 2));
            d = *((float *) PyArray_GETPTR1(diagonal_exclusion_transform_array, 3));

            delta = a1*point[dim1] - a2*point[dim2] + b12;
            if (ABS(delta) < d)
                break;
        }

        if (j < PyList_Size(diagonal_exclusion_dims_obj))
            continue; /* point is in some excluded diagonal */

        for (j = 0; j < PyList_Size(excluded_regions_obj); j++)
        {
            excluded_regions_array = (PyArrayObject *) PyList_GetItem(excluded_regions_obj, j);

            for (k = 0; k < ndim; k++)
            {
                a1 = *((float *) PyArray_GETPTR2(excluded_regions_array, 0, k));
                a2 = *((float *) PyArray_GETPTR2(excluded_regions_array, 1, k));
                if ((point[k] < a1) ||
                        (point[k] > a2))
                    break; /* point is not in excluded region in this dim */
            }

            if (k == ndim)
                break; /* point is in this excluded region */
        }

        if (j < PyList_Size(excluded_regions_obj))
            continue; /* point is in some excluded region */

        v = get_value_at_point(data_array, point);
        //printf("i = %d, v = %f, high = %f\n", i, v, high);

        if (have_high && (v >= high))
            find_maximum = CCPN_TRUE;
        else if (have_low && (v <= low))
            find_maximum = CCPN_FALSE;
        else
            continue;

        //printf("i = %d, nonadjacent = %d\n", i, nonadjacent);
        if (nonadjacent)
            ok_extreme = check_nonadjacent_points(data_array, find_maximum,
                                                  buffer, v, point, points, nadj_points, cumulative);
        else
            ok_extreme = check_adjacent_points(data_array, find_maximum,
                                               buffer, v, point, points);

        if (!ok_extreme)
            continue;

        ok_drop = check_drop(data_array, find_maximum, drop_factor, v, point, points);

        if (!ok_drop)
            continue;

        ok_linewidth = check_linewidth(data_array, find_maximum,
                                       min_linewidth, v, point, points);

        if (!ok_linewidth)
            continue;

        ok_buffer = check_buffer(data_array, peak_list, buffer, v, point);

        if (!ok_buffer)
            continue;

        CHECK_STATUS(new_peak(data_array, peak_list, v, point, points, error_msg));
        //printf(">>>>> new point...");
        //printf("     array_of_index: %i - %i, %i, %i\n", i, point[0], point[1], point[2]);

    }

    return CCPN_OK;
}

static float gaussian(int ndim, int *x, float *a, float *dy_da)
{
    float h = a[0], *position = a+1, *linewidth = a+1+ndim;
    float *dy_dh, *dy_dp, *dy_dl;
    float lw, dx, y = h;
    int i;

    if (dy_da)
    {
        dy_dh = dy_da;
        dy_dp = dy_da+1;
        dy_dl = dy_da+1+ndim;
    }

    for (i = 0; i < ndim; i++)
    {
        dx = x[i] - position[i];
        lw = linewidth[i];
        y *= exp(-4*log(2)*dx*dx/(lw*lw));
        if (dy_da)
        {
            dy_dp[i] = 8*log(2)*dx/(lw*lw);
            dy_dl[i] = 8*log(2)*dx*dx/(lw*lw*lw);
        }
    }

    if (dy_da)
    {
        *dy_dh = y / h;
        SCALE_VECTOR(dy_dp, dy_dp, y, ndim);
        SCALE_VECTOR(dy_dl, dy_dl, y, ndim);
    }

    return y;
}

static float lorentzian(int ndim, int *x, float *a, float *dy_da)
{
    float h = a[0], *position = a+1, *linewidth = a+1+ndim;
    float *dy_dh, *dy_dp, *dy_dl;
    float lw, dx, d, y = h;
    int i;

    if (dy_da)
    {
        dy_dh = dy_da;
        dy_dp = dy_da+1;
        dy_dl = dy_da+1+ndim;
    }

    for (i = 0; i < ndim; i++)
    {
        dx = x[i] - position[i];
        lw = linewidth[i];
        d = lw*lw+4*dx*dx;
        y *= lw*lw/d;
        dy_dp[i] = 8*dx/d;
        dy_dl[i] = 8*dx*dx/(lw*d);
    }

    if (dy_da)
    {
        *dy_dh = y / h;
        SCALE_VECTOR(dy_dp, dy_dp, y, ndim);
        SCALE_VECTOR(dy_dl, dy_dl, y, ndim);
    }

    return y;
}

static void _fitting_func(float xind, float *a, float *y_fit, float *dy_da, void *user_data)
{
    FitPeak *fitPeak = (FitPeak *) user_data;
    int ndim = fitPeak->ndim;
    int npeaks = fitPeak->npeaks;
    int *region_offset = fitPeak->region_offset;
    int *region_end = fitPeak->region_end;
    int *cumul_region = fitPeak->cumul_region;
    int method = fitPeak->method;
    int ind = NEAREST_INTEGER(xind);
    int nparams_per_peak = 1 + 2*ndim;
    int i, j, x[MAX_NDIM];
    float *position = a+1;

    ARRAY_OF_INDEX(x, ind, cumul_region, ndim);
    ADD_VECTORS(x, x, region_offset, ndim);

    // check whether position is outside the intended fitting region
    for (i = 0; i < ndim; i++)
    {
        if ((position[i] < region_offset[i]) || (position[i] >= region_end[i]))
        {
            *y_fit = LARGE_NUMBER;
            ZERO_VECTOR(dy_da, npeaks*nparams_per_peak); // arbitrary, hopefully ok
            return;
        }
    }

    *y_fit = 0;
    for (j = 0; j < npeaks; j++)
    {
        if (method == GAUSSIAN_METHOD)
            *y_fit += gaussian(ndim, x, a, dy_da);
        else
            *y_fit += lorentzian(ndim, x, a, dy_da);

        a += nparams_per_peak;
        if (dy_da)
            dy_da += nparams_per_peak;
    }
}

static CcpnStatus fit_parabolic(PyArrayObject *data_array,
                                PyArrayObject *region_array, PyArrayObject *peak_array,
                                PyObject *fit_list, char *error_msg)
{
    int i, j, k, ndim, total_region_size, first, last, nparams, npeaks, npts;
    int region_offset[MAX_NDIM], region_size[MAX_NDIM], cumul_region[MAX_NDIM], points[MAX_NDIM], region_end[MAX_NDIM];
    npy_intp array[MAX_NDIM], grid_posn[MAX_NDIM], posn;
    float *x, *y, *params, *params_dev, *w = NULL, *y_fit = NULL;
    float peak_posn[MAX_NDIM], height, chisq, max_iter = 0, noise = 0;
    float peakFit[MAX_NDIM], lineWidths[MAX_NDIM];
    float peakHeight;
    PyObject *fit_obj, *posn_obj, *lw_obj;
    FitPeak fitPeak;
    CcpnBool have_maximum;
    CcpnStatus status;

    ndim = PyArray_DIM(region_array, 1);
    for (i = 0; i < ndim; i++)
    {
        first = *((int *) PyArray_GETPTR2(region_array, 0, i));
        last = *((int *) PyArray_GETPTR2(region_array, 1, i));
        region_offset[i] = first;
        region_end[i] = last;
        region_size[i] = last - first;
    }

    CUMULATIVE(cumul_region, region_size, total_region_size, ndim);

    npeaks = PyArray_DIM(peak_array, 0);
    nparams = (1+2*ndim) * npeaks;

    sprintf(error_msg, "allocating memory for params, params_dev");
    MALLOC(params, float, nparams);

    for (i = 0; i < ndim; i++)
        points[i] = PyArray_DIM(data_array, ndim-1-i);

    k = 0;

    // iterate over all the peaks passed in
    for (j = 0; j < npeaks; j++)
    {
        // find the index point nearest to the peak position (floats)
        // relative to the dataArray, clipped to the dataArray bounds
        for (i = 0; i < ndim; i++)
        {
            peak_posn[i] = *((float *) PyArray_GETPTR2(peak_array, j, i));
            posn = NEAREST_INTEGER(peak_posn[i]);
            npts = PyArray_DIM(data_array, ndim-1-i);
            posn = MAX(0, posn);
            posn = MIN(npts-1, posn);
            grid_posn[i] = posn;

        }

        for (i = 0; i < ndim; i++)
            status = fitParabolicToNDim(data_array, &peakHeight, grid_posn, points, &peakFit[i], &lineWidths[i], i);

        params[k++] = peakHeight;
        for (i = 0; i < ndim; i++)
            params[k++] = peakFit[i];

        for (i = 0; i < ndim; i++)
            params[k++] = lineWidths[i];
    }

    status = CCPN_OK;

    if (status == CCPN_ERROR)
    {
        FREE(params, float);
        return CCPN_ERROR;
    }

    k = 0;
    for (j = 0; j < npeaks; j++)
    {
        fit_obj = PyTuple_New(3); // height, position, linewidth
        if (!fit_obj)
            RETURN_ERROR_MSG("allocating fit data");

        posn_obj = PyTuple_New(ndim);
        if (!posn_obj)
            RETURN_ERROR_MSG("allocating position");

        lw_obj = PyTuple_New(ndim);
        if (!lw_obj)
            RETURN_ERROR_MSG("allocating linewidth");

        height = params[k++];
        PyTuple_SetItem(fit_obj, 0, PyFloat_FromDouble((double) height));
        PyTuple_SetItem(fit_obj, 1, posn_obj);
        PyTuple_SetItem(fit_obj, 2, lw_obj);

        for (i = 0; i < ndim; i++)
            PyTuple_SetItem(posn_obj, i, PyFloat_FromDouble((double) params[k++]));

        for (i = 0; i < ndim; i++)
            PyTuple_SetItem(lw_obj, i, PyFloat_FromDouble((double) params[k++]));

        if (PyList_Append(fit_list, fit_obj))
            RETURN_ERROR_MSG("appending fit data to fit list");

        Py_DECREF(fit_obj);
    }

    FREE(params, float);

    return CCPN_OK;
}

static CcpnStatus fit_peaks(PyArrayObject *data_array,
                            PyArrayObject *region_array, PyArrayObject *peak_array,
                            int method, PyObject *fit_list, char *error_msg)
{
    int i, j, k, ndim, total_region_size, first, last, nparams, npeaks, npts;
    int region_offset[MAX_NDIM], region_size[MAX_NDIM], cumul_region[MAX_NDIM], points[MAX_NDIM], region_end[MAX_NDIM];
    npy_intp array[MAX_NDIM], grid_posn[MAX_NDIM], posn;
    float *x, *y, *params, *params_dev, *w = NULL, *y_fit = NULL;
    float peak_posn[MAX_NDIM], height, chisq, max_iter = 0, noise = 0;
    PyObject *fit_obj, *posn_obj, *lw_obj;
    FitPeak fitPeak;
    CcpnBool have_maximum;
    CcpnStatus status;

    ndim = PyArray_DIM(region_array, 1);
    for (i = 0; i < ndim; i++)
    {
        first = *((int *) PyArray_GETPTR2(region_array, 0, i));
        last = *((int *) PyArray_GETPTR2(region_array, 1, i));
        region_offset[i] = first;
        region_end[i] = last;
        region_size[i] = last - first;
    }

    CUMULATIVE(cumul_region, region_size, total_region_size, ndim);

    sprintf(error_msg, "allocating memory for x, y");
    MALLOC(x, float, total_region_size);
    MALLOC(y, float, total_region_size);

    // get the block of elements surrounding the peak to test
    for (j = 0; j < total_region_size; j++)
    {
        x[j] = j;  // the real x is multidimensional so have to use index into it
        ARRAY_OF_INDEX(array, j, cumul_region, ndim);
        ADD_VECTORS(array, array, region_offset, ndim);
        y[j] = get_value_at_point(data_array, array);
    }

    npeaks = PyArray_DIM(peak_array, 0);
    nparams = (1+2*ndim) * npeaks;

    //printf(">>> npeaks: %i\n", npeaks);

    sprintf(error_msg, "allocating memory for params, params_dev");
    MALLOC(params, float, nparams);
    MALLOC(params_dev, float, nparams);

    for (i = 0; i < ndim; i++)
        points[i] = PyArray_DIM(data_array, ndim-1-i);

    k = 0;

    // iterate over all the peaks passed in
    for (j = 0; j < npeaks; j++)
    {

        // find the index point nearest to the peak position (floats)
        // relative to the dataArray, clipped to the dataArray bounds
        for (i = 0; i < ndim; i++)
        {
            peak_posn[i] = *((float *) PyArray_GETPTR2(peak_array, j, i));
            posn = NEAREST_INTEGER(peak_posn[i]);
            npts = PyArray_DIM(data_array, ndim-1-i);
            posn = MAX(0, posn);
            posn = MIN(npts-1, posn);
            grid_posn[i] = posn;

            //printf(">>> npeak %i, %i -> [%i]\n", j, i, peak_posn[i]);

        }

        height = get_value_at_point(data_array, grid_posn);
        have_maximum = height > 0;  // TBD: possibly wrong

        //printf(">>> height %i, %f\n", j, height);

        params[k++] = height;
        for (i = 0; i < ndim; i++)
            params[k++] = grid_posn[i];

        for (i = 0; i < ndim; i++)
            params[k++] = half_max_linewidth(data_array, have_maximum, height, grid_posn, points, i);
    }

    fitPeak.ndim = ndim;
    fitPeak.npeaks = npeaks;
    fitPeak.region_offset = region_offset;
    fitPeak.region_end = region_end;
    fitPeak.cumul_region = cumul_region;
    fitPeak.method = method;

    status = nonlinear_fit(total_region_size, x, y, w, y_fit,
                           nparams, params, params_dev,
                           max_iter, noise, &chisq,
                           _fitting_func, (void *) &fitPeak, error_msg);

    FREE(x, float);
    FREE(y, float);

    if (status == CCPN_ERROR)
    {
        FREE(params, float);
        FREE(params_dev, float);
        return CCPN_ERROR;
    }

    k = 0;
    for (j = 0; j < npeaks; j++)
    {
        fit_obj = PyTuple_New(3); // height, position, linewidth
        if (!fit_obj)
            RETURN_ERROR_MSG("allocating fit data");

        posn_obj = PyTuple_New(ndim);
        if (!posn_obj)
            RETURN_ERROR_MSG("allocating position");

        lw_obj = PyTuple_New(ndim);
        if (!lw_obj)
            RETURN_ERROR_MSG("allocating linewidth");

        height = params[k++];
        PyTuple_SetItem(fit_obj, 0, PyFloat_FromDouble((double) height));
        PyTuple_SetItem(fit_obj, 1, posn_obj);
        PyTuple_SetItem(fit_obj, 2, lw_obj);

        for (i = 0; i < ndim; i++)
            PyTuple_SetItem(posn_obj, i, PyFloat_FromDouble((double) params[k++]));

        for (i = 0; i < ndim; i++)
            PyTuple_SetItem(lw_obj, i, PyFloat_FromDouble((double) params[k++]));

        if (PyList_Append(fit_list, fit_obj))
            RETURN_ERROR_MSG("appending fit data to fit list");

        Py_DECREF(fit_obj);
    }

    FREE(params, float);
    FREE(params_dev, float);

    return CCPN_OK;
}

static PyObject *findPeaks(PyObject *self, PyObject *args)
{
    long i, ndim, buffer[MAX_NDIM];
    CcpnBool nonadjacent, have_low, have_high;
    float low, high, drop_factor, min_linewidth[MAX_NDIM];
    PyObject *min_linewidth_obj, *buffer_obj, *z, *peak_list;
    PyObject *excluded_regions_obj, *diagonal_exclusion_dims_obj, *diagonal_exclusion_transform_obj;
    PyArrayObject *data_array, *excluded_regions_array, *diagonal_exclusion_dims_array, *diagonal_exclusion_transform_array;
    char error_msg[1000];

    if (!PyArg_ParseTuple(args, "O!iiffO!ifO!O!O!O!",
                          &PyArray_Type, &data_array,
                          &have_low, &have_high, &low, &high,
                          &PyList_Type, &buffer_obj,
                          &nonadjacent, &drop_factor,
                          &PyList_Type, &min_linewidth_obj,
                          &PyList_Type, &excluded_regions_obj,
                          &PyList_Type, &diagonal_exclusion_dims_obj,
                          &PyList_Type, &diagonal_exclusion_transform_obj))
        RETURN_OBJ_ERROR("need arguments: dataArray, haveLow, haveHigh, low, high, buffer, nonadjacent, dropFactor, minLinewidth, excludedRegions, diagonalExclusionDims, diagonalExclusionTransform");

    if (PyArray_TYPE(data_array) != NPY_FLOAT)
        RETURN_OBJ_ERROR("dataArray needs to be array of floats");

    ndim = PyArray_NDIM(data_array);

    if (ndim > MAX_NDIM)
    {
        sprintf(error_msg, "maximum ndim is %d", MAX_NDIM);
        RETURN_OBJ_ERROR(error_msg);
    }

    if (PyList_Size(buffer_obj) != ndim)
    {
        sprintf(error_msg, "buffer is a list of size %ld, should be %ld", (long) PyList_Size(buffer_obj), ndim);
        RETURN_OBJ_ERROR(error_msg);
    }

    for (i = 0; i < ndim; i++)
    {
        z = PyList_GetItem(buffer_obj, i);
        if (!PyLong_Check(z))
        {
            sprintf(error_msg, "buffer element %ld is not an int", i);
            RETURN_OBJ_ERROR(error_msg);
        }

        buffer[i] = (long) PyLong_AsLong(z);
    }

    if (PyList_Size(min_linewidth_obj) != ndim)
    {
        sprintf(error_msg, "minLinewidth is a list of size %ld, should be %ld\n", (long) PyList_Size(buffer_obj), ndim);
        RETURN_OBJ_ERROR(error_msg);
    }

    for (i = 0; i < ndim; i++)
    {
        z = PyList_GetItem(min_linewidth_obj, i);
        if (!PyFloat_Check(z))
        {
            sprintf(error_msg, "minLinewidth element %ld is not a float", i);
            RETURN_OBJ_ERROR(error_msg);
        }

        min_linewidth[i] = (float) PyFloat_AsDouble(z);
    }

    for (i = 0; i < PyList_Size(excluded_regions_obj); i++)
    {
        excluded_regions_array = (PyArrayObject *) PyList_GetItem(excluded_regions_obj, i);

        if (!PyArray_Check(excluded_regions_array))
            RETURN_OBJ_ERROR("excludedRegions needs to be list of NumPy arrays");

        if (PyArray_TYPE(excluded_regions_array) != NPY_FLOAT)
            RETURN_OBJ_ERROR("excludedRegions needs to be list of NumPy float arrays");

        if (PyArray_NDIM(excluded_regions_array) != 2)
        {
            sprintf(error_msg, "excludedRegions must be list of 2 dimensional NumPy arrays");
            RETURN_OBJ_ERROR(error_msg);
        }

        if ((PyArray_DIM(excluded_regions_array, 0) != 2) || (PyArray_DIM(excluded_regions_array, 1) != ndim))
        {
            sprintf(error_msg, "excludedRegions must be list of 2 x %ld NumPy arrays", ndim);
            RETURN_OBJ_ERROR(error_msg);
        }
    }

    if (PyList_Size(diagonal_exclusion_dims_obj) != PyList_Size(diagonal_exclusion_transform_obj))
    {
        sprintf(error_msg, "diagonalExclusionDims is a list of size %ld, diagonalExclusionTransform is of size %ld, should be the same",
                (long) PyList_Size(diagonal_exclusion_dims_obj), (long) PyList_Size(diagonal_exclusion_transform_obj));
        RETURN_OBJ_ERROR(error_msg);
    }

    for (i = 0; i < PyList_Size(diagonal_exclusion_dims_obj); i++)
    {
        diagonal_exclusion_dims_array = (PyArrayObject *) PyList_GetItem(diagonal_exclusion_dims_obj, i);

        if (!PyArray_Check(diagonal_exclusion_dims_array))
            RETURN_OBJ_ERROR("diagonalExclusionDims needs to be list of NumPy arrays");

        if (PyArray_TYPE(diagonal_exclusion_dims_array) != NPY_INT)
            RETURN_OBJ_ERROR("diagonalExclusionDims needs to be list of NumPy int arrays");

        if (PyArray_NDIM(diagonal_exclusion_dims_array) != 1)
        {
            sprintf(error_msg, "diagonalExclusionDims must be list of 1 dimensional NumPy arrays");
            RETURN_OBJ_ERROR(error_msg);
        }

        if (PyArray_DIM(diagonal_exclusion_dims_array, 0) != 2)
        {
            sprintf(error_msg, "diagonalExclusionDims must be list of size 2 NumPy arrays");
            RETURN_OBJ_ERROR(error_msg);
        }
    }

    for (i = 0; i < PyList_Size(diagonal_exclusion_transform_obj); i++)
    {
        diagonal_exclusion_transform_array = (PyArrayObject *) PyList_GetItem(diagonal_exclusion_transform_obj, i);

        if (!PyArray_Check(diagonal_exclusion_transform_array))
            RETURN_OBJ_ERROR("diagonalExclusionTransform needs to be list of NumPy arrays");

        if (PyArray_TYPE(diagonal_exclusion_transform_array) != NPY_FLOAT)
            RETURN_OBJ_ERROR("diagonalExclusionTransform needs to be list of NumPy float arrays");

        if (PyArray_NDIM(diagonal_exclusion_transform_array) != 1)
        {
            sprintf(error_msg, "diagonalExclusionTransform must be list of 1 dimensional NumPy arrays");
            RETURN_OBJ_ERROR(error_msg);
        }

        if (PyArray_DIM(diagonal_exclusion_transform_array, 0) != 4)
        {
            sprintf(error_msg, "diagonalExclusionTransform must be list of size 4 NumPy arrays");
            RETURN_OBJ_ERROR(error_msg);
        }
    }

    peak_list = PyList_New(0);
    if (!peak_list)
        RETURN_OBJ_ERROR("allocating memory for peak list");

    if (find_peaks(data_array, have_low, have_high, low, high, buffer, nonadjacent, drop_factor, min_linewidth, peak_list,
                   excluded_regions_obj, diagonal_exclusion_dims_obj, diagonal_exclusion_transform_obj, error_msg) == CCPN_ERROR)
        RETURN_OBJ_ERROR(error_msg);

    return peak_list;
}

static PyObject *fitPeaks(PyObject *self, PyObject *args)
{
    int i, ndim, method;
    PyObject *peak_list, *fit_list;
    PyArrayObject *data_array, *region_array, *peak_array;
    char error_msg[1000];

    if (!PyArg_ParseTuple(args, "O!O!O!i",
                          &PyArray_Type, &data_array,
                          &PyArray_Type, &region_array,
                          &PyArray_Type, &peak_array,
                          &method))
        RETURN_OBJ_ERROR("need arguments: dataArray, regionArray, peakArray, method");

    if (PyArray_TYPE(data_array) != NPY_FLOAT)
        RETURN_OBJ_ERROR("dataArray needs to be array of floats");

    ndim = PyArray_NDIM(data_array);

    if (ndim > MAX_NDIM)
    {
        sprintf(error_msg, "maximum ndim is %d", MAX_NDIM);
        RETURN_OBJ_ERROR(error_msg);
    }

    if (PyArray_TYPE(region_array) != NPY_INT32)
        RETURN_OBJ_ERROR("regionArray needs to be array of ints");

    if (PyArray_NDIM(region_array) != 2)
        RETURN_OBJ_ERROR("regionArray must be 2 dimensional");

    if ((PyArray_DIM(region_array, 0) != 2) || (PyArray_DIM(region_array, 1) != ndim))
    {
        sprintf(error_msg, "regionArray must be 2 x %d", ndim);
        RETURN_OBJ_ERROR(error_msg);
    }

    if (PyArray_TYPE(peak_array) != NPY_FLOAT)
        RETURN_OBJ_ERROR("peakArray needs to be array of floats");

    if (method != GAUSSIAN_METHOD && method != LORENTZIAN_METHOD)
    {
	    sprintf(error_msg, "method must be %d (Gaussian) or %d (Lorentzian)", GAUSSIAN_METHOD, LORENTZIAN_METHOD);
        RETURN_OBJ_ERROR(error_msg);
    }

    fit_list = PyList_New(0);
    if (!fit_list)
        RETURN_OBJ_ERROR("allocating memory for fit list");

    if (fit_peaks(data_array, region_array, peak_array, method, fit_list, error_msg) == CCPN_ERROR)
        RETURN_OBJ_ERROR(error_msg);

    return fit_list;
}

static PyObject *fitParabolicPeaks(PyObject *self, PyObject *args)
{
    int i, ndim;
    PyObject *peak_list, *fit_list;
    PyArrayObject *data_array, *region_array, *peak_array;
    char error_msg[1000];

    if (!PyArg_ParseTuple(args, "O!O!O!",
                          &PyArray_Type, &data_array,
                          &PyArray_Type, &region_array,
                          &PyArray_Type, &peak_array))
        RETURN_OBJ_ERROR("need arguments: dataArray, regionArray, peakArray");

    if (PyArray_TYPE(data_array) != NPY_FLOAT)
        RETURN_OBJ_ERROR("dataArray needs to be array of floats");

    ndim = PyArray_NDIM(data_array);

    if (ndim > MAX_NDIM)
    {
        sprintf(error_msg, "maximum ndim is %d", MAX_NDIM);
        RETURN_OBJ_ERROR(error_msg);
    }

    if (PyArray_TYPE(region_array) != NPY_INT32)
        RETURN_OBJ_ERROR("regionArray needs to be array of ints");

    if (PyArray_NDIM(region_array) != 2)
        RETURN_OBJ_ERROR("regionArray must be 2 dimensional");

    if ((PyArray_DIM(region_array, 0) != 2) || (PyArray_DIM(region_array, 1) != ndim))
    {
        sprintf(error_msg, "regionArray must be 2 x %d", ndim);
        RETURN_OBJ_ERROR(error_msg);
    }

    if (PyArray_TYPE(peak_array) != NPY_FLOAT)
        RETURN_OBJ_ERROR("peakArray needs to be array of floats");

    fit_list = PyList_New(0);
    if (!fit_list)
        RETURN_OBJ_ERROR("allocating memory for fit list");

    // iterate over all the maximum presented and return the parabolic closest elements and height
    if (fit_parabolic(data_array, region_array, peak_array, fit_list, error_msg) == CCPN_ERROR)
        RETURN_OBJ_ERROR(error_msg);
    
    return fit_list;
}

static char findPeaks_doc[] = "Find peaks in ND data";
static char fitPeaks_doc[] = "Fit peaks in ND data";
static char fitParabolicPeaks_doc[] = "Fit parabolic peaks in ND data";

static struct PyMethodDef Peak_type_methods[] =
{
    { "findPeaks",      (PyCFunction) findPeaks,        METH_VARARGS,   findPeaks_doc },
    { "fitPeaks",      (PyCFunction) fitPeaks,        METH_VARARGS,   fitPeaks_doc },
    { "fitParabolicPeaks",      (PyCFunction) fitParabolicPeaks,        METH_VARARGS,   fitParabolicPeaks_doc },
    { NULL,         NULL,                       0,              NULL }
};

struct module_state
{
    PyObject *error;
};

static struct PyModuleDef moduledef =
{
    PyModuleDef_HEAD_INIT,
    "Peak",
    NULL,
    sizeof(struct module_state),
    Peak_type_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyObject *PyInit_Peak(void)
{
    PyObject *module;

#ifdef WIN32
    Peak.ob_type = &PyType_Type;
#endif
    /* create the module and add the functions */
    module = PyModule_Create(&moduledef);

    import_array();  /* needed for numpy, otherwise it crashes */

    /* create exception object and add to module */
    ErrorObject = PyErr_NewException("Peak.error", NULL, NULL);
    Py_INCREF(ErrorObject);

    PyModule_AddObject(module, "error", ErrorObject);

    if (module == NULL)
        return NULL;

    struct module_state *st = (struct module_state*)PyModule_GetState(module);

    st->error = PyErr_NewException("Peak.error", NULL, NULL);
    if (st->error == NULL)
    {
        Py_DECREF(module);
        return NULL;
    }

    /* check for errors */
    if (PyErr_Occurred())
        Py_FatalError("can't initialize module Peak");

    return module;
}

