.. _quick start:

Quick Start
============

We are currently working on a nice, feature-filled interface that also helps you access the scan output and create plots and other fun stuff, but for now you should run ScannerBit via the following bare-bones interface. First, some preliminay setup stuff to help than scanner plugin libraries load correctly::

    import sys
    import ctypes
    flags = sys.getdlopenflags()
    sys.setdlopenflags(flags | ctypes.RTLD_GLOBAL)

Next import the 'bare-bones' interface from a few levels down in the package::

    # Dig past the extra python wrapping to the direct ScannerBit.so shared library interface level
    from pyscannerbit.ScannerBit.python import ScannerBit
 
Define the log-likelihood function you wish to scan, and (if desired) a prior transformation function::

    def loglike(m):
        a = m["model1::x"]
        ScannerBit.print("my_param", 0.5) # Send extra data to the output file at each point 
        return -a*a/2.0

    def prior(vec, map):
        # tell ScannerBit that the hypergrid dimension is 1
        ScannerBit.ensure_size(vec, 1) # this needs to be the first line!
        map["model1::x"] = 5.0 - 10.0*vec[0]

If you want to tell ScannerBit to handle the prior transformation itself via the scan settings then just set a dummy function for the prior (NOTE! Turns out this doesn't work either. For now you must manually specify the prior transformation as above. Whatever you set in the settings below will do nothing, and the dummy prior will just return a null transformation and an error)::

    def dummy_prior(vec, map):
        pass

Generate a settings dictionary. The structure of this should match the YAML format required by ScannerBit when run via GAMBIT (this is one thing that we will simplify in the nice wrapper....)::

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
      },
    "KeyValues": {
      "default_output_path": "pyscannerbit_run_data/",
      "likelihood": {
        "model_invalid_for_lnlike_below": -1e6
        }
      } 
    }

Run your scan!::

    myscan = ScannerBit.scan(True)
    myscan.run(inifile=settings, lnlike={"LogLike": like}, prior=prior, restart=True)

If all went well, your scan should begin, and generate HDF5 format output in :code:`pyscannerbit_run_data/samples/results.hdf5`.

Known problems:

There are many! But to list a couple:
 1. You need to get the format of the settings correct or you'll get a cryptic error.
 2. You must supply a 'prior' function always. Use a dummy one as shown above if you don't need it.
 3. External scanners (e.g. MultiNest, PolyChord, Diver) are currently broken due to some gnarly RPATH issues. We are working on this! For now stick to Twalk and J-swarm.
 
