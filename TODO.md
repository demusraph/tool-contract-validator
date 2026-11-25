# ToolContract Validator: Engineering Roadmap & Implementation Checklist

## Phase 1: Architecture Scaffolding & Foundation

### 1.1 Environment, Build System & Tooling Setup
- [x] Configure Python 3.11+ project workspace using `uv` and `pyproject.toml` with build-system backend set to `hatchling`.
- [x] Enforce strict linting and formatting configuration via `ruff.toml` (rules: `E`, `F`, `W`, `C90`, `I`, `N`, `UP`, `YTT`, `ANN`, `ASYNC`, `BLE`, `B`, `A`, `COM`, `C4`, `DTZ`, `T10`, `EM`, `EXE`, `FA`, `ISC`, `ICN`, `G`, `INP`, `PIE`, `T20`, `PT`, `Q`, `RSE`, `RET`, `SLF`, `SLOT`, `SIM`, `TID`, `TCH`, `ARG`, `PTH`, `ERA`, `PD`, `PGH`, `PL`, `TRY`, `FLY`, `NPY`, `RUF`).
- [x] Setup `mypy` static type checking in strict mode (`strict = true`, `disallow_untyped_calls = true`, `disallow_untyped_defs = true`, `warn_return_any = true`, `no_implicit_optional = true`).
- [x] Configure `pytest` with `pytest-cov`, `pytest-asyncio`, `pytest-xdist`, and `pytest-benchmark`.
- [ ] Create pre-commit hooks file `.pre-commit-config.yaml` for Ruff format, Ruff lint, Mypy check, Git secret scanning, and trailing whitespace trim.

### 1.2 Core Data Structures & Type Definitions
- [ ] Implement `toolcontract.core.types` containing standard domain models:
  - [ ] `JSONSchemaDraft` enum (`DRAFT_07`, `DRAFT_2020_12`, `OPENAPI_3_0`, `OPENAPI_3_1`).
  - [ ] `Severity` enum (`CRITICAL`, `ERROR`, `WARNING`, `INFO`).
  - [ ] Immutable `ContractViolation` dataclass with fields: `path: Tuple[str | int, ...]`, `message: str`, `constraint: str`, `value: Any`, `severity: Severity`, `repair_suggestion: str | None`.
  - [ ] `ValidationResult` Pydantic v2 model wrapping `is_valid: bool`, `violations: List[ContractViolation]`, `execution_time_ns: int`, and `repaired_payload: Dict[str, Any] | None`.
- [ ] Define the central `ToolContract` instance model mapping tools to names, descriptions, input schemas, output schemas, and security boundaries.

### 1.3 System Configuration & Infrastructure
- [ ] Implement `toolcontract.config.ValidatorConfig` using Pydantic Settings with:
  - [ ] `strict_mode: bool` (default: `True`).
  - [ ] `auto_repair_json: bool` (default: `False`).
  - [ ] `max_recursion_depth: int` (default: `64`).
  - [ ] `max_payload_bytes: int` (default: `10_485_760` / 10MB).
  - [ ] `enable_telemetry: bool` (default: `True`).
  - [ ] `custom_format_validators: Dict[str, Callable[[str], bool]]`.
- [ ] Implement structured logging interface via `structlog` with zero-allocation fallback for high-throughput invocation paths.
- [ ] Create `toolcontract.telemetry` containing OpenTelemetry tracing spans (`toolcontract.validate`, `toolcontract.repair`, `toolcontract.fuzz`) and metrics counters (`violations_total`, `validation_latency_seconds`).

---

### Phase 1 Definition of Done (DoD)
- [ ] Workspace builds cleanly using `uv sync` on Python 3.11, 3.12, and 3.13.
- [ ] `mypy --strict src/` and `ruff check src/` return zero errors or warnings.
- [ ] Baseline test suite runs with 100% test coverage on `toolcontract.core.types` and `toolcontract.config`.

---

## Phase 2: Core Domain Logic & Engine Implementation

