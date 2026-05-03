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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/bout_options.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/bout_options.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/bout_options.rst"
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

# BOUT++ options

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#bout-inp-input-file"
  class="reference internal nav-link">BOUT.inp input file</a>
  - <a href="#boolean-expressions"
    class="reference internal nav-link">Boolean expressions</a>
  - <a href="#special-symbols-in-option-names"
    class="reference internal nav-link">Special symbols in Option names</a>
  - <a href="#printing-options" class="reference internal nav-link">Printing
    Options</a>
- <a href="#command-line-options"
  class="reference internal nav-link">Command line options</a>
- <a href="#general-options" class="reference internal nav-link">General
  options</a>
  - <a href="#grids" class="reference internal nav-link">Grids</a>
- <a href="#communications"
  class="reference internal nav-link">Communications</a>
- <a href="#differencing-methods"
  class="reference internal nav-link">Differencing methods</a>
- <a href="#model-specific-options"
  class="reference internal nav-link">Model-specific options</a>
- <a href="#input-and-output" class="reference internal nav-link">Input
  and Output</a>
- <a href="#implementation"
  class="reference internal nav-link">Implementation</a>
  - <a href="#documentation"
    class="reference internal nav-link">Documentation</a>
  - <a href="#creating-options" class="reference internal nav-link">Creating
    Options</a>
  - <a href="#setting-option-attributes"
    class="reference internal nav-link">Setting option attributes</a>
  - <a href="#overriding-library-defaults"
    class="reference internal nav-link">Overriding library defaults</a>
  - <a href="#older-interface" class="reference internal nav-link">Older
    interface</a>
- <a href="#reading-options" class="reference internal nav-link">Reading
  options</a>
- <a href="#reading-and-writing-to-binary-formats"
  class="reference internal nav-link">Reading and writing to binary
  formats</a>
  - <a href="#time-dependence" class="reference internal nav-link">Time
    dependence</a>
- <a href="#fft" class="reference internal nav-link">FFT</a>
- <a href="#types-for-multi-valued-options"
  class="reference internal nav-link">Types for multi-valued options</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="bout-options" class="section">

<span id="sec-options"></span>

# BOUT++ options<a href="#bout-options" class="headerlink"
title="Permalink to this heading">#</a>

The inputs to BOUT++ are a text file containing options, command-line
options, and for complex grids a binary grid file in NetCDF format.
Generating input grids for tokamaks is described in
<a href="input_grids.html#sec-gridgen" class="reference internal"><span
class="std std-ref">Generating input grids</span></a>. The grid file
describes the size and topology of the X-Y domain, metric tensor
components and usually some initial profiles. The option file specifies
the size of the domain in the symmetric direction (Z), and controls how
the equations are evolved e.g. differencing schemes to use, and boundary
conditions. In most situations, the grid file will be used in many
different simulations, but the options may be changed frequently.

All options used in a simulation are saved to a
<span class="pre">`BOUT.settings`</span> file. This includes values
which are not explicitly set in <span class="pre">`BOUT.inp`</span>.

<div id="bout-inp-input-file" class="section">

## BOUT.inp input file<a href="#bout-inp-input-file" class="headerlink"
title="Permalink to this heading">#</a>

The text input file <span class="pre">`BOUT.inp`</span> is always in a
subdirectory called <span class="pre">`data`</span> for all examples.
The files include comments (starting with either
<span class="pre">`;`</span> or <span class="pre">`#`</span>) and should
be fairly self-explanatory. The format is the same as a windows INI
file, consisting of
<span class="pre">`name`</span>` `<span class="pre">`=`</span>` `<span class="pre">`value`</span>
pairs. Any type which can be read from a stream using the
<span class="pre">`>>`</span> operator can be stored in an option (see
later for the implementation details). Supported value types include:

- Integers

- Real values

- Booleans

- Strings

Options are also divided into sections, which start with the section
name in square brackets.

<div class="highlight-cfg notranslate">

<div class="highlight">

    [section1]
    something = 132         # an integer
    another = 5.131         # a real value
    工作的 = true            # a boolean
    इनपुट = "some text"      # a string

</div>

</div>

Option names can contain almost any character except ’=’ and ’:’,
including unicode. If they start with a number or
<span class="pre">`.`</span>, contain arithmetic/boolean operator
symbols (<span class="pre">`+-*/^&|!<>`</span>), brackets
(<span class="pre">`(){}[]`</span>), equality
(<span class="pre">`=`</span>), whitespace or comma
<span class="pre">`,`</span>, then these will need to be escaped in
expressions. See below for how this is done.

Subsections can also be used, separated by colons ’:’, e.g.

<div class="highlight-cfg notranslate">

<div class="highlight">

    [section:subsection]

</div>

</div>

Numerical quantities can be plain numbers or expressions:

<div class="highlight-cfg notranslate">

<div class="highlight">

    short_pi = 3.145
    foo = 6 * 9

</div>

</div>

Variables can even reference other variables:

<div class="highlight-cfg notranslate">

<div class="highlight">

    pressure = temperature * density
    temperature = 12
    density = 3

</div>

</div>

Note that variables can be used before their definition; all variables
are first read, and then processed afterwards on demand. The value
<span class="pre">`pi`</span> is already defined, as is
<span class="pre">`π`</span>, and can be used in expressions.

Uses for expressions include initialising variables
<a href="variable_init.html#sec-expressions"
class="reference internal"><span
class="std std-ref">Expressions</span></a> and input sources, defining
grids
<a href="input_grids.html#sec-gridgen" class="reference internal"><span
class="std std-ref">Generating input grids</span></a> and MMS
convergence tests
<a href="testing.html#sec-mms" class="reference internal"><span
class="std std-ref">Method of Manufactured Solutions</span></a>.

Expressions can include addition (<span class="pre">`+`</span>),
subtraction (<span class="pre">`-`</span>), multiplication
(<span class="pre">`*`</span>), division (<span class="pre">`/`</span>)
and exponentiation (<span class="pre">`^`</span>) operators, with the
usual precedence rules. In addition to <span class="pre">`π`</span>,
expressions can use predefined variables <span class="pre">`x`</span>,
<span class="pre">`y`</span>, <span class="pre">`z`</span> and
<span class="pre">`t`</span> to refer to the spatial and time
coordinates (for definitions of the values these variables take see
<a href="variable_init.html#sec-expressions"
class="reference internal"><span
class="std std-ref">Expressions</span></a>).

<div class="admonition note">

Note

The variables <span class="pre">`x`</span>,
<span class="pre">`y`</span>, <span class="pre">`z`</span> should only
be defined when reading a 3D field; <span class="pre">`t`</span> should
only be defined when reading a time-dependent value. Earlier BOUT++
versions (v5.1.0 and earler) defined all of these to be 0 by default
e.g. when reading scalar inputs.

</div>

