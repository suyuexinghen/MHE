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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/makefiles.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/makefiles.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/makefiles.rst"
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

# Makefiles and compiling BOUT++

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#executables-example"
  class="reference internal nav-link">Executables example</a>
  - <a href="#multiple-subdirectories"
    class="reference internal nav-link">Multiple subdirectories</a>
- <a href="#modules-example" class="reference internal nav-link">Modules
  example</a>
  - <a href="#adding-a-new-subdirectory-to-src"
    class="reference internal nav-link">Adding a new subdirectory to
    ’src’</a>
- <a href="#bout-config-script"
  class="reference internal nav-link">bout-config script</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="makefiles-and-compiling-bout" class="section">

# Makefiles and compiling BOUT++<a href="#makefiles-and-compiling-bout" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ has its own makefile system. These can be used to

1.  <a href="#sec-executables" class="reference internal"><span
    class="std std-ref">Write an example or executable</span></a>

2.  <a href="#sec-modules" class="reference internal"><span
    class="std std-ref">Add a feature to BOUT++</span></a>

In all makefiles, <span class="pre">`BOUT_TOP`</span> is required!

These makefiles are sufficient for most uses, but for more complicated,
an executable script <span class="pre">`bout-config`</span> can be used
to get the compilation flags (see
<a href="#sec-bout-config" class="reference internal"><span
class="std std-ref">bout-config script</span></a>).

<div id="executables-example" class="section">

<span id="sec-executables"></span>

## Executables example<a href="#executables-example" class="headerlink"
title="Permalink to this heading">#</a>

If writing an example (or physics module that executes) then the
makefile is very simple:

<div class="highlight-makefile notranslate">

<div class="highlight">

    BOUT_TOP        = ../..

    SOURCEC         = <filename>.cxx

    include $(BOUT_TOP)/make.config

</div>

</div>

where <span class="pre">`BOUT_TOP`</span> - refers to the relative (or
absolute) location of the BOUT directory (the one that includes
<span class="pre">`/lib`</span> and <span class="pre">`/src`</span>) and
<span class="pre">`SOURCEC`</span> is the name of your file, e.g.
<span class="pre">`gas_compress.cxx`</span>.

Optionally, it is possible to specify <span class="pre">`TARGET`</span>
which defines what the executable should be called (e.g. if you have
multiple source files). That’s it!

<div id="multiple-subdirectories" class="section">

### Multiple subdirectories<a href="#multiple-subdirectories" class="headerlink"
title="Permalink to this heading">#</a>

Large physics modules can have many files, and it can be helpful to
organise these into subdirectories. An example of how to do this is in
<span class="pre">`examples/make_subdir`</span>.

In the top level, list the directories

<div class="highlight-makefile notranslate">

<div class="highlight">

    DIRS = fuu bar

</div>

</div>

In the makefile in each subdirectory, specify

<div class="highlight-makefile notranslate">

<div class="highlight">

    TARGET = sub

</div>

</div>

then specify the path to the top-level directory

<div class="highlight-makefile notranslate">

<div class="highlight">

    MODULE_DIR = ..

</div>

</div>

and the name of the subdirectory that the makefile is in

<div class="highlight-makefile notranslate">

<div class="highlight">

    SUB_NAME = fuu

</div>

</div>

</div>

</div>

<div id="modules-example" class="section">

<span id="sec-modules"></span>

## Modules example<a href="#modules-example" class="headerlink"
title="Permalink to this heading">#</a>

If you are writing a new module (or concrete implementation) to go into
the BOUT++ library, then it is again pretty simple

<div class="highlight-makefile notranslate">

<div class="highlight">

    BOUT_TOP = ../..

    SOURCEC         = communicator.cxx difops.cxx geometry.cxx grid.cxx \
                      interpolation.cxx topology.cxx
    SOURCEH         = $(SOURCEC:%.cxx=%.h)
    TARGET          = lib

    include $(BOUT_TOP)/make.config

</div>

</div>

<span class="pre">`TARGET`</span> - must be
<span class="pre">`lib`</span> to signify you are adding to
<span class="pre">`libbout++.a`</span>.

The other variables should be pretty self explanatory.

<div id="adding-a-new-subdirectory-to-src" class="section">

### Adding a new subdirectory to ’src’<a href="#adding-a-new-subdirectory-to-src" class="headerlink"
title="Permalink to this heading">#</a>

No worries, just make sure to edit
<span class="pre">`src/makefile`</span> to add it to the
<span class="pre">`DIRS`</span> variable.

</div>

</div>

<div id="bout-config-script" class="section">

<span id="sec-bout-config"></span>

## bout-config script<a href="#bout-config-script" class="headerlink"
title="Permalink to this heading">#</a>

The <span class="pre">`bout-config`</span> script is in the
<span class="pre">`bin`</span> subdirectory of the BOUT++ distribution,
and is generated by <span class="pre">`configure`</span>. This script
can be used to get the compilers, flags and settings to compile BOUT++.
To get a list of available options:

<div class="highlight-bash notranslate">

<div class="highlight">

    $ bout-config --help

</div>

</div>

so to get the library linking flags, for example

<div class="highlight-bash notranslate">

<div class="highlight">

    $ bout-config --libs

</div>

</div>

This script can be used in makefiles to compile BOUT++ alongside other
libraries. The easiest way is to use
<span class="pre">`bout-config`</span> to find the
<span class="pre">`make.config`</span> file which contains the settings.
For example the heat conduction example can be compiled with the
following <span class="pre">`makefile`</span>:

<div class="highlight-makefile notranslate">

<div class="highlight">

    SOURCEC         = conduction.cxx
    include $(shell bout-config --config-file)

</div>

</div>

This includes the <span class="pre">`make.config`</span> file installed
with <span class="pre">`bout-config`</span>, rather than using the
<span class="pre">`BOUT_TOP`</span> variable.

A different way to use <span class="pre">`bout-config`</span> is to get
the compiler and linker flags, and use them in your own makefile, for
example:

<div class="highlight-makefile notranslate">

<div class="highlight">

    CXX=`bout-config --cxx`
    CFLAGS=`bout-config --cflags`
    LD=`bout-config --ld`
    LDFLAGS=`bout-config --libs

    conduction: conduction.cxx
        $(CXX) $(CFLAGS) -c conduction.cxx -o conduction.o
        $(LD) -o conduction conduction.o $(LDFLAGS)

</div>

</div>

A more general example is in
<span class="pre">`examples/make-script`</span>.

</div>

</div>

<div class="prev-next-area">

<a href="physics_models.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

BOUT++ physics models

</div>

<a href="variable_init.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Variable initialisation

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#executables-example"
  class="reference internal nav-link">Executables example</a>
  - <a href="#multiple-subdirectories"
    class="reference internal nav-link">Multiple subdirectories</a>
- <a href="#modules-example" class="reference internal nav-link">Modules
  example</a>
  - <a href="#adding-a-new-subdirectory-to-src"
    class="reference internal nav-link">Adding a new subdirectory to
    ’src’</a>
- <a href="#bout-config-script"
  class="reference internal nav-link">bout-config script</a>

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
