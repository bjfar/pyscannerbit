"""Python interface to ScannerBit library, from GAMBIT project"""

# Need to do a little voodoo so that dynamically loaded shared libraries
# can dynamically load other shared libraries (the scanner plugins)
import os
import sys
import ctypes
flags = sys.getdlopenflags()
sys.setdlopenflags(flags | ctypes.RTLD_GLOBAL)

from functools import partial
import inspect
import copy
import h5py

# Just doing this will initialise MPI, and it will automatically
# call 'finalize' upon exit. So we need do nothing except import this.
from mpi4py import MPI

# Need to tell ScannerBit where its config files are located
# We do this via a special environment variable
gambit_path = os.path.dirname(__file__)
print("Setting GAMBIT_RUN_DIR to:",gambit_path)
os.environ["GAMBIT_RUN_DIR"] = gambit_path

# Other python helper tools
from .defaults import _default_options
from .utils import _merge
from .hdf5_help import get_data, HDF5 
from .processify import processify

def _add_default_options(options):
   """Inspect user-supplied options, and fill in any missing
      bits with defaults"""
   _merge(options,_default_options)
   return options

@processify
def _run_scan(settings, loglike_func, prior_func):
   """Perform a scan. This function is decorated in such a 
      way that it runs in a new process. This is important
      because the GAMBIT plugins can only run once per
      process, because the shared libraries need to be reloaded
      to perform a second scan.
      """
   # Import functions from the ScannerBit.so library
   # Should also trigger the loading of the scanner plugin libraries
   from .ScannerBit.python import ScannerBit

   # Attach the ScannerBit object to the first argument of the wrapped likelihood function
   wrapped_loglike = partial(loglike_func,ScannerBit)

   # Create scan object
   myscan = ScannerBit.scan(True)
       
   # run scan
   # 'inifile' can be the name of a YAML file, or a dict.
   myscan.run(inifile=settings, lnlike={"LogLike": wrapped_loglike}, prior=prior_func, restart=True)
 
