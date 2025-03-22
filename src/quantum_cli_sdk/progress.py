"""
Rich progress indicators for Quantum CLI SDK.

This module provides progress bars and spinners for long-running operations,
with detailed status reporting and customization options.
"""

import sys
import time
import threading
from typing import Optional, Dict, Any, Callable, List, Union, Tuple
from enum import Enum
from contextlib import contextmanager

class ProgressStyle(Enum):
    """Progress bar style options."""
    BASIC = 1        # Simple ASCII progress bar
    UNICODE = 2      # Progress bar with Unicode block characters
    DETAILED = 3     # Progress bar with detailed statistics
    SPINNER = 4      # Spinner for indeterminate progress


class ProgressIndicator:
    """Base class for progress indicators."""
    
    def __init__(self, 
                 total: Optional[int] = None, 
                 desc: str = "", 
                 unit: str = "it",
                 file = sys.stderr):
        """
        Initialize a progress indicator.
        
        Args:
            total: Total number of steps (None for indeterminate progress)
            desc: Description of the progress operation
            unit: Unit for progress counting (e.g., "it", "MB", "files")
            file: File-like object to write to
        """
        self.total = total
        self.desc = desc
        self.unit = unit
        self.file = file
        self.n = 0
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.closed = False
    
    def update(self, n: int = 1) -> None:
        """
        Update the progress indicator.
        
        Args:
            n: Number of steps to increment
        """
        self.n += n
        self.last_update_time = time.time()
        self._draw()
    
    def set_description(self, desc: str) -> None:
        """
        Set the description text.
        
        Args:
            desc: New description
        """
        self.desc = desc
        self._draw()
    
    def set_total(self, total: int) -> None:
        """
        Set the total number of steps.
        
        Args:
            total: New total number of steps
        """
        self.total = total
        self._draw()
    
    def close(self) -> None:
        """Close the progress indicator."""
        if not self.closed:
            self._finalize()
            self.closed = True
    
    def _draw(self) -> None:
        """Draw the progress indicator."""
        raise NotImplementedError("Subclasses must implement _draw()")
    
    def _finalize(self) -> None:
        """Finalize the progress indicator."""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ProgressBar(ProgressIndicator):
    """Progress bar for displaying deterministic progress."""
    
    def __init__(self, 
                 total: int, 
                 desc: str = "", 
                 unit: str = "it",
                 bar_width: int = 40,
                 style: ProgressStyle = ProgressStyle.UNICODE,
                 stats: bool = True,
                 file = sys.stderr):
        """
        Initialize a progress bar.
        
        Args:
            total: Total number of steps
            desc: Description of the progress operation
            unit: Unit for progress counting
            bar_width: Width of the progress bar in characters
            style: Style of the progress bar
            stats: Whether to show statistics
            file: File-like object to write to
        """
        super().__init__(total, desc, unit, file)
        self.bar_width = bar_width
        self.style = style
        self.stats = stats
        
        # Choose characters based on style
        if style == ProgressStyle.BASIC:
            self.bar_fill = '#'
            self.bar_empty = ' '
            self.bar_left = '['
            self.bar_right = ']'
        else:  # Unicode
            self.bar_fill = '█'
            self.bar_empty = '░'
            self.bar_left = '|'
            self.bar_right = '|'
        
        # Initial draw
        self._draw()
    
    def _get_stats(self) -> str:
        """Get progress statistics as a string."""
        elapsed = time.time() - self.start_time
        
        if self.total is not None and self.n > 0:
            rate = self.n / elapsed
            remaining = (self.total - self.n) / rate if rate > 0 else 0
            return f"{self.n}/{self.total} [{self.n/self.total:.1%}] {rate:.2f}{self.unit}/s elapsed: {int(elapsed)}s remaining: {int(remaining)}s"
        else:
            return f"{self.n} {rate:.2f}{self.unit}/s elapsed: {int(elapsed)}s"
    
    def _draw(self) -> None:
        """Draw the progress bar."""
        if self.closed:
            return
        
        if self.total is not None:
            # Calculate progress fraction
            frac = min(1.0, self.n / self.total)
            
            # Build the bar
            filled_len = int(self.bar_width * frac)
            bar = self.bar_fill * filled_len + self.bar_empty * (self.bar_width - filled_len)
            
            # Format percentage and counts
            percent = f"{frac * 100:.1f}%"
            counts = f"{self.n}/{self.total}"
            
            if self.stats:
                stats = self._get_stats()
                line = f"\r{self.desc} {self.bar_left}{bar}{self.bar_right} {percent} {stats}"
            else:
                line = f"\r{self.desc} {self.bar_left}{bar}{self.bar_right} {percent} ({counts})"
        else:
            bar = self.bar_fill * self.bar_width
            line = f"\r{self.desc} {self.bar_left}{bar}{self.bar_right} {self.n} {self.unit}"
        
        print(line, end="", file=self.file)
        self.file.flush()
    
    def _finalize(self) -> None:
        """Finalize the progress bar."""
        if self.total is not None:
            self.n = self.total
            self._draw()
        print(file=self.file)  # New line after progress bar


