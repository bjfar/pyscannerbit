_default_options = {
"Printer": {
  "printer": "hdf5",
  "options": {
    "output_file": "results.hdf5",
    "group": "/",
    "delete_file_on_restart": True,
    }
  },
"Scanner": {
  "use_scanner": "multinest",
  "scanners": {
    "de": {
      "plugin": "diver",
      "like": "LogLike",
      "NP": 1000,
      },
    "multinest": {
      "plugin": "multinest",
      "like":  "LogLike",
      "nlive": 1000,
      "tol": 0.1,
      }
    }
  },
"KeyValues": {
  "default_output_path": "pyscannerbit_run_data/unnamed_run",
  "rng": "ranlux48",
  "likelihood": {
    "model_invalid_for_lnlike_below": -1e6
    }
  }
}

