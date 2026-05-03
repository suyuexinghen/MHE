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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/preconditioning.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/preconditioning.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/preconditioning.rst"
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

# BOUT++ preconditioning

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#introduction"
  class="reference internal nav-link">Introduction</a>
- <a href="#physics-problems" class="reference internal nav-link">Physics
  problems</a>
  - <a href="#resistive-drift-interchange-instability"
    class="reference internal nav-link">Resistive drift-interchange
    instability</a>
  - <a href="#reduced-3-field-mhd"
    class="reference internal nav-link">Reduced 3-field MHD</a>
  - <a href="#solving-phi-as-a-constraint"
    class="reference internal nav-link">Solving <span
    class="math notranslate nohighlight">\(\phi\)</span> as a constraint</a>
  - <a href="#uedge-equations" class="reference internal nav-link">UEDGE
    equations</a>
  - <a href="#fluid-turbulence" class="reference internal nav-link">2-fluid
    turbulence</a>
- <a href="#jacobian-vector-multiply"
  class="reference internal nav-link">Jacobian-vector multiply</a>
- <a href="#preconditioner-vector-multiply"
  class="reference internal nav-link">Preconditioner-vector multiply</a>
  - <a href="#reduced-3-field-mhd-1"
    class="reference internal nav-link">Reduced 3-field MHD</a>
- <a href="#stencils" class="reference internal nav-link">Stencils</a>
- <a href="#jacobian-calculation"
  class="reference internal nav-link">Jacobian calculation</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="bout-preconditioning" class="section">

# BOUT++ preconditioning<a href="#bout-preconditioning" class="headerlink"
title="Permalink to this heading">#</a>

Author<span class="colon">:</span>  
B.Dudson, University of York

<div id="introduction" class="section">

## Introduction<a href="#introduction" class="headerlink"
title="Permalink to this heading">#</a>

This manual describes some of the ways BOUT++ could (and in some cases
does) support preconditioning, Jacobian calculations and other methods
to speed up simulations. This manual assumes that you’re familiar with
how BOUT++ works internally.

Some notation: The ODE being solved is of the form

<div class="math notranslate nohighlight">

\\{\frac{\partial {\mathbf{f}}}{\partial t}} =
{\mathbf{F}}\left({\mathbf{f}}\right)\\

</div>

Here the state vector <span class="math notranslate nohighlight">\\f =
\left(f_0, f_1, f_2, \ldots\right)^T\\</span> is a vector containing the
evolving (3D) variables
<span class="math notranslate nohighlight">\\f_i\left(x,y,z\right)\\</span>.

The Jacobian of this system is then

<div class="math notranslate nohighlight">

\\{\mathbb{J}}= {\frac{\partial {\mathbf{F}}}{\partial {\mathbf{f}}}}\\

</div>

The order of the elements in the vector
<span class="math notranslate nohighlight">\\{\mathbf{f}}\\</span> is
determined in the solver code and SUNDIALS, so here just assume that
there exists a map
<span class="math notranslate nohighlight">\\\mathbb{I}\\</span> between
a global index <span class="math notranslate nohighlight">\\k\\</span>
and (variable, position) i.e.
<span class="math notranslate nohighlight">\\\left(i,x,y,z\right)\\</span>

<div class="math notranslate nohighlight">

\\\mathbf{I} : \left(i,x,y,z\right) \mapsto k\\

</div>

and its inverse

<div class="math notranslate nohighlight">

\\\mathbf{I}^{-1} : k \mapsto \left(i,x,y,z\right)\\

</div>

Some problem-specific operations which can be used to speed up the
timestepping

1.  Jacobian-vector multiply: Given a vector, multiply it by
    <span class="math notranslate nohighlight">\\{\mathbb{J}}\\</span>

2.  Preconditioner multiply: Given a vector, multiply by an approximate
    inverse of <span class="math notranslate nohighlight">\\\mathbb{M} =
    \mathbb{I} - \gamma\mathbb{J}\\</span>

3.  Calculate the stencils i.e. non-zero elements in
    <span class="math notranslate nohighlight">\\{\mathbb{J}}\\</span>

