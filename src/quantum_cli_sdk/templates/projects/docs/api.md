# API Documentation

This document describes the web API for accessing the quantum functionality provided by this project.

## Endpoints

### List Available Circuits

```
GET /circuits
```

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "bell",
      "name": "Bell State",
      "qubits": 2
    },
    {
      "id": "grover",
      "name": "Grover's Algorithm",
      "qubits": 3
    }
  ]
}
```

### Get Circuit Details

```
GET /circuits/{circuit_id}
```

**Parameters:**
- `circuit_id`: ID of the circuit to retrieve

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "bell",
    "name": "Bell State",
    "qubits": 2,
    "description": "Creates a maximally entangled state between two qubits"
  }
}
```

### Run Circuit

```
POST /run
```

**Request Body:**

```json
{
  "circuit_id": "bell",
  "shots": 1024,
  "params": {
    "optimized": true
  }
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "job_id": "job-1646932809",
    "status": "submitted",
    "message": "Circuit execution started"
  }
}
```

### Get Results

```
GET /results/{job_id}
```

**Parameters:**
- `job_id`: ID of the job to retrieve results for

**Response:**

```json
{
  "status": "success",
  "data": {
    "job_id": "job-1646932809",
    "status": "completed",
    "results": {
      "counts": {
        "00": 25,
        "01": 512,
        "10": 487,
        "11": 0
      },
      "execution_time": 0.05,
      "quantum_state": [0.0, 0.707, 0.707, 0.0]
    }
  }
}
```

## Error Handling

All API responses follow the same format for consistency:

**Success Response:**

```json
{
  "status": "success",
  "data": { ... }
}
```

**Error Response:**

```json
{
  "status": "error",
  "message": "Error description",
  "code": 404  // Optional error code
}
```

## Running the API

In a production environment, this API would be deployed using a proper web framework like Flask or FastAPI. For development purposes, the API can be started by running:

```bash
python -m src.api.server
```

The development server will be available at `http://localhost:8000`. 