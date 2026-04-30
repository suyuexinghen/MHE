# 05. Family Design

## 1. Why Family Is a First-Class Design Object

fealpy extension 的核心抽象是 PDE family，不是通用 Python 脚本运行器。每个 family 决定：

- **网格维度**（1D/2D/3D）
- **FE 空间类型**（Lagrange/Nedelec/RT/HuZhang/Taylor-Hood）
- **PDE 算子结构**（椭圆/双曲/鞍点/非线性/瞬态）
- **求解器方法**（direct 足够，还是需要迭代 Krylov）
- **输出指标**（L2 error 是否足以评价；是否需要 H1-seminorm 或 curl error）

将 family 作为一等设计对象可以在 compiler、validator、evidence 层做 per-family 决策，而非依赖 if-else 分支猜测。

## 2. Supported Families — Compiler Template Dispatch

`_FAMILY_RENDERERS` dict 将 18 个 PDE families 映射到 7 个模板方法：

| PDE Family | Template | FE Space | Key Integrator(s) |
|---|---|---|---|
| `poisson` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `diffusion_convection_reaction` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `diffusion_reaction` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `hyperbolic` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `parabolic` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `wave` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `interface_poisson` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `polyharmonic` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `quasilinear_elliptic` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `mgtensor_possion` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `helmholtz` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `surface_poisson` | scalar_diffusion | Lagrange | ScalarDiffusionIntegrator |
| `curlcurl` | curl_curl | FirstNedelec | CurlCurlIntegrator |
| `linear_elasticity` | linear_elasticity | HuZhang | LinearElasticityIntegrator |
| `darcy` | darcy | RT + Lagrange P0 | BlockForm (Div + Mass) |
| `darcyforchheimer` | darcy | RT + Lagrange P0 | BlockForm (Div + Mass) |
| `stokes` | stokes | Taylor-Hood P2/P1 | BlockForm (ViscousWork + Div) |
| `allen_cahn` | allen_cahn | Lagrange | Time loop + convex splitting |
| `navier_stokes` | navier_stokes | Taylor-Hood P2/P1 | Time loop + Picard iteration |

**Fallback**: 任何不在 `_FAMILY_RENDERERS` 中的 family 回退到 `_render_scalar_diffusion` 模板。

## 3. FE Space Types and DOF Estimation

| Type | DOF per cell (2D tri, p=1) | Mesh types | Used by |
|---|---|---|---|
| `Lagrange` | `(p+1)(p+2)/2` | tri, quad, tet, hex, uniform | 12 scalar families + Allen-Cahn |
| `FirstNedelec` | 3 | tri, quad | Curl-curl |
| `RaviartThomas` | 3 | tri, quad | Darcy (flux) |
| `HuZhang` | `(p+1)(p+2)` | tri, quad | Linear elasticity |
| `Taylor-Hood` | P2+P1 dofs combined | tri, tet | Stokes, Navier-Stokes |

DOF estimation (`quota.py`) accounts for mesh dimension and FE type to produce memory estimates. Default quota limits: 2M DOFs, 2048 MB.

## 4. Mesh Type Compatibility

| Mesh Type | Dimension | Supported FE Spaces |
|---|---|---|
| `interval` | 1D | Lagrange |
| `tri` | 2D | All |
| `quad` | 2D | Lagrange, FirstNedelec |
| `tet` | 3D | Lagrange, Taylor-Hood |
| `hex` | 3D | Lagrange |
| `uniform` | 1D/2D/3D | Lagrange |

## 5. Per-Family Output Metrics

| Family Group | Primary Metrics | Notes |
|---|---|---|
| Scalar diffusion | l2_error, h1_error, dof, wall_time | PDE model provides exact solution |
| Curl-curl | l2_error, dof, wall_time | Edge element error norms |
| Linear elasticity | l2_error, h1_error, dof, wall_time | Stress tensor formulation |
| Darcy mixed | dof, wall_time | Saddle-point; L2 error not always well-defined |
| Stokes | l2_error, dof, wall_time | Velocity-pressure decoupling |
| Allen-Cahn | l2_error, dof, wall_time | Final timestep error |
| Navier-Stokes | l2_error, dof, wall_time | Final timestep error |

## 6. Family Extension Rules

添加新 PDE family 的最低要求：

1. 确认 family 在 `types.py` 的 `FealpyPdeFamily` literal 中
2. 在 `compiler.py` 中编写 `_render_<family>()` 模板方法
3. 在 `_FAMILY_RENDERERS` dict 中添加映射
4. 如果涉及新的 FE 空间类型，更新 `estimate_dofs()` 和 `_render_mesh_builder()`
5. 在 `benchmark_cases.py` 中添加至少一个 benchmark case
6. 在 compiler 测试中添加模板内容验证
