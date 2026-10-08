"""Publish generated D3 and render page 3 using its source-derived SVG."""
from pathlib import Path
import argparse
import re
from run_pipeline import markdown_to_html

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('response', type=Path)
    parser.add_argument('diagram', type=Path)
    args = parser.parse_args()
    md = args.response.read_text(encoding='utf-8').strip()
    parts = re.split(r'^#### ', md, flags=re.M)[1:]
    sections = [(p.split('\n',1)[0],p.split('\n',1)[1].strip()) for p in parts]
    if len(sections) != 7:
        raise ValueError('Expected the seven Agent 3 sections.')
    notes = re.sub(r'```mermaid.*?```', '', md, flags=re.S)
    if len(notes.split()) > 550:
        raise ValueError('Notes exceed Agent 3 word limit.')
    svg = args.diagram.read_text(encoding='utf-8')
    svg = svg[svg.index('<svg'):]
    svg = re.sub(r'width="[^"]+" height="[^"]+"', 'class="d3-diagram" role="img" aria-label="Proposed shared referral coordination architecture"', svg, count=1)
    def render(i):
        title, content = sections[i]
        return '<h2>' + title + '</h2>' + markdown_to_html(content)
    diagram_notes = re.sub(r'```mermaid.*?```', '', sections[0][1], flags=re.S).strip()
    page = ('<section class="page d3-page"><div class="eyebrow">Healthcare referral architecture · Deliverable 3 of 5</div>'
            '<h1>D3. Target-state architecture</h1><p class="lede">Proposed shared coordination around the retained EHR · Select and approve one initial referral process.</p>'
            + svg + '<div class="d3-summary">' + markdown_to_html(diagram_notes) + '</div>'
            + '<div class="columns"><div>' + render(1) + render(2) + render(6) + '</div><div>'
            + render(3) + render(4) + render(5) + '</div></div>'
            + '<div class="footer"><span>Conceptual proposal · Interfaces, controls, scope, and operating responsibilities require validation.</span><span>3 / 5</span></div></section>')
    folder = ROOT/'output/healthcare'
    report = folder/'final-submission-report.html'
    original = report.read_text(encoding='utf-8')
    matches = list(re.finditer(r'<section class="page(?: [^\"]+)?">.*?</section>',original,re.S))
    if len(matches) != 5: raise ValueError('Expected five pages.')
    match = matches[2]
    updated = original[:match.start()] + page + original[match.end():]
    style = '''
/* D3 review layout */
.d3-page { font-size:14px; line-height:1.4; }
.d3-page h2 { font-size:16px; margin-top:12px; }
.d3-page .lede { font-size:13px; }
.d3-diagram { display:block; width:100%; height:auto; max-height:430px; margin:14px 0; }
.d3-summary { padding:10px 14px; background:#e6f5f5; border-left:4px solid #087f8c; }
.d3-page .columns { gap:25px; grid-template-columns:1.1fr 1fr; }
.d3-page table { font-size:12px; line-height:1.4; }
.d3-page th,.d3-page td { padding:7px; }
.d3-page th:nth-child(1) { width:25%; }
.d3-page th:nth-child(2) { width:40%; }
.d3-page th:nth-child(3) { width:35%; }
.d3-page li { margin:4px 0; }
@media print { .d3-page {font-size:12px;} .d3-page h2 {font-size:14px;} .d3-page table {font-size:11px;} .d3-diagram {max-height:370px;} }
@media screen and (max-width:850px) { .d3-page .columns {grid-template-columns:1fr;} }
/* End D3 review layout */
'''
    updated = re.sub(r'/\* D3 review layout \*/.*?/\* End D3 review layout \*/','',updated,flags=re.S)
    updated = updated.replace('</style>',style+'</style>',1)
    (folder/'D3-target-state-architecture.md').write_text(md+'\n',encoding='utf-8')
    (folder/'d3-architecture.svg').write_text(svg,encoding='utf-8')
    report.write_text(updated,encoding='utf-8')
    print(f'Published D3 ({len(notes.split())} note words) and source-derived page 3.')

if __name__ == '__main__':
    main()