4.  Calculate the non-zero elements of
    <span class="math notranslate nohighlight">\\{\mathbb{J}}\\</span>

</div>

<div id="physics-problems" class="section">

## Physics problems<a href="#physics-problems" class="headerlink"
title="Permalink to this heading">#</a>

Some interesting physics problems of increasing difficulty

<div id="resistive-drift-interchange-instability" class="section">

### Resistive drift-interchange instability<a href="#resistive-drift-interchange-instability" class="headerlink"
title="Permalink to this heading">#</a>

A “simple” test problem of 2 fields, which results in non-trivial
turbulent results. Supports resistive drift wave and interchange
instabilities.

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\frac{\partial N_i}{\partial t}} +
{{\mathbf{v}}\_E}\cdot\nabla N_i &=& 0 \\ {\frac{\partial
\omega}{\partial t}} + {{\mathbf{v}}\_E}\cdot\nabla\omega &=&
2\omega\_{ci}{\mathbf{b}}\times\kappa\cdot\nabla P + N_iZ_i e\frac{4\pi
V_A^2}{c^2}\nabla\_{||}j\_{||} \\ \nabla\_\perp^2\omega / N_i &=& \phi
\\ 0.51\nu\_{ei}j\_{||} &=& \frac{e}{m_e}\partial\_{||}\phi +
\frac{T_e}{N_i m_e}\partial\_{||} N_i\end{aligned}\end{split}\\

</div>

</div>

<div id="reduced-3-field-mhd" class="section">

### Reduced 3-field MHD<a href="#reduced-3-field-mhd" class="headerlink"
title="Permalink to this heading">#</a>

This is a 3-field system of pressure
<span class="math notranslate nohighlight">\\P\\</span>, magnetic flux
<span class="math notranslate nohighlight">\\\psi\\</span> and vorticity
<span class="math notranslate nohighlight">\\U\\</span>:

<div class="math notranslate nohighlight">

\\\begin{split}{\mathbf{f}} = \left(\begin{array}{c} P \\ \psi \\ U
\end{array}\right)\end{split}\\

</div>

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\frac{\partial \psi}{\partial t}} &=&
-\frac{1}{B_0}\nabla\_{||}\phi \\ &=&
-\frac{1}{B_0}\left\[{\mathbf{b}}\_0 -
\left({\mathbf{b}}\_0\times\nabla\psi\right)\right\]\cdot\nabla\phi \\
&=& -\frac{1}{B_0}{\mathbf{b}}\_0\cdot\nabla\phi -
\frac{1}{B_0}\left({\mathbf{b}}\_0\times\nabla\phi\right)\cdot\nabla\psi
\\ \Rightarrow \frac{d \psi}{dt} &=&
-\frac{1}{B_0}{\mathbf{b}}\_0\cdot\nabla \phi\end{aligned}\end{split}\\

</div>

The coupled set of equations to be solved are therefore

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} \frac{1}{B_0}\nabla\_\perp^2\phi &=& U \\
\left({\frac{\partial }{\partial t}} +
{\mathbf{v}}\_E\cdot\nabla\right)\psi &=&
-\frac{1}{B_0}{\mathbf{b}}\_0\cdot\nabla\phi \\ \left({\frac{\partial
}{\partial t}} + {\mathbf{v}}\_E\cdot\nabla\right)P &=& 0 \\
\left({\frac{\partial }{\partial t}} +
{\mathbf{v}}\_E\cdot\nabla\right)U &=&
\frac{1}{\rho}B_0^2\left\[{\mathbf{b}}\_0 -
\left({\mathbf{b}}\_0\times\nabla\psi\right)\right\]\cdot\left(\frac{J\_{||0}}{B_0} -
\frac{1}{\mu_0}\nabla\_\perp^2\psi\right) \nonumber \\ &+&
\frac{1}{\rho}{\mathbf{b}}\_0\times{\mathbf{\kappa}}\_0\cdot\nabla P \\
{\mathbf{v}}\_E &=&
\frac{1}{B_0}{\mathbf{b}}\_0\times\nabla\phi\end{aligned}\end{split}\\

