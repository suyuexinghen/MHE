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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/differential_operators.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/differential_operators.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/differential_operators.rst"
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

# Differential operators

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#differencing-methods"
  class="reference internal nav-link">Differencing methods</a>
- <a href="#user-registered-methods"
  class="reference internal nav-link">User registered methods</a>
- <a href="#mixed-second-derivative-operators"
  class="reference internal nav-link">Mixed second-derivative
  operators</a>
- <a href="#non-uniform-meshes"
  class="reference internal nav-link">Non-uniform meshes</a>
- <a href="#general-operators" class="reference internal nav-link">General
  operators</a>
- <a href="#clebsch-operators" class="reference internal nav-link">Clebsch
  operators</a>
- <a href="#the-bracket-operators" class="reference internal nav-link">The
  bracket operators</a>
- <a href="#finite-volume-conservative-finite-difference-methods"
  class="reference internal nav-link">Finite volume, conservative finite
  difference methods</a>
  - <a href="#parallel-divergence-div-par"
    class="reference internal nav-link">Parallel divergence <span
    class="pre"><code
    class="docutils literal notranslate">Div_par</code></span></a>
    - <a href="#example-and-convergence-test"
      class="reference internal nav-link">Example and convergence test</a>
  - <a href="#parallel-diffusion"
    class="reference internal nav-link">Parallel diffusion</a>
  - <a href="#advection-in-3d" class="reference internal nav-link">Advection
    in 3D</a>
  - <a href="#slope-limiters" class="reference internal nav-link">Slope
    limiters</a>
  - <a href="#staggered-grids" class="reference internal nav-link">Staggered
    grids</a>
- <a href="#derivatives-of-the-fourier-transform"
  class="reference internal nav-link">Derivatives of the Fourier
  transform</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="differential-operators" class="section">

<span id="sec-diffops"></span>

# Differential operators<a href="#differential-operators" class="headerlink"
title="Permalink to this heading">#</a>

There are a huge number of possible ways to perform differencing in
computational fluid dynamics, and BOUT++ is intended to be able to
implement a large number of them. This means that the way differentials
are handled internally is quite involved; see the developer’s manual for
full gory details. Much of the time this detail is not all that
important, and certainly not while learning to use BOUT++. Default
options are therefore set which work most of the time, so you can start
using the code without getting bogged down in these details.

In order to handle many different differencing methods and operations,
many layers are used, each of which handles just part of the problem.
The main division is between differencing methods (such as 4th-order
central differencing), and differential operators (such as
<span class="math notranslate nohighlight">\\\nabla\_{||}\\</span>).

<div id="differencing-methods" class="section">

<span id="sec-diffmethod"></span>

## Differencing methods<a href="#differencing-methods" class="headerlink"
title="Permalink to this heading">#</a>

Methods are typically implemented on *5-point* stencils (although
exceptions are possible) and are divided into three categories:

- Central-differencing methods, for diffusion operators
  <span class="math notranslate nohighlight">\\\frac{df}{dx}\\</span>,
  <span class="math notranslate nohighlight">\\\frac{d^2f}{dx^2}\\</span>.
  Each method has a short code, and currently include

  - <span class="pre">`C2`</span>:
    2<span class="math notranslate nohighlight">\\^{nd}\\</span> order
    <span class="math notranslate nohighlight">\\f\_{-1} - 2f_0 +
    f_1\\</span>

  - <span class="pre">`C4`</span>:
    4<span class="math notranslate nohighlight">\\^{th}\\</span> order
    <span class="math notranslate nohighlight">\\(-f\_{-2} + 16f\_{-1} -
    30f_0 + 16f_1 - f_2)/12\\</span>

  - <span class="pre">`S2`</span>:
    2<span class="math notranslate nohighlight">\\^{nd}\\</span> order
    smoothing derivative

  - <span class="pre">`W2`</span>:
    2<span class="math notranslate nohighlight">\\^{nd}\\</span> order
    CWENO

  - <span class="pre">`W3`</span>:
    3<span class="math notranslate nohighlight">\\^{rd}\\</span> order
    CWENO

- Upwinding methods for advection operators
  <span class="math notranslate nohighlight">\\v_x\frac{df}{dx}\\</span>

  - <span class="pre">`U1`</span>:
    1<span class="math notranslate nohighlight">\\^{st}\\</span> order
    upwinding

  - <span class="pre">`U2`</span>:
    2<span class="math notranslate nohighlight">\\^{nd}\\</span> order
    upwinding

  - <span class="pre">`U3`</span>:
    3<span class="math notranslate nohighlight">\\^{rd}\\</span> order
    upwinding

  - <span class="pre">`U4`</span>:
    4<span class="math notranslate nohighlight">\\^{th}\\</span> order
    upwinding

  - <span class="pre">`C2`</span>:
    2<span class="math notranslate nohighlight">\\^{nd}\\</span> order
    central

  - <span class="pre">`C4`</span>:
    4<span class="math notranslate nohighlight">\\^{th}\\</span> order
    central

  - <span class="pre">`W3`</span>:
    3<span class="math notranslate nohighlight">\\^{rd}\\</span> order
    <a href="https://doi.org/10.1137/S106482759732455X"
    class="reference external">Weighted Essentially Non-Oscillatory
    (WENO)</a>

- Flux conserving and limiting methods for terms of the form
  <span class="math notranslate nohighlight">\\\frac{d}{dx}(v_x
  f)\\</span>

  - <span class="pre">`U1`</span>:
    1<span class="math notranslate nohighlight">\\^{st}\\</span> order
    upwinding

  - <span class="pre">`C2`</span>:
    2<span class="math notranslate nohighlight">\\^{nd}\\</span> order
    central

  - <span class="pre">`C4`</span>:
    4<span class="math notranslate nohighlight">\\^{th}\\</span> order
    central

Special methods :

- <span class="pre">`FFT`</span>: Classed as a central method, Fourier Transform method in Z  
  (axisymmetric) direction only. Currently available for
  <span class="pre">`first`</span> and <span class="pre">`second`</span>
  order central difference

- <span class="pre">`SPLIT`</span>: A flux method that splits into upwind and central terms  
  <span class="math notranslate nohighlight">\\\frac{d}{dx}(v_x f) =
  v_x\frac{df}{dx} + f\frac{dv_x}{dx}\\</span>

