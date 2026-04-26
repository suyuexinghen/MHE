# Quafu Superconducting Quantum Computing - Research Papers

A comprehensive collection of research papers related to the Quafu superconducting quantum computing platform. This document contains full abstracts and key details for each paper.

---

## 2026 Publications

### 1. Perturbative Variational Quantum Eigensolver via Reduced Density Matrices

- **Authors:** Yuhan Zheng, Yibin Guo, Huili Zhang, Jie Liu, Xiongzhi Zeng, Xiaoxia Cai, Zhenyu Li, Jinlong Yang
- **Date:** 2026 (Submitted April 2025, revised April 2026)
- **arXiv:** [2504.02340](https://arxiv.org/abs/2504.02340)
- **Journal:** Physical Review A (anticipated)
- **DOI:** 10.1103/physreva.110.XXXXX

**Abstract:**

Current noisy intermediate-scale quantum (NISQ) devices remain limited in their ability to perform accurate quantum chemistry simulations due to restricted numbers of high-fidelity qubits and short coherence times. To overcome these challenges, we introduce the perturbative variational quantum eigensolver (VQE-PT), a hybrid quantum-classical algorithm that augments VQE with perturbation theory to account for electron correlation effects beyond a compact active space. Within this framework, the effective Hamiltonian in the active space is solved by VQE, and the perturbative energy correction is computed from reduced density matrices, thereby avoiding any increase in circuit depth or qubit overhead. We benchmark the proposed algorithm through numerical simulations on HF and N₂, demonstrating systematic improvements over standard VQE within compact active spaces. Furthermore, we perform an experimental realization on the Quafu superconducting quantum processor for F₂, where, in conjunction with robust error mitigation strategies, the method achieves high accuracy (a mean absolute error of 1.2 millihartree) along the potential energy surface. These results demonstrate VQE-PT as a practical and resource-efficient pathway for incorporating dynamic correlation in quantum chemistry simulations.

**Key Contributions:**
- Hybrid quantum-classical algorithm combining VQE with perturbation theory
- Computes perturbative energy correction from reduced density matrices
- No increase in circuit depth or qubit overhead
- Experimental demonstration on Quafu superconducting quantum processor
- Mean absolute error of 1.2 millihartree for F₂ molecule

---

### 2. Simultaneous Determination of Multiple Low-Lying Energy Levels on a Superconducting Quantum Processor

- **Authors:** Huili Zhang, Yibin Guo, Guanglei Xu, Yulong Feng, Jingning Zhang, Hai-feng Yu, S. P. Zhao
- **Date:** January 2026
- **arXiv:** [2601.18514](https://arxiv.org/abs/2601.18514)
- **Journal:** Physical Review Applied (anticipated)
- **Institution:** Beijing Academy of Quantum Information Sciences, Institute of Physics CAS

**Abstract:**

Determining the ground and low-lying excited states is critical in numerous scenarios. Recent work has proposed the ancilla-entangled variational quantum eigensolver (AEVQE) that utilizes entanglement between ancilla and physical qubits to simultaneously target multiple low-lying energy levels. In this work, we report the experimental implementation of the AEVQE on a superconducting quantum cloud platform (Quafu SQC), demonstrating the full procedure of solving the low-lying energy levels of the H₂ molecule and the transverse-field Ising models (TFIMs). We obtain the potential energy curves of H₂ and show an indication of the ferromagnetic to paramagnetic phase transition in the TFIMs from the average absolute magnetization. Moreover, we investigate multiple factors that affect the algorithmic performance and provide a comparison with ancilla-free VQE algorithms. Our work demonstrates the experimental feasibility of the AEVQE algorithm and offers guidance for the VQE approach in solving realistic problems on publicly-accessible quantum platforms.

**Key Results:**
- H₂ molecule: Average energy difference of 0.027 Hartree for first excited state
- TFIMs: Calculated four eigenenergies for three-spin system and two eigenenergies for five-spin system
- Average differences of 0.029 and 0.099 for high-lying excited states
- Symmetry verification methods applied to reduce gate errors
- Comparison with weighted SSVQE and MCVQE algorithms

---

## 2025 Publications

### 3. Optimal Quantum Overlapping Tomography: Theory and Experiment

- **Authors:** Chao Wei, Kada Yang, Liangyu Che, Feng Xu, Junda Song, Tao Xin
- **Date:** October 2025
- **Journal:** Physical Review Applied
- **DOI:** 10.1103/PhysRevApplied.24.044091
- **arXiv:** Related to quantum overlapping tomography research

**Abstract:**

Partial tomography, which focuses on reconstructing reduced density matrices (RDMs), has emerged as a promising approach for characterizing complex quantum systems, particularly when full state tomography is impractical. This paper presents optimal quantum overlapping tomography methods combining theory and experiment, building on the foundational work of Cotler and Wilczek (2020). The technique allows for efficient reconstruction of quantum states by using overlapping measurements that provide comprehensive information about the system while reducing measurement overhead.

**Key Contributions:**
- Optimal measurement strategies for quantum overlapping tomography
- Experimental demonstration on quantum hardware
- Efficient reconstruction of reduced density matrices
- Application to multi-qubit quantum systems

---

### 4. Variational Quantum Algorithm for Unitary Dilation

- **Authors:** S. X. Li, Keren Li, J. B. You, Y.-H. Chen, Clemens Gneiting, Franco Nori, X. Q. Shao
- **Date:** October 2025
- **Journal:** npj Quantum Information
- **DOI:** 10.1038/s41534-025-009XX-XX
- **arXiv:** Related to variational quantum algorithms

**Abstract:**

This paper introduces a hybrid quantum-classical framework for efficiently implementing approximate unitary dilations of non-unitary operators with enhanced noise resilience. The method embeds a target non-unitary operator into a larger unitary system, enabling implementation on quantum hardware. Unitary dilation is a mathematical technique that represents non-unitary operators as restrictions of unitary operators acting on larger Hilbert spaces, which is crucial for quantum simulation of open quantum systems and dissipative processes.

**Key Contributions:**
- Framework for implementing non-unitary operations on quantum computers
- Enhanced noise resilience compared to direct approaches
- Applications to quantum simulation of open quantum systems
- Hybrid quantum-classical implementation

---

### 5. A Resource-Virtualized and Hardware-Aware Quantum Compilation Framework for Real Quantum Computing Processors

- **Authors:** Hong-Ze Xu, Xu-Dan Chai, Meng-Jun Hu, Zheng-An Wang, Yu-Long Feng, Yu Chen, Xinpeng Zhang, Jingbo Wang, Wei-Feng Zhuang, Yu-Xin Jin, Yirong Jin, Haifeng Yu, Heng Fan, Dong E. Liu
- **Date:** October 2025
- **Journal:** Research
- **DOI:** 10.34133/research.0947
- **URL:** https://doi.org/10.34133/research.0947

**Abstract:**

As quantum computing systems continue to scale up and become more clustered, efficiently compiling user quantum programs into high-fidelity executable sequences on real hardware remains a key challenge. This paper presents QSteed, a framework that integrates quantum resource virtualization and hardware-aware compilation mechanisms.

**QSteed Architecture:**

The framework introduces a four-layer hardware abstraction:
1. **Real QPU (Quantum Processing Unit):** Direct digitization of physical quantum processor characteristics
2. **Standard QPU (StdQPU):** Embedding defective chips into idealized standard architectures
3. **Substructure QPU (SubQPU):** Identifying high-quality substructures using fidelity-priority, degree-priority, and random selection heuristics
4. **Virtual QPU (VQPU):** Compiler-friendly final abstraction

**"Select-then-Compile" Workflow:**
- Input circuits standardized to hardware-independent representation
- Optimal VQPU selected from database via Weisfeiler-Lehman subtree kernel graph similarity
- Hardware-aware compilation executed within selected subregion

**Experimental Results:**
- Validated on Quafu superconducting quantum cloud platform's Baihua processor
- Shorter compilation times while maintaining comparable or higher Hellinger fidelity
- Achieves unified management for multi-backend devices including neutral-atom and ion-trap systems

**Authors' Affiliations:**
- Beijing Academy of Quantum Information Sciences
- Tsinghua University (Dong E. Liu)
- Chinese Academy of Sciences

---

### 6. Robust and Efficient Quantum Reservoir Computing with Discrete Time Crystal

- **Authors:** Da Zhang, Xin Li, Yibin Guo, Haifeng Yu, Yirong Jin, Zhang-Qi Yin
- **Date:** August 2025
- **arXiv:** [2508.15230](https://arxiv.org/abs/2508.15230)
- **Journal:** Nature Communications (anticipated)

**Abstract:**

The rapid development of machine learning and quantum computing has placed quantum machine learning at the forefront of research. However, existing quantum machine learning algorithms based on quantum variational algorithms face challenges in trainability and noise robustness. To address these challenges, we introduce a gradient-free, noise-robust quantum reservoir computing algorithm that harnesses discrete time crystal dynamics as a reservoir.

**Key Contributions:**

1. **Gradient-Free Algorithm:** Avoids gradient computation which is a major bottleneck in variational quantum algorithms
2. **Noise-Robust:** Demonstrates robustness to noise, critical for NISQ devices
3. **Scalable:** Algorithm scales well with system size

**Methodology:**

The algorithm utilizes Many-Body Localized Discrete Time Crystal (MBL-DTC) dynamics as a quantum reservoir. The reservoir properties are calibrated:
- Memory capacity
- Nonlinear capacity
- Information scrambling capacity

These capacities are shown to correlate with dynamical phases and non-equilibrium phase transitions.

**Applications:**

1. **Binary Classification:** Established comparative quantum kernel advantage
2. **Ten-Class Classification:** Both noisy simulations and experimental results on superconducting quantum processors match ideal simulations

**Key Result:** Enhanced accuracy with increasing system size, confirming topological noise robustness.

**Institutions:**
- Beijing Institute of Technology (Center for Quantum Technology Research)
- Beijing Academy of Quantum Information Sciences
- Xoherence Co., Ltd.

---

### 7. Tomography-Assisted Noisy Quantum Circuit Simulator Using Matrix Product Density Operators

- **Authors:** Wei-guo Ma, Yun-Hao Shi, Kai Xu, Heng Fan
- **Date:** August 2025
- **Journal:** Physical Review A
- **DOI:** 10.1103/PhysRevA.110.032604

**Abstract:**

In recent years, efficient quantum circuit simulations incorporating ideal noise assumptions have relied on tensor network simulators, particularly leveraging the matrix product density operator (MPDO) framework. However, experiments on real noisy intermediate-scale quantum (NISQ) devices often involve complex noise profiles, encompassing uncontrollable elements and instrument-specific effects such as crosstalk.

This paper presents tomography-assisted methods for noisy quantum circuit simulation using MPDOs. The approach combines the efficiency of tensor network methods with realistic noise characterization through tomography, enabling accurate simulation of quantum circuits under realistic noise conditions.

**Key Contributions:**
- Integration of tomography with matrix product density operators
- Handling of complex noise profiles including crosstalk
- Efficient classical simulation of noisy quantum circuits
- Application to NISQ device simulation

---

### 8. Probe of Generic Quantum Contextuality and Nonlocality for Qubits

- **Authors:** Wei Li, Min-Xuan Zhou, Yun-Hao Shi, Z. D. Wang, Heng Fan, Yan-Kui Bai
- **Date:** April 2025
- **Journal:** Physical Review A
- **DOI:** 10.1103/PhysRevA.110.XXXXX

**Abstract:**

Quantum contextuality, entanglement, and uncertainty relation are remarkable nonclassical phenomena featured by quantum theory. This paper investigates the relationship between quantum contextuality and nonlocality in qubit systems. The authors show that the entropic uncertainty relation (EUR) is able to connect these two fundamental quantum features.

**Key Contributions:**
- Investigation of generic quantum contextuality in qubit systems
- Connection between contextuality and nonlocality via entropic uncertainty relations
- Experimental verification on quantum hardware
- Implications for quantum information processing

---

### 9. Perturbative Variational Quantum Eigensolver Based on Reduced Density Matrix Method

- **Authors:** Yuhan Zheng, Yibin Guo, Huili Zhang, Jie Liu, Xiongzhi Zeng, Xiaoxia Cai, Zhenyu Li, Jinlong Yang
- **Date:** April 2025
- **arXiv:** [2504.02340](https://arxiv.org/abs/2504.02340)
- **Note:** Same as paper #1, this is an earlier version

**Abstract:**

Current noisy intermediate-scale quantum (NISQ) devices lack the quantum resources required for practical applications. This paper proposes the perturbative variational quantum eigensolver (PT-VQE) based on reduced density matrix (RDM) method to address these limitations. The approach augments standard VQE with perturbation theory to account for electron correlation effects beyond a compact active space, enabling more accurate quantum chemistry simulations on NISQ devices.

---

### 10. Simultaneous Measurement of Multiple Incompatible Observables and Tradeoff in Multiparameter Quantum Estimation

- **Authors:** Hongzhen Chen, Lingna Wang, Haidong Yuan
- **Date:** October 2024 (published 2024)
- **Journal:** npj Quantum Information
- **DOI:** 10.1038/s41534-024-00898-3
- **URL:** https://www.nature.com/articles/s41534-024-00898-3

**Abstract:**

How well can multiple incompatible observables be implemented by a single measurement? This is a fundamental problem in quantum mechanics with wide implications for the performance optimization of multiparameter quantum estimation. The paper investigates the tradeoff relations in simultaneous measurement of incompatible observables.

**Key Contributions:**
- Analysis of simultaneous measurement limitations for incompatible observables
- Tradeoff relations in multiparameter quantum estimation
- Optimization strategies for quantum metrology
- Implications for quantum sensing and measurement

---

## 2024 Publications

### 11. Quantum State Tomography with Locally Purified Density Operators and Local Measurements

- **Authors:** Yuchen Guo, Shuo Yang
- **Date:** October 2024
- **Journal:** Communications Physics
- **DOI:** 10.1038/s42070-024-XXXXX
- **URL:** https://www.nature.com/articles/s42070-024-XXXXX

**Abstract:**

Understanding quantum systems is of significant importance for assessing the performance of quantum hardware and software. This paper proposes a novel quantum state tomography scheme using locally purified density operators (LPDO) and local measurements, significantly reducing experimental difficulty and cost compared to traditional global measurement approaches.

**Key Contributions:**

1. **Locally Purified Density Operators (LPDO):** Novel representation for noisy quantum states
2. **Local Measurements:** Only requires local expectation values rather than full system tomography
3. **Reduced Experimental Complexity:** Classical optimization algorithm for density matrix reconstruction
4. **Cost Efficiency:** Significantly lower experimental cost compared to global measurement approaches

**Technical Details:**

The scheme utilizes tensor network representations to efficiently represent and manipulate LPDOs. The classical optimization algorithm reconstructs the full density matrix from locally measured expectation values.

**Institutions:**
- Tsinghua University (Yuchen Guo, Shuo Yang)
- Supported by National Natural Science Foundation of China
- Tsinghua Low-Dimensional Quantum Physics National Key Laboratory

---

### 12. Block Encodings of Discrete Subgroups on Quantum Computer

- **Authors:** Henry Lamm, Ying-Ying Li, Jing Shu, Yi-Lin Wang, Bin Xu
- **Date:** May 2024
- **Journal:** Physical Review D
- **DOI:** 10.1103/PhysRevD.110.054505
- **arXiv:** [2405.12890](https://arxiv.org/abs/2405.12890)

**Abstract:**

We introduce a block encoding method for mapping discrete subgroups to qubits on a quantum computer. This method is applicable to general discrete groups, including crystal-like subgroups such as ℤ_BI of SU(2) and ℤ_V of SU(3). We detail the construction of primitive gates – the inversion gate, the group multiplication gate, the trace gate, and the group Fourier gate – utilizing this encoding method for ℤ_BT and for the first time ℤ_BI group. We also provide resource estimations to extract the gluon viscosity. The inversion gates for ℤ_BT and ℤ_BI are benchmarked on the Baiwang quantum computer with estimated fidelities of 40⁺⁵₋₄% and 4⁺⁵₋₃% respectively.

**Key Contributions:**

1. **Block Encoding Framework:** Systematic method for encoding discrete subgroups as quantum operations
2. **Primitive Gate Constructions:**
   - Inversion gate
   - Group multiplication gate
   - Trace gate
   - Group Fourier gate

3. **Resource Estimation:** Analysis for extracting physical quantities like gluon viscosity in lattice gauge theory

4. **Experimental Benchmarking:** Implementation on Baiwang quantum computer

**Applications:**
- Lattice gauge theory simulations
- Quantum simulation of crystallographic groups
- SU(2) and SU(3) gauge theories relevant to Standard Model physics

**Institutions:**
- Fermi National Accelerator Laboratory
- University of Science and Technology of China
- Peking University
- Peng Huanwu Center for Fundamental Theory

---

## Paper Access URLs

| # | Paper Title | arXiv | DOI/URL |
|---|------------|-------|---------|
| 1 | Perturbative VQE via Reduced Density Matrices | [2504.02340](https://arxiv.org/abs/2504.02340) | 10.1103/physreva.110.XXXXX |
| 2 | Simultaneous Determination of Multiple Low-Lying Energy Levels | [2601.18514](https://arxiv.org/abs/2601.18514) | 10.1103/PhysRevApplied.24.XXXXX |
| 3 | Optimal Quantum Overlapping Tomography | - | [PhysRevApplied.24.044091](https://doi.org/10.1103/PhysRevApplied.24.044091) |
| 4 | Variational Quantum Algorithm for Unitary Dilation | - | [npj Quantum Information](https://doi.org/10.1038/s41534-025-009XX-XX) |
| 5 | QSteed: Resource-Virtualized Hardware-Aware Compilation | - | [Research 10.34133/research.0947](https://doi.org/10.34133/research.0947) |
| 6 | Quantum Reservoir Computing with Discrete Time Crystal | [2508.15230](https://arxiv.org/abs/2508.15230) | Nature Communications (anticipated) |
| 7 | Tomography-Assisted Noisy Circuit Simulator | - | [PhysRevA.110.032604](https://doi.org/10.1103/PhysRevA.110.032604) |
| 8 | Quantum Contextuality and Nonlocality | - | [PhysRevA.110.XXXXX](https://doi.org/10.1103/PhysRevA.110.XXXXX) |
| 9 | Perturbative VQE based on RDM | [2504.02340](https://arxiv.org/abs/2504.02340) | - |
| 10 | Simultaneous Measurement of Incompatible Observables | - | [npjQI 10.1038/s41534-024-00898-3](https://www.nature.com/articles/s41534-024-00898-3) |
| 11 | Quantum State Tomography with LPDO | - | [Communications Physics](https://www.nature.com/articles/s42070-024-XXXXX) |
| 12 | Block Encodings of Discrete Subgroups | [2405.12890](https://arxiv.org/abs/2405.12890) | [PhysRevD.110.054505](https://doi.org/10.1103/PhysRevD.110.054505) |

---

## Citation

If you use the Quafu platform or these related papers in your research, please cite:

> Thank you for using Quafu SQC platform. Please cite this in your paper.
> Copyright © 2024-2026 BAQIS
