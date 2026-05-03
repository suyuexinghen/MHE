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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/variable_init.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/variable_init.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/variable_init.rst"
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

# Variable initialisation

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#initialisation-of-time-evolved-variables"
  class="reference internal nav-link">Initialisation of time evolved
  variables</a>
  - <a href="#expressions"
    class="reference internal nav-link">Expressions</a>
  - <a href="#context-variables-and-scope"
    class="reference internal nav-link">Context variables and scope</a>
  - <a href="#passing-data-into-expressions"
    class="reference internal nav-link">Passing data into expressions</a>
  - <a href="#defining-functions-in-input-options"
    class="reference internal nav-link">Defining functions in input
    options</a>
  - <a href="#recursive-functions"
    class="reference internal nav-link">Recursive functions</a>
- <a href="#initalising-variables-with-the-fieldfactory-class"
  class="reference internal nav-link">Initalising variables with the <span
  class="pre"><code
  class="docutils literal notranslate">FieldFactory</code></span>
  class</a>
- <a href="#adding-a-new-function"
  class="reference internal nav-link">Adding a new function</a>
- <a href="#parser-internals" class="reference internal nav-link">Parser
  internals</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="variable-initialisation" class="section">

# Variable initialisation<a href="#variable-initialisation" class="headerlink"
title="Permalink to this heading">#</a>

Variables in BOUT++ are not initialised automatically, but must be
explicitly given a value. For example the following code declares a
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> variable then attempts
to access a particular element:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D f;    // Declare a variable
    f(0,0,0) = 1.0;  // Error!

</div>

</div>

This results in an error because the data array to store values in
<span class="pre">`f`</span> has not been allocated. Allocating data can
be done in several ways:

1.  Initialise with a value:

    <div class="highlight-cpp notranslate">

    <div class="highlight">

        Field3D f = 0.0; // Allocates memory, fills with zeros
        f(0,0,0) = 1.0; // ok

    </div>

    </div>

    This cannot be done at a global scope, since it requires the mesh to
    already exist and have a defined size.

2.  Set to a scalar value:

    <div class="highlight-cpp notranslate">

    <div class="highlight">

        Field3D f;
        f = 0.0; // Allocates memory, fills with zeros
        f(0,0,0) = 1.0; // ok

    </div>

    </div>

    Note that setting a field equal to another field has the effect of
    making both fields share the same underlying data. This behaviour is
    similar to how NumPy arrays behave in Python.

    <div class="highlight-cpp notranslate">

    <div class="highlight">

        Field3D g = 0.0;  // Allocates memory, fills with zeros
        Field3D f = g; // f now shares memory with g

        f(0,0,0) = 1.0; // g also modified

    </div>

    </div>

    To ensure that a field has a unique underlying memory array call the
    <a
    href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv4N7Field3D8allocateEv"
    class="reference internal" title="Field3D::allocate"><span
    class="pre"><code
    class="sourceCode cpp">Field3D<span class="op">::</span>allocate<span class="op">()</span></code></span></a>
    method before writing to individual indices.

3.  Use <a
    href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv4N7Field3D8allocateEv"
    class="reference internal" title="Field3D::allocate"><span
    class="pre"><code
    class="sourceCode cpp">Field3D<span class="op">::</span>allocate<span class="op">()</span></code></span></a>
    to allocate memory:

    <div class="highlight-cpp notranslate">

    <div class="highlight">

        Field3D f;
        f.allocate(); // Allocates memory, values undefined
        f(0,0,0) = 1.0; // ok

    </div>

    </div>

In a BOUT++ simulation some variables are typically evolved in time. The
initialisation of these variables is handled by the time integration
solver.

<div id="initialisation-of-time-evolved-variables" class="section">

<span id="sec-init-time-evolved-vars"></span>

## Initialisation of time evolved variables<a href="#initialisation-of-time-evolved-variables" class="headerlink"
title="Permalink to this heading">#</a>

Each variable being evolved has its own section, with the same name as
the output data. For example, the
high-<span class="math notranslate nohighlight">\\\beta\\</span> model
has variables “P”, “jpar”, and “U”, and so has sections
<span class="pre">`[P]`</span>, <span class="pre">`[jpar]`</span>,
<span class="pre">`[U]`</span> (names are case sensitive).

<div id="expressions" class="section">

<span id="sec-expressions"></span>

### Expressions<a href="#expressions" class="headerlink"
title="Permalink to this heading">#</a>

The recommended way to initialise a variable is to use the
<span class="pre">`function`</span> option for each variable:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [p]
    function = 1 + gauss(x-0.5)*gauss(y)*sin(z)

</div>

</div>

This evaluates an analytic expression to initialise the
<span class="math notranslate nohighlight">\\P\\</span> variable.
Expressions can include the usual operators
(<span class="pre">`+`</span>,<span class="pre">`-`</span>,<span class="pre">`*`</span>,<span class="pre">`/`</span>),
including <span class="pre">`^`</span> for exponents. The following
values are also already defined:

<span id="tab-initexprvals"></span>

