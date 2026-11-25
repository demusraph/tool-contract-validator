# PRD.md — ToolContract Validator (`tool-contract-validator`)

## 1. Executive Summary & Problem-Solution Fit

### 1.1 Context & Problem Statement
Autonomous agent systems rely on tool execution interfaces—such as Model Context Protocol (MCP) servers, OpenAPI/REST endpoints, standard Python callables, and LangChain/LlamaIndex tool adapters—to interact with external state. In production environments, agent tools suffer from **silent interface degradation**:
* **Schema Drift**: Upstream APIs mutate schemas (e.g., dropping fields, changing types from `int` to `string`, modifying nullability) without updating agent context manifests.
* **Boundary Payload Failure**: LLMs produce boundary or edge-case tool inputs (empty strings, zero-value integers, out-of-bounds float ranges, multi-byte Unicode) that bypass initial LLM validation but crash downstream services.
* **Non-Deterministic Response Structures**: Heterogeneous external tool responses return variable payload schemas depending on runtime state, triggering silent parsing failures or triggering hallucination loops in the host LLM.
* **Lack of Conformance Observability**: Existing CI/CD testing frameworks target unit test logic rather than contract schema enforcement, allowing tools with incompatible structural guarantees to pass deployment gates.

### 1.2 Solution Statement
`tool-contract-validator` is an open-source, deterministic conformance test harness and schema verification library for agent skills. It evaluates skill input/output contracts against JSONSchema Draft-07 and 2020-12 specifications. 

The system programmatically inspects skill contracts, synthesizes valid and boundary test payloads via property-based constraint solving, executes target skills in isolated execution contexts (local process, HTTP/REST, or stdio/SSE MCP), verifies response payloads against output schemas, checks structural runtime invariants, calculates quantitative Conformance Scores (0.0–100.0), and flags schema drift before code hits production.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    tool-contract-validator Harness                      │
├───────────────────┬──────────────────────┬──────────────────────────────┤
│ Synthetic Payload │  Execution Sandbox   │ Contract & Invariant Engine │
│    Generator      │  (Process/HTTP/MCP)  │  (Schema Verification +     │
│ (Property Solvers)│                      │   Invariant Assertions)      │
└─────────┬─────────┴──────────┬───────────┴──────────────┬───────────────┘
          │                    │                          │
          ▼                    ▼                          ▼
  Synthesized Inputs   Skill Invocation Trace    Conformance Report &
   (Valid + Edge)      (Latency, Memory, Logs)    Scorecard (SARIF/JUnit)
