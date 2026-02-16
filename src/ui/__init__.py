"""
Rich UI components for AigenFlow pipeline visualization.

This module provides beautiful terminal UI components using Rich:
- PipelineProgress: Real-time progress bars for pipeline execution
- LogStream: Live log streaming with colored output
- PhaseSummary: Rich tables for phase completion summaries
"""

__version__ = "1.0.0"

from ui.logger import LogStream
from ui.progress import PipelineProgress
from ui.summary import PhaseSummary

__all__ = ["PipelineProgress", "LogStream", "PhaseSummary"]