A number of functions are defined, listed in table
<a href="variable_init.html#tab-initexprfunc"
class="reference internal"><span class="std std-numref">Table
2</span></a>. One slightly unusual feature (borrowed from
<a href="https://julialang.org/" class="reference external">Julia</a>)
is that if a number comes before a symbol or an opening bracket
(<span class="pre">`(`</span>) then a multiplication is assumed:
<span class="pre">`2x+3y^2`</span> is the same as
<span class="pre">`2*x`</span>` `<span class="pre">`+`</span>` `<span class="pre">`3*y^2`</span>,
which with the usual precedence rules is the same as
<span class="pre">`(2*x)`</span>` `<span class="pre">`+`</span>` `<span class="pre">`(3*(y^2))`</span>.

Expressions can span more than one line, which can make long expressions
easier to read:

<div class="highlight-cfg notranslate">

<div class="highlight">

    pressure = temperature * ( density0 +
                               density1 )
    temperature = 12
    density0 = 3
    density1 = 1

</div>

</div>

The convention is the same as in
<a href="https://www.python.org/" class="reference external">Python</a>:
If brackets are not balanced (closed) then the expression continues on
the next line.

All expressions are calculated in floating point and then converted to
an integer (or boolean) if needed when read inside BOUT++. The
conversion is done by rounding to the nearest integer, but throws an
error if the floating point value is not within
<span class="math notranslate nohighlight">\\1e-3\\</span> of an
integer. This is to minimise unexpected behaviour. If you want to round
any result to an integer, use the <span class="pre">`round`</span>
function:

<div class="highlight-cfg notranslate">

<div class="highlight">

    bad_integer = 256.4
    ok_integer = round(256.4)

</div>

</div>

Note that it is still possible to read
<span class="pre">`bad_integer`</span> as a real number, since the type
is determined by how it is used.

Have a look through the examples to see how the options are used.

<div id="boolean-expressions" class="section">

### Boolean expressions<a href="#boolean-expressions" class="headerlink"
title="Permalink to this heading">#</a>

Boolean values must be “true”, “false”, “True”, “False”, “1” or “0”. All
lowercase (“true”/”false”) is preferred, but the uppercase versions are
allowed to support Python string conversions. Booleans can be combined
into expressions using binary operators <span class="pre">`&`</span>
(logical AND), <span class="pre">`|`</span> (logical OR), and unary
operator (logical NOT). For example “true & false” evaluates to
<span class="pre">`false`</span>; “!false” evaluates to
<span class="pre">`true`</span>. Like real values and integers, boolean
expressions can refer to other variables:

<div class="highlight-cfg notranslate">

<div class="highlight">

    switch = true
    other_switch = !switch

</div>

</div>

Boolean expressions can be formed by comparing real values using
<span class="pre">`>`</span> and <span class="pre">`<`</span> comparison
operators:

<div class="highlight-cfg notranslate">

<div class="highlight">

    value = 3.2
    is_true = value > 3
    is_false = value < 2

</div>

</div>

<div class="admonition note">

Note

Previous BOUT++ versions (v5.1.0 and earlier) were case insensitive when
reading boolean values, so would read “True” or “yEs” as
<span class="pre">`true`</span>, and “False” or “No” as
<span class="pre">`false`</span>. These earlier versions did not allow
boolean expressions.

</div>

Internally, booleans are evaluated as real values, with
<span class="pre">`true`</span> being 1 and
<span class="pre">`false`</span> being 0. Logical operators
(<span class="pre">`&`</span>, <span class="pre">`|`</span>, ) check
that their left and right arguments are either close to 0 or close to 1
(like integers, “close to” is within 1e-3).

</div>

<div id="special-symbols-in-option-names" class="section">

### Special symbols in Option names<a href="#special-symbols-in-option-names" class="headerlink"
title="Permalink to this heading">#</a>

