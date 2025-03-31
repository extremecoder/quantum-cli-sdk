#!/usr/bin/env python3
"""
Setup script for the quantum project.
"""

from setuptools import setup, find_packages

# Read version from __init__.py
with open("src/__init__.py", "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break
    else:
        version = "0.1.0"

# Read long description from README.md
with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="quantum-project",
    version=version,
    description="Quantum computing project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/quantum-project",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Quantum Computing",
    ],
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.22.0",
        "matplotlib>=3.5.0",
        "qiskit>=1.0.0",
        "pyyaml>=6.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
        ],
        "api": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
        ],
        "cirq": [
            "cirq>=1.0.0",
        ],
        "braket": [
            "amazon-braket-sdk>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quantum-project=src.main:cli_main",
        ],
    },
) 