### 2.1 Schema Ingestion & Normalization Engine
- [ ] Implement `toolcontract.parser.openapi.OpenAPIParser`:
  - [ ] Support OpenAPI 3.0.x and 3.1.x `operationObject` parameter and `requestBody` decomposition.
  - [ ] Dereference local and remote `$ref` JSON pointers using an asynchronous, memoized `$ref` resolver with cycle detection.
- [ ] Implement `toolcontract.parser.pydantic.PydanticParser`:
  - [ ] Extract JSON schema representations from Pydantic `BaseModel` classes (v2 API).
  - [ ] Extract tool contracts directly from typed Python functions using AST and `inspect.signature` introspection.
- [ ] Implement `toolcontract.parser.normalizer.SchemaNormalizer`:
  - [ ] Transform disparate schema sources into an immutable, canonical AST (`CanonicalSchemaNode`).
  - [ ] Flatten `allOf`, `anyOf`, and `oneOf` logical operators into standard disjunctive normal form trees.

### 2.2 High-Performance Runtime Validation Engine
- [ ] Build `toolcontract.engine.validator.RuntimeValidator`:
  - [ ] Implement primitive type checking (`string`, `number`, `integer`, `boolean`, `null`, `array`, `object`).
  - [ ] Implement recursive object validation with property handling (`properties`, `required`, `additionalProperties`, `patternProperties`, `dependentRequired`).
  - [ ] Implement array constraint enforcement (`minItems`, `maxItems`, `uniqueItems`, `contains`, `prefixItems`).
  - [ ] Implement string format validators (`date-time`, `email`, `hostname`, `ipv4`, `ipv6`, `uri`, `uuid`, `regex`).
  - [ ] Implement numeric boundary validators (`minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`).
- [ ] Implement zero-copy fast-path validator using compiled `pydantic-core` validation routines for standard schemas.
- [ ] Add support for async validation pipelines (`async_validate()`) to avoid blocking thread pools during nested remote `$ref` checks.

### 2.3 Tool Call Interception & Invocation Runner
- [ ] Build `toolcontract.runner.ToolRunner` wrapper class:
  - [ ] Decorator `@contract_enforced(contract=ToolContract)` for wrapping Python async/sync function tools.
  - [ ] Pre-execution hook: Validate input arguments against contract input schema before target tool invocation.
  - [ ] Post-execution hook: Validate return payload against contract output schema before returning to caller.
  - [ ] Raise `ContractValidationError` on validation failure in strict mode.

### 2.4 Payload Repair & Remediation Engine
- [ ] Implement `toolcontract.repair.JSONRepairEngine`:
  - [ ] Parse and salvage truncated or malformed LLM JSON output (missing closing brackets, trailing commas, unescaped quotes).
  - [ ] Coerce types based on target schema (e.g., string `"123"` to integer `123`, single value `x` to list `[x]`).
  - [ ] Perform fuzzy property matching to repair slight field hallucination (e.g., `user_id` -> `userId`) using Levenshtein distance matching under threshold 0.85.
  - [ ] Strip unrecognized fields when `additionalProperties: false` is configured.

### 2.5 Security, Injection & Anomaly Auditor
- [ ] Implement `toolcontract.security.SecurityAuditor`:
  - [ ] Parameter injection detector: Scan string parameters against regex heuristics for SQL injection, Command injection (`bash`/`sh`), Path traversal, and Prompt injection patterns.
  - [ ] Size constraint enforcement: Prevent memory exhaustion vectors by capping total JSON string length, nesting depth, and array length.
  - [ ] Type confusion detector: Flags payload dynamic mutations where critical security flags are flipped from boolean to truthy strings.

### 2.6 Generative Contract Fuzzer Engine
- [ ] Implement `toolcontract.fuzz.ContractFuzzer`:
  - [ ] Integrate Hypothesis engine to dynamically build strategy generators from a `CanonicalSchemaNode`.
  - [ ] Generate valid boundary inputs, invalid off-by-one inputs, malformed types, and mutated null payloads.
  - [ ] Provide CLI command `toolcontract fuzz --contract schema.json --iterations 10000` to stress-test target tool handlers.

