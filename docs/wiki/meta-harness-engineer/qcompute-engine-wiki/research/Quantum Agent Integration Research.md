# Autonomous Agent Integration in Quantum-Classical Hybrid Workflows: Architectures, Platforms, and Algorithmic Discoveries

The integration of autonomous agents into the quantum software stack
represents a fundamental shift from manual, interactive circuit design
toward automated, self-optimizing quantum-classical hybrid workflows. As
the complexity of Noisy Intermediate-Scale Quantum (NISQ) devices
increases, the traditional approach of static compilation and
heuristic-based error mitigation faces significant scalability
challenges. Autonomous agents, powered by large language models (LLMs)
and reinforcement learning (RL), offer a mechanism for \"test-time
scaling,\" where the system uses computational effort to search for more
efficient circuit representations, more accurate routing solutions, and
hardware-specific error mitigation strategies.

## 1. Agent-Driven Quantum Circuit Compilation Systems

Circuit compilation---the process of translating high-level quantum
algorithms into hardware-compatible gate sequences---is an inherently
complex optimization problem involving topological constraints, noise
characteristics, and gate synthesis. Recent developments have
demonstrated that agentic systems can significantly outperform
traditional compilers by treating transpilation as a sequential
decision-making or search-based process.

### 1.1 QUASAR: Agentic RL for Assembly Generation

QUASAR has emerged as a specialized agentic reinforcement learning
framework tailored for the generation and optimization of OpenQASM 3.0
circuits.^1^ The system is built upon a 4B-parameter model, fine-tuned
from the Qwen3-Instruct series, utilizing a training paradigm that
emphasizes reward shaping to elicit high semantic fidelity.^3^

#### 1.1.1 RL State Representation and Action Space

The reinforcement learning environment for QUASAR is designed to bridge
the gap between high-level algorithmic intent and low-level assembly
syntax. The state representation in QUASAR is defined by the
concatenation of the natural language problem description, the target
Hamiltonian for optimization tasks (such as VQE or QAOA), and the
current partial OpenQASM 3.0 code string.^1^ Unlike compilers that
utilize graph-based embeddings of the hardware, QUASAR relies on the
LLM's internal latent representation to handle the structural nuances of
the circuit graph.^1^

The action space is comprised of the token vocabulary of the base LLM,
constrained during generation to adhere to the OpenQASM 3.0 grammar.^3^
Key actions include:

- **Qubit and Bit Declarations:** Initializing the quantum and classical
  registers (e.g., qubit\[n\] q; and bit\[n\] c;).

- **Gate Application:** Selecting from the standard gate set, including
  Clifford and T gates, as well as parameterized rotations.^2^

- **Parameter Specification:** Determining precise numerical values for
  gates like \$RX(\\theta)\$, \$RY(\\theta)\$, and \$RZ(\\theta)\$.

- **Measurement and Control:** Implementing measurement operations and
  classical feed-forward logic.

#### 1.1.2 Hierarchical Reward Mechanism and Formulas

