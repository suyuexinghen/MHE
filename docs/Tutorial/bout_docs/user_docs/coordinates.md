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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/coordinates.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/coordinates.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/coordinates.rst"
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

# Field-aligned coordinates

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#introduction"
  class="reference internal nav-link">Introduction</a>
- <a href="#orthogonal-toroidal-coordinates"
  class="reference internal nav-link">Orthogonal toroidal coordinates</a>
- <a href="#id1" class="reference internal nav-link">Field-aligned
  coordinates</a>
  - <a href="#magnetic-field" class="reference internal nav-link">Magnetic
    field</a>
  - <a href="#jacobian-and-metric-tensors"
    class="reference internal nav-link">Jacobian and metric tensors</a>
  - <a href="#zshift" class="reference internal nav-link">zShift</a>
  - <a href="#transform-back-to-cartesian"
    class="reference internal nav-link">Transform back to Cartesian</a>
- <a href="#right-handed-field-aligned-coordinates"
  class="reference internal nav-link">Right-handed field-aligned
  coordinates</a>
- <a href="#differential-operators-in-field-aligned-coordinates"
  class="reference internal nav-link">Differential operators in
  field-aligned coordinates</a>
  - <a href="#j-x-b-in-field-aligned-coordinates"
    class="reference internal nav-link">J x B in field-aligned
    coordinates</a>
  - <a href="#parallel-current" class="reference internal nav-link">Parallel
    current</a>
  - <a href="#curvature" class="reference internal nav-link">Curvature</a>
  - <a href="#curvature-from-nabla-times-left-frac-boldsymbol-b-b-right"
    class="reference internal nav-link">Curvature from <span
    class="math notranslate nohighlight">\({\nabla\times\left(\frac{\boldsymbol{b}}{B}\right)}\)</span></a>
  - <a href="#curvature-of-a-single-line"
    class="reference internal nav-link">Curvature of a single line</a>
  - <a href="#curvature-in-toroidal-coordinates"
    class="reference internal nav-link">Curvature in toroidal
    coordinates</a>
  - <a href="#psi-derivative-of-the-b-field"
    class="reference internal nav-link">psi derivative of the B field</a>
  - <a href="#parallel-derivative-of-the-b-field"
    class="reference internal nav-link">Parallel derivative of the B
    field</a>
  - <a href="#magnetic-shear-from-j-x-b"
    class="reference internal nav-link">Magnetic shear from J x B</a>
  - <a href="#magnetic-shear" class="reference internal nav-link">Magnetic
    shear</a>
  - <a href="#psi-derivative-of-h" class="reference internal nav-link">psi
    derivative of h</a>
- <a href="#shifted-radial-derivatives"
  class="reference internal nav-link">Shifted radial derivatives</a>
  - <a href="#perpendicular-laplacian"
    class="reference internal nav-link">Perpendicular Laplacian</a>
    - <a href="#in-orthogonal-psi-theta-zeta-flux-coordinates"
      class="reference internal nav-link">In orthogonal (psi, theta, zeta)
      flux coordinates</a>
  - <a href="#operator-b-x-nabla-phi-dot-nabla-a"
    class="reference internal nav-link">Operator B x Nabla Phi Dot Nabla
    A</a>
- <a href="#useful-identities" class="reference internal nav-link">Useful
  identities</a>
  - <a
    href="#mathbf-b-times-mathbf-kappa-cdot-nabla-psi-simeq-rb-zeta-partial-ln-b"
    class="reference internal nav-link"><span
    class="math notranslate nohighlight">\(\mathbf{b}\times\mathbf{\kappa}\cdot\nabla\psi
    \simeq -RB_\zeta\partial_{||}\ln B\)</span></a>
- <a href="#differential-geometry"
  class="reference internal nav-link">Differential geometry</a>
- <a href="#derivation-of-operators-in-the-bout-clebsch-system"
  class="reference internal nav-link">Derivation of operators in the
  BOUT++ Clebsch system</a>
  - <a href="#the-parallel-and-perpendicular-gradients"
    class="reference internal nav-link">The parallel and perpendicular
    gradients</a>
    - <a href="#the-perpendicular-gradients-in-laplacian-inversion"
      class="reference internal nav-link">The perpendicular gradients in
      Laplacian inversion</a>
  - <a href="#the-laplacian" class="reference internal nav-link">The
    Laplacian</a>
  - <a href="#the-parallel-laplacian"
    class="reference internal nav-link">The parallel Laplacian</a>
  - <a href="#the-perpendicular-laplacian"
    class="reference internal nav-link">The perpendicular Laplacian</a>
    - <a href="#the-perpendicular-laplacian-in-laplacian-inversion"
      class="reference internal nav-link">The perpendicular Laplacian in
      Laplacian inversion</a>
    - <a href="#the-perpendicular-laplacian-in-divergence-form"
      class="reference internal nav-link">The perpendicular Laplacian in
      divergence form</a>
  - <a href="#the-poisson-bracket-operator"
    class="reference internal nav-link">The Poisson bracket operator</a>
    - <a href="#the-electrostatic-exb-velocity"
      class="reference internal nav-link">The electrostatic ExB velocity</a>
    - <a href="#the-electrostatic-exb-advection"
      class="reference internal nav-link">The electrostatic ExB advection</a>
    - <a href="#the-bracket-operator-in-bout"
      class="reference internal nav-link">The bracket operator in BOUT++</a>
- <a href="#divergence-of-exb-velocity"
  class="reference internal nav-link">Divergence of ExB velocity</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="field-aligned-coordinates" class="section">

<span id="sec-field-aligned-coordinates"></span>

# Field-aligned coordinates<a href="#field-aligned-coordinates" class="headerlink"
title="Permalink to this heading">#</a>

Author<span class="colon">:</span>  
B.Dudson, John Omotani, M.V.Umansky, L.C.Wang, X.Q.Xu, L.L.LoDestro,
Department of Physics, University of York, UK; Culham Centre for Fusion
Energy, UKAEA, UK; Lawrence Livermore National Laboratory, USA; IFTS,
China

<div id="introduction" class="section">

## Introduction<a href="#introduction" class="headerlink"
title="Permalink to this heading">#</a>

This manual covers the field-aligned coordinate system used in many
BOUT++ tokamak models, and useful derivations and expressions.

</div>

<div id="orthogonal-toroidal-coordinates" class="section">

## Orthogonal toroidal coordinates<a href="#orthogonal-toroidal-coordinates" class="headerlink"
title="Permalink to this heading">#</a>

Starting with an orthogonal, right-handed toroidal coordinate system
<span class="math notranslate nohighlight">\\\left(r, \theta,
\phi\right)\\</span>.
<span class="math notranslate nohighlight">\\\theta\\</span> is the
poloidal angle (from
<span class="math notranslate nohighlight">\\0\\</span> to
<span class="math notranslate nohighlight">\\2\pi\\</span>) in the
clockwise direction in the right R-Z plane.
<span class="math notranslate nohighlight">\\\phi\\</span> is the
toroidal angle (also
<span class="math notranslate nohighlight">\\0\\</span> to
<span class="math notranslate nohighlight">\\2\pi\\</span>) going
anti-clockwise from the top of the tokamak.

We define the poloidal magnetic field
<span class="math notranslate nohighlight">\\B\_{pol}\\</span> as the
component of the magnetic field in the
<span class="math notranslate nohighlight">\\\theta\\</span> direction,
and the toroidal field
<span class="math notranslate nohighlight">\\B\_\text{tor}\\</span> as
the component of the magnetic field in the
<span class="math notranslate nohighlight">\\\phi\\</span> direction.

We now introduce the poloidal flux
<span class="math notranslate nohighlight">\\\psi\\</span> as the new
radial coordinate. If the poloidal magnetic field
<span class="math notranslate nohighlight">\\B\_\text{pol}\\</span> is
positive then <span class="math notranslate nohighlight">\\\psi\\</span>
increases with radius; if
<span class="math notranslate nohighlight">\\B\_\text{pol}\\</span> is
negative then <span class="math notranslate nohighlight">\\\psi\\</span>
decreases with radius. To keep the coordinate system right-handed, we
define a new toroidal coordinate
<span class="math notranslate nohighlight">\\\zeta\\</span> which is
defined as <span class="math notranslate nohighlight">\\\zeta =
\sigma\_{B\text{pol}}\phi\\</span>, where the sign of the poloidal
magnetic field is
<span class="math notranslate nohighlight">\\\sigma\_{B\text{pol}}
\equiv {B\_{\text{pol}}}/ \left|{B\_{\text{pol}}}\right|\\</span>. If
<span class="math notranslate nohighlight">\\B\_\text{pol} \> 0\\</span>
then <span class="math notranslate nohighlight">\\\zeta\\</span> is
anti-clockwise looking down from above the tokamak, and if
<span class="math notranslate nohighlight">\\B\_\text{pol} \< 0\\</span>
then <span class="math notranslate nohighlight">\\\zeta\\</span> is
clockwise. This coordinate system
<span class="math notranslate nohighlight">\\\left(\psi, \theta,
\zeta\right)\\</span> is orthogonal and right-handed.

The magnitudes of the basis vectors are

<div id="equation-eq-psithetazetabasisvectors"
class="math notranslate nohighlight">

<span class="eqno">(11)<a href="#equation-eq-psithetazetabasisvectors" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\left|{\boldsymbol{e}}\_\psi\right| =
\frac{1}{R\left|{B\_{\text{pol}}}\right|} \qquad
\left|\boldsymbol{e}\_\theta\right| = {h\_\theta} \qquad
\left|\boldsymbol{e}\_\zeta\right| = R \end{aligned}\\

</div>

where <span class="math notranslate nohighlight">\\{h\_\theta}\\</span>
is the poloidal arc length per radian. The non-zero covariant metric
coefficients are

<div id="equation-eq-psithetazetacovariantmetric"
class="math notranslate nohighlight">

<span class="eqno">(12)<a href="#equation-eq-psithetazetacovariantmetric" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
g\_{\psi\psi} = \frac{1}{\left(R\left|{B\_{\text{pol}}}\right|\right)^2}
\qquad g\_{\theta\theta} = h\_\theta^2 \qquad g\_{\zeta\zeta} =
R^2\end{aligned}\\

</div>

and the magnitudes of the reciprocal vectors are therefore

<div id="equation-eq-psithetazetareciprocalvectors"
class="math notranslate nohighlight">

<span class="eqno">(13)<a href="#equation-eq-psithetazetareciprocalvectors" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\left|\nabla\psi\right| = R\left|{B\_{\text{pol}}}\right| \qquad
\left|\nabla\theta\right| = \frac{1}{h\_\theta} \qquad
\left|\nabla\zeta\right| = \frac{1}{R}\end{aligned}\\

</div>

The cross products are:

<div id="equation-eq-psithetazetacrossproducts"
class="math notranslate nohighlight">

<span class="eqno">(14)<a href="#equation-eq-psithetazetacrossproducts" class="headerlink"
title="Permalink to this equation">#</a></span>\\\boldsymbol{e}\_\psi\times\boldsymbol{e}\_\theta
= J\_{\psi\theta\zeta} \nabla\zeta \qquad
\boldsymbol{e}\_\psi\times\boldsymbol{e}\_\zeta = -J\_{\psi\theta\zeta}
\nabla\theta \qquad \boldsymbol{e}\_\theta\times\boldsymbol{e}\_\zeta =
J\_{\psi\theta\zeta} \nabla\psi\\

</div>

where <span class="math notranslate nohighlight">\\J\_{\psi\theta\zeta}
= h\_\theta / \left|{B\_{\text{pol}}}\right|\\</span> is the Jacobian,
which is always positive. Similarly,

<div id="equation-eq-psithetazetareciprocalcrossproducts"
class="math notranslate nohighlight">

<span class="eqno">(15)<a href="#equation-eq-psithetazetareciprocalcrossproducts"
class="headerlink" title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\psi \times \nabla\theta = \frac{1}{J\_{\psi\theta\zeta}}
\boldsymbol{e}\_\zeta \qquad \nabla\psi \times \nabla\zeta = -
\frac{1}{J\_{\psi\theta\zeta}} \boldsymbol{e}\_\theta \qquad
\nabla\theta \times \nabla\zeta = \frac{1}{J\_{\psi\theta\zeta}}
\boldsymbol{e}\_\psi \end{aligned}\\

</div>

The magnetic field
<span class="math notranslate nohighlight">\\{\boldsymbol{B}}\\</span>
can be expressed as

<div id="equation-eq-psithetazetabcomponents"
class="math notranslate nohighlight">

<span class="eqno">(16)<a href="#equation-eq-psithetazetabcomponents" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{B}}=& B\_{\text{pol}}
\frac{\boldsymbol{e}\_\theta}{h\_\theta} + B\_{\text{tor}}
\frac{\boldsymbol{e}\_\phi}{R} \\ =&
{B\_{\text{pol}}}\hat{{\boldsymbol{e}}}\_\theta +
{B\_{\text{tor}}}\hat{{\boldsymbol{e}}}\_\phi\end{aligned}\end{split}\\

</div>

where the hats on the basis vectors indicate unit directions e.g.
<span class="math notranslate nohighlight">\\\hat{{\boldsymbol{e}}}\_\theta
= {\boldsymbol{e}}\_\theta /
\left|{\boldsymbol{e}}\_\theta\right|\\</span>.

</div>

<div id="id1" class="section">

## Field-aligned coordinates<a href="#id1" class="headerlink"
title="Permalink to this heading">#</a>

In order to efficiently simulate (predominantly) field-aligned
structures, the standard coordinate system used by BOUT++ models is a
Clebsch system where grid-points are aligned to the magnetic field along
the <span class="math notranslate nohighlight">\\y\\</span> coordinate.

To align to the magnetic field we define a local field line pitch
<span class="math notranslate nohighlight">\\\nu\\</span>:

<div id="equation-eq-fieldlinepitch"
class="math notranslate nohighlight">

<span class="eqno">(17)<a href="#equation-eq-fieldlinepitch" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nu\left(\psi, \theta\right) =
\frac{{\boldsymbol{B}}\cdot\nabla\phi}{{\boldsymbol{B}}\cdot\nabla\theta}
= \frac{{B\_{\text{tor}}}{h\_\theta}}{{B\_{\text{pol}}}R}
\end{aligned}\\

</div>

The sign of the poloidal field
<span class="math notranslate nohighlight">\\{B\_{\text{pol}}}\\</span>
and toroidal field
<span class="math notranslate nohighlight">\\{B\_{\text{tor}}}\\</span>
can be either + or -.

The field-aligned coordinates
<span class="math notranslate nohighlight">\\\left(x,y,z\right)\\</span>
are defined by:

<div id="equation-eq-coordtransform"
class="math notranslate nohighlight">

<span class="eqno">(18)<a href="#equation-eq-coordtransform" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} x =
{\sigma\_{B\text{pol}}}\left(\psi - \psi_0\right) \qquad y = \theta
\qquad z = \sigma\_{B\text{pol}} \left(\phi -
\int\_{\theta_0}^{\theta}\nu\left(\psi,\theta\right)d\theta\right)
\end{aligned}\\

</div>

The coordinate system is chosen so that
<span class="math notranslate nohighlight">\\x\\</span> increases
radially outwards, from plasma to the wall. The
<span class="math notranslate nohighlight">\\y\\</span> coordinate
increases in the same direction as
<span class="math notranslate nohighlight">\\\theta\\</span> i.e.
clockwise in the right-hand poloidal plane. The
<span class="math notranslate nohighlight">\\z\\</span> coordinate
increases in the same direction as
<span class="math notranslate nohighlight">\\\zeta\\</span> i.e.
anti-clockwise looking from the top if
<span class="math notranslate nohighlight">\\B\_{pol}\>0\\</span> and
clockwise if <span class="math notranslate nohighlight">\\B\_{pol} \<
0\\</span>.

This coordinate system is right-handed if
<span class="math notranslate nohighlight">\\B\_{pol}\>0\\</span>, and
left-handed if
<span class="math notranslate nohighlight">\\B\_{pol}\<0\\</span>. The
Jacobian of this coordinate system,
<span class="math notranslate nohighlight">\\J\_{xyz} = {h\_\theta} /
{B\_{\text{pol}}}\\</span>, can therefore be positive or negative. This
therefore differs from the Jacobian for the orthogonal system above:
<span class="math notranslate nohighlight">\\J\_{xyz} =
\sigma\_{B\text{pol}} J\_{\psi\theta\zeta}\\</span>.

The reciprocal basis vectors are

<div id="equation-eq-reciprocalbasis"
class="math notranslate nohighlight">

<span class="eqno">(19)<a href="#equation-eq-reciprocalbasis" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} \nabla
x = {\sigma\_{B\text{pol}}}\nabla \psi \qquad \nabla y = \nabla \theta
\qquad \nabla z = \nabla\zeta -
\sigma\_{B\text{pol}}\left\[\int\_{\theta_0}^\theta{\frac{\partial
\nu\left(\psi,\theta\right)}{\partial \psi}} d\theta\right\]
\nabla\psi - \sigma\_{B\text{pol}}\nu\left(\psi,
\theta\right)\nabla\theta \end{aligned}\\

</div>

The term in square brackets is the integrated local shear:

<div id="equation-eq-integratedshear"
class="math notranslate nohighlight">

<span class="eqno">(20)<a href="#equation-eq-integratedshear" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} I =
\int\_{y_0}^y\frac{\partial\nu\left(x,
y\right)}{\partial\psi}dy\end{aligned}\\

</div>

The basis vectors are:

<div id="equation-eq-basisvectors" class="math notranslate nohighlight">

<span class="eqno">(21)<a href="#equation-eq-basisvectors" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\boldsymbol{e}\_x =& J\_{xyz}\left(\nabla y \times \nabla z\right) =
{\sigma\_{B\text{pol}}} {\boldsymbol{e}}\_\psi +
I{\boldsymbol{e}}\_\zeta \\ \boldsymbol{e}\_y =& J\_{xyz}\left(\nabla z
\times \nabla x\right) = {\boldsymbol{e}}\_\theta +
\nu{\boldsymbol{e}}\_\phi \\ \boldsymbol{e}\_z =& J\_{xyz}\left(\nabla x
\times \nabla y\right) = {\boldsymbol{e}}\_\zeta
\end{aligned}\end{split}\\

</div>

where
<span class="math notranslate nohighlight">\\{\boldsymbol{e}}\_\phi =
{\sigma\_{B\text{pol}}}{\boldsymbol{e}}\_\zeta\\</span> is always
anticlockwise when seen from above the tokamak looking down. The
direction of
<span class="math notranslate nohighlight">\\{\boldsymbol{e}}\_\zeta\\</span>
depends on the sign of the poloidal field
<span class="math notranslate nohighlight">\\\sigma\_{B\text{pol}}\\</span>.
Note that <span class="math notranslate nohighlight">\\J\_{xyz} =
\sigma\_{B\text{pol}} J\_{\psi\theta\zeta}\\</span>, and can be either
positive or negative.

<div id="magnetic-field" class="section">

### Magnetic field<a href="#magnetic-field" class="headerlink"
title="Permalink to this heading">#</a>

Magnetic field is given in Clebsch form by:

<div id="equation-eq-clebschb" class="math notranslate nohighlight">

<span class="eqno">(22)<a href="#equation-eq-clebschb" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{B}}= \nabla z\times \nabla x =
\frac{1}{J\_{xyz}}{\boldsymbol{e}}\_y\end{aligned}\\

</div>

The contravariant components of this are then

<div id="equation-eq-bcontravariant"
class="math notranslate nohighlight">

<span class="eqno">(23)<a href="#equation-eq-bcontravariant" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} B^y =
\frac{{B\_{\text{pol}}}}{{h\_\theta}} \qquad B^x = B^z =
0\end{aligned}\\

</div>

i.e.
<span class="math notranslate nohighlight">\\{\boldsymbol{B}}\\</span>
can be written as

<div id="equation-eq-clebschb2" class="math notranslate nohighlight">

<span class="eqno">(24)<a href="#equation-eq-clebschb2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{B}}=
\frac{{B\_{\text{pol}}}}{{h\_\theta}}{\boldsymbol{e}}\_y\end{aligned}\\

</div>

and the covariant components calculated using
<span class="math notranslate nohighlight">\\g\_{ij}\\</span> as

<div id="equation-eq-bcovariant" class="math notranslate nohighlight">

<span class="eqno">(25)<a href="#equation-eq-bcovariant" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} B_x =
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}I R \qquad B_y = \frac{B^2
{h\_\theta}}{{B\_{\text{pol}}}} \qquad B_z =
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}R\end{aligned}\\

</div>

The unit vector in the direction of equilibrium
<span class="math notranslate nohighlight">\\{\boldsymbol{B}}\\</span>
is therefore

<div id="equation-eq-bunitvector" class="math notranslate nohighlight">

<span class="eqno">(26)<a href="#equation-eq-bunitvector" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{b}} = \frac{1}{J\_{xyz}B}{\boldsymbol{e}}\_y =
\frac{1}{J\_{xyz}B}\left\[g\_{xy}\nabla x + g\_{yy}\nabla y +
g\_{yz}\nabla z\right\]\end{aligned}\\

</div>

</div>

<div id="jacobian-and-metric-tensors" class="section">

### Jacobian and metric tensors<a href="#jacobian-and-metric-tensors" class="headerlink"
title="Permalink to this heading">#</a>

The Jacobian of this coordinate system is

<div id="equation-eq-jacobian" class="math notranslate nohighlight">

<span class="eqno">(27)<a href="#equation-eq-jacobian" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
J\_{xyz}^{-1} \equiv \left(\nabla x\times\nabla y\right)\cdot\nabla z =
{B\_{\text{pol}}}/ {h\_\theta}\end{aligned}\\

</div>

which can be either positive or negative, depending on the sign of
<span class="math notranslate nohighlight">\\{B\_{\text{pol}}}\\</span>.
The contravariant metric tensor is given by:

<div id="equation-eq-contravariantmetric"
class="math notranslate nohighlight">

<span class="eqno">(28)<a href="#equation-eq-contravariantmetric" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
g^{ij} \equiv {\boldsymbol{e}}^i \cdot{\boldsymbol{e}}^j \equiv \nabla
u^i \cdot \nabla u^j = \left(% \begin{array}{ccc}
\left(R{B\_{\text{pol}}}\right)^2 & 0 &
-I\left(R{B\_{\text{pol}}}\right)^2 \\ 0 & 1 / {h\_\theta}^2 &
-{\sigma\_{B\text{pol}}}\nu / {h\_\theta}^2 \\
-I\left(R{B\_{\text{pol}}}\right)^2 & -{\sigma\_{B\text{pol}}}\nu /
{h\_\theta}^2 & I^2\left(R{B\_{\text{pol}}}\right)^2 + B^2 /
\left(R{B\_{\text{pol}}}\right)^2 \end{array} %
\right)\end{aligned}\end{split}\\

</div>

and the covariant metric tensor:

<div id="equation-eq-covariantmetric"
class="math notranslate nohighlight">

<span class="eqno">(29)<a href="#equation-eq-covariantmetric" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
g\_{ij} \equiv {\boldsymbol{e}}\_i \cdot{\boldsymbol{e}}\_j = \left(%
\begin{array}{ccc} I^2 R^2 + 1 / {\left({R{B\_{\text{pol}}}}\right)^2}&
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}{h\_\theta}I R /
{B\_{\text{pol}}}& I R^2 \\
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}{h\_\theta}I R /
{B\_{\text{pol}}}& B^2{h\_\theta}^2 / {B\_{\text{pol}}}^2 &
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}{h\_\theta}R /
{B\_{\text{pol}}}\\ I R^2 &
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}{h\_\theta}R /
{B\_{\text{pol}}}& R^2 \end{array} % \right)\end{aligned}\end{split}\\

