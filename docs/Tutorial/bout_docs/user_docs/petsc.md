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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/petsc.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/petsc.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/petsc.rst"
  class="btn btn-sm btn-download-source-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Download source file"><span class="btn__icon-container">
  <em></em> </span> <span class="btn__text-container">.rst</span></a>
- <span class="btn__icon-container"> </span>
  <span class="btn__text-container">.pdf</span>

</div>

<span class="btn__icon-container"> </span>

</div>

</div>

</div>

</div>

</div>

<div id="jb-print-docs-body" class="onlyprint">

# PETSc solvers

<div id="print-main-content">

<div id="jb-print-toc">

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="petsc-solvers" class="section">

<span id="sec-petsc"></span>

# PETSc solvers<a href="#petsc-solvers" class="headerlink"
title="Permalink to this heading">#</a>

Options for PETSc solvers can be passed in the input file (or on the
command line). Global options are set in the
<span class="pre">`[petsc]`</span> section. To set options specific to a
particular PETSc-based solver, the options can be set in a
<span class="pre">`petsc`</span> subsection of the solver’s options,
e.g. for a LaplaceXY solver (using the default options section) use the
<span class="pre">`[laplacexy:petsc]`</span> section. Note that the
global options, including any passed on the command line [1], will be
ignored for that solver if the subsection is created. To set options
from the command line, it is recommended to use the BOUT++ options
system rather than PETSc’s, e.g.
<span class="pre">`./mymodel`</span>` `<span class="pre">`laplacexy:petsc:type=gmres`</span>.

Any options that can be passed on the command line to PETSc can be set,
with no preceding hyphen. Flags passed with no value can be passed as
options with no value. So for example, if the command line options would
be:

<div class="highlight-cpp notranslate">

<div class="highlight">

    -ksp_monitor -ksp_type gmres

</div>

</div>

to set for the LaplaceXY solver, in the input file you would put:

<div class="highlight-cpp notranslate">

<div class="highlight">

    [laplacexy:petsc]
    ksp_monitor
    ksp_type = gmres

</div>

</div>

<span class="label"><span class="fn-bracket">\[</span><a href="#id1" role="doc-backlink">*</a><span class="fn-bracket">\]</span></span>

The object-specific options are passed to PETSc by creating an
object-specific prefix
<span class="pre">`boutpetsclib_<sectionname>`</span>, where
<span class="pre">`<sectionname>`</span> is the name of the options
section used to create the PetscLib. So an option could in principle be
passed to a particular solver if you use the section name, e.g.:

<div class="highlight-cpp notranslate">

<div class="highlight">

    -boutpetsclib_laplacexyksp_type gmres

</div>

</div>

The PETSc arguments <span class="pre">`-options_view`</span> and
<span class="pre">`options_left`</span> might be helpful for this - they
will show what options have been set, so will show the prefixes used.

</div>

<div class="prev-next-area">

<a href="invertable_operator.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Invertable operators

</div>

<a href="coordinates.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Field-aligned coordinates

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

[1]
