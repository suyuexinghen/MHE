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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/new_in_v5.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/new_in_v5.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/new_in_v5.rst"
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

# New Features in BOUT++ v5.0

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#d-metrics" class="reference internal nav-link">3D Metrics</a>
  - <a href="#changes" class="reference internal nav-link">Changes</a>
    - <a href="#types" class="reference internal nav-link">Types</a>
    - <a href="#indexing" class="reference internal nav-link">Indexing</a>
    - <a href="#fixme-when-coordinates-refactored"
      class="reference internal nav-link">FIXME WHEN COORDINATES
      REFACTORED</a>
  - <a href="#incompatibilities"
    class="reference internal nav-link">Incompatibilities</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="new-features-in-bout-v5-0" class="section">

<span id="sec-newv5"></span>

# New Features in BOUT++ v5.0<a href="#new-features-in-bout-v5-0" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ v5.0 is a new major release, adding tons of new features,
improving existing code, as well as removing some old and deprecated
things. There are some breaking changes which will require modifications
to your physics model, but for the vast majority we have provided
tooling to automate this as much as possible.

<div id="d-metrics" class="section">

## 3D Metrics<a href="#d-metrics" class="headerlink"
title="Permalink to this heading">#</a>

Up until now, BOUT++ has been limited to varying the metric components
only in the XY plane. This release now introduces 3D metrics as a
compile-time option, allow simulations of devices such as stellarators.

To enable 3D metrics, build BOUT++ like:

<div class="highlight-console notranslate">

<div class="highlight">

    cmake . -B build -DBOUT_ENABLE_METRIC_3D=ON

</div>

</div>

<div id="changes" class="section">

### Changes<a href="#changes" class="headerlink"
title="Permalink to this heading">#</a>

<div id="types" class="section">

#### Types<a href="#types" class="headerlink"
title="Permalink to this heading">#</a>

Adding 3D metrics to BOUT++ has been a substantial effort, requiring
many changes to a significant amount of the source code. The main change
is that the metric components, <span class="pre">`g11`</span>,
<span class="pre">`g22`</span>, and so on, as well as the grid spacing,
<span class="pre">`dx`</span>, <span class="pre">`dy`</span>,
<span class="pre">`dz`</span>, have changed from
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> to <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4N11Coordinates11FieldMetricE"
class="reference internal" title="Coordinates::FieldMetric"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>FieldMetric</code></span></a>:
a type alias for either
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> or
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> depending on if BOUT++
was built with or without 3D metrics respectively.

<div class="admonition note">

Note

<a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4N11Coordinates2dzE"
class="reference internal" title="Coordinates::dz"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>dz</code></span></a>
has also changed to be
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> even without 3D
metrics. This is a breaking change, in that it may be necessary to
change user code in order to keep working. If you don’t use 3D metrics,
wrapping the use of <span class="pre">`dz`</span>, and similarly <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4NK11Coordinates7zlengthEv"
class="reference internal" title="Coordinates::zlength"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>zlength<span class="op">()</span></code></span></a>,
in a call to <a
href="../_breathe_autogen/file/field_8hxx.html#_CPPv4I00E10getUniform8BoutRealRK1TbRKNSt6stringE"
class="reference internal" title="getUniform"><span class="pre"><code
class="sourceCode cpp">getUniform<span class="op">()</span></code></span></a>
will return a <span class="pre">`BoutReal`</span>.

</div>

The use of <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4N11Coordinates11FieldMetricE"
class="reference internal" title="Coordinates::FieldMetric"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>FieldMetric</code></span></a>
has been followed through the rest of the code base. If a metric
component enters an expression that previously contained only
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> and
<a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv48BoutReal"
class="reference internal" title="BoutReal"><span class="pre"><code
class="sourceCode cpp">BoutReal</code></span></a> types, the result is
now a <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4N11Coordinates11FieldMetricE"
class="reference internal" title="Coordinates::FieldMetric"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>FieldMetric</code></span></a>.
This means that functions that previously both took and returned a
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> now return a <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4N11Coordinates11FieldMetricE"
class="reference internal" title="Coordinates::FieldMetric"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>FieldMetric</code></span></a>
(we could have chosen to make the return type
<span class="pre">`auto`</span> instead and rely on the compiler to
deduce the correct type, but we have chosen to make the dependence on
the metric dimensionality more explicit).

Because almost any operation on a vector involves the metric, the
individual components of
<a href="../_breathe_autogen/file/vector2d_8hxx.html#_CPPv48Vector2D"
class="reference internal" title="Vector2D"><span class="pre"><code
class="sourceCode cpp">Vector2D</code></span></a> are now also of type
<a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4N11Coordinates11FieldMetricE"
class="reference internal" title="Coordinates::FieldMetric"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>FieldMetric</code></span></a>.
Realistically, the use of
<a href="../_breathe_autogen/file/vector2d_8hxx.html#_CPPv48Vector2D"
class="reference internal" title="Vector2D"><span class="pre"><code
class="sourceCode cpp">Vector2D</code></span></a> in a model making use
of 3D metrics is probably ill-advised.

