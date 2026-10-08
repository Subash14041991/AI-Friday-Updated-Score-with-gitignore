"""Validate a current D4 source/evidence profile; publish only with --publish.

All scenario vocabulary and artifact locations come from the profile. By
default, this command checks consistency without writing deliverable outputs.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import hashlib
import html
import json
import re
from run_pipeline import markdown_to_html

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ['Question and hypothesis', 'Scope and safety', 'Prototype', 'Test method',
            'Results and learning', 'Limitations and what remains unproven', 'Handoff to D5']

def project_path(value):
    path = (ROOT / value).resolve()
    if ROOT != path and ROOT not in path.parents:
        raise ValueError('Profile path must stay within the project: '+str(value))
    return path

def prepare(profile):
    source = project_path(profile['sourceDirectory'])
    engine = json.loads(project_path(profile['engineEvidence']).read_text(encoding='utf-8'))
    browser = json.loads(project_path(profile['browserEvidence']).read_text(encoding='utf-8'))
    outcomes = engine.get('results', [])
    checks = browser.get('checks', [])
    if not outcomes or engine.get('passed') != len(outcomes) or any(
        row.get('result', row.get('actual')) != 'PASS' for row in outcomes):
        raise ValueError('Engine evidence is incomplete or did not pass.')
    if not checks or browser.get('passed') != len(checks) or browser.get('result', 'PASS') != 'PASS':
        raise ValueError('Browser evidence is incomplete or did not pass.')
    artifacts = profile['artifacts']
    if not artifacts:
        raise ValueError('A profile must identify its current runnable artifacts.')
    for name in artifacts:
        artifact = (source/name).resolve()
        if source not in artifact.parents:
            raise ValueError('Artifact escapes its source directory.')
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        for label, evidence in [('engine', engine), ('browser', browser)]:
            if evidence.get('artifactSha256', {}).get(name) != digest:
                raise ValueError(f'{label} evidence does not match current source: {name}')
    def local_time(value):
        return datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(
            timezone(timedelta(hours=5,minutes=30))).strftime('%d %b %Y, %I:%M %p IST')
    md = project_path(profile['response']).read_text(encoding='utf-8').strip()
    for key,value in {'engine_count':engine['passed'],'browser_count':browser['passed'],
                      'engine_run':local_time(engine['executedAt']),
                      'browser_run':local_time(browser['executedAt'])}.items():
        md = md.replace('{{'+key+'}}',str(value))
    if '{{' in md or len(md.split()) > 600:
        raise ValueError('Unresolved value or D4 word budget exceeded.')
    parts = re.split(r'^#### ',md,flags=re.M)[1:]
    sections = [(p.split('\n',1)[0],p.split('\n',1)[1].strip()) for p in parts]
    if [title for title,_ in sections] != SECTIONS:
        raise ValueError('D4 sections must match Agent 4 output format.')
    report = project_path(profile['report'])
    links = set(profile['links'])
    for destination in links:
        target = (report.parent/destination).resolve()
        if ROOT not in target.parents or not target.is_file():
            raise ValueError('Artifact link is missing or outside the project: '+destination)
    if set(re.findall(r'\[[^\]]+\]\(([^)]+)\)',md)) - links:
        raise ValueError('Response contains a link not declared in the current profile.')
    def render(index):
        title,content = sections[index]
        rendered = markdown_to_html(content)
        for destination in links:
            pattern = r'<span class="link">([^<]+) \('+re.escape(html.escape(destination,quote=False))+r'\)</span>'
            rendered = re.sub(pattern,lambda m:'<a href="'+html.escape(destination,quote=True)+'">'+m.group(1)+'</a>',rendered)
        return '<h2>'+html.escape(title)+'</h2>'+rendered
    page = ('<section class="page d4-page"><div class="eyebrow">'+html.escape(profile['eyebrow'])+'</div>'
            '<h1>D4. Focused POC / validation</h1><p class="lede">'+html.escape(profile['subtitle'])+'</p>'
            '<div class="columns"><div>'+render(0)+render(1)+render(2)
            +'</div><div>'+render(3)+render(4)+'</div></div><div class="columns"><div>'
            +render(5)+'</div><div>'+render(6)+'</div></div>'
            '<div class="footer"><span>'+html.escape(profile['footer'])+'</span><span>4 / 5</span></div></section>')
    original = report.read_text(encoding='utf-8')
    matches = list(re.finditer(r'<section class="page(?: [^\"]+)?">.*?</section>',original,re.S))
    if len(matches) != 5:
        raise ValueError('Expected five report sections.')
    match = matches[3]
    return md, original[:match.start()]+page+original[match.end():], engine['passed'], browser['passed']

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,default=ROOT/'poc/referral-coordination/report-source/profile.json')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-only',action='store_true',help='Validate only; this is the default.')
    mode.add_argument('--publish',action='store_true',help='Explicitly regenerate D4 Markdown and report page 4.')
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding='utf-8'))
    md, report, engine_count, browser_count = prepare(profile)
    if args.publish:
        project_path(profile['markdown']).write_text(md+'\n',encoding='utf-8')
        project_path(profile['report']).write_text(report,encoding='utf-8')
        print(f'Published current D4 ({len(md.split())} words) and report page 4.')
    else:
        print(f'Consistency check passed: {len(md.split())} words, {engine_count} rule tests, '
              f'{browser_count} browser checks, matching source hashes and valid artifact links. No output files changed.')

if __name__ == '__main__':
    main()