</div>

or equivalently:

<div id="equation-eq-covariantmetric2"
class="math notranslate nohighlight">

<span class="eqno">(30)<a href="#equation-eq-covariantmetric2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
g\_{ij} = \left(% \begin{array}{ccc} I^2 R^2 + 1 /
{\left({R{B\_{\text{pol}}}}\right)^2}& {\sigma\_{B\text{pol}}} I \nu R^2
& I R^2 \\ {\sigma\_{B\text{pol}}} I \nu R^2 & J\_{xyz}^2B^2 &
{\sigma\_{B\text{pol}}} \nu R^2 \\ I R^2 & {\sigma\_{B\text{pol}}}\nu
R^2 & R^2 \end{array} % \right)\end{aligned}\end{split}\\

</div>

</div>

<div id="zshift" class="section">

### zShift<a href="#zshift" class="headerlink"
title="Permalink to this heading">#</a>

The
<span class="math notranslate nohighlight">\\\texttt{zShift}\\</span> is
used to connect grid cells along the magnetic field. It is the
<span class="math notranslate nohighlight">\\z\\</span> angle of a point
on a field line relative to a reference location:

<div id="equation-eq-zshift" class="math notranslate nohighlight">

<span class="eqno">(31)<a href="#equation-eq-zshift" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\texttt{zShift}\left(x, y\right) &= \int\_{y =
0}^{y}\frac{{\boldsymbol{B}}\cdot\nabla z}{{\boldsymbol{B}}\cdot\nabla
y} dy \\ &= \int\_{\theta =
0}^{\theta}\frac{{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}{h\_\theta}}{{B\_{\text{pol}}}R}
d\theta \\ &= {\sigma\_{B\text{pol}}} \int\_{\theta = 0}^{\theta} \nu
d\theta \end{aligned}\end{split}\\

</div>

The
<span class="math notranslate nohighlight">\\\texttt{ShiftAngle}\\</span>
is then defined as the change in
<span class="math notranslate nohighlight">\\\texttt{zShift}\\</span>
between <span class="math notranslate nohighlight">\\y=0\\</span> and
<span class="math notranslate nohighlight">\\y=2\pi\\</span>: It is the
change in the <span class="math notranslate nohighlight">\\z\\</span>
coordinate after one poloidal circuit in
<span class="math notranslate nohighlight">\\y\\</span>.

Note that
<span class="math notranslate nohighlight">\\\texttt{zShift}\\</span>
can be related to the integrated shear
<span class="math notranslate nohighlight">\\I\\</span>:

<div id="equation-eq-zshiftfromi" class="math notranslate nohighlight">

<span class="eqno">(32)<a href="#equation-eq-zshiftfromi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} I =
\int\_{y_0}^y\frac{\partial\nu\left(x, y\right)}{\partial\psi}dy =
\frac{\partial}{\partial x} \texttt{zShift} \end{aligned}\\

</div>

</div>

<div id="transform-back-to-cartesian" class="section">

### Transform back to Cartesian<a href="#transform-back-to-cartesian" class="headerlink"
title="Permalink to this heading">#</a>

Contravariant components of vectors, for example
<span class="math notranslate nohighlight">\\\left(B^x, B^y,
B^z\right)\\</span>, can be transformed back to cylindrical coordinates
by first calculating the components of the poloidal magnetic field in
the major radius (R) and height (Z) directions:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} B_Z &= -\frac{1}{R}\frac{\partial
\psi}{\partial R} \qquad B_R = \frac{1}{R}\frac{\partial \psi}{\partial
Z} \\ \nabla \psi &= \frac{\partial\psi}{\partial R}\nabla R +
\frac{\partial \psi}{\partial Z}\nabla Z \\ &= -RB_Z\nabla R + RB_R
\nabla Z \end{aligned}\end{split}\\

</div>

If using an exising grid, the
<span class="math notranslate nohighlight">\\B_R\\</span> and
<span class="math notranslate nohighlight">\\B_Z\\</span> components can
be found by calculating the tangent vector along the
<span class="math notranslate nohighlight">\\x\\</span> direction, then
using the fact that the poloidal field is perpendicular to that tangent
vector. Note: This needs additional care if the grid is non-orthogonal.

Since the <span class="math notranslate nohighlight">\\\left(\psi,
\theta, \zeta\right)\\</span> coordinate system is orthogonal, we can
use

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\boldsymbol{e}}\_\psi &=
g\_{\psi\psi}\nabla\psi =
\frac{1}{RB\_{pol}^2}\left(B_R\hat{\boldsymbol{Z}} -
B_Z\hat{\boldsymbol{R}}\right) \\ {\boldsymbol{e}}\_\theta &=
J\_{\psi\theta\zeta}\nabla\theta\times\nabla\zeta \\ &=
\frac{h\_\theta}{B\_{pol}}\left(B_R \hat{\boldsymbol{R}} +
B_Z\hat{\boldsymbol{Z}}\right) \\ {\boldsymbol{e}}\_\zeta &=
{\sigma\_{B\text{pol}}}{\boldsymbol{e}}\_\phi =
{\sigma\_{B\text{pol}}}R\hat{\boldsymbol{\phi}}
\end{aligned}\end{split}\\

</div>

where
<span class="math notranslate nohighlight">\\\hat{\boldsymbol{R}}\\</span>,
<span class="math notranslate nohighlight">\\\hat{\boldsymbol{Z}}\\</span>
and
<span class="math notranslate nohighlight">\\\hat{\boldsymbol{\phi}}\\</span>
are unit vectors in the cylindrical coordinate system.

Then we can write down the basis vectors in the field-aligned
coordinates (equation
<a href="#equation-eq-basisvectors" class="reference internal">(21)</a>),
in terms of cylindrical coordinate unit vectors:

<div id="equation-eq-basisvectors-cyl"
class="math notranslate nohighlight">

<span class="eqno">(33)<a href="#equation-eq-basisvectors-cyl" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{e}}\_x &=
\frac{\sigma\_{B\text{pol}}}{RB\_{pol}^2}\left(B_R\hat{\boldsymbol{Z}} -
B_Z\hat{\boldsymbol{R}}\right) +
I{\sigma\_{B\text{pol}}}R\hat{\boldsymbol{\phi}} \\ {\boldsymbol{e}}\_y
&= \frac{h\_\theta}{B\_{pol}}\left(B_R \hat{\boldsymbol{R}} +
B_Z\hat{\boldsymbol{Z}}\right) + \nu R\hat{\boldsymbol{\phi}} \\
{\boldsymbol{e}}\_z &= {\sigma\_{B\text{pol}}}R\hat{\boldsymbol{\phi}}
\end{aligned}\end{split}\\

</div>

A vector, for example the magnetic field, can be written in
field-aligned coordinates in terms of its contravariant components:

<div class="math notranslate nohighlight">

\\\begin{aligned} {\boldsymbol{B}} &= B^x{\boldsymbol{e}}\_x +
B^y{\boldsymbol{e}}\_y + B^z{\boldsymbol{e}}\_z \end{aligned}\\

</div>

Substitituting in the expressions for the basis vectors in equation
<a href="#equation-eq-basisvectors-cyl"
class="reference internal">(33)</a>, and collecting terms, we get:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} \left(% \begin{array}{c} B\_{\hat{R}} \\
B\_{\hat{Z}} \\ B\_{\hat{\phi}} \end{array} % \right) = \left(%
\begin{array}{ccc} -\frac{\sigma\_{B\text{pol}}}{RB\_{pol}^2}B_Z &
\frac{h\_\theta}{B\_{pol}}B_R & 0 \\
\frac{\sigma\_{B\text{pol}}}{RB\_{pol}^2}B_R &
\frac{h\_\theta}{B\_{pol}}B_Z & 0 \\ I{\sigma\_{B\text{pol}}}R & \nu R &
{\sigma\_{B\text{pol}}} R \end{array} % \right) \left(% \begin{array}{c}
B^x \\ B^y \\ B^z \end{array} % \right) \end{aligned}\end{split}\\

</div>

</div>

</div>

<div id="right-handed-field-aligned-coordinates" class="section">

## Right-handed field-aligned coordinates<a href="#right-handed-field-aligned-coordinates" class="headerlink"
title="Permalink to this heading">#</a>

If the poloidal magnetic field is negative, i.e. anti-clockwise in the
right-hand R-Z plane, then the above coordinate system is left-handed
and the Jacobian
<span class="math notranslate nohighlight">\\J\_{xyz}\\</span> is
negative. To obtain a consistently right-handed coordinate system, we
have to reverse the direction of the
<span class="math notranslate nohighlight">\\y\\</span> coordinate when
<span class="math notranslate nohighlight">\\B\_{pol} \< 0\\</span>:

This
<span class="math notranslate nohighlight">\\\left(x,\eta,z\right)\\</span>
coordinate system is defined by:

<div id="equation-eq-coordtransform2"
class="math notranslate nohighlight">

<span class="eqno">(34)<a href="#equation-eq-coordtransform2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} x =
{\sigma\_{B\text{pol}}}\left(\psi - \psi_0\right) \qquad \eta =
{\sigma\_{B\text{pol}}}\theta \qquad z = \sigma\_{B\text{pol}}
\left(\phi -
\int\_{\theta_0}^{\theta}\nu\left(\psi,\theta\right)d\theta\right)
\end{aligned}\\

</div>

The radial coordinate
<span class="math notranslate nohighlight">\\x\\</span> always points
outwards. The <span class="math notranslate nohighlight">\\\eta\\</span>
coordinate increases in the direction of the poloidal magnetic field:
clockwise in the right-hand poloidal plane if
<span class="math notranslate nohighlight">\\B\_{pol} \> 0\\</span>, and
anti-clockwise otherwise. The
<span class="math notranslate nohighlight">\\z\\</span> coordinate
increases in the same direction as
<span class="math notranslate nohighlight">\\\zeta\\</span> i.e.
anti-clockwise looking from the top if
<span class="math notranslate nohighlight">\\B\_{pol}\>0\\</span> and
clockwise if <span class="math notranslate nohighlight">\\B\_{pol} \<
0\\</span>.

This is still a Clebsch coordinate system:

<div id="equation-eq-clebschbrighthanded"
class="math notranslate nohighlight">

<span class="eqno">(35)<a href="#equation-eq-clebschbrighthanded" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{B}}= \nabla z\times \nabla x = \frac{1}{J\_{x\eta
z}}{\boldsymbol{e}}\_\eta \end{aligned}\\

</div>

but the Jacobian is now always positive:

<div id="equation-eq-jacobianrighthanded"
class="math notranslate nohighlight">

<span class="eqno">(36)<a href="#equation-eq-jacobianrighthanded" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
J\_{x\eta z} = h\_\theta / \left|B\_{\text{pol}}\right| \end{aligned}\\

</div>

The reciprocal basis vectors are

<div id="equation-eq-reciprocalbasisvectorsrighthanded"
class="math notranslate nohighlight">

<span class="eqno">(37)<a href="#equation-eq-reciprocalbasisvectorsrighthanded"
class="headerlink" title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla x =& {\sigma\_{B\text{pol}}} \nabla \psi \\ \nabla \eta =&
{\sigma\_{B\text{pol}}} \nabla \theta \\ \nabla z =& \nabla \zeta -
{\sigma\_{B\text{pol}}} I \nabla \psi -
{\sigma\_{B\text{pol}}}\nu\nabla\theta \end{aligned}\end{split}\\

</div>

and basis vectors

<div id="equation-eq-basisvectorsrighthanded"
class="math notranslate nohighlight">

<span class="eqno">(38)<a href="#equation-eq-basisvectorsrighthanded" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\boldsymbol{e}\_x =& J\_{x\eta z}\left(\nabla y \times \nabla z\right) =
{\sigma\_{B\text{pol}}} {\boldsymbol{e}}\_\psi +
I{\boldsymbol{e}}\_\zeta \\ \boldsymbol{e}\_\eta =& J\_{x\eta
z}\left(\nabla z \times \nabla x\right) = {\sigma\_{B\text{pol}}}
{\boldsymbol{e}}\_\theta + \nu{\boldsymbol{e}}\_\zeta \\
\boldsymbol{e}\_z =& J\_{x\eta z}\left(\nabla x \times \nabla y\right) =
{\boldsymbol{e}}\_\zeta \end{aligned}\end{split}\\

</div>

The contravariant metric tensor is:

<div id="equation-eq-contravariantmetricrighthanded"
class="math notranslate nohighlight">

<span class="eqno">(39)<a href="#equation-eq-contravariantmetricrighthanded" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
g^{ij} \equiv {\boldsymbol{e}}^i \cdot{\boldsymbol{e}}^j \equiv \nabla
u^i \cdot \nabla u^j = \left(% \begin{array}{ccc}
\left(R{B\_{\text{pol}}}\right)^2 & 0 &
-I\left(R{B\_{\text{pol}}}\right)^2 \\ 0 & 1 / {h\_\theta}^2 & -\nu /
{h\_\theta}^2 \\ -I\left(R{B\_{\text{pol}}}\right)^2 & -\nu /
{h\_\theta}^2 & I^2\left(R{B\_{\text{pol}}}\right)^2 + B^2 /
\left(R{B\_{\text{pol}}}\right)^2 \end{array} %
\right)\end{aligned}\end{split}\\

</div>

and the covariant metric tensor:

<div id="equation-eq-covariantmetricrighthanded"
class="math notranslate nohighlight">

<span class="eqno">(40)<a href="#equation-eq-covariantmetricrighthanded" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
g\_{ij} = \left(% \begin{array}{ccc} I^2 R^2 + 1 /
{\left({R{B\_{\text{pol}}}}\right)^2}& I \nu R^2 & I R^2 \\ I \nu R^2 &
J\_{x\eta z}^2B^2 & \nu R^2 \\ I R^2 & \nu R^2 & R^2 \end{array} %
\right)\end{aligned}\end{split}\\

</div>

The
<span class="math notranslate nohighlight">\\\texttt{zShift}\\</span>
quantity is the <span class="math notranslate nohighlight">\\z\\</span>
angle of a point on a field line relative to a reference location. This
is a scalar which doesn’t change if the sign of the
<span class="math notranslate nohighlight">\\\eta\\</span> coordinate is
reversed:

<div id="equation-eq-zshiftrighthanded"
class="math notranslate nohighlight">

<span class="eqno">(41)<a href="#equation-eq-zshiftrighthanded" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\texttt{zShift}\left(x, \eta\right) = \int\_{\eta =
0}^{\eta}\frac{{\boldsymbol{B}}\cdot\nabla
z}{{\boldsymbol{B}}\cdot\nabla \eta} d\eta = \int\_{\theta =
0}^{{\sigma\_{B\text{pol}}}\theta}\frac{{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}{h\_\theta}}{{B\_{\text{pol}}}R}
d\theta \end{aligned}\\

</div>

The
<span class="math notranslate nohighlight">\\\texttt{ShiftAngle}\\</span>
quantity is related to
<span class="math notranslate nohighlight">\\\texttt{zShift}\\</span>:
It is the change in
<span class="math notranslate nohighlight">\\\texttt{zShift}\\</span>
from <span class="math notranslate nohighlight">\\\eta=0\\</span> to
<span class="math notranslate nohighlight">\\\eta=2\pi\\</span>. It
therefore does change sign if the
<span class="math notranslate nohighlight">\\\eta\\</span> direction is
reversed.

The differences from the previous
<span class="math notranslate nohighlight">\\\left(x,y,z\right)\\</span>
coordinate system are that
<span class="math notranslate nohighlight">\\g\_{xy}\\</span>,
<span class="math notranslate nohighlight">\\g\_{yz}\\</span>,
<span class="math notranslate nohighlight">\\g^{yz}\\</span>,
<span class="math notranslate nohighlight">\\J\\</span> and
<span class="math notranslate nohighlight">\\\texttt{ShiftAngle}\\</span>
are multiplied by
<span class="math notranslate nohighlight">\\{\sigma\_{B\text{pol}}}\\</span>
to obtain their equivalents in the
<span class="math notranslate nohighlight">\\\left(x,\eta,z\right)\\</span>
coordinate system. If
<span class="math notranslate nohighlight">\\B\_{pol} \< 0\\</span> so
the poloidal magnetic field is anticlockwise in the right-hand R-Z
plane, then the
<span class="math notranslate nohighlight">\\\eta\\</span> direction
changes.

</div>

<div id="differential-operators-in-field-aligned-coordinates"
class="section">

## Differential operators in field-aligned coordinates<a href="#differential-operators-in-field-aligned-coordinates"
class="headerlink" title="Permalink to this heading">#</a>

These operators are valid for either
<span class="math notranslate nohighlight">\\\left(x,y,z\right)\\</span>
or
<span class="math notranslate nohighlight">\\\left(x,\eta,z\right)\\</span>
field-aligned coordinates defined above. Unless explicitly stated, in
the sections that follow
<span class="math notranslate nohighlight">\\y\\</span> will be used to
indicate the parallel coordinate
(<span class="math notranslate nohighlight">\\y\\</span> or
<span class="math notranslate nohighlight">\\\eta\\</span>). In a few
places the sign of
<span class="math notranslate nohighlight">\\B\_\text{pol}\\</span> may
appear, depending on whether
<span class="math notranslate nohighlight">\\y\\</span> or
<span class="math notranslate nohighlight">\\\eta\\</span> is used for
the parallel coordinate, so we define

<div id="equation-eq-sigma-y" class="math notranslate nohighlight">

<span class="eqno">(42)<a href="#equation-eq-sigma-y" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split} \sigma_y
= \begin{cases} \sigma\_{B\text{pol}} & \text{if using }(x,y,z) \\ +1 &
\text{if using }(x,\eta,z) \end{cases}\end{split}\\

</div>

The derivative of a scalar field
<span class="math notranslate nohighlight">\\f\\</span> along the
*unperturbed* magnetic field
<span class="math notranslate nohighlight">\\{\boldsymbol{b}}\_0\\</span>
is given by

<div id="equation-eq-gradpar1" class="math notranslate nohighlight">

<span class="eqno">(43)<a href="#equation-eq-gradpar1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\partial^0\_{||}f \equiv {\boldsymbol{b}}\_0 \cdot\nabla f =
\frac{1}{JB}{\frac{\partial f}{\partial y}} =
\frac{\sigma_y|{B\_{\text{pol}}}|}{B{h\_\theta}}{\frac{\partial
f}{\partial y}}\end{aligned}\\

</div>

Note that J could be positive or negative. The parallel divergence is
given by

<div id="equation-eq-divpar" class="math notranslate nohighlight">

<span class="eqno">(44)<a href="#equation-eq-divpar" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla^0\_{||}f =
B_0\partial^0\_{||}\left(\frac{f}{B_0}\right)\end{aligned}\\

</div>

Using equation <a href="#equation-eq-general-laplacian"
class="reference internal">(155)</a>, the Laplacian operator is given by

<div id="equation-eq-laplacian" class="math notranslate nohighlight">

<span class="eqno">(45)<a href="#equation-eq-laplacian" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla^2 = &\frac{\partial^2}{\partial x^2}\left|\nabla x\right|^2 +
\frac{\partial^2}{\partial y^2}\left|\nabla y\right|^2 +
\frac{\partial^2}{\partial z^2}\left|\nabla z\right|^2 \nonumber \\
&-2\frac{\partial^2}{\partial x\partial
z}I\left(R{B\_{\text{pol}}}\right)^2 - 2\frac{\partial^2}{\partial
y\partial z}\frac{\sigma_y\nu}{h\_\theta^2}\\ &+\frac{\partial}{\partial
x}\nabla^2x + \frac{\partial}{\partial y}\nabla^2y +
\frac{\partial}{\partial z}\nabla^2z \nonumber\end{aligned}\end{split}\\

</div>

Using equation <a href="#equation-eq-laplace-expand"
class="reference internal">(154)</a> for
<span class="math notranslate nohighlight">\\\nabla^2x = G^x\\</span>
etc, the values are

<div id="equation-eq-gxgygz" class="math notranslate nohighlight">

<span class="eqno">(46)<a href="#equation-eq-gxgygz" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla^2x = \frac{{B\_{\text{pol}}}}{h\_\theta}\frac{\partial}{\partial
x}\left(h\_\theta R^2{B\_{\text{pol}}}\right) \qquad \nabla^2y =
\frac{{B\_{\text{pol}}}}{h\_\theta}\frac{\partial}{\partial
y}\left(\frac{1}{{B\_{\text{pol}}}h\_\theta}\right)\end{aligned}\\

</div>

<div class="math notranslate nohighlight">

\\\begin{aligned} \nabla^2z =
-\frac{{B\_{\text{pol}}}}{h\_\theta}\left\[\frac{\partial}{\partial
x}\left(IR^2{B\_{\text{pol}}} h\_\theta\right) + \sigma_y
\frac{\partial}{\partial
y}\left(\frac{\nu}{{B\_{\text{pol}}}h\_\theta}\right)\right\]\end{aligned}\\

</div>

Neglecting some parallel derivative terms, the perpendicular Laplacian
can be written:

<div id="equation-eq-laplace-perp" class="math notranslate nohighlight">

<span class="eqno">(47)<a href="#equation-eq-laplace-perp" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\_\perp^2=
{\left({R{B\_{\text{pol}}}}\right)^2}\left\[{\frac{\partial^2 }{\partial
{x}^2}} - 2I\frac{\partial^2}{\partial z\partial x} + \left(I^2 +
\frac{B^2}{\left({R{B\_{\text{pol}}}}\right)^4}\right){\frac{\partial^2
}{\partial {z}^2}}\right\] + \nabla^2 x {\frac{\partial }{\partial x}} +
\nabla^2 z{\frac{\partial }{\partial z}}\end{aligned}\\

</div>

The second derivative along the equilibrium field

<div id="equation-eq-grad2par2" class="math notranslate nohighlight">

<span class="eqno">(48)<a href="#equation-eq-grad2par2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\partial^2\_{||}\phi = \partial^0\_{||}\left(\partial^0\_{||}\phi\right)
= \frac{1}{JB}{\frac{\partial }{\partial
y}}\left(\frac{1}{JB}\right){\frac{\partial \phi}{\partial y}} +
\frac{1}{g\_{yy}}\frac{\partial^2\phi}{\partial y^2}\end{aligned}\\

</div>

A common expression (the Poisson bracket in reduced MHD) is (from
equation
<a href="#equation-eq-bracket" class="reference internal">(181)</a>)):

<div id="equation-eq-poissonbracket1"
class="math notranslate nohighlight">

<span class="eqno">(49)<a href="#equation-eq-poissonbracket1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{b}}\_0\cdot\nabla\phi\times\nabla A =
\frac{1}{J^2B}\left\[\left(g\_{yy}{\frac{\partial \phi}{\partial z}} -
g\_{yz}{\frac{\partial \phi}{\partial y}}\right){\frac{\partial
A}{\partial x}} + \left(g\_{yz}{\frac{\partial \phi}{\partial x}} -
g\_{xy}{\frac{\partial \phi}{\partial z}}\right){\frac{\partial
A}{\partial y}} + \left(g\_{xy}{\frac{\partial \phi}{\partial y}} -
g\_{yy}{\frac{\partial \phi}{\partial x}}\right){\frac{\partial
A}{\partial z}}\right\]\end{aligned}\\