<table id="id1" class="table">
<caption><span class="caption-number">Table 1 </span><span
class="caption-text">Initialisation expression values</span><a
href="#id1" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>x</p></td>
<td><p><span class="math notranslate nohighlight">\(x\)</span> position
between <span class="math notranslate nohighlight">\(0\)</span> and
<span class="math notranslate nohighlight">\(1\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p>y</p></td>
<td><p><span class="math notranslate nohighlight">\(y\)</span>
angle-like position, definition depends on topology of grid</p></td>
</tr>
<tr class="row-even">
<td><p>z</p></td>
<td><p><span class="math notranslate nohighlight">\(z\)</span> position
between <span class="math notranslate nohighlight">\(0\)</span> and
<span class="math notranslate nohighlight">\(2\pi\)</span> (excluding
the last point)</p></td>
</tr>
<tr class="row-odd">
<td><p>pi π</p></td>
<td><p><span
class="math notranslate nohighlight">\(3.1415\ldots\)</span></p></td>
</tr>
<tr class="row-even">
<td><p>is_periodic_y</p></td>
<td><p><span class="math notranslate nohighlight">\(1\)</span> in core
region where Y is periodic. <span
class="math notranslate nohighlight">\(0\)</span> otherwise</p></td>
</tr>
</tbody>
</table>

By default, <span class="math notranslate nohighlight">\\x\\</span> is
defined as
<span class="pre">`(i+0.5)`</span>` `<span class="pre">`/`</span>` `<span class="pre">`(nx`</span>` `<span class="pre">`-`</span>` `<span class="pre">`2*MXG)`</span>,
where <span class="pre">`MXG`</span> is the width of the boundary region
(by default 2) and <span class="pre">`i`</span> is the x-index value on
the grid *excluding boundary points*. Hence
<span class="math notranslate nohighlight">\\x\\</span> actually goes
from 0 on the boundary to the left of the leftmost point to 1 on the
rightmost point boundary to the right of the rightmost grid point.

<div class="admonition note">

Note

The previous default (prior to v3.0), was for
<span class="math notranslate nohighlight">\\x\\</span> to be defined as
<span class="pre">`(i`</span>` `<span class="pre">`+`</span>` `<span class="pre">`MXG)`</span>` `<span class="pre">`/`</span>` `<span class="pre">`(nx`</span>` `<span class="pre">`-`</span>` `<span class="pre">`2*MXG)`</span>.
Then <span class="math notranslate nohighlight">\\x\\</span> actually
goes from 0 on the leftmost boundary point to
<span class="pre">`(nx-1)/(nx-4)`</span> on the rightmost boundary
point. To revert to the old behaviour, set

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh]
    symmetricGlobalX = false

</div>

</div>

</div>

For slab-like or limiter-like geometries with no branch cuts,
<span class="math notranslate nohighlight">\\y\\</span> is an angular
coordinate between
<span class="math notranslate nohighlight">\\0\\</span> and
<span class="math notranslate nohighlight">\\2\pi\\</span>, defined as
<span class="pre">`(j`</span>` `<span class="pre">`+`</span>` `<span class="pre">`0.5)`</span>` `<span class="pre">`/`</span>` `<span class="pre">`ny`</span>
where <span class="pre">`j`</span> is the y-index value on the grid
*excluding boundary points*. Hence
<span class="math notranslate nohighlight">\\y\\</span> actually goes
from <span class="math notranslate nohighlight">\\0\\</span> on the
boundary to the left of the leftmost point to
<span class="math notranslate nohighlight">\\2\pi\\</span> on the
rightmost point boundary to the right of the rightmost grid point.

For tokamak geometries,
<span class="math notranslate nohighlight">\\y\\</span> is an angular
coordinate which goes between
<span class="math notranslate nohighlight">\\0\\</span> and
<span class="math notranslate nohighlight">\\2\pi\\</span> in the core
region. In a single-null geometry or before the upper divertor in a
double-null, <span class="math notranslate nohighlight">\\y\\</span> is
defined as
<span class="pre">`2*pi*(j`</span>` `<span class="pre">`-`</span>` `<span class="pre">`0.5`</span>` `<span class="pre">`-`</span>` `<span class="pre">`jyseps1_1)`</span>` `<span class="pre">`/`</span>` `<span class="pre">`ny_core`</span>,
where
<span class="pre">`ny_core`</span>` `<span class="pre">`=`</span>` `<span class="pre">`(jyseps2_1`</span>` `<span class="pre">`-`</span>` `<span class="pre">`jyseps1_1)`</span>` `<span class="pre">`+`</span>` `<span class="pre">`(jyseps2_2`</span>` `<span class="pre">`-`</span>` `<span class="pre">`jyseps1_2)`</span>
is the number of points in the core region. After the upper divertor in
a double-null, <span class="math notranslate nohighlight">\\y\\</span>
is defined as
<span class="pre">`2*pi*(j`</span>` `<span class="pre">`-`</span>` `<span class="pre">`0.5`</span>` `<span class="pre">`-`</span>` `<span class="pre">`jyseps1_1`</span>` `<span class="pre">`-`</span>` `<span class="pre">`(jyseps1_2`</span>` `<span class="pre">`-`</span>` `<span class="pre">`jyseps2_1))`</span>` `<span class="pre">`/`</span>` `<span class="pre">`ny_core`</span>.
So <span class="math notranslate nohighlight">\\y\\</span> has values
less than <span class="math notranslate nohighlight">\\0\\</span> in the
lower, inner divertor leg and greater than
<span class="math notranslate nohighlight">\\2\pi\\</span> in the lower,
outer divertor leg. In the upper, inner divertor leg of a double-null
geometry, <span class="math notranslate nohighlight">\\y\\</span>
increases smoothly from the value it had in the inner-core/inner-SOL,
jumping at the location of the target so that in the upper, outer
divertor leg it joins smoothly to the outer-core/outer-SOL.