</div>

The Jacobian of this system is therefore:

<div id="equation-eq-mhdjacobian" class="math notranslate nohighlight">

<span class="eqno">(191)<a href="#equation-eq-mhdjacobian" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\mathbb{J}
= \left\[ \begin{array}{c|c|c} \color{blue}{-{\mathbf{v}}\_E\cdot\nabla}
& 0 & \left\[{\mathbf{b}}\_0\times\nabla\left(P_0 +
\color{blue}{P}\right)\cdot\nabla\right\]\nabla\_\perp^{-2} \\ \hline 0
& \color{blue}{-{\mathbf{v}}\_E\cdot\nabla} &
\left({\mathbf{b}}\_0\cdot\nabla\right)\nabla\_\perp^{-2} \\ \hline
2{\mathbf{b}}\_0\times{\mathbf{\kappa}}\_0\cdot\nabla&
-\frac{B_0^2}{\mu_0\rho}\left({\mathbf{b}}\_0
\color{blue}{-{\mathbf{b}}\_0\times\nabla\psi}\right)\cdot\nabla\nabla\_\perp^2&
\color{blue}{-{\mathbf{v}}\_E\cdot\nabla} \\ & +
\frac{B_0^2}{\rho}\left\[{\mathbf{b}}\_0\times\nabla\left(\frac{J\_{||0}}{B_0}\right)\right\]\cdot\nabla
& \\ & +
\color{blue}{\frac{B_0^2}{\mu_0\rho}\nabla\left(\nabla\_\perp^2\psi\right)\cdot\left({\mathbf{b}}\_0\times\nabla\right)}
& \end{array}\right\]\end{split}\\

</div>

Where the blue terms are only included in nonlinear simulations.

This Jacobian has large dense blocks because of the Laplacian inversion
terms (involving
<span class="math notranslate nohighlight">\\\nabla\_\perp^{-2}\\</span>
which couples together all points in an X-Z plane. The way to make
<span class="math notranslate nohighlight">\\{\mathbb{J}}\\</span>
sparse is to solve
<span class="math notranslate nohighlight">\\\phi\\</span> as a
constraint (using e.g. the IDA solver) which moves the Laplacian
inversion to the preconditioner.

</div>

<div id="solving-phi-as-a-constraint" class="section">

### Solving <span class="math notranslate nohighlight">\\\phi\\</span> as a constraint<a href="#solving-phi-as-a-constraint" class="headerlink"
title="Permalink to this heading">#</a>

The evolving state vector becomes

<div class="math notranslate nohighlight">

\\\begin{split}{\mathbf{f}} = \left(\begin{array}{c} P \\ \psi \\ U \\
\phi \end{array}\right)\end{split}\\

</div>

</div>

<div id="uedge-equations" class="section">

### UEDGE equations<a href="#uedge-equations" class="headerlink"
title="Permalink to this heading">#</a>

The UEDGE benchmark is a 4-field model with the following equations:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\frac{\partial N_i}{\partial t}} +
{V\_{||}}\partial\_{||}N_i &=&
-N_i\nabla\_{||}{V\_{||}}+\nabla\_\psi\left(D\_\perp \partial\_\psi
N_i\right) \\ {\frac{\partial \left(N_i{V\_{||}}\right)}{\partial t}} +
{V\_{||}}\partial\_{||}\left(N_i{V\_{||}}\right) &=& -\partial\_{||}P +
\nabla\_\psi\left(N_i\mu\_\perp\partial\_\psi{V\_{||}}\right) \\
\frac{3}{2}{\frac{\partial }{\partial t}}\left(N_iT_e\right) &=&
\nabla\_{||}\left(\kappa_e\partial\_{||}T_e\right) +
\nabla\_\psi\left(N_i\chi\_\perp\partial\_\perp T_e\right) \\
\frac{3}{2}{\frac{\partial }{\partial t}}\left(N_iT_i\right) &=&
\nabla\_{||}\left(\kappa_i\partial\_{||}T_i\right) +
\nabla\_\psi\left(N_i\chi\_\perp\partial\_\perp
T_i\right)\end{aligned}\end{split}\\