</div>

The perpendicular nabla operator:

<div id="equation-eq-gradperp1" class="math notranslate nohighlight">

<span class="eqno">(50)<a href="#equation-eq-gradperp1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla\_\perp \equiv& \nabla -
{\boldsymbol{b}}\left({\boldsymbol{b}}\cdot\nabla\right) \\ =& \nabla
x\left({\frac{\partial }{\partial x}} -
\frac{g\_{xy}}{\left(JB\right)^2}{\frac{\partial }{\partial y}}\right) +
\nabla z\left({\frac{\partial }{\partial z}} -
\frac{g\_{yz}}{\left(JB\right)^2}{\frac{\partial }{\partial
y}}\right)\end{aligned}\end{split}\\

</div>

<div id="j-x-b-in-field-aligned-coordinates" class="section">

<span id="sec-jxb-fac"></span>

### J x B in field-aligned coordinates<a href="#j-x-b-in-field-aligned-coordinates" class="headerlink"
title="Permalink to this heading">#</a>

Components of the magnetic field in field-aligned coordinates:

<div id="equation-eq-bcontravariant2"
class="math notranslate nohighlight">

<span class="eqno">(51)<a href="#equation-eq-bcontravariant2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} B^y =
\frac{\sigma_y{|B\_{\text{pol}}|}}{{h\_\theta}} \qquad B^x = B^z =
0\end{aligned}\\

</div>

and

<div id="equation-eq-bcovariant2" class="math notranslate nohighlight">

<span class="eqno">(52)<a href="#equation-eq-bcovariant2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} B_x =
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}I R \qquad B_y =
\sigma_y\frac{B^2{h\_\theta}}{{|B\_{\text{pol}}|}} \qquad B_z =
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}R\end{aligned}\\

</div>

Calculate current
<span class="math notranslate nohighlight">\\{\boldsymbol{J}}=
\frac{1}{\mu}{\nabla\times {\boldsymbol{B}} }\\</span>

<div id="equation-eq-jcrossb1" class="math notranslate nohighlight">

<span class="eqno">(53)<a href="#equation-eq-jcrossb1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\left({\nabla\times {\boldsymbol{B}} }\right)^x =
\frac{1}{J}\left({\frac{\partial B_z}{\partial y}} - {\frac{\partial
B_y}{\partial z}}\right) = 0\end{aligned}\\

</div>

since
<span class="math notranslate nohighlight">\\{B\_{\text{tor}}}R\\</span>
is a flux-surface quantity, and
<span class="math notranslate nohighlight">\\{\boldsymbol{B}}\\</span>
is axisymmetric.

<div id="equation-eq-curlb-fieldaligned"
class="math notranslate nohighlight">

<span class="eqno">(54)<a href="#equation-eq-curlb-fieldaligned" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\left({\nabla\times {\boldsymbol{B}} }\right)^y =&
-{\sigma_y\sigma\_{B\text{pol}}}\frac{{B\_{\text{pol}}}}{{h\_\theta}}{\frac{\partial
}{\partial x}}\left({B\_{\text{tor}}}R\right) \\ \left({\nabla\times
{\boldsymbol{B}} }\right)^z =&
\frac{{B\_{\text{pol}}}}{{h\_\theta}}\left\[{\frac{\partial }{\partial
x}}\left(\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{\sigma\_{B\text{pol}}}{\frac{\partial }{\partial
y}}\left({B\_{\text{tor}}}I R\right)\right\]\end{aligned}\end{split}\\

</div>

The second term can be simplified, again using
<span class="math notranslate nohighlight">\\{B\_{\text{tor}}}R\\</span>
constant on flux-surfaces:

<div id="equation-eq-curlbintermediate"
class="math notranslate nohighlight">

<span class="eqno">(55)<a href="#equation-eq-curlbintermediate" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial y}}\left({B\_{\text{tor}}}I R\right) =
{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}R{\frac{\partial \nu}{\partial
x}} \qquad \nu =
\frac{{h\_\theta}{B\_{\text{tor}}}}{R{B\_{\text{pol}}}}\end{aligned}\\

</div>

From these, calculate covariant components:

<div id="equation-eq-curlb-y" class="math notranslate nohighlight">

<span class="eqno">(56)<a href="#equation-eq-curlb-y" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\left({\nabla\times {\boldsymbol{B}} }\right)\_x =& -{B\_{\text{tor}}}I
R {\frac{\partial }{\partial x}}\left({B\_{\text{tor}}}R\right) +
\frac{IR^2{B\_{\text{pol}}}}{{h\_\theta}}\left\[{\frac{\partial
}{\partial x}}\left(\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{B\_{\text{tor}}} R{\frac{\partial \nu}{\partial x}}\right\] \nonumber\\
% \left({\nabla\times {\boldsymbol{B}} }\right)\_y =&
-{\sigma_y\sigma\_{B\text{pol}}}\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}{\frac{\partial
}{\partial x}}\left({B\_{\text{tor}}}R\right) +
{\sigma_y\sigma\_{B\text{pol}}}{B\_{\text{tor}}}R\left\[{\frac{\partial
}{\partial x}}\left(\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{B\_{\text{tor}}}R{\frac{\partial \nu}{\partial x}}\right\] \\ %
\left({\nabla\times {\boldsymbol{B}} }\right)\_z =&
-{B\_{\text{tor}}}R{\frac{\partial }{\partial
x}}\left({B\_{\text{tor}}}R\right) +
\frac{R^2{B\_{\text{pol}}}}{{h\_\theta}}\left\[{\frac{\partial
}{\partial x}}\left(\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{B\_{\text{tor}}} R{\frac{\partial \nu}{\partial x}}\right\]
\nonumber\end{aligned}\end{split}\\

</div>

Calculate
<span class="math notranslate nohighlight">\\{\boldsymbol{J}}\times{\boldsymbol{B}}\\</span>
using

<div id="equation-eq-jcrossb2" class="math notranslate nohighlight">

<span class="eqno">(57)<a href="#equation-eq-jcrossb2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{e}}^i = \frac{1}{J}\left({\boldsymbol{e}}\_j \times
{\boldsymbol{e}}\_k\right) \qquad {\boldsymbol{e}}\_i =
J\left({\boldsymbol{e}}^j \times {\boldsymbol{e}}^k\right) \qquad i,j,k
\texttt{ cyc } 1,2,3\end{aligned}\\

</div>

gives

<div id="equation-eq-jcrossb3" class="math notranslate nohighlight">

<span class="eqno">(58)<a href="#equation-eq-jcrossb3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\mu_0 \left({\boldsymbol{J}}\times{\boldsymbol{B}}\right)^x =&
\frac{1}{J}\left\[\left({\nabla\times {\boldsymbol{B}} }\right)\_y B_z -
\left({\nabla\times {\boldsymbol{B}} }\right)\_z B_y \right\]\\ =&
-\frac{{B\_{\text{pol}}}^3 R^2}{{h\_\theta}}\left\[{\frac{\partial
}{\partial x}}\left(\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{B\_{\text{tor}}}R{\frac{\partial \nu}{\partial
x}}\right\]\end{aligned}\end{split}\\

</div>

Covariant components of
<span class="math notranslate nohighlight">\\\nabla P\\</span>:

<div id="equation-eq-gradpcovariant"
class="math notranslate nohighlight">

<span class="eqno">(59)<a href="#equation-eq-gradpcovariant" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\left(\nabla P\right)\_x = {\frac{\partial P}{\partial x}} \qquad
\left(\nabla P\right)\_y = \left(\nabla P\right)\_z = 0\end{aligned}\\

</div>

and contravariant:

<div id="equation-eq-gradpcontravariant"
class="math notranslate nohighlight">

<span class="eqno">(60)<a href="#equation-eq-gradpcontravariant" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\left(\nabla P\right)^x =
{\left({R{B\_{\text{pol}}}}\right)^2}{\frac{\partial P}{\partial x}}
\qquad \left(\nabla P\right)^y = 0 \qquad \left(\nabla P\right)^z =
-I{\left({R{B\_{\text{pol}}}}\right)^2}{\frac{\partial P}{\partial
x}}\end{aligned}\\

</div>

Hence equating contravariant x components of
<span class="math notranslate nohighlight">\\{\boldsymbol{J}}\times{\boldsymbol{B}}=
\nabla P\\</span>,

<div id="equation-eq-xbalance1" class="math notranslate nohighlight">

<span class="eqno">(61)<a href="#equation-eq-xbalance1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial
x}}\left(\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{B\_{\text{tor}}} R{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}{h\_\theta}}{R{B\_{\text{pol}}}}\right) +
\frac{\mu_0{h\_\theta}}{{B\_{\text{pol}}}}{\frac{\partial P}{\partial
x}} = 0 \end{aligned}\\

</div>

Use this to calculate
<span class="math notranslate nohighlight">\\{h\_\theta}\\</span>
profiles (need to fix
<span class="math notranslate nohighlight">\\{h\_\theta}\\</span> at one
radial location).

Close to x-points, the above expression becomes singular, so a better
way to write it is:

<div id="equation-eq-xbalance2" class="math notranslate nohighlight">

<span class="eqno">(62)<a href="#equation-eq-xbalance2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial x}}\left(B^2{h\_\theta}\right) -
{h\_\theta}{B\_{\text{pol}}}{\frac{\partial {B\_{\text{pol}}}}{\partial
x}} - {B\_{\text{tor}}} R{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}{h\_\theta}}{R}\right) +
\mu_0{h\_\theta}{\frac{\partial P}{\partial x}} = 0\end{aligned}\\

</div>

For solving force-balance by adjusting
<span class="math notranslate nohighlight">\\P\\</span> and
<span class="math notranslate nohighlight">\\f\\</span> profiles, the
form used is

<div id="equation-eq-xbalance3" class="math notranslate nohighlight">

<span class="eqno">(63)<a href="#equation-eq-xbalance3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{B\_{\text{tor}}}{h\_\theta}{\frac{\partial {B\_{\text{tor}}}}{\partial
x}} + \frac{{B\_{\text{tor}}}^2{h\_\theta}}{R}{\frac{\partial
R}{\partial x}} + \mu_0{h\_\theta}{\frac{\partial P}{\partial x}} =
-{B\_{\text{pol}}}{\frac{\partial }{\partial
x}}\left({B\_{\text{pol}}}{h\_\theta}\right)\end{aligned}\\

</div>

A quick way to calculate f is to rearrange this to:

<div id="equation-eq-xbalance4" class="math notranslate nohighlight">

<span class="eqno">(64)<a href="#equation-eq-xbalance4" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial {B\_{\text{tor}}}}{\partial x}} =
{B\_{\text{tor}}}\left\[-\frac{1}{R}{\frac{\partial R}{\partial
x}}\right\] + \frac{1}{{B\_{\text{tor}}}}\left\[-\mu_0{\frac{\partial
P}{\partial x}} - {\frac{\partial {B\_{\text{pol}}}}{\partial
{h\_\theta}}}{\frac{\partial }{\partial
x}}\left({B\_{\text{pol}}}{h\_\theta}\right)\right\]\end{aligned}\\

</div>

and then integrate this using LSODE.

</div>

<div id="parallel-current" class="section">

### Parallel current<a href="#parallel-current" class="headerlink"
title="Permalink to this heading">#</a>

<div id="equation-eq-jpar" class="math notranslate nohighlight">

<span class="eqno">(65)<a href="#equation-eq-jpar" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} J\_{||}
= {\boldsymbol{b}}\cdot{\boldsymbol{J}}\qquad b^y =
\sigma_y\frac{{|B\_{\text{pol}}|}}{B{h\_\theta}}\end{aligned}\\

</div>

and from equation
<a href="#equation-eq-curlb-y" class="reference internal">(56)</a>:

<div id="equation-eq-j-y" class="math notranslate nohighlight">

<span class="eqno">(66)<a href="#equation-eq-j-y" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} J_y =
\frac{{\sigma_y\sigma\_{B\text{pol}}}}{\mu_0}\left\\-\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}{\frac{\partial
}{\partial x}}\left({B\_{\text{tor}}}R\right) + {B\_{\text{tor}}}
R\left\[{\frac{\partial }{\partial
x}}\left(\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{B\_{\text{tor}}}R{\frac{\partial \nu}{\partial
x}}\right\]\right\\\end{aligned}\\

</div>

since <span class="math notranslate nohighlight">\\J\_{||} =
b^yJ_y\\</span>,

<div id="equation-eq-amperelaw" class="math notranslate nohighlight">

<span class="eqno">(67)<a href="#equation-eq-amperelaw" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} \mu_0
J\_{||} =\frac{{B\_{\text{pol}}}{B\_{\text{tor}}}
R}{B{h\_\theta}}\left\[{\frac{\partial }{\partial
x}}\left(\frac{B^2{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{B\_{\text{tor}}}R{\frac{\partial \nu}{\partial x}}\right\] -
B{\frac{\partial }{\partial
x}}\left({B\_{\text{tor}}}R\right)\end{aligned}\\

</div>

Note, this does not depend on our coordinate choices, so does not depend
on <span class="math notranslate nohighlight">\\\sigma_y\\</span> or
<span class="math notranslate nohighlight">\\\sigma\_{B\text{pol}}\\</span>,
as it should not since
<span class="math notranslate nohighlight">\\\mu_0 J\_\parallel\\</span>
is a scalar quantity.

</div>

<div id="curvature" class="section">

### Curvature<a href="#curvature" class="headerlink"
title="Permalink to this heading">#</a>

For reduced MHD, need to calculate curvature term
<span class="math notranslate nohighlight">\\{\boldsymbol{b}}\times{\boldsymbol{\kappa}}\\</span>,
where <span class="math notranslate nohighlight">\\{\boldsymbol{\kappa}}
= \left({\boldsymbol{b}}\cdot\nabla\right){\boldsymbol{b}}=
-{\boldsymbol{b}}\times\left(\nabla\times{\boldsymbol{b}}\right)\\</span>.
Re-arranging, this becomes:

<div id="equation-eq-bcrosskappa1" class="math notranslate nohighlight">

<span class="eqno">(68)<a href="#equation-eq-bcrosskappa1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{b}}\times{\boldsymbol{\kappa}} =
\nabla\times{\boldsymbol{b}}-
{\boldsymbol{b}}\left({\boldsymbol{b}}\cdot\left(\nabla\times{\boldsymbol{b}}\right)\right)\end{aligned}\\

</div>

Components of
<span class="math notranslate nohighlight">\\\nabla\times{\boldsymbol{b}}\\</span>
are [1]:

<div id="equation-eq-curlb-reducedmhd"
class="math notranslate nohighlight">

<span class="eqno">(69)<a href="#equation-eq-curlb-reducedmhd" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\left(\nabla\times{\boldsymbol{b}}\right)^x =&
{\sigma_y}\frac{{B\_{\text{pol}}}}{{h\_\theta}}{\frac{\partial
}{\partial y}}\left(\frac{{B\_{\text{tor}}} R}{B}\right) \\
\left(\nabla\times{\boldsymbol{b}}\right)^y =&
-{\sigma_y}\frac{{B\_{\text{pol}}}}{{h\_\theta}}{\frac{\partial
}{\partial x}}\left(\frac{{B\_{\text{tor}}}R}{B}\right) \\
\left(\nabla\times{\boldsymbol{b}}\right)^z =&
\frac{{B\_{\text{pol}}}}{{h\_\theta}}{\frac{\partial }{\partial
x}}\left(\frac{B{h\_\theta}}{{B\_{\text{pol}}}}\right) -
\frac{{B\_{\text{pol}}}{B\_{\text{tor}}} R}{{h\_\theta}B}{\frac{\partial
\nu}{\partial x}} -
{\sigma_y}I\frac{{|B\_{\text{pol}}|}}{{h\_\theta}}{\frac{\partial
}{\partial y}}\left(\frac{{B\_{\text{tor}}} R}{B}\right) \\
\end{aligned}\end{split}\\

</div>

giving:

<div id="equation-eq-curvature" class="math notranslate nohighlight">

<span class="eqno">(70)<a href="#equation-eq-curvature" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{\kappa}} =& -\frac{{B\_{\text{pol}}}}{B
h\_\theta}\left\[{\frac{\partial }{\partial x}}\left(\frac{B
h\_\theta}{{B\_{\text{pol}}}}\right) -
{\sigma_y\sigma\_{B\text{pol}}}{\frac{\partial }{\partial
y}}\left(\frac{{B\_{\text{tor}}}I R}{B}\right)\right\]\nabla x \nonumber
\\ &+ {\sigma_y}\frac{{B\_{\text{pol}}}}{B h\_\theta}{\frac{\partial
}{\partial y}}\left(\frac{{B\_{\text{tor}}}R}{B}\right)\nabla z
\end{aligned}\end{split}\\

</div>

<div class="math notranslate nohighlight">

\\\begin{aligned}
{\boldsymbol{b}}\cdot\left(\nabla\times{\boldsymbol{b}}\right) =
-{\sigma\_{B\text{pol}}}B{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}R}{B}\right) +
{\sigma\_{B\text{pol}}}\frac{{B\_{\text{tor}}}{B\_{\text{pol}}}R}{B{h\_\theta}}{\frac{\partial
}{\partial x}}\left(\frac{B{h\_\theta}}{{B\_{\text{pol}}}}\right) -
\sigma\_{B\text{pol}}\frac{{B\_{\text{pol}}}{B\_{\text{tor}}}^2R^2}{{h\_\theta}B^2}{\frac{\partial
\nu}{\partial x}}\end{aligned}\\

</div>

therefore,

<div id="equation-eq-bcrosskappacomponents1"
class="math notranslate nohighlight">

<span class="eqno">(71)<a href="#equation-eq-bcrosskappacomponents1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)^x =&
{\sigma_y}\frac{{B\_{\text{pol}}}}{{h\_\theta}}{\frac{\partial
}{\partial y}}\left(\frac{{B\_{\text{tor}}} R}{B}\right) =
-{\sigma_y}\frac{{B\_{\text{pol}}}{B\_{\text{tor}}}R}{{h\_\theta}B^2}{\frac{\partial
B}{\partial y}} \\
\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)^y =&
\sigma_y\frac{{B\_{\text{pol}}}^2{B\_{\text{tor}}}^2
R^2}{B^3{h\_\theta}^2}{\frac{\partial \nu}{\partial x}} -
{\sigma_y}\frac{{B\_{\text{pol}}}^2{B\_{\text{tor}}}
R}{B^2{h\_\theta}^2}{\frac{\partial }{\partial
x}}\left(\frac{B{h\_\theta}}{{B\_{\text{pol}}}}\right) \\
\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)^z =&
\frac{{B\_{\text{pol}}}}{{h\_\theta}}{\frac{\partial }{\partial
x}}\left(\frac{B{h\_\theta}}{{B\_{\text{pol}}}}\right) -
\frac{{B\_{\text{pol}}}{B\_{\text{tor}}} R}{{h\_\theta}B}{\frac{\partial
\nu}{\partial x}} - \sigma\_{B\text{pol}}
I\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)^x\end{aligned}\end{split}\\

</div>

Using equation
<a href="#equation-eq-xbalance1" class="reference internal">(61)</a>:

<div id="equation-eq-bcrosskappaintermediateidentity"
class="math notranslate nohighlight">

<span class="eqno">(72)<a href="#equation-eq-bcrosskappaintermediateidentity"
class="headerlink" title="Permalink to this equation">#</a></span>\\\begin{aligned}
\sigma\_{B\text{pol}}B{\frac{\partial }{\partial
x}}\left(\frac{B{h\_\theta}}{{B\_{\text{pol}}}}\right) +
\sigma\_{B\text{pol}}\frac{B{h\_\theta}}{{B\_{\text{pol}}}}{\frac{\partial
B}{\partial x}} - {\sigma\_{B\text{pol}}}{B\_{\text{tor}}}
R{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}{h\_\theta}}{R{B\_{\text{pol}}}}\right) +
\sigma\_{B\text{pol}}\frac{\mu_0{h\_\theta}}{{B\_{\text{pol}}}}{\frac{\partial
P}{\partial x}} = 0\end{aligned}\\

</div>

we can re-write the above components as:

<div id="equation-eq-bcrosskappacomponents2"
class="math notranslate nohighlight">

<span class="eqno">(73)<a href="#equation-eq-bcrosskappacomponents2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)^y =&
{\sigma_y}\frac{{B\_{\text{pol}}}{B\_{\text{tor}}}
R}{B^2{h\_\theta}}\left\[\frac{\mu_0}{B}{\frac{\partial P}{\partial
x}} + {\frac{\partial B}{\partial x}}\right\] \\
\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)^z =&
-\frac{\mu_0}{B}{\frac{\partial P}{\partial x}} - {\frac{\partial
B}{\partial x}} -
\sigma\_{B\text{pol}}I\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)^x\end{aligned}\end{split}\\

</div>

<span class="label"><span class="fn-bracket">\[</span><a href="#id2" role="doc-backlink">1</a><span class="fn-bracket">\]</span></span>

Note on signs:
<span class="math notranslate nohighlight">\\\nabla\times\boldsymbol{b}\\</span>
should flip sign if we flip the magnetic field direction (i.e.
<span class="math notranslate nohighlight">\\B\_\text{pol}\rightarrow
-B\_\text{pol}\\</span> and
<span class="math notranslate nohighlight">\\B\_\text{tor} \rightarrow
-B\_\text{tor}\\</span>). Under this flip, the
<span class="math notranslate nohighlight">\\x\\</span>-coordinate stays
the same and the
<span class="math notranslate nohighlight">\\z\\</span>-coordinate flips
sign. The
<span class="math notranslate nohighlight">\\y\\</span>-coordinate stays
the same, or the
<span class="math notranslate nohighlight">\\\eta\\</span>-coordinate
flips sign. Therefore the x-component of
<span class="math notranslate nohighlight">\\\nabla\times\boldsymbol{b}\\</span>
should flip sign, the
<span class="math notranslate nohighlight">\\z\\</span>-component should
not flip sign (product of two sign flips), and the
<span class="math notranslate nohighlight">\\y\\</span>-component should
flip sign if ‘<span class="math notranslate nohighlight">\\y\\</span>’
is <span class="math notranslate nohighlight">\\y\\</span> and not flip
sign if ‘<span class="math notranslate nohighlight">\\y\\</span>’ is
<span class="math notranslate nohighlight">\\\eta\\</span>.

</div>

<div id="curvature-from-nabla-times-left-frac-boldsymbol-b-b-right"
class="section">

### Curvature from <span class="math notranslate nohighlight">\\{\nabla\times\left(\frac{\boldsymbol{b}}{B}\right)}\\</span><a href="#curvature-from-nabla-times-left-frac-boldsymbol-b-b-right"
class="headerlink" title="Permalink to this heading">#</a>

The vector
<span class="math notranslate nohighlight">\\{\boldsymbol{b}}\times{\boldsymbol{\kappa}}\\</span>
is an approximation of

<div id="equation-eq-bcrosskappaapprox"
class="math notranslate nohighlight">

<span class="eqno">(74)<a href="#equation-eq-bcrosskappaapprox" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\frac{B}{2}\nabla\times\left(\frac{{\boldsymbol{b}}}{B}\right) \simeq
{\boldsymbol{b}}\times{\boldsymbol{\kappa}}\end{aligned}\\

</div>

so can just derive from the original expression. Using the covariant
components <span class="math notranslate nohighlight">\\{b_i}\\</span>
of
<span class="math notranslate nohighlight">\\{\boldsymbol{b}}\\</span>,
and the curl operator in curvilinear coordinates (see appendix):

