# AGENTS.md — Autonomous AI Agent Operational Protocol
## System Target: `ToolContract Validator`

---

## 1. Project Overview & Core Mission

`ToolContract Validator` is a high-assurance, deterministic validation engine and CLI runtime engineered for AI agent system architectures. Its primary mission is to enforce strict input/output contract compliance on Large Language Model (LLM) tool calls prior to execution and prior to returning responses to the agent loop.

The system ingests JSON Schema (Draft 2020-12 / OpenAPI 3.1 specifications) or runtime Pydantic v2 models, parses raw tool invocations emitted by LLMs, and executes static/runtime verification against parameters, types, required keys, enum constraints, and custom pre/post-conditions.

### Architectural Core Components

```
                +---------------------------------------+
                |        Raw LLM Tool Call / Output     |
                +---------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                       ToolContract Validator Core                     |
|                                                                       |
|  +------------------+   +--------------------+   +-----------------+  |
|  | Schema Normalizer|-->| Input Payload      |-->| Return Payload  |  |
|  | (OpenAPI/Pydantic|   | Contract Validator |   | Spec Verifier   |  |
|  +------------------+   +--------------------+   +-----------------+  |
|                                   |                       |           |
+-----------------------------------|-----------------------|-----------+
                                    v                       v
                        +---------------------------------------+
                        | ToolContractValidationResult (Result) |
                        +---------------------------------------+
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
         [Success: Executable]            [Failure: Fault Model]
                                          (Structured Exception)
```

1. **`toolcontract.core.normalizer`**: Converts arbitrary Pydantic v2 schemas, Python type hints, or JSON Schema documents into unified internal contract definitions (`ContractSpec`).
2. **`toolcontract.core.validator`**: Executes deterministic, zero-allocation schema checks against call arguments (`validate_call`) and tool execution returns (`validate_return`).
3. **`toolcontract.core.exceptions`**: Provides structured, machine-parseable exception models (`ContractValidationError`, `SchemaViolationError`, `ContractMismatchError`) containing JSON-Pointer paths to payload faults.
4. **`toolcontract.cli`**: Provides a zero-dependency CLI interface for CI/CD integration, local verification, and pipeline evaluation.

### Non-Functional Operational Constraints
* **Latency Overhead**: Sub-millisecond validation latency (< 1.5ms for schemas containing up to 100 parameters).
* **Failure Determinism**: 100% reproducible error reports; zero reliance on dynamic global state or unseeded RNG.
* **Type Integrity**: 100% explicit typing under `mypy --strict`. Zero untyped generic fallbacks (`Any` requires explicit, documented invariant rationale).

---

## 2. Local PowerShell Commands

All autonomous operations, environment management, static analysis, and testing in Windows/PowerShell 7+ must use the following standard commands. Do not substitute commands.

### 2.1 Virtual Environment Initialization & Maintenance

```powershell
# Create Python 3.11 Virtual Environment
py -3.11 -m venv .venv

# Set Execution Policy for Current Session (if required)
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process -Force

# Activate Virtual Environment
.\.venv\Scripts\Activate.ps1

# Upgrade Core Tooling
python -m pip install --upgrade pip setuptools wheel

# Install Package in Editable Mode with All Optional/Dev Dependencies
pip install -e .[dev,docs,test]
```

### 2.2 Execution & CLI Invocations

```powershell
# Execute CLI Core via Module Entrypoint
python -m toolcontract.cli --help

# Validate a Tool Definition Schema File Against Meta-Schema
python -m toolcontract.cli validate-schema --schema-path .\examples\schemas\weather_tool.json

# Validate a Tool Call Arguments Payload
python -m toolcontract.cli validate-call `
    --schema-path .\examples\schemas\weather_tool.json `
    --payload-path .\examples\payloads\valid_call.json

# Validate Tool Execution Return Value
python -m toolcontract.cli validate-return `
    --schema-path .\examples\schemas\weather_tool.json `
    --return-path .\examples\payloads\valid_return.json
```

### 2.3 Automated Testing Suites

