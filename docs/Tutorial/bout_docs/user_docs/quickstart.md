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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/quickstart.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/quickstart.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/quickstart.rst"
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

# Quickstart Guide

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#prerequisites"
  class="reference internal nav-link">Prerequisites</a>
- <a href="#building-bout" class="reference internal nav-link">Building
  BOUT++</a>
- <a href="#running-bout" class="reference internal nav-link">Running
  BOUT++</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="quickstart-guide" class="section">

<span id="sec-quickstart"></span>

# Quickstart Guide<a href="#quickstart-guide" class="headerlink"
title="Permalink to this heading">#</a>

This section will quickly walk you through getting and building the
BOUT++ source code, and running one of the examples.

<div id="prerequisites" class="section">

## Prerequisites<a href="#prerequisites" class="headerlink"
title="Permalink to this heading">#</a>

To build BOUT++ and analyse the output of its models, you will need the
following tools and libraries:

- <span class="pre">`git`</span> (\>= 2.x)

- <a href="https://cmake.org/" class="reference external">CMake</a>

- a C++-17 compiler (for example, GCC \>= 8.0)

- an <span class="pre">`MPI`</span> implementation (for example OpenMPI
  or MPICH)

- The <a href="https://www.unidata.ucar.edu/downloads/netcdf"
  class="reference external">NetCDF C library</a>

- <a href="https://github.com/boutproject/xBOUT"
  class="reference external">xBOUT</a> (for analysis)

See
<a href="installing.html#sec-install" class="reference internal"><span
class="std std-ref">Getting started</span></a> and
<a href="advanced_install.html#sec-advancedinstall"
class="reference internal"><span class="std std-ref">Advanced
installation options</span></a> for more information on installing these
and other optional dependencies.

Make sure you have all of these installed, and in particular that
<span class="pre">`nc-config`</span> is in your
<span class="pre">`$PATH`</span>.

</div>

<div id="building-bout" class="section">

## Building BOUT++<a href="#building-bout" class="headerlink"
title="Permalink to this heading">#</a>

We’ll clone the BOUT++ repository and build it in separate directories.
We’re going to automatically download and built the netCDF C++ library
as part of building BOUT++:

<div class="highlight-console notranslate">

<div class="highlight">

    # Downloads the repo into BOUT-dev:
    $ git clone https://github.com/boutproject/BOUT-dev.git
    # Configure the build directory:
    $ cmake -S BOUT-dev -B build_bout -DBOUT_DOWNLOAD_NETCDF_CXX4=ON
    # Build the library with four threads:
    $ cmake --build build_bout -j 4
    # Build the conduction example:
    $ cmake --build build_bout --target conduction

</div>

</div>

This might take a few minutes to build the whole library, especially the
first time you build it.

Assuming that all went ok, you’ll now have built the
<a href="physics_models.html#sec-heat-conduction-model"
class="reference internal"><span class="std std-ref">Heat
conduction</span></a> physics model in
<span class="pre">`build_bout/examples/conduction`</span>.

</div>

<div id="running-bout" class="section">

## Running BOUT++<a href="#running-bout" class="headerlink"
title="Permalink to this heading">#</a>

We can now run the conduction example:

<div class="highlight-console notranslate">

<div class="highlight">

    $ cd build_bout/examples/conduction
    $ mpiexec -np 2 ./conduction

</div>

</div>

You should see some output like:

<div class="highlight-console notranslate">

<div class="highlight">

    BOUT++ version 5.1.0
    Revision: b3ee80bfa2ad9b875b69ab072a392b3f548efea8
    Code compiled on Jul 27 2022 at 18:13:23

    B.Dudson (University of York), M.Umansky (LLNL) 2007
    Based on BOUT by Xueqiao Xu, 1999

    Processor number: 0 of 2

    pid: 28302

    Compile-time options:
            Runtime error checking enabled, level 2
            Parallel NetCDF support disabled
            Metrics mode is 2D

    ...

    9.900e+00          1       1.99e-02     0.8    0.0    0.1   66.4   32.8
    1.000e+01         10       2.10e-02     3.8    0.0    0.1   64.6   31.5
    Step 100 of 100. Elapsed 0:00:02.0 ETA 0:00:00.0
    Run finished at  : Thu Jul 28 10:17:31 2022
    Run time : 2 s
            Option datadir = data (default)
            Option settingsfile = BOUT.settings (default)
    Writing options to file data/BOUT.settings
            Option time_report:show = 0 (default)

</div>

</div>

(where we’ve cut out lots of text from the middle!)

Your exact output will differ a bit from the above, particularly the
revision hash and dates/times.

We can now have a look at the results using xBOUT:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> import xbout
    >>> df = xbout.open_boutdataset("data/BOUT.dmp.*.nc")
    >>> df["T"].plot()
    >>> import matplotlib.pyplot as plt ; plt.show()

</div>

</div>

which should produce something similar to the following figure:

<figure id="id1" class="align-default">
<img src="../_images/quickstart_conduction_example.png"
alt="Heat conduction example" />
<figcaption><p><span class="caption-number">Fig. 1 </span><span
class="caption-text">A 1D heat conduction example shows how an initial
Gaussian temperature perturbation changes over time.</span><a
href="#id1" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

</div>

<div class="prev-next-area">

<a href="introduction.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Introduction

</div>

<a href="installing.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Getting started

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#prerequisites"
  class="reference internal nav-link">Prerequisites</a>
- <a href="#building-bout" class="reference internal nav-link">Building
  BOUT++</a>
- <a href="#running-bout" class="reference internal nav-link">Running
  BOUT++</a>

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
