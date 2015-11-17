The code is divided in two layers:
- The data access or 'wrapper' layer that the appliation and macros interact with.
- The data storage or 'API' layer below the wrapper, which corresponds to the CcpNmr 
V2 data model. 

The API layer should be of little interest for most people outside the CCPN,
but we include some documentation for it (not recelty updated), as described here:


./procedures.txt : List of standard procedures for working with the framework

./quickguide.html : Overview of what is happening in the CCPN project

./api-description.html : Overview of the Python API structure

./HowToModel.html : 
a step-by-step description of how to use the CCPN framework for data
modeling.

../doc/apidoc/api.html : 
The detailed Python API documentation, including links to the diagrams of the
model.  This also serves as the best guide to the detail of the data model.

The header comments in ../python/ccpncore/memops/metamodel/MetaModel.py give a
detailed description of the 'business rules' for the model.  
The header comments in ../python/ccpncore/memops/scripts/ObjectDomain.py give details
for how to enter things in ObjectDomain, where this is different from the
MetaModel.  
Both comments are generally up to date.

tha API and related documentation is regenerated after a model change by
running the ccpncore/memops.scripts/malePython.py file.