```powershell
# Run Full Test Suite with Standard Terminal Output
pytest

# Run Full Test Suite with Coverage Enforcement (100% Threshold Required)
pytest --cov=toolcontract --cov-report=term-missing --cov-fail-under=100

# Execute Single Test File with Verbose Tracebacks
pytest tests/test_validator.py -vv --tb=short

# Execute Specific Test Function Under Debugging Mode
pytest tests/test_validator.py -k "test_schema_type_mismatch" -vv --pdb
```

### 2.4 Code Quality, Formatting & Static Type Inspection

```powershell
# Run Ruff Linter (Check Only)
ruff check src/toolcontract tests

# Run Ruff Auto-Fixer (Unsafe Fixes Included)
ruff check --fix --unsafe-fixes src/toolcontract tests

# Run Ruff Code Formatter (Check Alignment)
ruff format --check src/toolcontract tests

# Apply Ruff Code Formatting
ruff format src/toolcontract tests

# Run Mypy Strict Static Type Analysis
mypy --strict src/toolcontract tests
```

### 2.5 Unified Pre-Commit Quality Verification Gate (Single PowerShell Execution Block)

```powershell
$ErrorActionPreference = "Stop"
Write-Host "=== STARTING QUALITY GATE CHECK ===" -ForegroundColor Cyan
ruff format --check src/toolcontract tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
ruff check src/toolcontract tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
mypy --strict src/toolcontract tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
pytest --cov=toolcontract --cov-report=term-missing --cov-fail-under=100
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== ALL QUALITY GATES PASSED CLEANLY ===" -ForegroundColor Green
```

---

## 3. Engineering Invariants

AI agents executing modifications inside this repository must treat the following engineering invariants as non-negotiable rules. Any pull request or commit breaking an invariant will be rejected by the automated quality gate.

### 3.1 Zero-Placeholder Mandate
* **No Stubs**: Code containing `pass` (unless inside an `@abstractmethod` interface definition), `# TODO`, `# FIX ME`, `# HACK`, or `raise NotImplementedError` in executable paths is explicitly prohibited.
* **Complete Implementations Only**: Modules, classes, data structures, edge-case handlers, and tests must be fully written and tested prior to task completion.
* **No Mocking Internal Logic**: Unit tests must execute real parsing and validation logic. Mocking is restricted to external I/O operations (e.g., fetching a remote schema over HTTP).

### 3.2 Strict Typing Rules (`mypy --strict`)
* Python Version: Python 3.11+.
* Import Conventions: Must include `from __future__ import annotations` at the top of every module.
* Variable Annotations: Every function signature, function argument, class variable, and module-level constant must be fully annotated with explicit types.
* Avoidance of `Any`: `Any` is considered a type-system failure. Use type variables (`TypeVar`), generics (`Generic[T]`), `object`, or concrete unions (`Union[str, int]`, `str | int`).
* Container Explicit Types: Never use generic containers such as `list`, `dict`, `set`. Always specify element types: `list[str]`, `dict[str, Any]` (where value is bounded or guarded), `Sequence[T]`, `Mapping[str, ToolParameter]`.

```python
# CORRECT
from __future__ import annotations
from typing import Final, Sequence
from toolcontract.models import ToolParameter

def extract_required_keys(parameters: Sequence[ToolParameter]) -> list[str]:
    return [param.name for param in parameters if param.is_required]

# INCORRECT (WILL FAIL MYPY STRICT)
def extract_required_keys(parameters):
    return [param.name for param in parameters if param.is_required]
```

### 3.3 CRLF/LF and File Formatting Integrity
* Line Endings: Preserved as Git LF standard. Windows tools must not convert LF to CRLF in source files.
* Text Encoding: Strict `UTF-8` without Byte Order Mark (BOM).
* Trailing Whitespace: Zero trailing whitespace allowed on any line.
* Newlines: Exactly one trailing newline at the end of every file (`\n`).

### 3.4 Defensive Error Handling & Exception Synthesizer Pattern
* No Generic Catch Blocks: Bare `except:` or generic `except Exception:` without re-wrapping and preserving tracebacks via `raise ... from err` is prohibited.
* Exception Subclassing: All errors raised within this library must inherit from `toolcontract.exceptions.ToolContractBaseException`.
* Traceback Hygiene: Exceptions generated during runtime payload validation must synthesize structured JSON-Pointer paths (`/properties/user_id/type`) indicating exactly where schema evaluation failed.

