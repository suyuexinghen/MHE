# Quantum Computing × Agent Integration — Deep Research Prompt

## Background

We are studying how AI agents can be integrated with quantum computing to enable
automated quantum-classical hybrid workflows. Our focus is on the intersection of:

- **Agent-driven quantum circuit compilation**: using AI agents (LLM-based, RL-based,
  or evaluation-driven) to optimize quantum circuit transpilation, qubit routing,
  and backend-specific compilation
- **Programmatic quantum cloud platform access**: evaluating quantum cloud platforms
  from the perspective of automated, agent-orchestrated usage (not manual/interactive use)
- **Quantum chemistry with agent-in-the-loop**: classical DFT → quantum VQE hybrid
  workflows where an agent coordinates the iterative optimization
- **Error mitigation as a search problem**: treating NISQ error mitigation strategy
  selection as an agent-searchable space
- **Evaluation-driven discovery for quantum tasks**: applying scaling paradigms
  like SimpleTES C×L×K to quantum circuit optimization problems

A prior survey identified five integration paths (agent as hybrid control hub,
agent-driven compilation, quantum chemistry × agent, automated EM search,
quantum software stack evaluation). We now need deep, precise technical
information to ground our design in real system capabilities.

**Please prioritize**: API signatures and return schemas > published benchmark data >
architecture descriptions > speculative analysis. Cite sources. Flag inference.

---

## 1. Agent-Driven Quantum Circuit Compilation Systems

### QUASAR

Published as an agentic RL framework for quantum circuit compilation. Claims 99.31%
Pass@1 and 100% Pass@10 with 4-level hierarchical reward mechanism.

**Questions:**
- What is the RL state representation? (circuit graph embedding? gate sequence features?
  hardware topology encoding?) What is the action space?
- What are the 4 reward levels and their formulas? How are they weighted?
- How many simulator calls are needed to train to 99% Pass@1? Training hardware and time?
- Inference: once trained, what is compilation latency per circuit? Model size?
- Is the code public? If not, does the paper provide sufficient pseudocode to reimplement?

### QAgent (arXiv:2508.20134)

LLM-powered multi-agent system for automated OpenQASM programming. Claims 71.6%
accuracy improvement over static LLM baselines.

**Questions:**
- How do Planner, Coder (Dynamic-fewshot + Tool-augmented), and Reviewer agents communicate?
  Fixed DAG or dynamic? Message schema?
- What is in the RAG knowledge base? How is it indexed and retrieved?
- What are the tool-callable operations? (simulator, transpiler, syntax checker?)
  Tool call/response format?
- Can you reconstruct the system prompts for each agent? What few-shot examples are used?
- On what types of circuits does it fail? Most common error categories?
- Public code repo? If not, minimum set of prompts needed to reproduce?

### SimpleTES Evaluation-Driven Paradigm

Achieved 21.7% improvement over SABRE, 14.9% over LightSABRE on superconducting qubit routing.
IBM Q20 SWAP overhead reduced 24.5% (60,189→45,441).

**Questions:**
- What is the Generator's internal mechanism? LLM-based (which model, what prompt template?)
  or algorithmic (randomized SABRE with varied seeds)? How is candidate diversity ensured?
- Evaluator scoring function: how are SWAP count, circuit depth, and estimated fidelity combined?
  Weights? Single formula or learned?
- Policy: how does it select from K finalists? Pareto frontier dimensions?
  Exploration-exploitation balance mechanism?
- Actual C, L, K values used in qubit routing experiments? How do they scale with qubit count?
- How does the same C×L×K framework adapt across superconducting, neutral-atom, and
  trapped-ion architectures? Retrained per architecture or zero-shot?
- Is evaluation harness code open-source?

---

## 2. Quantum Cloud Platform APIs — Automation-Ready Assessment

### Quafu Platform

This is the primary Chinese quantum cloud platform (launched 2023, 136-qubit chip).
It has a Python SDK (pyQuafu) and a newly released MCP service (QuafuCloud MCP,
Sept 2025, on Alibaba Cloud Bailian).

**pyQuafu SDK (GitHub: ScQ-Cloud/pyquafu):**
- Current version? Minimum Python? Dependencies?
- `QuantumCircuit` class: complete constructor signature and method list with signatures.
  Supported gate set. Parameterized gate API (radians or degrees?).
- Backend discovery: function to list available chips, return structure (fields per backend descriptor).
  Coupling map retrieval method and format.
- Job submission: exact function signature with all parameter names, types, defaults.
  Returned job object type, methods, and status enum.
- Result retrieval: exact dict structure of `counts` — key format with example.
  Statevector availability. Timing metadata. Error/exception class hierarchy.
- Calibration data API: function name, response JSON schema. Update frequency.
- Rate limits: daily quotas, circuit depth/shots constraints, concurrency limits.
  Error message format when quota exceeded.
- VQE/QAOA high-level APIs: if they exist, exact function signatures.

**QuafuCloud MCP:**
- Complete tool list with schemas (name, description, inputSchema, outputSchema).
- Feature coverage comparison: MCP vs pyQuafu SDK — what can each do that the other can't?
- Practical question for automated use: which channel (MCP or SDK) has lower latency,
  better reliability, and finer-grained control?
- Authentication: how does an external agent authenticate to the MCP service?

### Qiskit & Qiskit Aer

- `AerSimulator` noise model: how to construct a `NoiseModel` from T1/T2/gate_fidelity
  calibration data? Is there a standard mapping?
- Transpiler: for each `optimization_level` (0-3), exact pass list. Which individual
  passes are configurable with what parameters?
