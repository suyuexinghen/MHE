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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/boundary_options.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/boundary_options.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/boundary_options.rst"
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

# Boundary conditions

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#boundary-conditions-for-non-orthogonal-grids"
  class="reference internal nav-link">Boundary conditions for
  non-orthogonal grids</a>
- <a href="#parallel-boundary-conditions"
  class="reference internal nav-link">Parallel boundary conditions</a>
  - <a href="#shifted-metric-boundary-conditions"
    class="reference internal nav-link">Shifted metric boundary
    conditions</a>
  - <a href="#aligned-transform-boundary-conditions"
    class="reference internal nav-link">Aligned transform boundary
    conditions</a>
  - <a href="#fci-boundary-conditions"
    class="reference internal nav-link">FCI boundary conditions</a>
- <a href="#relaxing-boundaries"
  class="reference internal nav-link">Relaxing boundaries</a>
- <a href="#changing-the-width-of-boundaries"
  class="reference internal nav-link">Changing the width of boundaries</a>
- <a href="#examples" class="reference internal nav-link">Examples</a>
- <a href="#boundary-regions" class="reference internal nav-link">Boundary
  regions</a>
- <a href="#id1" class="reference internal nav-link">Boundary regions</a>
- <a href="#boundary-operations"
  class="reference internal nav-link">Boundary operations</a>
- <a href="#boundary-modifiers"
  class="reference internal nav-link">Boundary modifiers</a>
- <a href="#boundary-factory" class="reference internal nav-link">Boundary
  factory</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="boundary-conditions" class="section">

<span id="sec-bndryopts"></span>

# Boundary conditions<a href="#boundary-conditions" class="headerlink"
title="Permalink to this heading">#</a>

See also
<a href="physics_models.html#sec-physicsmodel-boundary-conditions"
class="reference internal"><span class="std std-ref">Boundary
conditions</span></a>.

Like the variable initialisation, boundary conditions can be set for
each variable in individual sections, with default values in a section
<span class="pre">`[All]`</span>. Boundary conditions are specified for
each variable, being applied to variable itself during initialisation,
and the time-derivatives at each timestep. They are a combination of a
basic boundary condition, and optional modifiers.

When finding the boundary condition for a variable
<span class="pre">`var`</span> on a boundary region, the options are
checked in order from most to least specific:

- Section <span class="pre">`var`</span>,
  <span class="pre">`bndry_`</span> + region name. Depending on the mesh
  file, regions of the grid are given labels. Currently these are
  <span class="pre">`core`</span>, <span class="pre">`sol`</span>,
  <span class="pre">`pf`</span>, <span class="pre">`lower_target`</span>
  and <span class="pre">`upper_target`</span> which are intended for
  tokamak edge simulations. Hence the variables checked are
  <span class="pre">`bndry_core`</span>,
  <span class="pre">`bndry_pf`</span> etc.

- Section <span class="pre">`var`</span>,
  <span class="pre">`bndry_`</span> + boundary side. These names are
  <span class="pre">`xin`</span>, <span class="pre">`xout`</span>,
  <span class="pre">`yup`</span> and <span class="pre">`ydown`</span>.

- Section <span class="pre">`var`</span>, variable
  <span class="pre">`bndry_all`</span>

- The same settings again except in section
  <span class="pre">`All`</span>.

The default setting for everything is therefore
<span class="pre">`bndry_all`</span> in the
<span class="pre">`All`</span> section.

Boundary conditions are given names, with optional arguments in
brackets. Currently implemented boundary conditions are:

- <span class="pre">`dirichlet`</span> - Set to zero

- <span class="pre">`dirichlet(<number>)`</span> - Set to some number
  e.g. <span class="pre">`dirichlet(1)`</span> sets the boundary to
  <span class="math notranslate nohighlight">\\1.0\\</span>

- <span class="pre">`neumann`</span> - Zero gradient

- <span class="pre">`robin`</span> - A combination of zero-gradient and
  zero-value <span class="math notranslate nohighlight">\\a f +
  b{{\frac{\partial f}{\partial x}}} = g\\</span> where the syntax is
  <span class="pre">`robin(a,`</span>` `<span class="pre">`b,`</span>` `<span class="pre">`g)`</span>.

- <span class="pre">`constgradient`</span> - Constant gradient across
  boundary

- <span class="pre">`zerolaplace`</span> - Laplacian = 0, decaying
  solution (X boundaries only)

- <span class="pre">`zerolaplace2`</span> - Laplacian = 0, using
  coefficients from the Laplacian inversion and Delp2 operator.

- <span class="pre">`constlaplace`</span> - Laplacian = const, decaying
  solution (X boundaries only)

The zero- or constant-Laplacian boundary conditions works as follows:

<div class="math notranslate nohighlight">

\\\begin{split}\nabla\_\perp^2 f &= 0 \\ &\simeq g^{xx}\frac{\partial^2
f}{\partial x^2} + g^{zz}\frac{\partial^2 f}{\partial z^2}\end{split}\\

</div>

which when Fourier transformed in
<span class="math notranslate nohighlight">\\z\\</span> becomes:

<div class="math notranslate nohighlight">

\\g^{xx}\frac{\partial^2 \hat{f}}{\partial x^2} - g^{zz}k_z^2 \hat{f} =
0\\

</div>

which has the solution

<div class="math notranslate nohighlight">

\\\hat{f} = Ae^{xk_z\sqrt{g^{zz}/g^{xx}}} +
Be^{-xk_z\sqrt{g^{zz}/g^{xx}}}\\

</div>

Assuming that the solution should decay away from the domain, on the
inner <span class="math notranslate nohighlight">\\x\\</span> boundary
<span class="math notranslate nohighlight">\\B = 0\\</span>, and on the
outer boundary <span class="math notranslate nohighlight">\\A =
0\\</span>.