WENO methods avoid overshoots (Gibbs phenomena) at sharp gradients such
as shocks, but the simple 1st-order method has very large artificial
diffusion. WENO schemes are a development of the ENO reconstruction
schemes which combine good handling of sharp-gradient regions with high
accuracy in smooth regions.

The stencil based methods are based by a kernel that combines the data
in a stencil to produce a single BoutReal (note upwind/flux methods take
extra information about the flow, either a
<span class="pre">`BoutReal`</span> or another
<span class="pre">`stencil`</span>). It is not anticipated that the user
would wish to apply one of these kernels directly so documentation is
not provided here for how to do so. If this is of interest please look
at <span class="pre">`include/bout/index_derivs.hxx`</span>. Internally,
these kernel routines are combined within a functor struct that uses a
<span class="pre">`BOUT_FOR`</span> loop over the domain to provide a
routine that will apply the kernel to every point, calculating the
derivative everywhere. These routines are registered in the appropriate
<span class="pre">`DerivativeStore`</span> and identified by the
direction of differential, the staggering, the type
(central/upwind/flux) and a key such as “C2”. The typical user does not
need to interact with this store, instead one can add the following to
the top of your physics module:

<div class="highlight-cpp notranslate">

<div class="highlight">

    #include <derivs.hxx>

</div>

</div>

to provide access to the following routines. These take care of
selecting the appropriate method from the store and ensuring the
input/output field locations are compatible.

<span id="tab-coordinate-derivatives"></span>

