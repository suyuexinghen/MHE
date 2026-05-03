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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/staggered_grids.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/staggered_grids.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/staggered_grids.rst"
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

# Staggered grids

<div id="print-main-content">

<div id="jb-print-toc">

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="staggered-grids" class="section">

<span id="sec-staggergrids"></span>

# Staggered grids<a href="#staggered-grids" class="headerlink"
title="Permalink to this heading">#</a>

Until now all quantities have been cell-centred i.e. both velocities and
conserved quantities were defined at the same locations. This is because
these methods are simple and this was the scheme used in the original
BOUT. This class of methods can however be susceptible to grid-grid
oscillations, and so most shock-capturing schemes involve densities and
velocities (for example) which are not defined at the same location:
their grids are staggered.

By default BOUT++ runs with all quantities at cell centre. To enable
staggered grids, set:

<div class="highlight-cpp notranslate">

<div class="highlight">

    StaggerGrids = true

</div>

</div>

in the top section of the <span class="pre">`BOUT.inp`</span> file. The
**test-staggered** example illustrates how to use staggered grids in
BOUT++.

There are four possible locations in a grid cell where a quantity can be
defined in BOUT++: centre, lower X, lower Y, and lower Z. These are
illustrated in
<a href="#staggergrids-location" class="reference internal"><span
class="std std-numref">Fig. 18</span></a>.

<figure id="id1" class="align-default">
<span id="staggergrids-location"></span><img
src="../_images/stagLocations.png"
alt="Staggered grid cell locations" />
<figcaption><p><span class="caption-number">Fig. 18 </span><span
class="caption-text">The four possible cell locations for defining
quantities</span><a href="#id1" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

To specify the location of a variable, use the method <a
href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv4N7Field3D11setLocationE8CELL_LOC"
class="reference internal" title="Field3D::setLocation"><span
class="pre"><code
class="sourceCode cpp">Field3D<span class="op">::</span>setLocation<span class="op">()</span></code></span></a>
with one of the
<a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv48CELL_LOC"
class="reference internal" title="CELL_LOC"><span class="pre"><code
class="sourceCode cpp">CELL_LOC</code></span></a> locations <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv411CELL_CENTRE"
class="reference internal" title="CELL_CENTRE"><span class="pre"><code
class="sourceCode cpp">CELL_CENTRE</code></span></a>, <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv49CELL_XLOW"
class="reference internal" title="CELL_XLOW"><span class="pre"><code
class="sourceCode cpp">CELL_XLOW</code></span></a>, <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv49CELL_YLOW"
class="reference internal" title="CELL_YLOW"><span class="pre"><code
class="sourceCode cpp">CELL_YLOW</code></span></a>, or <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv49CELL_ZLOW"
class="reference internal" title="CELL_ZLOW"><span class="pre"><code
class="sourceCode cpp">CELL_ZLOW</code></span></a>.

