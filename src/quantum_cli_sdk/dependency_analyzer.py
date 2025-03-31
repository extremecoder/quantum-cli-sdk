#!/usr/bin/env python3
"""
Dependency Analyzer for Quantum CLI SDK.

This module provides functionality to:
- Check system dependencies required for Quantum CLI SDK
- Verify Python package dependencies
- Analyze version compatibility
- Generate dependency reports
"""

import os
import sys
import pkg_resources
import subprocess
import platform
import importlib
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class DependencyRequirement:
    """Represents a dependency requirement for the Quantum CLI SDK."""
    
    def __init__(self, name: str, required_version: str, 
                 importance: str = "required", 
                 description: str = "",
                 url: str = ""):
        """
        Initialize a dependency requirement.
        
        Args:
            name: Name of the dependency
            required_version: Required version (can be a version spec like >=1.0.0)
            importance: Importance of the dependency (required, recommended, optional)
            description: Description of what the dependency is used for
            url: URL for more information about the dependency
        """
        self.name = name
        self.required_version = required_version
        self.importance = importance
        self.description = description
        self.url = url
        
    def __str__(self) -> str:
        """Return string representation of the dependency requirement."""
        return f"{self.name} {self.required_version} ({self.importance})"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert dependency requirement to dictionary."""
        return {
            "name": self.name,
            "required_version": self.required_version,
            "importance": self.importance,
            "description": self.description,
            "url": self.url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'DependencyRequirement':
        """Create dependency requirement from dictionary."""
        return cls(
            name=data["name"],
            required_version=data["required_version"],
            importance=data.get("importance", "required"),
            description=data.get("description", ""),
            url=data.get("url", "")
        )


class DependencyStatus:
    """Represents the status of a dependency."""
    
    def __init__(self, requirement: DependencyRequirement, 
                 installed: bool, 
                 installed_version: Optional[str] = None,
                 compatible: Optional[bool] = None,
                 error_message: Optional[str] = None):
        """
        Initialize dependency status.
        
        Args:
            requirement: Dependency requirement
            installed: Whether the dependency is installed
            installed_version: Installed version of the dependency
            compatible: Whether the installed version is compatible
            error_message: Error message if any
        """
        self.requirement = requirement
        self.installed = installed
        self.installed_version = installed_version
        self.compatible = compatible
        self.error_message = error_message
        
    def __str__(self) -> str:
        """Return string representation of the dependency status."""
        status = "✅ " if self.is_ok() else "❌ "
        status += f"{self.requirement.name}"
        
        if self.installed and self.installed_version:
            status += f" {self.installed_version}"
            
            if self.compatible is False:
                status += f" (required: {self.requirement.required_version})"
                
        elif not self.installed:
            status += f" not found (required: {self.requirement.required_version})"
            
        if self.error_message:
            status += f" - {self.error_message}"
            
        return status
    
    def is_ok(self) -> bool:
        """Check if the dependency status is OK."""
        if self.requirement.importance == "optional" and not self.installed:
            return True
            
        return self.installed and (self.compatible is None or self.compatible)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dependency status to dictionary."""
        return {
            "requirement": self.requirement.to_dict(),
            "installed": self.installed,
            "installed_version": self.installed_version,
            "compatible": self.compatible,
            "error_message": self.error_message,
            "is_ok": self.is_ok()
        }


