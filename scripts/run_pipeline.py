#!/usr/bin/env python3
"""Run the five architecture agents sequentially against a scenario HTML file."""

from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, unquote

try:
    from . import pipeline_support as support
except ImportError:
    import pipeline_support as support


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS = (
    ("D1", "Problem & success snapshot", "agent-01-problem-success.md", 4000),
    ("D2", "Architecture options & decision", "agent-02-architecture-options-decision.md", 5000),
    ("D3", "Target-state architecture", "agent-03-target-state-architecture.md", 5000),
    ("D4", "Focused POC / validation", "agent-04-focused-poc-builder.md", 24000),
    ("D5", "Delivery & risk plan", "agent-05-delivery-risk-plan.md", 4000),
)
MAX_SCENARIO_CHARS = 100_000
MAX_OUTPUT_CHARS = 60_000
MAX_ARTIFACT_BYTES = 2_000_000


class ScenarioHTMLExtractor(HTMLParser):
    """Extract readable sectioned text while ignoring navigation and embedded code."""

    ignored_tags = {"script", "style", "nav", "noscript"}
    block_tags = {
        "article", "br", "dd", "div", "dt", "h1", "h2", "h3", "h4", "h5",
        "h6", "li", "ol", "p", "section", "tr", "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignore_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.ignored_tags:
            self.ignore_depth += 1
            return
        if self.ignore_depth:
            return
        if tag == "section":
            section_id = dict(attrs).get("id")
            if section_id:
                self.parts.append(f"\n\n[SECTION: {section_id}]\n")
        elif tag in self.block_tags:
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ignored_tags and self.ignore_depth:
            self.ignore_depth -= 1
            return
        if not self.ignore_depth and tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignore_depth:
            self.parts.append(data)


def extract_scenario_text(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"Scenario HTML file does not exist: {path}")
    source = path.read_text(encoding="utf-8")
    if len(source) > MAX_SCENARIO_CHARS * 4:
        raise ValueError(
            f"Scenario HTML is too large ({len(source)} characters). "
            "Provide the workbook HTML or a trimmed copy under 400,000 characters."
        )
    parser = ScenarioHTMLExtractor()
    parser.feed(source)
    parser.close()
    lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(parser.parts).splitlines()]
    text = "\n".join(line for line in lines if line)
    if not text:
        raise ValueError(f"No readable text found in scenario HTML: {path}")
    if len(text) > MAX_SCENARIO_CHARS:
        raise ValueError(
            f"Extracted scenario text is {len(text)} characters; limit is "
            f"{MAX_SCENARIO_CHARS}. Trim irrelevant workbook content before running."
        )
    return text


def load_prompt(prompt_path: Path) -> str:
    if not prompt_path.is_file():
        raise ValueError(f"Agent prompt file is missing: {prompt_path}")
    content = prompt_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Agent prompt file is empty: {prompt_path}")
    return content


def load_env_file(env_path: Path) -> None:
    """Load simple KEY=VALUE settings without overriding the caller's environment."""
    if not env_path.is_file():
        return
    for line_number, raw_line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"Invalid environment entry at {env_path}:{line_number}; expected KEY=VALUE.")
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"Invalid environment variable name at {env_path}:{line_number}.")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def safe_run_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._")
    return cleaned[:64] or "scenario"


def parse_agent_json(content: str, agent_id: str) -> dict[str, Any]:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, count=1, flags=re.IGNORECASE)
        candidate = re.sub(r"\s*```$", "", candidate, count=1)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{agent_id} returned invalid JSON at line {exc.lineno}, column {exc.colno}. "
            "The pipeline stopped before handing off incomplete output."
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("markdown"), str):
        raise ValueError(f"{agent_id} response must be a JSON object with a markdown string.")
    markdown = data["markdown"].strip()
    if not markdown:
        raise ValueError(f"{agent_id} returned empty Markdown.")
    if len(markdown) > MAX_OUTPUT_CHARS:
        raise ValueError(f"{agent_id} Markdown exceeds the {MAX_OUTPUT_CHARS}-character limit.")
    artifacts = data.get("artifacts", [])
    if agent_id == "D4" and not artifacts:
        raise ValueError(
            "D4 returned no runnable POC artifact. Expected at least one artifact under poc/."
        )
    if not isinstance(artifacts, list):
        raise ValueError(f"{agent_id} artifacts must be a JSON array.")
    if agent_id != 'D4' and artifacts:
        raise ValueError(f'{agent_id} must not return POC artifacts.')
    support.validate_markdown(markdown, agent_id)
    if agent_id == 'D4':
        for item in artifacts:
            validate_artifact(item)
        data['poc'] = support.validate_bundle(artifacts,data.get('poc'),Path.cwd())
    data["markdown"] = markdown
    data["artifacts"] = artifacts
    return data


