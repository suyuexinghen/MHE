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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/introduction.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/introduction.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/introduction.rst"
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

# Introduction

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#license-and-terms-of-use"
  class="reference internal nav-link">License and terms of use</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="introduction" class="section">

<span id="sec-userguide"></span>

# Introduction<a href="#introduction" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ is a C++ framework for writing plasma fluid simulations with an
arbitrary number of equations in 3D curvilinear coordinates. More
specifically, it is a multiblock structured finite difference (/volume)
code in curvilinear coordinates, with some features to support unusual
coordinate systems used in fusion plasma physics. It has been developed
from the original **BOU**ndary **T**urbulence 3D 2-fluid edge simulation
code written by X.Xu and M.Umansky at LLNL.

The aim of BOUT++ is to automate the common tasks needed for simulation
codes, and to separate the complicated (and error-prone) details such as
differential geometry, parallel communication, and file input/output
from the user-specified equations to be solved. Thus the equations being
solved are made clear, and can be easily changed with only minimal
knowledge of the inner workings of the code. As far as possible, this
allows the user to concentrate on the physics, rather than worrying
about the numerics. This doesn’t mean that users don’t have to think
about numerical methods, and so selecting differencing schemes and
boundary conditions is discussed in this manual. The generality of
BOUT++ of course also comes with a limitation: although there is a large
class of problems which can be tackled by this code, there are many more
problems which require a more specialised solver and which BOUT++ will
not be able to handle. Hopefully this manual will enable you to test
whether BOUT++ is suitable for your problem as quickly and painlessly as
possible.

BOUT++ treats time integration and spatial operators separately, an
approach called the Method of Lines (MOL). This means that BOUT++
consists of two main parts:

1.  A set of Ordinary Differential Equation (ODE) integrators, including
    implicit, explicit and IMEX schemes, such as Runge-Kutta and the
    CVODE solver from SUNDIALS. These don’t “know” anything about the
    equations being solved, only requiring the time derivative of the
    system state. For example they make no distinction between the
    different evolving fields, or the number of dimensions in the
    simulation. This kind of problem-specific information can be used to
    improve efficiency, and is usually supplied in the form of
    user-supplied preconditioners. See section
    <a href="time_integration.html#sec-timeoptions"
    class="reference internal"><span class="std std-ref">Options</span></a>
    for more details.

2.  A set of operators and data types for calculating time derivatives,
    given the system state. These calculate things like algebraic
    operations (+,-,\*,/ etc), spatial derivatives, and some integral
    operators.

Each of these two parts treats the other as a black box (mostly), and
they communicate by exchanging arrays of data: The ODE integrator finds
the system state at a given time and passes it to the problem-dependent
code, which uses a combination of operators to calculate the time
derivative. This time derivative is passed back to the ODE integrator,
which updates the state and the cycle continues. This scheme has some
advantages in terms of flexibility: Each part of the code doesn’t depend
on thedetails of the other, so can be changed without requiring
modifications to the other. Unfortunately for many problems the details
can make a big difference, so ways to provide problem-specific
information to time integrators, such as preconditioners, are also
provided.

Though designed to simulate tokamak edge plasmas, the methods used are
very general and almost any metric tensor can be specified, allowing the
code to be used to perform simulations in (for example) slab, sheared
slab, and cylindrical coordinates. The restrictions on the simulation
domain are that the equilibrium must be axisymmetric (in the z
coordinate), and that the parallelisation is done in the
<span class="math notranslate nohighlight">\\x\\</span> and
<span class="math notranslate nohighlight">\\y\\</span> (parallel to
<span class="math notranslate nohighlight">\\\mathbf{B}\\</span>)
directions.

