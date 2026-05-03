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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/advanced_install.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/advanced_install.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/advanced_install.rst"
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

# Advanced installation options

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#optimisation-and-run-time-checking"
  class="reference internal nav-link">Optimisation and run-time
  checking</a>
- <a href="#install-dependencies"
  class="reference internal nav-link">Install dependencies:</a>
- <a href="#machine-specific-installation"
  class="reference internal nav-link">Machine-specific installation</a>
  - <a href="#archer" class="reference internal nav-link">Archer</a>
  - <a href="#cori" class="reference internal nav-link">Cori</a>
  - <a href="#macos-apple-darwin" class="reference internal nav-link">MacOS
    / Apple Darwin</a>
  - <a href="#mpcdf-hpc-systems" class="reference internal nav-link">MPCDF
    HPC Systems</a>
- <a href="#file-formats" class="reference internal nav-link">File
  formats</a>
  - <a href="#installing-netcdf-from-source"
    class="reference internal nav-link">Installing NetCDF from source</a>
- <a href="#openmp" class="reference internal nav-link">OpenMP</a>
- <a href="#sundials" class="reference internal nav-link">SUNDIALS</a>
- <a href="#petsc" class="reference internal nav-link">PETSc</a>
- <a href="#lapack" class="reference internal nav-link">LAPACK</a>
- <a href="#mpi-compilers" class="reference internal nav-link">MPI
  compilers</a>
- <a href="#installing-fftw-from-source"
  class="reference internal nav-link">Installing FFTW from source</a>
- <a href="#compiling-and-running-under-aix"
  class="reference internal nav-link">Compiling and running under AIX</a>
  - <a href="#sundials-under-aix"
    class="reference internal nav-link">SUNDIALS under AIX</a>
  - <a href="#compiling-on-windows"
    class="reference internal nav-link">Compiling on Windows</a>
- <a href="#issues" class="reference internal nav-link">Issues</a>
  - <a href="#wrong-install-script"
    class="reference internal nav-link">Wrong install script</a>
  - <a href="#compiling-cvode-cxx-fails"
    class="reference internal nav-link">Compiling cvode.cxx fails</a>
  - <a href="#compiling-with-ibm-xlc-compiler-fails"
    class="reference internal nav-link">Compiling with IBM xlC compiler
    fails</a>
  - <a href="#compiling-fails-after-changing-branch"
    class="reference internal nav-link">Compiling fails after changing
    branch</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="advanced-installation-options" class="section">

<span id="sec-advancedinstall"></span>

# Advanced installation options<a href="#advanced-installation-options" class="headerlink"
title="Permalink to this heading">#</a>

This section describes some common issues encountered when configuring
and compiling BOUT++, how to manually install dependencies if they are
not available, and how to configure optional libraries like SUNDIALS and
PETSc.

<div id="optimisation-and-run-time-checking" class="section">

## Optimisation and run-time checking<a href="#optimisation-and-run-time-checking" class="headerlink"
title="Permalink to this heading">#</a>

Configure with <span class="pre">`-DCHECK=3`</span> enables a lot of
checks of operations performed by the field objects. This is very useful
for debugging a code, and can be omitted once bugs have been removed.
<span class="pre">`-DCHECK=2`</span> enables less checking, especially
the computationally rather expensive ones, while
<span class="pre">`-DCHECK=0`</span> disables most checks.

For (sometimes) more useful error messages, there is the
<span class="pre">`-DBOUT_ENABLE_TRACK=ON`</span> option. This keeps
track of the names of variables and includes these in error messages.

To get a backtrace, you can set the environment variable
<span class="pre">`BOUT_SHOW_BACKTRACE`</span> in order for the
exception to include the backtrace.

To enable optimization, configure with appropriate flags for your
compiler, e.g. with
<span class="pre">`-DCMAKE_CXX_FLAGS="`</span>` `<span class="pre">`-O3`</span>` `<span class="pre">`"`</span>
for a gnu compiler.

</div>

<div id="install-dependencies" class="section">

## Install dependencies:<a href="#install-dependencies" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ provides a way to install some (optional) dependencies that are
not always found on HPC systems. To do this, run from your BOUT++ source
directory:

<div class="highlight-bash notranslate">

<div class="highlight">

    bin/bout-build-deps.sh
    # or without any checks:
    CHECK=no bin/bout-build-deps.sh
    # or with openmp - not tested, maybe not good to add it to FFTW
    PETSCFLAGS=--with-openmp=1 FFTWFLAGS="--enable-avx512 --enable-avx-128-fma --with-openmp --enable-threads" bin/bout-build-deps.sh
    # and add "-DBOUT_ENABLE_OPENMP=ON" to cmake configure line

</div>

</div>

Infos about options and further info can be obtained by running:

<div class="highlight-bash notranslate">

<div class="highlight">

    bin/bout-build-deps.sh --help

</div>

</div>

If the script fails, it might be fixed by removing the folders that are
used for compiling and installing, and start again.

</div>

<div id="machine-specific-installation" class="section">

