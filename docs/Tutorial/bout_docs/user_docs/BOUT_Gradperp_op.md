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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/BOUT_Gradperp_op.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/BOUT_Gradperp_op.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/BOUT_Gradperp_op.rst"
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

# Geometry and Differential Operator

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#geometry" class="reference internal nav-link">Geometry</a>
- <a href="#geometry-and-differential-operators"
  class="reference internal nav-link">Geometry and Differential
  Operators</a>
  - <a href="#differential-operators"
    class="reference internal nav-link">Differential Operators</a>
  - <a
    href="#concentric-circular-cross-section-inside-the-separatrix-without-the-sol"
    class="reference internal nav-link">Concentric circular cross section
    inside the separatrix without the SOL</a>
  - <a
    href="#field-aligned-coordinates-with-theta-as-the-coordinate-along-the-field-line"
    class="reference internal nav-link">Field-aligned coordinates with <span
    class="math notranslate nohighlight">\(\theta\)</span> as the coordinate
    along the field line</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="geometry-and-differential-operator" class="section">

# Geometry and Differential Operator<a href="#geometry-and-differential-operator" class="headerlink"
title="Permalink to this heading">#</a>

Author<span class="colon">:</span>  
X. Q. Xu

<div id="geometry" class="section">

## Geometry<a href="#geometry" class="headerlink"
title="Permalink to this heading">#</a>

In a axisymmetric toroidal system, the magnetic field can be expressed
as

<div class="math notranslate nohighlight">

\\{\bf B}=I(\psi)\nabla\zeta+\nabla\zeta\times\nabla\psi,\\

</div>

where <span class="math notranslate nohighlight">\\\psi\\</span> is the
poloidal flux,
<span class="math notranslate nohighlight">\\\theta\\</span> is the
poloidal angle-like coordinate, and
<span class="math notranslate nohighlight">\\\zeta\\</span> is the
toroidal angle. Here,
<span class="math notranslate nohighlight">\\I(\psi)=RB_t\\</span>. The
two important geometrical parameters are: the curvature,
<span class="math notranslate nohighlight">\\\bf \kappa\\</span>, and
the local pitch,
<span class="math notranslate nohighlight">\\\nu(\psi,\theta)\\</span>,

<div class="math notranslate nohighlight">

\\\nu(\psi,\theta)= {I(\psi){\bf \cal J}/R^2}.\\

</div>

The local pitch
<span class="math notranslate nohighlight">\\\nu(\psi,\theta)\\</span>
is related to the MHD safety q by
<span class="math notranslate nohighlight">\\\hat
q(\psi)={2\pi}^{-1}\oint\nu(\psi,\theta) d\theta\\</span> in the closed
flux surface region, and
<span class="math notranslate nohighlight">\\\hat
q(\psi)={2\pi}^{-1}\int\_{inboard}^{outboard}\nu(\psi,\theta)
d\theta\\</span> in the scrape-off-layer. Here
<span class="math notranslate nohighlight">\\{\bf \cal
J}=(\nabla\psi\times\nabla\theta\cdot\nabla\zeta)^{-1}\\</span> is the
coordinate Jacobian,
<span class="math notranslate nohighlight">\\R\\</span> is the major
radius, and <span class="math notranslate nohighlight">\\Z\\</span> is
the vertical position.

</div>

<div id="geometry-and-differential-operators" class="section">

## Geometry and Differential Operators<a href="#geometry-and-differential-operators" class="headerlink"
title="Permalink to this heading">#</a>

