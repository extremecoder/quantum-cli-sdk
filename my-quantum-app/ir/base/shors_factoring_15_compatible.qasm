OPENQASM 2.0;
include "qelib1.inc";

qreg period[4];
qreg target[4];
creg measure[4];

x target[0];
h period[0];
h period[1];
h period[2];
h period[3];

cx period[3], target[0];
cx period[3], target[1];
cx period[3], target[2];
cx period[2], target[2];
cx period[1], target[0];
cx period[1], target[0];
cx period[0], target[0];
cx period[0], target[1];
cx period[0], target[2];
cx period[1], target[2];
cx period[1], target[1];
cx period[2], target[2];

swap period[0], period[3];
swap period[1], period[2];

h period[0];
h period[1];
h period[2];
h period[3];

cz period[0], period[1];
cz period[0], period[2];
cz period[1], period[2];
cz period[0], period[3];
cz period[1], period[3];
cz period[2], period[3];

measure period -> measure;