<span id="sec-machine-specific"></span>

## Machine-specific installation<a href="#machine-specific-installation" class="headerlink"
title="Permalink to this heading">#</a>

These are some configurations which have been found to work on
particular machines. There is also the repo
<a href="https://github.com/boutproject/BOUT-configs"
class="github reference external">boutproject/BOUT-configs</a> which
provides scripts for one or two line compilation, with dependencies, of
known-good versions on several machines (different machines are in
different branches).

<div id="archer" class="section">

### Archer<a href="#archer" class="headerlink"
title="Permalink to this heading">#</a>

As of 20th April 2018, the following configuration should work

<div class="highlight-bash notranslate">

<div class="highlight">

    $ module swap PrgEnv-cray PrgEnv-gnu/5.1.29
    $ module load fftw
    $ module load archer-netcdf/4.1.3

</div>

</div>

When using CMake on Cray systems like Archer, you need to pass
<span class="pre">`-DCMAKE_SYSTEM_NAME=CrayLinuxEnvironment`</span> so
that the Cray compiler wrappers are detected properly.

</div>

<div id="cori" class="section">

### Cori<a href="#cori" class="headerlink"
title="Permalink to this heading">#</a>

First set up the environment by loading the correct modules. For Bash
shell use:

<div class="highlight-bash notranslate">

<div class="highlight">

    source config/cori/setup-env-cgpu.sh

</div>

</div>

and for C shell:

<div class="highlight-csh notranslate">

<div class="highlight">

    source config/cori/setup-env-cgpu.sh

</div>

</div>

Then configure BOUT++ by running a script which calls CMake. Under bash:

<div class="highlight-bash notranslate">

<div class="highlight">

    ./config/cori/config-bout-cgpu.sh

</div>

</div>

and C shell:

<div class="highlight-csh notranslate">

<div class="highlight">

    ./config/cori/config-bout-cgpu.csh

</div>

</div>

At the time of writing, Hypre linking is not working with CUDA. If you
come across errors with the above configuration, try turning off Hypre
support:

<div class="highlight-bash notranslate">

<div class="highlight">

    ./config/cori/config-bout-cgpu-nohypre.sh

</div>

</div>

or

<div class="highlight-csh notranslate">

<div class="highlight">

    ./config/cori/config-bout-cgpu-nohypre.csh

</div>

</div>

See section <a href="gpu_support.html#sec-gpusupport"
class="reference internal"><span class="std std-ref">GPU
support</span></a> for details of compiling and running on GPU machines,
including Cori. Note that in order to access GPU nodes a request must be
made through <a href="https://nersc.servicenowservices.com/"
class="reference external">NERSC services</a>.

</div>

<div id="macos-apple-darwin" class="section">

### MacOS / Apple Darwin<a href="#macos-apple-darwin" class="headerlink"
title="Permalink to this heading">#</a>

Compiling with Apple Clang 12, the following configuration has been
known to work

<div class="highlight-tcsh notranslate">

<div class="highlight">

    cmake . -B <build-directory> -DBOUT_ENABLE_BACKTRACE=Off -DBUILD_SHARED_LIBS=Off -DBOUT_USE_NLS=Off -DBOUT_USE_UUID_SYSTEM_GENERATOR=Off
    cd <build-directory>
    cmake --build <build-directory>

</div>

</div>

where <span class="pre">`<build-directory>`</span> is the path to the
build directory

</div>

<div id="mpcdf-hpc-systems" class="section">

### MPCDF HPC Systems<a href="#mpcdf-hpc-systems" class="headerlink"
title="Permalink to this heading">#</a>

After cloning BOUT-dev and checking out the branch you want (e.g.
db-outer), run: .. code-block:: bash

> <div>
>
> module purge \# or at least onload intel module load gcc/13
> anaconda/3/2021.11 impi/2021.9 hdf5-serial/1.12.2 mkl/2022.0
> netcdf-serial/4.8.1 fftw-mpi/3.3.10 BUILD=/ptmp/$USER/bout-deps
> NO_HDF5=1 NO_NETCDF=1 NO_FFTW=1 bin/bout-build-deps.sh
>
> </div>

and follow the instructions for configuring BOUT++. To enable openMP for
a production run use:

<div class="highlight-bash notranslate">

<div class="highlight">

    module load bout-dep
    cmake .. -DBOUT_USE_NETCDF=ON -DnetCDFCxx_ROOT=$BOUT_DEP \
      -DBOUT_USE_PETSC=ON -DPETSC_DIR=$BOUT_DEP \
      -DBOUT_USE_FFTW=ON \
      -DBOUT_USE_SUNDIALS=ON -DSUNDIALS_ROOT=$BOUT_DEP \
      -DBOUT_ENABLE_OPENMP=OFF \
      -DCMAKE_BUILD_TYPE=Release

</div>

</div>

</div>

</div>

<div id="file-formats" class="section">

## File formats<a href="#file-formats" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ can currently use the
<a href="https://www.unidata.ucar.edu/software/netcdf/"
class="reference external">NetCDF-4</a> file format and the ADIOS2
library for high-performance parallel output.

