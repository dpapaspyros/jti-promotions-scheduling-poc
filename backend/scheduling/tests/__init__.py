import os as _os

# On Windows, os.path.abspath preserves the cwd's case (e.g. C:\users\...)
# while the filesystem reports C:\Users\... — unittest's discover compares
# these and raises ImportError on a mismatch.  Normalising __path__ here
# ensures the package path and discover's expected path share the same case.
__path__ = [_os.path.normcase(_os.path.abspath(_os.path.dirname(__file__)))]
del _os
