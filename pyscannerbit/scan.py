"""Python interface to ScannerBit library, from GAMBIT project"""

# Need to do a little voodoo so that dynamically loaded shared libraries
# can dynamically load other shared libraries (the scanner plugins)
import sys
import ctypes
flags = sys.getdlopenflags()
sys.setdlopenflags(flags | ctypes.RTLD_GLOBAL)

import inspect
import h5py

# Import functions from the pybind11-created interface to ScannerBitCAPI
from ._interface import hello, run_scan

# Other python helper tools
from .defaults import _default_options
from .utils import _merge
from .hdf5_help import get_data, HDF5 

def _add_default_options(options):
   """Inspect user-supplied options, and fill in any missing
      bits with defaults"""
   _merge(options,_default_options)
   return options

class Scan:
    """Helper object for setting up and running a scan, and
       making some basic plots.
    """
    def __init__(self, function, bounds, prior_types, kwargs=None, scanner=None,
      settings={}, model_name=None):
        """
        """
        self.function = function
        self.bounds = bounds # or mean/std-dev in case of normal prior
        self.prior_types = prior_types if prior_types else ["flat"] * len(bounds)
        self.scanner = scanner
        self.settings = _add_default_options(settings)
        self.kwargs = kwargs

        signature = inspect.getargspec(self.function)
        n_kwargs = len(signature.defaults or [])
        self._argument_names = signature.args[:-n_kwargs or None]
        assert len(self._argument_names) == len(self.bounds)
 
        if model_name is None:
           if "Parameters" in self.settings:
              self._model_name = self.settings["Parameters"].keys()[0]
           else:
              self._model_name = "default"
        self._wrapped_function = self._wrap_function()
        self._scanned = False

        self._process_settings()
        self.loglike_par = "LogLike"
        self.scanner = self.settings["Scanner"]["use_scanner"] # Might have been None and then filled by _process_settings with defaults
        if self.scanner == "multinest":
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
            for n, in self._argument_names:
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
        print(self.settings)

    def _wrap_function(self):
        """
        """
        def wrapped_function(par_dict):
            """
            """
            arguments = [par_dict["{}::{}".format(self._model_name, n)]
              for n in self._argument_names]
            return self.function(*arguments, **(self.kwargs or {}))

        return wrapped_function

    def scan(self):
        """
        """
        run_scan(self.settings, self._wrapped_function)
        self._scanned = True

    def get_hdf5(self):
        assert self._scanned
        return HDF5(self._get_hdf5_group().id,model=self._model_name,
          loglike=self.loglike_par, posterior=self.posterior_par)
 