- `SabreLayout` parameters (`max_iterations`, `swap_trials`, `layout_trials`)
  and sensible ranges for 4-20 qubit circuits.
- Pre-execution fidelity estimation: built-in function or standard heuristic?
  Published correlation (r²) with actual hardware fidelity?
- Qiskit→OpenQASM→pyQuafu roundtrip: gate set incompatibilities? Fidelity cost
  of format conversion?

### Other Platforms (brief)

- **IBM Quantum**: Qiskit Runtime Sessions API — how does it optimize iterative
  VQE loops (session reuse, reduced submission overhead)? Primitives API
  (Sampler, Estimator) — return schemas and error bar semantics?
- **PennyLane**: Multi-backend abstraction — how cleanly can it switch between
  simulators and real hardware? Does it support Quafu as a backend?

---

## 3. Quantum Chemistry Programmatic Workflows

- **VQE pipeline**: What is the standard programmatic pipeline from fermionic Hamiltonian
  → Jordan-Wigner/Bravyi-Kitaev mapping → ansatz → optimization?
  Function calls in Qiskit Nature or PennyLane for each step.
- **Ansatz families**: For UCCSD, HEA, EfficientSU2 — parameter count formulas?
  Circuit depth and CNOT count as functions of qubit number?
- **Active space selection**: Algorithms and Python implementations (PySCF, Qiskit Nature)
  for reducing full molecular orbital spaces to NISQ-manageable 4-12 qubits.
- **Published VQE results**: For H₂, LiH, H₂O on real hardware — best reported
  energy errors, iterations, circuit depths? This establishes realistic baselines.
- **Fermionic Hamiltonian exchange format**: Standard file format (FCIDUMP? HDF5?)
  for passing molecular integrals between classical DFT and quantum VQE?

---

## 4. Error Mitigation as a Searchable Space

- **Mitiq API precision**: `execute_with_zne()` — all parameters, types, defaults.
  Available `Factory` types and their parameters. Recommended `scale_factors`
  ranges for superconducting hardware.
- **Measurement error mitigation in Qiskit**: Complete API for `CompleteMeasFitter`
  and `TensoredMeasFitter`. How does calibration circuit count scale with qubit count?
- **Dynamical decoupling**: Does DD require pulse-level access or can work at gate level?
  Which sequences (XY4, CPMG, KDD, Uhrig) are available in Qiskit's `PassManager`?
- **EM stacking**: For DD + ZNE + MEM used together — cumulative sampling overhead formula?
  Published cases where stacking caused worse results than single technique?
- **Automated EM selection**: Any existing framework, paper, or tool that automatically
  selects EM strategy per circuit+backend? Even a grid search script with published results?

---

## 5. Quantum Transpilation as Optimization Target

- **Search space sizing**: For an 8-qubit, depth-50 circuit on a grid topology —
  how many meaningfully different transpilation outcomes exist across routing
  algorithm × optimization level × initial layout? Order of magnitude.
- **Pre-execution fidelity estimation**: What heuristics estimate circuit fidelity
  from calibration data? Formula? Published correlation with actual execution?
- **QSteed vs Qiskit on Quafu**: Published comparison data? If not, what differences
  would be expected based on QSteed's VQPU selection approach?
- **Compilation benchmarks**: Standard benchmark suites (QASMBench, MQT Bench, Benchpress)?
  Which are most relevant for measuring compilation improvement?

---

## 6. Cross-System Comparative Analysis

For each agent-driven quantum system (QUASAR, QAgent, SimpleTES, QuantumMetaGPT,
PhysMaster), characterize:

| System | Task Decomposition | Evaluation Signal | Agent Coordination | Backend Coupling | Code or Circuit? |
|--------|-------------------|-------------------|-------------------|------------------|------------------|

Key comparative questions:
- Which systems use RL-native architectures vs LLM-orchestrated vs evaluation-driven?
- What are the tradeoffs: sample efficiency, generalization across backends,
  dependence on simulator quality?
- Which architectures generalize best across different quantum tasks (compilation,
  algorithm design, error mitigation) vs being task-specific?

---

## 7. Evaluation Metrics & Benchmarks

- What evaluation benchmarks exist for quantum-agent systems?
- For quantum circuit compilation specifically: what are the standard metrics
  (SWAP count, depth, gate count, estimated fidelity, execution success rate)?
- How do pre-execution estimates correlate with post-execution reality —
  published r² values across different backends?
- What benchmark suites exist (QASMBench, MQT Bench, BenchRL-QAS, Benchpress)?
  Which provide standardized comparison across compilation approaches?

---

## Output Format

1. **API Precision Docs**: Function signatures, return schemas, error types
2. **Benchmark Data**: Published numbers — latencies, costs, sizes, thresholds, correlations
3. **Architecture Patterns**: Data flow descriptions, component decomposition for key systems
4. **Code Examples**: Key API calls for pyQuafu, Qiskit Nature, Mitiq
5. **Gap Report**: What cannot be determined from public information alone

## Key Sources

- pyQuafu: https://github.com/ScQ-Cloud/pyquafu
- QSteed: arXiv:2501.06993 + Research 2025 + https://pypi.org/project/qsteed/
- Quafu docs: https://quarkstudio.readthedocs.io/
- QAgent: arXiv:2508.20134
- SimpleTES: wizardquant.com/will/simpletes (April 2026)
- Qiskit: https://docs.quantum.ibm.com/
- Mitiq: https://mitiq.readthedocs.io/
- Qiskit Nature: https://qiskit-community.github.io/qiskit-nature/
- PennyLane: https://docs.pennylane.ai/
- Benchpress, QASMBench, MQT Bench
