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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/running_bout.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/running_bout.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/running_bout.rst"
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

# Running BOUT++

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#quick-start" class="reference internal nav-link">Quick
  start</a>
- <a href="#analysing-the-output-using-python"
  class="reference internal nav-link">Analysing the output using
  Python</a>
- <a href="#natural-language-support"
  class="reference internal nav-link">Natural language support</a>
- <a href="#when-things-go-wrong" class="reference internal nav-link">When
  things go wrong</a>
- <a href="#startup-output" class="reference internal nav-link">Startup
  output</a>
- <a href="#per-timestep-output"
  class="reference internal nav-link">Per-timestep output</a>
- <a href="#restarting-runs"
  class="reference internal nav-link">Restarting runs</a>
- <a href="#stopping-simulations"
  class="reference internal nav-link">Stopping simulations</a>
  - <a href="#stop-file" class="reference internal nav-link">Stop file</a>
  - <a href="#send-signal-usr1" class="reference internal nav-link">Send
    signal USR1</a>
- <a href="#manipulating-restart-files"
  class="reference internal nav-link">Manipulating restart files</a>
  - <a href="#changing-number-of-processors"
    class="reference internal nav-link">Changing number of processors</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="running-bout" class="section">

<span id="sec-running"></span>

# Running BOUT++<a href="#running-bout" class="headerlink"
title="Permalink to this heading">#</a>

<div id="quick-start" class="section">

## Quick start<a href="#quick-start" class="headerlink"
title="Permalink to this heading">#</a>

The <span class="pre">`examples/`</span> directory contains some example
physics models for a variety of fluid models. There are also some under
<span class="pre">`tests/integrated/`</span>, which often just run a
part of the code rather than a complete simulation. The simplest example
to start with is <span class="pre">`examples/conduction/`</span>. This
solves a single equation for a 3D scalar field
<span class="math notranslate nohighlight">\\T\\</span>:

<div class="math notranslate nohighlight">

\\\frac{\partial T}{\partial t} = \nabla\_{||}(\chi\partial\_{||} T)\\

</div>

There are several files involved:

- <span class="pre">`conduction.cxx`</span> contains the source code
  which specifies the equation to solve. See
  <a href="physics_models.html#sec-heat-conduction-model"
  class="reference internal"><span class="std std-ref">Heat
  conduction</span></a> for a line-by-line walkthrough of this file

- <span class="pre">`conduct_grid.nc`</span> is the grid file, which in
  this case just specifies the number of grid points in
  <span class="math notranslate nohighlight">\\X\\</span> and
  <span class="math notranslate nohighlight">\\Y\\</span>
  (<span class="pre">`nx`</span> & <span class="pre">`ny`</span>) with
  everything else being left as the default (e.g. grid spacings dx and
  dy are <span class="math notranslate nohighlight">\\1\\</span>, the
  metric tensor is the identity matrix). For details of the grid file
  format, see
  <a href="input_grids.html#sec-gridgen" class="reference internal"><span
  class="std std-ref">Generating input grids</span></a>.

- <span class="pre">`generate.py`</span> is a Python script to create
  the grid file. In this case it just writes nx and ny

- <span class="pre">`data/BOUT.inp`</span> is the settings file,
  specifying how many output timesteps to take, differencing schemes to
  use, and many other things. In this case it’s mostly empty so the
  defaults are used.

First you need to compile the example:

<div class="highlight-console notranslate">

<div class="highlight">

    $ gmake

</div>

</div>

which should print out something along the lines of:

<div class="highlight-console notranslate">

<div class="highlight">

    Compiling  conduction.cxx
    Linking conduction

</div>

</div>

If you get an error, most likely during the linking stage, you may need
to go back and make sure the libraries are all set up correctly. A
common problem is mixing MPI implementations, for example compiling
NetCDF using Open MPI and then BOUT++ with MPICH2. Unfortunately the
solution is to recompile everything with the same compiler.

Then try running the example. If you’re running on a standalone server,
desktop or laptop then try:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 2 ./conduction

</div>

</div>

If you’re running on a cluster or supercomputer, you should find out how
to submit jobs. This varies, but usually on these bigger machines there
will be a queueing system and you’ll need to use
<span class="pre">`qsub`</span>, <span class="pre">`msub`</span>,
<span class="pre">`llsubmit`</span> or similar to submit jobs.