Boundary modifiers change the behaviour of boundary conditions, and more
than one modifier can be used. Currently the following are available:

- <span class="pre">`relax`</span> - Relaxing boundaries. Evolve the
  variable towards the given boundary condition at a given rate

- <span class="pre">`width`</span> - Modifies the width of the region
  over which the boundary condition is applied

- <span class="pre">`fromFieldAligned`</span> - Transform the variable
  from toroidal to field aligned coordinates to apply the boundary
  condition (and transform back afterwards). Provides a way to apply
  parallel boundary conditions in a field aligned way, see
  <a href="#sec-parallel-boundary-conditions"
  class="reference internal"><span class="std std-ref">Parallel boundary
  conditions</span></a>.

- <span class="pre">`toFieldAligned`</span> - Transform the variable
  from field aligned to toroidal coordinates to apply the boundary
  condition (and transform back afterwards). Could be used to apply
  radial boundary conditions to a variable defined on a field aligned
  grid. Should probably never be useful.

These are described in the following subsections.

<div id="boundary-conditions-for-non-orthogonal-grids" class="section">

## Boundary conditions for non-orthogonal grids<a href="#boundary-conditions-for-non-orthogonal-grids"
class="headerlink" title="Permalink to this heading">#</a>

If non-orthogonal grids are used (meaning that the x- and y-directions
are not orthogonal, so
<span class="pre">`g12`</span>` `<span class="pre">`!=`</span>` `<span class="pre">`0.`</span>),
then corner cells may be required. The boundary conditions are applied
in corner cells\[#disablecorners\]\_ by applying the y-boundary
condition using x-boundary values. This requires that x-boundary
conditions are applied before y-boundary conditions. The ordering is
taken care of by the methods described in this section, but also needs
to be respected by any custom boundary conditions in user code (e.g.
sheath boundary conditions). Note that the iterators returned by the
<span class="pre">`BoutMesh`</span> methods
<span class="pre">`iterateBndryLowerY`</span>,
<span class="pre">`iterateBndryLowerInnerY`</span>,
<span class="pre">`iterateBndryLowerOuterY`</span>,
<span class="pre">`iterateBndryUpperY`</span>,
<span class="pre">`iterateBndryUpperInnerY`</span>, and
<span class="pre">`iterateBndryUpperOuterY`</span> do include the corner
cells at the domain boundary corners.

<span class="label"><span class="fn-bracket">\[</span>1<span class="fn-bracket">\]</span></span>

although this may be disabled, reverting to the behaviour of BOUT++ up
to v4, by setting the option
<span class="pre">`mesh:include_corner_cells`</span>` `<span class="pre">`=`</span>` `<span class="pre">`false`</span>.

</div>

<div id="parallel-boundary-conditions" class="section">

<span id="sec-parallel-boundary-conditions"></span>

## Parallel boundary conditions<a href="#parallel-boundary-conditions" class="headerlink"
title="Permalink to this heading">#</a>

Unless using slab geometry (with
<span class="pre">`ParallelTransformIdentity`</span>, see
<a href="parallel-transforms.html#sec-parallel-transforms"
class="reference internal"><span class="std std-ref">Parallel
Transforms</span></a>), some special handling is needed to apply
parallel boundary conditions. The details depend on the parallel
derivative scheme being used, see below. The default
<span class="pre">`bndry_yup`</span> and
<span class="pre">`bndry_ydown`</span> settings would apply boundary
conditions in the poloidal, rather than parallel direction. As the
poloidal direction generally has a coarse resolution, that is not
sufficient to resolve perpendicular gradients, this would result in
large numerical inaccuracies in the boundary conditions.

<div id="shifted-metric-boundary-conditions" class="section">

<span id="sec-parallel-bc-shifted-metric"></span>

### Shifted metric boundary conditions<a href="#shifted-metric-boundary-conditions" class="headerlink"
title="Permalink to this heading">#</a>

When using the <span class="pre">`ShiftedMetric`</span> implementation
of <span class="pre">`ParallelTransform`</span> (by setting
<span class="pre">`mesh:paralleltransform`</span>` `<span class="pre">`=`</span>` `<span class="pre">`shifted`</span>,
see <a href="parallel-transforms.html#sec-shifted-metric"
class="reference internal"><span class="std std-ref">Shifted
metric</span></a>), the recommended method is to apply boundary
conditions directly to the <span class="pre">`yup`</span> and
<span class="pre">`ydown`</span> parallel slices. This can be done by
setting <span class="pre">`bndry_par_yup`</span> and
<span class="pre">`bndry_par_ydown`</span>, or
<span class="pre">`bndry_par_all`</span> to set both at once. The
possible values are <span class="pre">`parallel_dirichlet_o1`</span>,
<span class="pre">`parallel_dirichlet_o2`</span>,
<span class="pre">`parallel_dirichlet_o3`</span> and
<span class="pre">`parallel_neumann_o1`</span>,
<span class="pre">`parallel_neumann_o2`</span>,
<span class="pre">`parallel_neumann_o3`</span>. The stencils used are
the same as for the standard boundary conditions without the
<span class="pre">`parallel_`</span> prefix, but are applied directly to
parallel slices. The boundary condition can only be applied after the
parallel slices are calculated, which is usually done during a call to
<span class="pre">`Mesh::communicate()`</span>, so the
<span class="pre">`applyBoundary()`</span> method must be called
explicitly (when boundary conditions are applied automatically to
evolving variables, they cannot set these parallel boundary conditions).
For maximum efficiency, set <span class="pre">`bndry_yup`</span> and
<span class="pre">`bndry_ydown`</span> to
<span class="pre">`none`</span> to skip using any boundary condition to
set the unused boundary cells of the base variable.

For example, for an evolving variable <span class="pre">`f`</span>, put
a section in the <span class="pre">`BOUT.inp`</span> input file like

<div class="highlight-cfg notranslate">

<div class="highlight">

    [f]
    bndry_xin = dirichlet
    bndry_xout = dirichlet
    bndry_par_all = parallel_neumann_o2
    bndry_ydown = none
    bndry_yup = none

</div>

</div>

and in the <span class="pre">`PhysicsModel::rhs()`</span> function,
before taking any derivatives of <span class="pre">`f`</span>, call

<div class="highlight-cpp notranslate">

<div class="highlight">

    mesh->communicate(f);
    f.applyBoundary();

</div>

</div>

The <span class="pre">`bndry_par_*`</span> options only provide a subset
of boundary conditions. If others are required, they can be used with a
different, slightly less optimised method. The modifier
<span class="pre">`fromFieldAligned()`</span> applies a boundary
condition by first transforming the variable to a globally field aligned
grid, then applying the boundary condition, then transforming back to
the toroidal grid. When this method is used, the boundary conditions
must be applied before communicating, so that the parallel slices are
calculated using the boundary cells of the base variable (for variables
that have been added to the time solver, this will automatically be the
case). For example, the settings in <span class="pre">`BOUT.inp`</span>
for a Robin parallel boundary condition could be

<div class="highlight-cfg notranslate">

<div class="highlight">

    [f]
    bndry_xin = dirichlet
    bndry_xout = dirichlet
    bndry_yup = fromFieldAligned(robin(1, -1, 0))
    bndry_ydown = fromFieldAligned(robin(1, 1, 0))

</div>

</div>

</div>

<div id="aligned-transform-boundary-conditions" class="section">

<span id="sec-parallel-bc-aligned-transform"></span>

### Aligned transform boundary conditions<a href="#aligned-transform-boundary-conditions" class="headerlink"
title="Permalink to this heading">#</a>

When using the ‘aligned transform’ method for parallel derivatives (see
<a href="parallel-transforms.html#sec-aligned-transform"
class="reference internal"><span class="std std-ref">Aligned
transform</span></a>), the way to apply parallel boundary conditions
depends on how the method was implemented.

For the ‘implicit transform’ version where the transformations to and
from the field aligned grid are done within each parallel derivative or
interpolation operator, the parallel boundary conditions must be applied
to the base variable, so they must be applied using the
<span class="pre">`fromFieldAligned()`</span> modifier, as described in
the previous section (<a href="#sec-parallel-bc-shifted-metric"
class="reference internal"><span class="std std-ref">Shifted metric
boundary conditions</span></a>).

For the optimised method with separate objects for the field aligned
versions of variables, it would be correct to apply boundary conditions
using the <span class="pre">`fromFieldAligned()`</span> modifier before
calculating the field aligned versions, but would add extra
interpolations. Therefore the recommended way to apply parallel boundary
conditions is to apply them directly to the field aligned versions of
variables. Since the objects for the field aligned versions are not
added to the time solver, it is necessary to load boundary conditions
explicitly from the <span class="pre">`BOUT.inp`</span> input file
during <span class="pre">`PhysicsModel::init()`</span>, for example by
calling:

<div class="highlight-cpp notranslate">

<div class="highlight">

    f_aligned.setBoundary("f_aligned")

</div>

</div>

where the argument to <span class="pre">`setBoundary()`</span> specifies
the name of the section in <span class="pre">`BOUT.inp`</span> from
which boundary conditions will be read. Then the boundary conditions
must be applied explicitly after the field aligned object has been
calculated in <span class="pre">`PhysicsModel::rhs()`</span>, for
example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    f_aligned = fromFieldAligned(f);
    f_aligned.applyBoundary();

</div>

</div>

The boundary condition should be applied directly to the array in
<span class="pre">`f_aligned`</span> (not to parallel slices, which are
not created for this scheme), so uses the ‘standard’
<span class="pre">`bndry_yup`</span>/<span class="pre">`bndry_ydown`</span>.
Radial boundary points should never be used from the aligned object, so
its x-boundaries should be set to <span class="pre">`none`</span>, and
parallel boundary points should never be used from the base variable, so
its y-boundaries should be set to <span class="pre">`none`</span>. The
input sections for <span class="pre">`f`</span> and
<span class="pre">`f_aligned`</span> might look like

<div class="highlight-cfg notranslate">

<div class="highlight">

    [f]
    bndry_xin = dirichlet
    bndry_xout = dirichlet
    bndry_yup = none
    bndry_ydown = none

    [f_aligned]
    bndry_xin = none
    bndry_xout = none
    bndry_yup = free_o3
    bndry_ydown = free_o3

</div>

</div>

</div>

<div id="fci-boundary-conditions" class="section">

<span id="sec-parallel-bc-fci"></span>

### FCI boundary conditions<a href="#fci-boundary-conditions" class="headerlink"
title="Permalink to this heading">#</a>

When using the FCI method (<a href="parallel-transforms.html#sec-fci"
class="reference internal"><span class="std std-ref">FCI
method</span></a>), parallel boundary conditions must be applied to the
parallel slices using <span class="pre">`bndry_par_yup`</span> and
<span class="pre">`bndry_par_ydown`</span>, or
<span class="pre">`bndry_par_all`</span> to set both together. It is
suggested, at least if there are boundaries in the y-direction of the
grid, to set
<span class="pre">`bndry_yup`</span>` `<span class="pre">`=`</span>` `<span class="pre">`none`</span>
and
<span class="pre">`bndry_down`</span>` `<span class="pre">`=`</span>` `<span class="pre">`none`</span>
to skip unnecessary operations on y-boundary cells of the base variable.
For example, for an evolving variable <span class="pre">`f`</span>, put
a section in the <span class="pre">`BOUT.inp`</span> input file like

<div class="highlight-cfg notranslate">

<div class="highlight">

    [f]
    bndry_xin = dirichlet
    bndry_xout = dirichlet
    bndry_par_all = parallel_dirichlet_o2
    bndry_ydown = none
    bndry_yup = none

</div>

</div>

One should not that the parallel boundary conditions have to be applied
after communication, while the perpendicular ones before:

<div class="highlight-C++ notranslate">

<div class="highlight">

    f.applyBoundary();
    mesh->communicate(f);
    f.applyParallelBoundary("parallel_neumann_o2");

</div>

</div>

Note that during grid generation care has to be taken to ensure that
there are no “short” connection lengths. Otherwise it can happen that
for a point on a slice, both yup() and ydown() are boundary cells, and
interpolation into the boundary can only use the single point on the
given cell.

</div>

</div>

<div id="relaxing-boundaries" class="section">

## Relaxing boundaries<a href="#relaxing-boundaries" class="headerlink"
title="Permalink to this heading">#</a>

All boundaries can be modified to be “relaxing” which are a combination
of zero-gradient time-derivative, and whatever boundary condition they
are applied to. The idea is that this prevents sharp discontinuities at
boundaries during transients, whilst maintaining the desired boundary
condition on longer time-scales. In some cases this can improve the
numerical stability and timestep.

For example, <span class="pre">`relax(dirichlet)`</span> will make a
field <span class="math notranslate nohighlight">\\f\\</span> at point
<span class="math notranslate nohighlight">\\i\\</span> in the boundary
follow a point <span class="math notranslate nohighlight">\\i-1\\</span>
in the domain:

<div class="math notranslate nohighlight">

\\.{{\frac{\partial f}{\partial t}}}|\_i = .{{\frac{\partial f}{\partial
t}}}|\_{i-1} - f_i / \tau\\

</div>

where <span class="math notranslate nohighlight">\\\tau\\</span> is a
time-scale for the boundary (currently set to 0.1, but will be a global
option). When the time-derivatives are slow close to the boundary, the
boundary relaxes to the desired condition (Dirichlet in this case), but
when the time-derivatives are large then the boundary approaches Neumann
to reduce discontinuities.

By default, the relaxation rate is set to
<span class="math notranslate nohighlight">\\10\\</span> (i.e. a
time-scale of
<span class="math notranslate nohighlight">\\\tau=0.1\\</span>). To
change this, give the rate as the second argument e.g.
<span class="pre">`relax(dirichlet,`</span>` `<span class="pre">`2)`</span>
would relax to a Dirichlet boundary condition at a rate of
<span class="math notranslate nohighlight">\\2\\</span>.

</div>

<div id="changing-the-width-of-boundaries" class="section">

## Changing the width of boundaries<a href="#changing-the-width-of-boundaries" class="headerlink"
title="Permalink to this heading">#</a>

To change the width of a boundary region, the
<span class="pre">`width`</span> modifier changes the width of a
boundary region before applying the boundary condition, then changes the
width back afterwards. To use, specify the boundary condition and the
width, for example

<div class="highlight-cpp notranslate">

<div class="highlight">

    bndry_core = width( neumann , 4 )

</div>

</div>

would apply a Neumann boundary condition on the innermost 4 cells in the
core, rather than the usual 2. When combining with other boundary
modifiers, this should be applied first e.g.

<div class="highlight-cpp notranslate">

<div class="highlight">

    bndry_sol = width( relax( dirichlet ), 3)

</div>

</div>

would relax the last 3 cells towards zero, whereas

<div class="highlight-cpp notranslate">

<div class="highlight">

    bndry_sol = relax( width( dirichlet, 3) )

</div>

</div>

would only apply to the usual 2, since relax didn’t use the updated
width.

Limitations:

1.  Because it modifies then restores a globally-used BoundaryRegion,
    this code is not thread safe.

2.  Boundary conditions can’t be applied across processors, and no
    checks are done that the width asked for fits within a single
    processor.

</div>

<div id="examples" class="section">

## Examples<a href="#examples" class="headerlink"
title="Permalink to this heading">#</a>

This example is taken from the UEDGE benchmark test (in
<span class="pre">`examples/uedge-benchmark`</span>):

<div class="highlight-cfg notranslate">

<div class="highlight">

    [All]
    bndry_all = neumann # Default for all variables, boundaries

    [Ni]
    bndry_target = neumann
    bndry_core = relax(dirichlet(1.))   # 1e13 cm^-3 on core boundary
    bndry_all  = relax(dirichlet(0.1))  # 1e12 cm^-3 on other boundaries

    [Vi]
    bndry_ydown = relax(dirichlet(-1.41648))   # -3.095e4/Vi_x
    bndry_yup   = relax(dirichlet( 1.41648))

</div>

</div>

The variable <span class="pre">`Ni`</span> (density) is set to a Neumann
boundary condition on the targets (yup and ydown), relaxes towards
<span class="math notranslate nohighlight">\\1\\</span> on the core
boundary, and relaxes to
<span class="math notranslate nohighlight">\\0.1\\</span> on all other
boundaries. Note that the
<span class="pre">`bndry_target`</span>` `<span class="pre">`=`</span>` `<span class="pre">`neumann`</span>
needs to be in the <span class="pre">`Ni`</span> section: If we just had

<div class="highlight-cfg notranslate">

<div class="highlight">

    [All]
    bndry_all = neumann # Default for all variables, boundaries

    [Ni]
    bndry_core = relax(dirichlet(1.))   # 1e13 cm^-3 on core boundary
    bndry_all  = relax(dirichlet(0.1))  # 1e12 cm^-3 on other boundaries

</div>

</div>

then the “target” boundary condition for <span class="pre">`Ni`</span>
would first search in the <span class="pre">`[Ni]`</span> section for
<span class="pre">`bndry_target`</span>, then for
<span class="pre">`bndry_all`</span> in the
<span class="pre">`[Ni]`</span> section. This is set to
<span class="pre">`relax(dirichlet(0.1))`</span>, not the Neumann
condition desired.

</div>

<div id="boundary-regions" class="section">

<span id="sec-boundaryregion"></span>

## Boundary regions<a href="#boundary-regions" class="headerlink"
title="Permalink to this heading">#</a>

The boundary condition code needs ways to loop over the boundary
regions, without needing to know the details of the mesh.

At the moment two mechanisms are provided: A RangeIterator over upper
and lower Y boundaries, and a vector of BoundaryRegion objects.

<div class="highlight-cpp notranslate">

<div class="highlight">

    // Boundary region iteration
    virtual const RangeIterator iterateBndryLowerY() const = 0;
    virtual const RangeIterator iterateBndryUpperY() const = 0;

    bool hasBndryLowerY();
    bool hasBndryUpperY();

    bool BoundaryOnCell; // NB: DOESN'T REALLY BELONG HERE

</div>

</div>

The
<a href="../_breathe_autogen/file/range_8hxx.html#_CPPv413RangeIterator"
class="reference internal" title="RangeIterator"><span class="pre"><code
class="sourceCode cpp">RangeIterator</code></span></a> class is an
iterator which allows looping over a set of indices. For example, in
<span class="pre">`src/solver/solver.cxx`</span> to loop over the upper
Y boundary of a 2D variable <span class="pre">`var`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    for(RangeIterator xi = mesh->iterateBndryUpperY(); !xi.isDone(); xi++) {
      ...
    }

</div>

</div>

The <a
href="../_breathe_autogen/file/boundary__region_8hxx.html#_CPPv414BoundaryRegion"
class="reference internal" title="BoundaryRegion"><span
class="pre"><code
class="sourceCode cpp">BoundaryRegion</code></span></a> class is defined
in <span class="pre">`include/boundary_region.hxx`</span>

</div>

<div id="id1" class="section">

## Boundary regions<a href="#id1" class="headerlink"
title="Permalink to this heading">#</a>

Different regions of the boundary such as “core”, “sol” etc. are
labelled by the
<a href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv44Mesh"
class="reference internal" title="Mesh"><span class="pre"><code
class="sourceCode cpp">Mesh</code></span></a> class (i.e.
<a href="../_breathe_autogen/file/boutmesh_8hxx.html#_CPPv48BoutMesh"
class="reference internal" title="BoutMesh"><span class="pre"><code
class="sourceCode cpp">BoutMesh</code></span></a>), which implements a
member function defined in <span class="pre">`mesh.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    // Boundary regions
    virtual vector<BoundaryRegion*> getBoundaries() = 0;

</div>

</div>

This returns a vector of pointers to <a
href="../_breathe_autogen/file/boundary__region_8hxx.html#_CPPv414BoundaryRegion"
class="reference internal" title="BoundaryRegion"><span
class="pre"><code
class="sourceCode cpp">BoundaryRegion</code></span></a> objects, each of
which describes a boundary region with a label, a
<span class="pre">`BndryLoc`</span> location (i.e. inner x, outer x,
lower y, upper y or all), and iterator functions for looping over the
points. This class is defined in
<span class="pre">`boundary_region.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    /// Describes a region of the boundary, and a means of iterating over it
    class BoundaryRegion {
      public:
      BoundaryRegion();
      BoundaryRegion(const string &name, int xd, int yd);
      virtual ~BoundaryRegion();

      string label; // Label for this boundary region

      BndryLoc location; // Which side of the domain is it on?

      int x,y; // Indices of the point in the boundary
      int bx, by; // Direction of the boundary [x+dx][y+dy] is going outwards

      virtual void first() = 0;
      virtual void next() = 0; // Loop over every element from inside out (in X or
    Y first)
      virtual void nextX() = 0; // Just loop over X
      virtual void nextY() = 0; // Just loop over Y
      virtual bool isDone() = 0; // Returns true if outside domain. Can use this
    with nested nextX, nextY
    };

