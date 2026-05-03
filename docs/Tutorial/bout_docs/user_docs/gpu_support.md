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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/gpu_support.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/gpu_support.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/gpu_support.rst"
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

# GPU support

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#examples" class="reference internal nav-link">Examples</a>
- <a href="#cmake-configuration" class="reference internal nav-link">CMake
  configuration</a>
- <a href="#single-index-operators"
  class="reference internal nav-link">Single index operators</a>
- <a href="#coordinatesaccessor"
  class="reference internal nav-link">CoordinatesAccessor</a>
- <a href="#memory-allocation-and-umpire"
  class="reference internal nav-link">Memory allocation and Umpire</a>
- <a href="#future-work" class="reference internal nav-link">Future
  work</a>
  - <a href="#indices" class="reference internal nav-link">Indices</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="gpu-support" class="section">

<span id="sec-gpusupport"></span>

# GPU support<a href="#gpu-support" class="headerlink"
title="Permalink to this heading">#</a>

This section describes work in progress to develop GPU support in BOUT++
models. It includes both configuration and compilation on GPU systems,
but also ways to write physics models which are designed to give higher
performance. These methods may also be beneficial for CPU architectures,
but have fewer safety checks, less functionality and run-time
flexibility than the field operators.

To use the single index operators and the
<span class="pre">`BOUT_FOR_RAJA`</span> loop macro:

<div class="highlight-cpp notranslate">

<div class="highlight">

    #include "bout/single_index_ops.hxx"
    #include "bout/rajalib.hxx"

</div>

</div>

To run parts of a physics model RHS function on a GPU, the basic outline
of the code is to (optionally) first copy any class member variables
which will be used in the loop into local variables (see below for an
alternative method):

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto _setting = setting; // Create a local variable to capture

</div>

</div>

Then create a <a
href="../_breathe_autogen/file/field__accessor_8hxx.html#_CPPv4I_8CELL_LOC0E13FieldAccessor"
class="reference internal" title="FieldAccessor"><span class="pre"><code
class="sourceCode cpp">FieldAccessor</code></span></a> to efficiently
access field and coordinate system data inside the loop:

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto n_acc = FieldAccessor<>(n);
    auto phi_acc = FieldAccessor<>(phi);

</div>

</div>

There are also
<span class="pre">``` Field2DAccessor``s ```</span>` `<span class="pre">`for`</span>` `<span class="pre">`accessing`</span>` `<span class="pre">``` ``Field2D ```</span>
types. If fields are staggered, then the expected location should be
passed as a template parameter:

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto Jpar_acc = FieldAccessor<CELL_YLOW>(Jpar);

</div>

</div>

which enables the cell location to be checked in the operators at
compile time rather than run time.

Finally the loop itself can be written something like:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BOUT_FOR_RAJA(i, region) {
      ddt(n_acc)[i] = -bracket(phi_acc, n_acc, i) - 2 * DDZ(n_acc, i);
      /* ... */
    };

</div>

</div>

