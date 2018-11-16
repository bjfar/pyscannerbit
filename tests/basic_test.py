# --- pyscannerbit import
import sys
import ctypes
flags = sys.getdlopenflags()
sys.setdlopenflags(flags | ctypes.RTLD_GLOBAL)
import pyscannerbit.scan as sb

# ---

# Test function
def test(pars):
  x = pars["test_model::x"]
  y = pars["test_model::y"]
  z = pars["test_model::z"]
  #print "pars: ", x, y, z
  
  return -0.5*( (x-10)**2 + (y-15)**2 + (z+3)**2 ) # fitness function to maximise (log-likelihood)

# Scan setup
pars = {"test_model": {
         "x": 20,
         "y": {"range": [0, 5]},
         "z": {"range": [0, 5]},
        }
       } 

setup = { "Parameters": pars }

# Bit ugly, but only other choice is to just use a YAML file I think.
# Or could do it with a sequence of setup calls? E.g.
# sb.setup_printer("hdf5",output_file="pyresults.hdf5",group="/pyspartan",delete_file_on_restart=True)
# sb.setup_scanner("multinest",nlive=1000,tol=0.1)

# Maybe with some kind of helper class? Which we pack/unpack using the above functions? Then it
# can be re-used and passed around a bit more conveniently

# class ScannerBitSetup:
#     def __init__(self):
#         printer_options = None
#         scanner_options = None
# 
#     def setup_printer(self,name,**args):
#         printer_options = {"printer": name, "options": args}
# 
#     def setup_scanner(self,name,**args):
#         scanner_options = {"use_scanner": name, name: args}

# Ok I think that is nicest. But fundamentally, on the C++ side,
# we just have to parse the nested Python dictionaries. We can
# make it nicer on the Python side in various ways.

sb.py_run_scan(setup,test)


