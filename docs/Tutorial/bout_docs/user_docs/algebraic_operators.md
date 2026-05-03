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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/algebraic_operators.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/algebraic_operators.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/algebraic_operators.rst"
  class="btn btn-sm btn-download-source-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Download source file"><span class="btn__icon-container">
  <em></em> </span> <span class="btn__text-container">.rst</span></a>
- <span class="btn__icon-container"> </span>
  <span class="btn__text-container">.pdf</span>

</div>

<span class="btn__icon-container"> </span>

</div>

</div>

</div>

</div>

</div>

<div id="jb-print-docs-body" class="onlyprint">

# Algebraic operators

<div id="print-main-content">

<div id="jb-print-toc">

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="algebraic-operators" class="section">

<span id="sec-algebraic-ops"></span>

# Algebraic operators<a href="#algebraic-operators" class="headerlink"
title="Permalink to this heading">#</a>

BOUT++ provides a wide variety of algebraic operators acting on fields.

The algebraic operators are listed in
<a href="#tab-algebraic-ops" class="reference internal"><span
class="std std-numref">Table 18</span></a>. For a completely up-to-date
list, see the
<span class="pre">`Non-member`</span>` `<span class="pre">`functions`</span>
part of <a href="../_breathe_autogen/file/field2d_8hxx.html"
class="reference internal"><span class="doc">field2d.hxx</span></a>,
<a href="../_breathe_autogen/file/field3d_8hxx.html"
class="reference internal"><span class="doc">field3d.hxx</span></a>,
<a href="../_breathe_autogen/file/fieldperp_8hxx.html"
class="reference internal"><span class="doc">fieldperp.hxx</span></a>.

<span id="tab-algebraic-ops"></span>

<table id="id3" class="table">
<caption><span class="caption-number">Table 18 </span><span
class="caption-text">Algebraic operators</span><a href="#id3"
class="headerlink" title="Permalink to this table">#</a></caption>
<thead>
<tr class="row-odd">
<th class="head"><p>Name</p></th>
<th class="head"><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">min(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">allpe=true,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p>Minimum (optionally over all processes)</p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">max(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">allpe=true,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p>Maximum (optionally over all processes)</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">pow(lhs,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">rhs,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\mathtt{lhs}^\mathtt{rhs}\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">sqrt(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\sqrt{(f)}\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">abs(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(|f|\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">exp(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(e^f\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">log(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\log(f)\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">sin(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\sin(f)\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">cos(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\cos(f)\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">tan(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\tan(f)\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">sinh(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\sinh(f)\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">cosh(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\cosh(f)\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">tanh(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p><span
class="math notranslate nohighlight">\(\tanh(f)\)</span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">floor(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p>Returns a field with the floor of <span class="pre"><code
class="sourceCode cpp">f</code></span> at each point</p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">filter(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">n,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p>Calculate the amplitude of the Fourier mode in the z-direction
with mode number <span class="pre"><code
class="sourceCode cpp">n</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">lowpass(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">nmax,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p>Remove Fourier modes (in the z-direction) with mode number higher
than <span class="pre"><code
class="sourceCode cpp">zmax</code></span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">lowpass(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">nmax,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">nmin,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p>Remove Fourier modes (in the z-direction) with mode number higher
than <span class="pre"><code class="sourceCode cpp">zmax</code></span>
or lower than <span class="pre"><code
class="sourceCode cpp">zmin</code></span></p></td>
</tr>
<tr class="row-odd">
<td><p><span class="pre"><code
class="docutils literal notranslate">shiftZ(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">angle,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p>Rotate <span class="pre"><code
class="sourceCode cpp">f</code></span> by <span class="pre"><code
class="sourceCode cpp">angle</code></span> in the z-direction. <span
class="math notranslate nohighlight">\(\mathtt{angle}/2\pi\)</span> is
the fraction of the domain multiplied by <span
class="math notranslate nohighlight">\(2\pi\)</span> so angle is in
radians if the total size of the domain is <span
class="math notranslate nohighlight">\(2\pi\)</span></p></td>
</tr>
<tr class="row-even">
<td><p><span class="pre"><code
class="docutils literal notranslate">DC(f,</code></span><code
class="docutils literal notranslate"> </code><span class="pre"><code
class="docutils literal notranslate">region)</code></span></p></td>
<td><p>The average in the z-direction of <span class="pre"><code
class="sourceCode cpp">f</code></span> (DC stands for direct current,
i.e. the constant part of <span class="pre"><code
class="sourceCode cpp">f</code></span> as opposed to the AC, alternating
current, or fluctuating part)</p></td>
</tr>
</tbody>
</table>

These operators take a <span class="pre">`region`</span> argument, whose
values can be [1] (see
<a href="../developer_docs/data_types.html#sec-iterating"
class="reference internal"><span class="std std-ref">Iterating over
fields</span></a>)

- <a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv47RGN_ALL"
  class="reference internal" title="RGN_ALL"><span class="pre"><code
  class="sourceCode cpp">RGN_ALL</code></span></a>, which is the whole
  mesh;

- <a
  href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv411RGN_NOBNDRY"
  class="reference internal" title="RGN_NOBNDRY"><span class="pre"><code
  class="sourceCode cpp">RGN_NOBNDRY</code></span></a>, which skips all
  boundaries;

- <a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv47RGN_NOX"
  class="reference internal" title="RGN_NOX"><span class="pre"><code
  class="sourceCode cpp">RGN_NOX</code></span></a>, which skips the x
  boundaries

- <a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv47RGN_NOY"
  class="reference internal" title="RGN_NOY"><span class="pre"><code
  class="sourceCode cpp">RGN_NOY</code></span></a>, which skips the y
  boundaries

The default value for the region argument is
<a href="../_breathe_autogen/file/bout__types_8hxx.html#_CPPv47RGN_ALL"
class="reference internal" title="RGN_ALL"><span class="pre"><code
class="sourceCode cpp">RGN_ALL</code></span></a> which should work in
all cases. However, the region argument can be used for optimization, to
skip calculations in guard cells if it is known that those results will
not be needed (for example, if no derivatives of the result will be
calculated). Since these operators can be relatively expensive compared
to addition, subtraction, multiplication this can be a useful
performance improvement.

<span class="label"><span class="fn-bracket">\[</span><a href="#id1" role="doc-backlink">1</a><span class="fn-bracket">\]</span></span>

More regions may be added in future, for example to act on only subsets
of the physical domain.

</div>

<div class="prev-next-area">

<a href="differential_operators.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Differential operators

</div>

<a href="staggered_grids.html" class="right-next" title="next page"></a>

<div class="prev-next-info">

next

Staggered grids

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
