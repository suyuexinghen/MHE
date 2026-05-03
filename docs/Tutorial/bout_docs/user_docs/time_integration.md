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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/time_integration.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/time_integration.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/time_integration.rst"
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

# Time integration

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#options" class="reference internal nav-link">Options</a>
- <a href="#cvode" class="reference internal nav-link">CVODE</a>
- <a href="#imex-bdf2" class="reference internal nav-link">IMEX-BDF2</a>
- <a href="#split-rk" class="reference internal nav-link">Split-RK</a>
- <a href="#backward-euler-snes"
  class="reference internal nav-link">Backward Euler - SNES</a>
  - <a href="#basic-configuration" class="reference internal nav-link">Basic
    Configuration</a>
  - <a href="#timestepping-modes"
    class="reference internal nav-link">Timestepping Modes</a>
  - <a href="#adaptive-timestepping"
    class="reference internal nav-link">Adaptive Timestepping</a>
    - <a href="#residual-ratio" class="reference internal nav-link">Residual
      Ratio</a>
    - <a href="#threshold-controller"
      class="reference internal nav-link">Threshold Controller</a>
  - <a href="#output-trigger" class="reference internal nav-link">Output
    trigger</a>
  - <a
    href="#pseudo-transient-continuation-and-switched-evolution-relaxation"
    class="reference internal nav-link">Pseudo-Transient Continuation and
    Switched Evolution Relaxation</a>
    - <a href="#ser-timestep-strategy" class="reference internal nav-link">SER
      timestep strategy</a>
    - <a href="#pid-controller" class="reference internal nav-link">PID
      Controller</a>
  - <a href="#jacobian-finite-difference-with-coloring"
    class="reference internal nav-link">Jacobian Finite Difference with
    Coloring</a>
    - <a href="#jacobian-coloring-stencil"
      class="reference internal nav-link">Jacobian coloring stencil</a>
- <a href="#diagnostics-and-monitoring"
  class="reference internal nav-link">Diagnostics and Monitoring</a>
  - <a href="#summary-of-solver-options"
    class="reference internal nav-link">Summary of solver options</a>
- <a href="#ode-integration" class="reference internal nav-link">ODE
  integration</a>
- <a href="#preconditioning"
  class="reference internal nav-link">Preconditioning</a>
- <a href="#jacobian-function"
  class="reference internal nav-link">Jacobian function</a>
- <a href="#dae-constraint-equations"
  class="reference internal nav-link">DAE constraint equations</a>
- <a href="#id4" class="reference internal nav-link">IMEX-BDF2</a>
- <a href="#monitoring-the-simulation-output"
  class="reference internal nav-link">Monitoring the simulation output</a>
- <a href="#implementation-internals"
  class="reference internal nav-link">Implementation internals</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="time-integration" class="section">

<span id="sec-time-integration"></span>

# Time integration<a href="#time-integration" class="headerlink"
title="Permalink to this heading">#</a>

<div id="options" class="section">

<span id="sec-timeoptions"></span>

## Options<a href="#options" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ can be compiled with several different time-integration solvers ,
and at minimum should have Runge-Kutta (RK4) and PVODE (BDF/Adams)
solvers available.

The solver library used is set using the
<span class="pre">`solver:type`</span> option, so either in BOUT.inp:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [solver]
    type = rk4  # Set the solver to use

</div>

</div>

or on the command line by adding
<span class="pre">`solver:type=pvode`</span> for example:

<div class="highlight-bash notranslate">

<div class="highlight">

    mpirun -np 4 ./2fluid solver:type=rk4

</div>

</div>

**NB**: Make sure there are no spaces around the “=” sign:
<span class="pre">`solver:type`</span>` `<span class="pre">`=pvode`</span>
won’t work (probably). Table
<a href="#tab-solvers" class="reference internal"><span
class="std std-numref">Table 10</span></a> gives a list of time
integration solvers, along with any compile-time options needed to make
the solver available.

<span id="tab-solvers"></span>

<table id="id8" class="table">
<caption><span class="caption-number">Table 10 </span><span
class="caption-text">Available time integration solvers</span><a
href="#id8" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Description</p></th>
<th class="head"><p>Compile options</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>euler</p></td>
<td><p>Euler explicit method (example only)</p></td>
<td><p>Always available</p></td>
</tr>
<tr class="row-odd">
<td><p>rk4</p></td>
<td><p>Runge-Kutta 4th-order explicit method</p></td>
<td><p>Always available</p></td>
</tr>
<tr class="row-even">
<td><p>rkgeneric</p></td>
<td><p>Generic Runge Kutta explicit methods</p></td>
<td><p>Always available</p></td>
</tr>
<tr class="row-odd">
<td><p>rk3ssp</p></td>
<td><p>3rd-order Strong Stability Preserving</p></td>
<td><p>Always available</p></td>
</tr>
<tr class="row-even">
<td><p>splitrk</p></td>
<td><p>Split RK3-SSP and RK-Legendre</p></td>
<td><p>Always available</p></td>
</tr>
<tr class="row-odd">
<td><p>pvode</p></td>
<td><p>1998 PVODE with BDF method</p></td>
<td><p>Always available</p></td>
</tr>
<tr class="row-even">
<td><p>cvode</p></td>
<td><p>SUNDIALS CVODE. BDF and Adams methods</p></td>
<td><p>-DBOUT_USE_SUNDIALS=ON</p></td>
</tr>
<tr class="row-odd">
<td><p>ida</p></td>
<td><p>SUNDIALS IDA. DAE solver</p></td>
<td><p>-DBOUT_USE_SUNDIALS=ON</p></td>
</tr>
<tr class="row-even">
<td><p>arkode</p></td>
<td><p>SUNDIALS ARKODE IMEX solver</p></td>
<td><p>-DBOUT_USE_SUNDIALS=ON</p></td>
</tr>
<tr class="row-odd">
<td><p>petsc</p></td>
<td><p>PETSc TS methods</p></td>
<td><p>-DBOUT_USE_PETSC=ON</p></td>
</tr>
<tr class="row-even">
<td><p>imexbdf2</p></td>
<td><p>IMEX-BDF2 scheme</p></td>
<td><p>-DBOUT_USE_PETSC=ON</p></td>
</tr>
<tr class="row-odd">
<td><p>beuler / snes</p></td>
<td><p>Backward Euler with SNES solvers</p></td>
<td><p>-DBOUT_USE_PETSC=ON</p></td>
</tr>
</tbody>
</table>

Each solver can have its own settings which work in slightly different
ways, but some common settings and which solvers they are used in are
given in table
<a href="#tab-solveropts" class="reference internal"><span
class="std std-numref">Table 11</span></a>.

<span id="tab-solveropts"></span>

<table id="id9" class="table">
<caption><span class="caption-number">Table 11 </span><span
class="caption-text">Time integration solver options</span><a
href="#id9" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Option</p></th>
<th class="head"><p>Description</p></th>
<th class="head"><p>Solvers used</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>atol</p></td>
<td><p>Absolute tolerance</p></td>
<td><p>rk4, pvode, cvode, ida, imexbdf2, beuler</p></td>
</tr>
<tr class="row-odd">
<td><p>rtol</p></td>
<td><p>Relative tolerance</p></td>
<td><p>rk4, pvode, cvode, ida, imexbdf2, beuler</p></td>
</tr>
<tr class="row-even">
<td><p>mxstep</p></td>
<td><p>Maximum internal steps per output step</p></td>
<td><p>rk4, imexbdf2</p></td>
</tr>
<tr class="row-odd">
<td><p>max_timestep</p></td>
<td><p>Maximum timestep</p></td>
<td><p>rk4, cvode</p></td>
</tr>
<tr class="row-even">
<td><p>timestep</p></td>
<td><p>Starting timestep</p></td>
<td><p>rk4, euler, imexbdf2, beuler</p></td>
</tr>
<tr class="row-odd">
<td><p>adaptive</p></td>
<td><p>Adapt timestep? (Y/N)</p></td>
<td><p>rk4, imexbdf2</p></td>
</tr>
<tr class="row-even">
<td><p>use_precon</p></td>
<td><p>Use a preconditioner? (Y/N)</p></td>
<td><p>pvode, cvode, ida, imexbdf2</p></td>
</tr>
<tr class="row-odd">
<td><p>mudq, mldq</p></td>
<td><p>BBD preconditioner settings</p></td>
<td><p>pvode, cvode, ida</p></td>
</tr>
<tr class="row-even">
<td><p>mukeep, mlkeep</p></td>
<td></td>
<td></td>
</tr>
<tr class="row-odd">
<td><p>maxl</p></td>
<td><p>Maximum number of linear iterations</p></td>
<td><p>cvode, imexbdf2</p></td>
</tr>
<tr class="row-even">
<td><p>max_nonlinear_iterations</p></td>
<td><p>Maximum number of nonlinear iterations</p></td>
<td><p>cvode, imexbdf2, beuler</p></td>
</tr>
<tr class="row-odd">
<td><p>use_jacobian</p></td>
<td><p>Use user-supplied Jacobian? (Y/N)</p></td>
<td><p>cvode</p></td>
</tr>
<tr class="row-even">
<td><p>adams_moulton</p></td>
<td><p>Use Adams-Moulton method rather than BDF</p></td>
<td><p>cvode</p></td>
</tr>
<tr class="row-odd">
<td><p>diagnose</p></td>
<td><p>Collect and print additional diagnostics</p></td>
<td><p>cvode, imexbdf2, beuler</p></td>
</tr>
</tbody>
</table>

<div class="line">

  

</div>

The most commonly changed options are the absolute and relative solver
tolerances, <span class="pre">`atol`</span> and
<span class="pre">`rtol`</span> which should be varied to check
convergence.