In a axisymmetric toroidal system, the magnetic field can be expressed
as <span class="math notranslate nohighlight">\\{\bf
B}=I(\psi)\nabla\zeta+\nabla\zeta\times\nabla\psi\\</span>, where
<span class="math notranslate nohighlight">\\\psi\\</span> is the
poloidal flux,
<span class="math notranslate nohighlight">\\\theta\\</span> is the
poloidal angle-like coordinate, and
<span class="math notranslate nohighlight">\\\zeta\\</span> is the
toroidal angle. Here,
<span class="math notranslate nohighlight">\\I(\psi)=RB_t\\</span>. The
two important geometrical parameters are: the curvature,
<span class="math notranslate nohighlight">\\\bf \kappa\\</span>, and
the local pitch,
<span class="math notranslate nohighlight">\\\nu(\psi,\theta)\\</span>,
and <span class="math notranslate nohighlight">\\\nu(\psi,\theta)=
{I(\psi){\bf \cal J}/R^2}\\</span>. The local pitch
<span class="math notranslate nohighlight">\\\nu(\psi,\theta)\\</span>
is related to the MHD safety q by
<span class="math notranslate nohighlight">\\\hat
q(\psi)={2\pi}^{-1}\oint\nu(\psi,\theta) d\theta\\</span> in the closed
flux surface region, and
<span class="math notranslate nohighlight">\\\hat
q(\psi)={2\pi}^{-1}\int\_{inboard}^{outboard}\nu(\psi,\theta)
d\theta\\</span> in the scrape-off-layer. Here
<span class="math notranslate nohighlight">\\{\bf \cal
J}=(\nabla\psi\times\nabla\theta\cdot\nabla\zeta)^{-1}\\</span> is the
coordinate Jacobian,
<span class="math notranslate nohighlight">\\R\\</span> is the major
radius, and <span class="math notranslate nohighlight">\\Z\\</span> is
the vertical position.

<div id="differential-operators" class="section">

### Differential Operators<a href="#differential-operators" class="headerlink"
title="Permalink to this heading">#</a>

For such an axisymmetric equilibrium the metric coefficients are only
functions of <span class="math notranslate nohighlight">\\\psi\\</span>
and <span class="math notranslate nohighlight">\\\theta\\</span>. Three
spatial differential operators appear in the equations given as:
<span class="math notranslate nohighlight">\\{\bf
v_E}\cdot\nabla\_\perp\\</span>,
<span class="math notranslate nohighlight">\\\nabla\_\\\\</span> and
<span class="math notranslate nohighlight">\\\nabla\_\perp^2\\</span>.

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} \nabla\_\\&=&{\bf b_0}\cdot\nabla={1\over
{\cal J}B}{\partial\over\partial\theta}+{I\over
BR^2}{\partial\over\partial\zeta}={B_p\over
hB}{\partial\over\partial\theta}+{B_t\over
RB}{\partial\over\partial\zeta}, \\ {\cal J}\nabla^2&=&
{\partial\over\partial\psi}\left({\cal
J}J\_{11}{\partial\over\partial\psi}\right)
+{\partial\over\partial\psi}\left({\cal
J}J\_{12}{\partial\over\partial\theta}\right) \nonumber\\
&+&{\partial\over\partial\theta}\left({\cal
J}J\_{22}{\partial\over\partial\theta}\right)
+{\partial\over\partial\theta}\left({\cal
J}J\_{12}{\partial\over\partial\psi}\right) \nonumber\\ &+&{1\over
R^2}{\partial^2\over\partial\zeta^2}. \\ \nabla\_\\^2&=&{\bf
b}\_0\cdot\nabla({\bf b}\_0\cdot\nabla)={1\over {\cal
J}B}{\partial\over\partial\theta}\left({1\over {\cal
J}B}{\partial\over\partial\theta}\right) +{1\over {\cal
J}B}{\partial\over\partial\theta}\left({B_t\over
RB}{\partial\over\partial\zeta}\right) \\ &+&{B_t\over {\cal
J}RB^2}{\partial^2\over\partial\theta\partial\zeta} +\left({B_t\over
{\cal J}RB}\right)^2{\partial^2\over\partial\zeta^2}, \\
\nabla\_\perp^2\Phi&=&-\nabla\cdot\[{\bf b}\times({\bf
b}\times\nabla\Phi)\]=\nabla^2\Phi-(\nabla\cdot{\bf b})({\bf
b}\cdot\nabla\Phi)-\nabla\_\\^2\Phi\end{aligned}\end{split}\\

</div>