</div>

<div id="indexing" class="section">

#### Indexing<a href="#indexing" class="headerlink"
title="Permalink to this heading">#</a>

3D metrics also requires changes in how fields are indexed. In
<span class="pre">`BOUT_FOR`</span> loops, generally no changes are
required, as they already do The Right Thing. In other cases, simply
changing, for example,
<span class="pre">`dx(x,`</span>` `<span class="pre">`y)`</span> to
<span class="pre">`dx(x,`</span>` `<span class="pre">`y,`</span>` `<span class="pre">`z)`</span>
is sufficient: in the 2D metric case, the third index is accepted and
discarded.

Many methods and operators have been upgraded to deal with 3D metrics.
For example, the <a
href="../_breathe_autogen/file/laplacexz-petsc_8hxx.html#_CPPv414LaplaceXZpetsc"
class="reference internal" title="LaplaceXZpetsc"><span
class="pre"><code
class="sourceCode cpp">LaplaceXZpetsc</code></span></a> implementation
has been modified to deal with non-zero
<span class="pre">`g_{xz}`</span> terms.

</div>

<div id="fixme-when-coordinates-refactored" class="section">

#### FIXME WHEN COORDINATES REFACTORED<a href="#fixme-when-coordinates-refactored" class="headerlink"
title="Permalink to this heading">#</a>

In order to simplify a lot of code, the call to <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4N11Coordinates8geometryEbb"
class="reference internal" title="Coordinates::geometry"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>geometry<span class="op">()</span></code></span></a>,
which calculates the connection coefficients <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv4N11Coordinates5G1_11E"
class="reference internal" title="Coordinates::G1_11"><span
class="pre"><code
class="sourceCode cpp">Coordinates<span class="op">::</span>G1_11</code></span></a>
and so on, has been moved out of the <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv411Coordinates"
class="reference internal" title="Coordinates"><span class="pre"><code
class="sourceCode cpp">Coordinates</code></span></a> constructor. This
is because computing the coefficients involves derivatives which
requires <a
href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv411Coordinates"
class="reference internal" title="Coordinates"><span class="pre"><code
class="sourceCode cpp">Coordinates</code></span></a> and causes all
sorts of headaches and shims. As most users do not call the constructor
themselves anyway, this change should not be much of an issue.

</div>

</div>

<div id="incompatibilities" class="section">

### Incompatibilities<a href="#incompatibilities" class="headerlink"
title="Permalink to this heading">#</a>

Many features of BOUT++ have been written assuming an axisymmetric
coordinate system. Once 3D metrics are enabled, this is no longer
(necessarily) true which breaks several features. For instance, many of
the Laplacian inversion solvers use intrinsically 2D methods, and so are
not available when using 3D metrics. Most of these features are runtime
options, and therefore will throw an exception if you try to use them.
To get a list of available Laplacian solvers, for example, you can pass
the <span class="pre">`--list-laplacians`</span> flag to a compiled
BOUT++ executable, which will print all the Laplacian solvers, noting
which are unavailable and why.

Several boundary conditions are also incompatible with 3D metrics,
unfortunately at the time of writing there is no easy way to list those
that are. Several of these, such as
<span class="pre">`zerolaplace`</span> have no alternative
implementations, so this may mean it is not possible to run a given
model with 3D metrics.

There are a few tests that don’t work with 3D metrics, mostly because
they rely on one of the above incompatible methods or operators.

There is a preprocessor macro,
<span class="pre">`BOUT_USE_METRIC_3D`</span>, and a
<span class="pre">`constexpr`</span>` `<span class="pre">`bool`</span>,
<a
href="../_breathe_autogen/file/build__config_8hxx.html#_CPPv4N4bout5build13use_metric_3dE"
class="reference internal" title="bout::build::use_metric_3d"><span
class="pre"><code
class="sourceCode cpp">bout<span class="op">::</span>build<span class="op">::</span>use_metric_3d</code></span></a>,
which can be used to guard code that doesn’t compile or work with 3D
metrics, or perhaps needs to be handled differently.

Caution should be exercised with FFT-based methods. Technically, FFTs do
work with 3D metrics, but will not give the correct answer with
non-constant <span class="pre">`dz`</span>.

</div>

</div>

</div>

<div class="prev-next-area">

<a href="running_bout.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Running BOUT++

</div>

<a href="physics_models.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

BOUT++ physics models

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#d-metrics" class="reference internal nav-link">3D Metrics</a>
  - <a href="#changes" class="reference internal nav-link">Changes</a>
    - <a href="#types" class="reference internal nav-link">Types</a>
    - <a href="#indexing" class="reference internal nav-link">Indexing</a>
    - <a href="#fixme-when-coordinates-refactored"
      class="reference internal nav-link">FIXME WHEN COORDINATES
      REFACTORED</a>
  - <a href="#incompatibilities"
    class="reference internal nav-link">Incompatibilities</a>

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