<div class="admonition note">

Note

The previous default (prior to v3.0), was for
<span class="math notranslate nohighlight">\\y\\</span> to be defined as
<span class="pre">`j_core`</span>` `<span class="pre">`/`</span>` `<span class="pre">`ny_core`</span>
where <span class="pre">`j_core`</span> is the grid index excluding
boundary points and points in any divertor legs
(<span class="pre">`j_core`</span>` `<span class="pre">`=`</span>` `<span class="pre">`0`</span>
in the lower, inner divertor leg,
<span class="pre">`j_core`</span>` `<span class="pre">`=`</span>` `<span class="pre">`jyseps2_1`</span>` `<span class="pre">`-`</span>` `<span class="pre">`jyseps1_1`</span>
in the upper divertor legs if present,
<span class="pre">`j_core`</span>` `<span class="pre">`=`</span>` `<span class="pre">`ny_core`</span>
in the lower, outer divertor leg). To revert to the old behaviour, set

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh]
    symmetricGlobalY = false

</div>

</div>

</div>

<span class="math notranslate nohighlight">\\z\\</span> is defined as
<span class="pre">`k`</span>` `<span class="pre">`/`</span>` `<span class="pre">`nz`</span>
where <span class="pre">`k`</span> is the z-index value on the grid. So
<span class="math notranslate nohighlight">\\z\\</span> is 0 at the
first grid point, and would be
<span class="math notranslate nohighlight">\\2\pi\\</span> at the next
point after the last grid point.

If a variable is at a staggered grid location
<span class="pre">`CELL_XLOW`</span>,
<span class="pre">`CELL_YLOW`</span>, or
<span class="pre">`CELL_ZLOW`</span>, the values of
<span class="math notranslate nohighlight">\\x\\</span>,
<span class="math notranslate nohighlight">\\y\\</span>, or
<span class="math notranslate nohighlight">\\z\\</span> respectively
will take into account the half-grid-point shift.

By default the expressions are evaluated in a field-aligned coordinate
system, i.e. if you are using the <span class="pre">`[mesh]`</span>
option
<span class="pre">`paralleltransform`</span>` `<span class="pre">`=`</span>` `<span class="pre">`shifted`</span>,
the input <span class="pre">`f`</span> will have
<span class="pre">`f`</span>` `<span class="pre">`=`</span>` `<span class="pre">`fromFieldAligned(f)`</span>
applied before being returned. To switch off this behaviour and evaluate
the input expressions in coordinates with orthogonal x-z (i.e. toroidal
<span class="math notranslate nohighlight">\\\\\psi,\theta,\phi\\\\</span>
coordinates when using
<span class="pre">`paralleltransform`</span>` `<span class="pre">`=`</span>` `<span class="pre">`shifted`</span>),
set in BOUT.inp

<div class="highlight-cfg notranslate">

<div class="highlight">

    [input]
    transform_from_field_aligned = false

</div>

</div>

The functions in
<a href="#tab-initexprfunc" class="reference internal"><span
class="std std-numref">Table 2</span></a> are also available in
expressions.

<span id="tab-initexprfunc"></span>

