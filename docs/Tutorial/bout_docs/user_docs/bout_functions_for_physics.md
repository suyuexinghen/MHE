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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/bout_functions_for_physics.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/bout_functions_for_physics.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/bout_functions_for_physics.rst"
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

# BOUT++ functions (alphabetical)

<div id="print-main-content">

<div id="jb-print-toc">

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="bout-functions-alphabetical" class="section">

# BOUT++ functions (alphabetical)<a href="#bout-functions-alphabetical" class="headerlink"
title="Permalink to this heading">#</a>

This is a list of functions which can be called by users writing a
physics module. For a full list of functions, see the Reference manual,
DOxygen documentation, and source code.

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`abs(Field`</span>` `<span class="pre">`|`</span>` `<span class="pre">`Vector)`</span>

- <div class="line">

  <span class="pre">`(Communicator).add(Field`</span>` `<span class="pre">`|`</span>` `<span class="pre">`Vector)`</span>

  </div>

  <div class="line">

  Add a variable to a communicator object.

  </div>

- <span class="pre">`apply_boundary(Field.`</span>` `<span class="pre">`name)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`b0xGrad_dot_Grad(Field,`</span>` `<span class="pre">`Field,`</span>` `<span class="pre">`CELL_LOC)`</span>

- <span class="pre">`bout_solve(Field,`</span>` `<span class="pre">`Field,`</span>` `<span class="pre">`name)`</span>

- <span class="pre">`bout_solve(Vector,`</span>` `<span class="pre">`Vector,`</span>` `<span class="pre">`name)`</span>

- <div class="line">

  <span class="pre">`(Communicator).clear()`</span>

  </div>

  <div class="line">

  Remove all variables from a Communicator object

  </div>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`cos(Field)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`cosh(Field)`</span>

- <span class="pre">`Vector`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Curl(Vector)`</span>

- <div class="line">

  <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Delp2(Field)`</span>

  </div>

  <div class="line">

  <span class="math notranslate nohighlight">\\\nabla\_\perp^2\\</span>
  operator

  </div>

- <div class="line">

  <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Div(Vector)`</span>

  </div>

  <div class="line">

  Divergence of a vector

  </div>

- <div class="line">

  <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Div_par(Field`</span>` `<span class="pre">`f)`</span>

  </div>

  <div class="line">

  Parallel divergence
  <span class="math notranslate nohighlight">\\B_0\mathbf{b}\cdot\nabla(f
  / B_0)\\</span>

  </div>

- <span class="pre">`dump.add(Field,`</span>` `<span class="pre">`name,`</span>` `<span class="pre">`1/0)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`filter(Field,`</span>` `<span class="pre">`modenr)`</span>

- <div class="line">

  <span class="pre">`geometry_derivs()`</span>

  </div>

  <div class="line">

  Calculates useful quantities from the metric tensor. Call this every
  time the metric tensor is changed.

  </div>

- <span class="pre">`Vector`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Grad(Field)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Grad_par(Field)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Grad2_par2(Field)`</span>

- <div class="line">

  <span class="pre">`grid_load(BoutReal,`</span>` `<span class="pre">`name)`</span>

  </div>

  <div class="line">

  Load a scalar real from the grid file

  </div>

- <div class="line">

  <span class="pre">`grid_load2d(Field2D,`</span>` `<span class="pre">`name)`</span>

  </div>

  <div class="line">

  Load a 2D scalar field from the grid file

  </div>

- <div class="line">

  <span class="pre">`grid_load3d(Field3D,`</span>` `<span class="pre">`name)`</span>

  </div>

  <div class="line">

  Load a 3D scalar field from the grid file

  </div>

- <span class="pre">`invert_laplace(Field`</span>` `<span class="pre">`input,`</span>` `<span class="pre">`Field`</span>` `<span class="pre">`output,`</span>` `<span class="pre">`flags,`</span>` `<span class="pre">`Field2D`</span>` `<span class="pre">`*A)`</span>

