
"""
autoimp -- Import all modules, load them lazily at first use.

Public domain, Connelly Barnes 2006-2015.  Works with Python 2.7, 3.3.

It can be tedious to import modules repeatedly at interactive Python prompts.
To solve this problem, one can now write:

  >>> from autoimp import *
  >>> os.stat('.')                     # Module loaded at first use.
  >>> Image.open('test.bmp')           # Module loaded at first use.
  >>> pylab.plot([1,2],[3,4])          # Module loaded at first use.
  >>> scipy.linalg.eig([[1,2],[3,4]])  # Module loaded at first use.
  >>> os.stat('..')                    # Module has already been
  >>> ...                              # imported -- subsequent uses
  >>>                                  # of os are fast.

The command "from autoimp import *" imports all modules found in
sys.path lazily.  This is done by placing lazy-import proxy objects
in the namespace of module autoimp.  The modules are actually loaded
when they are first used.  For ultimate laziness, place the command
"from autoimp import *" in your PYTHONSTARTUP file.  Now your
interactive session has all modules available by default.

One can also use "from autoimp import *" in Python source files.  This
is not recommended because it can result in more brittle code or be slow.

Auto-importing works on all of the packages which I tested (CGKit,
Numpy, Scipy, OpenGL, PIL, Pygame, ODE, scikit-image).

Note that the default behavior of "autoimp" is somewhat invasive: it
wraps all modules AND all sub-modules in the wrapper class
_LazyModule.  The benefit of this approach is that sub-modules are
lazily imported as well:

 >>> from autoimp import *
 >>> scipy.linalg
 >>> # Success

Finally, note that modules with leading underscores are not imported
(with the exception of __builtin__, __main__, and __future__), nor are
modules which have the same name as a builtin, such as "repr".  Also
reload() and help() are defined and exported by this module, so that
the these commands "do the right thing" when used with proxy import
objects.  The modified reload calls the __reload__() special method
on its argument (if available) and likewise for the help() function.

Submit bugs and patches to the GitHub project.

"""

__version__ = '1.0.3'
__all__ = ['reload']         # Lazily imported modules will go here

#TODO: .PY .pY .Py, various capitalizations of Python modules/packages.
#TODO: Test a whole lot on examples of lots of libraries.  Also test with
#      the Python lib unit tests.

# Use leading underscores on values used internally by this module so
# we don't get name conflicts with imported modules (which go in our
# globals() namespace).

import os as _os
import sys as _sys
import imp as _imp
import types as _types
try:
  import __builtin__ as _builtin
except ImportError:
  import builtins as _builtin
#from distutils.sysconfig import get_config_var as _get_config_var

# Modules with names of the form __name__ which are part of Python's lib.
_BUILTIN_SPECIAL_MODULES = '__builtin__ __main__ __future__'.split()

# Modules compiled or dynamically linked with Python binary (using
# _sys.builtin_module_names alone won't work, as 'math' may not be in
# here if math is dynamically linked, and searching sys.path also
# won't work, as this will find 'mathmodule' on Linux but not 'math').
_BUILTIN_COMPILED_MODULES = list(_sys.builtin_module_names) + """
  al array audioop binascii bsddb bz2 cd cmath cPickle crypt cStringIO
  datetime dbm dl errno fcntl fl fm fpectl functional gc gdbm gl grp
  imageop itertools linuxaudiodev math md5 mmap mpz nis operator
  ossaudiodev parser posix pcre pure pwd pyexpat readline regex
  resource rgbimg rotor select sgi sha256 sha512 sha shm signal socket
  spwd strop struct sunaudiodev sv symtable syslog termios thread time
  timing unicodedata xreadlines zipimport zlib
  """.split()

# Extensions known to be Python modules.
_PYTHON_EXTS = ['.py', '.pyc', '.pyo', '.pyw', '.pyd',
                '.dll', '.so', '.ppc.slb', '.carbon.slb', '.macho.slb']

_INIT_PY_NAMES = ['__init__.py', '__init__.pyc', '__init__.pyo']