<table id="id2" class="table">
<caption><span class="caption-number">Table 2 </span><span
class="caption-text">Initialisation expression functions</span><a
href="#id2" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">abs(x)</code></span></p></td>
<td><p>Absolute value <span
class="math notranslate nohighlight">\(|x|\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">asin(x)</code></span>, <span
class="pre"><code
class="docutils literal notranslate">acos(x)</code></span>, <span
class="pre"><code
class="docutils literal notranslate">atan(x)</code></span>, <span
class="pre"><code
class="docutils literal notranslate">atan(y,x)</code></span></p></td>
<td><p>Inverse trigonometric functions</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">ballooning(x)</code></span></p></td>
<td><p>Ballooning transform (<a href="#equation-ballooning-transform"
class="reference internal">(1)</a>, <a href="#fig-ballooning"
class="reference internal"><span class="std std-numref">Fig.
4</span></a>)</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">ballooning(x,n)</code></span></p></td>
<td><p>Ballooning transform, using <span
class="math notranslate nohighlight">\(n\)</span> terms (default
3)</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">cos(x)</code></span></p></td>
<td><p>Cosine</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">cosh(x)</code></span></p></td>
<td><p>Hyperbolic cosine</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">exp(x)</code></span></p></td>
<td><p>Exponential</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">tanh(x)</code></span></p></td>
<td><p>Hyperbolic tangent</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">gauss(x)</code></span></p></td>
<td><p>Gaussian <span
class="math notranslate nohighlight">\(\exp(-x^2/2) /
\sqrt{2\pi}\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">gauss(x,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">w)</code></span></p></td>
<td><p>Gaussian <span
class="math notranslate nohighlight">\(\exp[-x^2/(2w^2)] /
(w\sqrt{2\pi})\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">H(x)</code></span></p></td>
<td><p>Heaviside function: <span
class="math notranslate nohighlight">\(1\)</span> if <span
class="math notranslate nohighlight">\(x &gt; 0\)</span> otherwise <span
class="math notranslate nohighlight">\(0\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">log(x)</code></span></p></td>
<td><p>Natural logarithm</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">max(x,y,...)</code></span></p></td>
<td><p>Maximum (variable arguments)</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">min(x,y,...)</code></span></p></td>
<td><p>Minimum (variable arguments)</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">clamp(value,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">low,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">high)</code></span></p></td>
<td><p>If value &lt; low, return low; If value &gt; high, return high;
otherwise return value</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">mixmode(x)</code></span></p></td>
<td><p>A mixture of Fourier modes</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">mixmode(x,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">seed)</code></span></p></td>
<td><p>seed determines random phase (default 0.5)</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">power(x,y)</code></span></p></td>
<td><p>Exponent <span
class="math notranslate nohighlight">\(x^y\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">sin(x)</code></span></p></td>
<td><p>Sine</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">sinh(x)</code></span></p></td>
<td><p>Hyperbolic sine</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">sqrt(x)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\sqrt{x}\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">tan(x)</code></span></p></td>
<td><p>Tangent</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">erf(x)</code></span></p></td>
<td><p>The error function</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">TanhHat(x,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">width,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">centre,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">steepness)</code></span></p></td>
<td><p>The hat function <span
class="math notranslate nohighlight">\(\frac{1}{2}(\tanh[s
(x-[c-\frac{w}{2}])]\)</span> <span
class="math notranslate nohighlight">\(- \tanh[s (x-[c+\frac{w}{2}])]
)\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">fmod(x)</code></span></p></td>
<td><p>The modulo operator, returns floating point remainder</p></td>
</tr>
</tbody>
</table>

In addition there are some special functions which enable control flow

<span id="tab-exprcontrol"></span>

<table id="id3" class="table">
<caption><span class="caption-number">Table 3 </span><span
class="caption-text">Control flow and special functions</span><a
href="#id3" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">where(expr,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">gt0,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">lt0)</code></span></p></td>
<td><p>If the first <span class="pre"><code
class="docutils literal notranslate">expr</code></span> evaluates to a
value greater than zero then the second expression <span
class="pre"><code class="docutils literal notranslate">gt0</code></span>
is evaluated. Otherwise the last expression <span class="pre"><code
class="docutils literal notranslate">lt0</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">sum(symbol,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">count,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">expr)</code></span></p></td>
<td><p>Evaluate expression <span class="pre"><code
class="docutils literal notranslate">expr</code></span> <span
class="pre"><code
class="docutils literal notranslate">count</code></span> times, and sum
the result. Each time the symbol is incremented from 0 to <span
class="pre"><code
class="docutils literal notranslate">count</code></span>-1. The value of
the symbol is accessed by putting it in braces <span class="pre"><code
class="docutils literal notranslate">{}</code></span>. Example: <span
class="pre"><code
class="docutils literal notranslate">sum(i,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">3,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">{i}^2)</code></span> is <span
class="pre"><code
class="docutils literal notranslate">0^2</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">+</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">1^2</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">+</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">2^2</code></span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">[var</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">=</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">value,...](expr)</code></span></p></td>
<td><p>Define a new scope with variables whose value can be accessed
using braces <span class="pre"><code
class="docutils literal notranslate">{}</code></span>. The <span
class="pre"><code
class="docutils literal notranslate">value</code></span> each variable
<span class="pre"><code
class="docutils literal notranslate">var</code></span> is set to can be
an expression, and is evaluated before the <span class="pre"><code
class="docutils literal notranslate">expr</code></span> expression.
Example: <span class="pre"><code
class="docutils literal notranslate">[n=2](</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">{n}^{n}</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">)</code></span> is <span
class="pre"><code
class="docutils literal notranslate">2^2</code></span>.</p></td>
</tr>
</tbody>
</table>

For field-aligned tokamak simulations, the Y direction is along the
field and in the core this will have a discontinuity at the twist-shift
location where field-lines are matched onto each other. To handle this,
the <span class="pre">`ballooning`</span> function applies a truncated
Ballooning transformation to construct a smooth initial perturbation:

<div id="equation-ballooning-transform"
class="math notranslate nohighlight">

<span class="eqno">(1)<a href="#equation-ballooning-transform" class="headerlink"
title="Permalink to this equation">#</a></span>\\U_0^{balloon} =
\sum\_{i=-N}^N F(x)G(y + 2\pi i)H(z + q2\pi i)\\

</div>

<figure id="id4" class="align-default">
<span id="fig-ballooning"></span><a href="../_images/init_balloon.png"
class="reference internal image-reference"><img
src="../_images/init_balloon.png" style="width: 48.0%;"
alt="Initial profiles" /></a>
<figcaption><p><span class="caption-number">Fig. 4 </span><span
class="caption-text">Initial profiles in twist-shifted grid.
<strong>Left</strong>: Without ballooning transform, showing
discontinuity at the matching location <strong>Right</strong>: with
ballooning transform</span><a href="#id4" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

There is an example code <span class="pre">`test-ballooning`</span>
which compares methods of setting initial conditions with the ballooning
transform.

The <span class="pre">`mixmode(x)`</span> function is a mixture of
Fourier modes of the form:

<div class="math notranslate nohighlight">

\\\mathrm{mixmode}(x) = \sum\_{i=1}^{14} \frac{1}{(1 +
|i-4|)^2}\cos\[ix + \phi(i, \mathrm{seed})\]\\

</div>

where <span class="math notranslate nohighlight">\\\phi\\</span> is a
random phase between
<span class="math notranslate nohighlight">\\-\pi\\</span> and
<span class="math notranslate nohighlight">\\+\pi\\</span>, which
depends on the seed. The factor in front of each term is chosen so that
the 4th harmonic
(<span class="math notranslate nohighlight">\\i=4\\</span>) has the
highest amplitude. This is useful mainly for initialising turbulence
simulations, where a mixture of mode numbers is desired.

</div>

<div id="context-variables-and-scope" class="section">

### Context variables and scope<a href="#context-variables-and-scope" class="headerlink"
title="Permalink to this heading">#</a>

Expressions can use a form of local variables, by using
<span class="pre">`[]()`</span> to define new scopes:

<div class="highlight-cfg notranslate">

<div class="highlight">

    var = [a = 2,
           b = 3]( {a} + {b}^{a} )

</div>

</div>

Where here the braces <span class="pre">`{}`</span> refer to context
variables, to distinguish them from variables in the options which have
no braces. One application of these is a (modest) performance
improvement: If <span class="pre">`{a}`</span> is a large expression
then in the above example it would only be evaluated once, the value
stored as <span class="pre">`{a}`</span> and used twice in the
expression.

</div>

<div id="passing-data-into-expressions" class="section">

### Passing data into expressions<a href="#passing-data-into-expressions" class="headerlink"
title="Permalink to this heading">#</a>

A second application of context variables is that they can be set by the
calling C++ code, providing a way for data to be passed from BOUT++ into
these expressions. The evaluation of expressions is currently not very
efficient, but this provides a very flexible way for the input options
to modify simulation behaviour.

This can be done by first parsing an expression and then passing values
to <span class="pre">`generate`</span> in the
<span class="pre">`Context`</span> object.

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D shear = ...; // Value calculated in BOUT++

    FieldFactory factory(mesh);
    auto gen = factory->parse("model:viscosity");

    Field3D viscosity;
    viscosity.allocate();

    BOUT_FOR(i, viscosity.region("RGN_ALL")) {
      viscosity[i] = gen->generate(bout::generator::Context(i, CELL_CENTRE, mesh, 0.0)
                                     .set("shear", shear[i]));
    }

</div>

</div>

Note that the <span class="pre">`Context`</span> constructor takes the
index, the cell location (e.g. staggered), a mesh, and then the time
(set to 0.0 here). Additional variables can be
<span class="pre">`set`</span>, “shear” in this case. In the input
options file (or command line) the viscosity could now be a function of
<span class="pre">`{shear}`</span>

<div class="highlight-cfg notranslate">

<div class="highlight">

    [model]
    viscosity = 1 + {shear}

</div>

</div>

</div>

<div id="defining-functions-in-input-options" class="section">

### Defining functions in input options<a href="#defining-functions-in-input-options" class="headerlink"
title="Permalink to this heading">#</a>

Defining context variables in a new scope can be used to define and call
functions, as in the above example <span class="pre">`viscosity`</span>
is a function of <span class="pre">`{shear}`</span>. For example we
could define a cosh function using

<div class="highlight-cfg notranslate">

<div class="highlight">

    mycosh = 0.5 * (exp({arg}) + exp(-{arg}))

</div>

</div>

which uses <span class="pre">`{arg}`</span> as the input value. We could
then call this function:

<div class="highlight-cfg notranslate">

<div class="highlight">

    result = [arg = x*2](mycosh)

</div>

</div>

</div>

<div id="recursive-functions" class="section">

<span id="sec-recursive-functions"></span>

### Recursive functions<a href="#recursive-functions" class="headerlink"
title="Permalink to this heading">#</a>

By default recursive expressions are not allowed in the input options,
and a <span class="pre">`ParseException`</span> will be thrown if
circular dependencies occur. Recursive functions can however be enabled
by setting
<span class="pre">`input:max_recursion_depth`</span>` `<span class="pre">`!=`</span>` `<span class="pre">`0`</span>
e.g.:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [input]
    max_recursion_depth = 10  # 0 = none, -1 = unlimited

</div>

</div>

By putting a limit on the depth, expressions should (eventually)
terminate or fail with a <span class="pre">`BoutException`</span>,
rather than entering an infinite loop. To remove this restriction
<span class="pre">`max_recursion_depth`</span> can be set to -1 to allow
arbitrary recursion (limited by stack, memory sizes).

If recursion is allowed, then the <span class="pre">`where`</span>
special function and <span class="pre">`Context`</span> scopes can be
(ab)used to define quite general functions. For example the Fibonnacci
sequence <span class="pre">`1,1,2,3,5,8,...`</span> can be generated:

<div class="highlight-cfg notranslate">

<div class="highlight">

    fib = where({n} - 2.5,
                [n={n}-1](fib) + [n={n}-2](fib),
                1)

</div>

</div>

so if <span class="pre">`n`</span> = 1 or 2 then
<span class="pre">`fib`</span> = 1, but if n = 3 or above then recursion
is used.

Note: Use of this facility in general is not encouraged, as it can
easily lead to very inefficient and hard to understand code. It is here
because occasionally it might be necessary, and because making the input
language Turing complete was irresistible.

</div>

</div>

<div id="initalising-variables-with-the-fieldfactory-class"
class="section">

## Initalising variables with the <span class="pre">`FieldFactory`</span> class<a href="#initalising-variables-with-the-fieldfactory-class"
class="headerlink" title="Permalink to this heading">#</a>

This class provides a way to generate a field with a specified form. For
example to create a variable <span class="pre">`var`</span> from options
we could write

<div class="highlight-cpp notranslate">

<div class="highlight">

    FieldFactory f(mesh);
    Field2D var = f.create2D("var");

</div>

</div>

This will look for an option called “var”, and use that expression to
initialise the variable <span class="pre">`var`</span>. This could then
be set in the BOUT.inp file or on the command line.

<div class="highlight-cpp notranslate">

<div class="highlight">

    var = gauss(x-0.5,0.2)*gauss(y)*sin(3*z)

</div>

</div>

To do this, <a
href="../_breathe_autogen/file/field__factory_8hxx.html#_CPPv412FieldFactory"
class="reference internal" title="FieldFactory"><span class="pre"><code
class="sourceCode cpp">FieldFactory</code></span></a> implements a
recursive descent parser to turn a string containing something like
<span class="pre">`"gauss(x-0.5,0.2)*gauss(y)*sin(3*z)"`</span> into
values in a
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> or
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> object. Examples are
given in the <span class="pre">`test-fieldfactory`</span> example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    FieldFactory f(mesh);
    Field2D b = f.create2D("1 - x");
    Field3D d = f.create3D("gauss(x-0.5,0.2)*gauss(y)*sin(z)");

</div>

</div>

This is done by creating a tree of <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> objects which
then generate the field values:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class FieldGenerator {
     public:
      virtual ~FieldGenerator() { }
      virtual FieldGeneratorPtr clone(const list<FieldGeneratorPtr> args) {return NULL;}
      virtual BoutReal generate(const bout::generator::Context& ctx) = 0;
    };

</div>

</div>

where <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv417FieldGeneratorPtr"
class="reference internal" title="FieldGeneratorPtr"><span
class="pre"><code
class="sourceCode cpp">FieldGeneratorPtr</code></span></a> is an alias
for <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp"><span class="bu">std::</span>shared_ptr</code></span></a>,
a shared pointer to a <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a>. The
<span class="pre">`Context`</span> input to
<span class="pre">`generate`</span> is an object containing values which
can be used in expressions, in particular <span class="pre">`x`</span>,
<span class="pre">`y`</span>, <span class="pre">`z`</span> and
<span class="pre">`t`</span> coordinates. Additional values can be
stored in the <span class="pre">`Context`</span> object, allowing data
from BOUT++ to be used in expressions. There are also ways to manipulate
<span class="pre">`Context`</span> objects for more complex expressions
and functions, see below for details.

All classes inheriting from <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> must implement a
<a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv4N14FieldGenerator8generateERKN4bout9generator7ContextE"
class="reference internal" title="FieldGenerator::generate"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator<span class="op">::</span>generate<span class="op">()</span></code></span></a>
function, which returns the value at the given
<span class="pre">`(x,y,z,t)`</span> position. Classes should also
implement a <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv4N14FieldGenerator5cloneEKNSt4listI17FieldGeneratorPtrEE"
class="reference internal" title="FieldGenerator::clone"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator<span class="op">::</span>clone<span class="op">()</span></code></span></a>
function, which takes a list of arguments and creates a new instance of
its class. This takes as input a list of other <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> objects,
allowing a variable number of arguments.

The simplest generator is a fixed numerical value, which is represented
by a <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv410FieldValue"
class="reference internal" title="FieldValue"><span class="pre"><code
class="sourceCode cpp">FieldValue</code></span></a> object:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class FieldValue : public FieldGenerator {
     public:
      FieldValue(BoutReal val) : value(val) {}
      BoutReal generate(const bout::generator::Context&) override { return value; }
     private:
      BoutReal value;
    };

</div>

</div>

</div>

<div id="adding-a-new-function" class="section">

## Adding a new function<a href="#adding-a-new-function" class="headerlink"
title="Permalink to this heading">#</a>

To add a new function to the FieldFactory, a new <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> class must be
defined. Here we will use the example of the
<span class="pre">`sinh`</span> function, implemented using a class
<span class="pre">`FieldSinh`</span>. This takes a single argument as
input, but <span class="pre">`FieldPI`</span> takes no arguments, and <a
href="../_breathe_autogen/file/fieldgenerators_8hxx.html#_CPPv413FieldGaussian"
class="reference internal" title="FieldGaussian"><span class="pre"><code
class="sourceCode cpp">FieldGaussian</code></span></a> takes either one
or two. Study these after reading this to see how these are handled.

First, edit <span class="pre">`src/field/fieldgenerators.hxx`</span> and
add a class definition:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class FieldSinh : public FieldGenerator {
     public:
      FieldSinh(FieldGeneratorPtr g) : gen(g) {}

      FieldGeneratorPtr clone(const list<FieldGenerator*> args) override;
      BoutReal generate(const bout::generator::Context& ctx) override;
     private:
      FieldGeneratorPtr gen;
    };

</div>

</div>

The <span class="pre">`gen`</span> member is used to store the input
argument. The constructor takes a single input, the <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> argument to the
<span class="pre">`sinh`</span> function, which is stored in the member
<span class="pre">`gen`</span> .

Next edit <span class="pre">`src/field/fieldgenerators.cxx`</span> and
add the implementation of the <span class="pre">`clone`</span> and
<span class="pre">`generate`</span> functions:

<div class="highlight-cpp notranslate">

<div class="highlight">

    FieldGeneratorPtr FieldSinh::clone(const list<FieldGeneratorPtr> args) {
      if (args.size() != 1) {
        throw ParseException("Incorrect number of arguments to sinh function. Expecting 1, got %d", args.size());
      }

      return std::make_shared<FieldSinh>(args.front());
    }

    BoutReal FieldSinh::generate(const bout::generator::Context& ctx) {
      return sinh(gen->generate(ctx));
    }

</div>

</div>

The <span class="pre">`clone`</span> function first checks the number of
arguments using <span class="pre">`args.size()`</span> . This is used in
<a
href="../_breathe_autogen/file/fieldgenerators_8hxx.html#_CPPv413FieldGaussian"
class="reference internal" title="FieldGaussian"><span class="pre"><code
class="sourceCode cpp">FieldGaussian</code></span></a> to handle
different numbers of input, but in this case we throw a <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414ParseException"
class="reference internal" title="ParseException"><span
class="pre"><code
class="sourceCode cpp">ParseException</code></span></a> if the number of
inputs isn’t one. <span class="pre">`clone`</span> then creates a new
<span class="pre">`FieldSinh`</span> object, passing the first argument
( <span class="pre">`args.front()`</span> ) to the constructor (which
then gets stored in the <span class="pre">`gen`</span> member variable).
Note that <span class="pre">`std::make_shared`</span> is used to make a
shared pointer.

The <span class="pre">`generate`</span> function for
<span class="pre">`sinh`</span> just gets the value of the input by
calling <span class="pre">`gen->generate(ctx)`</span> with the input
<span class="pre">`Context`</span> object
<span class="pre">`ctx`</span>, calculates
<span class="pre">`sinh`</span> of it and returns the result.

The <span class="pre">`clone`</span> function means that the parsing
code can make copies of any <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> class if it’s
given a single instance to start with. The final step is therefore to
give the <a
href="../_breathe_autogen/file/field__factory_8hxx.html#_CPPv412FieldFactory"
class="reference internal" title="FieldFactory"><span class="pre"><code
class="sourceCode cpp">FieldFactory</code></span></a> class an instance
of this new generator. Edit the <a
href="../_breathe_autogen/file/field__factory_8hxx.html#_CPPv412FieldFactory"
class="reference internal" title="FieldFactory"><span class="pre"><code
class="sourceCode cpp">FieldFactory</code></span></a> constructor <a
href="../_breathe_autogen/file/field__factory_8hxx.html#_CPPv4N12FieldFactory12FieldFactoryEP4MeshP7Options"
class="reference internal" title="FieldFactory::FieldFactory"><span
class="pre"><code
class="sourceCode cpp">FieldFactory<span class="op">::</span>FieldFactory<span class="op">()</span></code></span></a>
in <span class="pre">`src/field/field_factory.cxx`</span> and add the
line:

<div class="highlight-cpp notranslate">

<div class="highlight">

    addGenerator("sinh", std::make_shared<FieldSinh>(nullptr));

</div>

</div>

That’s it! This line associates the string
<span class="pre">`"sinh"`</span> with a <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> . Even though <a
href="../_breathe_autogen/file/field__factory_8hxx.html#_CPPv412FieldFactory"
class="reference internal" title="FieldFactory"><span class="pre"><code
class="sourceCode cpp">FieldFactory</code></span></a> doesn’t know what
type of <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> it is, it can
make more copies by calling the <span class="pre">`clone`</span> member
function. This is a useful technique for polymorphic objects in C++
called the “Virtual Constructor” idiom.

</div>

<div id="parser-internals" class="section">

## Parser internals<a href="#parser-internals" class="headerlink"
title="Permalink to this heading">#</a>

The basic expression parser is defined in
<span class="pre">`include/bout/sys/expressionparser.hxx`</span> and the
code in <span class="pre">`src/sys/expressionparser.cxx`</span>. The
<span class="pre">`FieldFactory`</span> adds the function in table
<a href="#tab-initexprfunc" class="reference internal"><span
class="std std-numref">Table 2</span></a> on top of this basic
functionality, and also uses <span class="pre">`Options`</span> to
resolve unknown symbols to <span class="pre">`Options`</span>.

When a <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> is added using
the <span class="pre">`addGenerator`</span> function, it is entered into
a <span class="pre">`std::map`</span> which maps strings to <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> objects
(<span class="pre">`include/bout/sys/expressionparser.hxx`</span>):

<div class="highlight-cpp notranslate">

<div class="highlight">

    std::map<std::string, FieldGeneratorPtr> gen;

</div>

</div>

Parsing a string into a tree of <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> objects is done
by a first splitting the string up into separate tokens like operators
like ’\*’, brackets ’(’, names like ’sinh’ and so on
(<a href="https://en.wikipedia.org/wiki/Lexical_analysis"
class="reference external">Lexical analysis</a>), then recognising
patterns in the stream of tokens
(<a href="https://en.wikipedia.org/wiki/Parsing"
class="reference external">Parsing</a>). Recognising tokens is done in
<span class="pre">`src/sys/expressionparser.cxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    char ExpressionParser::LexInfo::nextToken() {
     ...

</div>

</div>

This returns the next token, and setting the variable
<span class="pre">`char`</span>` `<span class="pre">`curtok`</span> to
the same value. This can be one of:

- -1 if the next token is a number. The variable
  <span class="pre">`BoutReal`</span>` `<span class="pre">`curval`</span>
  is set to the value of the token

- -2 for a symbol (e.g. “sinh”, “x” or “pi”). This includes anything
  which starts with a letter, and contains only letters, numbers, and
  underscores. The string is stored in the variable
  <span class="pre">`string`</span>` `<span class="pre">`curident`</span>

- -3 for a <span class="pre">`Context`</span> parameter which appeared
  surrounded by braces <span class="pre">`{}`</span>.

- 0 to mean end of input

- The character if none of the above. Since letters and numbers are
  taken care of (see above), this includes brackets and operators like
  ’+’ and ’-’.

The parsing stage turns these tokens into a tree of <a
href="../_breathe_autogen/file/expressionparser_8hxx.html#_CPPv414FieldGenerator"
class="reference internal" title="FieldGenerator"><span
class="pre"><code
class="sourceCode cpp">FieldGenerator</code></span></a> objects,
starting with the <span class="pre">`parse()`</span> function:

<div class="highlight-cpp notranslate">

<div class="highlight">

    FieldGenerator* FieldFactory::parse(const string &input) {
       ...

</div>

</div>

which puts the input string into a stream so that
<span class="pre">`nextToken()`</span> can use it, then calls the
<span class="pre">`parseExpression()`</span> function to do the actual
parsing:

<div class="highlight-cpp notranslate">

<div class="highlight">

    FieldGenerator* FieldFactory::parseExpression() {
       ...

</div>

</div>

This breaks down expressions in stages, starting with writing every
expression as:

<div class="highlight-cpp notranslate">

<div class="highlight">

    expression := primary [ op primary ]

</div>

</div>

i.e. a primary expression, and optionally an operator and another
primary expression. Primary expressions are handled by the
<span class="pre">`parsePrimary()`</span> function, so first
<span class="pre">`parsePrimary()`</span> is called, and then
<span class="pre">`parseBinOpRHS`</span> which checks if there is an
operator, and if so calls <span class="pre">`parsePrimary()`</span> to
parse it. This code also takes care of operator precedence by keeping
track of the precedence of the current operator. Primary expressions are
then further broken down and can consist of either a number, a name
(identifier), a minus sign and a primary expression, or brackets around
an expression:

<div class="highlight-cpp notranslate">

<div class="highlight">

    primary := number
            := identifier
            := '-' primary
            := '(' expression ')'
            := '[' expression ']'

</div>

</div>

The minus sign case is needed to handle the unary minus e.g.
<span class="pre">`"-x"`</span> . Identifiers are handled in
<span class="pre">`parseIdentifierExpr()`</span> which handles either
variable names, or functions

<div class="highlight-cpp notranslate">

<div class="highlight">

    identifier := name
               := name '(' expression [ ',' expression [ ',' ... ] ] ')'

</div>

</div>

i.e. a name, optionally followed by brackets containing one or more
expressions separated by commas. names without brackets are treated the
same as those with empty brackets, so <span class="pre">`"x"`</span> is
the same as <span class="pre">`"x()"`</span>. A list of inputs
(<span class="pre">`list<FieldGeneratorPtr>`</span>` `<span class="pre">`args;`</span>
) is created, the <span class="pre">`gen`</span> map is searched to find
the <span class="pre">`FieldGenerator`</span> object corresponding to
the name, and the list of inputs is passed to the object’s
<span class="pre">`clone`</span> function.

</div>

</div>

<div class="prev-next-area">

<a href="makefiles.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Makefiles and compiling BOUT++

</div>

<a href="boundary_options.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Boundary conditions

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#initialisation-of-time-evolved-variables"
  class="reference internal nav-link">Initialisation of time evolved
  variables</a>
  - <a href="#expressions"
    class="reference internal nav-link">Expressions</a>
  - <a href="#context-variables-and-scope"
    class="reference internal nav-link">Context variables and scope</a>
  - <a href="#passing-data-into-expressions"
    class="reference internal nav-link">Passing data into expressions</a>
  - <a href="#defining-functions-in-input-options"
    class="reference internal nav-link">Defining functions in input
    options</a>
  - <a href="#recursive-functions"
    class="reference internal nav-link">Recursive functions</a>
- <a href="#initalising-variables-with-the-fieldfactory-class"
  class="reference internal nav-link">Initalising variables with the <span
  class="pre"><code
  class="docutils literal notranslate">FieldFactory</code></span>
  class</a>
- <a href="#adding-a-new-function"
  class="reference internal nav-link">Adding a new function</a>
- <a href="#parser-internals" class="reference internal nav-link">Parser
  internals</a>

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