</div>

</div>

**Example:** To loop over all points in
<span class="pre">`BoundaryRegion`</span>` `<span class="pre">`*bndry`</span>
, use

<div class="highlight-cpp notranslate">

<div class="highlight">

    for(bndry->first(); !bndry->isDone(); bndry->next()) {
      ...
    }

</div>

</div>

Inside the loop, <span class="pre">`bndry->x`</span> and
<span class="pre">`bndry->y`</span> are the indices of the point, whilst
<span class="pre">`bndry->bx`</span> and
<span class="pre">`bndry->by`</span> are unit vectors out of the domain.
The loop is over all the points from the domain outwards i.e. the point
<span class="pre">`[bndry->x`</span>` `<span class="pre">`-`</span>` `<span class="pre">`bndry->bx][bndry->y`</span>` `<span class="pre">`-`</span>` `<span class="pre">`bndry->by]`</span>
will always be defined.

Sometimes it’s useful to be able to loop over just one direction along
the boundary. To do this, it is possible to use
<span class="pre">`nextX()`</span> or <span class="pre">`nextY()`</span>
rather than <span class="pre">`next()`</span>. It is also possible to
loop over both dimensions using:

<div class="highlight-cpp notranslate">

<div class="highlight">

    for(bndry->first(); !bndry->isDone(); bndry->nextX())
      for(; !bndry->isDone(); bndry->nextY()) {
        ...
      }

