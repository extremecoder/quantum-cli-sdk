# quantum-shors_factoring_15_compatible_mitigated_zne-service

Quantum microservice for the shors_factoring_15_compatible_mitigated_zne circuit

## Overview

This is a microservice wrapper for a quantum circuit. It provides a REST API to run the quantum circuit on various simulators.

## API Endpoints

- `GET /`: Information about the service
- `GET /health`: Service health check
- `POST /run`: Submit a circuit job for execution
- `GET /jobs/{job_id}`: Get job status
- `GET /results/{job_id}`: Get job results

## Circuit Documentation

### shors_factoring_15_compatible_mitigated_zne

This microservice implements the shors_factoring_15_compatible_mitigated_zne quantum circuit.

- Number of qubits: 8
- Number of classical bits: 4
- Gate types: h, cx, measure, x
- Has measurements: Yes


## Running the Service

### Using Docker

```bash
# Build the Docker image
docker build -t quantum-shors_factoring_15_compatible_mitigated_zne-service .

# Run the container
docker run -p 8000:8000 quantum-shors_factoring_15_compatible_mitigated_zne-service
```

### Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API Usage Example

```bash
# Health check
curl http://localhost:8000/health

# Run a circuit
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "circuit": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;",
    "shots": 1024,
    "simulator": "qiskit"
  }'
```

## Version

- Version: 0.1.0
