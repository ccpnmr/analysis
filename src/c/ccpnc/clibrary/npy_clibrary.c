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

struct Node
{
    // Struct to contain nmrResidue information

    // data
    PyObject *object;
    double  relativeOffset;
    long    index;

    // pointers
    struct  Node *prev;
    struct  Node *next;
};

struct Node *newNode(PyObject *nmrResidue)
{
    // create a new element
    struct Node *temp = (struct Node*) malloc(sizeof(struct Node));

    // set up the data
    temp->relativeOffset = -0.1;
    temp->index = -1;
    temp->object = nmrResidue;

    // initialise the pointers
    temp->prev = NULL;
    temp->next = NULL;
    return temp;
}

static CcpnBool compareRes(struct Node* leftNode, struct Node* rightNode)
{
    // compare whether 2 residues in connected stretch are similar
    if (leftNode->index == rightNode->index)
        if (leftNode->relativeOffset < rightNode->relativeOffset)
            return CCPN_TRUE;
        else
            return CCPN_FALSE;

    if (leftNode->index < rightNode->index)
        return CCPN_TRUE;

    return CCPN_FALSE;
}

struct Node* insert(struct Node* node, struct Node* item)
{
    // If the tree is empty, return previously defined new node
    if (!node)
        return item;

    // Otherwise, recurse down the tree
    if (compareRes(item, node) == CCPN_TRUE)
        node->prev = insert(node->prev, item);
    else
        node->next = insert(node->next, item);

    return node;
}

static CcpnBool insertNode(struct Node **headRef, PyObject *offsetItem, long index)
{
    struct Node *temp = newNode(offsetItem);
    struct Node *ptr = (*headRef);
    double relOffset;
    PyObject *test;

    // test for None - means a main residue
    test = PyObject_GetAttrString(offsetItem, "relativeOffset");
    if (test != Py_None)
    {
        relOffset = PyFloat_AsDouble(PyObject_GetAttrString(offsetItem, "relativeOffset"));
        temp->relativeOffset = relOffset;
    }
    temp->index = index;

    (*headRef) = insert(ptr, temp);

    return CCPN_TRUE;
}

static void getIndexInList(struct Node *node, PyObject *item, long *index, long *found)
{
    if (node)
    {
        getIndexInList(node->prev, item, index, found);
        (*index)++;
        if (node->object == item)
            *found = *index;

        getIndexInList(node->next, item, index, found);
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
        if (ptr->object == item)
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
    PyTupleObject *nmrResidues;
    PyObject *nmrResidue;
    PyObject *returnValue;
    char error_msg[1000];
    long index = -1, numRes = 0, numOffsets = 0, found = -1, rg;
    PyObject *listRes;
    PyObject *apiNmrResidue;
    PyListObject *offsetList;
    PyObject *offsetRes;
//    PyListObject *foundResonanceGroups;
    PyListObject *resonanceGroups;
    PyDictObject *resonanceGroupDict;
    PyObject *project, *mainRes;

//    long    *ptrs = NULL;
//    MALLOC(ptrs, long, 10);     // remember to dealloc
//    REALLOC(ptrs, long, 12);
//    FREE(ptrs, long);

    if (!PyArg_ParseTuple(args, "O", &nmrResidue))
        RETURN_OBJ_ERROR("need arguments: nmrResidue");

    // testing through api

    apiNmrResidue = (PyObject *) PyObject_GetAttrString(nmrResidue, "_wrappedData");
    nmrChain = (PyObject *) PyObject_GetAttrString(apiNmrResidue, "nmrChain");
    nmrResidues = (PyListObject *) PyObject_GetAttrString(nmrChain, "mainResonanceGroups");

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


//    foundResonanceGroups = newList();
    project = (PyObject *) PyObject_GetAttrString(apiNmrResidue, "nmrProject");
    resonanceGroupDict = (PyDictObject *) PyObject_GetAttrString(project, "__dict__");
    resonanceGroups = (PyListObject *) PyDict_GetItemString(resonanceGroupDict, "resonanceGroups");

    // put the main residues into a list
    numRes = PyTuple_GET_SIZE(nmrResidues);
    PyObject *mainResGroups[numRes];
    for (long ii = 0; ii < numRes; ii++)
    {
        mainResGroups[ii] = (PyObject *) PyTuple_GET_ITEM(nmrResidues, ii);
    }

    // search all residues into the list
    rg = PyList_GET_SIZE(resonanceGroups);
    PyObject *foundResonanceGroups[rg];

    printf("%li \n", rg);
    int count = 0, jj;
    for (long ii = 0; ii < rg; ii++)
    {
        listRes = (PyObject *) PyList_GET_ITEM(resonanceGroups, ii);

//        mainRes = (PyObject *) PyObject_GetAttrString(listRes, "serial");     //  not pointing to the right place
//
        for (jj = 0; jj < numRes; jj++)
            if (listRes == mainResGroups[jj])
            {
                foundResonanceGroups[count] = listRes;
                count++;
            }
    }
    printf("%i \n", count);

    // iterate through the mainresonanceGroups
    // add tolinked list

    // iterate through offsetResonanceGroups
    // insert by relativeoffset if samemainResonanceGroup

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~

    struct Node *resonanceList = NULL;

    numRes = PyTuple_GET_SIZE(nmrResidues);
    for (long ii = 0; ii < numRes; ii++)
    {
        listRes = (PyObject *) PyTuple_GET_ITEM(nmrResidues, ii);
//        listRes = foundResonanceGroups[ii];       // nice, but order lost

        insertNode(&resonanceList, listRes, ii);

        offsetList = (PyListObject *) PyObject_GetAttrString(listRes, "offsetResonanceGroups");
        numOffsets = PyList_GET_SIZE(offsetList);
        for (long jj=0; jj < numOffsets; jj++)
        {
            offsetRes = (PyObject *) PyList_GET_ITEM(offsetList, jj);
            insertNode(&resonanceList, offsetRes, ii);
        }
    }

    getIndexInList(resonanceList, apiNmrResidue, &index, &found);
    returnValue = PyLong_FromLong(found);
    return returnValue;
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
    return returnValue;
}

static PyObject *testReturnList(PyObject *self, PyObject *args)
{
    PyArrayObject *data_obj, *levels_obj, *indices, *vertices, *colours;
    PyObject *returnObject;

    // create a new list
    returnObject = newList();

    // append an item to the list
    appendFloatList(returnObject, 126.45);
    appendFloatList(returnObject, 54.27);
    appendFloatList(returnObject, -2.6);

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

