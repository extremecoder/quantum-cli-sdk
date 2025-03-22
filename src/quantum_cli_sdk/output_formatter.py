"""
Output formatter for Quantum CLI SDK.

This module provides consistent formatting of command output in various formats
(JSON, YAML, CSV, Text) for easier integration with other tools.
"""

import sys
import json
import csv
import logging
import io
from typing import Dict, List, Any, Optional, Union, TextIO
from enum import Enum
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Try to import yaml
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML not found. YAML output format will not be available.")

# Try to import tabulate for nice table formatting
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    logger.warning("Tabulate not found. Table formatting will be basic.")


class OutputFormat(Enum):
    """Output format options."""
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    MARKDOWN = "markdown"


class OutputFormatter:
    """Handles formatting and output of data in various formats."""
    
    def __init__(self, format: Union[str, OutputFormat] = OutputFormat.TEXT):
        """
        Initialize an output formatter.
        
        Args:
            format: Output format (text, json, yaml, csv, markdown)
        """
        if isinstance(format, str):
            try:
                self.format = OutputFormat(format.lower())
            except ValueError:
                logger.warning(f"Unknown format '{format}', using text")
                self.format = OutputFormat.TEXT
        else:
            self.format = format
    
    def format_data(self, data: Any) -> str:
        """
        Format data according to the selected output format.
        
        Args:
            data: Data to format (dict, list, or other serializable object)
            
        Returns:
            Formatted string
        """
        try:
            if self.format == OutputFormat.TEXT:
                return self._format_as_text(data)
            elif self.format == OutputFormat.JSON:
                return self._format_as_json(data)
            elif self.format == OutputFormat.YAML:
                return self._format_as_yaml(data)
            elif self.format == OutputFormat.CSV:
                return self._format_as_csv(data)
            elif self.format == OutputFormat.MARKDOWN:
                return self._format_as_markdown(data)
            else:
                logger.warning(f"Unsupported format: {self.format}, using text")
                return self._format_as_text(data)
        except Exception as e:
            logger.error(f"Error formatting data: {e}")
            return f"Error formatting data: {str(e)}"
    
    def _format_as_text(self, data: Any) -> str:
        """Format data as plain text."""
        if isinstance(data, dict):
            return self._format_dict_as_text(data)
        elif isinstance(data, list):
            return self._format_list_as_text(data)
        else:
            return str(data)
    
    def _format_dict_as_text(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Format a dictionary as plain text."""
        result = []
        for key, value in data.items():
            if isinstance(value, dict):
                result.append(f"{' ' * indent}{key}:")
                result.append(self._format_dict_as_text(value, indent + 2))
            elif isinstance(value, list):
                result.append(f"{' ' * indent}{key}:")
                result.append(self._format_list_as_text(value, indent + 2))
            else:
                result.append(f"{' ' * indent}{key}: {value}")
        return "\n".join(result)
    
    def _format_list_as_text(self, data: List[Any], indent: int = 0) -> str:
        """Format a list as plain text."""
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(self._format_dict_as_text(item, indent))
                result.append("")
            elif isinstance(item, list):
                result.append(self._format_list_as_text(item, indent))
            else:
                result.append(f"{' ' * indent}- {item}")
        return "\n".join(result)
    
    def _format_as_json(self, data: Any) -> str:
        """Format data as JSON."""
        return json.dumps(data, indent=2)
    
    def _format_as_yaml(self, data: Any) -> str:
        """Format data as YAML."""
        if not YAML_AVAILABLE:
            logger.warning("PyYAML not available, falling back to JSON")
            return self._format_as_json(data)
        
        return yaml.dump(data, default_flow_style=False)
    
    def _format_as_csv(self, data: Any) -> str:
        """Format data as CSV."""
        if not isinstance(data, (list, dict)):
            logger.warning("Cannot format non-tabular data as CSV, falling back to text")
            return self._format_as_text(data)
        
        output = io.StringIO()
        writer = None
        
        # Handle list of dictionaries (most common tabular format)
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            if not data:
                return ""
            
            # Get all possible field names
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            fieldnames = sorted(fieldnames)
            
            # Write CSV
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        # Handle dictionary of lists
        elif isinstance(data, dict) and all(isinstance(value, list) for value in data.values()):
            # Find the maximum length of any list
            max_length = max(len(value) for value in data.values())
            
            # Prepare rows
            rows = []
            for i in range(max_length):
                row = {}
                for key, value in data.items():
                    row[key] = value[i] if i < len(value) else ""
                rows.append(row)
            
            # Write CSV
            writer = csv.DictWriter(output, fieldnames=data.keys())
            writer.writeheader()
            writer.writerows(rows)
        
        # Handle simple dictionary
        elif isinstance(data, dict):
            writer = csv.writer(output)
            writer.writerow(["Key", "Value"])
            for key, value in data.items():
                writer.writerow([key, value])
        
        # Handle simple list
        elif isinstance(data, list):
            writer = csv.writer(output)
            for item in data:
                writer.writerow([item])
        
        if writer:
            return output.getvalue()
        else:
            logger.warning("Could not format data as CSV, falling back to text")
            return self._format_as_text(data)
    
    def _format_as_markdown(self, data: Any) -> str:
        """Format data as Markdown."""
        if isinstance(data, dict):
            return self._format_dict_as_markdown(data)
        elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return self._format_list_of_dicts_as_markdown_table(data)
        elif isinstance(data, list):
            return self._format_list_as_markdown(data)
        else:
            return f"```\n{str(data)}\n```"
    
    def _format_dict_as_markdown(self, data: Dict[str, Any], level: int = 1) -> str:
        """Format a dictionary as Markdown."""
        result = []
        for key, value in data.items():
            if isinstance(value, dict):
                result.append(f"{'#' * level} {key}")
                result.append(self._format_dict_as_markdown(value, level + 1))
            elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
                result.append(f"{'#' * level} {key}")
                result.append(self._format_list_of_dicts_as_markdown_table(value))
            elif isinstance(value, list):
                result.append(f"{'#' * level} {key}")
                result.append(self._format_list_as_markdown(value))
            else:
                result.append(f"**{key}**: {value}")
        return "\n\n".join(result)
    
    def _format_list_as_markdown(self, data: List[Any]) -> str:
        """Format a list as Markdown."""
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(self._format_dict_as_markdown(item, 2))
            elif isinstance(item, list):
                result.append(self._format_list_as_markdown(item))
            else:
                result.append(f"- {item}")
        return "\n".join(result)
    
    def _format_list_of_dicts_as_markdown_table(self, data: List[Dict[str, Any]]) -> str:
        """Format a list of dictionaries as a Markdown table."""
        if not data:
            return ""
        
        # Get all possible field names
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)
        
        # Create table header
        result = ["| " + " | ".join(fieldnames) + " |"]
        result.append("| " + " | ".join(["---"] * len(fieldnames)) + " |")
        
        # Create table rows
        for item in data:
            row = []
            for field in fieldnames:
                row.append(str(item.get(field, "")))
            result.append("| " + " | ".join(row) + " |")
        
        return "\n".join(result)


def format_output(data: Any, format: str = "text", file: Optional[TextIO] = None) -> str:
    """
    Format and optionally write data to file.
    
    Args:
        data: Data to format
        format: Output format (text, json, yaml, csv, markdown)
        file: File-like object to write to (optional)
        
    Returns:
        Formatted string
    """
    formatter = OutputFormatter(format)
    formatted = formatter.format_data(data)
    
    if file:
        print(formatted, file=file)
    
    return formatted


def save_output(data: Any, output_file: str, format: Optional[str] = None) -> bool:
    """
    Save formatted data to a file.
    
    Args:
        data: Data to format and save
        output_file: Path to output file
        format: Output format (text, json, yaml, csv, markdown)
                If None, format is inferred from file extension
                
    Returns:
        True if successful, False otherwise
    """
    try:
        # If format is not specified, try to infer from file extension
        if format is None:
            ext = Path(output_file).suffix.lower()
            if ext == '.json':
                format = 'json'
            elif ext in ('.yml', '.yaml'):
                format = 'yaml'
            elif ext == '.csv':
                format = 'csv'
            elif ext == '.md':
                format = 'markdown'
            else:
                format = 'text'
        
        formatter = OutputFormatter(format)
        formatted = formatter.format_data(data)
        
        with open(output_file, 'w') as f:
            f.write(formatted)
        
        logger.info(f"Output saved to {output_file} in {format} format")
        return True
    
    except Exception as e:
        logger.error(f"Error saving output to {output_file}: {e}")
        return False 