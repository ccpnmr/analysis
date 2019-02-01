/*
======================COPYRIGHT/LICENSE START==========================

npy_clibrary2d.c: Part of the CcpNmr Analysis program

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

#include "Python.h"

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION  // so that warnings avoided
#include "arrayobject.h"

#include "npy_defns.h"

/*
  Module: Clibrary2d

  Function:

    Input:

    Output:

*/

static PyObject *ErrorObject;   /* locally-raised exception */

static PyObject *newList()
{
    PyObject *list;
    list = PyList_New(0);
    if (!list)
    {
        RETURN_OBJ_ERROR("allocating list memory");
    }
    return list;
}

static appendFloatList(PyObject *list, double value)
{
    if (PyList_Append(list, PyFloat_FromDouble((double) value)) != 0)
    {
        RETURN_OBJ_ERROR("appending item to list");
    }
}

static PyObject *testReturnList(PyObject *self, PyObject *args)
{
    PyArrayObject *data_obj, *levels_obj, *indices, *vertices, *colours;
    PyObject *returnObject;

    // create a new list
    returnObject = newList();
    /*    if (!returnObject)
        {
        	RETURN_OBJ_ERROR("allocating returnObject memory");
        }
    */
    // append an item to the list
    appendFloatList(returnObject, 126.45);
    appendFloatList(returnObject, 54.27);
    appendFloatList(returnObject, -2.6);

    // Needs the array to be defined first
//    appendFloatList(colours, -2.6);
//    appendFloatList(colours, 52.6);


    /*    if (PyList_Append(returnObject, PyFloat_FromDouble((double) 126.45)) != 0)
        {
            Py_DECREF(returnObject);
            RETURN_OBJ_ERROR("appending item to returnObject");
        }
        if (PyList_Append(returnObject, PyFloat_FromDouble((double) 15.67)) != 0)
        {
            Py_DECREF(returnObject);
            RETURN_OBJ_ERROR("appending item to returnObject");
        }
        if (PyList_Append(returnObject, PyFloat_FromDouble((double) -1.12)) != 0)
        {
            Py_DECREF(returnObject);
            RETURN_OBJ_ERROR("appending item to returnObject");
        }
    */
    return returnObject;
}

static char testReturnList_doc[] = "Return a list from a python c routine.";

static struct PyMethodDef Clibrary_type_methods[] =
{
    { "testReturnList",      (PyCFunction) testReturnList,        METH_VARARGS,   testReturnList_doc },
    { NULL,         NULL,                       0,              NULL }
};

struct module_state
{
    PyObject *error;
};

static struct PyModuleDef moduledef =
{
    PyModuleDef_HEAD_INIT,
    "Clibrary",
    NULL,
    sizeof(struct module_state),
    Clibrary_type_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyObject *PyInit_Clibrary(void)
{
    PyObject *module;

#ifdef WIN32
    Clibrary.ob_type = &PyType_Type;
#endif
    /* create the module and add the functions */
    module = PyModule_Create(&moduledef);

    import_array();  /* needed for numpy, otherwise it crashes */

    /* create exception object and add to module */
    ErrorObject = PyErr_NewException("ClibraryPy.error", NULL, NULL);
    Py_INCREF(ErrorObject);

    PyModule_AddObject(module, "error", ErrorObject);

    if (module == NULL)
        return NULL;

    struct module_state *st = (struct module_state*)PyModule_GetState(module);

    st->error = PyErr_NewException("ClibraryPy.error", NULL, NULL);
    if (st->error == NULL)
    {
        Py_DECREF(module);
        return NULL;
    }

    /* check for errors */
    if (PyErr_Occurred())
        Py_FatalError("can't initialize module ClibraryPy");

    return module;
}