<div id="equation-eq-curlboverb" class="math notranslate nohighlight">

<span class="eqno">(75)<a href="#equation-eq-curlboverb" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla\times\left(\frac{{\boldsymbol{b}}}{B}\right) =&
\frac{{B\_{\text{pol}}}}{{h\_\theta}}\left\[\left({\frac{\partial
}{\partial x}}\left(\frac{{h\_\theta}}{{B\_{\text{pol}}}}\right) -
\sigma_y{\frac{\partial }{\partial
y}}\left(\frac{{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}IR}{B^2}\right)\right){\boldsymbol{e}}\_z
\right. \\ &+ \sigma_y{\frac{\partial }{\partial
y}}\left(\frac{{B\_{\text{tor}}}R}{B^2}\right){\boldsymbol{e}}\_x \\ &-
\sigma_y\left.{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}R}{B^2}\right){\boldsymbol{e}}\_y\right\]\end{aligned}\end{split}\\

</div>

This can be simplified using

<div id="equation-eq-curlboverbintermediateidentity"
class="math notranslate nohighlight">

<span class="eqno">(76)<a href="#equation-eq-curlboverbintermediateidentity" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\sigma_y\frac{\partial }{\partial
y}}\left(\frac{{\sigma\_{B\text{pol}}}{B\_{\text{tor}}}IR}{B^2}\right) =
I{\sigma\_{B\text{pol}}}{B\_{\text{tor}}} R{\sigma_y\frac{\partial
}{\partial y}}\left(\frac{1}{B^2}\right) +
\frac{{B\_{\text{tor}}}R}{B^2}{\frac{\partial \nu}{\partial
x}}\end{aligned}\\

</div>

to give

<div id="equation-eq-curlboverbcomponents"
class="math notranslate nohighlight">

<span class="eqno">(77)<a href="#equation-eq-curlboverbcomponents" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\frac{B}{2}\left(\nabla\times\frac{\boldsymbol{b}}{B}\right)^x} =&
{-{\sigma_y}\frac{{B\_{\text{pol}}}{B\_{\text{tor}}}R}{{h\_\theta}B^2}{\frac{\partial
B}{\partial y}}} \\
{\frac{B}{2}\left(\nabla\times\frac{\boldsymbol{b}}{B}\right)^y} =&
{-{\sigma_y}\frac{B{B\_{\text{pol}}}}{2{h\_\theta}}{\frac{\partial
}{\partial x}}\left(\frac{{B\_{\text{tor}}} R}{B^2}\right)} \\
{\frac{B}{2}\left(\nabla\times\frac{\boldsymbol{b}}{B}\right)^z} =&
{\frac{B{B\_{\text{pol}}}}{2{h\_\theta}}{\frac{\partial }{\partial
x}}\left(\frac{{h\_\theta}}{{B\_{\text{pol}}}}\right) -
\frac{{B\_{\text{pol}}}{B\_{\text{tor}}}
R}{2{h\_\theta}B}{\frac{\partial \nu}{\partial x}} -
I\frac{B}{2}\left(\nabla\times\frac{\boldsymbol{b}}{B}\right)^x}
\end{aligned}\end{split}\\

</div>

The first and second terms in
<span class="math notranslate nohighlight">\\\frac{B}{2}\left(\nabla\times\frac{\boldsymbol{b}}{B}\right)^z\\</span>
almost cancel, so by expanding out
<span class="math notranslate nohighlight">\\\nu\\</span> a better
expression is

<div id="equation-eq-curlboverbz" class="math notranslate nohighlight">

<span class="eqno">(78)<a href="#equation-eq-curlboverbz" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\frac{B}{2}\left(\nabla\times\frac{\boldsymbol{b}}{B}\right)^z =
\frac{{B\_{\text{pol}}}^3}{2{h\_\theta} B}{\frac{\partial }{\partial
x}}\left(\frac{{h\_\theta}}{{B\_{\text{pol}}}}\right) -
\frac{{B\_{\text{tor}}} R}{2B}{\frac{\partial }{\partial
x}}\left(\frac{{B\_\text{tor}}}{R}\right)\end{aligned}\\

</div>

</div>

<div id="curvature-of-a-single-line" class="section">

### Curvature of a single line<a href="#curvature-of-a-single-line" class="headerlink"
title="Permalink to this heading">#</a>

The curvature vector can be calculated from the field-line toroidal
coordinates
<span class="math notranslate nohighlight">\\\left(R,Z,\phi\right)\\</span>
as follows. The line element is given by

<div id="equation-eq-linecurvature"
class="math notranslate nohighlight">

<span class="eqno">(79)<a href="#equation-eq-linecurvature" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
d{\boldsymbol{r}} = dR{\hat{{\boldsymbol{R}}}}+
dZ{\hat{{\boldsymbol{Z}}}}+
Rd\phi{\hat{{\boldsymbol{\phi}}}}\end{aligned}\\

</div>

Hence the tangent vector is

<div id="equation-eq-linetangent" class="math notranslate nohighlight">

<span class="eqno">(80)<a href="#equation-eq-linetangent" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\hat{{\boldsymbol{T}}} \equiv {\frac{d {\boldsymbol{r}}}{d s}} =
{\frac{d R}{d s}}{\hat{{\boldsymbol{R}}}}+ {\frac{d Z}{d
s}}{\hat{{\boldsymbol{Z}}}}+ R{\frac{d \phi}{d
s}}{\hat{{\boldsymbol{\phi}}}}\end{aligned}\\

</div>

where <span class="math notranslate nohighlight">\\s\\</span> is the
distance along the field-line. From this, the curvature vector is given
by

<div id="equation-eq-kappaline1" class="math notranslate nohighlight">

<span class="eqno">(81)<a href="#equation-eq-kappaline1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{\kappa}}\equiv {\frac{d {\boldsymbol{T}}}{d s}} =&
{\frac{d^2 R}{d s^2}}{\hat{{\boldsymbol{R}}}}+ {\frac{d R}{d s}}{\frac{d
\phi}{d s}}{\hat{{\boldsymbol{\phi}}}} \\ &+ {\frac{d^2 Z}{d
s^2}}{\hat{{\boldsymbol{Z}}}}\\ &+ {\frac{d R}{d s}}{\frac{d \phi}{d
s}}{\hat{{\boldsymbol{\phi}}}}+ R{\frac{d^2 \phi}{d
s^2}}{\hat{{\boldsymbol{\phi}}}}- R\left({\frac{d \phi}{d s}}\right)^2
{\hat{{\boldsymbol{R}}}}\end{aligned}\end{split}\\

</div>

i.e.

<div id="equation-eq-kappaline2" class="math notranslate nohighlight">

<span class="eqno">(82)<a href="#equation-eq-kappaline2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{\kappa}}= \left\[{\frac{d^2 R}{d s^2}} - R\left({\frac{d
\phi}{d s}}\right)^2\right\]{\hat{{\boldsymbol{R}}}}+ {\frac{d^2 Z}{d
s^2}}{\hat{{\boldsymbol{Z}}}}+ \left\[2{\frac{d R}{d s}}{\frac{d \phi}{d
s}} + R{\frac{d^2 \phi}{d s^2}}\right\]{\hat{{\boldsymbol{\phi}}}}
\end{aligned}\\

</div>

Want the components of
<span class="math notranslate nohighlight">\\{\boldsymbol{b}}\times{\boldsymbol{\kappa}}\\</span>,
and since the vector
<span class="math notranslate nohighlight">\\{\boldsymbol{b}}\\</span>
is just the tangent vector
<span class="math notranslate nohighlight">\\{\boldsymbol{T}}\\</span>
above, this can be written using the cross-products

<div id="equation-eq-bcrosskappaline"
class="math notranslate nohighlight">

<span class="eqno">(83)<a href="#equation-eq-bcrosskappaline" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\hat{{\boldsymbol{R}}}}\times{\hat{{\boldsymbol{Z}}}}=
-{\hat{{\boldsymbol{\phi}}}}\qquad
{\hat{{\boldsymbol{\phi}}}}\times{\hat{{\boldsymbol{Z}}}}=
{\hat{{\boldsymbol{R}}}}\qquad
{\hat{{\boldsymbol{R}}}}\times{\hat{{\boldsymbol{\phi}}}}=
{\hat{{\boldsymbol{Z}}}}\end{aligned}\\

</div>

This vector must then be dotted with
<span class="math notranslate nohighlight">\\\nabla\psi\\</span>,
<span class="math notranslate nohighlight">\\\nabla\theta\\</span>, and
<span class="math notranslate nohighlight">\\\nabla\phi\\</span>. This
is done by writing these vectors in cylindrical coordinates:

<div id="equation-eq-bcrosskappalinecomponents1"
class="math notranslate nohighlight">

<span class="eqno">(84)<a href="#equation-eq-bcrosskappalinecomponents1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla\psi =& {\frac{\partial \psi}{\partial R}}\hat{{\boldsymbol{R}}} +
{\frac{\partial \psi}{\partial Z}}\hat{{\boldsymbol{Z}}} \\ \nabla\theta
=& \frac{1}{{B\_{\text{pol}}}{h\_\theta}}\nabla\phi\times\nabla\psi =
\frac{1}{R{B\_{\text{pol}}}{h\_\theta}}\left({\frac{\partial
\psi}{\partial Z}}\hat{{\boldsymbol{R}}} - {\frac{\partial
\psi}{\partial R}}\hat{{\boldsymbol{Z}}}\right)
\\\end{aligned}\end{split}\\

</div>

An alternative is to use

<div id="equation-eq-bcrossgradphi"
class="math notranslate nohighlight">

<span class="eqno">(85)<a href="#equation-eq-bcrossgradphi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{b}}\times \nabla\phi =
\frac{{\sigma\_{B\text{pol}}}}{BR^2}\nabla\psi\end{aligned}\\

</div>

and that the tangent vector
<span class="math notranslate nohighlight">\\{\boldsymbol{T}} =
{\boldsymbol{b}}\\</span>. This gives

<div id="equation-eq-flinenablapsi"
class="math notranslate nohighlight">

<span class="eqno">(86)<a href="#equation-eq-flinenablapsi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\psi =
{\sigma\_{B\text{pol}}}BR\left\[\frac{dR}{ds}{\boldsymbol{Z}} -
\frac{dZ}{ds}{\boldsymbol{R}}\right\] \end{aligned}\\

</div>

and so because <span class="math notranslate nohighlight">\\d\phi / ds =
{B\_{\text{tor}}}/ \left(RB\right)\\</span>

<div id="equation-eq-flinekappsi" class="math notranslate nohighlight">

<span class="eqno">(87)<a href="#equation-eq-flinekappsi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{\kappa}}\cdot\nabla\psi = {\sigma\_{B\text{pol}}}BR\left\[
\left( \frac{{B\_{\text{tor}}}^2}{RB^2} - {\frac{d^2 R}{d
s^2}}\right){\frac{d Z}{d s}} + {\frac{d^2 Z}{d s^2}}\frac{dR}{ds}
\right\] \end{aligned}\\

</div>

Taking the cross-product of the tangent vector with the curvature in
equation
<a href="#equation-eq-kappaline2" class="reference internal">(82)</a>
above gives

<div id="equation-eq-bcrosskappaline3"
class="math notranslate nohighlight">

<span class="eqno">(88)<a href="#equation-eq-bcrosskappaline3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{b}}\times{\boldsymbol{\kappa}}=&
\left\[\frac{{B\_{\text{tor}}}}{B}{\frac{d^2 Z}{d s^2}} - {\frac{d Z}{d
s}}\left(2{\frac{d R}{d s}}{\frac{d \phi}{d s}} + R{\frac{d^2 \phi}{d
s^2}}\right)\right\]{\boldsymbol{R}} \\ &+ \left\[{\frac{d R}{d
s}}\left(2{\frac{d R}{d s}}{\frac{d \phi}{d s}} + R{\frac{d^2 \phi}{d
s^2}}\right) - \frac{{B\_{\text{tor}}}}{B}\left({\frac{d^2 R}{d s^2}} -
R\left({\frac{d \phi}{d s}}\right)^2\right)\right\]{\boldsymbol{Z}} \\
&+ \left\[{\frac{d Z}{d s}}\left({\frac{d^2 R}{d s^2}} - R\left({\frac{d
\phi}{d s}}\right)^2\right) - {\frac{d R}{d s}}{\frac{d^2 Z}{d
s^2}}\right\]{\hat{{\boldsymbol{\phi}}}}\end{aligned}\end{split}\\

</div>

The components in field-aligned coordinates can then be calculated:

<div id="equation-eq-bcrosskappalinecomponents2"
class="math notranslate nohighlight">

<span class="eqno">(89)<a href="#equation-eq-bcrosskappalinecomponents2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)^x =&
{\sigma\_{B\text{pol}}}\left({\boldsymbol{b}}\times{\boldsymbol{\kappa}}\right)\cdot\nabla\psi
\\ =& \frac{R{B\_{\text{pol}}}^2}{B}\left(2{\frac{d R}{d s}}{\frac{d
\phi}{d s}} + R{\frac{d^2 \phi}{d s^2}}\right) -
R{B\_{\text{tor}}}\left({\frac{d R}{d s}}{\frac{d^2 R}{d s^2}} +
{\frac{d Z}{d s}}{\frac{d^2 Z}{d s^2}}\right) +
\frac{{B\_{\text{tor}}}^3}{B^2}{\frac{d R}{d
s}}\end{aligned}\end{split}\\

</div>

</div>

<div id="curvature-in-toroidal-coordinates" class="section">

### Curvature in toroidal coordinates<a href="#curvature-in-toroidal-coordinates" class="headerlink"
title="Permalink to this heading">#</a>

In toroidal coordinates
<span class="math notranslate nohighlight">\\\left(\psi,\theta,\phi\right)\\</span>,
the
<span class="math notranslate nohighlight">\\{\boldsymbol{b}}\\</span>
vector is

<div id="equation-eq-bcomponents1" class="math notranslate nohighlight">

<span class="eqno">(90)<a href="#equation-eq-bcomponents1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{b}}=&
\frac{{B\_{\text{pol}}}}{B}{\hat{{\boldsymbol{e}}}}\_\theta +
\frac{{B\_{\text{tor}}}}{B}{\hat{{\boldsymbol{e}}}}\_\phi \\ =&
\frac{{B\_{\text{pol}}}{h\_\theta}}{B}\nabla\theta +
\frac{R{B\_{\text{tor}}}}{B}\nabla\phi\end{aligned}\end{split}\\

</div>

The curl of this vector is

<div id="equation-eq-curlb1" class="math notranslate nohighlight">

<span class="eqno">(91)<a href="#equation-eq-curlb1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\left(\nabla\times{\boldsymbol{b}}\right)^\psi =&
\frac{1}{\sqrt{g}}\left({\frac{\partial b\_\phi}{\partial \theta}} -
{\frac{\partial b\_\theta}{\partial \phi}}\right) \\
\left(\nabla\times{\boldsymbol{b}}\right)^\theta =&
\frac{1}{\sqrt{g}}\left({\frac{\partial b\_\psi}{\partial \phi}} -
{\frac{\partial b\_\phi}{\partial \psi}}\right) \\
\left(\nabla\times{\boldsymbol{b}}\right)^\phi =&
\frac{1}{\sqrt{g}}\left({\frac{\partial b\_\theta}{\partial \psi}} -
{\frac{\partial b\_\psi}{\partial
\theta}}\right)\end{aligned}\end{split}\\

</div>

where <span class="math notranslate nohighlight">\\1/\sqrt{g} =
{B\_{\text{pol}}}/{h\_\theta}\\</span>. Therefore, in terms of unit
vectors:

<div id="equation-eq-curlb2" class="math notranslate nohighlight">

<span class="eqno">(92)<a href="#equation-eq-curlb2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\times{\boldsymbol{b}}=
\frac{\sigma\_{B\text{pol}}}{R{h\_\theta}}{\frac{\partial }{\partial
\theta}}\left(\frac{R{B\_{\text{tor}}}}{B}\right){\hat{{\boldsymbol{e}}}}\_\psi -
{B\_{\text{pol}}}{\frac{\partial }{\partial
\psi}}\left(\frac{R{B\_{\text{tor}}}}{B}\right){\hat{{\boldsymbol{e}}}}\_\theta +
\frac{{B\_{\text{pol}}} R}{{h\_\theta}}{\frac{\partial }{\partial
\psi}}\left(\frac{{h\_\theta}{B\_{\text{pol}}}}{B}\right){\hat{{\boldsymbol{e}}}}\_\phi\end{aligned}\\

</div>

</div>

<div id="psi-derivative-of-the-b-field" class="section">

### psi derivative of the B field<a href="#psi-derivative-of-the-b-field" class="headerlink"
title="Permalink to this heading">#</a>

Needed to calculate magnetic shear, and one way to get the curvature.
The simplest way is to use finite differencing, but there is another way
using local derivatives (implemented using DCT).

<div id="equation-eq-bpol" class="math notranslate nohighlight">

<span class="eqno">(93)<a href="#equation-eq-bpol" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{|B\_{\text{pol}}|}= \frac{\left|\nabla\psi\right|}{R} =
\frac{1}{R}\sqrt{\left({\frac{\partial \psi}{\partial R}}\right)^2 +
\left({\frac{\partial \psi}{\partial R}}\right)^2}\end{aligned}\\

</div>

Using

<div id="equation-eq-gradbpol" class="math notranslate nohighlight">

<span class="eqno">(94)<a href="#equation-eq-gradbpol" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla{B\_{\text{pol}}}= {\frac{\partial {B\_{\text{pol}}}}{\partial
\psi}}\nabla\psi + {\frac{\partial {B\_{\text{pol}}}}{\partial
\theta}}\nabla\theta + {\frac{\partial {B\_{\text{pol}}}}{\partial
\phi}}\nabla\phi\end{aligned}\\

</div>

we get

<div id="equation-eq-gradbpoldotgradpsi"
class="math notranslate nohighlight">

<span class="eqno">(95)<a href="#equation-eq-gradbpoldotgradpsi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla{B\_{\text{pol}}}\cdot\nabla\psi = {\frac{\partial
{B\_{\text{pol}}}}{\partial
\psi}}\left|\nabla\psi\right|^2\end{aligned}\\

</div>

and so

<div id="equation-eq-dbpoldpsi" class="math notranslate nohighlight">

<span class="eqno">(96)<a href="#equation-eq-dbpoldpsi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial {B\_{\text{pol}}}}{\partial \psi}} =
\nabla{B\_{\text{pol}}}\cdot\nabla\psi /
\left(R{B\_{\text{pol}}}\right)^2\end{aligned}\\

</div>

The derivatives of
<span class="math notranslate nohighlight">\\{B\_{\text{pol}}}\\</span>
in <span class="math notranslate nohighlight">\\R\\</span> and
<span class="math notranslate nohighlight">\\Z\\</span> are:

<div id="equation-eq-dbpoldr-dbpoldz"
class="math notranslate nohighlight">

<span class="eqno">(97)<a href="#equation-eq-dbpoldr-dbpoldz" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\frac{\partial {B\_{\text{pol}}}}{\partial R}} =&
-\frac{{B\_{\text{pol}}}}{R} + \frac{1}{{B\_{\text{pol}}}
R^2}\left\[{\frac{\partial \psi}{\partial R}}{\frac{\partial^2
\psi}{\partial {R}^2}} + {\frac{\partial \psi}{\partial
Z}}\frac{\partial^2\psi}{\partial R\partial Z}\right\] \\
{\frac{\partial {B\_{\text{pol}}}}{\partial Z}} =&
\frac{1}{{B\_{\text{pol}}}R^2}\left\[{\frac{\partial \psi}{\partial
Z}}{\frac{\partial^2 \psi}{\partial {Z}^2}} + {\frac{\partial
\psi}{\partial R}}\frac{\partial^2\psi}{\partial R\partial
Z}\right\]\end{aligned}\end{split}\\

</div>

For the toroidal field,
<span class="math notranslate nohighlight">\\{B\_{\text{tor}}}=
f/R\\</span>

<div id="equation-eq-dbtordpsi1" class="math notranslate nohighlight">

<span class="eqno">(98)<a href="#equation-eq-dbtordpsi1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial {B\_{\text{tor}}}}{\partial \psi}} =
\frac{1}{R}{\frac{\partial f}{\partial \psi}} -
\frac{f}{R^2}{\frac{\partial R}{\partial \psi}}\end{aligned}\\

</div>

As above, <span class="math notranslate nohighlight">\\{\frac{\partial
R}{\partial \psi}} = \nabla R \cdot\nabla\psi /
\left(R{B\_{\text{pol}}}\right)^2\\</span>, and since
<span class="math notranslate nohighlight">\\\nabla R\cdot\nabla R =
1\\</span>,

<div id="equation-eq-drdpsi" class="math notranslate nohighlight">

<span class="eqno">(99)<a href="#equation-eq-drdpsi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial R}{\partial \psi}} = {\frac{\partial \psi}{\partial R}}
/ \left(R{B\_{\text{pol}}}\right)^2\end{aligned}\\

</div>

similarly,

<div id="equation-eq-dzdpsi" class="math notranslate nohighlight">

<span class="eqno">(100)<a href="#equation-eq-dzdpsi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial Z}{\partial \psi}} = {\frac{\partial \psi}{\partial Z}}
/ \left(R{B\_{\text{pol}}}\right)^2\end{aligned}\\

</div>

and so the variation of toroidal field with
<span class="math notranslate nohighlight">\\\psi\\</span> is

<div id="equation-eq-dbtordpsi2" class="math notranslate nohighlight">

<span class="eqno">(101)<a href="#equation-eq-dbtordpsi2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial {B\_{\text{tor}}}}{\partial \psi}} =
\frac{1}{R}{\frac{\partial f}{\partial \psi}} -
\frac{{B\_{\text{tor}}}}{R^3{B\_{\text{pol}}}^2}{\frac{\partial
\psi}{\partial R}}\end{aligned}\\

</div>

From the definition
<span class="math notranslate nohighlight">\\B=\sqrt{{B\_{\text{tor}}}^2 +
{B\_{\text{pol}}}^2}\\</span>,

<div id="equation-eq-dbdpsi" class="math notranslate nohighlight">

<span class="eqno">(102)<a href="#equation-eq-dbdpsi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial B}{\partial \psi}} =
\frac{1}{B}\left({B\_{\text{tor}}}{\frac{\partial
{B\_{\text{tor}}}}{\partial \psi}} + {B\_{\text{pol}}}{\frac{\partial
{B\_{\text{pol}}}}{\partial \psi}}\right)\end{aligned}\\

</div>

</div>

<div id="parallel-derivative-of-the-b-field" class="section">

### Parallel derivative of the B field<a href="#parallel-derivative-of-the-b-field" class="headerlink"
title="Permalink to this heading">#</a>

To get the parallel gradients of the
<span class="math notranslate nohighlight">\\B\\</span> field
components, start with

<div id="equation-eq-db2ds-1" class="math notranslate nohighlight">

<span class="eqno">(103)<a href="#equation-eq-db2ds-1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial s}}\left(B^2\right) = {\frac{\partial
}{\partial s}}\left({B\_{\text{tor}}}^2\right) + {\frac{\partial
}{\partial s}}\left({B\_{\text{pol}}}^2\right)\end{aligned}\\

</div>

Using the fact that
<span class="math notranslate nohighlight">\\R{B\_{\text{tor}}}\\</span>
is constant along
<span class="math notranslate nohighlight">\\s\\</span>,

