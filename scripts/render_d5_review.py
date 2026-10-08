"""Publish generated D5 and render page 5 from its Markdown source."""
from pathlib import Path
import argparse
import re
from run_pipeline import markdown_to_html

ROOT = Path(__file__).resolve().parent.parent
NAMES = ['Now / Next / Later roadmap','Top five risks and mitigations','AI-use reflection','Delivery guardrails']

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('response',type=Path)
    args = parser.parse_args()
    md = args.response.read_text(encoding='utf-8').strip()
    parts = re.split(r'^#### ',md,flags=re.M)[1:]
    sections = [(p.split('\n',1)[0],p.split('\n',1)[1].strip()) for p in parts]
    if [title for title,_ in sections] != NAMES or len(md.split()) > 600:
        raise ValueError('D5 section format or word budget mismatch.')
    for index, count in [(0,3),(1,5)]:
        rows=[line for line in sections[index][1].splitlines() if line.startswith('|')]
        if len(rows)!=count+2: raise ValueError('D5 must contain three phases and five risks.')
    def render(index):
        title, content = sections[index]
        return '<h2>'+title+'</h2>'+markdown_to_html(content)
    page = ('<section class="page d5-page"><div class="eyebrow">Healthcare referral architecture · Deliverable 5 of 5</div>'
            '<h1>D5. Delivery &amp; risk plan</h1><p class="lede">One phased plan · Five practical risks · Pilot decisions based on verified evidence.</p>'
            +render(0)+render(1)+'<div class="columns"><div>'+render(2)+'</div><div>'+render(3)
            +'</div></div><div class="footer"><span>Proposed plan and accountable roles · Business, clinical, and privacy approval remain pending.</span><span>5 / 5</span></div></section>')
    folder = ROOT/'output/healthcare'
    report = folder/'final-submission-report.html'
    original = report.read_text(encoding='utf-8')
    matches = list(re.finditer(r'<section class="page(?: [^\"]+)?">.*?</section>',original,re.S))
    if len(matches)!=5: raise ValueError('Expected five report sections.')
    match=matches[4]
    updated=original[:match.start()]+page+original[match.end():]
    style='''
/* D5 review layout */
.d5-page {font-size:15px;line-height:1.4;}
.d5-page h2 {font-size:17px;margin-top:14px;}
.d5-page .lede {font-size:13px;}
.d5-page table {font-size:13px;line-height:1.4;}
.d5-page th,.d5-page td {padding:9px;}
.d5-page table:first-of-type th:nth-child(1) {width:7%;}
.d5-page table:first-of-type th:nth-child(2) {width:38%;}
.d5-page table:first-of-type th:nth-child(3) {width:37%;}
.d5-page table:first-of-type th:nth-child(4) {width:18%;}
.d5-page table:nth-of-type(2) th:nth-child(1) {width:27%;}
.d5-page table:nth-of-type(2) th:nth-child(2) {width:55%;}
.d5-page table:nth-of-type(2) th:nth-child(3) {width:18%;}
.d5-page .columns {gap:28px;}
.d5-page li {margin:5px 0;}
@media print {.d5-page{font-size:13px;}.d5-page h2{font-size:15px;}.d5-page table{font-size:12px;}}
/* End D5 review layout */
'''
    updated=re.sub(r'/\* D5 review layout \*/.*?/\* End D5 review layout \*/','',updated,flags=re.S)
    updated=updated.replace('</style>',style+'</style>',1)
    (folder/'D5-delivery-safety-risk-plan.md').write_text(md+'\n',encoding='utf-8')
    report.write_text(updated,encoding='utf-8')
    print(f'Published D5 ({len(md.split())} words) and regenerated report page 5.')

if __name__=='__main__':
    main()
