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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/output_and_post.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/output_and_post.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/output_and_post.rst"
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

# Post-processing

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#" class="reference internal nav-link">Post-processing</a>
  - <a href="#python-routines" class="reference internal nav-link">Python
    routines</a>
    - <a href="#requirements"
      class="reference internal nav-link">Requirements</a>
    - <a href="#reading-bout-data" class="reference internal nav-link">Reading
      BOUT++ data</a>
  - <a href="#python-analysis-routines"
    class="reference internal nav-link">Python analysis routines</a>
  - <a href="#reading-bout-output-into-idl"
    class="reference internal nav-link">Reading BOUT++ output into IDL</a>
  - <a href="#summary-of-idl-file-routines"
    class="reference internal nav-link">Summary of IDL file routines</a>
  - <a href="#idl-analysis-routines" class="reference internal nav-link">IDL
    analysis routines</a>
  - <a href="#matlab-routines" class="reference internal nav-link">Matlab
    routines</a>
  - <a href="#mathematica-routines"
    class="reference internal nav-link">Mathematica routines</a>
  - <a href="#octave-routines" class="reference internal nav-link">Octave
    routines</a>
- <a href="#reproducibility-and-provenance-tracking"
  class="reference internal nav-link">Reproducibility and provenance
  tracking</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="post-processing" class="section">

<span id="sec-output"></span>

# Post-processing<a href="#post-processing" class="headerlink"
title="Permalink to this heading">#</a>

The recommended tool for analysing BOUT++ output is xBOUT, a Python
library that provides analysis, plotting and animation with
human-readable syntax (no magic numbers!) using
<a href="http://xarray.pydata.org/en/stable/"
class="reference external">xarray</a>. See the xBOUT documentation
<a href="https://xbout.readthedocs.io/en/latest/"
class="reference external">xbout.readthedocs.io</a>.

There is also older analysis and post-processing code, the majority
written in Python. Routines to read BOUT++ output data, usually called
“collect” because it collects data from multiple files, are also
available in IDL, Matlab, Mathematica and Octave. All these
post-processing routines are in the <span class="pre">`tools`</span>
directory, with Python modules in
<span class="pre">`tools/pylib`</span>. A summary of available routines
is in <a href="python.html#sec-python-routines-list"
class="reference internal"><span class="std std-ref">Python
routines</span></a>; see below for how to install the requirements.

<div id="python-routines" class="section">

<span id="sec-pythonroutines"></span>

## Python routines<a href="#python-routines" class="headerlink"
title="Permalink to this heading">#</a>

<div id="requirements" class="section">

<span id="sec-python-requirements"></span>

### Requirements<a href="#requirements" class="headerlink"
title="Permalink to this heading">#</a>

The Python tools provided with BOUT++ make heavy use of
<a href="http://www.numpy.org/" class="reference external">numpy</a> and
<a href="http://www.scipy.org/" class="reference external">scipy</a>, as
well as <a href="https://www.matplotlib.org"
class="reference external">matplotlib</a> for the plotting routines. In
order to read BOUT++ output in Python, you will need either
<a href="http://unidata.github.io/netcdf4-python/"
class="reference external">netcdf4</a>.

While we try to ensure that the Python tools are compatible with both
Python 2 and 3, we officially only support Python 3.

If you are developing BOUT++, you may also need
<a href="http://jinja.pocoo.org/" class="reference external">Jinja2</a>
to edit some of the generated code(see
<a href="../developer_docs/data_types.html#sec-fieldops"
class="reference internal"><span class="std std-ref">Field2D/Field3D
Arithmetic Operators</span></a> for more information).

You can install most of the required Python modules by running

<div class="highlight-console notranslate">

<div class="highlight">

    $ pip3 install --user --requirement requirements.txt

</div>

</div>

in the directory where you have unpacked BOUT++. This will install
supported versions of numpy, scipy, netcdf4, matplotlib and jinja2.

<div class="admonition note">