</div>

<div id="cvode" class="section">

## CVODE<a href="#cvode" class="headerlink"
title="Permalink to this heading">#</a>

The most commonly used time integration solver is CVODE, or its older
version PVODE. CVODE has several advantages over PVODE, including better
support for preconditioning and diagnostics.

Enabling diagnostics output using
<span class="pre">`solver:diagnose=true`</span> will print a set of
outputs for each timestep similar to:

<div class="highlight-bash notranslate">

<div class="highlight">

    CVODE: nsteps 51, nfevals 69, nniters 65, npevals 126, nliters 79
        -> Newton iterations per step: 1.274510e+00
        -> Linear iterations per Newton iteration: 1.215385e+00
        -> Preconditioner evaluations per Newton: 1.938462e+00
        -> Last step size: 1.026792e+00, order: 5
        -> Local error fails: 0, nonlinear convergence fails: 0
        -> Stability limit order reductions: 0
    1.000e+01        149       2.07e+01    78.3    0.0   10.0    0.9   10.8

</div>

</div>

When diagnosing slow performance, key quantities to look for are
nonlinear convergence failures, and the number of linear iterations per
Newton iteration. A large number of failures, and close to 5 linear
iterations per Newton iteration are a sign that the linear solver is not
converging quickly enough, and hitting the default limit of 5
iterations. This limit can be modified using the
<span class="pre">`solver:maxl`</span> setting. Giving it a large value
e.g. <span class="pre">`solver:maxl=1000`</span> will show how many
iterations are needed to solve the linear system. If the number of
iterations becomes large, this may be an indication that the system is
poorly conditioned, and a preconditioner might help improve performance.
See <a href="#sec-preconditioning" class="reference internal"><span
class="std std-ref">Preconditioning</span></a>.

CVODE can set constraints to keep some quantities positive,
non-negative, negative or non-positive. These constraints can be
activated by setting the option
<span class="pre">`solver:apply_positivity_constraints=true`</span>, and
then in the section for a certain variable (e.g.
<span class="pre">`[n]`</span>), setting the option
<span class="pre">`positivity_constraint`</span> to one of
<span class="pre">`positive`</span>,
<span class="pre">`non_negative`</span>,
<span class="pre">`negative`</span>, or
<span class="pre">`non_positive`</span>.

Additional options can be used to modify the behaviour of the linear and
nonlinear solvers:

- <span class="pre">`cvode_nonlinear_convergence_coef`</span> specifies
  the safety factor used in the nonlinear convergence test. Passed as a
  parameter to <a
  href="https://sundials.readthedocs.io/en/latest/cvodes/Usage/SIM.html#c.CVodeSetNonlinConvCoef"
  class="reference external">CVodeSetNonlinConvCoef</a>.

- <span class="pre">`cvode_linear_convergence_coef`</span> specifies the
  factor by which the Krylov linear solver’s convergence test constant
  is reduced from the nonlinear solver test constant. Passed as a
  parameter to <a
  href="https://sundials.readthedocs.io/en/latest/cvodes/Usage/SIM.html#c.CVodeSetEpsLin"
  class="reference external">CVodeSetEpsLin</a>.

The linear solver type can be set using the
<span class="pre">`linear_solver`</span> option. Valid choices include
<span class="pre">`gmres`</span> (the default),
<span class="pre">`fgmres`</span>, <span class="pre">`tfqmr`</span>,
<span class="pre">`bcgs`</span>.

</div>

<div id="imex-bdf2" class="section">

## IMEX-BDF2<a href="#imex-bdf2" class="headerlink"
title="Permalink to this heading">#</a>

This is an IMplicit-EXplicit time integration solver, which allows the
evolving function to be split into two parts: one which has relatively
long timescales and can be integrated using explicit methods, and a part
which has short timescales and must be integrated implicitly. The order
of accuracy is variable (up to 4th-order currently), and an adaptive
timestep can be used.

To use the IMEX-BDF2 solver, set the solver type to
<span class="pre">`imexbdf2`</span>, e.g. on the command-line add
<span class="pre">`solver:type=imexbdf2`</span> or in the options file:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [solver]
    type = imexbdf2

</div>

</div>

The order of the method is set to 2 by default, but can be increased up
to a maximum of 4:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [solver]
    type = imexbdf2
    maxOrder = 3

</div>

</div>

This is a multistep method, so the state from previous steps are used to
construct the next one. This means that at the start, when there are no
previous steps, the order is limited to 1 (backwards Euler method).
Similarly, the second step is limited to order 2, and so on. At the
moment the order is not adapted, so just increases until reaching
<span class="pre">`maxOrder`</span>.

At each step the explicit (non-stiff) part of the function is called,
and combined with previous timestep values. The implicit part of the
function is then solved using PETSc’s SNES, which consists of a
nonlinear solver (usually modified Newton iteration), each iteration of
which requires a linear solve (usually GMRES). Settings which affect
this implicit part of the solve are:

<table class="table">
<thead>
<tr class="row-odd">
<th class="head"><p>Option</p></th>
<th class="head"><p>Default</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>atol</p></td>
<td><p>1e-16</p></td>
<td><p>Absolute tolerance on SNES solver</p></td>
</tr>
<tr class="row-odd">
<td><p>rtol</p></td>
<td><p>1e-10</p></td>
<td><p>Relative tolerance on SNES solver</p></td>
</tr>
<tr class="row-even">
<td><p>max_nonlinear_it</p></td>
<td><p>5</p></td>
<td><p>Maximum number of nonlinear iterations If adaptive timestepping
is used then failure will cause timestep reduction</p></td>
</tr>
<tr class="row-odd">
<td><p>maxl</p></td>
<td><p>20</p></td>
<td><p>Maximum number of linear iterations If adaptive, failure will
cause timestep reduction</p></td>
</tr>
<tr class="row-even">
<td><p>predictor</p></td>
<td><p>1</p></td>
<td><p>Starting guess for the nonlinear solve Specifies order of
extrapolating polynomial</p></td>
</tr>
<tr class="row-odd">
<td><p>use_precon</p></td>
<td><p>false</p></td>
<td><p>Use user-supplied preconditioner?</p></td>
</tr>
<tr class="row-even">
<td><p>matrix_free</p></td>
<td><p>true</p></td>
<td><p>Use Jacobian-free methods? If false, calculates the Jacobian
matrix using finite difference</p></td>
</tr>
<tr class="row-odd">
<td><p>use_coloring</p></td>
<td><p>true</p></td>
<td><p>If not matrix free, use coloring to speed up calculation of the
Jacobian</p></td>
</tr>
</tbody>
</table>

Note that the SNES tolerances <span class="pre">`atol`</span> and
<span class="pre">`rtol`</span> are set very conservatively by default.
More reasonable values might be 1e-10 and 1e-5, but this must be
explicitly asked for in the input options.

The predictor extrapolates from previous timesteps to get a starting
estimate for the value at the next timestep. This estimate is then used
to initialise the SNES nonlinear solve. The value is the order of the
extrapolating polynomial, so 1 (the default) is a linear extrapolation
from the last two steps, 0 is the same as the last step. A value of -1
uses the explicit update to the state as the starting guess, i.e.
assuming that the implicit part of the problem is small. This is usually
not a good guess.

To diagnose what is happening in the time integration, for example to
see why it is failing to converge or why timesteps are small, there are
two settings which can be set to <span class="pre">`true`</span> to
enable:

- <span class="pre">`diagnose`</span> outputs a summary at each output
  time, similar to CVODE. This contains information like the last
  timestep, average number of iterations and number of convergence
  failures.

- <span class="pre">`verbose`</span> prints information at every
  internal step, with more information on the values used to modify
  timesteps, and the reasons for solver failures.

By default adaptive timestepping is turned on, using several factors to
modify the timestep:

1.  If the nonlinear solver (SNES) fails to converge, either because it
    diverges or exceeds the iteration limits
    <span class="pre">`max_nonlinear_its`</span> or
    <span class="pre">`maxl`</span>. Reduces the timestep by 2 and tries
    again, giving up after 10 failures.

2.  Every <span class="pre">`nadapt`</span> internal timesteps (default
    4), the error is checked by taking the timestep twice: Once with the
    current order of accuracy, and once with one order of accuracy
    lower. The difference between the solutions is then used to estimate
    the timestep required to achieve the required tolerances. If this is
    much larger or smaller than the current timestep, then the timestep
    is modified.

3.  The timestep is kept within user-specified maximum and minimum
    ranges.

The options which control this behaviour are:

<table class="table">
<thead>
<tr class="row-odd">
<th class="head"><p>Option</p></th>
<th class="head"><p>Default</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>adaptive</p></td>
<td><p>true</p></td>
<td><p>Turns on adaptive timestepping</p></td>
</tr>
<tr class="row-odd">
<td><p>timestep</p></td>
<td><p>output timestep</p></td>
<td><p>If adaptive sets the starting timestep. If not adaptive, timestep
fixed at this value</p></td>
</tr>
<tr class="row-even">
<td><p>dtMin</p></td>
<td><p>1e-10</p></td>
<td><p>Minimum timestep</p></td>
</tr>
<tr class="row-odd">
<td><p>dtMax</p></td>
<td><p>output timestep</p></td>
<td><p>Maximum timestep</p></td>
</tr>
<tr class="row-even">
<td><p>mxstep</p></td>
<td><p>1e5</p></td>
<td><p>Maximum number of internal steps between outputs</p></td>
</tr>
<tr class="row-odd">
<td><p>nadapt</p></td>
<td><p>4</p></td>
<td><p>How often is error checked and timestep adjusted?</p></td>
</tr>
<tr class="row-even">
<td><p>adaptRtol</p></td>
<td><p>1e-3</p></td>
<td><p>Target relative tolerance for adaptive timestep</p></td>
</tr>
<tr class="row-odd">
<td><p>scaleCushDown</p></td>
<td><p>1.0</p></td>
<td><p>Timestep scale factor below which the timestep is modified. By
default the timestep is always reduced</p></td>
</tr>
<tr class="row-even">
<td><p>scaleCushUp</p></td>
<td><p>1.5</p></td>
<td><p>Minimum timestep scale factor based on adaptRtol above which the
timestep will be modified. Currently the timestep increase is limited to
25%</p></td>
</tr>
</tbody>
</table>