<div id="equation-eq-dr2btor2ds" class="math notranslate nohighlight">

<span class="eqno">(104)<a href="#equation-eq-dr2btor2ds" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial s}}\left(R^2{B\_{\text{tor}}}^2\right) =
R^2{\frac{\partial }{\partial s}}\left({B\_{\text{tor}}}^2\right) +
{B\_{\text{tor}}}^2{\frac{\partial }{\partial s}}\left(R^2\right) =
0\end{aligned}\\

</div>

which gives

<div id="equation-eq-dbtor2ds" class="math notranslate nohighlight">

<span class="eqno">(105)<a href="#equation-eq-dbtor2ds" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial s}}\left({B\_{\text{tor}}}^2\right) =
-\frac{{B\_{\text{tor}}}^2}{R^2}{\frac{\partial }{\partial
s}}\left(R^2\right)\end{aligned}\\

</div>

The poloidal field can be calculated from

<div id="equation-eq-dr2bpol2ds" class="math notranslate nohighlight">

<span class="eqno">(106)<a href="#equation-eq-dr2bpol2ds" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial s}}\left(\nabla\psi \cdot \nabla\psi\right) =
{\frac{\partial }{\partial s}}\left(R^2{B\_{\text{pol}}}^2\right) =
R^2{\frac{\partial }{\partial s}}\left({B\_{\text{pol}}}^2\right) +
{B\_{\text{pol}}}^2{\frac{\partial }{\partial
s}}\left(R^2\right)\end{aligned}\\

</div>

Using equation
<a href="#equation-eq-flinenablapsi" class="reference internal">(86)</a>,
<span class="math notranslate nohighlight">\\\nabla\psi \cdot
\nabla\psi\\</span> can also be written as

<div id="equation-eq-gradpsi2" class="math notranslate nohighlight">

<span class="eqno">(107)<a href="#equation-eq-gradpsi2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\psi \cdot \nabla\psi = B^2R^2\left\[\left({\frac{\partial
R}{\partial s}}\right)^2 + \left({\frac{\partial Z}{\partial
s}}\right)^2\right\]\end{aligned}\\

</div>

and so (unsurprisingly)

<div id="equation-eq-bpol2overb2" class="math notranslate nohighlight">

<span class="eqno">(108)<a href="#equation-eq-bpol2overb2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\frac{{B\_{\text{pol}}}^2}{B^2} = \left\[\left({\frac{\partial
R}{\partial s}}\right)^2 + \left({\frac{\partial Z}{\partial
s}}\right)^2\right\]\end{aligned}\\

</div>

Hence

<div id="equation-eq-dbpol2ds-1" class="math notranslate nohighlight">

<span class="eqno">(109)<a href="#equation-eq-dbpol2ds-1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial s}}\left({B\_{\text{pol}}}^2\right) =
B^2{\frac{\partial }{\partial s}}\left\[\left({\frac{\partial
R}{\partial s}}\right)^2 + \left({\frac{\partial Z}{\partial
s}}\right)^2\right\] + \frac{{B\_{\text{pol}}}^2}{B^2}{\frac{\partial
}{\partial s}}\left(B^2\right)\end{aligned}\\

</div>

Which gives

<div id="equation-eq-db2ds-2" class="math notranslate nohighlight">

<span class="eqno">(110)<a href="#equation-eq-db2ds-2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial s}}\left(B^2\right) =
-\frac{B^2}{R^2}{\frac{\partial }{\partial s}}\left(R^2\right) +
\frac{B^4}{{B\_{\text{tor}}}^2}{\frac{\partial }{\partial
s}}\left\[\left({\frac{\partial R}{\partial s}}\right)^2 +
\left({\frac{\partial Z}{\partial s}}\right)^2\right\]\end{aligned}\\

</div>

<div id="equation-eq-dbpol2ds-2" class="math notranslate nohighlight">

<span class="eqno">(111)<a href="#equation-eq-dbpol2ds-2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial s}}\left({B\_{\text{pol}}}^2\right) =
\left(1 +
\frac{{B\_{\text{pol}}}^2}{{B\_{\text{tor}}}^2}\right)B^2{\frac{\partial
}{\partial s}}\left\[\left({\frac{\partial R}{\partial s}}\right)^2 +
\left({\frac{\partial Z}{\partial s}}\right)^2\right\] -
\frac{{B\_{\text{pol}}}^2}{R^2}{\frac{\partial }{\partial
s}}\left(R^2\right)\end{aligned}\\

</div>

</div>

<div id="magnetic-shear-from-j-x-b" class="section">

### Magnetic shear from J x B<a href="#magnetic-shear-from-j-x-b" class="headerlink"
title="Permalink to this heading">#</a>

Re-arranging the radial force balance equation
<a href="#equation-eq-xbalance1" class="reference internal">(61)</a>
gives

<div id="equation-eq-radialforcebalancerearranged"
class="math notranslate nohighlight">

<span class="eqno">(112)<a href="#equation-eq-radialforcebalancerearranged" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\frac{{B\_{\text{pol}}}^2R}{{B\_{\text{tor}}}}{\frac{\partial
\nu}{\partial \psi}} +
\nu\left(\frac{2RB}{{B\_{\text{tor}}}}{\frac{\partial B}{\partial
\psi}} + \frac{B^2}{{B\_{\text{tor}}}}{\frac{\partial R}{\partial
\psi}} - \frac{B^2R}{{B\_{\text{tor}}}^2}{\frac{\partial
{B\_{\text{tor}}}}{\partial \psi}}\right) +
\frac{\mu_0{h\_\theta}}{{B\_{\text{pol}}}}{\frac{\partial P}{\partial
\psi}} = 0\end{aligned}\\

</div>

</div>

<div id="magnetic-shear" class="section">

### Magnetic shear<a href="#magnetic-shear" class="headerlink"
title="Permalink to this heading">#</a>

The field-line pitch is given by

<div id="equation-eq-fieldlinepitch2"
class="math notranslate nohighlight">

<span class="eqno">(113)<a href="#equation-eq-fieldlinepitch2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} \nu =
\frac{{h\_\theta}{B\_{\text{tor}}}}{{B\_{\text{pol}}}R}\end{aligned}\\

</div>

and so

<div id="equation-eq-magneticshear1"
class="math notranslate nohighlight">

<span class="eqno">(114)<a href="#equation-eq-magneticshear1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial \nu}{\partial \psi}} =
\frac{\nu}{{h\_\theta}}{\frac{\partial {h\_\theta}}{\partial \psi}} +
\frac{\nu}{{B\_{\text{tor}}}}{\frac{\partial {B\_{\text{tor}}}}{\partial
\psi}} - \frac{\nu}{{B\_{\text{pol}}}}{\frac{\partial
{B\_{\text{pol}}}}{\partial \psi}} - \frac{\nu}{R}{\frac{\partial
R}{\partial \psi}}\end{aligned}\\

</div>

The last three terms are given in the previous section, but
<span class="math notranslate nohighlight">\\\partial{h\_\theta}/\partial\psi\\</span>
needs to be evaluated

</div>

<div id="psi-derivative-of-h" class="section">

### psi derivative of h<a href="#psi-derivative-of-h" class="headerlink"
title="Permalink to this heading">#</a>

From the expression for curvature (equation
<a href="#equation-eq-curvature" class="reference internal">(70)</a>),
and using <span class="math notranslate nohighlight">\\\nabla x \cdot
\nabla \psi =
{\sigma\_{B\text{pol}}}\left(R{B\_{\text{pol}}}\right)^2\\</span> and
<span class="math notranslate nohighlight">\\\nabla z\cdot\nabla \psi =
-I \left(R{B\_{\text{pol}}}\right)^2\\</span>

<div id="equation-eq-kappadotgradpsi1"
class="math notranslate nohighlight">

<span class="eqno">(115)<a href="#equation-eq-kappadotgradpsi1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{\kappa}}\cdot\nabla\psi =& -{\sigma\_{B\text{pol}}}
\frac{{B\_{\text{pol}}}}{B{h\_\theta}}{\left({R{B\_{\text{pol}}}}\right)^2}\left\[{\frac{\partial
}{\partial x}}\left(\frac{B{h\_\theta}}{{B\_{\text{pol}}}}\right) -
{\sigma_y\sigma\_{B\text{pol}}}{\frac{\partial }{\partial
y}}\left(\frac{{B\_{\text{tor}}}IR}{B}\right)\right\] \\ &-
\sigma_yI{\left({R{B\_{\text{pol}}}}\right)^2}
\frac{{B\_{\text{pol}}}}{B{h\_\theta}}{\frac{\partial }{\partial
y}}\left(\frac{{B\_{\text{tor}}}R}{B}\right)\end{aligned}\end{split}\\

</div>

The second and third terms partly cancel, and using
<span class="math notranslate nohighlight">\\\sigma_y\sigma\_{B\text{pol}}{\frac{\partial
I}{\partial y}} = {\frac{\partial \nu}{\partial x}}\\</span>

<div id="equation-eq-kappadotgradpsi2"
class="math notranslate nohighlight">

<span class="eqno">(116)<a href="#equation-eq-kappadotgradpsi2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\frac{{\boldsymbol{\kappa}}\cdot\nabla\psi}{{\left({R{B\_{\text{pol}}}}\right)^2}}
=&
-{\sigma\_{B\text{pol}}}\frac{{B\_{\text{pol}}}}{B{h\_\theta}}{\frac{\partial
}{\partial x}}\left(\frac{B{h\_\theta}}{{B\_{\text{pol}}}}\right) +
{\sigma\_{B\text{pol}}}\frac{{B\_{\text{pol}}}}{B{h\_\theta}}\frac{{B\_{\text{tor}}}R}{B}{\frac{\partial
\nu}{\partial x}} \\ =&
-{\sigma\_{B\text{pol}}}\frac{{B\_{\text{pol}}}}{B{h\_\theta}}\left\[{\frac{\partial
}{\partial x}}\left(\frac{B{h\_\theta}}{{B\_{\text{pol}}}}\right) -
\frac{{B\_{\text{tor}}} R}{B}{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}{h\_\theta}}{{B\_{\text{pol}}}R}\right)\right\]
\\ =&
-{\sigma\_{B\text{pol}}}\frac{{B\_{\text{pol}}}}{B{h\_\theta}}\left\[{h\_\theta}{\frac{\partial
}{\partial x}}\left(\frac{B}{{B\_{\text{pol}}}}\right) -
{h\_\theta}\frac{{B\_{\text{tor}}}R}{B}{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}}{{B\_{\text{pol}}}R}\right) +
\frac{B^2}{B{B\_{\text{pol}}}}{\frac{\partial {h\_\theta}}{\partial
x}} - \frac{{B\_{\text{tor}}}^2}{B{B\_{\text{pol}}}}{\frac{\partial
{h\_\theta}}{\partial x}}\right\] \\ =& -{\sigma\_{B\text{pol}}}
\frac{{B\_{\text{pol}}^2}}{B^2{h\_\theta}}{\frac{\partial
{h\_\theta}}{\partial x}} -
{\sigma\_{B\text{pol}}}\frac{{B\_{\text{pol}}}}{B^2}\left\[B{\frac{\partial
}{\partial x}}\left(\frac{B}{{B\_{\text{pol}}}}\right) -
{B\_{\text{tor}}} R{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}}{{B\_{\text{pol}}}R}\right)\right\]\end{aligned}\end{split}\\

</div>

Writing

<div id="equation-eq-kappadotgradpsiintermediateidentity"
class="math notranslate nohighlight">

<span class="eqno">(117)<a href="#equation-eq-kappadotgradpsiintermediateidentity"
class="headerlink" title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
B{\frac{\partial }{\partial x}}\left(\frac{B}{{B\_{\text{pol}}}}\right)
=& {\frac{\partial }{\partial
x}}\left(\frac{B^2}{{B\_{\text{pol}}}}\right) -
\frac{B}{{B\_{\text{pol}}}}{\frac{\partial B}{\partial x}} \\
{B\_{\text{tor}}}R{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}}{{B\_{\text{pol}}}R}\right) =&
{\frac{\partial }{\partial
x}}\left(\frac{{B\_{\text{tor}}}^2}{{B\_{\text{pol}}}}\right) -
\frac{{B\_{\text{tor}}}}{{B\_{\text{pol}}}R}{\frac{\partial }{\partial
x}}\left({B\_{\text{tor}}} R\right)\end{aligned}\end{split}\\

</div>

and using <span class="math notranslate nohighlight">\\B{\frac{\partial
B}{\partial x}} = {B\_{\text{tor}}}{\frac{\partial
{B\_{\text{tor}}}}{\partial x}} + {B\_{\text{pol}}}{\frac{\partial
{B\_{\text{pol}}}}{\partial x}}\\</span>, this simplifies to give

<div id="equation-eq-dhdpsi" class="math notranslate nohighlight">

<span class="eqno">(118)<a href="#equation-eq-dhdpsi" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\frac{{\boldsymbol{\kappa}}\cdot\nabla\psi}{{\left({R{B\_{\text{pol}}}}\right)^2}}
=
-{\sigma\_{B\text{pol}}}\frac{{B\_{\text{pol}}}^2}{B^2{h\_\theta}}{\frac{\partial
{h\_\theta}}{\partial x}} -
{\sigma\_{B\text{pol}}}\frac{{B\_{\text{tor}}}^2}{B^2 R}{\frac{\partial
R}{\partial x}} \end{aligned}\\

</div>

This can be transformed into an expression for
<span class="math notranslate nohighlight">\\{\frac{\partial
{h\_\theta}}{\partial x}}\\</span> involving only derivatives along
field-lines. Writing <span class="math notranslate nohighlight">\\\nabla
R = {\frac{\partial R}{\partial \psi}}\nabla\psi + {\frac{\partial
R}{\partial \theta}}\nabla\theta\\</span>,

<div id="equation-eq-gradrdotgradpsi1"
class="math notranslate nohighlight">

<span class="eqno">(119)<a href="#equation-eq-gradrdotgradpsi1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} \nabla
R \cdot \nabla\psi = {\frac{\partial R}{\partial
\psi}}{\left({R{B\_{\text{pol}}}}\right)^2}\end{aligned}\\

</div>

Using
<a href="#equation-eq-flinenablapsi" class="reference internal">(86)</a>,

<div id="equation-eq-gradrdotgradpsi2"
class="math notranslate nohighlight">

<span class="eqno">(120)<a href="#equation-eq-gradrdotgradpsi2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\psi \cdot \nabla R = -{\sigma\_{B\text{pol}}}B
R\frac{dZ}{ds}\end{aligned}\\

</div>

and so

<div id="equation-eq-drdx" class="math notranslate nohighlight">

<span class="eqno">(121)<a href="#equation-eq-drdx" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial R}{\partial x}} =
-\frac{BR}{{\left({R{B\_{\text{pol}}}}\right)^2}}\frac{dZ}{ds}\end{aligned}\\

</div>

Substituting this and equation
<a href="#equation-eq-flinekappsi" class="reference internal">(87)</a>
for
<span class="math notranslate nohighlight">\\{\boldsymbol{\kappa}}\cdot\nabla\psi\\</span>
into equation
<a href="#equation-eq-dhdpsi" class="reference internal">(118)</a> the
<span class="math notranslate nohighlight">\\{\frac{\partial R}{\partial
x}}\\</span> term cancels with part of the
<span class="math notranslate nohighlight">\\{\boldsymbol{\kappa}}\cdot\nabla\psi\\</span>
term, simplifying to

<div id="equation-eq-dhthetadx" class="math notranslate nohighlight">

<span class="eqno">(122)<a href="#equation-eq-dhthetadx" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial {h\_\theta}}{\partial x}} =
-{h\_\theta}\frac{B^3R}{{B\_{\text{pol}}}^2{\left({R{B\_{\text{pol}}}}\right)^2}}\left\[\frac{d^2Z}{ds^2}\frac{dR}{ds} -
\frac{d^2R}{ds^2}\frac{dZ}{ds}\right\]\end{aligned}\\

</div>

</div>

</div>

<div id="shifted-radial-derivatives" class="section">

<span id="sec-shiftcoords"></span>

## Shifted radial derivatives<a href="#shifted-radial-derivatives" class="headerlink"
title="Permalink to this heading">#</a>

The coordinate system given by equation
<a href="#equation-eq-coordtransform"
class="reference internal">(18)</a> and used in the above sections has a
problem: There is a special poloidal location
<span class="math notranslate nohighlight">\\\theta_0\\</span> where the
radial basis vector
<span class="math notranslate nohighlight">\\{\boldsymbol{e}}\_x\\</span>
is purely in the
<span class="math notranslate nohighlight">\\\nabla\psi\\</span>
direction. Moving away from this location, the coordinate system becomes
sheared in the toroidal direction.

Making the substitution

<div id="equation-eq-ddx" class="math notranslate nohighlight">

<span class="eqno">(123)<a href="#equation-eq-ddx" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\frac{\partial }{\partial x}} = {\frac{\partial }{\partial \psi}} +
I{\frac{\partial }{\partial z}}\end{aligned}\\

</div>

we also get the mixed derivative

<div id="equation-eq-d2dzdx" class="math notranslate nohighlight">

<span class="eqno">(124)<a href="#equation-eq-d2dzdx" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\frac{\partial^2}{\partial z\partial x} =& {\frac{\partial }{\partial
z}}{\frac{\partial }{\partial \psi}} + {\frac{\partial I}{\partial
z}}{\frac{\partial }{\partial z}} + I\frac{\partial^2}{\partial z^2}
\nonumber \\ =& \frac{\partial^2}{\partial z\partial \psi} +
I\frac{\partial^2}{\partial z^2}\end{aligned}\end{split}\\

</div>

and second-order <span class="math notranslate nohighlight">\\x\\</span>
derivative

<div id="equation-eq-d2dx2" class="math notranslate nohighlight">

<span class="eqno">(125)<a href="#equation-eq-d2dx2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\frac{\partial^2}{\partial x^2} =& \frac{\partial^2}{\partial \psi^2} +
{\frac{\partial }{\partial \psi}}\left(I{\frac{\partial }{\partial
z}}\right) + I{\frac{\partial }{\partial z}}\left({\frac{\partial
}{\partial \psi}} + I{\frac{\partial }{\partial z}}\right) \nonumber \\
=& \frac{\partial^2}{\partial \psi^2} + I^2\frac{\partial^2}{\partial
z^2} + 2I\frac{\partial^2}{\partial z\partial \psi} + {\frac{\partial
I}{\partial \psi}}{\frac{\partial }{\partial
z}}\end{aligned}\end{split}\\

</div>

<div id="perpendicular-laplacian" class="section">

### Perpendicular Laplacian<a href="#perpendicular-laplacian" class="headerlink"
title="Permalink to this heading">#</a>

<div id="equation-eq-laplace-perp1"
class="math notranslate nohighlight">

<span class="eqno">(126)<a href="#equation-eq-laplace-perp1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\_\perp^2=
{\left({R{B\_{\text{pol}}}}\right)^2}\left\[{\frac{\partial^2 }{\partial
{x}^2}} - 2I\frac{\partial^2}{\partial z\partial x} + \left(I^2 +
\frac{B^2}{\left({R{B\_{\text{pol}}}}\right)^4}\right){\frac{\partial^2
}{\partial {z}^2}}\right\]\end{aligned}\\

</div>

transforms to

<div id="equation-eq-laplace-perp2"
class="math notranslate nohighlight">

<span class="eqno">(127)<a href="#equation-eq-laplace-perp2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\_\perp^2=
{\left({R{B\_{\text{pol}}}}\right)^2}\left\[{\frac{\partial^2 }{\partial
{\psi}^2}} + {\frac{\partial I}{\partial \psi}}{\frac{\partial
}{\partial z}} +
\frac{B^2}{\left({R{B\_{\text{pol}}}}\right)^4}{\frac{\partial^2
}{\partial {z}^2}}\right\] \end{aligned}\\

</div>

The extra term involving
<span class="math notranslate nohighlight">\\I\\</span> disappears, but
only if both the <span class="math notranslate nohighlight">\\x\\</span>
and <span class="math notranslate nohighlight">\\z\\</span> first
derivatives are taken into account:

<div id="equation-eq-laplace-perp3"
class="math notranslate nohighlight">

<span class="eqno">(128)<a href="#equation-eq-laplace-perp3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\_\perp^2=
{\left({R{B\_{\text{pol}}}}\right)^2}\left\[{\frac{\partial^2 }{\partial
{x}^2}} - 2I\frac{\partial^2}{\partial z\partial x} + \left(I^2 +
\frac{B^2}{\left({R{B\_{\text{pol}}}}\right)^4}\right){\frac{\partial^2
}{\partial {z}^2}}\right\] + \nabla^2 x {\frac{\partial }{\partial x}} +
\nabla^2 z{\frac{\partial }{\partial z}}\end{aligned}\\

</div>

with

<div id="equation-eq-grad2x" class="math notranslate nohighlight">

<span class="eqno">(129)<a href="#equation-eq-grad2x" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla^2 x = \frac{1}{J}{\frac{\partial }{\partial
x}}\left\[J{\left({R{B\_{\text{pol}}}}\right)^2}\right\]\end{aligned}\\

</div>

<div id="equation-eq-grad2z" class="math notranslate nohighlight">

<span class="eqno">(130)<a href="#equation-eq-grad2z" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla^2 z =& \frac{1}{J}\left\[-{\frac{\partial }{\partial
x}}\left(JI{\left({R{B\_{\text{pol}}}}\right)^2}\right) -
{\frac{\partial }{\partial
y}}\left(\frac{{B\_{\text{tor}}}}{{B\_{\text{pol}}}^2R}\right)\right\]
\nonumber \\ =& \frac{1}{J}\left\[-I{\frac{\partial }{\partial
x}}\left(J{\left({R{B\_{\text{pol}}}}\right)^2}\right) - {\frac{\partial
I}{\partial x}}J{\left({R{B\_{\text{pol}}}}\right)^2}- {\frac{\partial
}{\partial
y}}\left(\frac{{B\_{\text{tor}}}}{{B\_{\text{pol}}}^2R}\right)\right\]
\end{aligned}\end{split}\\

</div>

where <span class="math notranslate nohighlight">\\J={h\_\theta}/
{B\_{\text{pol}}}\\</span> is the Jacobian. Transforming into
<span class="math notranslate nohighlight">\\\psi\\</span> derivatives,
the middle term of equation
<a href="#equation-eq-grad2z" class="reference internal">(130)</a>
cancels the <span class="math notranslate nohighlight">\\I\\</span> term
in equation <a href="#equation-eq-laplace-perp2"
class="reference internal">(127)</a>, but introduces another
<span class="math notranslate nohighlight">\\I\\</span> term (first term
in equation
<a href="#equation-eq-grad2z" class="reference internal">(130)</a>).
This term cancels with the
<span class="math notranslate nohighlight">\\\nabla^2 x\\</span> term
when <span class="math notranslate nohighlight">\\{\frac{\partial
}{\partial x}}\\</span> is expanded, so the full expression for
<span class="math notranslate nohighlight">\\\nabla\_\perp^2\\</span>
using <span class="math notranslate nohighlight">\\\psi\\</span>
derivatives is:

<div id="equation-eq-laplaceperp-shift"
class="math notranslate nohighlight">