NetCDF is a widely used format and has many tools for viewing and
manipulating files.

BOUT++ will look for <span class="pre">`ncxx4-config`</span> or
<span class="pre">`nc-config`</span> in your
<span class="pre">`$PATH`</span>. If it cannot find the libraries, or
finds a different version than the one you want, you can point it at the
correct version using:

<div class="highlight-console notranslate">

<div class="highlight">

    cmake -S .. -B . -DBOUT_USE_NETCDF=ON -DnetCDFCxx_ROOT=/path/to/ncxx4-config

</div>

</div>

where <span class="pre">`/path/to/ncxx4-config`</span> is the location
of the <span class="pre">`ncxx4-config`</span> tool
(<span class="pre">`nc-config`</span> will also work, but
<span class="pre">`ncxx4-config`</span> is preferred).

<div id="installing-netcdf-from-source" class="section">

<span id="sec-netcdf-from-source"></span>

### Installing NetCDF from source<a href="#installing-netcdf-from-source" class="headerlink"
title="Permalink to this heading">#</a>

The latest versions of NetCDF have separated out the C++ API from the
main C library. As a result, you will need to download and install both.
Download the latest versions of the NetCDF-C and NetCDF-4 C++ libraries
from <a href="https://www.unidata.ucar.edu/downloads/netcdf"
class="reference external">https://www.unidata.ucar.edu/downloads/netcdf</a>.
As of September 2020, these are versions 4.7.4 and 4.3.1 respectively.

Untar the file and ’cd’ into the resulting directory:

<div class="highlight-console notranslate">

<div class="highlight">

    $ tar -xzvf netcdf-4.7.4.tar.gz
    $ cd netcdf-4.7.4

</div>

</div>

Then run <span class="pre">`configure`</span>,
<span class="pre">`make`</span> and
<span class="pre">`make`</span>` `<span class="pre">`install`</span>:

<div class="highlight-console notranslate">

<div class="highlight">

    $ ./configure --prefix=$HOME/local
    $ make
    $ make install

</div>

</div>

Sometimes configure can fail, in which case try disabling Fortran:

<div class="highlight-console notranslate">

<div class="highlight">

    $ ./configure --prefix=$HOME/local --disable-fortran
    $ make
    $ make install

</div>

</div>

Similarly for the C++ API:

<div class="highlight-console notranslate">

<div class="highlight">

    $ tar -xzvf netcdf-cxx4-4.3.1.tar.gz
    $ cd netcdf-cxx4-4.3.1
    $ ./configure --prefix=$HOME/local
    $ make
    $ make install

</div>

</div>

You may need to set a couple of environment variables as well:

<div class="highlight-console notranslate">

<div class="highlight">

    $ export PATH=$HOME/local/bin:$PATH
    $ export LD_LIBRARY_PATH=$HOME/local/lib:$LD_LIBRARY_PATH

</div>

</div>

You should check where NetCDF actually installed its libraries. On some
systems this will be <span class="pre">`$HOME/local/lib`</span>, but on
others it may be, e.g. <span class="pre">`$HOME/local/lib64`</span>.
Check which it is, and set <span class="pre">`$LD_LIBRARY_PATH`</span>
appropriately.

</div>

</div>

<div id="openmp" class="section">

## OpenMP<a href="#openmp" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ can make use of OpenMP parallelism. To enable OpenMP, use the
<span class="pre">`-DBOUT_ENABLE_OPENMP=ON`</span> flag to configure:

<div class="highlight-console notranslate">

<div class="highlight">

    cmake -S .. -B . -DBOUT_ENABLE_OPENMP=ON

</div>

</div>

OpenMP can be used to parallelise in more directions than can be
achieved with MPI alone. For example, it is currently difficult to
parallelise in X using pure MPI if FCI is used, and impossible to
parallelise at all in Z with pure MPI.

OpenMP is in a large number of places now, such that a decent speed-up
can be achieved with OpenMP alone. Hybrid parallelisation with both MPI
and OpenMP can lead to more significant speed-ups, but it sometimes
requires some fine tuning of numerical parameters in order to achieve
this. This greatly depends on the details not just of your system, but
also your particular problem. We have tried to choose “sensible”
defaults that will work well for the most common cases, but this is not
always possible. You may need to perform some testing yourself to find
e.g. the optimum split of OpenMP threads and MPI ranks.

One such parameter that can potentially have a significant effect (for
some problem sizes on some machines) is setting the OpenMP schedule used
in some of the OpenMP loops (specifically those using
<span class="pre">`BOUT_FOR`</span>). This can be set using:

<div class="highlight-console notranslate">

<div class="highlight">

    cmake . -DBOUT_ENABLE_OPENMP=ON -DBOUT_OPENMP_SCHEDULE=<schedule>

</div>

</div>

with <span class="pre">`<schedule>`</span> being one of:
<span class="pre">`static`</span> (the default),
<span class="pre">`dynamic`</span>, <span class="pre">`guided`</span>,
<span class="pre">`auto`</span> or <span class="pre">`runtime`</span>.

