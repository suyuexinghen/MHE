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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/laplacian.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/laplacian.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/laplacian.rst"
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

# Laplacian inversion

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#usage-of-the-laplacian-inversion"
  class="reference internal nav-link">Usage of the laplacian inversion</a>
- <a href="#numerical-implementation"
  class="reference internal nav-link">Numerical implementation</a>
  - <a href="#using-tridiagonal-solvers"
    class="reference internal nav-link">Using tridiagonal solvers</a>
  - <a href="#using-petsc-solvers" class="reference internal nav-link">Using
    PETSc solvers</a>
  - <a href="#example-the-5-point-stencil"
    class="reference internal nav-link">Example: The 5-point stencil</a>
- <a href="#implementation-internals"
  class="reference internal nav-link">Implementation internals</a>
  - <a href="#serial-tridiagonal-solver"
    class="reference internal nav-link">Serial tridiagonal solver</a>
  - <a href="#serial-band-solver" class="reference internal nav-link">Serial
    band solver</a>
  - <a href="#spt-parallel-tridiagonal"
    class="reference internal nav-link">SPT parallel tridiagonal</a>
  - <a href="#cyclic-algorithm" class="reference internal nav-link">Cyclic
    algorithm</a>
  - <a href="#multigrid-solver"
    class="reference internal nav-link">Multigrid solver</a>
  - <a href="#naulin-solver" class="reference internal nav-link">Naulin
    solver</a>
  - <a href="#iterative-parallel-tridiagonal-solver"
    class="reference internal nav-link">Iterative Parallel Tridiagonal
    solver</a>
- <a href="#laplacexy" class="reference internal nav-link">LaplaceXY</a>
- <a href="#laplacexz" class="reference internal nav-link">LaplaceXZ</a>
  - <a href="#implementations"
    class="reference internal nav-link">Implementations</a>
  - <a href="#test-case" class="reference internal nav-link">Test case</a>
  - <a href="#blob2d-comparison" class="reference internal nav-link">Blob2d
    comparison</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="laplacian-inversion" class="section">

<span id="sec-laplacian"></span>

# Laplacian inversion<a href="#laplacian-inversion" class="headerlink"
title="Permalink to this heading">#</a>

A common problem in plasma models is to solve an equation of the form

<div id="equation-full-laplace-inv"
class="math notranslate nohighlight">

<span class="eqno">(3)<a href="#equation-full-laplace-inv" class="headerlink"
title="Permalink to this equation">#</a></span>\\d\nabla^2\_\perp x +
\frac{1}{c_1}(\nabla\_\perp c_2)\cdot\nabla\_\perp x + a x = b\\

</div>

For example,

<div class="math notranslate nohighlight">

\\\nabla\_\perp^2 x + a x = b\\

</div>

appears in reduced MHD for the vorticity inversion and
<span class="math notranslate nohighlight">\\j\_{||}\\</span>.

Alternative formulations and ways to invert equation
<a href="#equation-full-laplace-inv" class="reference internal">(3)</a>
can be found in section
<a href="#sec-laplacexy" class="reference internal"><span
class="std std-ref">LaplaceXY</span></a> and
<a href="#sec-laplacexz" class="reference internal"><span
class="std std-ref">LaplaceXZ</span></a>

Several implementations of the Laplacian solver are available, which are
selected by changing the “type” setting.The currently available
implementations are listed in table
<a href="#tab-laplacetypes" class="reference internal"><span
class="std std-numref">Table 12</span></a>.

<span id="tab-laplacetypes"></span>

<table id="id2" class="table">
<caption><span class="caption-number">Table 12 </span><span
class="caption-text">Laplacian implementation types</span><a href="#id2"
class="headerlink" title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Description</p></th>
<th class="head"><p>Requirements</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>cyclic</p></td>
<td><p>Serial/parallel. Gathers boundary rows onto one
processor.</p></td>
<td></td>
</tr>
<tr class="row-odd">
<td><p><a href="#sec-petsc-laplace"
class="reference internal">petsc</a></p></td>
<td><p>Serial/parallel. Lots of methods, no Boussinesq</p></td>
<td><p>PETSc (section <a href="advanced_install.html#sec-petsc-install"
class="reference internal"><span
class="std std-ref">PETSc</span></a>)</p></td>
</tr>
<tr class="row-even">
<td><p>petsc3damg</p></td>
<td><p>Serial/parallel. Solves full 3D operator (with y-derivatives)
with algebraic multigrid.</p></td>
<td><p>PETSc (section <a href="advanced_install.html#sec-petsc-install"
class="reference internal"><span
class="std std-ref">PETSc</span></a>)</p></td>
</tr>
<tr class="row-odd">
<td><p>multigrid</p></td>
<td><p>Serial/parallel. Geometric multigrid, no Boussinesq</p></td>
<td></td>
</tr>
<tr class="row-even">
<td><p><a href="#sec-naulin"
class="reference internal">naulin</a></p></td>
<td><p>Serial/parallel. Iterative treatment of non-Boussinesq
terms</p></td>
<td></td>
</tr>
<tr class="row-odd">
<td><p><a href="#sec-tri"
class="reference internal">serial_tri</a></p></td>
<td><p>Serial only. Thomas algorithm for tridiagonal system.</p></td>
<td><p>Lapack (section <a href="advanced_install.html#sec-lapack"
class="reference internal"><span
class="std std-ref">LAPACK</span></a>)</p></td>
</tr>
<tr class="row-even">
<td><p><a href="#sec-band"
class="reference internal">serial_band</a></p></td>
<td><p>Serial only. Enables 4th-order accuracy</p></td>
<td><p>Lapack (section <a href="advanced_install.html#sec-lapack"
class="reference internal"><span
class="std std-ref">LAPACK</span></a>)</p></td>
</tr>
<tr class="row-odd">
<td><p><a href="#sec-spt" class="reference internal">spt</a></p></td>
<td><p>Parallel only (NXPE&gt;1). Thomas algorithm.</p></td>
<td></td>
</tr>
<tr class="row-even">
<td><p><a href="#sec-ipt" class="reference internal">ipt</a></p></td>
<td><p>Iterative parallel tridiagonal solver. Parallel only, but
automatically falls back to Thomas algorithm for NXPE=1.</p></td>
<td></td>
</tr>
</tbody>
</table>

<div id="usage-of-the-laplacian-inversion" class="section">

## Usage of the laplacian inversion<a href="#usage-of-the-laplacian-inversion" class="headerlink"
title="Permalink to this heading">#</a>

In BOUT++, equation
<a href="#equation-full-laplace-inv" class="reference internal">(3)</a>
can be solved in two ways. The first method Fourier transforms in the
<span class="math notranslate nohighlight">\\z\\</span>-direction,
whilst the other solves the full two dimensional problem by matrix
inversion. The derivation of
<span class="math notranslate nohighlight">\\\nabla\_\perp^2f\\</span>
for a general coordinate system can be found in the
<a href="coordinates.html#sec-field-aligned-coordinates"
class="reference internal"><span class="std std-ref">Field-aligned
coordinates</span></a> section. What is important, is to note that if
<span class="math notranslate nohighlight">\\g\_{xy}\\</span> and
<span class="math notranslate nohighlight">\\g\_{yz}\\</span> are
non-zero, BOUT++ neglects the
<span class="math notranslate nohighlight">\\y\\</span>-parallel
derivatives when using the solvers <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> and
<a href="../_breathe_autogen/file/laplacexz_8hxx.html#_CPPv49LaplaceXZ"
class="reference internal" title="LaplaceXZ"><span class="pre"><code
class="sourceCode cpp">LaplaceXZ</code></span></a>.

By neglecting the
<span class="math notranslate nohighlight">\\y\\</span>-derivatives (or
if
<span class="math notranslate nohighlight">\\g\_{xy}=g\_{yz}=0\\</span>),
one can solve equation
<a href="#equation-full-laplace-inv" class="reference internal">(3)</a>
<span class="math notranslate nohighlight">\\y\\</span> plane by
<span class="math notranslate nohighlight">\\y\\</span> plane.

The first approach utilizes the fact that it is possible to Fourier
transform the equation in
<span class="math notranslate nohighlight">\\z\\</span> (using some
assumptions described in section
<a href="#sec-num-laplace" class="reference internal"><span
class="std std-ref">Numerical implementation</span></a>), and solve a
tridiagonal system for each mode. These inversion problems are
band-diagonal (tri-diagonal in the case of 2nd-order differencing) and
so inversions can be very efficient:
<span class="math notranslate nohighlight">\\O(n_z \log n_z)\\</span>
for the FFTs,
<span class="math notranslate nohighlight">\\O(n_x)\\</span> for
tridiagonal inversion using the Thomas algorithm, where
<span class="math notranslate nohighlight">\\n_x\\</span> and
<span class="math notranslate nohighlight">\\n_z\\</span> are the number
of grid-points in the
<span class="math notranslate nohighlight">\\x\\</span> and
<span class="math notranslate nohighlight">\\z\\</span> directions
respectively.

In the second approach, the full
<span class="math notranslate nohighlight">\\2\\</span>-D system is
solved. The available solvers for this approach are ‘multigrid’ using a
multigrid algorithm; ‘naulin’ using an iterative scheme to correct the
FFT-based approach; or ‘petsc’ using KSP linear solvers from the PETSc
library (this requires PETSc to be built with BOUT++).

The <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> class is defined in
<span class="pre">`invert_laplace.hxx`</span> and solves problems
formulated like equation
<a href="#equation-full-laplace-inv" class="reference internal">(3)</a>
To use this class, first create an instance of it:

<div class="highlight-cpp notranslate">

<div class="highlight">

    std::unique_ptr<Laplacian> lap = Laplacian::create();

</div>

</div>

By default, this will use the options in a section called “laplace”, but
can be given a different section as an argument. By default
<span class="math notranslate nohighlight">\\d = 1\\</span>,
<span class="math notranslate nohighlight">\\a = 0\\</span>, and
<span class="math notranslate nohighlight">\\c_1=c_2=1\\</span>. To set
the values of these coefficients, there are the
<span class="pre">`setCoefA()`</span>,
<span class="pre">`setCoefC1()`</span>,
<span class="pre">`setCoefC2()`</span>,
<span class="pre">`setCoefC()`</span> (which sets both
<span class="math notranslate nohighlight">\\c_1\\</span> and
<span class="math notranslate nohighlight">\\c_2\\</span> to its
argument), and <span class="pre">`setCoefD()`</span> methods:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field2D a = ...;
    lap->setCoefA(a);
    lap->setCoefC(0.5);

</div>

</div>

arguments can be
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a>,
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a>, or
<a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv48BoutReal"
class="reference internal" title="BoutReal"><span class="pre"><code
class="sourceCode cpp">BoutReal</code></span></a> values. Note that FFT
solvers will use only the DC part of
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> arguments.