class Scan:
    """Helper object for setting up and running a scan, and
       making some basic plots.
    """
    def __init__(self, function, prior_func=None, bounds=None, prior_types=None, kwargs=None, scanner=None,
      settings={}, model_name=None, output_path=None, fargs=None):
        """
        function - Python function to be scanned
        prior_func - User-define prior transformation function (optional)
        bounds - list of ranges of parameter values (function arguments) to scan,
                 or mean/std-dev in case of normal prior.
        prior_types - list of priors to use for scanning in each dimension (e.g. flat/log).
                      If None then the user is expected to do the inverse transform from
                      a unit hypercube to their parameter space themselves.
        scanner - Scanning algorithm to use
        f_args - List of names of function argments to use (if None these are
         inferred from the signature of 'function')
        """
        self.function = function
        self.prior_func = prior_func
        self.ScannerBit = None # To contain ScannerBit interface module when run begins

        # Determine parameter names, either automatically or from 'fargs' argument
        if fargs is None:
            signature = inspect.getargspec(self.function)
            # First argument needs to be the 'scan' object, to allow access to printers etc. Skip it in determination of parameter names.
            self._argument_names = signature.args[1:]
        else:
            self._argument_names = fargs

        # Determine prior to be used
        self.bounds = bounds if bounds else [(0,1)] * len(self._argument_names)
        self.prior_types = prior_types if prior_types else ["flat"] * len(self._argument_names)
        self.scanner = scanner
        self.settings = _add_default_options(copy.deepcopy(settings))
        self.kwargs = kwargs

        print(self._argument_names)
        print(self.bounds)
        assert len(self._argument_names) == len(self.bounds)
 
        if model_name is None:
           if "Parameters" in self.settings:
              #print(self.settings["Parameters"])
              self._model_name = list(self.settings["Parameters"].keys())[0]
           else:
              self._model_name = "default"
        self._wrapped_function = self._wrap_function()
        self._scanned = False

        # Make up a name for the run, if user didn't provide one
        if output_path is None:
            self.settings["KeyValues"]["default_output_path"] += "{0}_scan".format(self.scanner)
        else:
            self.settings["KeyValues"]["default_output_path"] = output_path

        self._process_settings()
        self.loglike_par = "LogLike"
        self.scanner = self.settings["Scanner"]["use_scanner"] # Might have been None and then filled by _process_settings with defaults
        if self.scanner == "multinest" \
        or self.scanner == "polychord":
            self.posterior_par = "Posterior"
        else:
            self.posterior_par = None

    def _get_hdf5_group(self):
        """
        """
        assert self.settings["Printer"]["printer"] == "hdf5"
        file_name = self.settings["Printer"]["options"]["output_file"]
        group_name = self.settings["Printer"]["options"]["group"]
        DIR = self.settings["KeyValues"]["default_output_path"]
        fullpath = "{}/samples/{}".format(DIR, file_name)
        f = h5py.File(fullpath,'r')
        g = f[group_name]
        return g

    def _process_settings(self):
        """Copy 'pythonic' options into the settings dictionary
           so that they can be automaticall converted into YAML 
           by the API, which ScannerBit can then read"""
        if(self.scanner is not None):
            self.settings["Scanner"]["use_scanner"] = self.scanner
        if("Parameters" not in self.settings):
            self.settings["Parameters"] = dict()
            self.settings["Parameters"][self._model_name] = dict()
            for n in self._argument_names:
                # Just add parameter names. We will write the prior settings out fully
                # in the Priors section next
                self.settings["Parameters"][self._model_name][n] = None
        if("Priors" not in self.settings):
            self.settings["Priors"] = dict()
            if (self.prior_types is not None) \
               and (self.bounds is not None):
                for n, b, t in zip(self._argument_names, self.bounds, self.prior_types):
                    prior_setup = {'prior_type': t, 'parameters': ["{0}::{1}".format(self._model_name,n)]}
                    if t is 'gaussian' or t is 'cauchy':
                       prior_setup['mean'] = [b[0]]
                       prior_setup['cov']  = [b[1]] # Assume this is the VARIANCE, not standard deviation
                    else:
                       prior_setup['range'] = b
                    self.settings["Priors"]["{0}_prior".format(n)] = prior_setup
            else:
                raise ValueError("No prior settings found! These need to be either supplied in simplified form via the 'bounds' and 'prior_types' arguments, or else supplied in long form (following the GAMBIT YAML format) in the 'settings' dictionary under the 'Priors' key (or under the 'Parameters' key in the short-cut format)")
        #print(self.settings)

    def _wrap_function(self):
        """
        """
        def wrapped_function(par_dict):
            """
            """
            arguments = [par_dict["{}::{}".format(self._model_name, n)]
              for n in self._argument_names]
            return self.function(self.scan, *arguments, **(self.kwargs or {}))

        return wrapped_function

    def scan(self):
       """Perform a scan. This runs a function that is decorated in such a 
       way that it runs in a new process. This is important
       because the GAMBIT plugins can only run once per
       process, because the shared libraries need to be reloaded
       to perform a second scan.

       Downside is that all arguments must be pickle-able.
       """
       _run_scan(self.settings, self._wrap_function, self.prior_func)
       MPI.COMM_WORLD.Barrier()
       rank = MPI.COMM_WORLD.Get_rank()
       print("Rank {0} passed scan end barrier!".format(rank))
       self._scanned = True

    def get_hdf5(self):
        try:
            g = HDF5(self._get_hdf5_group().id,model=self._model_name,
                loglike=self.loglike_par, posterior=self.posterior_par)
        except:
            if(self._scanned):
                raise IOError("Failed to open HDF5 output of scan!")
            else:
                raise IOError("Failed to open HDF5 output of scan, however we did not perform a scan just now. The output will only exist if you have previously run this scan. Please check that you did this!")
        return g