where the coordinate Jacobian and metric coefficients are defined as
following:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\cal
J}&=&\nabla\psi\times\nabla\theta\cdot\nabla\zeta={h\over B_p}, \\
h&=&\sqrt{Z\_\theta^2+R\_\theta^2}, \\
J\_{11}&=&|\nabla\psi|^2={R^2\over {\cal J}^2}(Z\_\theta^2+R\_\theta^2),
\\ J\_{12}&=&J\_{21}=\nabla\psi\cdot\nabla\theta=-{R^2\over {\cal
J}^2}(Z\_\theta Z\_\psi+R\_\psi R\_\theta), \\ J\_{13}&=&J\_{31}=0, \\
J\_{22}&=&|\nabla\theta|^2={R^2\over {\cal J}^2}(Z\_\psi^2+R\_\psi^2),
\\ J\_{23}&=&J\_{32}=0, \\ J\_{33}&=&|\nabla\zeta|^2={1\over
R^2}.\end{aligned}\end{split}\\

</div>

</div>

<div id="concentric-circular-cross-section-inside-the-separatrix-without-the-sol"
class="section">

### Concentric circular cross section inside the separatrix without the SOL<a
href="#concentric-circular-cross-section-inside-the-separatrix-without-the-sol"
class="headerlink" title="Permalink to this heading">#</a>

For concentric circular cross section inside the separatrix without the
SOL, the differential operators are reduced to:

<div class="math notranslate nohighlight">

\\\begin{split}R &= R_0+r\cos\theta, \\ Z &= r\sin\theta, \\ B_t &=
{B\_{t0}R_0\over R}, \\ B_p &= {1\over R}{\partial\psi\over\partial r},
\\ R\_\psi &= {\cos\theta\over RB_p}, \\ R\_\theta &= -r\sin\theta, \\
Z\_\psi &= {\sin\theta\over RB_p}, \\ Z\_\theta &= r\cos\theta, \\ {\cal
J} &= {r\over B_p}, \\ h &= r, \\ J\_{11} &= |\nabla\psi|^2=r^2B_p^2, \\
J\_{12} = J\_{21} &= \nabla\psi\cdot\nabla\theta=0,\\ J\_{13} = J\_{31}
&= 0, \\ J\_{22} &= |\nabla\theta|^2={1\over r^2}, \\ J\_{23} = J\_{32}
&= 0, \\ J\_{33} &= |\nabla\zeta|^2={1\over R^2},\\ \nabla^2 &\simeq
{1\over r}{\partial\over\partial r}\left(r{\partial\over\partial
r}\right)+{1\over r^2}{\partial^2\over\partial \theta^2}+{1\over
R^2}{\partial^2\over\partial \zeta^2}\end{split}\\

</div>

</div>

<div id="field-aligned-coordinates-with-theta-as-the-coordinate-along-the-field-line"
class="section">

### Field-aligned coordinates with <span class="math notranslate nohighlight">\\\theta\\</span> as the coordinate along the field line<a
href="#field-aligned-coordinates-with-theta-as-the-coordinate-along-the-field-line"
class="headerlink" title="Permalink to this heading">#</a>

A suitable coordinate mapping between field-aligned ballooning
coordinates (<span class="math notranslate nohighlight">\\x\\</span>,
<span class="math notranslate nohighlight">\\y\\</span>,
<span class="math notranslate nohighlight">\\z\\</span>) and the usual
flux coordinates
(<span class="math notranslate nohighlight">\\\psi\\</span>,
<span class="math notranslate nohighlight">\\\theta\\</span>,
<span class="math notranslate nohighlight">\\\zeta\\</span>) is

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} x&=&\psi-\psi_s, \nonumber \\ y&=&\theta,
\nonumber \\ z&=&\zeta-\int\_{\theta_0}^\theta
\nu(x,y)dy.\end{aligned}\end{split}\\

</div>

as shown in Fig. 1. The covering area given by the square ABCD in the
usual flux coordinates is the same as the parallelogram ABEF in the
field-aligned coordinates. The magnetic separatrix is denoted by
<span class="math notranslate nohighlight">\\\psi=\psi_s\\</span>. In
this choice of coordinates,
<span class="math notranslate nohighlight">\\x\\</span> is a flux
surface label, <span class="math notranslate nohighlight">\\y\\</span>,
the poloidal angle, is also the coordinate along the field line, and
<span class="math notranslate nohighlight">\\z\\</span> is a field line
label within the flux surface.