Settings for the inversion can be set in the input file under the
section <span class="pre">`laplace`</span> (default) or whichever
settings section name was specified when the <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> class was created.
Commonly used settings are listed in tables
<a href="#tab-laplacesettings" class="reference internal"><span
class="std std-numref">Table 13</span></a> to
<a href="#tab-laplaceflags" class="reference internal"><span
class="std std-numref">Table 16</span></a>.

In particular boundary conditions on the
<span class="math notranslate nohighlight">\\x\\</span> boundaries can
be set using the and <span class="pre">`outer_boundary_flags`</span>
variables, as detailed in table
<a href="#tab-laplacebcflags" class="reference internal"><span
class="std std-numref">Table 15</span></a>. Note that DC
(‘direct-current’) refers to
<span class="math notranslate nohighlight">\\k = 0\\</span> Fourier
component, AC (‘alternating-current’) refers to
<span class="math notranslate nohighlight">\\k \neq 0\\</span> Fourier
components. Non-Fourier solvers use AC options (and ignore DC ones).
Multiple boundary conditions can be selected by adding together the
required boundary condition flag values together. For example,
<span class="pre">`inner_boundary_flags`</span>` `<span class="pre">`=`</span>` `<span class="pre">`3`</span>
will set a Neumann boundary condition on both AC and DC components.

It is pertinent to note here that the boundary in BOUT++ is defined by
default to be located half way between the first guard point and first
point inside the domain. For example, when a Dirichlet boundary
condition is set, using
<span class="pre">`inner_boundary_flags`</span>` `<span class="pre">`=`</span>` `<span class="pre">`0`</span>
, <span class="pre">`16`</span>, or <span class="pre">`32`</span>, then
the first guard point,
<span class="math notranslate nohighlight">\\f\_{-}\\</span> will be set
to <span class="math notranslate nohighlight">\\f\_{-} = 2v -
f\_+\\</span>, where
<span class="math notranslate nohighlight">\\f\_+\\</span> is the first
grid point inside the domain, and
<span class="math notranslate nohighlight">\\v\\</span> is the value to
which the boundary is being set to.

The <span class="pre">`global_flags`</span>,
<span class="pre">`inner_boundary_flags`</span>,
<span class="pre">`outer_boundary_flags`</span> and
<span class="pre">`flags`</span> values can also be set from within the
physics module using <span class="pre">`setGlobalFlags`</span>,
<span class="pre">`setInnerBoundaryFlags`</span> ,
<span class="pre">`setOuterBoundaryFlags`</span> and
<span class="pre">`setFlags`</span>.

<div class="highlight-cpp notranslate">

<div class="highlight">

    lap->setGlobalFlags(Global_Flags_Value);
    lap->setInnerBoundaryFlags(Inner_Flags_Value);
    lap->setOuterBoundaryFlags(Outer_Flags_Value);
    lap->setFlags(Flags_Value);

</div>

</div>

<span id="tab-laplacesettings"></span>

<table id="id3" class="table">
<caption><span class="caption-number">Table 13 </span><span
class="caption-text">Laplacian inversion options</span><a href="#id3"
class="headerlink" title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Meaning</p></th>
<th class="head"><p>Default value</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">type</code></span></p></td>
<td><p>Which implementation to use. See table <a
href="#tab-laplacetypes" class="reference internal"><span
class="std std-numref">Table 12</span></a></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">cyclic</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">filter</code></span></p></td>
<td><p>Filter out modes above <span
class="math notranslate nohighlight">\((1-\)</span><span
class="pre"><code
class="docutils literal notranslate">filter</code></span><span
class="math notranslate nohighlight">\()\times k_{max}\)</span>, if
using Fourier solver</p></td>
<td><p>0</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">maxmode</code></span></p></td>
<td><p>Filter modes with <span class="math notranslate nohighlight">\(n
&gt;\)</span><span class="pre"><code
class="docutils literal notranslate">maxmode</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">MZ</code></span>/2</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">all_terms</code></span></p></td>
<td><p>Include first derivative terms</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">true</code></span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">nonuniform</code></span></p></td>
<td><p>Include <a
href="differential_operators.html#sec-diffmethod-nonuniform"
class="reference internal"><span class="std std-ref">corrections for
non-uniform meshes</span></a> (dx not constant)</p></td>
<td><p>Same as global <span class="pre"><code
class="docutils literal notranslate">non_uniform</code></span>. See <a
href="differential_operators.html#sec-diffmethod-nonuniform"
class="reference internal"><span
class="std std-ref">here</span></a></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">global_flags</code></span></p></td>
<td><p>Sets global inversion options See table <a
href="#tab-laplaceglobalflags" class="reference internal"><span
class="std std-ref">Laplace global flags</span></a></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">0</code></span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">inner_boundary_flags</code></span></p></td>
<td><p>Sets boundary conditions on inner boundary. See table <a
href="#tab-laplacebcflags" class="reference internal"><span
class="std std-ref">Laplace boundary flags</span></a></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">0</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">outer_boundary_flags</code></span></p></td>
<td><p>Sets boundary conditions on outer boundary. See table <a
href="#tab-laplacebcflags" class="reference internal"><span
class="std std-ref">Laplace boundary flags</span></a></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">0</code></span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">flags</code></span></p></td>
<td><p>DEPRECATED. Sets global solver options and boundary conditions.
See <a href="#tab-laplaceflags" class="reference internal"><span
class="std std-ref">Laplace flags</span></a> or <a
href="../_breathe_autogen/file/invert__laplace_8cxx.html"
class="reference internal"><span
class="doc">invert_laplace.cxx</span></a></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">0</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">include_yguards</code></span></p></td>
<td><p>Perform inversion in <span
class="math notranslate nohighlight">\(y\)</span>-boundary guard
cells</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">false</code></span></p></td>
</tr>
</tbody>
</table>

<div class="line">

  

</div>

<span id="tab-laplaceglobalflags"></span>