<span class="eqno">(131)<a href="#equation-eq-laplaceperp-shift" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla\_\perp^2=&
{\left({R{B\_{\text{pol}}}}\right)^2}\left\[{\frac{\partial^2 }{\partial
{\psi}^2}} +
\frac{B^2}{\left({R{B\_{\text{pol}}}}\right)^4}{\frac{\partial^2
}{\partial {z}^2}}\right\] \nonumber \\ &+ \frac{1}{J}{\frac{\partial
}{\partial
\psi}}\left\[J{\left({R{B\_{\text{pol}}}}\right)^2}\right\]{\frac{\partial
}{\partial \psi}} - \frac{1}{J}{\frac{\partial }{\partial
y}}\left(\frac{{B\_{\text{tor}}}}{{B\_{\text{pol}}}^2R}\right){\frac{\partial
}{\partial z}} \end{aligned}\end{split}\\

</div>

<div id="in-orthogonal-psi-theta-zeta-flux-coordinates" class="section">

#### In orthogonal (psi, theta, zeta) flux coordinates<a href="#in-orthogonal-psi-theta-zeta-flux-coordinates"
class="headerlink" title="Permalink to this heading">#</a>

For comparison, the perpendicular Laplacian can be derived in orthogonal
“flux” coordinates

<div id="equation-eq-fluxcoordsscalefactors"
class="math notranslate nohighlight">

<span class="eqno">(132)<a href="#equation-eq-fluxcoordsscalefactors" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\left|\nabla\psi\right| = {R{B\_{\text{pol}}}}\qquad
\left|\nabla\theta\right| = 1/{h\_\theta}\qquad \left|\nabla\zeta\right|
= 1/R\end{aligned}\\

</div>

The Laplacian operator is given by

<div id="equation-eq-fluxcoordslaplace"
class="math notranslate nohighlight">

<span class="eqno">(133)<a href="#equation-eq-fluxcoordslaplace" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla^2 A =& {\left({R{B\_{\text{pol}}}}\right)^2}{\frac{\partial^2
A}{\partial {\psi}^2}} + \frac{1}{{h\_\theta}^2}{\frac{\partial^2
A}{\partial {\theta}^2}} + \frac{1}{R^2}{\frac{\partial^2 A}{\partial
{\zeta}^2}} \nonumber \\ &+ \frac{1}{J}{\frac{\partial }{\partial
\psi}}\left\[J{\left({R{B\_{\text{pol}}}}\right)^2}\right\]{\frac{\partial
A}{\partial \psi}} + \frac{1}{J}{\frac{\partial }{\partial
\theta}}\left(J/{h\_\theta}^2\right){\frac{\partial A}{\partial
\theta}}\end{aligned}\end{split}\\

</div>

parallel derivative by

<div id="equation-eq-fluxcoordsgradpar"
class="math notranslate nohighlight">

<span class="eqno">(134)<a href="#equation-eq-fluxcoordsgradpar" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\partial\_{||} \equiv {\boldsymbol{b}}\cdot\nabla =
\frac{{B\_{\text{pol}}}}{B{h\_\theta}}{\frac{\partial }{\partial
\theta}} + \frac{{B\_{\text{tor}}}}{RB}{\frac{\partial }{\partial
\zeta}}\end{aligned}\\

</div>

and so

<div id="equation-eq-fluxcoordsgradpar2"
class="math notranslate nohighlight">

<span class="eqno">(135)<a href="#equation-eq-fluxcoordsgradpar2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\partial^2\_{||}A \equiv \partial\_{||}\left(\partial\_{||}A\right) =&
\left(\frac{{B\_{\text{pol}}}}{B{h\_\theta}}\right)^2{\frac{\partial^2
A}{\partial {\theta}^2}} +
\left(\frac{{B\_{\text{tor}}}}{RB}\right)^2{\frac{\partial^2 A}{\partial
{\zeta}^2}} \nonumber \\ &+
2\frac{{B\_{\text{pol}}}{B\_{\text{tor}}}}{B^2{h\_\theta}R}\frac{\partial^2
A}{\partial\theta\partial\zeta} \nonumber \\ &+ {\frac{\partial
}{\partial
\theta}}\left(\frac{{B\_{\text{pol}}}}{B{h\_\theta}}\right){\frac{\partial
A}{\partial \theta}} + {\frac{\partial }{\partial
\theta}}\left(\frac{{B\_{\text{tor}}}}{RB}\right){\frac{\partial
A}{\partial \zeta}}\end{aligned}\end{split}\\

</div>

Hence in orthogonal flux coordinates, the perpendicular Laplacian is:

<div id="equation-eq-fluxcoordinateslaplaceperp"
class="math notranslate nohighlight">

<span class="eqno">(136)<a href="#equation-eq-fluxcoordinateslaplaceperp" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\_\perp^2\equiv \nabla^2 - \partial\_{||}^2 =
{\left({R{B\_{\text{pol}}}}\right)^2}\left\[{\frac{\partial^2 }{\partial
{\psi}^2}} + \frac{1}{R^4B^2}{\frac{\partial^2 }{\partial
{\zeta^2}^2}}\right\] +
\frac{{B\_{\text{tor}}}^2}{{h\_\theta}^2B^2}{\frac{\partial^2 }{\partial
{\theta}^2}} + \cdots \end{aligned}\\

</div>

where the neglected terms are first-order derivatives. The coefficient
for the second-order
<span class="math notranslate nohighlight">\\z\\</span> derivative
differs from equation <a href="#equation-eq-laplaceperp-shift"
class="reference internal">(131)</a>, and equation
<a href="#equation-eq-fluxcoordinateslaplaceperp"
class="reference internal">(136)</a> still contains a derivative in
<span class="math notranslate nohighlight">\\\theta\\</span>. This shows
that the transformation made to get equation
<a href="#equation-eq-laplaceperp-shift"
class="reference internal">(131)</a> doesn’t result in the same answer
as orthogonal flux coordinates: equation
<a href="#equation-eq-laplaceperp-shift"
class="reference internal">(131)</a> is in field-aligned coordinates.

Note that in the limit of
<span class="math notranslate nohighlight">\\{B\_{\text{pol}}}=
B\\</span>, both equations <a href="#equation-eq-laplaceperp-shift"
class="reference internal">(131)</a> and
<a href="#equation-eq-fluxcoordinateslaplaceperp"
class="reference internal">(136)</a> are the same, as they should be.

</div>

</div>

<div id="operator-b-x-nabla-phi-dot-nabla-a" class="section">

### Operator B x Nabla Phi Dot Nabla A<a href="#operator-b-x-nabla-phi-dot-nabla-a" class="headerlink"
title="Permalink to this heading">#</a>

<div id="equation-eq-bcrossgradphidotgrada1"
class="math notranslate nohighlight">

<span class="eqno">(137)<a href="#equation-eq-bcrossgradphidotgrada1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{B}}\times\nabla\phi\cdot\nabla A =& \left({\frac{\partial
\phi}{\partial x}}{\frac{\partial A}{\partial y}} - {\frac{\partial
\phi}{\partial y}}{\frac{\partial A}{\partial
x}}\right)\left(-{B\_{\text{tor}}}\frac{{R{B\_{\text{pol}}}}}{{h\_\theta}}\right)
\\ &+ \left({\frac{\partial \phi}{\partial x}}{\frac{\partial
A}{\partial z}} - {\frac{\partial \phi}{\partial z}}{\frac{\partial
A}{\partial x}}\right)\left(-B^2\right) \\ &- \left({\frac{\partial
\phi}{\partial y}}{\frac{\partial A}{\partial z}} - {\frac{\partial
\phi}{\partial z}}{\frac{\partial A}{\partial
y}}\right)\left(I{B\_{\text{tor}}}\frac{{R{B\_{\text{pol}}}}}{{h\_\theta}}\right)\end{aligned}\end{split}\\

</div>

<div id="equation-eq-bcrossgradphidotgrada2"
class="math notranslate nohighlight">

<span class="eqno">(138)<a href="#equation-eq-bcrossgradphidotgrada2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{B}}\times\nabla\phi\cdot\nabla A =& \left({\frac{\partial
\phi}{\partial \psi}}{\frac{\partial A}{\partial y}} + I {\frac{\partial
\phi}{\partial z}}{\frac{\partial A}{\partial y}} - {\frac{\partial
\phi}{\partial y}}{\frac{\partial A}{\partial \psi}} - I{\frac{\partial
\phi}{\partial y}}{\frac{\partial A}{\partial
z}}\right)\left(-{B\_{\text{tor}}}\frac{{R{B\_{\text{pol}}}}}{{h\_\theta}}\right)
\\ &+ \left({\frac{\partial \phi}{\partial \psi}}{\frac{\partial
A}{\partial z}} + I{\frac{\partial \phi}{\partial z}}{\frac{\partial
A}{\partial z}} - {\frac{\partial \phi}{\partial z}}{\frac{\partial
A}{\partial \psi}} - I{\frac{\partial \phi}{\partial z}}{\frac{\partial
A}{\partial z}}\right)\left(-B^2\right) \\ &- \left({\frac{\partial
\phi}{\partial y}}{\frac{\partial A}{\partial z}} - {\frac{\partial
\phi}{\partial z}}{\frac{\partial A}{\partial
y}}\right)\left(I{B\_{\text{tor}}}\frac{{R{B\_{\text{pol}}}}}{{h\_\theta}}\right)\end{aligned}\end{split}\\

</div>

<div id="equation-eq-bcrossgradphidotgrada3"
class="math notranslate nohighlight">

<span class="eqno">(139)<a href="#equation-eq-bcrossgradphidotgrada3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{B}}\times\nabla\phi\cdot\nabla A =& \left({\frac{\partial
\phi}{\partial \psi}}{\frac{\partial A}{\partial y}} - {\frac{\partial
\phi}{\partial y}}{\frac{\partial A}{\partial
\psi}}\right)\left(-{B\_{\text{tor}}}\frac{{R{B\_{\text{pol}}}}}{{h\_\theta}}\right)
\nonumber \\ &+ \left({\frac{\partial \phi}{\partial
\psi}}{\frac{\partial A}{\partial z}} - {\frac{\partial \phi}{\partial
z}}{\frac{\partial A}{\partial \psi}}
\right)\left(-B^2\right)\end{aligned}\end{split}\\

</div>

</div>

</div>

<div id="useful-identities" class="section">

## Useful identities<a href="#useful-identities" class="headerlink"
title="Permalink to this heading">#</a>

<div id="mathbf-b-times-mathbf-kappa-cdot-nabla-psi-simeq-rb-zeta-partial-ln-b"
class="section">

### <span class="math notranslate nohighlight">\\\mathbf{b}\times\mathbf{\kappa}\cdot\nabla\psi \simeq -RB\_\zeta\partial\_{||}\ln B\\</span><a
href="#mathbf-b-times-mathbf-kappa-cdot-nabla-psi-simeq-rb-zeta-partial-ln-b"
class="headerlink" title="Permalink to this heading">#</a>

Using
<span class="math notranslate nohighlight">\\\mathbf{b}\times\mathbf{\kappa}
\simeq \frac{B}{2}\nabla\times\frac{\mathbf{b}}{B}\\</span>, and working
in orthogonal <span class="math notranslate nohighlight">\\\left(\psi,
\theta, \zeta\right)\\</span> coordinates. The magnetic field unit
vector is:

<div id="equation-eq-bcomponents2" class="math notranslate nohighlight">

<span class="eqno">(140)<a href="#equation-eq-bcomponents2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\mathbf{b} =
\frac{B\_\theta h\_\theta}{B}\nabla\theta + \frac{B\_\zeta
R}{B}\nabla\zeta\\

</div>

and using the definition of curl (equation
<a href="#equation-eq-curlcurvilinear"
class="reference internal">(156)</a>) we can write

<div id="equation-eq-bcrosskappa2" class="math notranslate nohighlight">

<span class="eqno">(141)<a href="#equation-eq-bcrosskappa2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\mathbf{b}\times\mathbf{\kappa}
\simeq \frac{B}{2}\nabla\times\frac{\mathbf{b}}{B} =
\frac{B}{2}\frac{B\_\theta}{h\_\theta}\left\[\frac{\partial}{\partial\theta}\left(\frac{B\_\zeta
R}{B^2}\right) - \frac{\partial}{\partial\zeta}\left(\frac{B\_\theta
h\_\theta}{B^2}\right)\right\]\mathbf{e}\_\psi +
\left\[\cdot\right\]\mathbf{e}\_\theta +
\left\[\cdot\right\]\mathbf{e}\_\zeta\\

</div>

so that when dotted with
<span class="math notranslate nohighlight">\\\nabla\psi\\</span>, only
the first bracket survives. The parallel gradient is

<div id="equation-eq-gradpar2" class="math notranslate nohighlight">

<span class="eqno">(142)<a href="#equation-eq-gradpar2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\partial\_{||} =
\mathbf{b}\cdot\nabla =
\frac{B\_\theta}{Bh\_\theta}\frac{\partial}{\partial\theta} +
\frac{B\_\theta}{BR}\frac{\partial}{\partial\zeta}\\

</div>

Neglecting derivatives for axisymmetric equilibrium

<div id="equation-eq-curlboverbdotgradpsi1"
class="math notranslate nohighlight">

<span class="eqno">(143)<a href="#equation-eq-curlboverbdotgradpsi1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\frac{B}{2}\nabla\times\frac{\mathbf{b}}{B}\cdot\nabla\psi
= \frac{B}{2}B\partial\_{||}\left(\frac{B\_\zeta R}{B^2}\right)\\

</div>

Since <span class="math notranslate nohighlight">\\B\_\zeta R\\</span>
is a flux function, this can be written as

<div id="equation-eq-curlboverbdotgradpsi2"
class="math notranslate nohighlight">

<span class="eqno">(144)<a href="#equation-eq-curlboverbdotgradpsi2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\frac{B}{2}\nabla\times\frac{\mathbf{b}}{B}\cdot\nabla\psi
= -B\_\zeta R\frac{1}{B}\partial\_{||} B\\

</div>

and so

<div id="equation-eq-curlboverbdotgradpsi3"
class="math notranslate nohighlight">

<span class="eqno">(145)<a href="#equation-eq-curlboverbdotgradpsi3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\mathbf{b}\times\mathbf{\kappa}\cdot\nabla\psi
\simeq -RB\_\zeta\partial\_{||}\ln B\\

</div>

</div>

</div>

<div id="differential-geometry" class="section">

## Differential geometry<a href="#differential-geometry" class="headerlink"
title="Permalink to this heading">#</a>

<div class="admonition warning">

Warning

The following are notes from <a href="#haeseleer" id="id4"
class="reference internal"><span>[haeseleer]</span></a>. If you are new
to this topic it is strongly suggested to read
<a href="#haeseleer" id="id5"
class="reference internal"><span>[haeseleer]</span></a> chapter 2
instead, as here not all terms are defined, and the discussion of co-
and contra variant components is incomplete. Similiarly, the notation is
based on <a href="#haeseleer" id="id6"
class="reference internal"><span>[haeseleer]</span></a> and not
explained in detail.

</div>

Sets of vectors
<span class="math notranslate nohighlight">\\\left\\\mathbf{A, B,
C}\right\\\\</span> and
<span class="math notranslate nohighlight">\\\left\\\mathbf{a, b,
c}\right\\\\</span> are reciprocal if

<div id="equation-eq-reciprocalvectors1"
class="math notranslate nohighlight">

<span class="eqno">(146)<a href="#equation-eq-reciprocalvectors1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\mathbf{A\cdot a} = \mathbf{B\cdot b} = \mathbf{C\cdot c} = 1\\
\mathbf{A\cdot b} = \mathbf{A\cdot c} = \mathbf{B\cdot a} =
\mathbf{B\cdot c} = \mathbf{C\cdot a} = \mathbf{C\cdot b} = 0
\\\end{aligned}\end{split}\\

</div>

which implies that
<span class="math notranslate nohighlight">\\\left\\\mathbf{A, B,
C}\right\\\\</span> and
<span class="math notranslate nohighlight">\\\left\\\mathbf{a, b,
c}\right\\\\</span> are each linearly independent. Equivalently,

<div id="equation-eq-reciprocalvectors2"
class="math notranslate nohighlight">

<span class="eqno">(147)<a href="#equation-eq-reciprocalvectors2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\mathbf{a} = \frac{\mathbf{B\times C}}{\mathbf{A\cdot\left(B\times
C\right)}}\qquad {\boldsymbol{b}}= \frac{\mathbf{C\times
A}}{\mathbf{B\cdot\left(C\times A\right)}}\qquad \mathbf{c} =
\frac{\mathbf{A\times B}}{\mathbf{C\cdot\left(A\times
B\right)}}\end{aligned}\\

</div>

Either of these sets can be used as a basis, and any vector
<span class="math notranslate nohighlight">\\\mathbf{w}\\</span> can be
represented as <span class="math notranslate nohighlight">\\\mathbf{w} =
\left(\mathbf{w\cdot a}\right)\mathbf{A} + \left(\mathbf{w\cdot
b}\right){\boldsymbol{B}}+ \left(\mathbf{w\cdot
c}\right)\mathbf{C}\\</span> or as
<span class="math notranslate nohighlight">\\\mathbf{w} =
\left(\mathbf{w\cdot A}\right)\mathbf{a} + \left(\mathbf{w\cdot
B}\right){\boldsymbol{b}} + \left(\mathbf{w\cdot
C}\right)\mathbf{c}\\</span>. In the Cartesian coordinate system, the
basis vectors are reciprocal to themselves so this distinction is not
needed. For a general set of coordinates
<span class="math notranslate nohighlight">\\\left\\u^1, u^2,
u^3\right\\\\</span>, tangent basis vectors can be defined. If the
Cartesian coordinates of a point are given by
<span class="math notranslate nohighlight">\\\left(x, y, z\right) =
\mathbf{R}\left(u^1, u^2, u^3\right)\\</span> then the tangent basis
vectors are:

<div id="equation-eq-tangentbasisvectors"
class="math notranslate nohighlight">

<span class="eqno">(148)<a href="#equation-eq-tangentbasisvectors" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{e}}\_i = \frac{\partial\mathbf{R}}{\partial
u^i}\end{aligned}\\

</div>

and in general these will vary from point to point. The scale factor or
metric coefficient <span class="math notranslate nohighlight">\\h_i
=\left|{\boldsymbol{e}}\_i\right|\\</span> is the distance moved for a
unit change in
<span class="math notranslate nohighlight">\\u^i\\</span>. The unit
vector
<span class="math notranslate nohighlight">\\\hat{{\boldsymbol{e}}}\_i =
{\boldsymbol{e}}\_i/h_i\\</span>. Definition of nabla operator:

<div id="equation-eq-nabladefinition"
class="math notranslate nohighlight">

<span class="eqno">(149)<a href="#equation-eq-nabladefinition" class="headerlink"
title="Permalink to this equation">#</a></span>\\\text{$\nabla\Phi$ of a
function $\Phi$ is defined so that $d\Phi = \nabla\Phi\cdot
d{\mathbf{R}}$}\\

</div>

From the chain rule,
<span class="math notranslate nohighlight">\\d\mathbf{R} =
\frac{\partial\mathbf{R}}{\partial u^i}du^i =
{\boldsymbol{e}}\_idu^i\\</span> and substituting
<span class="math notranslate nohighlight">\\\Phi = u^i\\</span>

<div id="equation-eq-dui" class="math notranslate nohighlight">

<span class="eqno">(150)<a href="#equation-eq-dui" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} du^i =
\nabla u^i\cdot{\boldsymbol{e}}\_jdu^j\end{aligned}\\

</div>

which can only be true if
<span class="math notranslate nohighlight">\\\nabla
u^i\cdot{\boldsymbol{e}}\_j = \delta^i_j\\</span> i.e. if

<div id="equation-eq-reciprocaluie-j"
class="math notranslate nohighlight">

<span class="eqno">(151)<a href="#equation-eq-reciprocaluie-j" class="headerlink"
title="Permalink to this equation">#</a></span>\\\text{Sets of vectors
$\boldsymbol{e}^i\equiv\nabla u^i$ and $\boldsymbol{e}\_j$ are
reciprocal}\\

</div>

Since the sets of vectors
<span class="math notranslate nohighlight">\\\left\\{\boldsymbol{e}}^i\right\\\\</span>
and
<span class="math notranslate nohighlight">\\\left\\{\boldsymbol{e}}\_i\right\\\\</span>
are reciprocal, any vector
<span class="math notranslate nohighlight">\\\mathbf{D}\\</span> can be
written as <span class="math notranslate nohighlight">\\\mathbf{D} =
D_i{\boldsymbol{e}}^i = D^i{\boldsymbol{e}}\_i\\</span> where
<span class="math notranslate nohighlight">\\D_i = \mathbf{D\cdot
e}\_i\\</span> are the covariant components and
<span class="math notranslate nohighlight">\\D^i = \mathbf{D\cdot
e}^i\\</span> are the contravariant components. To convert between
covariant and contravariant components, define the metric coefficients
<span class="math notranslate nohighlight">\\g\_{ij} = \mathbf{e_i\cdot
e_j}\\</span> and <span class="math notranslate nohighlight">\\g^{ij} =
\mathbf{e^i\cdot e^j}\\</span> so that
<span class="math notranslate nohighlight">\\{\boldsymbol{e}}\_i =
g\_{ij}{\boldsymbol{e}}^j\\</span>.
<span class="math notranslate nohighlight">\\g\_{ij}\\</span> and
<span class="math notranslate nohighlight">\\g^{ij}\\</span> are
symmetric and if the basis is orthogonal then
<span class="math notranslate nohighlight">\\g\_{ij}=g^{ij} = 0\\</span>
for <span class="math notranslate nohighlight">\\i\neq j\\</span> i.e.
the metric is diagonal.

For a general set of coordinates, the nabla operator can be expressed as

<div id="equation-eq-nabla" class="math notranslate nohighlight">

<span class="eqno">(152)<a href="#equation-eq-nabla" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} \nabla
= \nabla u^i\frac{\partial}{\partial u^i} =
{\boldsymbol{e}}^i\frac{\partial}{\partial u^i}\end{aligned}\\

</div>

and for a general set of (differentiable) coordinates
<span class="math notranslate nohighlight">\\\left\\u^i\right\\\\</span>,
the Laplacian is given by

<div id="equation-eq-laplacegen" class="math notranslate nohighlight">

<span class="eqno">(153)<a href="#equation-eq-laplacegen" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla^2\phi = \frac{1}{J}\frac{\partial}{\partial
u^i}\left(Jg^{ij}\frac{\partial\phi}{\partial u^j}\right)
\end{aligned}\\

</div>

with <span class="math notranslate nohighlight">\\J\\</span> the
determinant of the jacobian matrix
<span class="math notranslate nohighlight">\\J\_{ij}\\</span>, and
<span class="math notranslate nohighlight">\\g\_{ij}=J\_{ki}J\_{kj}\\</span>
and <span class="math notranslate nohighlight">\\\[g^{ij}\] =
\[g\_{ij}\]^{-1}\\</span>. This can be expanded as

<div id="equation-eq-laplace-expand"
class="math notranslate nohighlight">

<span class="eqno">(154)<a href="#equation-eq-laplace-expand" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla^2\phi = g^{ij}\frac{\partial^2\phi}{\partial u^i\partial u^j} +
\underbrace{\frac{1}{J}\frac{\partial}{\partial
u^i}\left(Jg^{ij}\right)}\_{G^j}\frac{\partial\phi}{\partial u^j}
\end{aligned}\\

</div>