When the example runs, it should print a lot of output. This is
recording all the settings being used by the code, and is also written
to log files for future reference. The test should take a few seconds to
run, and produce a bunch of files in the
<span class="pre">`data/`</span> subdirectory.

- <span class="pre">`BOUT.log.*`</span> contains a log from each
  process, so because we ran with “-np 2” there should be 2 logs. The
  one from processor
  <span class="math notranslate nohighlight">\\0\\</span> will be the
  same as what was printed to the screen. This is mainly useful because
  if one process crashes it may only put an error message into its own
  log.

- <span class="pre">`BOUT.settings`</span> contains all the options used
  in the code, including options which were not set and used the default
  values. It’s in the same format as BOUT.inp, so can be renamed and
  used to re-run simulations if needed. In some cases the options used
  have documentation, with a brief explanation of how they are used. In
  most cases the type the option is used as (e.g.
  <span class="pre">`int`</span>, <span class="pre">`BoutReal`</span> or
  <span class="pre">`bool`</span>) is given.

- <span class="pre">`BOUT.restart.*.nc`</span> are the restart files for
  the last time point. Currently each processor saves its own state in a
  separate file, but there is experimental support for parallel I/O. For
  the settings, see <a href="bout_options.html#sec-iooptions"
  class="reference internal"><span class="std std-ref">Input and
  Output</span></a>.

- <span class="pre">`BOUT.dmp.*.nc`</span> contain the output data,
  including time history. As with the restart files, each processor
  currently outputs a separate file.

Restart files allow the run to be restarted from where they left off:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 2 ./conduction restart

</div>

</div>

This will delete the output data
<span class="pre">`BOUT.dmp.*.nc`</span> files, and start again. If you
want to keep the output from the first run, add “append”:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 2 ./conduction restart append

</div>

</div>

which will then append any new outputs to the end of the old data files.
For more information on restarting, see
<a href="#sec-restarting" class="reference internal"><span
class="std std-ref">Restarting runs</span></a>.

To see some of the other command-line options try “-h”:

<div class="highlight-console notranslate">

<div class="highlight">

    $ ./conduction -h

</div>

</div>

and see the section on options
(<a href="bout_options.html#sec-options" class="reference internal"><span
class="std std-ref">BOUT++ options</span></a>).

There is also a python tool called
<a href="https://pypi.org/project/bout-runners/"
class="reference external"><span class="pre"><code
class="docutils literal notranslate">bout_runners</code></span></a>
which can be used for executing <span class="pre">`BOUT++`</span> runs.
In addition, this tool can be used to

- programmatically change parameters of a project in python

- keep track of all the metadata of the runs of the project

- automate the orchestration (including pre- and post-processing
  routines) of chains of runs locally or on a cluster

To analyse the output of the simulation, cd into the
<span class="pre">`data`</span> subdirectory and start Python.

</div>

<div id="analysing-the-output-using-python" class="section">

## Analysing the output using Python<a href="#analysing-the-output-using-python" class="headerlink"
title="Permalink to this heading">#</a>

The recommended tool for analysing BOUT++ output is xBOUT, a Python
library that provides analysis, plotting and animation with
human-readable syntax (no magic numbers!) using
<a href="http://xarray.pydata.org/en/stable/"
class="reference external">xarray</a>. See the xBOUT documentation
<a href="https://xbout.readthedocs.io/en/latest/"
class="reference external">xbout.readthedocs.io</a>.

There is also an older set of NumPy-based Python tools, described below.
In order to analyse the output of the simulation using Python, you will
first need to have set up python to use the BOUT++ libraries
<span class="pre">`boutdata`</span> and
<span class="pre">`boututils`</span>; see section
<a href="installing.html#sec-config-python"
class="reference internal"><span class="std std-ref">Python
configuration</span></a> for how to do this. The analysis routines have
some requirements such as SciPy; see section
<a href="output_and_post.html#sec-python-requirements"
class="reference internal"><span
class="std std-ref">Requirements</span></a> for details.

To print a list of variables in the output files, one way is to use the
<span class="pre">`DataFile`</span> class. This is a wrapper around the
various NetCDF libraries for python:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> from boututils.datafile import DataFile
    >>> DataFile("BOUT.dmp.0.nc").list()

</div>

</div>

To collect a variable, reading in the data as a NumPy-like
<span class="pre">`BoutArray`</span> array:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> from boutdata.collect import collect
    >>> T = collect("T")
    >>> T.shape

