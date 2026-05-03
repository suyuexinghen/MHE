<div id="main-content" class="bd-main" role="main">

<div class="sbt-scroll-pixel-helper">

</div>

<div class="bd-content">

<div class="bd-article-container">

<div class="bd-header-article">

<div class="header-article-items header-article__inner">

<div class="header-article-items__start">

<div class="header-article-item">

<span class="fa-solid fa-bars"></span>

</div>

</div>

<div class="header-article-items__end">

<div class="header-article-item">

<div class="article-header-buttons">

<div class="dropdown dropdown-source-buttons">

- <a href="https://github.com/boutproject/BOUT-dev"
  class="btn btn-sm btn-source-repository-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Source repository"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Repository</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/installing.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/installing.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/installing.rst"
  class="btn btn-sm btn-download-source-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Download source file"><span class="btn__icon-container">
  <em></em> </span> <span class="btn__text-container">.rst</span></a>
- <span class="btn__icon-container"> </span>
  <span class="btn__text-container">.pdf</span>

</div>

<span class="btn__icon-container"> </span>

<span class="fa-solid fa-list"></span>

</div>

</div>

</div>

</div>

</div>

<div id="jb-print-docs-body" class="onlyprint">

# Getting started

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#pre-built-binaries"
  class="reference internal nav-link">Pre-built binaries</a>
  - <a href="#docker-image" class="reference internal nav-link">Docker
    image</a>
- <a href="#obtaining-bout" class="reference internal nav-link">Obtaining
  BOUT++</a>
- <a href="#installing-dependencies"
  class="reference internal nav-link">Installing dependencies</a>
  - <a href="#on-a-cluster-or-supercomputer"
    class="reference internal nav-link">On a cluster or supercomputer</a>
  - <a href="#ubuntu-debian" class="reference internal nav-link">Ubuntu /
    Debian</a>
  - <a href="#arch-linux" class="reference internal nav-link">Arch Linux</a>
  - <a href="#fedora" class="reference internal nav-link">Fedora</a>
- <a href="#configuring-bout"
  class="reference internal nav-link">Configuring BOUT++</a>
  - <a href="#common-cmake-options"
    class="reference internal nav-link">Common CMake Options</a>
  - <a href="#downloading-dependencies"
    class="reference internal nav-link">Downloading Dependencies</a>
  - <a href="#bundled-dependencies"
    class="reference internal nav-link">Bundled Dependencies</a>
  - <a href="#working-with-an-active-conda-environment"
    class="reference internal nav-link">Working with an active <span
    class="pre"><code
    class="docutils literal notranslate">conda</code></span> environment</a>
- <a href="#natural-language-support"
  class="reference internal nav-link">Natural Language Support</a>
- <a href="#configuring-analysis-routines"
  class="reference internal nav-link">Configuring analysis routines</a>
  - <a href="#python-configuration"
    class="reference internal nav-link">Python configuration</a>
  - <a href="#sec-config-idl" class="reference internal nav-link">IDL
    configuration</a>
- <a href="#compiling-bout" class="reference internal nav-link">Compiling
  BOUT++</a>
- <a href="#running-the-test-suite"
  class="reference internal nav-link">Running the test suite</a>
- <a href="#installing-bout-experimental"
  class="reference internal nav-link">Installing BOUT++ (experimental)</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="getting-started" class="section">

<span id="sec-install"></span>

# Getting started<a href="#getting-started" class="headerlink"
title="Permalink to this heading">#</a>

This section goes through the process of getting, installing, and
starting to run BOUT++.

The quickest way to get started is to use a pre-built binary. These take
care of all dependencies, configuration and compilation. See section
<a href="#sec-prebuiltinstall" class="reference internal"><span
class="std std-ref">Docker image</span></a>.

The remainder of this section will go through the following steps to
manually install BOUT++. Only the basic functionality needed to use
BOUT++ is described here; the next section
(<a href="advanced_install.html#sec-advancedinstall"
class="reference internal"><span class="std std-ref">Advanced
installation options</span></a>) goes through more advanced options,
configurations for particular machines, and how to fix some common
problems.

1.  <a href="#sec-obtainbout" class="reference internal"><span
    class="std std-ref">Obtaining a copy of BOUT++</span></a>

2.  <a href="#sec-dependencies" class="reference internal"><span
    class="std std-ref">Installing dependencies</span></a>

3.  <a href="#sec-config-bout" class="reference internal"><span
    class="std std-ref">Configuring BOUT++</span></a>

4.  <a href="#sec-configanalysis" class="reference internal"><span
    class="std std-ref">Configuring BOUT++ analysis codes</span></a>

    1.  <a href="#sec-config-python" class="reference internal"><span
        class="std std-ref">Python</span></a>

    2.  <a href="#sec-config-idl" class="reference internal"><span
        class="std std-ref">IDL</span></a>

5.  <a href="#sec-compile-bout" class="reference internal"><span
    class="std std-ref">Compiling BOUT++</span></a>

6.  <a href="#sec-runtestsuite" class="reference internal"><span
    class="std std-ref">Running the test suite</span></a>

