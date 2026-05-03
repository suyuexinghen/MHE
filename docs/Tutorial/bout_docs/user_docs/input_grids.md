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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/input_grids.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/input_grids.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/input_grids.rst"
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

# Generating input grids

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#bout-topology" class="reference internal nav-link">BOUT++
  Topology</a>
  - <a href="#basic" class="reference internal nav-link">Basic</a>
  - <a href="#advanced" class="reference internal nav-link">Advanced</a>
  - <a href="#periodic-x-domains"
    class="reference internal nav-link">Periodic X domains</a>
  - <a href="#implementations"
    class="reference internal nav-link">Implementations</a>
- <a href="#d-variables" class="reference internal nav-link">3D
  variables</a>
- <a href="#from-efit-files" class="reference internal nav-link">From EFIT
  files</a>
- <a href="#from-elite-and-gato-files"
  class="reference internal nav-link">From ELITE and GATO files</a>
- <a href="#generating-equilibria"
  class="reference internal nav-link">Generating equilibria</a>
- <a href="#zoidberg-grid-generator"
  class="reference internal nav-link">Zoidberg grid generator</a>
  - <a href="#rectangular-grids"
    class="reference internal nav-link">Rectangular grids</a>
  - <a href="#more-general-grids" class="reference internal nav-link">More
    general grids</a>
  - <a href="#grids-aligned-to-flux-surfaces"
    class="reference internal nav-link">Grids aligned to flux surfaces</a>
  - <a href="#magnetic-fields" class="reference internal nav-link">Magnetic
    fields</a>
    - <a href="#slabs-and-curved-slabs"
      class="reference internal nav-link">Slabs and curved slabs</a>
    - <a href="#straight-stellarator"
      class="reference internal nav-link">Straight stellarator</a>
    - <a href="#g-eqdsk-files" class="reference internal nav-link">G-Eqdsk
      files</a>
    - <a href="#vmec-files" class="reference internal nav-link">VMEC files</a>
  - <a href="#plotting-the-magnetic-field"
    class="reference internal nav-link">Plotting the magnetic field</a>
  - <a href="#creating-poloidal-grids"
    class="reference internal nav-link">Creating poloidal grids</a>
    - <a href="#id1" class="reference internal nav-link">Rectangular grids</a>
    - <a href="#curvilinear-structured-grids"
      class="reference internal nav-link">Curvilinear structured grids</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="generating-input-grids" class="section">

<span id="sec-gridgen"></span>

# Generating input grids<a href="#generating-input-grids" class="headerlink"
title="Permalink to this heading">#</a>

The simulation mesh describes the number and topology of grid points,
the spacing between them, and the coordinate system. For many problems,
a simple mesh can be created using options.

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh]
    nx = 260  # X grid size
    ny = 256  # Y grid size

    dx = 0.1  # X mesh spacing
    dy = 0.1  # Y mesh spacing

</div>

</div>

The above options will create a
<span class="math notranslate nohighlight">\\256\times 256\\</span> mesh
in X and Y, assuming there are 2 guard cells in X direction. The Z
resolution can be specified with MZ. The mesh spacing is
<span class="math notranslate nohighlight">\\0.1\\</span> in both
directions. By default the coordinate system is Cartesian (metric tensor
is the identity matrix), but this can be changed by specifying the
metric tensor components.

Integer quantities such as <span class="pre">`nx`</span> can be numbers
(like “260”), or expressions (like “256 + 2\*MXG”). A common use is to
make <span class="pre">`x`</span> and <span class="pre">`z`</span>
dimensions have the same number of points, when
<span class="pre">`x`</span> has <span class="pre">`mxg`</span> boundary
cells on each boundary but <span class="pre">`z`</span> does not (since
it is usually periodic):

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh]
    nx = nz + 2*mxg  # X grid size
    nz = 256         # Z grid size
    mxg = 2

</div>

</div>

Note that the order of the defintion within a section isn’t important,
variables can be used before they are defined. All variables are first
read, and only processed if they are used.

Expressions are always calculated in floating point; When expressions
are used to set integer quantities (such as the number of grid points),
the expressions are calculated in floating point and then converted to
an integer. The conversion is done by rounding to the nearest integer,
but throws an error if the floating point value is not within 1e-3 of an
integer. This is to minimise unexpected behaviour. If you want to round
any result to the nearest integer, use the
<span class="pre">`round`</span> function:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh]
    nx = 256.4   # Error!
    nx = round(256.4) # ok

</div>

</div>

Real (floating-point) values can also be expressions, allowing quite
complicated analytic inputs. For example in the example
<span class="pre">`test-griddata`</span>:

<div class="highlight-cfg notranslate">

<div class="highlight">

    # Screw pinch

    rwidth = 0.4

    Rxy = 0.1 + rwidth*x  # Radius from axis     [m]
    L   = 10              # Length of the device [m]

    dy = L/ny
    hthe = 1.0

    Zxy = L * y / (2*pi)

    Bpxy = 1.0      # Axial field [T]
    Btxy = 0.1*Rxy  # Azimuthal field [T]
    Bxy = sqrt(Btxy^2 + Bpxy^2)

    dr = rwidth / nx
    dx = dr * Bpxy * Rxy

</div>

</div>

These expressions use the same mechanism as used for variable
initialisation (<a href="variable_init.html#sec-expressions"
class="reference internal"><span
class="std std-ref">Expressions</span></a>):
<span class="pre">`x`</span> is a variable from
<span class="math notranslate nohighlight">\\0\\</span> to
<span class="math notranslate nohighlight">\\1\\</span> in the domain
which is uniform in index space; <span class="pre">`y`</span> and
<span class="pre">`z`</span> go from
<span class="math notranslate nohighlight">\\0\\</span> to
<span class="math notranslate nohighlight">\\2\pi\\</span>. As with
variable initialisation, common trigonometric and mathematical functions
can be used. In the above example, some variables depend on each other,
for example <span class="pre">`dy`</span> depends on
<span class="pre">`L`</span> and <span class="pre">`ny`</span>. The
order in which these variables are defined doesn’t matter, so
<span class="pre">`L`</span> could be defined below
<span class="pre">`dy`</span>, but circular dependencies are not allowed
(by default; see section
<a href="variable_init.html#sec-recursive-functions"
class="reference internal"><span class="std std-ref">Recursive
functions</span></a>). If the variables are defined in the same section
(as <span class="pre">`dy`</span> and <span class="pre">`L`</span>) or a
parent section, then no section prefix is required. To refer to a
variable in a different section, prefix the variable with the section
name, for example, <span class="pre">`section:variable`</span> or
<span class="pre">`mesh:dx`</span>.