</div>

</div>

</div>

<div id="boundary-operations" class="section">

## Boundary operations<a href="#boundary-operations" class="headerlink"
title="Permalink to this heading">#</a>

On each boundary, conditions must be specified for each variable. The
different conditions are imposed by <a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv410BoundaryOp"
class="reference internal" title="BoundaryOp"><span class="pre"><code
class="sourceCode cpp">BoundaryOp</code></span></a> objects. These set
the values in the boundary region such that they obey e.g. Dirichlet or
Neumann conditions. The <a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv410BoundaryOp"
class="reference internal" title="BoundaryOp"><span class="pre"><code
class="sourceCode cpp">BoundaryOp</code></span></a> class is defined in
<span class="pre">`boundary_op.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    /// An operation on a boundary
    class BoundaryOp {
     public:
      BoundaryOp() {bndry = NULL;}
      BoundaryOp(BoundaryRegion *region)

      // Note: All methods must implement clone, except for modifiers (see below)
      virtual BoundaryOp* clone(BoundaryRegion *region, const list<string> &args);

      /// Apply a boundary condition on field f
      virtual void apply(Field2D &f) = 0;
      virtual void apply(Field3D &f) = 0;

      virtual void apply(Vector2D &f);

      virtual void apply(Vector3D &f);

      /// Apply a boundary condition on ddt(f)
      virtual void apply_ddt(Field2D &f);
      virtual void apply_ddt(Field3D &f);
      virtual void apply_ddt(Vector2D &f);
      virtual void apply_ddt(Vector3D &f);

      BoundaryRegion *bndry;
    };

</div>

</div>

(where the implementations have been removed for clarity). Which has a
pointer to a <a
href="../_breathe_autogen/file/boundary__region_8hxx.html#_CPPv414BoundaryRegion"
class="reference internal" title="BoundaryRegion"><span
class="pre"><code
class="sourceCode cpp">BoundaryRegion</code></span></a> object
specifying which region this boundary is operating on.

Boundary conditions need to be imposed on the initial conditions (after
<a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel4initEb"
class="reference internal" title="PhysicsModel::init"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>init<span class="op">()</span></code></span></a>),
and on the time-derivatives (after <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel3rhsE8BoutReal"
class="reference internal" title="PhysicsModel::rhs"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>rhs<span class="op">()</span></code></span></a>).
The <span class="pre">`apply()`</span> functions are therefore called
during initialisation and given the evolving variables, whilst the
<span class="pre">`apply_ddt`</span> functions are passed the
time-derivatives.

To implement a boundary operation, as a minimum the
<span class="pre">`apply(Field2D)`</span>,
<span class="pre">`apply(Field2D)`</span> and
<span class="pre">`clone()`</span> need to be implemented: By default
the <span class="pre">`apply(Vector)`</span> will call the
<span class="pre">`apply(Field)`</span> functions on each component
individually, and the <span class="pre">`apply_ddt()`</span> functions
just call the <span class="pre">`apply()`</span> functions.

**Example**: Neumann boundary conditions are defined in
<span class="pre">`boundary_standard.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    /// Neumann (zero-gradient) boundary condition
    class BoundaryNeumann : public BoundaryOp {
     public:
      BoundaryNeumann() {}
     BoundaryNeumann(BoundaryRegion *region):BoundaryOp(region) { }
      BoundaryOp* clone(BoundaryRegion *region, const list<string> &args);
      void apply(Field2D &f);
      void apply(Field3D &f);
    };