7.  <a href="#sec-install-bout" class="reference internal"><span
    class="std std-ref">Installing BOUT++ (experimental)</span></a>

**Note**: In this manual commands to run in a BASH shell will begin with
’$’, and commands specific to CSH with a ’%’.

<div id="pre-built-binaries" class="section">

## Pre-built binaries<a href="#pre-built-binaries" class="headerlink"
title="Permalink to this heading">#</a>

<div id="docker-image" class="section">

<span id="sec-prebuiltinstall"></span>

### Docker image<a href="#docker-image" class="headerlink"
title="Permalink to this heading">#</a>

<a href="https://www.docker.com" class="reference external">Docker</a>
is a widely used container system, which packages together the operating
system environment, libraries and other dependencies into an image. This
image can be downloaded and run reproducibly on a wide range of hosts,
including Windows, Linux and OS X. Here is the starting page for
<a href="https://docs.docker.com/install/"
class="reference external">instructions on installing Docker</a>.

The BOUT++ docker images are
<a href="https://hub.docker.com/u/boutproject/"
class="reference external">hosted on dockerhub</a> for some releases and
snapshots. Check the
<a href="https://hub.docker.com/r/boutproject/bout-next/tags/"
class="reference external">list of BOUT-next tags</a> if you want a
recent version of BOUT++ “next” (development) branch. First download the
image:

<div class="highlight-console notranslate">

<div class="highlight">

    $ sudo docker pull boutproject/boutproject/bout-next:9f4c663-petsc

</div>

</div>

then run:

<div class="highlight-console notranslate">

<div class="highlight">

    $ sudo docker run --rm -it boutproject/bout-next:9f4c663-petsc

</div>

</div>

This should give a terminal in a “boutuser” home directory, in which
there is “BOUT-next”, containing BOUT++ configured and compiled with
NetCDF, SUNDIALS, PETSc and SLEPc. Python 3 is also installed, with
ipython, NumPy, Scipy and Matplotlib libaries. To plot to screen an X11
display is needed. Alternatively a shared directory can be created to
pass files between the docker image and host. The following commands
both enable X11 and create a shared directory:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mkdir shared
    $ sudo docker run --rm -it \
       -e DISPLAY -v $HOME/.Xauthority:/home/boutuser/.Xauthority --net=host \
       -v $PWD/shared:/home/boutuser/bout-img-shared \
       boutproject/bout-next:9f4c663-petsc

</div>

</div>

This should enable plotting from python, and files in the docker image
put in “/home/boutuser/bout-img-shared” should be visible on the host in
the “shared” directory.

If this is successful, then you can skip to section
<a href="running_bout.html#sec-running" class="reference internal"><span
class="std std-ref">Running BOUT++</span></a>.

</div>

</div>

<div id="obtaining-bout" class="section">

<span id="sec-obtainbout"></span>

## Obtaining BOUT++<a href="#obtaining-bout" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ is hosted publicly on github at
<a href="https://github.com/boutproject/BOUT-dev"
class="github reference external">boutproject/BOUT-dev</a>. You can the
latest stable version from
<a href="https://github.com/boutproject/BOUT-dev/releases"
class="github reference external">boutproject/BOUT-dev</a>. If you want
to develop BOUT++, you should use git to clone the repository. To obtain
a copy of the latest version, run:

<div class="highlight-console notranslate">

<div class="highlight">

    $ git clone https://github.com/boutproject/BOUT-dev.git

</div>

</div>

which will create a directory <span class="pre">`BOUT-dev`</span>
containing the code:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cd BOUT-dev

</div>

</div>

To get the latest changes later, go into the
<span class="pre">`BOUT-dev`</span> directory and run:

<div class="highlight-console notranslate">

<div class="highlight">

    $ git pull

</div>

</div>

Development is done on the “next” branch, which you can checkout with:

<div class="highlight-console notranslate">

<div class="highlight">

    $ git checkout next

</div>

</div>

</div>

<div id="installing-dependencies" class="section">

<span id="sec-installmpi"></span>

## Installing dependencies<a href="#installing-dependencies" class="headerlink"
title="Permalink to this heading">#</a>

The bare-minimum requirements for compiling and running BOUT++ are:

1.  A C++ compiler that supports C++17

