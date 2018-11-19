#!/bin/bash

# A simple script to grab the ScannerBit standalone tarball from GAMBIT,
# strip out some junk we don't need, and move it into the pyScannerBit
# package

GAMBIT_DIR=$1

echo "Grabbing ScannerBit tarball from $1/build..."
mkdir pyscannerbit/scannerbit/ScannerBit_TEMP_dir
tar -C pyscannerbit/scannerbit/ScannerBit_TEMP_dir -xf $GAMBIT_DIR/build/ScannerBit-1.1.3.tar --strip-components=1 

CONTRIB_DIR=pyscannerbit/scannerbit/ScannerBit_TEMP_dir/contrib/

echo "Stripping unnecessary contrib packages..."
rm -rf $CONTRIB_DIR/Delphes*  
rm -rf $CONTRIB_DIR/heputils     
rm -rf $CONTRIB_DIR/mcutils  
rm -rf $CONTRIB_DIR/pybind11      
rm -rf $CONTRIB_DIR/RestFrames*        
rm -rf $CONTRIB_DIR/slhaea
rm -rf $CONTRIB_DIR/fjcore*   
rm -rf $CONTRIB_DIR/MassSpectra  
rm -rf $CONTRIB_DIR/pyscannerbit  
rm -rf $CONTRIB_DIR/restframes*.tar.gz  
rm -rf $CONTRIB_DIR/yaml-cpp*

echo "Recreating tarball..."
rm pyscannerbit/scannerbit/ScannerBit_stripped.tar
tar -C pyscannerbit/scannerbit -cf pyscannerbit/scannerbit/ScannerBit_stripped.tar ScannerBit_TEMP_dir
echo "Deleting temporary files..."
rm -rf pyscannerbit/scannerbit/ScannerBit_TEMP_dir
echo "Done!"
