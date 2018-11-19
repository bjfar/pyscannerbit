import os
import re
import sys
import sysconfig
import platform
import subprocess
import pathlib

from distutils.version import LooseVersion
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as build_ext_orig

# Need to detect path that package will be installed into
# so that we can add it to various rpaths
# from https://stackoverflow.com/a/36205159/1447953 
def binaries_directory():
    """Return the installation directory, or None"""
    if '--user' in sys.argv:
        paths = (site.getusersitepackages(),)
    else:
        py_version = '%s.%s' % (sys.version_info[0], sys.version_info[1])
        paths = (s % (py_version) for s in (
            sys.prefix + '/lib/python%s/dist-packages/',
            sys.prefix + '/lib/python%s/site-packages/',
            sys.prefix + '/local/lib/python%s/dist-packages/',
            sys.prefix + '/local/lib/python%s/site-packages/',
            '/Library/Python/%s/site-packages/',
        ))

    for path in paths:
        if os.path.exists(path):
            return path
    print('no installation path found', file=sys.stderr)
    return None
installation_path = binaries_directory() + 'pyscannerbit'
print("Installation path: {0}".format(installation_path))

class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)

class CMakeBuild(build_ext_orig):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            raise RuntimeError("Sorry, pyScannerBit doesn't work on Windows platforms. Please use Linux or OSX.")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable,
                      '-DCMAKE_VERBOSE_MAKEFILE:BOOL=OFF',
                      '-Wno-dev',
                      '-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=' + installation_path,
                      '-DSCANNERBIT_STANDALONE=True',
                      '-DCMAKE_INSTALL_RPATH=' + installation_path,
                      '-DCMAKE_BUILD_WITH_INSTALL_RPATH:BOOL=ON',
                      '-DCMAKE_INSTALL_RPATH_USE_LINK_PATH:BOOL=ON',
                      '-DCMAKE_INSTALL_PREFIX:PATH=' + installation_path,
                     ]
                 #    '-DPYBIND11_PYTHON_VERSION=3.6',
                 #]


        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j2']

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())

       
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        # Debugging paths
        print("Debugging paths:")
        subprocess.check_call(['pwd'], cwd=self.build_temp, env=env)
        subprocess.check_call(['echo',self.build_temp], cwd=self.build_temp, env=env)
        # cwd = pathlib.Path().absolute()
        # print("ext.sourcedir:")
        # subprocess.check_call(['echo', ext.sourcedir], cwd=self.build_temp, env=env)
        # subprocess.check_call(['echo',cwd], cwd=self.build_temp, env=env) 
        subprocess.check_call(['ls', ext.sourcedir], cwd=self.build_temp, env=env)
        subprocess.check_call(['ls', ext.sourcedir+'/pyscannerbit/scannerbit'], cwd=self.build_temp, env=env)
   
        # untar ScannerBit tarball
        subprocess.check_call(['tar','-C','pyscannerbit/scannerbit/untar/ScannerBit','-xf','pyscannerbit/scannerbit/ScannerBit_stripped.tar','--strip-components=1'], cwd=ext.sourcedir, env=env)
      
        # First cmake
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        # Build all the scanners
        subprocess.check_call(['cmake', '--build', '.', '--target', 'multinest'] + build_args, cwd=self.build_temp)
        # Re-run cmake to detect built scanner plugins
        subprocess.check_call(['cmake', ext.sourcedir], cwd=self.build_temp)
        # Main build
        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)
        # Install
        #subprocess.check_call(['cmake', '--build', '.', '--target', 'install'], cwd=self.build_temp)

    ##def build_cmake(self, ext):
    ##    cwd = pathlib.Path().absolute()
    ##    # 'tmpdir' is the temporary location where the package is constructed
    ##    # 'installation_path' is the final location where the package ends up on the system
    ##    # We want CMake to put all the libraries and other build stuff in the temp location,
    ##    # from where it will be automatically copied, however when it comes to setting
    ##    # rpaths and such then we need to use the final 'installation_path'
    ##    build_temp = pathlib.Path(self.build_temp)
    ##    build_temp.mkdir(parents=True, exist_ok=True)
    ##    tmpdir = pathlib.Path(self.get_ext_fullpath(ext.name))
    ##    tmpdir.parent.mkdir(parents=True, exist_ok=True)


    ##    # example of cmake args
    ##    config = 'Debug' if self.debug else 'Release'
    ##    cmake_args = ['-DPYTHON_EXECUTABLE=' + sys.executable]
    ##    #    '-Wno-dev',
    ##    #    '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + str(tmpdir.parent),
    ##    #    '-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=' + installation_path,
    ##    #    '-DCMAKE_BUILD_TYPE=' + config,
    ##    #    '-DSCANNERBIT_STANDALONE=True',
    ##    #    '-DCMAKE_INSTALL_RPATH=$ORIGIN',
    ##    #    '-DCMAKE_BUILD_WITH_INSTALL_RPATH:BOOL=ON',
    ##    #    '-DCMAKE_INSTALL_RPATH_USE_LINK_PATH:BOOL=ON',
    ##    #    '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON',
    ##    #    '-DPYBIND11_PYTHON_VERSION=3.6',
    ##    #]

    ##    env = os.environ.copy()
    ##    env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
    ##                                                          self.distribution.get_version())

    ##    # example of build args
    ##    build_args = [
    ##        '--config', config,
    ##        '--', '-j4'
    ##    ]

    ##    os.chdir(str(build_temp))
    ##    # untar ScannerBit tarball
    ##    #self.spawn(['pwd'])
    ##    #self.spawn(['echo',str(cwd)])
    ##    #self.spawn(['ls',str(cwd)+'/pyscannerbit/scannerbit'])
    ##    #self.spawn(['tar','-C',str(cwd)+'/pyscannerbit/scannerbit/untar/ScannerBit','-xvf',str(cwd)+'/pyscannerbit/scannerbit/ScannerBit-1.1.3.tar','--strip-components=1'])
    ##    self.spawn(['cmake', str(cwd)] + cmake_args)
    ##    if not self.dry_run:
    ##        # Build all the scanners
    ##        #self.spawn(['cmake', '--build', '.', '--target', 'scanners'] + build_args)
    ##        #self.spawn(['cmake', '--build', '.', '--target', 'multinest'] + build_args)
    ##        # Re-run cmake
    ##        self.spawn(['cmake', str(cwd)])
    ##        # Do the main build 
    ##        self.spawn(['cmake', '--build', '.'] + build_args)

    ##    os.chdir(str(cwd))

setup(
    name='pyscannerbit',
    version='0.0.3',
    author='Ben Farmer',
    # Add yourself if you contribute to this package
    author_email='ben.farmer@gmail.com',
    description='A python interface to the GAMBIT scanning module, ScannerBit',
    long_description='',
    ext_modules=[CMakeExtension('_interface')],
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
    packages=['pyscannerbit'],
)

# No 'package_data' stuff. We just need to get CMake to put everything into 'tmpdir' and it should get copied.