</div>

This set of equations is good in that there is no inversion needed, and
so the Jacobian is sparse everywhere. The state vector is

<div class="math notranslate nohighlight">

\\\begin{split}{\mathbf{f}} = \left(\begin{array}{c} N_i \\ {V\_{||}}\\
T_e \\ T_i \\ \end{array}\right)\end{split}\\

</div>

The Jacobian is:

<div class="math notranslate nohighlight">

\\\begin{split}\mathbb{J} = \left( \begin{array}{c|c|c|c}
-{V\_{||}}\partial\_{||} - \nabla\_{||}{V\_{||}}+ \nabla\_\psi
D\_\perp\partial\_\psi & -\partial\_{||}N_i - N_i\nabla\_{||} & 0 & 0 \\
-\frac{1}{N_i}{\frac{\partial {V\_{||}}}{\partial t}} -
\frac{1}{N_i}{V\_{||}}{\mathbb{J}}\_{N_iN_i} & & &
\end{array}\right)\end{split}\\

</div>

If instead the state vector is

<div class="math notranslate nohighlight">

\\\begin{split}{\mathbf{f}} = \left(\begin{array}{c} N_i \\
N_i{V\_{||}}\\ N_iT_e \\ N_iT_i \\ \end{array}\right)\end{split}\\

</div>

then the Jacobian is

</div>

<div id="fluid-turbulence" class="section">

### 2-fluid turbulence<a href="#fluid-turbulence" class="headerlink"
title="Permalink to this heading">#</a>

</div>

</div>

<div id="jacobian-vector-multiply" class="section">

## Jacobian-vector multiply<a href="#jacobian-vector-multiply" class="headerlink"
title="Permalink to this heading">#</a>

This is currently implemented into the CVODE (SUNDIALS) solver.

</div>

<div id="preconditioner-vector-multiply" class="section">

## Preconditioner-vector multiply<a href="#preconditioner-vector-multiply" class="headerlink"
title="Permalink to this heading">#</a>

<div id="reduced-3-field-mhd-1" class="section">

<span id="id1"></span>

### Reduced 3-field MHD<a href="#reduced-3-field-mhd-1" class="headerlink"
title="Permalink to this heading">#</a>

The matrix
<span class="math notranslate nohighlight">\\\mathbb{M}\\</span> to be
inverted can therefore be written

<div class="math notranslate nohighlight">

\\\begin{split}\mathbb{M} = \left\[ \begin{array}{ccc} \mathbb{D} & 0 &
\mathbb{U}\_P \\ 0 & \mathbb{D} & \mathbb{U}\_\psi \\ \mathbb{L}\_P &
\mathbb{L}\_\psi & \mathbb{D} \end{array}\right\]\end{split}\\

</div>

where

<div class="math notranslate nohighlight">

\\\mathbb{D} = \mathbb{I} \color{blue}{+
\gamma{\mathbf{v}}\_E\cdot\nabla}\\

</div>

For small flow velocities, the inverse of
<span class="math notranslate nohighlight">\\\mathbb{D}\\</span> can be
approximated using the Binomial theorem:

<div id="equation-eq-dapprox" class="math notranslate nohighlight">

<span class="eqno">(192)<a href="#equation-eq-dapprox" class="headerlink"
title="Permalink to this equation">#</a></span>\\\mathbb{D}^{-1} \simeq
\mathbb{I} \color{blue}{- \gamma{\mathbf{v}}\_E\cdot\nabla}\\

</div>

Following <a href="#chacon-2008" id="id2"
class="reference internal"><span>[chacon-2008]</span></a>,
<a href="#chacon-2002" id="id3"
class="reference internal"><span>[chacon-2002]</span></a>,
<span class="math notranslate nohighlight">\\\mathbb{M}\\</span> can be
re-written as

<div class="math notranslate nohighlight">