</div>

<div id="split-rk" class="section">

## Split-RK<a href="#split-rk" class="headerlink"
title="Permalink to this heading">#</a>

The <span class="pre">`splitrk`</span> solver type uses Strang splitting
to combine two explicit Runge Kutta schemes:

1.  <a href="https://doi.org/10.1016/j.jcp.2013.08.021"
    class="reference external">2nd order Runge-Kutta-Legendre method</a>
    for the diffusion (parabolic) part. These schemes use multiple
    stages to increase stability, rather than accuracy; this is always
    2nd order, but the stable timestep for diffusion problems increases
    as the square of the number of stages. The number of stages is an
    input option, and can be arbitrarily large.

2.  3rd order SSP-RK3 scheme for the advection (hyperbolic) part <a
    href="http://www.cscamm.umd.edu/tadmor/pub/linear-stability/Gottlieb-Shu-Tadmor.SIREV-01.pdf"
    class="reference external">http://www.cscamm.umd.edu/tadmor/pub/linear-stability/Gottlieb-Shu-Tadmor.SIREV-01.pdf</a>

Each timestep consists of

1.  A half timestep of the diffusion part

2.  A full timestep of the advection part

3.  A half timestep of the diffusion part

Options to control the behaviour of the solver are:

<table class="table">
<thead>
<tr class="row-odd">
<th class="head"><p>Option</p></th>
<th class="head"><p>Default</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>timestep</p></td>
<td><p>output timestep</p></td>
<td><p>If adaptive sets the starting timestep. If not adaptive, timestep
fixed at this value</p></td>
</tr>
<tr class="row-odd">
<td><p>nstages</p></td>
<td><p>10</p></td>
<td><p>Number of stages in RKL step. Must be &gt; 1</p></td>
</tr>
<tr class="row-even">
<td><p>diagnose</p></td>
<td><p>false</p></td>
<td><p>Print diagnostic information</p></td>
</tr>
</tbody>
</table>

And the adaptive timestepping options:

<table class="table">
<thead>
<tr class="row-odd">
<th class="head"><p>Option</p></th>
<th class="head"><p>Default</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>adaptive</p></td>
<td><p>true</p></td>
<td><p>Turn on adaptive timestepping</p></td>
</tr>
<tr class="row-odd">
<td><p>atol</p></td>
<td><p>1e-10</p></td>
<td><p>Absolute tolerance</p></td>
</tr>
<tr class="row-even">
<td><p>rtol</p></td>
<td><p>1e-5</p></td>
<td><p>Relative tolerance</p></td>
</tr>
<tr class="row-odd">
<td><p>max_timestep</p></td>
<td><p>output timestep</p></td>
<td><p>Maximum internal timestep</p></td>
</tr>
<tr class="row-even">
<td><p>max_timestep_change</p></td>
<td><p>2</p></td>
<td><p>Maximum factor by which the timestep by which the time step can
be changed at each step</p></td>
</tr>
<tr class="row-odd">
<td><p>mxstep</p></td>
<td><p>1000</p></td>
<td><p>Maximum number of internal steps before output</p></td>
</tr>
<tr class="row-even">
<td><p>adapt_period</p></td>
<td><p>1</p></td>
<td><p>Number of internal steps between tolerance checks</p></td>
</tr>
</tbody>
</table>

</div>

<div id="backward-euler-snes" class="section">

## Backward Euler - SNES<a href="#backward-euler-snes" class="headerlink"
title="Permalink to this heading">#</a>

The <span class="pre">`beuler`</span> or <span class="pre">`snes`</span>
solver type (either name can be used) is a PETSc-based implicit solver
for finding steady-state solutions to systems of partial differential
equations. It supports multiple solution strategies including backward
Euler timestepping, direct Newton iteration, and Pseudo-Transient
Continuation (PTC) with Switched Evolution Relaxation (SER).

<div id="basic-configuration" class="section">

### Basic Configuration<a href="#basic-configuration" class="headerlink"
title="Permalink to this heading">#</a>

The SNES solver is configured through the
<span class="pre">`[solver]`</span> section of the input file:

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    type = snes

    # Nonlinear solver settings
    snes_type = newtonls          # anderson, newtonls, newtontr, nrichardson
    atol = 1e-7                   # Absolute tolerance
    rtol = 1e-6                   # Relative tolerance
    stol = 1e-12                  # Solution change tolerance
    max_nonlinear_iterations = 20 # Maximum SNES iterations per solve

    # Linear solver settings
    ksp_type = fgmres             # Linear solver: gmres, bicgstab, etc.
    maxl = 20                     # Maximum linear iterations
    pc_type = ilu                 # Preconditioner: ilu, bjacobi, hypre, etc.

</div>

</div>

</div>

<div id="timestepping-modes" class="section">

### Timestepping Modes<a href="#timestepping-modes" class="headerlink"
title="Permalink to this heading">#</a>

The solver supports several timestepping strategies controlled by
<span class="pre">`equation_form`</span>:

**Backward Euler (default)**  
Standard implicit backward Euler method. Good for general timestepping.

<div class="highlight-ini notranslate">

<div class="highlight">

    equation_form = rearranged_backward_euler  # Default

</div>

</div>

This method has low accuracy in time but its dissipative properties are
helpful when evolving to steady state solutions.

**Direct Newton**  
Solves the steady-state problem F(u) = 0 directly without timestepping.

<div class="highlight-ini notranslate">

<div class="highlight">

    equation_form = direct_newton

</div>

</div>

This method is unlikely to converge unless the system is very close to
steady state.

**Pseudo-Transient Continuation**  
Uses pseudo-time to guide the solution to steady state. Recommended for
highly nonlinear problems where Newton’s method fails.

<div class="highlight-ini notranslate">

<div class="highlight">

    equation_form = pseudo_transient

</div>

</div>

This uses the same form as rearranged_backward_euler, but the time step
can be different for each cell.

</div>

<div id="adaptive-timestepping" class="section">

### Adaptive Timestepping<a href="#adaptive-timestepping" class="headerlink"
title="Permalink to this heading">#</a>

When
<span class="pre">`equation_form`</span>` `<span class="pre">`=`</span>` `<span class="pre">`rearranged_backward_euler`</span>
(default), the solver uses global timestepping with adaptive timestep
control based on nonlinear iteration count.

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    type = snes
    equation_form = rearranged_backward_euler

    # Initial and maximum timesteps
    timestep = 1.0                         # Initial timestep
    max_timestep = 1e10                    # Upper limit on timestep
    dt_min_reset = 1e-6                    # Reset the solver when timestep < this

    # Timestep adaptation
    timestep_control = pid_nonlinear_its
    target_its = 7        # Target number of nonlinear iterations
    kP = 0.7              # Proportional gain
    kI = 0.3              # Integral gain
    kD = 0.2              # Derivative gain

</div>

</div>

This uses a PID controller that adjusts the timestep to maintain
approximately <span class="pre">`target_its`</span> nonlinear iterations
per solve.

<div id="residual-ratio" class="section">

#### Residual Ratio<a href="#residual-ratio" class="headerlink"
title="Permalink to this heading">#</a>

This adjusts the timestep using the ratio of global residuals and a
timestep factor:

<div class="math notranslate nohighlight">