Note

If you have difficulties installing SciPy, please see their
<a href="https://www.scipy.org/install.html"
class="reference external">installation instructions</a>

</div>

</div>

<div id="reading-bout-data" class="section">

### Reading BOUT++ data<a href="#reading-bout-data" class="headerlink"
title="Permalink to this heading">#</a>

To read data from a BOUT++ simulation into Python, there is a
<span class="pre">`collect`</span> routine. This gathers together the
data from multiple processors, taking care of the correct layout.

<div class="highlight-python notranslate">

<div class="highlight">

    from boutdata.collect import collect

    Ni = collect("Ni")  # Collect the variable "Ni"

</div>

</div>

The result is an up to 4D array, <span class="pre">`Ni`</span> in this
case. The array is a BoutArray object: BoutArray is a wrapper class for
Numpy’s ndarray which adds an ‘attributes’ member variable containing a
dictionary of attributes. The array is ordered
<span class="pre">`[t,x,y,z]`</span>:

<div class="highlight-python notranslate">

<div class="highlight">

    >>> Ni.shape
    [10,1,2,3]

</div>

</div>

so <span class="pre">`Ni`</span> would have 10 time slices, 1 point in
x, 2 in y, and 3 in z. This should correspond to the grid size used in
the simulation. Since the collected data is a NumPy array, all the
useful routines in NumPy, SciPy and Matplotlib can be used for further
analysis.

The attributes of the data give:

- the <span class="pre">`bout_type`</span> of the variable

  - {<span class="pre">`'Field3D_t'`</span>,
    <span class="pre">`'Field2D_t'`</span>,
    <span class="pre">`'scalar_t'`</span>} for time-evolving variables

  - {<span class="pre">`'Field3D'`</span>,
    <span class="pre">`'Field2D'`</span>,
    <span class="pre">`'scalar'`</span>} for time-independent variables

- its location, one of {<span class="pre">`'CELL_CENTRE'`</span>,
  <span class="pre">`'CELL_XLOW'`</span>,
  <span class="pre">`'CELL_YLOW'`</span>,
  <span class="pre">`'CELL_ZLOW'`</span>}. See
  <a href="staggered_grids.html#sec-staggergrids"
  class="reference internal"><span class="std std-ref">Staggered
  grids</span></a>.

<div class="highlight-python notranslate">

<div class="highlight">

    >>> Ni.attributes("bout_type")
    'Field3D_t'
    >>> Ni.attributes("location")
    'CELL_CENTRE'

</div>

</div>

Attributes can also be read using the
<span class="pre">`attributes`</span> routine:

<div class="highlight-python notranslate">

<div class="highlight">

    from boutdata.collect import attributes

    attribs = attributes("Ni")

</div>

</div>

The result is a dictionary (map) of attribute name to attribute value.

If the data has less then 4 dimension, it can be checked with
<span class="pre">`dimension`</span> what dimensions are available:

<div class="highlight-python notranslate">

<div class="highlight">

    from boutdata.collect import dimension

    print(dimension("Ni"))
    print(dimension("dx"))

</div>

</div>

The first will print as expected
<span class="pre">`[t,`</span>` `<span class="pre">`x,`</span>` `<span class="pre">`y,`</span>` `<span class="pre">`z]`</span> -
while the second will print
<span class="pre">`[x,`</span>` `<span class="pre">`y]`</span> as dx is
nether evolved in time, nor does it has a <span class="pre">`z`</span>
dependency.

To access both the input options (in the BOUT.inp file) and output data,
there is the <span class="pre">`BoutData`</span> class.

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> from boutdata.data import BoutData
    >>> d = BoutData(path=".")

</div>

</div>

