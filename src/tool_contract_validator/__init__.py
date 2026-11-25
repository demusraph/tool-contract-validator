"""
ToolContract Validator: Enterprise-grade contract testing for AI Agent skills.
"""
from typing import Final

__version__: Final[str] = "0.1.0"

# Export core interfaces for package consumers
from .models import ContractSpec, ValidationReport, ExecutionResult
from .core import ContractEngine

__all__ = ["ContractSpec", "ValidationReport", "ExecutionResult", "ContractEngine"]