</div>

</div>

Note that the order of the indices is different in Python and IDL: In
Python, 4D variables are arranged as
<span class="pre">`[t,`</span>` `<span class="pre">`x,`</span>` `<span class="pre">`y,`</span>` `<span class="pre">`z]`</span>.

<span class="pre">`BoutArray`</span> as a thin wrapper for
<span class="pre">`numpy.ndarray`</span> which adds BOUT++ attributes.

To show an animation

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> from boututils.showdata import showdata
    >>> showdata(T[:,0,:,0])

</div>

</div>

The first index of the array passed to
<span class="pre">`showdata`</span> is assumed to be time, amd the
remaining indices are plotted. In this example we pass a 2D array
<span class="pre">`[t,y]`</span>, so <span class="pre">`showdata`</span>
will animate a line plot.

</div>

<div id="natural-language-support" class="section">

<span id="sec-run-nls"></span>

## Natural language support<a href="#natural-language-support" class="headerlink"
title="Permalink to this heading">#</a>

If you have locales installed, and configured the
<span class="pre">`locale`</span> path correctly (see
<a href="installing.html#sec-config-nls"
class="reference internal"><span class="std std-ref">Natural Language
Support</span></a>), then the <span class="pre">`LANG`</span>
environment variable selects the language to use. Currently BOUT++ only
has support for <span class="pre">`fr`</span>,
<span class="pre">`de`</span>, <span class="pre">`es`</span>,
<span class="pre">`zh_TW`</span> and <span class="pre">`zh_CN`</span>
locales e.g.

<div class="highlight-console notranslate">

<div class="highlight">

    LANG=zh_TW.utf8 ./conduction

</div>

</div>

which should produce an output like:

<div class="highlight-console notranslate">

<div class="highlight">

    BOUT++ 版 4.3.0
    版: 667c19c136fc3e72fcd7c7b2109d44886fdf818d
    MD5 checksum: 2263dc17fa414179c7ad87c3972f624b
    代碼於 Nov 21 2019 17:26:55 编译
    ...

</div>

</div>

or

<div class="highlight-console notranslate">

<div class="highlight">

    LANG=es_ES.utf8 ./conduction

</div>

</div>

which should produce:

<div class="highlight-console notranslate">

<div class="highlight">

    Versión de BOUT++ 4.3.0
    Revisión: 667c19c136fc3e72fcd7c7b2109d44886fdf818d
    MD5 checksum: 2263dc17fa414179c7ad87c3972f624b
    Código compilado en Nov 21 2019 en 17:26:55
    ...

</div>

</div>

The name of the locale (<span class="pre">`zh_TW.utf8`</span> or
<span class="pre">`es_ES.utf8`</span> above) can be different on
different machines. To see a list of available locales on your system
try running:

<div class="highlight-console notranslate">

<div class="highlight">

    locale -a

</div>

</div>

If you are missing a locale you need, see your distribution’s help, or
try this <a href="https://wiki.archlinux.org/index.php/locale"
class="reference external">Arch wiki page on locale</a>.

</div>

<div id="when-things-go-wrong" class="section">

## When things go wrong<a href="#when-things-go-wrong" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ is still under development, and so occasionally you may be lucky
enough to discover a new bug. This is particularly likely if you’re
modifying the physics module source code (see
<a href="physics_models.html#sec-equations"
class="reference internal"><span class="std std-ref">BOUT++ physics
models</span></a>) when you need a way to debug your code too.

- Check the end of each processor’s log file (tail data/BOUT.log.\*).
  When BOUT++ exits before it should, what is printed to screen is just
  the output from processor 0. If an error occurred on another processor
  then the error message will be written to it’s log file instead.

- By default when an error occurs a kind of stack trace is printed which
  shows which functions were being run (most recent first). This should
  give a good indication of where an error occurred. If this stack isn’t
  printed, make sure checking is set to level 2 or higher
  (<span class="pre">`cmake`</span>` `<span class="pre">`-DCHECK=2`</span>).

- If the error is due to non-finite numbers, increase the checking level
  (<span class="pre">`cmake`</span>` `<span class="pre">`-DCHECK=3`</span>)
  to perform more checking of values and (hopefully) find an error as
  soon as possible after it occurs.

- If the error is a segmentation fault, you can try a debugger such as
  gdb or totalview. You will likely need to compile with some debugging
  flags
  (<span class="pre">`cmake`</span>` `<span class="pre">`-DCMAKE_CXX_FLAGS="`</span>` `<span class="pre">`-g`</span>` `<span class="pre">`"`</span>).

