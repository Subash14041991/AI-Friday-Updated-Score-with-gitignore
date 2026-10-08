"""Scenario-neutral validation, runtime discovery, and run evidence helpers."""
from __future__ import annotations

import hashlib
import ast
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = {
    'D1': ['Problem statement','People and current process','Key constraints','Assumptions to validate','Success measures','Open questions','Handoff to D2'],
    'D2': ['Decision context','Option A','Option B','Trade-off comparison','Preferred direction','Decision dependencies and revisit triggers','Handoff to D3'],
    'D3': ['Architecture view','Major components and responsibilities','Integration and data','AI and human control','Security and resilience','Design assumptions and validation points','Alignment to D2'],
    'D4': ['Question and hypothesis','Scope and safety','Prototype','Test method','Results and learning','Limitations and what remains unproven','Handoff to D5'],
    'D5': ['Now / Next / Later roadmap','Top five risks and mitigations','AI-use reflection','Delivery guardrails'],
}
LIMITS = {'D1':750,'D2':750,'D3':550,'D4':600,'D5':600}

def sha(value: bytes | str) -> str:
    return hashlib.sha256(value.encode('utf-8') if isinstance(value,str) else value).hexdigest()

def atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(content,encoding='utf-8',newline='\n')
    temp.replace(path)

