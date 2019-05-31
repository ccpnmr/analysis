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

static appendFloatLong(PyObject *list, value)
{
    if (PyList_Append(list, PyLong_FromVoidPtr(value)) != 0)
    {
        RETURN_OBJ_ERROR("appending item to list");
    }
}

#define cat(z, a)          *((uint8_t *)memcpy(&(z), &(a), sizeof(a)) + sizeof(a))

struct Node
{
    // data
    PyObject *mainResonance;
    double  relativeOffset;
    double  index;

    // pointers
    struct  Node *prev;
    struct  Node *next;
};

struct Node *newNode(PyObject *item)
{
    // create a new element
    struct Node *temp = (struct Node*) malloc(sizeof(struct Node));

    // set up the data
    temp->relativeOffset = -0.1;
    temp->index = -1;
    temp->mainResonance = item;

    // initialise the pointers
    temp->prev = NULL;
    temp->next = NULL;
    return temp;
}

static appendNode(struct Node** headRef, PyObject *item, index)
{
    struct Node *temp = newNode(item);
    struct Node *ptr = (*headRef);

    if (!ptr)
        // set the head to the only element
        (*headRef) = temp;
    else
    {
        // find the end of the list
        while (ptr->next)
            ptr = ptr->next;

        // add the new item
        ptr->next = temp;
        temp->prev = ptr;
    }
    temp->index = (double) index;
}

void insertNode(struct Node **headRef, PyObject *mainResonance, PyObject *offsetItem, index)
{
    struct Node *temp = newNode(offsetItem);
    struct Node *ptr = (*headRef);
    double relOffset;

    // test whether the relativeOffsets are lower...
    // this is assumed to be offset

    if (!ptr)
        // just making sure - the list MAY be empty
        (*headRef) = temp;
    else
    {
        relOffset = PyFloat_AsDouble(PyObject_GetAttrString(offsetItem, "relativeOffset"));
        while (ptr)
        {
            if ((ptr->mainResonance == mainResonance) && (relOffset < ptr->relativeOffset))
            {
                if (!ptr->prev)
                {
                    // put at the head
                    temp->next = ptr;
                    ptr->prev = temp;
                    (*headRef) = temp;
                    return;
                }
                else
                {
                    // insert before
                    temp->next = ptr;
                    temp->prev = ptr->prev;
                    ptr->prev->next = temp;
                    ptr->prev = temp;
                    return;
                }
            }
            ptr = ptr->next;
        }
    }
}

long getIndex(struct Node *nodeList, PyObject *item)
{
    struct Node *ptr = nodeList;
    long index = -1, returnValue = -1;

    //start from the beginning
    while (ptr)
    {
        index++;
        if (ptr->mainResonance == item)
        {
            returnValue = index;
            break;
        }

        ptr = ptr->next;
    }

    return returnValue;
}