where the path is optional, and should point to the directory containing
the BOUT.inp (input) and BOUT.dmp.\* (output) files. This will return a
dictionary with keys “path” (the given path to the data), “options” (the
input options) and “outputs” (the output data). The tree of options can
be printed:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> print d["options"]
      options
       |- timestep = 50
       |- myg = 0
       |- nout = 50
       |- mxg = 2
       |- all
       |   |- bndry_all = neumann
       |   |- scale = 0.0
       |- phisolver
       |   |- fourth_order = true
       ...

</div>

</div>

and accessed as a tree of dictionaries:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> print d["options"]["phisolver"]["fourth_order"]
    true

</div>

</div>

Currently the values are either integers, floats, or strings, so in the
above example “true” is a string, not a Boolean.

In a similar way the outputs are available as dictionary keys:

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> print d["outputs"]
    ZMAX
    rho_s
    zperiod
    BOUT_VERSION
    ...
    >>> d["outputs"]["rho_s"]
    0.00092165524660235405

</div>

</div>

There are several modules available for reading NetCDF files, so to
provide a consistent interface, file access is wrapped into a class
DataFile. This provides a simple interface for reading and writing files
from any of the following modules: <span class="pre">`netCDF4`</span>;
<span class="pre">`Scientific.IO.NetCDF`</span>; and
<span class="pre">`scipy.io.netcdf`</span>. To open a file using
DataFile:

<div class="highlight-python notranslate">

<div class="highlight">

    from boututils.datafile import DataFile

    f = DataFile("file.nc")  # Open the file
    var = f.read("variable") # Read a variable from the file
    f.close()                # Close the file

</div>

</div>

A more robust way to read from DataFiles is to use the context manager
syntax:

<div class="highlight-python notranslate">

<div class="highlight">

    from boututils.datafile import DataFile

    with DataFile("file.nc") as f: # Open the file
        var = f.read("variable")     # Read a variable from the file

</div>

</div>

This way the DataFile is automatically closed at the end of the
<span class="pre">`with`</span> block, even if there is an error in
<span class="pre">`f.read`</span>. To list the variables in a file e.g.

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> f = DataFile("test_io.grd.nc")
    >>> print(f.list())
    ['f3d', 'f2d', 'nx', 'ny', 'rvar', 'ivar']

</div>

</div>

and to list the names of the dimensions

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> print(f.dimensions("f3d"))
    ('x', 'y', 'z')

</div>

</div>

or to get the sizes of the dimensions

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> print(f.size("f3d"))
    [12, 12, 5]

</div>

</div>

or the dictionary of attributes

<div class="highlight-pycon notranslate">

<div class="highlight">

    >>> print(f.attributes("f3d"))
    {}

</div>

</div>

To read in all variables in a file into a dictionary there is the
<span class="pre">`file_import`</span> function

<div class="highlight-python notranslate">

<div class="highlight">

    from boututils.file_import import file_import

    grid = file_import("grid.nc")

</div>

</div>

</div>

</div>

<div id="python-analysis-routines" class="section">

## Python analysis routines<a href="#python-analysis-routines" class="headerlink"
title="Permalink to this heading">#</a>

The analysis and postprocessing routines are currently divided into two
Python modules: <span class="pre">`boutdata`</span>, which contains
BOUT++ specific things like <span class="pre">`collect`</span>, and
<span class="pre">`boututils`</span> which contains more generic useful
routines.

To plot data, a convenient wrapper around matplotlib is
<span class="pre">`plotdata`</span>

<div class="highlight-python notranslate">

<div class="highlight">

    from boutdata import collect
    n = collect("n") # Read data as NumPy array [t,x,y,z]

    from boututils.plotdata import plotdata
    plotdata(n[-1,:,0,:])

</div>

</div>

If given a 2D array as in the above example, plotdata produces a contour
plot (using matplotlib pyplot.contourf) with colour bar. If given a 1D
array then it will plot a line plot (using pyplot.plot).

It is sometimes useful to see an animation of a simulation. To do this
there is <span class="pre">`showdata`</span>, which again is a wrapper
around matplotlib:

<div class="highlight-python notranslate">