- You can also enable exceptions on floating point errors
  (<span class="pre">`cmake`</span>` `<span class="pre">`-DBOUT_ENABLE_SIGFPE`</span>),
  though the majority of these types of errors should be caught with
  checking level set to 3.

- Expert users can try AddressSanitizer, which is a tool that comes with
  recent versions of GCC and Clang. To enable AddressSanitizer, include
  <span class="pre">`-fsanitize=leak`</span>` `<span class="pre">`-fsanitize=address`</span>` `<span class="pre">`-fsanitize=undefined`</span>
  in <span class="pre">`-DCMAKE_CXX_FLAGS`</span> when configuring
  BOUT++.

</div>

<div id="startup-output" class="section">

## Startup output<a href="#startup-output" class="headerlink"
title="Permalink to this heading">#</a>

When BOUT++ is run, it produces a lot of output initially, mainly
listing the options which have been used so you can check that it’s
doing what you think it should be. It’s generally a good idea to scan
over this see if there are any important warnings or errors. Each
processor outputs its own log file <span class="pre">`BOUT.log.#`</span>
and the log from processor 0 is also sent to the screen. This output may
look a little different if it’s out of date, but the general layout will
probably be the same. The exact order that options are printed in may
also vary between versions and models.

First comes the introductory blurb:

<div class="highlight-console notranslate">

<div class="highlight">

    BOUT++ version 4.4.0
    Revision: 7cfbc6890a82cb6b3b6c81870d8a8fca723de542
    Code compiled on Dec  7 2021 at 15:14:05

    B.Dudson (University of York), M.Umansky (LLNL) 2007
    Based on BOUT by Xueqiao Xu, 1999

</div>

</div>

The version number (4.4.0 here) gets increased occasionally after some
major feature has been added. To help match simulations to code
versions, the Git revision of the core BOUT++ code and the date and time
it was compiled is recorded. This information makes it possible to
verify precisely which version of the code was used for any given run.

The processor number comes next:

<div class="highlight-console notranslate">

<div class="highlight">

    Processor number: 0 of 1

</div>

</div>

This will always be processor number ’0’ on screen as only the output
from processor ’0’ is sent to the terminal.

The process ID (pid) is also printed:

<div class="highlight-console notranslate">

<div class="highlight">

    pid: 17835

</div>

</div>

which is useful for distinguishing multiple simulations running at the
same time and, for example, to stop one run if it starts misbehaving.

Next comes the compile-time options, which depend on how BOUT++ was
configured (see <a href="installing.html#sec-compile-bout"
class="reference internal"><span class="std std-ref">Compiling
BOUT++</span></a>):

<div class="highlight-console notranslate">

<div class="highlight">

    Compile-time options:
        Checking enabled, level 2
        Signal handling enabled
        netCDF support enabled
        Parallel NetCDF support disabled
        OpenMP parallelisation disabled
        Compiled with flags : "-Wall -Wextra ..."

</div>

</div>

This says that some run-time checking of values is enabled, that the
code will try to catch segmentation faults to print a useful error, that
NetCDF files are supported, but that the parallel flavour isn’t. The
compilation flags are printed, which can be useful for checking if a run
was built with optimisation or debugging enabled. These flags can be
quite long, so we’ve truncated them in the snippet above.

The complete command line is printed (excluding any MPI options):

<div class="highlight-console notranslate">

<div class="highlight">

    Command line options for this run : ./conduction nout=1

</div>

</div>

After this the core BOUT++ code reads some options:

<div class="highlight-console notranslate">

<div class="highlight">

    Reading options file data/BOUT.inp
        Option nout = 100 (data/BOUT.inp) overwritten with:
            nout = 1 (Command line)
    Writing options to file data/BOUT.settings

    Getting grid data from options
        Option mesh:type = bout (default)
        Option mesh:StaggerGrids = 0 (default)
        Option mesh:maxregionblocksize = 64 (default)
        Option mesh:calcParallelSlices_on_communicate = 1 (default)
        Option mesh:ddz:fft_filter = 0 (default)
        Option mesh:symmetricGlobalX = 1 (default)
        Option mesh:symmetricglobaly = true (data/BOUT.inp)

</div>

</div>