</div>

</div>

and implemented in <span class="pre">`boundary_standard.cxx`</span>

<div class="highlight-cpp notranslate">

<div class="highlight">

    void BoundaryNeumann::apply(Field2D &f) {
      // Loop over all elements and set equal to the next point in
      for(bndry->first(); !bndry->isDone(); bndry->next())
        f[bndry->x][bndry->y] = f[bndry->x - bndry->bx][bndry->y - bndry->by];
    }

    void BoundaryNeumann::apply(Field3D &f) {
      for(bndry->first(); !bndry->isDone(); bndry->next())
        for(int z= mesh->zstart; z <= mesh->zend;z++)
          f[bndry->x][bndry->y][z] = f[bndry->x - bndry->bx][bndry->y -
    bndry->by][z];
    }

</div>

</div>

This is all that’s needed in this case since there’s no difference
between applying Neumann conditions to a variable and to its
time-derivative, and Neumann conditions for vectors are just Neumann
conditions on each vector component.

To create a boundary condition, we need to give it a boundary region to
operate over:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoundaryRegion *bndry = ...
    BoundaryOp op = new BoundaryOp(bndry);

</div>

</div>

The <span class="pre">`clone`</span> function is used to create boundary
operations given a single object as a template in <a
href="../_breathe_autogen/file/boundary__factory_8hxx.html#_CPPv415BoundaryFactory"
class="reference internal" title="BoundaryFactory"><span
class="pre"><code
class="sourceCode cpp">BoundaryFactory</code></span></a>. This can take
additional arguments as a vector of strings - see explanation in
<a href="#sec-boundaryfactory" class="reference internal"><span
class="std std-ref">Boundary factory</span></a>.