<div class="highlight">

    from boutdata import collect
    n = collect("n") # Read data as NumPy array [t,x,y,z]

    from boututils.showdata import showdata
    showdata(n[:,:,0,:])

</div>

</div>

This always assumes that the first index is time and will be animated
over. The above example animates the variable
<span class="pre">`n`</span> in time, at each time point plotting a
contour plot in <span class="pre">`x`</span> and
<span class="pre">`z`</span> dimensions. The colour range is kept
constant by default. If a 2D array is given to
<span class="pre">`showdata`</span> then a line plot will be drawn at
each time, with the scale being kept constant.

</div>

<div id="reading-bout-output-into-idl" class="section">

## Reading BOUT++ output into IDL<a href="#reading-bout-output-into-idl" class="headerlink"
title="Permalink to this heading">#</a>

There are several routines provided for reading data from BOUT++ output
into IDL. In the directory containing the BOUT++ output files (usually
<span class="pre">`data/`</span>), you can list the variables available
using

<div class="highlight-idl notranslate">

<div class="highlight">

    IDL> print, file_list("BOUT.dmp.0.nc")
    Ajpar Apar BOUT_VERSION MXG MXSUB MYG MYSUB MZ NXPE NYPE Ni Ni0 Ni_x Te0 Te_x
    Ti0 Ti_x ZMAX ZMIN iteration jpar phi rho rho_s t_array wci

</div>

</div>

The <span class="pre">`file_list`</span> procedure just returns an
array, listing all the variables in a given file.

One thing new users can find confusing is that different simulations may
have very different outputs. This is because **BOUT++ is not a single
physics model**: the variables evolved and written to file are
determined by the model, and will be very different between (for
example) full MHD and reduced Braginskii models. There are however some
variables which all BOUT++ output files contain:

- <span class="pre">`BOUT_VERSION`</span>, which gives the version
  number of BOUT++ which produced the file. This is mainly to help
  output processing codes handle changes to the output file format. For
  example, BOUT++ version 0.30 introduced 2D domain decomposition which
  needs to be handled when collecting data.

- <span class="pre">`MXG`</span>,<span class="pre">`MYG`</span>. These
  are the sizes of the X and Y guard cells

- <span class="pre">`MXSUB`</span>, the number of X grid points in each
  processor. This does not include the guard cells, so the total X size
  of each field will be
  <span class="pre">`MXSUB`</span>` `<span class="pre">`+`</span>` `<span class="pre">`2*MXG`</span>.

- <span class="pre">`MYSUB`</span>, the number of Y grid points per
  processor (like MXSUB)

- <span class="pre">`MZ`</span>, the number of Z points

- <span class="pre">`NXPE,`</span>` `<span class="pre">`NYPE`</span>,
  the number of processors in the X and Y directions.
  <span class="pre">`NXPE`</span>` `<span class="pre">`*`</span>` `<span class="pre">`MXSUB`</span>` `<span class="pre">`+`</span>` `<span class="pre">`2*MXG=`</span>` `<span class="pre">`NX`</span>,
  <span class="pre">`NYPE`</span>` `<span class="pre">`*`</span>` `<span class="pre">`MYSUB`</span>` `<span class="pre">`=`</span>` `<span class="pre">`NY`</span>

- <span class="pre">`ZMIN`</span>, <span class="pre">`ZMAX`</span>, the
  range of Z in fractions of
  <span class="math notranslate nohighlight">\\2\pi\\</span>.

- <span class="pre">`iteration`</span>, the last timestep in the file

- <span class="pre">`t_array`</span>, an array of times

Most of these - particularly those concerned with grid size and
processor layout - are used by post-processing routines such as
<span class="pre">`collect`</span>, and are seldom needed directly. To
read a single variable from a file, there is the
<span class="pre">`file_read`</span> function:

<div class="highlight-idl notranslate">

<div class="highlight">

    IDL> wci = file_read("BOUT.dmp.0.nc", "wci")
    IDL> print, wci
      9.58000e+06