More complex meshes can be created by supplying an input grid file to
describe the grid points, geometry, and starting profiles. Currently
BOUT++ supports NetCDF format binary files. During startup, BOUT++ looks
in the grid file for the following variables. If any are not found, a
warning will be printed and the default values used.

- X and Y grid sizes (integers) <span class="pre">`nx`</span> and
  <span class="pre">`ny`</span> **REQUIRED**

- Differencing quantities in 2D/3D arrays
  <span class="pre">`dx(nx,ny[,nz])`</span>,
  <span class="pre">`dy(nx,ny[,nz])`</span> and
  <span class="pre">`dz(nx,ny[,nz])`</span>. If these are not found they
  will be set to 1. To allow variation in <span class="pre">`z`</span>
  direction, BOUT++ has to be configured
  <span class="pre">`-DBOUT_ENABLE_METRIC_3D`</span>, otherwise 2D
  fields are used for the metric fields. Note that prior to BOUT++
  version 5 <span class="pre">`dz`</span> was a constant.

- Diagonal terms of the metric tensor
  <span class="math notranslate nohighlight">\\g^{ij}\\</span>
  <span class="pre">`g11(nx,ny[,nz])`</span>,
  <span class="pre">`g22(nx,ny[,nz])`</span>, and
  <span class="pre">`g33(nx,ny[,nz])`</span>. If not found, these will
  be set to 1.

- Off-diagonal metric tensor
  <span class="math notranslate nohighlight">\\g^{ij}\\</span> elements
  <span class="pre">`g12(nx,ny[,nz])`</span>,
  <span class="pre">`g13(nx,ny[,nz])`</span>, and
  <span class="pre">`g23(nx,ny[,nz])`</span>. If not found, these will
  be set to 0.

- Z shift for interpolation between field-aligned coordinates and
  non-aligned coordinates (see
  <a href="coordinates.html#sec-field-aligned-coordinates"
  class="reference internal"><span class="std std-ref">Field-aligned
  coordinates</span></a>). Parallel differential operators are
  calculated using a shift to field-aligned values when
  <span class="pre">`paralleltransform:type`</span>` `<span class="pre">`=`</span>` `<span class="pre">`shifted`</span>
  (or <span class="pre">`shiftedinterp`</span>). The shifts must be
  provided in the gridfile in a field
  <span class="pre">`zShift(nx,ny)`</span>. If not found,
  <span class="pre">`zShift`</span> is set to zero.

The remaining quantities determine the topology of the grid. These are
based on tokamak single/double-null configurations, but can be adapted
to many other situations.

- Separatrix locations <span class="pre">`ixseps1`</span>, and
  <span class="pre">`ixseps2`</span> If neither is given, both are set
  to nx (i.e. all points in closed “core” region). If only
  <span class="pre">`ixseps1`</span> is found,
  <span class="pre">`ixseps2`</span> is set to nx, and if only ixseps2
  is found, ixseps1 is set to -1.

- Branch-cut locations <span class="pre">`jyseps1_1`</span>,
  <span class="pre">`jyseps1_2`</span>,
  <span class="pre">`jyseps2_1`</span>, and
  <span class="pre">`jyseps2_2`</span>

- Twist-shift matching condition
  <span class="pre">`ShiftAngle[nx]`</span> for field aligned
  coordinates. This is applied in the “core” region between indices
  <span class="pre">`jyseps2_2`</span>, and
  <span class="pre">`jyseps1_1`</span>` `<span class="pre">`+`</span>` `<span class="pre">`1`</span>,
  if either
  <span class="pre">`TwistShift`</span>` `<span class="pre">`=`</span>` `<span class="pre">`True`</span>
  enabled in the options file or in general the
  <span class="pre">`TwistShift`</span> flag in
  <span class="pre">`mesh/impls/bout/boutmesh.hxx`</span> is enabled by
  other means. BOUT++ automatically reads the twist shifts in the
  gridfile if the shifts are stored in a field ShiftAngle\[nx\];
  ShiftAngle must be given in the gridfile or grid-options if
  <span class="pre">`TwistShift`</span>` `<span class="pre">`=`</span>` `<span class="pre">`True`</span>.

The only quantities which are required are the sizes of the grid. If
these are the only quantities specified, then the coordinates revert to
Cartesian.

This section describes how to generate inputs for tokamak equilibria. If
you’re not interested in tokamaks then you can skip to the next section.

The directory <span class="pre">`tokamak_grids`</span> contains code to
generate input grid files for tokamaks. These can be used by, for
example, the <span class="pre">`2fluid`</span> and
<span class="pre">`highbeta_reduced`</span> modules.

<div id="bout-topology" class="section">

<span id="sec-bout-topology"></span>

## BOUT++ Topology<a href="#bout-topology" class="headerlink"
title="Permalink to this heading">#</a>

<div id="basic" class="section">

### Basic<a href="#basic" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ is designed to work in a variety of tokamak and non-tokamak
geometries, from simple slabs to disconnected double-null
configurations. In order to handle tokamak geometry BOUT++ contains an
internal topology which is built from six regions determined by four
branch-cut locations and two separatrix locations
(<span class="pre">`ixseps1`</span> and
<span class="pre">`ixseps2`</span>). There are some limitations on these
regions that we will discuss below, and some regions may be empty, all
of which enables BOUT++ to describe effectively seven types of topology:

- “core”: this type of topology can describe the closed field line
  regions inside the separatrix of tokamaks or other devices, or
  idealised geometries like periodic slabs;

- “SOL”: these can describe the open field line regions of the
  scrape-off layer (SOL) outside the separatrix of a tokamak, or linear
  devices with a target plate at either end;

- “limiter”: these topologies have an open field line region and a
  region where field lines hit a boundary, without an X-point;

- “X-point”: these topologies have four separate legs with their own
  boundaries, and no closed field line region;

- “single null”: this type of topology has one X-point with two separate
  legs, closed and an open field line regions, and a single separatrix;

- “connected double null”: these topologies have two X-points with two
  separate legs each, closed and open field line regions and a single
  separatrix that connects both X-points;

- “disconnected double null”: finally, these are similar to connected
  double null geometries except that they have two separatrices that do
  not connect the two X-points. These come in “lower” and “upper”
  flavours, depending on which X-point is adjacent to the closed field
  line region.

The six regions that form the building blocks of these topologies are:

- four separate “leg” regions that have a boundary in the
  <span class="pre">`y`</span> direction;

- two “core” regions that do not have boundaries in
  <span class="pre">`y`</span>.