class _RecursiveLazyModule:
  """
  Proxy class, imports modules and sub-modules automatically.
  """
  def __init__(self, modname, lib=None):
    self.__dict__['__name__'] = modname
    self.__set_lib(lib)

  def __set_lib(self, lib):
    # Set the self.__lib attribute to lib.
    if lib is not None:
      # Share __dict__ with the imported object.
      self.__dict__.update(lib.__dict__)
      self.__dict__['_autoimp_lib'] = lib
    else:
      self.__dict__['_autoimp_lib'] = None

  def __load_lib(self):
    # Load library if not yet loaded.
    self.__set_lib(__import__(self.__name__))

  def __reload__(self):
    if self.__dict__['_autoimp_lib'] is None:
      # If mod has not yet been imported, then only load mod once.
      self.__load_lib()
      return self
    else:
      _reload(self.__dict__['_autoimp_lib'])
      self.__set_lib(self.__dict__['_autoimp_lib'])
      return self

  def __help__(self):
    self.__load_lib()
    return _help(self.__dict__['_autoimp_lib'])

  def __getattr__(self, key):
    # Do the import.
    if self.__dict__['_autoimp_lib'] is None:
      self.__load_lib()

    lib = self.__dict__['_autoimp_lib']

    # Look up key, is it now found?
    if hasattr(lib, key):
      return getattr(lib, key)
    else:
      # Try importing a sub-module, wrapping it in a lazy import proxy.
      try:
        subname = '%s.%s' % (self.__name__, key)
        __import__(subname)
        sublib = getattr(lib, key)
      except ImportError:
        raise AttributeError("'module' object has no attribute %r" % key)
      self.__dict__[key] = _RecursiveLazyModule(subname, sublib)
      return self.__dict__[key]

  def __setattr__(self, key, value):
    # Import the module if user tries to set an attribute.
    if self.__dict__['_autoimp_lib'] is None:
      self.__load_lib()
    self.__dict__[key] = value

  def __call__(self, *args):
    raise TypeError("'module' object is not callable")


def _add_module_if_pymodule(L, path, modname, ext, zipnames=None):
  """
  Add module name to list L if it is a Python module.
  """
  mods = [modname]

  # For 'Xmodule.ext', trim off 'module' and import remaining name.
  if modname.lower().endswith('module'):
    mods.append(modname[:len(modname)-len('module')])

  for mod in mods:
    # Check if the file is clearly a Python source file.
    if ext in _PYTHON_EXTS:
      L.append(mod)
    else:
      if zipnames is None:
        modfull = _os.path.join(path, modname + ext)
        if _os.path.isdir(modfull):
          for init_py in _INIT_PY_NAMES:
            if _os.path.exists(_os.path.join(modfull, init_py)):
              L.append(mod)
              break
      else:
        for init_py in _INIT_PY_NAMES:
          if (modname + '/' + init_py in zipnames or
              modname + '\\' + init_py in zipnames):
            L.append(mod)
            break


if _sys.version_info[:2] >= (3, 0):
  _dir = dir
  def dir(obj):
    """
    Replacement for built-in dir().
    """
    try:
      obj.__load_lib()
    except:
      pass
    return _dir(obj)
  __all__.append('dir')

def _list_modules_in_path(path):
  """
  Return list of all modules in filesystem path.
  """
  ans = []
  for filename in _os.listdir(path):
    (pre, ext) = _os.path.splitext(filename)
    _add_module_if_pymodule(ans, path, pre, ext)
  return ans


def _list_modules_in_zip(zipname):
  """
  Return list of all modules in zip file with filename zipname.
  """
  import zipfile
  z = zipfile.ZipFile(zipname, 'r')
  zipnames = {}
  for filename in z.namelist():
    zipnames[filename] = None
  ans = []
  for filename in zipnames:
    filename = filename.rstrip('/').rstrip('\\')
    if '/' not in filename and '\\' not in filename:
      (pre, ext) = _os.path.splitext(filename)
      _add_module_if_pymodule(ans, zipname, pre, ext, zipnames)
  return ans


def _all_modules():
  """
  Return list of all module names to import, from sys.path.
  """
  ans = []
  for path in _sys.path:
    if path == '':
      path = _os.curdir
    if _os.path.isdir(path):
      ans.extend(_list_modules_in_path(path))
    elif (_os.path.splitext(path)[1].lower() == '.zip'
          and _os.path.exists(path)):
      ans.extend(_list_modules_in_zip(path))
    else:
      pass

  # Other modules compiled into the Python binary (for Python <= 2.5).
  extras = _sys.builtin_module_names
  tried = {}
  for x in ans:
    tried[x] = None
  for x in _BUILTIN_COMPILED_MODULES:
    if not x in tried:
      tried[x] = None
      try:
        _imp.find_module(x)
        ans.append(x)
      except ImportError:
        pass

  # Remove duplicates.
  d = {}
  for x in ans:
    d[x] = None
  return d.keys()