def write_json(path: Path, value) -> None:
    atomic_text(path,json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def sections(markdown: str) -> list[tuple[str,str]]:
    # Fenced code must never be interpreted as deliverable headings.
    found=[]; heading=None; body=[]; fenced=False
    for line in markdown.splitlines():
        if line.strip().startswith('```'): fenced=not fenced
        match=None if fenced else re.match(r'^#{2,6}\s+(.+?)\s*$',line)
        if match:
            if heading is not None: found.append((heading,'\n'.join(body).strip()))
            heading=match.group(1);body=[]
        elif heading is not None: body.append(line)
    if heading is not None: found.append((heading,'\n'.join(body).strip()))
    return [(h,b) for h,b in found if not re.match(r'^D[1-5][.\s]',h)]

def table_rows(content: str) -> list[list[str]]:
    rows=[]
    for line in content.splitlines():
        if not line.strip().startswith('|'):continue
        cells=[c.strip() for c in re.split(r'(?<!\\)\|',line.strip().strip('|'))]
        if all(re.fullmatch(r':?-{3,}:?',c.replace(' ','')) for c in cells):continue
        rows.append(cells)
    return rows

def validate_markdown(markdown: str, stage: str) -> None:
    found=sections(markdown); expected=SECTIONS[stage]
    names=[name for name,_ in found]
    if stage=='D2':
        option_names=[name for name in names if re.match(r'^Option [A-D](?:$|\s)',name)]
        if not 2<=len(option_names)<=4:raise ValueError('D2 requires at least two credible options (maximum four).')
        expected=['Decision context']+['Option '+chr(65+i) for i in range(len(option_names))]+SECTIONS[stage][3:]
    if stage=='D1' and 'Open questions' not in names:
        expected=[x for x in expected if x!='Open questions']
    valid=len(names)==len(expected) and all(
        actual.startswith(wanted+' — ') or actual.startswith(wanted+' - ') or actual==wanted
        for actual,wanted in zip(names,expected))
    if not valid:raise ValueError(f'{stage} requires these sections in order: '+', '.join(expected))
    if any(not body for _,body in found):raise ValueError(f'{stage} has an empty required section.')
    plain=re.sub(r'```.*?```','',markdown,flags=re.S)
    if len(plain.split())>LIMITS[stage]:raise ValueError(f'{stage} exceeds its {LIMITS[stage]}-word limit.')
    by_name={wanted:body for wanted,(_,body) in zip(expected,found)}
    if stage=='D1':
        count=len(re.findall(r'^\s*\d+[.)]\s+',by_name['Assumptions to validate'],re.M))
        if not 3<=count<=5:raise ValueError('D1 needs 3–5 numbered assumptions.')
        rows=table_rows(by_name['Success measures'])
        if not 5<=len(rows)<=7 or any(len(r)!=5 for r in rows):raise ValueError('D1 needs 4–6 measures with five columns.')
    if stage=='D2':
        rows=table_rows(by_name['Trade-off comparison'])
        width=len(option_names)+1
        if not 7<=len(rows)<=9 or any(len(r)!=width for r in rows):raise ValueError('D2 needs 6–8 comparison rows with one column per option plus criterion.')
    if stage=='D3':
        diagrams=re.findall(r'```mermaid\s*\n(.*?)```',markdown,re.S)
        if len(diagrams)!=1:raise ValueError('D3 needs exactly one Mermaid architecture diagram.')
    if stage=='D5':
        for name,count,width in [('Now / Next / Later roadmap',3,4),('Top five risks and mitigations',5,3)]:
            rows=table_rows(by_name[name])
            if len(rows)!=count+1 or any(len(r)!=width for r in rows):raise ValueError(f'D5 {name} needs {count} rows and {width} columns.')
        phases=[re.sub(r'[*_]', '',r[0]).strip().lower() for r in table_rows(by_name['Now / Next / Later roadmap'])[1:]]
        if not all(actual.startswith(wanted) for actual,wanted in zip(phases,['now','next','later'])):raise ValueError('D5 roadmap phases must be Now, Next, Later.')

def relative_path(value: str) -> Path:
    if not isinstance(value,str) or not value.strip():raise ValueError('An artifact path must be a non-empty string.')
    normalized=value.replace('\\','/')
    parts=PurePosixPath(normalized).parts
    if not parts or normalized.startswith('/') or any(p in {'.','..'} or ':' in p or p.endswith((' ','.')) for p in parts):
        raise ValueError('Unsafe artifact path: '+value)
    if any(re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',p) for p in parts):raise ValueError('Reserved artifact name: '+value)
    if parts[0]!='poc':raise ValueError('Artifacts must be under poc/: '+value)
    return Path(*parts)

def local_reference(source: Path, value: str, root: Path, paths: set[Path]) -> None:
    parsed=urlsplit(value)
    if parsed.scheme in {'data'}:return
    if parsed.scheme or parsed.netloc:raise ValueError(f'External runtime dependency is not allowed: {value}')
    if not parsed.path:return
    target=(source.parent/unquote(parsed.path).replace('\\','/')).resolve()
    if root.resolve() not in target.parents or target not in paths:
        raise ValueError(f'Missing or unsafe local reference in {source.name}: {value}')

class References(HTMLParser):
    def __init__(self):super().__init__();self.refs=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        for key in ('src','href'):
            if attrs.get(key):self.refs.append(attrs[key])

def validate_bundle(artifacts: list[dict], poc: dict, root: Path) -> dict:
    if not isinstance(poc,dict):raise ValueError('D4 requires poc metadata with entrypoint, engine_tests, and browser_test.')
    paths={};case_names=set()
    for item in artifacts:
        path=relative_path(item['path']);key=path.as_posix().lower()
        if key in case_names:raise ValueError('Duplicate artifact path: '+item['path'])
        case_names.add(key);paths[(root/path).resolve()]=item['content']
    entry=relative_path(poc.get('entrypoint',''))
    if (root/entry).resolve() not in paths or entry.suffix.lower() not in {'.html','.py','.js','.cjs','.mjs'}:
        raise ValueError('D4 requires a runnable entrypoint, not just documentation.')
    if not any(p.name.lower()=='readme.md' for p in paths):raise ValueError('D4 bundle requires README.md with setup, workflows, and validation instructions.')
    tests=poc.get('engine_tests',[])
    if not isinstance(tests,list) or not tests:raise ValueError('D4 requires at least one engine test.')
    for test in tests:
        if not isinstance(test,dict) or test.get('runtime') not in {'node','python'}:raise ValueError('Each engine test needs path and node/python runtime.')
        path=relative_path(test.get('path',''))
        suffixes={'.js','.cjs','.mjs'} if test['runtime']=='node' else {'.py'}
        if (root/path).resolve() not in paths or path.suffix not in suffixes:raise ValueError('Missing engine test: '+str(path))
    browser_test=poc.get('browser_test')
    if entry.suffix=='.html':
        if not browser_test:raise ValueError('Browser applications require a browser_test module.')
        path=relative_path(browser_test)
        if (root/path).resolve() not in paths or path.suffix not in {'.js','.cjs'}:raise ValueError('Missing browser_test module.')
    elif browser_test:raise ValueError('browser_test applies only to an HTML entrypoint.')
    for path,content in paths.items():
        if path.suffix=='.html':
            parser=References();parser.feed(content)
            for value in parser.refs:local_reference(path,value,root,set(paths))
        if path.suffix in {'.js','.cjs','.mjs','.css','.py'}:
            refs=re.findall(r'(?:require\(|from\s+|import\s*\(|import\s+)[\s]*[\'"]([^\'"]+)[\'"]',content)
            for value in refs:
                if value.startswith('.'):
                    candidates=[value,value+'.js',value+'.cjs',value+'/index.js']
                    if not any((path.parent/x).resolve() in paths for x in candidates):raise ValueError('Missing script dependency: '+value)
                elif path.suffix in {'.js','.cjs','.mjs'}:
                    builtin=value.removeprefix('node:').split('/')[0]
                    if builtin not in {'assert','fs','path','url','util','crypto','events','os','stream','buffer','timers','http','https','child_process','process','module','readline','zlib','worker_threads','test','perf_hooks'}:
                        raise ValueError('Undeclared external Node dependency: '+value)
                elif path.suffix=='.css':local_reference(path,value,root,set(paths))
            for value in re.findall(r'url\([\s\'"]*([^\)\'\"]+)',content):local_reference(path,value.strip(),root,set(paths))
        if path.suffix=='.py':
            try:tree=ast.parse(content)
            except SyntaxError as exc:raise ValueError('Python syntax error in '+path.name) from exc
            for node in ast.walk(tree):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and not node.level else []
                for name in filter(None,names):
                    module=name.split('.')[0]
                    if module not in sys.stdlib_module_names and (path.parent/(module+'.py')).resolve() not in paths:
                        raise ValueError('Undeclared external Python dependency: '+module)
    return {'entrypoint':entry.as_posix(),'engine_tests':tests,'browser_test':browser_test}

def static_check_bundle(root: Path, artifacts: list[str], runtime: dict) -> None:
    for name in artifacts:
        file=root/relative_path(name)
        if file.suffix in {'.js','.cjs','.mjs'}:
            result=subprocess.run([runtime['node'],'--check',str(file)],capture_output=True,text=True,encoding='utf-8',timeout=15)
            if result.returncode:raise ValueError('JavaScript syntax error in '+name+': '+result.stderr[-1500:])

def runtime_paths(args) -> dict:
    try:bundle=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies'
    except RuntimeError:bundle=ROOT/'.runtime-not-configured'
    node=getattr(args,'node_path',None) or os.environ.get('PIPELINE_NODE') or shutil.which('node') or str(bundle/'node/bin/node.exe')
    explicit_modules=getattr(args,'node_modules',None) or os.environ.get('PIPELINE_NODE_MODULES')
    local_modules=ROOT/'node_modules'
    local_ready=all((local_modules/package/'package.json').is_file() for package in ['@viz-js/viz','playwright'])
    modules=explicit_modules or str(local_modules if local_ready else bundle/'node/node_modules')
    if not Path(node).is_file():raise ValueError('Node runtime missing. Set --node-path or PIPELINE_NODE.')
    for package in ['@viz-js/viz','playwright']:
        if not (Path(modules)/package/'package.json').is_file():raise ValueError(f'{package} missing. Run npm ci from the repository root, or set --node-modules.')
    return {'node':str(Path(node).resolve()),'modules':str(Path(modules).resolve())}

def run_node(runtime: dict, operation: str, *args, timeout=90) -> dict:
    command=[runtime['node'],str(ROOT/'scripts/pipeline_browser.cjs'),operation,runtime['modules'],*[str(x) for x in args]]
    try:result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=timeout,cwd=str(ROOT))
    except subprocess.TimeoutExpired as exc:raise RuntimeError(f'{operation} timed out.') from exc
    if result.returncode:raise RuntimeError(f'{operation} failed: '+(result.stderr or result.stdout)[-2500:])
    return json.loads(result.stdout)

def execute_poc(root: Path, poc: dict, runtime: dict, timeout=60) -> dict:
    before={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in (root/'poc').rglob('*') if p.is_file()}
    results=[]
    for test in poc['engine_tests']:
        executable=runtime['node'] if test['runtime']=='node' else sys.executable
        try:
            result=subprocess.run([executable,str(root/relative_path(test['path']))],cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
            results.append({'path':test['path'],'result':'PASS' if result.returncode==0 else 'FAIL','exit_code':result.returncode,'output':(result.stdout+result.stderr)[-4000:]})
        except subprocess.TimeoutExpired:
            results.append({'path':test['path'],'result':'FAIL','output':'Execution timed out.'})
    if poc.get('browser_test'):
        try:results.append(run_node(runtime,'poc',root,poc['entrypoint'],poc['browser_test'],timeout,timeout=timeout+15))
        except RuntimeError as exc:results.append({'path':poc['browser_test'],'result':'FAIL','output':str(exc)})
    hashes={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in (root/'poc').rglob('*') if p.is_file()}
    if any(hashes.get(name)!=digest for name,digest in before.items()):
        results.append({'path':'source-integrity','result':'FAIL','output':'Generated tests modified source artifacts; results cannot be reused.'})
    evidence={'executedAt':datetime.now(timezone.utc).isoformat(),'status':'PASS' if all(r['result']=='PASS' for r in results) else 'FAIL',
              'execution_checks':len(results),'results':results,'artifactSha256':hashes,
              'scope':'Executed generated test scripts; not clinical, business, security, or representative-user acceptance. Execution is opt-in, not a sandbox.'}
    write_json(root/'poc-validation.json',evidence)
    if evidence['status']!='PASS':raise RuntimeError('POC tests failed; inspect poc-validation.json. D5 was not generated.')
    return evidence

def with_execution_evidence(markdown: str, evidence: dict | None) -> str:
    lines=['Execution status: **NOT RUN**. Generated tests were not executed; no PASS result is claimed. Review source before enabling test execution.'] if evidence is None else [
        f"Execution status: **PASS** — {evidence['execution_checks']} test-script execution checks completed at {evidence['executedAt']}. This counts scripts, not individual assertions.",
        '[Verified execution evidence](poc-validation.json). Artifact hashes identify the tested source.']
    lines.append('This proof targets the coordination/design question above. Business improvements, real integration, scale, and user acceptance remain unverified.')
    pattern=r'(^#{2,6}\s+Results and learning\s*\n).*?(?=^#{2,6}\s|\Z)'
    return re.sub(pattern,lambda m:m.group(1)+'\n'+'\n\n'.join(lines)+'\n\n',markdown,count=1,flags=re.M|re.S)
