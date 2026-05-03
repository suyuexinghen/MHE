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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/invertable_operator.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/invertable_operator.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/invertable_operator.rst"
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

# Invertable operators

<div id="print-main-content">

<div id="jb-print-toc">

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="invertable-operators" class="section">

<span id="sec-invertable"></span>

# Invertable operators<a href="#invertable-operators" class="headerlink"
title="Permalink to this heading">#</a>

A common problem in physics models is solve a matrix equation of the
form

<div class="math notranslate nohighlight">

\\\underline{\underline{A}} \cdot \underline{x} = \underline{b}\\

</div>

for the unknown
<span class="math notranslate nohighlight">\\\underline{x}\\</span>.
Here
<span class="math notranslate nohighlight">\\\underline{\underline{A}}\\</span>
represents some differential operator subject to boundary conditions. A
specific example is the set of Laplacian operators described in
<a href="laplacian.html#sec-laplacian" class="reference internal"><span
class="std std-ref">Laplacian inversion</span></a>.

Whilst specific tools are provided to deal with Laplacian and parallel
Helmholtz like equations these do not capture all possible systems and
are typically implemented (at least partially) independently of the
finite difference representation of the forward operators provided by
the rest of BOUT++. To address this a class
<span class="pre">`InvertableOperator`</span> has been implemented that
allows the user to define a generic differential operator and provides a
simple (for the user) method to invert the operator to find
<span class="math notranslate nohighlight">\\\underline{x}\\</span>.
This class currently relies on PETSc to provide the inversion
functionality and hence is not available when configuring without PETSc
support. It is available in the namespace
<span class="pre">`bout::inversion`</span>.

There is an example in
<span class="pre">`examples/invertable_operator`</span> that uses the
class to solve a simple Laplacian operator and compares to the specific
Laplacian inversion solvers.

The <span class="pre">`InvertableOperator`</span> class is templated on
the field type of the operator (essentially defining the domain over
which the problem exists). To define the operator that the
<span class="pre">`InvertableOperator`</span> instances represents one
should use the
<span class="pre">`InvertableOperator::setOperatorFunction`</span>
method. This takes a function of signature
<span class="pre">`std::function<T(const`</span>` `<span class="pre">`T&)>`</span>.
This can be a <span class="pre">`std::function`</span>, compatible
function pointer, lambda or a functor. The last of these allows more
complicated functions that use a local context. For example the
following code snippet demonstrates a functor that stores several
auxilliary <span class="pre">`Field3D`</span> variables used in the
<span class="pre">`operator()`</span> call:

<div class="highlight-cpp notranslate">

<div class="highlight">

    struct myLaplacian {
      Field3D D = 1.0, C = 1.0, A = 0.0;

      // Drop C term for now
      Field3D operator()(const Field3D &input) {
        Timer timer("invertable_operator_operate");
        Field3D result = A * input + D * Delp2(input);

        // Ensure boundary points are set appropriately as given by the input field.
        result.setBoundaryTo(input);

        return result;
      };
    };

</div>

</div>

A more complete example is

<div class="highlight-cpp notranslate">

<div class="highlight">

    struct myLaplacian {
      Field3D D = 1.0, C = 1.0, A = 0.0;

      // Drop C term for now
      Field3D operator()(const Field3D &input) {
        Timer timer("invertable_operator_operate");
        Field3D result = A * input + D * Delp2(input);

        // Ensure boundary points are set appropriately as given by the input field.
        result.setBoundaryTo(input);

        return result;
      };
    };

    bout::inversion::InveratbleOperator<Field3D> solver;
    myLaplacian laplacianOperator;
    laplacianOperator.A = 1.0;
    laplacianOperator.B = 2.0;

    // Set the function defining the operator
    solver.setOperatorFunction(laplacianOperator);

    // Perform initial setup
    solver.setup();

    // Now invert the operator for a given right hand side.
    Field3D rhs = 3.0*x;
    auto solution = solver.invert(rhs);

</div>

</div>

The PETSc backend solver is an iterative solver. It can be controlled
through the usual PETSc command line options. Note we define the options
prefix here to be <span class="pre">`-invertable`</span>, so instead of
<span class="pre">`-ksp_type`</span> one would use
<span class="pre">`-invertable_ksp_type`</span> for example.

By default the solver caches the result to use as the initial guess for
the next call to <span class="pre">`invert`</span>. There is an overload
of <span class="pre">`invert`</span> that takes a second field, which is
used to set the initial guess to use in that call.

The routine <span class="pre">`setOperatorFunction`</span> takes the
function by value, and hence subsequent changes to the functor will not
be reflected in the operator without a further call to
<span class="pre">`setOperatorFunction`</span>. For example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    using bout::inversion;
    InvertableOperator<Field3D> solver;
    myLaplacian laplacianOperator;
    laplacianOperator.A = 1.0;
    laplacianOperator.B = 2.0;

    // Set the function defining the operator
    solver.setOperatorFunction(laplacianOperator);

    // Perform initial setup
    solver.setup();

    // This does not change the operator represented by
    // solver yet.
    laplacianOperator.B = -1.0;

    // This call updates the function used by solver
    // and hence the operator is update to reflect the state
    // of laplacianOperator.
    solver.setOperatorFunction(laplacianOperator);

</div>

</div>

The class provides a <span class="pre">`reportTime`</span> method that
reports the time spent in various parts of the class. Note that by
including
<span class="pre">`Timer`</span>` `<span class="pre">`timer("invertable_operator_operate");`</span>
in the function representing the operator
<span class="pre">`reportTime`</span> will include the time spent
actually applying the operator.

The class provides both <span class="pre">`apply`</span> and
<span class="pre">`operator()`</span> methods that can be used to apply
the operator to a field. For example the following should be equivalent
to no operation:

<div class="highlight-cpp notranslate">

<div class="highlight">

    // Here result should == input, at least in the main simulation domain
    auto result = solver(solver.invert(input));

</div>

</div>

The class provides a <span class="pre">`verify`</span> method that
checks that applying the operator to the calculated inverse returns the
input field within some tolerance.

It’s also possible to register a function to use as a preconditioner. By
default this is the same as the full operator function.

</div>

<div class="prev-next-area">

<a href="nonlocal.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Nonlocal heat flux models

</div>

<a href="petsc.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

PETSc solvers

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