```

---

## 2. Target Personas & Core User Stories

### 2.1 Personas
* **Persona A: Agent Infrastructure Engineer (Alex)**  
  *Needs*: Automated deployment gates to block breaking API modifications and schema drift across 50+ agent tool integrations before release.
* **Persona B: Skill/Tool Developer (Devon)**  
  *Needs*: Rapid local verification of custom tool interfaces (MCP tools, custom functions) against boundary inputs without manually writing boilerplate edge-case tests.
* **Persona C: AI Systems Quality & Reliability Engineer (Sam)**  
  *Needs*: Continuous profiling of tool contract health, latency degradation, error rates, and SARIF/JUnit exportable metrics for security and compliance audits.

### 2.2 Core User Stories

| ID | Persona | Story Statement | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **US-01** | Alex | **As an** Agent Infra Engineer, **I want to** run a CLI contract validation command in CI/CD pipelines, **so that** deployments fail immediately if a tool's response payload deviates from its declared JSONSchema contract. | CLI returns exit code `1` on contract mismatch, outputs structural diffs, and generates a standard JUnit XML / SARIF artifact. |
| **US-02** | Devon | **As a** Skill Developer, **I want to** synthesize edge-case input payloads from a tool's JSONSchema input definition, **so that** I can test how my tool handles boundary values (e.g., empty arrays, max-length strings, nulls). | Generator produces deterministic boundary tests based on schema constraints (`minimum`, `pattern`, `required`, `enum`) using property-based generation within < 250ms. |
| **US-03** | Devon | **As a** Skill Developer, **I want to** declare logical runtime invariants (e.g., `output.total >= output.subtotal`), **so that** structural data integrity is enforced beyond base JSON types. | Invariant expression engine evaluates JESPath/JMESPath conditions against execution outputs and flags invariant violations separately from raw schema errors. |
| **US-04** | Sam | **As a** Reliability Engineer, **I want to** calculate a Conformance Score (0.0 - 100.0) for every tool, **so that** I can track quality degradation trends over historical test runs. | Engine produces a deterministic mathematical score factoring schema compliance, boundary handling pass rate, and execution exception counts. |
| **US-05** | Alex | **As an** Agent Infra Engineer, **I want to** validate tools exposing Model Context Protocol (MCP) over stdio or SSE transport, **so that** third-party agent servers follow strict protocol specifications. | Runner spins up target stdio/SSE MCP server, discovers tools via standard JSON-RPC interface, synthesizes tests, and verifies output contracts. |
| **US-06** | Devon | **As a** Skill Developer, **I want an** interactive CLI/TUI studio to test and inspect tools locally, **so that** I can rapidly debug failing payloads, step through payload responses, and modify schemas in real time. | TUI/Web studio provides live schema validation, payload execution triggers, side-by-side JSON diffs, and execution latency graphs. |
| **US-07** | Sam | **As a** Reliability Engineer, **I want to** profile tool invocation latency and memory footprint during contract test suites, **so that** performance bottlenecks are identified prior to production release. | Harness captures p50, p90, p95, p99 latency metrics and resident set size (RSS) memory consumption per skill execution run. |

---

## 3. MoSCoW Feature Matrix

### 3.1 Must-Have (P0)
* **Core Validation Engine**:
  * Compliance verification against JSONSchema Draft-07, Draft-09, and Draft 2020-12 specifications.
  * Support for complex JSONSchema constructs: `$ref`, `oneOf`, `anyOf`, `allOf`, `not`, `patternProperties`, `additionalProperties`, `prefixItems`.
  * Detailed structural diff output for schema failures showing JSON Path location, expected schema requirement, and actual received data payload.
* **Property-Based Synthetic Payload Generator**:
  * Automatic generation of compliant test payloads derived purely from input JSONSchema definitions.
  * Edge-case boundary synthesis mode: auto-injecting min/max numeric limits, boundary string lengths, regex-matching edge strings, empty arrays, and special Unicode sets.
  * Deterministic random seed controls (`--seed <int>`) for reproducible test suite runs.
* **Target Execution Adapters**:
  * `PythonCallableAdapter`: Direct execution of standard Python functions and async callables.
  * `HTTPAdapter`: Execution of external REST/OpenAPI tool endpoints via HTTP/HTTPS with custom auth headers.
  * `MCPAdapter`: Native JSON-RPC execution over stdio and Server-Sent Events (SSE) compliant with Model Context Protocol specification v1.0.
* **Invariant Engine**:
  * Logical runtime assertions using expressions (evaluating equality, inequality, length checks, and cross-field properties using JESPath syntax).
* **CLI & Reporting Suite**:
  * Headless CLI runner (`tool-contract-validator run --config contract.yaml`).
  * Standard exit status codes (`0`: Pass, `1`: Schema/Invariant Failure, `2`: Harness/Runtime Execution Exception).
  * Conformance Score Calculation Engine (0.0 to 100.0).

### 3.2 Should-Have (P1)
* **Performance Profiling Module**:
  * Profiling execution metrics per tool: latency distribution (p50, p90, p95, p99) and process memory footprint delta.
  * Configurable SLA thresholds (e.g., fail contract test if p95 latency > 500ms).
* **Drift & Regression Engine**:
  * Historical baseline file loading (`--baseline baseline.json`) to highlight backward-incompatible schema changes between API versions.
  * Breaking change classification: field removal, type narrowing, constraint tightening, new required properties.
* **Standard Test Exporters**:
  * Native exporters for standard reporting formats: JUnit XML, SARIF (Static Analysis Results Interchange Format v2.1.0), and JSON reports.
* **Mock Server Mode**:
  * Standalone mock server mode generating contract-compliant or synthetic-errored outputs to test downstream host agent resiliency.

### 3.3 Nice-to-Have / Delight (P2)
* **Interactive Contract Testing Studio**:
  * Local web studio interface (`tool-contract-validator studio`) built with FastAPI + HTML5/JS or Rich TUI interface.
  * Features live schema editing, visual JSON payload diffs, execution tracing, and single-click contract repair proposals.
* **Automated Schema Inference (AST / Docstrings / Tracing)**:
  * Automatic generation of JSONSchema specifications by analyzing Python docstrings, Type Hints, Pydantic models, or observing runtime execution traces.
* **Adversarial Fuzzing Engine**:
  * Security boundary fuzzing: injection of SQLi strings, path traversal sequences, shell escape characters, and giant payload blobs into tool parameters to verify parameter sanitization defense before handler execution.

---

## 4. Non-Functional Requirements (NFRs)

### 4.1 Latency & Computational Overhead
* **Schema Evaluation Overhead**: Schema validation processing time must be $\le 1.5\text{ ms}$ per 100KB payload on a standard single-thread vCPU execution environment.
* **Synthetic Payload Generation**: Generating a suite of 50 boundary payloads from a complex JSONSchema with nested references must complete in $\le 250\text{ ms}$.
* **Harness p95 Latency Overhead**: The internal wrapping overhead of the harness execution pipeline (excluding actual tool runtime execution time) must not exceed $\le 5\text{ ms}$ at p95.

### 4.2 Resource & Memory Footprint
* **CLI Engine Footprint**: Max Resident Set Size (RSS) memory consumption during headless test suite runs must remain $\le 85\text{ MB}$.
* **Studio Interactive Server Footprint**: Max RSS memory consumption when running the interactive local studio interface must remain $\le 150\text{ MB}$.
* **Zero Resource Leaks**: System process pools and async network execution loops must explicitly clean up file descriptors, subprocesses, and sockets without leaking resources across long-running continuous test execution loops (> 100,000 iterations).

### 4.3 Reliability & Offline Readiness
* **Strict Offline Operation**: 100% of validation, payload generation, invariant checking, and profiling functions must run in completely air-gapped environments without external LLM API calls or remote service calls.
* **Determinism**: Given identical random seeds (`--seed`), payload generation, test selection, and scoring outputs must be 100% bitwise reproducible across OS platforms (Linux x86_64/arm64, macOS arm64/x86_64, Windows x64).

### 4.4 Architecture & Code Quality
* **Runtime Standards**: Written strictly in Python 3.11+ using static type annotations (`mypy --strict` compliant).
* **Decoupled Engine**: Core engine (`validator-core`) must remain strictly decoupled from CLI presentation and UI modules, allowing standard import as an embedded library (`import tool_contract_validator`).
* **Test Coverage**: Maintain minimum 95% line and branch coverage across core validation, generator, and adapter modules.

### 4.5 Security & Execution Sandboxing
* **Local Code Sandbox**: Execution of local Python callables must occur within isolated subprocesses bounded by strict configurable timeouts (default `30s`) and RSS memory limits to prevent infinite loops or memory leaks from corrupting the harness process.
* **Safe Invariant Evaluation**: Invariant assertion expressions must be parsed via deterministic abstract syntax tree (AST) evaluators (JESPath) without using vulnerable arbitrary execution mechanisms (`eval()` or `exec()`).

---

## 5. Quantitative Success Metrics & KPIs

```
                          ┌───────────────────────────┐
                          │    Conformance Score      │
                          │        (0.0 - 100.0)      │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│ Schema Compliance    │    │ Boundary Handling    │    │ Runtime Reliability  │