static PyObject *getNmrResidueIndex(PyObject *self, PyObject *args)
{
    PyObject *nmrChain;
//    PyListObject *nmrResidues;
    PyTupleObject *nmrResidues;
    PyObject *nmrResidue;
    PyObject *returnValue;
    char error_msg[1000];
    long index, numRes = 0, numOffsets = 0;
    PyObject *listRes;
    PyObject *apiNmrResidue;
    PyListObject *offsetList;
    PyObject *offsetRes;

//    long    *ptrs = NULL;
//    MALLOC(ptrs, long, 10);     // remember to dealloc
//    REALLOC(ptrs, long, 12);
//    FREE(ptrs, long);

//    PyObject *returnObject;
//    returnObject = newList();


    if (!PyArg_ParseTuple(args, "O", &nmrResidue))
        RETURN_OBJ_ERROR("need arguments: nmrResidue");

    // testing through api

    apiNmrResidue = (PyObject *) PyObject_GetAttrString(nmrResidue, "_wrappedData");
    nmrChain = (PyObject *) PyObject_GetAttrString(apiNmrResidue, "nmrChain");
    nmrResidues = (PyListObject *) PyObject_GetAttrString(nmrChain, "mainResonanceGroups");

    // iterate through the mainresonanceGroups
    // add tolinked list

    // iterate through offsetResonanceGroups
    // insert by relativeoffset if samemainResonanceGroup

    struct Node *resonanceList = NULL;

    numRes = PyTuple_GET_SIZE(nmrResidues);
    for (long ii = 0; ii < numRes; ii++)
    {
        listRes = (PyObject *) PyTuple_GET_ITEM(nmrResidues, ii);

        appendNode(&resonanceList, listRes, ii);

        offsetList = (PyListObject *) PyObject_GetAttrString(listRes, "offsetResonanceGroups");
        numOffsets = PyList_GET_SIZE(offsetList);
        for (long jj=0; jj < numOffsets; jj++)
        {
            printf("~");
            offsetRes = (PyObject *) PyList_GET_ITEM(offsetList, jj);
            insertNode(&resonanceList, listRes, offsetRes, ii);
        }
    }

    index = getIndex(resonanceList, apiNmrResidue);
    printf("\nstrange %d\n\n", index);
    returnValue = PyLong_FromLong(index);
    return returnValue;



/*
//    appendFloatLong(returnObject, nmrResidue);
//    appendFloatLong(returnObject, apiNmrResidue);


//    numRes = PyTuple_GET_SIZE(nmrResidues);
    for (long ii = 0; ii < numRes; ii++)
    {
        listRes = (PyObject *) PyTuple_GET_ITEM(nmrResidues, ii);

//        appendFloatLong(returnObject, listRes);

        if (listRes == apiNmrResidue)
            return PyLong_FromLong(ii);
    }

    returnValue = PyLong_FromLong(index);
    return returnValue;

/*
    nmrChain = (PyObject *) PyObject_GetAttrString(nmrResidue, "nmrChain");
    if (!nmrChain)
        RETURN_OBJ_ERROR("nmrChain is not defined");

    nmrResidues = (PyListObject *) PyObject_GetAttrString(nmrChain, "nmrResidues");
    if (!nmrResidues)
        RETURN_OBJ_ERROR("nmrChain.nmrResidues is not defined");

    numRes = PyList_GET_SIZE(nmrResidues);
    if (!numRes)
        RETURN_OBJ_ERROR("nmrResidues is empty");

    for (int ii = 0; ii < numRes; ii++)
    {
        listRes = (PyObject *) PyList_GET_ITEM(nmrResidues, ii);
        if (listRes == nmrResidue)
        {
            index = ii;
            break;
        }
    }

    returnValue = PyLong_FromLong(index);
    return returnValue;

*/
}

static PyObject *getObjectIndex(PyObject *self, PyObject *args)
{
    PyListObject *nmrChain;
    PyObject *nmrResidue;
    PyObject *returnValue;
    char error_msg[1000];
    long index = -1, numRes = 0;
    PyObject *listRes;

    if (!PyArg_ParseTuple(args, "O!O",
                          &PyList_Type, &nmrChain,
                          &nmrResidue
                          ))
        RETURN_OBJ_ERROR("need arguments: nmrChain, nmrResidue");

    numRes = PyList_GET_SIZE(nmrChain);
    if (numRes == 0)
    {
        sprintf(error_msg, "nmrChain is empty");
        RETURN_OBJ_ERROR(error_msg);
    }

    for (int ii = 0; ii < numRes; ii++)
    {
        listRes = (PyObject *) PyList_GET_ITEM(nmrChain, ii);
        if (listRes == nmrResidue)
        {
            index = ii;
            break;
        }
    }

    returnValue = PyLong_FromLong(index);

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
    return returnValue;
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
static char getNmrResidueIndex_doc[] = "Return the index of an nmrResidue in a chain";
static char getObjectIndex_doc[] = "Return the index of an object in a list";

static struct PyMethodDef Clibrary_type_methods[] =
{
    { "testReturnList",      (PyCFunction) testReturnList,        METH_VARARGS,   testReturnList_doc },
    { "getNmrResidueIndex",  (PyCFunction) getNmrResidueIndex,    METH_VARARGS,   getNmrResidueIndex_doc },
    { "getObjectIndex",      (PyCFunction) getObjectIndex,        METH_VARARGS,   getObjectIndex_doc },
    { NULL,                  NULL,                                0,              NULL }
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

