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
  href="https://github.com/boutproject/BOUT-dev/edit/master/manual/sphinx/user_docs/python_boutpp.rst"
  class="btn btn-sm btn-source-edit-button dropdown-item" target="_blank"
  data-bs-placement="left" data-bs-toggle="tooltip"
  title="Suggest edit"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Suggest edit</span></a>
- <a
  href="https://github.com/boutproject/BOUT-dev/issues/new?title=Issue%20on%20page%20%2Fuser_docs/python_boutpp.html&amp;body=Your%20issue%20content%20here."
  class="btn btn-sm btn-source-issues-button dropdown-item"
  target="_blank" data-bs-placement="left" data-bs-toggle="tooltip"
  title="Open an issue"><span class="btn__icon-container"> <em></em>
  </span> <span class="btn__text-container">Open issue</span></a>

</div>

<div class="dropdown dropdown-download-buttons">

- <a href="../_sources/user_docs/python_boutpp.rst"
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

# The python boutpp module

<div id="print-main-content">

<div id="jb-print-toc">

<div>

## Contents

</div>

- <a href="#installing" class="reference internal nav-link">Installing</a>
- <a href="#purpose" class="reference internal nav-link">Purpose</a>
- <a href="#functions" class="reference internal nav-link">Functions</a>
- <a href="#examples" class="reference internal nav-link">Examples</a>

</div>

</div>

</div>

<div id="searchbox">

</div>

<div id="the-python-boutpp-module" class="section">

# The python boutpp module<a href="#the-python-boutpp-module" class="headerlink"
title="Permalink to this heading">#</a>

<div id="installing" class="section">

## Installing<a href="#installing" class="headerlink"
title="Permalink to this heading">#</a>

Installing boutpp can be tricky, however in most cases it should be
automatically enabled if all dependencies are available. To error out on
missing dependencies, explicitly enable it:

<div class="highlight-cpp notranslate">

<div class="highlight">

    .. code-block:: bash

</div>

</div>

> <div>
>
> cmake -DBOUT_ENABLE_PYTHON=ON
>
> </div>

It can be especially tricky if you want to run boutpp on login nodes for
simple post processing, but due to differences in the instruction set
the compiled modules for the compute nodes do not run there. In that
case you need to manually install all needed dependencies. It is
probably a good idea to use a different build directory, to not
unintentionally modify your BOUT++ compilation for the compute nodes.

If you are running fedora - you can install pre-build binaries:

<div class="highlight-bash notranslate">

<div class="highlight">

    sudo dnf install python3-bout++-mpich
    module load mpi/mpich-$(arch)

</div>

</div>

You can also pip install boutpp with:

<div class="highlight-bash notranslate">

<div class="highlight">

    pip install boutpp-nightly

</div>

</div>

This will download the latest boutpp-nightly version, compile and
install it. Note that you still need all the non-python dependencies
like mpi. Note that after
<span class="pre">`pip`</span>` `<span class="pre">`install`</span>` `<span class="pre">`boutpp-nightly`</span>
the <span class="pre">`boutpp`</span> module is installed, so you can
use
<span class="pre">`import`</span>` `<span class="pre">`boutpp`</span>
independent of the version used.

After the 5.0.0 release you will also be able to install the latest
released version of boutpp with:

<div class="highlight-bash notranslate">

<div class="highlight">

    pip install boutpp

</div>

</div>

</div>

<div id="purpose" class="section">

## Purpose<a href="#purpose" class="headerlink"
title="Permalink to this heading">#</a>

The boutpp module exposes (part) of the BOUT++ C++ library to python. It
allows to calculate e.g. BOUT++ derivatives in python.

State —– Field3D and Field2D are working. If other fields are needed,
please open an issue. Fields can be accessed directly using the \[\]
operators, similar to numpy. The get all data,
<span class="pre">`f3d[:]`</span> is equivalent to
<span class="pre">`f3d[:,`</span>` `<span class="pre">`:,`</span>` `<span class="pre">`:]`</span>
and returns a numpy array. This array can be addressed with e.g.
<span class="pre">`[]`</span> operators, and then the field can be set
again with
<span class="pre">`f3d[:]`</span>` `<span class="pre">`=`</span>` `<span class="pre">`numpyarray`</span>.
It is also possible to set a part of an Field3D with the
<span class="pre">`[]`</span> operators. Addition, multiplication etc.
are all available. The derivatives should all be working, if find a
missing one, please open an issue.

Note that views are currently not supported, thus
<span class="pre">`f3d[:]`</span>` `<span class="pre">`+=`</span>` `<span class="pre">`1`</span>
will modify the returned copy, and the <span class="pre">`f3d`</span>
object will be unchanged.

</div>

<div id="functions" class="section">

## Functions<a href="#functions" class="headerlink"
title="Permalink to this heading">#</a>

