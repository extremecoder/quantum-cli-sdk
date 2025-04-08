# ${app_name}

${app_description}

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

${circuit_documentation}

## Running the Service

### Using Docker

```bash
# Build the Docker image
docker build -t ${app_name} .

# Run the container
docker run -p ${port}:${port} ${app_name}
```

### Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app:app --host 0.0.0.0 --port ${port}
```

## API Usage Example

```bash
# Health check
curl http://localhost:${port}/health

# Run a circuit (non-blocking)
curl -X POST http://localhost:${port}/run \
  -H "Content-Type: application/json" \
  -d '{
    "circuit": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;",
    "shots": 1024,
    "simulator": "qiskit",
    "blocking": false
  }'
  
# Run a circuit (blocking - for synchronous execution)
curl -X POST http://localhost:${port}/run \
  -H "Content-Type: application/json" \
  -d '{
    "circuit": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;",
    "shots": 1024,
    "simulator": "qiskit",
    "blocking": true
  }'
```

## Version

- Version: ${app_version}