class DependencyAnalyzer:
    """Analyzer for checking and verifying dependencies."""
    
    def __init__(self, requirements_file: Optional[str] = None):
        """
        Initialize dependency analyzer.
        
        Args:
            requirements_file: Path to requirements file (defaults to pyproject.toml)
        """
        self.requirements_file = requirements_file
        self.system_requirements = self._get_system_requirements()
        self.python_requirements = self._get_python_requirements()
        
    def _get_system_requirements(self) -> List[DependencyRequirement]:
        """Get system requirements for Quantum CLI SDK."""
        return [
            DependencyRequirement(
                name="python",
                required_version=">=3.8.0",
                importance="required",
                description="Python interpreter",
                url="https://www.python.org/"
            ),
            DependencyRequirement(
                name="pip",
                required_version=">=20.0.0",
                importance="required",
                description="Python package installer",
                url="https://pip.pypa.io/"
            ),
            DependencyRequirement(
                name="gcc",
                required_version=">=7.0.0",
                importance="recommended",
                description="GNU Compiler Collection (required for some quantum packages)",
                url="https://gcc.gnu.org/"
            ),
            DependencyRequirement(
                name="git",
                required_version=">=2.0.0",
                importance="recommended",
                description="Version control system",
                url="https://git-scm.com/"
            ),
            DependencyRequirement(
                name="cmake",
                required_version=">=3.10.0",
                importance="optional",
                description="Build system for some quantum packages",
                url="https://cmake.org/"
            )
        ]
    
    def _get_python_requirements(self) -> List[DependencyRequirement]:
        """Get Python package requirements for Quantum CLI SDK."""
        requirements = [
            # Core scientific libraries
            DependencyRequirement(
                name="numpy",
                required_version=">=1.20.0",
                importance="required",
                description="Scientific computing library",
                url="https://numpy.org/"
            ),
            DependencyRequirement(
                name="scipy",
                required_version=">=1.7.0",
                importance="required",
                description="Scientific computing library",
                url="https://scipy.org/"
            ),
            DependencyRequirement(
                name="matplotlib",
                required_version=">=3.4.0",
                importance="required",
                description="Plotting library",
                url="https://matplotlib.org/"
            ),
            
            # Quantum libraries
            DependencyRequirement(
                name="qiskit",
                required_version=">=0.36.0",
                importance="required",
                description="IBM Quantum SDK",
                url="https://qiskit.org/"
            ),
            DependencyRequirement(
                name="braket",
                required_version=">=1.8.0",
                importance="recommended",
                description="Amazon Braket SDK",
                url="https://github.com/aws/amazon-braket-sdk-python"
            ),
            DependencyRequirement(
                name="cirq",
                required_version=">=1.0.0",
                importance="optional",
                description="Google Quantum SDK",
                url="https://quantumai.google/cirq"
            ),
            
            # Developer tools
            DependencyRequirement(
                name="pytest",
                required_version=">=7.0.0",
                importance="recommended",
                description="Testing framework",
                url="https://pytest.org/"
            ),
            DependencyRequirement(
                name="rich",
                required_version=">=13.0.0",
                importance="recommended",
                description="Rich text and formatting in the terminal",
                url="https://github.com/Textualize/rich"
            ),
            DependencyRequirement(
                name="plotly",
                required_version=">=5.10.0",
                importance="optional",
                description="Interactive visualizations",
                url="https://plotly.com/python/"
            )
        ]
        
        # Load additional requirements from pyproject.toml or requirements.txt if available
        try:
            if self.requirements_file:
                requirements.extend(self._parse_requirements_file(self.requirements_file))
        except Exception as e:
            logger.warning(f"Failed to parse requirements file: {e}")
            
        return requirements
    
    def _parse_requirements_file(self, file_path: str) -> List[DependencyRequirement]:
        """
        Parse requirements from a file.
        
        Args:
            file_path: Path to requirements file
            
        Returns:
            List of dependency requirements
        """
        if not os.path.exists(file_path):
            logger.warning(f"Requirements file not found: {file_path}")
            return []
            
        requirements = []
        
        if file_path.endswith('.toml'):
            # Parse pyproject.toml
            import tomli
            try:
                with open(file_path, 'rb') as f:
                    pyproject = tomli.load(f)
                
                # Extract dependencies
                deps = {}
                
                # Poetry dependencies
                if "tool" in pyproject and "poetry" in pyproject["tool"]:
                    if "dependencies" in pyproject["tool"]["poetry"]:
                        deps.update(pyproject["tool"]["poetry"]["dependencies"])
                        
                # PEP 621 dependencies
                elif "project" in pyproject and "dependencies" in pyproject["project"]:
                    for dep in pyproject["project"]["dependencies"]:
                        name = dep.split()[0].strip()
                        version = " ".join(dep.split()[1:]) if len(dep.split()) > 1 else ""
                        deps[name] = version
                
                # Convert to requirement objects
                for name, version in deps.items():
                    if name != "python" and not name.startswith("$"):
                        if isinstance(version, dict) and "version" in version:
                            version = version["version"]
                        requirements.append(DependencyRequirement(
                            name=name,
                            required_version=str(version) if version else "",
                            importance="required"  # Assuming all are required
                        ))
            except Exception as e:
                logger.warning(f"Failed to parse pyproject.toml: {e}")
                
        elif file_path.endswith('.txt'):
            # Parse requirements.txt
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            try:
                                req = pkg_resources.Requirement.parse(line)
                                requirements.append(DependencyRequirement(
                                    name=req.name,
                                    required_version=str(req.specifier) if req.specifier else "",
                                    importance="required"  # Assuming all are required
                                ))
                            except Exception:
                                # Skip invalid requirements
                                pass
            except Exception as e:
                logger.warning(f"Failed to parse requirements.txt: {e}")
        
        return requirements
    
    def check_system_dependency(self, requirement: DependencyRequirement) -> DependencyStatus:
        """
        Check a system dependency.
        
        Args:
            requirement: Dependency requirement
            
        Returns:
            Dependency status
        """
        if requirement.name == "python":
            # Check Python version
            installed_version = platform.python_version()
            compatible = self._check_version_compatibility(installed_version, requirement.required_version)
            
            return DependencyStatus(
                requirement=requirement,
                installed=True,
                installed_version=installed_version,
                compatible=compatible
            )
            
        elif requirement.name == "pip":
            # Check pip version
            try:
                import pip
                installed_version = pip.__version__
                compatible = self._check_version_compatibility(installed_version, requirement.required_version)
                
                return DependencyStatus(
                    requirement=requirement,
                    installed=True,
                    installed_version=installed_version,
                    compatible=compatible
                )
            except ImportError:
                return DependencyStatus(
                    requirement=requirement,
                    installed=False,
                    error_message="pip not found"
                )
                
        else:
            # Check command-line tool
            return self._check_command_line_tool(requirement)
    
    def _check_command_line_tool(self, requirement: DependencyRequirement) -> DependencyStatus:
        """
        Check if a command-line tool is installed.
        
        Args:
            requirement: Dependency requirement
            
        Returns:
            Dependency status
        """
        # Map of commands to version flags
        version_flags = {
            "gcc": "--version",
            "git": "--version",
            "cmake": "--version",
            "clang": "--version",
            "make": "--version",
            "docker": "--version",
            "java": "-version"
        }
        
        # Default version flag
        version_flag = version_flags.get(requirement.name, "--version")
        
        try:
            # Try to run the command with version flag
            result = subprocess.run(
                [requirement.name, version_flag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return DependencyStatus(
                    requirement=requirement,
                    installed=False,
                    error_message=f"Command returned non-zero exit code: {result.returncode}"
                )
                
            # Parse version from output
            version_output = result.stdout if result.stdout else result.stderr
            installed_version = self._parse_version_from_output(requirement.name, version_output)
            
            if not installed_version:
                return DependencyStatus(
                    requirement=requirement,
                    installed=True,
                    error_message="Version could not be determined"
                )
                
            # Check version compatibility
            compatible = self._check_version_compatibility(installed_version, requirement.required_version)
            
            return DependencyStatus(
                requirement=requirement,
                installed=True,
                installed_version=installed_version,
                compatible=compatible
            )
            
        except FileNotFoundError:
            return DependencyStatus(
                requirement=requirement,
                installed=False,
                error_message=f"Command not found: {requirement.name}"
            )
            
        except Exception as e:
            return DependencyStatus(
                requirement=requirement,
                installed=False,
                error_message=str(e)
            )
    
    def _parse_version_from_output(self, tool_name: str, output: str) -> Optional[str]:
        """
        Parse version from command output.
        
        Args:
            tool_name: Name of the tool
            output: Command output
            
        Returns:
            Extracted version or None if not found
        """
        # Basic version extraction using common patterns
        import re
        
        # Common version patterns
        patterns = [
            r'version\s+(\d+\.\d+\.\d+)',  # version X.Y.Z
            r'v?(\d+\.\d+\.\d+)',  # vX.Y.Z or X.Y.Z
            r'(\d+\.\d+)',  # X.Y
            r'(\d+\.\d+\.\d+[\w\.\-]*)'  # X.Y.Z with possible suffixes
        ]
        
        # Tool-specific patterns
        if tool_name == "gcc":
            patterns = [r'gcc\s+.+\s+(\d+\.\d+\.\d+)'] + patterns
        elif tool_name == "git":
            patterns = [r'git version (\d+\.\d+\.\d+)'] + patterns
            
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
                
        # Version not found
        return None
    
    def check_python_dependency(self, requirement: DependencyRequirement) -> DependencyStatus:
        """
        Check a Python package dependency.
        
        Args:
            requirement: Dependency requirement
            
        Returns:
            Dependency status
        """
        try:
            # Try to get package distribution
            dist = pkg_resources.get_distribution(requirement.name)
            installed_version = dist.version
            
            # Check version compatibility
            compatible = self._check_version_compatibility(installed_version, requirement.required_version)
            
            return DependencyStatus(
                requirement=requirement,
                installed=True,
                installed_version=installed_version,
                compatible=compatible
            )
            
        except pkg_resources.DistributionNotFound:
            # Package not installed
            return DependencyStatus(
                requirement=requirement,
                installed=False,
                error_message=f"Package not installed: {requirement.name}"
            )
            
        except Exception as e:
            # Other error
            return DependencyStatus(
                requirement=requirement,
                installed=False,
                error_message=str(e)
            )
    
    def _check_version_compatibility(self, installed_version: str, required_version: str) -> bool:
        """
        Check if installed version is compatible with required version.
        
        Args:
            installed_version: Installed version
            required_version: Required version specification
            
        Returns:
            True if compatible, False otherwise
        """
        if not required_version:
            # No version requirement specified
            return True
            
        try:
            # Parse required version using pkg_resources
            req = pkg_resources.Requirement.parse(f"package{required_version}")
            
            # Check if installed version is compatible
            return installed_version in req
            
        except Exception:
            # If parsing fails, assume compatible
            logger.warning(f"Failed to parse version requirement: {required_version}")
            return True
    
    def check_all_dependencies(self) -> Tuple[List[DependencyStatus], List[DependencyStatus]]:
        """
        Check all system and Python dependencies.
        
        Returns:
            Tuple of lists of dependency statuses (system, python)
        """
        # Check system dependencies
        system_statuses = [self.check_system_dependency(req) for req in self.system_requirements]
        
        # Check Python dependencies
        python_statuses = [self.check_python_dependency(req) for req in self.python_requirements]
        
        return system_statuses, python_statuses
    
    def generate_report(self, 
                       system_statuses: List[DependencyStatus], 
                       python_statuses: List[DependencyStatus],
                       format: str = "text") -> str:
        """
        Generate a dependency report.
        
        Args:
            system_statuses: System dependency statuses
            python_statuses: Python dependency statuses
            format: Report format (text, json, markdown)
            
        Returns:
            Report in the specified format
        """
        if format == "json":
            # Generate JSON report
            report = {
                "system": [status.to_dict() for status in system_statuses],
                "python": [status.to_dict() for status in python_statuses],
                "summary": {
                    "system": {
                        "total": len(system_statuses),
                        "ok": sum(1 for status in system_statuses if status.is_ok()),
                        "missing": sum(1 for status in system_statuses if not status.installed)
                    },
                    "python": {
                        "total": len(python_statuses),
                        "ok": sum(1 for status in python_statuses if status.is_ok()),
                        "missing": sum(1 for status in python_statuses if not status.installed)
                    }
                }
            }
            
            return json.dumps(report, indent=2)
            
        elif format == "markdown":
            # Generate Markdown report
            report = ["# Dependency Report\n"]
            
            # System dependencies
            report.append("## System Dependencies\n")
            for status in system_statuses:
                icon = "✅" if status.is_ok() else "❌"
                report.append(f"- {icon} **{status.requirement.name}**")
                if status.installed and status.installed_version:
                    report.append(f": {status.installed_version}")
                    if status.compatible is False:
                        report.append(f" (required: {status.requirement.required_version})")
                elif not status.installed:
                    report.append(f": not found (required: {status.requirement.required_version})")
                if status.error_message:
                    report.append(f" - {status.error_message}")
                report.append("\n")
            
            # Python dependencies
            report.append("\n## Python Dependencies\n")
            for status in python_statuses:
                icon = "✅" if status.is_ok() else "❌"
                report.append(f"- {icon} **{status.requirement.name}**")
                if status.installed and status.installed_version:
                    report.append(f": {status.installed_version}")
                    if status.compatible is False:
                        report.append(f" (required: {status.requirement.required_version})")
                elif not status.installed:
                    report.append(f": not found (required: {status.requirement.required_version})")
                if status.error_message:
                    report.append(f" - {status.error_message}")
                report.append("\n")
            
            # Summary
            report.append("\n## Summary\n")
            report.append(f"- System dependencies: {sum(1 for status in system_statuses if status.is_ok())}/{len(system_statuses)} OK\n")
            report.append(f"- Python dependencies: {sum(1 for status in python_statuses if status.is_ok())}/{len(python_statuses)} OK\n")
            
            return "".join(report)
        
        else:
            # Generate text report (default)
            report = ["Dependency Report\n"]
            report.append("=================\n\n")
            
            # System dependencies
            report.append("System Dependencies:\n")
            report.append("-------------------\n")
            for status in system_statuses:
                report.append(f"{status}\n")
            
            # Python dependencies
            report.append("\nPython Dependencies:\n")
            report.append("-------------------\n")
            for status in python_statuses:
                report.append(f"{status}\n")
            
            # Summary
            report.append("\nSummary:\n")
            report.append("--------\n")
            report.append(f"System dependencies: {sum(1 for status in system_statuses if status.is_ok())}/{len(system_statuses)} OK\n")
            report.append(f"Python dependencies: {sum(1 for status in python_statuses if status.is_ok())}/{len(python_statuses)} OK\n")
            
            return "".join(report)
    
    def save_report(self, 
                   system_statuses: List[DependencyStatus], 
                   python_statuses: List[DependencyStatus],
                   output_file: str,
                   format: str = "text") -> bool:
        """
        Generate and save a dependency report to a file.
        
        Args:
            system_statuses: System dependency statuses
            python_statuses: Python dependency statuses
            output_file: Output file path
            format: Report format (text, json, markdown)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate report
            report = self.generate_report(system_statuses, python_statuses, format)
            
            # Save to file
            with open(output_file, 'w') as f:
                f.write(report)
                
            logger.info(f"Saved dependency report to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save dependency report: {e}")
            return False
    
    def get_missing_python_packages(self, python_statuses: List[DependencyStatus]) -> List[str]:
        """
        Get a list of missing Python packages.
        
        Args:
            python_statuses: Python dependency statuses
            
        Returns:
            List of package requirements in pip format
        """
        missing = []
        
        for status in python_statuses:
            if not status.installed and status.requirement.importance != "optional":
                # Add package with version requirement
                if status.requirement.required_version:
                    missing.append(f"{status.requirement.name}{status.requirement.required_version}")
                else:
                    missing.append(status.requirement.name)
                    
        return missing
    
    def generate_install_command(self, python_statuses: List[DependencyStatus]) -> Optional[str]:
        """
        Generate pip install command for missing packages.
        
        Args:
            python_statuses: Python dependency statuses
            
        Returns:
            pip install command or None if no missing packages
        """
        missing = self.get_missing_python_packages(python_statuses)
        
        if not missing:
            return None
            
        # Generate pip install command
        packages = " ".join(missing)
        return f"pip install {packages}"


# Convenience functions for command-line use

def check_dependencies(requirements_file: Optional[str] = None) -> int:
    """
    Check all dependencies and print report.
    
    Args:
        requirements_file: Path to requirements file
        
    Returns:
        Exit code (0 if all required dependencies are satisfied, 1 otherwise)
    """
    analyzer = DependencyAnalyzer(requirements_file)
    
    print("Checking dependencies...")
    system_statuses, python_statuses = analyzer.check_all_dependencies()
    
    # Print report
    report = analyzer.generate_report(system_statuses, python_statuses)
    print(report)
    
    # Generate install command if needed
    install_cmd = analyzer.generate_install_command(python_statuses)
    if install_cmd:
        print("\nMissing Python packages can be installed with:")
        print(f"  {install_cmd}")
    
    # Return exit code
    for status in system_statuses + python_statuses:
        if not status.is_ok() and status.requirement.importance == "required":
            return 1
            
    return 0

def save_dependency_report(output_file: str, 
                          format: str = "text",
                          requirements_file: Optional[str] = None) -> bool:
    """
    Generate and save a dependency report.
    
    Args:
        output_file: Output file path
        format: Report format (text, json, markdown)
        requirements_file: Path to requirements file
        
    Returns:
        True if successful, False otherwise
    """
    analyzer = DependencyAnalyzer(requirements_file)
    
    print(f"Generating dependency report in {format} format...")
    system_statuses, python_statuses = analyzer.check_all_dependencies()
    
    return analyzer.save_report(system_statuses, python_statuses, output_file, format)

def get_install_command(requirements_file: Optional[str] = None) -> Optional[str]:
    """
    Get pip install command for missing packages.
    
    Args:
        requirements_file: Path to requirements file
        
    Returns:
        pip install command or None if no missing packages
    """
    analyzer = DependencyAnalyzer(requirements_file)
    
    print("Checking Python dependencies...")
    _, python_statuses = analyzer.check_all_dependencies()
    
    return analyzer.generate_install_command(python_statuses)

def verify_specific_package(package_name: str, required_version: Optional[str] = None) -> bool:
    """
    Verify a specific Python package.
    
    Args:
        package_name: Package name
        required_version: Required version specification
        
    Returns:
        True if package is installed and compatible, False otherwise
    """
    req = DependencyRequirement(
        name=package_name,
        required_version=required_version or ""
    )
    
    analyzer = DependencyAnalyzer()
    status = analyzer.check_python_dependency(req)
    
    print(status)
    return status.is_ok()

def analyze_dependencies(source_dir: str) -> Dict[str, List[str]]:
    """ 
    Placeholder function for analyzing dependencies.
    Returns a dummy dictionary.
    """
    logger.info(f"Placeholder: Would analyze dependencies for {source_dir}")
    print(f"Simulating dependency analysis for {source_dir}...")
    # Simulate finding some common dependencies
    return {
        "python": ["qiskit>=0.34.0", "numpy>=1.20.0"],
        "system": []
    }

def main():
    """Main function for command-line use."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dependency Analyzer for Quantum CLI SDK")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check dependencies")
    check_parser.add_argument("--requirements", "-r", help="Path to requirements file")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate dependency report")
    report_parser.add_argument("--output", "-o", required=True, help="Output file path")
    report_parser.add_argument("--format", "-f", choices=["text", "json", "markdown"], default="text", help="Report format")
    report_parser.add_argument("--requirements", "-r", help="Path to requirements file")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Get install command for missing packages")
    install_parser.add_argument("--requirements", "-r", help="Path to requirements file")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a specific package")
    verify_parser.add_argument("package", help="Package name")
    verify_parser.add_argument("--version", "-v", help="Required version specification")
    
    args = parser.parse_args()
    
    if args.command == "check":
        sys.exit(check_dependencies(args.requirements))
        
    elif args.command == "report":
        if save_dependency_report(args.output, args.format, args.requirements):
            print(f"Dependency report saved to {args.output}")
            sys.exit(0)
        else:
            print("Failed to save dependency report")
            sys.exit(1)
            
    elif args.command == "install":
        install_cmd = get_install_command(args.requirements)
        if install_cmd:
            print(install_cmd)
            sys.exit(0)
        else:
            print("No missing packages found")
            sys.exit(0)
            
    elif args.command == "verify":
        if verify_specific_package(args.package, args.version):
            print(f"Package {args.package} OK")
            sys.exit(0)
        else:
            print(f"Package {args.package} verification failed")
            sys.exit(1)
            
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main() 