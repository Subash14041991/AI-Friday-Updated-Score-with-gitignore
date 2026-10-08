"""Publish a generated D2 response and render report page 2 from its Markdown."""
from pathlib import Path
import argparse
import re
from run_pipeline import markdown_to_html

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('response', type=Path)
    args = parser.parse_args()
    md = args.response.read_text(encoding='utf-8').strip()
    parts = re.split(r'^#### ', md, flags=re.M)[1:]
    sections = [(p.split('\n', 1)[0], p.split('\n', 1)[1].strip()) for p in parts]
    if len(sections) != 7 or len(md.split()) > 750:
        raise ValueError('D2 must contain seven sections and at most 750 words.')
    def render(index):
        name, content = sections[index]
        return '<h2>' + name + '</h2>' + markdown_to_html(content)
    page = ('<section class="page d2-page"><div class="eyebrow">Healthcare referral architecture · Deliverable 2 of 5</div>'
            '<h1>D2. Architecture options &amp; decision</h1>' + render(0)
            + '<div class="columns"><div class="card">' + render(1) + '</div><div class="card">' + render(2)
            + '</div></div>' + render(3) + '<div class="columns"><div>' + render(4)
            + '</div><div>' + render(5) + render(6) + '</div></div>'
            + '<div class="footer"><span>Conditional recommendation · Clinical, operational, and technical review required.</span><span>2 / 5</span></div></section>')
    folder = ROOT / 'output/healthcare'
    report = folder / 'final-submission-report.html'
    original = report.read_text(encoding='utf-8')
    matches = list(re.finditer(r'<section class="page(?: [^\"]+)?">.*?</section>', original, re.S))
    if len(matches) != 5:
        raise ValueError('Expected five report sections.')
    second = matches[1]
    updated = original[:second.start()] + page + original[second.end():]
    style = '''
/* D2 review layout */
.d2-page { font-size:14px; line-height:1.4; }
.d2-page h2 { font-size:16px; margin-top:12px; }
.d2-page .columns { gap:22px; }
.d2-page table { font-size:12px; line-height:1.35; }
.d2-page th,.d2-page td { padding:7px; }
.d2-page th:nth-child(1) { width:22%; }
.d2-page th:nth-child(2),.d2-page th:nth-child(3) { width:39%; }
.d2-page li { margin:4px 0; }
@media print { .d2-page { font-size:12px; } .d2-page h2 { font-size:14px; } .d2-page table { font-size:11px; } }
/* End D2 review layout */
'''
    updated = re.sub(r'/\* D2 review layout \*/.*?/\* End D2 review layout \*/', '', updated, flags=re.S)
    updated = updated.replace('</style>', style + '</style>', 1)
    (folder / 'D2-architecture-options-decision.md').write_text(md + '\n', encoding='utf-8')
    report.write_text(updated, encoding='utf-8')
    print(f'Published D2 ({len(md.split())} words); page 2 rendered from generated Markdown.')

if __name__ == '__main__':
    main()