<div class="admonition note">

Note

If you want to use OpenMP with Clang, you will need Clang 3.7+, and
either <span class="pre">`libomp`</span> or
<span class="pre">`libiomp`</span>.

You will be able to compile BOUT++ with OpenMP with lower versions of
Clang, or using the GNU OpenMP library
<span class="pre">`libgomp`</span>, but it will only run with a single
thread.

</div>

<div class="admonition note">

Note

By default PVODE is built without OpenMP support. To enable this add
<span class="pre">`--enable-pvode-openmp`</span> to the configure
command.

</div>

<div class="admonition note">

Note

OpenMP will attempt to use all available threads by default. This can
cause oversubscription problems on certain systems. You can limit the
number of threads OpenMP uses with the
<span class="pre">`OMP_NUM_THREADS`</span> environment variable. See
your system documentation for more details.

</div>

</div>

<div id="sundials" class="section">

<span id="sec-sundials"></span>

## SUNDIALS<a href="#sundials" class="headerlink"
title="Permalink to this heading">#</a>

The BOUT++ distribution includes a 1998 version of CVODE (then called
PVODE) by Scott D. Cohen and Alan C. Hindmarsh, which is the default
time integration solver. Whilst no serious bugs have been found in this
code (as far as the authors are aware of), several features such as
user-supplied preconditioners and constraints cannot be used with this
solver. Currently, BOUT++ also supports the SUNDIALS solvers CVODE, IDA
and ARKODE which are available from
<a href="https://computation.llnl.gov/casc/sundials/main.html"
class="reference external">https://computation.llnl.gov/casc/sundials/main.html</a>.

<div class="admonition note">

Note

BOUT++ currently supports SUNDIALS \> 2.6, up to 6.7.0 as of January
2024. It is advisable to use the highest possible version. Support for
SUNDIALS versions \< 4 will be removed in the next release.

</div>

The full installation guide is found in the downloaded
<span class="pre">`.tar.gz`</span>, but we will provide a step-by-step
guide to install it and make it compatible with BOUT++ here:

<div class="highlight-console notranslate">

<div class="highlight">

    $ tar -xzvf sundials-5.4.0.tar.gz
    $ cd sundials-5.4.0
    $ mkdir build && cd build

    $ cmake .. \
      -DCMAKE_INSTALL_PREFIX=$HOME/local \
      -DLAPACK_ENABLE=ON \
      -DOPENMP_ENABLE=ON \
      -DMPI_ENABLE=ON \
      -DCMAKE_C_COMPILER=$(which mpicc) \
      -DCMAKE_CXX_COMPILER=$(which mpicxx) \

    $ make
    $ make test
    $ make install

</div>

</div>

The SUNDIALS IDA solver is a Differential-Algebraic Equation (DAE)
solver, which evolves a system of the form
<span class="math notranslate nohighlight">\\\mathbf{f}(\mathbf{u},\dot{\mathbf{u}},t)
= 0\\</span>. This allows algebraic constraints on variables to be
specified.

Use the
<span class="pre">`-DBOUT_USE_SUNDIALS=ON`</span>` `<span class="pre">`-DSUNDIALS_ROOT=`</span>
option to configure BOUT++ with SUNDIALS:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake . -DBOUT_USE_SUNDIALS=ON -DSUNDIALS_ROOT=/path/to/sundials/install

</div>

</div>

SUNDIALS will allow you to select at run-time which solver to use. See
<a href="time_integration.html#sec-timeoptions"
class="reference internal"><span class="std std-ref">Options</span></a>
for more details on how to do this.

Notes:

- If compiling SUNDIALS, make sure that it is configured with MPI
  (<span class="pre">`MPI_ENABLE=ON`</span>)

</div>

<div id="petsc" class="section">

<span id="sec-petsc-install"></span>

## PETSc<a href="#petsc" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ can use PETSc <a href="https://www.mcs.anl.gov/petsc/"
class="reference external">https://www.mcs.anl.gov/petsc/</a> for
time-integration and for solving elliptic problems, such as inverting
Poisson and Helmholtz equations.

Currently, BOUT++ supports PETSc versions 3.7 - 3.23. More recent
versions may well work, but the PETSc API does sometimes change in
backward-incompatible ways, so this is not guaranteed. To install PETSc
version 3.19, use the following steps:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cd ~
    $ wget https://ftp.mcs.anl.gov/pub/petsc/release-snapshots/petsc-3.19.1.tar.gz
    $ tar -xzvf petsc-3.19.1.tar.gz
    $ cd petsc-3.19.1

</div>

</div>

Use the following configure options to ensure PETSc is compatible with
BOUT++:

<div class="highlight-console notranslate">

<div class="highlight">

    $ ./configure \
      --with-mpi=yes \
      --with-precision=double \
      --with-scalar-type=real \
      --with-shared-libraries=1 \
      --with-debugging=0 \
      {C,CXX,F}OPTFLAGS="-O3 -march=native" \
      --prefix=$HOME/local/petsc-version-options