<table id="id5" class="table">
<caption><span class="caption-number">Table 17 </span><span
class="caption-text">Coordinate derivatives</span><a href="#id5"
class="headerlink" title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Function</p></th>
<th class="head"><p>Formula</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>DDX(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial f /
\partial x\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>DDY(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial f /
\partial y\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>DDZ(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial f /
\partial z\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>D2DX2(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^2 f /
\partial x^2\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>D2DY2(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^2 f /
\partial y^2\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>D2DZ2(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^2 f /
\partial z^2\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>D4DX4(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^4 f /
\partial x^4\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>D4DY4(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^4 f /
\partial y^4\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>D4DZ4(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^4 f /
\partial z^4\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>D2DXDZ(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^2 f /
\partial x\partial z\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>D2DYDZ(f)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^2 f /
\partial y\partial z\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>VDDX(f, g)</p></td>
<td><p><span class="math notranslate nohighlight">\(f \partial g /
\partial x\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>VDDY(f, g)</p></td>
<td><p><span class="math notranslate nohighlight">\(f \partial g /
\partial y\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>VDDZ(f, g)</p></td>
<td><p><span class="math notranslate nohighlight">\(f \partial g /
\partial z\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>FDDX(f, g)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial/\partial x(
f * g )\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>FDDY(f, g)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial/\partial x(
f * g )\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>FDDZ(f, g)</p></td>
<td><p><span class="math notranslate nohighlight">\(\partial/\partial x(
f * g )\)</span></p></td>
</tr>
</tbody>
</table>

By default the method used will be the one specified in the options
input file (see <a href="bout_options.html#sec-diffmethodoptions"
class="reference internal"><span class="std std-ref">Differencing
methods</span></a>), but most of these methods can take an optional
<span class="pre">`std::string`</span> argument (or a <a
href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv411DIFF_METHOD"
class="reference internal" title="DIFF_METHOD"><span class="pre"><code
class="sourceCode cpp">DIFF_METHOD</code></span></a> argument - to be
deprecated), specifying exactly which method to use.

</div>

<div id="user-registered-methods" class="section">

<span id="sec-diffmethod-userregistration"></span>

## User registered methods<a href="#user-registered-methods" class="headerlink"
title="Permalink to this heading">#</a>

<div class="admonition note">

Note

The following may be considered advanced usage.

</div>

It is possible for the user to define their own differencing routines,
either by supplying a stencil using kernel or writing their own functor
that calculates the differential everywhere. It is then possible to
register these methods with the derivative store (for any direction,
staggering etc.). For examples please look at
<span class="pre">`include/bout/index_derivs.hxx`</span> to see how
these approaches work.

Here is a verbose example showing how the <span class="pre">`C2`</span>
method is implemented.

<div class="highlight-cpp notranslate">

<div class="highlight">

    DEFINE_STANDARD_DERIV(DDX_C2, "C2", 1, DERIV::Stanard) {
        return 0.5*(f.p - f.m);
    };

</div>

</div>

Here <span class="pre">`DEFINE_STANARD_DERIV`</span> is a macro that
acts on the kernel
<span class="pre">`return`</span>` `<span class="pre">`0.5*(f.p`</span>` `<span class="pre">`-`</span>` `<span class="pre">`f.m);`</span>
and produces the functor that will apply the differencing method over an
entire field. The macro takes several arguments;

- the first (<span class="pre">`DDX_C2`</span>) is the name of the
  generated functor – this needs to be unique and allows advanced users
  to refer to a specific derivative functor without having to go through
  the derivative store if desired.

- the second (<span class="pre">`"C2"`</span>) is the string key that is
  used to refer to this specific method when registering/retrieving the
  method from the derivative store.

- the third (<span class="pre">`1`</span>) is the number of guard cells
  required to be able to use this method (i.e. here the stencil will
  consist of three values – the field at the current point and one point
  either side). This can be 1 or 2.

- the fourth (<a
  href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv4N5DERIV8StandardE"
  class="reference internal" title="DERIV::Standard"><span
  class="pre"><code
  class="sourceCode cpp">DERIV<span class="op">::</span>Standard</code></span></a>)
  identifies the type of method - here a central method.

Alongside <span class="pre">`DEFINE_STANDARD_DERIV`</span> there’s also
<span class="pre">`DEFINE_UPWIND_DERIV`</span>,
<span class="pre">`DEFINE_FLUX_DERIV`</span> and the staggered versions
<span class="pre">`DEFINE_STANDARD_DERIV_STAGGERED`</span>,
<span class="pre">`DEFINE_UPWIND_DERIV_STAGGERED`</span> and
<span class="pre">`DEFINE_FLUX_DERIV_STAGGERED`</span>.

To register this method with the derivative store in
<span class="pre">`X`</span> and <span class="pre">`Z`</span> with no
staggering for both field types we can then use the following code:

<div class="highlight-cpp notranslate">

<div class="highlight">

    produceCombinations<Set<WRAP_ENUM(DIRECTION, X), WRAP_ENUM(DIRECTION, Z)>,
                     Set<WRAP_ENUM(STAGGER, None)>,
                     Set<TypeContainer<Field2D, Field3D>>,
                     Set<DDX_C2>>
     someUniqueNameForDerivativeRegistration(registerMethod{});

</div>

</div>

For the common case where the user wishes to register the method in
<span class="pre">`X`</span>, <span class="pre">`Y`</span> and
<span class="pre">`Z`</span> and for both field types we provide the
helper macros, <span class="pre">`REGISTER_DERIVATIVE`</span> and
<span class="pre">`REGISTER_STAGGERED_DERIVATIVE`</span> which could be
used as <span class="pre">`REGISTER_DERIVATIVE(DDX_C2)`</span>.

To simplify matters further we provide
<span class="pre">`REGISTER_STANDARD_DERIVATIVE`</span>,
<span class="pre">`REGISTER_UPWIND_DERIVATIVE`</span>,
<span class="pre">`REGISTER_FLUX_DERIVATIVE`</span>,
<span class="pre">`REGISTER_STANDARD_STAGGERED_DERIVATIVE`</span>,
<span class="pre">`REGISTER_UPWIND_STAGGERED_DERIVATIVE`</span> and
<span class="pre">`REGISTER_FLUX_STAGGERED_DERIVATIVE`</span> macros
that can define and register a stencil using kernel in a single step.
For example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    REGISTER_STANDARD_DERIVATIVE(DDX_C2, "C2", 1, DERIV::Standard) { return 0.5*(f.p-f.m);};

</div>

</div>

Will define the <span class="pre">`DDX_C2`</span> functor and register
it with the derivative store using key <span class="pre">`"C2"`</span>
for all three directions and both fields with no staggering.

</div>

<div id="mixed-second-derivative-operators" class="section">

<span id="sec-diffmethod-mixedsecond"></span>

## Mixed second-derivative operators<a href="#mixed-second-derivative-operators" class="headerlink"
title="Permalink to this heading">#</a>

Coordinate derivatives commute, as long as the coordinates are globally
well-defined, i.e.

<div class="math notranslate nohighlight">

\\\begin{split}\frac{\partial}{\partial x}
\left(\frac{\partial}{\partial y} f \right) = \frac{\partial}{\partial
y} \left(\frac{\partial}{\partial x} f \right) \\
\frac{\partial}{\partial y} \left(\frac{\partial}{\partial z} f \right)
= \frac{\partial}{\partial z} \left(\frac{\partial}{\partial y} f
\right) \\ \frac{\partial}{\partial z} \left(\frac{\partial}{\partial x}
f \right) = \frac{\partial}{\partial x} \left(\frac{\partial}{\partial
z} f \right)\end{split}\\

</div>

When using
<span class="pre">`paralleltransform`</span>` `<span class="pre">`=`</span>` `<span class="pre">`shifted`</span>
or
<span class="pre">`paralleltransform`</span>` `<span class="pre">`=`</span>` `<span class="pre">`fci`</span>
(see <a href="parallel-transforms.html#sec-parallel-transforms"
class="reference internal"><span class="std std-ref">Parallel
Transforms</span></a>) we do not have globally well-defined coordinates.
In those cases the coordinate systems are field-aligned, but the grid
points are at constant toroidal angle. The field-aligned coordinates are
defined locally, on planes of constant
<span class="math notranslate nohighlight">\\y\\</span>. There are
different coordinate systems for each plane. However, within each local
coordinate system the derivatives do commute.
<span class="math notranslate nohighlight">\\y\\</span>-derivatives are
taken in the local field-aligned coordinate system, so mixed derivatives
are calculated as

<div class="highlight-cpp notranslate">

<div class="highlight">

    D2DXDY(f) = DDX(DDY(f))
    D2DYDZ(f) = DDZ(DDY(f))

</div>

</div>

This order is simpler – the alternative is possible. Using second-order
central difference operators for the y-derivatives we could calculate
(not worring about communications or boundary conditions here)

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D D2DXDY(Field3D f) {
      auto result{emptyFrom(f)};
      auto& coords = *f.getCoordinates()

      auto dfdx_yup = DDX(f.yup());
      auto dfdx_ydown = DDX(f.ydown());

      BOUT_FOR(i, f.getRegion()) {
        result[i] = (dfdx_yup[i.yp()] - dfdx_ydown[i.ym()]) / (2. * coords.dy[i])
      }

      return result;
    }

</div>

</div>

This would give equivalent results to the previous form [1] as
<span class="pre">`yup`</span> and <span class="pre">`ydown`</span> give
the values of <span class="pre">`f`</span> one grid point along the
magnetic field *in the local field-aligned coordinate system*.

The <span class="math notranslate nohighlight">\\x\mathrm{-}z\\</span>
derivative is unaffected as it is taken entirely on a plane of constant
<span class="math notranslate nohighlight">\\y\\</span> anyway. It is
evaluated as

<div class="highlight-cpp notranslate">

<div class="highlight">

    D2DXDZ(f) = DDZ(DDX(f))

</div>

</div>

As the <span class="pre">`z`</span>-direction is periodic and the
<span class="pre">`z`</span>-grid is not split across processors,
<span class="pre">`DDZ`</span> does not require any guard cells. By
taking <span class="pre">`DDZ`</span> second, we do not have to
communicate or set boundary conditions on the result of
<span class="pre">`DDX`</span> or <span class="pre">`DDY`</span> before
taking <span class="pre">`DDZ`</span>.

The derivatives in <span class="pre">`D2DXDY(f)`</span> are applied in
two steps. First
<span class="pre">`dfdy`</span>` `<span class="pre">`=`</span>` `<span class="pre">`DDY(f)`</span>
is calculated; <span class="pre">`dfdy`</span> is communicated and has a
boundary condition applied so that all the x-guard cells are filled. The
boundary condition is <span class="pre">`free_o3`</span> by default (3rd
order extrapolation into the boundary cells), but can be specified with
the fifth argument to <span class="pre">`D2DXDY`</span> (see
<a href="boundary_options.html#sec-bndryopts"
class="reference internal"><span class="std std-ref">Boundary
conditions</span></a> for possible options). Second
<span class="pre">`DDX(dfdy)`</span> is calculated, and returned from
the function.

<span class="label"><span class="fn-bracket">\[</span><a href="#id1" role="doc-backlink">1</a><span class="fn-bracket">\]</span></span>

Equivalent but not exactly the same numerically. Expanding out the
derivatives in second-order central-difference form shows that the two
differ in the grid points at which they evaluate
<span class="pre">`dx`</span> and <span class="pre">`dy`</span>. As long
as the grid spacings are smooth this should not affect the order of
accuracy of the scheme (?).

</div>

<div id="non-uniform-meshes" class="section">

<span id="sec-diffmethod-nonuniform"></span>

## Non-uniform meshes<a href="#non-uniform-meshes" class="headerlink"
title="Permalink to this heading">#</a>

**examples/test-nonuniform seems to not work?** Setting
<span class="pre">`non_uniform`</span>` `<span class="pre">`=`</span>` `<span class="pre">`true`</span>
in the BOUT.inp options file enables corrections to second derivatives
in <span class="math notranslate nohighlight">\\X\\</span> and
<span class="math notranslate nohighlight">\\Y\\</span>. This correction
is given by writing derivatives as:

<div class="math notranslate nohighlight">

\\{{\frac{\partial f}{\partial x}}} \simeq \frac{1}{\Delta x}
{{\frac{\partial f}{\partial i}}}\\

</div>

where <span class="math notranslate nohighlight">\\i\\</span> is the
cell index number. The second derivative is therefore given by

<div class="math notranslate nohighlight">

\\\frac{\partial^2 f}{\partial x^2} \simeq \frac{1}{\Delta
x^2}\frac{\partial^2 f}{\partial i^2} + \frac{1}{\Delta
x}{{\frac{\partial f}{\partial x}}} \cdot {{\frac{\partial }{\partial
i}}}(\frac{1}{\Delta x})\\

</div>

The correction factor
<span class="math notranslate nohighlight">\\\partial/\partial
i(1/\Delta x)\\</span> can be calculated automatically, but you can also
specify <span class="pre">`d2x`</span> in the grid file which is

<div class="math notranslate nohighlight">

\\\texttt{d2x} = {{\frac{\partial \Delta x}{\partial i}}} =
\frac{\partial^2 x}{\partial i^2}\\

</div>

The correction factor is then calculated from
<span class="pre">`d2x`</span> using

<div class="math notranslate nohighlight">

\\{{\frac{\partial }{\partial i}}}(\frac{1}{\Delta x}) =
-\frac{1}{\Delta x^2} {{\frac{\partial \Delta x}{\partial i}}}\\

</div>

**Note**: There is a separate switch in the
<a href="laplacian.html#sec-laplacian" class="reference internal"><span
class="std std-ref">Laplacian inversion code</span></a>, which enables
or disables non-uniform mesh corrections.

</div>

<div id="general-operators" class="section">

## General operators<a href="#general-operators" class="headerlink"
title="Permalink to this heading">#</a>

These are differential operators which are for a general coordinate
system.

<div class="math notranslate nohighlight">

\\\begin{split}\begin{array}{rclrcl} \mathbf{v} =& \nabla f &\qquad
{\texttt{Vector}} =& {\texttt{Grad(Field)}} \\ f =&
\nabla\cdot\mathbf{a} &\qquad {\texttt{Field}} =& {\texttt{Div(Vector)}}
\\ \mathbf{v} =& \nabla\times\mathbf{a} &\qquad {\texttt{Vector}} =&
{\texttt{Curl(Vector)}} \\ f =& \mathbf{v}\cdot\nabla g &\qquad
{\texttt{Field}} =& {\texttt{V\\dot\\Grad(Vector, Field)}} \\ \mathbf{v}
=& \mathbf{a}\cdot\nabla\mathbf{c} &\qquad {\texttt{Vector}} =&
{\texttt{V\\dot\\Grad(Vector, Vector)}} \\ f =& \nabla^2 f &\qquad
{\texttt{Field}} =& {\texttt{Laplace(Field)}} \end{array}\end{split}\\

</div>

<div class="math notranslate nohighlight">

\\\begin{split}\nabla\phi =& {{\frac{\partial \phi}{\partial
u^i}}}\nabla u^i \rightarrow (\nabla\phi)\_i = {{\frac{\partial
\phi}{\partial u^i}}} \\ \nabla\cdot A =& = \frac{1}{J}{{\frac{\partial
}{\partial u^i}}}(Jg^{ij}A_j) \\ \nabla^2\phi =& G^j{{\frac{\partial
\phi}{\partial u^i}}} + g^{ij}\frac{\partial^2\phi}{\partial u^i\partial
u^j}\end{split}\\

</div>

where we have defined

<div class="math notranslate nohighlight">

\\G^j = \frac{1}{J}{{\frac{\partial }{\partial u^i}}}(Jg^{ij})\\

</div>

**not** to be confused with the Christoffel symbol of the second kind
(see the coordinates manual for more details).

</div>

<div id="clebsch-operators" class="section">

## Clebsch operators<a href="#clebsch-operators" class="headerlink"
title="Permalink to this heading">#</a>

Another set of operators assume that the equilibrium magnetic field is
written in Clebsch form as

<div class="math notranslate nohighlight">

\\\mathbf{B}\_0 = \nabla z\times\nabla x \qquad B_0 =
\frac{\sqrt{g\_{yy}}}{J}\\

</div>

where

<div class="math notranslate nohighlight">

\\\mathbf{B}\_0 = |\mathbf{B}\_0|\mathbf{b}\_0 = B_0 \mathbf{b}\_0\\

</div>

is the background *equilibrium* magnetic field.

<table class="table">
<tbody>
<tr class="row-odd">
<td><p>Function</p></td>
<td><p>Formula</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">Grad_par</code></span></p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^0_{||} =
\mathbf{b}_0\cdot\nabla = \frac{1}{\sqrt{g_{yy}}}{{\frac{\partial
}{\partial y}}}\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">Div_par</code></span></p></td>
<td><p><span class="math notranslate nohighlight">\(\nabla^0_{||}f =
B_0\partial^0_{||}(\frac{f}{B_0})\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">Grad2_par2</code></span></p></td>
<td><p><span class="math notranslate nohighlight">\(\partial^2_{||}\phi
= \partial^0_{||}(\partial^0_{||}\phi) =
\frac{1}{\sqrt{g_{yy}}}{{\frac{\partial}{\partial
y}}}(\frac{1}{\sqrt{g_{yy}}}){{\frac{\partial \phi}{\partial y}}} +
\frac{1}{g_{yy}}\frac{\partial^2\phi}{\partial y^2}\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">Laplace_par</code></span></p></td>
<td><p><span class="math notranslate nohighlight">\(\nabla_{||}^2\phi =
\nabla\cdot\mathbf{b}_0\mathbf{b}_0\cdot\nabla\phi =
\frac{1}{J}{{\frac{\partial}{\partial
y}}}(\frac{J}{g_{yy}}{{\frac{\partial \phi}{\partial
y}}})\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">Laplace_perp</code></span></p></td>
<td><p><span class="math notranslate nohighlight">\(\nabla_\perp^2 =
\nabla^2 - \nabla_{||}^2\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">Delp2</code></span></p></td>
<td><p>Perpendicular Laplacian, neglecting all <span
class="math notranslate nohighlight">\(y\)</span> derivatives. The <a
href="../_breathe_autogen/file/invert__laplace_8hxx.html#_CPPv49Laplacian"
class="reference internal" title="Laplacian"><span class="pre"><code
class="sourceCode cpp">Laplacian</code></span></a> solver performs the
inverse operation</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">bracket</code></span></p></td>
<td><p>Poisson brackets. The Arakawa option, neglects the parallel <span
class="math notranslate nohighlight">\(y\)</span> derivatives if <span
class="math notranslate nohighlight">\(g_{xy}\)</span> and <span
class="math notranslate nohighlight">\(g_{yz}\)</span> are
non-zero</p></td>
</tr>
</tbody>
</table>

We have that

<div class="math notranslate nohighlight">

\\\mathbf{b}\_0\cdot\nabla\phi\times\nabla A =
\frac{1}{J\sqrt{g\_{yy}}}\[(g\_{yy}{{\frac{\partial \phi}{\partial
z}}} - g\_{yz}{{\frac{\partial \phi}{\partial y}}}){{\frac{\partial
A}{\partial x}}} + (g\_{yz}{{\frac{\partial \phi}{\partial x}}} -
g\_{xy}{{\frac{\partial \phi}{\partial z}}}){{\frac{\partial A}{\partial
y}}} + (g\_{xy}{{\frac{\partial \phi}{\partial y}}} -
g\_{yy}{{\frac{\partial \phi}{\partial x}}}){{\frac{\partial A}{\partial
z}}}\]\\

</div>

<div class="math notranslate nohighlight">

\\\nabla\_\perp \equiv \nabla -
{{\mathbf{b}}}({{\mathbf{b}}}\cdot\nabla)\\

</div>

<div class="math notranslate nohighlight">

\\{{\mathbf{b}}}\cdot\nabla = \frac{1}{JB}\frac{\partial}{\partial y}\\

</div>

<div class="math notranslate nohighlight">

\\{{\boldsymbol{b}}} = \frac{1}{JB}{{\boldsymbol{e}}}\_y =
\frac{1}{JB}\[g\_{xy}\nabla x + g\_{yy}\nabla y + g\_{yz}\nabla z\]\\

</div>

In a Clebsch coordinate system
<span class="math notranslate nohighlight">\\{{\boldsymbol{B}}} = \nabla
z \times \nabla x = \frac{1}{J}{{\boldsymbol{e}}}\_y\\</span>,
<span class="math notranslate nohighlight">\\g\_{yy} =
{{\boldsymbol{e}}}\_y\cdot{{\boldsymbol{e}}}\_y = J^2B^2\\</span>, and
so the <span class="math notranslate nohighlight">\\\nabla y\\</span>
term cancels out:

<div class="math notranslate nohighlight">

\\\nabla\_\perp = \nabla x({{\frac{\partial }{\partial x}}} -
\frac{g\_{xy}}{(JB)^2}{{\frac{\partial }{\partial y}}}) + \nabla
z({{\frac{\partial }{\partial z}}} -
\frac{g\_{yz}}{(JB)^2}{{\frac{\partial }{\partial y}}})\\

</div>

</div>

<div id="the-bracket-operators" class="section">

## The bracket operators<a href="#the-bracket-operators" class="headerlink"
title="Permalink to this heading">#</a>

The bracket operator
<span class="pre">`bracket(phi,`</span>` `<span class="pre">`f,`</span>` `<span class="pre">`method)`</span>
aims to differentiate equations on the form

<div class="math notranslate nohighlight">

\\-\frac{\nabla\phi\times{{\boldsymbol{b}}}}{B}\cdot\nabla f\\

</div>

Notice that when we use the Arakawa scheme,
<span class="math notranslate nohighlight">\\y\\</span>-derivatives are
neglected if
<span class="math notranslate nohighlight">\\g\_{xy}\\</span> and
<span class="math notranslate nohighlight">\\g\_{yz}\\</span> are
non-zero. An example of usage of the brackets can be found in for
example <span class="pre">`examples/MMS/advection`</span> or
<span class="pre">`examples/blob2d`</span>.

</div>

<div id="finite-volume-conservative-finite-difference-methods"
class="section">

## Finite volume, conservative finite difference methods<a href="#finite-volume-conservative-finite-difference-methods"
class="headerlink" title="Permalink to this heading">#</a>

These schemes aim to conserve the integral of the advected quantity over
the domain. If <span class="math notranslate nohighlight">\\f\\</span>
is being advected, then

<div class="math notranslate nohighlight">

\\\sum_i \left(f J dx dy dz\right)\_i = const\\

</div>

is conserved, where the index
<span class="math notranslate nohighlight">\\i\\</span> refers to cell
index. This is done by calculating fluxes between cells: Whatever leaves
one cell is added to another. There are several caveats to this:

- Boundary fluxes can still lead to changes in the total, unless no-flow
  boundary conditions are used

- When using an implicit time integration scheme, such as the default
  PVODE / CVODE, the total is not guaranteed to be conserved, but may
  vary depending on the solver tolerances.

- There will always be a small rounding error, even with double
  precision.

The methods can be used by including the
<a href="../_breathe_autogen/file/fv__ops_8cxx.html"
class="reference internal"><span class="doc">header</span></a>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    #include "bout/fv_ops.hxx"

</div>

</div>

**Note** The methods are defined in a namespace
<span class="pre">`FV`</span>.

Some methods (those with templates) are defined in the header, but
others are defined in
<a href="../_breathe_autogen/file/fv__ops_8cxx.html"
class="reference internal"><span
class="doc">src/mesh/fv_ops.cxx</span></a>.

<div id="parallel-divergence-div-par" class="section">

### Parallel divergence <span class="pre">`Div_par`</span><a href="#parallel-divergence-div-par" class="headerlink"
title="Permalink to this heading">#</a>

This function calculates the divergence of a flow in
<span class="math notranslate nohighlight">\\y\\</span> (parallel to the
magnetic field) by a given velocity.

<div class="highlight-cpp notranslate">

<div class="highlight">

    template<typename CellEdges = MC>
    const Field3D Div_par(const Field3D &f_in, const Field3D &v_in,
                          const Field3D &a, bool fixflux=true);

</div>

</div>

where <span class="pre">`f_in`</span> is the quantity being advected
(e.g. density), <span class="pre">`v_in`</span> is the parallel
advection velocity. The third input, <span class="pre">`a`</span>, is
the maximum wave speed, which multiplies the dissipation term in the
method.

<div class="highlight-cpp notranslate">

<div class="highlight">

    ddt(n) = -FV::Div_par( n, v, cs );

</div>

</div>

By default the <span class="pre">`MC`</span> slope limiter is used to
calculate cell edges, but this can be changed at compile time e.g:

<div class="highlight-cpp notranslate">

<div class="highlight">

    ddt(n) = -FV::Div_par<FV::Fromm>( n, v, cs );

</div>

</div>

A list of available limiters is given in section
<a href="#sec-slope-limiters" class="reference internal"><span
class="std std-ref">Slope limiters</span></a> below.

<div id="example-and-convergence-test" class="section">

#### Example and convergence test<a href="#example-and-convergence-test" class="headerlink"
title="Permalink to this heading">#</a>

The example code
<span class="pre">`examples/finite-volume/fluid/`</span> solves the
Euler equations for a 1D adiabatic fluid, using <a
href="../_breathe_autogen/file/fv__ops_8hxx.html#_CPPv4I0EN2FV7Div_parEK7Field3DRK7Field3DRK7Field3DRK7Field3Db"
class="reference internal" title="FV::Div_par"><span class="pre"><code
class="sourceCode cpp">FV<span class="op">::</span>Div_par<span class="op">()</span></code></span></a>
for the advection terms.

<div class="math notranslate nohighlight">

\\ \begin{align}\begin{aligned}\frac{\partial n}{\partial t} +
\nabla\_{||}\left(n v\_{||}\right) = 0\\\frac{\partial p}{\partial t} +
\nabla\_{||}\left(p v\_{||}\right) = -(\gamma-1) p
\nabla\_{||}v\_{||}\\\frac{\partial}{\partial t}\left(nv\_{||}\right) +
\nabla\_{||}\left(nv\_{||}v\_{||}\right) = -\partial\_{||}
p\end{aligned}\end{align} \\

</div>

where <span class="math notranslate nohighlight">\\n\\</span> is the
density, <span class="math notranslate nohighlight">\\p\\</span> is the
pressure, and
<span class="math notranslate nohighlight">\\nv\_{||}\\</span> is the
momentum in the direction parallel to the magnetic field. The operator
<span class="math notranslate nohighlight">\\\nabla\_{||}\\</span>
represents the divergence of a parallel flow
(<span class="pre">`Div_par`</span>), and
<span class="math notranslate nohighlight">\\\partial\_{||} =
\mathbf{b}\cdot\nabla\\</span> is the gradient in the parallel
direction.

There is a convergence test using the Method of Manufactured Solutions
(MMS) for this example. See section
<a href="testing.html#sec-mms" class="reference internal"><span
class="std std-ref">Method of Manufactured Solutions</span></a> for
details of the testing method. Running the
<span class="pre">`runtest`</span> script should produce the graph

<figure id="fluid-norm-mc" class="align-default">
<img src="../_images/fluid_norm_mc.png"
alt="Convergence test of the fluid example using `FV::Div_par` operator" />
<figcaption><p><span class="caption-number">Fig. 16 </span><span
class="caption-text">Convergence test, showing <span
class="math notranslate nohighlight">\(l^2\)</span> (RMS) and <span
class="math notranslate nohighlight">\(l^{\infty}\)</span> (maximum)
error for the evolving fields <span class="pre"><code
class="sourceCode cpp">n</code></span> (density), <span
class="pre"><code class="sourceCode cpp">p</code></span> (pressure) and
<span class="pre"><code class="sourceCode cpp">nv</code></span>
(momentum). All fields are shown to converge at the expected second
order accuracy.</span><a href="#fluid-norm-mc" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

</div>

<div id="parallel-diffusion" class="section">

### Parallel diffusion<a href="#parallel-diffusion" class="headerlink"
title="Permalink to this heading">#</a>

The parallel diffusion operator calculates
<span class="math notranslate nohighlight">\\\nabla\_{||}\left\[k\partial\_||\left(f\right)\right\]\\</span>

<div class="highlight-cpp notranslate">

<div class="highlight">

    const Field3D Div_par_K_Grad_par(const Field3D &k, const Field3D &f,
                                     bool bndry_flux=true);

</div>

</div>

This is done by calculating the flux
<span class="math notranslate nohighlight">\\k\partial\_{||}\left(f\right)\\</span>
on cell boundaries using central differencing.

</div>

<div id="advection-in-3d" class="section">

### Advection in 3D<a href="#advection-in-3d" class="headerlink"
title="Permalink to this heading">#</a>

This operator calculates
<span class="math notranslate nohighlight">\\\nabla\cdot\left( n
\mathbf{v} \right)\\</span> where
<span class="math notranslate nohighlight">\\\mathbf{v}\\</span> is a 3D
vector. It is written in flux form by discretising the expression

<div class="math notranslate nohighlight">

\\\nabla\cdot\left( \mathbf{A} \right) = \frac{1}{J}\partial_i \left(J
A^i\right)\\

</div>

Like the <span class="pre">`Div_par`</span> operator, a slope limiter is
used to calculate the value of the field
<span class="math notranslate nohighlight">\\n\\</span> on cell
boundaries. By default this is the MC method, but this can be set as a
template parameter.

<div class="highlight-cpp notranslate">

<div class="highlight">

    template<typename CellEdges = MC>
    const Field3D Div_f_v(const Field3D &n, const Vector3D &v, bool bndry_flux)

</div>

</div>

</div>

<div id="slope-limiters" class="section">

<span id="sec-slope-limiters"></span>

### Slope limiters<a href="#slope-limiters" class="headerlink"
title="Permalink to this heading">#</a>

Here limiters are implemented as slope limiters: The value of a given
quantity is calculated at the faces of a cell based on the cell-centre
values. Several slope limiters are defined in
<span class="pre">`fv_ops.hxx`</span>:

- <span class="pre">`Upwind`</span> - First order upwinding, in which
  the left and right edges of the cell are the same as the centre (zero
  slope).

- <span class="pre">`Fromm`</span> - A second-order scheme which is a
  fixed weighted average of upwinding and central difference schemes.

- <span class="pre">`MinMod`</span> - This second order scheme switches
  between the upwind and downwind gradient, choosing the one with the
  smallest absolute value. If the gradients have different signs, as at
  a maximum or minimum, then the method reverts to first order upwinding
  (zero slope).

- <span class="pre">`MC`</span> (Monotonised Central) is a second order
  scheme which switches between central, upwind and downwind
  differencing in a similar way to <span class="pre">`MinMod`</span>. It
  has smaller dissipation than <span class="pre">`MinMod`</span> so is
  the default.

</div>

<div id="staggered-grids" class="section">

<span id="sec-staggeredgrids"></span>

### Staggered grids<a href="#staggered-grids" class="headerlink"
title="Permalink to this heading">#</a>

By default, all quantities in BOUT++ are defined at cell centre, and all
derivative methods map cell-centred quantities to cell centres.
Switching on staggered grid support in BOUT.inp:

<div class="highlight-cpp notranslate">

<div class="highlight">

    StaggerGrids = true

</div>

</div>

allows quantities to be defined on cell boundaries. Functions such as
<span class="pre">`DDX`</span> now have to handle all possible
combinations of input and output locations, in addition to the possible
derivative methods.

Several things are not currently implemented, which probably should be:

- Only 3D fields currently have a cell location attribute. The location
  (cell centre etc) of 2D fields is ignored at the moment. The rationale
  for this is that 2D fields are assumed to be slowly-varying
  equilibrium quantities for which it won’t matter so much. Still, needs
  to be improved in future

- Twist-shift and X shifting still treat all quantities as cell-centred.

- No boundary condition functions yet account for cell location.

Currently, BOUT++ does not support values at cell corners; values can
only be defined at cell centre, or at the lower X,Y, or Z boundaries.
This is

Once staggered grids are enabled, two types of stencil are needed: those
which map between the same cell location (e.g. cell-centred values to
cell-centred values), and those which map to different locations (e.g.
cell-centred to lower X).

<figure id="id6" class="align-default">
<img src="../_images/diffStencils.png"
alt="Stencils with cell-centred and lower shifted values" />
<figcaption><p><span class="caption-number">Fig. 17 </span><span
class="caption-text">Stencils with cell-centred (solid) and lower
shifted values (open). Processor boundaries marked by vertical dashed
line</span><a href="#id6" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

Central differencing using 4-point stencil:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} y &=& \left(9y\_{-1/2} + 9y\_{1/2} -
y\_{-3/2} - y\_{3/2}\right) / 16 \\ {{\frac{\partial y}{\partial x}}}
&=& \left( 27y\_{1/2} - 27y\_{-1/2} - y\_{3/2} + y\_{-3/2}\right) /
24\Delta x \\ \frac{\partial^2 y}{\partial x^2} &=& \left(y\_{3/2} +
y\_{-3/2} - y\_{1/2} - y\_{-1/2}\right) / 2\Delta
x^2\end{aligned}\end{split}\\

</div>

<table class="table">
<thead>
<tr class="row-odd">
<th class="head"><p>Input</p></th>
<th class="head"><p>Output</p></th>
<th class="head"><p>Actions</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td></td>
<td><p>Central stencil</p></td>
<td></td>
</tr>
<tr class="row-odd">
<td><p>CENTRE</p></td>
<td><p>XLOW</p></td>
<td><p>Lower staggered stencil</p></td>
</tr>
<tr class="row-even">
<td><p>XLOW</p></td>
<td><p>CENTRE</p></td>
<td><p>Upper staggered stencil</p></td>
</tr>
<tr class="row-odd">
<td><p>XLOW</p></td>
<td><p>Any</p></td>
<td><p>Staggered stencil to CENTRE, then interpolate</p></td>
</tr>
<tr class="row-even">
<td><p>CENTRE</p></td>
<td><p>Any</p></td>
<td><p>Central stencil, then interpolate</p></td>
</tr>
<tr class="row-odd">
<td><p>Any</p></td>
<td><p>Any</p></td>
<td><p>Interpolate to centre, use central stencil, then
interpolate</p></td>
</tr>
</tbody>
</table>

Table: DDX actions depending on input and output locations. Uses first
match.

</div>

</div>

<div id="derivatives-of-the-fourier-transform" class="section">

<span id="sec-derivatives-of-fft"></span>

## Derivatives of the Fourier transform<a href="#derivatives-of-the-fourier-transform" class="headerlink"
title="Permalink to this heading">#</a>

By using the definition of the Fourier transformed, we have

<div class="math notranslate nohighlight">

\\F(x,y,\xi) = {\int\_{-\infty}^{\infty} {f(x,y,z)\exp(-2\pi iz\xi)} \\
\text{d} {z}}\\

</div>

this gives

<div id="equation-f-derivative" class="math notranslate nohighlight">

<span class="eqno">(9)<a href="#equation-f-derivative" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}&{\int\_{-\infty}^{\infty}
{(\partial_zf\[x,y,z\])\exp(-2\pi iz\xi)} \\ \text{d} {z}}\\ =&
{\int\_{-\infty}^{\infty} {\partial_z(f\[x,y,z\]\exp\[-2\pi iz\xi\])} \\
\text{d} {z}} - {\int\_{-\infty}^{\infty} {f(x,y,z)\partial_z\exp(-2\pi
iz\xi)} \\ \text{d} {z}}\\ =& (f\[x,y,z\]\exp\[-2\pi
iz\xi\])\bigg|\_{-\infty}^{\infty} - (-2\pi
i\xi){\int\_{-\infty}^{\infty} {f(x,y,z)\exp(-2\pi iz\xi)} \\ \text{d}
{z}}\\ =& 2\pi i\xi F(x,y,\xi)\end{split}\\

</div>

where we have used that
<span class="math notranslate nohighlight">\\f(x,y,\pm\infty)=0\\</span>
in order to have a well defined Fourier transform. This means that

<div class="math notranslate nohighlight">

\\\partial_z^n F(x,y,\xi) = (2\pi i \xi)^n F(x,y,\xi)\\

</div>

In our case, we are dealing with periodic boundary conditions. Strictly
speaking, the Fourier transform does not exist in such cases, but it is
possible to define a Fourier transform in the limit which in the end
lead to the Fourier series [2] By discretising the spatial domain, it is
no longer possible to represent the infinite amount of Fourier modes,
but only <span class="math notranslate nohighlight">\\N+1\\</span>
number of modes, where
<span class="math notranslate nohighlight">\\N\\</span> is the number of
points (this includes the modes with negative frequencies, and the
zeroth offset mode). For the discrete Fourier transform, we have

<div id="equation-dft" class="math notranslate nohighlight">

<span class="eqno">(10)<a href="#equation-dft" class="headerlink"
title="Permalink to this equation">#</a></span>\\F(x,y)\_{k} =
\frac{1}{N}\sum\_{Z=0}^{N-1}f(x,y)\_{Z}\exp(\frac{-2\pi i k Z}{N})\\

</div>

where <span class="math notranslate nohighlight">\\k\\</span> is the
mode number, <span class="math notranslate nohighlight">\\N\\</span> is
the number of points in
<span class="math notranslate nohighlight">\\z\\</span>. If we call the
sampling points of
<span class="math notranslate nohighlight">\\z\\</span> for
<span class="math notranslate nohighlight">\\z_Z\\</span>, where
<span class="math notranslate nohighlight">\\Z = 0, 1 \ldots
N-1\\</span>, we have that
<span class="math notranslate nohighlight">\\z_Z = Z \text{d}z\\</span>.
As our domain goes from
<span class="math notranslate nohighlight">\\\[0, 2\pi\[\\</span>, we
have that (since we have one less line segment than point)
<span class="math notranslate nohighlight">\\\text{d}z (N-1) = L_z =
2\pi - \text{d}z\\</span>, which gives
<span class="math notranslate nohighlight">\\\text{d}z =
\frac{2\pi}{N}\\</span>. Inserting this is equation
(<a href="#equation-dft" class="reference internal">(10)</a>) yields

<div class="math notranslate nohighlight">

\\F(x,y)\_{k} = \frac{1}{N}\sum\_{Z=0}^{N-1}f(x,y)\_{Z}\exp( - i k
Z\text{d}z) = \frac{1}{N}\sum\_{Z=0}^{N-1}f(x,y)\_{Z}\exp( - i k z_Z)\\

</div>

The discrete version of equation
(<a href="#equation-f-derivative" class="reference internal">(9)</a>)
thus gives

<div class="math notranslate nohighlight">

\\\partial_z^n F(x,y)\_k = (i k)^n F(x,y)\_k\\

</div>

<span class="label"><span class="fn-bracket">\[</span><a href="#id3" role="doc-backlink">2</a><span class="fn-bracket">\]</span></span>

For more detail see Bracewell, R. N. - The Fourier Transform and Its
Applications 3rd Edition chapter 10

</div>

</div>

<div class="prev-next-area">

<a href="laplacian.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Laplacian inversion

</div>

<a href="algebraic_operators.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Algebraic operators

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#differencing-methods"
  class="reference internal nav-link">Differencing methods</a>
- <a href="#user-registered-methods"
  class="reference internal nav-link">User registered methods</a>
- <a href="#mixed-second-derivative-operators"
  class="reference internal nav-link">Mixed second-derivative
  operators</a>
- <a href="#non-uniform-meshes"
  class="reference internal nav-link">Non-uniform meshes</a>
- <a href="#general-operators" class="reference internal nav-link">General
  operators</a>
- <a href="#clebsch-operators" class="reference internal nav-link">Clebsch
  operators</a>
- <a href="#the-bracket-operators" class="reference internal nav-link">The
  bracket operators</a>
- <a href="#finite-volume-conservative-finite-difference-methods"
  class="reference internal nav-link">Finite volume, conservative finite
  difference methods</a>
  - <a href="#parallel-divergence-div-par"
    class="reference internal nav-link">Parallel divergence <span
    class="pre"><code
    class="docutils literal notranslate">Div_par</code></span></a>
    - <a href="#example-and-convergence-test"
      class="reference internal nav-link">Example and convergence test</a>
  - <a href="#parallel-diffusion"
    class="reference internal nav-link">Parallel diffusion</a>
  - <a href="#advection-in-3d" class="reference internal nav-link">Advection
    in 3D</a>
  - <a href="#slope-limiters" class="reference internal nav-link">Slope
    limiters</a>
  - <a href="#staggered-grids" class="reference internal nav-link">Staggered
    grids</a>
- <a href="#derivatives-of-the-fourier-transform"
  class="reference internal nav-link">Derivatives of the Fourier
  transform</a>

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

[2]