See the API documentation <a href="../_apidoc/boutpp.html#boutpp-api"
class="reference internal"><span class="std std-ref">boutpp
package</span></a>

</div>

<div id="examples" class="section">

## Examples<a href="#examples" class="headerlink"
title="Permalink to this heading">#</a>

Some trivial post processing:

<div class="highlight-python notranslate">

<div class="highlight">

    import boutpp
    import numpy as np
    args="-d data -f BOUT.settings -o BOUT.post"
    boutpp.init(args)
    dens = boutpp.Field3D.fromCollect("n", path="data")
    temp = boutpp.Field3D.fromCollect("T", path="data")
    pres = dens * temp
    dpdz = boutpp.DDZ(pres, outloc="CELL_ZLOW")

</div>

</div>

A simple MMS test:

<div class="highlight-python notranslate">

<div class="highlight">

    import boutpp
    import numpy as np
    boutpp.init("-d data -f BOUT.settings -o BOUT.post")
    for nz in [64, 128, 256]:
        boutpp.setOption("meshz:nz", "%d"%nz)
        mesh = boutpp.Mesh(OptionSection="meshz")
        f = boutpp.create3D("sin(z)", mesh)
        sim = boutpp.DDZ(f)
        ana = boutpp.create3D("cos(z)", mesh)
        err = sim - ana
        err = boutpp.max(boutpp.abs(err))
        errors.append(err)

</div>

</div>

A real example - unstagger data:

<div class="highlight-python notranslate">

<div class="highlight">

    import boutpp
    boutpp.init("-d data -f BOUT.settings -o BOUT.post")
    # uses location from dump - is already staggered
    upar = boutpp.Field3D.fromCollect("Upar")
    upar = boutpp.interp_to(upar, "CELL_CENTRE")
    # convert to numpy array
    upar = upar[:]

</div>

</div>

A real example - check derivative contributions:

<div class="highlight-python notranslate">

<div class="highlight">

    #!/usr/bin/env python

    from boutpp import *
    import numpy as np
    from netCDF4 import Dataset
    import sys

    if len(sys.argv)> 1:
        path=sys.argv[1]
    else:
        path="data"

    times=collect("t_array",path=path)

    boutpp.init("-d data -f BOUT.settings -o BOUT.post")
    with Dataset(path+'/vort.nc', 'w', format='NETCDF4') as outdmp:
       phiSolver=Laplacian()
       phi=Field3D.fromCollect("n",path=path,tind=0,info=False)
       zeros=phi.getAll()*0
       phi.setAll(zeros)
       outdmp.createDimension('x',zeros.shape[0])
       outdmp.createDimension('y',zeros.shape[1])
       outdmp.createDimension('z',zeros.shape[2])
       outdmp.createDimension('t',None)
       t_array_=outdmp.createVariable('t_array','f4',('t'))
       t_array_[:]=times
       ExB     = outdmp.createVariable('ExB'    ,'f4',('t','x','y','z'))
       par_adv = outdmp.createVariable('par_adv','f4',('t','x','y','z'))
       def setXGuards(phi,phi_arr):
           for z in range(tmp.shape[2]):
               phi[0,:,z]=phi_arr
               phi[1,:,z]=phi_arr
               phi[-2,:,z]=phi_arr
               phi[-1,:,z]=phi_arr
       with open(path+"/equilibrium/phi_eq.dat","rb") as inf:
           phi_arr=np.fromfile(inf,dtype=np.double)
           bm="BRACKET_ARAKAWA"

           for tind in range(len(times)):
               vort     = Field3D.fromCollect("vort"     ,path=path,tind=tind,info=False)
               U        = Field3D.fromCollect("U"        ,path=path,tind=tind,info=False)
               setXGuards(phi,phi_arr)
               phi=phiSolver.solve(vort,phi)
               ExB[tind,:,:,:]=(-bracket(phi, vort, bm, "CELL_CENTRE")).getAll()
               par_adv[tind,:,:,:]=(- Vpar_Grad_par(U, vort)).getAll()

</div>

</div>

</div>

</div>

<div class="prev-next-area">

<a href="output_and_post.html" class="left-prev"
title="previous page"><em></em></a>

<div class="prev-next-info">

previous

Post-processing

</div>

<a href="time_integration.html" class="right-next"
title="next page"></a>

<div class="prev-next-info">

next

Time integration

</div>

</div>

</div>

<div class="bd-sidebar-secondary bd-toc">

<div class="sidebar-secondary-items sidebar-secondary__inner">

<div class="sidebar-secondary-item">

<div class="page-toc tocsection onthispage">

Contents

</div>

- <a href="#installing" class="reference internal nav-link">Installing</a>
- <a href="#purpose" class="reference internal nav-link">Purpose</a>
- <a href="#functions" class="reference internal nav-link">Functions</a>
- <a href="#examples" class="reference internal nav-link">Examples</a>

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