</div>

</div>

To read in all the variables in a file into a structure, use the
<span class="pre">`file_import`</span> function:

<div class="highlight-idl notranslate">

<div class="highlight">

    IDL> d = file_import("BOUT.dmp.0.nc")
    IDL> print, d.wci
      9.58000e+06

</div>

</div>

This is often used to read in the entire grid file at once. Doing this
for output data files can take a long time and use a lot of memory.

Reading from individual files is fine for scalar quantities and time
arrays, but reading arrays which are spread across processors (i.e.
evolving variables) is tedious to do manually. Instead, there is the
<span class="pre">`collect`</span> function to automate this:

<div class="highlight-idl notranslate">

<div class="highlight">

    IDL> ni = collect(var="ni")
    Variable 'ni' not found
    -> Variables are case-sensitive: Using 'Ni'
    Reading from .//BOUT.dmp.0.nc: [0-35][2-6] -> [0-35][0-4]

</div>

</div>

This function takes care of the case, so that reading “ni” is
automatically corrected to “Ni”. The result is a 4D variable:

<div class="highlight-idl notranslate">

<div class="highlight">

    IDL> help, ni
    NI              FLOAT     = Array[36, 5, 64, 400]

</div>

</div>

with the indices
<span class="pre">`[X,`</span>` `<span class="pre">`Y,`</span>` `<span class="pre">`Z,`</span>` `<span class="pre">`T]`</span>.
Note that in the output files, these variables are stored in
<span class="pre">`[T,`</span>` `<span class="pre">`X,`</span>` `<span class="pre">`Y,`</span>` `<span class="pre">`Z]`</span>
format instead but this is changed by
<span class="pre">`collect`</span>. Sometimes you don’t want to read in
the entire array (which may be very large). To read in only a subset,
there are several optional keywords with
<span class="pre">`[min,max]`</span> ranges:

<div class="highlight-idl notranslate">

<div class="highlight">

    IDL> ni = collect(var="Ni", xind=[10,20], yind=[2,2], zind=[0,31],
    tind=[300,399])
    Reading from .//BOUT.dmp.0.nc: [10-20][4-4] -> [10-20][2-2]
    IDL> help, ni
    NI              FLOAT     = Array[11, 1, 32, 100]

</div>

</div>

</div>

<div id="summary-of-idl-file-routines" class="section">

## Summary of IDL file routines<a href="#summary-of-idl-file-routines" class="headerlink"
title="Permalink to this heading">#</a>

Functions file\_ can currently only read/write NetCDF files.

Open a NetCDF file:

<div class="highlight-idl notranslate">

<div class="highlight">

    handle = file_open("filename", /write, /create)

</div>

</div>

Array of variable names:

<div class="highlight-idl notranslate">

<div class="highlight">

    list = file_list(handle)
    list = file_list("filename")

</div>

</div>

Number of dimensions:

<div class="highlight-idl notranslate">

<div class="highlight">

    nd = file_ndims(handle, "variable")
    nd = file_ndims("filename", "variable")

</div>

</div>

Read a variable from file. Inds = \[xmin, xmax, ymin, ymax, …\]

<div class="highlight-idl notranslate">

<div class="highlight">

    data = file_read(handle, "variable", inds=inds)
    data = file_read("filename", "variable", inds=inds)

</div>

</div>

Write a variable to file. For NetCDF it tries to match up dimensions,
and defines new dimensions when needed

<div class="highlight-idl notranslate">

<div class="highlight">

    status = file_write(handle, "variable", data)

</div>

</div>

Close a file after use

<div class="highlight-idl notranslate">

<div class="highlight">

    file_close, handle

</div>

</div>

To read in all the data in a file into a structure:

<div class="highlight-idl notranslate">

<div class="highlight">

    data = file_import("filename")

</div>

</div>

and to write a structure to file:

<div class="highlight-idl notranslate">

<div class="highlight">

    status = file_export("filename", data)

