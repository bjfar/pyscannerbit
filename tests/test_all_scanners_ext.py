"""Demo script which runs all the (serious) scanners to which pyScannerBit has access"""

import os
import numpy as np
import math
import matplotlib.pyplot as plt
import h5py
from pyscannerbit.hdf5_help import get_data, HDF5 
from pyscannerbit import ext_module as ext
from mpi4py import MPI
rank = MPI.COMM_WORLD.Get_rank()
size = MPI.COMM_WORLD.Get_size()

# Regenerate scan data?
new_scans = True

# Test function
def rastrigin(m):
    X = [m["model::x"],m["model::y"],m["model::z"]]
    A = 10
    return - (A + sum([(x**2 - A * np.cos(2 * math.pi * x)) for x in X]))

# Prior transformation from unit hypercube
def prior(vec, map):
    vec.ensure_size(3)
    map["model::x"] = -4 + 8*vec[0] # flat prior over [-4,4]
    map["model::y"] = -4 + 8*vec[1]
    map["model::z"] = -4 + 8*vec[2]

# Settings for quick and dirty scans. Won't do very well, because the test function is
# actually rather tough!
# Don't have to specify all scanner options; anything missing will revert to defaults (see defaults.py)
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
    "multinest": {"plugin": "multinest", "like": "LogLike", "tol": 0.5, "nlive": 100},
    "twalk": {"plugin": "twalk", "like": "LogLike", "sqrtR": 1.05},
    "polychord": {"plugin": "polychord", "like": "LogLike", "tol": 1.0, "nlive": 20},
    "diver": {"plugin": "diver", "like": "LogLike", "convthresh": 1e-2, "NP": 300}, 
    "random": {"plugin": "random", "like": "LogLike", "point_number": 10000},
    "toy_mcmc": {"plugin": "toy_mcmc", "like": "LogLike", "point_number": 10}, # Acceptance ratio is really bad with this scanner, so don't ask for much
    "badass": {"plugin": "badass", "like": "LogLike", "points": 1000, "jumps": 10},
    "pso": {"plugin": "pso", "like": "LogLike", "NP": 400}
    },    
  "use_scanner": "multinest",
  "objectives": {
    "gaussian": {
      "plugin": "gaussian",
      "purpose": "LogLike",
      "parameters": {
        "param...20": None,
        "range": [-5, 5]
        }
      }
    }
  },
"KeyValues": {
  "default_output_path": "pyscannerbit_run_data/",
  "likelihood": {
    "model_invalid_for_lnlike_below": -1e6
    }
  }
}
  
def _get_hdf5_group(settings):
    """
    """
    assert settings["Printer"]["printer"] == "hdf5"
    file_name = settings["Printer"]["options"]["output_file"]
    group_name = settings["Printer"]["options"]["group"]
    DIR = settings["KeyValues"]["default_output_path"]
    fullpath = "{}/samples/{}".format(DIR, file_name)
    f = h5py.File(fullpath,'r')
    g = f[group_name]
    return g

def get_hdf5(settings):
    
    loglike_par = "LogLike"
    scanner = settings["Scanner"]["use_scanner"] # Might have been None and then filled by _process_settings with defaults
    if scanner == "multinest" or scanner == "polychord":
        posterior_par = "Posterior"
    elif scanner == "twalk":
        posterior_par = "mult"
    else:
        posterior_par = None
    g = HDF5(_get_hdf5_group(settings).id,model="model",
                loglike=loglike_par, posterior=posterior_par)
    return g

def rm_samples(settings):
    file_name = settings["Printer"]["options"]["output_file"]
    DIR = settings["KeyValues"]["default_output_path"]
    fullpath = "{}/samples/{}".format(DIR, file_name)
    try:
        os.remove(fullpath)
    except:
        print("No such file: " + fullpath)


scanners = ["multinest","polychord","diver","twalk"]
#colors = ["r","m","b","g"]
#scanners = ["twalk","badass","pso"]
colors = ["r","b","g"]
if size is 1:
    scanners += ["random","toy_mcmc"] # "random" and "toy_mcmc" seem to not be MPI compatible. Should make GAMBIT throw an error about this, or fix them.
    colors += ["c","y"]

# Test just one scanner
#scanners = ["pso"]
#colors = ["r"]

Nscans = len(scanners)
results = {}

# Do all scans
for s in scanners:
    # Create scan manager object
    # (prior_types argument currently does nothing)
    # myscan = sb.Scan(rastrigin, prior_func=prior, scanner=s, scanner_options=scanner_options[s])
    rm_samples(settings)
    myscan = ext.sb.scan(False)
    settings["Scanner"]["use_scanner"] = s
    if new_scans:
        print("Running scan with {}".format(s))
        myscan.run(inifile=settings, lnlike={"LogLike": rastrigin}, prior=prior, restart=True)
    else:
        print("Retrieving results from previous {} scan".format(s)) 
    results[s] = get_hdf5(settings)
        
# Plot results
# Only want to do this on one process
if rank is 0:
    fig = plt.figure(figsize=(4*Nscans,8))
    for i,(s,c) in enumerate(zip(scanners,colors)):
        x,y = results[s].get_params(["x","y"])
        ax = fig.add_subplot(2,Nscans,i+1)
        ax.set_title("{0} (N={1})".format(s,len(x)))
        ax.scatter(x,y,c=c,label=s,s=0.5)
        ax = fig.add_subplot(2,Nscans,i+1+Nscans)
        results[s].plot_profile_likelihood(ax,"x","y") 
    
    ax.legend(loc=1, frameon=True, framealpha=1, prop={'size':10}) 
    plt.tight_layout()
    fig.savefig("test_all_scanners.png")
