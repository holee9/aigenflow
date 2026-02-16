"""
aigenflow: Multi-AI Pipeline CLI Tool
"""

from importlib import import_module

__version__ = "0.1.0"

__all__ = [
    "agents",
    "config",
    "core",
    "gateway",
    "pipeline",
    "output",
    "templates",
]


def __getattr__(name: str):
    """Lazy-load top-level submodules to avoid eager import chains."""
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