The key lines in the **staggered_grid** example which specify the
locations of the evolving variables are:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D n, v;

    int init(bool restart) {
      v.setLocation(CELL_YLOW); // Staggered relative to n
      SOLVE_FOR(n, v);
      ...

</div>

</div>

which makes the velocity <span class="pre">`v`</span> staggered to the
lower side of the cell in Y, whilst the density
<span class="math notranslate nohighlight">\\n\\</span> remains cell
centred.

<div class="admonition note">

Note

If BOUT++ was not configued with <span class="pre">`-DCHECK=0`</span>,
<a
href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv4N7Field3D11setLocationE8CELL_LOC"
class="reference internal" title="Field3D::setLocation"><span
class="pre"><code
class="sourceCode cpp">Field3D<span class="op">::</span>setLocation<span class="op">()</span></code></span></a>
will throw an exception if you don’t have staggered grids turned on and
try to set the location to something other than <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv411CELL_CENTRE"
class="reference internal" title="CELL_CENTRE"><span class="pre"><code
class="sourceCode cpp">CELL_CENTRE</code></span></a>. If you want to be
able to run your model with and without staggered grids, you should do
something like:

<div class="highlight-cpp notranslate">

<div class="highlight">

    if (v.getMesh()->StaggerGrids) {
      v.setLocation(CELL_YLOW);
    }

</div>

</div>

Compiling BOUT++ with checks turned off will instead cause <a
href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv4N7Field3D11setLocationE8CELL_LOC"
class="reference internal" title="Field3D::setLocation"><span
class="pre"><code
class="sourceCode cpp">Field3D<span class="op">::</span>setLocation<span class="op">()</span></code></span></a>
to silently set the location to <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv411CELL_CENTRE"
class="reference internal" title="CELL_CENTRE"><span class="pre"><code
class="sourceCode cpp">CELL_CENTRE</code></span></a> if staggered grids
are off, regardless of what you pass it.

</div>

Arithmetic operations can only be performed between variables with the
same location. When performing a calculation at one location, to include
a variable from a different location, use the interpolation routines.
Include the header file

<div class="highlight-cpp notranslate">

<div class="highlight">

    #include <interpolation.hxx>

</div>

</div>

then use the
<span class="pre">`interp_to(field,`</span>` `<span class="pre">`location,`</span>` `<span class="pre">`region)`</span>
function. For example, given a <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv411CELL_CENTRE"
class="reference internal" title="CELL_CENTRE"><span class="pre"><code
class="sourceCode cpp">CELL_CENTRE</code></span></a> field
<span class="pre">`n`</span> and a <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv49CELL_YLOW"
class="reference internal" title="CELL_YLOW"><span class="pre"><code
class="sourceCode cpp">CELL_YLOW</code></span></a> field
<span class="pre">`v`</span>, to calculate
<span class="pre">`n*v`</span> at <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv49CELL_YLOW"
class="reference internal" title="CELL_YLOW"><span class="pre"><code
class="sourceCode cpp">CELL_YLOW</code></span></a>, call
<span class="pre">`interp_to(n,`</span>` `<span class="pre">`CELL_YLOW)*v`</span>
whose result will be <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv49CELL_YLOW"
class="reference internal" title="CELL_YLOW"><span class="pre"><code
class="sourceCode cpp">CELL_YLOW</code></span></a> as
<span class="pre">`n`</span> is interpolated.

<div class="admonition note">

Note

The region argument is optional but useful (see
<a href="../developer_docs/data_types.html#sec-iterating"
class="reference internal"><span class="std std-ref">Iterating over
fields</span></a> for more on regions). The default
<a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv47RGN_ALL"
class="reference internal" title="RGN_ALL"><span class="pre"><code
class="sourceCode cpp">RGN_ALL</code></span></a> reproduces the
historical behaviour of BOUT++, which communicates before returning the
result from <span class="pre">`interp_to`</span>. Communication is
necessary because the result of interpolation in the guard cells depends
on data from another process (except, currently, in the case of
interpolation in the z-direction which can be done without communication
because all the z-points are on the same process).

Using RGN_NOBNDRY no communication is performed (so interp_to is faster,
potentially significantly faster when using many processes) and all the
guard cells are invalid. Whichever region is used, the boundary guard
cells are invalid since no boundary condition is applied in interp_to.
If the guard cells are needed (e.g. to calculate a derivative) a
boundary condition must be applied explicitly to the result.

RGN_NOX and RGN_NOY currently have identical behaviour to RGN_ALL
because at present BOUT++ has no functions for single-direction
communication which could in principle be used in these cases (if the
combination of region and direction of interpolation allows it). x- or
y-interpolation can never be calculated in guard cells without
communication because the corner guard cells are never valid.

</div>

Differential operators by default return fields which are defined at the
same location as their inputs, so here
<span class="pre">`Grad_par(v)`</span> would be <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv49CELL_YLOW"
class="reference internal" title="CELL_YLOW"><span class="pre"><code
class="sourceCode cpp">CELL_YLOW</code></span></a> . If this is not what
is wanted, give the location of the result as an additional argument:
<span class="pre">`Grad_par(v,`</span>` `<span class="pre">`CELL_CENTRE)`</span>
uses staggered differencing to produce a result which is defined at the
cell centres. It is an error to ask for the result to be staggered in a
different direction from the input as the best that could be done would
be to calculate output at <span class="pre">`CELL_CENTRE`</span> and
then interpolate this to the requested location, but the interpolation
would in general require boundary conditions to be applied first.

Advection operators which take two arguments return a result which is
defined at the location of the field being advected. For example
<span class="pre">`Vpar_Grad_par(v,`</span>` `<span class="pre">`f)`</span>
calculates <span class="math notranslate nohighlight">\\v \nabla\_{||}
f\\</span> and returns a result at the same location as
<span class="pre">`f`</span>. If <span class="pre">`v`</span> and
<span class="pre">`f`</span> are defined at the same locations then
centred differencing is used, if one is centred and the other staggered
then staggered differencing is used; it is an error for both to be
staggered to different locations. As with other differential operators,
the required location of the result can be given as an optional
argument, but at least for now it is an error for this to be different
from the location of the field being advected
(<span class="pre">`f`</span> here).

Laplace solvers (see
<a href="laplacian.html#sec-laplacian" class="reference internal"><span
class="std std-ref">Laplacian inversion</span></a>) also need a location
to be set in order not to operate at
<span class="pre">`CELL_CENTRE`</span>: this allows the solver to check
the locations of coefficients and right-hand-side which are passed to
it, and to return a result at the correct location. For example, in an
electromagnetic case with staggered grids, the solver for the magnetic
vector potential
<span class="math notranslate nohighlight">\\A\_\\\\</span> is probably
defined on the staggered grid. The location is set by the second
optional argument to <span class="pre">`Laplacian::create()`</span>,
after the options. For example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    aparSolver = Laplacian::create(&options["apar_solver"], CELL_YLOW);

</div>

</div>

</div>

<div class="prev-next-area">

<a href="algebraic_operators.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Algebraic operators

</div>

<a href="eigenvalue_solver.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Eigenvalue solver

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