2.  An MPI compiler such as OpenMPI (<a href="https://www.open-mpi.org/"
    class="reference external">www.open-mpi.org/</a>), MPICH (
    <a href="https://www.mpich.org/"
    class="reference external">https://www.mpich.org/</a>)

3.  The NetCDF library
    (<a href="https://www.unidata.ucar.edu/downloads/netcdf"
    class="reference external">https://www.unidata.ucar.edu/downloads/netcdf</a>)

The FFTW-3 library (<a href="http://www.fftw.org/"
class="reference external">http://www.fftw.org/</a>) is also strongly
recommended. Fourier transforms are used for some derivative methods, as
well as the <a
href="../_breathe_autogen/file/paralleltransform_8hxx.html#_CPPv413ShiftedMetric"
class="reference internal" title="ShiftedMetric"><span class="pre"><code
class="sourceCode cpp">ShiftedMetric</code></span></a> parallel
transform which is used in the majority of BOUT++ tokamak simulations.
Without FFTW-3, these options will not be available.

<div class="admonition note">

Note

If you use an Intel compiler, you must also make sure that you have a
version of GCC that supports C++17 (GCC 8+).

On supercomputers, or in other environments that use a module system,
you may need to load modules for both Intel and GCC.

</div>

<div id="on-a-cluster-or-supercomputer" class="section">

### On a cluster or supercomputer<a href="#on-a-cluster-or-supercomputer" class="headerlink"
title="Permalink to this heading">#</a>

If you are installing on a cluster or supercomputer then the MPI C++
compilers will already be installed, and on Cray or IBM machines will
probably be called <span class="pre">`CC`</span> and
<span class="pre">`xlC`</span> respectively.

On large facilities (e.g NERSC or Archer), the compilers and libraries
needed should already be installed, but you may need to load them to use
them. It is common to organise libraries using the
<span class="pre">`modules`</span> system, so try typing:

<div class="highlight-console notranslate">

<div class="highlight">

    modules avail

</div>

</div>

to get a list of available modules. Some instructions for specific
machines can be found in
<a href="advanced_install.html#sec-machine-specific"
class="reference internal"><span class="std std-ref">Machine-specific
installation</span></a>. See your system’s documentation on modules and
which ones to load. If you don’t know, or modules don’t work, you can
still install libraries in your home directory by following the
instructions below for
<a href="advanced_install.html#sec-fftw-from-source"
class="reference internal"><span class="std std-ref">FFTW</span></a> and
<a href="advanced_install.html#sec-netcdf-from-source"
class="reference internal"><span class="std std-ref">NetCDF</span></a>.

</div>

<div id="ubuntu-debian" class="section">

### Ubuntu / Debian<a href="#ubuntu-debian" class="headerlink"
title="Permalink to this heading">#</a>

On Ubuntu or Debian distributions if you have administrator rights then
you can install the basic dependencies with:

<div class="highlight-console notranslate">

<div class="highlight">

    $ sudo apt-get install libmpich-dev libfftw3-dev libnetcdf-c++4-dev git make

</div>

</div>

To additionally build the Python interface, you need some Python
packages:

<div class="highlight-console notranslate">

<div class="highlight">

    $ sudo apt-get install python3 python3-distutils python3-pip python3-numpy python3-netcdf4 python3-scipy
    $ pip3 install --user Cython

</div>

</div>

Further, the encoding for python needs to be utf8 - it may be required
to set
<span class="pre">`export`</span>` `<span class="pre">`LC_CTYPE=C.utf8`</span>.

If you do not have administrator rights, so can’t install packages, then
you need to install these libraries from source into your home
directory. See <a href="advanced_install.html#sec-advancedinstall"
class="reference internal"><span class="std std-ref">Advanced
installation options</span></a> for details on installing some of these.

</div>

<div id="arch-linux" class="section">

### Arch Linux<a href="#arch-linux" class="headerlink"
title="Permalink to this heading">#</a>

<div class="highlight-console notranslate">

<div class="highlight">

    $ pacman -S openmpi fftw netcdf-cxx make gcc

</div>

</div>

</div>

<div id="fedora" class="section">

### Fedora<a href="#fedora" class="headerlink"
title="Permalink to this heading">#</a>

On Fedora the required libraries can be installed by running:

<div class="highlight-console notranslate">

<div class="highlight">

    $ sudo dnf build-dep bout++

</div>

</div>

This will install all the dependencies that are used to install BOUT++
for fedora. Feel free to install only a subset of the suggested
packages. For example, only mpich or openmpi is required. To load an mpi
implementation type:

<div class="highlight-console notranslate">

<div class="highlight">

    $ module load mpi

</div>

</div>

After that the mpi library is loaded. Precompiled binaries are available
for fedora as well. To get precompiled BOUT++ run:

<div class="highlight-console notranslate">

<div class="highlight">

    $ # install the mpich version - openmpi is available as well
    $ sudo dnf install bout++-mpich-devel
    $ # get the python3 modules - python2 is available as well
    $ sudo dnf install python3-bout++

</div>

</div>

</div>

</div>

<div id="configuring-bout" class="section">

<span id="sec-config-bout"></span>

## Configuring BOUT++<a href="#configuring-bout" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ uses the
<a href="https://cmake.org/" class="reference external">CMake</a> build
system generator. You will need CMake \>= 3.17.

<div class="admonition note">

Note

It is possible to get the latest version of CMake using
<span class="pre">`pip`</span>:

<div class="highlight-console notranslate">

<div class="highlight">

    $ pip install --user --upgrade cmake

</div>

</div>

or <span class="pre">`conda`</span>:

<div class="highlight-console notranslate">

<div class="highlight">

    $ conda install cmake

</div>

</div>

You may need to put <span class="pre">`~/.local/bin`</span> in your
<span class="pre">`$PATH`</span>

</div>

CMake supports out-of-source builds by default, which are A Good Idea.
Basic configuration with CMake looks like:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake -S . -B build

</div>

</div>

which creates a new directory <span class="pre">`build`</span>. You can
call this directory anything you like, and you also put it anywhere you
like, you just need to specify the path to the BOUT++ source directory
with the <span class="pre">`-S`</span> argument. This makes it very easy
to keep two build directories alongside one another, one with a debug
build and one optimised, for example.

After configuring the build directory, you can then compile BOUT++ with:

<div class="highlight-console notranslate">

<div class="highlight">

    # Build the library
    $ cmake --build build
    # Build the library with 8 threads
    $ cmake --build build -j 8
    # Build the "blob2d" example
    $ cmake --build build --target blob2d

</div>

</div>

By default, CMake will use <span class="pre">`makefiles`</span>, and so
it is possible to also build BOUT++ with <span class="pre">`make`</span>
from the build directory – note that you must still run
<span class="pre">`cmake`</span> once first to configure BOUT++:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake . -B build
    $ cd build
    $ make

</div>

</div>

<div class="admonition note">

Note

You might see some instructions in the documentation using
<span class="pre">`make`</span> – they should be run from the
<span class="pre">`build`</span> directory.

</div>

You can see what build options are available with:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake . -B build -LH
    ...
    // Enable backtrace
    BOUT_ENABLE_BACKTRACE:BOOL=ON

    // Output coloring
    BOUT_ENABLE_COLOR:BOOL=ON

    // Enable OpenMP support
    BOUT_ENABLE_OPENMP:BOOL=OFF

    // Enable support for PETSc time solvers and inversions
    BOUT_USE_PETSC:BOOL=OFF
    ...

</div>

</div>

CMake uses the <span class="pre">`-D<variable>=<choice>`</span> syntax
to control these variables. You can set
<span class="pre">`<package>_ROOT`</span> to guide CMake in finding the
various optional third-party packages (except for PETSc/SLEPc, which use
<span class="pre">`_DIR`</span>). Note that some packages have funny
captialisation, for example <span class="pre">`NetCDF_ROOT`</span>! Use
<span class="pre">`-LH`</span> to see the form that each package
expects.

CMake understands the usual environment variables for setting the
compiler, compiler/linking flags, as well as having built-in options to
control them and things like static vs shared libraries, etc. See the
<a href="https://cmake.org/documentation/"
class="reference external">CMake documentation</a> for more infomation.

A more complicated CMake configuration command might look like:

<div class="highlight-console notranslate">

<div class="highlight">

    $ CC=mpicc CXX=mpic++ cmake . -B build \
        -DBOUT_USE_PETSC=ON -DPETSC_DIR=/path/to/petsc/ \
        -DBOUT_USE_SLEPC=ON -DSLEPC_DIR=/path/to/slepc/ \
        -DBOUT_USE_SUNDIALS=ON -DSUNDIALS_ROOT=/path/to/sundials \
        -DBOUT_USE_NETCDF=ON -DNetCDF_ROOT=/path/to/netcdf \
        -DBOUT_ENABLE_OPENMP=ON \
        -DBOUT_ENABLE_SIGFPE=OFF \
        -DCMAKE_BUILD_TYPE=Debug \
        -DBUILD_SHARED_LIBS=ON
        -DCMAKE_INSTALL_PREFIX=/path/to/install/BOUT++

</div>

</div>

If you wish to change the configuration after having built
<span class="pre">`BOUT++`</span>, it’s wise to delete the
<span class="pre">`CMakeCache.txt`</span> file in the build directory.
The equivalent of
<span class="pre">`make`</span>` `<span class="pre">`distclean`</span>
with CMake is to just delete the entire build directory and reconfigure.

If you need to debug a CMake build, you can see the compile and link
commands which are being issued by adding
<span class="pre">`--verbose`</span> to the build command:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake --build build --verbose

</div>

</div>

<div id="common-cmake-options" class="section">

### Common CMake Options<a href="#common-cmake-options" class="headerlink"
title="Permalink to this heading">#</a>

The default build configuration options try to be sensible for new users
and developers, but there are a few you probably want to set manually
for production runs or for debugging:

- <span class="pre">`CMAKE_BUILD_TYPE`</span>: The default is
  <span class="pre">`RelWithDebInfo`</span>, which builds an optimised
  executable with debug symbols included. This is generally the most
  useful, except for developers, who may wish to use
  <span class="pre">`Debug`</span> for an unoptimised build, but better
  debug experience. There are a couple of other choices
  (<span class="pre">`Release`</span> and
  <span class="pre">`MinSizeRel`</span>) which also produce optimised
  executables, but without debug symbols, which is only really useful
  for producing smaller binaries.

- <span class="pre">`CHECK`</span>: This sets the level of internal
  runtime checking done in the BOUT++ library, and ranges from 0 to 4
  (inclusive). By default, this is 2, which aims to be a balance between
  useful checks and speed. Set this to 0 for faster production runs, and
  to 4 for more in-depth (and slower) checking.

- <span class="pre">`BOUT_UPDATE_GIT_SUBMODULE`</span>: This is on by
  default, and ensures that the bundled git submodules are up-to-date.
  You should turn this off if you are using system versions, or if you
  run into problems updating the submodules.

- <span class="pre">`NetCDF_ROOT`</span>: NetCDF is one of the few
  required, non-bundled dependencies. If CMake is having trouble finding
  netCDF, or the correct version, you should set this variable to the
  installed location of the netCDF C library.

- <span class="pre">`BOUT_BUILD_EXAMPLES`</span>,
  <span class="pre">`BOUT_TESTS`</span>: These two options are
  particularly useful for developers of the BOUT++ library, and for new
  users. You can turn them off to save some time configuring the
  library. By default, these are on, but the examples and tests are not
  built unless you specifically ask for them, using the targets
  <span class="pre">`build-all-examples`</span> and
  <span class="pre">`build-check`</span> respectively.

</div>

<div id="downloading-dependencies" class="section">

### Downloading Dependencies<a href="#downloading-dependencies" class="headerlink"
title="Permalink to this heading">#</a>

If you don’t have some dependencies installed, CMake can be used to
download, configure and compile them alongside BOUT++.

For NetCDF, use
<span class="pre">`-DBOUT_DOWNLOAD_NETCDF_CXX4=ON`</span>

For SUNDIALS, use
<span class="pre">`-DBOUT_DOWNLOAD_SUNDIALS=ON`</span>. If using
<span class="pre">`ccmake`</span> this option may not appear initially.
This automatically sets <span class="pre">`BOUT_USE_SUNDIALS=ON`</span>,
and configures SUNDIALS to use MPI.

For ADIOS2, use <span class="pre">`-DBOUT_DOWNLOAD_ADIOS2=ON`</span>.
This will download and configure
<a href="https://adios2.readthedocs.io/"
class="reference external">ADIOS2</a>, enabling BOUT++ to read and write
this high-performance parallel file format.

</div>

<div id="bundled-dependencies" class="section">

### Bundled Dependencies<a href="#bundled-dependencies" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ bundles some dependencies, currently:

- <a href="https://github.com/mpark/variant"
  class="reference external">mpark.variant</a>

- <a href="https://fmt.dev" class="reference external">fmt</a>

- <a href="https://github.com/jeremy-rifkin/cpptrace"
  class="reference external">cpptrace</a>

- [<span id="id2" class="problematic">\`\`</span>](#id1)googletest
  \<<a href="https://github.com/google/googletest"
  class="github reference external">google/googletest</a>\>\`\_ (for
  unit tests)

Aside from <span class="pre">`googletest`</span>, the others are
required dependencies and can either be built as part of the BOUT++
build, or provided externally. If you wish to use existing installations
of some of these, set the following flags:

<table class="table">
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Flag for external installation</p></th>
<th class="head"><p>Library path</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">mpark.variant</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">BOUT_USE_SYSTEM_MPARK_VARIANT</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">mpark_variant_ROOT</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">fmt</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">BOUT_USE_SYSTEM_FMT</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">fmt_ROOT</code></span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">cpptrace</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">BOUT_USE_SYSTEM_CPPTRACE</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">cpptrace_ROOT</code></span></p></td>
</tr>
</tbody>
</table>

You can also set <span class="pre">`-DBOUT_USE_GIT_SUBMODULE=OFF`</span>
to not use any of the bundled versions.

If the libraries are in non-standard locations, you may also need to
supply the relevant library path flags.

The recommended way to use <span class="pre">`googletest`</span> is to
compile it at the same time as your project, therefore there is no
option to use an external installation for that.

</div>

<div id="working-with-an-active-conda-environment" class="section">

### Working with an active <span class="pre">`conda`</span> environment<a href="#working-with-an-active-conda-environment" class="headerlink"
title="Permalink to this heading">#</a>

When <span class="pre">`conda`</span> is used, it installs separate
versions of several libraries. These can cause warnings or even failures
when linking BOUT++ executables. There are several alternatives to deal
with this problem: \* The simplest but least convenient option is to use
<span class="pre">`conda`</span>` `<span class="pre">`deactivate`</span>
before

> <div>
>
> configuring, compiling, or running any BOUT++ program.
>
> </div>

- You might sometimes want to link to the conda-installed libraries.
  This is probably not ideal for production runs on an HPC system (as
  conda downloads binary packages that will not be optimized for
  specific hardware), but can be a simple way to get packages for
  testing or on a personal computer. In this case just keep your
  <span class="pre">`conda`</span> environment active, and with luck the
  libraries should be picked up by the standard search mechanisms.

- In case you do want a fully optimized and as-stable-as-possible build
  for production runs, it is probably best not to depend on any conda
  packages for compiling or running BOUT++ executables (restrict
  <span class="pre">`conda`</span> to providing Python packages for
  post-processing, and their dependencies). Passing
  <span class="pre">`-DBOUT_IGNORE_CONDA_ENV=ON`</span> (default
  <span class="pre">`OFF`</span>) excludes anything in the conda
  environment from CMake search paths. This should totally separate
  BOUT++ from the <span class="pre">`conda`</span> environment.

</div>

</div>

<div id="natural-language-support" class="section">

<span id="sec-config-nls"></span>

## Natural Language Support<a href="#natural-language-support" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ has support for languages other than English, using GNU gettext.
If you are planning on installing BOUT++ (see
<a href="#sec-install-bout" class="reference internal"><span
class="std std-ref">Installing BOUT++ (experimental)</span></a>) then
this should work automatically, but if you will be running BOUT++ from
the directory you downloaded it into, then configure with the option:

<div class="highlight-console notranslate">

<div class="highlight">

    cmake . -DCMAKE_INSTALL_LOCALEDIR=$PWD/locale

</div>

</div>

This will enable BOUT++ to find the translations.

See
<a href="running_bout.html#sec-run-nls" class="reference internal"><span
class="std std-ref">Natural language support</span></a> for details of
how to switch language when running BOUT++ simulations.

</div>

<div id="configuring-analysis-routines" class="section">

<span id="sec-configanalysis"></span>

## Configuring analysis routines<a href="#configuring-analysis-routines" class="headerlink"
title="Permalink to this heading">#</a>

The BOUT++ installation comes with a set of useful routines which can be
used to prepare inputs and analyse outputs. Most of this code is now in
Python, though IDL was used for many years. Python is useful In
particular because the test suite scripts and examples use Python, so to
run these you’ll need python configured.

When the configure script finishes, it prints out the paths you need to
get IDL, Python, and Octave analysis routines working. If you just want
to compile BOUT++ then you can skip to the next section, but make a note
of what configure printed out.

<div id="python-configuration" class="section">

<span id="sec-config-python"></span>

### Python configuration<a href="#python-configuration" class="headerlink"
title="Permalink to this heading">#</a>

To use Python, you will need the dependencies of the
<a href="https://github.com/boutproject/boututils"
class="reference external">boututils</a> and
<a href="https://github.com/boutproject/boutdata"
class="reference external">boutdata</a> libraries. The simplest way to
get these is to install the packages with pip:

<div class="highlight-console notranslate">

<div class="highlight">

    $ pip install --user boutdata

</div>

</div>

or conda:

<div class="highlight-console notranslate">

<div class="highlight">

    $ conda install boutdata

</div>

</div>

You can also install all the packages directly (see the documentation in
the <a href="https://github.com/boutproject/boututils"
class="reference external">boututils</a> and
<a href="https://github.com/boutproject/boutdata"
class="reference external">boutdata</a> repos for the most up to date
list) using pip:

<div class="highlight-console notranslate">

<div class="highlight">

    $ pip install --user numpy scipy matplotlib sympy netCDF4 future importlib-metadata

</div>

</div>

or conda:

<div class="highlight-console notranslate">

<div class="highlight">

    $ conda install numpy scipy matplotlib sympy netcdf4 future importlib-metadata

</div>

</div>

They may also be available from your Linux system’s package manager.

For example on Fedora:

<div class="highlight-console notranslate">

<div class="highlight">

    $ sudo dnf install python3-boututils python3-boutdata

</div>

</div>

To use the versions of <span class="pre">`boututils`</span> and
<span class="pre">`boutdata`</span> provided by BOUT++, the path to
<span class="pre">`tools/pylib`</span> should be added to the
<span class="pre">`PYTHONPATH`</span> environment variable. This is not
necessary if you have installed the <span class="pre">`boututils`</span>
and <span class="pre">`boutdata`</span> packages. Instructions for doing
this are printed at the end of the configure script, for example:

<div class="highlight-console notranslate">

<div class="highlight">

    Make sure that the tools/pylib directory is in your PYTHONPATH
    e.g. by adding to your ~/.bashrc file

       export PYTHONPATH=/home/ben/BOUT/tools/pylib/:$PYTHONPATH

</div>

</div>

To test if this command has worked, try running:

<div class="highlight-console notranslate">

<div class="highlight">

    $ python -c "import boutdata"

</div>

</div>

If this doesn’t produce any error messages then Python is configured
correctly.

Note that <span class="pre">`boututils`</span> and
<span class="pre">`boutdata`</span> are provided by BOUT++ as
submodules, so versions compatible with the checked out version of
BOUT++ are downloaded into the
<span class="pre">`externalpackages`</span> directory. These are the
versions used by the tests run by
<span class="pre">`make`</span>` `<span class="pre">`check`</span> even
if you have installed <span class="pre">`boututils`</span> and
<span class="pre">`boutdata`</span> on your system.

</div>

<div id="sec-config-idl" class="section">

<span id="idl-configuration"></span>

### IDL configuration<a href="#sec-config-idl" class="headerlink"
title="Permalink to this heading">#</a>

If you want to use
<a href="https://en.wikipedia.org/wiki/IDL_(programming_language)"
class="reference external">IDL</a> to analyse BOUT++ outputs, then the
<span class="pre">`IDL_PATH`</span> environment variable should include
the <span class="pre">`tools/idllib/`</span> subdirectory included with
BOUT++. The required command (for Bash) is printed at the end of the
BOUT++ configuration:

<div class="highlight-console notranslate">

<div class="highlight">

    $ export IDL_PATH=...

</div>

</div>

After running that command, check that <span class="pre">`idl`</span>
can find the analysis routines by running:

<div class="highlight-console notranslate">

<div class="highlight">

    $ idl
    IDL> .r collect
    IDL> help, /source

</div>

</div>

You should see the function <span class="pre">`COLLECT`</span> in the
<span class="pre">`BOUT/tools/idllib`</span> directory. If not,
something is wrong with your <span class="pre">`IDL_PATH`</span>
variable. On some machines, modifying
<span class="pre">`IDL_PATH`</span> causes problems, in which case you
can try modifying the path inside IDL by running:

<div class="highlight-console notranslate">

<div class="highlight">

    IDL> !path = !path + ":/path/to/BOUT-dev/tools/idllib"

</div>

</div>

where you should use the full path. You can get this by going to the
<span class="pre">`tools/idllib`</span> directory and typing
<span class="pre">`pwd`</span>. Once this is done you should be able to
use <span class="pre">`collect`</span> and other routines.

</div>

</div>

<div id="compiling-bout" class="section">

<span id="sec-compile-bout"></span>

## Compiling BOUT++<a href="#compiling-bout" class="headerlink"
title="Permalink to this heading">#</a>

Once BOUT++ has been configured, you can compile the bulk of the code by
going to the <span class="pre">`BOUT-dev`</span> directory and running:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake --build <build-directory>

</div>

</div>

where <span class="pre">`<build-directory>`</span> is the path to the
build directory

At the end of this, you should see a file
<span class="pre">`libbout++.so`</span> in the
<span class="pre">`lib/`</span> subdirectory of the BOUT++ build
directory. If you get an error, please
<a href="https://github.com/boutproject/BOUT-dev/issues"
class="reference external">create an issue on Github</a> including:

- Which machine you’re compiling on

- The output from make, including full error message

- The <span class="pre">`CMakeCache.txt`</span> file in the BOUT++ build
  directory

</div>

<div id="running-the-test-suite" class="section">

<span id="sec-runtestsuite"></span>

## Running the test suite<a href="#running-the-test-suite" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ comes with three sets of test suites: unit tests, integrated
tests and method of manufactured solutions (MMS) tests. The easiest way
to run all of them is to simply do:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake --build <build-directory> --target check

</div>

</div>

Alternatively, if you just want to run one set of them individually, you
can do:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake --build <build-directory> --target check-unit-tests
    $ cmake --build <build-directory> --target check-integrated-tests
    $ cmake --build <build-directory> --target check-mms-tests

</div>

</div>

**Note:** The integrated and MMS test suites currently uses the
<span class="pre">`mpirun`</span> command to launch the runs, so won’t
work on machines which use a job submission system like slurm or PBS.

These tests should all pass, but if not please
<a href="https://github.com/boutproject/BOUT-dev/issues"
class="reference external">create an issue on Github</a> containing:

- Which machine you’re running on

- The <span class="pre">`CMakeCache.txt`</span> file in the BOUT++ build
  directory

- The <span class="pre">`run.log.*`</span> files in the directory of the
  test which failed

If the tests pass, congratulations! You have now got a working
installation of BOUT++. Unless you want to use some experimental
features of BOUT++, skip to section \[sec-running\] to start running the
code.

</div>

<div id="installing-bout-experimental" class="section">

<span id="sec-install-bout"></span>

## Installing BOUT++ (experimental)<a href="#installing-bout-experimental" class="headerlink"
title="Permalink to this heading">#</a>

Most BOUT++ users install and develop their own copies in their home
directory, so do not need to install BOUT++ to a system directory. As of
version 4.1 (August 2017), it is possible to install BOUT++ but this is
not widely used and so should be considered experimental.

After configuring and compiling BOUT++ as above, BOUT++ can be installed
to system directories by running as superuser or
<span class="pre">`sudo`</span>:

<div class="highlight-console notranslate">

<div class="highlight">

    $ sudo cmake --build <build-directory> --target install

</div>

</div>

<div class="admonition danger">

Danger

Do not do this unless you know what you’re doing!

</div>

This will install the following files under
<span class="pre">`/usr/local/`</span>:

- <span class="pre">`/usr/local/bin/bout-config`</span> A script which
  can be used to query BOUT++ configuration and compile codes with
  BOUT++.

- <span class="pre">`/usr/local/include/bout++/...`</span> header files
  for BOUT++

- <span class="pre">`/usr/local/lib/libbout++.so`</span> The main BOUT++
  library

- <span class="pre">`/usr/local/lib/libpvode.so`</span> and
  <span class="pre">`/usr/local/lib/libpvpre.so`</span>, the PVODE
  library

- <span class="pre">`/usr/local/share/bout++/pylib/...`</span> Python
  analysis routines

- <span class="pre">`/usr/local/share/bout++/idllib/...`</span> IDL
  analysis routines

To install BOUT++ under a different directory, use the
<span class="pre">`prefix=`</span> flag e.g. to install in your home
directory:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake --build <build-directory> --target install -DCMAKE_INSTALL_PREFIX=$HOME/local/

</div>

</div>

You can also specify this prefix when configuring, in the usual way (see
<a href="#sec-config-bout" class="reference internal"><span
class="std std-ref">Configuring BOUT++</span></a>):

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake -S . -B <build-directory> -DCMAKE_INSTALL_PREFIX=$HOME/local/
    $ cmake --build <build-directory> -j 4
    $ cmake --build <build-directory> --target install

</div>

</div>

More control over where files are installed is possible by passing
options to <span class="pre">`cmake`</span>, following the GNU
conventions:

- <span class="pre">`-DCMAKE_INSTALL_BINDIR=`</span> sets where
  <span class="pre">`bout-config`</span> will be installed ( default
  <span class="pre">`/usr/local/bin`</span>)

- <span class="pre">`-DCMAKE_INSTALL_INCLUDEDIR=`</span> sets where the
  <span class="pre">`bout++/*.hxx`</span> header files wil be installed
  (default <span class="pre">`/usr/local/include`</span>)

- <span class="pre">`-DCMAKE_INSTALL_LIBDIR=`</span> sets where the
  <span class="pre">`libbout++.so`</span>,
  <span class="pre">`libpvode.so`</span> and
  <span class="pre">`libpvpre.so`</span> libraries are installed
  (default <span class="pre">`/usr/local/lib`</span>)

After installing, that you can run
<span class="pre">`bout-config`</span> e.g:

<div class="highlight-console notranslate">

<div class="highlight">

    $ bout-config --all

</div>

</div>

which should print out the list of configuration settings which
<span class="pre">`bout-config`</span> can provide. If this doesn’t
work, check that the directory containing
<span class="pre">`bout-config`</span> is in your
<span class="pre">`PATH`</span>.

The python and IDL analysis scripts can be configured using
<span class="pre">`bout-config`</span> rather than manually setting
paths as in
<a href="#sec-configanalysis" class="reference internal"><span
class="std std-ref">Configuring analysis routines</span></a>. Add this
line to your startup file (e.g.
<span class="pre">`$HOME/.bashrc`</span>):

<div class="highlight-console notranslate">

<div class="highlight">

    export PYTHONPATH=`bout-config --python`:$PYTHONPATH

</div>

</div>

note the back ticks around
<span class="pre">`bout-config`</span>` `<span class="pre">`--python`</span>
not quotes. Similarly for IDL:

<div class="highlight-console notranslate">

<div class="highlight">

    export IDL_PATH=`bout-config --idl`:'<IDL_DEFAULT>':$IDL_PATH

</div>

</div>

More details on using bout-config are in the
<a href="makefiles.html#sec-bout-config"
class="reference internal"><span class="std std-ref">section on
makefiles</span></a>.

</div>

</div>

<div class="prev-next-area">

<a href="quickstart.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Quickstart Guide

</div>

<a href="advanced_install.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Advanced installation options

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#pre-built-binaries"
  class="reference internal nav-link">Pre-built binaries</a>
  - <a href="#docker-image" class="reference internal nav-link">Docker
    image</a>
- <a href="#obtaining-bout" class="reference internal nav-link">Obtaining
  BOUT++</a>
- <a href="#installing-dependencies"
  class="reference internal nav-link">Installing dependencies</a>
  - <a href="#on-a-cluster-or-supercomputer"
    class="reference internal nav-link">On a cluster or supercomputer</a>
  - <a href="#ubuntu-debian" class="reference internal nav-link">Ubuntu /
    Debian</a>
  - <a href="#arch-linux" class="reference internal nav-link">Arch Linux</a>
  - <a href="#fedora" class="reference internal nav-link">Fedora</a>
- <a href="#configuring-bout"
  class="reference internal nav-link">Configuring BOUT++</a>
  - <a href="#common-cmake-options"
    class="reference internal nav-link">Common CMake Options</a>
  - <a href="#downloading-dependencies"
    class="reference internal nav-link">Downloading Dependencies</a>
  - <a href="#bundled-dependencies"
    class="reference internal nav-link">Bundled Dependencies</a>
  - <a href="#working-with-an-active-conda-environment"
    class="reference internal nav-link">Working with an active <span
    class="pre"><code
    class="docutils literal notranslate">conda</code></span> environment</a>
- <a href="#natural-language-support"
  class="reference internal nav-link">Natural Language Support</a>
- <a href="#configuring-analysis-routines"
  class="reference internal nav-link">Configuring analysis routines</a>
  - <a href="#python-configuration"
    class="reference internal nav-link">Python configuration</a>
  - <a href="#sec-config-idl" class="reference internal nav-link">IDL
    configuration</a>
- <a href="#compiling-bout" class="reference internal nav-link">Compiling
  BOUT++</a>
- <a href="#running-the-test-suite"
  class="reference internal nav-link">Running the test suite</a>
- <a href="#installing-bout-experimental"
  class="reference internal nav-link">Installing BOUT++ (experimental)</a>

</div>

</div>

</div>

</div>

<div class="bd-footer-content__inner container">

<div class="footer-item">

By B. Dudson and The BOUT++ team

</div>

<div class="footer-item">

© Copyright 2017-2023, B. Dudson and The BOUT++ team.  

</div>

<div class="footer-item">

</div>

<div class="footer-item">

</div>

</div>

</div>
