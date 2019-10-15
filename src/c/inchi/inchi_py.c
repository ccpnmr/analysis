#include "inchi_api.h"
#include "Python.h"

static PyObject *ErrorObject;   /* locally-raised exception */

static struct PyMethodDef Inchi_methods[] =
{
    { "CheckINCHI",      (PyCFunction) CheckINCHI,        METH_VARARGS,   NULL },
    { "CheckINCHIKey",      (PyCFunction) CheckINCHIKey,        METH_VARARGS,   NULL },
    { "FreeINCHI",      (PyCFunction) FreeINCHI,        METH_VARARGS,   NULL },
    { "FreeStdINCHI",      (PyCFunction) FreeStdINCHI,        METH_VARARGS,   NULL },
    { "FreeStructFromINCHI",      (PyCFunction) FreeStructFromINCHI,        METH_VARARGS,   NULL },
    { "FreeStructFromStdINCHI",      (PyCFunction) FreeStructFromStdINCHI,        METH_VARARGS,   NULL },
    { "GetINCHI",      (PyCFunction) GetINCHI,        METH_VARARGS,   NULL },
    { "GetINCHIKeyFromINCHI",      (PyCFunction) GetINCHIKeyFromINCHI,        METH_VARARGS,   NULL },
    { "GetStdINCHI",      (PyCFunction) GetStdINCHI,        METH_VARARGS,   NULL },
    { "GetStdINCHIKeyFromStdINCHI",      (PyCFunction) GetStdINCHIKeyFromStdINCHI,        METH_VARARGS,   NULL },
    { "GetStructFromINCHI",      (PyCFunction) GetStructFromINCHI,        METH_VARARGS,   NULL },
    { "GetINCHI",      (PyCFunction) GetINCHI,        METH_VARARGS,   NULL },
    { NULL,         NULL,                       0,              NULL }
};

struct module_state {
    PyObject *error;
};

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "inchi",
        NULL,
        sizeof(struct module_state),
        Inchi_methods,
        NULL,
        NULL,
        NULL,
        NULL
};

/*PyMODINIT_FUNC initlibinchi(void)*/
PyMODINIT_FUNC PyInit_inchi(void)
{
    PyObject *module;

    /* create the module and add the functions */
    /*module = Py_InitModule("libinchi", Inchi_methods);*/
    module = PyModule_Create(&moduledef);

    /* check for errors */
    /*if (module == NULL || PyErr_Occurred())
        Py_FatalError("can't initialize module libinchi");*/
    
/*    InchiError = PyErr_NewException("libinchi.error", NULL, NULL);
    Py_INCREF(InchiError);
    PyModule_AddObject(m, "error", InchiError);*/

    /* create exception object and add to module */
    ErrorObject = PyErr_NewException("inchi.error", NULL, NULL);
    Py_INCREF(ErrorObject);

    PyModule_AddObject(module, "error", ErrorObject);

    if (module == NULL)
        return NULL;

    struct module_state *st = (struct module_state*)PyModule_GetState(module);

    st->error = PyErr_NewException("inchi.error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        return NULL;
    }

    /* check for errors */
    if (PyErr_Occurred())
        Py_FatalError("can't initialize module inchi");

    return module;

}
