
import os
from apps.genapi import src

try:
    __path__.append(os.path.abspath(os.path.dirname(src.__file__)))
except ImportError:
    pass
