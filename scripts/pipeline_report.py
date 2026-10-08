"""One scenario-neutral report layout, shared by every orchestration run."""
from __future__ import annotations
import html
import re
try:
    from .pipeline_support import sections
except ImportError:
    from pipeline_support import sections

def build(deliverables, scenario_name, diagram_svg, render_markdown):
    titles={'D1':'Problem & success snapshot','D2':'Architecture options & decision','D3':'Target-state architecture','D4':'Focused POC / validation','D5':'Delivery & risk plan'}
    pages=[]
    for number,(stage,md) in enumerate(deliverables.items(),1):
        items=sections(md)
        def render(i):
            name,content=items[i]
            return '<div class="section-block"><h2>'+html.escape(name)+'</h2>'+render_markdown(content)+'</div>'
        if stage=='D1':
            split=next(i for i,(name,_) in enumerate(items) if name=='Assumptions to validate')
            body='<div class="columns"><div>'+''.join(render(i) for i in range(split))+'</div><div>'+''.join(render(i) for i in range(split,len(items)))+'</div></div>'
        elif stage=='D2':
            comparison=next(i for i,(name,_) in enumerate(items) if name=='Trade-off comparison')
            body=render(0)+'<div class="columns option-cards">'+''.join('<div>'+render(i)+'</div>' for i in range(1,comparison))+'</div>'+render(comparison)+'<div class="columns"><div>'+render(comparison+1)+'</div><div>'+render(comparison+2)+render(comparison+3)+'</div></div>'
        elif stage=='D3':
            notes=re.sub(r'```mermaid.*?```','',items[0][1],flags=re.S).strip()
            body=diagram_svg+'<div class="diagram-notes">'+render_markdown(notes)+'</div><div class="columns"><div>'+render(1)+render(2)+render(6)+'</div><div>'+render(3)+render(4)+render(5)+'</div></div>'
        elif stage=='D4':
            body='<div class="columns"><div>'+render(0)+render(1)+render(2)+'</div><div>'+render(3)+render(4)+'</div></div><div class="columns"><div>'+render(5)+'</div><div>'+render(6)+'</div></div>'
        else:body=render(0)+render(1)+'<div class="columns"><div>'+render(2)+'</div><div>'+render(3)+'</div></div>'
        pages.append(f'<section class="page {stage.lower()}"><header><div class="eyebrow">Architecture decision pack · {number} of 5</div><h1>{stage}. {html.escape(titles[stage])}</h1><p class="scenario">Scenario: {html.escape(scenario_name)}</p></header><article class="report-body">{body}</article><footer><span>Proposed design · Approvals and operational readiness are not implied.</span><span>{number} / 5</span></footer></section>')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Final submission report</title><style>
:root{--ink:#173047;--muted:#52677a;--line:#cbd7e1;--accent:#087f8c}*{box-sizing:border-box}body{margin:0;background:#e5ebef;color:var(--ink);font:14px/1.4 "Segoe UI",Arial,sans-serif}.page{width:min(100%,420mm);min-height:297mm;margin:14px auto;padding:11mm 13mm 14mm;background:white;position:relative;box-shadow:0 2px 16px #1d33451f;break-after:page}.page:last-child{break-after:auto}header{margin-bottom:14px}.eyebrow{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:800}h1{font-size:26px;margin:5px 0}.scenario{font-size:12px;color:var(--muted)}h2{font-size:16px;color:#075b67;margin:12px 0 5px}p{margin:4px 0 8px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start}.option-cards>div{padding:10px 14px;border:1px solid var(--line);border-radius:6px}.section-block{min-width:0}ul,ol{padding-left:20px;margin:4px 0 8px}li{margin:3px 0}table{border-collapse:collapse;table-layout:fixed;width:100%;font-size:12px;line-height:1.35;margin:7px 0 10px}th,td{border:1px solid var(--line);padding:7px;vertical-align:top;overflow-wrap:anywhere;text-align:left}th{background:#f1f6f9;color:#075b67}a{color:#087f8c;overflow-wrap:anywhere}code{font-family:Consolas,monospace;font-size:.9em;background:#f1f4f6;padding:1px 3px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:10px}.architecture-diagram{display:block;width:100%;height:auto;max-height:340px;margin:8px 0 14px}.diagram-notes{background:#e6f5f5;border-left:4px solid var(--accent);padding:8px 12px}.d1 table th:nth-child(2){width:32%}.d2 table th:first-child{width:22%}.d4 table th:first-child{width:25%}.d4 table th:nth-child(2){width:60%}.d5 table:first-of-type th:first-child{width:7%}.d5 table:first-of-type th:nth-child(2){width:38%}.d5 table:first-of-type th:nth-child(3){width:37%}footer{margin-top:20px;display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:5px;color:var(--muted);font-size:9px}
@media(max-width:850px){.page{min-height:0;margin:8px auto;padding:18px}.columns{grid-template-columns:1fr;gap:8px}.architecture-diagram{max-height:none}table{font-size:11px}}
@media print{@page{size:A3 landscape;margin:0}html,body{width:420mm;background:white;print-color-adjust:exact;-webkit-print-color-adjust:exact}body{font-size:12px}.page{width:420mm;min-height:297mm;height:297mm;margin:0;padding:10mm 13mm 14mm;box-shadow:none;overflow:visible}h1{font-size:23px}h2{font-size:14px}table{font-size:11px;line-height:1.35}.architecture-diagram{max-height:300px}footer{position:absolute;bottom:6mm;left:13mm;right:13mm}}
</style></head><body>'''+''.join(pages)+'</body></html>\n'
