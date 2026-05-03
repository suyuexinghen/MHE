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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/nonlocal.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/nonlocal.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/nonlocal.rst"
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

# Nonlocal heat flux models

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#spitzer-harm-heat-flux"
  class="reference internal nav-link">Spitzer-Harm heat flux</a>
- <a href="#snb-model" class="reference internal nav-link">SNB model</a>
  - <a href="#using-the-snb-model" class="reference internal nav-link">Using
    the SNB model</a>
  - <a href="#example-linear-perturbation"
    class="reference internal nav-link">Example: Linear perturbation</a>
  - <a href="#example-nonlinear-heat-flux"
    class="reference internal nav-link">Example: Nonlinear heat flux</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="nonlocal-heat-flux-models" class="section">

<span id="sec-nonlocal-heatflux"></span>

# Nonlocal heat flux models<a href="#nonlocal-heat-flux-models" class="headerlink"
title="Permalink to this heading">#</a>

<div id="spitzer-harm-heat-flux" class="section">

## Spitzer-Harm heat flux<a href="#spitzer-harm-heat-flux" class="headerlink"
title="Permalink to this heading">#</a>

The Spitzer-Harm heat flux
<span class="math notranslate nohighlight">\\q\_{SH}\\</span> is
calculated using

<div class="math notranslate nohighlight">

\\q\_{SH} = - \frac{n_e e
T_e}{m_e}\frac{3\sqrt{\pi}}{4}\tau\_{ei,T}\kappa_0\frac{Z+0.24}{Z+4.2}
\partial\_{||} T_e\\

</div>

where <span class="math notranslate nohighlight">\\n_e\\</span> is the
electron density in
<span class="math notranslate nohighlight">\\m^{-3}\\</span>,
<span class="math notranslate nohighlight">\\T_e\\</span> is the
electron temperature in eV,
<span class="math notranslate nohighlight">\\\kappa_0 = 13.58\\</span>,
<span class="math notranslate nohighlight">\\Z\\</span> is the average
ion charge. The resulting expression is in units of
<span class="math notranslate nohighlight">\\eV/m^2/s\\</span>.

The thermal collision time
<span class="math notranslate nohighlight">\\\tau\_{ei,T} =
\lambda\_{ei,T} / v\_{T}\\</span> is calculated using the thermal mean
free path and thermal velocity:

<div class="math notranslate nohighlight">

\\ \begin{align}\begin{aligned}\lambda\_{ee,T} = \frac{v_T^4}{Yn_e
\ln\Lambda}\\\lambda\_{ei,T} = \frac{v_T^4}{YZ^2n_i \ln\Lambda}\\v_T =
\sqrt{\frac{2eT_e}{m_e}}\end{aligned}\end{align} \\

</div>

where it is assumed that
<span class="math notranslate nohighlight">\\n_i = n_e\\</span>, and the
following are used:

<div class="math notranslate nohighlight">

\\ \begin{align}\begin{aligned}Y = 4\pi\left(\frac{e^2}{4\pi \epsilon_0
m_e}\right)^2\\\ln\Lambda = 6.6 -
0.5\log\left(\frac{n_e}{10^{20}}\right) + 1.5
\log\left(T_e\right);\end{aligned}\end{align} \\

</div>

Note: If comparing to <a
href="http://farside.ph.utexas.edu/teaching/plasma/Plasmahtml/node35.html"
class="reference external">online notes</a>,
<span class="math notranslate nohighlight">\\\kappa_0\frac{Z+0.24}{Z+4.2}
\simeq 3.2\\</span>, a different definition of collision time
<span class="math notranslate nohighlight">\\\tau\_{ei}\\</span> is used
here, but the other factors are included so that the heat flux
<span class="math notranslate nohighlight">\\q\_{SH}\\</span> is the
same here as in those notes.

</div>

<div id="snb-model" class="section">

## SNB model<a href="#snb-model" class="headerlink"
title="Permalink to this heading">#</a>

The SNB model calculates a correction to the Spitzer-Harm heat flux,
solving a diffusion equation for each of a set of energy groups with
normalised energy <span class="math notranslate nohighlight">\\\beta =
E_g / eT_e\\</span> where
<span class="math notranslate nohighlight">\\E_g\\</span> is the energy
of the group.

<div class="math notranslate nohighlight">