\\dt_n = r dt\_{n-1} \frac{||F(X\_{n-1})||}{||F(X\_{n})||\\

</div>

so that as the residual falls the timestep
<span class="math notranslate nohighlight">\\dt\\</span> is increased.
The <span class="math notranslate nohighlight">\\r\\</span> parameter is
input option <span class="pre">`timestep_factor`</span> that has default
value 1.1.

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    timestep_control = residual_ratio  # Use global residual
    timestep_factor = 1.1              # Constant timestep factor

</div>

</div>

</div>

<div id="threshold-controller" class="section">

#### Threshold Controller<a href="#threshold-controller" class="headerlink"
title="Permalink to this heading">#</a>

An alternative adaptive strategy uses thresholds in nonlinear iterations
to adjust the timestep:

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    timestep_control = threshold_nonlinear_its
    lower_its = 3                          # Increase dt if iterations < this
    upper_its = 10                         # Decrease dt if iterations > this
    timestep_factor_on_lower_its = 1.4     # Growth factor
    timestep_factor_on_upper_its = 0.9     # Reduction factor
    timestep_factor_on_failure = 0.5       # Reduction on convergence failure

</div>

</div>

The adjustments are less smooth than the default PID method, but the
timestep is changed less frequently. This may enable the Jacobian and
preconditioner to be used for more iterations.

</div>

</div>

<div id="output-trigger" class="section">

### Output trigger<a href="#output-trigger" class="headerlink"
title="Permalink to this heading">#</a>

The default behavior is to save outputs at a regular time interval, as
BOUT++ solvers do. This is desirable when performing time-dependent
simulations, but for simulations that are trying to get to steady state
a better measure of progress is reduction of the global residual (norm
of the time-derivatives of the system).

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    output_trigger = residual_ratio  # Trigger an output based on the ratio of residuals
    output_residual_ratio = 0.5     # Output when global residual is multiplied by this

</div>

</div>

With this choice, each output has a global residual that is less than or
equal to <span class="pre">`output_residual_ratio`</span> times the last
output global residual. This provides a way of measuring progress to
steady state that is independent of time integration accuracy.

</div>

<div id="pseudo-transient-continuation-and-switched-evolution-relaxation"
class="section">

### Pseudo-Transient Continuation and Switched Evolution Relaxation<a
href="#pseudo-transient-continuation-and-switched-evolution-relaxation"
class="headerlink" title="Permalink to this heading">#</a>

When
<span class="pre">`equation_form`</span>` `<span class="pre">`=`</span>` `<span class="pre">`pseudo_transient`</span>
the solver uses Pseudo-Transient Continuation (PTC). This is a robust
numerical technique for solving steady-state problems that are too
nonlinear for direct Newton iteration. Instead of solving the
steady-state system **F(u) = 0** directly, PTC solves a modified
time-dependent problem:

<div class="math notranslate nohighlight">

\\M(u) \frac{\partial u}{\partial \tau} + F(u) = 0\\

</div>

where <span class="math notranslate nohighlight">\\\tau\\</span> is a
pseudo-time variable (not physical time) and
<span class="math notranslate nohighlight">\\M(u)\\</span> is a
preconditioning matrix. As
<span class="math notranslate nohighlight">\\\tau \to \infty\\</span>,
the solution converges to the steady state **F(u) = 0**.

The key advantage of PTC is that it transforms a difficult root-finding
problem into a sequence of easier initial value problems. Poor initial
guesses that would cause Newton’s method to diverge can still reach the
solution via a stable pseudo-transient path.

The Switched Evolution Relaxation (SER) method is a spatially adaptive
variant of PTC that allows each cell to use a different pseudo-timestep
<span class="math notranslate nohighlight">\\\Delta\tau_i\\</span>. The
timestep in each cell adapts based on the local residual, allowing the
algorithm to take large timesteps in well-behaved regions (fast
convergence), while taking small timesteps in difficult regions (stable
advancement). The the same
<span class="math notranslate nohighlight">\\\Delta\tau_i\\</span> is
used for all equations (density, momentum, energy etc.) within each
cell. This maintains coupling between temperature, pressure, and
composition through the equation of state.

**Key parameters:**

<span class="pre">`pseudo_max_ratio`</span> (default: 2.0)  
Maximum allowed ratio of timesteps between neighboring cells. This
prevents sharp spatial gradients in convergence rate.

**Example PTC configuration:**

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    type = snes
    equation_form = pseudo_transient

    timestep = 1.0                # Initial timestep

    # SER parameters
    timestep_control = pid_nonlinear_its  # Scale timesteps based on iterations
    pseudo_max_ratio = 2.0         # Limit neighbor timestep ratio

    # Tolerances
    atol = 1e-7
    rtol = 1e-6
    stol = 1e-12

</div>

</div>

<div id="ser-timestep-strategy" class="section">

#### SER timestep strategy<a href="#ser-timestep-strategy" class="headerlink"
title="Permalink to this heading">#</a>

After each nonlinear solve the timesteps in each cell are adjusted. The
strategy used depends on the <span class="pre">`pseudo_strategy`</span>
option:

**inverse_residual** (default)

If
<span class="pre">`pseudo_strategy`</span>` `<span class="pre">`=`</span>` `<span class="pre">`inverse_residual`</span>
then the timestep is inversely proportional to the RMS residual in each
cell. <span class="pre">`pseudo_alpha`</span> (default: 100 × atol ×
timestep) Controls the relationship between residual and timestep. The
local timestep is computed as:

<div class="math notranslate nohighlight">

\\\Delta\tau_i = \frac{\alpha}{||R_i||}\\

</div>

Larger values allow more aggressive timestepping. The default is to use
a fixed <span class="pre">`pseudo_alpha`</span> but a better strategy is
to enable the PID controller that adjusts this parameter based on the
nonlinear solver convergence.

The timestep is limited to be between
<span class="pre">`dt_min_reset`</span> and
<span class="pre">`max_timestep`</span>. In addition the timestep is
limited between 0.67 × previous timestep and 1.5 × previous timestep, to
limit sudden changes in timestep.

In practice this strategy seems to work well, though problems could
arise when residuals become very small.

**history_based**

When
<span class="pre">`pseudo_strategy`</span>` `<span class="pre">`=`</span>` `<span class="pre">`history_based`</span>
the history of residuals within each cell is used to adjust the
timestep. The key parameters are:

<span class="pre">`pseudo_growth_factor`</span> (default: 1.1)  
Factor by which timestep increases when residual decreases successfully.

<span class="pre">`pseudo_reduction_factor`</span> (default: 0.5)  
Factor by which timestep decreases when residual increases (step
rejected).

This method may be less susceptible to fluctuations when residuals
become small, but tends to be slower to converge when residuals are
large.

**hybrid**

When
<span class="pre">`pseudo_strategy`</span>` `<span class="pre">`=`</span>` `<span class="pre">`hybrid`</span>
the <span class="pre">`inverse_residual`</span> and
<span class="pre">`history_based`</span> strategies are combined: When
the residuals are large the <span class="pre">`inverse_residual`</span>
method is used, and when residuals become small the method switches to
<span class="pre">`history_based`</span>.

</div>

<div id="pid-controller" class="section">

#### PID Controller<a href="#pid-controller" class="headerlink"
title="Permalink to this heading">#</a>

When using the PTC method the PID controller can be used to dynamically
adjust <span class="pre">`pseudo_alpha`</span> depending on the
nonlinearity of the system:

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    timestep_control = pid_nonlinear_its   # Scale global timestep using PID controller
    target_its = 7        # Target number of nonlinear iterations
    kP = 0.7              # Proportional gain
    kI = 0.3              # Integral gain
    kD = 0.2              # Derivative gain

</div>

</div>

The PID controller adjusts <span class="pre">`pseudo_alpha`</span>,
scaling all cell timesteps together, to maintain approximately
<span class="pre">`target_its`</span> nonlinear iterations per solve.

With this enabled the solver uses the number of nonlinear iterations to
scale timesteps globally, and residuals to scale timesteps locally. Note
that the PID controller has no effect on the
<span class="pre">`history_based`</span> strategy because that strategy
does not use <span class="pre">`pseudo_alpha`</span>.

</div>

</div>

<div id="jacobian-finite-difference-with-coloring" class="section">

### Jacobian Finite Difference with Coloring<a href="#jacobian-finite-difference-with-coloring" class="headerlink"
title="Permalink to this heading">#</a>

The default and recommended approach for most problems:

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    use_coloring = true               # Enable (default)
    lag_jacobian = 5                  # Reuse Jacobian for this many iterations

    # Stencil shape (determines Jacobian sparsity pattern)
    stencil:taxi = 2                  # Taxi-cab distance (default)
    stencil:square = 0                # Square stencil extent
    stencil:cross = 0                 # Cross stencil extent

</div>

</div>

The coloring algorithm exploits the sparse structure of the Jacobian to
reduce the number of function evaluations needed for finite
differencing.

<div id="jacobian-coloring-stencil" class="section">

#### Jacobian coloring stencil<a href="#jacobian-coloring-stencil" class="headerlink"
title="Permalink to this heading">#</a>

The stencil used to create the Jacobian colouring can be varied,
depending on which numerical operators are in use. It is important to
note that the coloring won’t work for every problem: It assumes that
each evolving quantity is coupled to all other evolving quantities on
the same grid cell, and on all the neighbouring grid cells. If the RHS
function includes Fourier transforms, or matrix inversions (e.g.
potential solves) then these will introduce longer-range coupling and
the Jacobian calculation will give spurious results. Generally the
method will then fail to converge. Two solutions are to a) switch to
matrix-free (<span class="pre">`matrix_free=true`</span>), or b) solve
the matrix inversion as a constraint.

<span class="pre">`solver:stencil:cross`</span>` `<span class="pre">`=`</span>` `<span class="pre">`N`</span>
e.g. for N == 2

<div class="highlight-bash notranslate">

<div class="highlight">

        *
        *
    * * x * *
        *
        *

</div>

</div>

<span class="pre">`solver:stencil:square`</span>` `<span class="pre">`=`</span>` `<span class="pre">`N`</span>
e.g. for N == 2

<div class="highlight-bash notranslate">

<div class="highlight">

    * * * * *
    * * * * *
    * * x * *
    * * * * *
    * * * * *

</div>

</div>

<span class="pre">`solver:stencil:taxi`</span>` `<span class="pre">`=`</span>` `<span class="pre">`N`</span>
e.g. for N == 2

<div class="highlight-bash notranslate">

<div class="highlight">

        *
      * * *
    * * x * *
      * * *
        *

</div>

</div>

Setting
<span class="pre">`solver:force_symmetric_coloring`</span>` `<span class="pre">`=`</span>` `<span class="pre">`true`</span>,
will make sure that the jacobian colouring matrix is symmetric. This
will often include a few extra non-zeros that the stencil will miss
otherwise

</div>

</div>

</div>

<div id="diagnostics-and-monitoring" class="section">

## Diagnostics and Monitoring<a href="#diagnostics-and-monitoring" class="headerlink"
title="Permalink to this heading">#</a>

<div class="highlight-ini notranslate">

<div class="highlight">

    [solver]
    diagnose = true                # Print iteration info to screen
    diagnose_failures = true       # Detailed diagnostics on failures

</div>

</div>

When
<span class="pre">`equation_form`</span>` `<span class="pre">`=`</span>` `<span class="pre">`pseudo_transient`</span>,
the solver saves additional diagnostic fields:

- <span class="pre">`snes_pseudo_residual`</span>: Local residual in
  each cell

- <span class="pre">`snes_pseudo_timestep`</span>: Local pseudo-timestep
  in each cell

- <span class="pre">`snes_pseudo_alpha`</span>: Global timestep scaling

These can be visualized to understand convergence behavior and identify
problematic regions.

<div id="summary-of-solver-options" class="section">

### Summary of solver options<a href="#summary-of-solver-options" class="headerlink"
title="Permalink to this heading">#</a>

<table class="table">
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="row-odd">
<th class="head"><p>Option</p></th>
<th class="head"><p>Default</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>pseudo_time</p></td>
<td><p>false</p></td>
<td><p>Pseudo-Transient Continuation (PTC) method, using a different
timestep for each cell.</p></td>
</tr>
<tr class="row-odd">
<td><p>pseudo_max_ratio</p></td>
<td><ol start="2">
<li></li>
</ol></td>
<td><p>Maximum timestep ratio between neighboring cells</p></td>
</tr>
<tr class="row-even">
<td><p>snes_type</p></td>
<td><p>newtonls</p></td>
<td><p>PETSc SNES nonlinear solver (try anderson, qn)</p></td>
</tr>
<tr class="row-odd">
<td><p>ksp_type</p></td>
<td><p>gmres</p></td>
<td><p>PETSc KSP linear solver</p></td>
</tr>
<tr class="row-even">
<td><p>pc_type</p></td>
<td><p>ilu / bjacobi</p></td>
<td><p>PETSc PC preconditioner (try hypre in parallel)</p></td>
</tr>
<tr class="row-odd">
<td><p>pc_hypre_type</p></td>
<td><p>pilut</p></td>
<td><p>If <span class="pre"><code
class="docutils literal notranslate">pc_type</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">=</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">hypre</code></span>. Hypre
preconditioner type: euclid, boomeramg</p></td>
</tr>
<tr class="row-even">
<td><p>max_nonlinear_iterations</p></td>
<td><p>20</p></td>
<td><p>If exceeded, solve restarts with timestep / 2</p></td>
</tr>
<tr class="row-odd">
<td><p>maxl</p></td>
<td><p>20</p></td>
<td><p>Maximum number of linear iterations</p></td>
</tr>
<tr class="row-even">
<td><p>atol</p></td>
<td><p>1e-12</p></td>
<td><p>Absolute tolerance of SNES solve</p></td>
</tr>
<tr class="row-odd">
<td><p>rtol</p></td>
<td><p>1e-5</p></td>
<td><p>Relative tolerance of SNES solve</p></td>
</tr>
<tr class="row-even">
<td><p>upper_its</p></td>
<td><p>80% max</p></td>
<td><p>If exceeded, next timestep reduced by 10%</p></td>
</tr>
<tr class="row-odd">
<td><p>lower_its</p></td>
<td><p>50% max</p></td>
<td><p>If under this, next timestep increased by 10%</p></td>
</tr>
<tr class="row-even">
<td><p>timestep</p></td>
<td><p>1</p></td>
<td><p>Initial timestep</p></td>
</tr>
<tr class="row-odd">
<td><p>predictor</p></td>
<td><p>true</p></td>
<td><p>Use linear predictor?</p></td>
</tr>
<tr class="row-even">
<td><p>matrix_free</p></td>
<td><p>false</p></td>
<td><p>Matrix-free preconditioning?</p></td>
</tr>
<tr class="row-odd">
<td><p>matrix_free_operator</p></td>
<td><p>false</p></td>
<td><p>Use matrix free Jacobian-vector product?</p></td>
</tr>
<tr class="row-even">
<td><p>use_coloring</p></td>
<td><p>true</p></td>
<td><p>If <span class="pre"><code
class="docutils literal notranslate">matrix_free=false</code></span>,
use coloring to speed up calculation of the Jacobian elements.</p></td>
</tr>
<tr class="row-odd">
<td><p>lag_jacobian</p></td>
<td><p>50</p></td>
<td><p>Re-use the Jacobian for successive inner solves</p></td>
</tr>
<tr class="row-even">
<td><p>kspsetinitialguessnonzero</p></td>
<td><p>false</p></td>
<td><p>If true, Use previous solution as KSP initial</p></td>
</tr>
<tr class="row-odd">
<td><p>use_precon</p></td>
<td><p>false</p></td>
<td><p>If <span class="pre"><code
class="docutils literal notranslate">matrix_free=true</code></span>, use
user-supplied preconditioner? If false, the default PETSc preconditioner
is used</p></td>
</tr>
<tr class="row-even">
<td><p>diagnose</p></td>
<td><p>false</p></td>
<td><p>Print diagnostic information every iteration</p></td>
</tr>
<tr class="row-odd">
<td><p>stencil:cross stencil:square stencil:taxi</p></td>
<td><p>0 0 2</p></td>
<td><p>If <span class="pre"><code
class="docutils literal notranslate">matrix_free=false</code></span> and
<span class="pre"><code
class="docutils literal notranslate">use_coloring=true</code></span> Set
the size and shape of the Jacobian coloring stencil.</p></td>
</tr>
<tr class="row-even">
<td><p>force_symmetric_coloring</p></td>
<td><p>false</p></td>
<td><p>Ensure that the Jacobian coloring is symmetric</p></td>
</tr>
</tbody>
</table>

The predictor is linear extrapolation from the last two timesteps. It
seems to be effective, but can be disabled by setting
<span class="pre">`predictor`</span>` `<span class="pre">`=`</span>` `<span class="pre">`false`</span>.

The default <span class="pre">`newtonls`</span> SNES type can be very
effective if combined with Jacobian coloring: The coloring enables the
Jacobian to be calculated relatively efficiently; once a Jacobian matrix
has been calculated, effective preconditioners can be used to speed up
convergence.

The <a
href="https://www.mcs.anl.gov/petsc/petsc-current/docs/manualpages/SNES/SNESType.html"
class="reference external">SNES type</a> can be set through PETSc
command-line options, or in the BOUT++ options as setting
<span class="pre">`snes_type`</span>. Good choices for unpreconditioned
problems where the Jacobian is not available
(<span class="pre">`matrix_free=true`</span>) seem to be <a
href="https://www.mcs.anl.gov/petsc/petsc-current/docs/manualpages/SNES/SNESANDERSON.html#SNESANDERSON"
class="reference external">anderson</a> and <a
href="https://www.mcs.anl.gov/petsc/petsc-current/docs/manualpages/SNES/SNESQN.html#SNESQN"
class="reference external">qn</a> (quasinewton).

Preconditioner types:

1.  On one processor the ILU solver is typically very effective, and is
    usually the default

2.  The Hypre package can be installed with PETSc and used as a
    preconditioner. One of the options available in Hypre is the Euler
    parallel ILU solver. Enable with command-line args
    <span class="pre">`-pc_type`</span>` `<span class="pre">`hypre`</span>` `<span class="pre">`-pc_hypre_type`</span>` `<span class="pre">`euclid`</span>` `<span class="pre">`-pc_hypre_euclid_levels`</span>` `<span class="pre">`k`</span>
    where <span class="pre">`k`</span> is the level (1-8 typically).

</div>

</div>

<div id="ode-integration" class="section">

## ODE integration<a href="#ode-integration" class="headerlink"
title="Permalink to this heading">#</a>

The <a href="../_breathe_autogen/file/solver_8hxx.html#_CPPv46Solver"
class="reference internal" title="Solver"><span class="pre"><code
class="sourceCode cpp">Solver</code></span></a> class can be used to
solve systems of ODEs inside a physics model: Multiple Solver objects
can exist besides the main one used for time integration. Example code
is in <span class="pre">`examples/test-integrate`</span>.

To use this feature, systems of ODEs must be represented by a class
derived from <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv412PhysicsModel"
class="reference internal" title="PhysicsModel"><span class="pre"><code
class="sourceCode cpp">PhysicsModel</code></span></a>.

<div class="highlight-cpp notranslate">

<div class="highlight">

    class MyFunction : public PhysicsModel {
     public:
      int init(bool restarting) {
        // Initialise ODE
        // Add variables to solver as usual
        solver->add(result, "result");
        ...
      }

      int rhs(BoutReal time) {
        // Specify derivatives of fields as usual
        ddt(result) = ...
      }
     private:
      Field3D result;
    };

</div>

</div>

To solve this ODE, create a new
<a href="../_breathe_autogen/file/solver_8hxx.html#_CPPv46Solver"
class="reference internal" title="Solver"><span class="pre"><code
class="sourceCode cpp">Solver</code></span></a> object:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Solver* ode = Solver::create(Options::getRoot()->getSection("ode"));

</div>

</div>

This will look in the section <span class="pre">`[ode]`</span> in the
options file. **Important:** To prevent this solver overwriting the main
restart files with its own restart files, either disable restart files:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [ode]
    enablerestart = false

</div>

</div>

or specify a different directory to put the restart files:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [ode]
    restartdir = ode  # Restart files ode/BOUT.restart.0.nc, ...

</div>

</div>

Create a model object, and pass it to the solver:

<div class="highlight-cpp notranslate">

<div class="highlight">

    MyFunction* model = new MyFunction();
    ode->setModel(model);

</div>

</div>

Finally tell the solver to perform the integration:

<div class="highlight-cpp notranslate">

<div class="highlight">

    ode->solve(5, 0.1);

</div>

</div>

The first argument is the number of steps to take, and the second is the
size of each step. These can also be specified in the options, so
calling

<div class="highlight-cpp notranslate">

<div class="highlight">

    ode->solve();