</div>

</div>

</div>

<div id="idl-analysis-routines" class="section">

## IDL analysis routines<a href="#idl-analysis-routines" class="headerlink"
title="Permalink to this heading">#</a>

Now that the BOUT++ results have been read into IDL, all the usual
analysis and plotting routines can be used. In addition, there are many
useful routines included in the <span class="pre">`idllib`</span>
subdirectory. There is a <span class="pre">`README`</span> file which
describes what each of these routines, but some of the most useful ones
are listed here. All these examples assume there is a variable
<span class="pre">`P`</span> which has been read into IDL as a 4D
\[x,y,z,t\] variable:

- <span class="pre">`fft_deriv`</span> and
  <span class="pre">`fft_integrate`</span> which differentiate and
  integrate periodic functions.

- <span class="pre">`get_integer`</span>,
  <span class="pre">`get_float`</span>, and
  <span class="pre">`get_yesno`</span> request integers, floats and a
  yes/no answer from the user respectively.

- <span class="pre">`showdata`</span> animates 1 or 2-dimensional
  variables. Useful for quickly displaying results in different ways.
  This is useful for taking a quick look at the data, but can also
  produce bitmap outputs for turning into a movie for presentation. To
  show an animated surface plot at a particular poloidal location (32
  here):

  <div class="highlight-idl notranslate">

  <div class="highlight">

      IDL> showdata, p[*,32,*,*]

  </div>

  </div>

  To turn this into a contour plot,

  <div class="highlight-idl notranslate">

  <div class="highlight">

      IDL> showdata, p[*,32,*,*], /cont

  </div>

  </div>

  To show a slice through this at a particular toroidal location (0
  here):

  <div class="highlight-idl notranslate">

  <div class="highlight">

      IDL> showdata, p[*,32,0,*]

  </div>

  </div>

  There are a few other options, and ways to show data using this code;
  see the README file, or comments in
  <span class="pre">`showdata.pro`</span>. Instead of plotting to
  screen, showdata can produce a series of numbered bitmap images by
  using the <span class="pre">`bmp`</span> option

  <div class="highlight-idl notranslate">

  <div class="highlight">

      IDL> showdata, p[*,32,*,*], /cont, bmp="result_"

  </div>

  </div>

  which will produce images called
  <span class="pre">`result_0000.bmp`</span>,
  <span class="pre">`result_0001.bmp`</span> and so on. Note that the
  plotting should not be obscured or minimised, since this works by
  plotting to screen, then grabbing an image of the resulting plot.

- <span class="pre">`moment_xyzt`</span> takes a 4D variable (such as
  those from <span class="pre">`collect`</span>), and calculates RMS, DC
  and AC components in the Z direction.

- <span class="pre">`safe_colors`</span> A general routine for IDL which
  arranges the color table so that colors are numbered 1 (black), 2
  (red), 3 (green), 4 (blue). Useful for plotting, and used by many
  other routines in this library.

There are many other useful routines in the
<span class="pre">`idllib`</span> directory. See the
<span class="pre">`idllib/README`</span> file for a short description of
each one.

</div>

<div id="matlab-routines" class="section">

## Matlab routines<a href="#matlab-routines" class="headerlink"
title="Permalink to this heading">#</a>

These are Matlab routines for collecting data, showing animation and
performing some basic analysis. To use these routines, either you may
copy these routines (from **tools/matlablib**) directly to your present
working directory or a path to **tools/matlablib** should be added
before analysis.

<div class="highlight-matlab notranslate">

<div class="highlight">

    >> addpath <full_path_BOUT_directory>/tools/matlablib/

</div>

</div>

Now, the first routine to collect data and import it to Matlab for
further analysis is

<div class="highlight-matlab notranslate">

<div class="highlight">

    >> var = import_dmp(path,var_name);

</div>

</div>

Here, *path* is the path where the output data in netcdf format has been
dumped. *var_name* is the name of variable which user want to load for
further analysis. For example, to load “P” variable from present working
directory:

<div class="highlight-matlab notranslate">

<div class="highlight">

    >> P = import_dmp('.','P');

</div>

</div>

Variable “P” can be any of \[X,Y,Z,T\]/\[X,Y,Z\]/\[X,Y\]/Constant
formats. If we are going to Import a large data set with \[X,Y,Z,T\]
format. Normally such data files are of very big size and Matlab goes
out of memory/ or may take too much time to load data for all time
steps. To resolve this limitation of above routine *import_dmp*, another
routine *import_data_netcdf* is being provided. It serves all purposes
the routine *import_dmp* does but also gives user freedom to import data
at only few/specific time steps.

<div class="highlight-matlab notranslate">

<div class="highlight">

    >> var = import_data_netcdf(path,var_name,nt,ntsp);

</div>

</div>

Here, *path* and *var_name* are same variables as described before. *nt*
is the number of time steps user wish to load data. *ntsp* is the steps
at which one wish to write data of of total simulation times the data
written.

<div class="highlight-matlab notranslate">

<div class="highlight">

    >> P = import_data_netcdf('.','P',5,100);

</div>

</div>

Variable “P” has been imported from present working directory for 5 time
steps. As the original netcdf data contains time information of 500
steps (assume NT=500 in BOUT++ simulations), user will pick only 5 time
steps at steps of *ntsp* i.e. 100 here. Details of other Matlab routines
provided with BOUT++ package can be looked in to README.txt of
**tools/matlablib** directory. The Matlab users can develop their own
routines using **\*ncread, ncinfo, ncwrite, ncdisp, netcdf etc.\***
functions provided in Matlab package.

</div>

<div id="mathematica-routines" class="section">

## Mathematica routines<a href="#mathematica-routines" class="headerlink"
title="Permalink to this heading">#</a>

A package to read BOUT++ output data into Mathematica is in
<span class="pre">`tools/mathematicalib`</span>. To read data into
Mathematica, first add this directory to Mathematica’s path by putting

<div class="highlight-mathematica notranslate">

<div class="highlight">

    AppendTo[$Path,"/full/path/to/BOUT/tools/mathematicalib"]

</div>

</div>

in your Mathematica startup file (usually
<span class="pre">`$HOME/.Mathematica/Kernel/init.m`</span> ). To use
the package, call

<div class="highlight-mathematica notranslate">

<div class="highlight">

    Import["BoutCollect.m"]

</div>

</div>

from inside Mathematica. Then you can use e.g.

<div class="highlight-mathematica notranslate">

<div class="highlight">

    f=BoutCollect[variable,path->"data"]

</div>

</div>

or

<div class="highlight-mathematica notranslate">

<div class="highlight">

    f=BoutCollect[variable,path->"data"]

</div>

</div>

’ <span class="pre">`bc`</span>’ is a shorthand for
’<span class="pre">`BoutCollect`</span> ’. All options supported by the
Python <span class="pre">`collect()`</span> function are included,
though Info does nothing yet.

</div>

<div id="octave-routines" class="section">

## Octave routines<a href="#octave-routines" class="headerlink"
title="Permalink to this heading">#</a>

There is minimal support for reading data into Octave, which has been
tested on Octave 3.2. It requires the <span class="pre">`octcdf`</span>
library to access NetCDF files.

<div class="highlight-octave notranslate">

<div class="highlight">

    f = bcollect()  # optional path argument is "." by default

    f = bsetxrange(f, 1, 10) # Set ranges
    # Same for y, z, and t (NOTE: indexing from 1!)

    u = bread(f, "U")  # Finally read the variable

</div>

</div>

</div>

</div>

<div id="reproducibility-and-provenance-tracking" class="section">

<span id="sec-reproducibility"></span>

# Reproducibility and provenance tracking<a href="#reproducibility-and-provenance-tracking" class="headerlink"
title="Permalink to this heading">#</a>