</div>

<div id="boundary-modifiers" class="section">

## Boundary modifiers<a href="#boundary-modifiers" class="headerlink"
title="Permalink to this heading">#</a>

To create more complicated boundary conditions from simple ones (such as
Neumann conditions above), boundary operations can be modified by
wrapping them up in a <a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv416BoundaryModifier"
class="reference internal" title="BoundaryModifier"><span
class="pre"><code
class="sourceCode cpp">BoundaryModifier</code></span></a> object,
defined in <span class="pre">`boundary_op.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class BoundaryModifier : public BoundaryOp {
     public:
      virtual BoundaryOp* clone(BoundaryOp *op, const list<string> &args) = 0;
     protected:
      BoundaryOp *op;
    };

</div>

</div>

Since <a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv416BoundaryModifier"
class="reference internal" title="BoundaryModifier"><span
class="pre"><code
class="sourceCode cpp">BoundaryModifier</code></span></a> inherits from
<a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv410BoundaryOp"
class="reference internal" title="BoundaryOp"><span class="pre"><code
class="sourceCode cpp">BoundaryOp</code></span></a>, modified boundary
operations are just a different boundary operation and can be treated
the same (Decorator pattern). Boundary modifiers could also be nested
inside each other to create even more complicated boundary operations.
Note that the <span class="pre">`clone`</span> function is different to
the <a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv410BoundaryOp"
class="reference internal" title="BoundaryOp"><span class="pre"><code
class="sourceCode cpp">BoundaryOp</code></span></a> one: instead of a <a
href="../_breathe_autogen/file/boundary__region_8hxx.html#_CPPv414BoundaryRegion"
class="reference internal" title="BoundaryRegion"><span
class="pre"><code
class="sourceCode cpp">BoundaryRegion</code></span></a> to operate on,
modifiers are passed a <a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv410BoundaryOp"
class="reference internal" title="BoundaryOp"><span class="pre"><code
class="sourceCode cpp">BoundaryOp</code></span></a> to modify.

Currently the only modifier is <a
href="../_breathe_autogen/file/boundary__standard_8hxx.html#_CPPv413BoundaryRelax"
class="reference internal" title="BoundaryRelax"><span class="pre"><code
class="sourceCode cpp">BoundaryRelax</code></span></a>, defined in
<span class="pre">`boundary_standard.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    /// Convert a boundary condition to a relaxing one
    class BoundaryRelax : public BoundaryModifier {
     public:
      BoundaryRelax(BoutReal rate) {r = fabs(rate);}
      BoundaryOp* clone(BoundaryOp *op, const list<string> &args);

      void apply(Field2D &f);
      void apply(Field3D &f);

      void apply_ddt(Field2D &f);
      void apply_ddt(Field3D &f);
     private:
      BoundaryRelax() {} // Must be initialised with a rate
      BoutReal r;
    };

