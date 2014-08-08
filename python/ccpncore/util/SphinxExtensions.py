"""Custom extensions to Sphinx documentation generator"""

__author__ = 'rhf22'

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

    if isinstance(obj, property):
      if not (lines and lines[0].startswith('Type:')):
        if hasattr(obj.fget, '__annotations__'):
          # Necessary because functools.patrial objects do note have __annotations__ attribute
          typ = obj.fget.__annotations__.get('return')
          ll = []
          if typ:
            # type is given, add it to doc string
            ll.append("Type: *%s*" % typ.__name__)
          if bool(obj.fset):
            # property is modifiable, add it to doc string
            ll.append('*settable*')
          if ll:
            lines[:0] = [', '.join(ll) + '\n', '\n']

  #
  return process