The coordinate Jacobian and metric coefficients are defined as
following:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\cal
J}&=&\nabla\psi\times\nabla\theta\cdot\nabla\zeta={h\over B_p}, \\
h&=&\sqrt{Z\_\theta^2+R\_\theta^2}, \\ {\cal J}\_{11}&=&|\nabla
x|^2={R^2\over {\cal J}^2}(Z\_\theta^2+R\_\theta^2), \\ {\cal
J}\_{12}&=&{\cal J}\_{21}=\nabla x\cdot\nabla y=-{R^2\over {\cal
J}^2}(Z\_\theta Z\_\psi+R\_\psi R\_\theta), \\ {\cal J}\_{22}&=&|\nabla
y|^2={R^2\over {\cal J}^2}(Z\_\psi^2+R\_\psi^2), \\ {\cal
J}\_{13}&=&{\cal J}\_{31}=\nabla x\cdot\nabla z=-\nu\nabla x\cdot\nabla
y-|\nabla x|^2\left(\int\_{y_0}^y {\partial
\nu(x,y)\over\partial\psi}dy\right)=-|\nabla x|^2I_s, \\ {\cal
J}\_{23}&=&{\cal J}\_{32}=\nabla y\cdot\nabla z=-\nu|\nabla
y|^2-\nu\nabla x\cdot\nabla y\left(\int\_{y_0}^y {\partial
\nu(x,y)\over\partial\psi}dy\right), \\ {\cal J}\_{33}&=&|\nabla
z|^2=\left |\nabla\zeta-\nu\nabla \theta-\nabla\psi\left(\int\_{y_0}^y
{\partial \nu(x,y)\over\partial\psi}dy\right)\right |^2, \\ I_s &=&
{{\cal J}\_{12}\over|\nabla\psi|^2}\nu(x,y)+\left(\int\_{y_0}^y
{\partial \nu(x,y)\over\partial\psi}dy\right).\end{aligned}\end{split}\\

</div>

Here <span class="math notranslate nohighlight">\\h\\</span> is the
local minor radius,
<span class="math notranslate nohighlight">\\I_s\\</span> is the
integrated local shear, and
<span class="math notranslate nohighlight">\\y_0\\</span> is an
arbitrary integration parameter, which, depending on the choice of
Jacobian, determines the location where
<span class="math notranslate nohighlight">\\I_s=0\\</span>. The
disadvantage of this choice of coordinates is that the Jacobian diverges
near the X-point as
<span class="math notranslate nohighlight">\\B_p\rightarrow 0\\</span>
and its effect spreads over the entire flux surafces near the separatrix
as the results of coordinate transform
<span class="math notranslate nohighlight">\\z\\</span>. Therefore a
better set of coordinates is needed for X-point divertor geometry. The
derivatives are obtained from the chain rule as follows:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {d\over d\psi}&=&{\partial\over \partial
x} - \left(\int\_{y_0}^y {\partial
\nu(x,y)\over\partial\psi}dy\right){\partial\over \partial z}, \\
{d\over d\theta}&=&{\partial\over \partial y} - \nu(x,y){\partial\over
\partial z}, \\ {d\over d\zeta}&=&{\partial\over \partial
z}.\end{aligned}\end{split}\\

</div>

In the field-aligned ballooning coordinates, the parallel differential
operator is simple, involving only one coordinate
<span class="math notranslate nohighlight">\\y\\</span>

<div class="math notranslate nohighlight">

\\\begin{aligned} \partial\_\\^0 &=& {\bf
b}\_0\cdot\nabla\_\\=\left({B_p\over hB}\right){\partial\over\partial
y}.\end{aligned}\\

</div>

which requires a few grid points. The total axisymmetric drift operator
becomes

