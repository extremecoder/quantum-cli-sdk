"""
Configuration system for the Quantum CLI SDK.

This module provides support for environment-specific configuration profiles
(dev, test, prod) and manages global settings for the Quantum CLI SDK.
"""

import os
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Set up logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "profile": "dev",
    "profiles": {
        "dev": {
            "simulator": "qiskit",
            "shots": 1024,
            "log_level": "DEBUG",
            "caching": True,
            "cache_dir": ".quantum_cache",
            "validate_circuits": True,
            "optimization_level": 1
        },
        "test": {
            "simulator": "qiskit",
            "shots": 4096,
            "log_level": "INFO",
            "caching": True,
            "cache_dir": ".quantum_cache",
            "validate_circuits": True,
            "optimization_level": 2
        },
        "prod": {
            "simulator": "qiskit",
            "shots": 8192,
            "log_level": "WARNING",
            "caching": False,
            "cache_dir": ".quantum_cache",
            "validate_circuits": True,
            "optimization_level": 3
        }
    },
    "quantum_providers": {
        "ibm": {
            "token": None,
            "hub": "ibm-q",
            "group": "open",
            "project": "main"
        },
        "aws": {
            "region": "us-east-1",
            "s3_bucket": None
        },
        "google": {
            "project_id": None
        }
    },
    "plugin_paths": [],
}

