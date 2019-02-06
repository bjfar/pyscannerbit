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

# Make sure -fPIC added when building subprojects like yaml-cpp
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Want any extra libraries built by dependencies (e.g. yaml-cpp) to end up
# in our package directory
#set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_SAVED ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
#set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/pyscannerbit")

# # Some stuff to make sure same version of python is used for this interface
# # and while building ScannerBit
# Check for Python interpreter
# We also need to search for PythonLibs before letting pybind11 look for them,
# otherwise it seems to get it wrong.  Also, we need to add versions of python
# greater than 3.3 manually, for compatibility with CMake 2.8.12.
set(Python_ADDITIONAL_VERSIONS 3.4 3.5 3.6 3.7)
if (FORCE_PYTHON2)
  message("${BoldYellow}   Python 2 requested; searching for Python 2.7${ColourReset}")
  find_package(PythonInterp 2.7 REQUIRED)
  find_package(PythonLibs ${PYTHON_VERSION_STRING} EXACT)
elseif (FORCE_PYTHON3)
  message("${BoldYellow}   Python 3 requested; searching for Python 3.x${ColourReset}")
  find_package(PythonInterp 3 REQUIRED)
  find_package(PythonLibs ${PYTHON_VERSION_STRING} EXACT)
else()
  find_package(PythonInterp 3)
  if(PYTHONINTERP_FOUND)
    find_package(PythonLibs 3)
  else()
    message("${BoldYellow}   Python 3 not found, searching for Python 2.7${ColourReset}")
    find_package(PythonInterp 2 REQUIRED)
    if (PYTHON_VERSION_MINOR LESS 7)
      message(FATAL_ERROR "\nGAMBIT requires Python 2.7.  \nIf you need to set the path to the Python interpreter manually, "
                          "please use -DPYTHON_EXECUTABLE:FILEPATH=path/to/preferred/python.")
    endif()
    find_package(PythonLibs 2)
  endif()
endif()

# Search for pybind11 and yaml-cpp installations
# If not found, use versions supplied with this package
# (TODO: Should probably add some version restrictions)
if(NOT USE_PYSB_YAML)
   find_package(yaml-cpp QUIET)
endif()

if(yaml-cpp_FOUND)
   message("   Found yaml-cpp")
   message("   libs are: ${YAML_CPP_INCLUDE_DIR}")
else()
   message("   yaml-cpp NOT found on system, using version included with pyScannerBit package")
   option(YAML_CPP_BUILD_TESTS "" OFF) # Disable building test suite
   option(YAML_CPP_BUILD_TOOLS "" OFF) # Disable building command line tools
   #option(BUILD_SHARED_LIBS "" ON) # Getting weird runtime errors using the static library; switch to shared.
   add_subdirectory("${PROJECT_SOURCE_DIR}/yaml-cpp")
   set(yaml_INCLUDE_DIR ${PROJECT_SOURCE_DIR}/yaml-cpp/include)
   include_directories("${yaml_INCLUDE_DIR}") # is this really necessary? Why not for pybind11? Seems needed though.
   set(USE_PYSB_YAML TRUE CACHE BOOL "Flag to skip find_package(yaml-cpp) and just use supplied version") # Store in cache so that we can avoid running find_package in later cmake runs (seems to spuriously 'find' yaml-cpp when it shouldn't, maybe due to cached targets imported via the add_subdirectory command? Not sure if CMake works like that or not)
endif()

find_package(pybind11 QUIET)
if(pybind11_FOUND)
   message("   Found pybind11 installation on system")
else()
   message("   pybind11 NOT found on system, using version included with pyScannerBit package")
   add_subdirectory("${PROJECT_SOURCE_DIR}/pybind11")
endif()

#find_package(ScannerBitCAPI REQUIRED)
# Get the ScannerBitCAPI target directly from subproject?

# Generate Python module
message("Extension module source: ${PROJECT_SOURCE_DIR}/src/pyScannerBit.cpp")
pybind11_add_module(_interface "${PROJECT_SOURCE_DIR}/src/pyScannerBit.cpp")
# set_target_properties(_interface PROPERTIES OUTPUT_NAME pyscannerbit/_interface)

#--- New experimental insertion
# Want to try and build and link ScannerBitCAPI directly from here, rather
# than build it separately. Let's see if this can be done easily or not...
set(GAMBIT_DIR "${PROJECT_SOURCE_DIR}/pyscannerbit/scannerbit/untar/ScannerBit")
set(GAMBIT_RUN_DIR "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}") # Final package installation path
#set(LIB_DIR "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/pyscannerbit") # Temporary build path (unused?)

message("Setting GAMBIT_RUN_DIR to: ${GAMBIT_RUN_DIR}")
add_subdirectory("${GAMBIT_DIR}")
#--- End experimental stuff

add_dependencies(_interface yaml-cpp pybind11 ScannerBitCAPI)
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
set(MULTINEST_VERSION 3.11)
set(POLYCHORD_VERSION 1.15)
set(DIVER_VERSION 1.0.4)

# Multinest
copy_file(${GAMBIT_DIR}/ScannerBit/installed/multinest/${MULTINEST_VERSION}/libnest3.so
          ${GAMBIT_RUN_DIR}/ScannerBit/installed/multinest/${MULTINEST_VERSION})

# Polychord
copy_file(${GAMBIT_DIR}/ScannerBit/installed/polychord/${POLYCHORD_VERSION}/lib/libchord.so
          ${GAMBIT_RUN_DIR}/ScannerBit/installed/polychord/${POLYCHORD_VERSION}/lib)

# Diver
copy_file(${GAMBIT_DIR}/ScannerBit/installed/diver/${DIVER_VERSION}/lib/libdiver.so
          ${GAMBIT_RUN_DIR}/ScannerBit/installed/diver/${DIVER_VERSION}/lib)

# Leaving GreAT out on purpose since it needs ROOT and that is just too painful to deal with.