</div>

</div>

will cause ode to look in the input for <span class="pre">`nout`</span>
and <span class="pre">`timestep`</span> options:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [ode]
    nout = 5
    timestep = 0.1

</div>

</div>

Finally, delete the model and solver when finished:

<div class="highlight-cpp notranslate">

<div class="highlight">

    delete model;
    delete solver;

</div>

</div>

**Note:** If an ODE needs to be solved multiple times, at the moment it
is recommended to delete the solver, and create a new one each time.

</div>

<div id="preconditioning" class="section">

<span id="sec-preconditioning"></span>

## Preconditioning<a href="#preconditioning" class="headerlink"
title="Permalink to this heading">#</a>

At every time step, an implicit scheme such as BDF has to solve a
non-linear problem to find the next solution. This is usually done using
Newton’s method, each step of which involves solving a linear (matrix)
problem. For <span class="math notranslate nohighlight">\\N\\</span>
evolving variables is an
<span class="math notranslate nohighlight">\\N\times N\\</span> matrix
and so can be very large. By default matrix-free methods are used, in
which the Jacobian
<span class="math notranslate nohighlight">\\\mathcal{J}\\</span> is
approximated by finite differences (see next subsection), and so this
matrix never needs to be explicitly calculated. Finding a solution to
this matrix can still be difficult, particularly as
<span class="math notranslate nohighlight">\\\delta t\\</span> gets
large compared with some time-scales in the system (i.e. a stiff
problem).

A preconditioner is a function which quickly finds an approximate
solution to this matrix, speeding up convergence to a solution. A
preconditioner does not need to include all the terms in the problem
being solved, as the preconditioner only affects the convergence rate
and not the final solution. A good preconditioner can therefore
concentrate on solving the parts of the problem with the fastest
time-scales.

A simple example [1] is a coupled wave equation, solved in the
<span class="pre">`test-precon`</span> example code:

<div class="math notranslate nohighlight">

\\\frac{\partial u}{\partial t} = \partial\_{||}v \qquad \frac{\partial
v}{\partial t} = \partial\_{||} u\\

</div>

First, calculate the Jacobian of this set of equations by taking partial
derivatives of the time-derivatives with respect to each of the evolving
variables

<div class="math notranslate nohighlight">

\\\begin{split}\mathcal{J} = (\begin{array}{cc} \frac{\partial}{\partial
u}\frac{\partial u}{\partial t} & \frac{\partial}{\partial
v}\frac{\partial u}{\partial t}\\ \frac{\partial}{\partial
u}\frac{\partial v}{\partial t} & \frac{\partial}{\partial
v}\frac{\partial v}{\partial t} \end{array} ) = (\begin{array}{cc} 0 &
\partial\_{||} \\ \partial\_{||} & 0 \end{array} )\end{split}\\

</div>

In this case <span class="math notranslate nohighlight">\\\frac{\partial
u}{\partial t}\\</span> doesn’t depend on
<span class="math notranslate nohighlight">\\u\\</span> nor
<span class="math notranslate nohighlight">\\\frac{\partial v}{\partial
t}\\</span> on <span class="math notranslate nohighlight">\\v\\</span>,
so the diagonal is empty. Since the equations are linear, the Jacobian
doesn’t depend on
<span class="math notranslate nohighlight">\\u\\</span> or
<span class="math notranslate nohighlight">\\v\\</span> and so

<div class="math notranslate nohighlight">

\\\begin{split}\frac{\partial}{\partial t}(\begin{array}{c} u \\ v
\end{array}) = \mathcal{J} (\begin{array}{c} u \\ v \end{array}
)\end{split}\\

</div>

In general for non-linear functions
<span class="math notranslate nohighlight">\\\mathcal{J}\\</span> gives
the change in time-derivatives in response to changes in the state
variables <span class="math notranslate nohighlight">\\u\\</span> and
<span class="math notranslate nohighlight">\\v\\</span>.

In implicit time stepping, the preconditioner needs to solve an equation

<div class="math notranslate nohighlight">

\\\mathcal{I} - \gamma \mathcal{J}\\

</div>

where <span class="math notranslate nohighlight">\\\mathcal{I}\\</span>
is the identity matrix, and
<span class="math notranslate nohighlight">\\\gamma\\</span> depends on
the time step and method (e.g.
<span class="math notranslate nohighlight">\\\gamma = \delta t\\</span>
for backwards Euler method). For the simple wave equation problem, this
is

<div class="math notranslate nohighlight">

\\\begin{split}\mathcal{I} - \gamma \mathcal{J} = (\begin{array}{cc} 1 &
-\gamma\partial\_{||} \\ -\gamma\partial\_{||} & 1 \end{array}
)\end{split}\\

</div>

This matrix can be block inverted using Schur factorisation [2]

<div class="math notranslate nohighlight">

\\\begin{split}(\begin{array}{cc} {\mathbf{E}} & {\mathbf{U}} \\
{\mathbf{L}} & {\mathbf{D}} \end{array})^{-1} = (\begin{array}{cc}
{\mathbf{I}} & -{\mathbf{E}}^{-1}{\mathbf{U}} \\ 0 & {\mathbf{I}}
\end{array} )(\begin{array}{cc} {\mathbf{E}}^{-1} & 0 \\ 0 &
{\mathbf{P}}\_{Schur}^{-1} \end{array} )(\begin{array}{cc} {\mathbf{I}}
& 0 \\ -{\mathbf{L}}{\mathbf{E}}^{-1} & {\mathbf{I}} \end{array}
)\end{split}\\

</div>

where <span class="math notranslate nohighlight">\\{\mathbf{P}}\_{Schur}
= {\mathbf{D}} - {\mathbf{L}}{\mathbf{E}}^{-1}{\mathbf{U}}\\</span>
Using this, the wave problem becomes:

<div id="equation-precon" class="math notranslate nohighlight">

<span class="eqno">(2)<a href="#equation-precon" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}(\begin{array}{cc}
1 & -\gamma\partial\_{||} \\ -\gamma\partial\_{||} & 1 \end{array})^{-1}
= (\begin{array}{cc} 1 & \gamma\partial\_{||}\\ 0 & 1 \end{array}
)(\begin{array}{cc} 1 & 0 \\ 0 & (1 -\gamma^2\partial^2\_{||})^{-1}
\end{array} )(\begin{array}{cc} 1 & 0\\ \gamma\partial\_{||} & 1
\end{array} )\end{split}\\

</div>

The preconditioner is implemented by defining a function of the form

<div class="highlight-cpp notranslate">

<div class="highlight">

    int precon(BoutReal t, BoutReal gamma, BoutReal delta) {
      ...
    }

</div>

</div>

which takes as input the current time, the
<span class="math notranslate nohighlight">\\\gamma\\</span> factor
appearing above, and
<span class="math notranslate nohighlight">\\\delta\\</span> which is
only important for constrained problems (not discussed here… yet). The
current state of the system is stored in the state variables (here
<span class="pre">`u`</span> and <span class="pre">`v`</span> ), whilst
the vector to be preconditioned is stored in the time derivatives (here
<span class="pre">`ddt(u)`</span> and <span class="pre">`ddt(v)`</span>
). At the end of the preconditioner the result should be in the time
derivatives. A preconditioner which is just the identity matrix and so
does nothing is therefore:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int precon(BoutReal t, BoutReal gamma, BoutReal delta) {
    }

</div>

</div>

To implement the preconditioner in equation
<a href="#equation-precon" class="reference internal">(2)</a>, first
apply the rightmost matrix to the given vector:

<div class="math notranslate nohighlight">

\\\begin{split}(\begin{array}{c} \texttt{ddt(u)} \\ \texttt{ddt(v)}
\end{array} ) = (\begin{array}{cc} 1 & 0 \\ \gamma\partial\_{||} & 1
\end{array} )(\begin{array}{c} \texttt{ddt(u)} \\ \texttt{ddt(v)}
\end{array} )\end{split}\\

</div>

<div class="highlight-cpp notranslate">