<table id="id4" class="table">
<caption><span class="caption-number">Table 14 </span><span
class="caption-text">Laplacian inversion <span class="pre"><code
class="docutils literal notranslate">global_flags</code></span> values:
add the required quantities together.</span><a href="#id4"
class="headerlink" title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Flag</p></th>
<th class="head"><p>Meaning</p></th>
<th class="head"><p>Code variable</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>0</p></td>
<td><p>No global option set</p></td>
<td><p><span class="math notranslate nohighlight">\(-\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>1</p></td>
<td><p>zero DC component (Fourier solvers)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_ZERO_DC</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>2</p></td>
<td><p>set initial guess to 0 (iterative solvers)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_START_NEW</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>4</p></td>
<td><p>equivalent to <span class="pre"><code
class="docutils literal notranslate">outer_boundary_flags</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">=</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">128</code></span>, <span
class="pre"><code
class="docutils literal notranslate">inner_boundary_flags</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">=</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">128</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_BOTH_BNDRY_ONE</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>8</p></td>
<td><p>Use 4th order differencing (Apparently not actually implemented
anywhere!!!)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_4TH_ORDER</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>16</p></td>
<td><p>Set constant component (<span
class="math notranslate nohighlight">\(k_x = k_z = 0\)</span>) to
zero</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_KX_ZERO</code></span></p></td>
</tr>
</tbody>
</table>

<div class="line">

  

</div>

<span id="tab-laplacebcflags"></span>

<table id="id5" class="table">
<caption><span class="caption-number">Table 15 </span><span
class="caption-text">Laplacian inversion <span class="pre"><code
class="docutils literal notranslate">outer_boundary_flags</code></span>
or <span class="pre"><code
class="docutils literal notranslate">inner_boundary_flags</code></span>
values: add the required quantities together.</span><a href="#id5"
class="headerlink" title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Flag</p></th>
<th class="head"><p>Meaning</p></th>
<th class="head"><p>Code variable</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>0</p></td>
<td><p>Dirichlet (Set boundary to 0)</p></td>
<td><p><span class="math notranslate nohighlight">\(-\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>1</p></td>
<td><p>Neumann on DC component (set gradient to 0)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_DC_GRAD</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>2</p></td>
<td><p>Neumann on AC component (set gradient to 0)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_AC_GRAD</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>4</p></td>
<td><p>Zero or decaying Laplacian on AC components ( <span
class="math notranslate nohighlight">\(\frac{\partial^2}{\partial
x^2}+k_z^2\)</span> vanishes/decays)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_AC_LAP</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>8</p></td>
<td><p>Use symmetry to enforce zero value or gradient (redundant for 2nd
order now)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_SYM</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>16</p></td>
<td><p>Set boundary condition to values in boundary guard cells of
second argument, <span class="pre"><code
class="docutils literal notranslate">x0</code></span>, of <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv4N9Laplacian5solveERK9FieldPerp"
class="reference internal" title="Laplacian::solve"><span
class="pre"><code
class="sourceCode cpp">Laplacian<span class="op">::</span>solve<span class="op">(</span><span class="at">const</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp">Field3D</code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="op">&amp;</span>b<span class="op">,</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="at">const</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp">Field3D</code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="op">&amp;</span>x0<span class="op">)</span></code></span></a>.
May be combined with any combination of 0, 1 and 2, i.e. a Dirichlet or
Neumann boundary condition set to values which are <span
class="math notranslate nohighlight">\(\neq 0\)</span> or <span
class="math notranslate nohighlight">\(f(y)\)</span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_SET</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>32</p></td>
<td><p>Set boundary condition to values in boundary guard cells of RHS,
<span class="pre"><code
class="docutils literal notranslate">b</code></span> in <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv4N9Laplacian5solveERK9FieldPerp"
class="reference internal" title="Laplacian::solve"><span
class="pre"><code
class="sourceCode cpp">Laplacian<span class="op">::</span>solve<span class="op">(</span><span class="at">const</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp">Field3D</code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="op">&amp;</span>b<span class="op">,</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="at">const</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp">Field3D</code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="op">&amp;</span>x0<span class="op">)</span></code></span></a>.
May be combined with any combination of 0, 1 and 2, i.e. a Dirichlet or
Neumann boundary condition set to values which are <span
class="math notranslate nohighlight">\(\neq 0\)</span> or <span
class="math notranslate nohighlight">\(f(y)\)</span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_RHS</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>64</p></td>
<td><p>Zero or decaying Laplacian on DC components (<span
class="math notranslate nohighlight">\(\frac{\partial^2}{\partial
x^2}\)</span> vanishes/decays)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_DC_LAP</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>128</p></td>
<td><p>Assert that there is only one guard cell in the <span
class="math notranslate nohighlight">\(x\)</span>-boundary</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_BNDRY_ONE</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>256</p></td>
<td><p>DC value is set to parallel gradient, <span
class="math notranslate nohighlight">\(\nabla_\parallel
f\)</span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_DC_GRADPAR</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>512</p></td>
<td><p>DC value is set to inverse of parallel gradient <span
class="math notranslate nohighlight">\(1/\nabla_\parallel
f\)</span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_DC_GRADPARINV</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>1024</p></td>
<td><p>Boundary condition for inner ‘boundary’ of cylinder</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">INVERT_IN_CYLINDER</code></span></p></td>
</tr>
</tbody>
</table>

<div class="line">

  

</div>

<span id="tab-laplaceflags"></span>

<table id="id6" class="table">
<caption><span class="caption-number">Table 16 </span><span
class="caption-text">Laplacian inversion <span class="pre"><code
class="docutils literal notranslate">flags</code></span> values
(DEPRECATED!): add the required quantities together.</span><a
href="#id6" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Flag</p></th>
<th class="head"><p>Meaning</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>1</p></td>
<td><p>Zero-gradient DC on inner (X) boundary. Default is
zero-value</p></td>
</tr>
<tr class="row-odd">
<td><p>2</p></td>
<td><p>Zero-gradient AC on inner boundary</p></td>
</tr>
<tr class="row-even">
<td><p>4</p></td>
<td><p>Zero-gradient DC on outer boundary</p></td>
</tr>
<tr class="row-odd">
<td><p>8</p></td>
<td><p>Zero-gradient AC on outer boundary</p></td>
</tr>
<tr class="row-even">
<td><p>16</p></td>
<td><p>Zero DC component everywhere</p></td>
</tr>
<tr class="row-odd">
<td><p>32</p></td>
<td><p>Not used currently</p></td>
</tr>
<tr class="row-even">
<td><p>64</p></td>
<td><p>Set width of boundary to 1 (default is <span class="pre"><code
class="docutils literal notranslate">MXG</code></span>)</p></td>
</tr>
<tr class="row-odd">
<td><p>128</p></td>
<td><p>Use 4<span
class="math notranslate nohighlight">\(^{th}\)</span>-order band solver
(default is 2<span class="math notranslate nohighlight">\(^{nd}\)</span>
order tridiagonal)</p></td>
</tr>
<tr class="row-even">
<td><p>256</p></td>
<td><p>Attempt to set zero laplacian AC component on inner boundary by
combining 2nd and 4th-order differencing at the boundary. Ignored if
tridiagonal solver used.</p></td>
</tr>
<tr class="row-odd">
<td><p>512</p></td>
<td><p>Zero laplacian AC on outer boundary</p></td>
</tr>
<tr class="row-even">
<td><p>1024</p></td>
<td><p>Symmetric boundary condition on inner boundary</p></td>
</tr>
<tr class="row-odd">
<td><p>2048</p></td>
<td><p>Symmetric outer boundary condition</p></td>
</tr>
</tbody>
</table>

To perform the inversion, there’s the <span class="pre">`solve`</span>
method

<div class="highlight-cpp notranslate">

<div class="highlight">

    x = lap->solve(b);

</div>

</div>

There are also functions compatible with older versions of the BOUT++
code, but these are deprecated:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field2D a, c, d;
    invert_laplace(b, x, flags, &a, &c, &d);

</div>

</div>

and

<div class="highlight-cpp notranslate">

<div class="highlight">

    x = invert_laplace(b, flags, &a, &c, &d);

</div>

</div>

The input <span class="pre">`b`</span> and output
<span class="pre">`x`</span> are 3D fields, and the coefficients
<span class="pre">`a`</span>, <span class="pre">`c`</span>, and
<span class="pre">`d`</span> are pointers to 2D fields. To omit any of
the three coefficients, set them to NULL.

</div>

<div id="numerical-implementation" class="section">

<span id="sec-num-laplace"></span>

## Numerical implementation<a href="#numerical-implementation" class="headerlink"
title="Permalink to this heading">#</a>

We will here go through the implementation of the laplacian inversion
algorithm, as it is performed in BOUT++. We would like to solve the
following equation for
<span class="math notranslate nohighlight">\\f\\</span>

<div id="equation-to-invert" class="math notranslate nohighlight">

<span class="eqno">(4)<a href="#equation-to-invert" class="headerlink"
title="Permalink to this equation">#</a></span>\\d\nabla\_\perp^2f +
\frac{1}{c_1}(\nabla\_\perp c_2)\cdot\nabla\_\perp f + af = b\\

</div>

BOUT++ neglects the
<span class="math notranslate nohighlight">\\y\\</span>-parallel
derivatives if
<span class="math notranslate nohighlight">\\g\_{xy}\\</span> and
<span class="math notranslate nohighlight">\\g\_{yz}\\</span> are
non-zero when using the solvers <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> and
<a href="../_breathe_autogen/file/laplacexz_8hxx.html#_CPPv49LaplaceXZ"
class="reference internal" title="LaplaceXZ"><span class="pre"><code
class="sourceCode cpp">LaplaceXZ</code></span></a>. For these two
solvers, equation
<a href="#equation-to-invert" class="reference internal">(4)</a> becomes
(see <a href="coordinates.html#sec-field-aligned-coordinates"
class="reference internal"><span class="std std-ref">Field-aligned
coordinates</span></a> for derivation)

<div id="equation-invert-expanded" class="math notranslate nohighlight">

<span class="eqno">(5)<a href="#equation-invert-expanded" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\\ &d
(g^{xx} \partial_x^2 + G^x \partial_x + g^{zz} \partial_z^2 + G^z
\partial_z + 2g^{xz} \partial_x \partial_z ) f \\ +& \frac{1}{c_1}(
{{\boldsymbol{e}}}^x \partial_x + {\boldsymbol{e}}^z \partial_z ) c_2
\cdot ({\boldsymbol{e}}^x \partial_x + {\boldsymbol{e}}^z \partial_z ) f
\\ +& af = b\end{split}\\

</div>

<div id="using-tridiagonal-solvers" class="section">

### Using tridiagonal solvers<a href="#using-tridiagonal-solvers" class="headerlink"
title="Permalink to this heading">#</a>

Since there are no parallel
<span class="math notranslate nohighlight">\\y\\</span>-derivatives if
<span class="math notranslate nohighlight">\\g\_{xy}=g\_{yz}=0\\</span>
(or if they are neglected), equation
<a href="#equation-to-invert" class="reference internal">(4)</a> will
only contain derivatives of
<span class="math notranslate nohighlight">\\x\\</span> and
<span class="math notranslate nohighlight">\\z\\</span> for the
dependent variable. The hope is that the modes in the periodic
<span class="math notranslate nohighlight">\\z\\</span> direction will
decouple, so that we in the end only have to invert for the
<span class="math notranslate nohighlight">\\x\\</span> coordinate.

If the modes decouples when Fourier transforming equation
<a href="#equation-invert-expanded" class="reference internal">(5)</a>,
we can use a tridiagonal solver to solve the equation for each Fourier
mode.

Using the discrete Fourier transform

<div class="math notranslate nohighlight">

\\F(x,y)\_{k} = \frac{1}{N}\sum\_{Z=0}^{N-1}f(x,y)\_{Z}\exp(\frac{-2\pi
i k Z}{N})\\

</div>

we see that the modes will not decouple if a term consist of a product
of two terms which depends on
<span class="math notranslate nohighlight">\\z\\</span>, as this would
give terms like

<div class="math notranslate nohighlight">

\\\frac{1}{N}\sum\_{Z=0}^{N-1} a(x,y)\_Z f(x,y)\_Z \exp(\frac{-2\pi i k
Z}{N})\\

</div>

Thus, in order to use a tridiagonal solver,
<span class="math notranslate nohighlight">\\a\\</span>,
<span class="math notranslate nohighlight">\\c_1\\</span>,
<span class="math notranslate nohighlight">\\c_2\\</span> and
<span class="math notranslate nohighlight">\\d\\</span> cannot be
functions of <span class="math notranslate nohighlight">\\z\\</span>.
Because of this, the
<span class="math notranslate nohighlight">\\{{\boldsymbol{e}}}^z
\partial_z c_2\\</span> term in equation
<a href="#equation-invert-expanded" class="reference internal">(5)</a>
is zero. Thus the tridiagonal solvers solve equations of the form

<div class="math notranslate nohighlight">

\\\begin{split}\\ &d(x,y) ( g^{xx}(x,y) \partial_x^2 + G^x(x,y)
\partial_x + g^{zz}(x,y) \partial_z^2 + G^z(x,y) \partial_z +
2g^{xz}(x,y) \partial_x \partial_z ) f(x,y,z) \\ +&
\frac{1}{c_1(x,y)}({{\boldsymbol{e}}}^x \partial_x c_2(x,y) ) \cdot (
{{\boldsymbol{e}}}^x \partial_x + \boldsymbol{e}^z \partial_z) f(x,y,z)
\\ +& a(x,y)f(x,y,z) = b(x,y,z)\end{split}\\

</div>

after using the discrete Fourier transform (see section
<a href="differential_operators.html#sec-derivatives-of-fft"
class="reference internal"><span class="std std-ref">Derivatives of the
Fourier transform</span></a>), we get

<div class="math notranslate nohighlight">

\\\begin{split}\\ &d ( g^{xx} \partial_x^2F_z + G^x \partial_xF_z +
g^{zz} \[i k\]^2F_z + G^z \[i k\]F_z + 2g^{xz} \partial_x\[i k\]F_z ) \\
+& \frac{1}{c_1}( {{\boldsymbol{e}}}^x \partial_x c_2 ) \cdot (
{{\boldsymbol{e}}}^x \partial_xF_z + \boldsymbol{e}^z i k F_z) \\ +&
aF_z = B_z\end{split}\\

</div>

which gives

<div id="equation-ft-laplace-inversion"
class="math notranslate nohighlight">

<span class="eqno">(6)<a href="#equation-ft-laplace-inversion" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\\ &d (
g^{xx} \partial_x^2 + G^x \partial_x - k^2 g^{zz} + i kG^z + i k2g^{xz}
\partial_x )F_z \\ +& \frac{1}{c_1} (\partial_x c_2 )
(g^{xx}\partial_xF_z + g^{xz} i k F_z) \\ +& aF_z = B_z\end{split}\\

</div>

As nothing in equation <a href="#equation-ft-laplace-inversion"
class="reference internal">(6)</a> couples points in
<span class="math notranslate nohighlight">\\y\\</span> together (since
we neglected the
<span class="math notranslate nohighlight">\\y\\</span>-derivatives if
<span class="math notranslate nohighlight">\\g\_{xy}\\</span> and
<span class="math notranslate nohighlight">\\g\_{yz}\\</span> were
non-zero) we can solve
<span class="math notranslate nohighlight">\\y\\</span>-plane by
<span class="math notranslate nohighlight">\\y\\</span>-plane. Also, as
the modes are decoupled, we may solve equation
<a href="#equation-ft-laplace-inversion"
class="reference internal">(6)</a>
<span class="math notranslate nohighlight">\\k\\</span> mode by
<span class="math notranslate nohighlight">\\k\\</span> mode in addition
to <span class="math notranslate nohighlight">\\y\\</span>-plane by
<span class="math notranslate nohighlight">\\y\\</span>-plane.

The second order centred approximation of the first and second
derivatives in <span class="math notranslate nohighlight">\\x\\</span>
reads

<div class="math notranslate nohighlight">

\\\begin{split}\partial_x f &\simeq \frac{-f\_{n-1} +
f\_{n+1}}{2\text{d}x} \\ \partial_x^2 f &\simeq \frac{f\_{n-1} -
f\_{n} + f\_{n+1}}{\text{d}x^2}\end{split}\\

</div>

This gives

<div class="math notranslate nohighlight">

\\\begin{split}\\ &d \left( g^{xx} \frac{F\_{z,n-1} - 2F\_{z,n} + F\_{z,
n+1}}{\text{d}x^2} + G^x \frac{-F\_{z,n-1} + F\_{z,n+1}}{2\text{d}x} -
k^2 g^{zz}F\_{z,n} \right. \\ &\left. \quad + i kG^zF\_{z,n} + i
k2g^{xz} \frac{-F\_{z,n-1} + F\_{z,n+1}}{2\text{d}x} \right) \\ +&
\frac{1}{c_1} \left( \frac{-c\_{2,n-1} + c\_{2,n+1}}{2\text{d}x} \right)
\left(g^{xx}\frac{-F\_{z,n-1} + F\_{z,n+1}}{2\text{d}x} + g^{xz} i k
F\_{z,n} \right) \\ +& aF\_{z,n} = B\_{z,n}\end{split}\\

</div>

collecting point by point

<div id="equation-discretized-laplace"
class="math notranslate nohighlight">

<span class="eqno">(7)<a href="#equation-discretized-laplace" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split} &\left(
\frac{dg^{xx}}{\text{d}x^2} - \frac{dG^x}{2\text{d}x} -
\frac{g^{xx}}{c\_{1,n}} \frac{-c\_{2,n-1} + c\_{2,n+1}}{4\text{d}x^2} -
i\frac{d k2g^{xz}}{2\text{d}x} \right) F\_{z,n-1} \\ +&\left( - \frac{
dg^{xx} }{\text{d}x^2} - dk^2 g^{zz} + a + idkG^z +
i\frac{g^{xz}}{c\_{1,n}} \frac{-c\_{2,n-1} + c\_{2,n+1}}{2\text{d}x}k
\right) F\_{z,n} \\ +&\left( \frac{dg^{xx}}{\text{d}x^2} +
\frac{dG^x}{2\text{d}x} + \frac{g^{xx}}{c\_{1,n}} \frac{-c\_{2,n-1} +
c\_{2,n+1}}{4\text{d}x^2} + i\frac{dk2g^{xz}}{2\text{d}x} \right) F\_{z,
n+1} \\ = B\_{z,n}\end{split}\\

</div>

We now introduce

<div class="math notranslate nohighlight">

\\ \begin{align}\begin{aligned}C_1 &= \frac{dg^{xx}}{\text{d}x^2}\\C_2
&= dg^{zz}\\C_3 &= \frac{2dg^{xz}}{2\text{d}x}\\C_4 &= \frac{dG^x +
g^{xx}\frac{-c\_{2,n-1} +
c\_{2,n+1}}{2c\_{1,n}\text{d}x}}{2\text{d}x}\\C_5 &= dG^z +
\frac{g^{xz}}{c\_{1,n}} \frac{-c\_{2,n-1} +
c\_{2,n+1}}{2\text{d}x}\end{aligned}\end{align} \\

</div>

which inserted in equation <a href="#equation-discretized-laplace"
class="reference internal">(7)</a> gives

<div class="math notranslate nohighlight">

\\( C_1 - C_4 -ikC_3 ) F\_{z,n-1} + ( -2C_1 - k^2C_2 +ikC_5 + a )
F\_{z,n} + ( C_1 + C_4 + ikC_3 ) F\_{z, n+1} = B\_{z,n}\\

</div>

This can be formulated as the matrix equation

<div class="math notranslate nohighlight">

\\AF_z=B_z\\

</div>

where the matrix <span class="math notranslate nohighlight">\\A\\</span>
is tridiagonal. The boundary conditions are set by setting the first and
last rows in <span class="math notranslate nohighlight">\\A\\</span> and
<span class="math notranslate nohighlight">\\B_z\\</span>.

The tridiagonal solvers previously required
<span class="math notranslate nohighlight">\\c_1 = c_2\\</span> in
equation
<a href="#equation-to-invert" class="reference internal">(4)</a>, but
from version 4.3 allow <span class="math notranslate nohighlight">\\c_1
\neq c_2\\</span>.

</div>

<div id="using-petsc-solvers" class="section">

<span id="sec-petsc-laplace"></span>

### Using PETSc solvers<a href="#using-petsc-solvers" class="headerlink"
title="Permalink to this heading">#</a>

When using PETSc, all terms of equation
<a href="#equation-invert-expanded" class="reference internal">(5)</a>
are used when inverting to find
<span class="math notranslate nohighlight">\\f\\</span>. Note that when
using PETSc, we do not Fourier decompose in the
<span class="math notranslate nohighlight">\\z\\</span>-direction, so it
may take substantially longer time to find the solution. As with the
tridiagonal solver, the fields are sliced in the
<span class="math notranslate nohighlight">\\y\\</span>-direction, and a
solution is found for one
<span class="math notranslate nohighlight">\\y\\</span> plane at the
time.

Before solving, equation
<a href="#equation-invert-expanded" class="reference internal">(5)</a>
is rewritten to the form
<span class="math notranslate nohighlight">\\A{{\boldsymbol{x}}}
={{\boldsymbol{b}}}\\</span> (however, the full
<span class="math notranslate nohighlight">\\A\\</span> is not expanded
in memory). To do this, a row
<span class="math notranslate nohighlight">\\i\\</span> in the matrix
<span class="math notranslate nohighlight">\\A\\</span> is indexed from
bottom left of the two dimensional field
<span class="math notranslate nohighlight">\\= (0,0) = 0\\</span> to top
right <span class="math notranslate nohighlight">\\= (\texttt{meshx}-1,
\texttt{meshz}-1) = \texttt{meshx}\cdot\texttt{meshz}-1\\</span> of the
two dimensional field. This is done in such a way so that a row
<span class="math notranslate nohighlight">\\i\\</span> in
<span class="math notranslate nohighlight">\\A\\</span> increments by
<span class="math notranslate nohighlight">\\1\\</span> for an increase
of <span class="math notranslate nohighlight">\\1\\</span> in the
<span class="math notranslate nohighlight">\\z-\\</span>direction, and
by <span class="math notranslate nohighlight">\\\texttt{meshz}\\</span>
for an increase of
<span class="math notranslate nohighlight">\\1\\</span> in the
<span class="math notranslate nohighlight">\\x-\\</span>direction, where
the variables
<span class="math notranslate nohighlight">\\\texttt{meshx}\\</span> and
<span class="math notranslate nohighlight">\\\texttt{meshz}\\</span>
represents the highest value of the field in the given direction.

Similarly to equation <a href="#equation-discretized-laplace"
class="reference internal">(7)</a>, the discretised version of equation
<a href="#equation-invert-expanded" class="reference internal">(5)</a>
can be written. Doing the same for the full two dimensional case yields:

Second order approximation

<div class="math notranslate nohighlight">

\\\begin{split}\\ & c\_{i,j} f\_{i,j} \\ &+ c\_{i-1,j-1} f\_{i-1,j-1} +
c\_{i-1,j} f\_{i-1,j} \\ &+ c\_{i-1,j+1} f\_{i-1,j+1} + c\_{i,j-1}
f\_{i,j-1} \\ &+ c\_{i,j+1} f\_{i,j+1} + c\_{i+1,j-1} f\_{i+1,j-1} \\ &+
c\_{i+1,j} f\_{i+1,j} + c\_{i+1,j+1} f\_{i+1,j+1} \\ =&
b\_{i,j}\end{split}\\

</div>

Fourth order approximation

<div class="math notranslate nohighlight">

\\\begin{split}\\ & c\_{i,j} f\_{i,j} \\ &+ c\_{i-2,j-2} f\_{i-2,j-2} +
c\_{i-2,j-1} f\_{i-2,j-1} \\ &+ c\_{i-2,j} f\_{i-2,j} + c\_{i-2,j+1}
f\_{i-2,j+1} \\ &+ c\_{i-2,j+2} f\_{i-2,j+2} + c\_{i-1,j-2} f\_{i-1,j-2}
\\ &+ c\_{i-1,j-1} f\_{i-1,j-1} + c\_{i-1,j} f\_{i-1,j} \\ &+
c\_{i-1,j+1} f\_{i-1,j+1} + c\_{i-1,j+2} f\_{i-1,j+2} \\ &+ c\_{i,j-2}
f\_{i,j-2} + c\_{i,j-1} f\_{i,j-1} \\ &+ c\_{i,j+1} f\_{i,j+1} +
c\_{i,j+2} f\_{i,j+2} \\ &+ c\_{i+1,j-2} f\_{i+1,j-2} + c\_{i+1,j-1}
f\_{i+1,j-1} \\ &+ c\_{i+1,j} f\_{i+1,j} + c\_{i+1,j+1} f\_{i+1,j+1} \\
&+ c\_{i+1,j+2} f\_{i+1,j+2} + c\_{i+2,j-2} f\_{i+2,j-2} \\ &+
c\_{i+2,j-1} f\_{i+2,j-1} + c\_{i+2,j} f\_{i+2,j} \\ &+ c\_{i+2,j+1}
f\_{i+2,j+1} + c\_{i+2,j+2} f\_{i+2,j+2} \\ =& b\_{i,j}\end{split}\\

</div>

To determine the coefficient for each node point, it is convenient to
introduce some quantities

<div class="math notranslate nohighlight">

\begin{align} &A_0 = a(x,y\_{\text{current}},z) &A_1 = dg^{xx}&\\ &A_2 =
dg^{zz} &A_3 = 2dg^{xz} \end{align}

</div>

In addition, we have:

Second order approximation (5-point stencil)

<div class="math notranslate nohighlight">

\\\begin{split}\texttt{ddx\\c} = \frac{\texttt{c2}\_{x+1} -
\texttt{c2}\_{x-1} }{2\texttt{c1}\text{d}x} \\ \texttt{ddz\\c} =
\frac{\texttt{c2}\_{z+1} - \texttt{c2}\_{z-1}
}{2\texttt{c1}\text{d}z}\end{split}\\

</div>

Fourth order approximation (9-point stencil)

<div class="math notranslate nohighlight">

\\\begin{split}\texttt{ddx\\c} = \frac{-\texttt{c2}\_{x+2} +
8\texttt{c2}\_{x+1} - 8\texttt{c2}\_{x-1} + \texttt{c2}\_{x-2} }{
12\texttt{c1}\text{d}x} \\ \texttt{ddz\\c} = \frac{-\texttt{c2}\_{z+2} +
8\texttt{c2}\_{z+1} - 8\texttt{c2}\_{z-1} + \texttt{c2}\_{z-2} }{
12\texttt{c1}\text{d}z}\end{split}\\

</div>

This gives

<div class="math notranslate nohighlight">

\\\begin{split}A_4 &= dG^x + g^{xx}\texttt{ddx\\c} +
g^{xz}\texttt{ddz\\c} \\ A_5 &= dG^z + g^{xz}\texttt{ddx\\c} +
g^{xx}\texttt{ddz\\c}\end{split}\\

</div>

The coefficients
<span class="math notranslate nohighlight">\\c\_{i+m,j+n}\\</span> are
finally being set according to the appropriate order of discretisation.
The coefficients can be found in the file
<span class="pre">`petsc_laplace.cxx`</span>.

</div>

<div id="example-the-5-point-stencil" class="section">

### Example: The 5-point stencil<a href="#example-the-5-point-stencil" class="headerlink"
title="Permalink to this heading">#</a>

Let us now consider the 5-point stencil for a mesh with
<span class="math notranslate nohighlight">\\3\\</span> inner points in
the <span class="math notranslate nohighlight">\\x\\</span>-direction,
and <span class="math notranslate nohighlight">\\3\\</span> inner points
in the
<span class="math notranslate nohighlight">\\z\\</span>-direction. The
<span class="math notranslate nohighlight">\\z\\</span> direction will
be periodic, and the
<span class="math notranslate nohighlight">\\x\\</span> direction will
have the boundaries half between the grid-point and the first ghost
point (see <a href="#fig-lapl-inv-mesh" class="reference internal"><span
class="std std-numref">Fig. 11</span></a>).

<figure id="id7" class="align-default">
<span id="fig-lapl-inv-mesh"></span><img
src="../_images/5PointStencilMesh.png" alt="The mesh" />
<figcaption><p><span class="caption-number">Fig. 11 </span><span
class="caption-text">The mesh: The inner boundary points in <span
class="math notranslate nohighlight">\(x\)</span> are coloured in
orange, whilst the outer boundary points in <span
class="math notranslate nohighlight">\(z\)</span> are coloured gray.
Inner points are coloured blue.</span><a href="#id7" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

Applying the
<span class="math notranslate nohighlight">\\5\\</span>-point stencil to
point <span class="math notranslate nohighlight">\\f\_{22}\\</span> this
mesh will result in
<a href="#fig-lapl-inv-mesh-w-stencil" class="reference internal"><span
class="std std-numref">Fig. 12</span></a>.

<figure id="id8" class="align-default">
<span id="fig-lapl-inv-mesh-w-stencil"></span><img
src="../_images/5PointStencilMeshWithStencil.png"
alt="The 5-point stencil for the Laplacian" />
<figcaption><p><span class="caption-number">Fig. 12 </span><span
class="caption-text">The mesh with a stencil in point <span
class="math notranslate nohighlight">\(f_{22}\)</span>: The point under
consideration is coloured blue. The point located <span
class="math notranslate nohighlight">\(+1\)</span> in <span
class="math notranslate nohighlight">\(z\)</span> direction (<span
class="pre"><code class="docutils literal notranslate">zp</code></span>)
is coloured yellow and the point located <span
class="math notranslate nohighlight">\(-1\)</span> in <span
class="math notranslate nohighlight">\(z\)</span> direction (<span
class="pre"><code class="docutils literal notranslate">zm</code></span>)
is coloured green. The point located <span
class="math notranslate nohighlight">\(+1\)</span> in <span
class="math notranslate nohighlight">\(x\)</span> direction (<span
class="pre"><code class="docutils literal notranslate">xp</code></span>)
is coloured purple and the point located <span
class="math notranslate nohighlight">\(-1\)</span> in <span
class="math notranslate nohighlight">\(x\)</span> direction (<span
class="pre"><code class="docutils literal notranslate">xm</code></span>)
is coloured red.</span><a href="#id8" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

We want to solve a problem on the form
<span class="math notranslate nohighlight">\\A{{\mathbf{x}}}={{\mathbf{b}}}\\</span>.
We will order
<span class="math notranslate nohighlight">\\{{\mathbf{x}}}\\</span> in
a row-major order (so that
<span class="math notranslate nohighlight">\\z\\</span> is varying
faster than <span class="math notranslate nohighlight">\\x\\</span>).
Further, we put the inner
<span class="math notranslate nohighlight">\\x\\</span> boundary points
first in
<span class="math notranslate nohighlight">\\{{\mathbf{x}}}\\</span>,
and the outer <span class="math notranslate nohighlight">\\x\\</span>
boundary points last in
<span class="math notranslate nohighlight">\\{{\mathbf{x}}}\\</span>.
The matrix problem for our mesh can then be written like in
<a href="#fig-lapl-inv-matrix" class="reference internal"><span
class="std std-numref">Fig. 13</span></a>.

<figure id="id9" class="align-default">
<span id="fig-lapl-inv-matrix"></span><img
src="../_images/5PointStencilMatrix.png"
alt="The matrix problem for the Laplacian inversion" />
<figcaption><p><span class="caption-number">Fig. 13 </span><span
class="caption-text">Matrix problem for our <span
class="math notranslate nohighlight">\(3\times3\)</span> mesh: The
colors follow that of figure <a href="#fig-lapl-inv-mesh"
class="reference internal"><span class="std std-numref">Fig.
11</span></a> and <a href="#fig-lapl-inv-mesh-w-stencil"
class="reference internal"><span class="std std-numref">Fig.
12</span></a>. The first index of the elements refers to the <span
class="math notranslate nohighlight">\(x\)</span>-position in figure <a
href="#fig-lapl-inv-mesh" class="reference internal"><span
class="std std-numref">Fig. 11</span></a>, and the last index of the
elements refers to the <span
class="math notranslate nohighlight">\(z\)</span>-position in figure <a
href="#fig-lapl-inv-mesh" class="reference internal"><span
class="std std-numref">Fig. 11</span></a>. <span class="pre"><code
class="docutils literal notranslate">ig</code></span> refers to “inner
ghost point”, <span class="pre"><code
class="docutils literal notranslate">og</code></span> refers to “outer
ghost point”, and <span class="pre"><code
class="docutils literal notranslate">c</code></span> refers to the point
of consideration. Notice the “wrap-around” in <span
class="math notranslate nohighlight">\(z\)</span>-direction when the
point of consideration neighbours the first/last <span
class="math notranslate nohighlight">\(z\)</span>-index.</span><a
href="#id9" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

As we are using a row-major implementation, the global indices of the
matrix will be as in
<a href="#fig-lapl-inv-global" class="reference internal"><span
class="std std-numref">Fig. 14</span></a>

<figure id="id10" class="align-default">
<span id="fig-lapl-inv-global"></span><img
src="../_images/5PointStencilGlobalIndices.png"
alt="Global indices of the matrix in figure :numref:`fig-lapl-inv-matrix`" />
<figcaption><p><span class="caption-number">Fig. 14 </span><span
class="caption-text">Global indices of the matrix in figure <a
href="#fig-lapl-inv-matrix" class="reference internal"><span
class="std std-numref">Fig. 13</span></a></span><a href="#id10"
class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

</div>

<div id="implementation-internals" class="section">

## Implementation internals<a href="#implementation-internals" class="headerlink"
title="Permalink to this heading">#</a>

The Laplacian inversion code solves the equation:

<div class="math notranslate nohighlight">

\\d\nabla^2\_\perp x + \frac{1}{c_1}\nabla\_\perp c_2\cdot\nabla\_\perp
x + a x = b\\

</div>

where <span class="math notranslate nohighlight">\\x\\</span> and
<span class="math notranslate nohighlight">\\b\\</span> are 3D
variables, whilst
<span class="math notranslate nohighlight">\\a\\</span>,
<span class="math notranslate nohighlight">\\c_1\\</span>,
<span class="math notranslate nohighlight">\\c_2\\</span> and
<span class="math notranslate nohighlight">\\d\\</span> are 2D variables
for the FFT solvers, or 3D variables otherwise. Several different
algorithms are implemented for Laplacian inversion, and they differ
between serial and parallel versions. Serial inversion can currently
either be done using a tridiagonal solver (Thomas algorithm), or a
band-solver (allowing
<span class="math notranslate nohighlight">\\4^{th}\\</span>-order
differencing).

To support multiple implementations, a base class <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> is defined in
<span class="pre">`include/invert_laplace.hxx`</span>. This defines a
set of functions which all implementations must provide:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class Laplacian {
    public:
      virtual void setCoefA(const Field2D &val) = 0;
      virtual void setCoefC(const Field2D &val) = 0;
      virtual void setCoefD(const Field2D &val) = 0;

      virtual const FieldPerp solve(const FieldPerp &b) = 0;
    }

</div>

</div>

At minimum, all implementations must provide a way to set coefficients,
and a solve function which operates on a single FieldPerp (X-Y) object
at once. Several other functions are also virtual, so default code
exists but can be overridden by an implementation.

For convenience, the <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> base class also
defines a function to calculate coefficients in a Tridiagonal matrix:

<div class="highlight-cpp notranslate">

<div class="highlight">

    void tridagCoefs(int jx, int jy, int jz, dcomplex &a, dcomplex &b,
                     dcomplex &c, const Field2D *c1coef = nullptr,
                     const Field2D *c2coef = nullptr,
                     const Field2D *d=nullptr);

</div>

</div>

For the user of the class, some static functions are defined:

<div class="highlight-cpp notranslate">

<div class="highlight">

    static std::unique_ptr<Laplacian> create(Options *opt = nullptr);
    static Laplacian* defaultInstance();

</div>

</div>

The create function allows new Laplacian implementations to be created,
based on options. To use the options in the
<span class="pre">`[laplace]`</span> section, just use the default:

<div class="highlight-cpp notranslate">

<div class="highlight">

    std::unique_ptr<Laplacian> lap = Laplacian::create();

</div>

</div>

The code for the <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> base class is in
<span class="pre">`src/invert/laplace/invert_laplace.cxx`</span>. The
actual creation of new Laplacian implementations is done in the <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv414LaplaceFactory"
class="reference internal" title="LaplaceFactory"><span
class="pre"><code
class="sourceCode cpp">LaplaceFactory</code></span></a> class, defined
in <span class="pre">`src/invert/laplace/laplacefactory.cxx`</span>.
This file includes all the headers for the implementations, and chooses
which one to create based on the <span class="pre">`type`</span> setting
in the input options. This factory therefore provides a single point of
access to the underlying Laplacian inversion implementations.

Each of the implementations is in a subdirectory of
<span class="pre">`src/invert/laplace/impls`</span> and is discussed
below.

<div id="serial-tridiagonal-solver" class="section">

<span id="sec-tri"></span>

### Serial tridiagonal solver<a href="#serial-tridiagonal-solver" class="headerlink"
title="Permalink to this heading">#</a>

This is the simplest implementation, and is in
<span class="pre">`src/invert/laplace/impls/serial_tri/`</span>

</div>

<div id="serial-band-solver" class="section">

<span id="sec-band"></span>

### Serial band solver<a href="#serial-band-solver" class="headerlink"
title="Permalink to this heading">#</a>

This is band-solver which performs a
<span class="math notranslate nohighlight">\\4^{th}\\</span>-order
inversion. Currently this is only available when
<span class="pre">`NXPE=1`</span>; when more than one processor is used
in <span class="math notranslate nohighlight">\\x\\</span>, the
Laplacian algorithm currently reverts to
<span class="math notranslate nohighlight">\\3^{rd}\\</span>-order.

</div>

<div id="spt-parallel-tridiagonal" class="section">

<span id="sec-spt"></span>

### SPT parallel tridiagonal<a href="#spt-parallel-tridiagonal" class="headerlink"
title="Permalink to this heading">#</a>

This is a reference code which performs the same operations as the
serial code. To invert a single XZ slice
(<a href="../_breathe_autogen/file/fieldperp_8hxx.html#_CPPv49FieldPerp"
class="reference internal" title="FieldPerp"><span class="pre"><code
class="sourceCode cpp">FieldPerp</code></span></a> object), data must
pass from the innermost processor
(<span class="pre">`mesh->PE_XIND`</span>` `<span class="pre">`=`</span>` `<span class="pre">`0`</span>)
to the outermost
<span class="pre">`mesh->PE_XIND`</span>` `<span class="pre">`=`</span>` `<span class="pre">`mesh->NXPE-1`</span>
and back again.

Some parallelism is achieved by running several inversions
simultaneously, so while processor 1 is inverting Y=0, processor 0 is
starting on Y=1. This works ok as long as the number of slices to be
inverted is greater than the number of X processors
(<span class="pre">`MYSUB`</span>` `<span class="pre">`>`</span>` `<span class="pre">`mesh->NXPE`</span>).
If
<span class="pre">`MYSUB`</span>` `<span class="pre">`<`</span>` `<span class="pre">`mesh->NXPE`</span>
then not all processors can be busy at once, and so efficiency will fall
sharply. <a href="#fig-par-laplace" class="reference internal"><span
class="std std-numref">Fig. 15</span></a> shows the useage of 4
processors inverting a set of 3 poloidal slices (i.e. MYSUB=3)

<figure id="id11" class="align-default">
<span id="fig-par-laplace"></span><img src="../_images/par_laplace.png"
alt="Parallel Laplacian inversion" />
<figcaption><p><span class="caption-number">Fig. 15 </span><span
class="caption-text">Parallel Laplacian inversion with MYSUB=3 on 4
processors. Red periods are where a processor is idle - in this case
about 40% of the time</span><a href="#id11" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

<div id="cyclic-algorithm" class="section">

<span id="sec-cyclic"></span>

### Cyclic algorithm<a href="#cyclic-algorithm" class="headerlink"
title="Permalink to this heading">#</a>

This is now the default solver in both serial and parallel. It is an
FFT-based solver using a cyclic reduction algorithm.

</div>

<div id="multigrid-solver" class="section">

<span id="sec-multigrid"></span>

### Multigrid solver<a href="#multigrid-solver" class="headerlink"
title="Permalink to this heading">#</a>

A solver using a geometric multigrid algorithm was introduced by
projects in 2015 and 2016 of CCFE and the EUROfusion HLST.

</div>

<div id="naulin-solver" class="section">

<span id="sec-naulin"></span>

### Naulin solver<a href="#naulin-solver" class="headerlink"
title="Permalink to this heading">#</a>

This scheme was introduced for BOUT++ by Michael Løiten in the
<a href="https://github.com/CELMA-project/CELMA"
class="reference external">CELMA code</a> and the iterative algorithm is
detailed in his thesis <a href="#loiten2017" id="id1"
class="reference internal"><span>[Løiten2017]</span></a>.

The iteration can be under-relaxed (see
<span class="pre">`naulin_laplace.cxx`</span> for more details of the
implementation). A factor
<span class="math notranslate nohighlight">\\0\<
\text{underrelax\\factor}\<=1\\</span> is used, with a value of 1
corresponding to no under-relaxation. If the iteration starts to diverge
(the error increases on any step) the underrelax_factor is reduced by a
factor of 0.9, and the iteration is restarted from the initial guess.
The initial value of underrelax_factor, which underrelax_factor is set
to at the beginning of each call to <span class="pre">`solve`</span> can
be set by the option
<span class="pre">`initial_underrelax_factor`</span> (default is 1.0) in
the appropriate section of the input file
(<span class="pre">`[laplace]`</span> by default). Reducing the value of
<span class="pre">`initial_underrelax_factor`</span> may speed up
convergence in some cases. Some statistics from the solver are written
to the output files to help in choosing this value. With
<span class="pre">`<i>`</span> being the number of the
<span class="pre">`LaplaceNaulin`</span> solver, counting in the order
they are created in the physics model:

- <span class="pre">`naulinsolver<i>_mean_underrelax_counts`</span>
  gives the mean number of times
  <span class="pre">`underrelax_factor`</span> had to be reduced to get
  the iteration to converge. If this is much above 0, it is probably
  worth reducing <span class="pre">`initial_underrelax_factor`</span>.

- <span class="pre">`naulinsolver<i>_mean_its`</span> is the mean number
  of iterations taken to converge. Try to minimise when adjusting
  <span class="pre">`initial_underrelax_factor`</span>.

<div class="citation-list" role="list">

<div id="loiten2017" class="citation" role="doc-biblioentry">

<span class="label"><span class="fn-bracket">\[</span><a href="#id1" role="doc-backlink">Løiten2017</a><span class="fn-bracket">\]</span></span>

Michael Løiten, “Global numerical modeling of magnetized plasma in a
linear device”, 2017, <a href="https://celma-project.github.io/"
class="reference external">https://celma-project.github.io/</a>.

</div>

</div>

</div>

<div id="iterative-parallel-tridiagonal-solver" class="section">

<span id="sec-ipt"></span>

### Iterative Parallel Tridiagonal solver<a href="#iterative-parallel-tridiagonal-solver" class="headerlink"
title="Permalink to this heading">#</a>

This solver uses a hybrid of multigrid and the Thomas algorithm to
invert tridiagonal matrices in parallel. The complexity of the algorithm
is <span class="pre">`O(nx)`</span> work and
<span class="pre">`O(log(NXPE))`</span> communications.

The Laplacian is second-order, so to invert it we need two boundary
conditions, one at each end of the domain. If we only have one
processor, that processor knows both boundary conditions, and we can
invert the Laplacian locally using the Thomas algorithm. When the domain
is subdivided between two or more processors, we can no longer use the
Thomas algorithm, as processors do not know the solution at the
subdomain boundaries.

In this hybrid approach, we reduce the original system of equations to a
smaller system for solution at the boundaries of each processor’s
subdomain. We solve this system in parallel using multigrid. Once the
boundary values are known, each processor can find the solution on its
subdomain using the Thomas algorithm.

**Parameters.**

- <span class="pre">`type`</span>` `<span class="pre">`=`</span>` `<span class="pre">`ipt`</span>
  selects this solver.

- <span class="pre">`rtol`</span> and <span class="pre">`atol`</span>
  are the relative and absolute error tolerances to determine when the
  residual has converged. The goal of setting these is to minimize the
  runtime by minimizing the number of iterations required to meet the
  tolerance. Intuitively we would expect tightening tolerances is bad,
  as doing so requires more iterations. This is true, but also
  *loosening* the tolerances too far can lead to very slowly
  convergence. Generally, as we scan from large to small tolerances, we
  start with very slow calculations, then meet some threshold in
  tolerance where the runtime drops sharply, then see runtime slowly
  increase again as tolerances tighten further. The run time for all
  tolerances below this threshold are similar though, and generally it
  is best to err on the side of tighter tolerances.

- <span class="pre">`maxits`</span> is the maximum number of iterations
  allowed before the job fails.

- <span class="pre">`max_cycle`</span> is the number of pre and post
  smoothing operations applied on each multigrid level. The optimal
  value appears to be
  <span class="pre">`max_cycle`</span>` `<span class="pre">`=`</span>` `<span class="pre">`1`</span>.

- <span class="pre">`max_level`</span> sets the number of multigrid
  levels. The optimal value is usually the largest possible value
  <span class="pre">`max_level`</span>` `<span class="pre">`=`</span>` `<span class="pre">`log2(NXPE)`</span>` `<span class="pre">`-`</span>` `<span class="pre">`2`</span>
  (see “constraints” below), but sometimes one or two levels less than
  this can be faster.

- <span class="pre">`predict_exit`</span>. Multigrid convergence rates
  are very robust. When
  <span class="pre">`predict_exit`</span>` `<span class="pre">`=`</span>` `<span class="pre">`true`</span>,
  we calculate the convergence rate from early iterations and predict
  the iteration at which the algorithm will have converged. This allows
  us to skip convergence checks at most iterations (these checks are
  expensive as they require global communication). Whether this is
  advantageous is problem-dependent: it is probably useful at low
  <span class="pre">`Z`</span> resolution but not at higher
  <span class="pre">`Z`</span> resolution. This is because the algorithm
  skips work associated with <span class="pre">`kz`</span> modes which
  have converged; but if we do not check convergence, we do not know
  which modes we can skip. Therefore at higher
  <span class="pre">`Z`</span> resolution we find that reduced
  communication costs are offset by increased work.
  <span class="pre">`predict_exit`</span> defaults to
  <span class="pre">`false`</span>.

**Constraints.** This method requires that:

- <span class="pre">`NXPE`</span> is a power of 2.

- <span class="pre">`NXPE`</span>` `<span class="pre">`>`</span>` `<span class="pre">`2^(max_levels+1)`</span>

</div>

</div>

<div id="laplacexy" class="section">

<span id="sec-laplacexy"></span>

## LaplaceXY<a href="#laplacexy" class="headerlink"
title="Permalink to this heading">#</a>

Perpendicular Laplacian solver in X-Y.

<div id="equation-nabl-perp-f" class="math notranslate nohighlight">

<span class="eqno">(8)<a href="#equation-nabl-perp-f" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\nabla\_\perp
f =& \nabla f - \mathbf{b}\left(\mathbf{b}\cdot\nabla\right) \nonumber
\\ =& \left(\frac{\partial f}{\partial x} -
\frac{g\_{xy}}{g\_{yy}}\frac{\partial f}{\partial y}\right)\nabla x +
\left(\frac{\partial f}{\partial z} -
\frac{g\_{yz}}{g\_{yy}}\frac{\partial f}{\partial y}\right)\nabla
z\end{split}\\

</div>

In 2D (X-Y), the
<span class="math notranslate nohighlight">\\g\_{xy}\\</span> component
can be dropped since this depends on integrated shear
<span class="math notranslate nohighlight">\\I\\</span> which will
cancel with the
<span class="math notranslate nohighlight">\\g\_{xz}\\</span> component.
The <span class="math notranslate nohighlight">\\z\\</span> derivative
is zero and so this simplifies to

<div class="math notranslate nohighlight">

\\\nabla\_\perp f = \frac{\partial f}{\partial x}\nabla x -
\frac{g\_{yz}}{g\_{yy}}\frac{\partial f}{\partial y}\nabla z\\

</div>

The divergence operator in conservative form is

<div class="math notranslate nohighlight">

\\\nabla\cdot\mathbf{A} = \frac{1}{J}\frac{\partial}{\partial
u^i}\left(Jg^{ij}A_j\right)\\

</div>

and so the perpendicular Laplacian in X-Y is

<div class="math notranslate nohighlight">

\\\nabla\_\perp^2f = \frac{1}{J}\frac{\partial}{\partial
x}\left(Jg^{xx}\frac{\partial f}{\partial x}\right) -
\frac{1}{J}\frac{\partial}{\partial
y}\left(Jg^{yz}\frac{g\_{yz}}{g\_{yy}}\frac{\partial f}{\partial
y}\right)\\

</div>

In field-aligned coordinates, the metrics in the
<span class="math notranslate nohighlight">\\y\\</span> derivative term
become:

<div class="math notranslate nohighlight">

\\g^{yz}\frac{g\_{yz}}{g\_{yy}} =
\frac{B\_{tor}^2}{B^2}\frac{1}{h\_\theta^2}\\

</div>

In the LaplaceXY operator this is implemented in terms of fluxes at cell
faces.

<div class="math notranslate nohighlight">

\\\frac{1}{J}\frac{\partial}{\partial x}\left(Jg^{xx}\frac{\partial
f}{\partial x}\right) \rightarrow
\frac{1}{J_i\mathrm{dx_i}}\left\[J\_{i+1/2}g^{xx}\_{i+1/2}\left(\frac{f\_{i+1} -
f\_{i}}{\mathrm{dx}\_{i+1/2}}\right) -
J\_{i-1/2}g^{xx}\_{i-1/2}\left(\frac{f\_{i} -
f\_{i-1}}{\mathrm{dx}\_{i-1/2}}\right)\right\]\\

</div>

Notes:

- The <span class="pre">`ShiftedMetric`</span> or
  <span class="pre">`FCITransform`</span> ParallelTransform must be used
  (i.e.
  <span class="pre">`mesh:paralleltransform:type`</span>` `<span class="pre">`=`</span>` `<span class="pre">`shifted`</span>
  or
  <span class="pre">`mesh:paralleltransform:type`</span>` `<span class="pre">`=`</span>` `<span class="pre">`fci`</span>)
  for this to work, since it assumes that
  <span class="math notranslate nohighlight">\\g^{xz} = 0\\</span>

- Setting the option
  <span class="pre">`pctype`</span>` `<span class="pre">`=`</span>` `<span class="pre">`hypre`</span>
  seems to work well, if PETSc has been compiled with the algebraic
  multigrid library hypre; this can be included by passing the option
  <span class="pre">`--download-hypre`</span> to PETSc’s
  <span class="pre">`configure`</span> script.

- <span class="pre">`LaplaceXY`</span> (with the default finite-volume
  discretisation) has a slightly different convention for passing
  non-zero boundary values than the <span class="pre">`Laplacian`</span>
  solvers. <span class="pre">`LaplaceXY`</span> uses the average of the
  last grid cell and first boundary cell of the initial guess (second
  argument to <span class="pre">`solve()`</span>) as the value to impose
  for the boundary condition.

An alternative discretization is available if the option
<span class="pre">`finite_volume`</span>` `<span class="pre">`=`</span>` `<span class="pre">`false`</span>
is set. Then a finite-difference discretization very close to the one
used when calling
<span class="pre">`A*Laplace_perp(f)`</span>` `<span class="pre">`+`</span>` `<span class="pre">`Grad_perp(A)*Grad_perp(f)`</span>` `<span class="pre">`+`</span>` `<span class="pre">`B*f`</span>
is used. This also supports non-orthogonal grids with
<span class="math notranslate nohighlight">\\g^{xy} \neq 0\\</span>. The
difference is that when
<span class="math notranslate nohighlight">\\g^{xy} \neq 0\\</span>,
<span class="pre">`Laplace_perp`</span> calls
<span class="pre">`D2DXDY(f)`</span> which applies a boundary condition
to
<span class="pre">`dfdy`</span>` `<span class="pre">`=`</span>` `<span class="pre">`DDY(f)`</span>
before calculating <span class="pre">`DDX(dfdy)`</span> with a slightly
different result than the way boundary conditions are applied in
<span class="pre">`LaplaceXY`</span>.

- The finite difference implementation of
  <span class="pre">`LaplaceXY`</span> passes non-zero values for the
  boundary conditions in the same way as the
  <span class="pre">`Laplacian`</span> solvers. The value in the first
  boundary cell of the initial guess (second argument to
  <span class="pre">`solve()`</span>) is used as the boundary value.
  (Note that this value is imposed as a boundary condition on the
  returned solution at a location half way between the last grid cell
  and first boundary cell.)

</div>

<div id="laplacexz" class="section">

<span id="sec-laplacexz"></span>

## LaplaceXZ<a href="#laplacexz" class="headerlink"
title="Permalink to this heading">#</a>

This is a Laplacian inversion code in X-Z, similar to the <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> solver described in
<a href="#sec-laplacian" class="reference internal"><span
class="std std-ref">Laplacian inversion</span></a>. The difference is in
the form of the Laplacian equation solved, and the approach used to
derive the finite difference formulae. The equation solved is:

<div class="math notranslate nohighlight">

\\\nabla\cdot\left( A \nabla\_\perp f \right) + Bf = b\\

</div>

where <span class="math notranslate nohighlight">\\A\\</span> and
<span class="math notranslate nohighlight">\\B\\</span> are
coefficients, <span class="math notranslate nohighlight">\\b\\</span> is
the known RHS vector (e.g. vorticity), and
<span class="math notranslate nohighlight">\\f\\</span> is the unknown
quantity to be calculated (e.g. potential), and
<span class="math notranslate nohighlight">\\\nabla\_\perp f\\</span> is
the same as equation
(<a href="#equation-nabl-perp-f" class="reference internal">(8)</a>),
but with negligible
<span class="math notranslate nohighlight">\\y\\</span>-parallel
derivatives if
<span class="math notranslate nohighlight">\\g\_{xy}\\</span>,
<span class="math notranslate nohighlight">\\g\_{yz}\\</span> and
<span class="math notranslate nohighlight">\\g\_{xz}\\</span> is
non-vanishing. The Laplacian is written in conservative form like the
<a href="../_breathe_autogen/file/laplacexy_8hxx.html#_CPPv49LaplaceXY"
class="reference internal" title="LaplaceXY"><span class="pre"><code
class="sourceCode cpp">LaplaceXY</code></span></a> solver, and
discretised in terms of fluxes through cell faces.

<div class="math notranslate nohighlight">

\\\frac{1}{J}\frac{\partial}{\partial x}\left(J A g^{xx}\frac{\partial
f}{\partial x}\right) + \frac{1}{J}\frac{\partial}{\partial z}\left(J A
g^{zz}\frac{\partial f}{\partial z}\right) + B f = b\\

</div>

The header file is
<span class="pre">`include/bout/invert/laplacexz.hxx`</span>. The solver
is constructed by using the <a
href="../_breathe_autogen/file/laplacexz_8hxx.html#_CPPv4N9LaplaceXZ6createEP4MeshP7Options8CELL_LOC"
class="reference internal" title="LaplaceXZ::create"><span
class="pre"><code
class="sourceCode cpp">LaplaceXZ<span class="op">::</span>create<span class="op">()</span></code></span></a>
function:

<div class="highlight-cpp notranslate">

<div class="highlight">

    std::unique_ptr<LaplaceXZ> lap = LaplaceXZ::create(mesh);

</div>

</div>

Note that a pointer to a
<a href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv44Mesh"
class="reference internal" title="Mesh"><span class="pre"><code
class="sourceCode cpp">Mesh</code></span></a> object must be given,
which for now is the global variable <span class="pre">`mesh`</span>. By
default the options section <span class="pre">`laplacexz`</span> is
used, so to set the type of solver created, set in the options

<div class="highlight-cfg notranslate">

<div class="highlight">

    [laplacexz]
    type = petsc  # Set LaplaceXZ type

</div>

</div>

or on the command-line <span class="pre">`laplacexz:type=petsc`</span> .

The coefficients must be set using <span class="pre">`setCoefs`</span> .
All coefficients must be set at the same time:

<div class="highlight-cpp notranslate">

<div class="highlight">

    lap->setCoefs(1.0, 0.0);

</div>

</div>

Constants,
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> or
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> values can be passed.
If the implementation doesn’t support
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> values then the average
over <span class="math notranslate nohighlight">\\z\\</span> will be
used as a
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> value.

To perform the inversion, call the <span class="pre">`solve`</span>
function:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D vort = ...;

    Field3D phi = lap->solve(vort, 0.0);

</div>

</div>

The second input to <span class="pre">`solve`</span> is an initial guess
for the solution, which can be used by iterative schemes e.g. using
PETSc.

<div id="implementations" class="section">

### Implementations<a href="#implementations" class="headerlink"
title="Permalink to this heading">#</a>

The currently available implementations are:

- <span class="pre">`cyclic`</span>: This implementation assumes
  coefficients are constant in
  <span class="math notranslate nohighlight">\\Z\\</span>, and uses FFTs
  in <span class="math notranslate nohighlight">\\z\\</span> and a
  complex tridiagonal solver in
  <span class="math notranslate nohighlight">\\x\\</span> for each
  <span class="math notranslate nohighlight">\\z\\</span> mode (the
  <span class="pre">`CyclicReduction`</span> solver). Code in
  <span class="pre">`src/invert/laplacexz/impls/cyclic/`</span>.

- <span class="pre">`petsc`</span>: This uses the PETSc KSP interface to
  solve a matrix with coefficients varying in both
  <span class="math notranslate nohighlight">\\x\\</span> and
  <span class="math notranslate nohighlight">\\z\\</span>. To improve
  efficiency of direct solves, a different matrix is used for
  preconditioning. When the coefficients are updated the preconditioner
  matrix is not usually updated. This means that LU factorisations of
  the preconditioner can be re-used. Since this factorisation is a large
  part of the cost of direct solves, this should greatly reduce the
  run-time.

</div>

<div id="test-case" class="section">

### Test case<a href="#test-case" class="headerlink"
title="Permalink to this heading">#</a>

The code in <span class="pre">`examples/test-laplacexz`</span> is a
simple test case for
<a href="../_breathe_autogen/file/laplacexz_8hxx.html#_CPPv49LaplaceXZ"
class="reference internal" title="LaplaceXZ"><span class="pre"><code
class="sourceCode cpp">LaplaceXZ</code></span></a> . First it creates a
<a href="../_breathe_autogen/file/laplacexz_8hxx.html#_CPPv49LaplaceXZ"
class="reference internal" title="LaplaceXZ"><span class="pre"><code
class="sourceCode cpp">LaplaceXZ</code></span></a> object:

<div class="highlight-cpp notranslate">

<div class="highlight">

    std::unique_ptr<LaplaceXZ> inv = LaplaceXZ::create(mesh);

</div>

</div>

For this test the <span class="pre">`petsc`</span> implementation is the
default:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [laplacexz]
    type = petsc
    ksptype = gmres # Iterative method
    pctype  = lu  # Preconditioner

</div>

</div>

By default the LU preconditioner is used. PETSc’s built-in factorisation
only works in serial, so for parallel solves a different package is
needed. This is set using:

<div class="highlight-cpp notranslate">

<div class="highlight">

    factor_package = superlu_dist

</div>

</div>

This setting can be “petsc” for the built-in (serial) code, or one of
“superlu”, “superlu_dist”, “mumps”, or “cusparse”.

Then we set the coefficients:

<div class="highlight-cpp notranslate">

<div class="highlight">

    inv->setCoefs(Field3D(1.0),Field3D(0.0));

</div>

</div>

Note that the scalars need to be cast to fields (Field2D or Field3D)
otherwise the call is ambiguous. Using the PETSc command-line flag
<span class="pre">`-mat_view`</span>` `<span class="pre">`::ascii_info`</span>
information on the assembled matrix is printed:

<div class="highlight-bash notranslate">

<div class="highlight">

    $ mpirun -np 2 ./test-laplacexz -mat_view ::ascii_info
    ...
    Matrix Object: 2 MPI processes
    type: mpiaij
    rows=1088, cols=1088
    total: nonzeros=5248, allocated nonzeros=5248
    total number of mallocs used during MatSetValues calls =0
      not using I-node (on process 0) routines
    ...

</div>

</div>

which confirms that the matrix element pre-allocation is setting the
correct number of non-zero elements, since no additional memory
allocation was needed.

A field to invert is created using FieldFactory:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D rhs = FieldFactory::get()->create3D("rhs",
                                                Options::getRoot(),
                                                mesh);

</div>

</div>

which is currently set to a simple function in the options:

<div class="highlight-cpp notranslate">

<div class="highlight">

    rhs = sin(x - z)

</div>

</div>

and then the system is solved:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D x = inv->solve(rhs, 0.0);

</div>

</div>

Using the PETSc command-line flags
<span class="pre">`-ksp_monitor`</span> to monitor the iterative solve,
and <span class="pre">`-mat_superlu_dist_statprint`</span> to monitor
SuperLU_dist we get:

<div class="highlight-bash notranslate">

<div class="highlight">

          Nonzeros in L       19984
          Nonzeros in U       19984
          nonzeros in L+U     38880
          nonzeros in LSUB    11900
          NUMfact space (MB) sum(procs):  L\U     0.45    all     0.61
          Total highmark (MB):  All       0.62    Avg     0.31    Max     0.36
          Mat conversion(PETSc->SuperLU_DIST) time (max/min/avg):
                                4.69685e-05 / 4.69685e-05 / 4.69685e-05
          EQUIL time             0.00
          ROWPERM time           0.00
          COLPERM time           0.00
          SYMBFACT time          0.00
          DISTRIBUTE time        0.00
          FACTOR time            0.00
          Factor flops    1.073774e+06    Mflops    222.08
          SOLVE time             0.00
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     28.67
    0 KSP Residual norm 5.169560044060e+02
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     60.50
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     49.86
    1 KSP Residual norm 1.359142853145e-12

</div>

</div>

So after the initial setup and factorisation, the system is solved in
one iteration using the LU direct solve.

As a test of re-using the preconditioner, the coefficients are then
modified:

<div class="highlight-cpp notranslate">

<div class="highlight">

    inv->setCoefs(Field3D(2.0),Field3D(0.1));

</div>

</div>

and solved again:

<div class="highlight-cpp notranslate">

<div class="highlight">

          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     84.15
    0 KSP Residual norm 5.169560044060e+02
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     90.42
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     98.51
    1 KSP Residual norm 2.813291076609e+02
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     94.88
    2 KSP Residual norm 1.688683980433e+02
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     87.27
    3 KSP Residual norm 7.436784980024e+01
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     88.77
    4 KSP Residual norm 1.835640800835e+01
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     89.55
    5 KSP Residual norm 2.431147365563e+00
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     88.00
    6 KSP Residual norm 5.386963293959e-01
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     93.50
    7 KSP Residual norm 2.093714782067e-01
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     91.91
    8 KSP Residual norm 1.306701698197e-02
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     89.44
    9 KSP Residual norm 5.838501185134e-04
          SOLVE time             0.00
          Solve flops     8.245800e+04    Mflops     81.47

</div>

</div>

Note that this time there is no factorisation step, but the direct solve
is still very effective.

</div>

<div id="blob2d-comparison" class="section">

### Blob2d comparison<a href="#blob2d-comparison" class="headerlink"
title="Permalink to this heading">#</a>

The example <span class="pre">`examples/blob2d-laplacexz`</span> is the
same as <span class="pre">`examples/blob2d`</span> but with
<span class="pre">`LaplaceXZ`</span> rather than <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a>.

Tests on one processor: Using Boussinesq approximation, so that the
matrix elements are not changed, the cyclic solver produces output:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        125       8.28e-01    71.8    8.2    0.4    0.6   18.9
    2.000e+02         44       3.00e-01    69.4    8.1    0.4    2.1   20.0

</div>

</div>

whilst the PETSc solver with LU preconditioner outputs:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        146       1.15e+00    61.9   20.5    0.5    0.9   16.2
    2.000e+02         42       3.30e-01    58.2   20.2    0.4    3.7   17.5

</div>

</div>

so the PETSc direct solver seems to take only slightly longer than the
cyclic solver. For comparison, GMRES with Jacobi preconditioning gives:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        130       2.66e+00    24.1   68.3    0.2    0.8    6.6
    2.000e+02         78       1.16e+00    33.8   54.9    0.3    1.1    9.9

</div>

</div>

and with SOR preconditioner:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        124       1.54e+00    38.6   50.2    0.3    0.4   10.5
    2.000e+02         45       4.51e-01    46.8   37.8    0.3    1.7   13.4

</div>

</div>

When the Boussinesq approximation is not used, the PETSc solver with LU
preconditioning, re-setting the preconditioner every 100 solves gives:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        142       3.06e+00    23.0   70.7    0.2    0.2    6.0
    2.000e+02         41       9.47e-01    21.0   72.1    0.3    0.6    6.1

</div>

</div>

i.e. around three times slower than the Boussinesq case. When using
jacobi preconditioner:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        128       2.59e+00    22.9   70.8    0.2    0.2    5.9
    2.000e+02         68       1.18e+00    26.5   64.6    0.2    0.6    8.1

</div>

</div>

For comparison, the <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> solver using the
tridiagonal solver as preconditioner gives:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        222       5.70e+00    17.4   77.9    0.1    0.1    4.5
    2.000e+02        172       3.84e+00    20.2   74.2    0.2    0.2    5.2

</div>

</div>

or with Jacobi preconditioner:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        107       3.13e+00    15.8   79.5    0.1    0.2    4.3
    2.000e+02        110       2.14e+00    23.5   69.2    0.2    0.3    6.7

</div>

</div>

The
<a href="../_breathe_autogen/file/laplacexz_8hxx.html#_CPPv49LaplaceXZ"
class="reference internal" title="LaplaceXZ"><span class="pre"><code
class="sourceCode cpp">LaplaceXZ</code></span></a> solver does not
appear to be dramatically faster **in serial** than the <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> solver when the
matrix coefficients are modified every solve. When matrix elements are
not modified then the solve time is competitive with the tridiagonal
solver.

As a test, timing only the <span class="pre">`setCoefs`</span> call for
the non-Boussinesq case gives:

<div class="highlight-console notranslate">

<div class="highlight">

    1.000e+02        142       1.86e+00    83.3    9.5    0.2    0.3    6.7
    2.000e+02         41       5.04e-01    83.1    8.0    0.3    1.2    7.3

</div>

</div>

so around 9% of the run-time is in setting the coefficients, and the
remaining <span class="math notranslate nohighlight">\\\sim 60\\</span>%
in the solve itself.

</div>

</div>

</div>

<div class="prev-next-area">

<a href="parallel-transforms.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Parallel Transforms

</div>

<a href="differential_operators.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Differential operators

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#usage-of-the-laplacian-inversion"
  class="reference internal nav-link">Usage of the laplacian inversion</a>
- <a href="#numerical-implementation"
  class="reference internal nav-link">Numerical implementation</a>
  - <a href="#using-tridiagonal-solvers"
    class="reference internal nav-link">Using tridiagonal solvers</a>
  - <a href="#using-petsc-solvers" class="reference internal nav-link">Using
    PETSc solvers</a>
  - <a href="#example-the-5-point-stencil"
    class="reference internal nav-link">Example: The 5-point stencil</a>
- <a href="#implementation-internals"
  class="reference internal nav-link">Implementation internals</a>
  - <a href="#serial-tridiagonal-solver"
    class="reference internal nav-link">Serial tridiagonal solver</a>
  - <a href="#serial-band-solver" class="reference internal nav-link">Serial
    band solver</a>
  - <a href="#spt-parallel-tridiagonal"
    class="reference internal nav-link">SPT parallel tridiagonal</a>
  - <a href="#cyclic-algorithm" class="reference internal nav-link">Cyclic
    algorithm</a>
  - <a href="#multigrid-solver"
    class="reference internal nav-link">Multigrid solver</a>
  - <a href="#naulin-solver" class="reference internal nav-link">Naulin
    solver</a>
  - <a href="#iterative-parallel-tridiagonal-solver"
    class="reference internal nav-link">Iterative Parallel Tridiagonal
    solver</a>
- <a href="#laplacexy" class="reference internal nav-link">LaplaceXY</a>
- <a href="#laplacexz" class="reference internal nav-link">LaplaceXZ</a>
  - <a href="#implementations"
    class="reference internal nav-link">Implementations</a>
  - <a href="#test-case" class="reference internal nav-link">Test case</a>
  - <a href="#blob2d-comparison" class="reference internal nav-link">Blob2d
    comparison</a>

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
