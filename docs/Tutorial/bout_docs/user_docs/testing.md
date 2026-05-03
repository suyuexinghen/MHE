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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/testing.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/testing.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/testing.rst"
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

# Testing

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#automated-tests-and-code-coverage"
  class="reference internal nav-link">Automated tests and code
  coverage</a>
- <a href="#unit-tests" class="reference internal nav-link">Unit tests</a>
- <a href="#integrated-tests"
  class="reference internal nav-link">Integrated tests</a>
  - <a href="#custom-test-requirements"
    class="reference internal nav-link">Custom test requirements</a>
- <a href="#method-of-manufactured-solutions"
  class="reference internal nav-link">Method of Manufactured Solutions</a>
  - <a href="#choosing-manufactured-solutions"
    class="reference internal nav-link">Choosing manufactured solutions</a>
- <a href="#timing" class="reference internal nav-link">Timing</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="testing" class="section">

# Testing<a href="#testing" class="headerlink"
title="Permalink to this heading">#</a>

There are three types of test used in BOUT++, in order of complexity:
unit tests, integrated tests, and “method of manufactured solutions”
(MMS) tests. Unit tests are very short, quick tests that test a single
“unit” – usually a single function or method. Integrated tests are
longer tests that range from tests that need a lot of set up and check
multiple conditions, to full physics model tests. MMS tests check the
numerical properties of operators, such as the error scaling of
derivatives.

There is a test suite that runs through all of the unit tests, and
selected integrated and MMS tests. The easiest way to run this is with:

<div class="highlight-console notranslate">

<div class="highlight">

    $ make check

</div>

</div>

We expect that any new feature or function implemented in BOUT++ also
has some corresponding tests, and *strongly* prefer unit tests.

The tests can be run in parallel, with the autotools based workflow

<div class="highlight-console notranslate">

<div class="highlight">

    $ make check -j 16

</div>

</div>

will build and run all tests on up to 16 threads. With cmake first
compile all test before running them in parallel

<div class="highlight-console notranslate">

<div class="highlight">

    $ make build-check -j 16
    $ ctest -j 8

</div>

</div>

will build with up to 16 threads in parallel, and then run up to 8 tests
in parallel, which may use more or less then 16 threads.

<div id="automated-tests-and-code-coverage" class="section">

<span id="sec-automated-testing"></span>

## Automated tests and code coverage<a href="#automated-tests-and-code-coverage" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ uses <a href="https://github.com/boutproject/BOUT-dev/actions"
class="reference external">Github Actions</a> to automatically run the
test suite on every push to the GitHub repository, as well as on every
submitted Pull Request. The Github Actions settings are in
<span class="pre">`.github/workflows/`</span>. Pull requests that fail
the tests will not be merged.

We also gather information from how well the unit tests cover the
library using <a href="https://codecov.io/gh/boutproject/BOUT-dev"
class="reference external">CodeCov</a>, the settings for which are
stored in <span class="pre">`.codecov.yml`</span>.

</div>

<div id="unit-tests" class="section">

<span id="sec-unit-tests"></span>

## Unit tests<a href="#unit-tests" class="headerlink"
title="Permalink to this heading">#</a>

The unit test suits aims to be a comprehensive set of tests that run
*very* fast and ensure the basic functionality of BOUT++ is correct. At
the time of writing, we have around 500 tests that run in less than a
second. Because these tests run very quickly, they should be run on
every commit (or even more often!). For more information on the unit
tests, see <span class="pre">`tests/unit/README.md`</span>.

You can run the unit tests with:

<div class="highlight-console notranslate">

<div class="highlight">

    $ make check-unit-tests

</div>

</div>

</div>

<div id="integrated-tests" class="section">

<span id="sec-integrated-tests"></span>

## Integrated tests<a href="#integrated-tests" class="headerlink"
title="Permalink to this heading">#</a>

This set of tests are designed to test that different components of the
BOUT++ library work together. These tests are more expensive than the
unit tests, but are expected to be run on at least every pull request,
and the majority on every commit.

You can run the integrated tests with:

<div class="highlight-console notranslate">