Each of these regions may have additional boundaries in the
<span class="pre">`x`</span> direction. The separate regions are
illustrated in <span class="pre">`fig-topology-cross-section`</span>:
the grey dashed lines show the region partitions, with the sections
labelled 1, 2, and 3 forming one leg; 4, 5, and 6 forming one core
region, and so on. The internal names for these separate regions use
“inner” and “outer” in reference to the major radius – that is, “inner”
regions correspond to the left-hand side of
<span class="pre">`fig-topology-cross-section`</span> and “outer”
regions to the right-hand side.

Two important limitations for BOUT++ grids are that a single processor
can only belong to one region, and that there must be the same number of
points on each processor. The first limitation means that certain
topologies require a minimum number of processors. For example, a
disconnected double null configuration uses all six regions – therefore
the minimum number of processors able to describe this in BOUT++ is six.
Having equal numbers of points on each processor can put some
restrictions on the resolution of simulations.

The two separatrix locations are <span class="pre">`ixseps1`</span> and
<span class="pre">`ixseps2`</span>, these are the global indices in the
<span class="pre">`x`</span> domain where the first and second
separatrices are located. These values are set either in the grid file
or in <span class="pre">`BOUT.inp`</span>.
<span class="pre">`fig-topology-cross-section`</span> shows
schematically how <span class="pre">`ixseps`</span> is used.

If
<span class="pre">`ixseps1`</span>` `<span class="pre">`==`</span>` `<span class="pre">`ixseps2`</span>
then there is a single separatrix representing the boundary between the
core region and the SOL region and the grid is a connected double null
configuration. If
<span class="pre">`ixseps1`</span>` `<span class="pre">`>`</span>` `<span class="pre">`ixseps2`</span>
then there are two separatrices and the inner separatrix is
<span class="pre">`ixseps2`</span> so the tokamak is an upper double
null. If
<span class="pre">`ixseps1`</span>` `<span class="pre">`<`</span>` `<span class="pre">`ixseps2`</span>
then there are two separatrices and the inner separatrix is
<span class="pre">`ixseps1`</span> so the tokamak is a lower double
null.

In other words: Let us for illustrative purposes say that
<span class="pre">`ixseps1`</span>` `<span class="pre">`>`</span>` `<span class="pre">`ixseps2`</span>
(see <span class="pre">`fig-topology-cross-section`</span>). Let us say
that we have a field <span class="pre">`f(x,y,z)`</span> with a global
<span class="pre">`x`</span>-index which includes ghost points.
<span class="pre">`f(x`</span>` `<span class="pre">`<=`</span>` `<span class="pre">`ixseps1,`</span>` `<span class="pre">`y,`</span>` `<span class="pre">`z)`</span>)
will then be periodic in the <span class="pre">`y`</span>-direction,
<span class="pre">`f(ixspes1`</span>` `<span class="pre">`<`</span>` `<span class="pre">`x`</span>` `<span class="pre">`<=`</span>` `<span class="pre">`ixseps2,`</span>` `<span class="pre">`y,`</span>` `<span class="pre">`z)`</span>)
will have boundary condition in the
<span class="pre">`y`</span>-direction set by the lowermost
<span class="pre">`ydown`</span> and <span class="pre">`yup`</span>. If
<span class="pre">`f(ixspes2`</span>` `<span class="pre">`<`</span>` `<span class="pre">`x,`</span>` `<span class="pre">`y,`</span>` `<span class="pre">`z)`</span>)
the boundary condition in the <span class="pre">`y`</span>-direction
will be set by the uppermost <span class="pre">`ydown`</span> and
<span class="pre">`yup`</span>. As for now, there is no difference
between the two sets of upper and lower <span class="pre">`ydown`</span>
and <span class="pre">`yup`</span> boundary conditions (unless manually
specified, see <a href="physics_models.html#sec-custom-bc"
class="reference internal"><span class="std std-ref">Custom boundary
conditions</span></a>).

The four branch cut locations, <span class="pre">`jyseps1_1`</span>,
<span class="pre">`jyseps1_2`</span>,
<span class="pre">`jyseps2_1`</span>, and
<span class="pre">`jyseps2_2`</span>, split the
<span class="pre">`y`</span> domain into logical regions defining the
SOL, the PFR (private flux region) and the core of the tokamak. This is
illustrated also in
<span class="pre">`fig-topology-cross-section`</span>. If
<span class="pre">`jyseps1_2`</span>` `<span class="pre">`==`</span>` `<span class="pre">`jyseps2_1`</span>
then the grid is a single null configuration, otherwise the grid is a
double null configuration.

<figure id="id2" class="align-default">
<span id="fig-topology-cross-section"></span><img
src="../_images/topology_cross_section.svg"
alt="Cross-section of the tokamak topology used in BOUT++" />
<figcaption><p><span class="caption-number">Fig. 5 </span><span
class="caption-text">Deconstruction of a poloidal tokamak cross-section
into logical domains using the parameters <span class="pre"><code
class="docutils literal notranslate">ixseps1</code></span>, <span
class="pre"><code
class="docutils literal notranslate">ixseps2</code></span>, <span
class="pre"><code
class="docutils literal notranslate">jyseps1_1</code></span>, <span
class="pre"><code
class="docutils literal notranslate">jyseps1_2</code></span>, <span
class="pre"><code
class="docutils literal notranslate">jyseps2_1</code></span>, and <span
class="pre"><code
class="docutils literal notranslate">jyseps2_2</code></span>. This
configuration is a “disconnected double null” and shows all the possible
regions used in the BOUT++ topology.</span><a href="#id2"
class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

<div id="advanced" class="section">

### Advanced<a href="#advanced" class="headerlink"
title="Permalink to this heading">#</a>

The internal domain in BOUT++ is deconstructed into a series of
logically rectangular sub-domains with boundaries determined by the
<span class="pre">`ixseps`</span> and <span class="pre">`jyseps`</span>
parameters. The boundaries coincide with processor boundaries so the
number of grid points within each sub-domain must be an integer multiple
of <span class="pre">`ny/nypes`</span> where
<span class="pre">`ny`</span> is the number of grid points in
<span class="pre">`y`</span> and <span class="pre">`nypes`</span> is the
number of processors used to split the y domain. Processor communication
across the domain boundaries is then handled internally.
<span class="pre">`fig-topology-schematic`</span> shows schematically
how the different regions of a double null tokamak with
<span class="pre">`ixseps1`</span>` `<span class="pre">`=`</span>` `<span class="pre">`ixseps2`</span>
are connected together via communications.

<div class="admonition note">

Note

To ensure that each subdomain follows logically, the
<span class="pre">`jyseps`</span> indices must adhere to the following
conditions:

> <div>
>
> - <span class="pre">`jyseps1_1`</span>` `<span class="pre">`>`</span>` `<span class="pre">`-1`</span>
>
> - <span class="pre">`jyseps2_1`</span>` `<span class="pre">`>=`</span>` `<span class="pre">`jyseps1_1`</span>` `<span class="pre">`+`</span>` `<span class="pre">`1`</span>
>
> - <span class="pre">`jyseps1_2`</span>` `<span class="pre">`>=`</span>` `<span class="pre">`jyseps2_1`</span>
>
> - <span class="pre">`jyseps2_2`</span>` `<span class="pre">`>=`</span>` `<span class="pre">`jyseps1_2`</span>
>
> - <span class="pre">`jyseps2_2`</span>` `<span class="pre">`<=`</span>` `<span class="pre">`ny`</span>` `<span class="pre">`-`</span>` `<span class="pre">`1`</span>
>
> </div>

To ensure that communications work branch cuts must align with processor
boundaries.

</div>

<figure id="id3" class="align-default">
<span id="fig-topology-schematic"></span><img
src="../_images/topology_schematic.svg"
alt="../_images/topology_schematic.svg" />
<figcaption><p><span class="caption-number">Fig. 6 </span><span
class="caption-text">Schematic illustration of domain decomposition and
communication in BOUT++ with <span class="pre"><code
class="docutils literal notranslate">ixseps1</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">=</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">ixseps2</code></span></span><a
href="#id3" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

<div id="periodic-x-domains" class="section">

### Periodic X domains<a href="#periodic-x-domains" class="headerlink"
title="Permalink to this heading">#</a>

The <span class="math notranslate nohighlight">\\x\\</span> coordinate
is usually a radial flux coordinate. In some simulations it is useful to
make this direction periodic, for example flux tube simulations or the
Hasegawa-Wakatani example in
<span class="pre">`examples/hasegawa-wakatani/hw.cxx`</span>. In that
example the <span class="math notranslate nohighlight">\\x\\</span>
coordinate is made periodic with the top-level
<span class="pre">`periodicX`</span> option:

<div class="highlight-cfg notranslate">

<div class="highlight">

    periodicX = true # Domain is periodic in X

    [mesh]

    nx = 260  # Note 4 guard cells in X
    ny = 1
    nz = 256  # Periodic, so no guard cells in Z

</div>

</div>

Note that some care is now needed if the model uses Laplacian
inversions, for example to calculate electrostatic potential from
vorticity: If both
<span class="math notranslate nohighlight">\\x\\</span> and
<span class="math notranslate nohighlight">\\z\\</span> coordinates are
both periodic then the inversion has no boundary conditions. In that
case the laplacian has a null space and so is singular; an arbitrary
constant offset can be added to the potential without changing the
vorticity.

The default <span class="pre">`cyclic`</span> solver treats the
<span class="math notranslate nohighlight">\\k_z = 0\\</span> (DC) mode
as a special case, setting the average of the potential over the
<span class="math notranslate nohighlight">\\x-z\\</span> domain to
zero. Other solvers may not handle the
<span class="pre">`periodicX`</span> case in the same way.

</div>

<div id="implementations" class="section">

### Implementations<a href="#implementations" class="headerlink"
title="Permalink to this heading">#</a>

In BOUT++ each processor has a logically rectangular domain, so any
branch cuts needed for X-point geometry (see
<span class="pre">`fig-topology-schematic`</span>) must be at processor
boundaries.

In the standard “bout” mesh
(<span class="pre">`src/mesh/impls/bout/`</span>), the communication is
controlled by the variables

<div class="highlight-cpp notranslate">

<div class="highlight">

    int UDATA_INDEST, UDATA_OUTDEST, UDATA_XSPLIT;
    int DDATA_INDEST, DDATA_OUTDEST, DDATA_XSPLIT;
    int IDATA_DEST, ODATA_DEST;

</div>

</div>

These control the behavior of the communications as shown in
<span class="pre">`fig-boutmesh-comms`</span>.

<figure id="id4" class="align-default">
<span id="fig-boutmesh-comms"></span><img
src="../_images/boutmesh-comms.png"
alt="Communication of guard cells in BOUT++" />
<figcaption><p><span class="caption-number">Fig. 7 </span><span
class="caption-text">Communication of guard cells in BOUT++. Boundaries
in X have only one neighbour each, but boundaries in Y can be split into
two, allowing branch cuts</span><a href="#id4" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

In the Y direction, each boundary region (**U**p and **D**own in Y) can
be split into two, with
<span class="pre">`0`</span>` `<span class="pre">`<=`</span>` `<span class="pre">`x`</span>` `<span class="pre">`<`</span>` `<span class="pre">`UDATA_XSPLIT`</span>
going to the processor index <span class="pre">`UDATA_INDEST`</span>,
and
<span class="pre">`UDATA_INDEST`</span>` `<span class="pre">`<=`</span>` `<span class="pre">`x`</span>` `<span class="pre">`<`</span>` `<span class="pre">`LocalNx`</span>
going to <span class="pre">`UDATA_OUTDEST`</span>. Similarly for the
Down boundary. Since there are no branch-cuts in the X direction, there
is just one destination for the **I**nner and **O**uter boundaries. In
all cases a negative processor number means that there’s a domain
boundary so no communication is needed.

The communication control variables are set in the <a
href="../_breathe_autogen/file/boutmesh_8hxx.html#_CPPv4N8BoutMesh8topologyEv"
class="reference internal" title="BoutMesh::topology"><span
class="pre"><code
class="sourceCode cpp">BoutMesh<span class="op">::</span>topology<span class="op">()</span></code></span></a>
function, in
<span class="pre">`src/mesh/impls/bout/boutmesh.cxx`</span>. First the
function <span class="pre">`default_connections`</span> sets the
topology to be a rectangle.

To change the topology, the function <a
href="../_breathe_autogen/file/boutmesh_8hxx.html#_CPPv4N8BoutMesh14set_connectionEiiiib"
class="reference internal" title="BoutMesh::set_connection"><span
class="pre"><code
class="sourceCode cpp">BoutMesh<span class="op">::</span>set_connection<span class="op">()</span></code></span></a>
checks that the requested branch cut is on a processor boundary, and
changes the communications consistently so that communications are
two-way and there are no “dangling” communications.

</div>

</div>

<div id="d-variables" class="section">

## 3D variables<a href="#d-variables" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ was originally designed for tokamak simulations where the input
equilibrium varies only in X-Y, and Z is used as the axisymmetric
toroidal angle direction. In those cases, it is often convenient to have
input grids which are only 2D, and allow the Z dimension to be specified
independently, such as in the options file. The problem then is how to
store 3D variables in the grid file?

Two representations are now supported for 3D variables:

1.  A Fourier representation. If the size of the toroidal domain is not
    specified in the grid file (<span class="pre">`nz`</span> is not
    defined), then 3D fields are stored as Fourier components. In the Z
    dimension the coefficients must be stored as

    <div class="math notranslate nohighlight">

    \\\[n = 0, n = 1 (\textrm{real}), n = 1 (\textrm{imag}), n = 2
    (\textrm{real}), n = 2 (\textrm{imag}), \ldots \]\\

    </div>

    where <span class="math notranslate nohighlight">\\n\\</span> is the
    toroidal mode number. The size of the array must therefore be odd in
    the Z dimension, to contain a constant
    (<span class="math notranslate nohighlight">\\n=0\\</span>)
    component followed by real/imaginary pairs for the non-axisymmetric
    components.

    If you are using IDL to create a grid file, there is a routine in
    <span class="pre">`tools/idllib/bout3dvar.pro`</span> for converting
    between BOUT++’s real and Fourier representation.

2.  Real space, as values on grid points. If
    <span class="pre">`nz`</span> is set in the grid file, then 3D
    variables in the grid file must have size
    <span class="pre">`nx`</span><span class="math notranslate nohighlight">\\\times\\</span><span class="pre">`ny`</span><span class="math notranslate nohighlight">\\\times\\</span><span class="pre">`nz`</span>.
    These are then read in directly into
    <a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
    class="reference internal" title="Field3D"><span class="pre"><code
    class="sourceCode cpp">Field3D</code></span></a> variables as
    required.

</div>

<div id="from-efit-files" class="section">

## From EFIT files<a href="#from-efit-files" class="headerlink"
title="Permalink to this heading">#</a>

A separate tool (in python) called
<a href="https://github.com/boutproject/hypnotoad"
class="reference external">Hypnotoad</a> has been developed to create
BOUT++ input files from R-Z equilibria. This can read EFIT ’g’ (geqdsk)
files, find flux surfaces, and calculate metric coefficients.

</div>

<div id="from-elite-and-gato-files" class="section">

## From ELITE and GATO files<a href="#from-elite-and-gato-files" class="headerlink"
title="Permalink to this heading">#</a>

Currently conversions exist for ELITE <span class="pre">`.eqin`</span>
and GATO <span class="pre">`dskgato`</span> equilibrium files.
Conversion of these into BOUT++ input grids is in two stages: In the
first, both these input files are converted into a common NetCDF format
which describes the Grad-Shafranov equilibrium. These intermediate files
are then converted to BOUT++ grids using an interactive IDL script.

</div>

<div id="generating-equilibria" class="section">

## Generating equilibria<a href="#generating-equilibria" class="headerlink"
title="Permalink to this heading">#</a>

The directory <span class="pre">`tokamak_grids/shifted_circle`</span>
contains IDL code to generate shifted circle (large aspect ratio)
Grad-Shafranov equilibria.

<figure id="id5" class="align-default">
<img src="../_images/grid_gen.png"
alt="IDL routines and file formats used in taking output from different codes and converting into input to BOUT++." />
<figcaption><p><span class="caption-number">Fig. 8 </span><span
class="caption-text">IDL routines and file formats used in taking output
from different codes and converting into input to BOUT++.</span><a
href="#id5" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

<div id="zoidberg-grid-generator" class="section">

<span id="sec-zoidberg"></span>

## Zoidberg grid generator<a href="#zoidberg-grid-generator" class="headerlink"
title="Permalink to this heading">#</a>

The <a href="https://github.com/boutproject/zoidberg"
class="reference external">Zoidberg</a> grid generator creates inputs
for the Flux Coordinate Independent (FCI) parallel transform (section
<a href="parallel-transforms.html#sec-parallel-transforms"
class="reference internal"><span class="std std-ref">Parallel
Transforms</span></a>). The domain is divided into a set of 2D grids in
the X-Z coordinates, and the magnetic field is followed along the Y
coordinate from each 2D grid to where it either intersects the forward
and backward grid, or hits a boundary.

A simple code which creates an output file is:

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg

    # Define the magnetic field
    field = zoidberg.field.Slab()
    # Define the grid points
    grid = zoidberg.grid.rectangular_grid(10,10,10)
    # Follow magnetic fields from each point
    maps = zoidberg.make_maps(grid, field)
    # Write everything to file - with default option for gridfile and metric2d
    zoidberg.write_maps(grid, field, maps, gridfile="grid.fci.nc", metric2d=True)

</div>

</div>

As in the above code, creating an output file consists of the following
steps:

1.  Define a magnetic field

2.  Define the grid points. This can be broken down into:

    1.  Define 2D “poloidal” grids

    2.  Form a 3D grid by putting 2D grids together along the Y
        direction

3.  Create maps from each 2D grid to its neighbours

4.  Save grids, fields and maps to file

Each of these stages can be customised to handle more complicated
magnetic fields, more complicated grids, and particular output formats.
Details of the functionality available are described in sections below,
and there are several examples in the
<span class="pre">`examples/zoidberg`</span> directory.

<div id="rectangular-grids" class="section">

### Rectangular grids<a href="#rectangular-grids" class="headerlink"
title="Permalink to this heading">#</a>

An important input to Zoidberg is the size of the domain in Y, and
whether the domain is periodic in Y. By default
<span class="pre">`rectangular_grid`</span> makes a non-periodic
rectangular box which is of length 10 in the Y direction. This means
that there are boundaries at
<span class="math notranslate nohighlight">\\y=0\\</span> and at
<span class="math notranslate nohighlight">\\y=10\\</span>.
<span class="pre">`rectangular_grid`</span> puts the y slices at equally
spaced intervals, and puts the first and last points half an interval
away from boundaries in y. In this case with 10 points in y (second
argument to <span class="pre">`rectangular_grid(nx,ny,nz)`</span>) the y
locations are <span class="math notranslate nohighlight">\\\left(0.5,
1.5, 2.5, \ldots, 9.5\right)\\</span>.

At each of these y locations <span class="pre">`rectangular_grid`</span>
defines a rectangular 2D poloidal grid in the X-Z coordinates, by
default with a length of 1 in each direction and centred on
<span class="math notranslate nohighlight">\\x=0,z=0\\</span>. These 2D
poloidal grids are then put together into a 3D
<span class="pre">`Grid`</span>. This process can be customised by
separating step 2 (the <span class="pre">`rectangular_grid`</span> call)
into stages 2a) and 2b). For example, to create a periodic rectangular
grid we could use the following:

<div class="highlight-python notranslate">