If option names start with numbers or <span class="pre">`.`</span> or
contain symbols such as <span class="pre">`+`</span> and
<span class="pre">`-`</span> then these symbols need to be escaped in
expressions or they will be treated as arithmetic operators like
addition or subtraction. To escape a single character
<span class="pre">`\`</span> (backslash) can be used, for example
<span class="pre">`plasma\-density`</span>` `<span class="pre">`*`</span>` `<span class="pre">`10`</span>
would read the option <span class="pre">`plasma-density`</span> and
multiply it by 10 e.g

<div class="highlight-cfg notranslate">

<div class="highlight">

    plasma-density = 1e19
    2ndvalue = 10
    value = plasma\-density * \2ndvalue

</div>

</div>

To escape multiple characters, \` (backquote) can be used:

<div class="highlight-cfg notranslate">

<div class="highlight">

    plasma-density = 1e19
    2ndvalue = 10
    value = `plasma-density` * `2ndvalue`

</div>

</div>

The character <span class="pre">`:`</span> cannot be part of an option
or section name, and cannot be escaped, as it is always used to separate
sections.

</div>

<div id="printing-options" class="section">

### Printing Options<a href="#printing-options" class="headerlink"
title="Permalink to this heading">#</a>

<a href="../_breathe_autogen/file/options_8hxx.html#_CPPv47Options"
class="reference internal" title="Options"><span class="pre"><code
class="sourceCode cpp">Options</code></span></a> have an
<span class="pre">`fmt::formatter`</span> which means they can be
printed directly with <a
href="../_breathe_autogen/file/output_8hxx.html#_CPPv4N6Output5writeERKNSt6stringE"
class="reference internal" title="Output::write"><span class="pre"><code
class="sourceCode cpp">Output<span class="op">::</span>write<span class="op">()</span></code></span></a>,
or converted to a <span class="pre">`std::string`</span> with
<span class="pre">`fmt::format`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    // Print a value or section
    output.write("{}", options["section"]);

    // Convert to a string
    std::string = fmt::format("{}", options["section"]);

</div>

</div>

The format can be controlled through the following four format codes:

- <span class="pre">`d`</span>: includes the
  <span class="pre">`doc`</span> and/or <span class="pre">`type`</span>
  attribute, if they are present

- <span class="pre">`i`</span>: format the section name(s) inline,
  rather than as a <span class="pre">`[section]`</span> header

- <span class="pre">`k`</span>: only include the key, and not the value

- <span class="pre">`s`</span>: include the
  <span class="pre">`source`</span> attribute, if it’s present

- <span class="pre">`u`</span>: if the option is unused add a comment,
  including whether it is conditionally used

Here are some examples of formatting the same
<a href="../_breathe_autogen/file/options_8hxx.html#_CPPv47Options"
class="reference internal" title="Options"><span class="pre"><code
class="sourceCode cpp">Options</code></span></a> object using different
combinations of the format codes:

<div class="highlight-cpp notranslate">

<div class="highlight">

    // Default format with no format codes
    output.write("{}", options);

    // Output is:

    // [section1]
    // value1 = 42
    // value2 = hello
    //
    // [section2]
    // value5 = 3
    //
    // [section2:subsection1]
    // value3 = true
    // value4 = 3.2

    // Include the 'doc' and 'type' attributes
    output.write("{:d}", options);

    // [section1]
    // value1 = 42
    // value2 = hello             # doc: This says hello
    //
    // [section2]
    // value5 = 3
    //
    // [section2:subsection1]
    // value3 = true              # type: bool, doc: This is a bool
    // value4 = 3.2

    // Only keys, inline sections, and 'doc', 'type', and 'source' attributes.
    // Note that order doesn't matter!
    output.write("{:kids}", options);

    // section1:value1
    // section1:value2            # doc: This says hello
    // section2:value5
    // section2:subsection1:value3                # type: bool, doc: This is a bool, source: a test
    // section2:subsection1:value4

</div>

</div>

</div>

</div>

<div id="command-line-options" class="section">

## Command line options<a href="#command-line-options" class="headerlink"
title="Permalink to this heading">#</a>

Command-line switches are:

<table class="table">
<thead>
<tr class="row-odd">
<th class="head"><p>Switch</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p>-h, –help</p></td>
<td><p>Prints a help message and quits</p></td>
</tr>
<tr class="row-odd">
<td><p>-v, –verbose</p></td>
<td><p>Outputs more messages to BOUT.log files</p></td>
</tr>
<tr class="row-even">
<td><p>-q, –quiet</p></td>
<td><p>Outputs fewer messages to log files</p></td>
</tr>
<tr class="row-odd">
<td><p>-d &lt;directory&gt;</p></td>
<td><p>Look in &lt;directory&gt; for input/output files (default
“data”)</p></td>
</tr>
<tr class="row-even">
<td><p>-f &lt;file&gt;</p></td>
<td><p>Use OPTIONS given in &lt;file&gt;</p></td>
</tr>
<tr class="row-odd">
<td><p>-o &lt;file&gt;</p></td>
<td><p>Save used OPTIONS given to &lt;file&gt; (default
BOUT.settings)</p></td>
</tr>
</tbody>
</table>

In addition all options in the BOUT.inp file can be set on the command
line, and will override those set in BOUT.inp. The most commonly used
are “restart” and “append”, described in
<a href="running_bout.html#sec-running" class="reference internal"><span
class="std std-ref">Running BOUT++</span></a>. If values are not given
for command-line arguments, then the value is set to
<span class="pre">`true`</span> , so putting
<span class="pre">`restart`</span> is equivalent to
<span class="pre">`restart=true`</span> .

Values can be specified on the command line for other settings, such as
the fraction of a torus to simulate (ZPERIOD):

<div class="highlight-bash notranslate">

<div class="highlight">

    ./command zperiod=10

</div>

</div>

Remember **no** spaces around the ’=’ sign. Like the BOUT.inp file,
setting names are not case sensitive.

Sections are separated by colons ’:’, so to set the solver type
(<a href="time_integration.html#sec-timeoptions"
class="reference internal"><span class="std std-ref">Options</span></a>)
you can either put this in BOUT.inp:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [solver]
    type = rk4

</div>

</div>

or put <span class="pre">`solver:type=rk4`</span> on the command line.
This capability is used in many test suite cases to change the
parameters for each run.

</div>

<div id="general-options" class="section">

<span id="sec-options-general"></span>

## General options<a href="#general-options" class="headerlink"
title="Permalink to this heading">#</a>

At the top of the BOUT.inp file (before any section headers), options
which affect the core code are listed. These are common to all physics
models, and the most useful of them are:

<div class="highlight-cfg notranslate">

<div class="highlight">

    nout = 100       # number of time-points output
    timestep = 1.0   # time between outputs

</div>

</div>

which set the number of outputs, and the time step between them. Note
that this has nothing to do with the internal timestep used to advance
the equations, which is adjusted automatically. What time-step to use
depends on many factors, but for
high-<span class="math notranslate nohighlight">\\\beta\\</span> reduced
MHD ELM simulations reasonable choices are
<span class="pre">`1.0`</span> for the first part of a run (to handle
initial transients), then around <span class="pre">`10.0`</span> for the
linear phase. Once non-linear effects become important, you will have to
reduce the timestep to around <span class="pre">`0.1`</span>.

Most large clusters or supercomputers have a limit on how long a job can
run for called “wall time”, because it’s the time taken according to a
clock on the wall, as opposed to the CPU time actually used. If this is
the case, you can use the option

<div class="highlight-cfg notranslate">

<div class="highlight">

    wall_limit = 10 # wall clock limit (in hours)

</div>

</div>

BOUT++ will then try to quit cleanly before this time runs out. Setting
a negative value (default is -1) means no limit.

Often it’s useful to be able to restart a simulation from a chosen
point, either to reproduce a previous run, or to modify the settings and
re-run. A restart file is output every timestep, but this is overwritten
each time, and so the simulation can only be continued from the end of
the last simulation. Whilst it is possible to create a restart file from
the output data afterwards, it’s much easier if you have the restart
files. Using the option

<div class="highlight-cfg notranslate">

<div class="highlight">

    archive = 20

</div>

</div>

saves a copy of the restart files every 20 timesteps, which can then be
used as a starting point.

<div id="grids" class="section">

<span id="sec-grid-options"></span>

### Grids<a href="#grids" class="headerlink"
title="Permalink to this heading">#</a>

You can set the size of the computational grid in the
<span class="pre">`mesh`</span> section of the input file (see
<a href="input_grids.html#sec-gridgen" class="reference internal"><span
class="std std-ref">Generating input grids</span></a> for more
information):

<div class="highlight-cfg notranslate">

<div class="highlight">

    [mesh]
    nx = 20  # Number of points in X
    ny = 16  # Number of points in Y
    nz = 32  # Number of points in Z

</div>

</div>

Due to historical reasons, <span class="pre">`nx`</span> is defined
differently to <span class="pre">`ny`</span> and
<span class="pre">`nz`</span>:

- <span class="pre">`nx`</span> is the number of points in X
  **including** the boundaries

- <span class="pre">`ny`</span> and <span class="pre">`nz`</span> are
  the number of points in Y and Z **not including** the boundaries

The default number of boundary points in X is 2, so taking into account
the boundary at each end of the domain, <span class="pre">`nx`</span>
usually means “the number of interior grid points in X plus four”. In
the example above, both X and Y have 16 interior grid points.

It is recommended, but not necessary, that this be
<span class="math notranslate nohighlight">\\\texttt{nz} = 2^n\\</span>,
that is
<span class="math notranslate nohighlight">\\1,2,4,8,\ldots\\</span>.
This is because FFTs are usually slightly faster with power-of-two
length arrays, and FFTs are used quite frequently in many models.

<div class="admonition note">

Note

In previous versions of BOUT++, <span class="pre">`nz`</span> was
constrained to be a power-of-two, and had to be specified as a
power-of-two plus one (i.e. a number of the form
<span class="math notranslate nohighlight">\\2^n + 1\\</span> like
<span class="math notranslate nohighlight">\\2, 3, 5, 9,\ldots\\</span>)
in order to account for an additional, unused, point in Z. Both of these
conditions were relaxed in BOUT++ 4.0. If you use an input file from a
previous version, check that this superfluous point is not included in
<span class="pre">`nz`</span>.

</div>

Since the Z dimension is periodic, the domain size is specified as
multiples or fractions of
<span class="math notranslate nohighlight">\\2\pi\\</span>. To specify a
fraction of <span class="math notranslate nohighlight">\\2\pi\\</span>,
use

<div class="highlight-cfg notranslate">

<div class="highlight">

    zperiod = 10

</div>

</div>

This specifies a Z range from
<span class="math notranslate nohighlight">\\0\\</span> to
<span class="math notranslate nohighlight">\\2\pi /
{\texttt{zperiod}}\\</span>, and is useful for simulation of tokamaks to
make sure that the domain is an integer fraction of a torus. If instead
you want to specify the Z range directly (for example if Z is not an
angle), there are the options

<div class="highlight-cfg notranslate">

<div class="highlight">

    ZMIN = 0.0
    ZMAX = 0.1

</div>

</div>

which specify the range in multiples of
<span class="math notranslate nohighlight">\\2\pi\\</span>.

In BOUT++, grids can be split between processors in both X and Y
directions. By default BOUT++ automatically divides the grid in both X
and Y, finding the decomposition with domains closest to square, whilst
satisfying constraints. These constraints are:

- Every processor must have the same size and shape domain

- Branch cuts, mostly at X-points, must be on processor boundaries. This
  is because the connection between grid points is modified in BOUT++ by
  changing which processors communicate.

To specify a splitting manually, the number of processors in the X
direction can be specified:

<div class="highlight-cfg notranslate">

<div class="highlight">

    NXPE = 1  # Set number of X processors

</div>

</div>

Alternatively, the number in the Y direction can be specified (if both
are given, <span class="pre">`NXPE`</span> takes precedence and
<span class="pre">`NYPE`</span> is ignored):

<div class="highlight-cfg notranslate">

<div class="highlight">

    NYPE = 1  # Set number of Y processors

</div>

</div>

When choosing <span class="pre">`NXPE`</span> or
<span class="pre">`NYPE`</span>, they must also obey some constraints:

- <span class="pre">`NXPE`</span> must be a factor of the number of grid
  points in the x-direction

  - That is,
    <span class="pre">`(nx`</span>` `<span class="pre">`-`</span>` `<span class="pre">`4)`</span>` `<span class="pre">`/`</span>` `<span class="pre">`NXPE`</span>
    must be an integer, assuming the usual two boundary points

- <span class="pre">`NYPE`</span> must be a factor of the number of grid
  points in the y-direction

  - That is,
    <span class="pre">`ny`</span>` `<span class="pre">`/`</span>` `<span class="pre">`NYPE`</span>
    must be an integer

- For more general topologies, the number of points per processor
  <span class="pre">`ny`</span>` `<span class="pre">`/`</span>` `<span class="pre">`NYPE`</span>
  must also be a factor of the number of points in each region. For
  example, in the usual tokamak topologies:

  - in single-null there are two divertor leg and one core regions

  - in double-null there are four divertor leg, one inner core and one
    outer core regions

Please note that here “core” means “core and adjacent SOL”. See
<a href="topology.html#sec-bout-topology"
class="reference internal"><span class="std std-ref">BOUT++
Topology</span></a> for a more detailed explanation of these regions.

When BOUT++ automatically chooses <span class="pre">`NXPE`</span> and
<span class="pre">`NYPE`</span> it finds all valid pairs which give
<span class="pre">`total`</span>` `<span class="pre">`number`</span>` `<span class="pre">`of`</span>` `<span class="pre">`processors`</span>` `<span class="pre">`==`</span>` `<span class="pre">`NPES`</span>` `<span class="pre">`=`</span>` `<span class="pre">`NXPE`</span>` `<span class="pre">`*`</span>` `<span class="pre">`NYPE`</span>
and also satisfy the constraints above. It then chooses the pair that
makes the grid on each processor as close to square as possible
(technically it chooses the pair that minimises
<span class="pre">`abs(sqrt(NPES`</span>` `<span class="pre">`*`</span>` `<span class="pre">`(nx`</span>` `<span class="pre">`-`</span>` `<span class="pre">`4)`</span>` `<span class="pre">`/`</span>` `<span class="pre">`ny)`</span>` `<span class="pre">`-`</span>` `<span class="pre">`NXPE)`</span>).

If you need to specify complex input values, e.g. numerical values from
experiment, you may want to use a grid file. The grid file to use is
specified relative to the root directory where the simulation is run
(i.e. running
“<span class="pre">`ls`</span>` `<span class="pre">`./data/BOUT.inp`</span>”
gives the options file). You can use the global option
<span class="pre">`grid`</span>, or
<span class="pre">`mesh:file`</span>:

<div class="highlight-cfg notranslate">

<div class="highlight">

    grid = "data/cbm18_8_y064_x260.nc"

    # Alternatively:
    [mesh]
    file = "data/cbm18_8_y064_x260.nc"

</div>

</div>

</div>

</div>

<div id="communications" class="section">

## Communications<a href="#communications" class="headerlink"
title="Permalink to this heading">#</a>

The communication system has a section
<span class="pre">`[comms]`</span>, with a true/false option
<span class="pre">`async`</span>. This determines whether asynchronous
MPI sends are used; which method is faster varies (though not by much)
with machine and problem.

</div>

<div id="differencing-methods" class="section">

<span id="sec-diffmethodoptions"></span>

## Differencing methods<a href="#differencing-methods" class="headerlink"
title="Permalink to this heading">#</a>

Differencing methods are specified in the section
(<span class="pre">`[mesh:ddx]`</span>,
<span class="pre">`[mesh:ddy]`</span>,
<span class="pre">`[mesh:ddz]`</span> and
<span class="pre">`[mesh:diff]`</span>), one for each dimension. The
<span class="pre">`[mesh:diff]`</span> section is only used if the
section for the dimension does not contain an option for the
differencing method. Note that <span class="pre">`[mesh]`</span> is the
name of the section passed to the mesh constructor, which is most often
<span class="pre">`mesh`</span> - but could have another name, e.g. if
multiple meshes are used.

- <span class="pre">`first`</span>, the method used for first
  derivatives

- <span class="pre">`second`</span>, method for second derivatives

- <span class="pre">`fourth`</span>, method for fourth derivatives

- <span class="pre">`upwind`</span>, method for upwinding terms

- <span class="pre">`flux`</span>, for conservation law terms

The methods which can be specified include U1, U4, C2, C4, W2, W3, FFT
Apart from FFT, the first letter gives the type of method (U = upwind, C
= central, W = WENO), and the number gives the order.

The staggered derivatives can be specified as
<span class="pre">`FirstStag`</span> or if the value is not set, then
<span class="pre">`First`</span> is checked. Note that for the staggered
quantities, if the staggered quantity in a dimension is not set, first
the staggered quantity in the <span class="pre">`[mesh:diff]`</span>
section is checked. This is useful, as the staggered quantities are more
restricted in the available choices than the non-staggered
differenciating operators.

</div>

<div id="model-specific-options" class="section">

## Model-specific options<a href="#model-specific-options" class="headerlink"
title="Permalink to this heading">#</a>

The options which affect a specific physics model vary, since they are
defined in the physics module itself (see
<a href="physics_models.html#sec-inputopts"
class="reference internal"><span class="std std-ref">Input
options</span></a>). They should have a separate section, for example
the high-<span class="math notranslate nohighlight">\\\beta\\</span>
reduced MHD code uses options in a section called
<span class="pre">`[highbeta]`</span>.

There are three places to look for these options: the BOUT.inp file; the
physics model C++ code, and the output logs. The physics module author
should ideally have an example input file, with commented options
explaining what they do; alternately they may have put comments in the
C++ code for the module. Another way is to look at the output logs: when
BOUT++ is run, (nearly) all options used are printed out with their
default values. This won’t provide much explanation of what they do, but
may be useful anyway. See <a href="output_and_post.html#sec-output"
class="reference internal"><span
class="std std-ref">Post-processing</span></a> for more details.

</div>

<div id="input-and-output" class="section">

<span id="sec-iooptions"></span>

## Input and Output<a href="#input-and-output" class="headerlink"
title="Permalink to this heading">#</a>

The output (dump) files with time-history are controlled by settings in
a section called <span class="pre">`"output"`</span>. Restart files
contain a single time-slice, and are controlled by a section called
<span class="pre">`"restart"`</span>. The options available are listed
in table <a href="#tab-outputopts" class="reference internal"><span
class="std std-numref">Table 6</span></a>.

<span id="tab-outputopts"></span>

<table id="id1" class="table">
<caption><span class="caption-number">Table 6 </span><span
class="caption-text">Output file options</span><a href="#id1"
class="headerlink" title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Option</p></th>
<th class="head"><p>Description</p></th>
<th class="head"><p>Default value</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">append</code></span></p></td>
<td><p>Append to existing file if true, otherwise overwrite</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">false</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">enabled</code></span></p></td>
<td><p>Writing is enabled</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">true</code></span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">flush_frequency</code></span></p></td>
<td><p>How many output timesteps between writing output to disk (NetCDF
only)</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">1</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">prefix</code></span></p></td>
<td><p>File name prefix</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">"BOUT.dmp"</code></span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">path</code></span></p></td>
<td><p>Directory to write the file into</p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">datadir</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">type</code></span></p></td>
<td><p>File type, either <span class="pre"><code
class="docutils literal notranslate">"netcdf"</code></span> or <span
class="pre"><code
class="docutils literal notranslate">"adios"</code></span></p></td>
<td><p><span class="pre"><code
class="docutils literal notranslate">"netcdf"</code></span></p></td>
</tr>
</tbody>
</table>

<div class="line">

  

</div>

- <span class="pre">`enabled`</span> is useful mainly for doing
  performance or scaling tests, where you want to exclude I/O from the
  timings.

- If you find that IO is taking more and more time as your simulation
  goes on, try setting <span class="pre">`flush_frequency`</span> to a
  larger value such as <span class="pre">`10`</span>. This can
  workaround an issue with NetCDF where subsequent writes take longer
  and longer. However, larger values risk losing more data in the event
  of a crash or the simulation being killed early.

</div>

<div id="implementation" class="section">

## Implementation<a href="#implementation" class="headerlink"
title="Permalink to this heading">#</a>

To control the behaviour of BOUT++ a set of options is used, with
options organised into sections which can be nested. To represent this
tree structure there is the
<a href="../_breathe_autogen/file/options_8hxx.html#_CPPv47Options"
class="reference internal" title="Options"><span class="pre"><code
class="sourceCode cpp">Options</code></span></a> class defined in
<span class="pre">`bout++/include/options.hxx`</span>.

To access the options, there is a static function (singleton):

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto& options = Options::root();

</div>

</div>

which returns a reference (type <span class="pre">`Options&`</span>).
Note that without the <span class="pre">`&`</span> the options tree will
be copied, so any changes made will not be retained in the global tree.
Options can be set by assigning, treating options as a map or
dictionary:

<div class="highlight-cpp notranslate">

<div class="highlight">

    options["nout"] = 10;    // Integer
    options["restart"] = true;  // bool

</div>

</div>

Internally these values are stored in a variant type, which supports
commonly used types including strings, integers, real numbers and fields
(2D and 3D). Since strings can be stored, any type can be assigned, so
long as it can be streamed to a string (using
<span class="pre">`<<`</span> operator and a
<span class="pre">`std::stringstream`</span>).

Often it’s useful to see where an option setting has come from e.g. the
name of the options file or “command line”. To specify a source, use the
<span class="pre">`assign`</span> function to assign values:

<div class="highlight-cpp notranslate">

<div class="highlight">

    options["nout"].assign(10, "manual");

</div>

</div>

A value cannot be assigned more than once with different values and the
same source (“manual” in this example). This is to catch a common error
in which a setting is inconsistently specified in an input file. To
force a value to change, overwriting the existing value (if any):

<div class="highlight-cpp notranslate">

<div class="highlight">

    options["nout"].force(20, "manual");

</div>

</div>

Sub-sections are created as they are accessed, so a value in a
sub-section could be set using:

<div class="highlight-cpp notranslate">

<div class="highlight">

    auto& section = options["mysection"];
    section["myswitch"] = true;

</div>

</div>

or just:

<div class="highlight-cpp notranslate">

<div class="highlight">

    options["mysection"]["myswitch"] = true;

</div>

</div>

Names including sections, subsections, etc. can be specified using
<span class="pre">`":"`</span> as a separator, e.g.:

<div class="highlight-cpp notranslate">

<div class="highlight">

    options["mysection:mysubsection:myswitch"] = true;

</div>

</div>

To get options, they can be assigned to a variable:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int nout = options["nout"];

</div>

</div>

If the option is not found then a
<span class="pre">`BoutException`</span> will be thrown. A default value
can be given, which will be used if the option has not been set:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int nout = options["nout"].withDefault(1);

</div>

</div>

If <span class="pre">`options`</span> is not
<span class="pre">`const`</span>, then the given default value will be
cached. If a default value has already been cached for this option, then
the default values must be consistent: A
<span class="pre">`BoutException`</span> is thrown if inconsistent
default values are detected.

The default can also be set from another option. This may be useful if
two or more options should usually be changed together:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoutReal value2 = options["value2"].withDefault(options["value1"]);

</div>

</div>

Note that if the result should be a real number (e.g.
<span class="pre">`BoutReal`</span>) then
<span class="pre">`withDefault`</span> should be given a real. Otherwise
it will convert the number to an integer:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoutReal value = options["value"].withDefault(42);  // Convert to integer

    BoutReal value = options["value"].withDefault(42.0); // ok

    auto value = options["value"].withDefault<BoutReal>(42); // ok

</div>

</div>

It is common for BOUT++ models to read in many settings which have the
same variable name as option setting (e.g. “nout” here). A convenient
macro reads options into an already-defined variable:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int nout;
    OPTION(options, nout, 1);

</div>

</div>

where the first argument is a section, second argument is the variable
whose name will also be used as the option string, and third argument is
the default value.

Every time an option is accessed, a message is written to
<span class="pre">`output_info`</span>. This message includes the value
used and the source of that value. By default this message is printed to
the terminal and saved in the log files, but this can be disabled by
changing the logging level: Add <span class="pre">`-q`</span> to the
command line to reduce logging level. See section
<a href="physics_models.html#sec-logging"
class="reference internal"><span class="std std-ref">Logging
output</span></a> for more details about logging.

The type to be returned can also be specified as a template argument:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoutReal nout = options["nout"].as<BoutReal>();

</div>

</div>

Any type can be used which can be streamed (operator
<span class="pre">`>>`</span>) from a
<span class="pre">`stringstream`</span>. There are special
implementations for <span class="pre">`bool`</span>,
<span class="pre">`int`</span> and <span class="pre">`BoutReal`</span>
which enable use of expressions in the input file. The type can also be
specified to <span class="pre">`withDefault`</span>, or will be inferred
from the argument:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BoutReal nout = options["nout"].withDefault<BoutReal>(1);

</div>

</div>

<div id="documentation" class="section">

### Documentation<a href="#documentation" class="headerlink"
title="Permalink to this heading">#</a>

Options can be given a <span class="pre">`doc`</span> attribute
describing what they do. This documentation will then be written to the
<span class="pre">`BOUT.settings`</span> file at the end of a run:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Te0 = options["Te0"].doc("Temperature in eV").withDefault(30.0);

</div>

</div>

The <span class="pre">`.doc()`</span> function returns a reference
<span class="pre">`Options&`</span> so can be chained with
<span class="pre">`withDefault`</span> or <span class="pre">`as`</span>
functions, or as part of an assignment:

<div class="highlight-cpp notranslate">

<div class="highlight">

    options["value"].doc("Useful setting info") = 42;

</div>

</div>

This string is stored in the attributes of the option:

<div class="highlight-cpp notranslate">

<div class="highlight">

    std::string docstring = options["value"].attributes["doc"];

</div>

</div>

</div>

<div id="creating-options" class="section">

### Creating Options<a href="#creating-options" class="headerlink"
title="Permalink to this heading">#</a>

Options and subsections can be created by setting values, creating
subsections as needed:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options options;
    options["value1"] = 42;
    options["subsection1"]["value2"] = "some string";
    options["subsection1"]["value3"] = 3.1415;

</div>

</div>

or using an initializer list:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options options {{"value1", 42},
                     {"subsection1", {{"value2", "some string"},
                                      {"value3", 3.1415}}}};

</div>

</div>

These are equivalent, but the initializer list method makes the tree
structure clearer. Note that the list can contain many of the types
which <span class="pre">`Options`</span> can hold, including
<span class="pre">`Field2D`</span> and
<span class="pre">`Field3D`</span> objects.

</div>

<div id="setting-option-attributes" class="section">

### Setting option attributes<a href="#setting-option-attributes" class="headerlink"
title="Permalink to this heading">#</a>

Options can have attributes attached to them, that can be
<span class="pre">`bool`</span>, <span class="pre">`int`</span>,
<span class="pre">`BoutReal`</span> or
<span class="pre">`std::string`</span> type. These are stored in an
<span class="pre">`attributes`</span> map that can be assigned to:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options options;
    options["value"].attributes["property"] = "something";

</div>

</div>

An arbitrary number of attributes can be attached to an option. If
assigning multiple attributes, an
<span class="pre">`initializer_list`</span> can be more readable:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options options;
    options["value"].setAttributes({
        {"units", "m/s"},
        {"conversion", 10.2},
        {"long_name", "important value"}
      });

</div>

</div>

</div>

<div id="overriding-library-defaults" class="section">

### Overriding library defaults<a href="#overriding-library-defaults" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ sets defaults for options controlling the mesh, etc. A physics
model (or other user code) can override these defaults by using the
convenience macro BOUT_OVERRIDE_DEFAULT_OPTION, for example if you want
to change the default value of
<span class="pre">`mesh::staggergrids`</span> from false to true, put
(outside any class/function body):

<div class="highlight-cpp notranslate">

<div class="highlight">

    BOUT_OVERRIDE_DEFAULT_OPTION("mesh:staggergrids", true);

</div>

</div>

</div>

<div id="older-interface" class="section">

### Older interface<a href="#older-interface" class="headerlink"
title="Permalink to this heading">#</a>

Some code in BOUT++ currently uses an older interface to
<span class="pre">`Options`</span> which uses pointers rather than
references. Both interfaces are currently supported, but use of the
newer interface above is encouraged.

To access the options, there is a static function (singleton):

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options *options = Options::getRoot();

</div>

</div>

which gives the top-level (root) options class. Setting options is done
using the <span class="pre">`set()`</span> methods which are currently
defined for <span class="pre">`int`</span>,
<span class="pre">`BoutReal`</span>, <span class="pre">`bool`</span> and
<span class="pre">`string`</span> . For example:

<div class="highlight-cpp notranslate">

<div class="highlight">

    options->set("nout", 10);      // Set an integer
    options->set("restart", true); // A bool

</div>

</div>

Often it’s useful to see where an option setting has come from e.g. the
name of the options file or “command line”. To specify a source, pass it
as a third argument:

<div class="highlight-cpp notranslate">

<div class="highlight">

    options->set("nout", 10, "manual");

</div>

</div>

To create a section, just use <span class="pre">`getSection`</span> : if
it doesn’t exist it will be created:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options *section = options->getSection("mysection");
    section->set("myswitch", true);

</div>

</div>

To get options, use the <span class="pre">`get()`</span> method which
take the name of the option, the variable to set, and the default value:

<div class="highlight-cpp notranslate">

<div class="highlight">

    int nout;
    options->get("nout", nout, 1);

</div>

</div>

Internally,
<a href="../_breathe_autogen/file/options_8hxx.html#_CPPv47Options"
class="reference internal" title="Options"><span class="pre"><code
class="sourceCode cpp">Options</code></span></a> converts all types to
strings and does type conversion when needed, so the following code
would work:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options *options = Options::getRoot();
    options->set("test", "123");
    int val;
    options->get("test", val, 1);

</div>

</div>

This is because often the type of the option is not known at the time
when it’s set, but only when it’s requested.

</div>

</div>

<div id="reading-options" class="section">

## Reading options<a href="#reading-options" class="headerlink"
title="Permalink to this heading">#</a>

To allow different input file formats, each file parser implements the
<a
href="../_breathe_autogen/file/optionparser_8hxx.html#_CPPv412OptionParser"
class="reference internal" title="OptionParser"><span class="pre"><code
class="sourceCode cpp">OptionParser</code></span></a> interface defined
in <span class="pre">`bout++/src/sys/options/optionparser.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class OptionParser {
     public:
      virtual void read(Options *options, const string &filename) = 0;
     private:
    };