<div class="highlight">

    $ make check-integrated-tests

</div>

</div>

The test suite is in the <span class="pre">`tests/integrated`</span>
directory, and is run using the <span class="pre">`test_suite`</span>
python script.
<span class="pre">`tests/integrated/test_suite_list`</span> contains a
list of the subdirectories to run (e.g.
<span class="pre">`test-io`</span>,
<span class="pre">`test-laplace`</span>,
<span class="pre">`interchange-instability`</span>). In each of those
subdirectories the script <span class="pre">`runtest`</span> is
executed, and the return value used to determine if the test passed or
failed.

All tests should be short, otherwise it discourages people from running
the tests before committing changes. A few minutes or less on a typical
desktop, and ideally only a few seconds. If you have a large simulation
which you want to stop anyone breaking, find starting parameters which
are as sensitive as possible so that the simulation can be run quickly.

<div id="custom-test-requirements" class="section">

### Custom test requirements<a href="#custom-test-requirements" class="headerlink"
title="Permalink to this heading">#</a>

Some tests require particular libraries or environments, so should be
skipped if these are not available. To do this, each
<span class="pre">`runtest`</span> script can contain a line starting
with <span class="pre">`#requires`</span>, followed by a python
expression which evaluates to <span class="pre">`True`</span> or
<span class="pre">`False`</span>. For example, a test which doesn’t work
if both ARKODE and PETSc are used:

<div class="highlight-console notranslate">

<div class="highlight">

    #requires not (arkode and petsc)

</div>

</div>

or if there were a test which required PETSc to be available, it could
specify

<div class="highlight-console notranslate">

<div class="highlight">

    #requires petsc

</div>

</div>

Currently the requirements which can be combined are
<span class="pre">`netcdf`</span>, <span class="pre">`pnetcdf`</span>,
<span class="pre">`pvode`</span>, <span class="pre">`cvode`</span>,
<span class="pre">`ida`</span>, <span class="pre">`lapack`</span>,
<span class="pre">`petsc`</span>, <span class="pre">`slepc`</span>,
<span class="pre">`arkode`</span>, <span class="pre">`openmp`</span> and
<span class="pre">`make`</span>. The <span class="pre">`make`</span>
requirement is set to True when the tests are being compiled (but not
run), and False when the scripts are run. It’s used for tests which do
not have a compilation stage.

</div>

</div>

<div id="method-of-manufactured-solutions" class="section">

<span id="sec-mms"></span>

## Method of Manufactured Solutions<a href="#method-of-manufactured-solutions" class="headerlink"
title="Permalink to this heading">#</a>

The Method of Manufactured solutions (MMS) is a rigorous way to check
that a numerical algorithm is implemented correctly. A known solution is
specified (manufactured), and it is possible to check that the code
output converges to this solution at the expected rate.

To enable testing by MMS, switch an input option “mms” to true:

<div class="highlight-cfg notranslate">

<div class="highlight">

    [solver]
    mms = true

</div>

</div>

This will have the following effect:

1.  For each evolving variable, the solution will be used to initialise
    and to calculate the error

2.  For each evolving variable, a source function will be read from the
    input file and added to the time derivative.

<div class="admonition note">

Note

The convergence behaviour of derivatives using FFTs is quite different
to the finite difference methods: once the highest frequency in the
manufactured solution is resolved, the accuracy will jump enormously,
and after that, finer grids will not increase the accuracy. Whereas with
finite difference methods, accuracy varies smoothly as the grid is
refined.

</div>

<div id="choosing-manufactured-solutions" class="section">

### Choosing manufactured solutions<a href="#choosing-manufactured-solutions" class="headerlink"
title="Permalink to this heading">#</a>

Manufactured solutions must be continuous and have continuous
derivatives. Common mistakes:

- Don’t use terms multiplying coordinates together e.g.
  <span class="pre">`x`</span>` `<span class="pre">`*`</span>` `<span class="pre">`z`</span>
  or
  <span class="pre">`y`</span>` `<span class="pre">`*`</span>` `<span class="pre">`z`</span>.
  These are not periodic in
  <span class="math notranslate nohighlight">\\y\\</span> and/or
  <span class="math notranslate nohighlight">\\z\\</span>, so will give
  strange answers and usually no convergence. Instead use
  <span class="pre">`x`</span>` `<span class="pre">`*`</span>` `<span class="pre">`sin(z)`</span>
  or similar, which are periodic.