The perturbed <span class="math notranslate nohighlight">\\{\bf E}\times
{\bf B}\\</span> drift operator becomes

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\delta\bf v_E}\cdot\nabla\_\perp&=&
{c\over BB\_\\^\*}\left\\ -{I\over
J}{\partial\langle\delta\phi\rangle\over\partial\theta} +{B_p^2}
{\partial\langle\delta\phi\rangle\over\partial z}
\right\\{\partial\over\partial\psi} \nonumber\\ &+&{c\over
BB\_\\^\*}\left\\{I\over{\cal J}}
{\partial\langle\delta\phi\rangle\over\partial\psi} +{{\cal
J}\_{12}\over R^2} {\partial\langle\delta\phi\rangle\over\partial z}
\right\\{\partial\over\partial\theta} \nonumber\\ &-&{c\over
BB\_\\^\*}\left\\B_p^2
{\partial\langle\delta\phi\rangle\over\partial\psi} +{{\cal
J}\_{12}\over R^2} {\partial\langle\delta\phi\rangle\over\partial\theta}
\right\\{\partial\over\partial z},\end{aligned}\end{split}\\

</div>

when the conventional turbulence ordering
(<span class="math notranslate nohighlight">\\k\_\\\ll
k\_\perp\\</span>) is used, the perturbed
<span class="math notranslate nohighlight">\\{\bf E}\times {\bf
B}\\</span> drift operator can be further reduced to a simple form

<div class="math notranslate nohighlight">

\\\begin{aligned} {\delta\bf v_E}\cdot\nabla\_\perp&=& {cB\over
B\_\\^\*}\left( {\partial\langle\delta\phi\rangle\over\partial
z}{\partial\over\partial x}
-{\partial\langle\delta\phi\rangle\over\partial x}{\partial\over\partial
z}\right)\end{aligned}\\

</div>

where
<span class="math notranslate nohighlight">\\\partial/\partial\theta\simeq
-\nu\partial/\partial z\\</span> is used. In the perturbed
<span class="math notranslate nohighlight">\\{\bf E}\times {\bf
B}\\</span> drift operator the poloidal and radial derivatives are
written in the usual flux
<span class="math notranslate nohighlight">\\(\psi,\theta,\zeta)\\</span>
coordinates in order to have various options for valid discretizations.
The general Laplacian operator for potential is

<div class="math notranslate nohighlight">

\\ \begin{align}\begin{aligned}\begin{split} \begin{aligned} {\cal
J}\nabla^2\Phi&=&{\partial\over\partial x}\left({\cal J}{\cal
J}\_{11}{\partial\Phi\over\partial x} +{\cal J}{\cal
J}\_{12}{\partial\Phi\over\partial y} +{\cal J}{\cal
J}\_{13}{\partial\Phi\over\partial z}\right) \nonumber\\
&+&{\partial\over\partial y}\left({\cal J}{\cal
J}\_{21}{\partial\Phi\over\partial x} +{\cal J}{\cal
J}\_{22}{\partial\Phi\over\partial y} +{\cal J}{\cal
J}\_{23}{\partial\Phi\over\partial z}\right) \nonumber\\
&+&{\partial\over\partial z}\left({\cal J}{\cal
J}\_{31}{\partial\Phi\over\partial x} +{\cal J}{\cal
J}\_{32}{\partial\Phi\over\partial y} +{\cal J}{\cal
J}\_{33}{\partial\Phi\over\partial
z}\right).\end{aligned}\end{split}\\The general perpendicular Laplacian
operator for potential is\end{aligned}\end{align} \\

</div>

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\cal
J}\nabla\_\perp^2\Phi&=&{\partial\over\partial x}\left({\cal J}{\cal
J}\_{11}{\partial\Phi\over\partial x} +{\cal J}{\cal
J}\_{12}{\partial\Phi\over\partial y} +{\cal J}{\cal
J}\_{13}{\partial\Phi\over\partial z}\right) \nonumber\\
&+&{\partial\over\partial y}\left({\cal J}{\cal
J}\_{21}{\partial\Phi\over\partial x} +{\cal J}{\cal
J}\_{22}{\partial\Phi\over\partial y} +{\cal J}{\cal
J}\_{23}{\partial\Phi\over\partial z}\right) \nonumber\\
&+&{\partial\over\partial z}\left({\cal J}{\cal
J}\_{31}{\partial\Phi\over\partial x} +{\cal J}{\cal
J}\_{32}{\partial\Phi\over\partial y} +{\cal J}{\cal
J}\_{33}{\partial\Phi\over\partial z}\right) \nonumber\\
&-&\left({B_p\over hB}\right){\partial\over\partial y}
\left\[\left({B_p\over hB}\right){\partial\Phi\over\partial y}\right\]
\nonumber\\ &-&\left({B_p\over hB}\right)^2{\partial\ln B\over\partial
y}{\partial\Phi\over\partial y}.\end{aligned}\end{split}\\

