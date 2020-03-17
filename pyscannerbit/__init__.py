import sys
import os
import ctypes

sys.setdlopenflags(sys.getdlopenflags() | ctypes.RTLD_GLOBAL)
os.environ["GAMBIT_RUN_DIR"] = os.path.dirname(__file__)
modulename = 'datetime'
if "h5py" in sys.modules:
    print("import hdf5 after importing pyscannerbit")
    exit(-1)
