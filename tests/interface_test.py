import sys
import ctypes

flags = sys.getdlopenflags()
sys.setdlopenflags(flags | ctypes.RTLD_GLOBAL)

# Dig past the extra python wrapping to the direct ScannerBit.so shared library interface level
import pyscannerbit.scan as sb
from pyscannerbit.ScannerBit.python import ScannerBit

# define likelihood, technically optional
def like(m):
    a = m["model1::x"]
    ScannerBit.print("my_param", 0.5) # can print custom parameters 

    return -a*a/2.0

# Version where ScannerBit interface is passed through via the wrapper
# (needed to allow multiple scans per python session)
def like2(scan,m):
    a = m["model1::x"]
    scan.print("my_param", 0.5) # can print custom parameters 
    return -a*a/2.0


# define prior, optional
def prior(vec, map):
    # tell ScannerBit that the hypergrid dimension is 1
    ScannerBit.ensure_size(vec, 1) # this needs to be the first line!

    map["model1::x"] = 5.0 - 10.0*vec[0]

# declare scan object
myscan = ScannerBit.scan(True)

settings = {
"Parameters": {
  "model1": {
    "x": None,
    }
  },
"Priors": {
  "x_prior": {
    "prior_type": 'flat',
    "parameters": ['model1::x'],
    "range": [1.0, 40.0],
    }
  },
"Printer": {
  "printer": "hdf5",
  "options": {
    "output_file": "results.hdf5",
    "group": "/",
    "delete_file_on_restart": "true",
    }
  },
"Scanner": {
  "scanners": {
    "twalk": {
      "plugin": "twalk",
      "like": "LogLike",
      "tolerance": 1.003,
      "kwalk_ratio": 0.9,
      "projection_dimension": 4
      }
    },
  "use_scanner": "twalk",
  },
"KeyValues": {
  "default_output_path": "pyscannerbit_run_data/",
  "likelihood": {
    "model_invalid_for_lnlike_below": -1e6
    }
  }
}

myscan.run(inifile=settings, lnlike={"LogLike": like}, prior=prior, restart=True)

# Try via wrapper to the above interface:
#sb._run_scan(settings, like2, prior)

#Try without prior
#sb._run_scan(settings, like2, "") # Fails!

# Try with dummy prior
def dummy_prior(vec, map):
    pass
 
#sb._run_scan(settings, like2, dummy_prior)




