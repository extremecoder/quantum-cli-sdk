// Standard gates library QASM 2.0
// file: qelib1.inc

// --- Standard Gates ---

// Pauli gate: bit-flip
gate x a { u3(pi,0,pi) a; }
// Pauli gate: bit and phase flip
gate y a { u3(pi,pi/2,pi/2) a; }
// Pauli gate: phase flip
gate z a { u1(pi) a; }
// Clifford gate: Hadamard
gate h a { u2(0,pi) a; }
// Clifford gate: sqrt(Z) phase gate
gate s a { u1(pi/2) a; }
// Clifford gate: conjugate of sqrt(Z)
gate sdg a { u1(-pi/2) a; }
// CNOT gate
gate cx c,t { CX c,t; }
// Clifford gate: sqrt(S) phase gate
gate t a { u1(pi/4) a; }
// Clifford gate: conjugate of sqrt(S)
gate tdg a { u1(-pi/4) a; }

// --- Standard User-Defined Gates  ---

// controlled-Phase
gate cz a,b { h b; cx a,b; h b; }
// controlled-Y
gate cy a,b { sdg b; cx a,b; s b; }
// controlled-H
gate ch a,b {
h b; sdg b;
cx a,b;
h b; t b;
cx a,b;
t b; h b; s b; x b; s a;
}
// controlled-Z
gate crz(lambda) a,b
{
u1(lambda/2) b;
cx a,b;
u1(-lambda/2) b;
cx a,b;
}
// controlled-U1
gate cu1(lambda) a,b
{
u1(lambda/2) a;
cx a,b;
u1(-lambda/2) b;
cx a,b;
u1(lambda/2) a;
}
// controlled-U3
gate cu3(theta,phi,lambda) c, t
{
// implements controlled-U(theta,phi,lambda) with target t and control c
u1((lambda-phi)/2) t;
cx c,t;
u3(-theta/2,0,-(phi+lambda)/2) t;
cx c,t;
u3(theta/2,phi,0) t;
}
// 3-qubit Toffoli gate
gate ccx a,b,c
{
h c;
cx b,c; tdg c;
cx a,c; t c;
cx b,c; tdg c;
cx a,c; t b; t c; h c;
cx a,b; t a; tdg b;
cx a,b;
}
// Swap gate
gate swap a,b { cx a,b; cx b,a; cx a,b; }


// --- Standard Single Qubit Gates ---

// Phase gate
gate p(lambda) a { u1(lambda) a; }
// idle gate specified by length (this is necessary for delay effect).
gate id a { u(0,0,0) a; } // ui changed to u
// idle gate
//gate id a {} // doesn't work with simulator
// Phase gate Rx(pi/2)
gate sx a { sxdg a; h a; sxdg a; }
// Phase gate Rx(pi/2)^dagger
gate sxdg a { u3(pi/2, -pi/2, pi/2) a; }
// Rotation around X-axis
gate rx(theta) a { u3(theta, -pi/2, pi/2) a; }
// rotation around Y-axis
gate ry(theta) a { u3(theta, 0, 0) a; }
// rotation around Z axis
gate rz(phi) a { u1(phi) a; }


// --- Standard Measurement ---
// measure qubit a into classical bit c
measure a -> c;

// --- Standard Reset ---
// reset qubit a to |0>
reset a;

// --- Standard User-Defined Gates ---

// --- Standard Single Qubit Unitary Errors ---
// phase-flip error
gate E_phase a { Z a; }
// bit-flip error
gate E_bit a { X a; }
// bit-phase error
gate E_bitphase a { Y a; }

// --- Standard Single Qubit Gates ---

// Unitary gate u3
gate u3(theta,phi,lambda) q { U(theta,phi,lambda) q; }
// Unitary gate u2
gate u2(phi,lambda) q { U(pi/2,phi,lambda) q; }
// Unitary gate u1
gate u1(lambda) q { U(0,0,lambda) q; }
// Basic single qubit gate U
gate u(theta,phi,lambda) q { U(theta, phi, lambda) q;} // Fixed U


// --- Standard Conditional ---
// if classical bit c == val, apply quantum operation g
if(c==val) g; 