"""
Logging configuration for Quantum CLI SDK.

This module provides enhanced logging capabilities with fine-grained control
over logging levels and destinations.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import json

# Default log levels
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_FILE_LEVEL = logging.DEBUG
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Module-specific loggers
LOGGER_MODULES = {
    "circuit": "quantum_cli_sdk.quantum_circuit",
    "simulation": "quantum_cli_sdk.simulator",
    "transpiler": "quantum_cli_sdk.transpiler",
    "visualization": "quantum_cli_sdk.visualizer",
    "interactive": "quantum_cli_sdk.interactive",
    "hardware": "quantum_cli_sdk.hardware_selector",
    "jobs": "quantum_cli_sdk.job_management",
    "config": "quantum_cli_sdk.config",
    "plugins": "quantum_cli_sdk.plugin_system",
    "versioning": "quantum_cli_sdk.versioning",
    "marketplace": "quantum_cli_sdk.marketplace",
    "sharing": "quantum_cli_sdk.sharing",
    "comparison": "quantum_cli_sdk.circuit_comparison",
    "dependencies": "quantum_cli_sdk.dependency_analyzer",
}


class LoggerManager:
    """Manages and configures logging for Quantum CLI SDK."""
    
    def __init__(self):
        """Initialize the logger manager."""
        self.root_logger = logging.getLogger("quantum_cli_sdk")
        self.handlers = {}
        self.module_levels = {}
        self.is_configured = False
    
    def configure(self, 
                 console_level: Union[str, int] = DEFAULT_CONSOLE_LEVEL,
                 file_level: Union[str, int] = DEFAULT_FILE_LEVEL,
                 log_file: Optional[str] = None,
                 format_str: str = DEFAULT_LOG_FORMAT,
                 date_format: str = DEFAULT_DATE_FORMAT,
                 module_levels: Optional[Dict[str, Union[str, int]]] = None,
                 rotating_file: bool = False,
                 max_bytes: int = 10 * 1024 * 1024,  # 10 MB
                 backup_count: int = 5,
                 ) -> None:
        """
        Configure logging system.
        
        Args:
            console_level: Logging level for console output
            file_level: Logging level for file output
            log_file: Path to log file (None for no file logging)
            format_str: Log format string
            date_format: Date format string
            module_levels: Dict of module-specific log levels
            rotating_file: Whether to use a rotating file handler
            max_bytes: Maximum file size for rotating handler
            backup_count: Number of backup files to keep
        """
        # Reset existing handlers
        self._reset_handlers()
        
        # Configure root logger
        self.root_logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter
        
        # Convert string levels to integers if needed
        if isinstance(console_level, str):
            console_level = self._get_level_from_string(console_level)
        
        if isinstance(file_level, str):
            file_level = self._get_level_from_string(file_level)
        
        # Create formatter
        formatter = logging.Formatter(format_str, date_format)
        
        # Console handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(console_level)
        console.setFormatter(formatter)
        self.root_logger.addHandler(console)
        self.handlers["console"] = console
        
        # File handler (if log_file is specified)
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            if rotating_file:
                file_handler = RotatingFileHandler(
                    log_file, maxBytes=max_bytes, backupCount=backup_count
                )
            else:
                file_handler = logging.FileHandler(log_file)
            
            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            self.root_logger.addHandler(file_handler)
            self.handlers["file"] = file_handler
        
        # Configure module-specific loggers
        if module_levels:
            for module, level in module_levels.items():
                self.set_module_level(module, level)
        
        self.is_configured = True
        self.root_logger.debug("Logging configured")
    
    def _reset_handlers(self) -> None:
        """Remove all handlers from the root logger."""
        for handler in list(self.root_logger.handlers):
            self.root_logger.removeHandler(handler)
        self.handlers = {}
    
    def _get_level_from_string(self, level_str: str) -> int:
        """Convert string log level to numeric value."""
        level_str = level_str.upper()
        level_map = {
            "CRITICAL": logging.CRITICAL,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
            "NOTSET": logging.NOTSET,
        }
        return level_map.get(level_str, logging.INFO)
    
    def set_console_level(self, level: Union[str, int]) -> None:
        """
        Set the console logging level.
        
        Args:
            level: Logging level (string or integer)
        """
        if isinstance(level, str):
            level = self._get_level_from_string(level)
        
        if "console" in self.handlers:
            self.handlers["console"].setLevel(level)
    
    def set_file_level(self, level: Union[str, int]) -> None:
        """
        Set the file logging level.
        
        Args:
            level: Logging level (string or integer)
        """
        if isinstance(level, str):
            level = self._get_level_from_string(level)
        
        if "file" in self.handlers:
            self.handlers["file"].setLevel(level)
    
    def set_module_level(self, module: str, level: Union[str, int]) -> None:
        """
        Set the logging level for a specific module.
        
        Args:
            module: Module name or identifier
            level: Logging level (string or integer)
        """
        if isinstance(level, str):
            level = self._get_level_from_string(level)
        
        # Get the fully qualified module name
        if module in LOGGER_MODULES:
            module_name = LOGGER_MODULES[module]
        else:
            module_name = module
        
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
        self.module_levels[module] = level
    
    def add_file_handler(self, 
                        log_file: str, 
                        level: Union[str, int] = DEFAULT_FILE_LEVEL,
                        format_str: str = DEFAULT_LOG_FORMAT,
                        date_format: str = DEFAULT_DATE_FORMAT,
                        rotating: bool = False,
                        max_bytes: int = 10 * 1024 * 1024,
                        backup_count: int = 5,
                        ) -> None:
        """
        Add a file handler to the logger.
        
        Args:
            log_file: Path to log file
            level: Logging level
            format_str: Log format string
            date_format: Date format string
            rotating: Whether to use a rotating file handler
            max_bytes: Maximum file size for rotating handler
            backup_count: Number of backup files to keep
        """
        if isinstance(level, str):
            level = self._get_level_from_string(level)
        
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        handler_name = f"file_{len([h for h in self.handlers if h.startswith('file')])}"
        
        formatter = logging.Formatter(format_str, date_format)
        
        if rotating:
            handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
        else:
            handler = logging.FileHandler(log_file)
        
        handler.setLevel(level)
        handler.setFormatter(formatter)
        self.root_logger.addHandler(handler)
        self.handlers[handler_name] = handler
    
    def add_time_rotating_file_handler(self,
                                     log_file: str,
                                     level: Union[str, int] = DEFAULT_FILE_LEVEL,
                                     format_str: str = DEFAULT_LOG_FORMAT,
                                     date_format: str = DEFAULT_DATE_FORMAT,
                                     when: str = 'midnight',
                                     backup_count: int = 7,
                                     ) -> None:
        """
        Add a time-based rotating file handler to the logger.
        
        Args:
            log_file: Path to log file
            level: Logging level
            format_str: Log format string
            date_format: Date format string
            when: Rotation time (midnight, h, d, w0-w6)
            backup_count: Number of backup files to keep
        """
        if isinstance(level, str):
            level = self._get_level_from_string(level)
        
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        handler_name = f"time_file_{len([h for h in self.handlers if h.startswith('time_file')])}"
        
        formatter = logging.Formatter(format_str, date_format)
        
        handler = TimedRotatingFileHandler(
            log_file, when=when, backupCount=backup_count
        )
        
        handler.setLevel(level)
        handler.setFormatter(formatter)
        self.root_logger.addHandler(handler)
        self.handlers[handler_name] = handler
    
    def get_module_logger(self, module: str) -> logging.Logger:
        """
        Get a logger for a specific module.
        
        Args:
            module: Module name or identifier
            
        Returns:
            Logger for the module
        """
        if module in LOGGER_MODULES:
            module_name = LOGGER_MODULES[module]
        else:
            module_name = module
        
        return logging.getLogger(module_name)
    
    def save_config(self, config_file: str) -> bool:
        """
        Save current logging configuration to a file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config = {
                "console_level": self._get_level_name(self.handlers.get("console", DEFAULT_CONSOLE_LEVEL)),
                "file_handlers": [],
                "module_levels": {k: self._get_level_name(v) for k, v in self.module_levels.items()},
            }
            
            for name, handler in self.handlers.items():
                if name.startswith("file") or name.startswith("time_file"):
                    if hasattr(handler, "baseFilename"):
                        handler_config = {
                            "file": handler.baseFilename,
                            "level": self._get_level_name(handler.level),
                            "rotating": isinstance(handler, RotatingFileHandler),
                        }
                        
                        if isinstance(handler, RotatingFileHandler):
                            handler_config["max_bytes"] = handler.maxBytes
                            handler_config["backup_count"] = handler.backupCount
                        
                        if isinstance(handler, TimedRotatingFileHandler):
                            handler_config["when"] = handler.when
                        
                        config["file_handlers"].append(handler_config)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        
        except Exception as e:
            self.root_logger.error(f"Error saving logging configuration: {e}")
            return False
    
    def load_config(self, config_file: str) -> bool:
        """
        Load logging configuration from a file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Reset handlers
            self._reset_handlers()
            
            # Configure console handler
            console_level = config.get("console_level", "INFO")
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(self._get_level_from_string(console_level))
            console.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT))
            self.root_logger.addHandler(console)
            self.handlers["console"] = console
            
            # Configure file handlers
            for handler_config in config.get("file_handlers", []):
                log_file = handler_config.get("file")
                level = handler_config.get("level", "DEBUG")
                rotating = handler_config.get("rotating", False)
                
                if rotating:
                    max_bytes = handler_config.get("max_bytes", 10 * 1024 * 1024)
                    backup_count = handler_config.get("backup_count", 5)
                    
                    if "when" in handler_config:
                        # Time-based rotating file
                        self.add_time_rotating_file_handler(
                            log_file, level, 
                            backup_count=backup_count,
                            when=handler_config.get("when", "midnight")
                        )
                    else:
                        # Size-based rotating file
                        self.add_file_handler(
                            log_file, level, 
                            rotating=True,
                            max_bytes=max_bytes,
                            backup_count=backup_count
                        )
                else:
                    # Regular file handler
                    self.add_file_handler(log_file, level)
            
            # Configure module-specific loggers
            for module, level in config.get("module_levels", {}).items():
                self.set_module_level(module, level)
            
            self.is_configured = True
            self.root_logger.debug("Logging configuration loaded from file")
            return True
        
        except Exception as e:
            # Set up basic logging as fallback
            self.configure()
            self.root_logger.error(f"Error loading logging configuration: {e}")
            return False
    
    def _get_level_name(self, level: Union[int, logging.Handler]) -> str:
        """Get the string name for a log level or handler."""
        if isinstance(level, logging.Handler):
            level = level.level
        return logging.getLevelName(level)


# Create singleton instance
logger_manager = LoggerManager()


def configure_logging(console_level: Union[str, int] = DEFAULT_CONSOLE_LEVEL,
                    file_level: Union[str, int] = DEFAULT_FILE_LEVEL,
                    log_file: Optional[str] = None,
                    **kwargs) -> None:
    """
    Configure the logging system.
    
    Args:
        console_level: Logging level for console output
        file_level: Logging level for file output
        log_file: Path to log file (None for no file logging)
        **kwargs: Additional configuration options
    """
    logger_manager.configure(console_level, file_level, log_file, **kwargs)


def get_logger(module: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        module: Module name or identifier
        
    Returns:
        Logger for the module
    """
    return logger_manager.get_module_logger(module)