where <span class="math notranslate nohighlight">\\G^j\\</span> must
**not** be mistaken as the so called connection coefficients (i.e. the
Christoffel symbols of second kind). Setting
<span class="math notranslate nohighlight">\\\phi = u^k\\</span> in
equation
<a href="#equation-eq-laplacegen" class="reference internal">(153)</a>
gives <span class="math notranslate nohighlight">\\\nabla^2u^k =
G^k\\</span>. Expanding
<a href="#equation-eq-laplacegen" class="reference internal">(153)</a>
and setting
<span class="math notranslate nohighlight">\\\left\\u^i\right\\ =
\left\\x, y, z\right\\\\</span> gives

<div id="equation-eq-general-laplacian"
class="math notranslate nohighlight">

<span class="eqno">(155)<a href="#equation-eq-general-laplacian" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla^2f &= \nabla\cdot\nabla f =
\nabla\cdot\left(\frac{\partial}{\partial x}\nabla x +
\frac{\partial}{\partial y}\nabla y + \frac{\partial}{\partial z}\nabla
z\right) \nonumber \\ =& \frac{\partial^2 f}{\partial x^2}\left|\nabla
x\right|^2 + \frac{\partial^2 f}{\partial y^2}\left|\nabla y\right|^2 +
\frac{\partial^2 f}{\partial z^2}\left|\nabla z\right|^2 \\
&+2\frac{\partial^2 f}{\partial x\partial y}\left(\nabla x\cdot\nabla
y\right) +2\frac{\partial^2 f}{\partial x\partial z}\left(\nabla
x\cdot\nabla z\right) +2\frac{\partial^2 f}{\partial y\partial
z}\left(\nabla y\cdot\nabla z\right) \nonumber \\
&+\nabla^2x\frac{\partial f}{\partial x} +\nabla^2y\frac{\partial
f}{\partial y} + \nabla^2z\frac{\partial f}{\partial z} \nonumber
\end{aligned}\end{split}\\

</div>

Curl defined as:

<div id="equation-eq-curlcurvilinear"
class="math notranslate nohighlight">

<span class="eqno">(156)<a href="#equation-eq-curlcurvilinear" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\times\mathbf{A} = \frac{1}{\sqrt{g}}\sum_k\left(\frac{\partial
A_j}{\partial u_i} - \frac{\partial A_i}{\partial
u_j}\right){\boldsymbol{e}}\_k \qquad i,j,k \texttt{ cyc } 1,2,3
\end{aligned}\\

</div>

Cross-product relation between contravariant and covariant vectors:

<div id="equation-eq-crossproductrelations"
class="math notranslate nohighlight">

<span class="eqno">(157)<a href="#equation-eq-crossproductrelations" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{e}}^i = \frac{1}{J}\left({\boldsymbol{e}}\_j \times
{\boldsymbol{e}}\_k\right) \qquad {\boldsymbol{e}}\_i =
J\left({\boldsymbol{e}}^j \times {\boldsymbol{e}}^k\right) \qquad i,j,k
\texttt{ cyc } 1,2,3\end{aligned}\\

</div>

</div>

<div id="derivation-of-operators-in-the-bout-clebsch-system"
class="section">

## Derivation of operators in the BOUT++ Clebsch system<a href="#derivation-of-operators-in-the-bout-clebsch-system"
class="headerlink" title="Permalink to this heading">#</a>

The Clebsch system in BOUT++ goes like this

<div id="equation-eq-clebschcoordinates"
class="math notranslate nohighlight">

<span class="eqno">(158)<a href="#equation-eq-clebschcoordinates" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{B}}=&\nabla z \times \nabla x\\ =&{\boldsymbol{e}}^z \times
{\boldsymbol{e}}^x\\ J^{-1}{\boldsymbol{e}}\_y=&{\boldsymbol{e}}^z
\times {\boldsymbol{e}}^x\end{aligned}\end{split}\\

</div>

We have

<div id="equation-eq-modb" class="math notranslate nohighlight">

<span class="eqno">(159)<a href="#equation-eq-modb" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
B{\overset{\text{def}}{=}}& \sqrt{{\boldsymbol{B}}\cdot{\boldsymbol{B}}}
= \sqrt{J^{-1}{\boldsymbol{e}}\_y\cdot J^{-1}{\boldsymbol{e}}\_y} =
\sqrt{J^{-2}g\_{yy}}\end{aligned}\\

</div>

Further on

<div id="equation-eq-bdefinitions" class="math notranslate nohighlight">

<span class="eqno">(160)<a href="#equation-eq-bdefinitions" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{B}}=&B{\boldsymbol{b}}\\
{\boldsymbol{b}}=&\frac{{\boldsymbol{B}}}{B}
=\frac{J^{-1}{\boldsymbol{e}}\_y}{\sqrt{J^{-2}g\_{yy}}}
=\frac{\sigma\_{B\text{pol}}{\boldsymbol{e}}\_y}{\sqrt{g\_{yy}}}\end{aligned}\end{split}\\

</div>

<div id="the-parallel-and-perpendicular-gradients" class="section">

### The parallel and perpendicular gradients<a href="#the-parallel-and-perpendicular-gradients" class="headerlink"
title="Permalink to this heading">#</a>

We have that

<div id="equation-eq-nabla-2" class="math notranslate nohighlight">

<span class="eqno">(161)<a href="#equation-eq-nabla-2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\nabla}=& {\boldsymbol{e}}^i \partial_i = {\boldsymbol{e}}^x
\partial_x + {\boldsymbol{e}}^y \partial_y + {\boldsymbol{e}}^z
\partial_z\end{aligned}\\

</div>

and that

<div id="equation-eq-gradpar3" class="math notranslate nohighlight">

<span class="eqno">(162)<a href="#equation-eq-gradpar3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\nabla}\_\\ =& \left({\boldsymbol{b}} \cdot {\nabla}\right)
{\boldsymbol{b}} = {\boldsymbol{b}} {\boldsymbol{b}} \cdot {\nabla}=
\frac{{\boldsymbol{e}}\_y {\boldsymbol{e}}\_y}{g\_{yy}} \cdot {\nabla}=
\frac{{\boldsymbol{e}}\_y {\boldsymbol{e}}\_y}{g\_{yy}} \cdot
{\boldsymbol{e}}^i \partial_i = \frac{{\boldsymbol{e}}\_y}{g\_{yy}}
\partial_y\end{aligned}\\

</div>

so that

<div id="equation-eq-gradperp2" class="math notranslate nohighlight">

<span class="eqno">(163)<a href="#equation-eq-gradperp2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\nabla}\_\perp =& {\nabla}- {\nabla}\_\\\\ % =& {\boldsymbol{e}}^x
\partial_x + {\boldsymbol{e}}^y \partial_y + {\boldsymbol{e}}^z
\partial_z - \frac{{\boldsymbol{e}}\_y}{g\_{yy}} \partial_y\\ % =&
{\boldsymbol{e}}^x \partial_x + {\boldsymbol{e}}^y \partial_y +
{\boldsymbol{e}}^z \partial_z -
\frac{g\_{yi}{\boldsymbol{e}}^i}{g\_{yy}} \partial_y\\ % =&
{\boldsymbol{e}}^x \partial_x + {\boldsymbol{e}}^y \partial_y +
{\boldsymbol{e}}^z \partial_z - \frac{g\_{yx}{\boldsymbol{e}}^x
+g\_{yy}{\boldsymbol{e}}^y +g\_{yz}{\boldsymbol{e}}^z
}{g\_{yy}}\partial_y\\ % =& {\boldsymbol{e}}^x \left(\partial_x -
\frac{g\_{yx}}{g\_{yy}}\partial_y\right) + {\boldsymbol{e}}^z
\left(\partial_z -
\frac{g\_{yz}}{g\_{yy}}\partial_y\right)\end{aligned}\end{split}\\

</div>

<div id="the-perpendicular-gradients-in-laplacian-inversion"
class="section">

#### The perpendicular gradients in Laplacian inversion<a href="#the-perpendicular-gradients-in-laplacian-inversion"
class="headerlink" title="Permalink to this heading">#</a>

In the Laplacian inversion BOUT++ currently neglects the parallel
<span class="math notranslate nohighlight">\\y\\</span> derivatives even
if <span class="math notranslate nohighlight">\\g\_{xy}\\</span> and
<span class="math notranslate nohighlight">\\g\_{yz}\\</span> are
non-zero, thus

<div id="equation-eq-reduced-grad-perp"
class="math notranslate nohighlight">

<span class="eqno">(164)<a href="#equation-eq-reduced-grad-perp" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\nabla}\_\perp \simeq& {\boldsymbol{e}}^x \partial_x +
{\boldsymbol{e}}^z \partial_z \end{aligned}\\

</div>

</div>

</div>

<div id="the-laplacian" class="section">

### The Laplacian<a href="#the-laplacian" class="headerlink"
title="Permalink to this heading">#</a>

We would here like to find an expression for the Laplacian

<div id="equation-eq-laplace1" class="math notranslate nohighlight">

<span class="eqno">(165)<a href="#equation-eq-laplace1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\nabla}^2 = {\nabla\cdot}{\nabla}\end{aligned}\\

</div>

In general we have (using equation (2.6.39) in D’haeseleer
<a href="#haeseleer" id="id7"
class="reference internal"><span>[haeseleer]</span></a>)

<div id="equation-eq-diva" class="math notranslate nohighlight">

<span class="eqno">(166)<a href="#equation-eq-diva" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\nabla\cdot}{\boldsymbol{A}} = \frac{1}{J} \partial_i \left(JA^i\right)
\end{aligned}\\

</div>

and that

<div id="equation-eq-acomponents" class="math notranslate nohighlight">

<span class="eqno">(167)<a href="#equation-eq-acomponents" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} A^i =
{\boldsymbol{A}}\cdot {\boldsymbol{e}}^i\end{aligned}\\

</div>

In our case <span class="math notranslate nohighlight">\\A \to
{\nabla}\\</span>, so that

<div id="equation-eq-gradcomponents"
class="math notranslate nohighlight">

<span class="eqno">(168)<a href="#equation-eq-gradcomponents" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\nabla}^i = \left({\nabla}\right)\cdot {\boldsymbol{e}}^i =
{\boldsymbol{e}}^i \cdot \left({\nabla}\right) = {\boldsymbol{e}}^i
\cdot \left({\boldsymbol{e}}^j \partial_j\right) = g^{ij}
\partial_j\end{aligned}\\

</div>

Thus

<div id="equation-eq-laplace2" class="math notranslate nohighlight">

<span class="eqno">(169)<a href="#equation-eq-laplace2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\nabla}^2 =& \frac{1}{J} \partial_i \left(J g^{ij} \partial_j\right)\\
=& \frac{1}{J} g^{ij} J \partial_i \partial_j + \frac{1}{J} \partial_i
\left(J g^{ij} \right) \partial_j\\ =& g^{ij} \partial_i \partial_j +
G^j \partial_j\\\end{aligned}\end{split}\\

</div>

where we have defined [2]

<div id="equation-eq-gj" class="math notranslate nohighlight">

<span class="eqno">(170)<a href="#equation-eq-gj" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
G^j =& \frac{1}{J} \partial_i \left(J g^{ij} \right)\\ =& \frac{1}{J}
\left( \partial_x \left\[J g^{xj} \right\] + \partial_y \left\[J g^{yj}
\right\] + \partial_z \left\[J g^{zj} \right\]
\right)\end{aligned}\end{split}\\

</div>

By writing the terms out, we get

<div id="equation-eq-laplace3" class="math notranslate nohighlight">

<span class="eqno">(171)<a href="#equation-eq-laplace3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\nabla}^2 =& g^{ij} \partial_i \partial_j + G^j \partial_j\\ % =&
\left( g^{xj} \partial_x \partial_j + g^{yj} \partial_y \partial_j +
g^{zj} \partial_z \partial_j\right) + \left(G^j \partial_j\right)\\ % =&
\quad \\ \left( g^{xx} \partial_x^2 + g^{yx} \partial_y \partial_x +
g^{zx} \partial_z \partial_x\right) + \left(G^x \partial_x\right)\\ &+
\left( g^{xy} \partial_x \partial_y + g^{yy} \partial_y^2 + g^{zy}
\partial_z \partial_y\right) + \left(G^y \partial_y\right)\\ &+ \left(
g^{xz} \partial_x \partial_z + g^{yz} \partial_y \partial_z + g^{zz}
\partial_z^y\right) + \left(G^z
\partial_z\right)\end{aligned}\end{split}\\

</div>

We now use that the metric tensor is symmetric (by definition), so that
<span class="math notranslate nohighlight">\\g^{ij}=g^{ji}\\</span>, and
<span class="math notranslate nohighlight">\\g\_{ij}=g\_{ji}\\</span>,
and that the partial derivatives commutes for smooth functions
<span class="math notranslate nohighlight">\\\partial_i\partial_j=\partial_j\partial_i\\</span>.
This gives

<div id="equation-eq-laplace4" class="math notranslate nohighlight">

<span class="eqno">(172)<a href="#equation-eq-laplace4" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\nabla}^2 =&\quad \\ \left(g^{xx} \partial_x^2 \right) + \left(G^x
\partial_x\right)\\ &+ \left(g^{yy} \partial_y^2 \right) + \left(G^y
\partial_y\right)\\ &+ \left(g^{zz} \partial_z^2\right) + \left(G^z
\partial_z\right)\\ &+ 2\left( g^{xy} \partial_x \partial_y + g^{xz}
\partial_x \partial_z + g^{yz} \partial_y \partial_z \right)\\ % =&\quad
\\ \left(g^{xx} \partial_x^2\right) + \left( \frac{1}{J} \left\[
\partial_x \left\\J g^{xx} \right\\ + \partial_y \left\\J g^{yx}
\right\\ + \partial_z \left\\J g^{zx} \right\\ \right\]
\partial_x\right)\\ &+ \left(g^{yy} \partial_y^2\right) + \left(
\frac{1}{J} \left\[ \partial_x \left\\J g^{xy} \right\\ + \partial_y
\left\\J g^{yy} \right\\ + \partial_z \left\\J g^{zy} \right\\ \right\]
\partial_y\right)\\ &+ \left(g^{zz} \partial_z^2\right) + \left(
\frac{1}{J} \left\[ \partial_x \left\\J g^{xz} \right\\ + \partial_y
\left\\J g^{yz} \right\\ + \partial_z \left\\J g^{zz} \right\\ \right\]
\partial_z\right)\\ &+ 2\left( g^{xy} \partial_x \partial_y + g^{xz}
\partial_x \partial_z + g^{yz} \partial_y \partial_z
\right)\end{aligned}\end{split}\\

</div>

Notice that <span class="math notranslate nohighlight">\\G^i\\</span>
does not operate on
<span class="math notranslate nohighlight">\\\partial_i\\</span>, but
rather that the two are multiplied together.

</div>

<div id="the-parallel-laplacian" class="section">

### The parallel Laplacian<a href="#the-parallel-laplacian" class="headerlink"
title="Permalink to this heading">#</a>

We have that

<div id="equation-eq-gradpar4" class="math notranslate nohighlight">

<span class="eqno">(173)<a href="#equation-eq-gradpar4" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\nabla}\_\\ =& \left({\boldsymbol{b}} \cdot {\nabla}\right)
{\boldsymbol{b}}\\ = {\boldsymbol{b}} {\boldsymbol{b}} \cdot {\nabla}=
\frac{{\boldsymbol{e}}\_y {\boldsymbol{e}}\_y}{g\_{yy}} \cdot {\nabla}=
\frac{{\boldsymbol{e}}\_y {\boldsymbol{e}}\_y}{g\_{yy}} \cdot
{\boldsymbol{e}}^i \partial_i = \frac{{\boldsymbol{e}}\_y}{g\_{yy}}
\partial_y\end{aligned}\\

</div>

we have that

<div id="equation-eq-gradparcomponents"
class="math notranslate nohighlight">

<span class="eqno">(174)<a href="#equation-eq-gradparcomponents" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\nabla}\_\\^i =& \left(\frac{{\boldsymbol{e}}\_y}{g\_{yy}}
\partial_y\right)\cdot {\boldsymbol{e}}^i = {\boldsymbol{e}}^i \cdot
\left(\frac{{\boldsymbol{e}}\_y}{g\_{yy}}
\partial_y\right)\end{aligned}\\

</div>

so that by equation
<a href="#equation-eq-diva" class="reference internal">(166)</a>,

<div id="equation-eq-laplacepar" class="math notranslate nohighlight">

<span class="eqno">(175)<a href="#equation-eq-laplacepar" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\nabla}\_\\^2 =& {\nabla\cdot}\left({\boldsymbol{b}} {\boldsymbol{b}}
\cdot {\nabla}\right)\\ =&
{\nabla\cdot}\left(\frac{{\boldsymbol{e}}\_y}{g\_{yy}} \cdot
\partial_y\right)\\ =& \frac{1}{J} \partial_i \left( J{\boldsymbol{e}}^i
\cdot \left\[\frac{{\boldsymbol{e}}\_y}{g\_{yy}} \partial_y\right\]
\right)\\ =& \frac{1}{J} \partial_y \left(\frac{J}{g\_{yy}}
\partial_y\right)\end{aligned}\end{split}\\

</div>

</div>

<div id="the-perpendicular-laplacian" class="section">

### The perpendicular Laplacian<a href="#the-perpendicular-laplacian" class="headerlink"
title="Permalink to this heading">#</a>

For the perpendicular Laplacian, we have that

<div id="equation-eq-laplaceperp" class="math notranslate nohighlight">

<span class="eqno">(176)<a href="#equation-eq-laplaceperp" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\nabla}\_\perp^2 =& {\nabla}^2 - {\nabla}\_\\^2\\ =& g^{ij} \partial_i
\partial_j + G^j \partial_j -\frac{1}{J} \partial_y
\left(\frac{J}{g\_{yy}} \partial_y\right)\\ % =& \quad \\ \left(g^{xx}
\partial_x^2\right) + \left( \frac{1}{J} \left\[ \partial_x \left\\J
g^{xx} \right\\ + \partial_y \left\\J g^{yx} \right\\ + \partial_z
\left\\J g^{zx} \right\\ \right\] \partial_x\right)\\ &+ \left(g^{yy}
\partial_y^2\right) + \left( \frac{1}{J} \left\[ \partial_x \left\\J
g^{xy} \right\\ + \partial_y \left\\J g^{yy} \right\\ + \partial_z
\left\\J g^{zy} \right\\ \right\] \partial_y\right)\\ &+ \left(g^{zz}
\partial_z^2\right) + \left( \frac{1}{J} \left\[ \partial_x \left\\J
g^{xz} \right\\ + \partial_y \left\\J g^{yz} \right\\ + \partial_z
\left\\J g^{zz} \right\\ \right\] \partial_z\right)\\ &+ 2\left( g^{xy}
\partial_x \partial_y + g^{xz} \partial_x \partial_z + g^{yz} \partial_y
\partial_z \right)\\ &- \frac{1}{J} \partial_y \left(\frac{J}{g\_{yy}}
\partial_y\right)\end{aligned}\end{split}\\

</div>

<div id="the-perpendicular-laplacian-in-laplacian-inversion"
class="section">

#### The perpendicular Laplacian in Laplacian inversion<a href="#the-perpendicular-laplacian-in-laplacian-inversion"
class="headerlink" title="Permalink to this heading">#</a>

Notice that BOUT++ currently assumes small parallel gradients in the
dependent variable in Laplacian inversion if
<span class="math notranslate nohighlight">\\g\_{xy}\\</span> and
<span class="math notranslate nohighlight">\\g\_{yz}\\</span> are
non-zero (if these are zero, the derivation can be done directly from
equation <a href="#equation-eq-reduced-grad-perp"
class="reference internal">(164)</a> instead), so that

<div id="equation-eq-laplaceperpapprox"
class="math notranslate nohighlight">

<span class="eqno">(177)<a href="#equation-eq-laplaceperpapprox" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\nabla}\_\perp^2 \simeq& \quad \\ \left(g^{xx} \partial_x^2\right) +
\left( \frac{1}{J} \left\[ \partial_x \left\\J g^{xx} \right\\ +
\partial_y \left\\J g^{yx} \right\\ + \partial_z \left\\J g^{zx}
\right\\ \right\] \partial_x\right)\\ &+ \left(g^{zz}
\partial_z^2\right) + \left( \frac{1}{J} \left\[ \partial_x \left\\J
g^{xz} \right\\ + \partial_y \left\\J g^{yz} \right\\ + \partial_z
\left\\J g^{zz} \right\\ \right\] \partial_z\right)\\ &+ 2\left(g^{xz}
\partial_x \partial_z\right)\\ % =& \left(g^{xx} \partial_x^2\right) +
G^x\partial_x + \left(g^{zz} \partial_z^2\right) + G^z \partial_z +
2\left(g^{xz} \partial_x \partial_z\right)\end{aligned}\end{split}\\

</div>

</div>

<div id="the-perpendicular-laplacian-in-divergence-form"
class="section">

#### The perpendicular Laplacian in divergence form<a href="#the-perpendicular-laplacian-in-divergence-form"
class="headerlink" title="Permalink to this heading">#</a>

The unit vector along the magnetic field is

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\boldsymbol{b}} &=
\frac{1}{JB}{\boldsymbol{e}}\_y\\ &=
\frac{1}{JB}\left(g\_{xy}{\boldsymbol{e}}^x +
g\_{yy}{\boldsymbol{e}}^y + g\_{yz}{\boldsymbol{e}}^z\right)
\end{aligned}\end{split}\\

</div>

The perpendicular gradient is:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\nabla}\_{\perp} &= {\nabla} -
{\boldsymbol{b}}{\boldsymbol{b}}{\nabla}\\ &= {\boldsymbol{e}}^x
\frac{\partial}{\partial x} + {\boldsymbol{e}}^y
\frac{\partial}{\partial y} + {\boldsymbol{e}}^z
\frac{\partial}{\partial z} -
\frac{g\_{xy}{\boldsymbol{e}}^x}{g\_{yy}}\frac{\partial}{\partial x} -
{\boldsymbol{e}}^y \frac{\partial}{\partial y} -
\frac{g\_{yz}{\boldsymbol{e}}^z}{g\_{yy}}\frac{\partial}{\partial z}\\
&= {\boldsymbol{e}}^x\left(\frac{\partial}{\partial x} -
\frac{g\_{xy}}{g\_{yy}}\frac{\partial}{\partial y}\right) +
{\boldsymbol{e}}^z\left(\frac{\partial}{\partial z} -
\frac{g\_{yz}}{g\_{yy}}\frac{\partial}{\partial y}\right)
\end{aligned}\end{split}\\

</div>

The perpendicular Laplacian can therefore be written in divergence form
as:

<div class="math notranslate nohighlight">

\\\begin{split}\begin{aligned} {\nabla}\cdot\left({\nabla}\_\perp
f\right) =& \frac{1}{J}\frac{\partial}{\partial
x}\left\[Jg^{xx}\left(\frac{\partial}{\partial x} -
\frac{g\_{xy}}{g\_{yy}}\frac{\partial}{\partial y}\right) +
Jg^{xz}\left(\frac{\partial}{\partial z} -
\frac{g\_{yz}}{g\_{yy}}\frac{\partial}{\partial y}\right)\right\]\\ +&
\frac{1}{J}\frac{\partial}{\partial
y}\left\[Jg^{xy}\left(\frac{\partial}{\partial x} -
\frac{g\_{xy}}{g\_{yy}}\frac{\partial}{\partial y}\right) +
Jg^{yz}\left(\frac{\partial}{\partial z} -
\frac{g\_{yz}}{g\_{yy}}\frac{\partial}{\partial y}\right)\right\]\\ +&
\frac{1}{J}\frac{\partial}{\partial
z}\left\[Jg^{xz}\left(\frac{\partial}{\partial x} -
\frac{g\_{xy}}{g\_{yy}}\frac{\partial}{\partial y}\right) +
Jg^{zz}\left(\frac{\partial}{\partial z} -
\frac{g\_{yz}}{g\_{yy}}\frac{\partial}{\partial y}\right)\right\]
\end{aligned}\end{split}\\