\\\begin{split}\mathbb{M} = \left\[ \begin{array}{cc} \mathbb{E} &
\mathbb{U} \\ \mathbb{L} & \mathbb{D} \end{array}\right\] \qquad
\mathbb{E} = \left\[ \begin{array}{cc} \mathbb{D} & 0 \\ 0 & \mathbb{D}
\end{array}\right\] \qquad \mathbb{U} = \left(\begin{array}{c}
\mathbb{U}\_P \\ \mathbb{U}\_\psi \end{array}\right) \qquad \mathbb{L} =
\left(\mathbb{L}\_P \quad \mathbb{L}\_\psi\right)\end{split}\\

</div>

The Schur factorization of
<span class="math notranslate nohighlight">\\\mathbb{M}\\</span> yields
(<a href="#chacon-2008" id="id4"
class="reference internal"><span>[chacon-2008]</span></a>)

<div class="math notranslate nohighlight">

\\\begin{split}\mathbb{M}^{-1} = \left\[ \begin{array}{cc} \mathbb{E} &
\mathbb{U} \\ \mathbb{L} & \mathbb{D} \end{array}\right\]^{-1} = \left\[
\begin{array}{cc} \mathbb{I} & -\mathbb{E}^{-1}\mathbb{U} \\ 0 &
\mathbb{I} \end{array}\right\] \left\[ \begin{array}{cc} \mathbb{E}^{-1}
& 0 \\ 0 & \mathbb{P}\_{Schur}^{-1} \end{array}\right\] \left\[
\begin{array}{cc} \mathbb{I} & 0 \\ -\mathbb{L}\mathbb{E}^{-1} &
\mathbb{I} \end{array}\right\]\end{split}\\

</div>

Where <span class="math notranslate nohighlight">\\\mathbb{P}\_{Schur} =
\mathbb{D} - \mathbb{L}\mathbb{E}^{-1}\mathbb{U}\\</span> is the Schur
complement. Note that this inversion is exact so far. Since
<span class="math notranslate nohighlight">\\\mathbb{E}\\</span> is
block-diagonal, and
<span class="math notranslate nohighlight">\\\mathbb{D}\\</span> can be
easily approximated using equation
<a href="#equation-eq-dapprox" class="reference internal">(192)</a>,
this simplifies the problem to inverting
<span class="math notranslate nohighlight">\\\mathbb{P}\_{Schur}\\</span>,
which is much smaller than
<span class="math notranslate nohighlight">\\\mathbb{M}\\</span>.

A possible approximation to
<span class="math notranslate nohighlight">\\\mathbb{P}\_{Schur}\\</span>
is to neglect:

- All drive terms

  - the curvature term
    <span class="math notranslate nohighlight">\\\mathbb{L}\_P\\</span>

  - the <span class="math notranslate nohighlight">\\J\_{||0}\\</span>
    term in
    <span class="math notranslate nohighlight">\\\mathbb{L}\_\psi\\</span>

- All nonlinear terms (blue terms in equation
  <a href="#equation-eq-mhdjacobian" class="reference internal">(191)</a>),
  including perpendicular terms (so
  <span class="math notranslate nohighlight">\\\mathbb{D} =
  \mathbb{I}\\</span>)

This gives

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} \mathbb{P}\_{Schur} &\simeq& \mathbb{I} +
\gamma^2
\frac{B_0^2}{\mu_0\rho}\left({\mathbf{b}}\_0\cdot\nabla\right)\nabla\_\perp^2\left({\mathbf{b}}\_0\cdot\nabla\right)\nabla\_\perp^{-2}
\nonumber \\ &\simeq& \mathbb{I} + \gamma^2 V_A^2
\left({\mathbf{b}}\_0\cdot\nabla\right)^2\end{aligned}\end{split}\\

</div>

Where the commutation of parallel and perpendicular derivatives is also
an approximation. This remaining term is just the shear Alfvén wave
propagating along field-lines, the fastest wave supported by these
equations.

</div>

</div>

<div id="stencils" class="section">

## Stencils<a href="#stencils" class="headerlink"
title="Permalink to this heading">#</a>

</div>

<div id="jacobian-calculation" class="section">

## Jacobian calculation<a href="#jacobian-calculation" class="headerlink"
title="Permalink to this heading">#</a>

