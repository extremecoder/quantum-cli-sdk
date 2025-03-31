# Quantum Project

A quantum computing project created with the Quantum CLI SDK.

## Features

- Bell state preparation and analysis
- Grover's search algorithm implementation
- Error mitigation techniques
- Web API for running quantum circuits
- Comprehensive testing framework
- CI/CD workflows with GitHub Actions

## Project Structure

```
.
├── src/                    # Source code
│   ├── circuits/           # Quantum circuit definitions
│   ├── utilities/          # Helper utilities
│   └── api/                # Web API
├── tests/                  # Unit tests
├── docs/                   # Documentation
├── examples/               # Example usage scripts
├── data/                   # Data files
├── results/                # Execution results
├── .github/                # GitHub configuration
│   └── workflows/          # CI/CD workflows
├── main.py                 # Main entry point
├── setup.py                # Package configuration
├── requirements.txt        # Dependencies
├── quantum_config.yaml     # Project configuration
└── README.md               # This file
```

## Setup

1. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. (Optional) Install development dependencies:
   ```
   pip install -e ".[dev]"
   ```

## Usage

### Running the example

```bash
python main.py
```

This will:
1. Create and visualize a Bell state circuit
2. Create and run a Grover's search algorithm
3. Apply error mitigation techniques
4. Set up a simple API

### Running tests

```bash
pytest
```

### Starting the API server

```bash
python -m src.api.server
```

## Configuration

Edit `quantum_config.yaml` to change settings such as:
- Default quantum backend
- Optimization level
- Error mitigation techniques
- API configuration
- Logging settings

## API Endpoints

- `GET /circuits` - List available circuits
- `GET /circuits/{circuit_id}` - Get circuit details
- `POST /run` - Run a quantum circuit
- `GET /results/{job_id}` - Get execution results

## Documentation

See the `docs/` directory for detailed documentation:
- `docs/index.md` - Main documentation
- `docs/api.md` - API documentation
- `docs/examples.md` - Usage examples

## License

MIT