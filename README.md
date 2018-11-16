pip package setup for pyscannerbit
---

This is a little complicated because we first have to build the standalone
version of ScannerBit. I think the best way to do this is to manually create
the ScannerBit standalone tarball and copy it here, then let setup.py
try to run its cmake stuff. I guess there will be various missing dependencies
in general, but hopefully the cmake errors will tell users what they need
to install...
