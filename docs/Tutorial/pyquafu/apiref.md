# API Reference

> **Note:** This page is still under refinement, the contents you see may be incomplete at present.

## Quantum Circuit

### class quafu.QuantumCircuit(qnum, cnum=None, name='', *args, **kwargs)

Representation of quantum circuit.

**Parameters:**

- `qnum` (int)
- `cnum` (int | None)

**Methods:**

#### add_gate(gate)

Add quantum gate to circuit, with some checking.

**Parameters:**

- `gate` (QuantumGate)

#### barrier(qlist=None)

Add barrier for qubits in qlist.

**Parameters:**

- `qlist` (list[int]) – A list contain the qubit need add barrier. When qlist contain at least two qubit, the barrier will be added from minimum qubit to maximum qubit. For example: `barrier([0, 2])` create barrier for qubits 0, 1, 2. To create discrete barrier, using `barrier([0])`, `barrier([2])`.

**Return type:** None

#### cnot(ctrl, tar)

CNOT gate.

**Parameters:**

- `ctrl` (int) – control qubit
- `tar` (int) – target qubit

**Return type:** None

## Quantum Elements

> **Hint:** hello

### class quafu.elements.Instruction(pos, paras=[], *args, **kwargs)

Base class for ALL the possible instructions on Quafu superconducting quantum circuits.

**Parameters:**

- `pos` (List[int])
- `paras` (List[float | Parameter | ParameterExpression])

**Properties:**

#### pos

Qubit position(s) of the instruction on the circuit.

#### paras

Parameters of the instruction.

#### named_paras (abstract property)

dict-mapping for parameters

#### named_pos (abstract property)

dict-mapping for positions

**Methods:**

#### classmethod register(name=None)

Register a virtual subclass of an ABC.

Returns the subclass, to allow usage as a class decorator.

**Parameters:**

- `name` (str | None)

**Returns:** subclass

## Task and User

### class quafu.Task(user=None)

Class for submitting quantum computation task to the backend.

**Parameters:**

- `user` (User | None)

**Properties:**

#### shots

Numbers of single shot measurement.

**Type:** int

#### compile

Whether compile the circuit on the backend

**Type:** bool

#### tomo

Whether do tomography (Not support yet)

**Type:** bool

#### priority

priority level of the task

**Type:** int

#### submit_history

circuit submitted with this task

**Type:** dict

#### backend

quantum backend that execute the task

**Type:** dict

**Methods:**

#### config(backend='ScQ-P10', shots=1000, compile=True, tomo=False, priority=2)

Configure the task properties

**Parameters:**

- `backend` (str) – Select the experimental backend.
- `shots` (int) – Numbers of single shot measurement.
- `compile` (bool) – Whether compile the circuit on the backend
- `tomo` (bool) – Whether to do tomography (Not support yet)
- `priority` (int) – Task priority.

**Return type:** None

#### retrieve(taskid)

Retrieve the results of submited task by taskid.

**Parameters:**

- `taskid` (str) – The taskid of the task need to be retrieved.

**Return type:** ExecResult

#### send(qc, name='', group='', wait=False)

Run the circuit on experimental device.

**Parameters:**

- `qc` (QuantumCircuit)
- `name` (str) – Task name.
- `group` (str) – The task belong which group.
- `wait` (bool) – Whether wait until the execution return.

**Returns:** ExecResult object that contain the dict return from quantum device.

**Return type:** ExecResult

### class quafu.User(api_token=None, token_dir=None)

**Parameters:**

- `api_token` (str | None)
- `token_dir` (str | None)

**Methods:**

#### get_available_backends(print_info=True)

Get available backends

#### save_apitoken(apitoken=None)

Save api-token associate your Quafu account.

### class quafu.results.results.Result

Basis class for quantum results