</div>

</div>

</div>

<div id="boundary-factory" class="section">

<span id="sec-boundaryfactory"></span>

## Boundary factory<a href="#boundary-factory" class="headerlink"
title="Permalink to this heading">#</a>

The boundary factory creates new boundary operations from input strings,
for example turning “relax(dirichlet)” into a relaxing Dirichlet
boundary operation on a given region. It is defined in
<span class="pre">`boundary_factory.hxx`</span> as a Singleton, so to
get a pointer to the boundary factory use

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoundaryFactory *bfact = BoundaryFactory::getInstance();

</div>

</div>

and to delete this singleton, free memory and clean-up at the end use:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoundaryFactory::cleanup();

</div>

</div>

Because users should be able to add new boundary conditions during <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel4initEb"
class="reference internal" title="PhysicsModel::init"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>init<span class="op">()</span></code></span></a>,
boundary conditions are not hard-wired into <a
href="../_breathe_autogen/file/boundary__factory_8hxx.html#_CPPv415BoundaryFactory"
class="reference internal" title="BoundaryFactory"><span
class="pre"><code
class="sourceCode cpp">BoundaryFactory</code></span></a>. Instead,
boundary conditions must be registered with the factory, passing an
instance which can later be cloned. This is done in
<span class="pre">`bout++.cxx`</span> for the standard boundary
conditions:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoundaryFactory* bndry = BoundaryFactory::getInstance();
    bndry->add(new BoundaryDirichlet(), "dirichlet");
    ...
    bndry->addMod(new BoundaryRelax(10.), "relax");

</div>

</div>

where the <span class="pre">`add`</span> function adds BoundaryOp
objects, whereas <span class="pre">`addMod`</span> adds <a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv416BoundaryModifier"
class="reference internal" title="BoundaryModifier"><span
class="pre"><code
class="sourceCode cpp">BoundaryModifier</code></span></a> objects.
**Note**: The objects passed to <a
href="../_breathe_autogen/file/boundary__factory_8hxx.html#_CPPv415BoundaryFactory"
class="reference internal" title="BoundaryFactory"><span
class="pre"><code
class="sourceCode cpp">BoundaryFactory</code></span></a> will be deleted
when <span class="pre">`cleanup()`</span> is called.

When a boundary operation is added, it is given a name such as
“dirichlet”, and similarly for the modifiers (“relax” above). These
labels and object pointers are stored internally in <a
href="../_breathe_autogen/file/boundary__factory_8hxx.html#_CPPv415BoundaryFactory"
class="reference internal" title="BoundaryFactory"><span
class="pre"><code
class="sourceCode cpp">BoundaryFactory</code></span></a> in maps defined
in <span class="pre">`boundary_factory.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    // Database of available boundary conditions and modifiers
    map<string, BoundaryOp*> opmap;
    map<string, BoundaryModifier*> modmap;

</div>

</div>

These are then used by <a
href="../_breathe_autogen/file/boundary__factory_8hxx.html#_CPPv4N15BoundaryFactory6createERKNSt6stringEP18BoundaryRegionBase"
class="reference internal" title="BoundaryFactory::create"><span
class="pre"><code
class="sourceCode cpp">BoundaryFactory<span class="op">::</span>create<span class="op">()</span></code></span></a>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    /// Create a boundary operation object
    BoundaryOp* create(const string &name, BoundaryRegion *region);
    BoundaryOp* create(const char* name, BoundaryRegion *region);

</div>

</div>

to turn a string such as “relax(dirichlet)” and a <a
href="../_breathe_autogen/file/boundary__region_8hxx.html#_CPPv414BoundaryRegion"
class="reference internal" title="BoundaryRegion"><span
class="pre"><code
class="sourceCode cpp">BoundaryRegion</code></span></a> pointer into a
<a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv410BoundaryOp"
class="reference internal" title="BoundaryOp"><span class="pre"><code
class="sourceCode cpp">BoundaryOp</code></span></a> object. These
functions are implemented in
<span class="pre">`boundary_factory.cxx`</span>, starting around line
42. The parsing is done recursively by matching the input string to one
of:

- <span class="pre">`modifier(<expression>,`</span>` `<span class="pre">`arg1,`</span>` `<span class="pre">`...)`</span>

- <span class="pre">`modifier(<expression>)`</span>

- <span class="pre">`operation(arg1,`</span>` `<span class="pre">`...)`</span>

- <span class="pre">`operation`</span>

the <span class="pre">`<expression>`</span> variable is then resolved
into a <a
href="../_breathe_autogen/file/boundary__op_8hxx.html#_CPPv410BoundaryOp"
class="reference internal" title="BoundaryOp"><span class="pre"><code
class="sourceCode cpp">BoundaryOp</code></span></a> object by calling
<span class="pre">`create(<expression>,`</span>` `<span class="pre">`region)`</span>.

When an operator or modifier is found, it is created from the pointer
stored in the <span class="pre">`opmap`</span> or
<span class="pre">`modmap`</span> maps using the
<span class="pre">`clone`</span> method, passing a
<span class="pre">`list<string>`</span> reference containing any
arguments. It’s up to the operation implementation to ensure that the
correct number of arguments are passed, and to parse them into floats or
other types.

**Example**: The Dirichlet boundary condition can take an optional
argument to change the value the boundary’s set to. In
<span class="pre">`boundary_standard.cxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoundaryOp* BoundaryDirichlet::clone(BoundaryRegion *region, const list<string>
    &args) {
      if(!args.empty()) {
        // First argument should be a value
        stringstream ss;
        ss << args.front();

        BoutReal val;
        ss >> val;
        return new BoundaryDirichlet(region, val);
      }
      return new BoundaryDirichlet(region);
    }

