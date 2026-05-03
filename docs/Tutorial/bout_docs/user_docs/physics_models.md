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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/physics_models.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/physics_models.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/physics_models.rst"
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

# BOUT++ physics models

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#building-physics-models"
  class="reference internal nav-link">Building Physics Models</a>
  - <a href="#using-cmake-with-your-physics-model"
    class="reference internal nav-link">Using CMake with your physics
    model</a>
- <a href="#heat-conduction" class="reference internal nav-link">Heat
  conduction</a>
  - <a href="#initialisation"
    class="reference internal nav-link">Initialisation</a>
  - <a href="#time-evolution" class="reference internal nav-link">Time
    evolution</a>
  - <a href="#running-the-model" class="reference internal nav-link">Running
    the model</a>
- <a href="#magnetohydrodynamics-mhd"
  class="reference internal nav-link">Magnetohydrodynamics (MHD)</a>
  - <a href="#variables" class="reference internal nav-link">Variables</a>
  - <a href="#evolution-equations"
    class="reference internal nav-link">Evolution equations</a>
  - <a href="#input-options" class="reference internal nav-link">Input
    options</a>
  - <a href="#communication"
    class="reference internal nav-link">Communication</a>
  - <a href="#error-handling" class="reference internal nav-link">Error
    handling</a>
  - <a href="#boundary-conditions"
    class="reference internal nav-link">Boundary conditions</a>
  - <a href="#custom-boundary-conditions"
    class="reference internal nav-link">Custom boundary conditions</a>
  - <a href="#initial-profiles" class="reference internal nav-link">Initial
    profiles</a>
  - <a href="#output-variables" class="reference internal nav-link">Output
    variables</a>
  - <a href="#variable-attributes"
    class="reference internal nav-link">Variable attributes</a>
- <a href="#reduced-mhd" class="reference internal nav-link">Reduced
  MHD</a>
- <a href="#logging-output" class="reference internal nav-link">Logging
  output</a>
  - <a href="#controlling-logging-level"
    class="reference internal nav-link">Controlling logging level</a>
- <a href="#updating-physics-models-from-v3-to-v4"
  class="reference internal nav-link">Updating Physics Models from v3 to
  v4</a>
- <a href="#more-examples" class="reference internal nav-link">More
  examples</a>
  - <a href="#advect1d" class="reference internal nav-link">advect1d</a>
  - <a href="#drift-instability"
    class="reference internal nav-link">drift-instability</a>
  - <a href="#interchange-instability"
    class="reference internal nav-link">interchange-instability</a>
  - <a href="#sod-shock" class="reference internal nav-link">sod-shock</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="bout-physics-models" class="section">

<span id="sec-equations"></span>

# BOUT++ physics models<a href="#bout-physics-models" class="headerlink"
title="Permalink to this heading">#</a>

Once you have tried some example codes, and generally got the hang of
running BOUT++ and analysing the results, there will probably come a
time when you want to change the equations being solved. This section
demonstrates how a BOUT++ physics model is put together. It assumes you
have a working knowledge of C or C++, but you don’t need to be an
expert - most of the messy code is hidden away from the physics model.
There are several good books on C and C++, but I’d recommend online
tutorials over books because there are a lot more of them, they’re
quicker to scan through, and they’re cheaper.

Many of the examples which come with BOUT++ are physics models, and can
be used as a starting point. Some relatively simple examples are
<span class="pre">`blob2d`</span> (2D plasma filament/blob propagation),
<span class="pre">`hasegawa-wakatani`</span> (2D turbulence),
<span class="pre">`finite-volume/fluid`</span> (1D compressible fluid)
and <span class="pre">`gas-compress`</span> (up to 3D compressible
fluid). Some of the integrated tests (under
<span class="pre">`tests/integrated`</span>) use either physics models
(e.g. <span class="pre">`test-delp2`</span> and
<span class="pre">`test-drift-instability`</span>), or define their own
<span class="pre">`main`</span> function (e.g.
<span class="pre">`test-io`</span> and
<span class="pre">`test-cyclic`</span>).

<div id="building-physics-models" class="section">

<span id="sec-build-examples"></span>

## Building Physics Models<a href="#building-physics-models" class="headerlink"
title="Permalink to this heading">#</a>

After building the library (see
<span class="xref std std-ref">sec-cmake</span>), you can build a
physics model in several different ways.

For the bundled examples, perhaps the easiest is to build it directly in
the build directory. For example, to build the
<span class="pre">`conduction`</span> example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    $ cmake --build build --target conduction

</div>

</div>

(assuming that your build directory is called
<span class="pre">`build`</span>!) which will build the executable in
<span class="pre">`build/examples/conduction`</span>.

You can also <span class="pre">`cd`</span> into that directory and build
it there:

<div class="highlight-cpp notranslate">

<div class="highlight">

    $ cd build/examples/conduction
    $ make

</div>

</div>

(Note for advanced users that this won’t work if you’ve used the
<span class="pre">`Ninja`</span> CMake generator).

Either of these two methods will actually build the entire BOUT++
library if necessary, which can be especially useful when developing.

<div id="using-cmake-with-your-physics-model" class="section">

<span id="sec-cmake-physics-model"></span>

### Using CMake with your physics model<a href="#using-cmake-with-your-physics-model" class="headerlink"
title="Permalink to this heading">#</a>

You can write a CMake configuration file
(<span class="pre">`CMakeLists.txt`</span>) for your physics model in
only four lines:

<div class="highlight-cmake notranslate">

<div class="highlight">

    project(blob2d LANGUAGES CXX)
    find_package(bout++ REQUIRED)
    add_executable(blob2d blob2d.cxx)
    target_link_libraries(blob2d PRIVATE bout++::bout++)

</div>

</div>

You just need to give CMake the location where you built or installed
BOUT++ via the <span class="pre">`bout++_DIR`</span> variable:

<div class="highlight-cpp notranslate">

<div class="highlight">

    $ cmake . -B build -Dbout++_DIR=/path/to/built/BOUT++

</div>

</div>

If you want to modify BOUT++ along with developing your model, you may
instead wish to place the BOUT++ as a subdirectory of your model and use
<span class="pre">`add_subdirectory`</span> instead of
<span class="pre">`find_package`</span> above:

<div class="highlight-cmake notranslate">

<div class="highlight">

    project(blob2d LANGUAGES CXX)
    add_subdirectory(BOUT++/source)
    add_executable(blob2d blob2d.cxx)
    target_link_libraries(blob2d PRIVATE bout++::bout++)

</div>

</div>

where <span class="pre">`BOUT++/source`</span> is the subdirectory
containing the BOUT++ source. Doing this has the advantage that any
changes you make to BOUT++ source files will trigger a rebuild of both
the BOUT++ library and your model when you next build your code.

</div>

</div>

<div id="heat-conduction" class="section">

<span id="sec-heat-conduction-model"></span>

## Heat conduction<a href="#heat-conduction" class="headerlink"
title="Permalink to this heading">#</a>

The <span class="pre">`conduction`</span> example solves 1D heat
conduction

<div class="math notranslate nohighlight">

\\\frac{\partial T}{\partial t} = \nabla\_{||}(\chi\partial\_{||} T)\\

</div>

The source code to solve this is in
<span class="pre">`conduction.cxx`</span>, which we show here:

<div id="conduction-cxx" class="highlight-cpp notranslate">

<div class="highlight">

     6#include <bout/physicsmodel.hxx>
     7
     8class Conduction : public PhysicsModel {
     9private:
    10  Field3D T; // Evolving temperature equation only
    11
    12  BoutReal chi; // Parallel conduction coefficient
    13
    14protected:
    15  // This is called once at the start
    16  int init(bool UNUSED(restarting)) override {
    17
    18    // Get the options
    19    auto& options = Options::root()["conduction"];
    20
    21    // Read from BOUT.inp, setting default to 1.0
    22    // The doc() provides some documentation in BOUT.settings
    23    chi = options["chi"].doc("Conduction coefficient").withDefault(1.0);
    24
    25    // Tell BOUT++ to solve T
    26    SOLVE_FOR(T);
    27
    28    return 0;
    29  }
    30
    31  int rhs(BoutReal UNUSED(time)) override {
    32    mesh->communicate(T); // Communicate guard cells
    33
    34    ddt(T) =
    35        Div_par_K_Grad_par(chi, T); // Parallel diffusion Div_{||}( chi * Grad_{||}(T) )
    36
    37    return 0;
    38  }
    39};
    40
    41BOUTMAIN(Conduction);

</div>

</div>