<div class="highlight">

    import numpy as np

    # Create a 10x10 grid in X-Z with sides of length 1
    poloidal_grid = zoidberg.poloidal_grid.RectangularPoloidalGrid(10, 10, 1.0, 1.0)
    # Define the length of the domain in y
    ylength = 10.0
    # Define the y locations
    ycoords = np.linspace(0.0, ylength, 10, endpoint=False)
    # Create the 3D grid by putting together 2D poloidal grids
    grid = zoidberg.grid.Grid(poloidal_grid, ycoords, ylength, yperiodic=True)

</div>

</div>

In the above code the length of the domain in the y direction needs to
be given to <span class="pre">`Grid`</span> so that it knows where to
put boundaries (if not periodic), or where to wrap the domain (if
periodic). The array of y locations ycoords can be arbitrary, but note
that finite difference methods (like FCI) work best if grid point
spacing varies smoothly.

A more realistic example is creating a grid for a MAST tokamak
equilibrium from a G-Eqdsk input file (this is in
<span class="pre">`examples/zoidberg/tokamak.py`</span>):

<div class="highlight-python notranslate">

<div class="highlight">

    import numpy as np
    import zoidberg

    field = zoidberg.field.GEQDSK("g014220.00200") # Read magnetic field

    grid = zoidberg.grid.rectangular_grid(100, 10, 100,
           1.5-0.1, # Range in R (max - min)
           2*np.pi, # Toroidal angle
           3., # Range in Z
           xcentre=(1.5+0.1)/2, # Middle of grid in R
           yperiodic=True) # Periodic in toroidal angle

    # Create the forward and backward maps
    maps = zoidberg.make_maps(grid, field)

    # Save to file
    zoidberg.write_maps(grid, field, maps, gridfile="grid.fci.nc")

    # Plot grid points and the points they map to in the forward direction
    zoidberg.plot.plot_forward_map(grid, maps)

</div>

</div>

In the last example only one poloidal grid was created (a
<span class="pre">`RectangularPoloidalGrid`</span>) and then re-used for
each y slice. We can instead define a different grid for each y
position. For example, to define a grid which expands along y (for some
reason) we could do:

<div class="highlight-python notranslate">

<div class="highlight">

    ylength = 10.0
    ycoords = np.linspace(0.0, ylength, 10, endpoint=False)
    # Create a list of poloidal grids, one for each y location
    poloidal_grids = [ RectangularPoloidalGrid(10, 10, 1.0 + y/10., 1.0 + y/10.)
                       for y in ycoords ]
    # Create the 3D grid by putting together 2D poloidal grids
    grid = zoidberg.grid.Grid(poloidal_grids, ycoords, ylength, yperiodic=True)

</div>

</div>

Note: Currently there is an assumption that the number of X and Z points
is the same on every poloidal grid. The shape of the grid can however be
completely different. The construction of a 3D
<span class="pre">`Grid`</span> is the same in all cases, so for now we
will concentrate on producing different poloidal grids.

</div>

<div id="more-general-grids" class="section">

### More general grids<a href="#more-general-grids" class="headerlink"
title="Permalink to this heading">#</a>

The FCI technique is not restricted to rectangular grids, and in
particular Zoidberg can handle structured grids in an annulus with quite
complicated shapes. The
<span class="pre">`StructuredPoloidalGrid`</span> class handles quite
general geometries, but still assumes that the grid is structured and
logically rectangular. Currently it also assumes that the z index is
periodic.

One way to create this grid is to define the grid points manually e.g.:

<div class="highlight-python notranslate">

<div class="highlight">

    import numpy as np
    import zoidberg

    # First argument is minor radius, second is angle
    r,theta = np.meshgrid(np.linspace(1,2,10),
                          np.linspace(0,2*np.pi, 10),
                          indexing="ij")

    R = r * np.sin(theta)
    Z = r * np.cos(theta)

    poloidal_grid = zoidberg.poloidal_grid.StructuredPoloidalGrid(R,Z)

</div>

</div>

For more complicated shapes than circles, Zoidberg comes with an
elliptic grid generator which needs to be given only the inner and outer
boundaries:

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg

    inner = zoidberg.rzline.shaped_line(R0=3.0, a=0.5,
                             elong=1.0, triang=0.0, indent=1.0,
                             n=50)

    outer = zoidberg.rzline.shaped_line(R0=2.8, a=1.5,
                             elong=1.0, triang=0.0, indent=0.2,
                             n=50)

    poloidal_grid = zoidberg.poloidal_grid.grid_elliptic(inner, outer,
                                                  100, 100, show=True)

</div>

</div>

which should produce the figure below:

<figure id="elliptic" class="align-default">
<a href="../_images/elliptic_grid.png"
class="reference internal image-reference"><img
src="../_images/elliptic_grid.png"
style="width: 425.5px; height: 446.0px;" /></a>
<figcaption><p><span class="caption-number">Fig. 9 </span><span
class="caption-text">A grid produced by <span class="pre"><code
class="docutils literal notranslate">grid_elliptic</code></span> from
shaped inner and outer lines</span><a href="#elliptic"
class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

<div id="grids-aligned-to-flux-surfaces" class="section">

### Grids aligned to flux surfaces<a href="#grids-aligned-to-flux-surfaces" class="headerlink"
title="Permalink to this heading">#</a>

The elliptic grid generator can be used to generate grids whose inner
and/or outer boundaries align with magnetic flux surfaces. All it needs
is two <span class="pre">`RZline`</span> objects as generated by
<span class="pre">`zoidberg.rzline.shaped_line`</span>, one for the
inner boundary and one for the outer boundary.
<span class="pre">`RZline`</span> objects represent periodic lines in
R-Z (X-Z coordinates), with interpolation using splines.

To create an <span class="pre">`RZline`</span> object for a flux surface
we first need to find where the flux surface is. To do this we can use a
Poincare plot: Start at a point and follow the magnetic field a number
of times around the periodic y direction (e.g. toroidal angle). Every
time the field line reaches a y location of interest, mark the position
to build up a scattered set of points which all lie on the same flux
surface.

At the moment this will not work correctly for slab geometries, but
expects closed flux surfaces such as in a stellarator or tokamak. A
simple test case is a straight stellarator:

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg
    field = zoidberg.field.StraightStellarator(I_coil=0.4, yperiod=10)

</div>

</div>

By default <span class="pre">`StraightStellarator`</span> calculates the
magnetic field due to four coils which spiral around the axis at a
distance <span class="math notranslate nohighlight">\\r=0.8\\</span> in
a classical stellarator configuration. The
<span class="pre">`yperiod`</span> argument is the period in y after
which the coils return to their starting locations.

To visualise the Poincare plot for this stellarator field, pass the
<span class="pre">`MagneticField`</span> object to
<span class="pre">`zoidberg.plot.plot_poincare`</span>, together with
start location(s) and periodicity information:

<div class="highlight-python notranslate">

