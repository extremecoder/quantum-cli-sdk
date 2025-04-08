# shors_factoring_15_compatible_mitigated_zne

Quantum application for shors_factoring_15_compatible_mitigated_zne

## Overview

This is a microservice wrapper for a quantum circuit. It provides a REST API to run the quantum circuit on various simulators.

## API Endpoints

- `GET /`: Information about the service
- `GET /health`: Service health check
- `POST /run`: Submit a circuit job for execution
  - Supports both blocking and non-blocking modes
- `GET /jobs/{job_id}`: Get job status
- `GET /jobs/{job_id}/results`: Get job results
- `GET /jobs`: List all jobs
- `DELETE /jobs/{job_id}`: Delete a job

## Circuit Documentation

### shors_factoring_15_compatible_mitigated_zne

This microservice implements the shors_factoring_15_compatible_mitigated_zne quantum circuit.

- Number of qubits: 8
- Number of classical bits: 4
- Gate types: cx, measure, x, h
- Has measurements: Yes


## Running the Service

### Using Docker

```bash
# Build the Docker image
docker build -t shors_factoring_15_compatible_mitigated_zne .

# Run the container
docker run -p 8000:8000 shors_factoring_15_compatible_mitigated_zne
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

# Run a circuit (non-blocking)
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "circuit": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;",
    "shots": 1024,
    "simulator": "qiskit",
    "blocking": false
  }'
  
# Run a circuit (blocking - for synchronous execution)
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "circuit": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;",
    "shots": 1024,
    "simulator": "qiskit",
    "blocking": true
  }'
```

## Version

- Version: 0.1.0
