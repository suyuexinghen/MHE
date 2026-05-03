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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/parallel-transforms.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/parallel-transforms.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/parallel-transforms.rst"
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

# Parallel Transforms

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#field-aligned-grid"
  class="reference internal nav-link">Field-aligned grid</a>
- <a href="#shifted-metric" class="reference internal nav-link">Shifted
  metric</a>
- <a href="#aligned-transform" class="reference internal nav-link">Aligned
  transform</a>
- <a href="#fci-method" class="reference internal nav-link">FCI method</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="parallel-transforms" class="section">

<span id="sec-parallel-transforms"></span>

# Parallel Transforms<a href="#parallel-transforms" class="headerlink"
title="Permalink to this heading">#</a>

In most BOUT++ simulations the Y coordinate is parallel to the magnetic
field. In particular if the magnetic field
<span class="math notranslate nohighlight">\\\mathbf{B}\\</span> can be
expressed as

<div class="math notranslate nohighlight">

\\\mathbf{B} = \nabla z \times \nabla x\\

</div>

then the Clebsch operators can be used. See section
<a href="differential_operators.html#sec-diffops"
class="reference internal"><span class="std std-ref">Differential
operators</span></a> for more details.

The structure of the magnetic field can be simple, as in a slab
geometry, but in many cases it is quite complicated. In a tokamak, for
example, the magnetic shear causes deformation of grid cells and
numerical issues. One way to overcome this is to transform between local
coordinate systems, interpolating in the toroidal (Z) direction when
calculating gradients along the magnetic field. This is called the
*shifted metric* method. In more general geometries such as
stellarators, the magnetic field can have a 3D structure and stochastic
regions. In this case the interpolation becomes 2D (in X and Z), and is
known as the Flux Coordinate Independent (FCI) method.

To handle these different cases in the same code, the BOUT++ mesh
implements different <a
href="../_breathe_autogen/file/paralleltransform_8hxx.html#_CPPv417ParallelTransform"
class="reference internal" title="ParallelTransform"><span
class="pre"><code
class="sourceCode cpp">ParallelTransform</code></span></a> classes. Each
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> class contains a
pointer to the values up and down in the Y direction, called yup and
ydown. These values are calculated during communication (unless
explicitly disabled, see
<a href="#sec-aligned-transform" class="reference internal"><span
class="std std-ref">Aligned transform</span></a>):

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D f(0.0);  // f allocated, set to zero
    f.yup();    // error: f.yup not allocated

    mesh->communicate(f);
    f.yup(); // ok

    f.ydown()(0,1,0); // ok

</div>

</div>

In the case of slab geometry, yup and ydown point to the original field
(f). For this reason the value of f along the magnetic field from
f(x,y,z) is given by f.ydown(x,y-1,z) and f.yup(x,y+1,z). To take a
centred difference along Y using the Field3D iterators (section
<a href="../developer_docs/data_types.html#sec-iterating"
class="reference internal"><span class="std std-ref">Iterating over
fields</span></a>):

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D result;
    result.allocate(); // Need to allocate before indexing

    for(const auto &i : result.region(RGN_NOBNDRY)) {
      result[i] = f.yup()[i.yp()] - f.ydown()[i.ym()];
    }

</div>

</div>

Note the use of yp() and ym() to increase and decrease the Y index.

Parallel derivatives or interpolations can also be calculated by
transforming to a globally field aligned grid,
<a href="#sec-aligned-transform" class="reference internal"><span
class="std std-ref">Aligned transform</span></a>. This method is also
used as a fallback when the input does not have parallel slices
calculated when using
<a href="#sec-shifted-metric" class="reference internal"><span
class="std std-ref">Shifted metric</span></a>.

<div id="field-aligned-grid" class="section">

## Field-aligned grid<a href="#field-aligned-grid" class="headerlink"
title="Permalink to this heading">#</a>