│      Weight: 50%     │    │      Weight: 30%     │    │      Weight: 20%     │
├──────────────────────┤    ├──────────────────────┤    ├──────────────────────┤
│ Valid Output %       │    │ Edge Input Pass %    │    │ Unhandled Exe %      │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

### 5.1 Conformance Score Formula
The system evaluates skill conformance using an objective mathematical score defined as:

$$S_{\text{conformance}} = 100 \times \left( 0.50 \cdot C_{\text{schema}} + 0.30 \cdot P_{\text{boundary}} + 0.20 \cdot (1 - E_{\text{unhandled}}) \right)$$

Where:
* $C_{\text{schema}}$: Percentage of valid execution responses strictly adhering to the output JSONSchema ($0.0 - 1.0$).
* $P_{\text{boundary}}$: Percentage of synthetic boundary input payloads correctly handled (either returning a valid output schema or returning a designated structural application error code rather than an unhandled process crash/exception) ($0.0 - 1.0$).
* $E_{\text{unhandled}}$: Ratio of unhandled skill runtime exceptions (HTTP 500, unhandled Python exceptions, non-zero subprocess crashes) to total executions ($0.0 - 1.0$).

### 5.2 Key Performance Indicators (KPIs)

| Metric | Target Baseline | Measure Method |
| :--- | :--- | :--- |
| **Schema Breaking Change Recall** | 100.0% | Detection rate when injecting schema drift (field drops, type shifts) into benchmark skill suites. |
| **False Positive Rate** | < 0.1% | Incorrect verification flags on valid, spec-compliant tool execution payloads. |
| **Execution Throughput** | > 2,000 validations / sec | Evaluation throughput of core schema validation engine on standard single vCPU. |
| **CI Initialization Overhead** | < 3.0 seconds | Total boot and configuration initialization delay when executed inside Github Actions / GitLab CI. |
| **Synthetic Boundary Coverage** | 100% of defined constraints | Percent of JSONSchema constraints (`min`, `max`, `pattern`, `enum`, `required`) targeted by the generator. |

