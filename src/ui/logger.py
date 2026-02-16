"""
Log streaming display using Rich Panel.

Provides real-time log streaming with:
- Log level indicators (INFO, WARNING, ERROR)
- Timestamps
- Colored output by log level
"""

from datetime import datetime
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogStream:
    """
    Rich panel for real-time log streaming.

    Displays log messages with timestamps, levels, and colored output.
    """

    def __init__(self, console: Console | None = None) -> None:
        """
        Initialize LogStream.

        Args:
            console: Rich console instance (creates new if None)
        """
        self.console = console or Console()
        self._log_count = 0

    def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Log a message with level and timestamp.

        Args:
            message: Log message to display
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            timestamp: Timestamp for log entry (uses now if None)
        """
        if timestamp is None:
            timestamp = datetime.now()

        self._log_count += 1

        # Format timestamp
        ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Color code by level
        level_colors = {
            LogLevel.DEBUG: "dim cyan",
            LogLevel.INFO: "blue",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "bold red",
        }

        color = level_colors.get(level, "white")

        # Build log message
        log_text = Text()
        log_text.append(f"[{ts_str}] ", style="dim")
        log_text.append(f"[{level.value}] ", style=color)
        log_text.append(message)

        # Display in panel
        panel = Panel(
            log_text,
            title=f"[{color}]Log Entry #{self._log_count}[/]",
            border_style=color,
            padding=(0, 1),
        )

        self.console.print(panel)

    def info(self, message: str, timestamp: datetime | None = None) -> None:
        """
        Log an INFO message.

        Args:
            message: Message to log
            timestamp: Optional timestamp
        """
        self.log(message, LogLevel.INFO, timestamp)

    def warning(self, message: str, timestamp: datetime | None = None) -> None:
        """
        Log a WARNING message.

        Args:
            message: Message to log
            timestamp: Optional timestamp
        """
        self.log(message, LogLevel.WARNING, timestamp)

    def error(self, message: str, timestamp: datetime | None = None) -> None:
        """
        Log an ERROR message.

        Args:
            message: Message to log
            timestamp: Optional timestamp
        """
        self.log(message, LogLevel.ERROR, timestamp)

    def debug(self, message: str, timestamp: datetime | None = None) -> None:
        """
        Log a DEBUG message.

        Args:
            message: Message to log
            timestamp: Optional timestamp
        """
        self.log(message, LogLevel.DEBUG, timestamp)

    def critical(self, message: str, timestamp: datetime | None = None) -> None:
        """
        Log a CRITICAL message.

        Args:
            message: Message to log
            timestamp: Optional timestamp
        """
        self.log(message, LogLevel.CRITICAL, timestamp)

    def get_log_count(self) -> int:
        """
        Get the number of log entries.

        Returns:
            Number of log entries
        """
        return self._log_count