To help with reproducibility of simulations and provenance tracking of
data, BOUT++ saves some metadata into output files.

<table id="id1" class="table">
<caption><span class="caption-number">Table 7 </span><span
class="caption-text">Provenance tracking metadata attributes</span><a
href="#id1" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th colspan="2" class="head"><p>File attributes</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="sourceCode cpp">BOUT_REVISION</code></span></p></td>
<td><p>Git hash of the BOUT++ version that the code was compiled
with.</p></td>
</tr>
</tbody>
</table>

<table id="id2" class="table">
<caption><span class="caption-number">Table 8 </span><span
class="caption-text">Provenance tracking metadata variables</span><a
href="#id2" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th colspan="2" class="head"><p>Variables</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="sourceCode cpp">run_id</code></span></p></td>
<td><p>Unique identifier (UUID) for a run</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="sourceCode cpp">run_restart_from</code></span></p></td>
<td><p>If the run was restarted, the <span class="pre"><code
class="sourceCode cpp">run_id</code></span> of the run it was restarted
from. <span class="pre"><code
class="docutils literal notranslate">"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"</code></span>
if the run was not restarted, or the previous run had no <span
class="pre"><code class="sourceCode cpp">run_id</code></span></p></td>
</tr>
</tbody>
</table>

<table id="id3" class="table">
<caption><span class="caption-number">Table 9 </span><span
class="caption-text">Provenance tracking grid metadata
variables</span><a href="#id3" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Grid-related variables</p></th>
<th class="head"><p>These variables are created if a grid file was used
for the run, and if the grid file was created with a new enough version
of hypnotoad</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="sourceCode cpp">grid_id</code></span></p></td>
<td><p>Unique identifier (UUID) for the grid file</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="sourceCode cpp">hypnotoad_version</code></span></p></td>
<td><p>Version number of hypnotoad used to create the grid file</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="sourceCode cpp">hypnotoad_git_hash</code></span></p></td>
<td><p>Git hash of the version of hypnotoad used to create the grid file
(only present if hypnotoad is used from a git repo rather installed as a
package).</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="sourceCode cpp">hypnotoad_git_diff</code></span></p></td>
<td><p>Git diff of the version of hypnotoad used to create the grid file
(only present if hypnotoad is used from a git repo rather installed as a
package and the code was changed since the latest commit)</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="sourceCode cpp">hypnotoad_geqdsk_filename</code></span></p></td>
<td><p>Name of the geqdsk file used to create the grid (if a geqdsk file
was used)</p></td>
</tr>
</tbody>
</table>

</div>

<div class="prev-next-area">

<a href="input_grids.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Generating input grids

</div>

<a href="python_boutpp.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

The python boutpp module

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#" class="reference internal nav-link">Post-processing</a>
  - <a href="#python-routines" class="reference internal nav-link">Python
    routines</a>
    - <a href="#requirements"
      class="reference internal nav-link">Requirements</a>
    - <a href="#reading-bout-data" class="reference internal nav-link">Reading
      BOUT++ data</a>
  - <a href="#python-analysis-routines"
    class="reference internal nav-link">Python analysis routines</a>
  - <a href="#reading-bout-output-into-idl"
    class="reference internal nav-link">Reading BOUT++ output into IDL</a>
  - <a href="#summary-of-idl-file-routines"
    class="reference internal nav-link">Summary of IDL file routines</a>
  - <a href="#idl-analysis-routines" class="reference internal nav-link">IDL
    analysis routines</a>
  - <a href="#matlab-routines" class="reference internal nav-link">Matlab
    routines</a>
  - <a href="#mathematica-routines"
    class="reference internal nav-link">Mathematica routines</a>
  - <a href="#octave-routines" class="reference internal nav-link">Octave
    routines</a>
- <a href="#reproducibility-and-provenance-tracking"
  class="reference internal nav-link">Reproducibility and provenance
  tracking</a>

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