class Spinner(ProgressIndicator):
    """Spinner for displaying indeterminate progress."""
    
    def __init__(self, 
                 desc: str = "", 
                 unit: str = "it",
                 fps: int = 10,
                 style: str = "dots",
                 file = sys.stderr):
        """
        Initialize a spinner.
        
        Args:
            desc: Description of the progress operation
            unit: Unit for progress counting
            fps: Frames per second for spinner animation
            style: Spinner style (dots, arrows, braille, bouncing)
            file: File-like object to write to
        """
        super().__init__(None, desc, unit, file)
        self.fps = fps
        self.update_interval = 1.0 / fps
        self.last_frame_time = time.time()
        self.frame_idx = 0
        
        # Choose spinner frames based on style
        spinner_styles = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "braille": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
            "bouncing": [".  ", ".. ", "...", " ..", "  .", " .."]
        }
        
        self.frames = spinner_styles.get(style, spinner_styles["dots"])
        
        # Initialize thread for animation
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
    
    def _spin(self) -> None:
        """Run the spinner animation."""
        while not self.stop_event.is_set():
            current_time = time.time()
            if current_time - self.last_frame_time >= self.update_interval:
                self.frame_idx = (self.frame_idx + 1) % len(self.frames)
                self._draw()
                self.last_frame_time = current_time
            time.sleep(0.01)  # Short sleep to avoid CPU hogging
    
    def _draw(self) -> None:
        """Draw the spinner frame."""
        if self.closed:
            return
        
        frame = self.frames[self.frame_idx]
        elapsed = time.time() - self.start_time
        
        if self.n > 0:
            stats = f"{self.n} {self.unit}, {elapsed:.1f}s"
        else:
            stats = f"{elapsed:.1f}s"
        
        line = f"\r{frame} {self.desc} {stats}"
        print(line, end="", file=self.file)
        self.file.flush()
    
    def _finalize(self) -> None:
        """Finalize the spinner."""
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(timeout=0.1)
        print(file=self.file)  # New line after spinner
    
    def close(self) -> None:
        """Close the spinner."""
        self.stop_event.set()
        super().close()


class DetailedProgressBar(ProgressBar):
    """Progress bar with detailed status information."""
    
    def __init__(self, 
                 total: int, 
                 desc: str = "", 
                 unit: str = "it",
                 bar_width: int = 40,
                 style: ProgressStyle = ProgressStyle.DETAILED,
                 file = sys.stderr):
        """
        Initialize a detailed progress bar.
        
        Args:
            total: Total number of steps
            desc: Description of the progress operation
            unit: Unit for progress counting
            bar_width: Width of the progress bar in characters
            style: Style of the progress bar
            file: File-like object to write to
        """
        super().__init__(total, desc, unit, bar_width, style, True, file)
        self.status_text = ""
        self.substeps: Dict[str, Tuple[int, int]] = {}  # name -> (current, total)
    
    def set_status(self, status: str) -> None:
        """
        Set the current status text.
        
        Args:
            status: Status text to display
        """
        self.status_text = status
        self._draw()
    
    def update_substep(self, name: str, n: int = 1, total: Optional[int] = None) -> None:
        """
        Update a named substep.
        
        Args:
            name: Name of the substep
            n: Current progress of the substep
            total: Total steps for this substep
        """
        if name in self.substeps:
            current, substep_total = self.substeps[name]
            if total is not None:
                substep_total = total
            self.substeps[name] = (current + n, substep_total)
        else:
            if total is None:
                total = 100  # Default total
            self.substeps[name] = (n, total)
        
        self._draw()
    
    def _format_substeps(self) -> str:
        """Format the substeps for display."""
        if not self.substeps:
            return ""
        
        result = []
        for name, (current, total) in self.substeps.items():
            if total > 0:
                percentage = current / total * 100
                result.append(f"{name}: {current}/{total} [{percentage:.1f}%]")
            else:
                result.append(f"{name}: {current}")
        
        return ", ".join(result)
    
    def _draw(self) -> None:
        """Draw the detailed progress bar."""
        if self.closed:
            return
        
        # Call parent draw method
        super()._draw()
        
        # Add additional status information
        if self.status_text or self.substeps:
            substeps_str = self._format_substeps()
            status_line = f"\n  Status: {self.status_text}"
            if substeps_str:
                status_line += f"\n  Substeps: {substeps_str}"
            
            print(status_line, end="", file=self.file)
            self.file.flush()
    
    def _finalize(self) -> None:
        """Finalize the detailed progress bar."""
        if self.total is not None:
            self.n = self.total
            self._draw()
        print("\n", file=self.file)  # New line after progress bar


@contextmanager
def progress_bar(total: int, desc: str = "", unit: str = "it",
                style: ProgressStyle = ProgressStyle.UNICODE, **kwargs) -> ProgressBar:
    """
    Context manager for progress bar.
    
    Args:
        total: Total number of steps
        desc: Description of the progress operation
        unit: Unit for progress counting
        style: Style of the progress bar
        **kwargs: Additional arguments for ProgressBar
    
    Yields:
        Progress bar instance
    """
    bar = ProgressBar(total, desc, unit, style=style, **kwargs)
    try:
        yield bar
    finally:
        bar.close()


@contextmanager
def spinner(desc: str = "", unit: str = "it", style: str = "dots", **kwargs) -> Spinner:
    """
    Context manager for spinner.
    
    Args:
        desc: Description of the progress operation
        unit: Unit for progress counting
        style: Spinner style
        **kwargs: Additional arguments for Spinner
    
    Yields:
        Spinner instance
    """
    spnr = Spinner(desc, unit, style=style, **kwargs)
    try:
        yield spnr
    finally:
        spnr.close()


@contextmanager
def detailed_progress(total: int, desc: str = "", unit: str = "it", **kwargs) -> DetailedProgressBar:
    """
    Context manager for detailed progress bar.
    
    Args:
        total: Total number of steps
        desc: Description of the progress operation
        unit: Unit for progress counting
        **kwargs: Additional arguments for DetailedProgressBar
    
    Yields:
        Detailed progress bar instance
    """
    bar = DetailedProgressBar(total, desc, unit, **kwargs)
    try:
        yield bar
    finally:
        bar.close() 