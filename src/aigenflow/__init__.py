"""
AigenFlow - Multi-AI Pipeline CLI Tool for Automated Business Plan Generation.

This package provides a unified CLI interface for orchestrating AI agents
across multiple providers to generate comprehensive business plans.
"""

__version__ = "0.1.0"
__author__ = "drake"
__license__ = "Apache-2.0"

from importlib import import_module

__all__ = [
    "main",
    "agents",
    "cli",
    "config",
    "core",
    "gateway",
    "pipeline",
    "output",
    "templates",
    "cache",
    "context",
    "monitoring",
    "resilience",
    "batch",
    "ui",
]


def __getattr__(name: str):
    """Lazy-load top-level submodules to avoid eager import chains."""
    if name in __all__:
        return import_module(f"aigenflow.{name}")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
