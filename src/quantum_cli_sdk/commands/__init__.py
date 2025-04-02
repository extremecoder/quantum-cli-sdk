"""
Commands for the quantum CLI SDK.
"""

# This file should generally be empty or only contain package-level
# initialization logic specific to the 'commands' package, if any.

# Avoid importing submodules directly here if they are used by cli.py,
# as it can lead to circular dependencies.

# Example: If cli.py imports `from .commands import run`, don't do `from . import run` here.

# The imports below were causing circular import issues and are removed.
# from . import run
# from . import (
#     generate_ir, validate, security_scan, simulate, optimize,
#     generate_tests, test, hw_run, finetune, visualize,
#     benchmark, microservice, package, publish, provision, run_app,
#     estimate_resources, template, mitigate, calculate_cost, init,
#     generate_microservice_tests, trial
# )