---

### Phase 2 Definition of Done (DoD)
- [ ] All components (`parser`, `engine`, `runner`, `repair`, `security`, `fuzz`) fully implemented.
- [ ] Unit test suite contains tests for all standard JSON Schema constraints (draft-07, 2020-12, OpenAPI 3.1).
- [ ] Full parameter injection audit suite passes with zero false negatives on baseline test payload set.
- [ ] JSON repair engine successfully restores valid state for 95%+ of standard LLM JSON output failure modes.

---

## Phase 3: Automated Stress Testing & Verification (DoD Gates)

### 3.1 Performance & Micro-benchmarking Setup
- [ ] Implement benchmark test suite in `benchmarks/test_validation_benchmarks.py` using `pytest-benchmark`.
- [ ] Measure baseline throughput for:
  - [ ] Small schema validation (10 fields): Target < 50 µs overhead per call.
  - [ ] Medium schema validation (100 fields, 3 nested levels): Target < 250 µs overhead per call.
  - [ ] Large schema validation (500 fields, 5 nested levels): Target < 1.0 ms overhead per call.
  - [ ] Malformed JSON repair overhead: Target < 1.5 ms per repair.
- [ ] Set up regression performance checks: fail CI run if performance degrades by > 10% relative to target baseline.

### 3.2 Concurrency & Thread-Safety Verification
- [ ] Build stress test harness `tests/stress/test_concurrency.py`:
  - [ ] Run 10,000 concurrent validations across 64 asyncio tasks using a single global `RuntimeValidator` instance.
  - [ ] Execute multi-threaded worker pool validation using `concurrent.futures.ThreadPoolExecutor` with 16 threads.
- [ ] Run memory leak detection suite using `memray` over 1,000,000 validation cycles; confirm flat memory footprint (< 1 MB total heap growth).

### 3.3 Generative Fuzzing & Crash Verification Gate
- [ ] Run automated fuzzing against `RuntimeValidator` for 100,000 random generated schemas and payloads.
- [ ] Assert zero unhandled generic exceptions (e.g., `AttributeError`, `IndexError`, `KeyError`, `RecursionError`). All failures must cleanly emit a `ContractViolation` or explicit `ToolContractException`.

### 3.4 Security & Robustness Verification Gate
- [ ] Execute injection test suite containing 500+ known prompt injection and shell escape vectors in tool input values.
- [ ] Confirm `SecurityAuditor` catches 100% of labeled malicious payloads when `strict_mode=True`.

---

### Phase 3 Definition of Done (DoD)
- [ ] Benchmark targets met: < 250 µs for 100-field schema validation.
- [ ] Zero thread-safety race conditions or memory leaks detected in `memray` run.
- [ ] 100k iteration fuzzing suite completes with zero unhandled panics or crashes.
- [ ] Code coverage report demonstrates >= 95% total line coverage and 100% branch coverage on core logic (`toolcontract.engine`, `toolcontract.parser`).

---

## Phase 4: Packaging, Documentation & README

### 4.1 Production Packaging Setup
- [ ] Finalize `pyproject.toml` with explicit metadata, license (Apache-2.0 or MIT), classifier list, author info, and URL mappings.
- [ ] Include explicit dependencies with pinned lower bounds: `pydantic>=2.6.0`, `jsonschema>=4.21.0`, `structlog>=24.1.0`, `opentelemetry-api>=1.22.0`.
- [ ] Configure optional dependencies: `[fuzz]` (`hypothesis`), `[cli]` (`typer`, `rich`), `[all]`.
- [ ] Embed `py.typed` marker file into `src/toolcontract/py.typed` to support PEP 561 compliance.

