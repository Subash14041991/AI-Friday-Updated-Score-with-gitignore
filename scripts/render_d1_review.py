"""Publish a generated D1 response and render report page 1 from that Markdown.

This renderer does not generate or rewrite business content. Pass the complete
agent response, produced using agent-01-problem-success.md, as its input.
"""
from pathlib import Path
import argparse
import re
from run_pipeline import markdown_to_html

ROOT = Path(__file__).resolve().parent.parent
NAMES = ['Problem statement', 'People and current process', 'Key constraints',
         'Assumptions to validate', 'Success measures', 'Open questions', 'Handoff to D2']

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('response', type=Path)
    args = parser.parse_args()
    md = args.response.read_text(encoding='utf-8').strip()
    parts = re.split(r'^#### ', md, flags=re.M)[1:]
    sections = {p.split('\n', 1)[0]: p.split('\n', 1)[1].strip() for p in parts}
    if list(sections) != NAMES:
        raise ValueError('D1 response must contain the revised prompt sections in order.')
    if len(md.split()) > 750:
        raise ValueError('D1 exceeds the prompt word limit.')
    def render(name):
        return '<h2>' + name + '</h2>' + markdown_to_html(sections[name])
    left = ''.join(render(n) for n in NAMES if n not in ['Assumptions to validate', 'Success measures'])
    right = render('Assumptions to validate') + render('Success measures')
    page = ('<section class="page d1-page"><div class="eyebrow">Healthcare referral architecture · Deliverable 1 of 5</div>'
            '<h1>D1. Problem &amp; success snapshot</h1><p class="lede">Problem, people, constraints, assumptions, and measurable outcomes — based on the supplied healthcare scenario.</p>'
            '<div class="columns wide-left"><div>' + left + '</div><div>' + right + '</div></div>'
            '<div class="footer"><span>Scenario-based brief · Business stakeholders confirm roles, measures, and targets.</span><span>1 / 5</span></div></section>')
    folder = ROOT / 'output/healthcare'
    report = folder / 'final-submission-report.html'
    original = report.read_text(encoding='utf-8')
    updated, count = re.subn(r'<section class="page(?: d1-page)?">.*?</section>', lambda m: page,
                            original, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Could not identify report page 1.')
    (folder / 'D1-patient-journey-success-snapshot.md').write_text(md + '\n', encoding='utf-8')
    report.write_text(updated, encoding='utf-8')
    print(f'Published generated D1 ({len(md.split())} words) and rendered page 1 from it.')

if __name__ == '__main__':
    main()
