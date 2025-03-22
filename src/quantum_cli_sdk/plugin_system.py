"""
Plugin system for the Quantum CLI SDK.

This module provides a plugin system that allows third-party developers
to extend the CLI's functionality without altering the core codebase.
"""

import os
import sys
import logging
import importlib.util
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Type

# Set up logging
logger = logging.getLogger(__name__)

class PluginInterface(ABC):
    """Base class for all plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the plugin."""
        pass
    
    @property
    def description(self) -> str:
        """Get the description of the plugin."""
        return self.__doc__ or "No description available"


class CommandPlugin(PluginInterface):
    """Base class for command plugins."""
    
    def setup_parser(self, parser):
        """Set up the argument parser for this command.
        
        Args:
            parser: ArgumentParser instance for this command
        """
        pass
    
    @abstractmethod
    def execute(self, args) -> int:
        """Execute the command.
        
        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass


class TranspilerPlugin(PluginInterface):
    """Base class for transpiler plugins."""
    
    @abstractmethod
    def transform(self, circuit: Any, options: Optional[Dict[str, Any]] = None) -> Any:
        """Transform a quantum circuit.
        
        Args:
            circuit: The quantum circuit to transform
            options: Optional parameters for the transformation
            
        Returns:
            Transformed quantum circuit
        """
        pass


# Global registries for plugins
_command_plugins: Dict[str, CommandPlugin] = {}
_transpiler_plugins: Dict[str, Type] = {}


def register_command_plugin(plugin: CommandPlugin) -> None:
    """Register a command plugin.
    
    Args:
        plugin: The command plugin to register
    """
    name = plugin.name
    if name in _command_plugins:
        logger.warning(f"Command plugin '{name}' is already registered, overwriting")
    
    _command_plugins[name] = plugin
    logger.debug(f"Registered command plugin: {name}")


def register_transpiler_plugin(plugin_class: Type) -> None:
    """Register a transpiler plugin class.
    
    Args:
        plugin_class: The transpiler plugin class to register
    """
    name = plugin_class.__name__
    if name in _transpiler_plugins:
        logger.warning(f"Transpiler plugin '{name}' is already registered, overwriting")
    
    _transpiler_plugins[name] = plugin_class
    logger.debug(f"Registered transpiler plugin: {name}")


def get_registered_command_plugins() -> Dict[str, CommandPlugin]:
    """Get all registered command plugins.
    
    Returns:
        Dictionary of command name to plugin
    """
    return _command_plugins


def get_registered_transpiler_plugins() -> Dict[str, Type]:
    """Get all registered transpiler plugin classes.
    
    Returns:
        Dictionary of plugin name to class
    """
    return _transpiler_plugins


def discover_plugins(plugin_dirs: Optional[List[str]] = None) -> int:
    """Discover and load plugins from specified directories.
    
    Args:
        plugin_dirs: List of directory paths to look for plugins (defaults to current directory)
        
    Returns:
        Number of plugins loaded
    """
    if plugin_dirs is None:
        plugin_dirs = [os.getcwd()]
    
    # Normalize and expand paths
    normalized_dirs = []
    for path in plugin_dirs:
        # Expand ~ to home directory
        if path.startswith("~"):
            path = os.path.expanduser(path)
            
        # Convert to absolute path
        path = os.path.abspath(path)
        
        if os.path.isdir(path):
            normalized_dirs.append(path)
        else:
            logger.warning(f"Plugin directory not found: {path}")
    
    count = 0
    for plugin_dir in normalized_dirs:
        logger.debug(f"Searching for plugins in {plugin_dir}")
        
        # Only look for .py files directly in the directory
        for filename in os.listdir(plugin_dir):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            
            plugin_path = os.path.join(plugin_dir, filename)
            try:
                # Import the module
                module_name = os.path.splitext(filename)[0]
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                if spec is None or spec.loader is None:
                    logger.warning(f"Failed to load plugin: {plugin_path}")
                    continue
                
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # The plugin should register itself using register_command_plugin
                # or register_transpiler_plugin
                count += 1
                logger.info(f"Loaded plugin: {plugin_path}")
                
            except Exception as e:
                logger.error(f"Error loading plugin {plugin_path}: {e}")
    
    return count


def setup_plugin_subparsers(subparsers):
    """Set up subparsers for registered command plugins.
    
    Args:
        subparsers: Subparsers object from argparse
    """
    for name, plugin in _command_plugins.items():
        # Create a subparser for the command
        plugin_parser = subparsers.add_parser(name, help=plugin.description)
        
        # Let the plugin set up its own arguments
        plugin.setup_parser(plugin_parser)
        
        # Store the plugin reference for execution
        plugin_parser.set_defaults(plugin=plugin)


def execute_plugin_command(args) -> int:
    """Execute a plugin command.
    
    Args:
        args: Command arguments with a plugin attribute
        
    Returns:
        Exit code from the plugin
    """
    if hasattr(args, 'plugin') and isinstance(args.plugin, CommandPlugin):
        plugin = args.plugin
        try:
            return plugin.execute(args)
        except Exception as e:
            logger.error(f"Error executing plugin {plugin.name}: {e}")
            return 1
    
    return 0 