### 4.2 CLI Application Implementation
- [ ] Build command-line interface in `toolcontract.cli.main` using `typer` and `rich`:
  - [ ] `toolcontract validate --schema <path> --payload <path>`
  - [ ] `toolcontract repair --schema <path> --payload <path> --output <path>`
  - [ ] `toolcontract audit --schema <path>` (Generates risk analysis for target schema).
  - [ ] `toolcontract fuzz --contract <path> --duration <seconds>`

### 4.3 Documentation & Architecture Artifacts
- [ ] Generate API Documentation using `mkdocs` with `mkdocstrings[python]` extension.
- [ ] Create detailed user guides:
  - [ ] Integration with OpenAI Function Calling / Tool Calling SDK.
  - [ ] Integration with Anthropic Claude Tool Use SDK.
  - [ ] Custom validation constraints & business logic plugins.
  - [ ] Security hardening guide.

### 4.4 High-Quality README.md Creation
- [ ] Draft comprehensive, professional `README.md` containing:
  - [ ] Concise project description and badge block (CI status, PyPI version, Python versions, Coverage, License).
  - [ ] Quickstart code snippets (Copy-paste runnable examples for standard usage, decorator usage, and JSON repair).
  - [ ] Key Features breakdown (High Performance, Repair Engine, Security Audit, Fuzzer).
  - [ ] Architecture diagram (Mermaid.js flowchart detailing data flow from raw LLM payload to validated tool call execution).
  - [ ] Performance benchmark charts.
  - [ ] CLI reference section.

---

### Phase 4 Definition of Done (DoD)
- [ ] Wheel package builds cleanly via `uv build` and verifies with `twine check`.
- [ ] Executable CLI tested against standard sample schemas and payloads.
- [ ] MkDocs site builds with zero warnings or broken internal links (`mkdocs build --strict`).
- [ ] `README.md` contains verified code blocks tested by `phmdoctest` or `pytest-codeblocks`.

---

## Phase 5: Release & Production Readiness

### 5.1 CI/CD Pipelines Implementation
- [ ] Setup GitHub Actions workflow `.github/workflows/ci.yml`:
  - [ ] Multi-OS matrix (Ubuntu Latest, macOS Latest, Windows Latest).
  - [ ] Python version matrix (3.11, 3.12, 3.13).
  - [ ] Jobs: `lint` (Ruff), `typecheck` (Mypy), `test` (Pytest with coverage report uploaded to Codecov), `benchmark`.
- [ ] Setup Security Analysis workflow `.github/workflows/security.yml`:
  - [ ] CodeQL analysis.
  - [ ] Dependency vulnerability scanning via `pip-audit`.
  - [ ] Secret scanning via TruffleHog.

### 5.2 Release & Deployment Automation
- [ ] Setup GitHub Actions release workflow `.github/workflows/release.yml`:
  - [ ] Trigger on semantic version tags (`v*.*.*`).
  - [ ] Automatic changelog generation via GitHub Releases API.
  - [ ] Build source distribution and wheel packages.
  - [ ] Secure publish to PyPI using Trusted Publisher (OIDC token authentication).
  - [ ] Produce and attach Sigstore signatures for published build artifacts.

### 5.3 Open-Source Governance & Community Files
- [ ] Add `LICENSE` file (Apache 2.0 or MIT).
- [ ] Add `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1).
- [ ] Add `CONTRIBUTING.md` with complete developer setup guide, branch naming standards, git commit guidelines (Conventional Commits), and PR checklist.
- [ ] Create GitHub Issue Templates (`.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`).
- [ ] Create GitHub Pull Request Template (`.github/PULL_REQUEST_TEMPLATE.md`).

---

### Phase 5 Definition of Done (DoD)
- [ ] CI/CD pipeline runs and passes 100% on a clean target branch.
- [ ] Dry-run deployment to TestPyPI succeeds without errors.
- [ ] CodeQL, Dependabot, and vulnerability scanners return zero `High` or `Critical` severity alerts.
- [ ] Repository governance files fully populated and verified.