This lists each option and the value it has been assigned. For every
option the source of the value being used is also given. If a value had
been given on the command line then
<span class="pre">`(command`</span>` `<span class="pre">`line)`</span>
would appear after the option.:

<div class="highlight-console notranslate">

<div class="highlight">

    Option mesh:ddx:first = c2 (data/BOUT.inp)
    Option mesh:ddx:second = c2 (data/BOUT.inp)
    Option mesh:ddx:upwind = w3 (data/BOUT.inp)
    Option mesh:ddy:first = c2 (data/BOUT.inp)
    Option mesh:ddy:second = c2 (data/BOUT.inp)
    Option mesh:ddy:upwind = w3 (data/BOUT.inp)
    Option mesh:ddz:first = fft (data/BOUT.inp)
    Option mesh:ddz:second = fft (data/BOUT.inp)
    Option mesh:ddz:upwind = w3 (data/BOUT.inp)

</div>

</div>

This is a list of the differential methods for each direction. These are
set in the BOUT.inp file (<span class="pre">`[mesh:ddx]`</span>,
<span class="pre">`[mesh:ddy]`</span> and
<span class="pre">`[mesh:ddz]`</span> sections), but can be overridden
for individual operators. For each direction, numerical methods can be
specified for first and second central difference terms, upwinding terms
of the form
<span class="math notranslate nohighlight">\\{{\frac{\partial
f}{\partial t}}} = {{\boldsymbol{v}}}\cdot\nabla f\\</span>, and flux
terms of the form
<span class="math notranslate nohighlight">\\{{\frac{\partial
f}{\partial t}}} = \nabla\cdot({{\boldsymbol{v}}}f)\\</span>. By default
the flux terms are just split into a central and an upwinding term. A
list of available methods is given in
<a href="differential_operators.html#sec-diffmethod"
class="reference internal"><span class="std std-ref">Differencing
methods</span></a>.:

<div class="highlight-console notranslate">

<div class="highlight">

    Loading mesh
        Option input:transform_from_field_aligned = 1 (default)
        Option mesh:nx = 1 (data/BOUT.inp)
        Option mesh:ny = 100 (data/BOUT.inp)
        Option mesh:nz = 1 (data/BOUT.inp)
        Read nz from input grid file
        Grid size: 1 x 100 x 1
    Variable 'MXG' not in mesh options. Setting to 0
        Option mxg = 0 (data/BOUT.inp)
    Variable 'MYG' not in mesh options. Setting to 0
        Option MYG = 2 (default)
        Guard cells (x,y,z): 0, 2, 0
        Option mesh:ixseps1 = -1 (data/BOUT.inp)
        Option mesh:ixseps2 = -1 (data/BOUT.inp)

</div>

</div>

Optional quantities (such as <span class="pre">`MXG/MYG`</span> in this
case) which are not specified are given a default (best-guess) value,
and a warning is printed.:

<div class="highlight-console notranslate">

<div class="highlight">

    EQUILIBRIUM IS SINGLE NULL (SND)
    MYPE_IN_CORE = 0
    DXS = 0, DIN = -1. DOUT = -1
    UXS = 0, UIN = -1. UOUT = -1
    XIN = -1, XOUT = -1
    Twist-shift:

</div>

</div>

At this point, BOUT++ reads the grid file, and works out the topology of
the grid, and connections between processors. BOUT++ then tries to read
the metric coefficients from the grid file:

<div class="highlight-console notranslate">

<div class="highlight">

    Variable 'g11' not in mesh options. Setting to 1.000000e+00
    Variable 'g22' not in mesh options. Setting to 1.000000e+00
    Variable 'g33' not in mesh options. Setting to 1.000000e+00
    Variable 'g12' not in mesh options. Setting to 0.000000e+00
    Variable 'g13' not in mesh options. Setting to 0.000000e+00
    Variable 'g23' not in mesh options. Setting to 0.000000e+00

</div>

</div>

These warnings are printed because the coefficients have not been
specified in the grid file, and so the metric tensor is set to the
default identity matrix. For this particular example we don’t need to do
anything special in the direction parallel to the magnetic field, so we
set the parallel transform to be the identity (see
<a href="parallel-transforms.html#sec-parallel-transforms"
class="reference internal"><span class="std std-ref">Parallel
Transforms</span></a>):

<div class="highlight-console notranslate">

<div class="highlight">

    Option mesh:paralleltransform = identity (default)

</div>

</div>

