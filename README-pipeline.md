# Scenario-to-submission pipeline

The runner reads a scenario HTML workbook, generates D1–D5 using the five revised prompts, saves the complete POC source, renders D3 as a diagram, and creates a checked HTML/PDF submission. It is scenario-neutral: a new scenario does not need healthcare-specific render scripts.

## First-time setup on another system

Start with [README.md](README.md), which contains the GitHub/VS Code setup and complete Windows/macOS/Linux installation commands. Codex is optional; the runner uses Python, Node, your installed browser and your gateway directly.

On Windows, install Python 3.10+ and Node 20+ with npm, then run from the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci
npm run install:browsers
Copy-Item .env.example .env
```

Use `python -m venv .venv` if the Python launcher is unavailable. Copy `.env.example` only on a fresh checkout; retain an existing configured `.env`. Edit it with key, base URL and each agent's exact model ID. Do not copy a virtual environment or node_modules from another machine. `requirements.txt` covers Python; `package.json` and `package-lock.json` cover Node. The browser is an additional one-time download.

## Requirements and gateway setup

- Python 3.10+ (create a fresh `.venv` on each machine).
- An approved OpenAI-compatible Chat Completions gateway supporting JSON-object responses.
- Exact model IDs and credentials from your gateway administrator.
- Node 20+, `@viz-js/viz` and Playwright installed with `npm ci`, plus Chromium installed with `npm run install:browsers`. Existing Edge is a fallback. No third-party Python packages are currently required.

Copy `.env.example` to `.env`, then populate `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `ARCH_AGENT_1_MODEL` through `ARCH_AGENT_5_MODEL`. `OPENAI_MODEL` is an optional shared fallback. `AVAILABLE_MODELS` is an optional exact-ID allowlist. Shell settings take precedence over `.env`; `--env-file` selects another file. Never put keys in scenario or POC files.

Node is found on PATH and project-local node_modules are preferred. Codex's bundled runtimes are only a fallback if available. Discovery can be overridden with `--node-path`, `--node-modules`, or `PIPELINE_NODE` / `PIPELINE_NODE_MODULES`. The module directory must contain both packages. `PIPELINE_BROWSER_CHANNEL` defaults to `auto`, preferring installed Playwright Chromium and falling back to Edge. `chromium` requires the downloaded Chromium browser; `msedge` requires installed Edge. These paths and choices are not tied to a username.

## 1. Put the scenario in input

For example, save `input/new-scenario.html`. Static readable HTML is supported. Text is extracted while scripts, styles and navigation are ignored; JavaScript-rendered-only pages, PDF/Word input, and facts embedded only in images require conversion first. The source is limited to 400,000 characters and extracted text to 100,000; trim irrelevant appendices if needed. The prompts distinguish business facts from workshop instructions and reference material, but business accuracy still requires human review.