</div>

</div>

If no arguments are passed i.e. the string was “dirichlet” or
“dirichlet()” then the <span class="pre">`args`</span> list is empty,
and the default value (0.0) is used. If one or more arguments is used
then the first argument is parsed into a
<a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv48BoutReal"
class="reference internal" title="BoutReal"><span class="pre"><code
class="sourceCode cpp">BoutReal</code></span></a> type and used to
create a new <a
href="../_breathe_autogen/file/boundary__standard_8hxx.html#_CPPv417BoundaryDirichlet"
class="reference internal" title="BoundaryDirichlet"><span
class="pre"><code
class="sourceCode cpp">BoundaryDirichlet</code></span></a> object. If
more arguments are passed then these are just ignored; probably a
warning should be printed.

To set boundary conditions on a field, <a
href="../_breathe_autogen/file/field__data_8hxx.html#_CPPv49FieldData"
class="reference internal" title="FieldData"><span class="pre"><code
class="sourceCode cpp">FieldData</code></span></a> methods are defined
in <span class="pre">`field_data.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    // Boundary conditions
      void setBoundary(const string &name); ///< Set the boundary conditions
      void setBoundary(const string &region, BoundaryOp *op); ///< Manually set
      virtual void applyBoundary() {}
      virtual void applyTDerivBoundary() {};
     protected:
      vector<BoundaryOp*> bndry_op; // Boundary conditions

</div>

</div>

The <a
href="../_breathe_autogen/file/field__data_8hxx.html#_CPPv4N9FieldData11setBoundaryERKNSt6stringE"
class="reference internal" title="FieldData::setBoundary"><span
class="pre"><code
class="sourceCode cpp">FieldData<span class="op">::</span>setBoundary<span class="op">()</span></code></span></a>
method is implemented in <span class="pre">`field_data.cxx`</span>. It
first gets a vector of pointers to <a
href="../_breathe_autogen/file/boundary__region_8hxx.html#_CPPv414BoundaryRegion"
class="reference internal" title="BoundaryRegion"><span
class="pre"><code
class="sourceCode cpp">BoundaryRegion</code></span></a>s from the mesh,
then loops over these calling <a
href="../_breathe_autogen/file/boundary__factory_8hxx.html#_CPPv4N15BoundaryFactory17createFromOptionsERKNSt6stringEP18BoundaryRegionBase"
class="reference internal"
title="BoundaryFactory::createFromOptions"><span class="pre"><code
class="sourceCode cpp">BoundaryFactory<span class="op">::</span>createFromOptions<span class="op">()</span></code></span></a>
for each one and adding the resulting boundary operator to the <a
href="../_breathe_autogen/file/field__data_8hxx.html#_CPPv4N9FieldData8bndry_opE"
class="reference internal" title="FieldData::bndry_op"><span
class="pre"><code
class="sourceCode cpp">FieldData<span class="op">::</span>bndry_op</code></span></a>
vector.

</div>

</div>

<div class="prev-next-area">

<a href="variable_init.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Variable initialisation

</div>

<a href="testing.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Testing

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#boundary-conditions-for-non-orthogonal-grids"
  class="reference internal nav-link">Boundary conditions for
  non-orthogonal grids</a>
- <a href="#parallel-boundary-conditions"
  class="reference internal nav-link">Parallel boundary conditions</a>
  - <a href="#shifted-metric-boundary-conditions"
    class="reference internal nav-link">Shifted metric boundary
    conditions</a>
  - <a href="#aligned-transform-boundary-conditions"
    class="reference internal nav-link">Aligned transform boundary
    conditions</a>
  - <a href="#fci-boundary-conditions"
    class="reference internal nav-link">FCI boundary conditions</a>
- <a href="#relaxing-boundaries"
  class="reference internal nav-link">Relaxing boundaries</a>
- <a href="#changing-the-width-of-boundaries"
  class="reference internal nav-link">Changing the width of boundaries</a>
- <a href="#examples" class="reference internal nav-link">Examples</a>
- <a href="#boundary-regions" class="reference internal nav-link">Boundary
  regions</a>
- <a href="#id1" class="reference internal nav-link">Boundary regions</a>
- <a href="#boundary-operations"
  class="reference internal nav-link">Boundary operations</a>
- <a href="#boundary-modifiers"
  class="reference internal nav-link">Boundary modifiers</a>
- <a href="#boundary-factory" class="reference internal nav-link">Boundary
  factory</a>

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