def set_level(module: str, level: Union[str, int]) -> None:
    """
    Set the logging level for a specific module.
    
    Args:
        module: Module name or identifier
        level: Logging level (string or integer)
    """
    logger_manager.set_module_level(module, level)


def set_console_level(level: Union[str, int]) -> None:
    """
    Set the console logging level.
    
    Args:
        level: Logging level (string or integer)
    """
    logger_manager.set_console_level(level)


def set_file_level(level: Union[str, int]) -> None:
    """
    Set the file logging level.
    
    Args:
        level: Logging level (string or integer)
    """
    logger_manager.set_file_level(level)


def add_log_file(log_file: str, level: Union[str, int] = DEFAULT_FILE_LEVEL, **kwargs) -> None:
    """
    Add a log file to the logging system.
    
    Args:
        log_file: Path to log file
        level: Logging level
        **kwargs: Additional configuration options
    """
    logger_manager.add_file_handler(log_file, level, **kwargs)


def add_rotating_log_file(log_file: str, 
                         level: Union[str, int] = DEFAULT_FILE_LEVEL,
                         max_bytes: int = 10 * 1024 * 1024,
                         backup_count: int = 5,
                         **kwargs) -> None:
    """
    Add a rotating log file to the logging system.
    
    Args:
        log_file: Path to log file
        level: Logging level
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep
        **kwargs: Additional configuration options
    """
    logger_manager.add_file_handler(
        log_file, level, rotating=True, max_bytes=max_bytes, backup_count=backup_count, **kwargs
    )


def add_daily_log_file(log_file: str,
                      level: Union[str, int] = DEFAULT_FILE_LEVEL,
                      backup_count: int = 7,
                      **kwargs) -> None:
    """
    Add a daily rotating log file to the logging system.
    
    Args:
        log_file: Path to log file
        level: Logging level
        backup_count: Number of backup files to keep
        **kwargs: Additional configuration options
    """
    logger_manager.add_time_rotating_file_handler(
        log_file, level, when='midnight', backup_count=backup_count, **kwargs
    )


def save_logging_config(config_file: str) -> bool:
    """
    Save current logging configuration to a file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        True if successful, False otherwise
    """
    return logger_manager.save_config(config_file)


def load_logging_config(config_file: str) -> bool:
    """
    Load logging configuration from a file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        True if successful, False otherwise
    """
    return logger_manager.load_config(config_file) 