<div class="highlight">

    zoidberg.plot.plot_poincare(field, 0.4, 0.0, 10.0)

</div>

</div>

which should produce the following figure:

<figure id="poincare" class="align-default">
<a href="../_images/poincare.png"
class="reference internal image-reference"><img
src="../_images/poincare.png" style="width: 425.5px; height: 446.0px;"
alt="Points on four oval shaped flux surfaces in x-z at three locations along the y direction" /></a>
<figcaption><p><span class="caption-number">Fig. 10 </span><span
class="caption-text">Poincare map of straight stellarator showing a
single flux surface. Each colour corresponds to a different x-z plane in
the y direction.</span><a href="#poincare" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

The inputs here are the starting location
<span class="math notranslate nohighlight">\\\left(x,z\right) =
\left(0.4, 0.0\right)\\</span>, and the periodicity in the y direction
(10.0). By default this will integrate from this given starting location
40 times (<span class="pre">`revs`</span> option) around the y domain (0
to 10).

To create an <span class="pre">`RZline`</span> from these Poincare plots
we need a list of points in order around the line. Since the points on a
flux surface in a Poincare will not generally be in order we need to
find the best fit i.e. the shortest path which passes through all the
points without crossing itself. In general this is a
<a href="https://en.wikipedia.org/wiki/Travelling_salesman_problem"
class="reference external">known hard problem</a> but fortunately in
this case the nearest neighbour algorithm seems to be quite robust
provided there are enough points.

An example of calculating a Poincare plot on a single y slice (y=0) and
producing an <span class="pre">`RZline`</span> is:

<div class="highlight-python notranslate">

<div class="highlight">

    from zoidberg.fieldtracer import trace_poincare
    rzcoord, ycoords = trace_poincare(field, 0.4, 0.0, 10.0,
                                      y_slices=[0])

    R = rzcoord[:,0,0]
    Z = rzcoord[:,0,1]

    line = zoidberg.rzline.line_from_points(R, Z)

    line.plot()

</div>

</div>

**Note**: Currently there is no checking that the line created is a good
solution. The line could cross itself, but this has to be diagnosed
manually at the moment. If the line is not a good approximation to the
flux surface, increase the number of points by setting the
<span class="pre">`revs`</span> keyword (y revolutions) in the
<span class="pre">`trace_poincare`</span> call.

In general the points along this line are not evenly distributed, but
tend to cluster together in some regions and have large gaps in others.
The elliptic grid generator places grid points on the boundaries which
are uniform in the index of the <span class="pre">`RZline`</span> it is
given. Passing a very uneven set of points will therefore result in a
poor quality mesh. To avoid this, define a new
<span class="pre">`RZline`</span> by placing points at equal distances
along the line:

<div class="highlight-python notranslate">

<div class="highlight">

    line = line.equallySpaced()

</div>

</div>

The example zoidberg/straight-stellarator-curvilinear.py puts the above
methods together to create a grid file for a straight stellarator.

Sections below now describe each part of Zoidberg in more detail.
Further documentation of the API can be found in the docstrings and unit
tests.

</div>

<div id="magnetic-fields" class="section">

### Magnetic fields<a href="#magnetic-fields" class="headerlink"
title="Permalink to this heading">#</a>

The magnetic field is represented by a
<span class="pre">`MagneticField`</span> class, in
<span class="pre">`zoidberg.field`</span>. Magnetic fields can be
defined in either cylindrical or Cartesian coordinates:

- In Cartesian coordinates all (x,y,z) directions have the same units of
  length

- In cylindrical coordinates the y coordinate is assumed to be an angle,
  so that the distance in y is given by
  <span class="math notranslate nohighlight">\\ds = R dy\\</span> where
  <span class="math notranslate nohighlight">\\R\\</span> is the major
  radius.

Which coordinate is used is controlled by the
<span class="pre">`Rfunc`</span> method, which should return the major
radius if using a cylindrical coordinate system. Should return
<span class="pre">`None`</span> for a Cartesian coordinate system (the
default).

Several implementations inherit from
<span class="pre">`MagneticField`</span>, and provide:
<span class="pre">`Bxfunc`</span>, <span class="pre">`Byfunc`</span>,
<span class="pre">`Bzfunc`</span> which give the components of the
magnetic field in the x,y and z directions respectively. These should be
in the same units (e.g. Tesla) for both Cartesian and cylindrical
coordinates, but the way they are integrated changes depending on the
coordinate system.

Using these functions the <span class="pre">`MagneticField`</span> class
provides a <span class="pre">`Bmag`</span> method and
<span class="pre">`field_direction`</span> method, which are called by
the field line tracer routines (in
<span class="pre">`zoidberg.field_tracer`</span>).

<div id="slabs-and-curved-slabs" class="section">

#### Slabs and curved slabs<a href="#slabs-and-curved-slabs" class="headerlink"
title="Permalink to this heading">#</a>

The simplest magnetic field is a straight slab geometry:

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg
    field = zoidberg.field.Slab()

</div>

</div>

By default this has a magnetic field
<span class="math notranslate nohighlight">\\\mathbf{B} = \left(0, 1,
0.1 + x\right)\\</span>.

A variant is a curved slab, which is defined in cylindrical coordinates
and has a given major radius (default 1):

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg
    field = zoidberg.field.CurvedSlab()

</div>

</div>

Note that this uses a large aspect-ratio approximation, so the major
radius is constant across the domain (independent of x).

</div>

<div id="straight-stellarator" class="section">

#### Straight stellarator<a href="#straight-stellarator" class="headerlink"
title="Permalink to this heading">#</a>

This is generated by four coils with alternating currents arranged on
the edge of a circle, which spiral around the axis:

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg
    field = zoidberg.field.StraightStellarator()

</div>

</div>

<div class="admonition note">

Note

This requires Sympy to generate the magnetic field, so if unavailable an
exception will be raised

</div>

</div>

<div id="g-eqdsk-files" class="section">

#### G-Eqdsk files<a href="#g-eqdsk-files" class="headerlink"
title="Permalink to this heading">#</a>

This format is commonly used for axisymmetric tokamak equilibria, for
example output from EFIT equilibrium reconstruction. It consists of the
poloidal flux psi, describing the magnetic field in R and Z, with the
toroidal magnetic field Bt given by a 1D function f(psi) = R\*Bt which
depends only on psi:

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg
    field = zoidberg.field.GEQDSK("gfile.eqdsk")

</div>

</div>

</div>

<div id="vmec-files" class="section">

#### VMEC files<a href="#vmec-files" class="headerlink"
title="Permalink to this heading">#</a>

The VMEC format describes 3D magnetic fields in toroidal geometry, but
only includes closed flux surfaces:

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg
    field = zoidberg.field.VMEC("w7x.wout")