The performance of QUASAR is largely attributed to its 4-level
hierarchical reward mechanism, which ensures that the agent prioritizes
syntactic validity before attempting to optimize semantic
performance.^1^ This mechanism uses a gated structure where failure at a
lower level results in a terminal negative reward, preventing the
computational waste of evaluating unexecutable code.

  -------------------------------------------------------------------------------
  **Reward Level**    **Objective**     **Evaluation      **Formula/Mechanism**
                                        Signal**          
  ------------------- ----------------- ----------------- -----------------------
  **Syntactic         Grammar validity  Qiskit QASM 3.0   \$R\_{syn} = 1\$ if
  (\$R\_{syn}\$)**                      Parser            parsable, else \$-1\$
                                                          (terminal)

  **Distributional    Basis state       Jensen-Shannon    \$R\_{dist} = 1 -
  (\$R\_{dist}\$)**   alignment         Distance          JS(P\_{gen} \\\|
                                                          P\_{ref}\$

  **Semantic          Expectation value Simulator         \$R\_{exp} =
  (\$R\_{exp}\$)**                      expectation       \\exp(-\\\| \\langle H
                                                          \\rangle\_{gen} -
                                                          \\langle H
                                                          \\rangle\_{ref} \\\$

  **Optimization      Operational       Iteration count & \$R\_{opt} = w_d \\cdot
  (\$R\_{opt}\$)**    efficiency        depth             (Depth)\^{-1} + w_n
                                                          \\cdot
                                                          (N\_{opt})\^{-1}\$
  -------------------------------------------------------------------------------

The Jensen-Shannon (JS) divergence is utilized to provide a smooth
gradient for distributional alignment, calculated as:

\$\$JS(P \\\| Q) = \\frac{1}{2} D\_{KL}(P \\\| M) + \\frac{1}{2}
D\_{KL}(Q \\\| M)\$\$

where \$M = \\frac{1}{2}(P + Q)\$.^2^ This reward encourages the agent
to produce circuits that result in the correct probability amplitudes
across all computational basis states, a prerequisite for accurate
expectation value estimation in hybrid algorithms.

#### 1.1.3 Training Logistics and Latency

Training the QUASAR 4B model required a significant computational
investment, utilizing 16 NVIDIA H100-64GB GPUs over a 48-hour period.^3^
The training process involved a batch size of 128 and 16 rollouts per
prompt, using Generalized Relative Policy Optimization (GRPO) to
stabilize learning across the hierarchical rewards.^1^ This intensive
post-training phase resulted in a Pass@1 rate of 99.31% and a Pass@10
rate of 100%, outperforming significantly larger models like GPT-4o and
DeepSeek-V3 in quantum-specific code generation.^1^ Once trained, the
model exhibits low inference latency, typically generating optimized
circuits in under 2 seconds, making it feasible for integration into
dynamic, agent-led hybrid loops.

### 1.2 QAgent: Multi-Agent Orchestration

QAgent (arXiv:2508.20134) takes a different approach by utilizing a
multi-agent system (MAS) to automate OpenQASM programming through
collaboration rather than end-to-end RL training.^5^ This architecture
is particularly effective for bridging the expertise gap between domain
scientists and quantum hardware.

#### 1.2.1 Agent Communication and Message Schema

The QAgent architecture consists of three core agent types---Planner,
Coder, and Reviewer---communicating through a structured, iterative
pipeline.^6^ The interaction is not a fixed linear DAG but rather a
dynamic loop governed by feedback from the Reviewer.

- **Planner Agent:** Analyzes the user\'s natural language request and
  decomposes it into a sequence of sub-tasks. For a Grover search, the
  Planner identifies stages for state preparation, oracle
  implementation, and diffusion.^6^

- **Coder Agent:** Implements each sub-task using a \"Dynamic-few-shot\"
  or \"Tool-augmented\" approach. The message schema includes the
  sub-task description, retrieved RAG context, and any previous failed
  attempts.^6^

- **Reviewer Agent:** Acts as the verifier, executing the generated code
  on an internal simulator and comparing the output to the expected
  behavior. If a failure occurs, the Reviewer provides a \"revised
  strategy\" back to the Coder, often using chain-of-thought (CoT)
  reasoning to explain the discrepancy.^6^

#### 1.2.2 RAG Knowledge Base and Toolset

To overcome the limitations of static training data, QAgent integrates a
Retrieval-Augmented Generation (RAG) system.^6^

- **Indexing:** The RAG database is indexed using vector embeddings of
  canonical quantum algorithms, OpenQASM 3.0 code snippets, and
  backend-specific documentation.^6^

- **Tools:** The \"Tools-augmented Coder\" can invoke external
  operations such as generate_oracle, apply_gate_set, and check_syntax.
  The tool call format typically follows a Pythonic function call
  structure, which the agent translates into the final OpenQASM
  output.^6^

### 1.3 SimpleTES: Evaluation-Driven Search

The SimpleTES framework represents an instantiation of the
evaluation-driven scaling paradigm, specifically applied to the qubit
routing problem on hardware like the IBM Q20 (20-qubit superconducting)
and neutral-atom architectures.^7^ SimpleTES achieved a 24.5% reduction
in SWAP gate overhead compared to the LightSABRE algorithm, which itself
is an optimized version of the standard SABRE heuristic.^7^

#### 1.3.1 The **\$C \\times L \\times K\$** Scaling Paradigm

The SimpleTES architecture is defined by three operational axes that
allow the agent to scale its performance by using more compute:

1.  **Parallel Exploration (\$C\$):** The system generates \$C\$
    independent routing candidates in parallel. In the context of qubit
    routing, this is often achieved by running randomized versions of
    the SABRE algorithm with varied initial layouts and seed values.^7^

2.  **Feedback-Driven Refinement (\$L\$):** Each candidate is refined
    over \$L\$ steps. An LLM refiner observes the SWAP count and depth
    of the current routing and suggests localized modifications to the
    initial layout or the swap-selection policy.^7^

3.  **Local Selection (\$K\$):** At each iteration, the system scores
    the candidates and selects the top \$K\$ finalists to proceed to the
    next refinement step. This prevents the search from getting stuck in
    local minima by maintaining a diverse set of high-performing
    options.^7^

#### 1.3.2 Evaluator Scoring Function

The scoring function in SimpleTES is a multi-objective heuristic that
estimates the quality of the compiled circuit without requiring
execution on the QPU. The score combines SWAP count, circuit depth, and
estimated fidelity:

\$\$Score = w_1 \\cdot N\_{SWAP} + w_2 \\cdot Depth - w_3 \\cdot
\\log(\\text{Fidelity}\_{est})\$\$

The estimated fidelity is derived from the hardware calibration data,
integrating the product of gate fidelities along the circuit\'s critical
path.^7^ While the specific weights \$w_i\$ are often tuned per
architecture, the emphasis on fidelity ensures that the agent does not
just minimize gate count at the expense of using higher-error qubits or
more noisy coupling links.^7^

## 2. Quantum Cloud Platform APIs: Automation-Ready Assessment

For an autonomous agent to coordinate hybrid workflows, it must possess
robust, programmatic access to quantum hardware and simulators. This
requires cloud platforms to move beyond interactive Jupyter notebooks
toward standardized, low-latency APIs and protocol-driven tool calling.

### 2.1 The Quafu Platform and pyQuafu SDK

The Quafu platform, launched by the Beijing Academy of Quantum
Information Sciences (BAQIS), is a primary resource for accessing
superconducting processors like the 136-qubit Baihua chip.^10^ Its
Python SDK, pyquafu, is designed for high-level circuit construction and
task management.^12^

#### 2.1.1 pyquafu SDK API Precision

The pyquafu SDK provides the primary programmatic interface for circuit
construction and backend interaction.^13^

- **QuantumCircuit Class:**

  - Constructor: QuantumCircuit(qubit_count: int)

  - Methods: x(q), y(q), z(q), h(q), cnot(c, t), ry(q, theta), rx(q,
    theta), rz(q, theta), cz(c, t). Rotation angles are specified in
    radians.^14^

- **Task Submission and Configuration:**

  - Task object: task = Task()

  - Config: task.config(backend=\"ScQ-P18\", shots=2000, compile=True).
    The compile flag determines whether the circuit is transpiled by the
    backend server or executed as provided.^14^

  - Execution: res = task.send(circuit). This is a synchronous call in
    the standard SDK, though asynchronous submission is supported via
    the task.submit() method.^14^

- **Result Schema:** The job result is returned as a dictionary-like
  object:\
  JSON\
  {\
  \"counts\": {\"00\": 1050, \"01\": 950},\
  \"job_id\": \"uuid-string\",\
  \"status\": \"completed\",\
  \"metadata\": {\
  \"execution_time\": 0.45,\
  \"calibration_date\": \"2025-09-24T10:00:00Z\"\
  }\
  }

- **Calibration Data API:** Accessible via task.get_backend_info(),
  returning the chip\'s coupling map, T1/T2 times, and gate fidelities
  for all active qubits.^14^

#### 2.1.2 QuafuCloud MCP (Model Context Protocol)

The QuafuCloud MCP service, launched on Alibaba Cloud Bailian, provides
a standardized tool-calling interface for LLM agents.^16^ MCP acts as a
\"USB-C for AI,\" allowing agents to interact with Quafu resources
through a unified protocol without needing to manage local Python
environments.^18^

- **Tool List:**

  - submit_qasm: Accepts an OpenQASM 3.0 string and backend ID, returns
    a job ID.

  - get_job_result: Accepts a job ID, returns the measurement counts.

  - get_backend_specs: Returns the coupling map and fidelity data for a
    specific chip.

- **Authentication:** External agents authenticate to the MCP gateway
  via API Key or OAuth 2.0 with PKCE.^19^ The AI Gateway manages access
  permissions and prevents \"tool poisoning\" by validating the input
  schemas before passing requests to the backend.^17^

### 2.2 QSteed: Architectural Virtualization on Quafu

QSteed is an innovative system-software framework integrated into Quafu
to handle multi-backend management and hardware-aware compilation.^10^
It virtualizes the physical hardware into a layered hierarchy:

1.  **Real QPU:** The physical superconducting chip (e.g., Baihua).^10^

2.  **Standard QPU (StdQPU):** A normalized representation of the chip's
    capabilities.^10^

3.  **Substructure QPU (SubQPU):** Smaller, connected subregions of the
    chip.

4.  **Virtual QPU (VQPU):** The optimal subregion selected specifically
    for a given user circuit.^10^

#### 2.2.1 VQPU Selection and Pre-execution Fidelity

QSteed's compiler uses a \"select-then-compile\" workflow.^10^ It first
queries the VQPU library to find a subregion whose topology matches the
circuit's interaction graph.^15^ The selection is guided by a fidelity
heuristic that aggregates the recent calibration data for the qubits and
couplers in that subregion.^21^ This approach allows QSteed to
consistently outperform Qiskit in both compilation speed and final
circuit fidelity on the 122-qubit Baihua chip.^10^

### 2.3 Qiskit and Qiskit Runtime Primitives

IBM's Qiskit Runtime provides the \"Primitives\" API---Sampler and
Estimator---which are essential for agent-driven iterative workflows
like VQE.^22^

- **Sampler:** Returns probability distributions (quasi-probabilities)
  from circuits.

- **Estimator:** Directly computes expectation values \$\\langle \\psi
  \| H \| \\psi \\rangle\$ for a given Hamiltonian, optimizing the
  measurement process by grouping commuting Pauli terms.^23^

- **Session API:** Qiskit Runtime Sessions allow an agent to submit a
  sequence of jobs to the same backend with reduced queue latency.^24^
  This is critical for VQE, where the iterative feedback loop between
  the classical optimizer and the quantum processor requires low-latency
  execution.^23^

#### 2.3.1 Transpiler Optimization Levels

Qiskit's transpiler uses a staged pass manager with four levels
(0-3).^22^

  --------------------------------------------------------------------------------
  **Level**         **Goal**           **Key Passes**            **Computational
                                                                 Effort**
  ----------------- ------------------ ------------------------- -----------------
  **0**             Characterization   Minimal mapping, basic    Minimal
                                       SWAP insertion            

  **1**             Standard           Default routing, basic    Default
                                       gate cancellation         

  **2**             Enhanced           Heuristic layout,         Moderate
                                       CommutativeCancellation   

  **3**             Maximum            SabreLayout (high         High
                                       trials), Collect2qBlocks  
  --------------------------------------------------------------------------------

For NISQ devices, SabreLayout is the most critical pass for reducing
2-qubit gate overhead. Its behavior is controlled by:

- max_iterations: Number of forward-backward passes to refine the
  layout.^26^

- layout_trials: Number of random initial layouts to attempt.^26^

- swap_trials: Number of swap-selection trials per layout trial. For
  circuits with 40-100 qubits, increasing these values from the default
  20 to 200 can reduce SWAP counts by over 10%.^26^

## 3. Quantum Chemistry Programmatic Workflows

Quantum chemistry is the primary driver for hybrid quantum-classical
algorithms. An autonomous agent in this context serves as the \"loop
controller,\" orchestrating the movement of data between classical
density functional theory (DFT) tools and the quantum variational
eigensolver (VQE).^28^

### 3.1 The Programmatic VQE Pipeline

The standard pipeline for estimating the ground state energy of a
molecule is as follows ^28^:

1.  **Classical Setup:** Use PySCF or OpenFermion to specify the
    molecular geometry (e.g., \$H_2O\$ bond lengths and angles) and
    basis set (e.g., STO-3G).^31^

2.  **Integral Generation:** Compute one- and two-electron integrals.
    These are often exported in **FCIDUMP** (ASCII) or **HDF5** (Binary)
    formats.^32^

3.  **Active Space Selection:** Reduce the number of orbitals to fit the
    available qubits. Algorithms like **LASSCF** (Localized Active Space
    Self-Consistent Field) are used to isolate the chemically active
    part of the molecule.^28^

4.  **Fermionic-to-Qubit Mapping:** Transform the fermionic Hamiltonian
    into a qubit operator using **Jordan-Wigner** or **Bravyi-Kitaev**
    transformations.^30^

5.  **Ansatz Selection:** Define the parameterized trial state
    \$\|\\psi(\\theta)\\rangle\$.^23^

6.  **Iterative Optimization:** The agent chooses a classical optimizer
    (e.g., COBYLA, L-BFGS-B, or SPSA) and iteratively calls the quantum
    Estimator primitive to minimize the energy.^23^

### 3.2 Ansatz Families and Resource Scaling

The success of VQE depends on the balance between the expressivity of
the ansatz and its circuit depth.

  ---------------------------------------------------------------------------
  **Ansatz**        **Parameter       **Gate Depth**    **Notes**
                    Scaling**                           
  ----------------- ----------------- ----------------- ---------------------
  **UCCSD**         \$O(n\_{occ}\^2   \$O(N\^4)\$       Chemically motivated,
                    n\_{virt}\^2)\$                     high accuracy ^28^

  **HEA**           \$O(L \\cdot N)\$ \$O(L)\$          Shallow,
                                                        hardware-efficient,
                                                        prone to barren
                                                        plateaus ^30^

  **ADAPT-VQE**     Adaptive          Growing           Iteratively adds
                                                        operators based on
                                                        energy gradients ^34^
  ---------------------------------------------------------------------------

Research on \$H_2\$ and \$LiH\$ on real hardware shows that UCCSD
combined with L-BFGS-B optimization can achieve chemical accuracy
(\$\\leq 1.6 \\text{ mHa}\$).^28^ However, for larger molecules like
\$H_2O\$, active space reduction is essential to keep the qubit count
within the 4-12 qubit range manageable by current NISQ devices.^28^

### 3.3 Data Exchange Formats: FCIDUMP vs HDF5

For an automated workflow, the choice of exchange format for molecular
integrals is critical for interoperability.^32^

- **FCIDUMP:** The de facto standard for many quantum chemistry codes
  (Molpro, PySCF, HANDE). It is an ASCII format that is human-readable
  and preserves double precision, but it can be slow to parse for large
  systems.^32^

- **HDF5:** A hierarchical binary format used by some programs (like
  some versions of PySCF or proprietary codes) to handle the \$O(N\^4)\$
  scaling of two-electron integrals efficiently. However, a lack of
  unified standard for the internal HDF5 schema often limits its
  transferability between different software packages.^33^

## 4. Error Mitigation as a Searchable Space

In the NISQ era, error mitigation (EM) is necessary to extract
meaningful results from noisy backends. Rather than applying a single
technique, modern agentic systems treat the EM strategy selection as a
search problem over a high-dimensional space of scaling factors,
extrapolation methods, and stacked sequences.

### 4.1 Mitiq API Precision

Mitiq is the leading extensible toolkit for implementing EM techniques
on quantum computers.^37^ Its primary function for zero-noise
extrapolation (ZNE) is execute_with_zne().^38^

- **execute_with_zne(circuit, executor, factory, scale_noise):**

  - circuit: The target quantum program (Qiskit, Cirq, or OpenQASM).^39^

  - executor: A user-defined function that takes a circuit and returns
    an expectation value.^39^

  - factory: A ZNEFactory object that determines the extrapolation
    method.^40^

    - LinearFactory(scale_factors=\[1.0, 2.0, 3.0\])

    - RichardsonFactory(scale_factors=\[1.0, 3.0, 5.0\])

    - PolyFactory(scale_factors=\[1.0, 2.0, 3.0\], order=2)

    - AdaExpFactory(scale_factor=2.0, steps=5): An adaptive factory that
      chooses scale factors dynamically.^40^

  - scale_noise: The scaling method, typically fold_global or
    fold_gates_at_random.^40^

### 4.2 Measurement Error Mitigation and Scaling

Measurement (readout) errors are often the dominant source of noise on
superconducting chips.^42^

- **CompleteMeasFitter:** Constructs a full \$2\^n \\times 2\^n\$
  calibration matrix. While accurate, it requires \$2\^n\$ calibration
  circuits, making it unscalable beyond 10-15 qubits.^24^

- **TensoredMeasFitter:** Assumes qubit-local errors and constructs the
  matrix as a tensor product of small \$2 \\times 2\$ matrices,
  requiring only 2 calibration circuits. This is the preferred method
  for agent-led workflows on large devices.^24^

- **TREX (Twirled Readout Error eXtinction):** A modern approach that
  uses Pauli twirling during measurement to transform complex noise into
  a simple bit-flip channel, which can then be mitigated with minimal
  overhead.^24^

### 4.3 Dynamical Decoupling (DD) and EM Stacking

Dynamical decoupling suppresses decoherence by applying sequences of
pulse-level or gate-level operations to idling qubits.^42^

- **Sequences:** Standard sequences like **XY4**, **CPMG**, and **KDD**
  are available in Qiskit's PassManager.^45^

- **Stacking:** Agents can combine DD with ZNE and MEM. However,
  stacking introduces a cumulative sampling overhead:\
  \$\$N\_{shots\\\_total} = N\_{shots} \\cdot \\prod\_{i \\in EM}
  \\gamma_i\$\$\
  where \$\\gamma_i\$ is the sampling overhead for technique \$i\$. For
  ZNE, \$\\gamma\$ scales with the number of scale factors and the
  extrapolation order.^24^ Agents must balance the gain in fidelity
  against the cost in QPU time.

## 5. Quantum Transpilation as Optimization Target

Transpilation is not a one-size-fits-all process. The same algorithm can
be transpiled into thousands of different circuits depending on the
routing algorithm, initial layout, and optimization level. This \"search
space\" is the primary target for evaluation-driven agents.

### 5.1 Search Space Sizing and Heuristics

For an 8-qubit circuit with depth 50 on a grid topology, the number of
meaningfully different transpilation outcomes is roughly \$O(N! \\cdot
R\^D)\$, where \$N\$ is the number of qubits, \$R\$ is the number of
routing choices per step, and \$D\$ is the depth. This
order-of-magnitude estimation (\$10\^5\$ to \$10\^7\$ configurations)
makes exhaustive search impossible, necessitating the use of
pre-execution fidelity heuristics.^7^

- **Estimated Success Probability (ESP):** The simplest heuristic,
  calculated as the product of all gate and readout fidelities along the
  circuit paths.^8^

- **Quantum Vulnerability Analysis (QVA):** A more advanced heuristic
  that accounts for error propagation through 2-qubit gates, using a
  system-specific weighting factor \$w\$.^8^ QVA has shown a
  significantly higher correlation (\$r\^2 \\approx 0.82\$) with actual
  hardware execution results compared to ESP.^8^

### 5.2 Compilation Benchmarks

Standard benchmark suites are used to measure the effectiveness of new
compilation strategies.^15^

- **QASMBench:** A cross-platform benchmark suite for circuits of
  various sizes (small, medium, large).^15^

- **MQT Bench:** A modern benchmark suite focusing on scalability and
  hardware-aware compilation.

- **Benchpress:** A suite focused on the performance of transpiler
  passes under extreme depth and width constraints.

  ------------------------------------------------------------------------------
  **Benchmark**   **Qubits**   **Logical   **Qiskit CX **QSteed    **SimpleTES
                               CX**        (L3)**      CX**        CX**
  --------------- ------------ ----------- ----------- ----------- -------------
  sym9_193        9            150         212         198         185

  hwb7_59         7            80          125         115         110

  random_30       30           500         850         780         N/A
  ------------------------------------------------------------------------------

Results on Quafu's Baihua processor show that QSteed and SimpleTES
consistently reduce CNOT counts by 10-20% relative to Qiskit's highest
optimization level, particularly on sparse interaction graphs where
initial layout selection is critical.^7^

## 6. Cross-System Comparative Analysis

The integration of agents into quantum workflows can be categorized by
their core architecture and task decomposition strategy.

  ----------------------------------------------------------------------------------------------------------------
  **System**      **Task Decomposition**   **Evaluation   **Agent             **Backend Coupling**    **Code or
                                           Signal**       Coordination**                              Circuit?**
  --------------- ------------------------ -------------- ------------------- ----------------------- ------------
  **QUASAR**      Sequential Token Gen     4-Level Reward Single Agent (RL)   Simulator-in-the-loop   OpenQASM 3.0

  **QAgent**      Planner-Coder-Reviewer   Multi-round    Hierarchical MAS    Python Tool Callbacks   OpenQASM 3.0
                                           Reflection                                                 

  **SimpleTES**   \$C \\times L \\times    Multi-obj      Evaluation-Driven   Hardware Calibration    Routed Trace
                  K\$ Search               Scoring                                                    

  **QSteed**      VQPU Selection           Fidelity       Resource            Direct Cloud Access     Executable
                                           Heuristic      Virtualization                              QASM

  **Meta-VQE**    Parameter Initializer    Energy         Meta-Learning       Estimator Primitive     Parameter
                                           Gradient                                                   Set
  ----------------------------------------------------------------------------------------------------------------

### 6.1 Tradeoffs and Generalization

- **Sample Efficiency:** RL-native systems like QUASAR require millions
  of simulator calls during training but are extremely fast at
  inference.^1^ Evaluation-driven systems like SimpleTES generalize
  better to new architectures because they perform the search at
  test-time, though they incur higher per-circuit latency.^7^

- **Task Generalization:** Multi-agent systems like QAgent are the most
  flexible, as they can adapt to different quantum tasks (compilation,
  algorithm design, error mitigation) simply by updating the RAG
  knowledge base and the tool-calling definitions.^6^ Task-specific
  architectures like QSteed offer the highest performance for their
  specific niche (compilation on superconducting chips) but require
  significant re-engineering for other architectures like neutral atoms
  or ion traps.^10^

## 7. Evaluation Metrics & Benchmarks for Agentic Systems

Evaluating an agent integrated with a quantum backend requires metrics
that capture both the efficiency of the classical agent and the quality
of the quantum output.

### 7.1 Key Metrics

- **SWAP Gate Overhead:** The ratio of SWAPs added during transpilation
  to the number of logical CNOT gates. This is the gold standard for
  routing efficiency.^7^

- **Hellinger Fidelity (\$F_H\$):** Measures the similarity between the
  observed measurement distribution and the ideal distribution. It is
  more robust than simple fidelity for NISQ results.^15^

- **Pass@k Rate:** For generative agents (QUASAR, QAgent), the
  probability that at least one of the top \$k\$ generated circuits is
  both syntactically and functionally correct.^1^

- **Inference Latency:** The time taken by the agent to produce an
  optimized circuit or error mitigation strategy.

### 7.2 Correlation of Estimates with Reality

A major challenge for autonomous agents is the \"drift\" in quantum
hardware. Pre-execution estimates based on calibration data (like QVA or
ESP) often lose accuracy if the data is more than a few hours old.^9^
Published \$r\^2\$ values for fidelity estimation typically range from
0.70 to 0.85 on IBM backends, suggesting that while heuristics are
useful for ranking candidates, they cannot yet perfectly predict the
execution success rate.^8^

## 8. Gap Report: Limitations of Public Information

Despite the high technical detail provided in recent publications,
several gaps remain that affect the implementation of fully autonomous
agent-quantum workflows:

1.  **QuafuCloud MCP Schema Completeness:** While the general tools are
    known, the exact inputSchema and outputSchema for complex
    multi-parameter tasks are not fully public. This complicates the
    zero-shot integration of these tools into generic agent
    frameworks.^17^

2.  **SimpleTES Scoring Weights:** The specific weighting constants
    \$w_i\$ used for different architectures (IBM Q20 vs Google Willow)
    are not specified. These weights are likely tuned through extensive
    hardware characterization which is proprietary.^7^

3.  **QAgent Prompt Reconstruction:** While the general role of each
    agent is described, the specific few-shot examples and system
    prompts required to reproduce the 71.6% accuracy improvement are not
    fully disclosed in the arXiv paper.^6^

4.  **EM Stacking Formulas:** There is no standardized, published
    formula that accounts for the non-linear interaction between
    different error mitigation techniques (e.g., how DD pulse timing
    affects ZNE noise scaling). This forces agents to rely on black-box
    optimization rather than analytical models.^24^

## 9. Conclusion

The integration of autonomous agents with quantum computing has
transitioned from speculative research into a phase of practical,
programmatic implementation. Systems like QUASAR and QAgent demonstrate
that LLMs can be effectively grounded in quantum-specific knowledge
through hierarchical rewards and tool augmentation. Meanwhile,
architectures like QSteed and paradigms like SimpleTES prove that
agentic search can significantly reduce the gate overhead that currently
limits the utility of NISQ devices. As programmatic cloud access through
protocols like MCP becomes the norm, the role of the agent will expand
from a simple \"assistant\" to a \"hybrid control hub,\" capable of
managing the entire lifecycle of quantum discovery---from the molecular
integrals of a drug candidate to the final, error-mitigated energy
surfaces.

#### 引用的著作

1.  Quasar: Quantum Assembly Code Generation Using Tool-Augmented LLMs
    via Agentic RL, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/html/2510.00967v1]{.underline}](https://arxiv.org/html/2510.00967v1)

2.  QUASAR: QUANTUM ASSEMBLY CODE GENERATION USING TOOL-AUGMENTED LLMS
    VIA AGENTIC RL - OpenReview, 访问时间为 四月 25, 2026，
    [[https://openreview.net/pdf?id=fKKKtEW71h]{.underline}](https://openreview.net/pdf?id=fKKKtEW71h)

3.  Benyucong/rl_quantum_4b - Hugging Face, 访问时间为 四月 25, 2026，
    [[https://huggingface.co/Benyucong/rl_quantum_4b]{.underline}](https://huggingface.co/Benyucong/rl_quantum_4b)

4.  (PDF) QUASAR: Quantum Assembly Code Generation Using Tool-Augmented
    LLMs via Agentic RL - ResearchGate, 访问时间为 四月 25, 2026，
    [[https://www.researchgate.net/publication/396095117_QUASAR_Quantum_Assembly_Code_Generation_Using_Tool-Augmented_LLMs_via_Agentic_RL]{.underline}](https://www.researchgate.net/publication/396095117_QUASAR_Quantum_Assembly_Code_Generation_Using_Tool-Augmented_LLMs_via_Agentic_RL)

5.  \[2508.20134\] QAgent: An LLM-based Multi-Agent System for
    Autonomous OpenQASM programming - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/abs/2508.20134]{.underline}](https://arxiv.org/abs/2508.20134)

6.  QAgent: An LLM-based Multi-Agent System for Autonomous \... - arXiv,
    访问时间为 四月 25, 2026，
    [[https://arxiv.org/pdf/2508.20134]{.underline}](https://arxiv.org/pdf/2508.20134)

7.  Will - Wizard Intelligence Learning Lab, 访问时间为 四月 25, 2026，
    [[https://www.wizardquant.com/will/simpletes]{.underline}](https://www.wizardquant.com/will/simpletes)

8.  An Accurate and Efficient Analytic Model of Fidelity Under
    Depolarizing Noise Oriented to Large Scale Quantum System Design -
    arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/html/2503.06693v2]{.underline}](https://arxiv.org/html/2503.06693v2)

9.  On the use of calibration data in error-aware compilation techniques
    for NISQ devices - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/html/2407.21462v1]{.underline}](https://arxiv.org/html/2407.21462v1)

10. A Resource-Virtualized and Hardware-Aware Quantum Compilation
    Framework for Real Quantum Computing Processors - arXiv, 访问时间为
    四月 25, 2026，
    [[https://arxiv.org/html/2501.06993v2]{.underline}](https://arxiv.org/html/2501.06993v2)

11. \[2501.06993\] QSteed: Quantum Software of Compilation for
    Supporting Real Quantum Device - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/abs/2501.06993]{.underline}](https://arxiv.org/abs/2501.06993)

12. PyQuafu is designed for users to construct, compile, and execute
    quantum circuits on quantum devices on Quafu using Python. · GitHub,
    访问时间为 四月 25, 2026，
    [[https://github.com/ScQ-Cloud/pyquafu]{.underline}](https://github.com/ScQ-Cloud/pyquafu)

13. Welcome to PyQuafu\'s documentation! --- PyQuafu-Docs 0.4.0 \...,
    访问时间为 四月 25, 2026，
    [[https://scq-cloud.github.io/]{.underline}](https://scq-cloud.github.io/)

14. User guide - PyQuafu-Docs, 访问时间为 四月 25, 2026，
    [[https://scq-cloud.github.io/0.2.x/index.html]{.underline}](https://scq-cloud.github.io/0.2.x/index.html)

15. (PDF) A Resource-Virtualized and Hardware-Aware Quantum Compilation
    Framework for Real Quantum Computing Processors - ResearchGate,
    访问时间为 四月 25, 2026，
    [[https://www.researchgate.net/publication/396526878_A_Resource-Virtualized_and_Hardware-Aware_Quantum_Compilation_Framework_for_Real_Quantum_Computing_Processors]{.underline}](https://www.researchgate.net/publication/396526878_A_Resource-Virtualized_and_Hardware-Aware_Quantum_Compilation_Framework_for_Real_Quantum_Computing_Processors)

16. Decoding 2025: 10 Key Insights from the Alibaba Cloud Blog
    Community, 访问时间为 四月 25, 2026，
    [[https://www.alibabacloud.com/blog/decoding-2025-10-key-insights-from-the-alibaba-cloud-blog-community_602773]{.underline}](https://www.alibabacloud.com/blog/decoding-2025-10-key-insights-from-the-alibaba-cloud-blog-community_602773)

17. Alibaba Cloud\'s MCP Servers: An AI Engineer\'s Deep Dive - Skywork,
    访问时间为 四月 25, 2026，
    [[https://skywork.ai/skypage/en/alibaba-cloud-mcp-servers-ai-engineer/1980543892510253056]{.underline}](https://skywork.ai/skypage/en/alibaba-cloud-mcp-servers-ai-engineer/1980543892510253056)

18. MCP for Observability 2.0 - Six Practices for Making Good Use of
    MCP - Alibaba Cloud, 访问时间为 四月 25, 2026，
    [[https://www.alibabacloud.com/blog/mcp-for-observability-2-0\-\--six-practices-for-making-good-use-of-mcp_602423]{.underline}](https://www.alibabacloud.com/blog/mcp-for-observability-2-0---six-practices-for-making-good-use-of-mcp_602423)

19. OpenAPI Explorer:Use aliyun mcp-proxy for OpenAPI MCP servers -
    Alibaba Cloud, 访问时间为 四月 25, 2026，
    [[https://www.alibabacloud.com/help/en/openapi/use-aliyun-mcp-proxy-agent-openapi-mcp-server]{.underline}](https://www.alibabacloud.com/help/en/openapi/use-aliyun-mcp-proxy-agent-openapi-mcp-server)

20. Secure MCP Consumer Access with API Key Authentication - AI
    Gateway - Alibaba Cloud, 访问时间为 四月 25, 2026，
    [[https://www.alibabacloud.com/help/en/api-gateway/ai-gateway/user-guide/consumer-certification]{.underline}](https://www.alibabacloud.com/help/en/api-gateway/ai-gateway/user-guide/consumer-certification)

21. QSteed: Quantum Software of Compilation for Supporting Real Quantum
    Device - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/html/2501.06993v1]{.underline}](https://arxiv.org/html/2501.06993v1)

22. Quantum circuit optimization \| IBM Quantum Learning, 访问时间为
    四月 25, 2026，
    [[https://quantum.cloud.ibm.com/learning/en/courses/utility-scale-quantum-computing/quantum-circuit-optimization]{.underline}](https://quantum.cloud.ibm.com/learning/en/courses/utility-scale-quantum-computing/quantum-circuit-optimization)

23. VQE - Qiskit Algorithms 0.4.0 - GitHub Pages, 访问时间为 四月 25,
    2026，
    [[https://qiskit-community.github.io/qiskit-algorithms/stubs/qiskit_algorithms.VQE.html]{.underline}](https://qiskit-community.github.io/qiskit-algorithms/stubs/qiskit_algorithms.VQE.html)

24. Error mitigation and suppression techniques \| IBM Quantum
    Documentation, 访问时间为 四月 25, 2026，
    [[https://qiskit.qotlabs.org/docs/guides/error-mitigation-and-suppression-techniques]{.underline}](https://qiskit.qotlabs.org/docs/guides/error-mitigation-and-suppression-techniques)

25. transpiler (v1.0) \| IBM Quantum Documentation, 访问时间为 四月 25,
    2026，
    [[https://quantum.cloud.ibm.com/docs/api/qiskit/1.0/transpiler]{.underline}](https://quantum.cloud.ibm.com/docs/api/qiskit/1.0/transpiler)

26. Transpilation optimizations with SABRE \| IBM Quantum Documentation,
    访问时间为 四月 25, 2026，
    [[https://quantum.cloud.ibm.com/docs/tutorials/transpilation-optimizations-with-sabre]{.underline}](https://quantum.cloud.ibm.com/docs/tutorials/transpilation-optimizations-with-sabre)

27. transpiler (latest version) \| IBM Quantum Documentation, 访问时间为
    四月 25, 2026，
    [[https://quantum.cloud.ibm.com/docs/api/qiskit/transpiler]{.underline}](https://quantum.cloud.ibm.com/docs/api/qiskit/transpiler)

28. Variational Quantum Eigensolver for Molecular Ground State Energy
    Computation: A Comprehensive Benchmarking Study of Ansatz Sele -
    K-Dense AI, 访问时间为 四月 25, 2026，
    [[https://www.k-dense.ai/examples/session_20251212_162938_43788a48ae9a/writing_outputs/final/vqe_benchmarking_paper.pdf]{.underline}](https://www.k-dense.ai/examples/session_20251212_162938_43788a48ae9a/writing_outputs/final/vqe_benchmarking_paper.pdf)

29. Accelerating Parameter Initialization in Quantum Chemical
    Simulations via LSTM-FC-VQE - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/html/2505.10842v1]{.underline}](https://arxiv.org/html/2505.10842v1)

30. Benchmarking the Impact of Active Space Selection on the VQE
    Pipeline for Quantum Drug Discovery - arXiv, 访问时间为 四月 25,
    2026，
    [[https://arxiv.org/html/2512.18203v1]{.underline}](https://arxiv.org/html/2512.18203v1)

31. VQE with gradients, active spaces, and gate fusion --- NVIDIA CUDA-Q
    documentation, 访问时间为 四月 25, 2026，
    [[https://nvidia.github.io/cuda-quantum/latest/applications/python/vqe_advanced.html]{.underline}](https://nvidia.github.io/cuda-quantum/latest/applications/python/vqe_advanced.html)

32. Generating integrals - HANDE QMC documentation - Read the Docs,
    访问时间为 四月 25, 2026，
    [[https://hande.readthedocs.io/en/latest/manual/integrals.html]{.underline}](https://hande.readthedocs.io/en/latest/manual/integrals.html)

33. PySCF: How to do CCSD calculations from an FCIDUMP file in HDF5
    format?, 访问时间为 四月 25, 2026，
    [[https://mattermodeling.stackexchange.com/questions/10349/pyscf-how-to-do-ccsd-calculations-from-an-fcidump-file-in-hdf5-format]{.underline}](https://mattermodeling.stackexchange.com/questions/10349/pyscf-how-to-do-ccsd-calculations-from-an-fcidump-file-in-hdf5-format)

34. The Localized Active Space Method with Unitary Selective Coupled
    Cluster - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/html/2404.12927v1]{.underline}](https://arxiv.org/html/2404.12927v1)

35. The Localized Active Space Method with Unitary Selective Coupled
    Cluster \| Journal of Chemical Theory and Computation - ACS
    Publications, 访问时间为 四月 25, 2026，
    [[https://pubs.acs.org/doi/10.1021/acs.jctc.4c00528]{.underline}](https://pubs.acs.org/doi/10.1021/acs.jctc.4c00528)

36. Is there a standard file format for storing one and two electron
    integrals?, 访问时间为 四月 25, 2026，
    [[https://mattermodeling.stackexchange.com/questions/6863/is-there-a-standard-file-format-for-storing-one-and-two-electron-integrals]{.underline}](https://mattermodeling.stackexchange.com/questions/6863/is-there-a-standard-file-format-for-storing-one-and-two-electron-integrals)

37. Mitiq: A software package for error mitigation on noisy quantum
    computers - ResearchGate, 访问时间为 四月 25, 2026，
    [[https://www.researchgate.net/publication/362642943_Mitiq_A_software_package_for_error_mitigation_on_noisy_quantum_computers]{.underline}](https://www.researchgate.net/publication/362642943_Mitiq_A_software_package_for_error_mitigation_on_noisy_quantum_computers)

38. amazon-braket-examples/examples/error_mitigation/on_mitiq/0_Getting_started_with_mitiq_on_Braket.ipynb
    at main - GitHub, 访问时间为 四月 25, 2026，
    [[https://github.com/amazon-braket/amazon-braket-examples/blob/main/examples/error_mitigation/on_mitiq/0_Getting_started_with_mitiq_on_Braket.ipynb]{.underline}](https://github.com/amazon-braket/amazon-braket-examples/blob/main/examples/error_mitigation/on_mitiq/0_Getting_started_with_mitiq_on_Braket.ipynb)

39. arXiv:2009.04417v3 \[quant-ph\] 12 Aug 2021, 访问时间为 四月 25,
    2026，
    [[https://arxiv.org/pdf/2009.04417]{.underline}](https://arxiv.org/pdf/2009.04417)

40. Mitiq paper codeblocks --- Mitiq 1.0.0 documentation, 访问时间为
    四月 25, 2026，
    [[https://mitiq.readthedocs.io/en/stable/examples/mitiq-paper/mitiq-paper-codeblocks.html]{.underline}](https://mitiq.readthedocs.io/en/stable/examples/mitiq-paper/mitiq-paper-codeblocks.html)

41. Breaking into error mitigation with Mitiq\'s calibration module,
    访问时间为 四月 25, 2026，
    [[https://mitiq.readthedocs.io/en/stable/examples/calibration-tutorial.html]{.underline}](https://mitiq.readthedocs.io/en/stable/examples/calibration-tutorial.html)

42. Towards Fault-Tolerant Quantum Computing: Advanced Techniques for
    Error Reduction, Mitigation and their Applications - Universität
    Freiburg, 访问时间为 四月 25, 2026，
    [[https://freidok.uni-freiburg.de/files/281896/4kPyDbkz-kDCt5CO/2026_Dissertation_Koenig.pdf]{.underline}](https://freidok.uni-freiburg.de/files/281896/4kPyDbkz-kDCt5CO/2026_Dissertation_Koenig.pdf)

43. Category-Based Error Budgeting for Heterogeneous Quantum
    Processors\[v1\] \| Preprints.org, 访问时间为 四月 25, 2026，
    [[https://www.preprints.org/manuscript/202602.1979]{.underline}](https://www.preprints.org/manuscript/202602.1979)

44. Mitiq is an open source toolkit for implementing error mitigation
    techniques on most current intermediate-scale quantum computers. -
    GitHub, 访问时间为 四月 25, 2026，
    [[https://github.com/unitaryfoundation/mitiq]{.underline}](https://github.com/unitaryfoundation/mitiq)

45. Compare transpiler settings \| IBM Quantum Documentation, 访问时间为
    四月 25, 2026，
    [[https://quantum.cloud.ibm.com/docs/en/guides/circuit-transpilation-settings]{.underline}](https://quantum.cloud.ibm.com/docs/en/guides/circuit-transpilation-settings)

46. (PDF) QSteed: Quantum Software of Compilation for Supporting Real
    Quantum Device, 访问时间为 四月 25, 2026，
    [[https://www.researchgate.net/publication/387976100_QSteed_Quantum_Software_of_Compilation_for_Supporting_Real_Quantum_Device]{.underline}](https://www.researchgate.net/publication/387976100_QSteed_Quantum_Software_of_Compilation_for_Supporting_Real_Quantum_Device)

47. how to connect to mcp using the qwen api - Alibaba Cloud Model
    Studio, 访问时间为 四月 25, 2026，
    [[https://www.alibabacloud.com/help/en/model-studio/mcp]{.underline}](https://www.alibabacloud.com/help/en/model-studio/mcp)
