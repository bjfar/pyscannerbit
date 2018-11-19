pyScannerBit: A Python wrapper for the ScannerBit module of GAMBIT
===

INSTALLATION
---

### For developers, via git repository

In order to make sure everything will build properly when the installing
the package via PyPI repositories, it is best to do local test installations as
follows:
 
    python setup.py sdist
    pip install dist/pyscannerbit-0.0.1.tar.gz  

This creates the source distribution tarball that is uploaded to PyPI, and
performs the installation directly from that. Following this procedure means
that nothing will accidentally get left out of the distribution tarball. If
you need to add new files to it, add them to the `MANIFEST.in` file.

### For users

If you have downloaded the source from github then feel free to use
the developer installation instructions above. But you can also install this
package via PyPI:

    pip install pyscannerbit


Package structure
---

This information is mainly for developers, but it might be helpful to know this
if you are having installation trouble (though if this is the case please file
or check the bug reports at 

    https://github.com/bjfar/pyscannerbit/issues

This package is primarily a Python interface to a C API that is built by the
GAMBIT build system. This system in turn automatically downloads and build
various scanning algorithm libraries and turns them into plugins for ScannerBit.


GAMBIT-side modifications
---

If you modify anything on the GAMBIT side, those changes will need to be
manually imported into this package. This is done via the ScannerBit
standalone tarball. So in the GAMBIT source do

    cmake ..
    make standalone_tarballs

then from this package run the script `grab_ScannerBit.sh` as follows

    ./grab_ScannerBit.sh <GAMBIT_SOURCE_ROOT>

and it will strip out contrib packages that we don't need, and then copy
the stripped tarball into pyscannerbit/scannerbit.

NOTE! The GAMBIT version number is not automatically detected, so if
this changes it will need to be updated in the `grab_ScannerBit.sh` script.  