</div>

</div>

</div>

</div>

<div id="plotting-the-magnetic-field" class="section">

### Plotting the magnetic field<a href="#plotting-the-magnetic-field" class="headerlink"
title="Permalink to this heading">#</a>

Routines to plot the magnetic field are in
<span class="pre">`zoidberg.plot`</span>. They include Poincare plots
and 3D field line plots.

For example, to make a Poincare plot from a MAST equilibrium:

<div class="highlight-python notranslate">

<div class="highlight">

    import numpy as np
    import zoidberg
    field = zoidberg.field.GEQDSK("g014220.00200")
    zoidberg.plot.plot_poincare(field, 1.4, 0.0, 2*np.pi, interactive=True)

</div>

</div>

This creates a flux surface starting at
<span class="math notranslate nohighlight">\\R=1.4\\</span> and
<span class="math notranslate nohighlight">\\Z=0.0\\</span>. The fourth
input (<span class="pre">`2*np.pi`</span>) is the periodicity in the
<span class="math notranslate nohighlight">\\y\\</span> direction. Since
this magnetic field is symmetric in y (toroidal angle), this parameter
only affects the toroidal planes where the points are plotted.

The <span class="pre">`interactive=True`</span> argument to
<span class="pre">`plot_poincare`</span> generates a new set of points
for every click on the plot window.

</div>

<div id="creating-poloidal-grids" class="section">

### Creating poloidal grids<a href="#creating-poloidal-grids" class="headerlink"
title="Permalink to this heading">#</a>

The FCI technique is used for derivatives along the magnetic field (in
Y), and doesn’t restrict the form of the grid in the X-Z poloidal
planes. A 3D grid created by Zoidberg is a collection of 2D planes
(poloidal grids), connected together by interpolations along the
magnetic field.To define a 3D grid we first need to define the 2D
poloidal grids.

Two types of poloidal grids can currently be created: Rectangular grids,
and curvilinear structured grids. All poloidal grids have the following
methods:

- <span class="pre">`getCoordinate()`</span> which returns the real
  space (R,Z) coordinates of a given (x,z) index, or derivatives thereof

- <span class="pre">`findIndex()`</span> which returns the (x,z) index
  of a given (R,Z) coordinate which in general is floating point

- <span class="pre">`metric()`</span> which returns the 2D metric tensor

- <span class="pre">`plot()`</span> which plots the grid

<div id="id1" class="section">

#### Rectangular grids<a href="#id1" class="headerlink"
title="Permalink to this heading">#</a>

To create a rectangular grid, pass the number of points and lengths in
the x and z directions to
<span class="pre">`RectangularPoloidalGrid`</span>:

<div class="highlight-python notranslate">

<div class="highlight">

    import zoidberg

    rect = zoidberg.poloidal_grid.RectangularPoloidalGrid( nx, nz, Lx, Lz )

</div>

</div>

By default the middle of the rectangle is at
<span class="math notranslate nohighlight">\\\left(R,Z\right) =
\left(0,0\right)\\</span> but this can be changed with the
<span class="pre">`Rcentre`</span> and
<span class="pre">`Zcentre`</span> options.

</div>

<div id="curvilinear-structured-grids" class="section">

#### Curvilinear structured grids<a href="#curvilinear-structured-grids" class="headerlink"
title="Permalink to this heading">#</a>

To create the structured curvilinear grids inner and outer lines are
needed (two <span class="pre">`RZline`</span> objects). The
<span class="pre">`shaped_line`</span> function creates
<span class="pre">`RZline`</span> shapes with the following formula:

<div class="math notranslate nohighlight">

\\ \begin{align}\begin{aligned}R = R_0 - b + \left(a + b
\cos\left(\theta\right)\cos\left(\theta +
\delta\sin\left(\theta\right)\right)\right)\\Z = \left(1 +
\epsilon\right)a\sin\left(\theta\right)\end{aligned}\end{align} \\

</div>

where <span class="math notranslate nohighlight">\\R_0\\</span> is the
major radius, <span class="math notranslate nohighlight">\\a\\</span> is
the minor radius,
<span class="math notranslate nohighlight">\\\epsilon\\</span> is the
elongation (<span class="pre">`elong`</span>),
<span class="math notranslate nohighlight">\\\delta\\</span> the
triangularity (<span class="pre">`triang`</span>), and
<span class="math notranslate nohighlight">\\b\\</span> the indentation
(<span class="pre">`indent`</span>).

</div>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="bout_options.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

BOUT++ options

</div>

<a href="output_and_post.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Post-processing

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#bout-topology" class="reference internal nav-link">BOUT++
  Topology</a>
  - <a href="#basic" class="reference internal nav-link">Basic</a>
  - <a href="#advanced" class="reference internal nav-link">Advanced</a>
  - <a href="#periodic-x-domains"
    class="reference internal nav-link">Periodic X domains</a>
  - <a href="#implementations"
    class="reference internal nav-link">Implementations</a>
- <a href="#d-variables" class="reference internal nav-link">3D
  variables</a>
- <a href="#from-efit-files" class="reference internal nav-link">From EFIT
  files</a>
- <a href="#from-elite-and-gato-files"
  class="reference internal nav-link">From ELITE and GATO files</a>
- <a href="#generating-equilibria"
  class="reference internal nav-link">Generating equilibria</a>
- <a href="#zoidberg-grid-generator"
  class="reference internal nav-link">Zoidberg grid generator</a>
  - <a href="#rectangular-grids"
    class="reference internal nav-link">Rectangular grids</a>
  - <a href="#more-general-grids" class="reference internal nav-link">More
    general grids</a>
  - <a href="#grids-aligned-to-flux-surfaces"
    class="reference internal nav-link">Grids aligned to flux surfaces</a>
  - <a href="#magnetic-fields" class="reference internal nav-link">Magnetic
    fields</a>
    - <a href="#slabs-and-curved-slabs"
      class="reference internal nav-link">Slabs and curved slabs</a>
    - <a href="#straight-stellarator"
      class="reference internal nav-link">Straight stellarator</a>
    - <a href="#g-eqdsk-files" class="reference internal nav-link">G-Eqdsk
      files</a>
    - <a href="#vmec-files" class="reference internal nav-link">VMEC files</a>
  - <a href="#plotting-the-magnetic-field"
    class="reference internal nav-link">Plotting the magnetic field</a>
  - <a href="#creating-poloidal-grids"
    class="reference internal nav-link">Creating poloidal grids</a>
    - <a href="#id1" class="reference internal nav-link">Rectangular grids</a>
    - <a href="#curvilinear-structured-grids"
      class="reference internal nav-link">Curvilinear structured grids</a>

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
