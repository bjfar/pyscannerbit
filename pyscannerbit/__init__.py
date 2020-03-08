import sys
import os
import ctypes

sys.setdlopenflags(sys.getdlopenflags() | ctypes.RTLD_GLOBAL)
os.environ["GAMBIT_RUN_DIR"] = os.path.dirname(__file__)