</div>

</div>

and so just needs to implement a single function which reads a given
file name and inserts the options into the given
<a href="../_breathe_autogen/file/options_8hxx.html#_CPPv47Options"
class="reference internal" title="Options"><span class="pre"><code
class="sourceCode cpp">Options</code></span></a> object.

To use these parsers and read in a file, there is the <a
href="../_breathe_autogen/file/optionsreader_8hxx.html#_CPPv413OptionsReader"
class="reference internal" title="OptionsReader"><span class="pre"><code
class="sourceCode cpp">OptionsReader</code></span></a> class defined in
<span class="pre">`bout++/include/optionsreader.hxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    class OptionsReader {
     public:
     void read(Options *options, const char *file, ...);
     void parseCommandLine(Options *options, int argc, char **argv);
    };

</div>

</div>

This is a singleton object which is accessed using:

<div class="highlight-cpp notranslate">

<div class="highlight">

    OptionsReader *reader = OptionsReader::getInstance();

</div>

</div>

so to read a file <span class="pre">`BOUT.inp`</span> in a directory
given in a variable <span class="pre">`data_dir`</span> the following
code is used in <span class="pre">`bout++.cxx`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options *options = Options::getRoot();
    OptionsReader *reader = OptionsReader::getInstance();
    reader->read(options, "%s/BOUT.inp", data_dir);

</div>

</div>

To parse command line arguments as options, the <a
href="../_breathe_autogen/file/optionsreader_8hxx.html#_CPPv413OptionsReader"
class="reference internal" title="OptionsReader"><span class="pre"><code
class="sourceCode cpp">OptionsReader</code></span></a> class has a
method:

<div class="highlight-cpp notranslate">

<div class="highlight">

    reader->parseCommandLine(options, argc, argv);

</div>

</div>

This is currently quite rudimentary and needs improving.

</div>

<div id="reading-and-writing-to-binary-formats" class="section">

<span id="sec-options-netcdf"></span>

## Reading and writing to binary formats<a href="#reading-and-writing-to-binary-formats" class="headerlink"
title="Permalink to this heading">#</a>

The <a
href="../_breathe_autogen/file/options__io_8hxx.html#_CPPv4N4bout9OptionsIOE"
class="reference internal" title="bout::OptionsIO"><span
class="pre"><code
class="sourceCode cpp">bout<span class="op">::</span>OptionsIO</code></span></a>
class provides an interface to read and write options to binary files.
Examples are in integrated test
<span class="pre">`tests/integrated/test-options-netcdf/`</span>

To write the current
<a href="../_breathe_autogen/file/options_8hxx.html#_CPPv47Options"
class="reference internal" title="Options"><span class="pre"><code
class="sourceCode cpp">Options</code></span></a> tree (e.g. from
<span class="pre">`BOUT.inp`</span>) to a NetCDF file:

<div class="highlight-cpp notranslate">

<div class="highlight">

    bout::OptionsIO::create("settings.nc")->write(Options::root());

</div>

</div>

and to read it in again:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options data = bout::OptionsIO::create("settings.nc")->read();

</div>

</div>

Fields can also be stored and written:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options fields;
    fields["f2d"] = Field2D(1.0);
    fields["f3d"] = Field3D(2.0);
    bout::OptionsIO::create("fields.nc")->write(fields);

</div>

</div>

This allows the input settings and evolving variables to be combined
into a single tree (see above on joining trees) and written to the
output dump or restart files.

Reading fields is a bit more difficult. Currently 1D data is read as an
<span class="pre">`Array<BoutReal>`</span>, 2D as
<span class="pre">`Matrix<BoutReal>`</span> and 3D as
<span class="pre">`Tensor<BoutReal>`</span>. These can be extracted
directly from the <span class="pre">`Options`</span> tree, or converted
to a Field:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options fields_in = bout::OptionsIO::create("fields.nc")->read();
    Field2D f2d = fields_in["f2d"].as<Field2D>();
    Field3D f3d = fields_in["f3d"].as<Field3D>();

</div>

</div>

Note that by default reading as <span class="pre">`Field2D`</span> or
<span class="pre">`Field3D`</span> will use the global
<span class="pre">`bout::globals::mesh`</span>. To use a different mesh,
or different cell location, pass a field which the result should be
similar to:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D example = ... // Some existing field

    Field3D f3d = fields_in["f3d"].as<Field3D>(example);

</div>

</div>

Meta data like <span class="pre">`Mesh`</span> pointer, will be taken
from <span class="pre">`example`</span>.

Currently converting from <span class="pre">`Matrix`</span> or
<span class="pre">`Tensor`</span> types only works if the data in the
<span class="pre">`Matrix`</span> or <span class="pre">`Tensor`</span>
is the same size as the <span class="pre">`Field`</span>. In the case of
grid files, the fields only needs a part of the global values. Some kind
of mapping from the global index to local index is needed, probably
defined by <span class="pre">`Mesh`</span>. For now it should be
possible to be compatible with the current system, so that all
quantities from the grid file are accessed through Mesh::get.

<div id="time-dependence" class="section">

### Time dependence<a href="#time-dependence" class="headerlink"
title="Permalink to this heading">#</a>

When writing NetCDF files, some variables should have a time dimension
added, and then be added to each time they are written. This has been
implemented using an attribute: If variables in the
<span class="pre">`Options`</span> tree have an attribute
<span class="pre">`"time_dimension"`</span> then that is used as the
name of the time dimension in the output file. This allows multiple time
dimensions e.g. high frequency diagnostics and low frequency outputs, to
exist in the same file. <a
href="../_breathe_autogen/file/options_8hxx.html#_CPPv4I0EN7Options12assignRepeatER7Options1TNSt6stringEbNSt6stringE"
class="reference internal" title="Options::assignRepeat"><span
class="pre"><code
class="sourceCode cpp">Options<span class="op">::</span>assignRepeat<span class="op">()</span></code></span></a>
can be used to automatically set the
<span class="pre">`"time_dimension"`</span> attribute:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Options data;
    data["scalar"] = 1.0;
    // You can set the attribute manually like so:
    data["scalar"].attributes["time_dimension"] = "t";

    // Or use `assignRepeat` to do it automatically:
    data["field"].assignRepeat(Field3D(2.0));

    bout::OptionsIO::create("time.nc")->write(data);

    // Update time-dependent values. This can be done without `force` if the time_dimension
    // attribute is set
    data["scalar"] = 2.0;
    data["field"] = Field3D(3.0);

    // Append data to file
    bout::OptionsIO::create({{"file", "time.nc"}, {"append", true}})->write(data);

</div>

</div>

<div class="admonition note">

Note

By default, <a
href="../_breathe_autogen/file/options__io_8hxx.html#_CPPv4N4bout9OptionsIO5writeERK7Options"
class="reference internal" title="bout::OptionsIO::write"><span
class="pre"><code
class="sourceCode cpp">bout<span class="op">::</span>OptionsIO<span class="op">::</span>write<span class="op">()</span></code></span></a>
will only write variables with a
<span class="pre">`"time_dimension"`</span> of
<span class="pre">`"t"`</span>. You can write variables with a different
time dimension by passing it as the second argument:
<span class="pre">`OptionsIO::create(filename)->write(options,`</span>` `<span class="pre">`"t2")`</span>
for example.

</div>

</div>

</div>

<div id="fft" class="section">

## FFT<a href="#fft" class="headerlink"
title="Permalink to this heading">#</a>

There is one option for Fourier transforms,
<span class="pre">`fft_measurement_flag`</span> (default:
<span class="pre">`estimate`</span>). This can be used to control FFTW’s
measurement mode: <span class="pre">`estimate`</span> for
<span class="pre">`FFTW_ESTIMATE`</span>,
<span class="pre">`measure`</span> for
<span class="pre">`FFTW_MEASURE`</span> or
<span class="pre">`exhaustive`</span> for
<span class="pre">`FFTW_EXHAUSTIVE`</span>:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [fft]
    fft_measurement_flag = measure

</div>

</div>

In <span class="pre">`FFTW_MEASURE`</span> mode, FFTW runs and measures
how long several FFTs take, and tries to find the optimal method;
<span class="pre">`FFTW_EXHAUSTIVE`</span> tests even more algorithms.

<div class="admonition note">

Note

Technically, <span class="pre">`FFTW_MEASURE`</span> and
<span class="pre">`FFTW_EXHAUSTIVE`</span> are non-deterministic and
enabling <span class="pre">`fft_measure`</span> may result in slightly
different answers from run to run, or be dependent on the number of MPI
processes. This may be important if you are trying to benchmark or
measure performance of your code.

See the <a href="http://www.fftw.org/faq/section3.html#nondeterministic"
class="reference external">FFTW FAQ</a> for more information.

</div>

</div>

<div id="types-for-multi-valued-options" class="section">

## Types for multi-valued options<a href="#types-for-multi-valued-options" class="headerlink"
title="Permalink to this heading">#</a>

An <span class="pre">`enum`</span>` `<span class="pre">`class`</span>
can be a useful construct for options in a physics model. It can have an
arbitrary number of user-defined, named values (although the code in
<span class="pre">`include/bout/bout_enum_class.hxx`</span> needs
extending for more than 10 values). The advantage over using a
<span class="pre">`std::string`</span> for an option is that a typo
cannot produce an unexpected value: in C++ code it is a compile-time
error and reading from <span class="pre">`BOUT.inp`</span> it is a
run-time exception. We provide a utility macro
<span class="pre">`BOUT_ENUM_CLASS`</span> to define an
<span class="pre">`enum`</span>` `<span class="pre">`class`</span> with
some extra convenience methods. For example, after defining
<span class="pre">`myoption`</span> like:

<div class="highlight-cpp notranslate">

<div class="highlight">

    BOUT_ENUM_TYPE(myoption, foo, bar, baz);

</div>

</div>

it is possible not only to test for a value, e.g.:

<div class="highlight-cpp notranslate">

<div class="highlight">

    myoption x = <something>;
    ...
    if (x == myoption::foo) {
      do a foo thing
    }

</div>

</div>

but also to convert the option to a string:

<div class="highlight-cpp notranslate">

<div class="highlight">

    std::string s = toString(x);

</div>

</div>

pass it to a stream:

<div class="highlight-cpp notranslate">

<div class="highlight">

    output << x;

</div>

</div>

or get an option like <span class="pre">`myinput=baz`</span> from an
input file or the command line as a <span class="pre">`myoption`</span>:

<div class="highlight-cpp notranslate">

<div class="highlight">

    myoption y = Options::root()["myinput"].as<myoption>();

</div>

</div>

or with a default value:

<div class="highlight-cpp notranslate">

<div class="highlight">

    myoption y = Options::root()["myinput"].withDefault(myoption::bar);

</div>

</div>

Only strings exactly (but case-insensitively) matching the name of one
of the defined <span class="pre">`myoption`</span> values are allowed,
anything else results in an exception being thrown.

</div>

</div>

<div class="prev-next-area">

<a href="adios2.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

ADIOS2 support

</div>

<a href="input_grids.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Generating input grids

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#bout-inp-input-file"
  class="reference internal nav-link">BOUT.inp input file</a>
  - <a href="#boolean-expressions"
    class="reference internal nav-link">Boolean expressions</a>
  - <a href="#special-symbols-in-option-names"
    class="reference internal nav-link">Special symbols in Option names</a>
  - <a href="#printing-options" class="reference internal nav-link">Printing
    Options</a>
- <a href="#command-line-options"
  class="reference internal nav-link">Command line options</a>
- <a href="#general-options" class="reference internal nav-link">General
  options</a>
  - <a href="#grids" class="reference internal nav-link">Grids</a>
- <a href="#communications"
  class="reference internal nav-link">Communications</a>
- <a href="#differencing-methods"
  class="reference internal nav-link">Differencing methods</a>
- <a href="#model-specific-options"
  class="reference internal nav-link">Model-specific options</a>
- <a href="#input-and-output" class="reference internal nav-link">Input
  and Output</a>
- <a href="#implementation"
  class="reference internal nav-link">Implementation</a>
  - <a href="#documentation"
    class="reference internal nav-link">Documentation</a>
  - <a href="#creating-options" class="reference internal nav-link">Creating
    Options</a>
  - <a href="#setting-option-attributes"
    class="reference internal nav-link">Setting option attributes</a>
  - <a href="#overriding-library-defaults"
    class="reference internal nav-link">Overriding library defaults</a>
  - <a href="#older-interface" class="reference internal nav-link">Older
    interface</a>
- <a href="#reading-options" class="reference internal nav-link">Reading
  options</a>
- <a href="#reading-and-writing-to-binary-formats"
  class="reference internal nav-link">Reading and writing to binary
  formats</a>
  - <a href="#time-dependence" class="reference internal nav-link">Time
    dependence</a>
- <a href="#fft" class="reference internal nav-link">FFT</a>
- <a href="#types-for-multi-valued-options"
  class="reference internal nav-link">Types for multi-valued options</a>

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