</div>

</div>

You may also wish to change to
<span class="pre">`--with-debugging=yes`</span> in the arguments to
<span class="pre">`./configure`</span>, in order to allow debugging of
PETSc. The optimisation flags need changing for cross compiling or non
gcc compilers. Set a different prefix to change the place PETSc will be
installed to.

<div class="admonition note">

Note

If you build BOUT++ using a standalone version of SUNDIALS, it is
advisable to not also build PETSc with SUNDIALS.

</div>

<div class="admonition note">

Note

It is also possible to get PETSc to download and install MUMPS, by
adding:

<div class="highlight-console notranslate">

<div class="highlight">

    --download-mumps \
    --download-scalapack \
    --download-blacs \
    --download-fblaslapack=1 \
    --download-parmetis \
    --download-ptscotch \
    --download-metis

</div>

</div>

to <span class="pre">`./configure`</span>.

</div>

To make PETSc, type what is shown in the terminal output after the
configure step, something like:

<div class="highlight-console notranslate">

<div class="highlight">

    $ make PETSC_DIR=$HOME/petsc-3.19.1 PETSC_ARCH=arch-linux2-cxx-debug all

</div>

</div>

Should BLAS, LAPACK, or any other packages be missing, you will get an
error, and a suggestion that you can append
<span class="pre">`--download-name-of-package`</span> to the
<span class="pre">`./configure`</span> line.

You may want to test that everything is configured properly. To do this
replace <span class="pre">`all`</span> with
<span class="pre">`test`</span> in the make command. It should be
something like:

<div class="highlight-console notranslate">

<div class="highlight">

    $ make PETSC_DIR=$HOME/petsc-3.19.1 PETSC_ARCH=arch-linux2-cxx-debug test

</div>

</div>

To install PETSc, replace
<span class="pre">`test`</span>/<span class="pre">`all`</span> with
<span class="pre">`install`</span> and run something like:

<div class="highlight-console notranslate">

<div class="highlight">

    $ make PETSC_DIR=$HOME/petsc-3.19.1 PETSC_ARCH=arch-linux2-cxx-debug install

</div>

</div>

To configure BOUT++ with PETSc, add to the cmake configure command:

<div class="highlight-console notranslate">

<div class="highlight">

    -DBOUT_USE_PETSC=ON -DPETSC_DIR=$HOME/local/petsc-version-options

</div>

</div>

For example like this:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake -S . -B <build-directory> -DBOUT_USE_PETSC=ON -DPETSC_DIR=$HOME/local/petsc-version-options

</div>

</div>

BOUT++ can also work with PETSc if it has not been installed. In this
case ensure that <span class="pre">`PETSC_DIR`</span> and
<span class="pre">`PETSC_ARCH`</span> are set, for example like this:

<div class="highlight-console notranslate">

<div class="highlight">

    $ PETSC_DIR=/path/to/petsc PETSC_ARCH=arch-linux2-cxx-debug cmake -DBOUT_USE_PETSC=ON

</div>

</div>

</div>

<div id="lapack" class="section">

<span id="sec-lapack"></span>

## LAPACK<a href="#lapack" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ comes with linear solvers for tridiagonal and band-diagonal
systems. Some implementations of these solvers (for example Laplacian
inversion, section
<a href="laplacian.html#sec-laplacian" class="reference internal"><span
class="std std-ref">Laplacian inversion</span></a>) use LAPACK for
efficient serial performance. This does not add new features, but may be
faster in some cases. LAPACK is however written in FORTRAN 77, which can
cause linking headaches. To enable these routines use:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake -S . -B <build-directory> -DBOUT_USE_LAPACK=ON

</div>

</div>

and to specify a non-standard path:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cmake -S . -B <build-directory> -DBOUT_USE_LAPACK=ON -DLAPACK_ROOT=/path/to/lapack

</div>

</div>

</div>

<div id="mpi-compilers" class="section">

## MPI compilers<a href="#mpi-compilers" class="headerlink"
title="Permalink to this heading">#</a>

These are usually called something like mpicc and mpiCC (or mpicxx), and
the configure script will look for several common names. If your
compilers aren’t recognised then check the <a
href="https://cmake.org/cmake/help/latest/module/FindMPI.html#variables-for-locating-mpi"
class="reference external">cmake documentation for MPI</a>

NOTES:

- On LLNL’s Grendel, mpicxx is broken. Use mpiCC instead by passing
  “MPICXX=mpiCC” to configure. Also need to specify this to NetCDF
  library by passing “CXX=mpiCC” to NetCDF configure.

</div>

<div id="installing-fftw-from-source" class="section">

<span id="sec-fftw-from-source"></span>

## Installing FFTW from source<a href="#installing-fftw-from-source" class="headerlink"
title="Permalink to this heading">#</a>

If you haven’t already, create directories “install” and “local” in your
home directory:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cd
    $ mkdir install
    $ mkdir local

</div>

</div>

