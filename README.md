# Scenario architecture pipeline

Turn a scenario HTML file into five architecture deliverables, a POC source bundle, and a checked final HTML/PDF report. VS Code, Codex, or any text editor can be used. **Codex is not required to run the pipeline**: it is a Python command-line application using your configured model gateway.

## What to install once on the new machine

- Python **3.10 or newer**, with pip and virtual-environment support.
- Node.js **20 or newer**, with npm (a supported LTS release is recommended).
- The Node packages in `package.json` / `package-lock.json`.
- Playwright's Chromium browser, installed by the command below. Existing Edge is an optional fallback, not a requirement.
- Access to your approved OpenAI-compatible Chat Completions gateway, supporting JSON-object responses and the selected models. The machine must be able to reach it.

Python dependencies are listed in `requirements.txt`; currently only the standard library is used. Node dependencies cannot be installed with pip: they are declared separately in `package.json`, with exact resolved versions in `package-lock.json`.

## Clean-machine setup — Windows / PowerShell

Download or clone the repository, open its folder in VS Code, and open **Terminal → New Terminal**. Run these commands from the repository root:

```powershell
py -3 --version
node --version
npm --version
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci
npm run install:browsers
Copy-Item .env.example .env
```

If the `py` launcher is unavailable but Python is installed, use `python -m venv .venv`. The explicit virtual-environment interpreter avoids PowerShell activation-policy issues. On a fresh clone `.env` does not exist; do not copy over an already configured `.env`.

Use `npm install` only if intentionally updating dependency versions, then commit the reviewed lockfile change. For a fresh machine use `npm ci` to reproduce the committed dependencies. Package/browser installation requires access to the relevant download endpoints or an organization-provided mirror/proxy.

### macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci
npm run install:browsers
cp .env.example .env
```

On supported Linux distributions, if browser system libraries are missing, use `npm run install:browsers:linux`; that installs Chromium with its OS dependencies and may require administrator privileges. Substitute `.venv/bin/python` for the Windows interpreter in the run commands below. The pipeline needs no Codex installation on these systems either.

## Configure your models

Edit `.env` with your approved values:

```dotenv
OPENAI_BASE_URL=https://<approved-gateway>/v1
OPENAI_API_KEY=<your-key>
AVAILABLE_MODELS=<model-a>,<model-b>,<model-c>,<model-d>,<model-e>
ARCH_AGENT_1_MODEL=<model-a>
ARCH_AGENT_2_MODEL=<model-b>
ARCH_AGENT_3_MODEL=<model-c>
ARCH_AGENT_4_MODEL=<model-d>
ARCH_AGENT_5_MODEL=<model-e>
```

Replace every placeholder with an exact gateway model ID. Each agent can use a different model. Select sufficient reasoning/coding capability and output-token capacity, especially for D4's complete application source. Environment variables already set in the terminal override `.env`; remove stale overrides if your edits seem ineffective.

You normally do **not** need `PIPELINE_NODE`, `PIPELINE_NODE_MODULES`, or a custom browser channel. Node is found on PATH, project-local packages are detected automatically, and Chromium installed by `npm run install:browsers` is preferred. Set `PIPELINE_BROWSER_CHANNEL=chromium` to require that browser; `msedge` selects installed Edge.

## Each new scenario — three steps

1. Save the static readable HTML scenario as `input/new-scenario.html` (any filename is fine).
2. Check settings and installed tools:

   ```powershell
   .\.venv\Scripts\python.exe scripts/run_pipeline.py input/new-scenario.html --validate-only
   ```

3. Generate the deliverables, POC source and checked report:

   ```powershell
   .\.venv\Scripts\python.exe scripts/run_pipeline.py input/new-scenario.html
   ```

Open the printed output directory under `output/runs/`. It contains `D1.md`–`D5.md`, the runnable `poc/` bundle and its README, `architecture.svg`, `final-submission-report.html`, `final-submission-report.pdf`, page previews, validation evidence and a progress manifest. The POC's own README explains its entrypoint and usage. The pipeline does not replace the existing healthcare examples.

By default, POC source is generated and statically checked but **not executed**. After reviewing it, execute its tests and regenerate the evidence-based report:

```powershell
.\.venv\Scripts\python.exe scripts/run_pipeline.py input/new-scenario.html --resume "output/runs/<actual-run-directory>" --execute-poc-tests
```

Generated tests run with your user's permissions; this option is not a security sandbox. The report always runs trusted layout/link checks. If a generation, test or layout check fails, inspect `manifest.json` and follow the printed resume instructions. **Only a run marked `complete` is the checked final output.**

## Before uploading to GitHub

Commit the source, `prompts/`, `scripts/`, `tests/`, source POC/examples you want to retain, `requirements.txt`, `package.json`, `package-lock.json`, README files and `.env.example`.

Do not upload `.env`, `.venv/`, `node_modules/`, Python caches, `.review/` or generated `output/runs/`. `.gitignore` excludes them for Git-based uploads. If using GitHub's browser upload, select files explicitly because that upload does not apply local ignore rules. `.gitignore` does not remove files already tracked by Git; check the selected/staged file list before pushing.

Virtual environments and installed packages are recreated on the target machine, not copied between machines. Keep any confidential scenarios/generated content out of a public repository; only upload approved examples.

## Optional checks before your first real model run

```powershell
.\.venv\Scripts\python.exe scripts/run_pipeline.py input/scenario-healthcare.html --validate-only --offline-check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/validate_pipeline_integration.py
```

These offline checks use deterministic model fixtures; they do not spend on a gateway. The optional `--validate-only --check-gateway` checks the model-list endpoint, but successful model generation still depends on gateway behavior, credentials, compatible model settings and account limits. Set an appropriate spend limit at your gateway; repairs/retries can add requests.

See [the complete pipeline guide](README-pipeline.md) for runtime overrides, supported HTML, generation contracts, resume rules, token budgets and troubleshooting.

Official installation references: [Playwright browsers](https://playwright.dev/docs/browsers), [Viz.js](https://github.com/mdaines/viz-js), [Node.js](https://nodejs.org/en/download), [Python](https://www.python.org/downloads/).