---

## 6. Execution & Verification Flow

### 6.1 Lifecycle Matrix

```
[Tool Manifest / JSONSchema] 
           │
           ▼
[Synthetic Generator Engine] ──(Generates Boundary Inputs)──► [Execution Sandbox Adapter]
                                                                        │
                                                                 (Executes Tool)
                                                                        │
                                                                        ▼
[Conformance & Score Engine] ◄──(Captures Output, Latency, RSS)─────────┘
           │
           ├──► [JSONSchema Output Verifier]
           ├──► [JESPath Invariant Asserter]
           └──► [Drift Analysis vs Baseline]
           │
           ▼
[Reports: Console / JUnit XML / SARIF / Conformance Score]
```

### 6.2 Structural Report Output Schema
Every execution generates a canonical JSON audit log formatted as follows:

```json
{
  "$schema": "https://raw.githubusercontent.com/tool-contract-validator/schema/v1/report.json",
  "summary": {
    "tool_name": "get_weather_forecast",
    "conformance_score": 94.5,
    "total_tests": 50,
    "passed": 47,
    "failed": 3,
    "duration_ms": 142.8,
    "p95_latency_ms": 12.4,
    "max_rss_mb": 42.1
  },
  "failures": [
    {
      "test_id": "test_boundary_numeric_min_004",
      "input_payload": {"latitude": -95.0, "longitude": 10.0},
      "failure_type": "SCHEMA_VIOLATION",
      "json_path": "$.latitude",
      "error_message": "-95.0 is less than the minimum of -90.0",
      "execution_trace_id": "tr-88f1a2"
    }
  ]
}
```