```python
# CORRECT
try:
    validated_payload = self._schema_adapter.validate(raw_payload)
except RawValidationError as err:
    raise SchemaViolationError(
        message=f"Field validation failed at path: {err.json_path}",
        path=err.json_path,
        schema_name=self.schema_name,
    ) from err
```

### 3.5 Immutability and Pure Functions
* Schema Representations (`ContractSpec`, `ToolParameter`, `ValidationResult`) must be declared as immutable data structures (`frozen=True` in Pydantic models or `dataclass(frozen=True)`).
* Mutation of input arguments is prohibited. Functions processing schemas or payloads must return new data structures.

---

## 4. Self-Healing & Error Recovery Protocol

When an AI agent encounters a test failure, lint failure, or typing issue during local execution, it must execute the following structured protocol to debug, diagnose, and remediate the issue without human intervention.

```
       +-------------------------------------------------------+
       |             Command Execution Failure                 |
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |             Step 1: Isolate Failure Output            |
       |  (Extract stderr, stdout, exit codes, file paths)     |
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |            Step 2: Classify Failure Domain             |
       +-------------------------------------------------------+
         /                         |                         \
        /                          |                          \
       v                           v                           v
[Domain A: Type Check]    [Domain B: Lint/Format]     [Domain C: Test Failure]
 (mypy error taxonomy)     (ruff rule violation)       (pytest traceback)
       |                           |                           |
       v                           v                           v
[Locate Type Invariant]   [Apply Precision Fix]       [Analyze AST & State]
       |                           |                           |
       +---------------------------+---------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |           Step 3: Apply Minimal Diff Fix              |
       +-------------------------------------------------------+
                                   |
                                   v
       +-------------------------------------------------------+
       |           Step 4: Execute Re-Verification             |
       |             (Run quality gate script)                 |
       +-------------------------------------------------------+
                                   |
                    +--------------+--------------+
                    |                             |
                    v                             v
            [Pass: Complete]             [Fail: Loop Step 1]
```

### Step 1: Isolate Failure Output
Capture stdout, stderr, exit code, and targeted line numbers. Never attempt to guess an error without reading the exact compiler/interpreter output.

### Step 2: Classify Failure Domain

#### Domain A: Static Type Analyzer Failure (`mypy`)
1. **Symptom**: `error: Item "None" of "Optional[X]" has no attribute "Y"`
   * **Fix**: Add an explicit type assertion or assertion check (`assert instance is not None`) before accessing attributes. Do not use `# type: ignore` unless an external third-party library completely lacks type stubs, and document it with a rationale.
2. **Symptom**: `error: Argument 1 to "fn" has incompatible type "X"; expected "Y"`
   * **Fix**: Check module imports and normalizer converters. Insert explicit casting or refine the type signature using `TypeVar` or type narrowing functions.

#### Domain B: Linter & Formatter Violations (`ruff`)
1. Run target auto-formatter:
   ```powershell
   ruff format src/toolcontract tests
   ```
2. If `ruff check` yields specific code violations (e.g., `F401` unused import, `UP006` non-PEPR 585 generics):
   ```powershell
   ruff check --fix src/toolcontract tests
   ```
3. Hand-fix any remaining violations that ruff cannot automatically auto-fix (e.g., complex code complexity `C901`, unhandled broad exceptions `BLE001`).

#### Domain C: Test & Coverage Failures (`pytest`)
1. Isolate the failing test using its exact node ID:
   ```powershell
   pytest tests/test_validator.py::test_specific_validation_failure -vv --tb=long
   ```
2. Trace the stack frame from the top of the application code down to the precise failure line.
3. If test failure is due to a **Coverage Threshold Gate (< 100%)**:
   * Inspect missing line numbers reported by `--cov-report=term-missing`.
   * Write explicit unit test cases targeting the un-executed code branches (e.g., edge-case input handling, error path re-throwing).