After describing how to install BOUT++ (section
<a href="installing.html#sec-install" class="reference internal"><span
class="std std-ref">Getting started</span></a>), run the test suite
(section <a href="installing.html#sec-runtestsuite"
class="reference internal"><span class="std std-ref">Running the test
suite</span></a>) and a few examples (section
<a href="running_bout.html#sec-running" class="reference internal"><span
class="std std-ref">Running BOUT++</span></a>, more detail in section
<a href="physics_models.html#sec-examples"
class="reference internal"><span class="std std-ref">More
examples</span></a>), increasingly sophisticated ways to modify the
problem being solved are introduced. The simplest way to modify a
simulation case is by altering the input options, described in section
<a href="bout_options.html#sec-options" class="reference internal"><span
class="std std-ref">BOUT++ options</span></a>. Checking that the options
are doing what you think they should be by looking at the output logs is
described in section
<a href="running_bout.html#sec-running" class="reference internal"><span
class="std std-ref">Running BOUT++</span></a>, and an overview of the
IDL analysis routines for data post-processing and visualisation is
given in section <a href="output_and_post.html#sec-output"
class="reference internal"><span
class="std std-ref">Post-processing</span></a>. Generating new grid
files, particularly for tokamak equilibria, is described in section
<a href="input_grids.html#sec-gridgen" class="reference internal"><span
class="std std-ref">Generating input grids</span></a>.

Up to this point, little programming experience has been assumed, but
performing more drastic alterations to the physics model requires
modifying C++ code. Section <a href="physics_models.html#sec-equations"
class="reference internal"><span class="std std-ref">BOUT++ physics
models</span></a> describes how to write a new physics model specifying
the equations to be solved, using ideal MHD as an example. The remaining
sections describe in more detail aspects of using BOUT++: section
<a href="differential_operators.html#sec-diffops"
class="reference internal"><span class="std std-ref">Differential
operators</span></a> describes the differential operators and methods
available; section <a href="staggered_grids.html#sec-staggergrids"
class="reference internal"><span class="std std-ref">Staggered
grids</span></a> covers the experimental staggered grid system.

Various sources of documentation are:

- This manual

- Most directories in the BOUT++ distribution contain a README file.
  This should describe briefly what the contents of the directory are
  and how to use them.

- Most of the code contains Doxygen comment tags (which are slowly
  getting better). Running
  <a href="www.doxygen.org" class="reference external">doxygen</a> on
  these files should therefore generate an HTML reference. This is
  probably going to be the most up-to-date documentation.

<div id="license-and-terms-of-use" class="section">

## License and terms of use<a href="#license-and-terms-of-use" class="headerlink"
title="Permalink to this heading">#</a>

Copyright 2010 - 2022 BOUT++ contributors

BOUT++ is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

BOUT++ is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
License for more details.

You should have received a copy of the GNU Lesser General Public License
along with BOUT++. If not, see \<<a href="https://www.gnu.org/licenses/"
class="reference external">https://www.gnu.org/licenses/</a>\>.

A copy of the LGPL license is in COPYING.LESSER. Since this is based on
(and refers to) the GPL, this is included in COPYING.

BOUT++ is free software, but since it is a scientific code we also ask
that you show professional courtesy when using this code:

1.  Since you are benefiting from work on BOUT++, we ask that you submit
    any improvements you make to the code to us via the boutproject
    github issues and pull-request system.

2.  If you use BOUT++ results in a paper or professional publication, we
    ask that you send your results to one of the BOUT++ authors first so
    that we can check them. It is understood that in most cases if one
    or more of the BOUT++ team are involved in preparing results then
    they should appear as co-authors.

3.  Publications or figures made with the BOUT++ code should acknowledge
    the BOUT++ code by citing
    <a href="https://doi.org/10.1016/j.cpc.2009.03.008"
    class="reference external">B.Dudson et. al. Comp.Phys.Comm 2009</a>
    and/or other BOUT++ papers. See the file CITATION for details.

</div>

</div>

<div class="prev-next-area">

<a href="../index.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Welcome to BOUT++’s documentation!

</div>

<a href="quickstart.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Quickstart Guide

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#license-and-terms-of-use"
  class="reference internal nav-link">License and terms of use</a>

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