def validate_artifact(item: Any) -> tuple[Path, str]:
    if not isinstance(item, dict) or not isinstance(item.get("path"), str):
        raise ValueError("Each POC artifact must have string path and content fields.")
    if not isinstance(item.get("content"), str):
        raise ValueError("Each POC artifact must have string path and content fields.")
    relative = support.relative_path(item['path'])
    if relative.suffix.lower() not in {".html", ".css", ".js", ".cjs", ".mjs", ".py", ".json", ".md", ".txt", ".svg"}:
        raise ValueError(f"Unsupported POC artifact extension: {relative.suffix!r}")
    if len(item["content"].encode("utf-8")) > MAX_ARTIFACT_BYTES:
        raise ValueError(f"Generated artifact exceeds {MAX_ARTIFACT_BYTES} bytes.")
    return relative, item["content"]


class CompletionTruncated(RuntimeError):
    pass


class OpenAICompatibleClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 180, retries: int = 2) -> None:
        if not base_url.startswith(("https://", "http://")):
            raise ValueError("API base URL must begin with https:// or http://.")
        if not api_key:
            raise ValueError("API key is empty.")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries

    def request_json(self, request):
        for attempt in range(self.retries+1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    body=json.loads(response.read().decode('utf-8'))
                    if not isinstance(body,dict):raise RuntimeError('Gateway response must be a JSON object.')
                    return body
            except HTTPError as exc:
                if exc.code in {429,500,502,503,504} and attempt < self.retries:
                    time.sleep(min(2**attempt,4));continue
                # Do not echo a gateway body that might contain credentials.
                raise RuntimeError(f'Model gateway returned HTTP {exc.code}. Check access, model support and gateway limits.') from exc
            except (URLError,TimeoutError) as exc:
                if attempt < self.retries:
                    time.sleep(min(2**attempt,4));continue
                raise RuntimeError('Gateway connection failed or timed out. Check the endpoint and network.') from exc
            except (json.JSONDecodeError,UnicodeDecodeError) as exc:
                raise RuntimeError('Gateway returned an invalid JSON response.') from exc

    def check_models(self, required):
        base=self.base_url.removesuffix('/chat/completions')
        result=self.request_json(Request(base+'/models',headers={'Authorization':'Bearer '+self.api_key}))
        available={item.get('id') for item in result.get('data',[]) if isinstance(item,dict)}
        missing=set(required)-available
        if missing:raise ValueError('Gateway does not list selected model IDs: '+', '.join(sorted(missing)))

    @property
    def endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def complete(
        self, *, model: str, system_prompt: str, user_prompt: str, max_tokens: int
    ) -> tuple[str, dict[str, Any]]:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        body = self.request_json(request)
        try:
            message = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Model gateway response did not contain a chat completion.") from exc
        if not isinstance(message, str):
            raise RuntimeError("Model gateway returned a non-text assistant message.")
        reason=body['choices'][0].get('finish_reason')
        if reason == 'length':
            error=CompletionTruncated('Model output was truncated. Increase this stage token budget and resume; incomplete output was not accepted.')
            error.usage=body.get('usage',{})
            raise error
        if reason and reason!='stop':raise RuntimeError('Model did not complete a normal text response: '+str(reason))
        usage = body.get("usage", {})
        return message, usage if isinstance(usage, dict) else {}


def render_inline(text: str) -> str:
    safe = html.escape(text, quote=False)
    safe = re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", safe)
    def link(match):
        label,destination=match.groups()
        decoded=html.unescape(destination)
        parsed=urlsplit(decoded)
        if parsed.scheme not in {'','http','https'} or decoded.startswith(('//','\\')):
            return label
        return '<a href="'+html.escape(decoded,quote=True)+'">'+label+'</a>'
    safe = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, safe)
    return safe


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_tag: str | None = None
    table_rows: list[list[str]] = []
    in_code = False
    code_lang = ""
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_tag
        if list_tag:
            output.append(f"</{list_tag}>")
            list_tag = None

    def flush_table() -> None:
        if not table_rows:
            return
        header = table_rows[0]
        rows = table_rows[1:]
        output.append("<table><thead><tr>" + "".join(
            f"<th>{render_inline(cell)}</th>" for cell in header
        ) + "</tr></thead><tbody>")
        for row in rows:
            output.append("<tr>" + "".join(f"<td>{render_inline(cell)}</td>" for cell in row) + "</tr>")
        output.append("</tbody></table>")
        table_rows.clear()

    def is_table_line(line: str) -> bool:
        return line.strip().startswith("|") and line.strip().endswith("|")

    for line in lines:
        if line.strip().startswith("```"):
            flush_paragraph()
            flush_list()
            flush_table()
            if in_code:
                cls = " class=\"mermaid-source\"" if code_lang.lower() == "mermaid" else ""
                output.append(f"<pre{cls}><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
                code_lang = ""
            else:
                in_code = True
                code_lang = line.strip()[3:].strip()
            continue
        if in_code:
            code_lines.append(line)
            continue
        if is_table_line(line):
            flush_paragraph()
            flush_list()
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
                table_rows.append(cells)
            continue
        flush_table()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = min(len(heading.group(1)) + 1, 6)
            output.append(f"<h{level}>{render_inline(heading.group(2))}</h{level}>")
            continue
        if stripped in {"---", "***", "___"}:
            flush_paragraph()
            flush_list()
            output.append("<hr>")
            continue
        list_match = re.match(r"^([-*+]|\d+[.)])\s+(.+)$", stripped)
        if list_match:
            flush_paragraph()
            next_tag = "ol" if list_match.group(1)[0].isdigit() else "ul"
            if list_tag != next_tag:
                flush_list()
                output.append(f"<{next_tag}>")
                list_tag = next_tag
            output.append(f"<li>{render_inline(list_match.group(2))}</li>")
            continue
        blockquote = re.match(r"^>\s?(.*)$", stripped)
        if blockquote:
            flush_paragraph()
            flush_list()
            output.append(f"<blockquote>{render_inline(blockquote.group(1))}</blockquote>")
            continue
        flush_list()
        paragraph.append(stripped)
    flush_paragraph()
    flush_list()
    flush_table()
    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    return "\n".join(output)


def build_final_html(deliverables: dict[str, str], scenario_name: str, diagram_svg: str = "") -> str:
    try:
        from .pipeline_report import build
    except ImportError:
        from pipeline_report import build
    return build(deliverables, scenario_name, diagram_svg, markdown_to_html)


def context_for_stage(
    agent_id: str, scenario_text: str, previous: dict[str, str], user_poc_question: str | None
) -> str:
    parts = [
        "Return exactly one JSON object with this shape:",
        '{"markdown":"complete deliverable Markdown","artifacts":[]}',
        "For D1, D2, D3, and D5, artifacts must be an empty array.",
        "For D4, artifacts must contain at least one runnable synthetic-data prototype file under poc/, such as "
        '{"path":"poc/exception-triage/index.html","content":"complete file contents"}.',
        "Do not wrap the JSON in a Markdown code fence. Do not use network services or real sensitive data.",
        "\n## Original scenario HTML, extracted as text\n",
        scenario_text,
    ]
    for prior_id, markdown in previous.items():
        parts.extend([f"\n## Upstream draft artifact — human approval not established {prior_id}\n", markdown])
    if agent_id == "D4" and user_poc_question:
        parts.extend(["\n## Team-selected POC question\n", user_poc_question])
    if agent_id == "D4":
        parts.append(
            "\nBuild the POC source file but do not execute it. Report all execution results as NOT RUN unless supplied in verified input evidence. Provide expected outcomes and repeatable test steps, never claim observed results from generated code. Any simulated AI must be labeled as simulation."
        )
        parts.append(
            '\nD4 JSON must also include "poc": {"entrypoint":"poc/application/index.html",'
            '"engine_tests":[{"path":"poc/tests/workflow.cjs","runtime":"node"}],'
            '"browser_test":"poc/tests/browser.cjs"}. Include every referenced local source file and '
            'a README.md. Use self-contained Node/Python engine assertions. The browser_test file must '
            'export module.exports = async ({page, assert, baseURL, root}) => { /* assert the real workflow */ }; '
            'do not launch another browser or require Playwright in generated tests; the trusted harness supplies page. '
            'For a CLI experiment, entrypoint may be .py/.js/.cjs and browser_test must be null. '
            'Use only local runtime dependencies. Markdown artifact links are relative to the run root, '
            'e.g. [Open application](poc/application/index.html). Expected results may be described, '
            'but Observed result cells and Results and learning must say NOT RUN. '
            'The orchestrator may execute tests later and add verified evidence before D5.'
        )
    if agent_id=='D3':
        parts.append(
            '\nOffline diagram renderer contract: exactly one ```mermaid flowchart LR block. '
            'Declare every box separately as ID["Short label"] (optional <br/> for a line break), '
            'then flows as A -->|"Label"| B or A <--> |"Label"| B. '
            'Up to three simple groups: subgraph Group["Title"], box declarations, end. '
            'No nested groups, styles, click directives, shaped nodes, or implicit node declarations. '
            'Use at most ten connected boxes. Optional capabilities/controls belong in brief notes. '
            'Keep all notes and table content within the prompt word budget.'
        )
    parts.append('\nUse exactly the section headings and table columns requested in the stage prompt; return complete source, not an outline.')
    return "\n".join(parts)


def stage_model(args: argparse.Namespace, index: int) -> str:
    explicit = getattr(args, f"model_d{index}", None)
    configured = os.environ.get(f"ARCH_AGENT_{index}_MODEL")
    selected = explicit or configured or args.model
    if not selected:
        raise ValueError(
            f"No model configured for D{index}. Set --model or ARCH_AGENT_{index}_MODEL."
        )
    available_models = getattr(args, "available_models", [])
    if available_models and selected not in available_models:
        raise ValueError(
            f"Model selected for D{index} ({selected}) is not in AVAILABLE_MODELS. "
            "Check the exact model ID supplied by the gateway."
        )
    return selected


def write_artifacts(run_dir: Path, artifacts: list[Any]) -> list[str]:
    written: list[str] = []
    for artifact in artifacts:
        relative, content = validate_artifact(artifact)
        destination = (run_dir / relative).resolve()
        root = run_dir.resolve()
        if destination != root and root not in destination.parents:
            raise ValueError(f"Generated artifact escapes run directory: {relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
        written.append(relative.as_posix())
    return written


def preflight(args, require_gateway=True):
    scenario_path = Path(args.scenario).expanduser().resolve()
    scenario_text = extract_scenario_text(scenario_path)
    prompt_dir = Path(args.prompt_dir).expanduser().resolve()
    prompts = [load_prompt(prompt_dir / name) for _, _, name, _ in AGENTS]
    if args.timeout <= 0 or args.max_context_chars < 1000:
        raise ValueError('Timeout must be positive and context limit at least 1000.')
    budgets = {}
    for index, (stage, _, _, default) in enumerate(AGENTS, 1):
        override = getattr(args, f'max_tokens_d{index}', None)
        cap = getattr(args, 'max_output_tokens', None)
        value = override or (min(cap, default) if cap else default)
        if not 256 <= value <= 64000:
            raise ValueError(f'{stage} output budget must be 256–64000 tokens.')
        budgets[stage] = value
    if not 0 <= getattr(args, 'repair_attempts', 1) <= 2:
        raise ValueError('Repair attempts must be 0–2.')
    if not 0 <= getattr(args, 'http_retries', 2) <= 3:
        raise ValueError('HTTP retries must be 0–3.')
    if not 1 <= getattr(args, 'test_timeout', 60) <= 300:
        raise ValueError('Test timeout must be 1–300 seconds.')
    if isinstance(getattr(args,'available_models',None),str):
        args.available_models = [x.strip() for x in args.available_models.split(',') if x.strip()]
    models = {}
    if require_gateway:
        base = args.base_url
        parsed = urlsplit(base)
        key = os.environ.get(args.api_key_env, '')
        if parsed.scheme not in {'http','https'} or not parsed.hostname or '<' in base or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Configure a valid OPENAI_BASE_URL or --base-url before generation.')
        if not key or '<' in key:
            raise ValueError(f'Configure {args.api_key_env} before generation. Credentials are never printed.')
        models = {stage: stage_model(args,index) for index,(stage,_,_,_) in enumerate(AGENTS,1)}
        if any('<' in model for model in models.values()):
            raise ValueError('Replace placeholder model IDs with gateway model IDs.')
    runtime = support.runtime_paths(args)
    return scenario_path, scenario_text, prompts, models, budgets, runtime


def run_pipeline(args: argparse.Namespace) -> Path:
    scenario_path, scenario_text, prompts, models, budgets, runtime = preflight(args)
    client = OpenAICompatibleClient(args.base_url, os.environ[args.api_key_env], args.timeout,
                                    getattr(args,'http_retries',2))
    if getattr(args,'check_gateway',False):client.check_models(models.values())
    scenario_hash = support.sha(scenario_path.read_bytes())
    prompt_hashes = {stage:support.sha(prompt) for (stage,_,_,_),prompt in zip(AGENTS,prompts)}
    execute = getattr(args,'execute_poc_tests',False)
    resume = getattr(args,'resume',None)
    if resume:
        run_dir = Path(resume).expanduser().resolve()
        manifest = json.loads((run_dir/'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('scenario_sha256') != scenario_hash or manifest.get('prompt_sha256') != prompt_hashes:
            raise ValueError('Scenario or prompts changed; start a new run instead of resuming stale decisions.')
        if manifest.get('models') != models:
            raise ValueError('Resume requires the same model choices.')
        if manifest.get('execute_poc_tests') and not execute:
            raise ValueError('Resume an executed run with --execute-poc-tests; evidence cannot be silently downgraded.')
        if execute and not manifest.get('execute_poc_tests'):
            # Explicitly promoting a reviewed, generated bundle invalidates the
            # unexecuted D5/report evidence. Verify old artifacts before reuse.
            saved=manifest['stages'].get('D4')
            if saved:
                for name,digest in saved.get('artifact_sha256',{}).items():
                    if support.sha((run_dir/support.relative_path(name)).read_bytes())!=digest:
                        raise ValueError('Reviewed POC source changed. Start a new run so decisions and evidence match.')
                saved['status']='tests_pending'
                manifest['stages'].pop('D5',None)
            manifest['execute_poc_tests']=True
    else:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
        run_dir = Path(args.output_dir).expanduser().resolve() / (safe_run_name(scenario_path.stem)+'-'+stamp+'-'+uuid.uuid4().hex[:6])
        run_dir.mkdir(parents=True,exist_ok=False)
        manifest = {'version':2,'status':'running','scenario':str(scenario_path),'scenario_sha256':scenario_hash,
            'prompt_sha256':prompt_hashes,'models':models,'execute_poc_tests':execute,
            'run_started_utc':datetime.now(timezone.utc).isoformat(),'stages':{},'attempts':[],
            'artifacts':[],'usage_reported_by_gateway':{},'cost_note':'Generation/repair/retries may incur gateway charges; enforce the spend limit at the gateway.'}
    manifest['token_budgets'] = budgets
    manifest['status']='running'
    manifest.pop('error',None)
    def checkpoint():support.write_json(run_dir/'manifest.json',manifest)
    checkpoint()
    previous = {}
    evidence = None
    current = 'preflight'
    try:
        # Validate saved stage data against hashes before reusing any of it.
        for stage, _, _, _ in AGENTS:
            saved=manifest['stages'].get(stage)
            if not saved or saved.get('status')!='complete':break
            response_path=run_dir/(stage+'.response.json')
            if support.sha(response_path.read_bytes()) != saved['response_sha256']:
                raise ValueError(f'{stage} saved response changed; cannot safely resume.')
            response=parse_agent_json(response_path.read_text(encoding='utf-8'),stage)
            md=(run_dir/(stage+'.md')).read_text(encoding='utf-8').strip()
            if support.sha(md) != saved['markdown_sha256']:raise ValueError(f'{stage} Markdown changed; cannot safely resume.')
            for name,digest in saved.get('artifact_sha256',{}).items():
                if support.sha((run_dir/support.relative_path(name)).read_bytes())!=digest:
                    raise ValueError('Saved POC artifact changed: '+name)
            previous[stage]=md
            if stage=='D4':
                manifest['poc']=response['poc']
                if execute:
                    ep=run_dir/'poc-validation.json'
                    if support.sha(ep.read_bytes()) != saved.get('evidence_sha256'):raise ValueError('D4 evidence changed; cannot safely resume.')
                    evidence=json.loads(ep.read_text(encoding='utf-8'))
        for index, ((stage,title,_,_),system_prompt) in enumerate(zip(AGENTS,prompts),1):
            current=stage
            if stage in previous:continue
            cached=run_dir/(stage+'.response.json')
            response=None
            saved=manifest['stages'].get(stage,{})
            if stage=='D4' and saved.get('status')=='tests_pending':
                if support.sha(cached.read_bytes())!=saved['response_sha256']:raise ValueError('Pending D4 response changed.')
                response=parse_agent_json(cached.read_text(encoding='utf-8'),stage)
                for name,digest in saved.get('artifact_sha256',{}).items():
                    if support.sha((run_dir/support.relative_path(name)).read_bytes())!=digest:
                        raise ValueError('Pending POC source changed; start a new run rather than overwriting edits.')
            if response is None:
                base_context=context_for_stage(stage,scenario_text,previous,args.poc_question)
                if stage=='D5':
                    base_context+='\n## Verified POC execution status\n'+json.dumps(evidence or {'status':'NOT RUN','reason':'Test execution was not enabled.'})
                repair=''
                for attempt in range(getattr(args,'repair_attempts',1)+1):
                    user_prompt=base_context+repair
                    if len(system_prompt)+len(user_prompt)>args.max_context_chars:
                        raise ValueError(f'{stage} exceeds --max-context-chars before the model call; shorten input or raise the limit.')
                    print(f'[{stage}/5] Generating {title} (attempt {attempt+1})...',flush=True)
                    manifest['active_stage']=stage;checkpoint()
                    record={'stage':stage,'attempt':attempt+1,'started_at':datetime.now(timezone.utc).isoformat()}
                    try:
                        raw,usage=client.complete(model=models[stage],system_prompt=system_prompt,user_prompt=user_prompt,max_tokens=budgets[stage])
                        record['usage']=usage
                        record['response_file']=stage+'.attempt-'+str(len(manifest['attempts'])+1)+'.json'
                        support.atomic_text(run_dir/record['response_file'],raw)
                        response=parse_agent_json(raw,stage)
                        if stage=='D3':
                            support.atomic_text(run_dir/'D3.candidate.md',response['markdown'])
                            try:support.run_node(runtime,'diagram',run_dir/'D3.candidate.md',run_dir/'architecture.svg')
                            except RuntimeError as exc:raise ValueError('D3 diagram validation: '+str(exc)) from exc
                        if stage=='D4':
                            support.validate_bundle(response['artifacts'],response['poc'],run_dir)
                            candidates=write_artifacts(run_dir/'candidate',response['artifacts'])
                            support.static_check_bundle(run_dir/'candidate',candidates,runtime)
                            # D4 generation has not executed tests yet. Evidence is added by the runner only.
                            results=dict(support.sections(response['markdown']))['Results and learning']
                            if not re.search(r'not[ _-]?run',results,re.I) or re.search(r'\b(?:tests?|checks?)\s+passed\b|\bPASS\b',results,re.I):
                                raise ValueError('Generated D4 results must be NOT RUN, not claimed PASS.')
                        if stage=='D5' and evidence is None and re.search(r'\b(?:tests?|checks?)\b.{0,30}\bpassed\b|\bverified execution\b',response['markdown'],re.I):
                            raise ValueError('D5 cannot claim executed checks when POC status is NOT RUN.')
                        record['status']='accepted';manifest['attempts'].append(record);checkpoint();break
                    except (ValueError,CompletionTruncated) as exc:
                        if getattr(exc,'usage',None):record['usage']=exc.usage
                        record['status']='rejected';record['error']=str(exc);manifest['attempts'].append(record);checkpoint()
                        if isinstance(exc,CompletionTruncated) or attempt>=getattr(args,'repair_attempts',1):raise
                        repair='\n## Correct the rejected response\n'+str(exc)+'\nReturn the complete corrected JSON and all source artifacts. Do not claim execution results.'
            support.atomic_text(cached,json.dumps(response,ensure_ascii=False))
            md=response['markdown']
            artifact_hashes={}
            if stage=='D4':
                manifest['artifacts']=write_artifacts(run_dir,response['artifacts'])
                support.static_check_bundle(run_dir,manifest['artifacts'],runtime)
                artifact_hashes={name:support.sha((run_dir/support.relative_path(name)).read_bytes()) for name in manifest['artifacts']}
                manifest['poc']=response['poc']
                manifest['stages'][stage]={'status':'tests_pending','response_sha256':support.sha(cached.read_bytes()),'artifact_sha256':artifact_hashes}
                checkpoint()
                if execute:
                    evidence=support.execute_poc(run_dir,response['poc'],runtime,getattr(args,'test_timeout',60))
                else:
                    evidence=None
                    support.write_json(run_dir/'poc-validation.json',{'status':'NOT RUN','reason':'Generated code was not executed. Enable --execute-poc-tests after reviewing source.','artifactSha256':artifact_hashes})
                md=support.with_execution_evidence(md,evidence)
            support.validate_markdown(md,stage)
            support.atomic_text(run_dir/(stage+'.md'),md+'\n')
            previous[stage]=md
            manifest['stages'][stage]={'status':'complete','response_sha256':support.sha(cached.read_bytes()),'markdown_sha256':support.sha(md),
                'artifact_sha256':artifact_hashes}
            if stage=='D4':manifest['stages'][stage]['evidence_sha256']=support.sha((run_dir/'poc-validation.json').read_bytes())
            manifest['usage_reported_by_gateway'][stage]=[r.get('usage',{}) for r in manifest['attempts'] if r['stage']==stage]
            checkpoint()
            print(f'[{stage}/5] Saved and validated {stage}.md',flush=True)
            if args.interactive and index<5:
                if input(f'Review {stage}.md; Enter continues, q pauses: ').strip().lower()=='q':
                    manifest['status']='paused';checkpoint();print('Paused. Resume directory: '+str(run_dir));return run_dir
        current='report'
        # Always regenerate from the saved source, never from a different hand-drawn diagram.
        support.run_node(runtime,'diagram',run_dir/'D3.md',run_dir/'architecture.svg')
        report=build_final_html(previous,scenario_path.name,(run_dir/'architecture.svg').read_text(encoding='utf-8'))
        pack='\n\n---\n\n'.join(previous.values())+'\n'
        for name in ['final-pack.md','final-submission-report.md']:support.atomic_text(run_dir/name,pack)
        for name in ['final-pack.html','final-submission-report.html']:support.atomic_text(run_dir/name,report)
        support.atomic_text(run_dir/'README.md',
            '# Generated submission\n\nOpen final-submission-report.html. D1.md–D5.md are its source. '+
            'The architecture SVG is rendered from D3. POC entrypoint: `'+manifest['poc']['entrypoint']+'`.\n\n'+
            'POC execution status: '+('PASS' if evidence else 'NOT RUN')+'. See poc-validation.json and the POC README for setup and checks. '+
            'Generated code execution is opt-in and is not a sandbox. Local prototype evidence does not establish operational approval.\n')
        qa=support.run_node(runtime,'report',run_dir/'final-submission-report.html',run_dir)
        support.write_json(run_dir/'report-validation.json',qa)
        manifest['status']='complete';manifest['report_validation']='PASS';manifest['poc_execution']='PASS' if evidence else 'NOT RUN'
        manifest['finished_at']=datetime.now(timezone.utc).isoformat();manifest.pop('active_stage',None);checkpoint()
        print('Complete. Final report: '+str(run_dir/'final-submission-report.html'))
        return run_dir
    except (Exception,KeyboardInterrupt) as exc:
        manifest['status']='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed'
        manifest['active_stage']=current;manifest['error']=str(exc);checkpoint()
        print('Run preserved. Resume directory: '+str(run_dir),file=sys.stderr)
        raise


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run five architecture agents sequentially on a workbook-style scenario HTML."
    )
    parser.add_argument("scenario", help="Path to the scenario HTML workbook.")
    parser.add_argument(
        "--env-file",
        default=str(PROJECT_ROOT / ".env"),
        help="Environment file to load (default: project .env; shell variables take precedence).",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", ""),
        help="OpenAI-compatible API base URL, e.g. https://approved-gateway.example/v1",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="Environment variable containing the approved gateway key (default: OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", ""),
        help="Fallback model ID. Agent-specific env vars/flags override this.",
    )
    parser.add_argument(
        "--available-models",
        default=os.environ.get("AVAILABLE_MODELS", ""),
        help="Comma-separated allowlist of model IDs supplied by the gateway.",
    )
    for index in range(1, 6):
        parser.add_argument(
            f"--model-d{index}",
            dest=f"model_d{index}",
            default=None,
            help=f"Model override for D{index}; alternatively set ARCH_AGENT_{index}_MODEL.",
        )
    parser.add_argument(
        "--prompt-dir",
        default=str(PROJECT_ROOT / "prompts"),
        help="Directory containing the five agent prompt Markdown files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "output" / "runs"),
        help="Directory for timestamped run artifacts.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=None,
        help="Optional global token cap; per-stage overrides take precedence.",
    )
    for index in range(1,6):
        parser.add_argument(f'--max-tokens-d{index}',type=int,help='Stage output budget, 256–64000 tokens.')
    parser.add_argument('--node-path',help='Node executable; alternatively PIPELINE_NODE.')
    parser.add_argument('--node-modules',help='Directory containing @viz-js/viz and playwright; alternatively PIPELINE_NODE_MODULES.')
    parser.add_argument('--execute-poc-tests',action='store_true',help='Explicitly execute generated engine/browser tests before D5. Review source first; not a sandbox.')
    parser.add_argument('--test-timeout',type=int,default=60,help='Per-test timeout in seconds, maximum 300.')
    parser.add_argument('--resume',help='Resume a preserved run directory; scenario, prompts, models and execution mode must match.')
    parser.add_argument('--repair-attempts',type=int,default=1,help='Bounded model regeneration after content validation failure, 0–2; may incur charges.')
    parser.add_argument('--http-retries',type=int,default=2,help='Transient gateway retry limit, 0–3.')
    parser.add_argument('--check-gateway',action='store_true',help='Check selected model IDs using the gateway /models endpoint; no completion request.')
    parser.add_argument('--offline-check',action='store_true',help='With --validate-only, check scenario/prompts/local runtimes without gateway credentials.')
    parser.add_argument(
        "--max-context-chars",
        type=int,
        default=120_000,
        help="Fail before calling the model if a stage prompt exceeds this character count.",
    )
    parser.add_argument("--timeout", type=int, default=180, help="Per-call timeout in seconds.")
    parser.add_argument(
        "--poc-question",
        help="Optional human-selected validation question to pass to D4.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Pause after each deliverable for human review before continuing.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Preflight all five model settings and local render runtimes; no generation calls. Use --offline-check for local checks only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    env_parser = argparse.ArgumentParser(add_help=False)
    env_parser.add_argument("--env-file", default=str(PROJECT_ROOT / ".env"))
    env_args, _ = env_parser.parse_known_args(argv)
    try:
        load_env_file(Path(env_args.env_file).expanduser().resolve())
    except (OSError, ValueError) as exc:
        print(f"Pipeline configuration error: {exc}", file=sys.stderr)
        return 1

    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        if args.offline_check and not args.validate_only:
            raise ValueError('--offline-check requires --validate-only.')
        if args.offline_check and args.check_gateway:
            raise ValueError('--offline-check cannot be combined with --check-gateway.')
        if args.validate_only:
            scenario, _, _, models, budgets, runtime = preflight(args, not args.offline_check)
            support.run_node(runtime,'preflight')
            if args.check_gateway:
                OpenAICompatibleClient(args.base_url,os.environ[args.api_key_env],args.timeout,args.http_retries).check_models(models.values())
            print('Local preflight passed: scenario, five prompts, Node graph renderer and browser runtime.')
            if args.offline_check:
                print('Gateway readiness was not checked. No model generation occurred.')
            else:
                print('All five model settings and credentials configured. '+
                      ('Gateway model list verified.' if args.check_gateway else 'Connectivity not tested; use --check-gateway.'))
            return 0
        run_pipeline(args)
        return 0
    except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as exc:
        print('Pipeline stopped: '+str(exc),file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