If only the contravariant components (<span class="pre">`g11`</span>
etc.) of the metric tensor are specified, the covariant components
(<span class="pre">`g_11`</span> etc.) are calculated by inverting the
metric tensor matrix. Error estimates are then calculated by calculating
<span class="math notranslate nohighlight">\\g\_{ij}g^{jk}\\</span> as a
check. Since no metrics were specified in the input, the metric tensor
was set to the identity matrix, making inversion easy and the error
tiny.:

<div class="highlight-console notranslate">

<div class="highlight">

    Variable 'J' not in mesh options. Setting to 0.000000e+00
        WARNING: Jacobian 'J' not found. Calculating from metric tensor
    Variable 'Bxy' not in mesh options. Setting to 0.000000e+00
        WARNING: Magnitude of B field 'Bxy' not found. Calculating from metric tensor
    Calculating differential geometry terms
    Communicating connection terms
    Boundary regions in this processor: upper_target, lower_target,
    Constructing default regions

</div>

</div>

The Laplacian inversion (see
<a href="laplacian.html#sec-laplacian" class="reference internal"><span
class="std std-ref">Laplacian inversion</span></a>) code is initialised,
and prints out the options used.:

<div class="highlight-console notranslate">

<div class="highlight">

    Initialising Laplacian inversion routines
        Option phiboussinesq:async = 1 (default)
        Option phiboussinesq:filter = 0 (default)
        Option phiboussinesq:maxmode = 128 (default)
        Option phiboussinesq:low_mem = 0 (default)
        Option phiboussinesq:nonuniform = 1 (default)
        Option phiboussinesq:all_terms = 1 (default)
        Option phiboussinesq:flags = 0 (delta_1/BOUT.inp)

</div>

</div>

After this comes the physics module-specific output:

<div class="highlight-console notranslate">

<div class="highlight">

    Initialising physics module
            Option solver:type = cvode (default)

</div>

</div>

This typically lists the options used, useful/important normalisation
factors, and so on.

Finally, once the physics module has been initialised, and the current
values loaded, the solver can be started:

<div class="highlight-console notranslate">

<div class="highlight">

    Initialising solver
        Option datadir = delta_1 ()
        Option dump_format = nc (default)
        Option restart_format = nc (default)
        Using NetCDF4 format for file 'delta_1/BOUT.restart.nc'

    Constructing default regions
        Boundary region inner X
        Boundary region outer X
        3d fields = 2, 2d fields = 0 neq=100, local_N=100

</div>

</div>

This last line gives the number of equations being evolved (in this case
100), and the number of these on this processor (here 100).:

The absolute and relative tolerances come next:

<div class="highlight-console notranslate">

<div class="highlight">

    Option solver:atol = 1e-12 (default)
    Option solver:rtol = 1e-05 (default)

</div>

</div>

This next option specifies the maximum number of internal timesteps that
CVODE will take between outputs.:

<div class="highlight-console notranslate">

<div class="highlight">

    Option solver:mxstep = 500 (default)

</div>

</div>

After (almost!) all of the options are read in, the simulation proper
starts:

<div class="highlight-console notranslate">

<div class="highlight">

    Running simulation

    Run ID: 332467c7-1210-401a-b44c-f8a3a3415827

    Run started at  : Tue 07 Dec 2021 17:50:39 GMT

</div>

</div>

The <span class="pre">`Run`</span>` `<span class="pre">`ID`</span> here
is a
<a href="https://en.wikipedia.org/wiki/Universally_unique_identifier"
class="reference external">universally unique identifier</a> (UUID)
which is a random 128-bit label unique to this current simulation. This
makes it easier to identify all of the associated outputs of a
simulation, and record the data for future reference.

A few more options may appear between these last progress messages and
the per-timestep output discussed in the next section.

</div>

<div id="per-timestep-output" class="section">

## Per-timestep output<a href="#per-timestep-output" class="headerlink"
title="Permalink to this heading">#</a>

At the beginning of a run, just after the last line in the previous
section, a header is printed out as a guide:

<div class="highlight-console notranslate">

<div class="highlight">

    Sim Time  |  RHS evals  | Wall Time |  Calc    Inv   Comm    I/O   SOLVER

</div>

</div>

Each timestep (the one specified in BOUT.inp, not the internal
timestep), BOUT++ prints out something like:

<div class="highlight-console notranslate">

