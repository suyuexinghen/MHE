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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/adios2.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/adios2.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/adios2.rst"
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

# ADIOS2 support

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#installation"
  class="reference internal nav-link">Installation</a>
- <a href="#output-files" class="reference internal nav-link">Output
  files</a>
- <a href="#restart-files" class="reference internal nav-link">Restart
  files</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="adios2-support" class="section">

<span id="sec-adios2"></span>

# ADIOS2 support<a href="#adios2-support" class="headerlink"
title="Permalink to this heading">#</a>

This section summarises the use of
<a href="https://adios2.readthedocs.io/"
class="reference external">ADIOS2</a> in BOUT++.

<div id="installation" class="section">

## Installation<a href="#installation" class="headerlink"
title="Permalink to this heading">#</a>

The easiest way to configure BOUT++ with ADIOS2 is to tell CMake to
download and build it with this flag:

<div class="highlight-cpp notranslate">

<div class="highlight">

    -DBOUT_DOWNLOAD_ADIOS2=ON

</div>

</div>

The <span class="pre">`master`</span> branch will be downloaded from
<a href="https://github.com/ornladios/ADIOS2"
class="reference external">Github</a>, configured and built with BOUT++.

Alternatively, if ADIOS2 is already installed then the following flags
can be used:

<div class="highlight-cpp notranslate">

<div class="highlight">

    -DBOUT_USE_ADIOS2=ON -DADIOS2_ROOT=/path/to/adios2

</div>

</div>

</div>

<div id="output-files" class="section">

## Output files<a href="#output-files" class="headerlink"
title="Permalink to this heading">#</a>

The output (dump) files are controlled with the root
<span class="pre">`output`</span> options. By default the output format
is NetCDF, so to use ADIOS2 instead set the output type in BOUT.inp:

<div class="highlight-cpp notranslate">

<div class="highlight">

    [output]
    type = adios

</div>

</div>

or on the BOUT++ command line set
<span class="pre">`output:type=adios`</span>. The default prefix is
“BOUT.dmp” so the ADIOS file will be called “BOUT.dmp.bp”. To change
this, set the <span class="pre">`output:prefix`</span> option.

</div>

<div id="restart-files" class="section">

## Restart files<a href="#restart-files" class="headerlink"
title="Permalink to this heading">#</a>

The restart files are contolled with the root
<span class="pre">`restart_files`</span> options, so to read and write
restarts from an ADIOS dataset, put in BOUT.inp:

<div class="highlight-cpp notranslate">

<div class="highlight">

    [restart_files]
    type = adios

</div>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="gpu_support.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

GPU support

</div>

<a href="bout_options.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

BOUT++ options

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#installation"
  class="reference internal nav-link">Installation</a>
- <a href="#output-files" class="reference internal nav-link">Output
  files</a>
- <a href="#restart-files" class="reference internal nav-link">Restart
  files</a>

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
