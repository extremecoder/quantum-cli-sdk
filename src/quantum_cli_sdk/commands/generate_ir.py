"""
Commands for generating intermediate representation (IR) from source code.
"""

import os
import sys
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Set up logging
logger = logging.getLogger(__name__)

# Attempt to import Together AI client
try:
    import together
    TOGETHER_AVAILABLE = True
except ImportError:
    TOGETHER_AVAILABLE = False

def import_circuit_from_file(file_path: str) -> tuple:
    """
    Dynamically imports a Python module from a given file path and attempts to find
    a quantum circuit object or a creation function within it.

    It tries to identify the framework (Qiskit, Cirq, Braket) based on the type
    of the circuit object found or the imports within the module.

    Args:
        file_path (str): The absolute or relative path to the Python source file.

    Returns:
        tuple: A tuple containing (module, framework, circuit_object_or_func).
               'framework' is one of 'qiskit', 'cirq', 'braket', or 'unknown'.
               'circuit_object_or_func' is the found circuit object or creation function.

    Raises:
        FileNotFoundError: If the file_path does not exist.
        ImportError: If the file cannot be imported or a circuit object/function cannot be found.
        ValueError: If the quantum framework cannot be determined.
    """
    path = Path(file_path).resolve()
    if not path.is_file():
        logger.error(f"Source file not found: {file_path}")
        raise FileNotFoundError(f"Source file not found: {file_path}")

    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None:
        raise ImportError(f"Could not create module spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    
    # Add the directory of the file to sys.path to handle relative imports within the user's code
    original_sys_path = list(sys.path)
    module_dir = str(path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
        logger.debug(f"Added {module_dir} to sys.path for import")
    
    try:
        spec.loader.exec_module(module)
        logger.debug(f"Successfully executed module: {module_name}")
    except Exception as e:
        logger.error(f"Error executing module {module_name} from {file_path}: {e}", exc_info=True)
        raise ImportError(f"Failed to execute module {file_path}: {e}")
    finally:
        # Restore original sys.path
        sys.path = original_sys_path
        if module_dir in sys.path:
             sys.path.remove(module_dir) # Clean up if we added it
        logger.debug("Restored sys.path")

    # --- Find the circuit object or function and determine framework --- 
    circuit_object = None
    circuit_func = None
    framework = None

    # 1. Check for existing Qiskit/Cirq/Braket circuit objects
    for name, obj in module.__dict__.items():
        # Qiskit Check
        try:
            from qiskit import QuantumCircuit
            if isinstance(obj, QuantumCircuit):
                circuit_object = obj
                framework = "qiskit"
                logger.debug(f"Found Qiskit circuit object: {name}")
                break
        except ImportError:
            pass # Qiskit not available
        
        # Cirq Check
        try:
            import cirq
            if isinstance(obj, cirq.Circuit):
                circuit_object = obj
                framework = "cirq"
                logger.debug(f"Found Cirq circuit object: {name}")
                break
        except ImportError:
            pass # Cirq not available
            
        # Braket Check
        try:
            from braket.circuits import Circuit as BraketCircuit
            if isinstance(obj, BraketCircuit):
                circuit_object = obj
                framework = "braket"
                logger.debug(f"Found Braket circuit object: {name}")
                break
        except ImportError:
            pass # Braket not available
        
        if circuit_object: # Break outer loop if found
            break

    # 2. If no object found, look for a function that likely creates a circuit
    if circuit_object is None:
        logger.debug("No circuit object found, looking for creation function...")
        # More flexible function name check, ensuring it's defined in the module
        possible_func_names = [
            f_name for f_name, func in module.__dict__.items()
            if callable(func) 
            and getattr(func, '__module__', None) == module.__name__ # Check if defined in this module
            and (("circuit" in f_name.lower()) or ("create" in f_name.lower()))
        ]
        
        if possible_func_names:
            # Prefer functions with simpler names if multiple candidates exist
            preferred_names = [n for n in possible_func_names if n in ["create_circuit", "build_circuit", "get_circuit", "circuit"]]
            if preferred_names:
                 circuit_func_name = preferred_names[0]
            else:
                 # Otherwise, take the first valid one found
                 circuit_func_name = possible_func_names[0] # Already filtered by __module__
            
            circuit_func = getattr(module, circuit_func_name)
            logger.debug(f"Found potential circuit creation function defined in module: {circuit_func_name}")
            # Determine framework based on imports if function found
            if framework is None: # Only determine if not found via object check
                if "qiskit" in module.__dict__ or 'qiskit' in sys.modules:
                    framework = "qiskit"
                elif "cirq" in module.__dict__ or 'cirq' in sys.modules:
                    framework = "cirq"
                elif "braket" in module.__dict__ or 'braket' in sys.modules:
                    framework = "braket"

    # --- Final checks and return --- 
    circuit_object_or_func = circuit_object if circuit_object else circuit_func

    if circuit_object_or_func is None:
         logger.error(f"Could not find a recognizable circuit object or function in {file_path}")
         raise ImportError(f"Could not find circuit object or function in {file_path}")

    # If framework still unknown, try inferring from module source code content
    if framework is None:
        logger.debug("Framework not determined by object type or function import context, analyzing source code...")
        try:
            with open(path, 'r') as f:
                module_code = f.read()
            if "import qiskit" in module_code or "from qiskit" in module_code: framework = "qiskit"
            elif "import cirq" in module_code or "from cirq" in module_code: framework = "cirq"
            elif "import braket" in module_code or "from braket" in module_code: framework = "braket"
            logger.warning(f"Could not definitively determine framework, guessing '{framework}' based on code content.")
        except Exception as e:
            logger.warning(f"Could not read source file {file_path} to infer framework: {e}")
        
        if framework is None: # If still unknown, raise error
             raise ValueError(f"Could not determine quantum framework for {file_path}")

    logger.info(f"Detected framework: {framework}")
    return module, framework, circuit_object_or_func

def convert_qiskit_to_qasm(circuit: Any) -> str:
    """
    Convert a Qiskit circuit to OpenQASM 2.0 string.
    Tries multiple methods for compatibility with different Qiskit versions.
    """
    logger.debug("Attempting to convert Qiskit circuit to QASM...")
    try:
        from qiskit import QuantumCircuit
        if not isinstance(circuit, QuantumCircuit):
             raise TypeError(f"Expected qiskit.QuantumCircuit, got {type(circuit)}")

        qasm_str = None
        # Method 1: qiskit.qasm2 (preferred for Qiskit 1.0+)
        try:
            from qiskit.qasm2 import dumps
            qasm_str = dumps(circuit)
            logger.debug("Converted using qiskit.qasm2.dumps")
            return qasm_str
        except ImportError:
            logger.debug("qiskit.qasm2 not available, trying circuit.qasm()")
        except Exception as e:
             logger.warning(f"qiskit.qasm2.dumps failed: {e}, trying circuit.qasm()")

        # Method 2: circuit.qasm() method (older Qiskit versions)
        if hasattr(circuit, 'qasm') and callable(circuit.qasm):
            try:
                qasm_str = circuit.qasm()
                logger.debug("Converted using circuit.qasm() method")
                # Basic validation: Check if it starts reasonably
                if qasm_str and qasm_str.strip().startswith("OPENQASM"): 
                    return qasm_str
                else:
                     logger.warning("circuit.qasm() output does not look like valid QASM. Trying older qiskit.qasm.dumps.")
            except Exception as e:
                logger.warning(f"circuit.qasm() failed: {e}, trying older qiskit.qasm.dumps")

        # Method 3: qiskit.qasm.dumps (very old Qiskit, less likely needed)
        try:
            import qiskit.qasm
            qasm_str = qiskit.qasm.dumps(circuit)
            logger.debug("Converted using qiskit.qasm.dumps")
            return qasm_str
        except ImportError:
            logger.error("Neither qiskit.qasm2, circuit.qasm(), nor qiskit.qasm are available or working.")
            raise ImportError("Could not find a suitable Qiskit QASM export method.")
        except Exception as e:
             logger.error(f"qiskit.qasm.dumps failed: {e}")
             raise ValueError(f"Failed to convert Qiskit circuit to QASM using any available method: {e}")

    except ImportError:
        logger.error("Qiskit library not found. Cannot convert Qiskit circuit.")
        raise ImportError("Qiskit is required for Qiskit circuit conversion, but it's not installed.")
    except Exception as e:
        logger.error(f"Error during Qiskit conversion: {e}", exc_info=True)
        raise ValueError(f"Failed to convert Qiskit circuit to QASM: {str(e)}")

def convert_cirq_to_qasm(circuit: Any) -> str:
    """Convert a Cirq circuit to OpenQASM 2.0 string."""
    logger.debug("Attempting to convert Cirq circuit to QASM...")
    try:
        import cirq
        if not isinstance(circuit, cirq.Circuit):
             raise TypeError(f"Expected cirq.Circuit, got {type(circuit)}")

        # Use the QASM converter from Cirq
        # Note: Cirq's QASM support might have limitations.
        from cirq.contrib.qasm_import import QasmOutput
        qasm_output = QasmOutput(circuit)
        qasm_str = str(qasm_output)
        logger.debug("Converted using cirq.contrib.qasm_import.QasmOutput")

        # Ensure header is present (Cirq might omit it sometimes)
        if not qasm_str.strip().startswith("OPENQASM 2.0"):
             logger.warning("Cirq QASM output missing header, adding OPENQASM 2.0;")
             qasm_str = "OPENQASM 2.0;\n" + qasm_str
        # Ensure standard include is present if common gates are likely used
        if "qelib1.inc" not in qasm_str and any(g in qasm_str for g in ['cx', ' u', ' h', ' x', ' y', ' z']):
            logger.warning("Cirq QASM output missing standard include, adding qelib1.inc")
            qasm_str = qasm_str.replace("OPENQASM 2.0;", "OPENQASM 2.0;\ninclude \"qelib1.inc\";")
        
        return qasm_str
    except ImportError:
        logger.error("Cirq library not found. Cannot convert Cirq circuit.")
        raise ImportError("Cirq is required for Cirq circuit conversion, but it's not installed.")
    except Exception as e:
        logger.error(f"Error during Cirq conversion: {e}", exc_info=True)
        raise ValueError(f"Failed to convert Cirq circuit to QASM: {str(e)}")

def convert_braket_to_qasm(circuit: Any) -> str:
    """Convert an AWS Braket circuit to OpenQASM 2.0 string."""
    logger.debug("Attempting to convert Braket circuit to QASM...")
    try:
        from braket.circuits import Circuit as BraketCircuit
        if not isinstance(circuit, BraketCircuit):
             raise TypeError(f"Expected braket.circuits.Circuit, got {type(circuit)}")

        # Braket's `to_ir` with type OpenQASM is the intended method
        from braket.ir.openqasm import Program as BraketProgram
        braket_program = circuit.to_ir(ir_type=BraketProgram)
        qasm_str = braket_program.source
        logger.debug("Converted using circuit.to_ir(ir_type=braket.ir.openqasm.Program)")

        # Braket generates OpenQASM 3 by default, we need 2.0 for broader compatibility initially.
        # We will perform a basic conversion/downgrade here.
        # TODO: Implement a more robust OpenQASM 3 to 2 conversion if needed.
        if qasm_str.strip().startswith("OPENQASM 3"):
             logger.warning("Braket generated OpenQASM 3, attempting basic downgrade to OpenQASM 2.0")
             qasm_str = qasm_str.replace("OPENQASM 3;", "OPENQASM 2.0;", 1)
             # Remove Braket-specific headers/syntax not in QASM 2
             qasm_str = qasm_str.replace("cal {", "// cal {") # Comment out cal blocks
             qasm_str = qasm_str.replace("defcalgrammar", "// defcalgrammar")
             qasm_str = qasm_str.replace("defcal ", "// defcal ")
             # Basic gate name changes
             qasm_str = qasm_str.replace(" cnot ", " cx ")
             qasm_str = qasm_str.replace("\nsi ", "\ntdg ") # Approximate inverse T gate
             qasm_str = qasm_str.replace("\nti ", "\nt ") # Approximate T gate
             qasm_str = qasm_str.replace("phaseshift", "u1") # Approximate phase gate
             # Add standard include if not present
             if "include " not in qasm_str:
                  qasm_str = qasm_str.replace("OPENQASM 2.0;", "OPENQASM 2.0;\ninclude \"qelib1.inc\";")

        return qasm_str
    except ImportError:
        logger.error("Braket SDK not found. Cannot convert Braket circuit.")
        raise ImportError("Braket SDK is required for Braket circuit conversion, but it's not installed.")
    except Exception as e:
        logger.error(f"Error during Braket conversion: {e}", exc_info=True)
        raise ValueError(f"Failed to convert Braket circuit to QASM: {str(e)}")

# Helper function to generate QASM using Together AI
def generate_qasm_with_llm(source_code: str, llm_model: str) -> Optional[str]:
    """
    Uses the Together AI API to generate OpenQASM 2.0 from Python source code.

    Args:
        source_code (str): The Python source code of the quantum circuit.
        llm_model (str): The specific Together AI model to use (e.g., 'mistralai/Mixtral-8x7B-Instruct-v0.1').

    Returns:
        Optional[str]: The generated OpenQASM 2.0 string, or None if generation fails.
    """
    if not TOGETHER_AVAILABLE:
        logger.error("Together AI library is not installed. Cannot use LLM generation.")
        print("Error: 'together' library not found. Please install it to use LLM generation.", file=sys.stderr)
        return None
        
    if not os.getenv("TOGETHER_API_KEY"):
        logger.error("TOGETHER_API_KEY environment variable not set.")
        print("Error: TOGETHER_API_KEY environment variable is not set. Cannot authenticate with Together AI.", file=sys.stderr)
        return None

    logger.info(f"Attempting QASM generation using Together AI model: {llm_model}")
    try:
        client = together.Together() # Client uses TOGETHER_API_KEY automatically
        
        # Construct a detailed prompt
        prompt = f"""Given the following Python code which defines a quantum circuit (likely using Qiskit, Cirq, or Braket), convert it *only* into its equivalent OpenQASM 2.0 representation. 

IMPORTANT:
- Output *only* the OpenQASM 2.0 code block.
- Do *not* include any explanations, introductions, apologies, or surrounding text like ```qasm ... ```.
- Ensure the output is valid OpenQASM 2.0 syntax.
- Include the standard header `OPENQASM 2.0;\ninclude "qelib1.inc";`.

Python Code:
```python
{source_code}
```

OpenQASM 2.0 Code:
"""
        
        response = client.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048, # Adjust as needed
            temperature=0.1, # Lower temperature for more deterministic output
        )
        
        qasm_output = response.choices[0].message.content.strip()
        
        # Basic validation: check for header and some content
        if not qasm_output.startswith("OPENQASM 2.0;"):
             logger.warning(f"LLM output did not start with expected QASM header. Output:\n{qasm_output}")
             # Attempt to add header if missing
             if "OPENQASM 2.0;" not in qasm_output and "qreg" in qasm_output:
                  logger.info("Attempting to prepend standard QASM header.")
                  qasm_output = f"OPENQASM 2.0;\ninclude \"qelib1.inc\";\n{qasm_output}"
             else:
                  logger.error("LLM output does not look like valid QASM.")
                  return None # Or raise an error?
        
        logger.info(f"Successfully received QASM from Together AI model: {llm_model}")
        logger.debug(f"Generated QASM:\n{qasm_output[:500]}...") # Log beginning of QASM
        return qasm_output

    except Exception as e:
        logger.error(f"Error calling Together AI API: {e}", exc_info=True)
        print(f"Error communicating with Together AI: {e}", file=sys.stderr)
        return None

def generate_ir(source: str = None, dest: str = None, use_llm: bool = False, 
                llm_provider: Optional[str] = None, llm_model: Optional[str] = None) -> Optional[str]:
    """
    Generates OpenQASM 2.0 Intermediate Representation (IR) from a source Python file.

    Can use either framework-specific conversion logic or an external LLM provider.

    Args:
        source (str, optional): Path to the source Python file containing the circuit definition.
                               If None, uses the default path 'source/circuits'.
        dest (str, optional): Path to save the generated OpenQASM file.
                             If None, uses the default path 'ir/base'.
        use_llm (bool): Whether to use LLM for generation.
        llm_provider (Optional[str]): The LLM provider to use (e.g., 'togetherai').
        llm_model (Optional[str]): The specific LLM model name to use.

    Returns:
        Optional[str]: The path to the generated QASM file if successful, None otherwise.
    """
    # Handle default source and destination paths
    if source is None:
        source = os.path.join(os.getcwd(), "source", "circuits")
        # If source is a directory, look for Python files
        if os.path.isdir(source):
            python_files = [f for f in os.listdir(source) if f.endswith('.py')]
            if not python_files:
                logger.error(f"No Python files found in default source directory: {source}")
                print(f"Error: No Python files found in default source directory: {source}", file=sys.stderr)
                return None
            # Use the first Python file found
            source = os.path.join(source, python_files[0])
            logger.info(f"Using default source file: {source}")
        else:
            logger.error(f"Default source directory not found: {source}")
            print(f"Error: Default source directory not found: {source}. Please create it or specify --source.", file=sys.stderr)
            return None
    
    if dest is None:
        dest_dir = os.path.join(os.getcwd(), "ir", "openqasm", "base")
        os.makedirs(dest_dir, exist_ok=True)
        # Extract filename from source and use it for destination
        source_filename = os.path.basename(source)
        dest_filename = os.path.splitext(source_filename)[0] + ".qasm"
        dest = os.path.join(dest_dir, dest_filename)
        logger.info(f"Using default destination path: {dest}")
    
    source_path = Path(source).resolve()
    dest_path = Path(dest).resolve()
    logger.info(f"Starting IR generation from source: {source}")

    qasm_string = None

    # --- LLM Generation Path --- 
    if use_llm:
        # Set default LLM provider and model if not specified
        if not llm_provider:
            llm_provider = "togetherai"
            logger.info(f"Using default LLM provider: {llm_provider}")
        
        if not llm_model:
            llm_model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
            logger.info(f"Using default LLM model: {llm_model}")
            
        logger.info(f"LLM generation requested: Provider={llm_provider}, Model={llm_model}")
        if llm_provider.lower() == "togetherai":
            try:
                with open(source_path, 'r') as f:
                    source_code = f.read()
                qasm_string = generate_qasm_with_llm(source_code, llm_model)
                if qasm_string is None:
                    logger.error("LLM generation failed.")
                    return None # Explicitly return None if LLM fails
            except FileNotFoundError:
                 logger.error(f"Source file not found: {source}")
                 print(f"Error: Source file not found: {source}", file=sys.stderr)
                 return None
            except Exception as e:
                 logger.error(f"Error during LLM generation prep: {e}", exc_info=True)
                 print(f"Error preparing for LLM generation: {e}", file=sys.stderr)
                 return None
        else:
            logger.error(f"Unsupported LLM provider: {llm_provider}")
            print(f"Error: LLM provider '{llm_provider}' is not supported.", file=sys.stderr)
            return None
            
    # --- Framework-Specific Conversion Path --- 
    else:
        logger.info("Using framework-specific conversion logic.")
        try:
            # 1. Import module and find circuit
            module, framework, circuit_object_or_func = import_circuit_from_file(str(source_path))

            # 2. Get the circuit object (call function if necessary)
            if callable(circuit_object_or_func):
                func_name = getattr(circuit_object_or_func, '__name__', 'unknown function')
                logger.debug(f"Calling circuit function: {func_name}")
                try:
                    circuit = circuit_object_or_func()
                    logger.debug(f"Circuit object obtained from function call, type: {type(circuit)}")
                    # Re-check framework based on returned object type for certainty
                    try:
                        from qiskit import QuantumCircuit
                        if isinstance(circuit, QuantumCircuit): framework = "qiskit"
                    except ImportError: pass
                    try:
                        import cirq
                        if isinstance(circuit, cirq.Circuit): framework = "cirq"
                    except ImportError: pass
                    try:
                        from braket.circuits import Circuit as BraketCircuit
                        if isinstance(circuit, BraketCircuit): framework = "braket"
                    except ImportError: pass
                    logger.debug(f"Framework confirmed/updated based on returned object: {framework}")

                except Exception as e:
                    logger.error(f"Error calling circuit creation function '{func_name}' from {source}: {e}", exc_info=True)
                    raise ValueError(f"Failed to create circuit by calling function '{func_name}' in {source}: {str(e)}")
            else:
                circuit = circuit_object_or_func
                logger.debug(f"Using pre-defined circuit object, type: {type(circuit)}")

            # 3. Convert to QASM based on framework
            logger.info(f"Converting {framework} circuit to OpenQASM 2.0")
            if framework == "qiskit":
                qasm_string = convert_qiskit_to_qasm(circuit)
            elif framework == "cirq":
                qasm_string = convert_cirq_to_qasm(circuit)
            elif framework == "braket":
                qasm_string = convert_braket_to_qasm(circuit)
            else:
                # This case should ideally be unreachable due to checks in import_circuit_from_file
                logger.error(f"Unsupported or undetermined framework '{framework}' for conversion.")
                raise ValueError(f"Cannot convert unknown framework '{framework}'")

            if qasm_string is None:
                raise ValueError(f"Conversion to QASM failed for framework {framework}")

        except FileNotFoundError as e:
            logger.error(f"File not found during framework conversion: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return None
        except (ImportError, ValueError, TypeError) as e:
            logger.error(f"Failed framework conversion for {source}: {e}")
            print(f"Error during framework conversion: {e}", file=sys.stderr)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during framework conversion for {source}: {e}", exc_info=True)
            print(f"An unexpected error occurred during framework conversion: {e}", file=sys.stderr)
            return None

    # --- Save QASM string (common to both paths if successful) --- 
    if qasm_string is not None:
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "w") as f:
                f.write(qasm_string)
            logger.info(f"Successfully generated OpenQASM 2.0 IR at: {dest_path}")
            return str(dest_path)
        except Exception as e:
             logger.error(f"Failed to write generated QASM to {dest_path}: {e}", exc_info=True)
             print(f"Error writing QASM file: {e}", file=sys.stderr)
             return None
    else:
        # If we reach here, qasm_string is None, meaning generation failed in one of the paths
        logger.error("QASM string generation failed.")
        print("Error: Failed to generate QASM string.", file=sys.stderr)
        return None

# Example of how this might be called by the CLI handler
# (This main block is illustrative and wouldn't typically be in the command file)
if __name__ == '__main__':
    # Example Usage (replace with actual CLI argument parsing)
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <source_python_file> <destination_qasm_file>")
        sys.exit(1)

    source_file_arg = sys.argv[1]
    dest_file_arg = sys.argv[2]

    # Configure logging for standalone run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    result = generate_ir(source=source_file_arg, dest=dest_file_arg)

    if result:
        print(f"\nGeneration successful. Details: {result}")
        # Optionally print the generated file content
        # try:
        #     print("\nGenerated QASM Content:")
        #     print(Path(result['dest']).read_text())
        # except Exception as e:
        #     print(f"Could not read generated file: {e}")
    else:
        print("\nIR Generation failed.")
        sys.exit(1) 