<div class="highlight">

    1.001e+02         76       2.27e+02    87.1    5.3    1.0    0.0    6.6

</div>

</div>

This gives the simulation time; the number of times the time-derivatives
(RHS) were evaluated; the wall-time this took to run, and percentages
for the time spent in different parts of the code.

- <span class="pre">`Calc`</span> is the time spent doing calculations
  such as multiplications, derivatives etc

- <span class="pre">`Inv`</span> is the time spent in inversion code
  (i.e. inverting Laplacians), including any communication which may be
  needed to do the inversion.

- <span class="pre">`Comm`</span> is the time spent communicating
  variables (outside the inversion routine)

- <span class="pre">`I/O`</span> is the time spent writing dump and
  restart files to disk. Most of the time this should not be an issue

- <span class="pre">`SOLVER`</span> is the time spent in the implicit
  solver code.

The output sent to the terminal (not the log files) also includes a run
time, and estimated remaining time.

</div>

<div id="restarting-runs" class="section">

<span id="sec-restarting"></span>

## Restarting runs<a href="#restarting-runs" class="headerlink"
title="Permalink to this heading">#</a>

Every output timestep, BOUT++ writes a set of files named
“BOUT.restart.#.nc” where ’#’ is the processor number (for parallel
output, a single file “BOUT.restart.nc” is used). To restart from where
the previous run finished, just add the keyword **restart** to the end
of the command, for example:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 2 ./conduction restart

</div>

</div>

Equivalently, put “restart=true” near the top of the BOUT.inp input
file. Note that this will overwrite the existing data in the
<span class="pre">`BOUT.dmp.\*.nc`</span> files. If you want to append
to them instead then add the keyword append to the command, for example:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 2 ./conduction restart append

</div>

</div>

or also put <span class="pre">`append=true`</span> near the top of the
BOUT.inp input file.

When restarting simulations BOUT++ will by default output the initial
state, unless appending to existing data files when it will not output
until the first timestep is completed. To override this behaviour, you
can specify the option <span class="pre">`dump_on_restart`</span>
manually. If <span class="pre">`dump_on_restart`</span> is true then the
initial state will always be written out, if false then it never will be
(regardless of the values of <span class="pre">`restart`</span> and
<span class="pre">`append`</span>).

If you need to restart from a different point in your simulation, or the
<span class="pre">`BOUT.restart`</span> files become corrupted, you can
use <a href="https://xbout.readthedocs.io/en/latest"
class="reference external">xBOUT</a> to create new restart files from
any time-point in your output files. Use the <a
href="https://xbout.readthedocs.io/en/latest/xbout.html#xbout.boutdataset.BoutDatasetAccessor.to_restart"
class="reference external">.to_restart()</a> method:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> import xbout
    >>> df = xbout.open_boutdataset("data/BOUT.dmp.*.nc")
    >>> df.bout.to_restart(tind=10)

</div>

</div>

The above will take time point 10 from the
<span class="pre">`BOUT.dmp.*.nc`</span> files in the
<span class="pre">`data`</span> directory. For each one, it will output
a <span class="pre">`BOUT.restart.*.nc`</span> file in the output
directory <span class="pre">`.`</span>.

</div>

<div id="stopping-simulations" class="section">

## Stopping simulations<a href="#stopping-simulations" class="headerlink"
title="Permalink to this heading">#</a>

If you need to stop a simulation early this can be done by Ctrl-C in a
terminal, but this will stop the simulation immediately without shutting
down cleanly. Most of the time this will be fine, but interrupting a
simulation while it is writing data to file could result in inconsistent
or corrupted data.

<div id="stop-file" class="section">

### Stop file<a href="#stop-file" class="headerlink"
title="Permalink to this heading">#</a>

**Note** This method needs to be enabled before the simulation starts by
setting <span class="pre">`stopCheck=true`</span> on the command line or
input options:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 4 ./conduction stopCheck=true

</div>

</div>

or in the top section of <span class="pre">`BOUT.inp`</span> set
<span class="pre">`stopCheck=true`</span>.

At every output time, the monitor checks for the existence of a file, by
default called <span class="pre">`BOUT.stop`</span>, in the same
directory as the output data. If the file exists then the monitor
signals the time integration solver to quit. This should result in a
clean shutdown.

To stop a simulation using this method, just create an empty file in the
output directory:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 4 ./conduction stopCheck=true
    ...
    $ touch data/BOUT.stop

</div>

</div>

