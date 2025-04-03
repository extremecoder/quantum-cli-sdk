#!/usr/bin/env python3
"""
Configuration Manager for setting and retrieving default parameters.

This module provides functionality to:
- Set default parameters for commands
- Retrieve default values
- Manage configuration profiles
- Import/export configurations
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration and default parameters for the Quantum CLI SDK."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or os.path.expanduser("~/.quantum-cli/config.json")
        self.config_dir = os.path.dirname(self.config_path)
        self.profiles_dir = os.path.join(self.config_dir, "profiles")
        
        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.profiles_dir, exist_ok=True)
        
        # Load default configuration
        self.config = self._load_config()
        
        # Initialize default configuration if not exists
        if not self.config:
            self._initialize_default_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # logger.info(f"Loaded configuration from {self.config_path}")
                return config
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def _save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _initialize_default_config(self) -> None:
        """Initialize default configuration values."""
        self.config = {
            "version": "1.0.0",
            "active_profile": "default",
            "default_parameters": {
                "run": {
                    "shots": 1024,
                    "simulator": "qiskit"
                },
                "simulate": {
                    "shots": 1024,
                    "simulator": "qiskit"
                },
                "optimize": {
                    "level": 1,
                    "target_gates": "default"
                },
                "mitigate": {
                    "method": "zne",
                    "noise_factor": 1.0
                },
                "estimate-resources": {
                    "detailed": False,
                    "target": "generic"
                },
                "circuit": {
                    "output_format": "qasm"
                },
                "template": {
                    "output_format": "qasm"
                },
                "generate-ir": {
                    "format": "qasm"
                },
                "validate": {
                    "strict": False
                },
                "security-scan": {
                    "level": "medium"
                },
                "calculate-cost": {
                    "currency": "USD",
                    "providers": ["ibm", "aws", "azure"]
                },
                "version": {
                    "repo_path": "~/quantum_repo"
                },
                "marketplace": {
                    "sort_by": "rating"
                },
                "share": {
                    "storage_path": "~/.quantum-cli/shared",
                    "permission": "read_only"
                },
                "jobs": {
                    "storage_path": "~/.quantum-cli/jobs",
                    "monitor_interval": 5
                },
                "compare": {
                    "output_format": "text"
                },
                "find-hardware": {
                    "criteria": "overall"
                }
            },
            "api_keys": {},
            "user": {
                "name": os.environ.get("USER", "unknown"),
                "email": ""
            },
            "preferences": {
                "output_format": "text",
                "verbosity": "normal",
                "auto_update": True
            }
        }
        
        self._save_config()
        logger.info("Initialized default configuration")
    
    def get_default_param(self, command: str, param_name: str) -> Any:
        """
        Get a default parameter value.
        
        Args:
            command: Command name
            param_name: Parameter name
            
        Returns:
            Parameter value or None if not found
        """
        try:
            return self.config.get("default_parameters", {}).get(command, {}).get(param_name)
        except Exception as e:
            logger.error(f"Failed to get default parameter {command}.{param_name}: {e}")
            return None
    
    def set_default_param(self, command: str, param_name: str, value: Any) -> bool:
        """
        Set a default parameter value.
        
        Args:
            command: Command name
            param_name: Parameter name
            value: Parameter value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if "default_parameters" not in self.config:
                self.config["default_parameters"] = {}
                
            if command not in self.config["default_parameters"]:
                self.config["default_parameters"][command] = {}
                
            self.config["default_parameters"][command][param_name] = value
            
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Failed to set default parameter {command}.{param_name}: {e}")
            return False
    
    def get_default_params(self, command: str) -> Dict[str, Any]:
        """
        Get all default parameters for a command.
        
        Args:
            command: Command name
            
        Returns:
            Dictionary of parameter names to values
        """
        return self.config.get("default_parameters", {}).get(command, {})
    
    def get_active_profile(self) -> str:
        """
        Get the name of the active profile.
        
        Returns:
            Profile name
        """
        return self.config.get("active_profile", "default")
    
    def set_active_profile(self, profile_name: str) -> bool:
        """
        Set the active profile.
        
        Args:
            profile_name: Profile name
            
        Returns:
            True if successful, False otherwise
        """
        # Check if profile exists
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        
        if not os.path.exists(profile_path):
            logger.error(f"Profile {profile_name} does not exist")
            return False
            
        self.config["active_profile"] = profile_name
        return self._save_config()
    
    def list_profiles(self) -> List[str]:
        """
        List available profiles.
        
        Returns:
            List of profile names
        """
        try:
            profiles = []
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith(".json"):
                    profiles.append(filename.replace(".json", ""))
            return profiles
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
            return []
    
    def create_profile(self, profile_name: str, 
                     default_params: Optional[Dict[str, Dict[str, Any]]] = None,
                     description: Optional[str] = None) -> bool:
        """
        Create a new profile.
        
        Args:
            profile_name: Profile name
            default_params: Default parameters for the profile
            description: Profile description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
            
            # Check if profile already exists
            if os.path.exists(profile_path):
                logger.error(f"Profile {profile_name} already exists")
                return False
                
            # Create profile
            profile = {
                "name": profile_name,
                "description": description or f"Configuration profile for {profile_name}",
                "created_at": str(datetime.datetime.now()),
                "default_parameters": default_params or self.config.get("default_parameters", {})
            }
            
            # Save profile
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
                
            logger.info(f"Created profile {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create profile {profile_name}: {e}")
            return False
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile.
        
        Args:
            profile_name: Profile name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Cannot delete default profile
            if profile_name == "default":
                logger.error("Cannot delete default profile")
                return False
                
            profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
            
            # Check if profile exists
            if not os.path.exists(profile_path):
                logger.error(f"Profile {profile_name} does not exist")
                return False
                
            # Delete profile
            os.remove(profile_path)
            
            # If active profile was deleted, switch to default
            if self.config.get("active_profile") == profile_name:
                self.config["active_profile"] = "default"
                self._save_config()
                
            logger.info(f"Deleted profile {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete profile {profile_name}: {e}")
            return False
    
    def get_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Get a profile.
        
        Args:
            profile_name: Profile name
            
        Returns:
            Profile dictionary
        """
        try:
            profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
            
            if not os.path.exists(profile_path):
                logger.error(f"Profile {profile_name} does not exist")
                return {}
                
            with open(profile_path, 'r') as f:
                profile = json.load(f)
                
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get profile {profile_name}: {e}")
            return {}
    
    def load_profile(self, profile_name: str) -> bool:
        """
        Load a profile into the current configuration.
        
        Args:
            profile_name: Profile name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            profile = self.get_profile(profile_name)
            
            if not profile:
                return False
                
            # Update default parameters
            self.config["default_parameters"] = profile.get("default_parameters", {})
            
            # Set active profile
            self.config["active_profile"] = profile_name
            
            # Save configuration
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Failed to load profile {profile_name}: {e}")
            return False
    
    def export_config(self, output_path: str) -> bool:
        """
        Export configuration to a file.
        
        Args:
            output_path: Path to export configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a deep copy of the config
            import copy
            export_config = copy.deepcopy(self.config)
            
            # Remove sensitive data
            if "api_keys" in export_config:
                del export_config["api_keys"]
                
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(export_config, f, indent=2)
                
            logger.info(f"Exported configuration to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, input_path: str, overwrite: bool = False) -> bool:
        """
        Import configuration from a file.
        
        Args:
            input_path: Path to import configuration from
            overwrite: Whether to overwrite existing configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read configuration
            with open(input_path, 'r') as f:
                import_config = json.load(f)
                
            # Validate configuration
            if "version" not in import_config:
                logger.error("Invalid configuration file: missing version")
                return False
                
            # Backup current configuration
            backup_path = f"{self.config_path}.bak"
            with open(backup_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            # Merge or overwrite
            if overwrite:
                # Keep sensitive data
                if "api_keys" in self.config:
                    import_config["api_keys"] = self.config["api_keys"]
                    
                self.config = import_config
            else:
                # Merge configurations
                self._merge_configs(import_config)
                
            # Save configuration
            result = self._save_config()
            
            if result:
                logger.info(f"Imported configuration from {input_path}")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def _merge_configs(self, import_config: Dict[str, Any]) -> None:
        """
        Merge imported configuration with current configuration.
        
        Args:
            import_config: Imported configuration
        """
        # Merge default parameters
        if "default_parameters" in import_config:
            if "default_parameters" not in self.config:
                self.config["default_parameters"] = {}
                
            for command, params in import_config["default_parameters"].items():
                if command not in self.config["default_parameters"]:
                    self.config["default_parameters"][command] = {}
                    
                for param_name, value in params.items():
                    self.config["default_parameters"][command][param_name] = value
                    
        # Merge preferences
        if "preferences" in import_config:
            if "preferences" not in self.config:
                self.config["preferences"] = {}
                
            for key, value in import_config["preferences"].items():
                self.config["preferences"][key] = value
                
        # Merge user info (except sensitive data)
        if "user" in import_config:
            if "user" not in self.config:
                self.config["user"] = {}
                
            for key, value in import_config["user"].items():
                if key not in ["password", "token"]:
                    self.config["user"][key] = value
    
    def set_api_key(self, provider: str, api_key: str) -> bool:
        """
        Set an API key for a provider.
        
        Args:
            provider: Provider name
            api_key: API key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if "api_keys" not in self.config:
                self.config["api_keys"] = {}
                
            self.config["api_keys"][provider] = api_key
            
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Failed to set API key for {provider}: {e}")
            return False
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get an API key for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            API key or None if not found
        """
        try:
            return self.config.get("api_keys", {}).get(provider)
        except Exception as e:
            logger.error(f"Failed to get API key for {provider}: {e}")
            return None
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value
        """
        return self.config.get("preferences", {}).get(key, default)
    
    def set_preference(self, key: str, value: Any) -> bool:
        """
        Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if "preferences" not in self.config:
                self.config["preferences"] = {}
                
            self.config["preferences"][key] = value
            
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Failed to set preference {key}: {e}")
            return False


# Convenience functions for command-line use

def get_config_value(path: str, default: Any = None) -> Any:
    """
    Get a configuration value by path.
    
    Args:
        path: Path in the form "section.key" or "section.subsection.key"
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    manager = ConfigManager()
    
    # Split path into components
    components = path.split('.')
    
    # Navigate through configuration
    value = manager.config
    try:
        for component in components:
            value = value.get(component, {})
            
        # Check if we reached the end
        if value == {}:
            return default
            
        return value
        
    except Exception:
        return default

def set_config_value(path: str, value: Any) -> bool:
    """
    Set a configuration value by path.
    
    Args:
        path: Path in the form "section.key" or "section.subsection.key"
        value: Value to set
        
    Returns:
        True if successful, False otherwise
    """
    manager = ConfigManager()
    
    # Split path into components
    components = path.split('.')
    
    # Navigate through configuration
    config = manager.config
    parent = config
    
    try:
        # Traverse to the parent of the target
        for i, component in enumerate(components[:-1]):
            if component not in parent:
                parent[component] = {}
            parent = parent[component]
            
        # Set the value
        parent[components[-1]] = value
        
        # Save configuration
        return manager._save_config()
        
    except Exception as e:
        logger.error(f"Failed to set configuration value at {path}: {e}")
        return False

def get_default_param(command: str, param_name: str, default: Any = None) -> Any:
    """
    Get a default parameter value.
    
    Args:
        command: Command name
        param_name: Parameter name
        default: Default value if not found
        
    Returns:
        Parameter value
    """
    manager = ConfigManager()
    value = manager.get_default_param(command, param_name)
    return value if value is not None else default

def set_default_param(command: str, param_name: str, value: Any) -> bool:
    """
    Set a default parameter value.
    
    Args:
        command: Command name
        param_name: Parameter name
        value: Parameter value
        
    Returns:
        True if successful, False otherwise
    """
    manager = ConfigManager()
    return manager.set_default_param(command, param_name, value)

def list_profiles() -> List[str]:
    """
    List available profiles.
    
    Returns:
        List of profile names
    """
    manager = ConfigManager()
    return manager.list_profiles()

def create_profile(profile_name: str, description: Optional[str] = None) -> bool:
    """
    Create a new profile.
    
    Args:
        profile_name: Profile name
        description: Profile description
        
    Returns:
        True if successful, False otherwise
    """
    manager = ConfigManager()
    return manager.create_profile(profile_name, description=description)

def load_profile(profile_name: str) -> bool:
    """
    Load a profile.
    
    Args:
        profile_name: Profile name
        
    Returns:
        True if successful, False otherwise
    """
    manager = ConfigManager()
    return manager.load_profile(profile_name)

def export_config(output_path: str) -> bool:
    """
    Export configuration to a file.
    
    Args:
        output_path: Path to export configuration
        
    Returns:
        True if successful, False otherwise
    """
    manager = ConfigManager()
    return manager.export_config(output_path)

def import_config(input_path: str, overwrite: bool = False) -> bool:
    """
    Import configuration from a file.
    
    Args:
        input_path: Path to import configuration from
        overwrite: Whether to overwrite existing configuration
        
    Returns:
        True if successful, False otherwise
    """
    manager = ConfigManager()
    return manager.import_config(input_path, overwrite)

def print_config() -> None:
    """Print the current configuration."""
    manager = ConfigManager()
    
    # Create a copy without sensitive data
    import copy
    config = copy.deepcopy(manager.config)
    
    if "api_keys" in config:
        for provider in config["api_keys"]:
            config["api_keys"][provider] = "********"
    
    import json
    print(json.dumps(config, indent=2))

def print_default_params(command: Optional[str] = None) -> None:
    """
    Print default parameters.
    
    Args:
        command: Command to print parameters for, or None for all commands
    """
    manager = ConfigManager()
    
    if command:
        params = manager.get_default_params(command)
        print(f"Default parameters for command '{command}':")
        for param_name, value in params.items():
            print(f"  {param_name}: {value}")
    else:
        default_params = manager.config.get("default_parameters", {})
        print("Default parameters:")
        for command, params in default_params.items():
            print(f"\n{command}:")
            for param_name, value in params.items():
                print(f"  {param_name}: {value}")

# Add datetime import for create_profile function
import datetime 