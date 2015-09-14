"""Custom extensions to Sphinx documentation generator

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

import re

replaceInDocStrings = (
  ('ccpncore.lib.typing.',''),
  ('typing.', ''),
  # ('NoneType', 'None')
)

# Format for inserting class documentation in wrapper module
wrappedClassFormat= """

.. _%(moduleName)s-%(className)s-ref:

%(moduleName)s.%(className)s
%(underline)s

.. autoclass:: %(moduleName)s.%(className)s
"""

# Pattern for replacing (e.g.) 'ccpn._wrapper._Spectrum.Spectrum' with 'ccpn.Spectrum'
wrappedClassFullName = re.compile(
  "(ccpn|ccpnmr)[.](_wrapper[.]_(?P<classname>[a-zA-Z]+)[.])(?P=classname)"
)
optionalType = re.compile("Union\[(.+), *NoneType\]")

classRepresentation = re.compile("<class '(.*?)'>")

classesHeader = [
  '',
'Classes :',
'---------',
''
]


def autodoc_process_docstring():
  """Return a listener that will modify doc strings from their  Python annotations.
  If *what* is a sequence of strings, only docstrings of a type in *what* will be processed.

  In the first version it adds type and  modifiability annotation to properties"""
  def process(app, what_, name, obj, options, lines):
    """
    Emitted when autodoc has read and processed a docstring. lines is a list of strings - the lines of the processed docstring - that the event handler can modify in place to change what Sphinx puts into the output.
    Parameters:

        app - the Sphinx application object
        what - the type of the object which the docstring belongs to (one of "module", "class", "exception", "function", "method", "attribute")
        name - the fully qualified name of the object
        obj - the object itself
        options - the options given to the directive: an object with attributes inherited_members, undoc_members, show_inheritance and noindex that are true if the flag option of same name was given to the auto directive
        lines - the lines of the docstring, see above
    """

    # # TEMP DEBUG
    # return

    if isinstance(obj, property):
      if not (lines and lines[0].startswith('- ')):
        if hasattr(obj.fget, '__annotations__'):
          # Necessary because functools.partial objects do note have __annotations__ attribute
          typ =repr(obj.fget.__annotations__.get('return'))
          typ = optionalType.sub(r'\g<1>=None',typ)
          for fromText, toText in replaceInDocStrings:
            typ = typ.replace(fromText, toText)
          ll = []
          if typ:
            ll.append("*%s*" % typ)
          if bool(obj.fset):
            # property is modifiable, add it to doc string
            ll.append('*settable*')
          if ll:
            #lines[:0] = [', '.join(ll) + '\n', '\n']
            lines[:0] = ['\- %s - ' % ', '.join(ll)]

    elif what_ == 'module' and hasattr(obj, '_sphinxWrappedClasses'):
      lines.extend(classesHeader)
      for cls in obj._sphinxWrappedClasses:
        tag = cls.__name__
        name = obj.__name__
        text = wrappedClassFormat % {'className':tag, 'moduleName':name,
                                     'underline':'^'*(len(tag)+len(name)+1)}
        lines.extend(text.splitlines())

    # Change wrapped class names to shorter form,
    for ii,line in enumerate(lines):
      # removing '_wrapper._ClassName'
      lines[ii] = wrappedClassFullName.sub(r'\g<1>.\g<3>',line)
      lines[ii] = classRepresentation.sub(r'\g<1>', lines[ii])

  #
  return process

def autodoc_process_signature():
  """Return a listener that will modify doc strings from their  Python annotations.
  If *what* is a sequence of strings, only docstrings of a type in *what* will be processed.

  In the first version it adds type and  modifiability annotation to properties"""
  def process(app, what, name, obj, options, signature, return_annotation):
    """Emitted when autodoc has formatted a signature for an object. The event handler can return a
    new tuple (signature, return_annotation) to change what Sphinx puts into the output.

    Parameters:
    -app – the Sphinx application object
    -what – the type of the object which the docstring belongs to
      (one of "module", "class", "exception", "function", "method", "attribute")
    -name – the fully qualified name of the object
    -obj – the object itself
    -options – the options given to the directive: an object with attributes inherited_members,
      undoc_members, show_inheritance and noindex that are true if the flag option of same name was
      given to the auto directive
    -signature – function signature, as a string of the form "(parameter_1, parameter_2)", or
      None if introspection didn’t succeed and signature wasn’t specified in the directive.
    -return_annotation – function return annotation as a string of the form " -> annotation",
      or None if there is no return annotation
    """

    if signature:
      signature = wrappedClassFullName.sub(r'\g<1>.\g<3>', signature)
      signature = classRepresentation.sub(r'\g<1>', signature)
      for fromText, toText in replaceInDocStrings:
        signature = signature.replace(fromText, toText)
    if return_annotation:
      return_annotation = wrappedClassFullName.sub(r'\g<1>.\g<3>', return_annotation)
      return_annotation = classRepresentation.sub(r'\g<1>', return_annotation)
      for fromText, toText in replaceInDocStrings:
        return_annotation = return_annotation.replace(fromText, toText)

    return (signature, return_annotation)

  #
  return process
