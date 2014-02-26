import string
import types

# Python 2.1 dual-use constants
try:
  IntType = types.IntType
  StringType = types.StringType
  TupleType = types.TupleType
except AttributeError:
  IntType = int
  StringType = str
  TupleType = tuple

# General constants

class DummyClass:
  pass
sentinel = DummyClass()


# Errors - must be here to avoid circular import problem from Util/MetaModel
class MemopsError(Exception):
  """ Base class for all Memops Errors
  """
  # TODO reorganise error system
  pass


trueString = 'True'
falseString = 'False'

# Special constants
infinity = -1



# Directory names for Python code api subdirectories
apiCodeDir = 'api'

# Directory names for Python code xml subdirectories
xmlCodeDir = 'xml'


# names of basic data types
int_code = 'Int'
float_code = 'Float'
string_code = 'String'
boolean_code = 'Boolean'
datetime_code = 'DateTime'
dict_code = 'Dict'
typeCode_enumeration = [int_code, float_code,
 string_code, boolean_code, datetime_code, dict_code,
]
typeCode_enumeration.sort()

baseDataTypeModule = __import__(
 'ccpncore.memops.baseDataTypes', globals(), locals(), typeCode_enumeration
)

# NBNB TBD the codes for 'Dict and List are short-term hacks

# names of jdbc data types.
# jdbcTypeCode_enumeration = [
#  'CLOB', 'VARCHAR', 'BIT', 'INTEGER', 'BIGINT', 'FLOAT', 'DOUBLE', 'TIMESTAMP',
#  'Dict','List'
# ]
# jdbcTypeCode_enumeration.sort()

# names of java data types.
javaTypeCode_enumeration = ['java.lang.Integer',
'java.lang.Float','java.lang.String','java.lang.Boolean',
'java.util.Map', 'java.util.Collection'
]
javaTypeCode_enumeration.sort()

# names of java simple data types.
# NB the simpleType for strings is the empty string
javaSimpleTypeCode_enumeration = [
# TBD: is excluding None (which is not allowed in Python 3 because of sort()) a problem?
# 'int','long','float','double','boolean', None
 'int,''float','boolean'
]
javaSimpleTypeCode_enumeration.sort()

# names of xml data types.
xmlTypeCode_enumeration = ['string', 'boolean', 'int', 'float', 'Dict','List']
xmlTypeCode_enumeration.sort()

# dictionary of all typeCodes and their enumeration, to simplify processing
typeCodes = {
 'typeCode':typeCode_enumeration,
 # 'jdbcTypeCode':jdbcTypeCode_enumeration,
 # 'javaTypeCode':javaTypeCode_enumeration,
 # 'javaSimpleTypeCode':javaSimpleTypeCode_enumeration,
 'xmlTypeCode':xmlTypeCode_enumeration
}


# MetaModel constants

# visibility enumeration
public_visibility = 'public_vis'
protected_visibility = 'protected_vis'
private_visibility = 'private_vis'
visibility_enumeration = ( public_visibility, protected_visibility,
 private_visibility
)

# scope enumeration
instance_level = 'instance_level'
classifier_level = 'classifier_level'
scope_enumeration = (instance_level, classifier_level)

# aggregation enumeration
no_aggregation = None
composite_aggregation = 'composite'
aggregation_enumeration = ( no_aggregation, composite_aggregation )

# direction enumeration
in_direction = 'in_dir'
out_direction = 'out_dir'
inout_direction = 'inout_dir'
return_direction = 'return_dir'
direction_enumeration = ( in_direction, out_direction, inout_direction, 
 return_direction
)

# changeability enumeration
changeable = 'changeable'
frozen = 'frozen'
add_only = 'add_only'
changeability_enumeration = (changeable, frozen, add_only)

# role hierarchy enumeration
parent_hierarchy = 'parent'
child_hierarchy = 'child'
no_hierarchy = None
hierarchy_enumeration = ( parent_hierarchy, child_hierarchy, no_hierarchy )


# valid characters for names. 
# NB avoiding string.ascii_xxx attributes 
#    as we need 2.1 compatibility for ObjectDomain
lowercase = "abcdefghijklmnopqrstuvwxyz"
uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
underscore = "_"
validNameChars = uppercase + lowercase + string.digits + underscore

# Putting this in a single string is incompatible with Emacs python mode 
# (wish they would fix it)
xmlDisallowedChars = "&'<>" + '"'


# tags for 'code' dictionaries, 
# with code for different languages/implementations
codeStubTags = ('python', 'java', 'xml')

# maximum length of various names.
maxTagLength = 32
maxClassNameLength = 32
maxShortNameLength = 4

# names of attributes with special treatment:
serial_attribute = 'serial'
serialdict_attribute = 'serialDict'
details_attribute = 'details'
timestamp_attribute = 'timestamp'
guid_attribute = 'guid'
           
# Implementation directory, file, and class names:
rootPackageDirName = 'RootPackage'
modellingPackageName = 'memops'
implementationPackageName = 'Implementation'
rootPackageName = 'Root'

dataRootName = 'MemopsRoot'
baseClassName = 'MemopsObject'
rootClassName = 'ComplexDataType'
topObjClassName = 'TopObject'
dataObjClassName = 'DataObject'
implObjClassName = 'ImplementationObject'
baseDataTypeObjName = 'MemopsDataTypeObject'

repositoryRole = 'repositories'
packageLocatorRole = 'packageLocators'

implementationClassNames = [dataRootName, baseClassName, topObjClassName,
                            dataObjClassName, implObjClassName,]

#############################################################################
# NBNB TBD Old, possibly obsolete:

# # Implementation directory, file, and class names:
# imageDir = 'doc/graphics'
# docDir = 'doc'
