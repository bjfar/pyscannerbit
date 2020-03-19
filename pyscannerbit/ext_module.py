import sys
import ctypes

saved_flags = sys.getdlopenflags()
sys.setdlopenflags(saved_flags | ctypes.RTLD_GLOBAL)
from .ScannerBit.python import ScannerBit as sb
sys.setdlopenflags(saved_flags)