</div>

</div>

<div id="timing" class="section">

<span id="sec-timerclass"></span>

## Timing<a href="#timing" class="headerlink"
title="Permalink to this heading">#</a>

To time parts of the code, and calculate the percentage of time spent in
communications, file I/O, etc. there is the
<a href="../_breathe_autogen/file/timer_8hxx.html#_CPPv45Timer"
class="reference internal" title="Timer"><span class="pre"><code
class="sourceCode cpp">Timer</code></span></a> class defined in
<span class="pre">`include/bout/sys/timer.hxx`</span>. To use it, just
create a <a href="../_breathe_autogen/file/timer_8hxx.html#_CPPv45Timer"
class="reference internal" title="Timer"><span class="pre"><code
class="sourceCode cpp">Timer</code></span></a> object at the beginning
of the function you want to time:

<div class="highlight-cpp notranslate">

<div class="highlight">

    #include <bout/sys/timer.hxx>

    void someFunction() {
      Timer timer("test")
      ...
    }

</div>

</div>

Creating the object starts the timer, and since the object is destroyed
when the function returns (since it goes out of scope) the destructor
stops the timer.

<div class="highlight-cpp notranslate">

<div class="highlight">

    class Timer {
    public:
      Timer();
      Timer(const std::string &label);
      ~Timer();

      double getTime();
      double resetTime();
    };

</div>

</div>

The empty constructor is equivalent to setting
<span class="pre">`label`</span>` `<span class="pre">`=`</span>` `<span class="pre">`""`</span>
. Constructors call a private function
<span class="pre">`getInfo()`</span> , which looks up the
<span class="pre">`timer_info`</span> structure corresponding to the
label in a
<span class="pre">`map<string,`</span>` `<span class="pre">`timer_info*>`</span>
. If no such structure exists, then one is created. This structure is
defined as:

<div class="highlight-cpp notranslate">

<div class="highlight">

    struct timer_info {
      double time;    ///< Total time
      bool running;   ///< Is the timer currently running?
      double started; ///< Start time
    };

</div>

</div>

Since each timer can only have one entry in the map, creating two timers
with the same label at the same time will lead to trouble. Hence this
code is **not** thread-safe.

The member functions <span class="pre">`getTime()`</span> and
<span class="pre">`resetTime()`</span> both return the current time.
Whereas <span class="pre">`getTime()`</span> only returns the time
without modifying the timer, <span class="pre">`resetTime()`</span> also
resets the timer to zero.

If you don’t have the object, you can still get and reset the time using
static methods:

<div class="highlight-cpp notranslate">

<div class="highlight">

    double Timer::getTime(const std::string &label);
    double Timer::resetTime(const std::string &label);

</div>

</div>

These look up the <span class="pre">`timer_info`</span> structure, and
perform the same task as their non-static namesakes. These functions are
used by the monitor function in <span class="pre">`bout++.cxx`</span> to
print the percentage timing information.

</div>

</div>

<div class="prev-next-area">

<a href="boundary_options.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Boundary conditions

</div>

<a href="gpu_support.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

GPU support

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#automated-tests-and-code-coverage"
  class="reference internal nav-link">Automated tests and code
  coverage</a>
- <a href="#unit-tests" class="reference internal nav-link">Unit tests</a>
- <a href="#integrated-tests"
  class="reference internal nav-link">Integrated tests</a>
  - <a href="#custom-test-requirements"
    class="reference internal nav-link">Custom test requirements</a>
- <a href="#method-of-manufactured-solutions"
  class="reference internal nav-link">Method of Manufactured Solutions</a>
  - <a href="#choosing-manufactured-solutions"
    class="reference internal nav-link">Choosing manufactured solutions</a>
- <a href="#timing" class="reference internal nav-link">Timing</a>

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