Download the latest stable version from
<a href="http://www.fftw.org/download.html"
class="reference external">http://www.fftw.org/download.html</a> into
the “install” directory. At the time of writing, this was called
<span class="pre">`fftw-3.3.2.tar.gz`</span>. Untar this file, and ’cd’
into the resulting directory. As with the MPI compiler, configure and
install the FFTW library into <span class="pre">`$HOME/local`</span> by
running:

<div class="highlight-console notranslate">

<div class="highlight">

    $ ./configure --prefix=$HOME/local
    $ make
    $ make install

</div>

</div>

</div>

<div id="compiling-and-running-under-aix" class="section">

## Compiling and running under AIX<a href="#compiling-and-running-under-aix" class="headerlink"
title="Permalink to this heading">#</a>

Most development and running of BOUT++ is done under Linux, with the
occasional FreeBSD and OSX. The configuration scripts are therefore
heavily tested on these architectures. IBM’s POWER architecture however
runs AIX, which has some crucial differences which make compiling a
pain.

- Under Linux/BSD, it’s usual for a Fortran routine
  <span class="pre">`foo`</span> to appear under C as
  <span class="pre">`foo_`</span>, whilst under AIX the name is
  unchanged

- MPI compiler scripts are usually given the names
  <span class="pre">`mpicc`</span> and either
  <span class="pre">`mpiCC`</span> or <span class="pre">`mpicxx`</span>.
  AIX uses <span class="pre">`mpcc`</span> and
  <span class="pre">`mpCC`</span>.

- Like BSD, the <span class="pre">`make`</span> command isn’t compatible
  with GNU make, so you have to run <span class="pre">`gmake`</span> to
  compile everything.

- The POWER architecture is big-endian, different to the little endian
  Intel and AMD chips. This can cause problems with binary file formats.

<div id="sundials-under-aix" class="section">

### SUNDIALS under AIX<a href="#sundials-under-aix" class="headerlink"
title="Permalink to this heading">#</a>

To compile SUNDIALS, use:

<div class="highlight-bash notranslate">

<div class="highlight">

    export CC=cc
    export CXX=xlC
    export F77=xlf
    export OBJECT_MODE=64
    ./configure --prefix=$HOME/local/ --with-mpicc=mpcc --with-mpif77=mpxlf CFLAGS=-maix64

</div>

</div>

You may get an error message like

<div class="highlight-bash notranslate">

<div class="highlight">

    make: Not a recognized flag: w

</div>

</div>

This is because the AIX <span class="pre">`make`</span> is being used,
rather than <span class="pre">`gmake`</span>. The easiest way to fix
this is to make a link to <span class="pre">`gmake`</span> in your local
bin directory

<div class="highlight-bash notranslate">

<div class="highlight">

    ln -s /usr/bin/gmake $HOME/local/bin/make

</div>

</div>

Running
<span class="pre">`which`</span>` `<span class="pre">`make`</span>
should now point to this <span class="pre">`local/bin/make`</span>, and
if not then you need to make sure that your bin directory appears first
in the <span class="pre">`PATH`</span>

<div class="highlight-bash notranslate">

<div class="highlight">

    export PATH=$HOME/local/bin:$PATH

</div>

</div>

If you see an error like this

<div class="highlight-bash notranslate">

<div class="highlight">

    ar: 0707-126 ../../src/sundials/sundials_math.o is not valid with the current object file mode.
            Use the -X option to specify the desired object mode.

</div>

</div>

then you need to set the environment variable
<span class="pre">`OBJECT_MODE`</span>

<div class="highlight-bash notranslate">

<div class="highlight">

    export OBJECT_MODE=64

</div>

</div>

Configuring BOUT++, you may get the error

<div class="highlight-bash notranslate">

<div class="highlight">

    configure: error: C compiler cannot create executables

</div>

</div>

In that case, you can try using:

<div class="highlight-bash notranslate">

<div class="highlight">

    ./configure CFLAGS="-maix64"

</div>

</div>

When compiling, you may see warnings:

<div class="highlight-bash notranslate">

<div class="highlight">

    xlC_r: 1501-216 (W) command option -64 is not recognized - passed to ld

</div>

</div>

At this point, the main BOUT++ library should compile, and you can try
compiling one of the examples.

<div class="highlight-bash notranslate">

<div class="highlight">

    ld: 0711-317 ERROR: Undefined symbol: .NcError::NcError(NcError::Behavior)
    ld: 0711-317 ERROR: Undefined symbol: .NcFile::is_valid() const
    ld: 0711-317 ERROR: Undefined symbol: .NcError::~NcError()
    ld: 0711-317 ERROR: Undefined symbol: .NcFile::get_dim(const char*) const

</div>

</div>

This is probably because the NetCDF libraries are 32-bit, whilst BOUT++
has been compiled as 64-bit. You can try compiling BOUT++ as 32-bit

<div class="highlight-bash notranslate">

<div class="highlight">

    export OBJECT_MODE=32
    ./configure CFLAGS="-maix32"
    gmake

</div>

</div>

