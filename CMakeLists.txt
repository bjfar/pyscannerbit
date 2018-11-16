# GAMBIT: Global and Modular BSM Inference Tool
#************************************************
# \file
#
#  CMake configuration script for building
#  the python interface to ScannerBit
#
#************************************************
#
#  Authors (add name and date if you modify):
#
#  \author Ben Farmer
#          (ben.farmer@gmail.com)
#  \date 2017 Nov
#
#************************************************

# Require a minimum cmake version of 2.8.5
cmake_minimum_required(VERSION 2.8.5 FATAL_ERROR)
project(pyscannerbit)

# # Some stuff to make sure same version of python is used for this interface
# # and while building ScannerBit
# find_package(PythonInterp 3)
# if(PythonInterp_FOUND)
#    find_package(PythonLibs 3 REQUIRED)
# else()
#     message("${BoldYellow}   Python 3 not found, searching for Python 2.7${ColourReset}")
#     find_package(PythonInterp 2 REQUIRED)
#     if (PYTHON_VERSION_MAJOR GREATER 2 OR PYTHON_VERSION_MINOR LESS 7)
#       message(FATAL_ERROR "\nGAMBIT requires Python 2.7 or greater.  \nIf you need to set the path to the Python interpreter manually, "
#                           "please use -DPYTHON_EXECUTABLE:FILEPATH=path/to/preferred/python.")
#     endif()
#     find_package(PythonLibs 2 REQUIRED)
# endif()

# Search for pybind11 and yaml-cpp installations
# If not found, use versions supplied with this package
find_package(yaml-cpp REQUIRED)
#find_package(pybind11 REQUIRED)
add_subdirectory("${PROJECT_SOURCE_DIR}/pybind11")


#find_package(ScannerBitCAPI REQUIRED)
# Get the ScannerBitCAPI target directly from subproject?

# Generate Python module
message("Extension module source: ${PROJECT_SOURCE_DIR}/src/pyScannerBit.cpp")
pybind11_add_module(_interface "${PROJECT_SOURCE_DIR}/src/pyScannerBit.cpp")
set_target_properties(_interface PROPERTIES OUTPUT_NAME pyscannerbit/_interface)

#--- New experimental insertion
# Want to try and build and link ScannerBitCAPI directly from here, rather
# than build it separately. Let's see if this can be done easily or not...
set(GAMBIT_DIR "${PROJECT_SOURCE_DIR}/pyscannerbit/scannerbit/untar/ScannerBit")
set(GAMBIT_RUN_DIR "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}") # Final package installation path
#set(LIB_DIR "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/pyscannerbit") # Temporary build path (unused?)

message("Setting GAMBIT_RUN_DIR to: ${GAMBIT_RUN_DIR}")

# Want to change the library output path for this part of the build:
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_SAVED ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/pyscannerbit")
add_subdirectory("${GAMBIT_DIR}")
# Revert library output path to what it was
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_LIBRARY_OUTPUT_DIRECTORY_SAVED})
#--- End experimental stuff

add_dependencies(_interface ScannerBitCAPI)
target_link_libraries(_interface PRIVATE yaml-cpp ScannerBitCAPI)

#--- Post-build copying
# Ok the build seems to be working, but now I need to copy all the scanner stuff
# into the final python package install directory.
# There might be a "cleaner" CMake way to do this... I will do it this "dumb"
# way for now.

# Copies stuff after _interface target is built
function(copy_file in out)
   message("Generating post-build instructions to copy ${in} to ${out}")
   add_custom_command(
        TARGET _interface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E echo "Copying ${in} to ${out}...")
   add_custom_command(
        TARGET _interface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory ${out})
   add_custom_command(
        TARGET _interface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy ${in} ${out})
endfunction(copy_file)

function(copy_dir in out)
   message("Generating post-build instructions to copy ${in} to ${out}")
   add_custom_command(
        TARGET _interface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E echo "Copying ${in} to ${out}...")
   add_custom_command(
        TARGET _interface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory ${out})
   add_custom_command(
        TARGET _interface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory ${in} ${out})
endfunction(copy_dir)
  
# Copy the scanner plugins directory
copy_dir(${GAMBIT_DIR}/ScannerBit/lib
         ${GAMBIT_RUN_DIR}/ScannerBit/lib)

# Copy the GAMBIT scratch directory (contains some config files that scannerbit reads)
copy_dir(${GAMBIT_DIR}/scratch
         ${GAMBIT_RUN_DIR}/scratch)

# Copy each of the scanner 'backend' shared libraries
copy_file(${GAMBIT_DIR}/ScannerBit/installed/multinest/3.10/libnest3.so
          ${GAMBIT_RUN_DIR}/ScannerBit/installed/multinest/3.10) 