\\\left\[\frac{1}{\lambda'\_{g,ee}} -
\nabla\_{||}\left(\frac{\lambda'\_{g,ei}}{3}\partial\_{||}\right)\right\]H_g
= -\nabla\_{||} U_g\\

</div>

where <span class="math notranslate nohighlight">\\\nabla\_{||}\\</span>
is the divergence of a parallel flux, and
<span class="math notranslate nohighlight">\\\partial\_{||}\\</span> is
a parallel gradient. <span class="math notranslate nohighlight">\\U_g =
W_g q\_{SH}\\</span> is the contribution to the Spitzer-Harm heat flux
from a group:

<div class="math notranslate nohighlight">

\\W_g = \frac{1}{24}\int\_{\beta\_{g-1}}^{\beta^{g+1}} \beta^4
e^{-\beta} d\beta\\

</div>

The modified mean free paths for each group are:

<div class="math notranslate nohighlight">

\\ \begin{align}\begin{aligned}\lambda'\_{g,ee} = \beta^2
\lambda\_{ee,T} / r\\\lambda'\_{g,ei} = \beta^2 \lambda\_{ei,T}
\frac{Z + 0.24}{Z + 4.2}\end{aligned}\end{align} \\

</div>

From the quantities
<span class="math notranslate nohighlight">\\H_g\\</span> for each
group, the SNB heat flux is:

<div class="math notranslate nohighlight">

\\q\_{SNB} = q\_{SH} - \sum_g\frac{\lambda_g,ei}{3}\nabla H_g\\

</div>

In flud models we actually want the divergence of the heat flux, rather
than the heat flux itself. We therefore rearrange to get:

<div class="math notranslate nohighlight">

\\\nabla\_{||}\left(\frac{\lambda'\_{g,ei}}{3}\partial\_{||}\right)H_g =
\nabla\_{||} U_g + H_g / \lambda'\_{g,ee}\\

</div>

and so calculate the divergence of the heat flux as:

<div class="math notranslate nohighlight">

\\\nabla\_{||} q\_{SNB} = \nabla\_{||} q\_{SH} -
\sum_g\left(\nabla\_{||} U_g + H_g / \lambda'\_{g,ee}\right)\\

</div>

The Helmholtz type equation along the magnetic field is solved using a
tridiagonal solver. The parallel divergence term is currently split into
a second derivative term, and a first derivative correction:

<div class="math notranslate nohighlight">

\\\nabla\_{||}\left(k\partial\_{||} T\right) =
\frac{1}{J}\frac{\partial}{\partial y}\left(\frac{k
J}{g\_{22}}\frac{\partial T}{\partial y}\right) =
k\frac{1}{g_22}\frac{\partial^2 T}{\partial y^2} +
\frac{1}{J}\frac{\partial}{\partial y}\left(\frac{k
J}{g\_{22}}\right)\frac{\partial T}{\partial y}\\

</div>

<div id="using-the-snb-model" class="section">

### Using the SNB model<a href="#using-the-snb-model" class="headerlink"
title="Permalink to this heading">#</a>

To use the SNB model, first include the header:

<div class="highlight-cpp notranslate">

<div class="highlight">

    #include <bout/snb.hxx>

</div>

</div>

then create an instance:

<div class="highlight-cpp notranslate">

<div class="highlight">

    HeatFluxSNB snb;

</div>

</div>

By default this will use options in a section called “snb”, but if
needed a different <span class="pre">`Options&`</span> section can be
given to the constructor:

<div class="highlight-cpp notranslate">

<div class="highlight">

    HeatFluxSNB snb(Options::root()["mysnb"]);

</div>

</div>

The options are listed in table
<a href="#tab-snb-options" class="reference internal"><span
class="std std-numref">Table 19</span></a>.

<span id="tab-snb-options"></span>

<table id="id1" class="table">
<caption><span class="caption-number">Table 19 </span><span
class="caption-text">SNB options</span><a href="#id1" class="headerlink"
title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Meaning</p></th>
<th class="head"><p>Default value</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">beta_max</code></span> <span
class="pre"><code
class="docutils literal notranslate">ngroups</code></span> <span
class="pre"><code
class="docutils literal notranslate">r</code></span></p></td>
<td><p>Maximum energy group to consider (multiple of eT) Number of
energy groups Scaling down the electron-electron mean free path</p></td>
<td><p>10 40 2</p></td>
</tr>
</tbody>
</table>

The divergence of the heat flux can then be calculated:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D Div_q = snb.divHeatFlux(Te, Ne);

</div>

</div>

where <span class="pre">`Te`</span> is the temperature in eV, and
<span class="pre">`Ne`</span> is the electron density in
<span class="math notranslate nohighlight">\\m^{-3}\\</span>. The result
is in eV per <span class="math notranslate nohighlight">\\m^3\\</span>
per second, so multiplying by
<span class="math notranslate nohighlight">\\e=1.602\times
10^{-19}\\</span> will give Watts per cubic meter.

To compare to the Spitzer-Harm result, pass in a pointer to a
<span class="pre">`Field3D`</span> as the third argument. This field
will be set to the Spitzer-Harm value:

<div class="highlight-cpp notranslate">

<div class="highlight">

    Field3D Div_q_SH;
    Field3D Div_q = snb.divHeatFlux(Te, Ne, &Div_q_SH);

</div>

</div>

This is used in the examples discussed below.

</div>

<div id="example-linear-perturbation" class="section">

### Example: Linear perturbation<a href="#example-linear-perturbation" class="headerlink"
title="Permalink to this heading">#</a>

The <span class="pre">`examples/conduction-snb`</span> example
calculates the heat flux for a given density and temperature profile,
comparing the SNB and Spitzer-Harm fluxes. The
<span class="pre">`sinusoidal.py`</span> case uses a periodic domain of
length 1 meter and a small (0.01eV) perturbation to the temperature. The
temperature is varied from 1eV to 1keV, so that the mean free path
varies. This is done for different SNB settings, changing the number of
groups and the maximum
<span class="math notranslate nohighlight">\\\beta\\</span>:

<div class="highlight-console notranslate">

<div class="highlight">

    $ python sinusoid.py

</div>

</div>

This should output a file <span class="pre">`snb-sinusoidal.png`</span>
and display the results, shown in figure
<a href="#fig-snb-sinusoidal" class="reference internal"><span
class="std std-numref">Fig. 19</span></a>.

<figure id="id2" class="align-default">
<span id="fig-snb-sinusoidal"></span><img
src="../_images/snb-sinusoidal.png"
alt="When the mean free path is short, the SNB heat flux is close to the Spitzer-Harm value. When the mean free path is long, the ratio goes towards zero." />
<figcaption><p><span class="caption-number">Fig. 19 </span><span
class="caption-text">The ratio of SNB heat flux to Spitzer-Harm heat
flux, as a function of electron mean free path divided by temperature
perturbation wavelength. Note that the difference between SNB and
Spitzer-Harm becomes significant (20%) when the mean free path is just
1% of the wavelength.</span><a href="#id2" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

<div id="example-nonlinear-heat-flux" class="section">

### Example: Nonlinear heat flux<a href="#example-nonlinear-heat-flux" class="headerlink"
title="Permalink to this heading">#</a>

A nonlinear test is also included in
<span class="pre">`examples/conduction-snb`</span>, a step function in
temperature from around 200eV to 950eV over a distance of around 0.1mm,
at an electron density of 5e26 per cubic meter:

<div class="highlight-console notranslate">

<div class="highlight">

    $ python step.py

</div>

</div>

This should output a file <span class="pre">`snb-step.png`</span>, shown
in figure <a href="#fig-snb-step" class="reference internal"><span
class="std std-numref">Fig. 20</span></a>.

<figure id="id3" class="align-default">
<span id="fig-snb-step"></span><img src="../_images/snb-step.png"
alt="The SNB peak heat flux in the steep gradient region is lower than Spitzer-Harm by nearly a factor of 2. In the cold region the SNB heat flux is above the Spitzer-Harm value, and is nonzero in regions where the temperature gradient is zero." />
<figcaption><p><span class="caption-number">Fig. 20 </span><span
class="caption-text">Temperature profile and heat flux calculated using
Spitzer-Harm and the SNB model, for a temperature step profile, at a
density of 5e26 per cubic meter. Note the reduction in peak heat flux
(flux limit) and higher flux in the cold region (preheat) with the SNB
model.</span><a href="#id3" class="headerlink"
title="Permalink to this image">#</a></p></figcaption>
</figure>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="eigenvalue_solver.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Eigenvalue solver

</div>

<a href="invertable_operator.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Invertable operators

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#spitzer-harm-heat-flux"
  class="reference internal nav-link">Spitzer-Harm heat flux</a>
- <a href="#snb-model" class="reference internal nav-link">SNB model</a>
  - <a href="#using-the-snb-model" class="reference internal nav-link">Using
    the SNB model</a>
  - <a href="#example-linear-perturbation"
    class="reference internal nav-link">Example: Linear perturbation</a>
  - <a href="#example-nonlinear-heat-flux"
    class="reference internal nav-link">Example: Nonlinear heat flux</a>

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