The default <a
href="../_breathe_autogen/file/paralleltransform_8hxx.html#_CPPv417ParallelTransform"
class="reference internal" title="ParallelTransform"><span
class="pre"><code
class="sourceCode cpp">ParallelTransform</code></span></a> is the
identity transform, which sets yup() and ydown() to point to the same
field. In the input options the setting is

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh:paralleltransform]
    type = identity

</div>

</div>

This then uses the <a
href="../_breathe_autogen/file/paralleltransform_8hxx.html#_CPPv425ParallelTransformIdentity"
class="reference internal" title="ParallelTransformIdentity"><span
class="pre"><code
class="sourceCode cpp">ParallelTransformIdentity</code></span></a> class
to calculate the yup and ydown fields.

This is mostly useful for slab geometries, where for a straight magnetic
field the grid is either periodic in the y-direction or ends on a
y-boundary. By setting the global option
<span class="pre">`TwistShift`</span>` `<span class="pre">`=`</span>` `<span class="pre">`true`</span>
and providing a <span class="pre">`ShiftAngle`</span> in the gridfile or
<span class="pre">`[mesh]`</span> options a branch cut can be introduced
between the beginning and end of the y-domain.

<a
href="../_breathe_autogen/file/paralleltransform_8hxx.html#_CPPv425ParallelTransformIdentity"
class="reference internal" title="ParallelTransformIdentity"><span
class="pre"><code
class="sourceCode cpp">ParallelTransformIdentity</code></span></a> can
also be used in non-slab geometries. Then
<span class="pre">`TwistShift`</span>` `<span class="pre">`=`</span>` `<span class="pre">`true`</span>
should be set so that a twist-shift boundary condition is applied on
closed field lines, as field-line following coordinates are not periodic
in poloidal angle. Note that it is not recommended to use <a
href="../_breathe_autogen/file/paralleltransform_8hxx.html#_CPPv425ParallelTransformIdentity"
class="reference internal" title="ParallelTransformIdentity"><span
class="pre"><code
class="sourceCode cpp">ParallelTransformIdentity</code></span></a> with
toroidal geometries, as magnetic shear will make the radial derivatives
inaccurate away from the outboard midplane (which is normall chosen as
the zero point for the integrated shear).

</div>

<div id="shifted-metric" class="section">

<span id="sec-shifted-metric"></span>

## Shifted metric<a href="#shifted-metric" class="headerlink"
title="Permalink to this heading">#</a>

The shifted metric method is selected using:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh:paralleltransform]
    type = shifted

</div>

</div>

so that mesh uses the <a
href="../_breathe_autogen/file/paralleltransform_8hxx.html#_CPPv413ShiftedMetric"
class="reference internal" title="ShiftedMetric"><span class="pre"><code
class="sourceCode cpp">ShiftedMetric</code></span></a> class to
calculate parallel transforms. During initialisation, this class reads a
quantity zShift from the input or grid file. If zShift is not found then
qinty is read instead. If qinty is not found then the angle is zero, and
this method becomes the same as the identity transform. For each X and Z
index, the zShift variable should contain the toroidal angle of a
magnetic field line at
<span class="math notranslate nohighlight">\\z=0\\</span> starting at
<span class="math notranslate nohighlight">\\\phi=0\\</span> at a
reference location
<span class="math notranslate nohighlight">\\\theta_0\\</span>:

<div class="math notranslate nohighlight">

\\\mathtt{zShift} = \int\_{\theta_0}^\theta \frac{B\_\phi
h\_\theta}{B\_\theta R} d\theta\\

</div>

Note that here
<span class="math notranslate nohighlight">\\\theta_0\\</span> does not
need to be constant in X (radius), since it is only the relative shifts
between Y locations which matters.

Special handling is needed for parallel boundary conditions, see
<a href="boundary_options.html#sec-parallel-bc-shifted-metric"
class="reference internal"><span class="std std-ref">Shifted metric
boundary conditions</span></a>.

</div>

<div id="aligned-transform" class="section">

<span id="sec-aligned-transform"></span>