- <div class="line">

  <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`invert_parderiv(Field2D|BoutReal`</span>` `<span class="pre">`A,`</span>` `<span class="pre">`Field2D|BoutReal`</span>` `<span class="pre">`B,`</span>` `<span class="pre">`Field3D`</span>` `<span class="pre">`r)`</span>

  </div>

  <div class="line">

  Inverts an equation
  <span class="pre">`A*x`</span>` `<span class="pre">`+`</span>` `<span class="pre">`B*Grad2_par2(x)`</span>` `<span class="pre">`=`</span>` `<span class="pre">`r`</span>

  </div>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Laplacian(Field)`</span>

- <span class="pre">`Field3D`</span>` `<span class="pre">`=`</span>` `<span class="pre">`low_pass(Field3D,`</span>` `<span class="pre">`max_modenr)`</span>

- <span class="pre">`BoutReal`</span>` `<span class="pre">`=`</span>` `<span class="pre">`max(Field)`</span>

- <span class="pre">`BoutReal`</span>` `<span class="pre">`=`</span>` `<span class="pre">`min(Field)`</span>

- <div class="line">

  <span class="pre">`msg_stack.pop(`</span>` `<span class="pre">`|int)`</span>

  </div>

  <div class="line">

  Remove a message from the top of the stack. If a message ID is passed,
  removes all messages back to that point.

  </div>

- <div class="line">

  <span class="pre">`int`</span>` `<span class="pre">`=`</span>` `<span class="pre">`msg_stack.push(format,`</span>` `<span class="pre">`...)`</span>

  </div>

  <div class="line">

  Put a message onto the stack. Works like
  <span class="pre">`printf`</span> (and
  <span class="pre">`output.write`</span>).

  </div>

- <div class="line">

  <span class="pre">`options.get(name,`</span>` `<span class="pre">`variable,`</span>` `<span class="pre">`default)`</span>

  </div>

  <div class="line">

  Get an integer, real or boolean value from the options file. If not in
  the file, the default value is used. The value used is printed to log
  file.

  </div>

- <span class="pre">`options.setSection(name)`</span> Set the section
  name in the input file

- <div class="line">

  <span class="pre">`output`</span>` `<span class="pre">`<`</span>` `<span class="pre">`<`</span>` `<span class="pre">`values`</span>

  </div>

  <div class="line">

  Behaves like cout for stream output

  </div>

- <div class="line">

  <span class="pre">`output.write(format,`</span>` `<span class="pre">`...)`</span>

  </div>

  <div class="line">

  Behaves like printf for formatted output

  </div>

- <div class="line">

  <span class="pre">`(Communicator).receive()`</span>

  </div>

  <div class="line">

  Receive data from other processors. Must be preceded by a
  <span class="pre">`send`</span> call.

  </div>

- <div class="line">

  <span class="pre">`(Communicator).run()`</span>

  </div>

  <div class="line">

  Sends and receives data.

  </div>

- <div class="line">

  <span class="pre">`(Communicator).send()`</span>

  </div>

  <div class="line">

  Sends data to other processors (and posts receives). This must be
  followed by a call to <span class="pre">`receive()`</span> before
  calling send again, or adding new variables.

  </div>

- <span class="pre">`(Field3D).setLocation(CELL_LOC)`</span>

- <span class="pre">`(Field3D).ShiftZ(bool)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`sin(Field)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`sinh(Field)`</span>

- <div class="line">

  <span class="pre">`solver.setPrecon(PhysicsPrecon)`</span>

  </div>

  <div class="line">

  Set a preconditioner function

  </div>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`sqrt(Field)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`tan(Field)`</span>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`tanh(Field)`</span>

- <div class="line">

  <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`V_dot_Grad(Vector`</span>` `<span class="pre">`v,`</span>` `<span class="pre">`Field`</span>` `<span class="pre">`f)`</span>

  </div>

  <div class="line">

  Calculates an advection term
  <span class="math notranslate nohighlight">\\\mathbf{v}\cdot\nabla
  f\\</span>

  </div>

- <div class="line">

  <span class="pre">`Vector`</span>` `<span class="pre">`=`</span>` `<span class="pre">`V_dot_Grad(Vector`</span>` `<span class="pre">`v,`</span>` `<span class="pre">`Vector`</span>` `<span class="pre">`u)`</span>

  </div>

  <div class="line">

  Advection term
  <span class="math notranslate nohighlight">\\\mathbf{v}\cdot\nabla\mathbf{u}\\</span>

  </div>

- <span class="pre">`Field`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Vpar_Grad_par(Field`</span>` `<span class="pre">`v,`</span>` `<span class="pre">`Field`</span>` `<span class="pre">`f)`</span>

- <div class="line">

  <span class="pre">`Field3D`</span>` `<span class="pre">`=`</span>` `<span class="pre">`where(Field2D`</span>` `<span class="pre">`test,`</span>` `<span class="pre">`Field|BoutReal`</span>` `<span class="pre">`gt0,`</span>` `<span class="pre">`Field|BoutReal`</span>` `<span class="pre">`lt0)`</span>

  </div>

  <div class="line">

  Chooses between two values, depending on sign of
  <span class="pre">`test`</span>.

  </div>

</div>

<div class="prev-next-area">

<a href="../api_reference.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

API reference

</div>

<a href="../_breathe_autogen/filelist.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

File list

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