Let’s go through it line-by-line. First, we include the header that
defines the <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv412PhysicsModel"
class="reference internal" title="PhysicsModel"><span class="pre"><code
class="sourceCode cpp">PhysicsModel</code></span></a> class:

<div class="highlight-cpp notranslate">

<div class="highlight">

    #include <bout/physicsmodel.hxx>

</div>

</div>

This also brings in the header files that we need for the rest of the
code. Next, we need to define a new class,
<span class="pre">`Conduction`</span>, that inherits from <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv412PhysicsModel"
class="reference internal" title="PhysicsModel"><span class="pre"><code
class="sourceCode cpp">PhysicsModel</code></span></a> (line 8):

<div class="highlight-cpp notranslate">

<div class="highlight">

    class Conduction : public PhysicsModel {

</div>

</div>

The <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv412PhysicsModel"
class="reference internal" title="PhysicsModel"><span class="pre"><code
class="sourceCode cpp">PhysicsModel</code></span></a> contains both the
physical variables we want to evolve, like the temperature:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D T; // Evolving temperature equation only

</div>

</div>

as well as any physical or numerical coefficients. In this case, we only
have the parallel conduction coefficient,
<span class="pre">`chi`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoutReal chi; // Parallel conduction coefficient

</div>

</div>

A <a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> represents a 3D scalar
quantity, while a
<a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv48BoutReal"
class="reference internal" title="BoutReal"><span class="pre"><code
class="sourceCode cpp">BoutReal</code></span></a> represents a single
number. See the later section on
<a href="#sec-variables" class="reference internal"><span
class="std std-ref">Variables</span></a> for more information.

After declaring our model variables, we need to define two functions: an
initialisation function, <span class="pre">`init`</span>, that is called
to set up the simulation and specify which variables are evolving in
time; and a “right-hand side” function, <span class="pre">`rhs`</span>,
that calculates the time derivatives of our evolving variables. These
are defined in lines 18 and 21 respectively above:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int init(bool restarting) override {
    ...
    }
    int rhs(BoutReal time) override {
    ...
    }

</div>

</div>

<a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel4initEb"
class="reference internal" title="PhysicsModel::init"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>init<span class="op">()</span></code></span></a>
takes as input a <span class="pre">`bool`</span>
(<span class="pre">`true`</span> or <span class="pre">`false`</span>)
that tells it whether or not the model is being restarted, which can be
useful if something only needs to be done once before the simulation
starts properly. The simulation (physical) time is passed to
<span class="pre">`PhyiscsModel::rhs`</span> as a
<a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv48BoutReal"
class="reference internal" title="BoutReal"><span class="pre"><code
class="sourceCode cpp">BoutReal</code></span></a>.

The <span class="pre">`override`</span> keyword is just to let the
compiler know we’re overriding a method in the base class and is not
important to understand.

<div id="initialisation" class="section">

### Initialisation<a href="#initialisation" class="headerlink"
title="Permalink to this heading">#</a>

During initialisation (the <span class="pre">`init`</span> function),
the conduction example first reads an option (lines 21 and 24) from the
input settings file (<span class="pre">`data/BOUT.inp`</span> by
default):

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto& options = Options::root()["conduction"];

    OPTION(options, chi, 1.0);

</div>

</div>

This first gets a section called “conduction”, then requests an option
called “chi” inside this section. If this setting is not found, then the
default value of 1.0 will be used. To set this value the BOUT.inp file
contains:

<div class="highlight-bash notranslate">

<div class="highlight">

    [conduction]
    chi = 1.0

</div>

</div>

which defines a section called “conduction”, and within that section a
variable called “chi”. This value can also be overridden by specifying
the setting on the command line:

<div class="highlight-bash notranslate">

<div class="highlight">

    $ ./conduction conduction:chi=2

</div>

</div>

where <span class="pre">`conduction:chi`</span> means the variable “chi”
in the section “conduction”. When this option is read, a message is
printed to the BOUT.log files, giving the value used and the source of
that value:

<div class="highlight-bash notranslate">

<div class="highlight">

    Option conduction:chi = 1 (data/BOUT.inp)

</div>

</div>

For more information on options and input files, see
<a href="bout_options.html#sec-options" class="reference internal"><span
class="std std-ref">BOUT++ options</span></a>, as well as the
documentation for the
<a href="../_breathe_autogen/file/options_8hxx.html#_CPPv47Options"
class="reference internal" title="Options"><span class="pre"><code
class="sourceCode cpp">Options</code></span></a> class.

After reading the chi option, the <span class="pre">`init`</span> method
then specifies which variables to evolve using the
<span class="pre">`SOLVE_FOR`</span> macro:

<div class="highlight-cpp notranslate">

<div class="highlight">

    // Tell BOUT++ to solve T
    SOLVE_FOR(T);

</div>

</div>

This tells the BOUT++ time integration solver to set the variable
<span class="pre">`T`</span> using values from the input settings. It
looks in a section with the same name as the variable
(<span class="pre">`T`</span> here) for variables “scale” and
“function”:

<div class="highlight-bash notranslate">

<div class="highlight">

    [T] # Settings for the T variable

    scale = 1.0  # Size of the initial perturbation
    function = gauss(y-pi, 0.2)  # The form of the initial perturbation. y from 0 to 2*pi

</div>

</div>

The function is evaluated using expressions which can involve x,y and z
coordinates. More details are given in section
<a href="variable_init.html#sec-init-time-evolved-vars"
class="reference internal"><span class="std std-ref">Initialisation of
time evolved variables</span></a>.

Finally an error code is returned, here 0 indicates no error. If
<span class="pre">`init`</span> returns non-zero then the simulation
will stop.

</div>

<div id="time-evolution" class="section">

### Time evolution<a href="#time-evolution" class="headerlink"
title="Permalink to this heading">#</a>

During time evolution, the time integration method (ODE integrator)
calculates the system state (here <span class="pre">`T`</span>) at a
give time. It then calls the <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel3rhsE8BoutReal"
class="reference internal" title="PhysicsModel::rhs"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>rhs<span class="op">()</span></code></span></a>
function, which should calculate the time derivative of all the evolving
variables. In this case the job of the <span class="pre">`rhs`</span>
function is to calculate <span class="pre">`ddt(T)`</span>, the
**partial derivative** of the variable <span class="pre">`T`</span> with
respect to time, given the value of <span class="pre">`T`</span>:

> <div>
>
> <div class="math notranslate nohighlight">
>
> \\\frac{\partial T}{\partial t} = \nabla\_{||}(\chi\partial\_{||} T)\\
>
> </div>
>
> </div>

The first thing the <span class="pre">`rhs`</span> function function
does is communicate the guard (halo) cells using <a
href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4IDpEN4Mesh11communicateEvDpR2Ts"
class="reference internal" title="Mesh::communicate"><span
class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>communicate<span class="op">()</span></code></span></a>
on line 33:

<div class="highlight-cpp notranslate">

<div class="highlight">

    mesh->communicate(T);

</div>

</div>

This is because BOUT++ does not (generally) do communications, but
leaves it up to the user to decide when the most efficient or convenient
time to do them is. Before we can take derivatives of a variable (here
<span class="pre">`T`</span>), the values of the function must be known
in the boundaries and guard cells, which requires communication between
processors. By default the values in the guard cells are set to
<span class="pre">`NaN`</span>, so if they are accidentally used without
first communicating then the code should crash fairly quickly with a
non-finite number error.

Once the guard cells have been communicated, we calculate the right hand
side (RHS) of the equation above (line 35):

<div class="highlight-cpp notranslate">

<div class="highlight">

    ddt(T) = Div_par_K_Grad_par(chi, T);

</div>

</div>

The function <a
href="../_breathe_autogen/file/difops_8cxx.html#_CPPv418Div_par_K_Grad_par8BoutRealRK7Field2D8CELL_LOC"
class="reference internal" title="Div_par_K_Grad_par"><span
class="pre"><code
class="sourceCode cpp">Div_par_K_Grad_par<span class="op">()</span></code></span></a>
is a function in the BOUT++ library which calculates the divergence in
the parallel (y) direction of a constant multiplied by the gradient of a
function in the parallel direction.

As with the <span class="pre">`init`</span> code, a non-zero return
value indicates an error and will stop the simulation.

</div>

<div id="running-the-model" class="section">

### Running the model<a href="#running-the-model" class="headerlink"
title="Permalink to this heading">#</a>

The very last thing we need to do in our physics model is to define a
<span class="pre">`main`</span> function. Here, we do it with the
<span class="pre">`BOUTMAIN`</span> macro:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BOUTMAIN(Conduction);

</div>

</div>

You can define your own <span class="pre">`main()`</span> function, but
for most cases this is enough. The macro expands to something like:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int main(int argc, char **argv) {
      BoutInitialise(argc, argv); // Initialise BOUT++

      Conduction *model = new Conduction(); // Create a model

      Solver *solver = Solver::create(); // Create a solver
      solver->setModel(model); // Specify the model to solve
      solver->addMonitor(bout_monitor); // Monitor the solver

      solver->solve(); // Run the solver

      delete model;
      delete solver;
      BoutFinalise(); // Finished with BOUT++
      return 0;
    }

</div>

</div>

This initialises the main BOUT++ library, creates the <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv412PhysicsModel"
class="reference internal" title="PhysicsModel"><span class="pre"><code
class="sourceCode cpp">PhysicsModel</code></span></a> and
<a href="../_breathe_autogen/file/solver_8hxx.html#_CPPv46Solver"
class="reference internal" title="Solver"><span class="pre"><code
class="sourceCode cpp">Solver</code></span></a>, runs the solver, and
finally cleans up the model, solver and library.

</div>

</div>

<div id="magnetohydrodynamics-mhd" class="section">

## Magnetohydrodynamics (MHD)<a href="#magnetohydrodynamics-mhd" class="headerlink"
title="Permalink to this heading">#</a>

When going through this section, it may help to refer to the finished
code, which is given in the file <span class="pre">`mhd.cxx`</span> in
the BOUT++ examples directory under
<span class="pre">`orszag-tang`</span>. The equations to be solved are:

<div class="math notranslate nohighlight">

\\\begin{split}{{\frac{\partial \rho}{\partial t}}} =&
-\mathbf{v}\cdot\nabla\rho - \rho\nabla\cdot\mathbf{v} \\
{{\frac{\partial p}{\partial t}}} =& -\mathbf{v}\cdot\nabla p - \gamma
p\nabla\cdot\mathbf{v} \\ {{\frac{\partial \mathbf{v}}{\partial t}}} =&
-\mathbf{v}\cdot\nabla\mathbf{v} + \frac{1}{\rho}(-\nabla p +
(\nabla\times\mathbf{B})\times\mathbf{B}) \\ {{\frac{\partial
\mathbf{B}}{\partial t}}} =&
\nabla\times(\mathbf{v}\times\mathbf{B})\end{split}\\

</div>

As in the
<a href="#sec-heat-conduction-model" class="reference internal"><span
class="std std-ref">heat conduction example</span></a>, a class is
created which inherits from <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv412PhysicsModel"
class="reference internal" title="PhysicsModel"><span class="pre"><code
class="sourceCode cpp">PhysicsModel</code></span></a> and defines
<span class="pre">`init`</span> and <span class="pre">`rhs`</span>
functions:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class MHD : public PhysicsModel {
      private:
      int init(bool restarting) override {
        ...
      }
      int rhs(BoutReal t) override {
        ...
      }
    };

</div>

</div>

The <span class="pre">`init`</span> function is called once at the start
of the simulation, and should set up the problem, specifying which
variables are to be evolved. The argument
<span class="pre">`restarting`</span> is false the first time a problem
is run, and true if loading the state from a restart file.

The <span class="pre">`rhs`</span> function is called every time-step,
and should calculate the time-derivatives for a given state. In both
cases returning non-zero tells BOUT++ that an error occurred.

<div id="variables" class="section">

<span id="sec-variables"></span>

### Variables<a href="#variables" class="headerlink"
title="Permalink to this heading">#</a>

We need to define the variables to evolve as member variables (so they
can be used in <span class="pre">`init`</span> and
<span class="pre">`rhs`</span>).

For ideal MHD, we need two 3D scalar fields density
<span class="math notranslate nohighlight">\\\rho\\</span> and pressure
<span class="math notranslate nohighlight">\\p\\</span>, and two 3D
vector fields velocity
<span class="math notranslate nohighlight">\\v\\</span>, and magnetic
field <span class="math notranslate nohighlight">\\B\\</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class MHD : public PhysicsModel {
      private:
      Field3D rho, p; // 3D scalar fields
      Vector3D v, B;  // 3D vector fields
      ...
    };

</div>

</div>

Scalar and vector fields behave much as you would expect:
<a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
class="reference internal" title="Field3D"><span class="pre"><code
class="sourceCode cpp">Field3D</code></span></a> objects can be added,
subtracted, multiplied and divided, so the following examples are all
valid operations:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D a, b, c;
    BoutReal r;

    a = b + c; a = b - c;
    a = b * c; a = r * b;
    a = b / c; a = b / r; a = r / b;

</div>

</div>

Similarly, vector objects can be added/subtracted from each other,
multiplied/divided by scalar fields and real numbers, for example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Vector3D a, b, c;
    Field3D f;
    BoutReal r;

    a = b + c; a = b - c;
    a = b * f; a = b * r;
    a = b / f; a = b / r;

</div>

</div>

In addition the dot and cross products are represented by
<span class="pre">`*`</span> and
<span class="math notranslate nohighlight">\\\wedge\\</span> symbols:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Vector3D a, b, c;
    Field3D f;

    f = a * b // Dot-product
    a = b ^ c // Cross-product

</div>

</div>

For both scalar and vector field operations, so long as the result of an
operation is of the correct type, the usual C/C++ shorthand notation can
be used:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D a, b;
    Vector3D v, w;

    a += b; v *= a; v -= w; v ^= w; // valid
    v *= w; // NOT valid: result of dot-product is a scalar

</div>

</div>

**Note**: The operator precedence for
<span class="math notranslate nohighlight">\\\wedge\\</span> is lower
than <span class="pre">`+`</span>, <span class="pre">`*`</span> and
<span class="pre">`/`</span> so it is recommended to surround
<span class="pre">`a`</span>` `<span class="pre">`^`</span>` `<span class="pre">`b`</span>
with braces.

</div>

<div id="evolution-equations" class="section">

### Evolution equations<a href="#evolution-equations" class="headerlink"
title="Permalink to this heading">#</a>

At this point we can tell BOUT++ which variables to evolve, and where
the state and time-derivatives will be stored. This is done using the <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel10bout_solveER7Field2DPKcRKNSt6stringE"
class="reference internal" title="PhysicsModel::bout_solve"><span
class="pre"><code
class="sourceCode cpp">bout_solve<span class="op">(</span>variable<span class="op">,</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp">name<span class="op">)</span></code></span></a>
function in your physics model <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel4initEb"
class="reference internal" title="PhysicsModel::init"><span
class="pre"><code class="sourceCode cpp">init</code></span></a>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int init(bool restarting) {
      bout_solve(rho, "density");
      bout_solve(p,   "pressure");
      v.covariant = true; // evolve covariant components
      bout_solve(v,   "v");
      B.covariant = false; // evolve contravariant components
      bout_solve(B,   "B");

      return 0;
    }

</div>

</div>

The name given to this function will be used in the output and restart
data files. These will be automatically read and written depending on
input options (see
<a href="bout_options.html#sec-options" class="reference internal"><span
class="std std-ref">BOUT++ options</span></a>). Input options based on
these names are also used to initialise the variables.

You can add a description of the variable which will be saved as an
attribute in the output files by adding a third argument to
<span class="pre">`bout_solve()`</span> e.g.:

<div class="highlight-cpp notranslate">

<div class="highlight">

    bout_solve(rho, "density", "electron density");
    bout_solve(B, "B", "total magnetic field strength");

</div>

</div>

If the name of the variable in the output file is the same as the
variable name, you can use a shorthand macro. In this case, we could use
this shorthand for <span class="pre">`v`</span> and
<span class="pre">`B`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    SOLVE_FOR(v);
    SOLVE_FOR(B);

</div>

</div>

To make this even shorter, multiple fields can be passed to
<span class="pre">`SOLVE_FOR`</span> (up to 10 at the time of writing).
We can also use macros <span class="pre">`SOLVE_FOR2`</span>,
<span class="pre">`SOLVE_FOR3`</span>, …,
<span class="pre">`SOLVE_FOR6`</span> which are used in many models. Our
initialisation code becomes:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int init(bool restarting) override {
      ...
      bout_solve(rho, "density");
      bout_solve(p,   "pressure");
      v.covariant = true; // evolve covariant components
      B.covariant = false; // evolve contravariant components
      SOLVE_FOR(v, B);
      ...
      return 0;
    }

</div>

</div>

Vector quantities can be stored in either covariant or contravariant
form. The value of the <a
href="../_breathe_autogen/file/vector3d_8hxx.html#_CPPv4N8Vector3D9covariantE"
class="reference internal" title="Vector3D::covariant"><span
class="pre"><code
class="sourceCode cpp">Vector3D<span class="op">::</span>covariant</code></span></a>
property when <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel10bout_solveER7Field2DPKcRKNSt6stringE"
class="reference internal" title="PhysicsModel::bout_solve"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>bout_solve<span class="op">()</span></code></span></a>
(or <span class="pre">`SOLVE_FOR`</span>) is called is the form which is
evolved in time and saved to the output file.

The equations to be solved can now be written in the
<span class="pre">`rhs`</span> function. The value passed to the
function
(<span class="pre">`BoutReal`</span>` `<span class="pre">`t`</span>) is
the simulation time - only needed if your equations contain
time-dependent sources or similar terms. To refer to the time-derivative
of a variable <span class="pre">`var`</span>, use
<span class="pre">`ddt(var)`</span>. The ideal MHD equations can be
written as:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int rhs(BoutReal t) override {
      ddt(rho) = -V_dot_Grad(v, rho) - rho*Div(v);
      ddt(p) = -V_dot_Grad(v, p) - g*p*Div(v);
      ddt(v) = -V_dot_Grad(v, v) + ( (Curl(B)^B) - Grad(p) ) / rho;
      ddt(B) = Curl(v^B);
    }

</div>

</div>

Where the differential operators <a
href="../_breathe_autogen/file/vecops_8cxx.html#_CPPv44GradRK7Field2D8CELL_LOCRKNSt6stringE"
class="reference internal" title="Grad"><span class="pre"><code
class="sourceCode cpp">vector</code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="op">=</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp">Grad<span class="op">(</span>scalar<span class="op">)</span></code></span></a>,
<a
href="../_breathe_autogen/file/vecops_8cxx.html#_CPPv43DivRK8Vector2D8CELL_LOCRKNSt6stringE"
class="reference internal" title="Div"><span class="pre"><code
class="sourceCode cpp">scalar</code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="op">=</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp">Div<span class="op">(</span>vector<span class="op">)</span></code></span></a>,
and <a
href="../_breathe_autogen/file/vecops_8cxx.html#_CPPv44CurlRK8Vector2D"
class="reference internal" title="Curl"><span class="pre"><code
class="sourceCode cpp">vector</code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp"><span class="op">=</span></code></span><code
class="sourceCode cpp"> </code><span class="pre"><code
class="sourceCode cpp">Curl<span class="op">(</span>vector<span class="op">)</span></code></span></a>
are used. For the density and pressure equations, the
<span class="math notranslate nohighlight">\\\mathbf{v}\cdot\nabla\rho\\</span>
term could be written as <span class="pre">`v*Grad(rho)`</span>, but
this would then use central differencing in the Grad operator. Instead,
the function <a
href="../_breathe_autogen/file/vecops_8cxx.html#_CPPv410V_dot_GradRK8Vector2DRK7Field2D"
class="reference internal" title="V_dot_Grad"><span class="pre"><code
class="sourceCode cpp">V_dot_Grad<span class="op">()</span></code></span></a>
uses upwinding methods for these advection terms. In addition, the <a
href="../_breathe_autogen/file/vecops_8cxx.html#_CPPv44GradRK7Field2D8CELL_LOCRKNSt6stringE"
class="reference internal" title="Grad"><span class="pre"><code
class="sourceCode cpp">Grad<span class="op">()</span></code></span></a>
function will not operate on vector objects (since result is neither
scalar nor vector), so the
<span class="math notranslate nohighlight">\\\mathbf{v}\cdot\nabla\mathbf{v}\\</span>
term CANNOT be written as <span class="pre">`v*Grad(v)`</span>.

</div>

<div id="input-options" class="section">

<span id="sec-inputopts"></span>

### Input options<a href="#input-options" class="headerlink"
title="Permalink to this heading">#</a>

Note that in the above equations the extra parameter
<span class="pre">`g`</span> has been used for the ratio of specific
heats. To enable this to be set in the input options file (see
<a href="bout_options.html#sec-options" class="reference internal"><span
class="std std-ref">BOUT++ options</span></a>), we use the
<a href="../_breathe_autogen/file/options_8hxx.html#_CPPv47Options"
class="reference internal" title="Options"><span class="pre"><code
class="sourceCode cpp">Options</code></span></a> object in the
initialisation function:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class MHD : public PhysicsModel {
      private:
      BoutReal gamma;

      int init(bool restarting) override {
        auto& globalOptions = Options::root();
        auto& options = globalOptions["mhd"];

        OPTION(options, g, 5.0 / 3.0);
        ...

</div>

</div>

This specifies that an option called “g” in a section called “mhd”
should be put into the variable <span class="pre">`g`</span>. If the
option could not be found, or was of the wrong type, the variable should
be set to a default value of
<span class="math notranslate nohighlight">\\5/3\\</span>. The value
used will be printed to the output file, so if
<span class="pre">`g`</span> is not set in the input file the following
line will appear:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Option mhd:g = 1.66667 (default)

</div>

</div>

This function can be used to get integers and booleans. To get strings,
there is the function
(<span class="pre">`char*`</span>` `<span class="pre">`options.getString(section,`</span>` `<span class="pre">`name)`</span>.
To separate options specific to the physics model, these options should
be put in a separate section, for example here the “mhd” section has
been specified.

Most of the time, the name of the variable (e.g.
<span class="pre">`g`</span>) will be the same as the identifier in the
options file (“g”). In this case, there is the macro:

<div class="highlight-cpp notranslate">

<div class="highlight">

    OPTION(options, g, 5.0/3.0);

</div>

</div>

which is equivalent to:

<div class="highlight-cpp notranslate">

<div class="highlight">

    g = options["g"].withDefault( 5.0/3.0 );

</div>

</div>

See
<a href="bout_options.html#sec-options" class="reference internal"><span
class="std std-ref">BOUT++ options</span></a> for more details of how to
use the input options.

</div>

<div id="communication" class="section">

### Communication<a href="#communication" class="headerlink"
title="Permalink to this heading">#</a>

If you plan to run BOUT++ on more than one processor, any operations
involving derivatives will require knowledge of data stored on other
processors. To handle the necessary parallel communication, there is the
<a
href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4IDpEN4Mesh11communicateEvDpR2Ts"
class="reference internal" title="Mesh::communicate"><span
class="pre"><code
class="sourceCode cpp">mesh<span class="op">-&gt;</span>communicate</code></span></a>
function. This takes care of where the data needs to go to/from, and
only needs to be told which variables to transfer.

If you only need to communicate a small number (up to 5 currently) of
variables then just call the <a
href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4IDpEN4Mesh11communicateEvDpR2Ts"
class="reference internal" title="Mesh::communicate"><span
class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>communicate<span class="op">()</span></code></span></a>
function directly. For the MHD code, we need to communicate the
variables <span class="pre">`rho,p,v,B`</span> at the beginning of the
<a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel3rhsE8BoutReal"
class="reference internal" title="PhysicsModel::rhs"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>rhs<span class="op">()</span></code></span></a>
function before any derivatives are calculated:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int rhs(BoutReal t) override {
      mesh->communicate(rho, p, v, B);

</div>

</div>

If you need to communicate lots of variables, or want to change at
run-time which variables are evolved (e.g. depending on input options),
then you can create a group of variables and communicate them later. To
do this, first create a <a
href="../_breathe_autogen/file/fieldgroup_8hxx.html#_CPPv410FieldGroup"
class="reference internal" title="FieldGroup"><span class="pre"><code
class="sourceCode cpp">FieldGroup</code></span></a> object , in this
case called <span class="pre">`comms`</span> , then use the add method.
This method does no communication, but records which variables to
transfer when the communication is done later:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class MHD : public PhysicsModel {
      private:
      FieldGroup comms;

      int init(bool restarting) override {
        ...
        comms.add(rho);
        comms.add(p);
        comms.add(v);
        comms.add(B);
        ...

</div>

</div>

The <a
href="../_breathe_autogen/file/fieldgroup_8hxx.html#_CPPv4N10FieldGroup3addERK10FieldGroup"
class="reference internal" title="FieldGroup::add"><span
class="pre"><code
class="sourceCode cpp">comms<span class="op">.</span>add<span class="op">()</span></code></span></a>
routine can be given any number of variables at once (there’s no
practical limit on the total number of variables which are added to a <a
href="../_breathe_autogen/file/fieldgroup_8hxx.html#_CPPv410FieldGroup"
class="reference internal" title="FieldGroup"><span class="pre"><code
class="sourceCode cpp">FieldGroup</code></span></a> ), so this can be
shortened to:

<div class="highlight-cpp notranslate">

<div class="highlight">

    comms.add(rho, p, v, B);

</div>

</div>

To perform the actual communication, call the <a
href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4IDpEN4Mesh11communicateEvDpR2Ts"
class="reference internal" title="Mesh::communicate"><span
class="pre"><code
class="sourceCode cpp">mesh<span class="op">-&gt;</span>communicate</code></span></a>
function with the group. In this case we need to communicate all these
variables before performing any calculations, so call this function at
the start of the <span class="pre">`rhs`</span> routine:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int rhs(BoutReal t) override {
      mesh->communicate(comms);
      ...

</div>

</div>

In many situations there may be several groups of variables which can be
communicated at different times. The function
<span class="pre">`mesh->communicate`</span> consists of a call to <a
href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4IDpEN4Mesh4sendE11comm_handleDpR2Ts"
class="reference internal" title="Mesh::send"><span class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>send<span class="op">()</span></code></span></a>
followed by <a
href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4N4Mesh4waitE11comm_handle"
class="reference internal" title="Mesh::wait"><span class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>wait<span class="op">()</span></code></span></a>
which can be done separately to interleave calculations and
communications. This will speed up the code if parallel communication
bandwidth is a problem for your simulation.

In our MHD example, the calculation of
<span class="pre">`ddt(rho)`</span> and
<span class="pre">`ddt(p)`</span> does not require
<span class="pre">`B`</span>, so we could first communicate
<span class="pre">`rho`</span>, <span class="pre">`p`</span>, and
<span class="pre">`v`</span>, send <span class="pre">`B`</span> and do
some calculations whilst communications are performed:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int rhs(BoutReal t) override {
      mesh->communicate(rho, p, v); // sends and receives rho, p and v
      comm_handle ch = mesh->send(B);// only send B

      ddt(rho) = ...
      ddt(p) = ...

      mesh->wait(ch); // now wait for B to arrive

      ddt(v) = ...
      ddt(B) = ...

      return 0;
    }

</div>

</div>

This scheme is not used in <span class="pre">`mhd.cxx`</span>, partly
for clarity, and partly because currently communications are not a
significant bottleneck (too much inefficiency elsewhere!).

When a differential is calculated, points on neighbouring cells are
assumed to be in the guard cells. There is no way to calculate the
result of the differential in the guard cells, and so after every
differential operator the values in the guard cells are invalid.
Therefore, if you take the output of one differential operator and use
it as input to another differential operator, you must perform
communications (and set boundary conditions) first. See
<a href="differential_operators.html#sec-diffops"
class="reference internal"><span class="std std-ref">Differential
operators</span></a>.

</div>

<div id="error-handling" class="section">

### Error handling<a href="#error-handling" class="headerlink"
title="Permalink to this heading">#</a>

Finding where bugs have occurred in a (fairly large) parallel code is a
difficult problem. This is more of a concern for developers of BOUT++
(see the developers manual), but it is still useful for the user to be
able to hunt down bug in their own code, or help narrow down where a bug
could be occurring. BOUT++ comes with a <span class="pre">`TRACE`</span>
macro that can be used to easily identify specific regions in a model
when an error occurs.

In the <span class="pre">`mhd.cxx`</span> example each part of the
<span class="pre">`rhs`</span> function has a separate
<span class="pre">`TRACE`</span> macro:

<div class="highlight-cpp notranslate">

<div class="highlight">

    {
      TRACE("ddt(rho)");
      ddt(rho) = -V_dot_Grad(v, rho) - rho*Div(v);
    }

</div>

</div>

If there’s a problem here that causes the model to crash, BOUT++ will
print something like:

<div class="highlight-text notranslate">

<div class="highlight">

    ====== Back trace ======
    -> ddt(rho) on line 83 of 'examples/orszag-tang/mhd.cxx'

</div>

</div>

For more details on what you can do with
<span class="pre">`TRACE`</span> macros, see
<a href="../developer_docs/debugging.html#sec-debugging"
class="reference internal"><span class="std std-ref">Debugging
Models</span></a>.

</div>

<div id="boundary-conditions" class="section">

<span id="sec-physicsmodel-boundary-conditions"></span>

### Boundary conditions<a href="#boundary-conditions" class="headerlink"
title="Permalink to this heading">#</a>

All evolving variables have boundary conditions applied automatically
before the <span class="pre">`rhs`</span> function is called (or
afterwards if the boundaries are being evolved in time). Which condition
is applied depends on the options file settings (see
<a href="boundary_options.html#sec-bndryopts"
class="reference internal"><span class="std std-ref">Boundary
conditions</span></a>). If you want to disable this and apply your own
boundary conditions then set boundary condition to
<span class="pre">`none`</span> in the
<span class="pre">`BOUT.inp`</span> options file.

In addition to evolving variables, it’s sometimes necessary to impose
boundary conditions on other quantities which are not explicitly
evolved.

The simplest way to set a boundary condition is to specify it as text,
so to apply a Dirichlet boundary condition:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D var;
    ...
    var.applyBoundary("dirichlet");

</div>

</div>

The format is exactly the same as in the options file. Each time this is
called it must parse the text, create and destroy boundary objects. To
avoid this overhead and have different boundary conditions for each
region, it’s better to set the boundary conditions you want to use first
in <span class="pre">`init`</span>, then just apply them every time:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class MHD : public PhysicsModel {
      Field3D var;

      int init(bool restarting) override {
        ...
        var.setBoundary("myVar");
        ...
      }

      int rhs(BoutReal t) override {
        ...
        var.applyBoundary();
        ...
      }
    }

</div>

</div>

This will look in the options file for a section called
<span class="pre">`[myvar]`</span> (upper or lower case doesn’t matter)
in the same way that evolving variables are handled. In fact this is
precisely what is done: inside <a
href="../_breathe_autogen/file/physicsmodel_8hxx.html#_CPPv4N12PhysicsModel10bout_solveER7Field2DPKcRKNSt6stringE"
class="reference internal" title="PhysicsModel::bout_solve"><span
class="pre"><code
class="sourceCode cpp">PhysicsModel<span class="op">::</span>bout_solve<span class="op">()</span></code></span></a>
(or <span class="pre">`SOLVE_FOR`</span>) the
<span class="pre">`Field3D::setBoundary`</span> method is called, and
then after <span class="pre">`rhs`</span> the <a
href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv4N7Field3D13applyBoundaryEb"
class="reference internal" title="Field3D::applyBoundary"><span
class="pre"><code
class="sourceCode cpp">Field3D<span class="op">::</span>applyBoundary<span class="op">()</span></code></span></a>
method is called on each evolving variable. This method also gives you
the flexibility to apply different boundary conditions on different
boundary regions (e.g. radial boundaries and target plates); the first
method just applies the same boundary condition to all boundaries.

Another way to set the boundaries is to copy them from another variable:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D a, b;
    ...
    a.setBoundaryTo(b); // Copy b's boundaries into a
    ...

</div>

</div>

Note that this will copy the value at the boundary, which is half-way
between mesh points. This is not the same as copying the guard cells
from field <span class="pre">`b`</span> to field
<span class="pre">`a`</span>. The value at the boundary cell is
calculated using second-order central difference. For example if there
is one boundary cell, so that <span class="pre">`a(0,y,z)`</span> is the
boundary cell, and <span class="pre">`a(1,y,z)`</span> is in the domain,
then the boundary would be set so that:

<div class="highlight-cpp notranslate">

<div class="highlight">

    a(0,y,z) + a(1,y,z) = b(0,y,z) + b(1,y,z)

</div>

</div>

rearranged as:

<div class="highlight-cpp notranslate">

<div class="highlight">

    a(0,y,z) = - a(1,y,z) + b(0,y,z) + b(1,y,z)

</div>

</div>

To copy the boundary cells (and communication guard cells), iterate over
them:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BOUT_FOR(i, a.getRegion("RGN_GUARDS")) {
      a[i] = b[i];
    }

</div>

</div>

See <a href="../developer_docs/data_types.html#sec-iterating"
class="reference internal"><span class="std std-ref">Iterating over
fields</span></a> for more details on iterating over custom regions.

</div>

<div id="custom-boundary-conditions" class="section">

<span id="sec-custom-bc"></span>

### Custom boundary conditions<a href="#custom-boundary-conditions" class="headerlink"
title="Permalink to this heading">#</a>

The boundary conditions supplied with the BOUT++ library cover the most
common situations, but cannot cover all of them. If the boundary
condition you need isn’t available, then it’s quite straightforward to
write your own. First you need to make sure that your boundary condition
isn’t going to be overwritten. To do this, set the boundary condition to
“none” in the BOUT.inp options file, and BOUT++ will leave that boundary
alone. For example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    [P]
    bndry_all = dirichlet
    bndry_xin = none
    bndry_xout = none

</div>

</div>

would set all boundaries for the variable “P” to zero value, except for
the X inner and outer boundaries which will be left alone for you to
modify.

To set an X boundary condition, it’s necessary to test if the processor
is at the left boundary (first in X), or right boundary (last in X).
Note that it might be both if
<span class="pre">`NXPE`</span>` `<span class="pre">`=`</span>` `<span class="pre">`1`</span>,
or neither if
<span class="pre">`NXPE`</span>` `<span class="pre">`>`</span>` `<span class="pre">`2`</span>.

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D f;
    ...
    if(mesh->firstX()) {
      // At the left of the X domain
      // set f[0:1][*][*] i.e. first two points in X, all Y and all Z
      for(int x=0; x < 2; x++)
        for(int y=0; y < mesh->LocalNy; y++)
          for(int z=0; z < mesh->LocalNz; z++) {
            f(x,y,z) = ...
          }
    }
    if(mesh->lastX()) {
      // At the right of the X domain
      // Set last two points in X
      for(int x=mesh->LocalNx-2; x < mesh->LocalNx; x++)
        for(int y=0; y < mesh->LocalNy; y++)
          for(int z=0; z < mesh->LocalNz; z++) {
            f(x,y,z) = ...
          }
    }

</div>

</div>

note the size of the local mesh including guard cells is given by
<a href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4N4Mesh7LocalNxE"
class="reference internal" title="Mesh::LocalNx"><span class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>LocalNx</code></span></a>,
<a href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4N4Mesh7LocalNyE"
class="reference internal" title="Mesh::LocalNy"><span class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>LocalNy</code></span></a>,
and
<a href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4N4Mesh7LocalNzE"
class="reference internal" title="Mesh::LocalNz"><span class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>LocalNz</code></span></a>.
The functions
<a href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4NK4Mesh6firstXEv"
class="reference internal" title="Mesh::firstX"><span class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>firstX<span class="op">()</span></code></span></a>
and
<a href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4NK4Mesh5lastXEv"
class="reference internal" title="Mesh::lastX"><span class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>lastX<span class="op">()</span></code></span></a>
return true only if the current processor is on the left or right of the
X domain respectively.

Setting custom Y boundaries is slightly more complicated than X
boundaries, because target or limiter plates could cover only part of
the domain. Rather than use a <span class="pre">`for`</span> loop to
iterate over the points in the boundary, we need to use a more general
iterator:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D f;
    ...
    RangeIterator it = mesh->iterateBndryLowerY();
    for(it.first(); !it.isDone(); it++) {
      // it.ind contains the x index
      for(int y=2;y>=0;y--)  // Boundary width 3 points
        for(int z=0;z<mesh->LocalNz;z++) {
          ddt(f)(it.ind,y,z) = 0.;  // Set time-derivative to zero in boundary
        }
    }

</div>

</div>

This would set the time-derivative of <span class="pre">`f`</span> to
zero in a boundary of width 3 in Y (from 0 to 2 inclusive). In the same
way <span class="pre">`mesh->iterateBndryUpperY()`</span> can be used to
iterate over the upper boundary:

<div class="highlight-cpp notranslate">

<div class="highlight">

    RangeIterator it = mesh->iterateBndryUpperY();
    for(it.first(); !it.isDone(); it++) {
      // it.ind contains the x index
      for(int y=mesh->LocalNy-3;y<mesh->LocalNy;y--)  // Boundary width 3 points
        for(int z=0;z<mesh->LocalNz;z++) {
          ddt(f)(it.ind,y,z) = 0.;  // Set time-derivative to zero in boundary
        }
    }

</div>

</div>

</div>

<div id="initial-profiles" class="section">

### Initial profiles<a href="#initial-profiles" class="headerlink"
title="Permalink to this heading">#</a>

Up to this point the code is evolving total density, pressure etc. This
has advantages for clarity, but has problems numerically: For small
perturbations, rounding error and tolerances in the time-integration
mean that linear dispersion relations are not calculated correctly. The
solution to this is to write all equations in terms of an initial
“background” quantity and a time-evolving perturbation, for example
<span class="math notranslate nohighlight">\\\rho(t) \rightarrow
\rho_0 + \tilde{\rho}(t)\\</span>. For this reason, **the initialisation
of all variables passed to the \`PhysicsModel::bout_solve\` function is
a combination of small-amplitude gaussians and waves; the user is
expected to have performed this separation into background and perturbed
quantities.**

To read in a quantity from a grid file, there is the
<span class="pre">`mesh->get`</span> function:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field2D Ni0; // Background density

    int init(bool restarting) override {
      ...
      mesh->get(Ni0, "Ni0");
      ...
    }

</div>

</div>

As with the input options, most of the time the name of the variable in
the physics code will be the same as the name in the grid file to avoid
confusion. In this case, you can just use:

<div class="highlight-cpp notranslate">

<div class="highlight">

    GRID_LOAD(Ni0);

</div>

</div>

which is equivalent to:

<div class="highlight-cpp notranslate">

<div class="highlight">

    mesh->get(Ni0, "Ni0");

</div>

</div>

(see <a
href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv4N4Mesh3getERNSt6stringERKNSt6stringERKNSt6stringE"
class="reference internal" title="Mesh::get"><span class="pre"><code
class="sourceCode cpp">Mesh<span class="op">::</span>get<span class="op">()</span></code></span></a>).

</div>

<div id="output-variables" class="section">

### Output variables<a href="#output-variables" class="headerlink"
title="Permalink to this heading">#</a>

<div class="admonition warning">

Warning

File IO has changed significantly in BOUT++ v5. See
<a href="../developer_docs/file_io.html#sec-file-io-v5"
class="reference internal"><span class="std std-ref">Changes in BOUT++
v5</span></a> for more details

</div>

BOUT++ always writes the evolving variables to file, but often it’s
useful to add other variables to the output. For convenience you might
want to write the normalised starting profiles or other non-evolving
values to file. For example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field2D Ni0;
    ...
    GRID_LOAD(Ni0);
    dump.add(Ni0, "Ni0", false);

</div>

</div>

where the ’false’ at the end means the variable should only be written
to file once at the start of the simulation. For convenience there are
some macros e.g.:

<div class="highlight-cpp notranslate">

<div class="highlight">

    SAVE_ONCE(Ni0);

</div>

</div>

is equivalent to:

<div class="highlight-cpp notranslate">

<div class="highlight">

    dump.add(Ni0, "Ni0", false);

</div>

</div>

Optionally, you can add a description to document what the variable
represents, which will be saved as an attribute of the variable in the
output file, e.g.:

<div class="highlight-cpp notranslate">

<div class="highlight">

    dump.add(Ni0, "Ni0", false, "background density profile");

</div>

</div>

(see <span class="pre">`Datafile::add`</span>). In some situations you
might also want to write some data to a different file. To do this,
create a <span class="pre">`Datafile`</span> object:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Datafile mydata;

</div>

</div>

in <span class="pre">`init`</span>, you then:

1.  (optional) Initialise the file, passing it the options to use. If
    you skip this step, default (sane) options will be used. This just
    allows you to enable/disable, use parallel I/O, set whether files
    are opened and closed every time etc.:

    <div class="highlight-cpp notranslate">

    <div class="highlight">

        mydata = Datafile(Options::getRoot()->getSection("mydata"));

    </div>

    </div>

    which would use options in a section
    <span class="pre">`[mydata]`</span> in BOUT.inp

2.  Open the file for writing:

    <div class="highlight-cpp notranslate">

    <div class="highlight">

        mydata.openw("mydata.nc")

    </div>

    </div>

    (see <span class="pre">`Datafile::openw`</span>). By default this
    only specifies the file name; actual opening of the file happens
    later when the data is written. If you are not using parallel I/O,
    the processor number is also inserted into the file name before the
    last “.”, so mydata.nc” becomes “mydata.0.nc”, “mydata.1.nc” etc.

    (see e.g. src/fileio/datafile.cxx line 139, which calls
    src/fileio/dataformat.cxx line 23, which then calls the file format
    interface e.g. src/fileio/impls/netcdf/nc_format.cxx line 172).

3.  Add variables to the file

    <div class="highlight-cpp notranslate">

    <div class="highlight">

        // Not evolving. Every time the file is written, this will be overwritten
        mydata.add(variable, "name");
        // Evolving. Will output a sequence of values
        mydata.add(variable2, "name2", true);

    </div>

    </div>

Whenever you want to write values to the file, for example in
<span class="pre">`rhs`</span> or a monitor, just call:

<div class="highlight-cpp notranslate">

<div class="highlight">

    mydata.write();

</div>

</div>

(see <span class="pre">`Datafile::write`</span>). To collect the data
afterwards, you can specify the prefix to collect. In Python (see
<a href="../_apidoc/boutdata.html#boutdata.collect.collect"
class="reference internal" title="boutdata.collect.collect"><span
class="pre"><code class="sourceCode python">collect()</code></span></a>):

<div class="highlight-cpp notranslate">

<div class="highlight">

    >>> var = collect("name", prefix="mydata")

</div>

</div>

By default the prefix is “BOUT.dmp”.

</div>

<div id="variable-attributes" class="section">

### Variable attributes<a href="#variable-attributes" class="headerlink"
title="Permalink to this heading">#</a>

An experimental feature is the ability to add attributes to output
variables. Do this using with
<span class="pre">`Datafile::setAttribute`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    dump.setAttribute(variable, attribute, value);

</div>

</div>

where <span class="pre">`variable`</span> is the name of the variable;
<span class="pre">`attribute`</span> is the name of the attribute, and
<span class="pre">`value`</span> can be either a string or an integer.
For example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    dump.setAttribute("Ni0", "units", "m^-3");

</div>

</div>

</div>

</div>

<div id="reduced-mhd" class="section">

## Reduced MHD<a href="#reduced-mhd" class="headerlink"
title="Permalink to this heading">#</a>

The MHD example presented previously covered some of the functions
available in BOUT++, which can be used for a wide variety of models.
There are however several other significant functions and classes which
are commonly used, which will be illustrated using the
<span class="pre">`reconnect-2field`</span> example. This is solving
equations for
<span class="math notranslate nohighlight">\\A\_{||}\\</span> and
vorticity <span class="math notranslate nohighlight">\\U\\</span>

<div class="math notranslate nohighlight">

\\\begin{split}{{\frac{\partial U}{\partial t}}} =&
-\frac{1}{B}\mathbf{b}\_0\times\nabla\phi\cdot\nabla U + B^2
\nabla\_{||}(j\_{||} / B) \\ {{\frac{\partial A\_{||}}{\partial t}}} =&
-\frac{1}{\hat{\beta}}\nabla\_{||}\phi - \eta\frac{1}{\hat{\beta}}
j\_{||}\end{split}\\

</div>

with <span class="math notranslate nohighlight">\\\phi\\</span> and
<span class="math notranslate nohighlight">\\j\_{||}\\</span> given by

<div class="math notranslate nohighlight">

\\\begin{split}U =& \frac{1}{B}\nabla\_\perp^2\phi \\ j\_{||} =&
-\nabla\_\perp^2 A\_{||}\end{split}\\

</div>

First create the variables which are going to be evolved, ensure they’re
communicated:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class TwoField : public PhysicsModel {
      private:
      Field3D U, Apar; // Evolving variables

      int init(bool restarting) override {

        SOLVE_FOR(U, Apar);
      }

      int rhs(BoutReal t) override {
        mesh->communicate(U, Apar);
      }
    };

</div>

</div>

In order to calculate the time derivatives, we need the auxiliary
variables <span class="math notranslate nohighlight">\\\phi\\</span> and
<span class="math notranslate nohighlight">\\j\_{||}\\</span>.
Calculating
<span class="math notranslate nohighlight">\\j\_{||}\\</span> from
<span class="math notranslate nohighlight">\\A\_{||}\\</span> is a
straightforward differential operation, but getting
<span class="math notranslate nohighlight">\\\phi\\</span> from
<span class="math notranslate nohighlight">\\U\\</span> means inverting
a Laplacian.

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D U, Apar;
    Field3D phi, jpar; // Auxilliary variables

    int init(bool restarting) override {
      SOLVE_FOR(U, Apar);
      SAVE_REPEAT(phi, jpar); // Save variables in output file
      return 0;
    }

    int rhs(BoutReal t) override {
      phi = invert_laplace(mesh->Bxy*U, phi_flags); // Solve for phi
      mesh->communicate(U, Apar, phi);  // Communicate phi
      jpar = -Delp2(Apar);     // Calculate jpar
      mesh->communicate(jpar); // Communicate jpar
      return 0;
    }

</div>

</div>

Note that the Laplacian inversion code takes care of boundary regions,
so <span class="pre">`U`</span> doesn’t need to be communicated first.
The differential operator <span class="pre">`Delp2`</span> , like all
differential operators, needs the values in the guard cells and so
<span class="pre">`Apar`</span> needs to be communicated before
calculating <span class="pre">`jpar`</span> . Since we will need to take
derivatives of <span class="pre">`jpar`</span> later, this needs to be
communicated as well.

<div class="highlight-cpp notranslate">

<div class="highlight">

    int rhs(BoutReal t) override {
      ...
      mesh->communicate(jpar);

      ddt(U) = -b0xGrad_dot_Grad(phi, U) + SQ(mesh->Bxy)*Grad_par(Jpar / mesh->Bxy)
      ddt(Apar) = -Grad_par(phi) / beta_hat - eta*jpar / beta_hat; }

</div>

</div>

</div>

<div id="logging-output" class="section">

<span id="sec-logging"></span>

## Logging output<a href="#logging-output" class="headerlink"
title="Permalink to this heading">#</a>

Logging should be used to report simulation progress, record
information, and warn about potential problems. BOUT++ includes a simple
logging facility which supports both C printf and C++ iostream styles.
For example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    output.write("This is an integer: {}, and this a real: {}\n", 5, 2.0)

    output << "This is an integer: " << 5 << ", and this a real: " << 2.0 << '\n';

</div>

</div>

Formatting in the <span class="pre">`output.write`</span> function is
done using the
<a href="https://fmt.dev" class="reference external">{fmt} library</a>.
By default this cannot format BOUT++ types, but by including
<span class="pre">`output_bout_types.hxx`</span> some BOUT++ types can
be formatted.

Messages sent to <span class="pre">`output`</span> on processor 0 will
be printed to console and saved to
<span class="pre">`BOUT.log.0`</span>. Messages from all other
processors will only go to their log files,
<span class="pre">`BOUT.log.#`</span> where <span class="pre">`#`</span>
is the processor number.

**Note**: If an error occurs on a processor other than processor 0, then
the error message will usually only be in the log file, not printed to
console. If BOUT++ crashes but no error message is printed, try looking
at the ends of all log files:

<div class="highlight-bash notranslate">

<div class="highlight">

    $ tail BOUT.log.*

</div>

</div>

For finer control over which messages are printed, several outputs are
available, listed in the table below.

<table class="table">
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Usage</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">output_debug</code></span></p></td>
<td><p>For highly verbose output messages, that are normally not needed.
Needs to be enabled with a compile switch</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">output_info</code></span></p></td>
<td><p>For infos like what options are used</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">output_progress</code></span></p></td>
<td><p>For infos about the current progress</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">output_warn</code></span></p></td>
<td><p>For warnings</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">output_error</code></span></p></td>
<td><p>For errors</p></td>
</tr>
</tbody>
</table>

<div id="controlling-logging-level" class="section">

### Controlling logging level<a href="#controlling-logging-level" class="headerlink"
title="Permalink to this heading">#</a>

By default all of the outputs (except
<span class="pre">`output_debug`</span>) are saved to log and printed to
console (processor 0 only).

To reduce the volume of outputs the command line argument
<span class="pre">`--quiet`</span> (<span class="pre">`-q`</span> for
short) reduces the output level by one, and
<span class="pre">`--verbose`</span> (<span class="pre">`-v`</span> for
short) increases it by one. Running with <span class="pre">`-q`</span>
in the command line arguments suppresses the
<span class="pre">`output_info`</span> messages, so that they will not
appear in the console or log file. Running with
<span class="pre">`-q`</span>` `<span class="pre">`-q`</span> suppresses
everything except <span class="pre">`output_warn`</span> and
<span class="pre">`output_error`</span>.

To enable the <span class="pre">`output_debug`</span> messages,
configure BOUT++ with a <span class="pre">`CHECK`</span> level
<span class="pre">`>=`</span>` `<span class="pre">`3`</span>. To enable
it at lower check levels, configure BOUT++ with
<span class="pre">`-DBOUT_ENABLE_OUTPUT_DEBUG=ON`</span>. When running
BOUT++ add a
<span class="pre">`-v`</span>` `<span class="pre">`-v`</span> flag to
see <span class="pre">`output_debug`</span> messages.

</div>

</div>

<div id="updating-physics-models-from-v3-to-v4" class="section">

<span id="sec-3to4"></span>

## Updating Physics Models from v3 to v4<a href="#updating-physics-models-from-v3-to-v4" class="headerlink"
title="Permalink to this heading">#</a>

Version 4.0.0 of BOUT++ introduced several features which break
backwards compatibility. If you already have physics models, you will
most likely need to update them to work with version 4. The main
breaking changes which you are likely to come across are:

- Using round brackets <span class="pre">`()`</span> instead of square
  brackets <span class="pre">`[]`</span> for indexing fields

- Moving components of
  <a href="../_breathe_autogen/file/mesh_8hxx.html#_CPPv44Mesh"
  class="reference internal" title="Mesh"><span class="pre"><code
  class="sourceCode cpp">Mesh</code></span></a> related to the metric
  tensor and “real space” out into a new object, <a
  href="../_breathe_autogen/file/coordinates_8hxx.html#_CPPv411Coordinates"
  class="reference internal" title="Coordinates"><span class="pre"><code
  class="sourceCode cpp">Coordinates</code></span></a>

- Changed some
  <a href="../_breathe_autogen/file/field3d_8hxx.html#_CPPv47Field3D"
  class="reference internal" title="Field3D"><span class="pre"><code
  class="sourceCode cpp">Field3D</code></span></a> member functions into
  non-member functions

- The shifted metric method has changed in version 4, so that fields are
  stored in orthogonal X-Z coordinates rather than field aligned
  coordinates. This has implications for boundary conditions and
  post-processing. See
  <a href="parallel-transforms.html#sec-parallel-transforms"
  class="reference internal"><span class="std std-ref">Parallel
  Transforms</span></a> for more information.

A new tool is provided, <span class="pre">`bin/bout_3to4.py`</span>,
which can identify these changes, and fix most of them automatically.
Simply run this program on your physic model to see how to update it to
work with version 4:

<div class="highlight-bash notranslate">

<div class="highlight">

    $ ${BOUT_TOP}/bin/bout_3to4.py my_model.cxx

</div>

</div>

The output of this command will show you how to fix each problem it
identifies. To automatically apply them, you can use the
<span class="pre">`--replace`</span> option:

<div class="highlight-bash notranslate">

<div class="highlight">

    $ ${BOUT_TOP}/bin/bout_3to4.py --replace my_model.cxx

</div>

</div>

Also in version 4 is a new syntax for looping over each point in a
field. See <a href="../developer_docs/data_types.html#sec-iterating"
class="reference internal"><span class="std std-ref">Iterating over
fields</span></a> for more information.

</div>

<div id="more-examples" class="section">

<span id="sec-examples"></span>

## More examples<a href="#more-examples" class="headerlink"
title="Permalink to this heading">#</a>

The code and input files in the <span class="pre">`examples/`</span>
subdirectory are for research, demonstrating BOUT++, and to check for
broken functionality. Some proper unit tests have been implemented, but
this is something which needs improving. The examples which were
published in <a href="#dudson2009" id="id1"
class="reference internal"><span>[Dudson2009]</span></a> were
<span class="pre">`drift-instability`</span>,
<span class="pre">`interchange-instability`</span> and
<span class="pre">`orszag-tang`</span>.

<div class="citation-list" role="list">

<div id="dudson2009" class="citation" role="doc-biblioentry">

<span class="label"><span class="fn-bracket">\[</span><a href="#id1" role="doc-backlink">Dudson2009</a><span class="fn-bracket">\]</span></span>

<a href="https://doi.org/10.1016/j.cpc.2009.03.008"
class="reference external">https://doi.org/10.1016/j.cpc.2009.03.008</a>

</div>

</div>

<div id="advect1d" class="section">

### advect1d<a href="#advect1d" class="headerlink"
title="Permalink to this heading">#</a>

The model in <span class="pre">`gas_compress.cxx`</span> solves the
compressible gas dynamics equations for the density
<span class="math notranslate nohighlight">\\n\\</span>, velocity
<span class="math notranslate nohighlight">\\\mathbf{V}\\</span>, and
pressure <span class="math notranslate nohighlight">\\P\\</span>:

</div>

<div id="drift-instability" class="section">

### drift-instability<a href="#drift-instability" class="headerlink"
title="Permalink to this heading">#</a>

The physics code <span class="pre">`2fluid.cxx`</span> implements a set
of reduced Braginskii 2-fluid equations, similar to those solved by the
original BOUT code. This evolves 6 variables: Density, electron and ion
temperatures, parallel ion velocity, parallel current density and
vorticity.

Input grid files are the same as the original BOUT code, but the output
format is different.

</div>

<div id="interchange-instability" class="section">

### interchange-instability<a href="#interchange-instability" class="headerlink"
title="Permalink to this heading">#</a>

<figure id="id2" class="align-default">
<img src="../_images/interchange_inst_test.png"
alt="Interchange instability test" />
<figcaption><p><span class="caption-number">Fig. 2 </span><span
class="caption-text">Interchange instability test. Solid lines are from
analytic theory, symbols from BOUT++ simulations, and the RMS density is
averaged over <span class="math notranslate nohighlight">\(z\)</span>.
Vertical dashed line marks the reference point, where analytic and
simulation results are set equal</span><a href="#id2" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

<div id="sod-shock" class="section">

### sod-shock<a href="#sod-shock" class="headerlink"
title="Permalink to this heading">#</a>

<figure id="id3" class="align-default">
<a href="../_images/sod_result.png"
class="reference internal image-reference"><img
src="../_images/sod_result.png" style="width: 48.0%;"
alt="Sod shock-tube problem for testing shock-handling methods" /></a>
<figcaption><p><span class="caption-number">Fig. 3 </span><span
class="caption-text">Sod shock-tube problem for testing shock-handling
methods</span><a href="#id3" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="new_in_v5.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

New Features in BOUT++ v5.0

</div>

<a href="makefiles.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Makefiles and compiling BOUT++

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#building-physics-models"
  class="reference internal nav-link">Building Physics Models</a>
  - <a href="#using-cmake-with-your-physics-model"
    class="reference internal nav-link">Using CMake with your physics
    model</a>
- <a href="#heat-conduction" class="reference internal nav-link">Heat
  conduction</a>
  - <a href="#initialisation"
    class="reference internal nav-link">Initialisation</a>
  - <a href="#time-evolution" class="reference internal nav-link">Time
    evolution</a>
  - <a href="#running-the-model" class="reference internal nav-link">Running
    the model</a>
- <a href="#magnetohydrodynamics-mhd"
  class="reference internal nav-link">Magnetohydrodynamics (MHD)</a>
  - <a href="#variables" class="reference internal nav-link">Variables</a>
  - <a href="#evolution-equations"
    class="reference internal nav-link">Evolution equations</a>
  - <a href="#input-options" class="reference internal nav-link">Input
    options</a>
  - <a href="#communication"
    class="reference internal nav-link">Communication</a>
  - <a href="#error-handling" class="reference internal nav-link">Error
    handling</a>
  - <a href="#boundary-conditions"
    class="reference internal nav-link">Boundary conditions</a>
  - <a href="#custom-boundary-conditions"
    class="reference internal nav-link">Custom boundary conditions</a>
  - <a href="#initial-profiles" class="reference internal nav-link">Initial
    profiles</a>
  - <a href="#output-variables" class="reference internal nav-link">Output
    variables</a>
  - <a href="#variable-attributes"
    class="reference internal nav-link">Variable attributes</a>
- <a href="#reduced-mhd" class="reference internal nav-link">Reduced
  MHD</a>
- <a href="#logging-output" class="reference internal nav-link">Logging
  output</a>
  - <a href="#controlling-logging-level"
    class="reference internal nav-link">Controlling logging level</a>
- <a href="#updating-physics-models-from-v3-to-v4"
  class="reference internal nav-link">Updating Physics Models from v3 to
  v4</a>
- <a href="#more-examples" class="reference internal nav-link">More
  examples</a>
  - <a href="#advect1d" class="reference internal nav-link">advect1d</a>
  - <a href="#drift-instability"
    class="reference internal nav-link">drift-instability</a>
  - <a href="#interchange-instability"
    class="reference internal nav-link">interchange-instability</a>
  - <a href="#sod-shock" class="reference internal nav-link">sod-shock</a>

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