class ConfigManager:
    """Manages configuration profiles and settings for the Quantum CLI SDK."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._config = DEFAULT_CONFIG.copy()
        self._config_file = None
        self._active_profile = None
    
    def load_config(self, config_file: Optional[str] = None) -> bool:
        """Load configuration from file.
        
        Args:
            config_file: Path to configuration file (optional)
            
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        # Priority for config file location:
        # 1. Explicit path provided as argument
        # 2. Path specified in QUANTUM_CONFIG environment variable
        # 3. quantum_config.yaml/json in current directory
        # 4. .quantum_config.yaml/json in user's home directory
        
        if config_file is None:
            config_file = os.environ.get("QUANTUM_CONFIG")
            
        if config_file is None:
            # Look for config in current directory
            for ext in [".yaml", ".yml", ".json"]:
                if os.path.exists(f"quantum_config{ext}"):
                    config_file = f"quantum_config{ext}"
                    break
        
        if config_file is None:
            # Look for config in home directory
            home_dir = str(Path.home())
            for ext in [".yaml", ".yml", ".json"]:
                home_config = os.path.join(home_dir, f".quantum_config{ext}")
                if os.path.exists(home_config):
                    config_file = home_config
                    break
        
        if config_file is None:
            logger.debug("No configuration file found, using defaults")
            self._set_active_profile()
            return False
        
        try:
            # Load configuration from file
            with open(config_file, 'r') as f:
                if config_file.endswith(('.yaml', '.yml')):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # Update configuration with loaded data
            self._update_config(config_data)
            self._config_file = config_file
            # logger.info(f"Loaded configuration from {config_file}")
            
            # Set active profile
            self._set_active_profile()
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")
            self._set_active_profile()
            return False
    
    def _update_config(self, config_data: Dict[str, Any]) -> None:
        """Update configuration with new data.
        
        Args:
            config_data: New configuration data
        """
        # Helper function for deep dictionary update
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v
        
        deep_update(self._config, config_data)
    
    def _set_active_profile(self) -> None:
        """Set the active profile based on configuration or environment."""
        # Check environment variable first
        env_profile = os.environ.get("QUANTUM_PROFILE")
        if env_profile and env_profile in self._config["profiles"]:
            self._active_profile = env_profile
        else:
            # Use profile from config
            profile = self._config.get("profile", "dev")
            if profile in self._config["profiles"]:
                self._active_profile = profile
            else:
                # Fall back to dev profile
                self._active_profile = "dev"
                logger.warning(f"Profile '{profile}' not found, using 'dev' profile")
    
    def save_config(self, config_file: Optional[str] = None) -> bool:
        """Save current configuration to file.
        
        Args:
            config_file: Path to configuration file (optional)
            
        Returns:
            True if configuration was saved successfully, False otherwise
        """
        if config_file is None:
            config_file = self._config_file
        
        if config_file is None:
            config_file = "quantum_config.yaml"
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)
            
            # Save configuration to file
            with open(config_file, 'w') as f:
                if config_file.endswith(('.yaml', '.yml')):
                    yaml.dump(self._config, f, default_flow_style=False)
                else:
                    json.dump(self._config, f, indent=2)
            
            self._config_file = config_file
            logger.info(f"Saved configuration to {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration to {config_file}: {e}")
            return False
    
    def get_active_profile(self) -> str:
        """Get the name of the active profile.
        
        Returns:
            Name of the active profile
        """
        return self._active_profile
    
    def set_active_profile(self, profile: str) -> bool:
        """Set the active profile.
        
        Args:
            profile: Name of the profile to activate
            
        Returns:
            True if profile was activated, False if profile doesn't exist
        """
        if profile in self._config["profiles"]:
            self._active_profile = profile
            self._config["profile"] = profile
            logger.info(f"Activated profile: {profile}")
            return True
        else:
            logger.error(f"Profile '{profile}' not found")
            return False
    
    def get_profile_config(self, profile: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific profile or the active profile.
        
        Args:
            profile: Name of the profile (optional, defaults to active profile)
            
        Returns:
            Profile configuration
        """
        profile = profile or self._active_profile
        return self._config["profiles"].get(profile, {})
    
    def get_setting(self, key: str, default: Any = None, profile: Optional[str] = None) -> Any:
        """Get a configuration setting from the specified or active profile.
        
        Args:
            key: Setting key
            default: Default value if setting is not found
            profile: Profile name (optional, defaults to active profile)
            
        Returns:
            Setting value or default
        """
        profile_config = self.get_profile_config(profile)
        return profile_config.get(key, default)
    
    def set_setting(self, key: str, value: Any, profile: Optional[str] = None) -> None:
        """Set a configuration setting in the specified or active profile.
        
        Args:
            key: Setting key
            value: Setting value
            profile: Profile name (optional, defaults to active profile)
        """
        profile = profile or self._active_profile
        if profile in self._config["profiles"]:
            self._config["profiles"][profile][key] = value
        else:
            logger.error(f"Profile '{profile}' not found")
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific quantum provider.
        
        Args:
            provider: Quantum provider name (e.g., 'ibm', 'aws', 'google')
            
        Returns:
            Provider configuration
        """
        return self._config.get("quantum_providers", {}).get(provider, {})
    
    def set_provider_config(self, provider: str, key: str, value: Any) -> None:
        """Set a configuration setting for a specific quantum provider.
        
        Args:
            provider: Quantum provider name
            key: Setting key
            value: Setting value
        """
        if "quantum_providers" not in self._config:
            self._config["quantum_providers"] = {}
        
        if provider not in self._config["quantum_providers"]:
            self._config["quantum_providers"][provider] = {}
        
        self._config["quantum_providers"][provider][key] = value
    
    def get_all_profiles(self) -> List[str]:
        """Get a list of all available profiles.
        
        Returns:
            List of profile names
        """
        return list(self._config.get("profiles", {}).keys())
    
    def create_profile(self, profile: str, base_profile: Optional[str] = None) -> bool:
        """Create a new profile based on an existing one.
        
        Args:
            profile: Name of the new profile
            base_profile: Name of the profile to base the new one on (optional)
            
        Returns:
            True if profile was created, False if profile already exists
        """
        if profile in self._config["profiles"]:
            logger.error(f"Profile '{profile}' already exists")
            return False
        
        if base_profile and base_profile in self._config["profiles"]:
            # Copy base profile
            self._config["profiles"][profile] = self._config["profiles"][base_profile].copy()
        else:
            # Create empty profile or use dev as base
            base = "dev" if "dev" in self._config["profiles"] else None
            if base:
                self._config["profiles"][profile] = self._config["profiles"][base].copy()
            else:
                self._config["profiles"][profile] = {}
        
        logger.info(f"Created profile: {profile}")
        return True
    
    def delete_profile(self, profile: str) -> bool:
        """Delete a profile.
        
        Args:
            profile: Name of the profile to delete
            
        Returns:
            True if profile was deleted, False if profile doesn't exist
        """
        if profile not in self._config["profiles"]:
            logger.error(f"Profile '{profile}' not found")
            return False
        
        # Don't delete the active profile
        if profile == self._active_profile:
            logger.error(f"Cannot delete active profile: {profile}")
            return False
        
        del self._config["profiles"][profile]
        logger.info(f"Deleted profile: {profile}")
        return True
    
    def add_plugin_path(self, path: str) -> None:
        """Add a path to the list of plugin directories.
        
        Args:
            path: Directory path to add
        """
        if "plugin_paths" not in self._config:
            self._config["plugin_paths"] = []
        
        if path not in self._config["plugin_paths"]:
            self._config["plugin_paths"].append(path)
    
    def get_plugin_paths(self) -> List[str]:
        """Get the list of plugin directories.
        
        Returns:
            List of plugin directory paths
        """
        return self._config.get("plugin_paths", [])

# Global configuration manager instance
_config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    return _config_manager

def initialize_config(config_file: Optional[str] = None) -> ConfigManager:
    """Initialize the configuration system.
    
    Args:
        config_file: Path to configuration file (optional)
        
    Returns:
        ConfigManager instance
    """
    _config_manager.load_config(config_file)
    return _config_manager 