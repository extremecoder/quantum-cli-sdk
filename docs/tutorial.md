# Quantum Computing Tutorial

This tutorial will guide you through the basics of quantum computing using the Quantum CLI SDK.

## Prerequisites

- Quantum CLI SDK installed (see [Installation Guide](user_guide.md#installation))
- Basic understanding of command-line interfaces
- No prior quantum computing knowledge required

## Table of Contents

1. [What is Quantum Computing?](#what-is-quantum-computing)
2. [Your First Quantum Circuit](#your-first-quantum-circuit)
3. [Understanding Qubits](#understanding-qubits)
4. [Quantum Gates](#quantum-gates)
5. [Creating a Bell State](#creating-a-bell-state)
6. [Simulating Your Circuit](#simulating-your-circuit)
7. [Next Steps](#next-steps)

## What is Quantum Computing?

Quantum computing is a type of computation that harnesses the phenomena of quantum mechanics to perform operations on data. Unlike classical computers that use bits (0s and 1s), quantum computers use quantum bits or "qubits." 

Key concepts include:

- **Superposition**: Qubits can exist in multiple states simultaneously
- **Entanglement**: Qubits can be connected in ways that their states become correlated
- **Interference**: Quantum algorithms manipulate probabilities to increase the likelihood of correct answers

## Your First Quantum Circuit

Let's start by creating a simple quantum circuit. We'll use the interactive mode of the Quantum CLI SDK:

```bash
quantum-cli interactive
```

Once in interactive mode, create a circuit with one qubit:

```
quantum> circuit create 1
Created circuit with 1 qubits
```

Congratulations! You've created your first quantum circuit.

## Understanding Qubits

A qubit is the fundamental unit of quantum information. Unlike a classical bit that can be either 0 or 1, a qubit can exist in a superposition of both states.

In our circuit, the qubit starts in the |0⟩ state by default (a quantum state representing the classical 0). We can visualize this as a point on the Bloch sphere pointing to the north pole.

## Quantum Gates

Quantum gates are operations that manipulate qubits. They're analogous to classical logic gates but operate according to quantum mechanics.

Let's add a Hadamard gate to our circuit, which puts a qubit into superposition:

```
quantum> gate h 0
Added H gate to qubit 0
```

The Hadamard gate (H) transforms the |0⟩ state into an equal superposition of |0⟩ and |1⟩, represented as:

|0⟩ → (|0⟩ + |1⟩)/√2

Now our qubit is in a superposition state, meaning it's simultaneously in both 0 and 1 states with equal probability.

## Creating a Bell State

Let's create a more interesting circuit: a Bell state, which is a simple example of quantum entanglement.

Start by creating a new 2-qubit circuit (or use the shortcut command):

```
quantum> bell
Created Bell state circuit:
q₀: ─[H]─■─
q₁: ────╰X╯
```

This circuit has:
1. A Hadamard gate (H) on qubit 0, putting it in superposition
2. A CNOT gate with control qubit 0 and target qubit 1, entangling the two qubits

The resulting state is (|00⟩ + |11⟩)/√2, meaning that if you measure both qubits, you'll always get either both 0s or both 1s, never a mix.

## Simulating Your Circuit

Now let's simulate this circuit to see the results:

```
quantum> simulate
Running simulation with 1024 shots...
```

You should see results showing roughly equal probabilities for the states |00⟩ and |11⟩, and zero probability for |01⟩ and |10⟩. This demonstrates quantum entanglement - measuring one qubit instantly reveals the state of the other, even though individually they're in superposition.

Try running the simulation multiple times. Despite the probabilistic nature of quantum mechanics, you'll consistently see that the qubits always share the same value.

## Next Steps

Congratulations! You've created and simulated your first quantum circuits and observed quantum phenomena like superposition and entanglement.

Here are some suggestions for continuing your quantum journey:

### Try More Complex Circuits

```
quantum> examples load ghz
Created GHZ state circuit
```

The GHZ state is a multi-qubit entangled state, a generalization of the Bell state to 3 or more qubits.

### Explore Quantum Algorithms

Quantum algorithms are procedures that harness quantum effects to solve problems more efficiently than classical algorithms. Try creating:

1. **Quantum Fourier Transform**: The foundation of many quantum algorithms
   ```
   quantum> examples load qft
   ```

2. **Grover's Algorithm**: A quantum search algorithm
   ```
   quantum> examples load grover
   ```

### Learn More About Quantum Computing

To deepen your understanding of quantum computing, consider exploring:

1. The **Rich Documentation** of the Quantum CLI SDK:
   ```
   quantum> help
   ```

2. **Interactive Tutorials** provided by the SDK:
   ```
   quantum> tutorial list
   quantum> tutorial start basics
   ```

3. **External Resources**:
   - [Quantum Country](https://quantum.country/)
   - [IBM Quantum Experience](https://quantum-computing.ibm.com/)
   - [Qiskit Textbook](https://qiskit.org/textbook/)

### Exit Interactive Mode

When you're done experimenting:

```
quantum> exit
```

Remember, you can always return to interactive mode with:

```bash
quantum-cli interactive
```

Happy quantum computing! 