If you still get undefined symbols, then go back to 64-bit, and edit
make.config, replacing <span class="pre">`-lnetcdf_c++`</span> with
-lnetcdf64_c++, and <span class="pre">`-lnetcdf`</span> with -lnetcdf64.
This can be done by running

<div class="highlight-bash notranslate">

<div class="highlight">

    sed 's/netcdf/netcdf64/g' make.config > make.config.new
    mv make.config.new make.config

</div>

</div>

</div>

<div id="compiling-on-windows" class="section">

### Compiling on Windows<a href="#compiling-on-windows" class="headerlink"
title="Permalink to this heading">#</a>

It is possible to compile BOUT++ on Windows using the CMake interface.
Support is currently very experimental, and some features do not work.
Testing has been done with MSVC 19.24 and Visual Studio 16.4, although
previous versions may still work.

The main difficulty of using BOUT++ on Windows is getting the
dependencies sorted. The easiest way to install dependencies on Windows
is using <a href="https://github.com/microsoft/vcpkg/"
class="reference external">vcpkg</a>. You may need to set the CMake
toolchain file if calling <span class="pre">`cmake`</span> from
PowerShell, or on older versions of Visual Studio. This will be a file
somewhere like
<span class="pre">`C:/vcpkg/scripts/buildsystems/vcpkg.cmake`</span>

The minimal required CMake options are as follows:

<div class="highlight-bash notranslate">

<div class="highlight">

    -DBOUT_ENABLE_BACKTRACE=OFF \
    -DCMAKE_CXX_FLAGS="/permissive- /EHsc /bigobj" \
    -DBUILD_SHARED_LIBS=OFF

</div>

</div>

<span class="pre">`ENABLE_BACKTRACE`</span> must be turned off due to
the currently required <span class="pre">`addr2line`</span> executable
not being available on Windows.

The following flags for the MSVC compiler are required:

- <span class="pre">`/permissive-`</span> for standards compliance, such
  as treating the binary operator alternative tokens
  (<span class="pre">`and`</span>, <span class="pre">`or`</span>, etc)
  as tokens

- <span class="pre">`/EHsc`</span> for standard C++ exception handling,
  and to assume that
  <span class="pre">`extern`</span>` `<span class="pre">`"C"`</span>
  functions never throw

- <span class="pre">`/bigobj`</span> to increase the number of sections
  in the .obj file, required for the template-heavy derivatives
  machinery

No modification to the source has been done to export the correct
symbols for shared libraries on Windows, so you must either specifiy
<span class="pre">`-DBUILD_SHARED_LIBS=OFF`</span> to only build static
libraries, or, if you really want shared libraries,
<span class="pre">`-DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=ON`</span>. The
latter is untested, use at your own risk!

The unit tests should all pass, but most of the integrated tests will
not run work out of the box yet as Windows doesn’t understand shabangs.
That is, without a file extension, it doesn’t know what program to use
to run <span class="pre">`runtest`</span>. The majority of the tests can
be run manually with
<span class="pre">`python.exe`</span>` `<span class="pre">`runtest`</span>.
You will stil need to set <span class="pre">`PYTHONPATH`</span> and have
a suitable Python environment.

</div>

</div>

<div id="issues" class="section">

## Issues<a href="#issues" class="headerlink"
title="Permalink to this heading">#</a>

<div id="wrong-install-script" class="section">

### Wrong install script<a href="#wrong-install-script" class="headerlink"
title="Permalink to this heading">#</a>

Before installing, make sure the correct version of
<span class="pre">`install`</span> is being used by running:

<div class="highlight-console notranslate">

<div class="highlight">

    $ which install

</div>

</div>

This should point to a system directory like
<span class="pre">`/usr/bin/install`</span>. Sometimes when IDL has been
installed, this points to the IDL install (e.g. something like
<span class="pre">`/usr/common/usg/idl/idl70/bin/install`</span> on
Franklin). A quick way to fix this is to create a link from your local
bin to the system install:

<div class="highlight-console notranslate">

<div class="highlight">

    $ ln -s /usr/bin/install $HOME/local/bin/

</div>

</div>

“which install” should now print the install in your local bin
directory.

</div>

<div id="compiling-cvode-cxx-fails" class="section">

### Compiling cvode.cxx fails<a href="#compiling-cvode-cxx-fails" class="headerlink"
title="Permalink to this heading">#</a>

Occasionally compiling the CVODE solver interface will fail with an
error similar to:

<div class="highlight-console notranslate">