</div>

This form is currently implemented in
<span class="pre">`FV::Div_a_Grad_perp`</span>
(<span class="pre">`bout/fv_ops.hxx`</span>) but that operator currently
assumes that the off-diagonal terms
<span class="math notranslate nohighlight">\\g^{xz}\\</span> and
<span class="math notranslate nohighlight">\\g^{xy}\\</span> are zero,
which is the case for orthogonal grids with shifted metrics but not in
general.

</div>

</div>

<div id="the-poisson-bracket-operator" class="section">

### The Poisson bracket operator<a href="#the-poisson-bracket-operator" class="headerlink"
title="Permalink to this heading">#</a>

We will here derive the bracket operators, as they are used in BOUT++.

<div id="the-electrostatic-exb-velocity" class="section">

#### The electrostatic ExB velocity<a href="#the-electrostatic-exb-velocity" class="headerlink"
title="Permalink to this heading">#</a>

Under electrostatic conditions, we have that
<span class="math notranslate nohighlight">\\{\boldsymbol{v}}\_E =
-\frac{\nabla\phi\times{\boldsymbol{b}}}{B}\\</span>, which is similar
to
<span class="math notranslate nohighlight">\\{\boldsymbol{v}}={\boldsymbol{k}}\times\nabla\psi\\</span>
found in incompressible fluid flow

<div id="equation-eq-v-e" class="math notranslate nohighlight">

<span class="eqno">(178)<a href="#equation-eq-v-e" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{v}}\_E =& -\frac{\nabla\phi\times{\boldsymbol{b}}}{B}\\ %
=&-\frac{\nabla\phi\times{\sigma\_{B\text{pol}}\boldsymbol{e}}\_y}{
\sqrt{g\_{yy}J^{-2}}\sqrt{g\_{yy}}}\\ %
=&-\frac{J}{g\_{yy}}\nabla\phi\times{\boldsymbol{e}}\_y\\ %
=&\frac{J}{g\_{yy}}{\boldsymbol{e}}\_y\times\nabla\phi\\ %
=&\frac{J}{g\_{yy}}{\boldsymbol{e}}\_y\times
\left({\boldsymbol{e}}^x\partial_x + {\boldsymbol{e}}^y\partial_y +
{\boldsymbol{e}}^z\partial_z\right)\phi\\ % =&\frac{J}{g\_{yy}}
\left(g\_{yx}{\boldsymbol{e}}^x + g\_{yy}{\boldsymbol{e}}^y +
g\_{yz}{\boldsymbol{e}}^z\right) \times
\left({\boldsymbol{e}}^x\partial_x + {\boldsymbol{e}}^y\partial_y +
{\boldsymbol{e}}^z\partial_z\right)\phi\\ % =&\frac{J}{g\_{yy}} \left(
g\_{yx}{\boldsymbol{e}}^x\times{\boldsymbol{e}}^x\partial_x +
g\_{yy}{\boldsymbol{e}}^y\times{\boldsymbol{e}}^x\partial_x +
g\_{yz}{\boldsymbol{e}}^z\times{\boldsymbol{e}}^x\partial_x \right. \\
&\quad\\ + g\_{yx}{\boldsymbol{e}}^x\times{\boldsymbol{e}}^y\partial_y +
g\_{yy}{\boldsymbol{e}}^y\times{\boldsymbol{e}}^y\partial_y +
g\_{yz}{\boldsymbol{e}}^z\times{\boldsymbol{e}}^y\partial_y \\ &\quad\\
\left. + g\_{yx}{\boldsymbol{e}}^x\times{\boldsymbol{e}}^z\partial_z +
g\_{yy}{\boldsymbol{e}}^y\times{\boldsymbol{e}}^z\partial_z +
g\_{yz}{\boldsymbol{e}}^z\times{\boldsymbol{e}}^z\partial_z \right)
\phi\\ % =&\frac{J}{g\_{yy}} \left( -
g\_{yy}{\boldsymbol{e}}^x\times{\boldsymbol{e}}^y\partial_x +
g\_{yz}{\boldsymbol{e}}^z\times{\boldsymbol{e}}^x\partial_x \right. \\
&\quad + g\_{yx}{\boldsymbol{e}}^x\times{\boldsymbol{e}}^y\partial_y -
g\_{yz}{\boldsymbol{e}}^y\times{\boldsymbol{e}}^z\partial_y \\ &\quad
\left. - g\_{yx}{\boldsymbol{e}}^z\times{\boldsymbol{e}}^x\partial_z +
g\_{yy}{\boldsymbol{e}}^y\times{\boldsymbol{e}}^z\partial_z \right)
\phi\\ % =&\frac{1}{g\_{yy}} \left( -
g\_{yy}{\boldsymbol{e}}\_z\partial_x +
g\_{yz}{\boldsymbol{e}}\_y\partial_x +
g\_{yx}{\boldsymbol{e}}\_z\partial_y -
g\_{yz}{\boldsymbol{e}}\_x\partial_y -
g\_{yx}{\boldsymbol{e}}\_y\partial_z +
g\_{yy}{\boldsymbol{e}}\_x\partial_z \right)
\phi\end{aligned}\end{split}\\

</div>

</div>

<div id="the-electrostatic-exb-advection" class="section">

#### The electrostatic ExB advection<a href="#the-electrostatic-exb-advection" class="headerlink"
title="Permalink to this heading">#</a>

The electrostatic <span class="math notranslate nohighlight">\\E\times
B\\</span> advection operator thus becomes

<div id="equation-eq-v-edotgrad" class="math notranslate nohighlight">

<span class="eqno">(179)<a href="#equation-eq-v-edotgrad" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{v}}\_E\cdot\nabla =&
-\frac{\nabla\phi\times{\boldsymbol{b}}}{B}\cdot\nabla\\ %
=&\frac{1}{g\_{yy}} \left( - g\_{yy}{\boldsymbol{e}}\_z\partial_x +
g\_{yz}{\boldsymbol{e}}\_y\partial_x +
g\_{yx}{\boldsymbol{e}}\_z\partial_y -
g\_{yz}{\boldsymbol{e}}\_x\partial_y -
g\_{yx}{\boldsymbol{e}}\_y\partial_z +
g\_{yy}{\boldsymbol{e}}\_x\partial_z \right) \phi
\cdot\left({\boldsymbol{e}}^x\partial_x + {\boldsymbol{e}}^y\partial_y +
{\boldsymbol{e}}^z\partial_z\right)\\ % =& \frac{1}{g\_{yy}} \left( -
g\_{yy}\partial_x\phi\partial_z + g\_{yz}\partial_x\phi\partial_y +
g\_{yx}\partial_y\phi\partial_z - g\_{yz}\partial_y\phi\partial_x -
g\_{yx}\partial_z\phi\partial_y + g\_{yy}\partial_z\phi\partial_x
\right)\\ % =& \frac{1}{g\_{yy}} \left( \left\[ g\_{yy}\partial_z\phi -
g\_{yz}\partial_y\phi \right\]\partial_x + \left\[
g\_{yz}\partial_x\phi - g\_{yx}\partial_z\phi \right\]\partial_y +
\left\[ g\_{yx}\partial_y\phi - g\_{yy}\partial_x\phi \right\]\partial_z
\right)\\ % =& \frac{1}{g\_{yy}} \left( g\_{yx}\\\phi, \cdot\\\_{y,z} +
g\_{yy}\\\phi, \cdot\\\_{z,x} + g\_{yz}\\\phi, \cdot\\\_{x,y}
\right)\end{aligned}\end{split}\\

</div>

Where we have used the definition of the Poisson bracket

<div id="equation-eq-poissonbracket2"
class="math notranslate nohighlight">

<span class="eqno">(180)<a href="#equation-eq-poissonbracket2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned} \\a,
b\\\_{i,j} = \left(\partial_i a\right) \partial_j b - \left(\partial_j
a\right) \partial_i b\end{aligned}\\

</div>

The pure solenoidal advection is thus

<div id="equation-eq-bracket" class="math notranslate nohighlight">

<span class="eqno">(181)<a href="#equation-eq-bracket" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}
B{\boldsymbol{v}}\_E\cdot\nabla =&
-\nabla\phi\times{\boldsymbol{b}}\cdot\nabla\\ =& {\boldsymbol{b}}
\times \nabla\phi\cdot\nabla\\ =& \frac{\sqrt{g\_{yy}}}{Jg\_{yy}} \left(
g\_{yx}\\\phi, \cdot\\\_{y,z} + g\_{yy}\\\phi, \cdot\\\_{z,x} +
g\_{yz}\\\phi, \cdot\\\_{x,y} \right) \\ =& \frac{1}{J\sqrt{g\_{yy}}}
\left( g\_{yx}\\\phi, \cdot\\\_{y,z} + g\_{yy}\\\phi, \cdot\\\_{z,x} +
g\_{yz}\\\phi, \cdot\\\_{x,y} \right)\end{split}\\

</div>

</div>

<div id="the-bracket-operator-in-bout" class="section">

#### The bracket operator in BOUT++<a href="#the-bracket-operator-in-bout" class="headerlink"
title="Permalink to this heading">#</a>

Notice that the
<span class="math notranslate nohighlight">\\\mathtt{bracket(phi,f)}\\</span>
operators in BOUT++ returns
<span class="math notranslate nohighlight">\\-\frac{\nabla\phi\times{\boldsymbol{b}}}{B}\cdot\nabla
f\\</span> rather than
<span class="math notranslate nohighlight">\\-\nabla\phi\times{\boldsymbol{b}}\cdot\nabla
f\\</span>.

Notice also that the Arakawa brackets neglects the
<span class="math notranslate nohighlight">\\\partial_y\\</span>
derivative terms (the
<span class="math notranslate nohighlight">\\y\\</span>-derivative
terms) if <span class="math notranslate nohighlight">\\g\_{xy}\\</span>
and <span class="math notranslate nohighlight">\\g\_{yz}\\</span> are
non-zero, so for the Arakawa brackets, BOUT++ returns

<div id="equation-eq-arakawabracket"
class="math notranslate nohighlight">

<span class="eqno">(182)<a href="#equation-eq-arakawabracket" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
{\boldsymbol{v}}\_E\cdot\nabla =&
-\frac{\nabla\phi\times{\boldsymbol{b}}}{B}\cdot\nabla\\ % \simeq&
\frac{1}{g\_{yy}} \left( g\_{yy}\\\phi, \cdot\\\_{z,x} \right)\\ % =&
\partial_z\phi\partial_x -
\partial_x\phi\partial_z\end{aligned}\end{split}\\

</div>

</div>

</div>

</div>

<div id="divergence-of-exb-velocity" class="section">

## Divergence of ExB velocity<a href="#divergence-of-exb-velocity" class="headerlink"
title="Permalink to this heading">#</a>

<div id="equation-eq-v-exb" class="math notranslate nohighlight">

<span class="eqno">(183)<a href="#equation-eq-v-exb" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{v}}\_{E\times B} =
\frac{{\boldsymbol{b}}\times\nabla\phi}{B}\end{aligned}\\

</div>

Using

<div id="equation-eq-divfcrossg" class="math notranslate nohighlight">

<span class="eqno">(184)<a href="#equation-eq-divfcrossg" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\cdot\left({\boldsymbol{F}}\times{\boldsymbol{G}}\right) =
\left(\nabla\times{\boldsymbol{F}}\right)\cdot{\boldsymbol{G}} -
{\boldsymbol{F}}\cdot\left(\nabla\times{\boldsymbol{G}}\right)\end{aligned}\\

</div>

the divergence of the
<span class="math notranslate nohighlight">\\{\boldsymbol{E}}\times{\boldsymbol{B}}\\</span>
velocity can be written as

<div id="equation-eq-exb1" class="math notranslate nohighlight">

<span class="eqno">(185)<a href="#equation-eq-exb1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\nabla\cdot\left(\frac{1}{B}{\boldsymbol{b}}\times\nabla\phi\right) =
\left\[\nabla\times\left(\frac{1}{B}{\boldsymbol{b}}\right)\right\]\cdot\nabla\phi -
\frac{1}{B}{\boldsymbol{b}}\cdot\nabla\times\nabla\phi \end{aligned}\\

</div>

The second term on the right is identically zero (curl of a gradient).
The first term on the right can be expanded as

<div id="equation-eq-exbintermediate1"
class="math notranslate nohighlight">

<span class="eqno">(186)<a href="#equation-eq-exbintermediate1" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
\left\[\nabla\times\left(\frac{1}{B}{\boldsymbol{b}}\right)\right\]\cdot\nabla\phi
= \left\[\nabla\left(\frac{1}{B}\right)\times{\boldsymbol{b}} +
\frac{1}{B}\nabla\times{\boldsymbol{b}}\right\]\cdot\nabla\phi\end{aligned}\\

</div>

Using

<div id="equation-eq-bcrosskappa3" class="math notranslate nohighlight">

<span class="eqno">(187)<a href="#equation-eq-bcrosskappa3" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{aligned}
{\boldsymbol{b}}\times{\boldsymbol{\kappa}} =
\nabla\times{\boldsymbol{b}} -
{\boldsymbol{b}}\left\[{\boldsymbol{b}}\cdot\left(\nabla\times{\boldsymbol{b}}\right)\right\]\end{aligned}\\

</div>

this becomes:

<div id="equation-eq-exbintermediate2"
class="math notranslate nohighlight">

<span class="eqno">(188)<a href="#equation-eq-exbintermediate2" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla\cdot\left(\frac{1}{B}{\boldsymbol{b}}\times\nabla\phi\right) =
&-{\boldsymbol{b}}\times\nabla\left(\frac{1}{B}\right)\cdot\nabla\phi \\
&+ \frac{1}{B}{\boldsymbol{b}}\times{\boldsymbol{\kappa}}\cdot\nabla\phi
\\ &+
\frac{1}{B}\left\[{\boldsymbol{b}}\cdot\left(\nabla\times{\boldsymbol{b}}\right)\right\]{\boldsymbol{b}}\cdot\nabla\phi\end{aligned}\end{split}\\

</div>

Alternatively, equation
<a href="#equation-eq-exb1" class="reference internal">(185)</a> can be
expanded as

<div id="equation-eq-divv-exb" class="math notranslate nohighlight">

<span class="eqno">(189)<a href="#equation-eq-divv-exb" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla\cdot\left(\frac{1}{B}{\boldsymbol{b}}\times\nabla\phi\right) =&
-B{\boldsymbol{b}}\times\nabla\left(\frac{1}{B^2}\right)\cdot\nabla\phi +
\frac{1}{B^2}\nabla\times{\boldsymbol{B}}\cdot\nabla\phi \\ =&
-B{\boldsymbol{b}}\times\nabla\left(\frac{1}{B^2}\right)\cdot\nabla\phi +
\frac{1}{B^2}{\mu_0\boldsymbol{J}}\cdot\nabla\phi\end{aligned}\end{split}\\

</div>

<div id="equation-eq-divnv-exb" class="math notranslate nohighlight">

<span class="eqno">(190)<a href="#equation-eq-divnv-exb" class="headerlink"
title="Permalink to this equation">#</a></span>\\\begin{split}\begin{aligned}
\nabla\cdot\left(n\frac{\mathbf{b}\times\nabla\phi}{B}\right) &=
\frac{1}{J}\frac{\partial}{\partial\psi}\left(Jn\frac{\partial\phi}{\partial
z} \right) - \frac{1}{J}\frac{\partial}{\partial
z}\left(Jn\frac{\partial\phi}{\partial\psi}\right) \\ & \quad +
\frac{1}{J}\frac{\partial}{\partial\psi}\left(Jn\frac{g^{\psi\psi}g^{yz}}{B^2}\frac{\partial\phi}{\partial
y}\right) - \frac{1}{J}\frac{\partial}{\partial
y}\left(Jn\frac{g^{\psi\psi}g^{yz}}{B^2}\frac{\partial\phi}{\partial\psi}\right)\end{aligned}\end{split}\\

</div>

<div class="citation-list" role="list">

<div id="haeseleer" class="citation" role="doc-biblioentry">

<span class="label"><span class="fn-bracket">\[</span>haeseleer<span class="fn-bracket">\]</span></span>
<span class="backrefs">(<a href="#id4" role="doc-backlink">1</a>,<a href="#id5" role="doc-backlink">2</a>,<a href="#id6" role="doc-backlink">3</a>,<a href="#id7" role="doc-backlink">4</a>)</span>

D’haeseleer, W. D.: Flux Coordinates and Magnetic Field Structure,
Springer-Verlag, 1991, ISBN 3-540-52419-3

</div>

</div>

Footnotes

<span class="label"><span class="fn-bracket">\[</span><a href="#id8" role="doc-backlink">2</a><span class="fn-bracket">\]</span></span>

Notice that <span class="math notranslate nohighlight">\\G^i\\</span> is
**not** the same as the *Christoffel symbols of second kind* (also known
as the *connection coefficients* or
<span class="math notranslate nohighlight">\\\Gamma^i\_{jk}={\boldsymbol{e}}^i\cdot\partial_k
{\boldsymbol{e}}\_j\\</span>), although the derivation of the two are
quite similar. | We find that
<span class="math notranslate nohighlight">\\\Gamma^i\_{ji}={\boldsymbol{e}}^i\cdot\partial_i
{\boldsymbol{e}}\_j = {\nabla\cdot}{\boldsymbol{e}}\_j\\</span>, whereas
using equation
<a href="#equation-eq-diva" class="reference internal">(166)</a> leads
to
<span class="math notranslate nohighlight">\\G^i={\boldsymbol{e}}^i\cdot\partial_i
{\boldsymbol{e}}^j = {\nabla\cdot} {\boldsymbol{e}}^j\\</span>, since
<span class="math notranslate nohighlight">\\g^{ji}=g^{ij}\\</span> due
to symmetry.

</div>

</div>

<div class="prev-next-area">

<a href="petsc.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

PETSc solvers

</div>

<a href="preconditioning.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

BOUT++ preconditioning

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
- <a href="#orthogonal-toroidal-coordinates"
  class="reference internal nav-link">Orthogonal toroidal coordinates</a>
- <a href="#id1" class="reference internal nav-link">Field-aligned
  coordinates</a>
  - <a href="#magnetic-field" class="reference internal nav-link">Magnetic
    field</a>
  - <a href="#jacobian-and-metric-tensors"
    class="reference internal nav-link">Jacobian and metric tensors</a>
  - <a href="#zshift" class="reference internal nav-link">zShift</a>
  - <a href="#transform-back-to-cartesian"
    class="reference internal nav-link">Transform back to Cartesian</a>
- <a href="#right-handed-field-aligned-coordinates"
  class="reference internal nav-link">Right-handed field-aligned
  coordinates</a>
- <a href="#differential-operators-in-field-aligned-coordinates"
  class="reference internal nav-link">Differential operators in
  field-aligned coordinates</a>
  - <a href="#j-x-b-in-field-aligned-coordinates"
    class="reference internal nav-link">J x B in field-aligned
    coordinates</a>
  - <a href="#parallel-current" class="reference internal nav-link">Parallel
    current</a>
  - <a href="#curvature" class="reference internal nav-link">Curvature</a>
  - <a href="#curvature-from-nabla-times-left-frac-boldsymbol-b-b-right"
    class="reference internal nav-link">Curvature from <span
    class="math notranslate nohighlight">\({\nabla\times\left(\frac{\boldsymbol{b}}{B}\right)}\)</span></a>
  - <a href="#curvature-of-a-single-line"
    class="reference internal nav-link">Curvature of a single line</a>
  - <a href="#curvature-in-toroidal-coordinates"
    class="reference internal nav-link">Curvature in toroidal
    coordinates</a>
  - <a href="#psi-derivative-of-the-b-field"
    class="reference internal nav-link">psi derivative of the B field</a>
  - <a href="#parallel-derivative-of-the-b-field"
    class="reference internal nav-link">Parallel derivative of the B
    field</a>
  - <a href="#magnetic-shear-from-j-x-b"
    class="reference internal nav-link">Magnetic shear from J x B</a>
  - <a href="#magnetic-shear" class="reference internal nav-link">Magnetic
    shear</a>
  - <a href="#psi-derivative-of-h" class="reference internal nav-link">psi
    derivative of h</a>
- <a href="#shifted-radial-derivatives"
  class="reference internal nav-link">Shifted radial derivatives</a>
  - <a href="#perpendicular-laplacian"
    class="reference internal nav-link">Perpendicular Laplacian</a>
    - <a href="#in-orthogonal-psi-theta-zeta-flux-coordinates"
      class="reference internal nav-link">In orthogonal (psi, theta, zeta)
      flux coordinates</a>
  - <a href="#operator-b-x-nabla-phi-dot-nabla-a"
    class="reference internal nav-link">Operator B x Nabla Phi Dot Nabla
    A</a>
- <a href="#useful-identities" class="reference internal nav-link">Useful
  identities</a>
  - <a
    href="#mathbf-b-times-mathbf-kappa-cdot-nabla-psi-simeq-rb-zeta-partial-ln-b"
    class="reference internal nav-link"><span
    class="math notranslate nohighlight">\(\mathbf{b}\times\mathbf{\kappa}\cdot\nabla\psi
    \simeq -RB_\zeta\partial_{||}\ln B\)</span></a>
- <a href="#differential-geometry"
  class="reference internal nav-link">Differential geometry</a>
- <a href="#derivation-of-operators-in-the-bout-clebsch-system"
  class="reference internal nav-link">Derivation of operators in the
  BOUT++ Clebsch system</a>
  - <a href="#the-parallel-and-perpendicular-gradients"
    class="reference internal nav-link">The parallel and perpendicular
    gradients</a>
    - <a href="#the-perpendicular-gradients-in-laplacian-inversion"
      class="reference internal nav-link">The perpendicular gradients in
      Laplacian inversion</a>
  - <a href="#the-laplacian" class="reference internal nav-link">The
    Laplacian</a>
  - <a href="#the-parallel-laplacian"
    class="reference internal nav-link">The parallel Laplacian</a>
  - <a href="#the-perpendicular-laplacian"
    class="reference internal nav-link">The perpendicular Laplacian</a>
    - <a href="#the-perpendicular-laplacian-in-laplacian-inversion"
      class="reference internal nav-link">The perpendicular Laplacian in
      Laplacian inversion</a>
    - <a href="#the-perpendicular-laplacian-in-divergence-form"
      class="reference internal nav-link">The perpendicular Laplacian in
      divergence form</a>
  - <a href="#the-poisson-bracket-operator"
    class="reference internal nav-link">The Poisson bracket operator</a>
    - <a href="#the-electrostatic-exb-velocity"
      class="reference internal nav-link">The electrostatic ExB velocity</a>
    - <a href="#the-electrostatic-exb-advection"
      class="reference internal nav-link">The electrostatic ExB advection</a>
    - <a href="#the-bracket-operator-in-bout"
      class="reference internal nav-link">The bracket operator in BOUT++</a>
- <a href="#divergence-of-exb-velocity"
  class="reference internal nav-link">Divergence of ExB velocity</a>

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