The (sparse) Jacobian matrix elements can be calculated automatically
from the physics code by keeping track of the (linearised) operations
going through the RHS function.

For each point, keep the value (as usual), plus the non-zero elements in
that row of
<span class="math notranslate nohighlight">\\{\mathbb{J}}\\</span> and
the constant: result = Ax + b Keep track of elements using product rule.

<div class="highlight-cpp notranslate">

<div class="highlight">

    class Field3D {
      data[ngx][ngy][ngz]; // The data as now

      int JacIndex; // Variable index in Jacobian
      SparseMatrix *jac; // Set of rows for indices (JacIndex,*,*,*)
    };

</div>

</div>

JacIndex is set by the solver, so for the system

<div class="math notranslate nohighlight">

\\\begin{split}{\mathbf{f}} = \left(\begin{array}{c} P \\ \psi \\ U
\end{array}\right)\end{split}\\

</div>

<span class="pre">`P.JacIndex`</span>` `<span class="pre">`=`</span>` `<span class="pre">`0`</span>,
<span class="pre">`psi.JacIndex`</span>` `<span class="pre">`=`</span>` `<span class="pre">`1`</span>
and
<span class="pre">`U.JacIndex`</span>` `<span class="pre">`=`</span>` `<span class="pre">`2`</span>.
All other fields are given
<span class="pre">`JacIndex`</span>` `<span class="pre">`=`</span>` `<span class="pre">`-1`</span>.

SparseMatrix stores the non-zero Jacobian components for the set of rows
corresponding to this variable. Evolving variables do not have an
associated <span class="pre">`SparseMatrix`</span> object, but any
fields which result from operations on evolving fields will have one.

<div class="citation-list" role="list">

<div id="chacon-2008" class="citation" role="doc-biblioentry">

<span class="label"><span class="fn-bracket">\[</span>chacon-2008<span class="fn-bracket">\]</span></span>
<span class="backrefs">(<a href="#id2" role="doc-backlink">1</a>,<a href="#id4" role="doc-backlink">2</a>)</span>

12. Chacón, An optimal, parallel, fully implicit Newton-Krylov solver
    for three-dimensional viscoresistive magnetohydrodynamics, POP,
    2008, 15, 056103

</div>

<div id="chacon-2002" class="citation" role="doc-biblioentry">

<span class="label"><span class="fn-bracket">\[</span><a href="#id3" role="doc-backlink">chacon-2002</a><span class="fn-bracket">\]</span></span>

12. Chacón, D.A. Knoll, and J.M. Finn, An Implicit, Nonlinear Reduced
    Resistive MHD Solver, JCP, 2002, 178, 15-36

</div>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="coordinates.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Field-aligned coordinates

</div>

<a href="BOUT_Gradperp_op.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Geometry and Differential Operator

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#introduction"
  class="reference internal nav-link">Introduction</a>
- <a href="#physics-problems" class="reference internal nav-link">Physics
  problems</a>
  - <a href="#resistive-drift-interchange-instability"
    class="reference internal nav-link">Resistive drift-interchange
    instability</a>
  - <a href="#reduced-3-field-mhd"
    class="reference internal nav-link">Reduced 3-field MHD</a>
  - <a href="#solving-phi-as-a-constraint"
    class="reference internal nav-link">Solving <span
    class="math notranslate nohighlight">\(\phi\)</span> as a constraint</a>
  - <a href="#uedge-equations" class="reference internal nav-link">UEDGE
    equations</a>
  - <a href="#fluid-turbulence" class="reference internal nav-link">2-fluid
    turbulence</a>
- <a href="#jacobian-vector-multiply"
  class="reference internal nav-link">Jacobian-vector multiply</a>
- <a href="#preconditioner-vector-multiply"
  class="reference internal nav-link">Preconditioner-vector multiply</a>
  - <a href="#reduced-3-field-mhd-1"
    class="reference internal nav-link">Reduced 3-field MHD</a>
- <a href="#stencils" class="reference internal nav-link">Stencils</a>
- <a href="#jacobian-calculation"
  class="reference internal nav-link">Jacobian calculation</a>

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