<div class="highlight">

    int precon(BoutReal t, BoutReal gamma, BoutReal delta) {
      mesh->communicate(ddt(u));
      //ddt(u) = ddt(u);
      ddt(v) = gamma*Grad_par(ddt(u)) + ddt(v);

</div>

</div>

note that since the preconditioner is linear, it doesn’t depend on
<span class="math notranslate nohighlight">\\u\\</span> or
<span class="math notranslate nohighlight">\\v\\</span>. As in the RHS
function, since we are taking a differential of
<span class="pre">`ddt(u)`</span>, it first needs to be communicated to
exchange guard cell values.

The second matrix

<div class="math notranslate nohighlight">

\\\begin{split}(\begin{array}{c} \texttt{ddt(u)} \\ \texttt{ddt(v)}
\end{array} ) \rightarrow (\begin{array}{cc} 1 & 0 \\ 0 & (1 -
\gamma^2\partial^2\_{||})^{-1} \end{array} )(\begin{array}{c}
\texttt{ddt(u)} \\ \texttt{ddt(v)} \end{array} )\end{split}\\

</div>

doesn’t alter <span class="math notranslate nohighlight">\\u\\</span>,
but solves a parabolic equation in the parallel direction. There is a
solver class to do this called <a
href="../_breathe_autogen/file/invert__parderiv_8hxx.html#_CPPv49InvertPar"
class="reference internal" title="InvertPar"><span class="pre"><code
class="sourceCode cpp">InvertPar</code></span></a> which solves the
equation <span class="math notranslate nohighlight">\\(A +
B\partial\_{||}^2)x = b\\</span> where
<span class="math notranslate nohighlight">\\A\\</span> and
<span class="math notranslate nohighlight">\\B\\</span> are
<a href="../_breathe_autogen/file/field2d_8hxx.html#_CPPv47Field2D"
class="reference internal" title="Field2D"><span class="pre"><code
class="sourceCode cpp">Field2D</code></span></a> or constants [3]. In <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel4initEb"
class="reference internal" title="PhysicsModel::init"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>init<span class="op">()</span></code></span></a>
we create one of these solvers:

<div class="highlight-cpp notranslate">

<div class="highlight">

    InvertPar *inv; // Parallel inversion class
    int init(bool restarting) {
       ...
       inv = InvertPar::Create();
       inv->setCoefA(1.0);
       ...
    }

</div>

</div>

In the preconditioner we then use this solver to update
<span class="math notranslate nohighlight">\\v\\</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    inv->setCoefB(-SQ(gamma));
    ddt(v) = inv->solve(ddt(v));

</div>

</div>

which solves <span class="math notranslate nohighlight">\\ddt(v)
\rightarrow (1 - \gamma^2\partial\_{||}^2)^{-1} ddt(v)\\</span>. The
final matrix just updates
<span class="math notranslate nohighlight">\\u\\</span> using this new
solution for <span class="math notranslate nohighlight">\\v\\</span>

<div class="math notranslate nohighlight">

\\\begin{split}(\begin{array}{c} \texttt{ddt(u)} \\ \texttt{ddt(v)}
\end{array} ) \rightarrow (\begin{array}{cc} 1 & \gamma\partial\_{||} \\
0 & 1 \end{array} )(\begin{array}{c} \texttt{ddt(u)} \\ \texttt{ddt(v)}
\end{array} )\end{split}\\

</div>

<div class="highlight-cpp notranslate">

<div class="highlight">

    mesh->communicate(ddt(v));
    ddt(u) = ddt(u) + gamma*Grad_par(ddt(v));

</div>

</div>

Finally, boundary conditions need to be imposed, which should be
consistent with the conditions used in the RHS:

<div class="highlight-cpp notranslate">

<div class="highlight">

    ddt(u).applyBoundary("dirichlet");
    ddt(v).applyBoundary("dirichlet");

</div>

</div>

To use the preconditioner, pass the function to the solver in <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel4initEb"
class="reference internal" title="PhysicsModel::init"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>init<span class="op">()</span></code></span></a>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int init(bool restarting) {
      solver->setPrecon(precon);
      ...
    }

</div>

</div>

then in the <span class="pre">`BOUT.inp`</span> settings file switch on
the preconditioner

<div class="highlight-bash notranslate">

<div class="highlight">

    [solver]
    type = cvode          # Need CVODE or PETSc
    use_precon = true     # Use preconditioner
    rightprec = false     # Use Right preconditioner (default left)

</div>

</div>

</div>

<div id="jacobian-function" class="section">

## Jacobian function<a href="#jacobian-function" class="headerlink"
title="Permalink to this heading">#</a>

</div>

<div id="dae-constraint-equations" class="section">

## DAE constraint equations<a href="#dae-constraint-equations" class="headerlink"
title="Permalink to this heading">#</a>

Using the IDA or IMEX-BDF2 solvers, BOUT++ can solve Differential
Algebraic Equations (DAEs), in which algebraic constraints are used for
some variables. Examples of how this is used are in the
<span class="pre">`examples/constraints`</span> subdirectory.

First the variable to be constrained is added to the solver, in a
similar way to time integrated variables. For example

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D phi;
    ...
    solver->constraint(phi, ddt(phi), "phi");

</div>

</div>

The first argument is the variable to be solved for (constrained). The
second argument is the field to contain the residual (error). In this
example the time derivative field <span class="pre">`ddt(phi)`</span> is
used, but it could be another
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> variable. The solver
will attempt to find a solution to the first argument
(<span class="pre">`phi`</span> here) such that the second argument
(<span class="pre">`ddt(phi)`</span>) is zero to within tolerances.

In the RHS function the residual should be calculated. In this example
(<span class="pre">`examples/constraints/drift-wave-constraint`</span>)
we have:

<div class="highlight-cpp notranslate">

<div class="highlight">

    ddt(phi) = Delp2(phi) - Vort;

</div>

</div>

so the time integration solver includes the algebraic constraint
<span class="pre">`Delp2(phi)`</span>` `<span class="pre">`=`</span>` `<span class="pre">`Vort`</span>
i.e. (<span class="math notranslate nohighlight">\\\nabla\_\perp^2\phi =
\omega\\</span>).

</div>

<div id="id4" class="section">

## IMEX-BDF2<a href="#id4" class="headerlink"
title="Permalink to this heading">#</a>

This is an implicit-explicit multistep method, which uses the PETSc
library for the SNES nonlinear solver. To use this solver, BOUT++ must
have been configured with PETSc support, and the solver type set to
<span class="pre">`imexbdf2`</span>

<div class="highlight-cpp notranslate">

<div class="highlight">

    [solver]
    type = imexbdf2

</div>

</div>

For examples of using IMEX-BDF2, see the
<span class="pre">`examples/IMEX/`</span> subdirectory, in particular
the <span class="pre">`diffusion-nl`</span>,
<span class="pre">`drift-wave`</span> and
<span class="pre">`drift-wave-constrain`</span> examples.

The time step is currently fixed (not adaptive), and defaults to the
output timestep. To set a smaller internal timestep, the
<span class="pre">`solver:timestep`</span> option can be set. If the
timestep is too large, then the explicit part of the problem may become
unstable, or the implicit part may fail to converge.

The implicit part of the problem can be solved matrix-free, in which
case the Jacobian-vector product is approximated using finite
differences. This is currently the default, and can be set on the
command-line using the options:

<div class="highlight-cpp notranslate">

<div class="highlight">

    solver:matrix_free=true  -snes_mf

</div>

</div>

Note the <span class="pre">`-snes_mf`</span> flag which is passed to
PETSc. When using a matrix free solver, the Jacobian is not calculated
and so the amount of memory used is minimal. However, since the Jacobian
is not known, many standard preconditioning methods cannot be used, and
so in many cases a custom preconditioner is needed to obtain good
convergence.

An experimental feature uses PETSc’s ability to calculate the Jacobian
using finite differences. This can then speed up the linear solve, and
allows more options for preconditioning. To enable this option:

<div class="highlight-cpp notranslate">

<div class="highlight">

    solver:matrix_free=false

</div>

</div>

There are two ways to calculate the Jacobian: A brute force method which
is set up by this call to PETSc which is generally very slow, and a
“coloring” scheme which can be quite fast and is the default. Coloring
uses knowledge of where the non-zero values are in the Jacobian, to work
out which rows can be calculated simultaneously. The coloring code in
IMEX-BDF2 currently assumes that every field is coupled to every other
field in a star pattern: one cell on each side, a 7 point stencil for 3D
fields. If this is not the case for your problem, then the solver may
not converge.

The brute force method can be useful for comparing the Jacobian
structure, so to turn off coloring:

<div class="highlight-cpp notranslate">

<div class="highlight">

    solver:use_coloring=false

</div>

</div>

Using MatView calls, or the <span class="pre">`-mat_view`</span> PETSc
options, the non-zero structure of the Jacobian can be plotted or
printed.

</div>

<div id="monitoring-the-simulation-output" class="section">

## Monitoring the simulation output<a href="#monitoring-the-simulation-output" class="headerlink"
title="Permalink to this heading">#</a>

Monitoring of the solution can be done at two levels: output monitoring,
and timestep monitoring. Output monitoring occurs only when data is
written to file, whereas timestep monitoring is every timestep and so
(usually) much more frequent. Examples of both are in
<span class="pre">`examples/monitor`</span> and
<span class="pre">`examples/monitor-newapi`</span>.

**Output monitoring**: At every output timestep the solver calls a
monitor method of the BoutMonitor class, which writes the output dump
file, calculates and prints timing information and estimated time
remaining. If you want to run additional code or write data to a
different file, you can implement the outputMonitor method of
PhysicsModel:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int outputMonitor(BoutReal simtime, int iter, int nout)

</div>

</div>

The first input is the current simulation time, the second is the output
number, and the last is the total number of outputs requested. This
method is called by a monitor object PhysicsModel::modelMonitor, which
writes the restart files at the same time. You can change the frequency
at which the monitor is called by calling, in PhysicsModel::init:

<div class="highlight-cpp notranslate">

<div class="highlight">

    modelMonitor.setTimestep(new_timestep)

</div>

</div>

where <span class="pre">`new_timestep`</span> is a BoutReal which is
either <span class="pre">`timestep*n`</span> or
<span class="pre">`timestep/n`</span> for an integer
<span class="pre">`n`</span>. Note that this will change the frequency
of writing restarts as well as of calling
<span class="pre">`outputMonitor()`</span>.

You can also add custom monitor object(s) for more flexibility.

You can call your output monitor class whatever you like, but it must be
a subclass of Monitor and provide the method
<span class="pre">`call`</span> which takes 4 inputs and returns an int:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class MyOutputMonitor : public Monitor {
      int call(Solver *solver, BoutReal simtime, int iter, int NOUT) {
        ...
      }
    };

</div>

</div>

The first input is the solver object, the second is the current
simulation time, the third is the output number, and the last is the
total number of outputs requested. To get the solver to call this
function every output time, define a
<span class="pre">`MyOutputMonitor`</span> object as a member of your
PhysicsModel:

<div class="highlight-cpp notranslate">

<div class="highlight">

    MyOutputMonitor my_output_monitor;

</div>

</div>

and put in your <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel4initEb"
class="reference internal" title="PhysicsModel::init"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>init<span class="op">()</span></code></span></a>
code:

<div class="highlight-cpp notranslate">

<div class="highlight">

    solver->addMonitor(&my_output_monitor);

</div>

</div>

Note that the solver only stores a pointer to the
<a href="../_breathe_autogen/file/monitor_8hxx.html#_CPPv47Monitor"
class="reference internal" title="Monitor"><span class="pre"><code
class="sourceCode cpp">Monitor</code></span></a>, so you must make sure
the object is persistent, e.g. a member of a <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv412PhysicsModel"
class="reference internal" title="PhysicsModel"><span class="pre"><code
class="sourceCode cpp">PhysicsModel</code></span></a> class, not a local
variable in a constructor. If you want to later remove a monitor, you
can do so with:

<div class="highlight-cpp notranslate">

<div class="highlight">

    solver->removeMonitor(&my_output_monitor);

</div>

</div>

A simple example using this monitor is:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class MyOutputMonitor: public Monitor{
    public:
      MyOutputMonitor(BoutReal timestep=-1):Monitor(timestep){};
      int call(Solver *solver, BoutReal simtime, int iter, int NOUT) override;
    };

    int MyOutputMonitor::call(Solver *solver, BoutReal simtime, int iter, int NOUT) {
      output.write("Output monitor, time = %e, step %d of %d\n",
                   simtime, iter, NOUT);
      return 0;
    }

    MyOutputMonitor my_monitor;

    int init(bool restarting) {
      solver->addMonitor(&my_monitor);
    }

</div>

</div>

See the monitor example (<span class="pre">`examples/monitor`</span>)
for full code.

**Timestep monitoring**: This uses functions instead of objects. First
define a monitor function:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int my_timestep_monitor(Solver *solver, BoutReal simtime, BoutReal lastdt) {
      ...
    }

</div>

</div>

where <span class="pre">`simtime`</span> will again contain the current
simulation time, and <span class="pre">`lastdt`</span> the last timestep
taken. Add this function to the solver:

<div class="highlight-cpp notranslate">

<div class="highlight">

    solver->addTimestepMonitor(my_timestep_monitor);

</div>

</div>

Timestep monitoring is disabled by default, unlike output monitoring. To
enable timestep monitoring, set in the options file (BOUT.inp):

<div class="highlight-cpp notranslate">

<div class="highlight">

    [solver]
    monitor_timestep = true

</div>

</div>

or put on the command line
<span class="pre">`solver:monitor_timestep=true`</span> . When this is
enabled, it will change how solvers like CVODE and PVODE (the default
solvers) are used. Rather than being run in NORMAL mode, they will
instead be run in SINGLE_STEP mode (see the SUNDIALS notes
here:<a href="https://computation.llnl.gov/casc/sundials/support/notes.html"
class="reference external">https://computation.llnl.gov/casc/sundials/support/notes.html</a>).
This may in some cases be less efficient.

</div>

<div id="implementation-internals" class="section">

## Implementation internals<a href="#implementation-internals" class="headerlink"
title="Permalink to this heading">#</a>

The solver is the interface between BOUT++ and the time-integration code
such as SUNDIALS. All solvers implement the
<a href="../_breathe_autogen/file/solver_8hxx.html#_CPPv46Solver"
class="reference internal" title="Solver"><span class="pre"><code
class="sourceCode cpp">Solver</code></span></a> class interface (see
<span class="pre">`src/solver/generic_solver.hxx`</span>).

First all the fields which are to be evolved need to be added to the
solver. These are always done in pairs, the first specifying the field,
and the second the time-derivative:

<div class="highlight-cpp notranslate">

<div class="highlight">

    void add(Field2D &v, Field2D &F_v, const char* name);

</div>

</div>

This is normally called in the <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel4initEb"
class="reference internal" title="PhysicsModel::init"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>init<span class="op">()</span></code></span></a>
initialisation routine. Some solvers (e.g. IDA) can support constraints,
which need to be added in the same way as evolving fields:

<div class="highlight-cpp notranslate">

<div class="highlight">

    bool constraints();
    void constraint(Field2D &v, Field2D &C_v, const char* name);

</div>

</div>

The <span class="pre">`constraints()`</span> function tests whether or
not the current solver supports constraints. The format of
<span class="pre">`constraint(...)`</span> is the same as
<span class="pre">`add`</span>, except that now the solver will attempt
to make <span class="pre">`C_v`</span> zero. If
<span class="pre">`constraint`</span> is called when the solver doesn’t
support them then an error should occur.

If the physics model implements a preconditioner or Jacobian-vector
multiplication routine, these can be passed to the solver during
initialisation:

<div class="highlight-cpp notranslate">

<div class="highlight">

    typedef int (*PhysicsPrecon)(BoutReal t, BoutReal gamma, BoutReal delta);
    void setPrecon(PhysicsPrecon f); // Specify a preconditioner
    typedef int (*Jacobian)(BoutReal t);
    void setJacobian(Jacobian j); // Specify a Jacobian

</div>

</div>

If the solver doesn’t support these functions then the calls will just
be ignored.

Once the problem to be solved has been specified, the solver can be
initialised using:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int init();

</div>

</div>

which returns an error code (0 on success). This is currently called in
<a href="../_breathe_autogen/file/bout_09_09_8cxx.html"
class="reference internal"><span class="doc">bout++.cxx</span></a>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    if (solver.init()) {
      output.write("Failed to initialise solver. Aborting\n");
      return(1);
    }

</div>

</div>

which passes the (physics module) RHS function <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel3rhsE8BoutReal"
class="reference internal" title="PhysicsModel::rhs"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>rhs<span class="op">()</span></code></span></a>
to the solver along with the number and size of the output steps.

<div class="highlight-cpp notranslate">

<div class="highlight">

    typedef int (*MonitorFunc)(BoutReal simtime, int iter, int NOUT);
    int run(MonitorFunc f);

</div>

</div>

<span class="label"><span class="fn-bracket">\[</span><a href="#id1" role="doc-backlink">1</a><span class="fn-bracket">\]</span></span>

Taken from a talk by L.Chacon available here
<a href="https://bout2011.llnl.gov/pdf/talks/Chacon_bout2011.pdf"
class="reference external">https://bout2011.llnl.gov/pdf/talks/Chacon_bout2011.pdf</a>

<span class="label"><span class="fn-bracket">\[</span><a href="#id2" role="doc-backlink">2</a><span class="fn-bracket">\]</span></span>

See paper <a href="https://arxiv.org/abs/1209.2054"
class="reference external">https://arxiv.org/abs/1209.2054</a> for an
application to 2-fluid equations

<span class="label"><span class="fn-bracket">\[</span><a href="#id3" role="doc-backlink">3</a><span class="fn-bracket">\]</span></span>

This <a
href="../_breathe_autogen/file/invert__parderiv_8hxx.html#_CPPv49InvertPar"
class="reference internal" title="InvertPar"><span class="pre"><code
class="sourceCode cpp">InvertPar</code></span></a> class can handle
cases with closed field-lines and twist-shift boundary conditions for
tokamak simulations

</div>

</div>

<div class="prev-next-area">

<a href="python_boutpp.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

The python boutpp module

</div>

<a href="parallel-transforms.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Parallel Transforms

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#options" class="reference internal nav-link">Options</a>
- <a href="#cvode" class="reference internal nav-link">CVODE</a>
- <a href="#imex-bdf2" class="reference internal nav-link">IMEX-BDF2</a>
- <a href="#split-rk" class="reference internal nav-link">Split-RK</a>
- <a href="#backward-euler-snes"
  class="reference internal nav-link">Backward Euler - SNES</a>
  - <a href="#basic-configuration" class="reference internal nav-link">Basic
    Configuration</a>
  - <a href="#timestepping-modes"
    class="reference internal nav-link">Timestepping Modes</a>
  - <a href="#adaptive-timestepping"
    class="reference internal nav-link">Adaptive Timestepping</a>
    - <a href="#residual-ratio" class="reference internal nav-link">Residual
      Ratio</a>
    - <a href="#threshold-controller"
      class="reference internal nav-link">Threshold Controller</a>
  - <a href="#output-trigger" class="reference internal nav-link">Output
    trigger</a>
  - <a
    href="#pseudo-transient-continuation-and-switched-evolution-relaxation"
    class="reference internal nav-link">Pseudo-Transient Continuation and
    Switched Evolution Relaxation</a>
    - <a href="#ser-timestep-strategy" class="reference internal nav-link">SER
      timestep strategy</a>
    - <a href="#pid-controller" class="reference internal nav-link">PID
      Controller</a>
  - <a href="#jacobian-finite-difference-with-coloring"
    class="reference internal nav-link">Jacobian Finite Difference with
    Coloring</a>
    - <a href="#jacobian-coloring-stencil"
      class="reference internal nav-link">Jacobian coloring stencil</a>
- <a href="#diagnostics-and-monitoring"
  class="reference internal nav-link">Diagnostics and Monitoring</a>
  - <a href="#summary-of-solver-options"
    class="reference internal nav-link">Summary of solver options</a>
- <a href="#ode-integration" class="reference internal nav-link">ODE
  integration</a>
- <a href="#preconditioning"
  class="reference internal nav-link">Preconditioning</a>
- <a href="#jacobian-function"
  class="reference internal nav-link">Jacobian function</a>
- <a href="#dae-constraint-equations"
  class="reference internal nav-link">DAE constraint equations</a>
- <a href="#id4" class="reference internal nav-link">IMEX-BDF2</a>
- <a href="#monitoring-the-simulation-output"
  class="reference internal nav-link">Monitoring the simulation output</a>
- <a href="#implementation-internals"
  class="reference internal nav-link">Implementation internals</a>

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

[3]