just remember to delete the file afterwards.

</div>

<div id="send-signal-usr1" class="section">

### Send signal USR1<a href="#send-signal-usr1" class="headerlink"
title="Permalink to this heading">#</a>

Another option is to send signal
<span class="pre">`user`</span>` `<span class="pre">`defined`</span>` `<span class="pre">`signal`</span>` `<span class="pre">`1`</span>:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 4 ./conduction &
    ...
    $ killall -s USR1 conduction

</div>

</div>

Note that this will stop all conduction simulation on this node. Many
HPC systems provide tools to send signals to the simulation nodes, such
as <span class="pre">`qsig`</span> on archer.

To just stop one simulation, the
<span class="pre">`bout-stop-script`</span> can send a signal based on
the path of the simulation data dir:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 4 ./conduction &
    ...
    $ bout-stop-script data

</div>

</div>

This will stop the simulation cleanly, and:

<div class="highlight-console notranslate">

<div class="highlight">

    $ mpirun -np 4 ./conduction &
    ...
    $ bout-stop-script data -force

</div>

</div>

will kill the simulation immediately.

</div>

</div>

<div id="manipulating-restart-files" class="section">

## Manipulating restart files<a href="#manipulating-restart-files" class="headerlink"
title="Permalink to this heading">#</a>

It is sometimes useful to change the number of processors used in a
simulation, or to modify restart files in various ways. For example, a
3D turbulence simulation might start with a quick 2D simulation with
diffusive transport to reach a steady-state. The restart files can then
be extended into 3D, noise added to seed instabilities, and the files
split over a more processors.

Routines to modify restart files are in
<span class="pre">`tools/pylib/boutdata/restart.py`</span>:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> from boutdata import restart
    >>> help(restart)

</div>

</div>

<div id="changing-number-of-processors" class="section">

### Changing number of processors<a href="#changing-number-of-processors" class="headerlink"
title="Permalink to this heading">#</a>

To change the number of processors use the
<span class="pre">`redistribute`</span> function:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> from boutdata import restart
    >>> restart.redistribute(32, path="../oldrun", output=".")

</div>

</div>

where in this example <span class="pre">`32`</span> is the number of
processors desired; <span class="pre">`path`</span> sets the path to the
existing restart files, and <span class="pre">`output`</span> is the
path where the new restart files should go. **Note** Make sure that
<span class="pre">`path`</span> and <span class="pre">`output`</span>
are different.

If your simulation is divided in X and Y directions then you should also
specify the number of processors in the X direction,
<span class="pre">`NXPE`</span>:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> restart.redistribute(32, path="../oldrun", output=".", nxpe=8)

</div>

</div>

**Note** Currently this routine doesn’t check that this split is
consistent with branch cuts, e.g. for X-point tokamak simulations. If an
inconsistent choice is made then the BOUT++ restart will fail.

**Note** It is a good idea to set <span class="pre">`nxpe`</span> in the
<span class="pre">`BOUT.inp`</span> file to be consistent with what you
set here. If it is inconsistent then the restart will fail, but the
error message may not be particularly enlightening.

</div>

</div>

</div>

<div class="prev-next-area">

<a href="advanced_install.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Advanced installation options

</div>

<a href="new_in_v5.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

New Features in BOUT++ v5.0

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#quick-start" class="reference internal nav-link">Quick
  start</a>
- <a href="#analysing-the-output-using-python"
  class="reference internal nav-link">Analysing the output using
  Python</a>
- <a href="#natural-language-support"
  class="reference internal nav-link">Natural language support</a>
- <a href="#when-things-go-wrong" class="reference internal nav-link">When
  things go wrong</a>
- <a href="#startup-output" class="reference internal nav-link">Startup
  output</a>
- <a href="#per-timestep-output"
  class="reference internal nav-link">Per-timestep output</a>
- <a href="#restarting-runs"
  class="reference internal nav-link">Restarting runs</a>
- <a href="#stopping-simulations"
  class="reference internal nav-link">Stopping simulations</a>
  - <a href="#stop-file" class="reference internal nav-link">Stop file</a>
  - <a href="#send-signal-usr1" class="reference internal nav-link">Send
    signal USR1</a>
- <a href="#manipulating-restart-files"
  class="reference internal nav-link">Manipulating restart files</a>
  - <a href="#changing-number-of-processors"
    class="reference internal nav-link">Changing number of processors</a>

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