## 2. Check readiness before spending on generation

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/run_pipeline.py input/new-scenario.html --validate-only
```

This checks the scenario, five prompt files, all five model choices, credential/endpoint configuration, and the installed graph/browser runtimes. It does not generate content. Missing settings cause failure rather than a misleading successful readiness message.

To check only local input and tools before credentials are available:

```powershell
.\.venv\Scripts\python.exe scripts/run_pipeline.py input/new-scenario.html --validate-only --offline-check
```

To also verify the gateway's model list, add `--check-gateway` to the regular readiness command. This uses authenticated `GET /models`, without a model completion request. A gateway that does not expose that route cannot pass this optional connectivity check. Configuration checks alone cannot establish live model quality, JSON support, account limits, or generation feasibility.

## 3. Generate a submission

```powershell
.\.venv\Scripts\python.exe scripts/run_pipeline.py input/new-scenario.html
```

Use `--interactive` to review each saved deliverable and pause with `q`. A paused or failed run prints its directory. Specify `--poc-question "Your architecture question"` if you want to select the proof's focus.

The default saves and statically checks generated code but does not execute it. D4 and D5 explicitly receive **NOT RUN** evidence. Report rendering/quality checks run automatically because they use trusted renderer code and escaped deliverable text, not the generated POC.

## 4. Review source, then optionally execute POC tests

After reviewing the POC source and README in the run directory, promote the run using its actual directory:

```powershell
.\.venv\Scripts\python.exe scripts/run_pipeline.py input/new-scenario.html --resume "output/runs/<actual-run-directory>" --execute-poc-tests
```

This executes the supplied engine tests and browser test, updates D4 with verified evidence, regenerates D5 against that evidence, and rebuilds/checks the report. Completed D1–D3 are reused rather than requested again. Alternatively, supply `--execute-poc-tests` on the initial run only if you intend to authorize execution of the generated tests without that separate review step.

Generated code execution is **not an OS sandbox**: engine/browser-test modules run with the current user's permissions. The browser uses an isolated profile and its requests are restricted to the harness's loopback origin; that does not restrict arbitrary Node/Python code inside generated tests. Use approved, non-sensitive synthetic inputs and review the source. Failed tests stop before D5 and save failure evidence. Counts represent test-script execution checks, not a fabricated count of individual assertions.

The harness serves generated files on loopback for browser validation and closes the server afterward. It does not install generated dependencies or contact real partner systems. Python tests use the runner's interpreter; Node tests use the configured Node executable. Test timeouts default to 60 seconds (`--test-timeout`, maximum 300).

## Outputs

Each run is isolated under `output/runs/<scenario>-<UTC-timestamp>-<unique-id>/`:

```text
D1.md ... D5.md                   Validated source deliverables
D1.response.json ...             Saved model responses for recovery
poc/                             Runnable source, tests, and README
poc-validation.json              PASS / FAIL / NOT RUN with source hashes
architecture.svg                 Rendered directly from D3
final-submission-report.md       Combined source document
final-submission-report.html     Five-section readable report
final-submission-report.pdf      Checked printable report
page-1.png ... page-5.png         Page previews
report-validation.json           Links, diagram, screen/print layout results
manifest.json                    Progress, models, attempts, usage and hashes
README.md                        Run-specific entrypoint and evidence status
```

`final-pack.md` and `final-pack.html` are compatibility copies. Current manually reviewed artifacts under `output/healthcare` are not overwritten by a new pipeline run. The older `render_d1_review.py`–`render_d5_review.py` helpers are for that existing pack, not the scenario-neutral orchestration path.

The report includes clickable POC/documentation links and an embedded SVG, with no CDN or online diagram dependency. Quality checks verify all local links, desktop/mobile width, five printed pages, footer overlap, script errors, and a rendered diagram. A layout failure leaves the run **failed**, even if HTML was written; inspect the manifest before treating output as final. Print content is not hidden to mask overflow. If a new model output is too dense, reduce content and start a new run rather than treating a clipped draft as complete.

## Enforced output contracts

- Exact prompt sections and word budgets; D1 has 3–5 assumptions/4–6 measures, D2 has 6–8 comparison rows, D5 has one three-phase roadmap and five risks.
- Only D4 can return POC artifacts. It must declare an executable entrypoint, all local supporting sources, a README, engine tests, and a browser test for HTML applications.
- Missing references, case-insensitive duplicate paths, traversal/Windows reserved paths, external runtime dependencies and invalid Python/JavaScript are rejected. Static checking does not prove runtime correctness.
- D3 uses a deliberately small offline-renderable Mermaid subset: `flowchart LR`, separately declared `ID["Label"]` boxes, labeled `-->`/`<-->` flows, at most three simple groups and ten connected boxes. The stage context supplies this contract. Unsupported Mermaid syntax fails explicitly; it is not replaced silently by a different architecture.
- Browser tests export `module.exports = async ({page, assert, baseURL, root}) => { ... }`; the trusted harness supplies the browser. CLI experiments may use Python/Node entrypoints without a browser test.
- Generated D4 results must be NOT RUN; only actual execution adds PASS evidence. D5 is given that evidence before it is generated. Tests that mutate their source are rejected.

## Recovery, budgets and retry behavior

Resume a failed/paused run with `--resume` and the same scenario, prompts and model choices. Completed response/Markdown/artifact hashes are checked before reuse. A report-only failure can resume without new model calls. A POC-test failure can rerun the preserved tests without regenerating D4. The source must still match; edited source or changed scenario/prompts requires a new run so stale decisions are not silently reused. Previously executed runs require `--execute-poc-tests` on resume; evidence is not silently downgraded.

Progress is checkpointed after each accepted stage; failures preserve the manifest and identify the active stage. Run names have microseconds and a unique suffix to avoid collisions. Rejected response attempts and reported token usage are retained. There is no guaranteed dollar ceiling: enforce the budget at the gateway.

Default stage token budgets are D1 4,000; D2 5,000; D3 5,000; D4 24,000; D5 4,000. `--max-tokens-d1` through `--max-tokens-d5` can override them up to 64,000. `--max-output-tokens` sets a global cap unless a per-stage override is supplied. Truncated responses are rejected; increase the relevant budget and resume. `--max-context-chars` defaults to 120,000 and prevents an oversized stage request before that call.

Content validation gets one corrective generation attempt by default (`--repair-attempts`, 0–2). Transient gateway errors get two retries (`--http-retries`, 0–3). These requests may incur charges; a timeout can be billed without reported usage. Authentication/model errors are not endlessly retried, and response error bodies/credentials are not printed.

## Validate the implementation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/validate_pipeline_integration.py
```

Unit tests cover structure/artifact validation, client responses, retries, evidence hand-offs, saved hashes, interruption recovery, promotion after source review and report failures. The offline integration uses deterministic warehouse-scenario model fixtures and the actual graph/browser adapters, generated engine/browser tests, and five-page report QA. It makes no external or paid model request. Integration output is saved under `.review/pipeline-integration`; that proves orchestration behavior, not real gateway access or model reasoning quality.