def _import_all():
  """
  Lazy import all modules found by _all_modules().
  """
  for mod in _all_modules():
    # Do not replace existing builtins, such as repr().
    if (not hasattr(_builtin, mod) and (not mod.startswith('_') or
        mod in _BUILTIN_SPECIAL_MODULES)):
      d = globals()
      d[mod] = _RecursiveLazyModule(mod)
      __all__.append(mod)


def _export_builtins():
  """
  Export all lazily imported modules to the __builtin__ namespace.
  """
  for k in __all__:
    setattr(_builtin, k, globals()[k])


try:
  _reload = reload
except:
  try:
    from importlib import reload as _reload
  except:
    from imp import reload as _reload

def reload(x):
  """
  Replacement for builtin reload() by autoimp.py.

  Reloads the module argument, and returns the reloaded module.  The
  module need not have been already imported.  If the argument has the
  special method __reload__(), then that method is called and its
  return value is returned by reload().
  """
  if hasattr(x, '__reload__'):
    return x.__reload__()
  else:
    return _reload(x)

if _sys.version_info[:2] >= (2, 2):
  _help = help
  __all__.append('help')

  def help(x):
    """
    Get help on the given object.
    """
    if hasattr(x, '__help__'):
      return x.__help__()
    else:
      return _help(x)

_import_all()


# -------------------------------------------------------------------
# Unit tests
# -------------------------------------------------------------------

def _require_importable(L):
  """
  Given a list of module names, make sure each one can be imported.
  """
  for x in L:
    exec("dir(" + x + ")")


def _require_not_importable(L):
  """
  Given a list of module names, make sure none can be imported.
  """
  for x in L:
    try:
      exec("dir(" + x + ")")
      ok = 0
    except NameError:
      ok = 1
    if not ok:
      raise ValueError


def _test_pythonlib():
  """
  Unit test for modules bundled with Python.
  """
  # Test out a few commands in the lazily imported modules.
  os.stat('.')
  assert os.path.os.path is os.path
#  assert isinstance(os.path.os.path.os.path.os, _RecursiveLazyModule)
#  assert isinstance(os.path.os.path.os.path.os.path, _RecursiveLazyModule)
  os.path.os.path.os.path.os.stat('.')
  assert operator.add(1, 2) == 3
  v = [1, 2]
  assert copy.copy(v) is not v and copy.copy(v) == v
  assert (xml.dom.minidom.parseString('<a>b</a>').documentElement.tagName
          == u'a')

  # Check that the appropriate modules can be lazily imported.
  L = """
  bisect cmath re random pickle stat os.path os socket zlib zipfile
  """.split()

  _require_importable(L)
  _require_not_importable("""dsfajsk zckaz askad.akjl akjlsd.dfjdf""".split())

  reload(os)
  reload(_os)

#  def f():
#    pass
#
#  global sys
#  sys.exitfunc = f
#  import sys
#  assert sys.exitfunc is f
  print('Unit tests passed')

def _test_thirdparty():
  """
  Test a few third party modules.
  """
  # CGKit
  assert cgkit.cgtypes.vec3(1,2,3) * 2 == cgkit.cgtypes.vec3(2,4,6)

  # Numpy
  assert numpy.sum(numpy.sum(abs(numpy.linalg.inv(numpy.array([[1,2],[3,4]])) -
                   numpy.array([[-2.0,1.0],[1.5,-0.5]])))) < 1e-10

  # Scipy
  assert numpy.sum(numpy.sum(abs(scipy.fftpack.convolve.convolve(
                   numpy.array([1.0,2]),numpy.array([5.0,6]))-
                   numpy.array([9.0,21])))) < 1e-10
  # OpenGL
  assert sum([abs(x) for x in OpenGL.quaternion.quaternion(1,2,3,4).conj() -
              OpenGL.quaternion.quaternion(1,-2,-3,-4)]) < 1e-10

  # PIL (Python Imaging Library)
  assert ImageColor.getrgb('#77FFAA') == (119, 255, 170)

  # Pygame
  assert pygame.Rect(1,2,3,4).move(5,6) == pygame.Rect(6,8,3,4)

  # ODE (Open Dynamics Engine)
  assert ode.World().getCFM() > 0.0


if __name__ == '__main__':
  _test_pythonlib()
#  _test_thirdparty()
