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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/eigenvalue_solver.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/eigenvalue_solver.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/eigenvalue_solver.rst"
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

# Eigenvalue solver

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#configuring-with-slepc"
  class="reference internal nav-link">Configuring with SLEPc</a>
- <a href="#slepc-options" class="reference internal nav-link">SLEPc
  options</a>
- <a href="#examples" class="reference internal nav-link">Examples</a>
  - <a href="#wave-in-a-box" class="reference internal nav-link">Wave in a
    box</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="eigenvalue-solver" class="section">

# Eigenvalue solver<a href="#eigenvalue-solver" class="headerlink"
title="Permalink to this heading">#</a>

By using the SLEPc library, BOUT++ can be used as an eigenvalue solver
to find the eigenvectors and eigenvalues of sets of equations.

<div id="configuring-with-slepc" class="section">

## Configuring with SLEPc<a href="#configuring-with-slepc" class="headerlink"
title="Permalink to this heading">#</a>

The BOUT++ interface has been tested with SLEPc version 3.4.3, itself
compiled with PETSc 3.4.2. SLEPc version 3.4 should work, but other
versions will not yet.

</div>

<div id="slepc-options" class="section">

## SLEPc options<a href="#slepc-options" class="headerlink"
title="Permalink to this heading">#</a>

Time derivatives can be taken directly from the RHS function, or by
advancing the simulation in time by a relatively large increment. This
second method acts to damp high frequency components

</div>

<div id="examples" class="section">

## Examples<a href="#examples" class="headerlink"
title="Permalink to this heading">#</a>

<div id="wave-in-a-box" class="section">

### Wave in a box<a href="#wave-in-a-box" class="headerlink"
title="Permalink to this heading">#</a>

<span class="pre">`examples/eigen-box`</span>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="staggered_grids.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Staggered grids

</div>

<a href="nonlocal.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Nonlocal heat flux models

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#configuring-with-slepc"
  class="reference internal nav-link">Configuring with SLEPc</a>
- <a href="#slepc-options" class="reference internal nav-link">SLEPc
  options</a>
- <a href="#examples" class="reference internal nav-link">Examples</a>
  - <a href="#wave-in-a-box" class="reference internal nav-link">Wave in a
    box</a>

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