</div>

The general perpendicular Laplacian operator for axisymmetric potential
<span class="math notranslate nohighlight">\\\Phi_0(x,y)\\</span> is

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\cal
J}\nabla\_\perp^2\Phi_0&=&{\partial\over\partial x}\left({\cal J}{\cal
J}\_{11}{\partial\Phi_0\over\partial x} +{\cal J}{\cal
J}\_{12}{\partial\Phi_0\over\partial y}\right) \nonumber\\
&+&{\partial\over\partial y}\left({\cal J}{\cal
J}\_{21}{\partial\Phi_0\over\partial x} +{\cal J}{\cal
J}\_{22}{\partial\Phi_0\over\partial y}\right) \nonumber\\
&-&\left({B_p\over hB}\right){\partial\over\partial y}
\left\[\left({B_p\over hB}\right){\partial\Phi_0\over\partial y}\right\]
\nonumber\\ &-&\left({B_p\over hB}\right)^2{\partial\ln B\over\partial
y}{\partial\Phi\over\partial y}.\end{aligned}\end{split}\\

</div>

For the perturbed potential
<span class="math notranslate nohighlight">\\\delta\phi\\</span>, we can
drop the <span class="math notranslate nohighlight">\\\partial/\partial
y\\</span> terms in Eq. (69) due to the elongated nature of the
turbulence
(<span class="math notranslate nohighlight">\\k\_\\/k\_\perp\ll1\\</span>).
The general perpendicular Laplacian operator for perturbed potential
<span class="math notranslate nohighlight">\\\delta\phi\\</span> reduces
to

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\cal J}\nabla\_\perp^2\delta\phi&=&
{\partial\over\partial x}\left({\cal J}{\cal
J}\_{11}{\partial\delta\phi\over\partial x} +{\cal J}{\cal
J}\_{13}{\partial\delta\phi\over\partial z}\right) \nonumber\\
&+&{\partial\over\partial z}\left({\cal J}{\cal
J}\_{31}{\partial\delta\phi\over\partial x} +{\cal J}{\cal
J}\_{33}{\partial\delta\phi\over\partial
z}\right).\end{aligned}\end{split}\\

</div>

If the non-split potential
<span class="math notranslate nohighlight">\\\Phi\\</span> is a
preferred option, the gyrokinetic Poisson equation (18) and the general
perpendicular Laplacian operator Eq. (69) have to be used. Then the
assumption
<span class="math notranslate nohighlight">\\k\_\\/k\_\perp\ll1\\</span>
is not used to simplify the perpendicular Laplacian operator.

</div>

</div>

</div>

<div class="prev-next-area">

<a href="preconditioning.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

BOUT++ preconditioning

</div>

<a href="../developer_docs/contributing.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Contributing to BOUT++

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#geometry" class="reference internal nav-link">Geometry</a>
- <a href="#geometry-and-differential-operators"
  class="reference internal nav-link">Geometry and Differential
  Operators</a>
  - <a href="#differential-operators"
    class="reference internal nav-link">Differential Operators</a>
  - <a
    href="#concentric-circular-cross-section-inside-the-separatrix-without-the-sol"
    class="reference internal nav-link">Concentric circular cross section
    inside the separatrix without the SOL</a>
  - <a
    href="#field-aligned-coordinates-with-theta-as-the-coordinate-along-the-field-line"
    class="reference internal nav-link">Field-aligned coordinates with <span
    class="math notranslate nohighlight">\(\theta\)</span> as the coordinate
    along the field line</a>

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