<div class="highlight">

    cvode.cxx: In member function ‘virtual int CvodeSolver::init(rhsfunc, bool, int, BoutR...
    cvode.cxx:234:56: error: invalid conversion from ‘int (*)(CVINT...
    ...

</div>

</div>

This is caused by different sizes of ints used in different versions of
the CVODE library. The configure script tries to determine the correct
type to use, but may fail in unusual circumstances. To fix, edit
<span class="pre">`src/solver/impls/cvode/cvode.cxx`</span>, and change
line 48 from

<div class="highlight-cpp notranslate">

<div class="highlight">

    typedef int CVODEINT;

</div>

</div>

to

<div class="highlight-cpp notranslate">

<div class="highlight">

    typedef long CVODEINT;

</div>

</div>

</div>

<div id="compiling-with-ibm-xlc-compiler-fails" class="section">

### Compiling with IBM xlC compiler fails<a href="#compiling-with-ibm-xlc-compiler-fails" class="headerlink"
title="Permalink to this heading">#</a>

When using the <span class="pre">`xlC`</span> compiler, an error may
occur:

<div class="highlight-console notranslate">

<div class="highlight">

    variant.hpp(1568) parameter pack "Ts" was referenced but not expanded

</div>

</div>

The workaround is to change line 428 of
<span class="pre">`externalpackages/mpark.variant/include/mpark/lib.hpp`</span>
from:

<div class="highlight-console notranslate">

<div class="highlight">

    #ifdef MPARK_TYPE_PACK_ELEMENT

</div>

</div>

to:

<div class="highlight-console notranslate">

<div class="highlight">

    #ifdef CAUSES_ERROR // MPARK_TYPE_PACK_ELEMENT

</div>

</div>

This will force an alternate implementation of type_pack_element to be
defined. See also <a
href="https://software.intel.com/en-us/forums/intel-c-compiler/topic/501502"
class="reference external">https://software.intel.com/en-us/forums/intel-c-compiler/topic/501502</a>

</div>

<div id="compiling-fails-after-changing-branch" class="section">

### Compiling fails after changing branch<a href="#compiling-fails-after-changing-branch" class="headerlink"
title="Permalink to this heading">#</a>

If compiling fails after changing branch, for example from
<span class="pre">`master`</span> to <span class="pre">`next`</span>,
with an error like the following:

<div class="highlight-console notranslate">

<div class="highlight">

    $ make
    Downloading mpark.variant
    You need to run this command from the toplevel of the working tree.
    make[2]: *** [BOUT-dev/externalpackages/mpark.variant/include/mpark/variant.hpp] Error 1
    make[1]: *** [field] Error 2
    make: *** [src] Error 2

</div>

</div>

it’s possible something has gone wrong with the submodules. To fix, just
run:

<div class="highlight-console notranslate">

<div class="highlight">

    $ git submodule update --init --recursive  ./externalpackages/*

</div>

</div>

If you regularly work on two different branches and need to run the
above command a lot, you may consider telling git to automatically
update the submodules:

<div class="highlight-console notranslate">

<div class="highlight">

    git config submodule.recurse=true

</div>

</div>

This requires
<span class="pre">`git`</span>` `<span class="pre">`>=`</span>` `<span class="pre">`2.14`</span>.

</div>

</div>

</div>

<div class="prev-next-area">

<a href="installing.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Getting started

</div>

<a href="running_bout.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Running BOUT++

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#optimisation-and-run-time-checking"
  class="reference internal nav-link">Optimisation and run-time
  checking</a>
- <a href="#install-dependencies"
  class="reference internal nav-link">Install dependencies:</a>
- <a href="#machine-specific-installation"
  class="reference internal nav-link">Machine-specific installation</a>
  - <a href="#archer" class="reference internal nav-link">Archer</a>
  - <a href="#cori" class="reference internal nav-link">Cori</a>
  - <a href="#macos-apple-darwin" class="reference internal nav-link">MacOS
    / Apple Darwin</a>
  - <a href="#mpcdf-hpc-systems" class="reference internal nav-link">MPCDF
    HPC Systems</a>
- <a href="#file-formats" class="reference internal nav-link">File
  formats</a>
  - <a href="#installing-netcdf-from-source"
    class="reference internal nav-link">Installing NetCDF from source</a>
- <a href="#openmp" class="reference internal nav-link">OpenMP</a>
- <a href="#sundials" class="reference internal nav-link">SUNDIALS</a>
- <a href="#petsc" class="reference internal nav-link">PETSc</a>
- <a href="#lapack" class="reference internal nav-link">LAPACK</a>
- <a href="#mpi-compilers" class="reference internal nav-link">MPI
  compilers</a>
- <a href="#installing-fftw-from-source"
  class="reference internal nav-link">Installing FFTW from source</a>
- <a href="#compiling-and-running-under-aix"
  class="reference internal nav-link">Compiling and running under AIX</a>
  - <a href="#sundials-under-aix"
    class="reference internal nav-link">SUNDIALS under AIX</a>
  - <a href="#compiling-on-windows"
    class="reference internal nav-link">Compiling on Windows</a>
- <a href="#issues" class="reference internal nav-link">Issues</a>
  - <a href="#wrong-install-script"
    class="reference internal nav-link">Wrong install script</a>
  - <a href="#compiling-cvode-cxx-fails"
    class="reference internal nav-link">Compiling cvode.cxx fails</a>
  - <a href="#compiling-with-ibm-xlc-compiler-fails"
    class="reference internal nav-link">Compiling with IBM xlC compiler
    fails</a>
  - <a href="#compiling-fails-after-changing-branch"
    class="reference internal nav-link">Compiling fails after changing
    branch</a>

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