### Step 3: Minimal Diff Remediation Strategy
* Apply changes only to files directly responsible for the failure.
* Never rewrite unrelated classes or refactor public interfaces to solve an isolated type check or logic error.
* Keep diffs dense, precise, and logically sound.

### Step 4: Re-Verification Loop
Rerun the unified pre-commit quality gate. The task is not finished until all tools report exit code `0`.

---

## 5. Definition of Done (DoD) Quality Gate

An AI agent must verify that every requirement in this checklist evaluates to `TRUE` before declaring a task completed or submitting a pull request.

| Gate Component | Verification Command | Required Outcome |
| :--- | :--- | :--- |
| **Code Formatting** | `ruff format --check src/toolcontract tests` | Exit Code `0`. Zero formatting diffs. |
| **Lint Compliance** | `ruff check src/toolcontract tests` | Exit Code `0`. Zero linter warnings or errors. |
| **Static Type Integrity**| `mypy --strict src/toolcontract tests` | Exit Code `0`. Success: no issues found in X source files. |
| **Test Suite Execution** | `pytest` | Exit Code `0`. 100% of defined tests pass. |
| **Code Coverage** | `pytest --cov=toolcontract --cov-fail-under=100` | Exit Code `0`. Total coverage is 100.00%. |
| **Zero Placeholders** | Visual AST / Search Inspection | Zero instances of `# TODO`, `# FIX ME`, `pass` in concrete classes, or unhandled stubs. |
| **CLI Functionality** | `python -m toolcontract.cli --help` | Exit Code `0`. Help options render correctly without runtime import errors. |
| **Clean Encoding** | Local Verification | All saved files use standard UTF-8 without BOM and LF standard line endings. |

---

## 6. Project Architecture & File Mapping Reference

Agents modifying the codebase must follow the established directory layout:

```
ToolContract-Validator/
├── .gitignore
├── pyproject.toml              # Centralized build configuration (ruff, mypy, pytest)
├── README.md                   # Public documentation
├── AGENTS.md                   # Autonomous agent operational specification
├── src/
│   └── toolcontract/
│       ├── __init__.py         # Package exports & version attributes
│       ├── py.typed            # PEP 561 type marker file
│       ├── cli.py              # Command-line interface parser & router
│       ├── core/
│       │   ├── __init__.py
│       │   ├── engine.py       # Primary contract validation orchestration
│       │   ├── exceptions.py   # Hierarchical exception models
│       │   ├── normalizer.py   # Schema normalization logic (JSON Schema / OpenAPI)
│       │   └── types.py        # Core dataclasses and typing primitives
│       └── models/
│           ├── __init__.py
│           ├── contract.py     # ContractSpec and ToolParameter definitions
│           └── result.py       # ValidationResult and ErrorDetail models
└── tests/
    ├── __init__.py
    ├── conftest.py             # Common fixtures (valid/invalid schemas & payloads)
    ├── test_cli.py             # CLI command invocation tests
    ├── test_engine.py          # Core engine unit tests
    ├── test_normalizer.py      # Schema parser unit tests
    └── test_types.py           # Type validation edge case tests
```

### Standard Code Pattern for New Modules

When adding a new module under `src/toolcontract/`, adhere strictly to this file structure:

```python
"""Module description explaining its exact role in the ToolContract ecosystem."""

from __future__ import annotations

import logging
from typing import Final, Sequence

from toolcontract.core.exceptions import ToolContractBaseException
from toolcontract.models.contract import ContractSpec

__all__: Final[list[str]] = ["process_contract_spec"]

logger: Final[logging.Logger] = logging.getLogger(__name__)


def process_contract_spec(spec: ContractSpec, rules: Sequence[str]) -> bool:
    """Processes a contract specification against a sequence of structural rules.

    Args:
        spec: The immutable contract specification object.
        rules: A sequence of validation rule identifiers to evaluate.

    Returns:
        True if all rules pass validation successfully.

    Raises:
        ToolContractBaseException: Raised when a rule evaluation encounters a fatal error.
    """
    if not spec.parameters:
        logger.debug("Contract spec contains zero parameters; passing by default.")
        return True

    # Implementation logic here
    return True
```