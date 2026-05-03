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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/python.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/python.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/python.rst"
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

# Python routines

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#boututils" class="reference internal nav-link">boututils</a>
- <a href="#boutdata" class="reference internal nav-link">boutdata</a>
  - <a href="#boutdata.attributes" class="reference internal nav-link"><span
    class="pre"><code
    class="docutils literal notranslate">attributes()</code></span></a>
  - <a href="#boutdata.collect" class="reference internal nav-link"><span
    class="pre"><code
    class="docutils literal notranslate">collect()</code></span></a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="python-routines" class="section">

<span id="sec-python-routines-list"></span>

# Python routines<a href="#python-routines" class="headerlink"
title="Permalink to this heading">#</a>

<div id="boututils" class="section">

## boututils<a href="#boututils" class="headerlink"
title="Permalink to this heading">#</a>

- <span class="pre">`class`</span>` `<span class="pre">`Datafile`</span>
  provides a convenient way to read and write NetCDF files. There are
  many different NetCDF libraries available for Python, so this class
  tries to provide a consistent interface to many of them.

- <span class="pre">`deriv()`</span>

- <span class="pre">`determineNumberOfCPUs()`</span>

- <span class="pre">`file_import()`</span> reads the contents of a
  NetCDF file into a dictionary

- <span class="pre">`integrate()`</span>

- <span class="pre">`launch()`</span>

- <span class="pre">`linear_regression()`</span>

- <span class="pre">`showdata()`</span> visualises and animates 2D data
  (time + 1 spatial dimension) or 3D data (time + 2 spatial dimensions).
  The animation object can be returned, or the animation can be saved to
  a file or displayed on screen.

- <span class="pre">`boutwarnings`</span> contains functions to raise
  warning messages. <span class="pre">`alwayswarn()`</span> by default
  prints the warning every time it is called.
  <span class="pre">`defaultwarn()`</span> by default prints the warning
  only the first time an instance of it is called. This module is a
  wrapper for the Python <span class="pre">`warnings`</span> module, so
  printing the warnings can be controlled using
  <span class="pre">`warnings.simplefilter()`</span> or
  <span class="pre">`warnings.filterwarnings()`</span>.

<span id="module-boututils" class="target"></span>

Generic routines, useful for all data

</div>

<div id="boutdata" class="section">

## boutdata<a href="#boutdata" class="headerlink"
title="Permalink to this heading">#</a>

- <span class="pre">`collect()`</span> provides an interface to read
  BOUT++ data outputs, returning NumPy arrays of data. It deals with the
  processor layout, working out which file contains each part of the
  domain.

  <div class="highlight-python notranslate">

  <div class="highlight">

      from boutdata.collect import collect

      t = collect("t_array")  # Collect the time values

  </div>

  </div>

- <span class="pre">`pol_slice()`</span> takes a 3 or 4-D data set for a
  toroidal equilibrium, and calculates a slice through it at fixed
  toroidal angle.

- <span class="pre">`gen_surface()`</span> is a generator for iterating
  over flux surfaces

<span id="module-boutdata" class="target"></span>

Routines for exchanging data to/from BOUT++

<span class="sig-prename descclassname"><span class="pre">boutdata.</span></span><span class="sig-name descname"><span class="pre">attributes</span></span><span class="sig-paren">(</span>*<span class="n"><span class="pre">varname</span></span>*, *<span class="n"><span class="pre">path</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">'.'</span></span>*, *<span class="n"><span class="pre">prefix</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">'BOUT.dmp'</span></span>*<span class="sig-paren">)</span><a href="#boutdata.attributes" class="headerlink"
title="Permalink to this definition">#</a>  
Return a dictionary of variable attributes in an output file

Parameters<span class="colon">:</span>  
- **varname** (*str*) – Name of the variable

- **path** (*str, optional*) – Path to data files (default: “.”)

- **prefix** (*str, optional*) – File prefix (default: “BOUT.dmp”)

Returns<span class="colon">:</span>  
A dictionary of attributes of varname

Return type<span class="colon">:</span>  
dict

<!-- -->

<span class="sig-prename descclassname"><span class="pre">boutdata.</span></span><span class="sig-name descname"><span class="pre">collect</span></span><span class="sig-paren">(</span>*<span class="n"><span class="pre">varname</span></span>*, *<span class="n"><span class="pre">xind</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span>*, *<span class="n"><span class="pre">yind</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span>*, *<span class="n"><span class="pre">zind</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span>*, *<span class="n"><span class="pre">tind</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span>*, *<span class="n"><span class="pre">path</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">'.'</span></span>*, *<span class="n"><span class="pre">yguards</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">False</span></span>*, *<span class="n"><span class="pre">xguards</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">True</span></span>*, *<span class="n"><span class="pre">info</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">True</span></span>*, *<span class="n"><span class="pre">prefix</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">'BOUT.dmp'</span></span>*, *<span class="n"><span class="pre">strict</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">False</span></span>*, *<span class="n"><span class="pre">tind_auto</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">False</span></span>*, *<span class="n"><span class="pre">datafile_cache</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span>*<span class="sig-paren">)</span><a href="#boutdata.collect" class="headerlink"
title="Permalink to this definition">#</a>  
Collect a variable from a set of BOUT++ outputs.

Parameters<span class="colon">:</span>  
- **varname** (*str*) – Name of the variable

- **xind, yind, zind, tind** (*int, slice or list of int, optional*) –
  Range of X, Y, Z or time indices to collect. Either a single index to
  collect, a list containing \[start, end\] (inclusive end), or a slice
  object (usual python indexing). Default is to fetch all indices

- **path** (*str, optional*) – Path to data files (default: “.”)

- **prefix** (*str, optional*) – File prefix (default: “BOUT.dmp”)

- **yguards** (*bool or “include_upper”, optional*) – Collect Y boundary
  guard cells? (default: False) If yguards==”include_upper” the
  y-boundary cells from the upper (second) target are also included.

- **xguards** (*bool, optional*) – Collect X boundary guard cells?
  (default: True) (Set to True to be consistent with the definition of
  nx)

- **info** (*bool, optional*) – Print information about collect?
  (default: True)

- **strict** (*bool, optional*) – Fail if the exact variable name is not
  found? (default: False)

- **tind_auto** (*bool, optional*) – Read all files, to get the shortest
  length of time_indices. Useful if writing got interrupted (default:
  False)

- **datafile_cache** (*datafile_cache_tuple, optional*) – Optional cache
  of open DataFile instances: namedtuple as returned by create_cache.
  Used by BoutOutputs to pass in a cache so that we do not have to
  re-open the dump files to read another variable (default: None)

Examples

<div class="doctest highlight-default notranslate">

<div class="highlight">

    >>> collect(name)
    BoutArray([[[[...]]]])

</div>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="../_breathe_autogen/file/where_8hxx.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

File where.hxx

</div>

<a href="../_apidoc/boutdata.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

boutdata package

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#boututils" class="reference internal nav-link">boututils</a>
- <a href="#boutdata" class="reference internal nav-link">boutdata</a>
  - <a href="#boutdata.attributes" class="reference internal nav-link"><span
    class="pre"><code
    class="docutils literal notranslate">attributes()</code></span></a>
  - <a href="#boutdata.collect" class="reference internal nav-link"><span
    class="pre"><code
    class="docutils literal notranslate">collect()</code></span></a>

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