## Aligned transform<a href="#aligned-transform" class="headerlink"
title="Permalink to this heading">#</a>

The aligned transform method is a variation of shifted metric. Parallel
derivatives are calculated by transforming their argument to a globally
field aligned mesh, by toroidal interpolation using zShift, calculating
the derivative or interpolation on the globally aligned grid, and then
transforming the result back to the standard toroidal grid.

The aligned transform scheme is implemented using the
<span class="pre">`ShiftedMetric`</span> class for parallel transforms,
by disabling the calculation of parallel slices. Select it by using:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh:paralleltransform]
    type = shifted
    calcParallelSlices_on_communicate = false

</div>

</div>

With these settings, inputs to parallel derivative or interpolation
operators will be implicitly transformed to the globally aligned grid,
and the results transformed back.

Using implicit transformations can result in more interpolations than
absolutely necessary being done. For example, when using y-staggered
grids, most variables will need both a parallel interpolation between
<span class="pre">`CELL_CENTRE`</span> and
<span class="pre">`CELL_YLOW`</span> and also at least one parallel
derivative. To optimise such cases, the field aligned version of a
variable can be calculated and stored in a separate object. BOUT++
operators return their result on the same grid as the input argument, so
if the result of an operation on a field aligned variable is needed on
the toroidal grid, it must be transformed explicitly. For example,
parallel diffusion of a variable <span class="pre">`f`</span> in this
scheme might look something like:

<div class="highlight-cpp notranslate">

<div class="highlight">

    f_aligned = toFieldAligned(f);

    ddt(f) = D_par * fromFieldAligned(Grad2_par2(f_aligned));

</div>

</div>

Special handling is needed for parallel boundary conditions, see
<a href="boundary_options.html#sec-parallel-bc-aligned-transform"
class="reference internal"><span class="std std-ref">Aligned transform
boundary conditions</span></a>.

</div>

<div id="fci-method" class="section">

<span id="sec-fci"></span>

## FCI method<a href="#fci-method" class="headerlink"
title="Permalink to this heading">#</a>

To use the FCI method for parallel transforms, set

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh:paralleltransform]
    type = fci

</div>

</div>

which causes the
<a href="../_breathe_autogen/file/fci_8hxx.html#_CPPv412FCITransform"
class="reference internal" title="FCITransform"><span class="pre"><code
class="sourceCode cpp">FCITransform</code></span></a> class to be used
for parallel transforms. This reads four variables (3D fields) from the
input grid: <span class="pre">`forward_xt_prime`</span>,
<span class="pre">`forward_zt_prime`</span>,
<span class="pre">`backward_xt_prime`</span>, and
<span class="pre">`backward_zt_prime`</span>. These give the cell
indices, not in general integers, in the forward (yup) and backward
(ydown) directions. These are arranged so that forward_xt_prime(x,y,z)
is the x index at y+1. Hence f.yup()(x,y+1,z) is calculated using
forward_xt_prime(x,y,z) and forward_zt_prime(x,y,z), whilst
f.ydown()(x,y-1,z) is calculated using backward_xt_prime(x,y,z) and
backward_zt_prime(x,y,z).

Tools for calculating these mappings include Zoidberg, a Python tool
which carries out field-line tracing and generates FCI inputs.

Special handling is needed for parallel boundary conditions, see
<a href="boundary_options.html#sec-parallel-bc-fci"
class="reference internal"><span class="std std-ref">FCI boundary
conditions</span></a>.

</div>

</div>

<div class="prev-next-area">

<a href="time_integration.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Time integration

</div>

<a href="laplacian.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Laplacian inversion

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#field-aligned-grid"
  class="reference internal nav-link">Field-aligned grid</a>
- <a href="#shifted-metric" class="reference internal nav-link">Shifted
  metric</a>
- <a href="#aligned-transform" class="reference internal nav-link">Aligned
  transform</a>
- <a href="#fci-method" class="reference internal nav-link">FCI method</a>

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