Note the semicolon after the closing brace, which is needed because this
is the body of a lambda function. Inside the body of the loop, the
operators like <span class="pre">`bracket`</span> and
<span class="pre">`DDZ`</span> calculate the derivatives at a single
index <span class="pre">`i`</span>. These are “single index operators\`
and are defined in <span class="pre">`bout/single_index_ops.hxx`</span>.

Any class member variables which are used inside the loop must be
captured as a local variable. If this is not done, then the code will
probably compile, but may produce an illegal memory access error at
runtime on the GPU. To capture the class member, you can copy any class
member variables which will be used in the loop into local variables:

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto _setting = setting; // Create a local variable to capture

</div>

</div>

and then use <span class="pre">`_setting`</span> rather than
<span class="pre">`setting`</span> inside the loop. Alternatively, add
variables to be captured to a CAPTURE argument to the
<span class="pre">`BOUT_FOR_RAJA`</span> loop:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BOUT_FOR_RAJA(i, region, CAPTURE(setting)) {
      ddt(n_acc)[i] = -bracket(phi_acc, n_acc, i) - 2 * DDZ(n_acc, i);
      /* ... code which uses `setting` ... */
    };

</div>

</div>

If RAJA is not available, the <span class="pre">`BOUT_FOR_RAJA`</span>
macro will revert to <span class="pre">`BOUT_FOR`</span>. For testing,
this can be forced by defining <span class="pre">`DISABLE_RAJA`</span>
before including <span class="pre">`bout/rajalib.hxx`</span>.

Note: An important difference between
<span class="pre">`BOUT_FOR`</span> and
<span class="pre">`BOUT_FOR_RAJA`</span> (apart from the closing
semicolon) is that the type of the index <span class="pre">`i`</span> is
different inside the loop: <span class="pre">`BOUT_FOR`</span> uses
<span class="pre">`SpecificInd`</span> types (typically
<span class="pre">`Ind3D`</span>), but
<span class="pre">`BOUT_FOR_RAJA`</span> uses
<span class="pre">`int`</span>. <span class="pre">`SpecificInd`</span>
can be explicitly cast to <span class="pre">`int`</span> so use
<span class="pre">`static_cast<int>(i)`</span> to ensure that it’s an
integer both with and without RAJA. This might (hopefully) change in
future versions.

<div id="examples" class="section">

## Examples<a href="#examples" class="headerlink"
title="Permalink to this heading">#</a>

The <span class="pre">`blob2d-outerloop`</span> example is the simplest
one which uses single index operators and (optionally) RAJA. It should
solve the same set of equations, with the same inputs, as
<span class="pre">`blob2d`</span>.

<span class="pre">`hasegawa-wakatani-3d`</span> is a 3D turbulence
model, typically solved in a slab geometry.

<span class="pre">`elm-pb-outerloop`</span> is a much more complicated
model, which should solve the same equations, and have the same inputs,
as <span class="pre">`elm-pb`</span>. Note that there are some
differences:

- The numerical methods used in <span class="pre">`elm-pb`</span> can be
  selected at run-time, and typically include WENO schemes e.g W3. In
  <span class="pre">`elm-pb-outerloop`</span> the methods are fixed to
  C2 in all cases.

- The equations solved by <span class="pre">`elm-pb`</span> can be
  changed by modifying input settings. To achieve higher performance,
  <span class="pre">`elm-pb-outerloop`</span> does this at compile time.
  There are checks to ensure that the code has been compiled with flags
  consistent with the input settings. See the README file for more
  details.

Notes:

- When RAJA is used in a physics model, all members of the PhysicsModel
  should be public. If this is not done, then a compiler error like
  “error: The enclosing parent function (“rhs”) for an extended
  \_\_device\_\_ lambda cannot have private or protected access within
  its class” may be encountered.

- Class member variables cannot in general be used inside a RAJA loop:
  The <span class="pre">`this`</span> pointer is captured by value in
  the lambda function, not the value of the member variable. When the
  member variable is used on the GPU, the
  <span class="pre">`this`</span> pointer is generally not valid (e.g.
  on NERSC Cori GPUs). Some architectures have Address Translation
  Services (ATS) which enable host pointers to be resolved on the GPU.

</div>

<div id="cmake-configuration" class="section">

## CMake configuration<a href="#cmake-configuration" class="headerlink"
title="Permalink to this heading">#</a>

To compile BOUT++ components into GPU kernels a few different pieces
need to be configured to work together: RAJA, Umpire, and a CUDA
compiler.

<span id="tab-gpusupport-cmake"></span>

<table id="id1" class="table">
<caption><span class="caption-number">Table 4 </span><span
class="caption-text">Useful CMake configuration settings</span><a
href="#id1" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Description</p></th>
<th class="head"><p>Default</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>BOUT_ENABLE_RAJA</p></td>
<td><p>Include RAJA header, use RAJA loops</p></td>
<td><p>Off</p></td>
</tr>
<tr class="row-odd">
<td><p>BOUT_ENABLE_UMPIRE</p></td>
<td><p>Use Umpire to allocate Array memory</p></td>
<td><p>Off</p></td>
</tr>
<tr class="row-even">
<td><p>BOUT_ENABLE_CUDA</p></td>
<td><p>Compile with nvcc compiler</p></td>
<td><p>Off</p></td>
</tr>
<tr class="row-odd">
<td><p>CUDA_ARCH</p></td>
<td><p>Set CUDA architecture to compile for</p></td>
<td><p>compute_70,code=sm_70</p></td>
</tr>
<tr class="row-even">
<td><p>BOUT_ENABLE_WARNINGS</p></td>
<td><p>nvcc has incompatible warning flags</p></td>
<td><p>On (turn Off for CUDA)</p></td>
</tr>
</tbody>
</table>

</div>

<div id="single-index-operators" class="section">

## Single index operators<a href="#single-index-operators" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ models are typically implemented using operations which take in
fields, perform an operation, and return a new field. These are
convenient, but the consequence is that an expression like
<span class="pre">`Grad_par(phi)`</span>` `<span class="pre">`*`</span>` `<span class="pre">`B0`</span>
contains two loops over the domain, one for the gradient operator
<span class="pre">`Grad_par`</span>, and another for the multiplication.
Complex models can contain dozens of these loops. When using OpenMP or
GPU threads this results in many small kernels being launched, and
typically poor efficiency.

The “single index operators” in BOUT++ offer a way to manually combine
loops over the domain into a smaller number of loops. It is perhaps less
convenient than a template expression system might be, but considerably
easier to debug and maintain.

Single index operators have the same name as field operations, but the
interface has two key differences:

1.  The functions take an index as an additional final argument

2.  Rather than fields (e.g Field2D, Field3D types), these operate on
    field accessors (Field2DAccessor, FieldAccessor types). These offer
    faster, more direct, but less safe access to the underlying data
    arrays.

For example a simple field operation:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D phi;
    ...
    Field3D result = DDX(phi);

</div>

</div>

might be written as:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D phi;
    ...
    Field3D result;

    // Create accessors for fast (unsafe) data access
    auto phi_acc = FieldAccessor<>(phi);
    auto result_acc = FieldAccessor<>(result);

    BOUT_FOR_RAJA(i, result.region("RGN_NOBNDRY")) {
      result_acc[i] = DDX(phi_acc, i);
    }

</div>

</div>

For a simple example like this the code is harder to read, and there is
not much benefit because there is one loop over the domain in both
cases. The benefit becomes more apparent when multiple operations are
combined.

The operators are implemented in a header file, so that they can be
inlined. These are in
<span class="pre">`include/bout/single_index_ops.hxx`</span>. Table
<a href="#tab-gpusupport-singleindexfunctions"
class="reference internal"><span class="std std-numref">Table
5</span></a> lists the functions which have been implemented.

<span id="tab-gpusupport-singleindexfunctions"></span>

<table id="id2" class="table">
<caption><span class="caption-number">Table 5 </span><span
class="caption-text">Single index operator functions</span><a
href="#id2" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Function</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>DDX(F3D, i)</p></td>
<td><p>Derivative in X with <span class="pre"><code
class="docutils literal notranslate">ddx:first=C2</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>DDY(F3D, i)</p></td>
<td><p>Derivative in Y with <span class="pre"><code
class="docutils literal notranslate">ddy:first=C2</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>DDZ(F3D, i)</p></td>
<td><p>Derivative in Z with <span class="pre"><code
class="docutils literal notranslate">ddz:first=C2</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p>bracket(F2D, F3D, i)</p></td>
<td><p>bracket(F2D, F3D, BRACKET_ARAKAWA)</p></td>
</tr>
<tr class="row-even">
<td><p>bracket(F3D, F3D, i)</p></td>
<td><p>bracket(F3D, F2D, BRACKET_ARAKAWA)</p></td>
</tr>
<tr class="row-odd">
<td><p>Delp2(F3D, i)</p></td>
<td><p>Delp2 with useFFT=false, C2 central diff.</p></td>
</tr>
<tr class="row-even">
<td><p>Div_par_Grad_par(F3D, i)</p></td>
<td><p>2nd order central difference</p></td>
</tr>
<tr class="row-odd">
<td><p>b0xGrad_dot_Grad(F3D, F2D, i)</p></td>
<td><p>C2 central diff. for all derivatives</p></td>
</tr>
<tr class="row-even">
<td><p>b0xGrad_dot_Grad(F2D, F3D, i)</p></td>
<td><p>C2 central diff. for all derivatives</p></td>
</tr>
<tr class="row-odd">
<td><p>D2DY2(F3D, i)</p></td>
<td><p>C2 2nd-order derivative <span class="pre"><code
class="docutils literal notranslate">ddy:second=C2</code></span></p></td>
</tr>
<tr class="row-even">
<td><p>Grad_par(F3D, i)</p></td>
<td><p>C2 derivative, <span class="pre"><code
class="docutils literal notranslate">ddy:first=C2</code></span></p></td>
</tr>
</tbody>
</table>

Note that for efficiency the method used in the single index operators
cannot be changed at runtime: The numerical method is fixed at compile
time. The <span class="pre">`DDX`</span> single index operator, for
example, always uses 2nd order central difference.

Unit tests which ensure that the single index operators produce the same
result as the original field operations are in
<span class="pre">`tests/unit/include/bout/test_single_index_ops.cxx`</span>.
Note that there are limitations to these unit tests, in particular the
geometry may not be fully exercised. Additional errors are possible when
combining these methods, or porting code from field operations to single
index operations. It is therefore essential to have integrated tests and
benchmarks for each model implementation: Unit tests are necessary but
not sufficient for correctness.

</div>

<div id="coordinatesaccessor" class="section">

## CoordinatesAccessor<a href="#coordinatesaccessor" class="headerlink"
title="Permalink to this heading">#</a>

The differential operators used in physics models typically need access
to grid spacing (eg. dx), non-uniform grid corrections (e.g. d1_dx), and
multiple coordinate system fields (metric tensor components). When a
<span class="pre">`FieldAccessor`</span> is created from a field, it
uses the field’s coordinate system to create a
<span class="pre">`CoordinateAccessor`</span>, which provides fast
access to this extra data.

The coordinate system data is usually stored in separate arrays, so that
many different pointers would need to be passed to the CUDA kernels to
use this data directly. This was found to cause compilation errors with
<span class="pre">`nvcc`</span> along the lines of “Formal parameter
space overflowed”.

The <span class="pre">`CoordinatesAccessor`</span> reduces the number of
parameters (data pointers) by packing all
<span class="pre">`Coordinates`</span> data (grid spacing, metric tensor
components) into a single array. The ordering of this data in the array
has not been optimised, but is currently striped: Data for the same grid
cell is close to each other in memory. Some guidance on memory layout
can be found <a
href="https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#coalesced-access-to-global-memory"
class="reference external">on the NVidia website</a> and might be used
to improve performance in future. It is likely that the results might be
architecture dependent.

To minimise the number of times this data needs to be copied from
individual fields into the single array, and then copied from CPU to
GPU,
<span class="pre">``` CoordinatesAccessor``s ```</span>` `<span class="pre">`are`</span>` `<span class="pre">`cached.`</span>` `<span class="pre">`A`</span>` `<span class="pre">`map`</span>` `<span class="pre">``` (``coords_store ```</span>
defined in <span class="pre">`coordinates_accessor.cxx`</span>)
associates <span class="pre">`Array<BoutReal>`</span> objects
(containing the array of data) to <span class="pre">`Coordinates`</span>
pointers. If a <span class="pre">`CoordinatesAccessor`</span> is
constructed with a <span class="pre">`Coordinates`</span> pointer which
is in the cache, then the previously created
<span class="pre">`Array`</span> data is used. Some care is therefore
needed if the <span class="pre">`Coordinates`</span> data is modified,
to ensure that a new <span class="pre">`CoordinatesAccessor`</span> data
array is created by clearing the old data from the cache.

The easiest way to clear the cache is to call the static function
<span class="pre">`CoordinatesAccessor::clear()`</span>, which will
delete all arrays from the cache. To remove a single
<span class="pre">`Coordinates`</span> key from the cache, pass the
pointer to
<span class="pre">`CoordinatesAccessor::clear(coordinates_ptr)`</span>.
In both cases the number of keys removed from the cache will be
returned.

</div>

<div id="memory-allocation-and-umpire" class="section">

## Memory allocation and Umpire<a href="#memory-allocation-and-umpire" class="headerlink"
title="Permalink to this heading">#</a>

Using GPUs effectively requires keeping track of even more levels of
memory than usual. An extra complication is that trying to dereference a
pointer to CPU memory while on the GPU device (or a device memory
pointer while on the CPU) will result in a segfault on some
architectures, while other architectures with Address Translation
Services (ATS) will trap this access and transfer the required memory
addresses, with a corresponding performance penalty for the time this
transfer takes.

At a low level, CPU and GPU memory are allocated separately, with
buffers being explicitly synchronised by data transfer. To do this
allocation, and automatically move data from CPU to GPU or back when
needed, BOUT++ uses <a href="https://github.com/LLNL/Umpire"
class="reference external">Umpire</a> . In order for this to work with
data structures or multiple indirections, all steps in chain of pointers
must be in the right place (CPU or device). Allocating everything with
Umpire is the easiest way to ensure that this is the case.

The calculations done in BOUT++ typically involve using blocks of memory
of the a few common sizes, and the same calculations are done every
timestep on different data as the simulation state evolves. BOUT++
therefore uses an arena system to store arrays which have been released,
so that they can be re-used rather than deleted and allocated. Allocator
chaining is used: If the object pool runs out of arrays of the requested
size, then a new one is allocated using Umpire or the native allocator
(<span class="pre">`new`</span>).

This is a <a href="https://www.youtube.com/watch?v=d1DpVR0tw0U"
class="reference external">good talk by John Lakos [ACCU 2017] on memory
allocators</a>

</div>

<div id="future-work" class="section">

## Future work<a href="#future-work" class="headerlink"
title="Permalink to this heading">#</a>

<div id="indices" class="section">

### Indices<a href="#indices" class="headerlink"
title="Permalink to this heading">#</a>

Setting up a RAJA loop to run on a GPU is still cumbersome and
inefficient due to the need to transform CPU data structures into a form
which can be passed to and used on the GPU. In the
<span class="pre">`bout/rajalib.hxx`</span> header there is code like:

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto indices = n.getRegion("RGN_NOBNDRY").getIndices();
     Array<int> _ob_i_ind(indices.size()); // Backing data is device safe
     // Copy indices into Array
     for(auto i = 0; i < indices.size(); i++) {
       _ob_i_ind[i] = indices[i].ind;
     }
     // Get the raw pointer to use on the device
     auto _ob_i_ind_raw = &_ob_i_ind[0];

</div>

</div>

which is creating a raw pointer
(<span class="pre">`_ob_i_ind_raw`</span>) to an array of
<span class="pre">``` int``s ```</span>` `<span class="pre">`which`</span>` `<span class="pre">`are`</span>` `<span class="pre">`allocated`</span>` `<span class="pre">`using`</span>` `<span class="pre">`Umpire.`</span>` `<span class="pre">`The`</span>` `<span class="pre">`original`</span>` `<span class="pre">``` ``indices ```</span>
are allocated using <span class="pre">`new`</span> and are inside a C++
<span class="pre">`std::vector`</span>. The RAJA loop then uses this
array like this:

<div class="highlight-cpp notranslate">

<div class="highlight">

    RAJA::forall<EXEC_POL>(RAJA::RangeSegment(0, indices.size()), [=] RAJA_DEVICE(int id) {
      int i = _ob_i_ind_raw[id]; // int passed to loop body

</div>

</div>

This code has several issues:

1.  It is inefficiently creating a new
    <span class="pre">`Array<int>`</span> and copying the indices into
    it every time. In almost every case the indices will not be
    changing.

2.  The indices lose their type information: Inside the loop an index
    into a 3D field has the same type as an index into a 2D field (both
    <span class="pre">`int`</span>). This is a possible source of bugs.

Possible fixes include:

1.  Changing <span class="pre">`Region`</span> to store indices inside
    an <span class="pre">`Array`</span> rather than
    <span class="pre">`std::vector`</span>. This would ensure that the
    <span class="pre">`SpecificInd`</span> objects were allocated with
    Umpire. Then the GPU-side code could use
    <span class="pre">`SpecificInd`</span> objects for index conversion
    and type safety. This would still leave the problem of extracting
    the pointer from the <span class="pre">`Array`</span>, and would
    send more information to the GPU
    (<span class="pre">`SpecificInd`</span> contains 3
    <span class="pre">`ints`</span>).

2.  The indices could be stored in two forms, one the
    <span class="pre">`std::vector`</span> as now, and alongside it an
    <span class="pre">`Array<int>`</span>.

In either case it might be useful to have an
<span class="pre">`ArrayAccessor`</span> type, which is just a range
(begin/end pair, or pointer and length), and doesn’t take ownership of
the array data.

Then the code might look something like:

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto indices_acc = ArrayAccessor<>(n.getRegion("RGN_NOBNDRY").getIndices());

    RAJA::forall<EXEC_POL>(RAJA::RangeSegment(0, indices.size()), [=] RAJA_DEVICE(int id) {
      const Ind3D& i = indices_acc[id];

</div>

</div>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="testing.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Testing

</div>

<a href="adios2.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

ADIOS2 support

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#examples" class="reference internal nav-link">Examples</a>
- <a href="#cmake-configuration" class="reference internal nav-link">CMake
  configuration</a>
- <a href="#single-index-operators"
  class="reference internal nav-link">Single index operators</a>
- <a href="#coordinatesaccessor"
  class="reference internal nav-link">CoordinatesAccessor</a>
- <a href="#memory-allocation-and-umpire"
  class="reference internal nav-link">Memory allocation and Umpire</a>
- <a href="#future-work" class="reference internal nav-link">Future
  work</a>
  - <a href="#indices" class="reference internal nav-link">Indices</a>

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
